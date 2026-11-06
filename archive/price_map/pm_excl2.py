"""Exclusive against shared: open nights and nights per open night, by host size and inside the same host."""
import sys,os,warnings;warnings.filterwarnings('ignore')
B=os.path.expanduser('~/Downloads/ABNB/');sys.path.insert(0,B+'rival_overlap/04_analysis/scripts')
import numpy as np,pandas as pd,statsmodels.formula.api as smf,ro_common as r
from ro_overlap_lib import air
H=pd.read_parquet(B+'price_map/out/excl_homes.parquet')
rows=[]
for m in ['seattle','san_diego']:
    a=air(m)[['id','host_id','neighbourhood_cleansed','review_scores_rating','accommodates']].copy();a['id']=pd.to_numeric(a.id,errors='coerce')
    x=H[H.mkt==m].merge(a,on='id',how='left')
    x['acc']=pd.to_numeric(x.accommodates,errors='coerce')
    for c in ['sh','bk']:
        for lab,z in [('all',x)]+[(h,x[x.hs==h]) for h in ['h1','h2','h6','h21']]:
            g=z[z.av>=30].groupby(c);t=g.n.sum()/g.av.sum()*100
            rows.append(dict(market=m,split=c,hosts=lab,excl_homes=int((z[c]==0).sum()),shared_homes=int((z[c]==1).sum()),excl_open=z[z[c]==0].av.mean(),shared_open=z[z[c]==1].av.mean(),excl_n=z[z[c]==0].n.mean(),shared_n=z[z[c]==1].n.mean(),excl_per100=t.get(0),shared_per100=t.get(1)))
    # same-host test
    x['lp']=np.log(x.price);x['lb']=np.log(x.bedrooms.clip(lower=1));x['conv']=x.n/x.av.where(x.av>=30)
    mix=x.groupby('host_id').sh.transform(lambda s:s.nunique()>1);y=x[mix]
    print(m,'mixed hosts',y.host_id.nunique(),'homes',len(y),'shared',int(y.sh.sum()))
    for v in ['lp','n','av','conv']:
        z=y.dropna(subset=[v,'lb','acc']);o=smf.ols(f'{v} ~ sh + lb + acc + C(host_id)',z).fit(cov_type='cluster',cov_kwds={'groups':z.host_id.astype('category').cat.codes})
        print('  same host',v,round(o.params['sh'],3),'se',round(o.bse['sh'],3),'p',round(o.pvalues['sh'],4),'n',int(o.nobs))
T=pd.DataFrame(rows).round(1);T.to_csv(B+'price_map/out/excl_table.csv',index=False);print(T.to_string())
