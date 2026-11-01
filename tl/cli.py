"""tl — training analysis for the Chianti 120K macrocycle.

uv run tl                     everything: status, weeks, diary, verdict
uv run tl status              where the prep stands today
uv run tl weeks [n|all]       week map (default: last 16)
uv run tl months [n|all]      month map (default: all)
uv run tl seasons             season map
uv run tl plan                the 29-week macrocycle vs what happened
uv run tl diary [n|all|DATE]  diary entries (default: plan weeks so far)
uv run tl hills | segments | reps      quality-session analysis
uv run tl export [path]       full JSON dump
uv run tl site [path]         write web/src/payload.json for the diary page
"""

import datetime as dt
import json
import sys
from pathlib import Path

from tl import config, diary, export, plan, quality, render
from tl.data import Dataset
from tl.periods import build_months, build_seasons, build_weeks, fitness_curve


class Lab:
    """One load of the cache, everything derived from it."""

    def __init__(self) -> None:
        self.ds = Dataset.load()
        load = self.ds.daily_load()
        self.weeks = build_weeks(self.ds)
        self.months = build_months(self.ds)
        self.seasons = build_seasons(self.ds)
        self.fitness = fitness_curve(self.ds, load)
        self.entries = [diary.Entry(w, self.fitness, load) for w in self.weeks]
        self.by_start = {w.start: w for w in self.weeks}


def _tail[T](seq: list[T], arg: str | None, default: int) -> list[T]:
    if arg in ("all", "full"):
        return seq
    try:
        return seq[-int(arg) :] if arg else seq[-default:]
    except ValueError:
        return seq[-default:]


def cmd_status(lab: Lab, _arg: str | None = None) -> str:
    ds, out = lab.ds, []
    done = [w for w in lab.weeks if not w.partial]
    cur = next((w for w in lab.weeks if w.current), None)
    p = plan.week_for(config.TODAY)
    out.append(render.title(f"CHIANTI PREP — {config.TODAY:%A %d %B %Y}"))
    out.append(
        f"  {plan.RACE_NAME}, {plan.RACE:%d %B %Y} — "
        f"{plan.weeks_to_race():.1f} weeks out"
        + (f", plan week {p.index}/29 ({p.phase} {plan.PHASE_NAME[p.phase]})" if p else "")
    )
    out.append(
        f"  Cache: {len(ds.activities)} activities, {ds.first} → {ds.last} "
        f"({(config.TODAY - ds.last).days} d behind today)"
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
        + ("above" if dens >= config.VERT_FLOOR else "BELOW")
        + f" the {config.VERT_FLOOR} m/h floor"
    )
    f = lab.fitness.get(config.TODAY) or lab.fitness[max(lab.fitness)]
    out.append(
        f"  Fitness / fatigue     CTL {f['ctl']:.0f} · ATL {f['atl']:.0f} · form {f['tsb']:+.0f}"
    )
    if cur and p:
        elapsed = (min(config.TODAY, cur.end) - cur.start).days + 1
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
    if config.TODAY.month in config.RISK_MONTHS:
        out.append("  Calendar is inside the Dec–Apr injury window — hold R1 hard.")
    return "\n".join(out)


def cmd_weeks(lab: Lab, arg: str | None = None) -> str:
    return render.weeks_table(_tail(lab.weeks, arg, 16))


def cmd_months(lab: Lab, arg: str | None = None) -> str:
    return render.months_table(_tail(lab.months, arg, len(lab.months)))


def cmd_seasons(lab: Lab, _arg: str | None = None) -> str:
    return render.seasons_table(lab.seasons)


def cmd_plan(lab: Lab, _arg: str | None = None) -> str:
    return render.plan_table(lab.by_start)


def cmd_diary(lab: Lab, arg: str | None = None) -> str:
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


def cmd_hills(lab: Lab, _arg: str | None = None) -> str:
    return render.hills_block(quality.hill_sessions(lab.ds))


def cmd_segments(lab: Lab, _arg: str | None = None) -> str:
    return render.segments_block(quality.segment_history(lab.ds))


def cmd_reps(_lab: Lab, _arg: str | None = None) -> str:
    return render.reps_block(quality.rep_sessions())


def cmd_site(lab: Lab, arg: str | None = None) -> str:
    """Write the diary page's payload to web/src/payload.json.

    Pages cannot run tl (the CSVs never leave this machine), so the React app
    builds from this committed file. The diary starts the week before the
    macrocycle opens, so the entries lead in with week 1's setup.
    """
    out = arg or config.DATA.parent / "web" / "src" / "payload.json"
    obj = export.web_payload(lab.ds, lab.weeks, lab.entries, lab.months, lab.seasons, lab.fitness)
    with open(out, "w") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return (
        f"wrote {out}  ({Path(out).stat().st_size // 1024} KB, "
        f"{len(obj['diary'])} diary weeks, {len(obj['months'])} months)"
    )


def cmd_export(lab: Lab, arg: str | None = None) -> str:
    path = arg or config.path("diary.json")
    obj = export.payload(lab.ds, lab.entries, lab.months, lab.seasons)
    export.write(obj, path)
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


def main(argv: list[str] | None = None) -> int:
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
