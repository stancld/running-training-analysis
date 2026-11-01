"""JSON export — the shape the diary artifact reads."""

import datetime as dt
import json

from tl import config, periods, plan


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
        "wow": (round(w.wow, 2) if w.wow is not None else None),
        "acwr": (round(w.acwr, 2) if w.acwr is not None else None),
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


def _zones(ds):
    """Running time per HR zone for each phase that has started."""
    out = []
    for code, name, *_ in plan.PHASES:
        weeks = plan.PHASE_WEEKS[code]
        start, end = weeks[0].start, weeks[-1].start + dt.timedelta(days=6)
        if start > config.TODAY:
            break
        acts = [a for a in ds.activities if start <= a.date <= end]
        z = periods.Period(start, end, acts).zone_minutes()
        out.append(
            {
                "phase": code,
                "name": name,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "current": start <= config.TODAY <= end,
                "minutes": [round(m) for m in z["minutes"]],
                "measured": round(z["measured"]),
                "modelled": round(z["modelled"]),
                "no_hr": round(z["no_hr"]),
            }
        )
    lo = 0
    bands = []
    for code, name, top in config.HR_ZONES:
        bands.append({"code": code, "name": name, "lo": lo, "hi": top})
        lo = top
    return {"bands": bands, "phases": out}


def payload(ds, entries, months, seasons):
    return {
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "today": config.TODAY.isoformat(),
        "race": {
            "name": plan.RACE_NAME,
            "date": plan.RACE.isoformat(),
            "weeks_to_go": round(plan.weeks_to_race(), 1),
        },
        "cache": {
            "first": ds.first.isoformat(),
            "last": ds.last.isoformat(),
            "activities": len(ds.activities),
            "stale_days": (config.TODAY - ds.last).days,
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


def web_payload(ds, weeks, entries, months, seasons, fitness, diary_from=None):
    """Trimmed payload for the diary page: enough to draw, not the whole cache."""
    diary_from = diary_from or plan.DIARY_START
    return {
        "generated": dt.datetime.now().strftime("%d %B %Y, %H:%M"),
        "today": config.TODAY.isoformat(),
        "race": {
            "name": plan.RACE_NAME,
            "date": plan.RACE.isoformat(),
            "weeks_to_go": round(plan.weeks_to_race(), 1),
        },
        "cache": {
            "first": ds.first.isoformat(),
            "last": ds.last.isoformat(),
            "n": len(ds.activities),
            "stale": (config.TODAY - ds.last).days,
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
                "wow": (round(w.wow, 2) if w.wow is not None else None),
                "acwr": (round(w.acwr, 2) if w.acwr is not None else None),
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
        # Daily, not weekly: a 7-day ATL swings too much within a week to read from week ends.
        "fitness": [
            {"date": d.isoformat(), **{k: round(v, 1) for k, v in f.items()}}
            for d, f in fitness.items()
            if config.TODAY - dt.timedelta(days=83) <= d <= config.TODAY
        ],
        "zones": _zones(ds),
        "guardrails": {
            "wow": config.WOW_CAP,
            "acwr": config.ACWR_CAP,
            "vert_floor": config.VERT_FLOOR,
            "big_week_h": config.BIG_WEEK_H,
            "km": config.KM_CEILING,
        },
    }
