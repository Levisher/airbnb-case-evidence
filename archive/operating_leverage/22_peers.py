import sys; sys.path.insert(0,'_scripts')
from inputs import *
import pandas as pd,numpy as np
pd.set_option('display.width',200)
v=pd.DataFrame({k:V[k] for k in V if k!='y'},index=V['y'])
v['adj_oi']=v.rev-v.cogs-v.ops-v.tech-v.sm-v.ga-v.dep   # before amortisation and impairment
v['gp']=v.rev-v.cogs; v['c1']=v.gp-v.ops; v['c2']=v.c1-v.sm
print((v[['rev','cogs','ops','tech','sm','ga','adj_oi','gp','c1','c2']].div(v.nights,axis=0)).round(1).to_string())
print((v[['rev','gp','c1','c2','adj_oi']].div(v.gbv,axis=0)*100).round(1).to_string()); print((v[['gp','c1','c2','adj_oi','sm']].div(v.rev,axis=0)*100).round(1).to_string()); print((v.gbv/v.nights).round(0).to_dict())
def w(d,a,b,cols,den):
    x=d.loc[b]-d.loc[a]; return {c:round(x[c]/x[den]*100,1) for c in cols}
for a,b in ((2019,2022),(2019,2021),(2022,2024),(2023,2024)):
    x=v.loc[b]-v.loc[a]; print(a,b,'dn',round(x.nights,3),'per night',{c:round(x[c]/x.nights,1) for c in ('rev','cogs','ops','sm','tech','ga','gp','c1','c2','adj_oi')},'%rev',w(v,a,b,('gp','c1','c2','adj_oi'),'rev'),'%gbv',w(v,a,b,('gp','c1','c2','adj_oi'),'gbv'))
a=pd.read_pickle('out/abnb.pkl')
a['gp']=a.rev-a.cogs; a['c1']=a.gp-a.opsx; a['c2']=a.c1-a.mkt
for p,q in ((2019,2022),(2022,2025),(2023,2025),(2022,'TTM Q2 26')):
    x=a.loc[q,['rev','gbv','gp','c1','c2','clean','pre','nights']]-a.loc[p,['rev','gbv','gp','c1','c2','clean','pre','nights']]
    print(p,q,'%rev',{c:round(x[c]/x.rev*100,1) for c in ('gp','c1','c2','clean','pre')},'%gbv',{c:round(x[c]/x.gbv*100,2) for c in ('rev','gp','c1','c2','clean','pre')},'per night',{c:round(x[c]/x.nights,2) for c in ('rev','gp','c1','c2','clean','pre')})
print((a.loc[[2022,2024,2025,'TTM Q2 26'],['rev','gp','c1','c2','clean','pre']].div(a.loc[[2022,2024,2025,'TTM Q2 26'],'gbv'],axis=0)*100).round(2).to_string())
s=pd.DataFrame({k:S[k] for k in ('occ','book','rev','cogs','ops','ga','rd','sm')},index=S['y']); s['gp']=s.rev-s.cogs; s['c1']=s.gp-s.ops; s['c2']=s.c1-s.sm; s['o']=s.c2-s.ga-s.rd
print(s[['rev','cogs','ops','sm','ga','gp','c1','c2','o']].div(s.occ,axis=0).round(1).to_string()); print((s[['gp','c1','c2','o']].div(s.rev,axis=0)*100).round(1).to_string()); x=s.loc[2023]-s.loc[2021]; print('S 21-23',{c:round(x[c]/x.occ,1) for c in('rev','cogs','ops','gp','c1','c2','o')},{c:round(x[c]/x.rev*100,1) for c in('gp','c1','c2','o')})
b=pd.DataFrame({k:B[k] for k in B if k!='y'},index=B['y']).astype(float); b['cl']=b.oi+b.imp; b['pre']=b.cl+b.sbc
e=pd.DataFrame({k:E_[k] for k in E_ if k!='y'},index=E_['y']).astype(float); e['cl']=e.oi+e.imp; e['pre']=e.cl+e.sbc
print((b[['cl','pre','sbc','mkt']].div(b.rev,axis=0)*100).round(1).assign(take=(b.rev/b.gb*100).round(2),mk_gb=(b.mkt/b.gb*100).round(2),rpn=(b.rev/b.nights).round(2),gbpn=(b.gb/b.nights).round(1)).to_string())
print((e[['cl','pre','sbc','mkt']].div(e.rev,axis=0)*100).round(1).assign(take=(e.rev/e.gb*100).round(2),mk_gb=(e.mkt/e.gb*100).round(2)).to_string())
for n,d in (('B',b),('E',e)):
    for p,q in ((2019,2025),(2022,2025),(2023,2025),(2024,2025)):
        x=d.loc[q]-d.loc[p]; print(n,p,q,'inc cl',round(x.cl/x.rev*100,1),'inc pre',round(x.pre/x.rev*100,1),'of GB',round(x.cl/x.gb*100,2),round(x.pre/x.gb*100,2), 'DOL',round((x.cl/d.loc[p,'cl'])/(x.rev/d.loc[p,'rev']),2))
print('B per added night 22-25',round((b.loc[2025,'rev']-b.loc[2022,'rev'])/(b.loc[2025,'nights']-b.loc[2022,'nights']),2),round((b.loc[2025,'cl']-b.loc[2022,'cl'])/(b.loc[2025,'nights']-b.loc[2022,'nights']),2))
for x,y in ((2022,2025),(2023,2025)): print('A DOL',round((a.loc[y,'clean']/a.loc[x,'clean']-1)/(a.loc[y,'rev']/a.loc[x,'rev']-1),2),round((a.loc[y,'pre']/a.loc[x,'pre']-1)/(a.loc[y,'rev']/a.loc[x,'rev']-1),2))
print('A mk',(a.mkt/a.gbv*100).round(2).to_dict()); print('A sm',(a.sm/a.gbv*100).round(2).to_dict())
