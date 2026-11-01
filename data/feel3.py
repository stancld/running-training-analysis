exec(open('/Users/stancld/projects/training/data/feel2.py').read().split('# ---------------- MODEL A')[0])

A=[]
for d in sorted(lab):
    if d not in main or not lab[d][1] or d not in wx: continue
    r=build(d)
    if not r: continue
    ty=lab[d][0]
    r['feel']=sum(lab[d][1])/len(lab[d][1])
    r['hard']=1.0 if any(x in ('T','I','R','M','RACE','F') for x in ty) else 0.0
    r['long']=1.0 if 'L' in ty else 0.0
    w=wx[d]
    r['tapp']=w['tapp']; r['tmax']=w['tmax']
    r['tapp_anom30']=w['tapp']-(sum(wx[d-dt.timedelta(days=k)]['tapp'] for k in range(1,31) if d-dt.timedelta(days=k) in wx)/30)
    r['heat']=max(0.0,w['tmax']-22.0)         # hours-above-threshold proxy
    r['cold']=max(0.0,2.0-w['tmin'])
    r['humidex']=w['tmean']+0.05*w['rh']
    A.append(r)
print(f"n = {len(A)} labelled runs, {A[0]['date']} -> {A[-1]['date']}")

CORE=['hard','long','dsi','ln_dur','vpk']
def spec(extra,label):
    F=CORE+extra; st=zed(A,F)
    nm=['const']+F
    X=[[1.0]+[(r[f]-st[f][0])/st[f][1] for f in F] for r in A]
    return ols([r['feel'] for r in A],X,nm,label,show=extra)

print("\n### Which temperature variable actually carries the signal? (each added to the same 5 controls)")
for e,l in [(['temp'],'daily mean temp'),(['tmax'],'daily max temp'),(['tapp'],'apparent temp'),
            (['humidex'],'temp + humidity index'),(['heat'],'heat excess above 22C max'),
            (['t_anom30'],'temp anomaly vs prior 30d'),(['tapp_anom30'],'apparent-temp anomaly vs 30d'),
            (['heat','t_anom30'],'heat excess + anomaly together')]:
    spec(e,f"feel ~ {l} + controls")

print("\n\n### Pre-specified model: the three things Dan writes about (heat, load, gym)")
spec(['heat','t_anom30','acwr','acute7','gym7'],"feel ~ heat + acclimatisation + load + gym + controls")

print("\n\n### Full kitchen sink, for reference (18 predictors, n=192 - expect ~1 false positive at p<.05)")
F=CORE+['temp','temp2','heat','t_anom30','rh','prcp','wind','acute7','chronic28','acwr','yday','rest','gym7','cross7']
st=zed(A,F); nm=['const']+F
ols([r['feel'] for r in A],[[1.0]+[(r[f]-st[f][0])/st[f][1] for f in F] for r in A],nm,
    "feel ~ everything")

print("\n\n### Effect size in plain units: fitted feel vs heat excess")
F=CORE+['heat','t_anom30']; st=zed(A,F); nm=['const']+F
b,_=ols([r['feel'] for r in A],[[1.0]+[(r[f]-st[f][0])/st[f][1] for f in F] for r in A],nm,
        "final",show=['heat','t_anom30'])
ih=nm.index('heat'); ia=nm.index('t_anom30')
print(f"\n  per +1 SD heat excess ({st['heat'][1]:.1f} deg-C above a 22C max day): {b[ih]:+.2f} feel points")
print(f"  per +1 SD warm anomaly ({st['t_anom30'][1]:.1f} C warmer than the prior month): {b[ia]:+.2f} feel points")
print(f"  a 32C day vs a 15C day  = {(max(0,32-22)-0)/st['heat'][1]*b[ih]:+.2f} feel points on a -2..+2 scale")

print("\n\n### What changed recently? last 6 weeks vs the 20 months before")
cut=A[-1]['date']-dt.timedelta(days=42)
rec=[r for r in A if r['date']>=cut]; old=[r for r in A if r['date']<cut]
print(f"  recent n={len(rec)}   earlier n={len(old)}")
print(f"  {'variable':14} {'earlier':>9} {'recent':>9} {'change':>9}")
for f in ['feel','heat','temp','t_anom30','acute7','chronic28','acwr','gym7','cross7','dsi','rest']:
    a=sum(r[f] for r in old)/len(old); c=sum(r[f] for r in rec)/len(rec)
    print(f"  {f:14} {a:9.2f} {c:9.2f} {c-a:+9.2f}")
