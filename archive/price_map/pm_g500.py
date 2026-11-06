"""500 m layer, all direct Google: hotels with review counts (Nearby Enterprise), grocery, pharmacy and transit (Nearby Pro), beaches (Nearby Pro), walk times (Routes), sights for ten model cities and 123 regions (Text Search)."""
import json,math,os,re,sys,glob,time,numpy as np,pandas as pd
from concurrent.futures import ThreadPoolExecutor as TP
import pm_gmp as g
from pm_loc import hav
W=g.W; N='https://places.googleapis.com/v1/places:searchNearby'
def nb(lat,lon,rad,types,mask,rank='POPULARITY'):
    r=g.post(N,{'includedTypes':types,'maxResultCount':20,'rankPreference':rank,'locationRestriction':{'circle':{'center':{'latitude':lat,'longitude':lon},'radius':rad}}},{'X-Goog-FieldMask':mask})
    return r.get('places',[]) if 'err' not in r else None
c1=pd.read_parquet(W+'cells.parquet')
# 500 m cells
C=[]
for m in g.CFG:
    d=g.frame(m); la=d.latitude.mean(); dl=.0045; do=dl/math.cos(math.radians(la))
    cy=np.floor(d.latitude/dl).astype(int); cx=np.floor(d.longitude/do).astype(int); k=pd.DataFrame({'cy':cy,'cx':cx}).value_counts().reset_index(name='n'); k=k[k.n>=3]
    k['lat']=(k.cy+.5)*dl; k['lon']=(k.cx+.5)*do; k['market']=m; k['dl']=dl; k['do']=do; C.append(k)
C=pd.concat(C,ignore_index=True); print('cells',len(C),flush=True)
# hotels: Nearby Enterprise, one call per 1 km cell with a hotel, four quadrants where the cell holds over 18
J=[]
for r in c1[c1.hotel>0].itertuples():
    if r.hotel>18: J+=[(r.market,r.lat+a*.0032,r.lon+b*.0032/math.cos(math.radians(r.lat)),380) for a in(-1,1) for b in(-1,1)]
    else: J.append((r.market,r.lat,r.lon,750))
print('hotel calls',len(J),flush=True); assert len(J)<=980
def hj(a):
    p=nb(a[1],a[2],a[3],['hotel'],'places.id,places.location,places.userRatingCount,places.rating,places.primaryType')
    return [(a[0],x['id'],x['location']['latitude'],x['location']['longitude'],x.get('userRatingCount',0),x.get('rating')) for x in (p or [])]
with TP(10) as ex: H=[y for x in ex.map(hj,J) for y in x]
H=pd.DataFrame(H,columns=['market','pid','lat','lon','reviews','rating']).drop_duplicates('pid'); H.to_parquet(W+'hotels.parquet'); print('hotels',H.groupby('market').size().to_dict(),flush=True)
# grocery plus pharmacy, and transit: Nearby Pro at 500 m by distance
M='places.id,places.location,places.types'
def am(a):
    i,la,lo=a
    x=nb(la,lo,500,['grocery_store','supermarket','pharmacy'],M,'DISTANCE'); y=nb(la,lo,750,['subway_station','train_station','light_rail_station','transit_station','bus_station'],M,'DISTANCE')
    gr=[p for p in (x or []) if set(p['types'])&{'grocery_store','supermarket'}]; ph=[p for p in (x or []) if 'pharmacy' in p['types']]
    ds=[hav(la,lo,p['location']['latitude'],p['location']['longitude']) for p in (y or [])]
    return i,len(gr),len(ph),len(y or []),min(ds) if ds else np.nan
with TP(10) as ex: A=list(ex.map(am,[(i,r.lat,r.lon) for i,r in enumerate(C.itertuples())]))
A=pd.DataFrame(A,columns=['i','groc500','pharm500','tr750','tr_km']).set_index('i'); C=C.join(A); C.to_parquet(W+'cells500.parquet'); print('amenity done',flush=True)
# beaches: Nearby Pro on 5 km tiles
B=[]
for m,x in C.groupby('market'):
    la=np.arange(x.lat.min()-.03,x.lat.max()+.04,.06); lo=np.arange(x.lon.min()-.03,x.lon.max()+.04,.06/math.cos(math.radians(x.lat.mean())))
    T=[(a,b) for a in la for b in lo if hav(a,b,x.lat.values,x.lon.values).min()<8]
    with TP(8) as ex: R=list(ex.map(lambda t:nb(t[0],t[1],5000,['beach'],'places.id,places.location'),T))
    for p in [y for r in R for y in (r or [])]: B.append((m,p['id'],p['location']['latitude'],p['location']['longitude']))
B=pd.DataFrame(B,columns=['market','pid','lat','lon']).drop_duplicates('pid'); B.to_parquet(W+'beaches.parquet'); print('beaches',B.groupby('market').size().to_dict(),flush=True)
# walk times to nearest of top 5, 10, 20 sights and nearest beach within 2.5 km
S=pd.read_csv(W+'sights.csv'); S=S[S.name!='AIRPORT']; n_el=0; rows=[]
def rj(r):
    s=S[S.market==r.market].sort_values('reviews',ascending=False); dest={}; o={}
    for t in (5,10,20):
        q=s.head(t); k=int(np.argmin(hav(r.lat,r.lon,q.lat.values,q.lon.values))); o[f'k{t}']=hav(r.lat,r.lon,q.lat.values,q.lon.values)[k]; dest.setdefault((q.lat.values[k],q.lon.values[k]),[]).append(f'w{t}')
    b=B[B.market==r.market]
    if len(b):
        dd=hav(r.lat,r.lon,b.lat.values,b.lon.values); k=int(np.argmin(dd)); o['kb']=dd[k]
        if dd[k]<=2.5: dest.setdefault((b.lat.values[k],b.lon.values[k]),[]).append('wb')
    D=list(dest); e=g.post('https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix',{'origins':[{'waypoint':{'location':{'latLng':{'latitude':r.lat,'longitude':r.lon}}}}],'destinations':[{'waypoint':{'location':{'latLng':{'latitude':a,'longitude':b_}}}} for a,b_ in D],'travelMode':'WALK'},{'X-Goog-FieldMask':'destinationIndex,duration,condition'})
    for x in (e if isinstance(e,list) else []):
        if 'duration' in x:
            for v in dest[D[x.get('destinationIndex',0)]]: o[v]=int(x['duration'][:-1])/60
    o['i']=r.Index; o['ne']=len(D); return o
with TP(8) as ex: Rr=list(ex.map(rj,C.itertuples()))
R=pd.DataFrame(Rr).set_index('i'); print('elements',R.ne.sum(),flush=True); C=C.join(R); C.to_parquet(W+'cells500.parquet'); print('routes done',C[['w5','w10','w20','wb']].notna().sum().to_dict(),flush=True)
# sights for ten model cities and all regions: Text Search with review counts
def sg(a):
    k,la,lo=a; p=g.search(f'top tourist attractions in {k}',la,lo,30000)
    return [(k,x['displayName']['text'],x['location']['latitude'],x['location']['longitude'],x.get('userRatingCount',0)) for x in p]
Q=[]
for f in sorted(glob.glob(os.path.expanduser('~/Downloads/ABNB/inventory/raw_regions/*.parquet'))):
    b=os.path.basename(f).split('_')[0]+'_'+os.path.basename(f).split('_')[1] if False else os.path.basename(f); reg=re.sub(r'_\d{4}-\d\d-\d\d\.parquet','',b).split('__')[-1].replace('-',' ')
    d=pd.read_parquet(f,columns=['latitude','longitude']); la=pd.to_numeric(d.latitude,errors='coerce').median(); lo=pd.to_numeric(d.longitude,errors='coerce').median(); Q.append((reg,la,lo))
for k,la,lo in [('amsterdam',52.37,4.89),('barcelona',41.39,2.17),('broward county florida',26.12,-80.14),('london',51.51,-.13),('los angeles',34.05,-118.25),('madrid',40.42,-3.70),('new york city',40.73,-73.99),('paris',48.86,2.34),('rome',41.9,12.49),('lisbon',38.72,-9.14)]: Q.append((k,la,lo))
Q=list({q[0]:q for q in Q}.values()); print('text searches',len(Q),flush=True)
with TP(6) as ex: T=[y for x in ex.map(sg,Q) for y in x]
pd.DataFrame(T,columns=['region','name','lat','lon','reviews']).to_csv(W+'sights_regions.csv',index=False); print('done',flush=True)
