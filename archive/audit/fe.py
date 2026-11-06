import duckdb,os,numpy as np,pandas as pd,sys
B=os.path.expanduser('~/Downloads/ABNB'); g=f'{B}/audit/_ladder/g.parquet'
k=duckdb.connect(); k.execute("set memory_limit='9GB'; set threads=4")
# stays and trips sequences for guests first seen 2019 or later
k.execute(f"""create temp table st as select reviewer,dn,seq,c,fdn,dn-pdn gap,pdn,year(date '2000-01-01'+cast(fdn as int)) fy from '{g}'""")
k.execute("""create temp table tr as with a as (select reviewer,dn,fdn,fy,
     sum(case when gap is null or gap>14 then 1 else 0 end) over (partition by reviewer order by dn,seq) tn from st where fy>=2019),
   b as (select reviewer,tn,min(dn) dn,max(dn) dl,min(fdn) fdn,min(fy) fy from a group by 1,2)
   select reviewer,tn seq,dn,fdn,fy,dn-lag(dl) over w gap,lag(dl) over w pdn,count(*) over (partition by reviewer) c from b window w as (partition by reviewer order by tn)""")
def fe(tbl,lo,hi=2026,label=''):
    d=k.execute(f"""select reviewer,seq-1 pos,gap,pdn,fy,dn from {tbl} where c>=4 and fy between {lo} and {hi} and seq between 2 and 4 and gap>0""").df()
    n=d.groupby('reviewer').pos.transform('size'); d=d[n==3].copy()
    d['lg']=np.log(d.gap); d['q']=(d.pdn//91).astype(int)
    gi=pd.factorize(d.reviewer)[0]; qi=pd.factorize(d.q)[0]; ng=gi.max()+1; nq=qi.max()+1
    Y=np.column_stack([d.lg,(d.pos==2)*1.0,(d.pos==3)*1.0])
    R=Y.copy()
    for it in range(200):
        prev=R.copy()
        for idx,m in ((gi,ng),(qi,nq)):
            for j in range(3):
                s=np.bincount(idx,R[:,j],m)/np.bincount(idx,minlength=m)
                R[:,j]-=s[idx]
        if np.abs(R-prev).max()<1e-8: break
    X=R[:,1:]; y=R[:,0]; XtX=np.linalg.inv(X.T@X); b=XtX@X.T@y; e=y-X@b
    sc=np.column_stack([np.bincount(gi,X[:,j]*e,ng) for j in range(2)]); V=XtX@(sc.T@sc)@XtX; se=np.sqrt(np.diag(V))
    # no calendar control
    R2=Y.copy()
    for j in range(3): R2[:,j]-=(np.bincount(gi,R2[:,j],ng)/3)[gi]
    b0=np.linalg.lstsq(R2[:,1:],R2[:,0],rcond=None)[0]
    med=d.groupby('pos').gap.median().values
    return dict(sample=label,tbl=tbl,fy_lo=lo,fy_hi=hi,guests=ng,med1=med[0],med2=med[1],med3=med[2],
       guestfe_pos2=100*(np.exp(b0[0])-1),guestfe_pos3=100*(np.exp(b0[1])-1),
       cal_pos2=100*(np.exp(b[0])-1),cal_pos3=100*(np.exp(b[1])-1),se2=100*se[0],se3=100*se[1])
out=[fe('st',2019,label='all stays'),fe('st',2021,label='stays, first seen 2021+'),fe('st',2022,label='stays, first seen 2022+'),fe('st',2019,2023,label='stays, first seen to 2023'),fe('st',2022,2023,label='stays, first seen 2022-23'),
     fe('tr',2019,label='trips'),fe('tr',2022,label='trips, first seen 2022+'),fe('tr',2022,2023,label='trips, first seen 2022-23')]
o=pd.DataFrame(out); print(o.round(2).to_string()); o.to_csv(f'{B}/audit/_ladder/fe.csv',index=False)
