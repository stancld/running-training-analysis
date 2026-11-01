"""What predicts a good day? Two outcomes:
   A) self-reported feel (-2..+2), parsed from Strava descriptions, Jan 2025 - Aug 2026
   B) objective easy-run speed, controlling terrain + fitness drift, 2023-2026
   Pure python OLS (no numpy in this env)."""
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

# labels: date -> (types, mean feel)
lab=defaultdict(lambda:[[],[]])
for r in csv.DictReader(open(D+'labels.csv')):
    d=dt.date.fromisoformat(r['date']); lab[d][0].append(r['type'])
    if r['feel'].strip()!='': lab[d][1].append(float(r['feel']))

run_min=defaultdict(float); run_vert=defaultdict(float)
cross_min=defaultdict(float); gym_min=defaultdict(float)
for d,s,km,mn,v in acts:
    if s in RUN: run_min[d]+=mn; run_vert[d]+=v
    elif s in CROSS: cross_min[d]+=mn
    else: gym_min[d]+=mn

def wsum(t,d,n):  return sum(t[d-dt.timedelta(days=k)] for k in range(1,n+1))
def tprior(d,n):
    v=[wx[d-dt.timedelta(days=k)]['tmean'] for k in range(1,n+1) if d-dt.timedelta(days=k) in wx]
    return sum(v)/len(v) if v else None

# main run of each day = longest
main={}
for d,s,km,mn,v in acts:
    if s in RUN and mn>=25 and km>=4:
        if d not in main or mn>main[d][1]: main[d]=(km,mn,v)

run_days=sorted(main)
prev={d:p for p,d in zip(run_days,run_days[1:])}

def build(d):
    km,mn,v=main[d]; w=wx[d]
    spd=km/(mn/60)
    if not 6.0<spd<18.0: return None
    t30=tprior(d,30)
    if t30 is None: return None
    past=[x for x in INJ if x<d]
    a7=wsum(run_min,d,7)/60.0; c28=wsum(run_min,d,28)/60.0/4.0
    return dict(date=d,spd=spd,ln_dur=math.log(mn),vpk=v/max(km,.1),mn=mn,
        temp=w['tmean'],temp2=(w['tmean']-13.0)**2,tmax=w['tmax'],rh=w['rh'],
        prcp=math.log1p(w['prcp']),wind=w['wind'],
        t_anom30=w['tmean']-t30,
        acute7=a7,chronic28=c28,acwr=a7/c28 if c28>0.5 else 1.0,
        yday=run_min[d-dt.timedelta(days=1)]/60.0,
        rest=min((d-prev[d]).days,7) if d in prev else 1,
        gym7=wsum(gym_min,d,7)/60.0,cross7=wsum(cross_min,d,7)/60.0,
        dsi=math.log1p(min((d-max(past)).days if past else 400,365)),
        t=(d-dt.date(2023,1,1)).days/365.25)

def solve(A,b):
    n=len(A);M=[r[:]+[b[i]] for i,r in enumerate(A)]
    for c in range(n):
        p=max(range(c,n),key=lambda r:abs(M[r][c]));M[c],M[p]=M[p],M[c]
        if abs(M[c][c])<1e-11: raise ValueError('singular col %d'%c)
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
def pv(t): return math.erfc(abs(t)/math.sqrt(2))

def ols(y,X,names,label,show=None,unit=''):
    n=len(y);k=len(X[0])
    XtX=[[sum(X[i][a]*X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    Xty=[sum(X[i][a]*y[i] for i in range(n)) for a in range(k)]
    beta=solve([r[:] for r in XtX],Xty)
    fit=[sum(X[i][j]*beta[j] for j in range(k)) for i in range(n)]
    res=[y[i]-fit[i] for i in range(n)]
    ym=sum(y)/n; ssr=sum(r*r for r in res); sst=sum((v-ym)**2 for v in y)
    s2=ssr/(n-k); Xi=inv(XtX)
    se=[math.sqrt(max(s2*Xi[j][j],0)) for j in range(k)]
    r2=1-ssr/sst
    print(f"\n{'='*76}\n{label}\n{'='*76}")
    print(f"n={n}  params={k}  R2={r2:.3f}  adjR2={1-(1-r2)*(n-1)/(n-k):.3f}  resid sd={math.sqrt(s2):.3f}{unit}")
    print(f"\n{'variable':16} {'beta/SD':>9} {'se':>7} {'t':>7} {'p':>8}")
    idx=[j for j in range(k) if names[j]!='const' and not names[j].startswith('tt')]
    if show: idx=[j for j in idx if names[j] in show]
    for j in sorted(idx,key=lambda j:-abs(beta[j]/se[j]) if se[j] else 0):
        t=beta[j]/se[j] if se[j] else 0; p=pv(t)
        st='***' if p<.001 else '**' if p<.01 else '*' if p<.05 else '.' if p<.10 else ''
        print(f"{names[j]:16} {beta[j]:9.3f} {se[j]:7.3f} {t:7.2f} {p:8.4f} {st}")
    return beta,res

def zed(recs,feats):
    st={}
    for f in feats:
        v=[r[f] for r in recs];m=sum(v)/len(v)
        sd=math.sqrt(sum((x-m)**2 for x in v)/len(v)) or 1.0
        st[f]=(m,sd)
    return st

# ---------------- MODEL A : self-reported feel ----------------
A=[]
for d in sorted(lab):
    if d not in main or not lab[d][1] or d not in wx: continue
    r=build(d)
    if not r: continue
    ty=lab[d][0]
    r['feel']=sum(lab[d][1])/len(lab[d][1])
    r['hard']=1.0 if any(x in ('T','I','R','M','RACE','F') for x in ty) else 0.0
    r['long']=1.0 if 'L' in ty else 0.0
    A.append(r)
F=['temp','temp2','t_anom30','rh','prcp','wind','acute7','chronic28','acwr',
   'yday','rest','gym7','cross7','dsi','ln_dur','vpk','hard','long']
st=zed(A,F)
names=['const']+F+['tt0']
X=[[1.0]+[(r[f]-st[f][0])/st[f][1] for f in F]+[r['t']] for r in A]
y=[r['feel'] for r in A]
print(f"MODEL A - self-reported feel, {A[0]['date']} to {A[-1]['date']}")
bA,resA=ols(y,X,names,"FEEL (-2..+2) ~ weather + load + injury history   [beta per 1 SD of predictor]")

print("\nmean reported feel by daily mean temperature")
for lo,hi in [(-10,0),(0,5),(5,10),(10,15),(15,20),(20,25),(25,40)]:
    g=[r['feel'] for r in A if lo<=r['temp']<hi]
    if len(g)>=6:
        m=sum(g)/len(g)
        print(f"  {lo:4.0f}-{hi:3.0f}C  n={len(g):3d}  mean feel {m:+.2f}  "
              f"{'+'*int(max(0,m)*12)}{'-'*int(max(0,-m)*12)}")
print("\nmean reported feel by days since last injury onset")
for lo,hi in [(0,21),(21,60),(60,120),(120,400)]:
    g=[r['feel'] for r in A if lo<=math.expm1(r['dsi'])<hi]
    if len(g)>=6:
        m=sum(g)/len(g)
        print(f"  {lo:4d}-{hi:4d}d n={len(g):3d}  mean feel {m:+.2f}  "
              f"{'+'*int(max(0,m)*12)}{'-'*int(max(0,-m)*12)}")

# ---------------- MODEL B : objective easy/long-run speed ----------------
B=[]
for d in sorted(lab):
    if d not in main or d not in wx: continue
    ty=lab[d][0]
    if not all(x in ('E','L') for x in ty): continue
    r=build(d)
    if r: B.append(r)
F2=['temp','temp2','t_anom30','rh','prcp','wind','acute7','chronic28','acwr',
    'yday','rest','gym7','cross7','dsi','ln_dur','vpk']
st2=zed(B,F2)
tmax_=max(r['t'] for r in B); tmin_=min(r['t'] for r in B)
knots=[k*0.5 for k in range(1,12) if tmin_+0.25<k*0.5<tmax_-0.25]
names2=['const']+F2+[f'tt{i}' for i in range(len(knots)+1)]
X2=[]
for r in B:
    row=[1.0]+[(r[f]-st2[f][0])/st2[f][1] for f in F2]+[r['t']]+[max(0.0,r['t']-k) for k in knots]
    X2.append(row)
y2=[r['spd'] for r in B]
print(f"\n\nMODEL B - easy/long runs only, {B[0]['date']} to {B[-1]['date']}")
ols(y2,X2,names2,"EASY-RUN SPEED (km/h) ~ same predictors + terrain + 6-monthly fitness spline",unit=' km/h')
