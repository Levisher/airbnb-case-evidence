"""Rebuild the ten-city conversion sample from eq_inventory.py with coordinates kept, so location can enter the same model."""
import duckdb,glob,os,numpy as np,pandas as pd
os.chdir(os.path.expanduser('~/Downloads/ABNB')); num=lambda s:pd.to_numeric(s,errors='coerce')
R=[pd.read_parquet(f,columns=['city','id','price','bedrooms','neighbourhood_cleansed','room_type','host_id','availability_365','estimated_occupancy_l365d','review_scores_rating','calculated_host_listings_count','latitude','longitude']) for f in glob.glob('altdata/raw/listings_*_2026-09-*.parquet')]
d=pd.concat(R); d['p']=num(d.price.astype(str).str.replace(r'[^0-9.]','',regex=True)); d['br']=num(d.bedrooms).clip(upper=4); d['id']=num(d.id); d['host_id']=num(d.host_id); d['av']=num(d.availability_365); d['oc']=num(d.estimated_occupancy_l365d); d['rt']=num(d.review_scores_rating); d['lat']=num(d.latitude); d['lon']=num(d.longitude)
d=d[(d.room_type=='Entire home/apt')&(d.p>10)&(d.p<3000)&d.br.notna()]
k=duckdb.connect('altdata/abnb.duckdb',read_only=True); k.execute("set memory_limit='12GB'")
pre=k.execute("select listing_id id,count(*) n0,sum(bad::int) b0 from s where eng and y<=2025 group by 1").df(); post=k.execute("select listing_id id,count(*) n1,sum(bad::int) b1 from s where eng and y=2026 group by 1").df(); hs=k.execute("select host_id,count(*) hn,sum(bad::int) hb from s where eng and y<=2025 group by 1").df()
for x in (pre,post): x['id']=num(x.id)
hs['host_id']=num(hs.host_id); m=d.merge(pre,on='id').merge(hs,on='host_id',how='left'); m=m[m.n0>=3].copy()
r0=pre.b0.sum()/pre.n0.sum(); K=30; m['bad_l']=100*(m.b0+K*r0)/(m.n0+K); m['oth_n']=(m.hn-m.n0).clip(lower=0); m['oth_b']=(m.hb-m.b0).clip(lower=0); m['bad_h']=100*(m.oth_b+K*r0)/(m.oth_n+K)
g=['city','neighbourhood_cleansed','br']; m=m[m.groupby(g).id.transform('size')>=20].copy()
m=m.merge(post,on='id',how='left'); m['n1']=m.n1.fillna(0)
z=m[m.av.notna()&m.p.notna()].copy(); z['y']=np.log1p(z.n1); z['lp']=np.log(z.p); z['ln0']=np.log(z.n0); z['lo']=np.log1p(z.av)
z[['city','neighbourhood_cleansed','br','id','lat','lon','y','lp','ln0','bad_l','bad_h','lo','av','oc','rt','n1','n0','calculated_host_listings_count']].assign(neighbourhood_cleansed=z.neighbourhood_cleansed.astype(str),calculated_host_listings_count=num(z.calculated_host_listings_count)).to_parquet(os.path.expanduser('~/Downloads/ABNB/price_map/out/conv_base.parquet')); print('base',len(z),z.groupby('city').size().to_dict())
