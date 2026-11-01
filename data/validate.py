import csv,math,datetime as dt
from collections import defaultdict
acts={}
for r in csv.DictReader(open('activities.csv')):
    d=dt.date.fromisoformat(r['date'])
    if r['sport'] in ("Run","RACE_Run","TrailRun"):
        mn=float(r['min'])
        if d not in acts or mn>acts[d][1]: acts[d]=(float(r['km']),mn,float(r['vert']))
re_={dt.date.fromisoformat(r['date']):float(r['re']) for r in csv.DictReader(open('re.csv'))}
hr={}
for r in csv.DictReader(open('hr.csv')):
    d=dt.date.fromisoformat(r['date'])
    if d not in hr or float(r['min'])>hr[d][0]: hr[d]=(float(r['min']),float(r['hr']))
P=[]
for d in sorted(set(re_)&set(hr)&set(acts)):
    km,mn,v=acts[d]
    if abs(hr[d][0]-mn)>8: continue          # make sure it's the same run
    P.append((math.log(re_[d]/(mn/60)),hr[d][1],d))
def corr(a,b):
    n=len(a);ma=sum(a)/n;mb=sum(b)/n
    sa=math.sqrt(sum((x-ma)**2 for x in a));sb=math.sqrt(sum((x-mb)**2 for x in b))
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/(sa*sb)
x=[p[0] for p in P];y=[p[1] for p in P]
print(f"overlap where Strava relative-effort AND COROS avg HR exist for the same run: n={len(P)}")
print(f"  corr( log(relative_effort per hour) , COROS avg HR ) = {corr(x,y):.3f}")
n=len(x);mx=sum(x)/n;my=sum(y)/n
b=sum((a-mx)*(c-my) for a,c in zip(x,y))/sum((a-mx)**2 for a in x); a0=my-b*mx
res=[c-(a0+b*a) for a,c in zip(x,y)]
print(f"  regression: avgHR = {a0:.1f} + {b:.1f} * log(RE/h)   residual sd = "
      f"{math.sqrt(sum(r*r for r in res)/(n-2)):.1f} bpm")
print(f"  => relative-effort per hour recovers avg HR to about +-{math.sqrt(sum(r*r for r in res)/(n-2)):.0f} bpm")
