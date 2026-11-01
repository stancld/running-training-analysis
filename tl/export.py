"""JSON export — the shape the diary artifact reads."""

import datetime as dt
import json

from . import config as C
from . import plan


def _week(e):
    w, p = e.week, e.plan
    return {
        "label": w.label,
        "start": w.start.isoformat(),
        "end": w.end.isoformat(),
        "partial": w.partial,
        "current": w.current,
        "run_h": round(w.run_h, 2),
        "run_km": round(w.run_km, 1),
        "run_vert": round(w.run_vert),
        "density": round(w.density),
        "bike_h": round(w.bike_h, 2),
        "gym_h": round(w.gym_h, 2),
        "total_h": round(w.total_h, 2),
        "run_days": w.run_days,
        "rest_days": w.rest_days,
        "longest": (round(w.longest_run.mins) if w.longest_run else 0),
        "longest_km": (round(w.longest_run.km, 1) if w.longest_run else 0),
        "longest_vert": (round(w.longest_run.vert) if w.longest_run else 0),
        "back_to_back": w.back_to_back,
        "wow": (round(w.wow, 2) if w.wow else None),
        "acwr": (round(w.acwr, 2) if w.acwr else None),
        "feel": (round(w.mean_feel, 2) if w.mean_feel is not None else None),
        "monotony": (round(e.mono, 2) if e.mono else None),
        "ctl": (round(e.fitness["ctl"], 1) if e.fitness else None),
        "atl": (round(e.fitness["atl"], 1) if e.fitness else None),
        "tsb": (round(e.fitness["tsb"], 1) if e.fitness else None),
        "flags": [{"code": c, "msg": m} for c, m in e.flags],
        "notes": e.notes(),
        "plan": (
            {
                "index": p.index,
                "phase": p.phase,
                "phase_name": plan.PHASE_NAME[p.phase],
                "run_h": p.run_h,
                "bike_h": p.bike_h,
                "gym_h": p.gym_h,
                "total_h": p.total_h,
                "run_km": round(p.run_km, 1),
                "run_vert": round(p.run_vert),
                "weekend": p.weekend,
                "race": p.race,
                "to_race": p.to_race,
            }
            if p
            else None
        ),
        "days": [
            {
                "day": name,
                "date": d.isoformat(),
                "acts": [
                    {
                        "sport": a.sport,
                        "group": a.group,
                        "type": a.type,
                        "name": a.name,
                        "note": a.note,
                        "mins": round(a.mins),
                        "km": round(a.km, 1),
                        "vert": round(a.vert),
                        "feel": a.feel,
                    }
                    for a in acts
                ],
            }
            for name, d, acts in e.days()
        ],
    }


def _period(p):
    a = p.hr_at_pace()
    return {
        "label": p.label,
        "run_h": round(p.run_h, 1),
        "run_km": round(p.run_km, 1),
        "run_vert": round(p.run_vert),
        "density": round(p.density),
        "bike_h": round(p.bike_h, 1),
        "gym_h": round(p.gym_h, 1),
        "total_h": round(p.total_h, 1),
        "run_days": p.run_days,
        "quality": len(p.quality),
        "feel": (round(p.mean_feel, 2) if p.mean_feel is not None else None),
        "hr": (round(a["hr"], 1) if a else None),
        "pace": (round(a["pace"], 3) if a else None),
        "longest": (round(p.longest_run.mins) if p.longest_run else 0),
    }


def payload(ds, entries, months, seasons):
    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "today": C.TODAY.isoformat(),
        "race": {
            "name": plan.RACE_NAME,
            "date": plan.RACE.isoformat(),
            "weeks_to_go": round(plan.weeks_to_race(), 1),
        },
        "cache": {
            "first": ds.first.isoformat(),
            "last": ds.last.isoformat(),
            "activities": len(ds.activities),
            "stale_days": (C.TODAY - ds.last).days,
        },
        "phases": [
            {"code": c, "name": n, "weeks": k, "km": km, "vert": v}
            for c, n, k, km, v in plan.PHASES
        ],
        "plan": [
            {
                "index": p.index,
                "phase": p.phase,
                "start": p.start.isoformat(),
                "total_h": p.total_h,
                "run_h": p.run_h,
                "bike_h": p.bike_h,
                "gym_h": p.gym_h,
                "run_km": round(p.run_km, 1),
                "run_vert": round(p.run_vert),
                "weekend": p.weekend,
                "race": p.race,
            }
            for p in plan.WEEKS
        ],
        "weeks": [_week(e) for e in entries],
        "months": [_period(m) for m in months],
        "seasons": [_period(s) for s in seasons],
    }


def write(obj, path):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1)


def web_payload(ds, weeks, entries, months, seasons, diary_from=None):
    """Trimmed payload for the diary page: enough to draw, not the whole cache."""
    diary_from = diary_from or plan.DIARY_START
    return {
        "generated": dt.datetime.now().strftime("%d %B %Y, %H:%M"),
        "today": C.TODAY.isoformat(),
        "race": {
            "name": plan.RACE_NAME,
            "date": plan.RACE.isoformat(),
            "weeks_to_go": round(plan.weeks_to_race(), 1),
        },
        "cache": {
            "first": ds.first.isoformat(),
            "last": ds.last.isoformat(),
            "n": len(ds.activities),
            "stale": (C.TODAY - ds.last).days,
        },
        "seasons": [_period(s) for s in seasons],
        "months": [_period(m) for m in months],
        "weeks": [
            {
                "label": w.label,
                "start": w.start.isoformat(),
                "run_h": round(w.run_h, 2),
                "km": round(w.run_km, 1),
                "vert": round(w.run_vert),
                "density": round(w.density),
                "bike_h": round(w.bike_h, 2),
                "gym_h": round(w.gym_h, 2),
                "total_h": round(w.total_h, 2),
                "wow": (round(w.wow, 2) if w.wow else None),
                "acwr": (round(w.acwr, 2) if w.acwr else None),
                "flags": [c for c, _ in w.flags()],
                "current": w.current,
            }
            for w in weeks[-60:]
        ],
        "horizon": {
            "weeks": plan.HORIZON_WEEKS,
            "date": plan.horizon_date().isoformat(),
            "committed": len(plan.committed_weeks()),
        },
        "plan": [
            {
                "index": p.index,
                "phase": p.phase,
                "phase_name": plan.PHASE_NAME[p.phase],
                "start": p.start.isoformat(),
                "total_h": p.total_h,
                "run_h": p.run_h,
                "bike_h": p.bike_h,
                "gym_h": p.gym_h,
                "km": round(p.run_km),
                "vert": round(p.run_vert),
                "weekend": p.weekend,
                "race": p.race,
                "committed": p.committed,
            }
            for p in plan.WEEKS
        ],
        "provisional": [
            {
                "phase": q["phase"],
                "name": q["name"],
                "weeks": q["weeks"],
                "start": q["start"].isoformat(),
                "end": q["end"].isoformat(),
                "run_h": list(q["bands"]["run_h"]),
                "bike_h": list(q["bands"]["bike_h"]),
                "gym_h": list(q["bands"]["gym_h"]),
                "km": [round(x) for x in q["bands"]["run_km"]],
                "vert": [round(x) for x in q["bands"]["run_vert"]],
                "total_km": q["km"],
                "total_vert": q["vert"],
            }
            for q in plan.provisional_phases()
        ],
        "diary": [_week(e) for e in entries if e.week.start >= diary_from],
    }
