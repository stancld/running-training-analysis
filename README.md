# Training Logbook

[![Current focus: Chianti 120K by UTMB · 20 Mar 2027](https://img.shields.io/badge/current_focus-Chianti_120K_by_UTMB_%C2%B7_20_Mar_2027-2f5d63)](https://stancld.github.io/running-training-analysis/)

Dan's training logbook, and `tl`, the dependency-free Python package that builds
it from his local Strava/COROS cache. The current focus is the Chianti 120K by
UTMB (Ultra Trail Chianti Castles, 20 March 2027), shown as a badge on the page.

**Read it:** https://stancld.github.io/running-training-analysis/. The page is
public by link and marked `noindex`, so search engines don't list it.

## The diary

A small React app (Vite + TypeScript, under `web/`) built from a JSON payload
that `tl` writes every time the cache is topped up. On a laptop it is a
dashboard grid; on a phone it is an app with Today, Plan, Diary and History tabs.


| section | what it shows |
|---|---|
| This week | running hours against the plan, km, climb, m/h of climb density and the weekend's planned long run |
| Training guardrails | the five guardrails (WoW, ACWR, climb density, no flat intervals, weekly km) for the current week, each with its last six weeks |
| Fitness & form | fitness (CTL), fatigue (ATL) and form (CTL − ATL) day by day over the last 12 weeks |
| The 29-week plan | planned against actual running hours for every week of the macrocycle, its five phases, race weeks, and the 8-week horizon: weeks beyond it are bands, not numbers |
| Heart-rate zones by phase | running time per HR zone (Dan's Strava zones, `HR_ZONES` in `tl/config.py`) for each phase so far; each run counts whole in the zone of its average HR, since the cache has no HR streams |
| Weekly diary | one collapsible entry per week since the plan started: day-by-day sessions, Dan's notes, the plan comparison and the derived verdicts |
| Every month since 2023 | a heatmap of monthly running hours; hover or tap a month for its volume, climb, longest run, easy/long HR and pace, and feel |
| Week ledger | the last 26 weeks with ratios and guardrail flags |

Everything on the page is derived from the cache. Nothing is written by hand
except Dan's own session notes.

## The package

`tl` maps the whole history onto weeks, months and seasons, scores every week
against the injury guardrails, compares actuals with the macrocycle and writes
the page's payload to `web/src/payload.json`. The CSV cache in `data/` is personal and
stays on Dan's machine; it is gitignored, so a fresh clone has no data.

### Use

Set up once with `uv sync`, which installs Python 3.14 and the dev tools
(pre-commit with Ruff, and the ty type checker: `uv run ty check`).

    uv run tl                     status + weeks + plan + diary
    uv run tl status              where the prep stands today
    uv run tl weeks 20 | all      week map
    uv run tl months | seasons    month and season maps
    uv run tl plan                29-week macrocycle vs what happened
    uv run tl diary 4 | all | DATE
    uv run tl hills | segments | reps
    uv run tl export [path]       full JSON dump (data/diary.json)
    uv run tl site                write web/src/payload.json; pushing it publishes the page
    uv run pytest                 e2e: a temp cache through `tl site` (never touches data/)

### Layout

| module | what it holds |
|---|---|
| `config.py` | paths, sport taxonomy, guardrail thresholds, the HR and load models |
| `data.py` | loads the CSVs into `Activity` objects; attaches type/feel/RE/HR/notes |
| `periods.py` | `Week` / `Month` / `Season`, ACWR, WoW, density, CTL/ATL/TSB, monotony |
| `plan.py` | the Chianti macrocycle as data — 29 weeks, 5 phases, per-week targets |
| `diary.py` | one derived `Entry` per week: day log, plan comparison, verdicts |
| `quality.py` | uphill reps (VAM, power:HR decoupling), repeated segments, 1k reps |
| `render.py` | terminal tables |
| `export.py` | JSON for the diary page |
| `cli.py` | commands |

### The page

The CSVs never leave Dan's machine, so GitHub Pages cannot run `tl`; it builds
the app from the committed payload instead. To work on the page:

    cd web && bun install && bun run dev    # live preview; reloads when tl site rewrites the payload
    cd web && bun run build                 # type-check and build web/dist, as Pages does
    cd web && bunx playwright test          # e2e on the built page; CI runs it on a synthetic cache

## Workflow after a session

1. Append to `data/activities.csv`, `labels.csv`, `re.csv`, `hr.csv` — never
   re-pull history, it costs ~12k tokens per 100 activities. On a day with
   several runs, write one `labels.csv` / `re.csv` row per run in the same order
   as `activities.csv`; `hr.csv` rows are matched to runs by duration.
2. Session notes worth keeping go in `data/notes.csv` (`date,name,note`);
   rows for one day are matched to that day's activities runs-first, then by
   duration.
3. `uv run python scripts/fetch_zones.py` appends HR-zone seconds for new
   plan-period runs to `zones.csv` from their Strava HR streams (needs
   `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET` and a refresh token with
   `activity:read_all`). Runs without a row fall back to their average HR.
4. After an uphill session, extend `hills.csv` and `segments.csv` — Strava
   `get_activity_performance` returns laps and segment efforts with per-rep HR
   and watts in one call.
5. `uv run tl status` to check, `uv run tl site` to rebuild the payload, then
   commit and push `web/src/payload.json`. The Pages workflow builds the app
   with Bun and publishes it to
   https://stancld.github.io/running-training-analysis/ — readable by link,
   `noindex` for search engines.

## Guardrails encoded

Every threshold is a constant in `tl/config.py`; change it there and the CLI,
the flags and the page all follow. They come from Dan's own injury history, not
textbook defaults.

| rule | limit | `tl/config.py` | why, from Dan's record |
|---|---|---|---|
| R1 | week-over-week running hours ≤ 1.25× | `WOW_CAP` | the single strongest injury predictor in the record |
| R2 | acute:chronic running hours (1 wk : 4 wk) ≤ 1.30 | `ACWR_CAP` | |
| R3 | ≥ 300 m of climb per running hour on weeks over 8 h | `VERT_FLOOR`, `BIG_WEEK_H` | flat volume is the mechanism behind the calf and shin failures |
| R4 | no *flat* interval or repetition work | `BANNED_TYPES` | uphill reps carry the intent of the rule and are not flagged |
| R6 | ≤ 100 km of running per week | `KM_CEILING` | |
| Dec–Apr | big weeks in these months are called out | `RISK_MONTHS` | six of nine overuse onsets fall in that window |
