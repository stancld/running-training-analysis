"""Loads the CSV cache into one Dataset."""

import csv
import datetime as dt
import itertools
import math
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence
from typing import Self

from tl import config


def _date(s: str | None) -> dt.date | None:
    try:
        return dt.date.fromisoformat(s.strip()) if s else None
    except ValueError:
        return None


def runs_first(acts: Iterable[Activity]) -> list[Activity]:
    """Runs before other sports, longest first."""
    return sorted(acts, key=lambda a: (a.group != config.SportGroup.RUN, -a.mins))


def _by_day[T](name: str, parse: Callable[[dict[str, str]], T]) -> dict[dt.date, list[T]]:
    out = defaultdict(list)
    for d, r in read_rows(name):
        out[d].append(parse(r))
    return out


def _pair[R](
    runs: Sequence[Activity], rows: list[R], cost: Callable[[Activity, R], float] | None = None
) -> Iterable[tuple[Activity, R]]:
    """Pair a day's runs with that day's rows from one CSV.

    With one row per run, rows pair in file order, or by the lowest total `cost`
    when given; otherwise the day's last row describes its longest run.
    """
    if len(rows) == len(runs):
        if cost:
            runs = min(
                itertools.permutations(runs),
                key=lambda p: sum(map(cost, p, rows, strict=True)),
            )
        return zip(runs, rows, strict=True)
    return [(max(runs, key=lambda a: a.mins), rows[-1])] if rows else []


def read_rows(name: str) -> Iterator[tuple[dt.date, dict[str, str]]]:
    """Yield (date, row) pairs, skipping stray repeated headers and blank lines."""
    try:
        fh = open(config.path(name))
    except FileNotFoundError:
        return
    with fh:
        for r in csv.DictReader(fh):
            d = _date(r.get("date"))
            if d:
                yield d, r


# (minutes, HR-zone seconds, power-zone seconds) from one stream-cache row.
type _ZoneRow = tuple[float, list[float] | None, list[float] | None]


def _attach_streams(acts: list[Activity]) -> None:
    """Attach zone seconds from the stream caches, matched to same-day activities by duration."""

    def by_dur(a: Activity, r: _ZoneRow) -> float:
        return abs(a.mins - r[0])

    files = (
        (config.SportGroup.RUN, "zones.csv", False),
        (config.SportGroup.BIKE, "ride_zones.csv", True),
    )
    for group, name, ride in files:
        rows: dict[dt.date, list[_ZoneRow]] = _by_day(
            name,
            lambda r, ride=ride: (
                float(r["min"]),
                [float(r[f"z{i}"]) for i in range(1, 6)] if r["z1"] else None,
                [float(r[f"p{i}"]) for i in range(1, 8)] if ride and r["p1"] else None,
            ),
        )
        days = defaultdict(list)
        for a in acts:
            if a.group == group:
                days[a.date].append(a)
        for d, day in days.items():
            for a, (_, z, p) in _pair(day, rows.get(d, []), by_dur):
                a.zones, a.power = z, p


class Activity:
    date: dt.date
    sport: str
    group: config.SportGroup
    km: float
    mins: float
    vert: float
    # Attached from the side CSVs by Dataset.load.
    type: str | None
    feel: float | None
    re: float | None
    hr: float | None
    name: str | None
    note: str | None
    # Seconds per HR zone from the HR stream (zones.csv for runs, ride_zones.csv for
    # rides) and per power zone from a ride's watts stream, when fetched.
    zones: list[float] | None
    power: list[float] | None

    def __init__(self, date: dt.date, sport: str, km: float, mins: float, vert: float) -> None:
        self.date, self.sport = date, sport
        self.group = config.group_of(sport)
        self.km, self.mins, self.vert = km, mins, vert
        self.type = self.feel = self.re = self.hr = self.zones = self.power = None
        self.name = self.note = None

    @property
    def vert_per_km(self) -> float:
        return self.vert / self.km if self.km else 0.0

    @property
    def pace(self) -> float | None:
        """min/km."""
        return self.mins / self.km if self.km else None

    @property
    def is_run(self) -> bool:
        return self.group == config.SportGroup.RUN

    def est_hr(self) -> float | None:
        """Measured HR when COROS has it, else the relative-effort model."""
        if self.hr:
            return self.hr
        if self.re and self.mins:
            per_h = self.re / (self.mins / 60)
            if per_h > 0:
                return config.HR_A + config.HR_B * math.log(per_h)
        return None


class Dataset:
    def __init__(self, activities: list[Activity]) -> None:
        self.activities = sorted(activities, key=lambda a: (a.date, a.sport))
        self.first = self.activities[0].date
        self.last = self.activities[-1].date

    @classmethod
    def load(cls) -> Self:
        acts = [
            Activity(
                d,
                r["sport"],
                float(r["km"] or 0),
                float(r["min"] or 0),
                float(r["vert"] or 0),
            )
            for d, r in read_rows("activities.csv")
        ]
        if not acts:
            # The cache is personal data kept out of git, so a fresh checkout has none.
            raise SystemExit(
                f"no activities in {config.path('activities.csv')}; top up the cache first"
            )

        labels = _by_day(
            "labels.csv",
            lambda r: (r["type"] or None, float(r["feel"]) if r.get("feel") else None),
        )
        re_ = _by_day("re.csv", lambda r: float(r["re"]))
        hr = _by_day("hr.csv", lambda r: (float(r["min"]), float(r["hr"])))
        notes = defaultdict(list)
        for d, r in read_rows("notes.csv"):
            notes[d].append((r.get("name") or "", r.get("note") or ""))

        runs = defaultdict(list)
        for a in acts:
            if a.is_run:
                runs[a.date].append(a)
        for d, day in runs.items():
            for a, (typ, feel) in _pair(day, labels.get(d, [])):
                a.type, a.feel = typ, feel
            for a, v in _pair(day, re_.get(d, [])):
                a.re = v
            # hr.csv carries minutes, so rows match runs by duration.
            for a, (_, v) in _pair(day, hr.get(d, []), lambda a, r: abs(a.mins - r[0])):
                a.hr = v
        _attach_streams(acts)

        for d, items in notes.items():
            same_day = runs_first(a for a in acts if a.date == d)
            for a, (name, note) in zip(same_day, items, strict=False):
                a.name, a.note = name, note

        return cls(acts)

    def daily_load(self) -> dict[dt.date, float]:
        """Load units per date: RE where Strava has it, else a scaled minute."""
        rates = sorted(a.re / a.mins for a in self.activities if a.is_run and a.re and a.mins > 5)
        rate = rates[len(rates) // 2] if rates else 0.35
        out = defaultdict(float)
        for a in self.activities:
            if a.is_run and a.re:
                out[a.date] += a.re
            else:
                out[a.date] += a.mins * rate * config.LOAD_RATIO[a.group]
        return dict(out)
