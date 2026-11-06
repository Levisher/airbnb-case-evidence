"""Overlap tables from rung 1, rung 2 recall test, Vrbo and Booking.com cross-check, and the Seattle reverse rate from the near-census of Booking.com."""
import glob,math,re,sys
import numpy as np,pandas as pd,ro_common as r
import importlib
RAD={'vrbo':520,'booking':200}
out=[]; rec=[]
def toks(m,s):
    if m=='lisbon': return set(re.findall(r'(\d{3,7})\s*/\s*AL',str(s),re.I))
    o=set()
    for t in re.findall(r'[A-Za-z0-9][A-Za-z0-9\-/\.]{3,}',str(s)):
        u=re.sub(r'[^A-Z0-9]','',t.upper())
        if len(u)>=5 and re.search(r'\d',u): o.add(u)
    return o
def air(m):
    a=pd.read_csv(r.P+'01_raw/quarantine_20261105/airbnb/lisbon.csv.gz',low_memory=False) if m=='lisbon' else pd.read_parquet(sorted(glob.glob(r.G+r.M[m][0]+'_*.parquet'))[-1])
    for k in ['latitude','longitude','bedrooms','minimum_nights','calculated_host_listings_count']: a[k]=pd.to_numeric(a[k],errors='coerce')
    a['k']=[toks(m,l) if pd.notna(l) else set() for l in a.license]
    a['elig']=(a.minimum_nights<30)&a.room_type.eq('Entire home/apt')
    return a
for m in ['san_diego','seattle','hawaii','lisbon']:
    d=pd.read_csv(r.P+f'02_interim/candidate_pairs/{m}_rung1.csv')
    d=d[~d.type.astype(str).str.contains('hotel|hostel|resort',case=False)]
    a=air(m); nk=a[(a.k.str.len()==0)&a.elig]
    la=nk.latitude.values; lo=nk.longitude.values; be=nk.bedrooms.values
    A=a.set_index('id'); cl=math.cos(math.radians(a.latitude.mean()))
    for s,g in d.groupby('site'):
        keyed=g[g['keyed']]; hit=keyed[keyed.hit]; miss=keyed[~keyed.hit]; nok=g[~g['keyed']]
        # rung 2 on misses and unkeyed rows: Airbnb listings with no key, in radius, same bedrooms
        def cand(x):
            if pd.isna(x.lat): return 0
            dd=np.hypot((la-x.lat)*111000,(lo-x.lng)*111000*cl); c=dd<RAD[s]
            if pd.notna(x.bedrooms): c=c&(be==float(x.bedrooms))
            return int(c.sum())
        cm=miss.apply(cand,axis=1) if len(miss) else pd.Series(dtype=int)
        out.append(dict(market=m,site=s,rows=len(g),keyed=len(keyed),key_share=round(len(keyed)/len(g)*100,1),joined=len(hit),joined_pct=round(len(hit)/max(1,len(keyed))*100,1),one_listing=int((hit.ab_n==1).sum()),multi=int((hit.ab_n>1).sum()),beds_agree_pct=round((hit.bedrooms.astype(float)==hit.ab_beds.astype(float))[hit.bedrooms.notna()].mean()*100,1) if hit.bedrooms.notna().any() else None,
            miss=len(miss),miss_with_unkeyed_candidate=int((cm>0).sum()),not_required=int(g.notreq.sum()),no_key=len(nok)))
        # recall of the fallback on key-confirmed pairs
        h=hit[hit.ab_m.notna()&hit.ab_id.notna()]
        if len(h):
            ok=(h.ab_m<RAD[s])
            bd=(h.bedrooms.astype(float)==h.ab_beds.astype(float))|h.bedrooms.isna()
            rec.append(dict(market=m,site=s,pairs=len(h),in_radius=round(ok.mean()*100,1),radius_and_beds=round((ok&bd).mean()*100,1)))
    # Vrbo vs Booking keys
    v=set(); b=set()
    for x in d[d.site=='vrbo']['keys'].dropna(): v|=set(str(x).split('|'))
    for x in d[d.site=='booking']['keys'].dropna(): b|=set(str(x).split('|'))
    print(m,'vrbo keys',len(v),'booking keys',len(b),'both',len(v&b))
    if m=='seattle':
        e=a[a.elig&(a.k.str.len()>0)].copy()
        e['bk']=[len(x&b)>0 for x in e.k]
        e['size']=pd.cut(e.calculated_host_listings_count,[0,1,5,20,1e6],labels=['1','2-5','6-20','21+'])
        print('SEATTLE reverse: eligible Airbnb listings with key',len(e),'also on Booking.com',int(e.bk.sum()),round(e.bk.mean()*100,1),'%')
        print(e.groupby('size',observed=True).bk.agg(['size','sum','mean']).round(3).to_string())
    # host size of matched Airbnb listings vs frame, both rivals
    fr=a[a.elig]
    size=lambda s:pd.cut(s,[0,1,5,20,1e6],labels=['1','2-5','6-20','21+']).value_counts(normalize=True).sort_index().round(3).to_dict()
    print(m,'airbnb eligible host size',size(fr.calculated_host_listings_count))
    for s,g in d.groupby('site'):
        ids=g[g.hit&g.ab_id.notna()].ab_id
        ids=[i for i in ids if i in A.index or str(int(i)) in A.index]
        if ids:
            try: hs=A.loc[[i if i in A.index else str(int(i)) for i in ids]].calculated_host_listings_count
            except Exception: hs=pd.Series(dtype=float)
            print('   ',s,'matched host size',size(hs))
o=pd.DataFrame(out); o.to_csv(r.P+'03_derived/market_overlap.csv',index=False); print(o.to_string(index=False))
q=pd.DataFrame(rec); q.to_csv(r.P+'03_derived/fallback_recall.csv',index=False); print(q.to_string(index=False))
