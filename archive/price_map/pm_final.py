"""Final location results for the rebuilt note. A: 500 m model in four markets. B: same conversion model as the note with location added, ten cities. C: all regions. Aggregates only."""
import glob,json,math,os,re,numpy as np,pandas as pd,statsmodels.api as sm,warnings
from scipy.spatial import cKDTree
import pm_gmp as g
from pm_loc import hav
warnings.filterwarnings('ignore')
W=g.W; O=g.P+'out/'; num=lambda s:pd.to_numeric(s,errors='coerce')
def dem(z,cols,keys):
    k=z.groupby(keys,observed=True); return z[cols]-k[cols].transform('mean')
def reg(z,y,X,keys,cl):
    v=z.dropna(subset=[y]+X).copy(); v=v[v.groupby(keys,observed=True)[y].transform('size')>=2]
    D=dem(v,[y]+X,keys); r=sm.OLS(D[y],D[X]).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(v[cl])[0]}); return r,len(v)
c1=pd.read_parquet(W+'cells.parquet'); c5=pd.read_parquet(W+'cells500.parquet'); H=pd.read_parquet(W+'hotels.parquet'); S=pd.read_csv(W+'sights.csv'); S=S[S.name!='AIRPORT']
def km(lat,lon,pl,po):
    a=np.radians(lat)[:,None]; b=np.radians(lon)[:,None]; c=np.radians(pl)[None,:]; d=np.radians(po)[None,:]
    h=np.sin((c-a)/2)**2+np.cos(a)*np.cos(c)*np.sin((d-b)/2)**2; return 6371*2*np.arcsin(np.sqrt(h))
def within(lat,lon,pl,po,r,w=None):
    la0=np.mean(lat); f=lambda a,b:np.c_[np.radians(a)*6371,np.radians(b)*6371*math.cos(math.radians(la0))]
    t=cKDTree(f(pl,po)); q=t.query_ball_point(f(lat,lon),r)
    return np.array([len(x) for x in q]) if w is None else np.array([w[x].sum() for x in q])
F=[]
for m in g.CFG:
    d,_=g.cells(g.frame(m)); x=c5[c5.market==m].iloc[0]; d['cy5']=np.floor(d.latitude/x.dl).astype(int); d['cx5']=np.floor(d.longitude/x.do).astype(int); d['market']=m
    d=d.merge(c5[c5.market==m].drop(columns=['market','lat','lon','n','dl','do']),left_on=['cy5','cx5'],right_on=['cy','cx'],suffixes=('','_5')).merge(c1[c1.market==m][['cell','restaurant','cafe_bar','sight','drive_air_min']],on='cell')
    h=H[H.market==m]; la,lo=d.latitude.values,d.longitude.values
    for r,n in [(.5,'h500'),(1,'h1'),(2,'h2')]: d[n]=within(la,lo,h.lat.values,h.lon.values,r)
    d['hrev1']=within(la,lo,h.lat.values,h.lon.values,1,h.reviews.values.astype(float))
    s=S[S.market==m].sort_values('reviews',ascending=False)
    for t in (5,10,20): d[f'd{t}']=km(la,lo,s.lat.values[:t],s.lon.values[:t]).min(1)
    F.append(d)
cols=['market','id','neighbourhood_cleansed','cell','cy5','cx5','latitude','longitude','price','accommodates','bedrooms','review_scores_rating','number_of_reviews','number_of_reviews_ltm','availability_365','estimated_occupancy_l365d','calculated_host_listings_count','w10','wb','kb','groc500','pharm500','tr750','tr_km','restaurant','cafe_bar','sight','drive_air_min','h500','h1','h2','hrev1','d5','d10','d20']
d=pd.concat([x[cols] for x in F],ignore_index=True)
for k in cols[9:17]: d[k]=num(d[k])
d['p']=num(d.price.astype(str).str.replace(r'[^0-9.]','',regex=True))
d=d[d.p.between(20,5000)&d.bedrooms.notna()&d.accommodates.notna()].copy(); d['br']=d.bedrooms.clip(upper=4); d['c5']=d.market+d.cy5.astype(str)+'_'+d.cx5.astype(str)
d['lp']=np.log(d.p); d['lr']=np.log1p(d.number_of_reviews_ltm); d['occ']=d.estimated_occupancy_l365d.clip(upper=365); d['open']=(d.occ+d.availability_365).clip(upper=365); d['lo']=np.log1p(d.availability_365)
d['prior']=np.log1p((d.number_of_reviews-d.number_of_reviews_ltm).clip(lower=0)); d['rate']=d.review_scores_rating; d['hl']=np.log1p(d.calculated_host_listings_count); d['ac']=d.accommodates
d['vpn']=np.log((d.p*d.occ/d.open).where((d.occ>0)&(d.open>0)))
for k,v in [('lw10','w10'),('lair','drive_air_min'),('lrest','restaurant'),('lcafe','cafe_bar')]: d[k]=np.log1p(d[v].clip(lower=0))
for k,v in [('lh500','h500'),('lh1','h1'),('lh2','h2'),('lhrev','hrev1'),('lgroc','groc500'),('lpharm','pharm500'),('ltr','tr750')]: d[k]=np.log1p(d[v])
d['ltrk']=np.log(d.tr_km.clip(lower=.02).fillna(1.5))
d['mb']=d.market+'_'+d.br.astype(str); d['nb']=d.market+'_'+d.neighbourhood_cleansed.astype(str)+'_'+d.br.astype(str)
print('A homes',len(d),d.groupby('market').size().to_dict(),'with rating',d.rate.notna().sum())
Q=['lo','prior','rate','hl','ac']
LOC=['lw10','lh1','lhrev','lrest','lgroc','lpharm','ltrk','lair']
sd=lambda k,z:z[k].std()
R=[]
for m in list(g.CFG)+['pooled']:
    z=d if m=='pooled' else d[d.market==m]
    for y,yn,ctrl in [('lp','ln price',['prior','rate','hl','ac']),('lr','ln(1+reviews last 12m)',['lp','lo','prior','rate','hl','ac']),('occ','estimated nights',['lp','lo','rate','hl','ac'])]:
        for fe,keys in [('market x bedrooms',['mb']),('neighbourhood x bedrooms',['nb'])]:
            r,n=reg(z,y,ctrl+LOC,keys,'c5')
            for k in LOC:
                u=sd(k,z); R.append(dict(market=m,y=yn,fe=fe,var=k,b=r.params[k],se=r.bse[k],p=r.pvalues[k],sd=u,per_sd=r.params[k]*u,n=n))
R=pd.DataFrame(R); R.to_csv(O+'final_rows1to6.csv',index=False)
for y in R.y.unique():
    for fe in R.fe.unique():
        t=R[(R.y==y)&(R.fe==fe)]; print('\n',y,'|',fe,'| per 1 SD; n',t.groupby('market').n.first().to_dict()); print(t.pivot(index='var',columns='market',values='per_sd').round(3).to_string()); print(t.pivot(index='var',columns='market',values='p').round(3).rename(columns=lambda c:'p_'+c[:4]).to_string())
# Row 1 bands
for m,z in d.groupby('market'):
    z=z.assign(b=pd.cut(z.w10,[0,10,20,30,60,1e4],labels=['<=10','10-20','20-30','30-60','60+'])); print(m,'walk to top-10 sight',z.groupby('b',observed=True).agg(homes=('id','size'),price=('p','median'),rev=('number_of_reviews_ltm','median'),occ=('occ','median'),openn=('open','median')).round(0).T.to_dict())
# Row 5 beach bands
z=d[d.market.ne('zz')].copy(); z['bb']=pd.cut(z.wb.fillna(99),[0,5,10,20,1e4],labels=['b5','b10','b20','far'])
for k in ['b5','b10','b20']: z[k]=(z.bb==k).astype(float)
for m,x in z.groupby('market'):
    r,n=reg(x,'lp',['prior','rate','hl','ac','lw10','lh1','lrest','lair','b5','b10','b20'],['mb'],'c5'); print('BEACH',m,n,{k:(round(100*(math.exp(r.params[k])-1),1),round(r.pvalues[k],3),int(x[k].sum())) for k in ['b5','b10','b20']})
# Row 7 ladder, value per open night
for m in list(g.CFG):
    x=d[d.market==m].dropna(subset=['vpn','rate','prior','hl','ac']+LOC)
    r2=lambda X:sm.OLS(dem(x,['vpn'],['br'])['vpn'],dem(x,X,['br'])).fit().rsquared
    A=['ac']; Bq=['rate','prior','hl']; print('LADDER',m,len(x),'traits',round(r2(A),3),'traits+quality',round(r2(A+Bq),3),'all',round(r2(A+Bq+LOC),3),'traits+location',round(r2(A+LOC),3))
    rr=sm.OLS(dem(x,['vpn'],['br'])['vpn'],dem(x,A+Bq+LOC,['br'])).fit(); s=(dem(x,LOC,['br'])*rr.params[LOC]).sum(axis=1); q=pd.qcut(s.rank(method='first'),5,labels=False); print('  location fifth',np.round(np.exp(s.groupby(q).mean().values-s.groupby(q).mean().values[0]),3).tolist(),'price',x.groupby(q).p.median().round(0).tolist(),'nights',x.groupby(q).occ.median().round(0).tolist())
# Row 8 homes against hotels
for m in g.CFG:
    h=H[H.market==m]; x=d[d.market==m]; s=S[S.market==m].sort_values('reviews',ascending=False); o={}
    for t in (5,10,20):
        hk=km(h.lat.values,h.lon.values,s.lat.values[:t],s.lon.values[:t]).min(1); o[t]=(round(x[f'd{t}'].median(),2),round(np.median(hk),2))
    h=h.assign(hk=km(h.lat.values,h.lon.values,s.lat.values[:10],s.lon.values[:10]).min(1)); dl=.018; do=dl/math.cos(math.radians(x.latitude.mean()))
    a=x.assign(c=np.floor(x.latitude/dl).astype(int).astype(str)+'_'+np.floor(x.longitude/do).astype(int).astype(str)).groupby('c').agg(hm=('d10','median'),nh=('id','size')); b=h.assign(c=np.floor(h.lat/dl).astype(int).astype(str)+'_'+np.floor(h.lon/do).astype(int).astype(str)).groupby('c').agg(ht=('hk','median'),nt=('pid','size')); j=a.join(b,how='inner'); j=j[(j.nh>=5)&(j.nt>=2)]
    print('ROW8',m,'homes',len(x),'hotels',len(h),'top5/10/20 (home,hotel) km',o,'2km cells',len(j),'median gap home-hotel km',round((j.hm-j.ht).median(),3),'share homes closer',round(((j.hm<j.ht).mean()),3),'homes in those cells',round(j.nh.sum()/len(x),3))
# calibration of walk minutes per straight km
print('walk min per km',round((d.w10/d.d10).replace(np.inf,np.nan).median(),1))
# B: note model plus location
b=pd.read_parquet(O+'conv_base.parquet'); T=pd.read_csv(W+'sights_regions.csv'); MP={'amsterdam':'amsterdam','barcelona':'barcelona','broward-county':'broward county florida','lisbon':'lisbon','london':'london','los-angeles':'los angeles','madrid':'madrid','new-york-city':'new york city','paris':'paris','rome':'rome'}
HM={'broward-county':'broward','new-york-city':'new-york'}
b=b.dropna(subset=['lat','lon']).copy(); b['dk']=np.nan; b['h1']=np.nan
for c,x in b.groupby('city'):
    s=T[T.region==MP[c]].sort_values('reviews',ascending=False); s=s[km(s.lat.values,s.lon.values,np.array([x.lat.median()]),np.array([x.lon.median()]))[:,0]<40].head(10)
    b.loc[x.index,'dk']=km(x.lat.values,x.lon.values,s.lat.values,s.lon.values).min(1)
    j=json.load(open(os.path.expanduser(f'~/Downloads/ABNB/altdata/reframe/hotelmap/{HM.get(c,c)}.json')))['elements']; P=np.array([[(e.get('center') or e)['lat'],(e.get('center') or e)['lon']] for e in j if (e.get('center') or e).get('lat')])
    b.loc[x.index,'h1']=within(x.lat.values,x.lon.values,P[:,0],P[:,1],1)
    print('  ',c,len(x),'sights',len(s),'top',list(s.name.head(3)),'median km',round(np.median(b.loc[x.index,'dk']),2))
b['ldk']=np.log(b.dk.clip(lower=.05)); b['lh']=np.log1p(b.h1); b['cb']=b.city+b.br.astype(str); b['cnb']=b.city+b.neighbourhood_cleansed+b.br.astype(str); b['oc2']=b.oc.clip(upper=365)
print('B n',len(b)); X0=['lp','ln0','bad_l','bad_h','lo']
for nm,keys in [('city x neighbourhood x bedrooms',['cnb']),('city x bedrooms',['cb'])]:
    for X in [X0,X0+['ldk'],X0+['ldk','lh']]:
        D=dem(b,['y']+X,keys); r=sm.OLS(D.y,D[X]).fit(cov_type='HC1'); print(nm,len(b),'R2',round(r.rsquared,4),{k:(round(r.params[k],4),round(r.bse[k],4)) for k in X})
    X=X0[1:]+['ldk','lh']; D=dem(b,['lp']+X,keys); r=sm.OLS(D.lp,D[X]).fit(cov_type='HC1'); print('  PRICE',{k:(round(r.params[k],4),round(r.bse[k],4)) for k in ['ldk','lh','bad_l','bad_h','ln0']},'R2',round(r.rsquared,3))
print('sd within',dem(b,['ldk','lh'],['cnb']).std().round(3).to_dict(),'sd citybed',dem(b,['ldk','lh'],['cb']).std().round(3).to_dict(),'ldk med km',round(b.dk.median(),2))
# C: all regions
rows=[]; Tg=T.groupby('region')
for f in sorted(glob.glob(os.path.expanduser('~/Downloads/ABNB/inventory/raw_regions/*.parquet'))):
    reg_=re.sub(r'_\d{4}-\d\d-\d\d\.parquet','',os.path.basename(f)).split('__')[-1].replace('-',' ')
    if reg_ not in Tg.groups: continue
    z=pd.read_parquet(f,columns=['latitude','longitude','price','room_type','bedrooms','accommodates','review_scores_rating','number_of_reviews','number_of_reviews_ltm','availability_365','calculated_host_listings_count'])
    z=z[z.room_type=='Entire home/apt'].copy()
    for k in z.columns:
        if k not in('room_type',): z[k]=num(z[k].astype(str).str.replace(r'[^0-9.\-]','',regex=True))
    z=z[z.price.between(15,5000)&z.latitude.notna()&z.bedrooms.notna()&z.review_scores_rating.notna()]
    s=Tg.get_group(reg_).sort_values('reviews',ascending=False); s=s[km(s.lat.values,s.lon.values,np.array([z.latitude.median()]),np.array([z.longitude.median()]))[:,0]<40].head(10) if len(z) else s
    if len(z)<300 or len(s)<5: continue
    z['l']=np.log(km(z.latitude.values,z.longitude.values,s.lat.values,s.lon.values).min(1).clip(.05)); z['lp']=np.log(z.price); z['lr']=np.log1p(z.number_of_reviews_ltm); z['br']=z.bedrooms.clip(upper=4); z['ac']=z.accommodates; z['rt']=z.review_scores_rating; z['pr']=np.log1p((z.number_of_reviews-z.number_of_reviews_ltm).clip(lower=0)); z['lo']=np.log1p(z.availability_365)
    z=z.dropna(subset=['l','lp','lr','ac','rt','pr','lo']); D=dem(z,['lp','lr','l','ac','rt','pr','lo'],['br'])
    a=sm.OLS(D.lp,D[['l','ac','rt','pr']]).fit(); e=sm.OLS(D.lr,D[['l','lp','ac','rt','pr','lo']]).fit(); rows.append(dict(region=reg_,n=len(z),bp=a.params['l'],pp=a.pvalues['l'],br=e.params['l'],pr=e.pvalues['l']))
C=pd.DataFrame(rows); C.to_csv(O+'final_regions.csv',index=False)
print('C regions',len(C),'homes',C.n.sum(),'price coef median',round(C.bp.median(),3),'negative',round((C.bp<0).mean(),3),'neg and p<.05',round(((C.bp<0)&(C.pp<.05)).mean(),3),'pos and p<.05',round(((C.bp>0)&(C.pp<.05)).mean(),3))
print('  reviews coef median',round(C.br.median(),3),'negative',round((C.br<0).mean(),3),'neg sig',round(((C.br<0)&(C.pr<.05)).mean(),3),'pos sig',round(((C.br>0)&(C.pr<.05)).mean(),3))
