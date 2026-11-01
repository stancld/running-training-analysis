#!/usr/bin/env bash
# CI's stand-in for Dan's personal cache, which is never pushed: a race week, then a
# ride-only week so WoW and ACWR are 0.00 (not null). The e2e tests rely on these rows.
set -euo pipefail
cd "$(dirname "$0")/../data"

printf 'date,sport,km,min,vert\n2026-08-31,Run,10.0,55,300\n2026-09-02,TrailRun,12.0,70,600\n2026-09-05,Ride,40.0,90,400\n2026-09-06,RACE_Run,47.6,240,1924\n2026-09-08,Ride,30.0,60,200\n' > activities.csv
printf 'date,type,feel\n2026-08-31,E,1\n2026-09-02,L,\n2026-09-06,RACE,2\n' > labels.csv
printf 'date,re\n2026-08-31,20\n2026-09-02,40\n2026-09-06,235\n' > re.csv
printf 'date,min,hr\n2026-09-06,240,162\n' > hr.csv
