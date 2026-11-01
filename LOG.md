# Training log

Dan's week-by-week training decisions, the record he and an agent work from. Dan plans
the training; the agent's job is to check it, not to write it: it brings the numbers
from `tl`, checks Dan's intentions against the guardrails and the plan, and says plainly
what fails and why. `tl/plan.py` holds the week-level numbers; this file holds Dan's
reasons for changing them and the days he settles on.

## How to use it

- **Date first.** Run `TZ=Europe/Prague date`; orbs run on UTC. Weeks run Monday to
  Sunday. The *close week* is the one that ended last Sunday, or the current one when
  today is Sunday; the *next week* starts on the following Monday. Find their plan rows
  in `tl/plan.py` and the actual numbers with `uv run tl status`, or in
  `data/diary.json` (`today`, `weeks`, `plan`) when the cache is not on this machine.
- **Dan decides, the agent checks.** Write down what Dan says he wants, in his words.
  Check it against R1 (week-over-week ≤ 1.25×), R2 (ACWR ≤ 1.44 against the 4 weeks before), R3, R4, R6 and the
  plan, and report the result with the numbers behind it. When something fails, say by
  how much and what would pass. Don't hand Dan a ready-made week he didn't ask for.
- **Numbers come from `tl`.** Quote actual hours, km and vert from `tl`, never estimate
  them. If a check disagrees with what Dan knows about his training, look at `tl`
  first: the log is how its numbers and guardrails get validated.
- **Plan changes.** When Dan changes a week, edit its row in `tl/plan.py` and record
  old → new with his reason under *Plan changes*.
- **Newest week on top.** One `##` section per week, headed by its Monday. Keep older
  sections as written; correct them with a dated line. **Open** lists what Dan hasn't
  decided yet.

## Template

```markdown
## Week of YYYY-MM-DD · plan wk N (Pn)

**Close week (YYYY-MM-DD):** actual run h / km / vert vs plan, long run, guardrail
flags, and how Dan felt about it.

**Dan's plan:** what Dan intends this week, in his words, with any day-by-day he fixes.

**Checks:** each guardrail and the plan row against Dan's plan: passes, or fails by how much.

**Plan changes:** `tl/plan.py` wk N run_h 6.5 → 5.0 (Dan's reason).

**Open:** what Dan hasn't decided yet.
```

## Week of 2026-11-02 · plan wk 10 (P2)

**Close week (2026-10-26):** 3.6 h running, 38.9 km, 653 m vert (183 m/h); no bike or
gym. Longest run 70 min. The first week after Slapy 47K (24 Oct).

**Dan's plan:** "Two weeks after Slapy are my off-season, I'm aiming for ~40k of
running with no extra cross-training." That covers wk 9 (26 Oct) and wk 10 (2 Nov).

**Checks:**
- Wk 9 fits it: 38.9 km, no cross-training.
- Wk 10 at ~40 km (~3.5 h at wk 9's 5:30/km) is WoW ~1.0× and ACWR ~0.8: no flags.
- Wk 11's row (7.0 h running, "A · 2:30+2:00") would fail after a 3.5 h week: R1 at
  2.0× (the cap allows ~4.4 h) and R2 at ~1.41 (mean of 5.85, 3.57, 3.5, 7.0 h). Wk 12
  (7.5 h) and wk 13 (7.0 h) need checking against whatever wk 11 becomes.

**Plan changes:**
- `tl/plan.py` wk 9: 9 h total, 5.5 run, 2.5 bike, 1.0 gym, "Long 2:00" → 3.5 h run
  only, "Off-season · easy" (Dan's off-season).
- `tl/plan.py` wk 10: 11 h total, 6.5 run, 2.5 bike, 2.0 gym, "Long 2:30" → 3.5 h run
  only, "Off-season · easy" (Dan's off-season).
- P2 published totals 427 km / 12,500 m → 371 km / 10,850 m: the cut hours times the
  phase's own 11.24 km/h and 329 m/h. Otherwise `_build` would spread the old totals
  over the remaining P2 weeks; wk 8 and wk 11–13 keep their targets.

**Open:**
- How Dan returns from the off-season in wk 11–13 (currently 7.0 / 7.5 / 7.0 h running
  with 2 h bike and 2 h gym), given the R1 and R2 checks above. Ramps suggested while
  working out how to encode the off-season are in [Claude Fable's](https://ampcode.com/threads/T-01a197fb-7ab3-77f6-9458-97685581d6b1)
  and [Gemini Argon's](https://ampcode.com/threads/T-01a197fb-86eb-71ce-b0fc-fe456016dc44)
  threads; neither is adopted.
