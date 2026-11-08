"""End to end: a CSV cache through the `tl site` command into the page payload.

Each test points tl at its own cache in a temp dir, so Dan's real data/ is never touched.
Expected values are worked out by hand from the rows, not read back from tl.
"""

import base64
import datetime as dt
import json
import secrets
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from scripts import fetch_zones
from tl import cli, config

ROOT = Path(__file__).resolve().parents[1]


def test_refresh_appends_completed_days_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    today = dt.datetime.now(fetch_zones.ZoneInfo("Europe/Prague")).date()
    seed = today - dt.timedelta(days=10)
    original = f"date,sport,km,min,vert\n{seed},Run,9.1,51,240\n"
    (tmp_path / "activities.csv").write_text(original)
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(fetch_zones, "TOKEN_FILE", tmp_path / "token")
    monkeypatch.setattr(fetch_zones.sys, "argv", ["fetch_zones.py", "--refresh"])
    monkeypatch.setenv("STRAVA_CLIENT_ID", "client")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")
    monkeypatch.setenv("STRAVA_REFRESH_TOKEN", "initial")
    monkeypatch.delenv("TRAINING_STATE_KEY", raising=False)

    def activity(ident: int, ago: int, minutes: int) -> dict[str, Any]:
        return {
            "id": ident,
            "start_date_local": f"{today - dt.timedelta(days=ago)}T12:00:00Z",
            "sport_type": "Run",
            "distance": 12345,
            "moving_time": minutes * 60,
            "total_elevation_gain": 321,
            "average_heartrate": 147,
            "has_heartrate": True,
        }

    activities = [
        activity(1, 10, 51),
        activity(2, 8, 64),
        activity(3, 1, 37),
        activity(4, 0, 22),
        activity(6, 1, 29),
    ]

    def request(url: str, token: str | None = None, data: dict | None = None) -> Any:  # noqa: ANN401, ARG001
        if url.endswith("/oauth/token"):
            return {"access_token": "access", "refresh_token": "rotated"}
        if "/streams?" in url:
            ident = int(url.split("/activities/")[1].split("/", maxsplit=1)[0])
            minutes = next(a["moving_time"] for a in activities if a["id"] == ident)
            return {
                "time": {"data": [0, minutes]},
                "heartrate": {"data": [147, 147]},
            }
        query = fetch_zones.urllib.parse.parse_qs(fetch_zones.urllib.parse.urlparse(url).query)
        after = int(query["after"][0])
        # An implementation that fetches plan-period or full history fails here.
        assert after >= int(dt.datetime.combine(seed, dt.time(), dt.UTC).timestamp())
        if query["page"] == ["1"]:
            return activities
        # A new upload can shift an activity across two page boundaries.
        return [activities[1]] if query["page"] == ["2"] else []

    monkeypatch.setattr(fetch_zones, "_call", request)
    assert fetch_zones.main() == 0
    activities.append(activity(5, 4, 42))  # late upload inside the overlap
    assert fetch_zones.main() == 0
    snapshot = (tmp_path / "activities.csv").read_bytes()
    assert fetch_zones.main() == 0
    assert (tmp_path / "activities.csv").read_bytes() == snapshot
    assert snapshot.decode().startswith(original)
    dataset = fetch_zones.data.Dataset.load()
    assert sorted(a.mins for a in dataset.activities) == [29, 37, 42, 51, 64]
    for a in dataset.activities:
        if a.date != seed:
            assert a.zones is not None
            assert sum(a.zones) == a.mins * 60
    assert [(a.km, a.vert, a.hr) for a in dataset.activities if a.mins == 42] == [
        (12.345, 321, 147)
    ]
    assert (tmp_path / "token").read_text() == "rotated"
    assert (tmp_path / "token").stat().st_mode & 0o777 == 0o600


def test_refresh_stops_when_rotated_token_cannot_be_checkpointed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = "date,sport,km,min,vert\n2026-09-01,Run,10,60,300\n"
    (tmp_path / "activities.csv").write_text(original)
    monkeypatch.setattr(config, "DATA", tmp_path)
    monkeypatch.setattr(fetch_zones, "TOKEN_FILE", tmp_path / "token")
    monkeypatch.setattr(fetch_zones.sys, "argv", ["fetch_zones.py", "--refresh"])
    monkeypatch.setenv("STRAVA_CLIENT_ID", "client")
    monkeypatch.setenv("STRAVA_CLIENT_SECRET", "secret")
    monkeypatch.setenv("STRAVA_REFRESH_TOKEN", "initial")
    monkeypatch.setenv("TRAINING_STATE_KEY", secrets.token_hex(32))
    monkeypatch.setenv("GNUPGHOME", str(tmp_path / "gnupg"))
    (tmp_path / "gnupg").mkdir(mode=0o700)
    monkeypatch.setattr(fetch_zones, "STATE_HEAD", tmp_path / "head.json")
    (tmp_path / "head.json").write_text('{"name":"main","target":{"oid":"seed"}}')
    monkeypatch.setattr(
        fetch_zones,
        "_call",
        lambda *_args, **_kwargs: {"access_token": "access", "refresh_token": "rotated"},
    )

    def denied(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401, ARG001
        raise subprocess.CalledProcessError(1, "gh")

    monkeypatch.setattr(fetch_zones, "_github", denied)
    with pytest.raises(subprocess.CalledProcessError):
        fetch_zones.main()
    assert (tmp_path / "activities.csv").read_text() == original
    assert not (tmp_path / "strava_sync.json").exists()
    assert (tmp_path / "token").read_text() == "rotated"


def test_private_checkpoint_encrypts_and_rejects_stale_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = tmp_path / "seed"
    cache.mkdir()
    original = b"date,sport,km,min,vert\n2026-09-01,Run,10,60,300\n"
    (cache / "activities.csv").write_bytes(original)
    token = tmp_path / "token"
    token.write_text("private-refresh-token")
    monkeypatch.setattr(config, "DATA", cache)
    monkeypatch.setattr(fetch_zones, "TOKEN_FILE", token)
    monkeypatch.setattr(fetch_zones, "STATE_HEAD", tmp_path / "head.json")
    key = secrets.token_hex(32)
    monkeypatch.setenv("TRAINING_STATE_KEY", key)
    monkeypatch.setenv("GNUPGHOME", str(tmp_path / "gnupg"))
    (tmp_path / "gnupg").mkdir(mode=0o700)
    remote: dict[str, bytes] = {}
    head = "initial"
    private = False

    def github(args: list[str], payload: dict | None = None) -> bytes:
        nonlocal head
        if payload is None:
            assert f"?ref={head}" in args[0]
            name = args[0].split("/contents/")[1].split("?")[0]
            return remote[name]
        if "variables" not in payload:
            return json.dumps(
                {
                    "data": {
                        "repository": {
                            "isPrivate": private,
                            "defaultBranchRef": {"name": "main", "target": {"oid": head}},
                            "cache": {"oid": head} if remote else None,
                            "token": {"oid": head} if remote else None,
                        }
                    }
                }
            ).encode()
        mutation = payload["variables"]["input"]
        if mutation["expectedHeadOid"] != head or mutation["branch"].get("branchName") != "main":
            raise subprocess.CalledProcessError(1, "gh")
        remote.update(
            {
                f["path"]: base64.b64decode(f["contents"])
                for f in mutation["fileChanges"]["additions"]
            }
        )
        head += "-next"
        return json.dumps(
            {
                "data": {
                    "createCommitOnBranch": {
                        "commit": {
                            "oid": head,
                            "signature": {"isValid": True},
                        }
                    }
                }
            }
        ).encode()

    monkeypatch.setattr(fetch_zones, "_github", github)
    monkeypatch.setattr(fetch_zones.sys, "argv", ["fetch_zones.py", "--seed"])
    with pytest.raises(SystemExit, match="must be private"):
        fetch_zones.main()
    assert not remote
    private = True
    assert fetch_zones.main() == 0
    assert set(remote) == {"cache.tar.gz.gpg", "refresh-token.gpg"}
    assert all(original not in blob and token.read_bytes() not in blob for blob in remote.values())
    with pytest.raises(SystemExit, match="already seeded"):
        fetch_zones.main()

    restored = tmp_path / "restored"
    monkeypatch.setattr(config, "DATA", restored)
    monkeypatch.setattr(fetch_zones.sys, "argv", ["fetch_zones.py", "--restore"])
    monkeypatch.setenv("TRAINING_STATE_KEY", secrets.token_hex(32))
    with pytest.raises(subprocess.CalledProcessError):
        fetch_zones.main()
    assert not list(restored.iterdir())
    monkeypatch.setenv("TRAINING_STATE_KEY", key)
    assert fetch_zones.main() == 0
    assert (restored / "activities.csv").read_bytes() == original
    assert token.read_text() == "private-refresh-token"
    with pytest.raises(SystemExit, match="empty raw-cache"):
        fetch_zones.main()

    monkeypatch.setattr(fetch_zones.sys, "argv", ["fetch_zones.py", "--save"])
    assert fetch_zones.main() == 0
    previous = remote.copy()
    head += "-concurrent-write"
    (restored / "notes.csv").write_text("date,name,note\n2026-09-01,Run,local note\n")
    with pytest.raises(subprocess.CalledProcessError):
        fetch_zones.main()
    assert remote == previous


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
