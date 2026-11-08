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

## Week of 2026-11-09 · plan wk 11 (P2)

**Close week (2026-11-02), checked 8 Nov before Sunday's run:** fresh incremental
Strava pull found 2 h 47 min 30 sec running / 32.20 km / 412 m climb, plus 58 min
22 sec gym. Longest run 90 min. Dan plans another ~8 km to finish around 40 km;
that run is not yet recorded, so the final weekly hours remain open.

**Dan's plan:** "60k mainly Z1/Z2, 1 strides + 1 weekend long; 2 gym sessions;
2 cycling training." No uphill tempo. Cycling remains the agreed 2×1 h easy
aerobic. Keep the existing 2 h gym budget across two sessions. Running is 60 km;
5.25 h is only a planning estimate (5:15/km), not a pace prescription or time cap.
No day-by-day schedule or fixed long-run duration has been chosen.

**Checks:**
- R1: if Sunday's run takes 40–45 min, W10 ends at 3.46–3.54 h. W11's estimated
  5.25 h gives 1.48–1.52×, above 1.25×; the passing ceiling would be 4 h 19–25 min.
  Dan chose 60 km after this warning; the threshold is not relaxed and the plan
  is not being described as medically safe.
- R2: approximately 1.17–1.18, below 1.44, using W7–9's exported 4.93 / 5.85 /
  3.57 h and W10's projected finish (the baseline is W7–10). Final checks require
  Sunday's actual duration and next week's actual running hours.
- R3 does not bind at the estimated 5.25 h; no vert quota is adopted. R6: 60 km
  is below 100 km. November is outside the Dec–Apr risk window.
- R4 remains unchanged: no flat I/R workout. Strides are not prescribed as an
  interval session; duration, repetitions and effort remain to be settled.

**Plan changes:** W11 7.0 → 5.25 estimated run h; derived 78.6 → fixed 60 km;
2,302 m → no vert target; back-to-back 2:30+2:00 → one weekend long. Bike and gym
remain 2 h each, in two sessions each; total 11 → 9.25 h. W11 explicitly skips
P2's uphill tempo and hill-sprint suggestions in favour of one strides session.
P2 totals 372 km / 8,550 m → 353.4 km / 6,248 m, removing W11's old allocation
without increasing the other weeks' targets at display precision.

**Open:** Sunday's actual run; long-run and strides details; gym-session duration
split and content. W12's unchanged 7.5 h would be 1.43× after a 5.25 h W11, so it
still needs review rather than automatic adoption.

## Week of 2026-11-02 · plan wk 10 (P2)

**Close week (2026-10-26):** 3.6 h running, 38.9 km, 653 m vert (183 m/h); no bike or
gym. Longest run 70 min. The first week after Slapy 47K (24 Oct).

**Dan's plan:** "Two weeks after Slapy are my off-season, I'm aiming for ~40k of
running with no extra cross-training." Then: "40 km, 4 hour target, no vert target, no
long." That covers wk 9 (26 Oct) and wk 10 (2 Nov).

**Checks** (R2 is now the week over the mean of the 4 weeks before, cap 1.44):
- Wk 9 fits it: 3.6 h, 38.9 km, no cross-training.
- Wk 10 at 4.0 h is WoW 1.12× over wk 9's 3.57 h and ACWR 0.76 over wk 6–9 (6.77,
  4.93, 5.85, 3.57 h): no flags.
- Wk 11's row (7.0 h running, "A · 2:30+2:00") would fail after a 4.0 h wk 10: R1 at
  1.75× (the cap allows 5.0 h) and R2 at 1.53 over wk 7–10 (4.93, 5.85, 3.57, 4.0 h;
  the cap allows 6.6 h). Both limits move with what wk 10 actually comes in at. Wk 12
  (7.5 h) and wk 13 (7.0 h) need checking against whatever wk 11 becomes.

**Plan changes:**
- `tl/plan.py` wk 9 and wk 10 (were 9 h / 5.5 run / 2.5 bike / 1.0 gym / "Long 2:00"
  and 11 h / 6.5 / 2.5 / 2.0 / "Long 2:30") → 4 h running only, 40 km, no vert target,
  "Off-season · no long run". The 40 km sits in `OWN_KM` and is kept out of P2's km/vert
  split.
- P2 published totals 427 km / 12,500 m → 372 km / 8,550 m, so wk 8 and wk 11–13 keep
  their km and vert targets (the off-season weeks carry 80 km and no vert).

**Chianti goal (set 2026-11-02):** UTMB index ≥ 700, 720+ if the back half holds. Dan
first put it at 720–750 and Slapy 47K at ~780; the utmb.world data says otherwise. His
record there is 100K index 665 (Lavaredo 80K, 10:20:23), and Slapy 2026 is not yet
scored: fitting the 2025 Slapy finishers maps 3:59:57 to ~700–725. A log-time fit of
UTCC 2026 finishers whose only indexed 100M result is that race (n = 81, residual sd
3–4 pts), scaled 1.029× for the 2027 course (123 km / 5200 m), gives: 650 ≈ 14:20,
665 ≈ 14:00, 700 ≈ 13:20, 720 ≈ 12:57, 750 ≈ 12:25. The formula is private, so these
are estimates, ±10 min. 720–750 means 10–15 % faster than his Lavaredo-level decay
over 123 km, so it hangs on the back half: 4–5 h longs with 350–450 m/h, back-to-back
weekends, one 60–75 km rehearsal at 80–90 g/h, pre-dawn kit runs for the 04:00 start.
Workings in [this thread](https://ampcode.com/threads/T-01a19750-5309-73cb-bc24-fc9dd100d866).

**Open:**
- How Dan returns from the off-season in wk 11–13 (currently 7.0 / 7.5 / 7.0 h running
  with 2 h bike and 2 h gym), given the R1 and R2 checks above. Ramps suggested while
  working out how to encode the off-season are in [Claude Fable's](https://ampcode.com/threads/T-01a197fb-7ab3-77f6-9458-97685581d6b1)
  and [Gemini Argon's](https://ampcode.com/threads/T-01a197fb-86eb-71ce-b0fc-fe456016dc44)
  threads; neither is adopted.
