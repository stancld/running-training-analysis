"""The Chianti 120K macrocycle as data, so actual weeks can be scored against it.

Source: the plan artifact of 28 Aug 2026. Weekly targets are hours by discipline;
vert targets are derived from each phase's published total divided across that
phase's running hours, so they stay consistent with the plan rather than being
invented per week.
"""

import datetime as dt

from tl import config

# Weeks written week by week; beyond that a phase carries a band, not a number.
HORIZON_WEEKS = 8

RACE = dt.date(2027, 3, 20)
RACE_NAME = "Chianti 120K"
PLAN_START = dt.date(2026, 8, 31)
# The diary leads in one week early: week 1 only reads against the week before it.
DIARY_START = PLAN_START - dt.timedelta(days=7)

# (monday, total_h, run_h, bike_h, gym_h, weekend format, race)
_W = [
    ("2026-08-31", 11, 7.5, 3.5, 0, "Long 3:00", None),
    ("2026-09-07", 12, 8.0, 4.0, 0, "A · 3:00+2:30", None),
    ("2026-09-14", 11, 7.5, 3.5, 0, "Long 3:00", None),
    ("2026-09-21", 12, 8.5, 3.5, 0, "Long 3:30", None),
    ("2026-09-28", 12, 8.5, 3.5, 0, "A · 3:30+2:00", None),
    ("2026-10-05", 10, 7.0, 3.0, 0, "Long 2:30", None),
    ("2026-10-12", 7, 5.5, 1.5, 0, "Easy 90'", None),
    ("2026-10-19", 7, 4.5, 2.5, 0, "Race", "Slapy Trailmaniacs 47K · 24 Oct"),
    ("2026-10-26", 9, 5.5, 2.5, 1.0, "Long 2:00", None),
    ("2026-11-02", 11, 6.5, 2.5, 2.0, "Long 2:30", None),
    ("2026-11-09", 11, 7.0, 2.0, 2.0, "A · 2:30+2:00", None),
    ("2026-11-16", 12, 7.5, 2.5, 2.0, "A · 3:00+2:15", None),
    ("2026-11-23", 11, 7.0, 2.0, 2.0, "Long 2:45", None),
    ("2026-11-30", 12, 7.5, 2.5, 2.0, "A · 3:00+2:15", None),
    ("2026-12-07", 12, 8.0, 2.0, 2.0, "A · 3:00+2:30", None),
    ("2026-12-14", 13, 8.5, 2.5, 2.0, "A · 3:00+2:30", None),
    ("2026-12-21", 11, 7.5, 2.0, 1.5, "Long 3:00", None),
    ("2026-12-28", 13, 8.5, 2.5, 2.0, "B · two-phase", None),
    ("2027-01-04", 13, 9.0, 2.0, 2.0, "A · 3:00+2:30", None),
    ("2027-01-11", 13, 9.0, 2.5, 1.5, "A · 3:15+2:30", None),
    ("2027-01-18", 11, 8.0, 2.0, 1.0, "Long 3:00", None),
    ("2027-01-25", 12, 8.5, 2.5, 1.0, "A · 3:15+2:30", None),
    ("2027-02-01", 13, 9.0, 2.5, 1.5, "C · race-specific", None),
    ("2027-02-08", 12, 8.0, 2.5, 1.5, "Long 3:00", None),
    ("2027-02-15", 13, 9.0, 2.5, 1.5, "A · 3:30+2:30", None),
    ("2027-02-22", 13, 9.5, 2.5, 1.0, "C · 3:30+2:35", None),
    ("2027-03-01", 11, 8.0, 2.0, 1.0, "A · 3:00+2:00", None),
    ("2027-03-08", 8, 5.5, 2.0, 0.5, "Long 2:00", None),
    ("2027-03-15", 4, 3.0, 1.0, 0, "Race", "Chianti 120K · 20 Mar"),
]

# name, weeks, published km total, published vert total
PHASES = [
    ("P1", "Slapy build", 7, 569, 21000),
    ("P2", "Recovery & gym on-ramp", 6, 427, 12500),
    ("P3", "Base — the Kilian block", 8, 703, 28400),
    ("P4", "Specific build", 6, 544, 23900),
    ("P5", "Taper", 2, 97, 2550),
]


class PlanWeek:
    def __init__(self, i, row, phase):
        (d, h, r, b, g, we, race) = row
        self.index = i + 1
        self.start = dt.date.fromisoformat(d)
        self.end = self.start + dt.timedelta(days=6)
        self.total_h, self.run_h, self.bike_h, self.gym_h = h, r, b, g
        self.weekend, self.race = we, race
        self.phase = phase
        self.run_km = self.run_vert = None  # filled by _build

    @property
    def to_race(self):
        return (RACE - self.start).days // 7

    @property
    def committed(self):
        """Inside the detail horizon — a real weekly target, not a placeholder."""
        return self.start <= horizon_date()

    def __repr__(self):
        return f"<plan wk{self.index} {self.start} {self.run_h}h run>"


def _build():
    weeks, i = [], 0
    for code, _name, n, km, vert in PHASES:
        rows = _W[i : i + n]
        block = [PlanWeek(i + j, r, code) for j, r in enumerate(rows)]
        run_h = sum(w.run_h for w in block)
        for w in block:
            share = w.run_h / run_h
            w.run_km = km * share
            w.run_vert = vert * share
        weeks += block
        i += n
    return weeks


WEEKS = _build()
PHASE_NAME = {c: n for c, n, *_ in PHASES}
PHASE_WEEKS = {c: [w for w in WEEKS if w.phase == c] for c, *_ in PHASES}


def _bands():
    """Each phase's range, read off its own weeks.

    A band the plan already implies rather than a new set of invented numbers.
    """
    out = {}
    for code, block in PHASE_WEEKS.items():
        out[code] = {
            f: (min(getattr(w, f) for w in block), max(getattr(w, f) for w in block))
            for f in ("run_h", "bike_h", "gym_h", "total_h", "run_km", "run_vert")
        }
    return out


PHASE_BANDS = _bands()


def horizon_date():
    """Last Monday still written week by week."""
    return config.TODAY + dt.timedelta(weeks=HORIZON_WEEKS)


def committed_weeks():
    return [w for w in WEEKS if w.start <= horizon_date()]


def provisional_phases():
    """Phases with any week beyond the horizon, with their bands."""
    h = horizon_date()
    out = []
    for code, name, _n, km, vert in PHASES:
        block = [w for w in PHASE_WEEKS[code] if w.start > h]
        if block:
            out.append(
                {
                    "phase": code,
                    "name": name,
                    "weeks": len(block),
                    "start": block[0].start,
                    "end": block[-1].end,
                    "bands": PHASE_BANDS[code],
                    "km": km,
                    "vert": vert,
                }
            )
    return out


def week_for(d):
    """The plan week containing date d, or None if outside the macrocycle."""
    for w in WEEKS:
        if w.start <= d <= w.end:
            return w
    return None


def compare(actual, planned):
    """(actual, planned, actual/planned) per discipline, or None outside the plan."""
    if planned is None:
        return None
    out = {}
    for f in ("run_h", "bike_h", "gym_h"):
        a, p = getattr(actual, f), getattr(planned, f)
        out[f] = (a, p, a / p if p else None)
    return out


def weeks_to_race():
    return (RACE - config.TODAY).days / 7
