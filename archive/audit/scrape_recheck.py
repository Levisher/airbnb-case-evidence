"""Recheck of three scrape results from source files, written for ABNB/reverse_eng. Prints the row count behind every figure and saves scrape_recheck.csv.
Frame: rebuilt from wayback/child and sitemap/universe. Survival: rebuilt from grid/fc_status.csv. Seattle: rebuilt from raw Booking JSON and the Inside Airbnb file with its own key parser, independent of ro_match.py."""
import duckdb,glob,json,math,os,re,collections
import numpy as np,pandas as pd
A=os.path.expanduser('~/Downloads/ABNB/'); I=A+'inventory/'; F=I+'final/'; R=A+'rival_overlap/'; O=A+'reverse_eng/'
rows=[]
def add(block,metric,group,value,unit,prior,n,note=''):
    d=None if prior is None or value is None else round(value-prior,3)
    if prior is None: st='NO PRIOR'
    elif unit=='count': st='REPRODUCED' if value==prior else 'FAIL'
    else: st='REPRODUCED' if abs(d)<=1 else 'FAIL'
    rows.append(dict(block=block,metric=metric,group=group,value=None if value is None else round(value,3),unit=unit,prior=prior,diff=d,rows_behind=n,status=st,note=note))
    print(f"{block:9}|{metric[:52]:52}|{str(group)[:22]:22}|{value if value is None else round(value,2)}|prior {prior}|n {n}|{st}")
def wil(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return c-h,c+h
# ---------- 1 frame
c=duckdb.connect(); c.execute("pragma threads=6")
PAN=['202303','202311','202405','202411','202502','202506','202508','202601','202605']
print('child files on disk',sorted(os.path.basename(f)[:6] for f in glob.glob(I+'wayback/child/*.parquet')))
parts=[f"select id,'{m}' m from read_parquet('{I}wayback/child/{m}.parquet')" for m in PAN]+[f"select id,'202611' m from read_parquet('{I}sitemap/universe.parquet')"]
c.execute(f"create table raw as {' union all '.join(parts)}")
nraw=c.execute("select count(*) from raw").fetchone()[0]
c.execute("create table fr as select id,max((m='202611')::int) now,min(m) first_m,count(distinct m) k from raw where id is not null group by 1")
ever,now=c.execute("select count(*),sum(now) from fr").fetchone(); now=int(now)
add('frame','Unique ids, union of ten snapshots','all',ever,'count',16150130,nraw,'rows = sitemap rows read before de-duplication')
add('frame','Unique ids, November 2026 sitemap','all',now,'count',6934269,now)
add('frame','Ids absent in November 2026','all',ever-now,'count',9215861,ever)
fs=sorted(glob.glob(I+'raw_regions/*.parquet'))
ia=c.execute(f"select regexp_extract(filename,'.*/(.*)_[0-9-]+\\.parquet',1) city,try_cast(id as bigint) id from read_parquet({fs!r},filename=true,union_by_name=true)").df()
ia=ia.dropna().drop_duplicates(['city','id']); c.register('ia',ia)
c.execute("create table j as select ia.city,ia.id,coalesce(fr.now,0) now,(fr.id is not null)::int inframe from ia left join fr using(id)")
t=c.execute("select count(*),sum(now),sum(inframe),count(distinct city) from j").fetchone(); n=t[0]
print('census files',len(fs),'rows',n,'regions',t[3])
add('frame','Census listings inside November sitemap (%)','123 regions',100*t[1]/n,'pct',65.26,n,'prior 1,116,456 of 1,710,831')
add('frame','Census listings inside union frame (%)','123 regions',100*t[2]/n,'pct',None,n)
for city,lab in [('united-state__seattle','Seattle'),('united-state__san-diego','San Diego'),('united-state__hawaii','Hawaii')]:
    q=c.execute(f"select count(*),sum(now),sum(inframe) from j where city='{city}'").fetchone()
    if q[0]:
        add('frame','City file inside November sitemap (%)',lab,100*q[1]/q[0],'pct',None,q[0]); add('frame','City file inside union frame (%)',lab,100*q[2]/q[0],'pct',None,q[0])
pc=c.execute("select city,count(*) n,100.0*sum(inframe)/count(*) u from j group by 1 having count(*)>=500").df()
print('union share across regions with 500+ rows: min',round(pc.u.min(),1),'median',round(pc.u.median(),1),'max',round(pc.u.max(),1),'regions',len(pc))
add('frame','City file inside union frame, median region (%)','regions with 500+ rows',pc.u.median(),'pct',None,int(pc.n.sum()),f'range {pc.u.min():.1f} to {pc.u.max():.1f} over {len(pc)} regions')
# ---------- 2 survival
fc=pd.read_csv(I+'grid/fc_status.csv',dtype={'status':str}); raw_n=len(fc)
print('sample status rows',fc.status.value_counts().to_dict())
fc=fc[fc.status.isin(['200','410','404','301','302','200nojson'])].drop_duplicates('id'); fc['live']=fc.status.eq('200')
add('survival','Dropped ids returning a withdrawn page (%)','all',100*(1-fc.live.mean()),'pct',86.75,len(fc),f'{raw_n} status rows before removing rate limits and duplicates')
v=pd.read_parquet(F+'panel_v.parquet',columns=['id','vy']); c.register('v',v); c.register('fc',fc[['id','live']])
d=c.execute("select fr.id,fr.now,fr.first_m,v.vy,fc.live from fr left join v using(id) left join fc using(id)").df()
d['g']=np.where(d.vy<2023,'Before 2023',d.vy.astype('Int64').astype(str)); d.loc[d.vy>=2025,'g']='2025 and 2026'
print('ids with no id-year',int(d.vy.isna().sum()))
def surv(col,label,priors):
    allv=fc.live.mean()
    for g,t in d.groupby(col):
        e=len(t); nw=int(t.now.sum()); ab=e-nw; s=t[t.live.notna()]; k=int(s.live.sum()); n=len(s)
        lv=k/n if n else allv; lo,hi=wil(k,n) if n else (np.nan,np.nan)
        sv=100*(nw+ab*lv)/e
        add('survival',f'Still viewable, {label} (%)',g,sv,'pct',priors.get(g),n,f'{k} live of {n} sampled absent ids, {e} ids in group, interval {100*(nw+ab*lo)/e:.1f} to {100*(nw+ab*hi)/e:.1f}')
surv('g','by id year',{'2023':39.01,'2024':45.28,'2025 and 2026':75.09,'Before 2023':44.59})
surv('first_m','by first snapshot seen',{})
tot_lv=fc.live.mean(); add('survival','Ids no longer viewable (m)','all',(ever-now)*(1-tot_lv)/1e6,'m',7.99,len(fc),'pooled live rate; difference shown in m')
# ---------- 3 Seattle
K=re.compile(r'STR[\s\-]*(BB[\s\-]*)?OPLI[\s\-]*(\d{2})[\s\-]*(\d{6})',re.I)
def keys(s): return {f"STR{'BB' if x else ''}OPLI{a}{b}" for x,a,b in K.findall(str(s))}
a=pd.read_parquet(sorted(glob.glob(I+'raw_regions/united-state__seattle_*.parquet'))[-1])
for k in ['minimum_nights','calculated_host_listings_count','latitude','longitude','estimated_occupancy_l365d','estimated_revenue_l365d']:
    if k in a: a[k]=pd.to_numeric(a[k],errors='coerce')
price=pd.to_numeric(a.price.astype(str).str.replace(r'[$,]','',regex=True),errors='coerce')
a['nights']=a.estimated_occupancy_l365d; a['rev']=a.estimated_revenue_l365d.fillna(a.nights*price)
a['k']=[keys(x) for x in a.license]; e0=a[(a.minimum_nights<30)&(a.room_type=='Entire home/apt')].copy(); e=e0[e0.k.str.len()>0].copy()
print('seattle file rows',len(a),'eligible',len(e0),'keyed canonical',len(e))
print('other licence text on eligible rows',e0[e0.k.str.len()==0].license.astype(str).str[:12].value_counts().head(5).to_dict())
b={}
for f in sorted(glob.glob(R+'01_raw/booking/seattle/BOOKING_*')):
    for x in json.load(open(f)): b.setdefault(x.get('hotelId') or x.get('url'),x)
rawn=len(b); br=[]
la0,la1,lo0,lo1=e0.latitude.min()-.1,e0.latitude.max()+.1,e0.longitude.min()-.1,e0.longitude.max()+.1
for h,x in b.items():
    l=x.get('location') or {}; lat=float(l.get('lat') or 0); lng=float(l.get('lng') or 0); li=x.get('licenseInfo') or {}
    ks=set()
    for z in (li if isinstance(li,list) else [li]):
        if isinstance(z,dict):
            for nmb in z.get('numbers') or []: ks|=keys(nmb)
    br.append(dict(id=h,type=str(x.get('type')),lat=lat,lng=lng,k=ks,phr=str(li)))
B=pd.DataFrame(br); B=B[B.lat.between(la0,la1)&B.lng.between(lo0,lo1)]; inb=len(B); B=B[~B.type.str.contains('hotel|hostel|resort',case=False)]
print('booking unique',rawn,'in bounds',inb,'non-hotel',len(B),'keyed',int((B.k.str.len()>0).sum()),'not required',int(B.phr.str.contains('does not require').sum()))
add('seattle','Booking rows in the near-census','non-hotel',len(B),'count',773,rawn,'site filter total was 801')
add('seattle','Booking rows with a licence key','non-hotel',int((B.k.str.len()>0).sum()),'count',558,len(B))
add('seattle','Airbnb keyed entire homes under 30 nights','all',len(e),'count',4538,len(e0))
cnt=collections.Counter(t for s in B.k for t in s); S=set(cnt)
e['bk']=[len(s&S)>0 for s in e.k]
e['hs']=pd.cut(e.calculated_host_listings_count,[0,1,5,20,1e6],labels=['1','2-5','6-20','21+'])
add('seattle','Airbnb keyed homes also on Booking (%)','all',100*e.bk.mean(),'pct',12.5,len(e),f'{int(e.bk.sum())} homes')
add('seattle','Share of Airbnb nights on those homes (%)','all',100*e[e.bk].nights.sum()/e.nights.sum(),'pct',12.1,len(e))
add('seattle','Share of Airbnb revenue on those homes (%)','all',100*e[e.bk].rev.sum()/e.rev.sum(),'pct',13.9,len(e))
pri={'1':5.2,'2-5':10.8,'6-20':22.4,'21+':33.7}
for g,t in e.groupby('hs',observed=True):
    k=int(t.bk.sum()); lo,hi=wil(k,len(t)); add('seattle','Airbnb keyed homes also on Booking (%)',f'host size {g}',100*t.bk.mean(),'pct',pri[str(g)],len(t),f'{k} homes, interval {100*lo:.1f} to {100*hi:.1f}')
# floor tests
ak=collections.defaultdict(list)
for i,s in zip(e.index,e.k):
    for t in s: ak[t].append(i)
sh=sum(len(v)>1 for v in ak.values()); print('unique keys',len(ak),'keys on 2+ eligible homes',sh,'homes on shared keys',sum(len(v) for v in ak.values() if len(v)>1))
e['cap']=0.0
for t,v in ak.items():
    if t in S:
        m=min(len(v),cnt[t])
        for i in v: e.loc[i,'cap']=max(e.loc[i,'cap'],m/len(v))
add('seattle','One Booking row per Airbnb home, lower bound (%)','all',100*e.cap.sum()/len(e),'pct',None,len(e),f'{e.cap.sum():.0f} homes; a Booking row can match only as many Airbnb homes as it has rows on that key')
for g,t in e.groupby('hs',observed=True): add('seattle','One Booking row per Airbnb home, lower bound (%)',f'host size {g}',100*t.cap.sum()/len(t),'pct',None,len(t),f'{t.cap.sum():.0f} homes, headline {pri[str(g)]}')
keyhit=sum(1 for t in ak if t in S); add('seattle','Unique Airbnb keys also on Booking (%)','all',100*keyhit/len(ak),'pct',None,len(ak),f'{keyhit} keys')
add('seattle','Unique Airbnb homes matched from Booking rows','Booking keys joined',sum(1 for t in S if t in ak),'count',None,int((B.k.str.len()>0).sum()),'distinct keys on Booking that exist on Airbnb')
U=B[B.k.str.len()==0]; la=e0.latitude.values; lo=e0.longitude.values; hit=0; un=set()
free=e0[~e0.index.isin(e[e.bk].index)]; fl,fo=free.latitude.values,free.longitude.values
for _,r_ in U.iterrows():
    dm=6371000*np.hypot((fo-r_.lng)*np.cos(math.radians(r_.lat))*math.pi/180,(fl-r_.lat)*math.pi/180)
    if (dm<=151).any(): hit+=1
add('seattle','Unkeyed Booking rows with an unmatched Airbnb home within 151 m','non-hotel',hit,'count',None,len(U),'candidates only, 151 m is the keyed-pair p95')
up=(e.bk.sum()+hit+28)/len(e)*100; add('seattle','Ceiling if every candidate and the 28 rows between 801 and 773 matched (%)','all',up,'pct',None,len(e),'loose ceiling on Booking only')
df=pd.DataFrame(rows); df.loc[df.metric.str.contains('lower bound'),'status']='FLOOR TEST'; df.loc[df.metric.str.contains('Ceiling|Unkeyed'),'status']='CEILING TEST'
df.to_csv(O+'scrape_recheck.csv',index=False); print('saved',len(rows))
