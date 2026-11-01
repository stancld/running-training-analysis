"""The Chianti 120K macrocycle as data, so actual weeks can be scored against it.

Source: the plan artifact of 28 Aug 2026. Weekly targets are hours by discipline;
vert targets are derived from each phase's published total divided across that
phase's running hours, so they stay consistent with the plan rather than being
invented per week. Dan's later changes, with the reasons, are in LOG.md.
"""

import datetime as dt
from typing import Any

from tl import config

# Weeks written week by week; beyond that a phase carries a band, not a number.
HORIZON_WEEKS = 8

RACE = dt.date(2027, 3, 20)
RACE_NAME = "Chianti 120K"
PLAN_START = dt.date(2026, 8, 31)
# The diary leads in one week early: week 1 only reads against the week before it.
DIARY_START = PLAN_START - dt.timedelta(days=7)

# (monday, total_h, run_h, bike_h, gym_h, weekend format, race)
type _Row = tuple[str, float, float, float, float, str, str | None]
_W: list[_Row] = [
    ("2026-08-31", 11, 7.5, 3.5, 0, "Long 3:00", None),
    ("2026-09-07", 12, 8.0, 4.0, 0, "A · 3:00+2:30", None),
    ("2026-09-14", 11, 7.5, 3.5, 0, "Long 3:00", None),
    ("2026-09-21", 12, 8.5, 3.5, 0, "Long 3:30", None),
    ("2026-09-28", 12, 8.5, 3.5, 0, "A · 3:30+2:00", None),
    ("2026-10-05", 10, 7.0, 3.0, 0, "Long 2:30", None),
    ("2026-10-12", 7, 5.5, 1.5, 0, "Easy 90'", None),
    ("2026-10-19", 7, 4.5, 2.5, 0, "Race", "Slapy Trailmaniacs 47K · 24 Oct"),
    # Off-season after Slapy: easy running only, km fixed in OWN_KM.
    ("2026-10-26", 4, 4.0, 0, 0, "Off-season · no long run", None),
    ("2026-11-02", 4, 4.0, 0, 0, "Off-season · no long run", None),
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

# Weeks with Dan's own km target and no vert target; the rest of their phase's totals
# is split over the other weeks.
OWN_KM = {dt.date(2026, 10, 26): 40.0, dt.date(2026, 11, 2): 40.0}

# name, weeks, published km total, published vert total
PHASES = [
    ("P1", "Slapy build", 7, 569, 21000),
    # Was 427 km / 12,500 m: the off-season weeks now carry 40 km and no vert, and the
    # other P2 weeks keep their targets.
    ("P2", "Recovery & gym on-ramp", 6, 372, 8550),
    ("P3", "Base — the Kilian block", 8, 703, 28400),
    ("P4", "Specific build", 6, 544, 23900),
    ("P5", "Taper", 2, 97, 2550),
]

_KILIAN_UPHILL = ("Kilian · uphill training", "https://mtnath.com/training-for-uphill-running/")
_KILIAN_2022 = ("Kilian · 2022 season", "https://mtnath.com/training2022/")
_KILIAN_2024 = ("Kilian · 2024 training", "https://mtnath.com/training2024")
_KILIAN_WSER = ("Kilian · Western States 2025", "https://mtnath.com/wsertraining")
_UA_TRAIL = (
    "Uphill Athlete · trail running",
    "https://uphillathlete.com/trail-running/training-for-trail-running/",
)
_UA_GYM = (
    "Uphill Athlete · gym ME",
    "https://uphillathlete.com/strength-training/at-home-muscular-endurance-workout-with-progression/",
)

# Quality sessions per phase in Kilian Jornet's style: threshold mostly uphill, no flat
# speed in the Dec-Apr injury window. Advice beside the targets, not a target itself.
# name, prescription; then notes; then (label, url) sources.
QUALITY: dict[str, tuple[list[tuple[str, str]], list[str], list[tuple[str, str]]]] = {
    "P2": (
        [
            ("Uphill tempo", "3×10′ · 6–8 % · HR 164–172 · from 9 Nov"),
            (
                "Gym strength-endurance",
                "step-ups, lunges, jump squats 4×10 · +10 % BW from session 4",
            ),
            ("Hill sprints", "6–8×10″ · ≥ 20 % · 2–3′ walk down"),
        ],
        [
            "No intervals in the two weeks after Slapy: Kilian's order is get healthy, get aerobic, get ready.",
            "Keep jump height near 80 % at first; calves and shins are the history to respect.",
        ],
        [
            ("Kilian · coming back", "https://mtnath.com/coming-back-from-injury/"),
            _UA_GYM,
            _UA_TRAIL,
        ],
    ),
    "P3": (
        [
            ("Uphill threshold", "3×8′ → 2×12′ → 2×15′ · 8–15 % · HR 172–178"),
            ("Strength-endurance hill", "400–600 m at Z3 on Petřín 15 % · +3–6 kg from week 4"),
            ("Hill sprints", "6–8×10″ · ≥ 20 % · 2–3′ walk down"),
        ],
        [
            "Weeks 1–4: the hill session is the only quality; from week 5 alternate it with uphill threshold.",
            "No flat T or speed: Kilian's flat speed in his own Chianti winter gave him a TFL tendonitis.",
            "Add weight or vertical each week, never both; three easy days after a weighted session.",
        ],
        [_KILIAN_UPHILL, _KILIAN_WSER, _UA_TRAIL],
    ),
    "P4": (
        [
            (
                "Uphill + rolling",
                "20–30′ uphill threshold, then 30–40′ rolling Z2–Z3 · run the descents",
            ),
            ("Race simulation", "C weekends: 2:00 high Z2, then race effort and race fuelling"),
            ("Hill sprints", "6–8×10″ · keep weekly"),
        ],
        [
            "Drop the strength-endurance sessions; back-to-backs carry the neuromuscular load.",
            "Flat T at most every other week, and only while the legs are quiet.",
        ],
        [_KILIAN_2022, _KILIAN_2024, _UA_TRAIL],
    ),
    "P5": (
        [
            ("Uphill threshold", "3×6′ · 8–15 % · week 28 only"),
            ("Activation", "3×1′ T → VO2max two days out · otherwise 30–60′ Z1"),
        ],
        ["Keep the intensity, cut the volume about 25 % a week."],
        [_KILIAN_2022, _UA_TRAIL],
    ),
}


class PlanWeek:
    run_km: float  # set by _build from the phase totals or OWN_KM
    run_vert: float | None  # None: no vert target

    def __init__(self, i: int, row: _Row, phase: str) -> None:
        (d, h, r, b, g, we, race) = row
        self.index = i + 1
        self.start = dt.date.fromisoformat(d)
        self.end = self.start + dt.timedelta(days=6)
        self.total_h, self.run_h, self.bike_h, self.gym_h = h, r, b, g
        self.weekend, self.race = we, race
        self.phase = phase

    @property
    def to_race(self) -> int:
        return (RACE - self.start).days // 7

    @property
    def committed(self) -> bool:
        """Inside the detail horizon — a real weekly target, not a placeholder."""
        return self.start <= horizon_date()

    def __repr__(self) -> str:
        return f"<plan wk{self.index} {self.start} {self.run_h}h run>"


def _build() -> list[PlanWeek]:
    weeks, i = [], 0
    for code, _name, n, km, vert in PHASES:
        rows = _W[i : i + n]
        block = [PlanWeek(i + j, r, code) for j, r in enumerate(rows)]
        split = [w for w in block if w.start not in OWN_KM]
        split_km = km - sum(OWN_KM[w.start] for w in block if w not in split)
        run_h = sum(w.run_h for w in split)
        for w in block:
            if w in split:
                share = w.run_h / run_h
                w.run_km, w.run_vert = split_km * share, vert * share
            else:
                w.run_km, w.run_vert = OWN_KM[w.start], None
        weeks += block
        i += n
    return weeks


WEEKS = _build()
PHASE_NAME = {c: n for c, n, *_ in PHASES}
PHASE_WEEKS = {c: [w for w in WEEKS if w.phase == c] for c, *_ in PHASES}


def _bands() -> dict[str, dict[str, tuple[float, float]]]:
    """Each phase's range, read off its own weeks.

    A band the plan already implies rather than a new set of invented numbers.
    """
    out = {}
    for code, block in PHASE_WEEKS.items():
        out[code] = {
            f: (min(vs := [v for w in block if (v := getattr(w, f)) is not None]), max(vs))
            for f in ("run_h", "bike_h", "gym_h", "total_h", "run_km", "run_vert")
        }
    return out


PHASE_BANDS = _bands()


def horizon_date() -> dt.date:
    """Last Monday still written week by week."""
    return config.TODAY + dt.timedelta(weeks=HORIZON_WEEKS)


def committed_weeks() -> list[PlanWeek]:
    return [w for w in WEEKS if w.start <= horizon_date()]


def provisional_phases() -> list[dict[str, Any]]:
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


def week_for(d: dt.date) -> PlanWeek | None:
    """The plan week containing date d, or None if outside the macrocycle."""
    for w in WEEKS:
        if w.start <= d <= w.end:
            return w
    return None


def weeks_to_race() -> float:
    return (RACE - config.TODAY).days / 7
