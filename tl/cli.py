"""tl — training analysis for the Chianti 120K macrocycle.

python3 -m tl                     everything: status, weeks, diary, verdict
python3 -m tl status              where the prep stands today
python3 -m tl weeks [n|all]       week map (default: last 16)
python3 -m tl months [n|all]      month map (default: all)
python3 -m tl seasons             season map
python3 -m tl plan                the 29-week macrocycle vs what happened
python3 -m tl diary [n|all|DATE]  diary entries (default: plan weeks so far)
python3 -m tl hills | segments | reps      quality-session analysis
python3 -m tl export [path]       full JSON dump
python3 -m tl site [path]         render web/diary.html for publishing
"""

import datetime as dt
import json
import os
import pathlib
import sys

from . import config as C
from . import diary as diary_mod
from . import export as export_mod
from . import plan, quality, render
from .data import Dataset
from .periods import build_months, build_seasons, build_weeks, fitness_curve


class Lab:
    """One load of the cache, everything derived from it."""

    def __init__(self):
        self.ds = Dataset.load()
        load = self.ds.daily_load()
        self.weeks = build_weeks(self.ds)
        self.months = build_months(self.ds)
        self.seasons = build_seasons(self.ds)
        self.fitness = fitness_curve(self.ds, load)
        self.entries = diary_mod.build(self.weeks, self.fitness, load)
        self.by_start = {w.start: w for w in self.weeks}


def _tail(seq, arg, default):
    if arg in ("all", "full"):
        return seq
    try:
        return seq[-int(arg) :]
    except TypeError, ValueError:
        return seq[-default:]


def cmd_status(lab, arg=None):
    ds, out = lab.ds, []
    done = [w for w in lab.weeks if not w.partial]
    cur = next((w for w in lab.weeks if w.current), None)
    p = plan.week_for(C.TODAY)
    out.append(render.title(f"CHIANTI PREP — {C.TODAY:%A %d %B %Y}"))
    out.append(
        f"  {plan.RACE_NAME}, {plan.RACE:%d %B %Y} — "
        f"{plan.weeks_to_race():.1f} weeks out"
        + (f", plan week {p.index}/29 ({p.phase} {plan.PHASE_NAME[p.phase]})" if p else "")
    )
    out.append(
        f"  Cache: {len(ds.activities)} activities, {ds.first} → {ds.last} "
        f"({(C.TODAY - ds.last).days} d behind today)"
    )
    last4 = done[-4:]
    prev4 = done[-8:-4]
    l4 = sum(w.run_h for w in last4) / 4
    p4 = sum(w.run_h for w in prev4) / 4 if prev4 else None
    dens = (
        sum(w.run_vert for w in last4) / sum(w.run_h for w in last4)
        if sum(w.run_h for w in last4)
        else 0
    )
    out.append("")
    out.append(
        f"  4-week running load   {l4:.1f} h/wk"
        + (f"   vs {p4:.1f} h/wk in the four before  ({l4 / p4:.2f}x)" if p4 else "")
    )
    out.append(
        f"  4-week vert density   {dens:.0f} m/h   "
        + ("above" if dens >= C.VERT_FLOOR else "BELOW")
        + f" the {C.VERT_FLOOR} m/h floor"
    )
    f = lab.fitness.get(C.TODAY) or lab.fitness[max(lab.fitness)]
    out.append(
        f"  Fitness / fatigue     CTL {f['ctl']:.0f} · ATL {f['atl']:.0f} · form {f['tsb']:+.0f}"
    )
    if cur and p:
        elapsed = (min(C.TODAY, cur.end) - cur.start).days + 1
        out.append("")
        out.append(
            f"  This week ({cur.label}, {elapsed}/7 days): "
            f"run {cur.run_h:.1f} of {p.run_h:.1f} h "
            f"({cur.run_h / p.run_h * 100:.0f}%), bike {cur.bike_h:.1f} of "
            f"{p.bike_h:.1f} h, {cur.run_km:.0f} km, {cur.run_vert:.0f} m, "
            f"{cur.density:.0f} m/h"
        )
        out.append(f"  Weekend called for: {p.weekend}")
    recent = [w for w in done[-6:] if w.flags()]
    out.append("")
    if recent:
        out.append("  Guardrail flags in the last six completed weeks:")
        for w in recent:
            for c, m in w.flags():
                out.append(f"    {w.label}  [{c}] {m}")
    else:
        out.append("  No guardrail flags in the last six completed weeks.")
    if C.TODAY.month in C.RISK_MONTHS:
        out.append("  Calendar is inside the Dec–Apr injury window — hold R1 hard.")
    return "\n".join(out)


def cmd_weeks(lab, arg=None):
    return render.weeks_table(_tail(lab.weeks, arg, 16))


def cmd_months(lab, arg=None):
    return render.months_table(_tail(lab.months, arg, len(lab.months)))


def cmd_seasons(lab, arg=None):
    return render.seasons_table(lab.seasons)


def cmd_plan(lab, arg=None):
    return render.plan_table(lab.by_start)


def cmd_diary(lab, arg=None):
    if arg and arg not in ("all", "full"):
        try:
            d = dt.date.fromisoformat(arg)
            entries = [e for e in lab.entries if e.week.start <= d <= e.week.end]
        except ValueError:
            entries = _tail([e for e in lab.entries if e.week.start >= plan.DIARY_START], arg, 4)
    elif arg in ("all", "full"):
        entries = lab.entries
    else:
        entries = [e for e in lab.entries if e.week.start >= plan.DIARY_START]
    head = render.title("TRAINING DIARY")
    body = [render.diary_entry(e) for e in entries]
    return head + "\n" + "\n".join(body)


def cmd_hills(lab, arg=None):
    return render.hills_block(quality.hill_sessions(lab.ds))


def cmd_segments(lab, arg=None):
    return render.segments_block(quality.segment_history(lab.ds))


def cmd_reps(lab, arg=None):
    return render.reps_block(quality.rep_sessions())


def cmd_site(lab, arg=None):
    """Render the diary page from web/diary.tmpl.html.

    The optional argument is either an output path or a date — the Monday the
    diary should start from. It defaults to the week before the macrocycle
    opens, so the entries lead in with the week that set up week 1.
    """
    root = os.path.dirname(C.DATA)
    tmpl = os.path.join(root, "web", "diary.tmpl.html")
    since = None
    out = os.path.join(root, "web", "diary.html")
    if arg:
        try:
            since = dt.date.fromisoformat(arg)
        except ValueError:
            out = arg
    obj = export_mod.web_payload(
        lab.ds, lab.weeks, lab.entries, lab.months, lab.seasons, diary_from=since
    )
    html = pathlib.Path(tmpl).read_text()
    if "/*DATA*/" not in html:
        return f"{tmpl} has no /*DATA*/ placeholder"
    with open(out, "w") as fh:
        fh.write(html.replace("/*DATA*/", json.dumps(obj, ensure_ascii=False)))
    return (
        f"wrote {out}  ({os.path.getsize(out) // 1024} KB, "
        f"{len(obj['diary'])} diary weeks, {len(obj['months'])} months)"
    )


def cmd_export(lab, arg=None):
    path = arg or C.path("diary.json")
    obj = export_mod.payload(lab.ds, lab.entries, lab.months, lab.seasons)
    export_mod.write(obj, path)
    return f"wrote {path}  ({len(obj['weeks'])} weeks, {len(obj['months'])} months)"


COMMANDS = {
    "status": cmd_status,
    "weeks": cmd_weeks,
    "months": cmd_months,
    "seasons": cmd_seasons,
    "plan": cmd_plan,
    "diary": cmd_diary,
    "hills": cmd_hills,
    "segments": cmd_segments,
    "reps": cmd_reps,
    "export": cmd_export,
    "site": cmd_site,
}

DEFAULT = ["status", "weeks", "plan", "diary"]


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if argv and argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    lab = Lab()
    if not argv:
        for name in DEFAULT:
            print(COMMANDS[name](lab))
        return 0
    while argv:
        name = argv.pop(0)
        if name not in COMMANDS:
            print(f"unknown command {name!r}\n")
            print(__doc__)
            return 1
        arg = argv.pop(0) if argv and argv[0] not in COMMANDS else None
        print(COMMANDS[name](lab, arg))
    return 0
