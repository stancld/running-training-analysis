"""Progress evaluation for Dan's training.

Re-runnable dashboard over the local cache. Top the CSVs up from Strava/COROS
first (see MEMORY: strava-mcp-and-data-cache), then just run this.

    python3 progress.py            # everything
    python3 progress.py load hills # only those sections

Sections: load, quality, hills, segments, aero, verdict
"""
import csv, math, sys, datetime as dt

D = '/Users/stancld/projects/training/data/'
TODAY = dt.date.today()

# Governing constraints from the injury analysis (MEMORY: injury-pattern-flat-volume)
WOW_CAP      = 1.25   # max week-over-week running-hour ratio
ACWR_CAP     = 1.30   # acute:chronic running hours
VERT_FLOOR   = 300    # m/h required on weeks over BIG_WEEK hours
BIG_WEEK_H   = 8.0
RISK_MONTHS  = (12, 1, 2, 3, 4)  # Dec-Apr: 6 of 9 injury onsets

# HR-at-pace calibration (MEMORY: feel-drivers-regression), r=0.91, +-3.5 bpm
def hr_from_re(re_per_hour):
    return 81.2 + 21.1 * math.log(re_per_hour) if re_per_hour > 0 else None


def mmss(s):
    return f"{int(s)//60}:{int(round(s)) % 60:02d}"


def load():
    acts = []
    for r in csv.DictReader(open(D + 'activities.csv')):
        try:
            d = dt.date.fromisoformat(r['date'])
        except ValueError:
            continue          # stray repeated header
        acts.append(dict(d=d, sport=r['sport'], km=float(r['km'] or 0),
                         mins=float(r['min'] or 0), vert=float(r['vert'] or 0)))
    lab = {}
    for r in csv.DictReader(open(D + 'labels.csv')):
        try:
            lab[dt.date.fromisoformat(r['date'])] = (
                r['type'], float(r['feel']) if r['feel'] else None)
        except ValueError:
            continue
    re_ = {}
    for r in csv.DictReader(open(D + 're.csv')):
        try:
            re_[dt.date.fromisoformat(r['date'])] = float(r['re'])
        except ValueError:
            continue
    hr = {}
    for r in csv.DictReader(open(D + 'hr.csv')):
        try:
            hr[dt.date.fromisoformat(r['date'])] = float(r['hr'])
        except ValueError:
            continue
    wx = {}
    L = open(D + 'weather_raw.csv').read().splitlines()
    h = [i for i, l in enumerate(L) if l.startswith('time,')][0]
    for l in L[h + 1:]:
        if not l.strip():
            continue
        p = l.split(',')
        wx[dt.date.fromisoformat(p[0])] = dict(
            tmean=float(p[1]), tmax=float(p[2]), tapp=float(p[4]),
            prcp=float(p[5]), rh=float(p[6]), wind=float(p[7]))
    return acts, lab, re_, hr, wx


ACTS, LAB, RE, HRD, WX = load()
RUNS = [a for a in ACTS if a['sport'] in ('Run', 'TrailRun', 'RACE_Run')]


def week_of(d):
    return d - dt.timedelta(days=d.weekday())


def weekly(acts, weeks=14, end=None):
    """Aggregate into Mon-start weeks, newest last."""
    end = week_of(end or max(a['d'] for a in acts))
    out = []
    for k in range(weeks - 1, -1, -1):
        w = end - dt.timedelta(weeks=k)
        sel = [a for a in acts if week_of(a['d']) == w]
        runs = [a for a in sel if a['sport'] in ('Run', 'TrailRun', 'RACE_Run')]
        rides = [a for a in sel if a['sport'] in ('Ride', 'VirtualRide')]
        out.append(dict(
            w=w,
            rh=sum(a['mins'] for a in runs) / 60,
            rkm=sum(a['km'] for a in runs),
            rvert=sum(a['vert'] for a in runs),
            bh=sum(a['mins'] for a in rides) / 60,
            n=len(runs),
            partial=(w + dt.timedelta(days=6)) > TODAY,
            current=(w <= TODAY <= w + dt.timedelta(days=6))))
    for r in out:
        r['dens'] = r['rvert'] / r['rh'] if r['rh'] else 0
    return out


# ----------------------------------------------------------------- sections
def sec_load():
    print("=" * 92)
    print("TRAINING LOAD — running weeks (Mon-start)")
    print("=" * 92)
    W = weekly(RUNS, 14)
    print(f"{'week':11} {'runs':>4} {'hours':>6} {'km':>7} {'vert':>7} {'m/h':>6} "
          f"{'WoW':>5} {'ACWR':>5} {'bike h':>7}  flags")
    for i, r in enumerate(W):
        prev = W[i - 1]['rh'] if i else 0
        wow = r['rh'] / prev if prev else float('nan')
        # ACWR: this week vs mean of the 4 weeks ending here
        chron = [x['rh'] for x in W[max(0, i - 3):i + 1]]
        acwr = r['rh'] / (sum(chron) / len(chron)) if sum(chron) else float('nan')
        f = []
        if r['current']:
            f.append(f"current week, through {min(TODAY, r['w']+dt.timedelta(days=6))}")
        if r['partial']:
            pass
        else:
            if wow == wow and wow > WOW_CAP:
                f.append(f'WoW {wow:.2f}x >{WOW_CAP}')
            if acwr == acwr and acwr > ACWR_CAP:
                f.append(f'ACWR {acwr:.2f}')
            if r['rh'] > BIG_WEEK_H and r['dens'] < VERT_FLOOR:
                f.append(f"flat volume {r['dens']:.0f} m/h < {VERT_FLOOR}")
            if r['w'].month in RISK_MONTHS and r['rh'] > BIG_WEEK_H:
                f.append('injury-risk month')
        ws = f"{wow:5.2f}" if wow == wow else "    -"
        acs = f"{acwr:5.2f}" if acwr == acwr else "    -"
        print(f"{str(r['w']):11} {r['n']:4d} {r['rh']:6.1f} {r['rkm']:7.1f} "
              f"{r['rvert']:7.0f} {r['dens']:6.0f} {ws} {acs} {r['bh']:7.1f}  "
              + ('; '.join(f) if f else 'ok'))
    print(f"\n  Rules applied: WoW cap {WOW_CAP}x, ACWR cap {ACWR_CAP}, "
          f">={VERT_FLOOR} m/h on weeks over {BIG_WEEK_H} h.")
    return W


def sec_quality():
    print("\n" + "=" * 92)
    print("FLAT THRESHOLD PROGRESSION — every logged 1k-rep session")
    print("=" * 92)
    rows = []
    for r in csv.DictReader(open(D + 'reps.csv')):
        s = [float(x) for x in r['secs'].split(',')]
        rows.append(dict(d=dt.date.fromisoformat(r['date']), name=r['session'],
                         rest=r['rest'], s=s))
    rows.sort(key=lambda x: x['d'])
    print(f"{'date':11} {'session':22} {'rest':5} {'n':>3} {'avg':>7} {'last3':>7} "
          f"{'best':>6} {'fade':>6}")
    for r in rows:
        s = r['s']
        avg = sum(s) / len(s)
        l3 = sum(s[-3:]) / 3
        print(f"{str(r['d']):11} {r['name']:22} {r['rest']:5} {len(s):3d} "
              f"{mmss(avg):>7} {mmss(l3):>7} {mmss(min(s)):>6} {s[0]-s[-1]:+5.0f}s")
    y = [r for r in rows if r['d'].year == 2026]
    b = [r for r in rows if r['d'].year < 2026]
    if y and b:
        bb = min(min(r['s']) for r in b)
        yb = min(min(r['s']) for r in y)
        print(f"\n  best 1k rep ever pre-2026 {mmss(bb)}  |  2026 {mmss(yb)} "
              f"({yb-bb:+.0f}s)")
        print(f"  rep volume: pre-2026 {sum(len(r['s']) for r in b)/len(b):.1f} km/session"
              f"  |  2026 {sum(len(r['s']) for r in y)/len(y):.1f} km/session")


def sec_hills():
    print("\n" + "=" * 92)
    print("UPHILL QUALITY SESSIONS — vertical rate, HR and decoupling")
    print("=" * 92)
    S = {}
    for r in csv.DictReader(open(D + 'hills.csv')):
        S.setdefault((r['date'], r['session']), []).append(r)
    for (date, name), reps in sorted(S.items()):
        reps.sort(key=lambda x: int(x['rep']))
        print(f"\n  {date}  {name}")
        print(f"    {'rep':>3} {'dur':>6} {'dist':>7} {'vert':>6} {'grade':>6} "
              f"{'VAM':>7} {'speed':>7} {'HR':>6} {'W':>6} {'W/HR':>6}")
        vam, whr = [], []
        for x in reps:
            dur, dist = float(x['dur_s']), float(x['dist_m'])
            v, hr = float(x['vert_m']), float(x['hr'])
            w = float(x['watts']) if x['watts'] else None
            V = v / dur * 3600
            vam.append(V)
            ratio = w / hr if w else None
            if ratio:
                whr.append(ratio)
            print(f"    {x['rep']:>3} {mmss(dur):>6} {dist:7.0f} {v:6.0f} "
                  f"{float(x['grade_pct']):5.1f}% {V:7.0f} {dist/dur*3.6:6.1f}k "
                  f"{hr:6.1f} {(f'{w:.0f}' if w else '-'):>6} "
                  f"{(f'{ratio:.3f}' if ratio else '-'):>6}")
        hrs = [float(x['hr']) for x in reps]
        print(f"    -> mean VAM {sum(vam)/len(vam):7.0f} m/h   "
              f"HR {hrs[0]:.0f}->{hrs[-1]:.0f} across reps "
              f"({hrs[-1]-hrs[0]:+.1f} bpm), peak {max(hrs):.0f}")
        if len(whr) > 1:
            dec = (whr[-1] - whr[0]) / whr[0] * 100
            grade = ("excellent" if abs(dec) < 3 else
                     "acceptable" if abs(dec) < 5 else "large — session was too hard")
            print(f"    -> power:HR decoupling {dec:+.1f}%  ({grade})")
    print("\n  VAM = vertical metres per hour sustained during the rep.")
    print("  Decoupling = change in watts-per-heartbeat first rep -> last rep.")


def sec_segments():
    print("\n" + "=" * 92)
    print("SAME-SEGMENT BENCHMARKS — identical hill, different days")
    print("=" * 92)
    S = {}
    for r in csv.DictReader(open(D + 'segments.csv')):
        S.setdefault(r['segment'], []).append(r)
    for seg, rows in S.items():
        d0 = rows[0]
        print(f"\n  {seg}  ({float(d0['dist_m']):.0f} m, {float(d0['vert_m']):.0f} m up, "
              f"{float(d0['vert_m'])/float(d0['dist_m'])*100:.1f}%)")
        print(f"    {'date':11} {'ctx':10} {'rep':>3} {'time':>7} {'VAM':>7} "
              f"{'HR':>6} {'W':>6} {'m/beat':>7}")
        for r in sorted(rows, key=lambda x: (x['date'], int(x['rep']))):
            t, hr = float(r['secs']), float(r['hr'])
            v, dist = float(r['vert_m']), float(r['dist_m'])
            w = float(r['watts']) if r['watts'] else None
            print(f"    {r['date']:11} {r['context']:10} {r['rep']:>3} {mmss(t):>7} "
                  f"{v/t*3600:7.0f} {hr:6.1f} {(f'{w:.0f}' if w else '-'):>6} "
                  f"{dist/(hr*t/60):7.2f}")
        by = {}
        for r in rows:
            by.setdefault(r['context'], []).append(float(r['secs']))
        if len(by) > 1:
            items = sorted(by.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
            fast, slow = items[0], items[-1]
            fa = sum(fast[1]) / len(fast[1])
            sa = sum(slow[1]) / len(slow[1])
            print(f"    -> {fast[0]} is {(sa-fa)/sa*100:.0f}% faster than {slow[0]}")


def sec_aero():
    print("\n" + "=" * 92)
    print("AEROBIC TREND — HR at a given effort on easy/long runs, by month")
    print("=" * 92)
    rows = []
    for a in RUNS:
        t = LAB.get(a['d'], (None, None))[0]
        if t not in ('E', 'L') or a['mins'] < 25:
            continue
        re = RE.get(a['d'])
        if not re:
            continue
        est = hr_from_re(re / (a['mins'] / 60))
        rows.append(dict(d=a['d'], hr=HRD.get(a['d']) or est,
                         meas=a['d'] in HRD, pace=a['mins'] / a['km'] * 60,
                         vpk=a['vert'] / a['km'], km=a['km']))
    rows = [r for r in rows if r['hr']]
    months = {}
    for r in rows:
        months.setdefault((r['d'].year, r['d'].month), []).append(r)
    print(f"{'month':9} {'runs':>4} {'km':>7} {'pace':>7} {'vert/km':>8} {'HR':>6} "
          f"{'m/beat':>7} {'measured':>9}")
    for k in sorted(months)[-15:]:
        g = months[k]
        pace = sum(r['pace'] for r in g) / len(g)
        hr = sum(r['hr'] for r in g) / len(g)
        km = sum(r['km'] for r in g)
        mpb = sum(r['km'] * 1000 / (r['hr'] * r['pace'] * r['km'] / 60) for r in g) / len(g)
        print(f"{k[0]}-{k[1]:02d}  {len(g):4d} {km:7.1f} {mmss(pace):>7} "
              f"{sum(r['vpk'] for r in g)/len(g):7.0f}m {hr:6.1f} {mpb:7.2f} "
              f"{sum(1 for r in g if r['meas']):9d}")
    print("\n  HR is COROS-measured where available, else estimated from Strava")
    print("  relative_effort (HR = 81.2 + 21.1*ln(RE/h), +-3.5 bpm).")
    print("  m/beat = metres covered per heartbeat; higher is fitter, but it is")
    print("  confounded by pace and terrain, so read it alongside those columns.")


def sec_verdict(W):
    print("\n" + "=" * 92)
    print("FLAGS")
    print("=" * 92)
    out = []
    done = [r for r in W if not r['partial']]
    if len(done) >= 5:
        last4 = sum(r['rh'] for r in done[-4:]) / 4
        prev4 = sum(r['rh'] for r in done[-8:-4]) / 4 if len(done) >= 8 else None
        out.append(f"4-week running load {last4:.1f} h/wk"
                   + (f" vs {prev4:.1f} h/wk in the four before ({last4/prev4:.2f}x)"
                      if prev4 else ""))
        dens = sum(r['rvert'] for r in done[-4:]) / sum(r['rh'] for r in done[-4:])
        out.append(f"vert density over those 4 weeks {dens:.0f} m/h "
                   + ("(above the 300 m/h floor)" if dens >= VERT_FLOOR
                      else "(BELOW the 300 m/h floor — flat-volume injury pattern)"))
    if TODAY.month in RISK_MONTHS:
        out.append("calendar is in the Dec-Apr injury window — hold the WoW cap hard")
    stale = (TODAY - max(a['d'] for a in ACTS)).days
    out.append(f"cache last activity {max(a['d'] for a in ACTS)} ({stale} d old)")
    for o in out:
        print("  - " + o)


SECTIONS = dict(load=sec_load, quality=sec_quality, hills=sec_hills,
                segments=sec_segments, aero=sec_aero)

if __name__ == '__main__':
    want = sys.argv[1:] or list(SECTIONS) + ['verdict']
    W = None
    for name in want:
        if name == 'verdict':
            sec_verdict(W or weekly(RUNS, 14))
        elif name in SECTIONS:
            r = SECTIONS[name]()
            if name == 'load':
                W = r
        else:
            print(f"unknown section {name!r}; have {list(SECTIONS)} + verdict")
