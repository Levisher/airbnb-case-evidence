"""How much of price does Google location explain: step R-squared, one-SD effects, home-weighted location, Lisbon substitution by hotel density."""
import numpy as np,pandas as pd,os,statsmodels.formula.api as smf
from pm_loc import hav
O=os.path.expanduser('~/Downloads/ABNB/price_map/out/'); d=pd.read_parquet(O+'homes_joined.parquet')
X='bedrooms+accommodates+review_scores_rating+np.log1p(number_of_reviews)+np.log1p(calculated_host_listings_count)'
Ls=['l_restaurant','l_cafe_bar','l_grocery','l_sight','l_transit','l_hotel','l_walk','l_air']; rows=[]
for m,x in d.groupby('market'):
    v=x.dropna(subset=['lp','bedrooms','accommodates','review_scores_rating','walk_sight_min','drive_air_min']).copy()
    a=smf.ols(f'lp~{X}',v).fit().rsquared; b=smf.ols(f'lp~{X}+'+'+'.join(Ls),v).fit(); c=smf.ols(f'lp~{X}+C(neighbourhood_cleansed)',v).fit().rsquared; e=smf.ols(f'lp~{X}+'+'+'.join(Ls)+'+C(neighbourhood_cleansed)',v).fit().rsquared
    z=v.copy()
    for k in Ls: z[k]=(z[k]-z[k].mean())/z[k].std()
    r=smf.ols(f'lp~{X}+'+'+'.join(Ls),z).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(z.cell)[0]})
    rows.append(dict(market=m,n=len(v),r2_property=round(a,3),r2_google=round(b.rsquared,3),r2_neigh=round(c,3),r2_both=round(e,3),**{k[2:]:round(100*(np.exp(r.params[k])-1),1) for k in Ls},**{'p_'+k[2:]:round(r.pvalues[k],3) for k in Ls}))
    print(m,'home-weighted medians: walk',round(x.walk_sight_min.median(),1),'min, restaurants',x.restaurant.median(),'hotels',x.hotel.median(),'grocery',x.grocery.median(),'transit',x.transit.median(),'zero-hotel share of homes',round((x.hotel==0).mean()*100,1),'walk<=15',round((x.walk_sight_min<=15).mean()*100,1))
R=pd.DataFrame(rows); R.to_csv(O+'location_r2.csv',index=False); print(R.T.to_string())
# Lisbon substitution by Google hotel count in the home's own area
of=pd.read_parquet(O+'offers.parquet'); g=pd.read_parquet(O+'google_props.parquet')
a=of[(of.provider=='Airbnb')&(of.kind=='home')&(of.market=='lisbon')]; h=g[(g.market=='lisbon')&(g.kind=='hotel')&g.top.notna()]; s=pd.read_csv(os.path.expanduser('~/Downloads/ABNB/price_map/raw/gmp/sights.csv')); s=s[(s.market=='lisbon')&(s.name!='AIRPORT')].sort_values('reviews',ascending=False).head(15)
r=[]
for x in a.itertuples():
    k=hav(x.lat,x.lon,h.lat.values,h.lon.values); w=h[k<1]
    if len(w)>=3: r.append((x.lat,x.lon,x.total,x.bedrooms,2*w.top.median(),len(w),hav(x.lat,x.lon,s.lat.values,s.lon.values).min()))
t=pd.DataFrame(r,columns=['lat','lon','home','bed','two','nh','km']); t['ratio']=t.home/t.two; t.to_parquet(O+'lisbon_ratio.parquet')
t['hb']=pd.qcut(t.nh,3,labels=['fewer hotels','mid','most hotels'],duplicates='drop'); print(t.groupby('hb',observed=True).agg(n=('ratio','size'),nh=('nh','median'),home=('home','median'),two=('two','median'),ratio=('ratio','median'),cheaper=('ratio',lambda q:(q<1).mean())).round(3).to_string())
print(t.groupby(pd.cut(t.km,[0,.5,1,2,9]),observed=True).agg(n=('ratio','size'),home=('home','median'),two=('two','median'),ratio=('ratio','median')).round(3).to_string())
