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
| Rebuild the diary page | `uv run tl site` (writes `web/src/payload.json`) |
| Preview / build the page | `cd web && bun run dev` / `bun run build` (Vite + React + TypeScript) |
| Publish the diary page | commit and push `web/src/payload.json`; `.github/workflows/pages.yml` builds and deploys it |
| Lint, format and hygiene | `uv run pre-commit run --all-files` (install once with `uv run pre-commit install`) |
| Type-check | `uv run ty check` (also a pre-commit hook) |

There are no unit tests. CI (`.github/workflows/ci.yml`) runs pre-commit, smoke-tests
every command on a synthetic cache, and runs two e2e suites: `tests/` (pytest: a
cache through `tl site` into the payload, checking hand-worked numbers and guardrail
boundaries) and `web/e2e/` (Playwright: the synthetic cache into the built page, at
laptop and phone widths). Run `uv run pytest` after changing `tl`. Verify a
change by running the commands it affects and checking that the numbers make sense
against the data. Run pre-commit before every commit; Ruff settings live in `ruff.toml`.
Code must pass ty; declare attributes the checker cannot infer instead of silencing it.

## Where things live

- `tl/` is the maintained code. Each module has one job (see the README layout table);
  put new behaviour in the module that already owns it.
- `tl/config.py` holds every threshold and model constant. Change numbers there, not inline.
- `tl/plan.py` holds the macrocycle as data — week-level targets only.
- `LOG.md` holds Dan's weekly decisions: the close week's review, his plan for the next
  week, the guardrail checks against it and why plan volumes changed. Dan plans; agents
  check. Before talking training, get today's date with `TZ=Europe/Prague date`, read
  `LOG.md`, and follow its rules.
- `data/*.csv` is the cache and the source of truth. It is personal data, gitignored and
  kept on Dan's machine only — never commit it. `data/diary.json` and
  `web/src/payload.json` are generated: regenerate them, never hand-edit them.

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
- Publish the diary anywhere but GitHub Pages. Pushing `web/` to `master`
  deploys it to https://stancld.github.io/running-training-analysis/; Dan has approved that.

## Code style

- Small modules, plain functions and classes.
- Absolute imports under real module names: `from tl import config`, then `config.WOW_CAP`;
  no relative imports or aliases like `config as C`. Ruff enforces both (TID252, ICN001);
  a new module also goes in `ruff.toml`'s import-conventions list.
- Comments and docstrings say *why* in 2–3 lines; skip narration the code already states.
- No dead code, compatibility shims or speculative configuration.

## Commits

One logical change per commit, committed and pushed straight to `master` — no branches
or PRs. Commits in this repo need not be signed. Subject plus a short body carrying the why.
Commit as `stancld <daniel.stancl@gmail.com>` (set in the local git config).
