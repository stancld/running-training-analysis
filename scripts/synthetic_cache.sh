#!/usr/bin/env bash
# CI's stand-in for Dan's personal cache, which is never pushed: a race week, then a
# ride-only week so WoW and ACWR are 0.00 (not null), then a 105 km week over the R6
# ceiling so the diary shows a guardrail flag; the race and the first ride have
# stream zone rows.
# The e2e tests rely on these rows.
# Writes into data/ unless given a directory; never run it there on Dan's machine.
set -euo pipefail
dir="${1:-$(dirname "$0")/../data}"
mkdir -p "$dir"
cd "$dir"

printf 'date,sport,km,min,vert\n2026-08-31,Run,10.0,55,300\n2026-09-02,TrailRun,12.0,70,600\n2026-09-05,Ride,40.0,90,400\n2026-09-06,RACE_Run,47.6,240,1924\n2026-09-08,Ride,30.0,60,200\n2026-09-15,Run,105.0,600,3000\n' > activities.csv
printf 'date,type,feel\n2026-08-31,E,1\n2026-09-02,L,\n2026-09-06,RACE,2\n' > labels.csv
printf 'date,re\n2026-08-31,20\n2026-09-02,40\n2026-09-06,235\n' > re.csv
printf 'date,min,hr\n2026-09-06,240,162\n' > hr.csv
printf 'date,min,z1,z2,z3,z4,z5\n2026-09-06,240,0,7200,3600,1800,1800\n' > zones.csv
printf 'date,min,z1,z2,z3,z4,z5,p1,p2,p3,p4,p5,p6,p7\n2026-09-05,90,1800,2700,900,0,0,0,3600,1200,600,0,0,0\n' > ride_zones.csv
