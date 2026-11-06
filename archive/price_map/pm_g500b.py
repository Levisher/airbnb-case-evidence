"""Second half of the 500 m pull: walk times and region sights. First attempt lost its results to a column-name bug, so this run calls fewer elements."""
import json,math,os,re,sys,glob,time,numpy as np,pandas as pd
from concurrent.futures import ThreadPoolExecutor as TP
import pm_gmp as g
from pm_loc import hav
W=g.W; C=pd.read_parquet(W+'cells500.parquet'); B=pd.read_parquet(W+'beaches.parquet')
# walk times to nearest of top 5, 10, 20 sights and nearest beach within 2.5 km
S=pd.read_csv(W+'sights.csv'); S=S[S.name!='AIRPORT']; n_el=0; rows=[]
def rj(r):
    s=S[S.market==r.market].sort_values('reviews',ascending=False); dest={}; o={}
    for t in (10,):
        q=s.head(t); k=int(np.argmin(hav(r.lat,r.lon,q.lat.values,q.lon.values))); o[f'k{t}']=hav(r.lat,r.lon,q.lat.values,q.lon.values)[k]; dest.setdefault((q.lat.values[k],q.lon.values[k]),[]).append(f'w{t}')
    b=B[B.market==r.market]
    if len(b):
        dd=hav(r.lat,r.lon,b.lat.values,b.lon.values); k=int(np.argmin(dd)); o['kb']=dd[k]
        if dd[k]<=2.5: dest.setdefault((b.lat.values[k],b.lon.values[k]),[]).append('wb')
    D=list(dest); e=g.post('https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix',{'origins':[{'waypoint':{'location':{'latLng':{'latitude':r.lat,'longitude':r.lon}}}}],'destinations':[{'waypoint':{'location':{'latLng':{'latitude':a,'longitude':b_}}}} for a,b_ in D],'travelMode':'WALK'},{'X-Goog-FieldMask':'destinationIndex,duration,condition'})
    for x in (e if isinstance(e,list) else []):
        if 'duration' in x:
            for v in dest[D[x.get('destinationIndex',0)]]: o[v]=int(x['duration'][:-1])/60
    o['i']=r.Index; o['nel']=len(D); return o
with TP(8) as ex: Rr=list(ex.map(rj,C.itertuples()))
R=pd.DataFrame(Rr).set_index('i'); print('elements',R.nel.sum(),flush=True); C=C.join(R); C.to_parquet(W+'cells500.parquet'); print('routes done',C[['w10','wb']].notna().sum().to_dict(),flush=True)
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
