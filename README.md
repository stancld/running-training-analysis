# Chianti Logbook

Dan's training diary for the Chianti 120K (Ultra Trail Chianti Castles, 20 March
2027), and `tl`, the dependency-free Python package that builds it from his local
Strava/COROS cache.

**Read it:** https://stancld.github.io/running-training-analysis/. The page is
public by link and marked `noindex`, so search engines don't list it.

## The diary

One self-contained page with the data built in, rebuilt every time the cache is
topped up. Top to bottom:

| section | what it shows |
|---|---|
| This week | running hours against the plan, km, climb, m/h of climb density, the weekend's planned long run, and the five guardrails (WoW, ACWR, climb density, weekly km, no flat intervals) for the current week |
| Fitness & form | fitness (CTL), fatigue (ATL) and form (CTL − ATL) day by day over the last 12 weeks |
| The 29-week plan | planned against actual running hours for every week of the macrocycle, its five phases, race weeks, and the 8-week horizon: weeks beyond it are bands, not numbers |
| Weekly diary | one collapsible entry per week since the plan started: day-by-day sessions, Dan's notes, the plan comparison and the derived verdicts |
| Every month since 2023 | a heatmap of monthly running hours plus a table of monthly volume, climb, longest run, easy/long HR and pace, and feel |
| Week ledger | the last 26 weeks with ratios and guardrail flags |

Everything on the page is derived from the cache. Nothing is written by hand
except Dan's own session notes.

## The package

`tl` maps the whole history onto weeks, months and seasons, scores every week
against the injury guardrails, compares actuals with the macrocycle and renders
the page from `web/diary.tmpl.html`. The CSV cache in `data/` is personal and
stays on Dan's machine; it is gitignored, so a fresh clone has no data.

### Use

Set up once with `uv sync`, which installs Python 3.14 and the dev tools.

    uv run tl                     status + weeks + plan + diary
    uv run tl status              where the prep stands today
    uv run tl weeks 20 | all      week map
    uv run tl months | seasons    month and season maps
    uv run tl plan                29-week macrocycle vs what happened
    uv run tl diary 4 | all | DATE
    uv run tl hills | segments | reps
    uv run tl export [path]       full JSON dump (data/diary.json)
    uv run tl site                render web/diary.html; pushing it publishes it

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

## Workflow after a session

1. Append to `data/activities.csv`, `labels.csv`, `re.csv`, `hr.csv` — never
   re-pull history, it costs ~12k tokens per 100 activities. On a day with
   several runs, write one `labels.csv` / `re.csv` row per run in the same order
   as `activities.csv`; `hr.csv` rows are matched to runs by duration.
2. Session notes worth keeping go in `data/notes.csv` (`date,name,note`);
   rows for one day are matched to that day's activities runs-first, then by
   duration.
3. After an uphill session, extend `hills.csv` and `segments.csv` — Strava
   `get_activity_performance` returns laps and segment efforts with per-rep HR
   and watts in one call.
4. `uv run tl status` to check, `uv run tl site` to rebuild the page, then
   commit and push `web/diary.html`. The Pages workflow publishes it to
   https://stancld.github.io/running-training-analysis/ — readable by link,
   `noindex` for search engines.

## Guardrails encoded

R1 week-over-week running hours ≤ 1.25×. R2 ACWR ≤ 1.30. R3 ≥ 300 m/h of climb
on weeks over 8 h. R4 no *flat* interval or repetition work (uphill reps carry
the intent of the rule and are not flagged). R6 ≤ 100 km per week. Dec–Apr big
weeks are called out separately — six of nine overuse onsets fall in that window.
