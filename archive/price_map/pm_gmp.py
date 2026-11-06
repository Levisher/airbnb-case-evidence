"""Google Maps Platform layers, direct: 1 km cells over Airbnb whole-home supply, place counts from Places Aggregate, sights and airports from Places, times from Routes."""
import json,os,sys,math,re,ssl,time,urllib.request,urllib.error,certifi,numpy as np,pandas as pd
from concurrent.futures import ThreadPoolExecutor as TP
sys.path.insert(0,os.path.expanduser('~/Downloads/ABNB/rival_overlap/04_analysis/scripts'))
import ro_common as rc
ctx=ssl.create_default_context(cafile=certifi.where())
K=open(os.path.expanduser('~/api_key.txt')).read().strip()
P=os.path.expanduser('~/Downloads/ABNB/price_map/'); W=P+'raw/gmp/'
CFG={'lisbon':('lisbon','Lisbon','Lisbon Airport',(38.72,-9.14)),'san_diego':('san_diego','San Diego','San Diego International Airport',(32.75,-117.15)),'seattle':('seattle','Seattle','Seattle-Tacoma International Airport',(47.61,-122.33)),'maui':('hawaii','Maui','Kahului Airport',(20.8,-156.33))}
GR={'restaurant':['restaurant'],'cafe_bar':['cafe','bar'],'grocery':['grocery_store','supermarket'],'sight':['tourist_attraction','museum'],'transit':['transit_station','subway_station','train_station','light_rail_station','bus_station'],'hotel':['hotel']}
def post(u,b,h):
    for i in range(6):
        try:
            r=urllib.request.Request(u,data=json.dumps(b).encode(),headers={'Content-Type':'application/json','X-Goog-Api-Key':K,**h}); return json.load(urllib.request.urlopen(r,context=ctx,timeout=40))
        except urllib.error.HTTPError as e:
            t=e.read().decode()[:200]
            if e.code in(429,500,503): time.sleep(2*(i+1)); continue
            return {'err':e.code,'t':t}
        except Exception as e: time.sleep(2*(i+1))
    return {'err':'retry'}
def frame(m):
    d=rc.frame(CFG[m][0])
    if m=='maui': d=d[d.latitude.between(20.55,21.05)&d.longitude.between(-156.72,-155.95)]
    return d
def cells(d):
    la0=d.latitude.mean(); dl=.009; do=.009/math.cos(math.radians(la0))
    d=d.assign(cy=np.floor(d.latitude/dl).astype(int),cx=np.floor(d.longitude/do).astype(int)); d['cell']=d.cy.astype(str)+'_'+d.cx.astype(str)
    c=d.groupby('cell').agg(n=('id','size'),cy=('cy','first'),cx=('cx','first')).reset_index(); c['lat']=(c.cy+.5)*dl; c['lon']=(c.cx+.5)*do
    return d,c
def count(a):
    la,lo,ty=a
    r=post('https://areainsights.googleapis.com/v1:computeInsights',{'insights':['INSIGHT_COUNT'],'filter':{'locationFilter':{'circle':{'latLng':{'latitude':la,'longitude':lo},'radius':700}},'typeFilter':{'includedTypes':ty},'operatingStatus':['OPERATING_STATUS_OPERATIONAL']}},{})
    return int(r.get('count',0)) if 'err' not in r else -1
def search(q,la,lo,rad,n=20):
    r=post('https://places.googleapis.com/v1/places:searchText',{'textQuery':q,'pageSize':n,'locationBias':{'circle':{'center':{'latitude':la,'longitude':lo},'radius':rad}}},{'X-Goog-FieldMask':'places.id,places.displayName,places.location,places.userRatingCount,places.primaryType'})
    return r.get('places',[])
if __name__=='__main__':
    MIN=int(sys.argv[1]); F={};C={}
    for m in CFG:
        d,c=cells(frame(m)); F[m]=d; c['market']=m; C[m]=c[c.n>=MIN]; print(m,'homes',len(d),'cells',len(c),'kept',len(C[m]),'covering',round(C[m].n.sum()/len(d),3),flush=True)
    c=pd.concat(C.values(),ignore_index=True); print('cells',len(c),'calls',len(c)*len(GR),flush=True)
    if len(sys.argv)>2 and sys.argv[2]=='plan': sys.exit()
    assert len(c)*len(GR)<=4900
    S=[]
    for m,(k,nm,ap,(la,lo)) in CFG.items():
        seen={}
        for q in [f'top tourist attractions in {nm}',f'museums in {nm}',f'beaches in {nm}',f'parks and viewpoints in {nm}',f'landmarks in {nm}']:
            for p in search(q,la,lo,40000 if m=='maui' else 15000): seen[p['id']]=dict(market=m,name=p['displayName']['text'],lat=p['location']['latitude'],lon=p['location']['longitude'],reviews=p.get('userRatingCount',0),type=p.get('primaryType'))
        a=search(ap,la,lo,50000,1)[0]; S+=list(seen.values())+[dict(market=m,name='AIRPORT',lat=a['location']['latitude'],lon=a['location']['longitude'],reviews=0,type='airport')]
    S=pd.DataFrame(S); S.to_csv(W+'sights.csv',index=False); print(S.groupby('market').size().to_dict(),flush=True)
    J=[(r.lat,r.lon,ty) for r in c.itertuples() for ty in GR.values()]; t=time.time()
    with TP(12) as ex: R=list(ex.map(count,J))
    print('counts done',round(time.time()-t),'bad',sum(x<0 for x in R),flush=True)
    A=np.array(R).reshape(len(c),len(GR))
    for i,g in enumerate(GR): c[g]=A[:,i]
    c.to_parquet(W+'cells.parquet')
    # Routes: walk from each cell to its nearest of the top 15 sights, drive to the airport
    from pm_loc import hav
    res=[]
    def rm(origs,dests,mode):
        b={'origins':[{'waypoint':{'location':{'latLng':{'latitude':a,'longitude':o}}}} for a,o in origs],'destinations':[{'waypoint':{'location':{'latLng':{'latitude':a,'longitude':o}}}} for a,o in dests],'travelMode':mode}
        return post('https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix',b,{'X-Goog-FieldMask':'originIndex,destinationIndex,duration,distanceMeters,condition'})
    out=[]
    for m,g in c.groupby('market'):
        s=S[(S.market==m)&(S.name!='AIRPORT')].sort_values('reviews',ascending=False).head(15); ap=S[(S.market==m)&(S.name=='AIRPORT')].iloc[0]
        g=g.reset_index(drop=True); near=[int(np.argmin(hav(r.lat,r.lon,s.lat.values,s.lon.values))) for r in g.itertuples()]
        g['sight_km']=[hav(r.lat,r.lon,s.lat.values,s.lon.values).min() for r in g.itertuples()]
        def job(i):
            o=[(g.lat[j],g.lon[j]) for j in range(i,min(i+25,len(g)))]
            return i,rm(o,[(ap.lat,ap.lon)],'DRIVE')
        def wj(j):
            r=rm([(g.lat[j],g.lon[j])],[(s.lat.values[near[j]],s.lon.values[near[j]])],'WALK'); return j,r
        dr=np.full(len(g),np.nan); wk=np.full(len(g),np.nan)
        with TP(6) as ex:
            for i,r in ex.map(job,range(0,len(g),25)):
                for e in (r if isinstance(r,list) else []):
                    if 'duration' in e: dr[i+e['originIndex']]=int(e['duration'][:-1])/60
            for j,r in ex.map(wj,range(len(g))):
                for e in (r if isinstance(r,list) else []):
                    if 'duration' in e: wk[j]=int(e['duration'][:-1])/60
        g['drive_air_min']=dr; g['walk_sight_min']=wk; out.append(g); print(m,'routes',np.isfinite(dr).sum(),np.isfinite(wk).sum(),flush=True)
    pd.concat(out,ignore_index=True).to_parquet(W+'cells.parquet'); print('done',flush=True)
