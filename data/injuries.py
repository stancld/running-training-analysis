import csv, datetime as dt
from collections import defaultdict
RUN={"Run","RACE_Run","TrailRun"}
rows=[]
with open('/Users/stancld/projects/training/data/activities.csv') as f:
    for r in csv.DictReader(f):
        rows.append((dt.date.fromisoformat(r['date']),r['sport'],float(r['km']),float(r['min']),float(r['vert'])))
def monday(d): return d-dt.timedelta(days=d.weekday())
wk=defaultdict(lambda:[0,0,0])   # rmin, rvert, rkm
for d,s,km,mn,v in rows:
    if s in RUN:
        w=wk[monday(d)]; w[0]+=mn; w[1]+=v; w[2]+=km

# onset dates taken from the athlete's own activity notes
INJ=[
 ("2023-04-04","calf / achilles (R)"),
 ("2024-03-10","periosteum / shin"),
 ("2024-08-09","knee tendons (post-KAT)"),
 ("2024-12-17","periosteum 'classics'"),
 ("2025-02-18","calf"),
 ("2025-04-02","shin + calf (R)"),
 ("2025-06-05","thigh"),
 ("2025-08-10","knee - CRASH (traumatic)"),
 ("2026-01-05","calf (L) - 2 months"),
 ("2026-04-08","achilles (L)"),
 ("2026-07-14","thigh/glute (L), chronic"),
]
print("="*96)
print("LOAD IN THE 4 WEEKS IMMEDIATELY BEFORE EACH INJURY ONSET  (run hours / vert per week)")
print("="*96)
print(f"{'onset':12} {'what':26} {'w-4':>12} {'w-3':>12} {'w-2':>12} {'w-1':>12}   4wk vert")
for ds,label in INJ:
    d=dt.date.fromisoformat(ds); m=monday(d)
    cells=[];tv=0
    for k in range(4,0,-1):
        w=wk[m-dt.timedelta(weeks=k)]
        cells.append(f"{w[0]/60:4.1f}h/{w[1]:4.0f}"); tv+=w[1]
    print(f"{ds:12} {label:26} " + " ".join(f"{c:>12}" for c in cells) + f"   {tv:6.0f}")

print()
print("="*96)
print("MONTH OF ONSET")
print("="*96)
mon=defaultdict(list)
for ds,label in INJ: mon[dt.date.fromisoformat(ds).month].append(label)
names="Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
for i in range(1,13):
    bar="#"*len(mon.get(i,[]))
    print(f"  {names[i-1]}  {bar:6} {', '.join(mon.get(i,[]))}")

print()
print("="*96)
print("VERT DENSITY: vert per running hour, by quarter")
print("="*96)
q=defaultdict(lambda:[0,0])
for d,s,km,mn,v in rows:
    if s in RUN:
        key=f"{d.year}Q{(d.month-1)//3+1}"; q[key][0]+=mn; q[key][1]+=v
for k in sorted(q):
    mn,v=q[k]
    if mn: print(f"  {k}  {mn/60:6.1f} h   {v:7.0f} m   -> {v/(mn/60):5.0f} m/h")
