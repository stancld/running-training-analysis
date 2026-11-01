"""Quality-session analysis: uphill reps, repeated segments, flat 1k reps."""

import csv
from collections import defaultdict

from tl import config


def hill_sessions(ds):
    sessions = defaultdict(list)
    for r in ds.hills:
        sessions[(r["date"], r["session"])].append(r)
    out = []
    for (date, name), reps in sorted(sessions.items()):
        reps.sort(key=lambda x: int(x["rep"]))
        rows, vam, whr = [], [], []
        for x in reps:
            dur, dist = float(x["dur_s"]), float(x["dist_m"])
            v, hr = float(x["vert_m"]), float(x["hr"])
            w = float(x["watts"]) if x["watts"] else None
            rate = v / dur * 3600
            vam.append(rate)
            ratio = w / hr if w else None
            if ratio:
                whr.append(ratio)
            rows.append(
                {
                    "rep": int(x["rep"]),
                    "dur": dur,
                    "dist": dist,
                    "vert": v,
                    "grade": float(x["grade_pct"]),
                    "vam": rate,
                    "hr": hr,
                    "watts": w,
                    "w_per_hr": ratio,
                    "speed": dist / dur * 3.6,
                }
            )
        hrs = [r["hr"] for r in rows]
        dec = ((whr[-1] - whr[0]) / whr[0] * 100) if len(whr) > 1 else None
        out.append(
            {
                "date": date,
                "name": name,
                "reps": rows,
                "mean_vam": sum(vam) / len(vam),
                "hr_drift": hrs[-1] - hrs[0],
                "hr_peak": max(hrs),
                "decoupling": dec,
            }
        )
    return out


def segment_history(ds):
    rows_by_segment = defaultdict(list)
    for r in ds.segments:
        rows_by_segment[r["segment"]].append(r)
    out = []
    for seg, rows in rows_by_segment.items():
        d0 = rows[0]
        efforts = []
        for r in sorted(rows, key=lambda x: (x["date"], int(x["rep"]))):
            t, hr = float(r["secs"]), float(r["hr"])
            v, dist = float(r["vert_m"]), float(r["dist_m"])
            w = float(r["watts"]) if r["watts"] else None
            efforts.append(
                {
                    "date": r["date"],
                    "context": r["context"],
                    "rep": int(r["rep"]),
                    "secs": t,
                    "vam": v / t * 3600,
                    "hr": hr,
                    "watts": w,
                    "m_per_beat": dist / (hr * t / 60),
                }
            )
        by = defaultdict(list)
        for e in efforts:
            by[e["context"]].append(e["secs"])
        out.append(
            {
                "segment": seg,
                "dist": float(d0["dist_m"]),
                "vert": float(d0["vert_m"]),
                "grade": float(d0["vert_m"]) / float(d0["dist_m"]) * 100,
                "efforts": efforts,
                "by_context": {k: sum(v) / len(v) for k, v in by.items()},
            }
        )
    return out


def rep_sessions():
    """Flat 1k-rep sessions from reps.csv — the threshold-pace record."""
    out = []
    try:
        fh = open(config.path("reps.csv"))
    except FileNotFoundError:
        return out
    with fh:
        for r in csv.DictReader(fh):
            s = [float(x) for x in r["secs"].split(",")]
            out.append(
                {
                    "date": r["date"],
                    "name": r["session"],
                    "rest": r["rest"],
                    "secs": s,
                    "n": len(s),
                    "avg": sum(s) / len(s),
                    "last3": sum(s[-3:]) / 3,
                    "best": min(s),
                    "fade": s[0] - s[-1],
                }
            )
    out.sort(key=lambda x: x["date"])
    return out
