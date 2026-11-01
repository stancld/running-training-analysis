"""Loads the CSV cache into one Dataset."""

import csv
import datetime as dt
import itertools
import math
from collections import defaultdict

from tl import config


def _date(s):
    try:
        return dt.date.fromisoformat(s.strip())
    except ValueError, AttributeError:
        return None


def runs_first(acts):
    """Runs before other sports, longest first."""
    return sorted(acts, key=lambda a: (a.group != "run", -a.mins))


def _by_day(name, parse):
    out = defaultdict(list)
    for r in _rows(name):
        out[_date(r["date"])].append(parse(r))
    return out


def _pair(runs, rows, cost=None):
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


def _rows(name):
    """Yield dict rows, skipping stray repeated headers and blank lines."""
    try:
        fh = open(config.path(name))
    except FileNotFoundError:
        return
    with fh:
        for r in csv.DictReader(fh):
            if r.get("date") and _date(r["date"]):
                yield r


class Activity:
    __slots__ = (
        "date",
        "feel",
        "group",
        "hr",
        "km",
        "mins",
        "name",
        "note",
        "re",
        "sport",
        "type",
        "vert",
    )

    def __init__(self, date, sport, km, mins, vert):
        self.date, self.sport = date, sport
        self.group = config.group_of(sport)
        self.km, self.mins, self.vert = km, mins, vert
        self.type = self.feel = self.re = self.hr = None
        self.name = self.note = None

    @property
    def vert_per_km(self):
        return self.vert / self.km if self.km else 0.0

    @property
    def pace(self):
        """min/km."""
        return self.mins / self.km if self.km else None

    @property
    def is_run(self):
        return self.group == "run"

    def est_hr(self):
        """Measured HR when COROS has it, else the relative-effort model."""
        if self.hr:
            return self.hr
        if self.re and self.mins:
            per_h = self.re / (self.mins / 60)
            if per_h > 0:
                return config.HR_A + config.HR_B * math.log(per_h)
        return None

    def __repr__(self):
        return f"<{self.date} {self.sport} {self.km:.1f}km {self.mins:.0f}min>"


class Dataset:
    def __init__(self, activities, hills, segments):
        self.activities = sorted(activities, key=lambda a: (a.date, a.sport))
        self.hills, self.segments = hills, segments
        self.first = self.activities[0].date
        self.last = self.activities[-1].date

    @classmethod
    def load(cls):
        acts = [
            Activity(
                _date(r["date"]),
                r["sport"],
                float(r["km"] or 0),
                float(r["min"] or 0),
                float(r["vert"] or 0),
            )
            for r in _rows("activities.csv")
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
        for r in _rows("notes.csv"):
            notes[_date(r["date"])].append((r.get("name") or "", r.get("note") or ""))

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

        for d, items in notes.items():
            same_day = runs_first(a for a in acts if a.date == d)
            for a, (name, note) in zip(same_day, items, strict=False):
                a.name, a.note = name, note

        return cls(acts, list(_rows("hills.csv")), list(_rows("segments.csv")))

    def daily_load(self):
        """Load units per date: RE where Strava has it, else a scaled minute."""
        runs = [a for a in self.activities if a.is_run and a.re and a.mins > 5]
        rate = (sorted(a.re / a.mins for a in runs)[len(runs) // 2]) if runs else 0.35
        out = defaultdict(float)
        for a in self.activities:
            if a.is_run and a.re:
                out[a.date] += a.re
            else:
                out[a.date] += a.mins * rate * config.LOAD_RATIO[a.group]
        return dict(out)
