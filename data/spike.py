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
     "2025-04-02","2025-06-05","2026-01-05","2026-04-08"]   # crash + post-race excluded
injw={monday(dt.date.fromisoformat(x)) for x in INJ}

print("Does a >=1.5x week-over-week jump in RUN HOURS predict injury?\n")
spike=set(); 
for a,b in zip(weeks,weeks[1:]):
    pa,pb=wk[a][0]/60,wk[b][0]/60
    if pa>=1.0 and pb/pa>=1.5 and pb>=5.0:
        spike.add(b)
# an injury 'follows' a spike if onset week == spike week or the week after
hit=0
for s in spike:
    if s in injw or (s+dt.timedelta(weeks=1)) in injw: hit+=1
covered=sum(1 for i in injw if i in spike or (i-dt.timedelta(weeks=1)) in spike)
tot=len(weeks)
print(f"  total weeks analysed            : {tot}")
print(f"  weeks that were a >=1.5x spike  : {len(spike)}  ({len(spike)/tot:.0%} of all weeks)")
print(f"  spikes followed by an injury    : {hit}/{len(spike)}  ({hit/len(spike):.0%})")
print(f"  injuries preceded by a spike    : {covered}/{len(injw)}  ({covered/len(injw):.0%})")
print(f"  base rate of injury in any week : {len(injw)}/{tot} = {len(injw)/tot:.1%}")
print(f"  -> relative risk after a spike  : {(hit/len(spike))/(len(injw)/tot):.1f}x\n")

print("The spike weeks that did NOT lead to injury (for honesty):")
for s in sorted(spike):
    if not (s in injw or (s+dt.timedelta(weeks=1)) in injw):
        print(f"    {s}  {wk[s][0]/60:.1f}h")
