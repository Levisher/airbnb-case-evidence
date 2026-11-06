"""Second block behind gmp_cells.csv: listing-file stand-in for the hotel share, OpenStreetMap stand-in, and held-out R-squared over ten cell splits with a straight-line geometry model that needs no Google call beyond two coordinates."""
import glob,json,os,sys,numpy as np,pandas as pd
A=os.path.expanduser('~/Downloads/ABNB/'); sys.path.insert(0,A+'price_map/scripts')
import pm_gmp as g, ro_common as rc
from pm_loc import hav
from gmp_common import prop,dummies,ols,r2,Ls
d=pd.read_parquet(A+'price_map/out/homes_joined.parquet'); c=pd.read_parquet(g.W+'cells.parquet'); S=pd.read_csv(g.W+'sights.csv')
def raw(m):
    k=g.CFG[m][0]
    x=pd.read_csv(rc.P+'01_raw/quarantine_20261105/airbnb/lisbon.csv.gz',low_memory=False,usecols=['latitude','longitude','room_type']) if k=='lisbon' else pd.read_parquet(sorted(glob.glob(rc.G+rc.M[k][0]+'_*.parquet'))[-1],columns=['latitude','longitude','room_type'])
    for q in ['latitude','longitude']: x[q]=pd.to_numeric(x[q],errors='coerce')
    return x.dropna()
def none_within(fr,pl,po,rad=.7):
    if len(pl)==0: return 100.
    h=np.full(len(fr),np.inf)
    for i in range(0,len(pl),200): h=np.minimum(h,hav(fr.latitude.values[:,None],fr.longitude.values[:,None],pl[None,i:i+200],po[None,i:i+200]).min(axis=1))
    return float((h>rad).mean()*100)
out={}
for m in g.CFG:
    fr=g.frame(m); fr['id']=fr.id.astype(str); fc,_=g.cells(fr); cov=fc[fc.cell.isin(c[c.market==m].cell)]
    x=raw(m); hr=x[x.room_type.eq('Hotel room')]
    if m=='maui': hr=hr[hr.latitude.between(20.55,21.05)&hr.longitude.between(-156.72,-155.95)]
    r={'hotel_room_rows':len(hr),'none_700_hotelroom_listing':none_within(cov,hr.latitude.values,hr.longitude.values)}
    j=json.load(open(A+f"altdata/reframe/hotelmap/{ {'lisbon':'lisbon','maui':'hawaii','san_diego':'san-diego','seattle':'seattle'}[m]}.json"))['elements']
    o=np.array([((e.get('center') or e)['lat'],(e.get('center') or e)['lon']) for e in j if (e.get('center') or e).get('lat')])
    if m=='maui': o=o[(o[:,0]>20.55)&(o[:,0]<21.05)&(o[:,1]>-156.72)&(o[:,1]<-155.95)]
    r['osm_hotels']=len(o); r['none_700_osm']=none_within(cov,o[:,0],o[:,1])
    v=d[d.market==m].dropna(subset=['lp','bedrooms','accommodates','review_scores_rating','walk_sight_min','drive_air_min']).reset_index(drop=True)
    v=v.merge(fr[['id','latitude','longitude']].drop_duplicates('id'),on='id',how='left')
    s=S[S.market==m]; ap=s[s.name=='AIRPORT'].iloc[0]; top=s[s.name!='AIRPORT'].sort_values('reviews',ascending=False).head(15)
    gk=np.log(hav(v.latitude.values,v.longitude.values,ap.lat,ap.lon)+.1); sk=np.log(.1+np.array([hav(a,b,top.lat.values,top.lon.values).min() for a,b in zip(v.latitude,v.longitude)]))
    y=v.lp.values; P=prop(v); N=dummies(v.neighbourhood_cleansed); L=v[Ls].values; Gm=np.column_stack([gk,sk,gk**2,sk**2])
    Cn=v[['l_restaurant','l_cafe_bar','l_grocery','l_sight','l_transit','l_hotel']].values
    X={'prop':P,'neigh':np.column_stack([P,N]),'geom':np.column_stack([P,Gm]),'neigh_geom':np.column_stack([P,N,Gm]),'google':np.column_stack([P,L]),'google_counts_only':np.column_stack([P,Cn]),'neigh_google':np.column_stack([P,N,L]),'neigh_geom_google':np.column_stack([P,N,Gm,L])}
    res={k:[] for k in X}
    for seed in range(10):
        rng=np.random.default_rng(seed); cl=v.cell.unique(); rng.shuffle(cl); f=v.cell.map(dict(zip(cl,np.arange(len(cl))%5))).values
        for k,Z in X.items():
            p=np.zeros(len(v))
            for j in range(5): p[f==j]=ols(Z[f!=j],y[f!=j],Z[f==j])
            res[k].append(r2(y,p))
    for k in res: r['ho_'+k]=float(np.mean(res[k])); r['ho_'+k+'_lo']=float(np.min(res[k])); r['ho_'+k+'_hi']=float(np.max(res[k]))
    r['splits']=res; r['neigh_levels']=int(v.neighbourhood_cleansed.nunique())
    out[m]=r; print(m,json.dumps({k:(round(q,4) if isinstance(q,float) else q) for k,q in r.items() if not k.endswith(('_lo','_hi')) and k!='splits'}),flush=True)
json.dump(out,open(A+'audit/gmp_tests2.json','w'),indent=1)
