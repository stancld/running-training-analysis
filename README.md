# tl — training analysis

A small, dependency-free library and CLI over the local Strava/COROS cache in
`data/`. It maps the whole history onto weeks, months and seasons, scores every
week against the injury guardrails, compares actuals to the Chianti 120K
macrocycle, and renders the diary page in `web/`.

## Use

Set up once with `uv sync`, which installs Python 3.14 and the dev tools.

    uv run tl                     status + weeks + plan + diary
    uv run tl status              where the prep stands today
    uv run tl weeks 20 | all      week map
    uv run tl months | seasons    month and season maps
    uv run tl plan                29-week macrocycle vs what happened
    uv run tl diary 4 | all | DATE
    uv run tl hills | segments | reps
    uv run tl export [path]       full JSON dump (data/diary.json)
    uv run tl site                render web/diary.html, then publish it

## Layout

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
4. `uv run tl     status` to check, `uv run tl site` to rebuild the page,
   then republish `web/diary.html` to the same artifact URL.

## Guardrails encoded

R1 week-over-week running hours ≤ 1.25×. R2 ACWR ≤ 1.30. R3 ≥ 300 m/h of climb
on weeks over 8 h. R4 no *flat* interval or repetition work (uphill reps carry
the intent of the rule and are not flagged). R6 ≤ 100 km per week. Dec–Apr big
weeks are called out separately — six of nine overuse onsets fall in that window.
