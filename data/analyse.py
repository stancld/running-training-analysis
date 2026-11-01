import csv, datetime as dt
from collections import defaultdict

RUN = {"Run","RACE_Run","TrailRun"}
CROSS = {"Ride","VirtualRide","Hike","Snowshoe","NordicSki","AlpineSki","Swim","Walk"}

rows=[]
with open('/Users/stancld/projects/training/data/activities.csv') as f:
    for r in csv.DictReader(f):
        rows.append((dt.date.fromisoformat(r['date']), r['sport'], float(r['km']), float(r['min']), float(r['vert'])))
rows.sort()

def monday(d): return d - dt.timedelta(days=d.weekday())

wk=defaultdict(lambda: dict(rkm=0,rmin=0,rvert=0,xmin=0,gym=0,tot=0))
for d,s,km,mn,v in rows:
    w=wk[monday(d)]
    if s in RUN: w['rkm']+=km; w['rmin']+=mn; w['rvert']+=v
    elif s in CROSS: w['xmin']+=mn
    else: w['gym']+=mn
    w['tot']+=mn

print("="*78)
print("SEASON SUMMARY  (season = Nov 1 -> Oct 31)")
print("="*78)
def season(d):
    return f"{d.year}/{d.year+1}" if d.month>=11 else f"{d.year-1}/{d.year}"
S=defaultdict(lambda: dict(rkm=0,rmin=0,rvert=0,xmin=0,gym=0,days=set(),rdays=set()))
for d,s,km,mn,v in rows:
    x=S[season(d)]
    if s in RUN: x['rkm']+=km; x['rmin']+=mn; x['rvert']+=v; x['rdays'].add(d)
    elif s in CROSS: x['xmin']+=mn
    else: x['gym']+=mn
    x['days'].add(d)
print(f"{'season':10} {'run km':>8} {'run h':>7} {'vert m':>9} {'cross h':>8} {'gym h':>6} {'run days':>9}")
for k in sorted(S):
    x=S[k]
    print(f"{k:10} {x['rkm']:8.0f} {x['rmin']/60:7.0f} {x['rvert']:9.0f} {x['xmin']/60:8.0f} {x['gym']/60:6.0f} {len(x['rdays']):9d}")

print()
print("="*78)
print("WEEKLY TOTAL HOURS - distribution by calendar year")
print("="*78)
byyear=defaultdict(list)
for m,w in wk.items(): byyear[m.year].append(w['tot']/60)
print(f"{'year':6} {'weeks':>6} {'mean':>6} {'median':>7} {'p75':>6} {'p90':>6} {'max':>6}")
for y in sorted(byyear):
    v=sorted(byyear[y]); n=len(v)
    q=lambda p: v[min(n-1,int(p*n))]
    print(f"{y:6} {n:6d} {sum(v)/n:6.1f} {q(.5):7.1f} {q(.75):6.1f} {q(.9):6.1f} {max(v):6.1f}")

print()
print("="*78)
print("RUN-ONLY WEEKLY HOURS - same distribution")
print("="*78)
byyear=defaultdict(list)
for m,w in wk.items(): byyear[m.year].append(w['rmin']/60)
for y in sorted(byyear):
    v=sorted(byyear[y]); n=len(v)
    q=lambda p: v[min(n-1,int(p*n))]
    print(f"{y:6} {n:6d} mean {sum(v)/n:5.1f}  med {q(.5):5.1f}  p75 {q(.75):5.1f}  p90 {q(.9):5.1f}  max {max(v):5.1f}")

print()
print("="*78)
print("RUNNING GAPS >= 6 DAYS  (candidate injury / illness layoffs)")
print("="*78)
rd=sorted({d for d,s,*_ in rows if s in RUN})
for a,b in zip(rd, rd[1:]):
    g=(b-a).days
    if g>=6:
        print(f"  {a} -> {b}   {g:3d} days without running")
