"""End to end: a CSV cache through the `tl site` command into the page payload.

Each test points tl at its own cache in a temp dir, so Dan's real data/ is never touched.
Expected values are worked out by hand from the rows, not read back from tl.
"""

import json
import subprocess
from pathlib import Path

import pytest

from tl import cli, config

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def site(tmp_path, monkeypatch):
    """Run `tl site` on the cache in tmp_path and return the payload."""
    monkeypatch.setattr(config, "DATA", tmp_path)

    def run():
        out = tmp_path / "payload.json"
        assert cli.main(["site", str(out)]) == 0
        return json.loads(out.read_text())

    return run


def test_payload_carries_the_cache(tmp_path, site):
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

    # All three runs average 139-163 bpm, so Z2: the race measured at 162, the others
    # modelled from relative effort (146 and 156 bpm).
    p1 = p["zones"]["phases"][0]
    assert (p1["minutes"], p1["measured"], p1["modelled"]) == ([0, 365, 0, 0, 0], 240, 125)


def test_guardrails_fire_past_the_limit_not_at_it(tmp_path, site):
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
