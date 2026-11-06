"""Test of the candidate rungs on key-confirmed pairs, San Diego and Seattle. Licence keys are hidden from the rungs and used only to score them.
Recovered: the rung's pick is a listing that shares the rival row's key. False pair: the rung's pick is any other listing.
Placebo: the same rows with every true listing removed from the pool, so any pick is false. This is the rung's behaviour on a rival home with no Airbnb twin."""
import sys,glob,math,re,os,json
sys.path.insert(0,os.path.expanduser('~/Downloads/ABNB/rival_overlap/04_analysis/scripts'))
import numpy as np,pandas as pd,ro_common as r
from ro_overlap_lib import air
O=os.path.expanduser('~/Downloads/ABNB/reverse_eng/')
OP={'booking':200,'vrbo':520}
def wil(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return 100*(c-h),100*(c+h)
D={}
for m in ['san_diego','seattle']:
    a=air(m); a=a[a.elig&a.latitude.notna()].reset_index(drop=True)
    d=pd.read_csv(r.P+f'02_interim/candidate_pairs/{m}_rung1.csv'); d=d[~d.type.astype(str).str.contains('hotel|hostel|resort',case=False)]; d=d[d.lat.notna()]
    idx={}
    for i,s in enumerate(a.k):
        for t in s: idx.setdefault(t,set()).add(i)
    a['accommodates']=pd.to_numeric(a.accommodates,errors='coerce'); cap={}
    for f in glob.glob(r.P+f'01_raw/vrbo/{m}/VRBO_*_LISTINGS_*'):
        if 'PILOT' in f or 'FULL' in f:
            for x in json.load(open(f)):
                if x.get('sleeps'): cap[('vrbo',str(x.get('expediaPropertyId')))]=float(x['sleeps'])
    for f in glob.glob(r.P+f'01_raw/booking/{m}/BOOKING_*'):
        if 'PILOT' in f or 'FULL' in f:
            for x in json.load(open(f)):
                g=re.search(r'(?:sleeps|accommodates|up to)\s+(\d{1,2})\s*(?:guests|people|persons|adults)?',str(x.get('description')),re.I)
                if g: cap[('booking',str(x.get('hotelId')))]=float(g.group(1))
    d['cap']=[cap.get((s_,str(i))) for s_,i in zip(d.site,d.id)]; print(m,'capacity known',d.groupby('site').cap.apply(lambda z:round(100*z.notna().mean(),1)).to_dict())
    d['ks']=[set(str(x).split('|'))-{'','nan'} for x in d['keys']]
    d['true']=[set().union(*[idx.get(t,set()) for t in s]) if s else set() for s in d.ks]
    D[m]=(a,d); print(m,'airbnb pool',len(a),'unkeyed in pool',int((a.k.str.len()==0).sum()),'pool columns ok')
def dists(a,x):
    cl=math.cos(math.radians(x.lat)); return 6371000*np.hypot((a.longitude.values-x.lng)*cl*math.pi/180,(a.latitude.values-x.lat)*math.pi/180)
def pick(a,x,dd,R,rung,excl=frozenset()):
    c=np.where(dd<=R)[0]
    if excl: c=np.array([i for i in c if i not in excl],dtype=int)
    if len(c)==0: return None
    if rung in('rung2_nearest','rung2_unique'):
        if rung=='rung2_unique' and len(c)>1: return None
        return int(c[np.argmin(dd[c])])
    if pd.notna(x.bedrooms): c=c[a.bedrooms.values[c]==float(x.bedrooms)]
    if len(c)==0: return None
    if rung=='rung3_beds_nearest': return int(c[np.argmin(dd[c])])
    if rung=='rung3_beds_unique': return int(c[0]) if len(c)==1 else None
    if pd.notna(x.cap): c=c[a.accommodates.values[c]==float(x.cap)]
    if len(c)==0: return None
    if rung=='rung3_beds_cap_nearest': return int(c[np.argmin(dd[c])])
    return int(c[0]) if len(c)==1 else None
RUNGS=['rung2_nearest','rung2_unique','rung3_beds_nearest','rung3_beds_unique','rung3_beds_cap_nearest','rung3_beds_cap_unique']
p95={}
for m,(a,d) in D.items():
    for s in ('booking','vrbo'):
        t=d[(d.site==s)&d.true.str.len().gt(0)]; v=[]
        for x in t.itertuples(): v.append(dists(a,x)[list(x.true)].min())
        p95[(m,s)]=float(np.percentile(v,95)); print(m,s,'true pairs',len(t),'median m',round(float(np.median(v))),'p95',round(p95[(m,s)]))
out=[]; other={'san_diego':'seattle','seattle':'san_diego'}
for m,(a,d) in D.items():
    for s in ('booking','vrbo'):
        T=d[(d.site==s)&d.true.str.len().gt(0)]; U=d[(d.site==s)&~d.keyed.astype(bool)]; Mz=d[(d.site==s)&d.keyed.astype(bool)&d.true.str.len().eq(0)]
        for rs,R in [('own p95 (in sample)',p95[(m,s)]),('other market p95 (out of sample)',p95[(other[m],s)]),('operating radius in ro_overlap_lib',OP[s])]:
            for g in RUNGS:
                rec=fk=fu=no=pf=sr=sn=0; 
                for x in T.itertuples():
                    dd=dists(a,x); q=pick(a,x,dd,R,g); one=len(x.true)==1; sn+=one
                    if q is None: no+=1
                    elif q in x.true: rec+=1; sr+=one
                    elif len(a.k.iat[q])>0: fk+=1
                    else: fu+=1
                    if pick(a,x,dd,R,g,frozenset(x.true)) is not None: pf+=1
                n=len(T); nf=fk+fu; lo,hi=wil(rec,n); plo,phi=wil(pf,n)
                um=sum(pick(a,x,dists(a,x),R,g) is not None for x in U.itertuples()); mm=sum(pick(a,x,dists(a,x),R,g) is not None for x in Mz.itertuples())
                rr=rec/n; fp=pf/n; pi=(um/len(U)-fp)/(rr-fp) if len(U) and rr>fp else np.nan
                out.append(dict(market=m,rival=s,radius_source=rs,radius_m=round(R),rung=g,known_pairs=n,recovered=rec,recovered_pct=round(100*rr,1),recovered_lo=round(lo,1),recovered_hi=round(hi,1),recovered_single_key_pct=round(100*sr/max(1,sn),1),single_key_pairs=sn,false_pairs=nf,false_on_keyed_listing=fk,false_on_unkeyed_listing=fu,no_pick=no,precision_pct=round(100*rec/max(1,rec+nf),1),placebo_false_pairs=pf,placebo_false_pct=round(100*fp,1),placebo_lo=round(plo,1),placebo_hi=round(phi,1),unkeyed_rows=len(U),unkeyed_picked=um,keyed_unjoined_rows=len(Mz),keyed_unjoined_picked=mm,implied_true_share_of_unkeyed_pct=None if pd.isna(pi) else round(100*pi,1)))
                print(m,s,rs[:9],round(R),g,'rec',out[-1]['recovered_pct'],'false',nf,'placebo',out[-1]['placebo_false_pct'],'unk',um,'/',len(U),flush=True)
pd.DataFrame(out).to_csv(O+'match_ladder.csv',index=False); print('saved',len(out))
