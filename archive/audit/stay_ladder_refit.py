"""Stay ladder refit. Reads _ladder/g.parquet (stay_ladder_build.py) and writes stay_ladder_refit.csv and stay_ladder_refit_tests.csv.
A stay is one review on a listing live in Sep 2026 in ten cities. Return = next review within 730 days. Trip = stays with gaps of 14 days or less merged."""
import duckdb,os,numpy as np,pandas as pd
from scipy.optimize import minimize
from scipy.stats import chi2
B=os.path.expanduser('~/Downloads/ABNB'); A=f'{B}/audit'; g=f'{A}/_ladder/g.parquet'
k=duckdb.connect(); k.execute("set memory_limit='9GB'; set threads=4")
q=lambda s:k.execute(s).df()
CAP=9764-730; E25=9132; E23=8401
k.execute(f"""create temp table st as select reviewer,dn,seq,c,fdn,ndn,dn-pdn gap,pdn,y,least(seq,6) s,
  year(date '2000-01-01'+cast(fdn as int)) fy,(ndn is not null and ndn-dn<=730 and ndn>dn)::int ret from '{g}'""")
k.execute("""create temp table tr as with a as (select reviewer,dn,fdn,fy,
     sum(case when gap is null or gap>14 then 1 else 0 end) over (partition by reviewer order by dn,gap nulls first) tn from st),
   b as (select reviewer,greatest(tn,1) tn,min(dn) dn,max(dn) dl,min(fdn) fdn,min(fy) fy from a group by 1,2)
   select reviewer,tn seq,dl dn,fdn,fy,lead(dn) over w ndn,count(*) over (partition by reviewer) c,year(date '2000-01-01'+cast(dl as int)) y from b window w as (partition by reviewer order by tn)""")
F=f"y between 2019 and 2024 and dn<={CAP}"
main=q(f"select s stay,count(*) stays,avg(ret)*100 ret from st where {F} group by 1 order by 1").set_index('stay')
main['ci']=1.96*np.sqrt(main.ret*(100-main.ret)/main.stays)
# calendar year fixed
yr=q(f"select s,y,count(*) n,avg(ret)*100 r from st where {F} group by 1,2"); w=yr.groupby('y').n.sum()/yr.n.sum()
main['year_fixed']=yr.assign(x=yr.r*yr.y.map(w)).groupby('s').x.sum()
# past-only frequency fixed
p=q(f"""select s,y,case when r<0.5 then 'a' when r<1 then 'b' when r<2 then 'c' when r<4 then 'd' else 'e' end band,count(*) n,avg(ret)*100 ret from
   (select *,(seq-1)*365.25/greatest(dn-fdn,1) r from st where {F} and seq>=2) group by 1,2,3""")
base=p[p.s==2].set_index(['band','y']).n
def stdz(sv):
    j=p[p.s==sv].set_index(['band','y']).join(base.rename('w'),how='inner'); return (j.ret*j.w).sum()/j.w.sum()
main['past_rate_fixed']=[np.nan]+[stdz(v) for v in range(2,7)]
# later frequency fixed, stays 2021-22 so the return window closes before 2025
k.execute(f"create temp table lat as select reviewer,least(sum((dn>={E25})::int),3) later from st group by 1")
L=q(f"select s,later,count(*) n,avg(ret)*100 r from st join lat using(reviewer) where y between 2021 and 2022 and dn<{E23} group by 1,2")
wl=L[L.s==1].set_index('later').n
main['raw_2021_22']=q(f"select s,avg(ret)*100 r from st where y between 2021 and 2022 and dn<{E23} group by 1").set_index('s').r
main['later_freq_fixed_2021_22']=[(L[L.s==v].set_index('later').r*wl).sum()/wl.sum() for v in range(1,7)]
# same-guest return: guests with 6+ stays, first seen 2019+, fifth stay inside the cap
k.execute(f"create temp table p6 as select reviewer from st where seq=5 and dn<={CAP} and c>=6 and fy>=2019")
sg=q("select seq,count(*) n,avg(ret)*100 r from st join p6 using(reviewer) where seq<=5 group by 1 order by 1").set_index('seq')
main['same_guest_return_6plus']=sg.r
main['same_guest_n']=sg.n
# trips
main['trip_return']=q(f"select least(seq,6) s,avg((ndn is not null and ndn-dn<=730 and ndn>dn)::int)*100 r from tr where {F} group by 1").set_index('s').r
# selection model
def cells(t,where):
    return q(f"select least(seq,12) k,floor((dn-fdn)/91.0) tq,count(*) n,sum((ndn is not null and ndn-dn<=730 and ndn>dn)::int) r,avg((dn-fdn)/365.25) t from {t} where {where} group by 1,2")
def fit(d,free,start=None):
    kk,t,n,r=d.k.values,d.t.values,d.n.values,d.r.values
    def nll(p):
        a0,al=np.exp(p[0]),np.exp(p[1]); de=p[2] if free else 0.0
        pr=np.clip(1-((al+t)/(al+t+2))**(a0+(1+de)*(kk-1)),1e-9,1-1e-9); return -(r*np.log(pr)+(n-r)*np.log(1-pr)).sum()
    best=None
    for s0 in (start and [start] or [[-.5,2,0],[.3,1,.3],[.6,3,1],[.2,4,-.3]]):
        o=minimize(nll,s0,method='Nelder-Mead',options=dict(maxiter=4000,xatol=1e-4,fatol=1e-3))
        if best is None or o.fun<best.fun: best=o
    x=best.x; return np.exp(x[0]),np.exp(x[1]),(x[2] if free else 0.0),best.fun,x
def lad(d,a0,al,de):
    x=d.copy(); x['p']=1-((al+x.t)/(al+x.t+2))**(a0+(1+de)*(x.k-1)); x['s']=np.minimum(x.k,6)
    return x.groupby('s').apply(lambda z:(z.p*z.n).sum()/z.n.sum()*100,include_groups=False)
T=[]
def add(block,metric,group,value,unit,n='',note=''): T.append(dict(block=block,metric=metric,group=group,value=value,unit=unit,n=n,note=note))
res={}
rng=np.random.default_rng(7)
for lab,t,wh in [('stays',  'st',F),('trips','tr',F),('stays first seen 2022+','st',f"{F} and fy>=2022"),('trips first seen 2022+','tr',f"{F} and fy>=2022")]:
    d=cells(t,wh); d=d[d.k>=1]
    a,b,de,f1,x1=fit(d,True); a2,b2,_,f0,x0=fit(d,False)
    obs=d.assign(s=np.minimum(d.k,6)).groupby('s')[['r','n']].sum(); obs=obs.r/obs.n*100
    pc=lad(d,a2,b2,0); pf=lad(d,a,b,0); rise=obs[5]-obs[1]
    res[lab]=pc
    lr=2*(f0-f1); pv=chi2.sf(max(lr,0),1)
    add('selection',f'Extra rate per stay beyond selection (delta)',lab,de,'ratio',int(d.n.sum()),f'LR {lr:.1f}, p {pv:.3g}')
    add('selection','Share of stay 1 to 5 rise reproduced, selection-only refit',lab,100*(pc[5]-pc[1])/rise,'pct',int(d.n.sum()),f'alpha {b2:.2f}, a0 {a2:.3f}')
    add('selection','Share of stay 1 to 5 rise left at delta 0 in the free fit',lab,100*(pf[5]-pf[1])/rise,'pct',int(d.n.sum()),f'alpha {b:.2f}, a0 {a:.3f}, delta {de:.3f}')
    add('selection','Observed less selection-only at stay 5',lab,obs[5]-pc[5],'points',int(d.n.sum()),'')
    if lab in('stays','trips'):
        sh=[];dl=[]
        for i in range(150):
            e=d.copy(); e['n']=rng.poisson(d.n.values); e['r']=np.minimum(rng.poisson(d.r.values),e.n); e=e[e.n>0]
            A2,B2,_,_,_=fit(e,False,list(x0[:2])+[0]); o2=e.assign(s=np.minimum(e.k,6)).groupby('s')[['r','n']].sum(); o2=o2.r/o2.n*100; pp=lad(e,A2,B2,0)
            sh.append(100*(pp[5]-pp[1])/(o2[5]-o2[1]))
        add('selection','Selection-only share, 95% interval',lab,f'{np.percentile(sh,2.5):.1f} to {np.percentile(sh,97.5):.1f}','pct',150,'Poisson resampling of cells, clustered guests not resampled')
main['selection_only_stays']=res['stays']; main['selection_only_trips']=res['trips']
# same-guest gaps
k.execute("""create temp table w as select reviewer,min(fy) fy,max(c) c,max(case when seq=2 then gap end) g1,max(case when seq=3 then gap end) g2,max(case when seq=4 then gap end) g3
  from st where c>=4 and fy>=2019 and seq between 2 and 4 group by 1""")
def med(wh):
    r=q(f"select count(*) n,median(g1) a,median(g2) b,median(g3) c from w where g1>0 and g2>0 and g3>0 and {wh}").iloc[0]; return r
m=med('true'); m2=med('fy in (2022,2023)'); m3=med('fy>=2022')
main['same_guest_gap_next_days']=[m.a,m.b,m.c,np.nan,np.nan,np.nan]
main['same_guest_gap_first_seen_2022_23']=[m2.a,m2.b,m2.c,np.nan,np.nan,np.nan]
main['same_guest_gap_first_seen_2022_on']=[m3.a,m3.b,m3.c,np.nan,np.nan,np.nan]
# gap by frequency band (lifetime stays) inside first seen 2022-23
cb=q("select least(c,7) cc,count(*) n,median(g1) a,median(g2) b,median(g3) c from w where fy in (2022,2023) and g1>0 and g2>0 and g3>0 group by 1 order by 1")
for r in cb.itertuples():
    add('gap by frequency',f'Median gaps, lifetime stays {int(r.cc)}{"+" if r.cc==7 else ""}','first seen 2022-23',f'{r.a:.0f}, {r.b:.0f}, {r.c:.0f}','days',r.n,f'third against first {100*(r.c/r.a-1):.1f}%')
main['same_guest_gap_freq_fixed']=[(cb[x]*cb.n).sum()/cb.n.sum() for x in 'abc']+[np.nan]*3
fe=pd.read_csv(f'{A}/_ladder/fe.csv')
for r in fe.itertuples():
    add('gap, guest fixed effects',f'Change against first gap, second and third',r.sample,f'{r.guestfe_pos2:.1f}, {r.guestfe_pos3:.1f}','pct',r.guests,'Guest fixed effects on log gap')
fy=q("select fy,count(*) n,median(g1) a,median(g2) b,median(g3) c from w where g1>0 and g2>0 and g3>0 group by 1 order by 1")
for r in fy.itertuples(): add('gap by first year','Median gaps',int(r.fy),f'{r.a:.0f}, {r.b:.0f}, {r.c:.0f}','days',r.n,'')
sg2=q("select sum((g2<g1)::int) a,sum((g2>g1)::int) b,sum((g3<g2)::int) c,sum((g3>g2)::int) d from w where fy>=2022 and g1>0 and g2>0 and g3>0").iloc[0]
for lab,x,y in [('second against first',sg2.a,sg2.b),('third against second',sg2.c,sg2.d)]:
    s=x/(x+y); z=(s-.5)/np.sqrt(.25/(x+y)); add('gap sign test',f'Shorter share excluding ties, {lab}','first seen 2022+',100*s,'pct',int(x+y),f'z {z:.1f}')
# null simulations of gaps
def sim(d,N=3000000,seed=1):
    r=np.random.default_rng(seed); T=4.72  # Jan 2022 to Sep 2026 in years
    lam=r.gamma(0.53,1/6.7,N); keep=lam>1e-4; lam=lam[keep]; s0=r.uniform(0,T,lam.size)
    Lam=lambda t:(np.exp(d*t)-1)/d if d else t
    Inv=lambda u:np.log1p(d*u)/d if d else u
    u=Lam(s0); out=[]; t=s0
    gaps=[]
    for i in range(3):
        u=u+r.exponential(1/lam); tn=Inv(u); gaps.append(tn-t); t=tn
    ok=t<=T; return [np.median(x[ok])*365.25 for x in gaps],int(ok.sum())
for d in (0,.04,.08,.18):
    gm,n=sim(d); add('gap null simulation','Median gaps with no change in behaviour',f'observed stay rate drifting {100*d:.0f}% a year',f'{gm[0]:.0f}, {gm[1]:.0f}, {gm[2]:.0f}','days',n,f'third against first {100*(gm[2]/gm[0]-1):.1f}%')
yr2=q(f"select s,y,avg(ret) r from st where y between 2021 and 2024 and dn<={CAP} group by 1,2"); yr2['h']=-np.log(1-yr2.r)
for sv,x in yr2.groupby('s'): add('calendar drift','Yearly change in return hazard at fixed stay number',f'stay {sv}, 2021 to 2024',100*np.polyfit(x.y,np.log(x.h),1)[0],'pct a year')
rl=pd.read_csv(f'{A}/_ladder/review_loss.csv')
for r in rl[rl.y.between(2019,2025)].itertuples(): add('snapshot loss','Reviews in Dec 2025 files absent in Sep 2026',int(r.y),r.loss,'pct',r.n,'Paris, Barcelona, Los Angeles')
add('measurement','Rise in review probability needed for the first seen 2022+ fall',' third against first',100*(1/(1-.1561)-1),'pct','','Fixed-effect fall of 15.6%')
main=main.rename(index={6:'6+'}).reset_index()
main.round(2).to_csv(f'{A}/stay_ladder_refit.csv',index=False)
pd.DataFrame(T).to_csv(f'{A}/stay_ladder_refit_tests.csv',index=False)
print(main.round(2).T.to_string()); t=pd.DataFrame(T); print(t[t.block.isin(['selection','gap sign test','gap null simulation','gap by frequency','measurement'])].drop(columns=['block']).to_string())
