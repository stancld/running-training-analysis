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
| The 29-week plan | planned against actual running hours for every week, its phases and race weeks; beyond 8 weeks, bands instead of numbers. The selected week also lists its phase's suggested quality sessions (`plan.QUALITY`, uphill-first sessions drawn from Kilian Jornet's posts and Uphill Athlete and adapted to Dan's record; each note says whose claim it is), with the reasoning and sources folded away |
| Heart-rate zones by phase | time per HR zone for each phase, opening into weekly columns; Running or Total (runs plus rides, with ride power zones) |
| Weekly diary | one entry per week since the plan started: sessions, notes, plan comparison and verdicts |
| Every month since 2023 | monthly running hours or climb density (m/h) as a trend line and a heatmap, with injury months, Dec–Apr risk months and yearly totals; each month opens into its stats, sport split and the same month in other years |
| Week ledger | the last 26 weeks with the same ok / watch / flag status, ratios and volumes |
| Chianti 120K goal | Dan's UTMB-index goal (`plan.GOAL`) on a scale of what each index means on the course: an estimated finish time, a place in the 2026 field and the Lavaredo 80K equivalent, with his current index, the goal, the stretch and the fade band marked |

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
text. The current calendar week is included even before its first activity.
On a phone each tab has its own URL hash (`#today`, `#plan`, `#diary`,
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

Without the optional private refresh setup below, GitHub Actions only builds the
committed payload. An Amp orb can run the same workflow on a copy of the cache:

1. Append the session to the CSVs locally (steps 1–2 above) and upload the whole
   cache into the orb's `data/`. A fresh orb has no CSVs.
2. `uv run python scripts/fetch_zones.py` reads `STRAVA_CLIENT_ID`,
   `STRAVA_CLIENT_SECRET` and `STRAVA_REFRESH_TOKEN` from the orb's environment,
   set as Amp secrets. If Strava rotates the token, the new one lands only in
   the orb's `~/.config/tl/strava_refresh_token`, so update the secret with it.
3. `uv run tl status`, `uv run tl site`, `uv run pytest`, then commit and push
   only `web/src/payload.json`; the CSVs stay gitignored.
4. Download the updated `zones.csv` and `ride_zones.csv` back to Dan's machine;
   the orb's copy is disposable, not a durable checkpoint.

### Free daily refresh (GitHub-only, requires private setup)

`Refresh training data` (`.github/workflows/refresh.yml`) supports a daily run at
06:23 UTC (07:23 Prague in winter, 08:23 in summer) and **Run workflow** on master.
It stays disabled until `TRAINING_REFRESH_ENABLED=true` is configured. Standard
Linux runners in this public repository are free; the state repository does not
run Actions or use billed artifacts. GitHub can delay scheduled runs;
inactive public repositories may have schedules disabled after 60 days.

The private `stancld/training-data-state` repository holds only
`cache.tar.gz.gpg` (CSV cache plus ID ledger) and `refresh-token.gpg`, encrypted
with GnuPG AES-256 and integrity protection. Raw CSVs and plaintext tokens are
**never committed**, even to the private repository. No AWS account, paid service,
Actions cache or raw-data workflow artifact is needed. Both private repositories
and standard public-repository Actions runners are included in GitHub Free.

Setup:

1. Create `stancld/training-data-state` as **private**, initialized with a README.
   Keep it private and do not add workflows. The script verifies its visibility
   and uses its default branch. GitHub keeps old encrypted checkpoints in Git
   history; budget for gradual repository growth and retain the encryption key
   in a password manager. Key rotation does not erase old ciphertext/history.
2. Create a fine-grained GitHub token restricted to **that state repository**,
   with Contents read/write (and required Metadata read). Store it as the
   `TRAINING_STATE_TOKEN` Actions secret on `running-training-analysis`.
   Its normal `GITHUB_TOKEN` cannot access another private repository. Set a
   suitable expiry and replace the token before it expires.
3. Generate a strong random single-line encryption key (at least 32 characters)
   in a password manager. Store it as `TRAINING_STATE_KEY`, alongside
   `STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET`, in GitHub's private Actions
   secret settings. Never enter these in chat, tracked files or command-line
   arguments. Existing Amp secrets are not automatically GitHub secrets.
   Restrict the **github-pages environment** to master; never run secret-bearing
   refresh code from untrusted branches or PRs.
4. On the machine holding the **authoritative raw cache**, privately configure
   `GH_TOKEN` and `TRAINING_STATE_KEY` using secure environment input. Put the
   current Strava refresh token in `~/.config/tl/strava_refresh_token` (mode 600),
   then run `uv run python scripts/fetch_zones.py --seed`. This encrypts and
   uploads the full seed plus token in one GitHub-signed commit; it refuses to
   overwrite an existing seed. The cache must be complete through its last
   activity day, including every session that day. Never reconstruct it from
   rounded `data/diary.json`. All curated CSVs are preserved.
5. Set the Actions variable `TRAINING_REFRESH_ENABLED=true` and run the workflow
   manually first (choose master).
   Missing seed/token or denied storage access fails closed: no history re-pull,
   fallback to an old token, or partial page deployment. Verify the private checkpoint
   and Pages result before relying on the schedule.

`uv run python scripts/fetch_zones.py --refresh` appends activities (distance,
moving minutes, climb, race sport marker), measured run HR and plan-period zone
streams. The first run starts **after the seed's last complete day**. Subsequent
runs re-query a seven-day overlap by Strava ID; IDs and the scan watermark live
in private `data/strava_sync.json`. Uploaded activities dated today are included
too; future local dates are excluded. The ID ledger prevents duplicates when
another workout is uploaded later the same day. A refresh is a snapshot of what
is already uploaded, not a live workout feed.
Delayed uploads older than that overlap, edits/deletions on Strava, COROS-only
activities and historical omissions require a deliberate manual cache update.
No existing rows are rewritten. Labels, feel, notes, relative effort, hill and
segment annotations remain manual; new activities without RE use the existing
load fallback, rather than inventing effort or workout labels.

Every CI run uses `--restore` to download the archive and token from one exact
private-repository commit. It saves Strava's returned encrypted refresh token
**before** using the access token; only a successfully fetched
and rendered cache replaces the archive. A later build/deployment failure can
therefore retry without duplicating activities or losing a rotated token. There
is still an unavoidable failure window between Strava issuing a token and GitHub
acknowledging its write; recover via private OAuth reauthorization if that happens.
Writes use GitHub's `createCommitOnBranch` API (GitHub-signed commits, checked for
a valid signature), with `expectedHeadOid` compare-and-swap. A stale writer fails
instead of overwriting newer state. An ambiguous API failure is not retried
blindly: restore remote state first. No signing key is stored in the workflow.
Do not refresh the same Strava grant simultaneously from another orb/machine:
GitHub's concurrency lock cannot serialize external OAuth clients.

Refresh and existing manual Pages deployments share one non-cancelling lock.
GitHub may replace an older *pending* run with a newer pending run; it never runs
two holders concurrently. A refresh refuses to publish if master advanced while
it ran. It builds/deploys the generated page directly, **without committing the
payload** or requiring a bot signing key. The usual manual payload-push workflow
remains available; a later refresh will regenerate from the private checkpoint.
Only `web/dist` is published. Committed payload freshness is independent of the
daily deployed page.

Before manually extending the cache, disable refresh and wait for the active run
to finish. On a fresh disposable checkout, configure the private secrets and run
`uv run python scripts/fetch_zones.py --restore` (it refuses to overwrite raw
CSVs). Preserve its ID ledger while adding manual rows; render with `uv run tl site`,
then upload with `uv run python scripts/fetch_zones.py --save`. Do not manually
add Strava activities the next refresh will ingest, or upload a stale local cache
over the checkpoint. Re-enable only after uploading a complete archive. For a local
`--refresh`, retain the disposable copy only on full success; CI never persists
partially appended files. Keep raw CSVs, the ledger and tokens out of commits,
logs and public artifacts throughout.

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
