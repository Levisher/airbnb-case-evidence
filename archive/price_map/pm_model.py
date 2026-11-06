"""Location-to-price model and related tests on Airbnb whole homes joined to Google cell layers. Coefficients only; no listing rows leave this script."""
import os,re,sys,numpy as np,pandas as pd,statsmodels.formula.api as smf
import pm_gmp as g
W=g.W; O=g.P+'out/'
c=pd.read_parquet(W+'cells.parquet'); fr=[]
for m in g.CFG:
    d,_=g.cells(g.frame(m)); d['market']=m; fr.append(d)
cols=['market','cell','host_id','id','price','accommodates','bedrooms','review_scores_rating','number_of_reviews','number_of_reviews_ltm','availability_365','estimated_occupancy_l365d','calculated_host_listings_count','neighbourhood_cleansed']
d=pd.concat([x[[k for k in cols if k in x]] for x in fr],ignore_index=True)
d['price']=pd.to_numeric(d.price.astype(str).str.replace(r'[^0-9.]','',regex=True),errors='coerce')
for k in cols[5:13]: d[k]=pd.to_numeric(d[k],errors='coerce')
d=d.merge(c.drop(columns=['n','cy','cx','lat','lon']),on=['market','cell'])
for k in ['restaurant','cafe_bar','grocery','sight','transit','hotel']: d['l_'+k]=np.log1p(d[k].clip(lower=0))
d['l_walk']=np.log1p(d.walk_sight_min); d['l_air']=np.log1p(d.drive_air_min)
print('joined homes',len(d),d.groupby('market').size().to_dict(),'priced',d.price.notna().sum())
print(c.groupby('market')[['restaurant','grocery','sight','transit','hotel','walk_sight_min','drive_air_min']].median().round(1).to_string())
d['lp']=np.log(d.price.where(d.price.between(20,5000)))
X='bedrooms+accommodates+review_scores_rating+np.log1p(number_of_reviews)+np.log1p(calculated_host_listings_count)'
L='l_restaurant+l_cafe_bar+l_grocery+l_sight+l_transit+l_hotel+l_walk+l_air'
def fit(y,df,fe,extra=''):
    v=df.dropna(subset=[y,'bedrooms','accommodates','review_scores_rating','walk_sight_min','drive_air_min'])
    r=smf.ols(f'{y}~{X}+{L}{extra}+C({fe})',v).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(v.cell+v.market)[0]})
    return r,len(v)
rows=[]
for m in list(g.CFG)+['pooled']:
    df=d if m=='pooled' else d[d.market==m]
    for y in ['lp','np.log1p(number_of_reviews_ltm)','estimated_occupancy_l365d']:
        yy=y
        if y.startswith('np'): df=df.assign(lr=np.log1p(df.number_of_reviews_ltm)); yy='lr'
        fe='market' if m=='pooled' else 'neighbourhood_cleansed'
        try:
            r,n=fit(yy,df,fe); r0,_=fit(yy,df,fe) 
            for k in L.split('+'): rows.append(dict(market=m,y=yy,var=k,b=r.params[k],lo=r.conf_int().loc[k,0],hi=r.conf_int().loc[k,1],p=r.pvalues[k],n=n,r2=r.rsquared))
        except Exception as e: print('fail',m,y,str(e)[:100])
R=pd.DataFrame(rows); R.to_csv(O+'hedonic.csv',index=False)
print(R[R.y=='lp'].pivot(index='var',columns='market',values='b').round(3).to_string())
print(R[R.y=='lp'].pivot(index='var',columns='market',values='p').round(3).to_string())
print('r2',R[R.y=='lp'].groupby('market').agg(r2=('r2','first'),n=('n','first')).round(3).to_dict('index'))
print('REVIEWS');print(R[R.y=='lr'].pivot(index='var',columns='market',values='b').round(3).to_string())
print('OCC');print(R[R.y=='estimated_occupancy_l365d'].pivot(index='var',columns='market',values='b').round(2).to_string())
# Interactions: large homes and groceries, apartments and transit
df=d.assign(big=(d.bedrooms>=3).astype(int))
r,n=fit('lp',df,'market','+big:l_grocery+big:l_transit+big:l_sight+big:l_restaurant+big'); print('INTERACT',{k:(round(r.params[k],3),round(r.pvalues[k],3)) for k in r.params.index if k.startswith('big')},n)
# Hotel scarcity: cells with sights and restaurants above the market median, split by hotels
out=[]
for m,x in d.groupby('market'):
    cc=c[c.market==m]; hi=(cc.restaurant>=cc.restaurant.median())&(cc.sight>=cc.sight.median()); q=cc[hi].hotel.median()
    t=cc.assign(seg=np.where(~hi,'lower amenity',np.where(cc.hotel<=q,'high amenity, few hotels','high amenity, many hotels')))
    y=x.merge(t[['cell','seg']],on='cell')
    a=y.groupby('seg').agg(homes=('id','size'),price=('price','median'),open_nights=('availability_365','median'),occ=('estimated_occupancy_l365d','median'),rev_ltm=('number_of_reviews_ltm','median'),big=('bedrooms',lambda s:(s>=3).mean()),pro=('calculated_host_listings_count',lambda s:(s>=21).mean())).round(3); a['share']=(a.homes/a.homes.sum()).round(3); a['hotels_cell']=t.groupby('seg').hotel.median(); a['cells']=t.groupby('seg').size(); a['market']=m; out.append(a.reset_index())
S=pd.concat(out); S.to_csv(O+'hotel_scarcity.csv',index=False); print(S.to_string())
# Saturation: price against density inside neighbourhoods
d['dens']=d.groupby(['market','cell']).id.transform('size')
d['l_dens']=np.log(d.dens); r,n=fit('lp',d,'market','+l_dens'); print('DENS price',round(r.params['l_dens'],3),r.conf_int().loc['l_dens'].round(3).tolist(),n)
d['lr']=np.log1p(d.number_of_reviews_ltm); r,n=fit('estimated_occupancy_l365d',d,'market','+l_dens'); print('DENS occ',round(r.params['l_dens'],2),r.conf_int().loc['l_dens'].round(2).tolist())
d.drop(columns=['host_id']).assign(id=d.id.astype(str),neighbourhood_cleansed=d.neighbourhood_cleansed.astype(str)).to_parquet(O+'homes_joined.parquet')
