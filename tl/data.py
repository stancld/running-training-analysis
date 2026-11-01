"""Loading and normalising the local cache into one queryable dataset."""
import csv
import datetime as dt
import math
from collections import defaultdict

from . import config as C


def _date(s):
    try:
        return dt.date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        return None


def _rows(name):
    """Yield dict rows, skipping stray repeated headers and blank lines."""
    try:
        fh = open(C.path(name))
    except FileNotFoundError:
        return
    with fh:
        for r in csv.DictReader(fh):
            if r.get('date') and _date(r['date']):
                yield r


class Activity:
    __slots__ = ('date', 'sport', 'group', 'km', 'mins', 'vert', 'type',
                 'feel', 're', 'hr', 'name', 'note')

    def __init__(self, date, sport, km, mins, vert):
        self.date, self.sport = date, sport
        self.group = C.group_of(sport)
        self.km, self.mins, self.vert = km, mins, vert
        self.type = self.feel = self.re = self.hr = None
        self.name = self.note = None

    @property
    def hours(self):
        return self.mins / 60

    @property
    def vert_per_km(self):
        return self.vert / self.km if self.km else 0.0

    @property
    def pace(self):
        """min/km."""
        return self.mins / self.km if self.km else None

    @property
    def is_run(self):
        return self.group == 'run'

    def est_hr(self):
        """Measured HR when COROS has it, else the relative-effort model."""
        if self.hr:
            return self.hr, True
        if self.re and self.mins:
            per_h = self.re / (self.mins / 60)
            if per_h > 0:
                return C.HR_A + C.HR_B * math.log(per_h), False
        return None, False

    def __repr__(self):
        return f'<{self.date} {self.sport} {self.km:.1f}km {self.mins:.0f}min>'


class Dataset:
    """Everything the local cache knows, indexed by date."""

    def __init__(self, activities, hills, segments, weather):
        self.activities = sorted(activities, key=lambda a: (a.date, a.sport))
        self.hills, self.segments, self.weather = hills, segments, weather
        self.by_date = defaultdict(list)
        for a in self.activities:
            self.by_date[a.date].append(a)
        self.first = self.activities[0].date
        self.last = self.activities[-1].date

    # -------------------------------------------------------------- loading
    @classmethod
    def load(cls):
        acts = []
        for r in _rows('activities.csv'):
            acts.append(Activity(_date(r['date']), r['sport'],
                                 float(r['km'] or 0), float(r['min'] or 0),
                                 float(r['vert'] or 0)))

        labels, re_, hr = {}, {}, {}
        for r in _rows('labels.csv'):
            labels[_date(r['date'])] = (
                r['type'] or None,
                float(r['feel']) if r.get('feel') else None)
        for r in _rows('re.csv'):
            re_[_date(r['date'])] = float(r['re'])
        for r in _rows('hr.csv'):
            hr[_date(r['date'])] = float(r['hr'])

        notes = defaultdict(list)
        for r in _rows('notes.csv'):
            notes[_date(r['date'])].append((r.get('name') or '', r.get('note') or ''))

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
            for a, (name, note) in zip(cls._runs_first(acts, d), items):
                a.name, a.note = name, note

        hills = list(_rows('hills.csv'))
        segs = list(_rows('segments.csv'))
        return cls(acts, hills, segs, _weather())

    @staticmethod
    def _runs_first(acts, d):
        same = [a for a in acts if a.date == d]
        return sorted(same, key=lambda a: (a.group != 'run', -a.mins))

    # ------------------------------------------------------------- querying
    def between(self, start, end, groups=None):
        return [a for a in self.activities
                if start <= a.date <= end and (groups is None or a.group in groups)]

    def runs(self, start=None, end=None):
        return self.between(start or self.first, end or self.last, {'run'})

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
        return dict(out), rate


def _weather():
    """Open-Meteo archive export for Prague; header row is found, not assumed."""
    try:
        lines = open(C.path('weather_raw.csv')).read().splitlines()
    except FileNotFoundError:
        return {}
    head = next((i for i, l in enumerate(lines) if l.startswith('time,')), None)
    if head is None:
        return {}
    out = {}
    for line in lines[head + 1:]:
        if not line.strip():
            continue
        p = line.split(',')
        d = _date(p[0])
        if not d:
            continue
        try:
            out[d] = dict(tmean=float(p[1]), tmax=float(p[2]), tapp=float(p[4]),
                          prcp=float(p[5]), rh=float(p[6]), wind=float(p[7]))
        except (ValueError, IndexError):
            continue
    return out
