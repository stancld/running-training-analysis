import csv,math,datetime as dt
D='/Users/stancld/projects/training/data/'
wx={}
L=open(D+'weather_raw.csv').read().splitlines()
h=[i for i,l in enumerate(L) if l.startswith('time,')][0]
for l in L[h+1:]:
    if not l.strip(): continue
    p=l.split(',')
    wx[dt.date.fromisoformat(p[0])]=dict(tmean=float(p[1]),tmax=float(p[2]),tapp=float(p[4]),
        prcp=float(p[5]),rh=float(p[6]),wind=float(p[7]))
hr={}
for r in csv.DictReader(open(D+'hr.csv')): hr[dt.date.fromisoformat(r['date'])]=float(r['hr'])
re_={dt.date.fromisoformat(r['date']):float(r['re']) for r in csv.DictReader(open(D+'re.csv'))}
def mmss(s): return f"{int(s)//60}:{int(round(s))%60:02d}"
def anom(d):
    v=[wx[d-dt.timedelta(days=k)]['tapp'] for k in range(1,31) if d-dt.timedelta(days=k) in wx]
    return wx[d]['tapp']-sum(v)/len(v)

rows=[]
for r in csv.DictReader(open(D+'reps.csv')):
    d=dt.date.fromisoformat(r['date']); s=[float(x) for x in r['secs'].split(',')]
    w=wx[d]
    rows.append(dict(d=d,name=r['session'],rest=r['rest'],n=int(r['reps']),s=s,
        avg=sum(s)/len(s),best=min(s),first=s[0],last=s[-1],
        vol=len(s), tapp=w['tapp'],an=anom(d),wind=w['wind'],
        hr=hr.get(d),re=re_.get(d)))

print("="*100)
print("KILOMETRE REPS — every 1k-rep session in the record")
print("="*100)
print(f"{'date':11} {'session':19} {'rest':5} {'vol':>4} {'avg':>7} {'best':>6} {'1st':>6} {'last':>6} "
      f"{'fade':>6} {'app.T':>6} {'vs30d':>6} {'wind':>5} {'HR':>4}")
for r in sorted(rows,key=lambda x:x['d']):
    hrs=f"{r['hr']:.0f}" if r['hr'] else "  -"
    print(f"{str(r['d']):11} {r['name']:19} {r['rest']:5} {r['vol']:3d}k {mmss(r['avg']):>7} "
          f"{mmss(r['best']):>6} {mmss(r['first']):>6} {mmss(r['last']):>6} "
          f"{r['first']-r['last']:+5.0f}s {r['tapp']:5.1f}C {r['an']:+5.1f}C {r['wind']:4.0f} {hrs:>4}")

print("\n"+"="*100)
print("2026 ONLY — how the year has moved")
print("="*100)
Y=[r for r in rows if r['d'].year==2026]
base=[r for r in rows if r['d'].year<2026]
bavg=sum(r['avg'] for r in base)/len(base)
print(f"  2023-2025 benchmark (7 sessions): avg rep {mmss(bavg)} /km, best single rep "
      f"{mmss(min(r['best'] for r in base))}\n")
for r in Y:
    print(f"  {r['d']}  {r['name']:19} avg {mmss(r['avg'])}  best {mmss(r['best'])}  "
          f"{r['vol']:2d} reps  ({r['avg']-bavg:+.0f}s vs benchmark)")

print("\n  Volume of quality: total km of reps")
for r in Y: print(f"    {r['d']}  {r['vol']:2d} km at T")
print(f"    2023-25 sessions averaged {sum(r['vol'] for r in base)/len(base):.1f} km of reps")

print("\n"+"="*100)
print("SAME SESSION, DIFFERENT DAY — the three straight 1' -rest T sessions of 2026")
print("="*100)
for r in Y:
    if 'progressive' in r['name']: continue
    print(f"\n  {r['d']}  {r['name']}  ({r['tapp']:.0f}C, {r['an']:+.1f}C vs prior month, wind {r['wind']:.0f} km/h)")
    print("    splits: "+"  ".join(mmss(x) for x in r['s']))
    if r['hr']: print(f"    avg HR for the whole session {r['hr']:.0f} bpm")

print("\n"+"="*100)
print("PACING SHAPE (each rep vs that session's average, seconds)")
print("="*100)
for r in Y:
    dev=[x-r['avg'] for x in r['s']]
    print(f"  {r['d']}  "+" ".join(f"{x:+5.0f}" for x in dev))

print("\n"+"="*100)
print("EFFICIENCY — whole-session pace vs whole-session HR (COROS, 2026 sessions only)")
print("="*100)
S=[("2026-07-21","8x1k T",12.00,54.5,155),
   ("2026-08-05","6x1600m T",12.12,51.6,162),
   ("2026-08-18","8x1k progressive T",14.01,61.4,157),
   ("2026-08-29","10x1k T",16.50,68.9,152)]
print(f"  {'date':11} {'session':20} {'dist':>6} {'time':>6} {'pace':>7} {'HR':>4} {'m/beat':>8}")
for d,n,km,mn,h in S:
    pace=mn*60/km
    print(f"  {d:11} {n:20} {km:5.1f}k {mn:5.1f}m {mmss(pace):>7} {h:4.0f} "
          f"{km*1000/(h*mn):8.2f}")
print("\n  metres per heartbeat = distance / (avg HR x minutes). Higher is better.")
print("  Caveat: whole-activity averages, so warm-up/cool-down share differs between sessions.")

print("\n"+"="*100)
print("THE OTHER 2026 T SESSIONS (mile and 2k reps), for the full picture")
print("="*100)
O=[("2026-01-02","5x1600m T","1:40 walk","3:34 3:32 3:33 3:31 3:34",None),
   ("2026-01-20","4x2k progressive","-","marathon pace -> half pace",None),
   ("2026-03-10","5x1.5k progressive","-","3:45 3:40 3:36 3:34 3:34",None),
   ("2026-03-14","3x4k Z3","1k jg","3:52 3:48 3:45",None),
   ("2026-04-07","3x1600m T","1:36 walk","3:34 3:35 3:32",None),
   ("2026-04-24","2x3k M","-","(no splits logged)",None),
   ("2026-07-28","4x2k T","2:00","3:35 3:34 3:31 3:35",None),
   ("2026-08-05","6x1600m T","1:36","3:39 3:38 3:37 3:37 3:36 3:33",162)]
for d,n,rest,sp,h in O:
    hh=f"  HR {h}" if h else ""
    print(f"  {d}  {n:20} rest {rest:10} {sp}{hh}")
