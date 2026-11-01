"""Which conditions predict a good run?
   OLS on per-run grade/duration-adjusted speed anomaly, 2023-01 -> 2026-08.
   Pure python (no numpy in this env)."""
import csv, math, datetime as dt
from collections import defaultdict

D = '/Users/stancld/projects/training/data/'
RUN   = {"Run","RACE_Run","TrailRun"}
CROSS = {"Ride","VirtualRide","Hike","Snowshoe","NordicSki","AlpineSki","Swim","Walk"}

# ---------- data ----------
acts=[]
for r in csv.DictReader(open(D+'activities.csv')):
    acts.append((dt.date.fromisoformat(r['date']), r['sport'],
                 float(r['km']), float(r['min']), float(r['vert'])))
acts.sort()

wx={}
lines=[l for l in open(D+'weather_raw.csv').read().splitlines()]
hdr=[i for i,l in enumerate(lines) if l.startswith('time,')][0]
for l in lines[hdr+1:]:
    if not l.strip(): continue
    p=l.split(',')
    wx[dt.date.fromisoformat(p[0])]=dict(tmean=float(p[1]),tmax=float(p[2]),tmin=float(p[3]),
        tapp=float(p[4]),prcp=float(p[5]),rh=float(p[6]),wind=float(p[7]))

INJ=[dt.date.fromisoformat(x) for x in
     ["2023-04-04","2024-03-10","2024-08-09","2024-12-17","2025-02-18","2025-04-02",
      "2025-06-05","2026-01-05","2026-04-08","2026-07-14"]]

# ---------- daily load ----------
run_min=defaultdict(float); run_vert=defaultdict(float)
cross_min=defaultdict(float); gym_min=defaultdict(float)
for d,s,km,mn,v in acts:
    if s in RUN: run_min[d]+=mn; run_vert[d]+=v
    elif s in CROSS: cross_min[d]+=mn
    else: gym_min[d]+=mn

def wsum(tbl,d,n,skip_today=True):
    a=1 if skip_today else 0
    return sum(tbl[d-dt.timedelta(days=k)] for k in range(a,n+a))

def tmean_prior(d,n):
    v=[wx[d-dt.timedelta(days=k)]['tmean'] for k in range(1,n+1) if d-dt.timedelta(days=k) in wx]
    return sum(v)/len(v) if v else None

# ---------- build rows ----------
recs=[]
run_days=sorted({d for d,s,*_ in acts if s in RUN})
prev_run={d:p for p,d in zip(run_days,run_days[1:])}
for d,s,km,mn,v in acts:
    if s not in RUN or d not in wx: continue
    if mn<25 or km<4: continue                      # drop shakeouts / strides
    if d < dt.date(2023,1,15): continue             # need 14d of history
    spd=km/(mn/60)
    if not 6.0<spd<18.0: continue                   # junk / bad GPS
    t30=tmean_prior(d,30); t7=tmean_prior(d,7)
    if t30 is None: continue
    past=[x for x in INJ if x<d]
    dsi=(d-max(past)).days if past else 400
    a7=wsum(run_min,d,7)/60.0
    c28=wsum(run_min,d,28)/60.0/4.0
    w=wx[d]
    recs.append(dict(
        date=d, spd=spd, ln_dur=math.log(mn), vpk=v/max(km,.1), km=km, mn=mn, vert=v,
        temp=w['tmean'], tapp=w['tapp'], tmax=w['tmax'], rh=w['rh'],
        prcp=math.log1p(w['prcp']), wind=w['wind'],
        t_anom30=w['tmean']-t30, t_anom7=w['tmean']-t7,
        acute7=a7, chronic28=c28, acwr=a7/c28 if c28>0.5 else 1.0,
        yday=run_min[d-dt.timedelta(days=1)]/60.0,
        rest=min((d-prev_run[d]).days,7) if d in prev_run else 1,
        gym7=wsum(gym_min,d,7)/60.0, cross7=wsum(cross_min,d,7)/60.0,
        dsi=math.log1p(min(dsi,365)),
        t=(d-dt.date(2023,1,1)).days/365.25))
print(f"runs in model: {len(recs)}   {recs[0]['date']} -> {recs[-1]['date']}")

# ---------- linear-algebra ----------
def solve(A,b):
    n=len(A); M=[row[:]+[b[i]] for i,row in enumerate(A)]
    for c in range(n):
        p=max(range(c,n),key=lambda r:abs(M[r][c])); M[c],M[p]=M[p],M[c]
        if abs(M[c][c])<1e-12: raise ValueError('singular')
        pv=M[c][c]
        for j in range(c,n+1): M[c][j]/=pv
        for r in range(n):
            if r!=c and M[r][c]:
                f=M[r][c]
                for j in range(c,n+1): M[r][j]-=f*M[c][j]
    return [M[i][n] for i in range(n)]

def inv(A):
    n=len(A); M=[row[:]+[1.0 if i==j else 0.0 for j in range(n)] for i,row in enumerate(A)]
    for c in range(n):
        p=max(range(c,n),key=lambda r:abs(M[r][c])); M[c],M[p]=M[p],M[c]
        pv=M[c][c]
        for j in range(c,2*n): M[c][j]/=pv
        for r in range(n):
            if r!=c and M[r][c]:
                f=M[r][c]
                for j in range(c,2*n): M[r][j]-=f*M[c][j]
    return [M[i][n:] for i in range(n)]

def pval(t):
    return math.erfc(abs(t)/math.sqrt(2))

def ols(y,X,names,label):
    n=len(y); k=len(X[0])
    XtX=[[sum(X[i][a]*X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty=[sum(X[i][a]*y[i] for i in range(n)) for a in range(k)]
    beta=solve([r[:] for r in XtX],Xty)
    fit=[sum(X[i][j]*beta[j] for j in range(k)) for i in range(n)]
    res=[y[i]-fit[i] for i in range(n)]
    ym=sum(y)/n
    ssr=sum(r*r for r in res); sst=sum((v-ym)**2 for v in y)
    s2=ssr/(n-k); XtXi=inv(XtX)
    se=[math.sqrt(max(s2*XtXi[j][j],0)) for j in range(k)]
    r2=1-ssr/sst; adj=1-(1-r2)*(n-1)/(n-k)
    print(f"\n{'='*78}\n{label}\n{'='*78}")
    print(f"n={n}  k={k}  R2={r2:.3f}  adjR2={adj:.3f}  resid sd={math.sqrt(s2):.3f} km/h")
    print(f"\n{'variable':22} {'beta':>9} {'se':>8} {'t':>7} {'p':>8}")
    order=sorted(range(k),key=lambda j:-abs(beta[j]/se[j]) if se[j] else 0)
    for j in order:
        if names[j]=='const': continue
        if names[j].startswith('tt'): continue
        t=beta[j]/se[j] if se[j] else 0
        star='***' if pval(t)<.001 else '**' if pval(t)<.01 else '*' if pval(t)<.05 else ''
        print(f"{names[j]:22} {beta[j]:9.4f} {se[j]:8.4f} {t:7.2f} {pval(t):8.4f} {star}")
    return beta,res,fit

# ---------- standardise ----------
FEAT=['ln_dur','vpk','temp','temp2','t_anom30','rh','prcp','wind',
      'acute7','acwr','yday','rest','gym7','cross7','dsi']
for r in recs:
    r['temp2']=(r['temp']-14.0)**2
stats={}
for f in FEAT:
    v=[r[f] for r in recs]; m=sum(v)/len(v)
    sd=math.sqrt(sum((x-m)**2 for x in v)/len(v)) or 1.0
    stats[f]=(m,sd)

# quarterly linear-spline basis for fitness drift
tmax_=max(r['t'] for r in recs)
import os
KN=float(os.environ.get('KNOT','1.0'))
knots=[k*KN for k in range(1,40) if k*KN < tmax_-0.15]
names=['const']+FEAT+[f'tt{i}' for i in range(len(knots)+1)]
X=[];y=[]
for r in recs:
    row=[1.0]+[(r[f]-stats[f][0])/stats[f][1] for f in FEAT]
    row.append(r['t'])
    row += [max(0.0, r['t']-k) for k in knots]
    X.append(row); y.append(r['spd'])
beta,res,fit=ols(y,X,names,
  "SPEED (km/h) ~ conditions + load + fitness-drift spline   [betas per 1 SD]")

for r,e in zip(recs,res): r['resid']=e

# ---------- descriptives on the residual ----------
def bins(key,edges,label):
    print(f"\n{label}")
    print(f"  {'bin':>16} {'n':>4} {'mean resid':>11} {'sd':>6}")
    for lo,hi in zip(edges,edges[1:]):
        g=[r['resid'] for r in recs if lo<=r[key]<hi]
        if len(g)<8: continue
        m=sum(g)/len(g); sd=math.sqrt(sum((x-m)**2 for x in g)/len(g))
        print(f"  {lo:6.1f}-{hi:6.1f} {len(g):4d} {m:11.3f} {sd:6.2f}  {'+'*int(max(0,m)*40)}{'-'*int(max(0,-m)*40)}")
bins('temp',[-10,0,5,10,15,20,25,35],'RESIDUAL SPEED by daily mean temperature (deg C)')
bins('t_anom30',[-15,-6,-3,0,3,6,15],'RESIDUAL SPEED by temp anomaly vs prior 30d')
bins('acwr',[0,.6,.9,1.1,1.4,5],'RESIDUAL SPEED by acute:chronic run-hours ratio')
bins('acute7',[0,3,5,7,9,20],'RESIDUAL SPEED by run hours in prior 7 days')

print("\nRESIDUAL SPEED by calendar month")
mo=defaultdict(list)
for r in recs: mo[r['date'].month].append(r['resid'])
for m in range(1,13):
    g=mo[m]; mm=sum(g)/len(g)
    print(f"  {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[m-1]} {len(g):4d} {mm:7.3f}  {'+'*int(max(0,mm)*40)}{'-'*int(max(0,-mm)*40)}")

print("\nSPREAD CHECK - is the residual dominated by workout type?")
q=sorted(r['resid'] for r in recs)
print(f"  residual deciles: " + " ".join(f"{q[int(p*len(q))]:+.2f}" for p in [.1,.25,.5,.75,.9]))
print(f"  overall sd {math.sqrt(sum(x*x for x in q)/len(q)):.3f} km/h")
