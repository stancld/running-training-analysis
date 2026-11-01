"""Append HR- and power-zone seconds for plan-period runs and rides the cache lacks.

Reads each activity's Strava streams once and keeps only the time per zone: runs in
zones.csv (config.HR_ZONES), rides in ride_zones.csv (Garmin HR and power zones), so
the cache stays small. Needs STRAVA_CLIENT_ID,
STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN; Strava may rotate the refresh
token, so the newest one is kept in ~/.config/tl/strava_refresh_token (mode 600).
"""

import csv
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from tl import config, plan

API = "https://www.strava.com/api/v3"
TOKEN_FILE = Path.home() / ".config" / "tl" / "strava_refresh_token"
RUNS = {"Run", "TrailRun"}


def _call(url: str, token: str | None = None, data: dict[str, str] | None = None) -> Any:  # noqa: ANN401
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body)  # noqa: S310 - fixed https Strava URLs
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return json.load(resp)


def _access_token() -> str:
    refresh = (
        TOKEN_FILE.read_text().strip()
        if TOKEN_FILE.exists()
        else os.environ["STRAVA_REFRESH_TOKEN"]
    )
    tok = _call(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": os.environ["STRAVA_CLIENT_ID"],
            "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
            "grant_type": "refresh_token",
            "refresh_token": refresh,
        },
    )
    if tok["refresh_token"] != refresh:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.touch(mode=0o600)
        TOKEN_FILE.write_text(tok["refresh_token"])
    return tok["access_token"]


def _seconds(streams: dict[str, Any], key: str, zones: tuple) -> list[int] | None:
    """Seconds per zone over moving samples; paused gaps are not training time."""
    if key not in streams:
        return None
    t, v = streams["time"]["data"], streams[key]["data"]
    moving = streams.get("moving", {}).get("data") or [True] * len(t)
    out = [0.0] * len(zones)
    for i in range(1, len(t)):
        if moving[i] and v[i] is not None:
            out[config.zone_index(v[i], zones)] += t[i] - t[i - 1]
    return [round(s) for s in out] if any(out) else None


# cache file, Strava sport types, stream keys, header, how a stream becomes zone columns
KINDS = (
    ("zones.csv", RUNS, "time,heartrate,moving", [f"z{i}" for i in range(1, 6)]),
    (
        "ride_zones.csv",
        config.BIKE,
        "time,heartrate,watts,moving",
        [f"z{i}" for i in range(1, 6)] + [f"p{i}" for i in range(1, 8)],
    ),
)


def _row(kind: str, streams: dict[str, Any]) -> list[int | str] | None:
    if kind == "zones.csv":
        hr = _seconds(streams, "heartrate", config.HR_ZONES)
        return list(hr) if hr else None
    hr = _seconds(streams, "heartrate", config.BIKE_HR_ZONES)
    watts = _seconds(streams, "watts", config.POWER_ZONES)
    if not hr and not watts:
        return None
    return [*(hr or [""] * 5), *(watts or [""] * 7)]


def _have(path: Path) -> set[tuple[str, int]]:
    if not path.exists():
        return set()
    with path.open() as fh:
        return {
            (r["date"], round(float(r["min"]))) for r in csv.DictReader(fh) if r["date"] != "date"
        }


def main() -> int:
    token = _access_token()
    after = int(dt.datetime.combine(plan.PLAN_START, dt.time(), tzinfo=dt.UTC).timestamp())
    acts, page = [], 1
    while batch := _call(f"{API}/athlete/activities?after={after}&per_page=100&page={page}", token):
        acts += batch
        page += 1

    for kind, sports, keys, header in KINDS:
        path = config.path(kind)
        have = _have(path)
        todo = [
            a
            for a in acts
            if a["sport_type"] in sports and (a.get("has_heartrate") or a.get("device_watts"))
        ]
        rows = []
        for a in sorted(todo, key=lambda a: a["start_date_local"]):
            key = (a["start_date_local"][:10], round(a["moving_time"] / 60))
            if key in have:
                continue
            streams = _call(
                f"{API}/activities/{a['id']}/streams?keys={keys}&key_by_type=true", token
            )
            if row := _row(kind, streams):
                rows.append([*key, *row])
        new = not path.exists()
        with path.open("a", newline="") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["date", "min", *header])
            w.writerows(rows)
        sys.stdout.write(f"{kind}: appended {len(rows)} of {len(todo)} activities\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
