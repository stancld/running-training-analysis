exec(open('/Users/stancld/projects/training/data/feel2.py').read().split('# ---------------- MODEL A')[0])

# --- continuity: days since the last running gap of >=5 days ---
rd=sorted(main)
gapend={}
last_break=rd[0]
for a,b in zip(rd,rd[1:]):
    gapend[b]=last_break
    if (b-a).days>=5: last_break=b
gapend[rd[0]]=rd[0]

A=[]
for d in sorted(lab):
    if d not in main or not lab[d][1] or d not in wx: continue
    r=build(d)
    if not r: continue
    ty=lab[d][0]; w=wx[d]
    r['feel']=sum(lab[d][1])/len(lab[d][1])
    r['hard']=1.0 if any(x in ('T','I','R','M','RACE','F') for x in ty) else 0.0
    r['long']=1.0 if 'L' in ty else 0.0
    r['tapp_anom30']=w['tapp']-(sum(wx[d-dt.timedelta(days=k)]['tapp'] for k in range(1,31) if d-dt.timedelta(days=k) in wx)/30)
    r['streak']=math.log1p(min((d-gapend.get(d,d)).days,200))
    r['nrun28']=sum(1 for k in range(1,29) if run_min[d-dt.timedelta(days=k)]>0)
    A.append(r)

CORE=['hard','long','ln_dur','vpk']
def run(extra,label,show=None):
    F=CORE+extra; st=zed(A,F); nm=['const']+F
    X=[[1.0]+[(r[f]-st[f][0])/st[f][1] for f in F] for r in A]
    b,res=ols([r['feel'] for r in A],X,nm,label,show=show or extra)
    return F,st,nm,b,res

print("### Does training CONTINUITY matter more than load volume?")
run(['streak'],"feel ~ uninterrupted-running streak + controls")
run(['nrun28'],"feel ~ number of running days in prior 28 + controls")
run(['dsi'],"feel ~ days since last injury onset + controls")

print("\n### The model I'd actually keep")
F,st,nm,b,res=run(['tapp_anom30','streak','acwr','gym7'],
    "feel ~ temp anomaly + continuity + acute:chronic + gym load + session type")

print("\n\n### 8-week rolling mean of reported feel (is the current patch unusual?)")
A.sort(key=lambda r:r['date'])
for i in range(len(A)):
    pass
step=[]
d0=A[0]['date']
while d0<=A[-1]['date']:
    g=[r['feel'] for r in A if d0<=r['date']<d0+dt.timedelta(days=56)]
    if len(g)>=5:
        m=sum(g)/len(g)
        bar=('+'*int(max(0,m)*14)) or ('-'*int(max(0,-m)*14))
        step.append(f"  {d0} n={len(g):2d}  {m:+.2f}  {bar}")
    d0+=dt.timedelta(days=28)
print("\n".join(step))

print("\n\n### Does the model explain the last 6 weeks, or is it a residual surprise?")
cut=A[-1]['date']-dt.timedelta(days=42)
fit=[sum(X*Bb for X,Bb in zip([1.0]+[(r[f]-st[f][0])/st[f][1] for f in F],b)) for r in A]
rec=[(r,f) for r,f in zip(A,fit) if r['date']>=cut]
old=[(r,f) for r,f in zip(A,fit) if r['date']<cut]
def sm(g,k): return sum(x[k] for x in g)/len(g)
print(f"  earlier (n={len(old)}): actual feel {sm(old,0) if 0 else sum(r['feel'] for r,_ in old)/len(old):+.2f}"
      f"   model-predicted {sum(f for _,f in old)/len(old):+.2f}")
print(f"  last 6wk (n={len(rec)}): actual feel {sum(r['feel'] for r,_ in rec)/len(rec):+.2f}"
      f"   model-predicted {sum(f for _,f in rec)/len(rec):+.2f}")
print("\n  contribution of each term to the recent-vs-earlier gap (feel points):")
tot=0
for j,f in enumerate(F,start=1):
    da=(sum(r[f] for r,_ in rec)/len(rec)-sum(r[f] for r,_ in old)/len(old))/st[f][1]*b[j]
    tot+=da
    print(f"    {f:14} {da:+.3f}")
print(f"    {'TOTAL explained':14} {tot:+.3f}")
print(f"    {'unexplained':14} "
      f"{(sum(r['feel'] for r,_ in rec)/len(rec)-sum(r['feel'] for r,_ in old)/len(old))-tot:+.3f}")
