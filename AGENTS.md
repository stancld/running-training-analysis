# AGENTS.md

`tl` is a dependency-free Python CLI over Dan's local Strava/COROS cache in `data/`.
It scores training weeks against injury guardrails, compares them with the Chianti 120K
macrocycle and renders the diary page in `web/`. Read `README.md` before changing anything.

## Commands

| Task | Command |
|---|---|
| Status of the prep | `uv run tl status` |
| Full report | `uv run tl` |
| JSON dump | `uv run tl export` (writes `data/diary.json`) |
| Rebuild the diary page | `uv run tl site` (renders `web/diary.tmpl.html` → `web/diary.html`) |
| Publish the diary page | commit and push `web/diary.html`; `.github/workflows/pages.yml` deploys it |
| Lint, format and hygiene | `uv run pre-commit run --all-files` (install once with `uv run pre-commit install`) |

There is no test suite. CI (`.github/workflows/ci.yml`) runs pre-commit and smoke-tests
every command on a synthetic cache, so it catches crashes, not wrong numbers. Verify a
change by running the commands it affects and checking that the numbers make sense
against the data. Run pre-commit before every commit; Ruff settings live in `ruff.toml`.

## Where things live

- `tl/` is the maintained code. Each module has one job (see the README layout table);
  put new behaviour in the module that already owns it.
- `tl/config.py` holds every threshold and model constant. Change numbers there, not inline.
- `tl/plan.py` holds the macrocycle as data — week-level targets only.
- `data/*.csv` is the cache and the source of truth. It is personal data, gitignored and
  kept on Dan's machine only — never commit it. `data/diary.json` and
  `web/diary.html` are generated: regenerate them, never hand-edit them.

## Boundaries

**Always**
- Use uv for everything: `uv sync` to set up, `uv run` for every command, `uv add --dev` for
  tooling. Never pip or a bare `python`. The runtime stays on the standard library, so
  `pyproject.toml` has no `dependencies`; Python is pinned in `.python-version`.
- Append to the CSVs; keep their column order and date format.
- Keep the README in sync when commands, modules or guardrails change.

**Ask first**
- Adding a dependency, tooling (packaging, linters, tests) or a new module.
- Changing a guardrail threshold, the HR/load model or the plan — they encode Dan's
  injury and physiology history, not arbitrary defaults.
- Rewriting or deleting existing CSV rows.

**Never**
- Re-pull full history from Strava/COROS; fetch only the missing days.
- Publish the diary anywhere but GitHub Pages. Pushing `web/diary.html` to `master`
  deploys it to https://stancld.github.io/running-training-analysis/; Dan has approved that.

## Code style

- Small modules, plain functions and classes; inside `tl`, keep the existing relative imports.
- Comments and docstrings say *why* in 2–3 lines; skip narration the code already states.
- No dead code, compatibility shims or speculative configuration.

## Commits

One logical change per commit, committed and pushed straight to `master` — no branches
or PRs. Subject plus a short body carrying the why.
Commit as `stancld <daniel.stancl@gmail.com>` (set in the local git config).
