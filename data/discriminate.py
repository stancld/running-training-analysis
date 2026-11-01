import csv, datetime as dt
from collections import defaultdict
RUN={"Run","RACE_Run","TrailRun"}
rows=[]
with open('/Users/stancld/projects/training/data/activities.csv') as f:
    for r in csv.DictReader(f):
        rows.append((dt.date.fromisoformat(r['date']),r['sport'],float(r['min']),float(r['vert'])))
def monday(d): return d-dt.timedelta(days=d.weekday())
wk=defaultdict(lambda:[0.0,0.0])
for d,s,mn,v in rows:
    if s in RUN:
        w=wk[monday(d)]; w[0]+=mn; w[1]+=v
weeks=sorted(wk)
INJ=["2023-04-04","2024-03-10","2024-08-09","2024-12-17","2025-02-18",
     "2025-04-02","2025-06-05","2026-01-05","2026-04-08"]
injw={monday(dt.date.fromisoformat(x)) for x in INJ}
spike=[]
for a,b in zip(weeks,weeks[1:]):
    pa,pb=wk[a][0]/60,wk[b][0]/60
    if pa>=1.0 and pb/pa>=1.5 and pb>=5.0: spike.append(b)

def dens(w):
    h=wk[w][0]/60
    return wk[w][1]/h if h else 0

bad=[s for s in spike if s in injw or (s+dt.timedelta(weeks=1)) in injw]
ok =[s for s in spike if s not in bad]

def stats(name,g):
    if not g: return
    d=[dens(x) for x in g]; d.sort()
    winter=sum(1 for x in g if x.month in (11,12,1,2,3,4))
    print(f"  {name:22} n={len(g):2d}  median vert/h = {d[len(d)//2]:5.0f} m   "
          f"Nov-Apr: {winter}/{len(g)} ({winter/len(g):.0%})")
print("WHAT SEPARATES A HARMFUL SPIKE FROM A HARMLESS ONE?\n")
stats("spike -> INJURY", bad)
stats("spike -> fine",   ok)

print("\nHarmful spike weeks in detail:")
for s in sorted(bad):
    print(f"    {s}  {wk[s][0]/60:5.1f}h  {wk[s][1]:5.0f}m  = {dens(s):4.0f} m/h")
