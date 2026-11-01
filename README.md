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
| This week | running hours against the plan, km, climb, climb density and the weekend's planned long run |
| Training guardrails | the five guardrails for the current week, each with its last six weeks |
| Fitness & form | fitness (CTL), fatigue (ATL) and form (CTL − ATL) over the last 12 weeks |
| The 29-week plan | planned against actual running hours for every week, its phases and race weeks; beyond 8 weeks, bands instead of numbers |
| Heart-rate zones by phase | running time per HR zone for each phase so far |
| Weekly diary | one entry per week since the plan started: sessions, notes, plan comparison and verdicts |
| Every month since 2023 | a heatmap of monthly running hours, with details per month |
| Week ledger | the last 26 weeks with ratios and guardrail flags |

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
    cd web && bunx playwright test          # e2e on the built page

## Workflow after a session

1. Append to `data/activities.csv`, `labels.csv`, `re.csv`, `hr.csv` — never
   re-pull history. On a day with several runs, write one `labels.csv` /
   `re.csv` row per run in the same order as `activities.csv`; `hr.csv` rows are
   matched to runs by duration.
2. Session notes go in `data/notes.csv` (`date,name,note`).
3. `uv run python scripts/fetch_zones.py` appends HR-zone seconds for new
   plan-period runs to `zones.csv` from their Strava HR streams (needs
   `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET` and a refresh token with
   `activity:read_all`). Runs without a row fall back to their average HR.
4. After an uphill session, extend `hills.csv` and `segments.csv`.
5. `uv run tl status` to check, `uv run tl site` to rebuild the payload, then
   commit and push `web/src/payload.json`; the Pages workflow publishes it.

## Guardrails encoded

Every threshold is a constant in `tl/config.py`, drawn from Dan's own injury
history.

| rule | limit | `tl/config.py` | why, from Dan's record |
|---|---|---|---|
| R1 | week-over-week running hours ≤ 1.25× | `WOW_CAP` | the single strongest injury predictor in the record |
| R2 | acute:chronic running hours (1 wk : 4 wk) ≤ 1.30 | `ACWR_CAP` | |
| R3 | ≥ 300 m of climb per running hour on weeks over 8 h | `VERT_FLOOR`, `BIG_WEEK_H` | flat volume is the mechanism behind the calf and shin failures |
| R4 | no *flat* interval or repetition work | `BANNED_TYPES` | uphill reps carry the intent of the rule and are not flagged |
| R6 | ≤ 100 km of running per week | `KM_CEILING` | |
| Dec–Apr | big weeks in these months are called out | `RISK_MONTHS` | six of nine overuse onsets fall in that window |
