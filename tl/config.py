"""Static configuration: paths, sport taxonomy, physiology, guardrails.

Every constant here traces back to a specific piece of Dan's own history —
see MEMORY: injury-pattern-flat-volume and feel-drivers-regression.
"""

import datetime as dt
import os

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def path(name):
    return os.path.join(DATA, name)


# ----------------------------------------------------------------- taxonomy
RUN = {"Run", "TrailRun", "RACE_Run"}
BIKE = {"Ride", "VirtualRide"}
STRENGTH = {"Gym", "Workout", "Yoga"}
HIKE = {"Hike", "Snowshoe", "Climb", "AlpineSki", "NordicSki"}
OTHER = {"Walk", "Other", "Swim"}

GROUPS = [("run", RUN), ("bike", BIKE), ("gym", STRENGTH), ("hike", HIKE), ("other", OTHER)]


def group_of(sport):
    for name, members in GROUPS:
        if sport in members:
            return name
    return "other"


# Daniels session types as Dan writes them in his own titles
SESSION_TYPES = {
    "E": "easy",
    "L": "long",
    "T": "threshold",
    "I": "interval",
    "R": "repetition",
    "M": "marathon pace",
    "F": "fartlek",
    "S": "strides",
    "RACE": "race",
}
QUALITY = {"T", "I", "R", "M", "F", "RACE"}

# ---------------------------------------------------------------- guardrails
WOW_CAP = 1.25  # R1/R2 — max week-over-week running-hour ratio
ACWR_CAP = 1.30  # acute (1 wk) : chronic (4 wk) running hours
VERT_FLOOR = 300  # R3 — m of climb per running hour on big weeks
BIG_WEEK_H = 8.0
KM_CEILING = 100.0  # R6 — hard weekly running-kilometre ceiling
RISK_MONTHS = (12, 1, 2, 3, 4)  # Dec-Apr: 6 of 9 overuse onsets
BANNED_TYPES = {"I", "R"}  # R4 — no interval/repetition work this season
CALF_SESSIONS_PER_WEEK = 2  # R7

# ------------------------------------------------------------- HR modelling
# HR = 81.2 + 21.1*ln(relative_effort per hour); r=0.91, +-3.5 bpm, n=46
HR_A, HR_B = 81.2, 21.1
HR_MAX_EST = 190
LT_HR = 174  # COROS Z4 floor; T sessions run 168-172

# Load-unit model. Strava relative_effort is a TRIMP-like quantity and is the
# anchor; sports without it are scored as a fraction of a running minute.
# These ratios are estimates, not measurements — read trends, not levels.
LOAD_RATIO = {"run": 1.00, "bike": 0.75, "gym": 0.50, "hike": 0.60, "other": 0.0}
CTL_TAU, ATL_TAU = 42, 7

# ------------------------------------------------------------------ context
SEASON_START_MONTH = 1  # Dan counts seasons as calendar years
TODAY = dt.date.today()
