"""Append HR- and power-zone seconds for plan-period runs and rides the cache lacks.

Reads each activity's Strava streams once and keeps only the time per zone: runs in
zones.csv (config.HR_ZONES), rides in ride_zones.csv (Garmin HR and power zones), so
the cache stays small. Needs STRAVA_CLIENT_ID,
STRAVA_CLIENT_SECRET and STRAVA_REFRESH_TOKEN; Strava may rotate the refresh
token, so the newest one is kept in ~/.config/tl/strava_refresh_token (mode 600).
"""

import base64
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from tl import config, data, plan

API = "https://www.strava.com/api/v3"
TOKEN_FILE = Path.home() / ".config" / "tl" / "strava_refresh_token"
STATE_HEAD = TOKEN_FILE.with_name("state_head.json")
STATE_REPO = "stancld/training-data-state"
RUNS = {"Run", "TrailRun"}


def _github(args: list[str], payload: dict | None = None) -> bytes:
    return subprocess.run(  # noqa: S603 - fixed gh executable, no shell
        ["gh", "api", *args],  # noqa: S607
        input=json.dumps(payload).encode() if payload else None,
        check=True,
        capture_output=True,
    ).stdout


def _state_repository() -> dict[str, Any]:
    result = json.loads(
        _github(
            ["graphql", "--input", "-"],
            {
                "query": """query {
                  repository(owner: "stancld", name: "training-data-state") {
                    isPrivate defaultBranchRef { name target { oid } }
                    cache: object(expression: "HEAD:cache.tar.gz.gpg") { oid }
                    token: object(expression: "HEAD:refresh-token.gpg") { oid }
                  }
                }""",
            },
        )
    )["data"]["repository"]
    if not result or not result["isPrivate"] or not result["defaultBranchRef"]:
        raise SystemExit("state repository must be private and initialized with a README")
    return result


def _crypt(source: Path, target: Path, *, decrypt: bool = False) -> None:
    # With --no-options, decrypt-first on a fresh runner does not create this directory.
    gnupg_home = Path(os.environ.get("GNUPGHOME", Path.home() / ".gnupg"))
    gnupg_home.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Pass the key through stdin, never command arguments or a tracked key file.
    result = subprocess.run(  # noqa: S603 - fixed gpg executable, no shell
        [  # noqa: S607 - GnuPG is provided by the runner
            "gpg",
            "--no-options",
            "--batch",
            "--yes",
            "--no-tty",
            "--status-fd",
            "2",
            "--force-mdc",
            "--pinentry-mode",
            "loopback",
            "--no-symkey-cache",
            "--passphrase-fd",
            "0",
            "--cipher-algo",
            "AES256",
            "--s2k-digest-algo",
            "SHA256",
            "--s2k-count",
            "65011712",
            "--compress-algo",
            "none",
            "--output",
            str(target),
            "--decrypt" if decrypt else "--symmetric",
            str(source),
        ],
        input=os.environ["TRAINING_STATE_KEY"].encode(),
        check=False,
        capture_output=True,
    )
    if result.returncode:
        # GPG's prose can contain filenames/plaintext metadata. Report only fixed
        # status names and numeric error codes, never the captured output itself.
        statuses = []
        for line in result.stderr.decode(errors="replace").splitlines():
            fields = line.split()
            if (
                len(fields) >= 2
                and fields[0] == "[GNUPG:]"
                and fields[1]
                in {
                    "BADMDC",
                    "DECRYPTION_FAILED",
                    "BAD_PASSPHRASE",
                    "MISSING_PASSPHRASE",
                    "NODATA",
                    "FAILURE",
                    "ERROR",
                    "DECRYPTION_OKAY",
                    "GOODMDC",
                }
            ):
                code = (
                    f" {fields[-1]}"
                    if fields[1] in {"FAILURE", "ERROR"} and fields[-1].isdigit()
                    else ""
                )
                statuses.append(fields[1] + code)
        error = subprocess.CalledProcessError(result.returncode, result.args)
        error.add_note(f"GPG status: {', '.join(statuses) or 'no recognized status'}")
        raise error


def _checkpoint(files: dict[str, Path]) -> None:
    head = json.loads(STATE_HEAD.read_text())
    with tempfile.TemporaryDirectory() as directory:
        additions = []
        for name, source in files.items():
            encrypted = Path(directory) / name
            _crypt(source, encrypted)
            additions.append(
                {"path": name, "contents": base64.b64encode(encrypted.read_bytes()).decode()}
            )
        result = json.loads(
            _github(
                ["graphql", "--input", "-"],
                {
                    "query": """mutation($input: CreateCommitOnBranchInput!) {
                      createCommitOnBranch(input: $input) {
                        commit { oid signature { isValid } }
                      }
                    }""",
                    "variables": {
                        "input": {
                            "branch": {
                                "repositoryNameWithOwner": STATE_REPO,
                                "branchName": head["name"],
                            },
                            "expectedHeadOid": head["target"]["oid"],
                            "message": {"headline": "Update encrypted training checkpoint"},
                            "fileChanges": {"additions": additions},
                        }
                    },
                },
            )
        )["data"]["createCommitOnBranch"]["commit"]
    if not result["signature"] or not result["signature"]["isValid"]:
        raise SystemExit(
            "GitHub did not verify the checkpoint commit signature; inspect remote state"
        )
    head["target"]["oid"] = result["oid"]
    STATE_HEAD.write_text(json.dumps(head))


def _save(*, seed: bool = False) -> None:
    if not any(data.read_rows("activities.csv")) or not TOKEN_FILE.exists():
        raise SystemExit("private raw cache and refresh-token file are required")
    if seed:
        repository = _state_repository()
        if repository["cache"] or repository["token"]:
            raise SystemExit("state is already seeded; restore it instead of overwriting it")
        STATE_HEAD.parent.mkdir(parents=True, exist_ok=True)
        STATE_HEAD.write_text(json.dumps(repository["defaultBranchRef"]))
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / "cache.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for path in [*sorted(config.DATA.glob("*.csv")), config.path("strava_sync.json")]:
                if path.exists():
                    if not path.is_file() or path.is_symlink():
                        raise SystemExit("cache must contain regular files, not links")
                    tar.add(path, arcname=path.name)
        files = {"cache.tar.gz.gpg": archive}
        if seed:
            files["refresh-token.gpg"] = TOKEN_FILE
        _checkpoint(files)


def _restore() -> None:
    if list(config.DATA.glob("*.csv")) or config.path("strava_sync.json").exists():
        raise SystemExit("restore requires an empty raw-cache directory")
    repository = _state_repository()
    head = repository["defaultBranchRef"]
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.DATA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        for name in ("cache.tar.gz", "refresh-token"):
            encrypted, plain = Path(directory) / f"{name}.gpg", Path(directory) / name
            encrypted.write_bytes(
                _github(
                    [
                        f"repos/{STATE_REPO}/contents/{name}.gpg?ref={head['target']['oid']}",
                        "-H",
                        "Accept: application/vnd.github.raw",
                    ]
                )
            )
            _crypt(encrypted, plain, decrypt=True)
        with tarfile.open(Path(directory) / "cache.tar.gz") as tar:
            for member in tar.getmembers():
                if (
                    not member.isfile()
                    or Path(member.name).name != member.name
                    or not (member.name.endswith(".csv") or member.name == "strava_sync.json")
                ):
                    raise SystemExit("unexpected file in private cache archive")
            tar.extractall(config.DATA, filter="data")
        TOKEN_FILE.touch(mode=0o600)
        TOKEN_FILE.chmod(0o600)
        TOKEN_FILE.write_bytes((Path(directory) / "refresh-token").read_bytes())
    STATE_HEAD.write_text(json.dumps(head))


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
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.touch(mode=0o600)
    TOKEN_FILE.chmod(0o600)
    TOKEN_FILE.write_text(tok["refresh_token"])
    # A failed ingestion must not strand the next runner with a rotated-out token.
    if os.environ.get("TRAINING_STATE_KEY"):
        _checkpoint({"refresh-token.gpg": TOKEN_FILE})
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


def _have(kind: str) -> set[tuple[str, int]]:
    return {(d.isoformat(), round(float(r["min"]))) for d, r in data.read_rows(kind)}


def _activities(token: str, after: int, before: int) -> list[dict[str, Any]]:
    acts, page = [], 1
    while batch := _call(
        f"{API}/athlete/activities?after={after}&before={before}&per_page=100&page={page}", token
    ):
        acts += batch
        page += 1
    return sorted(
        {a["id"]: a for a in acts}.values(), key=lambda a: (a["start_date_local"], a["id"])
    )


def _zones(token: str, acts: list[dict[str, Any]]) -> None:
    for kind, sports, keys, header in KINDS:
        path = config.path(kind)
        have = _have(kind)
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


def _append(name: str, header: list[str], rows: list[list]) -> None:
    path = config.path(name)
    new = not path.exists()
    with path.open("a", newline="") as fh:
        writer = csv.writer(fh)
        if new:
            writer.writerow(header)
        writer.writerows(rows)


def _refresh() -> None:
    """Append uploaded activities, including today; IDs make overlap queries idempotent.

    The seed cache must be complete through its last day. We never infer missing
    historical sessions or overwrite manual COROS values, labels or notes.
    """
    state_path = config.path("strava_sync.json")
    days = [day for day, _ in data.read_rows("activities.csv")]
    if not days:
        raise SystemExit("refresh requires an authoritative activities.csv seed")
    if os.environ.get("TRAINING_STATE_KEY") and not STATE_HEAD.exists():
        raise SystemExit("restore the private checkpoint before refreshing")
    today = dt.datetime.now(ZoneInfo("Europe/Prague")).date()
    state: dict[str, Any] = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else {"since": (max(days) + dt.timedelta(days=1)).isoformat(), "ids": [], "until": None}
    )
    since = dt.date.fromisoformat(state["since"])
    if since > today:
        raise SystemExit("seed cache extends beyond the last completed Prague day")
    start = max(
        since,
        dt.date.fromisoformat(state["until"]) - dt.timedelta(days=7) if state["until"] else since,
    )
    # UTC bounds cover local dates even when an activity was recorded while travelling.
    after = int(dt.datetime.combine(start - dt.timedelta(days=1), dt.time(), dt.UTC).timestamp())
    before = int(dt.datetime.combine(today + dt.timedelta(days=1), dt.time(), dt.UTC).timestamp())
    token = _access_token()
    acts = [
        a
        for a in _activities(token, after, before)
        if start.isoformat() <= a["start_date_local"][:10] <= today.isoformat()
    ]
    have = set(state["ids"])
    fresh = [a for a in acts if a["id"] not in have]
    rows, hr = [], []
    for a in fresh:
        day = a["start_date_local"][:10]
        sport = a["sport_type"]
        if sport in RUNS and a.get("workout_type") == 1:
            sport = "RACE_Run"
        rows.append(
            [day, sport, a["distance"] / 1000, a["moving_time"] / 60, a["total_elevation_gain"]]
        )
        if a["sport_type"] in RUNS and a.get("average_heartrate"):
            hr.append([day, a["moving_time"] / 60, a["average_heartrate"]])
    # Fetch all streams before appending activities; CI persists the directory only on success.
    _zones(token, [a for a in acts if a["start_date_local"][:10] >= plan.PLAN_START.isoformat()])
    _append("activities.csv", ["date", "sport", "km", "min", "vert"], rows)
    _append("hr.csv", ["date", "min", "hr"], hr)
    state["ids"] = sorted(have | {a["id"] for a in fresh})
    state["until"] = today.isoformat()
    state_path.write_text(json.dumps(state))
    print(f"activities.csv: appended {len(fresh)} activities; including today")


def main() -> int:
    if (
        sys.argv[1:] in (["--restore"], ["--save"], ["--seed"])
        or "TRAINING_STATE_KEY" in os.environ
    ):
        key = os.environ.get("TRAINING_STATE_KEY", "")
        if len(key) < 32 or "\n" in key or "\r" in key:
            raise SystemExit(
                "TRAINING_STATE_KEY must be a random single-line key of at least 32 characters"
            )
    if sys.argv[1:] == ["--refresh"]:
        _refresh()
    elif sys.argv[1:] == ["--restore"]:
        _restore()
    elif sys.argv[1:] == ["--save"]:
        _save()
    elif sys.argv[1:] == ["--seed"]:
        _save(seed=True)
    elif sys.argv[1:]:
        raise SystemExit("usage: fetch_zones.py [--refresh|--restore|--save|--seed]")
    else:
        token = _access_token()
        after = int(dt.datetime.combine(plan.PLAN_START, dt.time(), tzinfo=dt.UTC).timestamp())
        _zones(token, _activities(token, after, int(dt.datetime.now(dt.UTC).timestamp())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
