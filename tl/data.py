"""Loads the CSV cache into one Dataset."""

import csv
import datetime as dt
import math
from collections import defaultdict

from . import config as C


def _date(s):
    try:
        return dt.date.fromisoformat(s.strip())
    except ValueError, AttributeError:
        return None


def runs_first(acts):
    """Runs before other sports, longest first."""
    return sorted(acts, key=lambda a: (a.group != "run", -a.mins))


def _rows(name):
    """Yield dict rows, skipping stray repeated headers and blank lines."""
    try:
        fh = open(C.path(name))
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
        self.group = C.group_of(sport)
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
                return C.HR_A + C.HR_B * math.log(per_h)
        return None

    def __repr__(self):
        return f"<{self.date} {self.sport} {self.km:.1f}km {self.mins:.0f}min>"


class Dataset:
    def __init__(self, activities, hills, segments, reps):
        self.activities = sorted(activities, key=lambda a: (a.date, a.sport))
        self.hills, self.segments, self.reps = hills, segments, reps
        self.first = self.activities[0].date
        self.last = self.activities[-1].date

    @classmethod
    def load(cls):
        acts = []
        for r in _rows("activities.csv"):
            acts.append(
                Activity(
                    _date(r["date"]),
                    r["sport"],
                    float(r["km"] or 0),
                    float(r["min"] or 0),
                    float(r["vert"] or 0),
                )
            )

        labels, re_, hr = {}, {}, {}
        for r in _rows("labels.csv"):
            labels[_date(r["date"])] = (
                r["type"] or None,
                float(r["feel"]) if r.get("feel") else None,
            )
        for r in _rows("re.csv"):
            re_[_date(r["date"])] = float(r["re"])
        for r in _rows("hr.csv"):
            hr[_date(r["date"])] = float(r["hr"])

        notes = defaultdict(list)
        for r in _rows("notes.csv"):
            notes[_date(r["date"])].append((r.get("name") or "", r.get("note") or ""))

        # Labels/RE/HR are one-per-day and describe the day's *main* run, so
        # attach them to the longest run of that day and nothing else.
        main = {}
        for a in acts:
            if a.is_run:
                cur = main.get(a.date)
                if cur is None or a.mins > cur.mins:
                    main[a.date] = a
        for d, a in main.items():
            a.type, a.feel = labels.get(d, (None, None))
            a.re, a.hr = re_.get(d), hr.get(d)

        for d, items in notes.items():
            same_day = runs_first(a for a in acts if a.date == d)
            for a, (name, note) in zip(same_day, items, strict=False):
                a.name, a.note = name, note

        return cls(
            acts, list(_rows("hills.csv")), list(_rows("segments.csv")), list(_rows("reps.csv"))
        )

    def daily_load(self):
        """date -> load units. RE where Strava has it, else a scaled minute."""
        runs = [a for a in self.activities if a.is_run and a.re and a.mins > 5]
        rate = (sorted(a.re / a.mins for a in runs)[len(runs) // 2]) if runs else 0.35
        out = defaultdict(float)
        for a in self.activities:
            if a.is_run and a.re:
                out[a.date] += a.re
            else:
                out[a.date] += a.mins * rate * C.LOAD_RATIO[a.group]
        return dict(out)
