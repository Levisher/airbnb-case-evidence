"""Tests behind gmp_cells.csv, from local files only, no Google calls. Prints per market: R-squared steps, leave-cells-out R-squared, cell ceiling, home-level hotel distance, failed-count sensitivity. Saves gmp_tests.json."""
import json,os,sys,numpy as np,pandas as pd
A=os.path.expanduser('~/Downloads/ABNB/'); sys.path.insert(0,A+'price_map/scripts')
import pm_gmp as g
from pm_loc import hav
from gmp_common import prop,dummies,ols,r2,Ls
W=g.W; O=A+'price_map/out/'; G=['restaurant','cafe_bar','grocery','sight','transit','hotel']
d=pd.read_parquet(O+'homes_joined.parquet'); c=pd.read_parquet(W+'cells.parquet'); H=pd.read_parquet(W+'hotels.parquet')
def prop(v):
    return np.column_stack([v.bedrooms,v.accommodates,v.review_scores_rating,np.log1p(v.number_of_reviews),np.log1p(v.calculated_host_listings_count)])
def dummies(s):
    return pd.get_dummies(s.astype(str),drop_first=True).values.astype(float)
def ols(Xa,y,Xb=None):
    Xa=np.column_stack([np.ones(len(Xa)),Xa]); b=np.linalg.lstsq(Xa,y,rcond=None)[0]
    if Xb is None: return Xa@b
    return np.column_stack([np.ones(len(Xb)),Xb])@b
def r2(y,f): return 1-((y-f)**2).sum()/((y-y.mean())**2).sum()
def within(X,y,grp):
    x=pd.DataFrame(X); yy=pd.Series(y); k=pd.factorize(grp)[0]
    xd=x-x.groupby(k).transform('mean'); yd=yy-yy.groupby(k).transform('mean'); b=np.linalg.lstsq(xd.values,yd.values,rcond=None)[0]
    return 1-((yd.values-xd.values@b)**2).sum()/((y-y.mean())**2).sum(),len(np.unique(k))
out={}; rng=np.random.default_rng(7)
for m in g.CFG:
    v=d[d.market==m].dropna(subset=['lp','bedrooms','accommodates','review_scores_rating','walk_sight_min','drive_air_min']).reset_index(drop=True)
    fr=g.frame(m); fr['id']=fr.id.astype(str); v=v.merge(fr[['id','latitude','longitude']].drop_duplicates('id'),on='id',how='left')
    y=v.lp.values; P=prop(v); L=v[Ls].values; N=dummies(v.neighbourhood_cleansed)
    la=(v.latitude-v.latitude.mean())*10; lo=(v.longitude-v.longitude.mean())*10; Q=np.column_stack([la,lo,la**2,lo**2,la*lo,la**3,lo**3,la**2*lo,la*lo**2])
    dens=np.log(v.groupby('cell').id.transform('size').values)
    r={'n':len(v),'cells_in_model':int(v.cell.nunique())}
    r['r2_prop']=r2(y,ols(P,y)); r['r2_prop_google']=r2(y,ols(np.column_stack([P,L]),y)); r['r2_prop_neigh']=r2(y,ols(np.column_stack([P,N]),y)); r['r2_prop_neigh_google']=r2(y,ols(np.column_stack([P,N,L]),y))
    r['r2_prop_cell_ceiling'],_=within(P,y,v.cell.values)
    r['r2_prop_coords']=r2(y,ols(np.column_stack([P,Q,dens]),y))
    # cells held out: whole cells leave the fit, so a cell has no price history of its own
    cells=v.cell.unique(); rng.shuffle(cells); fold=dict(zip(cells,np.arange(len(cells))%5)); f=v.cell.map(fold).values
    pr={k:np.zeros(len(v)) for k in ['prop','coords','neigh','google','coords_google','neigh_google']}
    Xs={'prop':P,'coords':np.column_stack([P,Q,dens]),'neigh':np.column_stack([P,N]),'google':np.column_stack([P,L]),'coords_google':np.column_stack([P,Q,dens,L]),'neigh_google':np.column_stack([P,N,L])}
    for k in range(5):
        a=f!=k; b=f==k
        for n_,X in Xs.items(): pr[n_][b]=ols(X[a],y[a],X[b])
    for n_ in pr: r['cv_'+n_]=r2(y,pr[n_])
    # gain over the neighbourhood field, 200 cell-cluster bootstraps
    idx={k:np.where(v.cell.values==k)[0] for k in cells}; gains=[];gp=[]
    B0=np.column_stack([P,N]); B1=np.column_stack([P,N,L]); C1=np.column_stack([P,L])
    for _ in range(200):
        s=np.concatenate([idx[k] for k in rng.choice(cells,len(cells))]); ys=y[s]
        gains.append(r2(ys,ols(B1[s],ys))-r2(ys,ols(B0[s],ys))); gp.append(r2(ys,ols(C1[s],ys))-r2(ys,ols(P[s],ys)))
    r['gain_neigh_lo'],r['gain_neigh_hi']=np.percentile(gains,[2.5,97.5]); r['gain_prop_lo'],r['gain_prop_hi']=np.percentile(gp,[2.5,97.5])
    # failed counts: drop the cells with any failed count
    bad=set(c[(c.market==m)&(c[G]<0).any(axis=1)].cell); k=~v.cell.isin(bad).values
    r['gain_prop_drop_failed']=r2(y[k],ols(np.column_stack([P,L])[k],y[k]))-r2(y[k],ols(P[k],y[k])); r['failed_cells_homes_in_model']=int((~k).sum())
    # home-level distance to Google hotels, all homes in the frame
    h=H[H.market==m]; la_=np.radians(fr.latitude.values); hd=np.full(len(fr),np.inf)
    for i in range(0,len(h),200):
        q=h.iloc[i:i+200]; hd=np.minimum(hd,hav(fr.latitude.values[:,None],fr.longitude.values[:,None],q.lat.values[None,:],q.lon.values[None,:]).min(axis=1))
    fc,_=g.cells(fr); cov=fc.cell.isin(c[c.market==m].cell).values
    for rad in (.5,.7,1.): r[f'home_none_{int(rad*1000)}_covered']=float((hd[cov]>rad).mean()*100)
    r['home_none_700_all']=float((hd>.7).mean()*100)
    x=d[d.market==m]; cm=c[c.market==m]
    r['homes_joined']=len(x); r['homes_frame']=len(fr); r['zero_cell_share']=float((x.hotel==0).mean()*100); r['failed_hotel_homes']=int((x.hotel<0).sum())
    r['zero_or_failed_share']=float((x.hotel<=0).mean()*100); r['bound_all_uncovered_none']=float(((x.hotel==0).sum()+(len(fr)-len(x)))/len(fr)*100)
    out[m]=r; print(m,json.dumps({k:(round(v_,4) if isinstance(v_,float) else v_) for k,v_ in r.items()}),flush=True)
json.dump(out,open(A+'audit/gmp_tests.json','w'),indent=1)
