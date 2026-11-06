"""Exclusive against shared inventory: Airbnb homes also found on Booking or Vrbo by licence key, Seattle and San Diego."""
import sys,os,warnings;warnings.filterwarnings('ignore')
B=os.path.expanduser('~/Downloads/ABNB/');sys.path.insert(0,B+'rival_overlap/04_analysis/scripts')
import numpy as np,pandas as pd,statsmodels.formula.api as smf,ro_common as r
from ro_overlap_lib import air
J=pd.read_parquet(B+'price_map/out/homes_joined.parquet');J['id']=pd.to_numeric(J.id,errors='coerce')
res=[];keep=[]
for m in ['seattle','san_diego']:
    a=air(m);d=pd.read_csv(r.P+f'02_interim/candidate_pairs/{m}_rung1.csv');d=d[~d.type.astype(str).str.contains('hotel|hostel|resort',case=False)]
    S={s:set().union(*[set(str(x).split('|')) for x in d[d.site==s]['keys'].dropna()]) for s in ['booking','vrbo']}
    e=a[a.elig&(a.k.str.len()>0)].copy()
    e['bk']=[int(len(k&S['booking'])>0) for k in e.k];e['vr']=[int(len(k&S['vrbo'])>0) for k in e.k];e['sh']=e.bk|e.vr
    e['id']=pd.to_numeric(e.id,errors='coerce')
    e['price']=pd.to_numeric(e.price.astype(str).str.replace(r'[$,]','',regex=True),errors='coerce')
    e['n']=pd.to_numeric(e.estimated_occupancy_l365d,errors='coerce');e['av']=pd.to_numeric(e.availability_365,errors='coerce')
    e['rev']=pd.to_numeric(e.get('estimated_revenue_l365d'),errors='coerce');e['rev']=e.rev.fillna(e.n*e.price)
    e['rt']=pd.to_numeric(e.review_scores_rating,errors='coerce');e['acc']=pd.to_numeric(e.accommodates,errors='coerce');e['nr']=pd.to_numeric(e.number_of_reviews,errors='coerce')
    e['ltm']=pd.to_numeric(e.number_of_reviews_ltm,errors='coerce')
    e['hs']=pd.cut(e.calculated_host_listings_count,[0,1,5,20,1e6],labels=['h1','h2','h6','h21']).astype(str)
    e['pro']=(e.calculated_host_listings_count>=6).astype(int);e['mkt']=m
    print('\n==',m,'keyed homes',len(e),'on Booking %.1f on Vrbo %.1f on either %.1f'%(100*e.bk.mean(),100*e.vr.mean(),100*e.sh.mean()))
    for c,l in [('bk','Booking'),('sh','either')]:
        print(l,'share of Airbnb nights %.1f revenue %.1f'%(100*e[e[c]==1].n.sum()/e.n.sum(),100*e[e[c]==1].rev.sum()/e.rev.sum()))
    print(e.groupby('sh').agg(homes=('id','count'),price=('price','median'),beds=('bedrooms','median'),acc=('acc','median'),nights=('n','mean'),open=('av','mean'),rev=('rev','mean'),rate=('rt','mean'),ltm=('ltm','mean'),pro=('pro','mean')).round(2).T.to_string())
    x=e.merge(J[J.market==m][['id','cell','sight_km','hotel','restaurant','sight','transit','drive_air_min','walk_sight_min','dens']],on='id',how='left')
    print('joined to Google layers',x.cell.notna().sum())
    print(x.groupby('sh')[['sight_km','hotel','restaurant','sight','transit','drive_air_min','walk_sight_min','dens']].median().round(2).T.to_string())
    x['lp']=np.log(x.price);x['lrev']=np.log(x.rev.where(x.rev>0));x['conv']=x.n/x.av.where(x.av>=30)
    x['nb']=x.neighbourhood_cleansed.astype(str);x['ls']=np.log(x.sight_km.clip(lower=.05));x['lh']=np.log1p(x.hotel);x['lbed']=np.log(x.bedrooms.clip(lower=1))
    for treat in ['sh','bk']:
      for y in ['lp','n','lrev','conv','av','ltm','rt']:
        f=f'{y} ~ {treat} + lbed + acc + C(hs) + C(nb)'+('' if y=='rt' else ' + rt')
        z=x.dropna(subset=[y,'lbed','acc','rt'] );o=smf.ols(f,z).fit(cov_type='cluster',cov_kwds={'groups':z.nb.astype('category').cat.codes})
        res.append(dict(market=m,treat=treat,y=y,b=o.params[treat],se=o.bse[treat],p=o.pvalues[treat],n=int(o.nobs)))
    x['lrest']=np.log1p(x.restaurant);z=x.replace([np.inf,-np.inf],np.nan).dropna(subset=['ls','lh','lbed','lrest','pro']);o=smf.logit('sh ~ ls + lh + lrest + lbed + pro',z).fit(disp=0);print(o.summary2().tables[1][['Coef.','Std.Err.','P>|z|']].round(4).to_string())
    x['hq']=pd.qcut(x.hotel.rank(method='first'),3,labels=['few','mid','many'])
    print(x.groupby('hq',observed=True).agg(homes=('id','count'),excl=('sh',lambda s:100*(1-s.mean())),hotels=('hotel','median'),nights=('n','sum')).round(1).to_string())
    print('excl nights share by hotel tercile',(x[x.sh==0].groupby('hq',observed=True).n.sum()/x.groupby('hq',observed=True).n.sum()*100).round(1).to_dict())
    print(e.groupby('hs').apply(lambda g:pd.Series({'homes':len(g),'excl%':100*(1-g.sh.mean()),'nights share':100*g.n.sum()/e.n.sum(),'excl nights of all':100*g[g.sh==0].n.sum()/e.n.sum()})).round(1).to_string())
    keep.append(x[['mkt','id','latitude','longitude','sh','bk','vr','price','n','av','rev','bedrooms','hs','cell','hotel','sight_km']])
R=pd.DataFrame(res);R.to_csv(B+'price_map/out/excl_models.csv',index=False);pd.concat(keep).to_parquet(B+'price_map/out/excl_homes.parquet')
print(R.round(4).to_string())
