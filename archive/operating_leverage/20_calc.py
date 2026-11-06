import sys; sys.path.insert(0,'_scripts')
from inputs import *
import pandas as pd,numpy as np
d=pd.DataFrame(A,index=Y).astype(float)
print('check OI',(d.rev-d.cogs-d.ops-d.pd-d.sm-d.ga-d.restr-d.oi).round(1).to_dict())
print('check ebitda',(d.ebitda-(d.oi+d.da+d.sbc_ops+d.sbc_pd+d.sbc_sm+d.sbc_ga+d.reserves+d.acq+d.restr)).round(1).to_dict())
h=pd.DataFrame(H,index=['H1 25','H1 26']).astype(float); ttm=d.loc[2025].copy()
for c in h: ttm[c]=d.loc[2025,c]+h.loc['H1 26',c]-h.loc['H1 25',c]
for c in ('funds','emp','acq','intinc'): ttm[c]=d.loc[2025,c]
ttm['reserves']=92
d.loc['TTM Q2 26']=ttm
d['sbc']=d.sbc_ops+d.sbc_pd+d.sbc_sm+d.sbc_ga
d['adr']=d.gbv/d.nights; d['take']=d.rev/d.gbv; d['rpn']=d.rev/d.nights
d['clean']=d.oi+d.restr+d.reserves.fillna(0)+d.acq.fillna(0)
d['pre']=d.clean+d.sbc
d['fo']=d.sm-d.bp-d.sbc_sm
for c,e in (('ops','sbc_ops'),('pd','sbc_pd'),('ga','sbc_ga')): d[c+'x']=d[c]-d[e]
d['gax']=d.gax-d.reserves.fillna(0)
d['mkt']=d.bp
pd.set_option('display.width',220)
print(d[['nights','adr','take','rpn','rev','oi','clean','pre','sbc']].round(3).to_string())
per=d[['cogs','opsx','mkt','fo','pdx','gax','sbc','clean','pre']].div(d.nights,axis=0); print(per.round(2).to_string())
print((d[['cogs','opsx','mkt','fo','pdx','gax','sbc','clean','pre']].div(d.rev,axis=0)*100).round(1).to_string())
def win(a,b):
    x,y=d.loc[a],d.loc[b]; dn=y.nights-x.nights
    vol=dn*x.rpn; adr=y.nights*(y.adr-x.adr)*x['take']; tk=y.nights*y.adr*(y['take']-x['take'])
    return dict(win=f'{a}-{b}',dn=dn,drev=y.rev-x.rev,vol=vol,adr=adr,take=tk,rev_n=(y.rev-x.rev)/dn,clean_n=(y.clean-x.clean)/dn,pre_n=(y.pre-x.pre)/dn,oi_n=(y.oi-x.oi)/dn,inc_clean=(y.clean-x.clean)/(y.rev-x.rev),inc_pre=(y.pre-x.pre)/(y.rev-x.rev),cogs=y.cogs-x.cogs,ops=y.opsx-x.opsx,mkt=y.mkt-x.mkt,fo=y.fo-x.fo,pd=y.pdx-x.pdx,ga=y.gax-x.gax,sbc=y.sbc-x.sbc,dclean=y.clean-x.clean)
W=[(2019,2022),(2022,2025),(2019,2025),(2022,2023),(2023,2024),(2024,2025),(2025,'TTM Q2 26'),(2022,'TTM Q2 26')]
print(pd.DataFrame([win(a,b) for a,b in W]).round(2).T.to_string())
hh=h.copy(); hh['sbc']=hh.sbc_ops+hh.sbc_pd+hh.sbc_sm+hh.sbc_ga
print('H1',(hh.loc['H1 26']-hh.loc['H1 25']).round(1).to_dict()); dn=27
print('per added night H1', {k:round((hh.loc['H1 26',k]-hh.loc['H1 25',k])/dn,2) for k in ('rev','cogs','ops','bp','pd','ga','sm','oi')})
print('merchant', [(y,m+c, round((m+c)/((d.loc[y,'gbv']-d.loc[y-1,'gbv']))*100,2)) for y,m,c in MERCH[:4]],round(156/(56434-47962)*100,2))
d.to_pickle('out/abnb.pkl')
