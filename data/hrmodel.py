"""Cardiac cost model: heart rate at a given pace.
   HR estimated from Strava relative-effort per hour, calibrated against COROS avg HR
   (n=46 overlap, r=0.91, +-3.5 bpm):   HR = 81.2 + 21.1 * ln(RE/h)
   Jan 2023 - Aug 2026."""
import csv, math, datetime as dt
from collections import defaultdict
D='/Users/stancld/projects/training/data/'
RUN={"Run","RACE_Run","TrailRun"}
CROSS={"Ride","VirtualRide","Hike","Snowshoe","NordicSki","AlpineSki","Swim","Walk"}

acts=[]
for r in csv.DictReader(open(D+'activities.csv')):
    acts.append((dt.date.fromisoformat(r['date']),r['sport'],float(r['km']),float(r['min']),float(r['vert'])))
acts.sort()
wx={}
L=open(D+'weather_raw.csv').read().splitlines()
h=[i for i,l in enumerate(L) if l.startswith('time,')][0]
for l in L[h+1:]:
    if not l.strip(): continue
    p=l.split(',')
    wx[dt.date.fromisoformat(p[0])]=dict(tmean=float(p[1]),tmax=float(p[2]),tmin=float(p[3]),
        tapp=float(p[4]),prcp=float(p[5]),rh=float(p[6]),wind=float(p[7]))
INJ=[dt.date.fromisoformat(x) for x in ["2023-04-04","2024-03-10","2024-08-09","2024-12-17",
  "2025-02-18","2025-04-02","2025-06-05","2026-01-05","2026-04-08","2026-07-14"]]
lab=defaultdict(lambda:[[],[]])
for r in csv.DictReader(open(D+'labels.csv')):
    d=dt.date.fromisoformat(r['date']); lab[d][0].append(r['type'])
    if r['feel'].strip()!='': lab[d][1].append(float(r['feel']))
re_={dt.date.fromisoformat(r['date']):float(r['re']) for r in csv.DictReader(open(D+'re.csv'))}

run_min=defaultdict(float); cross_min=defaultdict(float); gym_min=defaultdict(float)
for d,s,km,mn,v in acts:
    if s in RUN: run_min[d]+=mn
    elif s in CROSS: cross_min[d]+=mn
    else: gym_min[d]+=mn
main={}
for d,s,km,mn,v in acts:
    if s in RUN and mn>=25 and km>=4:
        if d not in main or mn>main[d][1]: main[d]=(km,mn,v)
rd=sorted(main); prev={d:p for p,d in zip(rd,rd[1:])}
def wsum(t,d,n): return sum(t[d-dt.timedelta(days=k)] for k in range(1,n+1))
def tprior(d,n,k='tapp'):
    v=[wx[d-dt.timedelta(days=j)][k] for j in range(1,n+1) if d-dt.timedelta(days=j) in wx]
    return sum(v)/len(v) if v else None

R=[]
for d in sorted(lab):
    if d not in main or d not in wx or d not in re_: continue
    if re_[d]<5: continue
    km,mn,v=main[d]; w=wx[d]
    ta=tprior(d,30)
    if ta is None: continue
    past=[x for x in INJ if x<d]
    a7=wsum(run_min,d,7)/60.0; c28=wsum(run_min,d,28)/60.0/4.0
    ty=lab[d][0]
    R.append(dict(date=d,
        hr=81.2+21.1*math.log(re_[d]/(mn/60.0)),
        ln_spd=math.log(km/(mn/60.0)), vpk=v/max(km,.1), ln_dur=math.log(mn),
        temp=w['tmean'], tapp=w['tapp'], t_anom30=w['tapp']-ta, rh=w['rh'],
        prcp=math.log1p(w['prcp']), wind=w['wind'],
        acute7=a7, chronic28=c28, acwr=a7/c28 if c28>0.5 else 1.0,
        yday=run_min[d-dt.timedelta(days=1)]/60.0,
        rest=min((d-prev[d]).days,7) if d in prev else 1,
        gym7=wsum(gym_min,d,7)/60.0, cross7=wsum(cross_min,d,7)/60.0,
        dsi=math.log1p(min((d-max(past)).days if past else 400,365)),
        hard=1.0 if any(x in ('T','I','R','M','RACE','F') for x in ty) else 0.0,
        long=1.0 if 'L' in ty else 0.0,
        feel=(sum(lab[d][1])/len(lab[d][1])) if lab[d][1] else None,
        t=(d-dt.date(2023,1,1)).days/365.25))
print(f"runs with an HR estimate: {len(R)}   {R[0]['date']} -> {R[-1]['date']}")

def solve(A,b):
    n=len(A);M=[r[:]+[b[i]] for i,r in enumerate(A)]
    for c in range(n):
        p=max(range(c,n),key=lambda r:abs(M[r][c]));M[c],M[p]=M[p],M[c]
        if abs(M[c][c])<1e-11: raise ValueError('singular %d'%c)
        pv=M[c][c]
        for j in range(c,n+1): M[c][j]/=pv
        for r in range(n):
            if r!=c and M[r][c]:
                f=M[r][c]
                for j in range(c,n+1): M[r][j]-=f*M[c][j]
    return [M[i][n] for i in range(n)]
def inv(A):
    n=len(A);M=[r[:]+[1.0 if i==j else 0.0 for j in range(n)] for i,r in enumerate(A)]
    for c in range(n):
        p=max(range(c,n),key=lambda r:abs(M[r][c]));M[c],M[p]=M[p],M[c]
        pv=M[c][c]
        for j in range(c,2*n): M[c][j]/=pv
        for r in range(n):
            if r!=c and M[r][c]:
                f=M[r][c]
                for j in range(c,2*n): M[r][j]-=f*M[c][j]
    return [M[i][n:] for i in range(n)]
def pv_(t): return math.erfc(abs(t)/math.sqrt(2))
def ols(y,X,names,label,show=None,unit=''):
    n=len(y);k=len(X[0])
    XtX=[[sum(X[i][a]*X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty=[sum(X[i][a]*y[i] for i in range(n)) for a in range(k)]
    beta=solve([r[:] for r in XtX],Xty)
    fit=[sum(X[i][j]*beta[j] for j in range(k)) for i in range(n)]
    res=[y[i]-fit[i] for i in range(n)]
    ym=sum(y)/n;ssr=sum(r*r for r in res);sst=sum((q-ym)**2 for q in y)
    s2=ssr/(n-k);Xi=inv(XtX)
    se=[math.sqrt(max(s2*Xi[j][j],0)) for j in range(k)]
    r2=1-ssr/sst
    print(f"\n{'='*74}\n{label}\n{'='*74}")
    print(f"n={n}  params={k}  R2={r2:.3f}  adjR2={1-(1-r2)*(n-1)/(n-k):.3f}  resid sd={math.sqrt(s2):.2f}{unit}")
    print(f"\n{'variable':14} {'beta/SD':>9} {'se':>7} {'t':>7} {'p':>8}")
    idx=[j for j in range(k) if names[j]!='const' and not names[j].startswith('tt')]
    if show: idx=[j for j in idx if names[j] in show]
    for j in sorted(idx,key=lambda j:-abs(beta[j]/se[j]) if se[j] else 0):
        t=beta[j]/se[j] if se[j] else 0;p=pv_(t)
        st='***' if p<.001 else '**' if p<.01 else '*' if p<.05 else '.' if p<.10 else ''
        print(f"{names[j]:14} {beta[j]:9.3f} {se[j]:7.3f} {t:7.2f} {p:8.4f} {st}")
    return beta,se,names

def zed(rows,F):
    st={}
    for f in F:
        v=[r[f] for r in rows];m=sum(v)/len(v)
        sd=math.sqrt(sum((x-m)**2 for x in v)/len(v)) or 1.0
        st[f]=(m,sd)
    return st

def fit(rows,F,label,knot=1.0,show=None):
    st=zed(rows,F)
    tmin=min(r['t'] for r in rows);tmx=max(r['t'] for r in rows)
    kn=[k*knot for k in range(1,20) if tmin+0.3<k*knot<tmx-0.3]
    nm=['const']+F+[f'tt{i}' for i in range(len(kn)+1)]
    X=[[1.0]+[(r[f]-st[f][0])/st[f][1] for f in F]+[r['t']]+[max(0.0,r['t']-k) for k in kn] for r in rows]
    b,se,_=ols([r['hr'] for r in rows],X,nm,label,show=show,unit=' bpm')
    return b,se,nm,st

CTRL=['ln_spd','vpk','ln_dur','hard','long']
COND=['tapp','t_anom30','rh','prcp','wind']
LOAD=['acute7','chronic28','acwr','yday','rest','gym7','cross7','dsi']

print("\n\n>>> ALL RUNS, everything in")
b,se,nm,st=fit(R,CTRL+COND+LOAD,"HR at a given pace ~ conditions + load + injury history")

print("\n\n>>> EASY / LONG RUNS ONLY (comparable aerobic intent)")
EL=[r for r in R if r['hard']==0.0]
b2,se2,nm2,st2=fit(EL,['ln_spd','vpk','ln_dur']+COND+LOAD,
                   "HR at a given pace, easy+long runs only")

print("\n\n>>> effect sizes in bpm")
for v in ['tapp','t_anom30','rh','acute7','chronic28','acwr','gym7','cross7','dsi','rest']:
    j=nm2.index(v)
    print(f"  {v:12} {b2[j]:+6.2f} bpm per 1 SD ({st2[v][1]:.1f} units)   p={pv_(b2[j]/se2[j]):.4f}")

print("\n\n>>> raw check: HR at a given pace, by apparent-temp anomaly vs prior 30d (easy/long runs)")
for lo,hi in [(-20,-5),(-5,-2),(-2,2),(2,5),(5,20)]:
    g=[r for r in EL if lo<=r['t_anom30']<hi]
    if len(g)>=10:
        # crude pace-adjust: residual from a pace-only regression
        print(f"  {lo:+3.0f}..{hi:+3.0f}C  n={len(g):3d}  mean HR {sum(r['hr'] for r in g)/len(g):5.1f} bpm"
              f"   mean pace {sum(math.exp(r['ln_spd']) for r in g)/len(g):.2f} km/h")

print("\n\n>>> does estimated HR agree with the self-reported feel score?")
P=[(r['hr'],r['feel']) for r in R if r['feel'] is not None]
n=len(P);mx=sum(p[0] for p in P)/n;my=sum(p[1] for p in P)/n
sx=math.sqrt(sum((p[0]-mx)**2 for p in P));sy=math.sqrt(sum((p[1]-my)**2 for p in P))
print(f"  n={n}  corr(HR, feel) = {sum((a-mx)*(b_-my) for a,b_ in P)/(sx*sy):+.3f}  (raw, uncontrolled)")

print("\n\n>>> PACE- AND TERRAIN-ADJUSTED HR by apparent-temp anomaly (easy/long runs)")
F0=['ln_spd','vpk','ln_dur']
st0=zed(EL,F0); tmin=min(r['t'] for r in EL); tmx=max(r['t'] for r in EL)
kn=[k*1.0 for k in range(1,20) if tmin+0.3<k*1.0<tmx-0.3]
nm0=['const']+F0+[f'tt{i}' for i in range(len(kn)+1)]
X0=[[1.0]+[(r[f]-st0[f][0])/st0[f][1] for f in F0]+[r['t']]+[max(0.0,r['t']-k) for k in kn] for r in EL]
y0=[r['hr'] for r in EL]
import sys
_o=sys.stdout; sys.stdout=open('/dev/null','w')
b0,_,_=ols(y0,X0,nm0,"")
sys.stdout=_o
for r,x in zip(EL,X0): r['hres']=r['hr']-sum(x[j]*b0[j] for j in range(len(b0)))
for lo,hi in [(-20,-5),(-5,-2),(-2,2),(2,5),(5,20)]:
    g=[r['hres'] for r in EL if lo<=r['t_anom30']<hi]
    if len(g)>=10:
        m=sum(g)/len(g); s=math.sqrt(sum((x-m)**2 for x in g)/len(g))/math.sqrt(len(g))
        print(f"  {lo:+3.0f}..{hi:+3.0f} C   n={len(g):3d}   {m:+5.2f} bpm +-{s:.2f}   "
              f"{'+'*int(max(0,m)*6)}{'-'*int(max(0,-m)*6)}")

print("\n>>> per degree C")
j1=nm2.index('tapp'); j2=nm2.index('t_anom30')
print(f"  +1 C above the month you're adapted to : {b2[j2]/st2['t_anom30'][1]:+.2f} bpm at the same pace")
print(f"  +1 C of sustained (adapted) warmth     : {b2[j1]/st2['tapp'][1]:+.2f} bpm at the same pace")
print(f"  => a 10 C warm snap costs ~{10*b2[j2]/st2['t_anom30'][1]:.1f} bpm; once the month catches up, "
      f"net {10*(b2[j2]/st2['t_anom30'][1]+b2[j1]/st2['tapp'][1]):+.1f} bpm")

print("\n\n>>> does pace-adjusted HR track the self-reported feel score?")
P=[(r['hres'],r['feel']) for r in EL if r['feel'] is not None]
n=len(P);mx=sum(p[0] for p in P)/n;my=sum(p[1] for p in P)/n
sx=math.sqrt(sum((p[0]-mx)**2 for p in P));sy=math.sqrt(sum((p[1]-my)**2 for p in P))
print(f"  n={n}  corr(pace-adjusted HR, feel) = {sum((a-mx)*(c-my) for a,c in P)/(sx*sy):+.3f}")
for lo,hi in [(-2.5,-0.5),(-0.5,0.5),(0.5,2.5)]:
    g=[a for a,c in P if lo<=c<hi]
    if len(g)>=8:
        lb={-2.5:'felt bad',-0.5:'neutral',0.5:'felt good'}[lo]
        print(f"  {lb:10} n={len(g):3d}   pace-adjusted HR {sum(g)/len(g):+5.2f} bpm")

print("\n\n>>> the last 8 weeks vs the rest, on the objective measure")
cut=EL[-1]['date']-dt.timedelta(days=56)
rec=[r for r in EL if r['date']>=cut]; old=[r for r in EL if r['date']<cut]
print(f"  earlier n={len(old)}  pace-adjusted HR {sum(r['hres'] for r in old)/len(old):+.2f} bpm")
print(f"  last 8wk n={len(rec)}  pace-adjusted HR {sum(r['hres'] for r in rec)/len(rec):+.2f} bpm")
