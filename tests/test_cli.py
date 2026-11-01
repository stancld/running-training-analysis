"""End to end: a CSV cache through the `tl site` command into the page payload.

Each test points tl at its own cache in a temp dir, so Dan's real data/ is never touched.
Expected values are worked out by hand from the rows, not read back from tl.
"""

import json
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tl import cli, config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def site(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[[], dict[str, Any]]:
    """Run `tl site` on the cache in tmp_path and return the payload."""
    monkeypatch.setattr(config, "DATA", tmp_path)

    def run() -> dict[str, Any]:
        out = tmp_path / "payload.json"
        assert cli.main(["site", str(out)]) == 0
        return json.loads(out.read_text())

    return run


def test_payload_carries_the_cache(tmp_path: Path, site: Callable[[], dict[str, Any]]) -> None:
    # The cache CI and the Playwright tests use, plus a stray header from hand-appending.
    subprocess.run([ROOT / "scripts" / "synthetic_cache.sh", tmp_path], check=True)
    with (tmp_path / "activities.csv").open("a") as fh:
        fh.write("date,sport,km,min,vert\n")
    p = site()

    week = {w["start"]: w for w in p["weeks"]}
    race, ride = week["2026-08-31"], week["2026-09-07"]
    assert (race["run_h"], race["km"]) == (6.08, 69.6)  # 55 + 70 + 240 min; 10 + 12 + 47.6 km
    # No running before the race week: WoW is undefined (null); after the ride week it is a real 0.
    assert (race["wow"], race["acwr"]) == (None, 1.0)
    assert (ride["wow"], ride["acwr"]) == (0.0, 0.0)

    acts = [a for d in p["diary"][0]["days"] for a in d["acts"]]
    assert {"type": "RACE", "mins": 240, "km": 47.6} in [
        {k: a[k] for k in ("type", "mins", "km")} for a in acts
    ]

    # The race splits by its stream (2 h Z2, 1 h Z3, 30 min each Z4 and Z5), not its 162 bpm
    # average; the other runs count whole in Z2, modelled from relative effort (146, 156 bpm).
    p1 = p["zones"]["phases"][0]
    run, bike = p1["run"], p1["bike"]
    assert run["minutes"] == [0, 245, 60, 30, 30]
    assert (run["stream"], run["measured"], run["modelled"]) == (240, 0, 125)
    # The 90-min ride splits 30/45/15 min by HR and 60/20/10 min by power (Garmin zones);
    # the 60-min ride has no stream and no HR fallback.
    assert (bike["minutes"], bike["power"]) == ([30, 45, 15, 0, 0], [0, 60, 20, 10, 0, 0, 0])
    assert (bike["stream"], bike["no_hr"]) == (90, 60)


def test_guardrails_fire_past_the_limit_not_at_it(
    tmp_path: Path, site: Callable[[], dict[str, Any]]
) -> None:
    # 4 h -> 5 h (WoW exactly 1.25, exactly 100 km) -> 6.5 h (WoW 1.30, 101 km).
    # ACWR on the last week is 6.5 / 5.17 = 1.26, under its 1.30 cap. June is outside Dec-Apr.
    (tmp_path / "activities.csv").write_text(
        "date,sport,km,min,vert\n"
        "2026-06-06,Run,40.0,240,1500\n"
        "2026-06-13,Run,100.0,300,1800\n"
        "2026-06-20,Run,101.0,390,2400\n"
    )
    flags = {w["start"]: w["flags"] for w in site()["weeks"]}
    assert flags == {"2026-06-01": [], "2026-06-08": [], "2026-06-15": ["R1", "R6"]}
