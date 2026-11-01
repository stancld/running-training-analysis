"""tl — a small training-analysis library over Dan's Strava/COROS cache.

    from tl.data import Dataset
    from tl.periods import build_weeks, build_months, build_seasons

Command line: python3 -m tl --help
"""

__all__ = [
    "cli",
    "config",
    "data",
    "diary",
    "export",
    "periods",
    "plan",
    "quality",
    "render",
]
