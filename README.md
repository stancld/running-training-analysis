# Training Logbook

[![Current focus: Chianti 120K by UTMB · 20 Mar 2027](https://img.shields.io/badge/current_focus-Chianti_120K_by_UTMB_%C2%B7_20_Mar_2027-2f5d63)](https://stancld.github.io/running-training-analysis/)

Dan's training logbook, and `tl`, the dependency-free Python package that builds
it from his local Strava/COROS cache. The current focus is the Chianti 120K by
UTMB (Ultra Trail Chianti Castles, 20 March 2027).

**Read it:** https://stancld.github.io/running-training-analysis/ (public by
link, `noindex`).

## The diary

A React app under `web/`, built from the JSON payload `tl` writes. Everything on
it is derived from the cache except Dan's own session notes.

| section | what it shows |
|---|---|
| This week | running hours against the plan, km, climb, climb density, the weekend's planned long run, a link to the phase's quality sessions and next week's plan targets |
| Training guardrails | the five guardrails for the current week, each with its last six weeks, as ok, watch (R3 under the floor on a week the rule does not cover) or flag |
| Fitness & form | fitness (CTL), fatigue (ATL) and form (yesterday's CTL − ATL, as in the TrainingPeaks PMC) over the last 12 weeks |
| The 29-week plan | planned against actual running hours for every week, its phases and race weeks; beyond 8 weeks, bands instead of numbers. The selected week also lists its phase's suggested quality sessions (`plan.QUALITY`, Kilian Jornet's uphill-first approach), with the reasoning and sources folded away |
| Heart-rate zones by phase | time per HR zone for each phase, opening into weekly columns; Running or Total (runs plus rides, with ride power zones) |
| Weekly diary | one entry per week since the plan started: sessions, notes, plan comparison and verdicts |
| Every month since 2023 | monthly running hours or climb density (m/h) as a trend line and a heatmap, with injury months, Dec–Apr risk months and yearly totals; each month opens into its stats, sport split and the same month in other years |
| Week ledger | the last 26 weeks with the same ok / watch / flag status, ratios and volumes |

## Running tl

The CSV cache in `data/` is personal and gitignored, so a fresh clone has no
data. Set up once with `uv sync`.

    uv run tl                     status + weeks + plan + diary
    uv run tl status              where the prep stands today
    uv run tl weeks 20 | all      week map
    uv run tl months | seasons    month and season maps
    uv run tl plan                29-week macrocycle vs what happened
    uv run tl diary 4 | all | DATE
    uv run tl hills | segments | reps
    uv run tl export [path]       full JSON dump (data/diary.json)
    uv run tl site                write web/src/payload.json
    uv run pytest                 e2e: a temp cache through `tl site` (never touches data/)

## Working on the page

GitHub Pages cannot run `tl`, so it builds the app from the committed payload.

    cd web && bun install && bun run dev    # live preview; reloads when tl site rewrites the payload
    cd web && bun run build                 # type-check and build web/dist, as Pages does
    cd web && bun run lint                  # Biome lint + format check; `bun run format` fixes; husky runs it on commit
    cd web && bunx playwright test          # e2e on the built page

Weeks are named by plan week (W1–W29) and dates, with the ISO week as secondary
text. On a phone each tab has its own URL hash (`#today`, `#plan`, `#diary`,
`#history`); every section also has an anchor (`#rails`, `#quality`, `#ledger`, …)
that the laptop's jump bar uses.

## Workflow after a session

1. Append to `data/activities.csv`, `labels.csv`, `re.csv`, `hr.csv` — never
   re-pull history. On a day with several runs, write one `labels.csv` /
   `re.csv` row per run in the same order as `activities.csv`; `hr.csv` rows are
   matched to runs by duration.
2. Session notes go in `data/notes.csv` (`date,name,note`).
3. `uv run python scripts/fetch_zones.py` appends zone seconds for new
   plan-period runs to `zones.csv` and rides (HR and power) to `ride_zones.csv`
   from their Strava streams (needs
   `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET` and a refresh token with
   `activity:read_all`). Runs without a row fall back to their average HR.
4. After an uphill session, extend `hills.csv` and `segments.csv`.
5. `uv run tl status` to check, `uv run tl site` to rebuild the payload, then
   commit and push `web/src/payload.json`; the Pages workflow publishes it.
6. Once a week, review the close week with an agent in `LOG.md`: Dan plans the next
   one, the agent checks it against the guardrails, and his volume changes go into
   `tl/plan.py`.

### From an Amp orb

GitHub Actions cannot recalculate the page because the cache never leaves Dan's
machine. An Amp orb can run the same workflow on a copy of the cache:

1. Append the session to the CSVs locally (steps 1–2 above) and upload the whole
   cache into the orb's `data/`. A fresh orb has no CSVs.
2. `uv run python scripts/fetch_zones.py` reads `STRAVA_CLIENT_ID`,
   `STRAVA_CLIENT_SECRET` and `STRAVA_REFRESH_TOKEN` from the orb's environment,
   set as Amp secrets. If Strava rotates the token, the new one lands only in
   the orb's `~/.config/tl/strava_refresh_token`, so update the secret with it.
3. `uv run tl status`, `uv run tl site`, `uv run pytest`, then commit and push
   only `web/src/payload.json`; the CSVs stay gitignored.
4. Download the updated `zones.csv` and `ride_zones.csv` back to Dan's machine;
   the orb's copy of the cache is not kept anywhere else.

## Guardrails encoded

Every threshold is a constant in `tl/config.py`, drawn from Dan's own injury
history.

| rule | limit | `tl/config.py` | why, from Dan's record |
|---|---|---|---|
| R1 | week-over-week running hours ≤ 1.25× | `WOW_CAP` | the single strongest injury predictor in the record |
| R2 | acute:chronic running hours (the week : mean of the 4 before it) ≤ 1.44 | `ACWR_CAP` | uncoupled, so the week does not dilute its own baseline; as strict as the old coupled 1 wk : 4 wk ≤ 1.30 |
| R3 | ≥ 300 m of climb per running hour on weeks over 8 h | `VERT_FLOOR`, `BIG_WEEK_H` | flat volume is the mechanism behind the calf and shin failures |
| R4 | no *flat* interval or repetition work | `BANNED_TYPES` | uphill reps carry the intent of the rule and are not flagged |
| R6 | ≤ 100 km of running per week | `KM_CEILING` | |
| Dec–Apr | big weeks in these months are called out | `RISK_MONTHS` | six of nine overuse onsets fall in that window |
