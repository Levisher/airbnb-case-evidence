import duckdb,os,pandas as pd
g=os.path.expanduser('~/Downloads/ABNB/audit/_ladder/g.parquet')
k=duckdb.connect(); k.execute("set memory_limit='9GB'; set threads=4")
MX=9764; CAP=MX-730
q=lambda s:k.execute(s).df()
k.execute(f"""create temp table h as select reviewer,dn,y,seq,c,fdn,pre,ndn,dn-pdn lastgap,
  least(seq,6) s,(ndn is not null and ndn-dn<=730 and ndn>dn)::int ret,
  year(date '2000-01-01'+cast(fdn as int)) fy,
  case when seq=1 then null else (seq-1)*365.25/greatest(dn-fdn,1) end rate
  from '{g}' where y between 2019 and 2024 and dn<={CAP}""")
# year fixed: weights = all-stays year mix
yr=q("select s,y,count(*) n,avg(ret)*100 r from h group by 1,2")
w=yr.groupby('y').n.sum()/yr.n.sum()
print((yr.assign(w=yr.y.map(w),wr=lambda d:d.r*d.y.map(w)).groupby('s').wr.sum()).round(2).to_string())
print('post-covid stays 2022-24, first seen any');print(q("select s,count(*) n,avg(ret)*100 r from h where y>=2022 group by 1 order by 1").round(2).to_string())
print('guests first seen 2022+');print(q("select s,count(*) n,avg(ret)*100 r from h where fy>=2022 group by 1 order by 1").round(2).to_string())
# past rate bands
k.execute("""create temp table b as select *, case when rate<0.5 then 'a<0.5' when rate<1 then 'b0.5-1' when rate<2 then 'c1-2' when rate<4 then 'd2-4' else 'e4+' end band from h where seq>=2""")
p=q("select s,band,y,count(*) n,avg(ret)*100 r from b group by 1,2,3")
print(p.groupby(['band','s']).apply(lambda d:(d.r*d.n).sum()/d.n.sum()).unstack().round(1).to_string())
print(p.groupby(['band','s']).n.sum().unstack().to_string())
base=p[p.s==2].set_index(['band','y']).n
def st(sv):
    d=p[p.s==sv].set_index(['band','y']); j=d.join(base.rename('w'),how='inner')
    return (j.r*j.w).sum()/j.w.sum(), j.w.sum()/base.sum()
print({sv:tuple(round(x,3) for x in st(sv)) for sv in [2,3,4,5,6]})
# later-frequency band: stays 2021-22 window ends by 2024-12-31; band from count of stays in 2025-26
E25=9132  # 2025-01-01 from 2000-01-01
