"""Numbers behind exclusivity_claim.md and scrape_limits.md, rebuilt from source files. Saves claim_calc.json."""
import collections,json,math,os,re,sys,numpy as np,pandas as pd
A=os.path.expanduser('~/Downloads/ABNB/'); sys.path.insert(0,A+'rival_overlap/04_analysis/scripts')
import ro_common as r, ro_overlap_lib as L
def wil(k,n,z=1.96):
    if n==0: return (float('nan'),)*2
    p=k/n; d=1+z*z/n; c=(p+z*z/2/n)/d; h=z*math.sqrt(p*(1-p)/n+z*z/4/n/n)/d; return c-h,c+h
O={}
d=pd.read_csv(r.P+'02_interim/candidate_pairs/seattle_rung1.csv',dtype={'id':str}); d=d[~d.type.astype(str).str.contains('hotel|hostel|resort',case=False)]; B=d[d.site=='booking'].copy()
B['kset']=[set(str(x).split('|')) if pd.notna(x) and str(x) else set() for x in B['keys']]
cnt=collections.Counter(t for s in B.kset for t in s); S=set(cnt)
a=L.air('seattle'); e=a[a.elig&(a.k.str.len()>0)].copy(); e['bk']=[len(k&S)>0 for k in e.k]
e['host']=pd.to_numeric(e.calculated_host_listings_count,errors='coerce'); e['av']=pd.to_numeric(e.availability_365,errors='coerce'); e['n']=pd.to_numeric(e.estimated_occupancy_l365d,errors='coerce')
ak=collections.defaultdict(list)
for i,s in zip(e.index,e.k):
    for t in s: ak[t].append(i)
e['cap']=0.0
for t,v in ak.items():
    if t in S:
        m=min(len(v),cnt[t])
        for i in v: e.loc[i,'cap']=max(e.loc[i,'cap'],m/len(v))
N=len(e); match=int(e.bk.sum()); floor=e.cap.sum()
unk=int((~B['keyed']).sum()); notreq=int((B.notreq&~B['keyed']).sum()); miss=int((B['keyed']&~B.hit).sum()); gap=801-len(B)
ceil=match+unk+miss+gap
O['seattle']=dict(homes=N,all_homes=4659,match=match,match_pct=100*match/N,floor=round(floor,1),floor_pct=100*floor/N,unkeyed=unk,unkeyed_notreq=notreq,keyed_miss=miss,gap_rows=gap,ceiling_homes=ceil,ceiling_pct=100*ceil/N,absent=[100-100*ceil/N,100-100*match/N,100-100*floor/N],note17=100*(match+unk)/N,keys_on_booking=sum(1 for t in S if t in ak),joined_rows=int((B['keyed']&B.hit).sum()),nights_share=100*e[e.bk].n.sum()/e.n.sum())
rows=[]
def add(lbl,t):
    k=int(t.bk.sum()); lo,hi=wil(k,len(t)); rows.append(dict(cell=lbl,homes=len(t),share_of_homes=100*len(t)/N,on_booking=k,match_pct=100*k/len(t),lo=100*lo,hi=100*hi,floor_pct=100*t.cap.sum()/len(t),nights_share=100*t.n.sum()/e.n.sum(),open_mean=t.av.mean()))
e['hs']=pd.cut(e.host,[0,1,5,20,1e9],labels=['1','2-5','6-20','21+'])
for g,t in e.groupby('hs',observed=True): add('host '+str(g),t)
sm=e.host<=5; op=e.av<=240
for a_,b_,l in [(sm,op,'1-5 homes, open up to 240 days'),(sm,~op,'1-5 homes, open over 240 days'),(~sm,op,'6+ homes, open up to 240 days'),(~sm,~op,'6+ homes, open over 240 days')]: add(l,e[a_&b_])
O['split']=rows; print(pd.DataFrame(rows).round(1).to_string()); print({k:(round(v,2) if isinstance(v,float) else v) for k,v in O['seattle'].items()})
# survival
F=A+'inventory/final/'; fc=pd.read_csv(F+'framec_rows.csv').drop_duplicates('id'); S_=pd.read_csv(F+'survival.csv').set_index('g'); t=pd.read_csv(F+'panel_totals.csv').iloc[0]
print(fc.groupby('g').live.agg(['sum','size']).to_dict('index')); print(t.to_dict())
sv={}
rng=np.random.default_rng(3); tot=[]
gs=list(S_.index); lv=[int(fc[fc.g==g].live.sum()) for g in gs]; nn=[int((fc.g==g).sum()) for g in gs]
for _ in range(20000):
    gone=0
    for g,k,n in zip(gs,lv,nn): gone+=S_.absent[g]*(1-rng.beta(k+.5,n-k+.5))
    tot.append(gone)
O['gone_stratified_m']=[float(np.percentile(tot,q))/1e6 for q in (2.5,50,97.5)]
for g,k,n in zip(gs,lv,nn):
    lo,hi=wil(k,n); ever,now,ab=S_.ever[g],S_.now[g],S_.absent[g]; sv[g]=dict(live=k,n=n,surv=S_.surv[g]*100,lo=100*(now+ab*lo)/ever,hi=100*(now+ab*hi)/ever,live_lo=100*lo,live_hi=100*hi)
O['surv']=sv; print(sv); print(O['gone_stratified_m'])
json.dump(O,open(A+'audit/claim_calc.json','w'),indent=1,default=float)
