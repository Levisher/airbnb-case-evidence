"""Rung 1 of the match ladder: normalize licence keys on Airbnb, Vrbo and Booking.com, join them, and report coverage. Usage: ro_match.py <market> [PHASE...]. Aggregates to stdout, row-level files to 02_interim."""
import glob,json,math,os,re,sys,collections
import numpy as np,pandas as pd
import ro_common as r
m=sys.argv[1]; PH=sys.argv[2:] or ['PILOT','FULL']
TOK=re.compile(r'[A-Za-z0-9][A-Za-z0-9\-/\.]{3,}')
STOP={'EXEMPT','PENDING','NONE','REQUIRED','NUMBER','LICENSE','LICENCE','REGISTRATION','HOSTED','CITY','HTTPS'}
def toks(s):
    out=set()
    if m=='lisbon':
        return {x for x in re.findall(r'(\d{3,7})\s*/\s*AL',str(s),re.I)}
    for t in TOK.findall(str(s)):
        u=re.sub(r'[^A-Z0-9]','',t.upper())
        if len(u)>=5 and re.search(r'\d',u) and u not in STOP: out.add(u)
    return out
def dist(a,b,c,d):
    k=math.pi/180; return 6371000*math.hypot((b-d)*math.cos((a+c)/2*k)*k,(a-c)*k)
def airbnb():
    if m=='lisbon': a=pd.read_csv(r.P+'01_raw/quarantine_20261105/airbnb/lisbon.csv.gz',low_memory=False)
    else: a=pd.read_parquet(sorted(glob.glob(r.G+r.M[m][0]+'_*.parquet'))[-1])
    a['latitude']=pd.to_numeric(a.latitude,errors='coerce'); a['longitude']=pd.to_numeric(a.longitude,errors='coerce')
    a['bedrooms']=pd.to_numeric(a.bedrooms,errors='coerce'); a['minimum_nights']=pd.to_numeric(a.minimum_nights,errors='coerce')
    return a
a=airbnb(); idx=collections.defaultdict(list)
for i,l in zip(a.index,a.license):
    if pd.notna(l):
        for t in toks(l): idx[t].append(i)
fr=r.frame(m); print(m,'airbnb all',len(a),'eligible',len(fr),'unique keys',len(idx),'keys on 2+ listings',sum(len(v)>1 for v in idx.values()))
c0=(fr.latitude.median(),fr.longitude.median())
def loads(pat):
    o=[]
    for f in sorted(glob.glob(pat)):
        if any(p in f for p in PH):
            o+=json.load(open(f))
    return o
HOT=re.compile(r'hotel|resort|hostel|motel|bed & breakfast|inn\b',re.I)
# Vrbo
v={}
for x in loads(f'{r.P}01_raw/vrbo/{m}/VRBO_*_LISTINGS_*'):
    if x.get('vrboId'): v[str(x['expediaPropertyId'])]=x
det={str(x.get('Property ID')):str(x.get('Raw') or '') for x in loads(f'{r.P}01_raw/vrbo/{m}/VRBO_*_DETAIL_*')}
rows=[]
for k,x in v.items():
    s=det.get(k,''); keys=set()
    if m=='lisbon': keys=toks(s)
    else:
        for g in re.findall(r'(?:Property Registration Number|Registration number|License number|Licence number|Permit number)[:\s]*([^"\\]{3,80})',s,re.I): keys|=toks(g)
    c=x.get('coordinates') or {}
    rows.append(dict(site='vrbo',id=k,title=x.get('title'),type=x.get('propertyType'),lat=c.get('lat'),lng=c.get('lng'),bedrooms=x.get('bedrooms'),host=(x.get('host') or {}).get('name'),keys='|'.join(sorted(keys)),notreq=bool(re.search(r'Registration Number not required',s,re.I))))
b={}
for x in loads(f'{r.P}01_raw/booking/{m}/BOOKING_*'):
    b.setdefault(x.get('hotelId') or x.get('url'),x)
for k,x in b.items():
    li=x.get('licenseInfo') or {}
    nums=[]
    for e in (li if isinstance(li,list) else [li]):
        if isinstance(e,dict): nums+=e.get('numbers') or []
    keys=set()
    for n in nums: keys|=toks(n)
    l=x.get('location') or {}
    W={'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8}
    txt=str(x.get('description') or '')+' '+str(x.get('name') or '')
    br=re.search(r'\b(\d+|one|two|three|four|five|six|seven|eight)[- ]?(?:bedroom|bed room|br\b)',txt,re.I)
    rows.append(dict(site='booking',id=str(k),title=x.get('name'),type=x.get('type'),lat=float(l.get('lat') or 0) or None,lng=float(l.get('lng') or 0) or None,bedrooms=(W.get(br.group(1).lower()) or int(br.group(1))) if br else (0 if re.search(r'\bstudio\b',txt,re.I) else None),host=json.dumps(x.get('hostInfo'))[:80] if x.get('hostInfo') else None,keys='|'.join(sorted(keys)),notreq=bool(re.search('does not require',json.dumps(li)))))
d=pd.DataFrame(rows)
if d.empty: print('no rows'); sys.exit()
la0,la1,lo0,lo1=fr.latitude.min()-.1,fr.latitude.max()+.1,fr.longitude.min()-.1,fr.longitude.max()+.1
inb=d.lat.between(la0,la1)&d.lng.between(lo0,lo1)
print('rows outside market bounds dropped',int((~inb).sum()),d[~inb].groupby('site').size().to_dict()); d=d[inb].copy()
def join(rw):
    best=None;hit=[]
    for t in str(rw['keys']).split('|'):
        if t and t in idx: hit+=idx[t]
    if not hit: return pd.Series([0,None,None,None])
    g=a.loc[list(set(hit))]
    dd=[dist(rw['lat'],rw['lng'],x,y) for x,y in zip(g.latitude,g.longitude)] if rw['lat'] else [np.nan]
    j=int(np.nanargmin(dd)) if rw['lat'] else 0
    return pd.Series([len(g),g.id.iloc[j],dd[j],g.bedrooms.iloc[j]])
d[['ab_n','ab_id','ab_m','ab_beds']]=d.apply(join,axis=1)
d['keyed']=d['keys'].ne('')
d['hit']=d.ab_n>0
d['km_centre']=[dist(c0[0],c0[1],x,y)/1000 if pd.notna(x) else np.nan for x,y in zip(d.lat,d.lng)]
os.makedirs(r.P+'02_interim/candidate_pairs',exist_ok=True); d.to_csv(r.P+f'02_interim/candidate_pairs/{m}_rung1.csv',index=False)
km=[dist(c0[0],c0[1],x,y)/1000 for x,y in zip(fr.latitude,fr.longitude)]
print('airbnb eligible km from centre median',round(np.median(km),1),'p90',round(np.percentile(km,90),1))
for s,g in d.groupby('site'):
    res=g[~g.type.astype(str).str.contains('hotel|hostel|resort',case=False)]
    print(f"{s}: rows {len(g)} non-hotel {len(res)} keyed {int(res.keyed.sum())} ({res.keyed.mean()*100:.0f}%) not-required {int(res.notreq.sum())} joined {int(res.hit.sum())} ({(res.hit.sum()/max(1,res.keyed.sum()))*100:.1f}% of keyed) one-listing keys {int((res.ab_n==1).sum())} multi {int((res.ab_n>1).sum())} median km {res.km_centre.median():.1f} p90 {res.km_centre.quantile(.9):.1f} beds known {int(res.bedrooms.notna().sum())}")
    h=res[res.hit&res.ab_m.notna()].ab_m
    if len(h): print('   metres median',round(h.median()),'p90',round(h.quantile(.9)),'p95',round(h.quantile(.95)),'beds agree',round((res[res.hit].bedrooms.astype(float)==res[res.hit].ab_beds.astype(float)).mean()*100),'%')
    print('   types',g.type.astype(str).value_counts().head(5).to_dict()); print('   sample keys',[x for x in res['keys'] if x][:5])
