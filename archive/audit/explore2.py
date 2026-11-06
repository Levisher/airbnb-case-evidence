import duckdb,os,numpy as np,pandas as pd
B=os.path.expanduser('~/Downloads/ABNB')
g=f'{B}/audit/_ladder/g.parquet'
k=duckdb.connect(); k.execute("set memory_limit='9GB'; set threads=4")
q=lambda s:k.execute(s).df()
print(q(f"describe select * from '{B}/altdata/surv/reviews_paris_2025-12-13.parquet'").iloc[:,:2].to_string())
print(q(f"describe select * from '{B}/altdata/raw/reviews_paris_2026-09-16.parquet'").iloc[:,:2].to_string())
res=[]
for c,d1,d2 in [('paris','2025-12-13','2026-09-16'),('barcelona','2025-12-14','2026-09-17'),('los-angeles','2025-12-04','2026-09-14')]:
    a=f"{B}/altdata/surv/reviews_{c}_{d1}.parquet"; b=f"{B}/altdata/raw/reviews_{c}_{d2}.parquet"
    r=q(f"""select year(cast(a.date as date)) y,count(*) n,sum((b.review_id is null)::int) lost
       from '{a}' a left join (select review_id from '{b}') b on a.review_id=b.review_id group by 1 order by 1""")
    r['city']=c; res.append(r)
r=pd.concat(res); r['loss']=r.lost/r.n*100
print(r.pivot(index='y',columns='city',values='loss').round(2).to_string())
t=r.groupby('y')[['n','lost']].sum(); t['loss']=t.lost/t.n*100; print(t.round(2).to_string())
t.to_csv(f'{B}/audit/_ladder/review_loss.csv')
