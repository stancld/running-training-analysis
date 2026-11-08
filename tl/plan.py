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
RACE_COURSE = "123 km / 5200 m"

# The UTMB-index goal Dan set on 2 Nov 2026 (LOG.md) and what each index means on the
# course. Times are estimates: a log-time fit of 81 UTCC 2026 finishers whose only indexed
# 100M result is that race, scaled by 1.029 for the 2027 course; the formula itself is private.
GOAL: dict[str, Any] = {
    "now": 665,  # Dan's 100K index from Lavaredo 80K 2026, 10:20:23
    "goal": 700,
    "stretch": 720,  # if the back half holds
    "fade": (650, 700),
    "field": 539,  # UTCC 2026 finishers, for the places
    # index, finish time (±10 min), place in the 2026 field, Lavaredo 80K equivalent
    "ladder": [
        (600, "15:33", 85, "11:27"),
        (650, "14:21", 43, "10:35"),
        (665, "14:01", 36, "10:20"),
        (700, "13:19", 25, "9:36"),
        (720, "12:57", 20, "9:16"),
        (750, "12:25", 16, "8:47"),
        (780, "11:57", 14, "8:20"),
    ],
    "note": (
        "Estimates from a log-time fit of UTCC 2026 finishers (n = 81, ±10 min), scaled to "
        "the 2027 course; the UTMB formula is private. Lavaredo 80K 10:20 = 665."
    ),
}
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
    (
        "2026-11-09",
        10.25,
        6.25,
        2.0,
        2.0,
        "Easy Z1/Z2 · 1× strides · 1 weekend long · 2× gym · 2×1 h easy bike",
        None,
    ),
    ("2026-11-16", 11, 6.5, 2.5, 2.0, "A · 3:00+2:15", None),
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
OWN_KM = {
    dt.date(2026, 10, 26): 40.0,
    dt.date(2026, 11, 2): 40.0,
    dt.date(2026, 11, 9): 70.0,
    dt.date(2026, 11, 16): 70.0,
}

# name, weeks, published km total, published vert total
PHASES = [
    ("P1", "Slapy build", 7, 569, 21000),
    # W9-12 have fixed km; W12 is reduced to 6.5 h (LOG.md).
    # Remove each reduction rather than redistribute it into the other weeks.
    ("P2", "Recovery & gym on-ramp", 6, 349.16, 3782),
    ("P3", "Base", 8, 703, 28400),
    ("P4", "Specific build", 6, 544, 23900),
    ("P5", "Taper", 2, 97, 2550),
]

_MTNATH_UPHILL = ("mtnath · uphill running 2019", "https://mtnath.com/training-for-uphill-running/")
_KILIAN_2022 = ("Kilian · 2022 season", "https://mtnath.com/training2022/")
_KILIAN_2024 = ("Kilian · 2024 training", "https://mtnath.com/training2024")
_KILIAN_WSER = ("Kilian · Western States 2025", "https://mtnath.com/wsertraining")
_KILIAN_BACK = ("Kilian · coming back", "https://mtnath.com/coming-back-from-injury/")
_UA_TRAIL = (
    "Uphill Athlete · trail running",
    "https://uphillathlete.com/trail-running/training-for-trail-running/",
)
_UA_GYM = (
    "Uphill Athlete · gym ME",
    "https://uphillathlete.com/strength-training/at-home-muscular-endurance-workout-with-progression/",
)
_UA_CARRY = (
    "Uphill Athlete · weighted ME",
    "https://uphillathlete.com/aerobic-training/vertical-beast-mode-what-is-muscular-endurance-why-it-is-important-for-any-alpinist-or-mountaineer-and-how-do-you-train-it/",
)

# Quality sessions per phase: threshold mostly uphill, flat speed rationed in the Dec-Apr
# injury window. Drawn from Kilian Jornet's posts and Uphill Athlete, adapted to Dan's
# record; each note opens with whose claim it is. Advice beside the targets, not a target.
# name, prescription; then notes; then (label, url) sources.
QUALITY: dict[str, tuple[list[tuple[str, str]], list[str], list[tuple[str, str]]]] = {
    "P2": (
        [
            ("Uphill tempo", "3×10′ · 6–8 % · HR 164–172, Dan's Z3 · from 9 Nov, except W11"),
            (
                "Gym strength-endurance",
                "step-ups, lunges, jump squats 4×10 · +10 % BW from session 4 · after Uphill Athlete",
            ),
            ("Hill sprints", "6–8×10″ · ≥ 20 % · 2–3′ walk down · Uphill Athlete · except W11"),
        ],
        [
            "Dan's W11 override, revised 8 Nov: 70 km easy Z1/Z2 apart from one strides session, one weekend long; no uphill tempo or hill sprints. Two gym sessions and two 1 h easy aerobic rides. The 6.25 running hours are a planning estimate, not a pace prescription; long-run duration remains open. His history includes six consecutive 79.7-85.4 km weeks before the taper, but this still exceeds the projected R1 ramp after the off-season; the guardrail is unchanged.",
            "Our rule: no intervals in the two weeks after Slapy. Kilian (2022) plans nothing specific for the week after a race and comes back by muscle soreness, how tired he feels when he starts running, and the desire to train.",
            "Uphill Athlete: body weight only for the first 2–3 gym sessions, then no more than 10 % BW from session 4; once a week is enough, with 2–3 easy days after. Start jumps at about 80 % of height and range.",
            "Dan's record: calves and shins are the injury history to respect.",
        ],
        [_KILIAN_2022, _UA_GYM, _UA_TRAIL],
    ),
    "P3": (
        [
            (
                "Strength-endurance hill",
                "400–600 m of climb at Z3 on Petřín 15 % · +3–6 kg from week 4 · our version of Uphill Athlete's weighted carry",
            ),
            ("Hill sprints", "6–8×10″ · ≥ 20 % · 2–3′ walk down · Uphill Athlete"),
            ("Bike", "the plan's 2–2.5 h at Z2 · takes any hours R1 or R2 cut from running"),
        ],
        [
            "Our plan: a base block of Z1–Z2 volume around one hill session. Kilian (2024): his base runs Dec–Mar at ~30 h a week, mostly Z2 skimo with 40–70 km of running and one progressive run to touch Z4–Z5; his uphill threshold belongs to the specific block (P4).",
            "Scale: Dan logged 490 h of running, riding and gym in 2025, about 9.4 h a week. Kilian asks readers to plan to their own needs, not to copy other athletes (Western States 2025).",
            "Our adaptation: the hill session. mtnath (2019) climbs 500–750 m on 25–35 %, 2–3 reps, with no weight mentioned. Uphill Athlete adds 5–10 % of body weight to start, on 30–100 % slopes, and warns HR reads below Z3 under weight: the legs set the limit. Petřín's 15 % is under both ranges. +3–6 kg assumes ~67 kg, inferred from a ride's W/kg, not weighed.",
            "Our adaptation: the bike stands in for Kilian's skimo. In his Western States build he alternated run days with 2 h heat-training bike days, which also let his knee recover.",
            "Our rule: one key session a week, hill sprints aside. From week 5 flat T may replace the hill session at most every other week: ≤ 20′ at T (2×4k, 6×1.5k), never in or right after a week flagged R1 or R2. No R or I (R4).",
            "Dan's record, a correlation (the cache logs injury months, not causes): the Feb–Mar 2024 and Jan 2026 injuries each followed 3+ straight weeks of two flat T/R/I/M sessions plus an R1 jump; Apr 2025 followed weeks of I and T, half of them uphill, with repeated R1 jumps. Aug–Sep 2026, one session a week alternating flat T and uphill 5×5′, stayed clean.",
            "Kilian (2024) always struggled with small injuries when running a lot of high speed on the flat, so he kept one short flat threshold a week (10×400 m). Before Chianti 2025 he ran a few times a week on top of his usual ski base, with one speed session a week; he blames those sessions for a TFL tendonitis and calls training on through the growing pain a mistake (Western States 2025). Our rule: stop a session type at the first localised pain.",
            "Uphill Athlete: add weight or vertical, never both at once; at least three easy days after each weighted session at first.",
        ],
        [_MTNATH_UPHILL, _KILIAN_2024, _KILIAN_WSER, _UA_CARRY, _UA_TRAIL],
    ),
    "P4": (
        [
            (
                "Uphill threshold",
                "3×8′ → 2×12′ → 2×15′ · 8–15 % · HR 172–178, Dan's Z3–Z4 · weeks 1, 3, 5",
            ),
            (
                "Uphill + rolling",
                "20–30′ uphill threshold, then 30–40′ rolling Z2–Z3 · run the descents",
            ),
            ("Race simulation", "C weekends: 2:00 high Z2, then race effort and race fuelling"),
            ("Hill sprints", "6–8×10″ · keep weekly · Uphill Athlete"),
        ],
        [
            "Our plan: one key session a week, uphill threshold in weeks 1, 3 and 5, one progression step each; uphill + rolling in weeks 2, 4 and 6.",
            "Kilian (2024): his specific block is 6 weeks, with two uphill thresholds a week, one of them 2×15–16′ at 10–15 %; he puts getting race-ready at 6–8 weeks once the base is there (Coming back from injury). The 3×8′ and 2×12′ steps and the 8 % floor are ours.",
            "Dan's record: HR 172–178 is his band around an LTHR of 176 taken from his session notes; Kilian goes by feel and tracks progress on repeat uphill routes.",
            "Kilian (2022) runs race simulations at high Z2 until as tired as at the race's key moment, then at race effort; the 2:00 is ours.",
            "Uphill Athlete: in the specific phase, swap the strength-endurance work for back-to-back long runs and one Z3 or Z4 interval session, and keep the hill sprints.",
            "Our rule: flat T at most every other week, and only while the legs are quiet.",
        ],
        [_KILIAN_2022, _KILIAN_2024, _KILIAN_BACK, _UA_TRAIL],
    ),
    "P5": (
        [
            ("Uphill threshold", "3×6′ · 8–15 % · week 28 only"),
            ("Activation", "3×1′ T → VO2max two days out · otherwise 30–60′ Z1"),
        ],
        [
            "Uphill Athlete: cut total hours about 25 % a week and keep speed work, trimming it about half as much as the volume. The plan's own rows cut total hours more: 11 → 8, then 4 in race week.",
            "Dan's record: 3×1′ T → VO2max is his Slapy opener, run the day before the race; two days out and the 3×6′ are ours. Kilian (2022): his Zegama race week was very easy, 30′ to 1 h at Z1 except one 3 h day at Z2.",
        ],
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
