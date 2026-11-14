"""Quality-session analysis: uphill reps, repeated segments, flat 1k reps."""

import csv
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

from tl import config

if TYPE_CHECKING:
    from tl.data import Dataset


@dataclass(frozen=True)
class HillRep:
    rep: int
    dur: float
    dist: float
    vert: float
    grade: float
    vam: float
    hr: float
    watts: float | None
    w_per_hr: float | None
    speed: float

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Self:
        dur, dist = float(row["dur_s"]), float(row["dist_m"])
        vert, hr = float(row["vert_m"]), float(row["hr"])
        watts = float(row["watts"]) if row["watts"] else None
        return cls(
            rep=int(row["rep"]),
            dur=dur,
            dist=dist,
            vert=vert,
            grade=float(row["grade_pct"]),
            vam=vert / dur * 3600,
            hr=hr,
            watts=watts,
            w_per_hr=watts / hr if watts else None,
            speed=dist / dur * 3.6,
        )


@dataclass(frozen=True)
class HillSession:
    date: str
    name: str
    reps: list[HillRep]
    mean_vam: float
    hr_drift: float
    hr_peak: float
    decoupling: float | None


@dataclass(frozen=True)
class SegmentEffort:
    date: str
    context: str
    rep: int
    secs: float
    vam: float
    hr: float
    watts: float | None
    m_per_beat: float

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Self:
        secs, hr = float(row["secs"]), float(row["hr"])
        return cls(
            date=row["date"],
            context=row["context"],
            rep=int(row["rep"]),
            secs=secs,
            vam=float(row["vert_m"]) / secs * 3600,
            hr=hr,
            watts=float(row["watts"]) if row["watts"] else None,
            m_per_beat=float(row["dist_m"]) / (hr * secs / 60),
        )


@dataclass(frozen=True)
class SegmentHistory:
    segment: str
    dist: float
    vert: float
    grade: float
    efforts: list[SegmentEffort]
    by_context: dict[str, float]


@dataclass(frozen=True)
class RepSession:
    date: str
    name: str
    rest: str
    secs: list[float]
    n: int
    avg: float
    last3: float
    best: float
    fade: float

    @classmethod
    def from_row(cls, row: dict[str, str]) -> Self:
        secs = [float(rep) for rep in row["secs"].split(",")]
        return cls(
            date=row["date"],
            name=row["session"],
            rest=row["rest"],
            secs=secs,
            n=len(secs),
            avg=sum(secs) / len(secs),
            last3=sum(secs[-3:]) / 3,
            best=min(secs),
            fade=secs[0] - secs[-1],
        )


def hill_sessions(ds: Dataset) -> list[HillSession]:
    sessions = defaultdict(list)
    for row in ds.hills:
        sessions[(row["date"], row["session"])].append(row)
    out = []
    for (date, name), rows in sorted(sessions.items()):
        reps = sorted((HillRep.from_row(row) for row in rows), key=lambda rep: rep.rep)
        vams = [rep.vam for rep in reps]
        w_per_hrs = [rep.w_per_hr for rep in reps if rep.w_per_hr]
        hrs = [rep.hr for rep in reps]
        decoupling = (
            (w_per_hrs[-1] - w_per_hrs[0]) / w_per_hrs[0] * 100 if len(w_per_hrs) > 1 else None
        )
        out.append(
            HillSession(
                date=date,
                name=name,
                reps=reps,
                mean_vam=sum(vams) / len(vams),
                hr_drift=hrs[-1] - hrs[0],
                hr_peak=max(hrs),
                decoupling=decoupling,
            )
        )
    return out


def segment_history(ds: Dataset) -> list[SegmentHistory]:
    rows_by_segment = defaultdict(list)
    for row in ds.segments:
        rows_by_segment[row["segment"]].append(row)
    out = []
    for seg, rows in rows_by_segment.items():
        first = rows[0]
        efforts = [
            SegmentEffort.from_row(row)
            for row in sorted(rows, key=lambda row: (row["date"], int(row["rep"])))
        ]
        secs_by_context = defaultdict(list)
        for effort in efforts:
            secs_by_context[effort.context].append(effort.secs)
        out.append(
            SegmentHistory(
                segment=seg,
                dist=float(first["dist_m"]),
                vert=float(first["vert_m"]),
                grade=float(first["vert_m"]) / float(first["dist_m"]) * 100,
                efforts=efforts,
                by_context={
                    context: sum(secs) / len(secs) for context, secs in secs_by_context.items()
                },
            )
        )
    return out


def rep_sessions() -> list[RepSession]:
    """Flat 1k-rep sessions from reps.csv — the threshold-pace record."""
    try:
        fh = open(config.path("reps.csv"))
    except FileNotFoundError:
        return []
    with fh:
        sessions = [RepSession.from_row(row) for row in csv.DictReader(fh)]
    return sorted(sessions, key=lambda session: session.date)
