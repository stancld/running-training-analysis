# AGENTS.md

`tl` is a dependency-free Python CLI over Dan's local Strava/COROS cache in `data/`.
It scores training weeks against injury guardrails, compares them with the Chianti 120K
macrocycle and renders the diary page in `web/`. Read `README.md` before changing anything.

## Commands

| Task | Command |
|---|---|
| Status of the prep | `python3 -m tl status` |
| Full report | `python3 -m tl` |
| JSON dump | `python3 -m tl export` (writes `data/diary.json`) |
| Rebuild the diary page | `python3 -m tl site` (renders `web/diary.tmpl.html` → `web/diary.html`) |

There is no test suite. Verify a change by running the commands it affects and checking
that the numbers make sense against the data.

## Where things live

- `tl/` is the maintained code. Each module has one job (see the README layout table);
  put new behaviour in the module that already owns it.
- `tl/config.py` holds every threshold and model constant. Change numbers there, not inline.
- `tl/plan.py` holds the macrocycle as data — week-level targets only.
- `data/*.csv` is the cache and the source of truth. `data/diary.json` and
  `web/diary.html` are generated: regenerate them, never hand-edit them.
- `data/*.py` and `data/progress.py` are earlier one-off analyses superseded by `tl`.
  Do not extend or cite them as patterns; several hardcode the old
  `~/projects/training` path.

## Boundaries

**Always**
- Stay on the standard library. Python 3.14+.
- Append to the CSVs; keep their column order and date format.
- Keep the README in sync when commands, modules or guardrails change.

**Ask first**
- Adding a dependency, tooling (packaging, linters, tests) or a new module.
- Changing a guardrail threshold, the HR/load model or the plan — they encode Dan's
  injury and physiology history, not arbitrary defaults.
- Rewriting or deleting existing CSV rows.

**Never**
- Re-pull full history from Strava/COROS; fetch only the missing days.
- Publish or republish the diary artifact without Dan's go-ahead.

## Code style

- Small modules, plain functions and classes; inside `tl`, keep the existing relative imports.
- Comments and docstrings say *why* in 2–3 lines; skip narration the code already states.
- No dead code, compatibility shims or speculative configuration.

## Commits

Subject plus a short body carrying the why. Branches use the `ds/` prefix.
Commit as `stancld <daniel.stancl@gmail.com>` (set in the local git config).
