"""Terminal rendering. Plain ASCII tables, tabular numbers, no dependencies."""

import datetime as dt
from typing import TYPE_CHECKING, Any

from tl import config, plan

if TYPE_CHECKING:
    from tl.diary import Entry
    from tl.periods import Month, Season, Week

W = 100


def title(text: str, ch: str = "=") -> str:
    return f"\n{ch * W}\n{text}\n{ch * W}"


def mmss(s: float) -> str:
    t = round(s)
    return f"{t // 60}:{t % 60:02d}"


def hmm(hours: float) -> str:
    m = round(hours * 60)
    return f"{m // 60}:{m % 60:02d}"


def rng(bands: dict[str, tuple[float, float]], f: str, fmt: str = "{:.1f}") -> str:
    lo, hi = bands[f]
    return f"{fmt.format(lo)}–{fmt.format(hi)}"


def _opt(x: float | None, fmt: str = "{:.0f}", dash: str = "-", width: int = 6) -> str:
    """Format a value that may be absent, right-aligned to `width`."""
    return f"{(fmt.format(x) if x is not None else dash):>{width}}"


def weeks_table(weeks: list[Week]) -> str:
    lines = [title("WEEKS — Monday-start, every week in range")]
    lines.append(
        f"{'week':11} {'start':11} {'run h':>6} {'km':>6} {'vert':>6} {'m/h':>5} "
        f"{'bike':>5} {'gym':>4} {'tot':>5} {'WoW':>5} {'ACWR':>5} {'d':>2}"
        f" {'plan':>5} {'%':>5}  flags"
    )
    for w in weeks:
        p = plan.week_for(w.start)
        f = [f"{c}:{m}" for c, m in w.flags()]
        if w.current:
            f.insert(0, f"current, through {config.TODAY}")
        row = (
            f"{w.label:11} {w.start!s:11} {w.run_h:6.1f} {w.run_km:6.1f} "
            f"{w.run_vert:6.0f} {w.density:5.0f} {w.bike_h:5.1f} {w.gym_h:4.1f} "
            f"{w.total_h:5.1f} {_opt(w.wow, '{:.2f}', width=5)} "
            f"{_opt(w.acwr, '{:.2f}', width=5)} {w.run_days:2d}"
        )
        if p:
            pct = w.run_h / p.run_h * 100 if p.run_h else 0
            row += f" {p.run_h:5.1f} {pct:4.0f}%"
        else:
            row += f" {'-':>5} {'-':>5}"
        lines.append(row + "  " + ("; ".join(f) if f else "ok"))
    lines.append(
        f"\n  Guardrails: WoW <= {config.WOW_CAP}x, ACWR <= {config.ACWR_CAP}, "
        f">= {config.VERT_FLOOR} m/h above {config.BIG_WEEK_H} h, "
        f"<= {config.KM_CEILING:.0f} km/wk, no flat I/R."
    )
    return "\n".join(lines)


def months_table(months: list[Month]) -> str:
    lines = [title("MONTHS — the full history, one row per calendar month")]
    lines.append(
        f"{'month':9} {'run h':>6} {'km':>7} {'vert':>7} {'m/h':>5} {'days':>5} "
        f"{'long':>6} {'bike h':>7} {'gym h':>6} {'tot h':>6} {'E/L HR':>7} "
        f"{'pace':>6} {'feel':>5}"
    )
    for m in months:
        a = m.hr_at_pace()
        lr = m.longest_run
        lines.append(
            f"{m.label:9} {m.run_h:6.1f} {m.run_km:7.1f} {m.run_vert:7.0f} "
            f"{m.density:5.0f} {m.run_days:5d} {hmm(lr.mins / 60) if lr else '-':>6} "
            f"{m.bike_h:7.1f} {m.gym_h:6.1f} {m.total_h:6.1f} "
            f"{_opt(a['hr'] if a else None, '{:.1f}', width=7)} "
            f"{(mmss(a['pace'] * 60) if a else '-'):>6} "
            f"{_opt(m.mean_feel, '{:+.1f}', width=5)}"
        )
    lines.append(
        "\n  E/L HR is COROS-measured where available, else estimated from Strava"
        "\n  relative_effort (HR = 81.2 + 21.1*ln(RE/h), +-3.5 bpm). Read it "
        "against pace,\n  which is in the next column, and against m/h — terrain "
        "moves both."
    )
    return "\n".join(lines)


def seasons_table(seasons: list[Season]) -> str:
    lines = [title("SEASONS — calendar years, as Dan counts them")]
    lines.append(
        f"{'season':7} {'run h':>7} {'km':>8} {'vert':>8} {'m/h':>5} "
        f"{'run days':>9} {'bike h':>7} {'gym h':>6} {'total h':>8} "
        f"{'quality':>8} {'races':>6}"
    )
    for s in seasons:
        races = sum(1 for a in s.acts if a.sport == "RACE_Run" or a.type == "RACE")
        lines.append(
            f"{s.label:7} {s.run_h:7.1f} {s.run_km:8.1f} {s.run_vert:8.0f} "
            f"{s.density:5.0f} {s.run_days:9d} {s.bike_h:7.1f} {s.gym_h:6.1f} "
            f"{s.total_h:8.1f} {len(s.quality):8d} {races:6d}"
        )
    return "\n".join(lines)


def plan_table(weeks_by_start: dict[dt.date, Week]) -> str:
    lines = [title(f"MACROCYCLE — {plan.RACE_NAME}, {plan.RACE:%d %b %Y}")]
    lines.append(
        f"  Written week by week to {plan.horizon_date():%d %b %Y} "
        f"({plan.HORIZON_WEEKS} weeks out); beyond that each phase carries a "
        f"band, not a number.\n"
    )
    lines.append(
        f"{'#':>3} {'ph':>3} {'week':11} {'run':>5} {'act':>5} {'%':>5} "
        f"{'bike':>5} {'act':>5} {'gym':>4} {'act':>4} {'km':>5} {'act':>5} "
        f"{'vert':>5} {'act':>5}  weekend"
    )
    for p in plan.committed_weeks():
        a = weeks_by_start.get(p.start)
        ph, ah = _opt(p.run_h, "{:.1f}", width=5), _opt(a.run_h if a else None, "{:.1f}", width=5)
        pb, ab = _opt(p.bike_h, "{:.1f}", width=5), _opt(a.bike_h if a else None, "{:.1f}", width=5)
        pg, ag = _opt(p.gym_h, "{:.1f}", width=4), _opt(a.gym_h if a else None, "{:.1f}", width=4)
        pk, ak = _opt(p.run_km, width=5), _opt(a.run_km if a else None, width=5)
        pv, av = _opt(p.run_vert, width=5), _opt(a.run_vert if a else None, width=5)
        pct = f"{a.run_h / p.run_h * 100:4.0f}%" if a and p.run_h else "    -"
        mark = " <" if a and a.current else ""
        lines.append(
            f"{p.index:3d} {p.phase:>3} {p.start!s:11} {ph} {ah} {pct} "
            f"{pb} {ab} {pg} {ag} {pk} {ak} {pv} {av}  "
            f"{(p.race or p.weekend)}{mark}"
        )

    prov = plan.provisional_phases()
    if prov:
        lines.append(
            f"\n  PROVISIONAL — bands only, to be written week by week as each "
            f"block comes inside {plan.HORIZON_WEEKS} weeks"
        )
        lines.append(
            f"  {'ph':>3} {'weeks':>6} {'window':23} {'run h':>11} "
            f"{'bike h':>10} {'km':>11} {'vert':>13}  focus"
        )
        for q in prov:
            b = q["bands"]
            window = f"{q['start']:%d %b %Y} – {q['end']:%d %b %Y}"
            lines.append(
                f"  {q['phase']:>3} {q['weeks']:6d} {window:23} "
                f"{rng(b, 'run_h'):>11} {rng(b, 'bike_h'):>10} "
                f"{rng(b, 'run_km', '{:.0f}'):>11} "
                f"{rng(b, 'run_vert', '{:,.0f}'):>13}  {q['name']}"
            )
        lines.append(
            f"\n  Phase totals stay fixed ({', '.join(f'{c} {km:,} km / {v:,} m' for c, n, w, km, v in plan.PHASES)});"
        )
        lines.append("  only the week-by-week split inside a provisional phase is open.")
    tot_h = sum(p.run_h for p in plan.WEEKS)
    tot_km = sum(p.run_km for p in plan.WEEKS)
    tot_v = sum(p.run_vert or 0 for p in plan.WEEKS)
    lines.append(
        f"\n  29 weeks: {tot_h:.0f} h running, {tot_km:.0f} km, {tot_v:,.0f} m "
        f"of climb. {plan.weeks_to_race():.1f} weeks to the start line."
    )
    return "\n".join(lines)


def diary_entry(e: Entry) -> str:
    w = e.week
    head = f"{w.label}   {w.start:%d %b} – {w.end:%d %b %Y}"
    if e.plan:
        head += (
            f"   ·   plan week {e.plan.index}/29   ·   {e.plan.phase} "
            f"{plan.PHASE_NAME[e.plan.phase]}   ·   {e.plan.to_race} wk to race"
        )
    lines = [title(head, "-")]
    lines.append("  " + e.headline())
    if e.plan:
        lines.append(
            f"  Planned: {hmm(e.plan.total_h)} total · {e.plan.run_h:.1f} h run · "
            f"{e.plan.bike_h:.1f} h bike · {e.plan.gym_h:.1f} h gym · "
            f"weekend {e.plan.weekend}"
        )
    lines.append("")
    for name, d, acts in e.days():
        if not acts:
            lines.append(f"  {name} {d:%d/%m}  —  rest")
            continue
        first = True
        for a in acts:
            tag = f"[{a.type}]" if a.type else "   "
            label = a.name or a.sport
            lines.append(
                f"  {(name + ' ' + format(d, '%d/%m')) if first else '':<12} "
                f"{tag:>4} {label[:34]:<34} "
                f"{a.mins:5.0f}′ {a.km:6.1f} km {a.vert:5.0f} m"
                + (f"  feel {a.feel:+.0f}" if a.feel is not None else "")
            )
            first = False
    lines.append("")
    lines.extend("  · " + n for n in e.notes())
    hl = e.highlights()
    if hl:
        lines.append("")
        for d, name, note in hl:
            lines.append(f"  “{note}”  — {name}, {d:%d %b}")
    if e.fitness:
        lines.append("")
        lines.append(
            f"  Fitness {e.fitness['ctl']:.0f} · fatigue {e.fitness['atl']:.0f} · "
            f"form {e.fitness['tsb']:+.0f}" + (f"   ·   monotony {e.mono:.2f}" if e.mono else "")
        )
    return "\n".join(lines)


def hills_block(sessions: list[dict[str, Any]]) -> str:
    lines = [title("UPHILL QUALITY — vertical rate, HR drift and power:HR decoupling")]
    for s in sessions:
        lines.append(f"\n  {s['date']}  {s['name']}")
        lines.append(
            f"    {'rep':>3} {'dur':>6} {'dist':>7} {'vert':>6} {'grade':>6} "
            f"{'VAM':>7} {'speed':>7} {'HR':>6} {'W':>6} {'W/HR':>6}"
        )
        lines.extend(
            f"    {r['rep']:3d} {mmss(r['dur']):>6} {r['dist']:7.0f} "
            f"{r['vert']:6.0f} {r['grade']:5.1f}% {r['vam']:7.0f} "
            f"{r['speed']:6.1f}k {r['hr']:6.1f} "
            f"{_opt(r['watts'])} {_opt(r['w_per_hr'], '{:.3f}')}"
            for r in s["reps"]
        )
        lines.append(
            f"    -> mean VAM {s['mean_vam']:.0f} m/h, HR drift "
            f"{s['hr_drift']:+.1f} bpm across reps, peak {s['hr_peak']:.0f}"
        )
        if s["decoupling"] is not None:
            d = abs(s["decoupling"])
            g = "excellent" if d < 3 else "acceptable" if d < 5 else "large — too hard"
            lines.append(f"    -> power:HR decoupling {s['decoupling']:+.1f}%  ({g})")
    return "\n".join(lines)


def segments_block(segs: list[dict[str, Any]]) -> str:
    lines = [title("SAME-SEGMENT BENCHMARKS — identical hill, different days")]
    for s in segs:
        lines.append(
            f"\n  {s['segment']}  ({s['dist']:.0f} m, {s['vert']:.0f} m up, {s['grade']:.1f}%)"
        )
        lines.append(
            f"    {'date':11} {'context':12} {'rep':>3} {'time':>7} {'VAM':>7} "
            f"{'HR':>6} {'W':>6} {'m/beat':>7}"
        )
        lines.extend(
            f"    {e['date']:11} {e['context']:12} {e['rep']:3d} "
            f"{mmss(e['secs']):>7} {e['vam']:7.0f} {e['hr']:6.1f} "
            f"{_opt(e['watts'])} {e['m_per_beat']:7.2f}"
            for e in s["efforts"]
        )
        if len(s["by_context"]) > 1:
            items = sorted(s["by_context"].items(), key=lambda kv: kv[1])
            fast, slow = items[0], items[-1]
            lines.append(
                f"    -> {fast[0]} is {(slow[1] - fast[1]) / slow[1] * 100:.0f}% "
                f"faster than {slow[0]}"
            )
    return "\n".join(lines)


def reps_block(rows: list[dict[str, Any]]) -> str:
    lines = [title("FLAT THRESHOLD PROGRESSION — every logged 1k-rep session")]
    lines.append(
        f"{'date':11} {'session':24} {'rest':6} {'n':>3} {'avg':>7} "
        f"{'last3':>7} {'best':>6} {'fade':>7}"
    )
    lines.extend(
        f"{r['date']:11} {r['name'][:24]:24} {r['rest']:6} {r['n']:3d} "
        f"{mmss(r['avg']):>7} {mmss(r['last3']):>7} {mmss(r['best']):>6} "
        f"{r['fade']:+6.0f}s"
        for r in rows
    )
    return "\n".join(lines)
