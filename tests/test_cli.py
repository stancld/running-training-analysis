"""End to end: a CSV cache through the `tl site` command into the page payload.

Each test points tl at its own cache in a temp dir, so Dan's real data/ is never touched.
Expected values are worked out by hand from the rows, not read back from tl.
"""

import datetime as dt
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
    # No weeks before the race week: WoW and ACWR are undefined (null); after the ride week, a real 0.
    assert (race["wow"], race["acwr"]) == (None, None)
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
    # 4.5, 4.5, 5, 6 h, then 7.2 h: ACWR 7.2 / mean(4.5, 4.5, 5, 6) = exactly 1.44, at its cap.
    # 9 h: WoW exactly 1.25 and exactly 100 km, but ACWR 9 / 5.675 = 1.59.
    # 11.7 h: WoW 1.30, ACWR 11.7 / 6.8 = 1.72, 101 km. Climb keeps R3 quiet; Jun-Aug is outside
    # Dec-Apr. Then four empty weeks: a 4 h week after them has no baseline and still flags R2.
    (tmp_path / "activities.csv").write_text(
        "date,sport,km,min,vert\n"
        "2026-06-06,Run,40.0,270,1000\n"
        "2026-06-13,Run,40.0,270,1000\n"
        "2026-06-20,Run,45.0,300,1000\n"
        "2026-06-27,Run,55.0,360,1500\n"
        "2026-07-04,Run,70.0,432,2000\n"
        "2026-07-11,Run,100.0,540,3000\n"
        "2026-07-18,Run,101.0,702,3600\n"
        "2026-08-22,Run,40.0,240,1000\n"
    )
    weeks = site()["weeks"]
    assert {w["start"]: w["acwr"] for w in weeks}["2026-06-29"] == 1.44  # coupled, it read 1.27
    flags = {w["start"]: w["flags"] for w in weeks if w["flags"]}
    assert flags == {
        "2026-07-06": ["R2"],
        "2026-07-13": ["R1", "R2", "R6"],
        "2026-08-17": ["R2"],
    }


def test_form_is_freshness_going_into_the_day(
    tmp_path: Path, site: Callable[[], dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    # No relative effort, so a running minute is 0.35 load units: 35 on Saturday, 70 on Sunday.
    # CTL/ATL close each day with gains 1 - e^(-1/42) = 0.02353 and 1 - e^(-1/7) = 0.13312.
    monkeypatch.setattr(config, "TODAY", dt.date(2026, 6, 8))
    (tmp_path / "activities.csv").write_text(
        "date,sport,km,min,vert\n2026-06-06,Run,20.0,100,500\n2026-06-07,Run,40.0,200,1000\n"
    )
    fit = {f["date"]: f for f in site()["fitness"]}
    # Sunday's form is Saturday's close (0.82 - 4.66), not after Sunday's long run (2.45 - 13.36).
    assert fit["2026-06-07"] == {"date": "2026-06-07", "ctl": 2.5, "atl": 13.4, "tsb": -3.8}
    assert fit["2026-06-08"] == {"date": "2026-06-08", "ctl": 2.4, "atl": 11.6, "tsb": -10.9}
