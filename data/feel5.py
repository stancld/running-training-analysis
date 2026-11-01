exec(open('/Users/stancld/projects/training/data/feel4.py').read().split('CORE=')[0])
A.sort(key=lambda r:r['date'])
def mean(v): return sum(v)/len(v)
def sd(v):
    m=mean(v); return math.sqrt(sum((x-m)**2 for x in v)/max(1,len(v)-1))

print("### Is the recent patch a real level shift or noise?")
for w in (42,56,84):
    cut=A[-1]['date']-dt.timedelta(days=w)
    r=[x['feel'] for x in A if x['date']>=cut]; o=[x['feel'] for x in A if x['date']<cut]
    t=(mean(r)-mean(o))/math.sqrt(sd(r)**2/len(r)+sd(o)**2/len(o))
    print(f"  last {w:2d} days: n={len(r):3d} feel {mean(r):+.2f} vs {mean(o):+.2f} earlier"
          f"   t={t:.2f}  p={math.erfc(abs(t)/math.sqrt(2)):.4f}")

print("\n### Reported feel by temperature anomaly vs the prior 30 days (the one robust effect)")
for lo,hi in [(-20,-5),(-5,-2),(-2,2),(2,5),(5,20)]:
    g=[x['feel'] for x in A if lo<=x['tapp_anom30']<hi]
    if len(g)>=8:
        m=mean(g)
        print(f"  {lo:+3.0f}..{hi:+3.0f} C   n={len(g):3d}   mean feel {m:+.2f} "
              f"+-{sd(g)/math.sqrt(len(g)):.2f}   {'+'*int(max(0,m)*14)}{'-'*int(max(0,-m)*14)}")

print("\n### Context for the last 8 weeks")
cut=A[-1]['date']-dt.timedelta(days=56)
rec=[x for x in A if x['date']>=cut]
print(f"  runs labelled: {len(rec)}   mean feel {mean([x['feel'] for x in rec]):+.2f}")
print(f"  uninterrupted running streak on the last run: {int(math.expm1(A[-1]['streak']))} days")
print(f"  running days in prior 28: {A[-1]['nrun28']}")
print(f"  cross-training h/week (recent vs earlier): "
      f"{mean([x['cross7'] for x in rec]):.1f} vs {mean([x['cross7'] for x in A if x['date']<cut]):.1f}")
print(f"  gym h/week (recent vs earlier): "
      f"{mean([x['gym7'] for x in rec]):.1f} vs {mean([x['gym7'] for x in A if x['date']<cut]):.1f}")

print("\n### Longest injury-free running stretches in the record")
rd=sorted(main); runs=[]; s=rd[0]
for a,b in zip(rd,rd[1:]):
    if (b-a).days>=5: runs.append((s,a,(a-s).days)); s=b
runs.append((s,rd[-1],(rd[-1]-s).days))
for a,b,n in sorted(runs,key=lambda x:-x[2])[:6]:
    print(f"  {a} -> {b}   {n:3d} days unbroken")
