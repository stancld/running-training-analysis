"""Append HR-zone seconds for plan-period runs that data/zones.csv lacks.

Reads each run's Strava HR stream once and keeps only the time per zone (Dan's
config.HR_ZONES), so the cache stays small. Needs STRAVA_CLIENT_ID,
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
    refresh = TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else os.environ["STRAVA_REFRESH_TOKEN"]
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


def _zone_seconds(streams: dict[str, Any]) -> list[float]:
    """Seconds per zone over moving samples; paused gaps are not training time."""
    t, hr = streams["time"]["data"], streams["heartrate"]["data"]
    moving = streams.get("moving", {}).get("data") or [True] * len(t)
    out = [0.0] * len(config.HR_ZONES)
    for i in range(1, len(t)):
        if moving[i]:
            zone = next(
                z for z, (*_, top) in enumerate(config.HR_ZONES) if top is None or hr[i] <= top
            )
            out[zone] += t[i] - t[i - 1]
    return out


def main() -> int:
    path = config.path("zones.csv")
    have: set[tuple[str, int]] = set()
    if path.exists():
        with path.open() as fh:
            have = {(r["date"], round(float(r["min"]))) for r in csv.DictReader(fh) if r["date"] != "date"}
    token = _access_token()

    after = int(dt.datetime.combine(plan.PLAN_START, dt.time(), tzinfo=dt.UTC).timestamp())
    runs, page = [], 1
    while batch := _call(f"{API}/athlete/activities?after={after}&per_page=100&page={page}", token):
        runs += [a for a in batch if a["sport_type"] in RUNS and a.get("has_heartrate")]
        page += 1

    rows = []
    for a in sorted(runs, key=lambda a: a["start_date_local"]):
        key = (a["start_date_local"][:10], round(a["moving_time"] / 60))
        if key in have:
            continue
        streams = _call(
            f"{API}/activities/{a['id']}/streams?keys=time,heartrate,moving&key_by_type=true", token
        )
        if "heartrate" in streams:
            rows.append([*key, *(round(s) for s in _zone_seconds(streams))])

    new = not path.exists()
    with path.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["date", "min", "z1", "z2", "z3", "z4", "z5"])
        w.writerows(rows)
    sys.stdout.write(f"appended {len(rows)} runs to {path} ({len(runs) - len(rows)} already there)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
