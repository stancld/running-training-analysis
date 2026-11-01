"""Weeks, months and seasons over the whole history, plus the fitness curve.

Every Monday between the first and last activity gets a Week, trained or not.
"""

import datetime as dt
import itertools
import math
from collections import defaultdict

from . import config as C


def week_start(d):
    return d - dt.timedelta(days=d.weekday())


def iso_label(d):
    y, w, _ = week_start(d).isocalendar()
    return f"{y}-W{w:02d}"


class Period:
    """Shared aggregation over a list of activities."""

    def __init__(self, start, end, acts):
        self.start, self.end, self.acts = start, end, acts
        for name, _ in C.GROUPS:
            sel = [a for a in acts if a.group == name]
            setattr(self, name + "_h", sum(a.mins for a in sel) / 60)
            setattr(self, name + "_km", sum(a.km for a in sel))
            setattr(self, name + "_vert", sum(a.vert for a in sel))
            setattr(self, name + "_n", len(sel))
        self.runs = [a for a in acts if a.is_run]
        self.total_h = sum(a.mins for a in acts) / 60

    @property
    def days(self):
        return (self.end - self.start).days + 1

    @property
    def density(self):
        """Metres of climb per running hour — the R3 discriminator."""
        return self.run_vert / self.run_h if self.run_h else 0.0

    @property
    def run_days(self):
        return len({a.date for a in self.runs})

    @property
    def rest_days(self):
        return self.days - len({a.date for a in self.acts if a.mins >= 20})

    @property
    def longest_run(self):
        return max(self.runs, key=lambda a: a.mins) if self.runs else None

    @property
    def quality(self):
        return [a for a in self.runs if a.type in C.QUALITY]

    @property
    def feels(self):
        return [a.feel for a in self.runs if a.feel is not None]

    @property
    def mean_feel(self):
        f = self.feels
        return sum(f) / len(f) if f else None

    @property
    def partial(self):
        return self.end > C.TODAY

    def hr_at_pace(self):
        """Mean easy/long HR and pace — the aerobic-drift read."""
        rows = []
        for a in self.runs:
            if a.type not in ("E", "L") or a.mins < 25 or not a.km:
                continue
            hr = a.est_hr()
            if hr:
                rows.append((hr, a.pace))
        if not rows:
            return None
        return {
            "hr": sum(r[0] for r in rows) / len(rows),
            "pace": sum(r[1] for r in rows) / len(rows),
        }


class Week(Period):
    def __init__(self, start, acts):
        super().__init__(start, start + dt.timedelta(days=6), acts)
        self.label = iso_label(start)
        self.prev = None  # wired up by build_weeks
        self.chronic = None  # mean running hours of the 4 weeks ending here

    @property
    def current(self):
        return self.start <= C.TODAY <= self.end

    @property
    def wow(self):
        if self.prev is None or not self.prev.run_h:
            return None
        return self.run_h / self.prev.run_h

    @property
    def acwr(self):
        if not self.chronic:
            return None
        return self.run_h / self.chronic

    @property
    def back_to_back(self):
        """Consecutive days each carrying >=90 min of running — the Chianti stimulus."""
        long_days = sorted(
            {a.date for a in self.runs if sum(x.mins for x in self.runs if x.date == a.date) >= 90}
        )
        return any((b - a).days == 1 for a, b in itertools.pairwise(long_days))

    def flags(self):
        """Guardrail violations, in the language of the plan's R1-R7."""
        out = []
        if self.partial:
            return out
        if self.wow and self.wow > C.WOW_CAP and self.run_h > 3:
            out.append(("R1", f"week-over-week {self.wow:.2f}x > {C.WOW_CAP}"))
        if self.acwr and self.acwr > C.ACWR_CAP and self.run_h > 3:
            out.append(("R2", f"ACWR {self.acwr:.2f} > {C.ACWR_CAP}"))
        if self.run_h > C.BIG_WEEK_H and self.density < C.VERT_FLOOR:
            out.append(("R3", f"{self.density:.0f} m/h on a {self.run_h:.1f} h week — flat volume"))
        # R4 bans I/R, but the ban exists to keep hard running off flat ground.
        # An uphill rep session carries the intent, so only flat ones are flagged.
        flat_hard = [a for a in self.runs if a.type in C.BANNED_TYPES and a.vert_per_km < 20]
        if flat_hard:
            kinds = sorted({a.type for a in flat_hard})
            out.append(("R4", f"flat {'/'.join(kinds)} session this season"))
        if self.run_km > C.KM_CEILING:
            out.append(("R6", f"{self.run_km:.0f} km > {C.KM_CEILING:.0f} km ceiling"))
        if self.start.month in C.RISK_MONTHS and self.run_h > C.BIG_WEEK_H:
            out.append(("--", "big week inside the Dec-Apr injury window"))
        return out


class Month(Period):
    def __init__(self, year, month, acts):
        last = dt.date(year + month // 12, month % 12 + 1, 1) - dt.timedelta(days=1)
        super().__init__(dt.date(year, month, 1), last, acts)
        self.label = f"{year}-{month:02d}"


class Season(Period):
    def __init__(self, year, acts):
        super().__init__(dt.date(year, 1, 1), dt.date(year, 12, 31), acts)
        self.label = str(year)


def build_weeks(ds):
    start, end = week_start(ds.first), week_start(ds.last)
    by_week = defaultdict(list)
    for a in ds.activities:
        by_week[week_start(a.date)].append(a)
    weeks, w = [], start
    while w <= end:
        weeks.append(Week(w, by_week.get(w, [])))
        w += dt.timedelta(days=7)
    for i, wk in enumerate(weeks):
        wk.prev = weeks[i - 1] if i else None
        window = weeks[max(0, i - 3) : i + 1]
        wk.chronic = sum(x.run_h for x in window) / len(window)
    return weeks


def build_months(ds):
    by_month = defaultdict(list)
    for a in ds.activities:
        by_month[(a.date.year, a.date.month)].append(a)
    return [Month(y, m, by_month[(y, m)]) for y, m in sorted(by_month)]


def build_seasons(ds):
    by_year = defaultdict(list)
    for a in ds.activities:
        by_year[a.date.year].append(a)
    return [Season(y, by_year[y]) for y in sorted(by_year)]


def fitness_curve(ds, load):
    """Exponential CTL/ATL/TSB over daily load units.

    CTL tau=42 d (fitness), ATL tau=7 d (fatigue), TSB = CTL - ATL (form).
    Absolute numbers depend on the load model in config.LOAD_RATIO; the shape
    is what carries information.
    """
    ctl = atl = 0.0
    kc, ka = 1 - math.exp(-1 / C.CTL_TAU), 1 - math.exp(-1 / C.ATL_TAU)
    out, d = {}, ds.first
    while d <= max(ds.last, C.TODAY):
        v = load.get(d, 0.0)
        ctl += (v - ctl) * kc
        atl += (v - atl) * ka
        out[d] = {"ctl": ctl, "atl": atl, "tsb": ctl - atl}
        d += dt.timedelta(days=1)
    return out


def monotony(load, week):
    """Foster monotony: mean daily load over its standard deviation."""
    vals = [load.get(week.start + dt.timedelta(days=i), 0.0) for i in range(7)]
    mean = sum(vals) / 7
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / 7)
    return mean / sd if sd > 0.01 else None
