# Training log

The week-by-week decisions Dan and an agent agree on: how the close week went, what
the next week looks like day by day, and any change to the weekly volumes in
`tl/plan.py`. `tl/plan.py` holds the numbers; this file holds the agreed days and the
reasons the numbers moved. Agents read it before prescribing anything and append to it
once a week is agreed.

## How to use it

- **Date first.** Run `TZ=Europe/Prague date`; orbs run on UTC. Weeks run Monday to
  Sunday. The *close week* is the one that ended last Sunday, or the current one when
  today is Sunday; the *next week* starts on the following Monday. Find their plan rows
  in `tl/plan.py` and the actual numbers with `uv run tl status`, or in
  `data/diary.json` (`today`, `weeks`, `plan`) when the cache is not on this machine.
- **Newest week on top.** One `##` section per week, headed by its Monday. Keep older
  sections as they were written; correct them with a dated line, not by rewriting.
- **Numbers come from `tl`.** Quote actual hours, km and vert from `tl`, never estimate
  them. Check every proposal against the guardrails (R1 week-over-week ≤ 1.25×, R2
  ACWR ≤ 1.30, R3 vert floor, R4, R6) before writing it down.
- **Volume changes are Dan's call.** Propose, discuss, and only once Dan agrees edit the
  row in `tl/plan.py` and record old → new with the reason under *Plan changes*.
- **Open** lists what is not settled yet; clear it once it is agreed.

## Template

```markdown
## Week of YYYY-MM-DD · plan wk N (Pn)

**Close week (YYYY-MM-DD):** actual run h / km / vert vs plan, long run, guardrail
flags, how Dan felt.

**Agreed for this week:** run h, bike h, gym h, km, vert.

| day | session |
|---|---|
| Mon | |
| Tue | |
| Wed | |
| Thu | |
| Fri | |
| Sat | |
| Sun | |

**Plan changes:** `tl/plan.py` wk N run_h 6.5 → 5.0 (reason).

**Open:** questions still to settle.
```

## Week of 2026-11-02 · plan wk 10 (P2)

**Close week (2026-10-26):** 3.6 h running, 38.9 km, 653 m vert (183 m/h); plan wk 9
asked for 5.5 h run, 2.5 h bike, 1.0 h gym and a 2:00 long run. Longest run 70 min.
No bike sessions; total 4.7 h against 9 h. Week-over-week 0.61×, ACWR 0.68, the week
after Slapy 47K.

**Agreed for this week:** not yet.

**Plan changes:** none yet.

**Open:**
- The plan row asks for 6.5 h running, 1.82× the close week. R1 caps the jump at
  1.25×, about 4.5 h. Decide whether wk 10 drops to around 4.5 h and how wk 11–13
  (7.0 / 7.5 / 7.0 h) ramp back up.
- The day-by-day for the week, including the 2:30 long run.
