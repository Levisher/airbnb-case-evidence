import duckdb,os,numpy as np,pandas as pd
from scipy.optimize import minimize
B=os.path.expanduser('~/Downloads/ABNB'); g=f'{B}/audit/_ladder/g.parquet'
k=duckdb.connect(); k.execute("set memory_limit='9GB'; set threads=4")
q=lambda s:k.execute(s).df()
CAP=9764-730
k.execute(f"""create temp table st as select reviewer,dn,seq,c,fdn,ndn,dn-pdn gap,y,year(date '2000-01-01'+cast(fdn as int)) fy from '{g}'""")
k.execute(f"""create temp table tr as with a as (select reviewer,dn,fdn,fy,
     sum(case when gap is null or gap>14 then 1 else 0 end) over (partition by reviewer order by dn,seq) tn from st),
   b as (select reviewer,tn,min(dn) dn,max(dn) dl,min(fdn) fdn,min(fy) fy from a group by 1,2)
   select reviewer,tn seq,dl dn,fdn,fy,lead(dn) over w ndn,count(*) over (partition by reviewer) c,year(date '2000-01-01'+cast(dl as int)) y from b window w as (partition by reviewer order by tn)""")
def cells(tbl,lo,ylo):
    d=q(f"""select least(seq,12) k,floor((dn-fdn)/91.0) tq,count(*) n,sum((ndn is not null and ndn-dn<=730 and ndn>dn)::int) r,avg((dn-fdn)/365.25) t
       from {tbl} where fy>={lo} and y>={ylo} and y<=2024 and dn<={CAP} group by 1,2""")
    return d[d.n>0]
def fit(d,free=True):
    kk,t,n,r=d.k.values,d.t.values,d.n.values,d.r.values
    def P(a0,al,de):
        sh=a0+(1+de)*(kk-1); return 1-((al+t)/(al+t+2))**sh
    def nll(p):
        a0,al=np.exp(p[0]),np.exp(p[1]); de=p[2] if free else 0.0
        pr=np.clip(P(a0,al,de),1e-9,1-1e-9); return -(r*np.log(pr)+(n-r)*np.log(1-pr)).sum()
    best=None
    for st in ([0,2,0],[0.3,1,0.3],[-0.5,3,0.5],[0.2,4,-0.3]):
        o=minimize(nll,st,method='Nelder-Mead',options=dict(maxiter=4000,xatol=1e-4,fatol=1e-3))
        if best is None or o.fun<best.fun: best=o
    p=best.x; return np.exp(p[0]),np.exp(p[1]),(p[2] if free else 0.0),best.fun
def ladder(d,a0,al,de):
    x=d[d.k<=6].copy(); sh=a0+(1+de)*(x.k-1); x['p']=1-((al+x.t)/(al+x.t+2))**sh
    return x.groupby('k').apply(lambda z:(z.p*z.n).sum()/z.n.sum()*100,include_groups=False)
out=[]
for lab,tbl,lo,ylo in [('stays, first seen 2022+','st',2022,2022),('trips, first seen 2022+','tr',2022,2022),('stays, first seen 2019+, stays 2022-24','st',2019,2022),('trips, first seen 2019+, stays 2022-24','tr',2019,2022),('stays, all history, stays 2022-24','st',2015,2022),('stays, all history, stays 2019-24','st',2015,2019)]:
    d=cells(tbl,lo,ylo)
    a0,al,de,f1=fit(d,True); b0,bl,_,f0=fit(d,False)
    obs=d[d.k<=6].groupby('k').apply(lambda z:z.r.sum()/z.n.sum()*100,include_groups=False)
    pF=ladder(d,a0,al,de); pS=ladder(d,a0,al,0.0); pC=ladder(d,b0,bl,0.0)
    rise=obs[5]-obs[1]
    print(lab,'n',d.n.sum(),'a0 %.3f alpha %.2f delta %.3f | constrained a0 %.3f alpha %.2f | LR %.0f'%(a0,al,de,b0,bl,2*(f0-f1)))
    print(pd.DataFrame(dict(obs=obs,full=pF,sel_only=pS,sel_refit=pC)).round(1).T.to_string())
    print('share of rise 1 to 5: sel_only %.1f%% refit %.1f%%; 2 to 5 sel_only %.1f%%'%(100*(pS[5]-pS[1])/rise,100*(pC[5]-pC[1])/rise,100*(pS[5]-pS[2])/(obs[5]-obs[2])))
    out.append(dict(sample=lab,n=d.n.sum(),a0=a0,alpha=al,delta=de,a0_c=b0,alpha_c=bl,lr=2*(f0-f1),raw1=obs[1],raw5=obs[5],sel1=pS[1],sel5=pS[5],ref1=pC[1],ref5=pC[5],share=100*(pS[5]-pS[1])/rise,share_refit=100*(pC[5]-pC[1])/rise))
pd.DataFrame(out).to_csv(f'{B}/audit/_ladder/sel.csv',index=False)
# hazard scale check
for nm,vals in [('obs',[14.93,27.39,39.52,51.38,60.74])]:
    v=-np.log(1-np.array(vals)/100); print(nm,v.round(3),(v/v[0]).round(2))
