---
description: Top up the training cache from Strava/COROS, evaluate the week, rebuild and publish the Chianti logbook
---

Weekly training review for Dan. Work in `/Users/stancld/projects/running-training-analysis`.

1. **Find the gap.** `tail -3 data/activities.csv` for the last cached date, and
   `uv run tl status` for the staleness line.
2. **Fetch only what is missing.** `mcp__strava__list_activities` (per_page small —
   bulk pulls cost ~12k tokens per 100 activities). Append one row per activity to
   `data/activities.csv` (`date,sport,km,min,vert`; minutes = moving_time).
   Treadmill/indoor runs record vert 0 on Strava — enter the real climb by hand from
   the activity description and say so in the note.
3. **Top up the sidecars** for the new days: `labels.csv` (`date,type,feel` — Daniels
   E/L/T/I/R/M/F/S/RACE, feel −2..+2 from his own description), `re.csv` (Strava
   relative_effort, runs only), `hr.csv` (`date,min,hr` — COROS avg HR via
   `mcp__coros__querySportRecords`), `notes.csv` (`date,name,note`).
4. **Pull recovery context** for the week: `queryTrainingLoadAssessment`,
   `queryRestingHeartRate`, `queryAvgHeartRate`. Use `querySleepHrv` sparingly — its
   time series is enormous; the daily assessment lines are what matter. A same-day
   COROS reading can lag the phone app by hours — his app wins.
5. **Check what was already agreed.** The day-by-day plan for the coming week is
   decided in conversation and lives only in the session transcripts under
   `~/.claude/projects/-Users-stancld-projects-training/*.jsonl` — `tl/plan.py` carries
   week-level targets only. Grep those transcripts before prescribing anything, and if a
   week was already agreed, print that one.
6. **Evaluate.** `uv run tl status`, `weeks 6`, `diary 1`, `plan`. Judge the week on:
   plan vs actual (run h, vert, weekend long), the R1–R7 guardrails, CTL/ATL/form and
   monotony, the quality session's HR/power against LTHR 176, and what next week's plan
   row asks for. Flag anything that pushes the week-over-week running jump past 1.25×.
7. **Publish.** `uv run tl site`, then commit and push `web/diary.html` to `master`.
   The Pages workflow deploys it to https://stancld.github.io/running-training-analysis/.
8. **Report** in the terminal: what happened, what it means, and the call for next week.
