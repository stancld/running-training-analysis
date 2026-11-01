"""Paths, sport taxonomy, guardrail thresholds and the HR and load models.

The thresholds come from Dan's own injury history, not textbook defaults.
"""

import datetime as dt
from pathlib import Path

DATA = Path(__file__).absolute().parent.parent / "data"


def path(name: str) -> Path:
    return DATA / name


RUN = {"Run", "TrailRun", "RACE_Run"}
BIKE = {"Ride", "VirtualRide"}
STRENGTH = {"Gym", "Workout", "Yoga"}
HIKE = {"Hike", "Snowshoe", "Climb", "AlpineSki", "NordicSki"}
OTHER = {"Walk", "Other", "Swim"}

GROUPS = [("run", RUN), ("bike", BIKE), ("gym", STRENGTH), ("hike", HIKE), ("other", OTHER)]


def group_of(sport: str) -> str:
    for name, members in GROUPS:
        if sport in members:
            return name
    return "other"


# Daniels session types (E L T I R M F S RACE) as Dan writes them in his titles.
QUALITY = {"T", "I", "R", "M", "F", "RACE"}

WOW_CAP = 1.25  # R1/R2 — max week-over-week running-hour ratio
# Acute week over the mean of the 4 weeks before it. Uncoupled (Lolli 2019), so the week
# does not dilute its own baseline; 1.44 is as strict as the old coupled 1.30.
ACWR_CAP = 1.44  # acute (1 wk) : chronic (previous 4 wk) running hours
VERT_FLOOR = 300  # R3 — m of climb per running hour on big weeks
BIG_WEEK_H = 8.0
KM_CEILING = 100.0  # R6 — hard weekly running-kilometre ceiling
RISK_MONTHS = (12, 1, 2, 3, 4)  # Dec-Apr: 6 of 9 overuse onsets
BANNED_TYPES = {"I", "R"}  # R4 — no interval/repetition work this season

# Dan's running HR zones from Strava, as set in zonelens: (code, name, top bpm, inclusive).
HR_ZONES = (
    ("Z1", "Recovery", 139),
    ("Z2", "Endurance", 163),
    ("Z3", "Tempo", 173),
    ("Z4", "Threshold", 181),
    ("Z5", "Anaerobic", None),
)
# Cycling zones from Garmin: HR, and power from the ride's watts stream.
BIKE_HR_ZONES = (
    ("Z1", "Warm up", 127),
    ("Z2", "Easy", 152),
    ("Z3", "Aerobic", 167),
    ("Z4", "Threshold", 173),
    ("Z5", "Maximum", None),
)
POWER_ZONES = (
    ("Z1", "Active recovery", 155),
    ("Z2", "Endurance", 211),
    ("Z3", "Tempo", 254),
    ("Z4", "Threshold", 296),
    ("Z5", "VO2 max", 339),
    ("Z6", "Anaerobic", 424),
    ("Z7", "Neuromuscular", None),
)


def zone_index(value: float, zones: tuple[tuple[str, str, int | None], ...]) -> int:
    """Index of the zone whose inclusive top `value` stays under; the last zone is open."""
    return next(i for i, (*_, top) in enumerate(zones) if top is None or value <= top)


# HR = 81.2 + 21.1*ln(relative_effort per hour); r=0.91, +-3.5 bpm, n=46
HR_A, HR_B = 81.2, 21.1

# Load-unit model. Strava relative_effort is a TRIMP-like quantity and is the
# anchor; sports without it are scored as a fraction of a running minute.
# These ratios are estimates, not measurements — read trends, not levels.
LOAD_RATIO = {"run": 1.00, "bike": 0.75, "gym": 0.50, "hike": 0.60, "other": 0.0}
CTL_TAU, ATL_TAU = 42, 7

TODAY = dt.datetime.now().astimezone().date()
