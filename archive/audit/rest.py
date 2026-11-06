import duckdb,os,numpy as np,pandas as pd
B=os.path.expanduser('~/Downloads/ABNB'); g=f'{B}/audit/_ladder/g.parquet'
k=duckdb.connect(); k.execute("set memory_limit='9GB'; set threads=4")
q=lambda s:k.execute(s).df()
CAP=9764-730; E25=9132; E23=8401
k.execute(f"""create temp table st as select reviewer,dn,seq,c,fdn,ndn,dn-pdn gap,pdn,y,least(seq,6) s,
  year(date '2000-01-01'+cast(fdn as int)) fy,(ndn is not null and ndn-dn<=730 and ndn>dn)::int ret from '{g}'""")
# later-frequency band
k.execute(f"create temp table lat as select reviewer,sum((dn>={E25})::int) later from st group by 1")
d=q(f"""select s,case when later=0 then '0' when later=1 then '1' when later=2 then '2' else '3+' end band,count(*) n,avg(ret)*100 r
   from st join lat using(reviewer) where y between 2021 and 2022 and dn<{E23} group by 1,2""")
print(d.pivot(index='band',columns='s',values='r').round(1).to_string()); print(d.pivot(index='band',columns='s',values='n').to_string())
raw=q(f"select s,count(*) n,avg(ret)*100 r from st where y between 2021 and 2022 and dn<{E23} group by 1 order by 1"); print(raw.round(2).T.to_string())
w=d[d.s==1].set_index('band').n
print('later fixed',{sv:round(float((d[d.s==sv].set_index('band').r*w).sum()/w.sum()),2) for sv in range(1,7)})
w2=d.groupby('band').n.sum()
print('later fixed all-stay weights',{sv:round(float((d[d.s==sv].set_index('band').r*w2).sum()/w2.sum()),2) for sv in range(1,7)})
d.to_csv(f'{B}/audit/_ladder/later.csv',index=False)
# same-guest ladder: guests with 6+ stays, first seen 2019+, stay 5 inside the cap
k.execute(f"create temp table p6 as select reviewer from st where seq=5 and dn<={CAP} and c>=6 and fy>=2019")
print('p6 all',q("select seq,count(*) n,avg(ret)*100 r,median(ndn-dn) gap from st join p6 using(reviewer) where seq<=5 group by 1 order by 1").round(2).to_string())
print('p6 2022+',q("select seq,count(*) n,avg(ret)*100 r,median(ndn-dn) gap from st join p6 using(reviewer) where seq<=5 and fy>=2022 group by 1 order by 1").round(2).to_string())
# wide
k.execute("""create temp table w as select reviewer,min(fy) fy,max(c) c,max(case when seq=2 then gap end) g1,max(case when seq=3 then gap end) g2,max(case when seq=4 then gap end) g3,max(case when seq=5 then gap end) g4,max(case when seq=6 then gap end) g5
  from st where c>=4 and fy>=2019 and seq between 2 and 6 group by 1""")
print('c band first seen 2022-23');print(q("select least(c,7) c,count(*) n,median(g1) m1,median(g2) m2,median(g3) m3 from w where fy in (2022,2023) and g1>0 and g2>0 and g3>0 group by 1 order by 1").round(1).to_string())
print('band on g3');print(q("""with z as (select *,ntile(4) over (order by g3) b from w where fy in (2022,2023) and g1>0 and g2>0 and g3>0)
   select b,min(g3) lo,max(g3) hi,count(*) n,median(g1) m1,median(g2) m2,avg((g2<g1)::int)*100 f,avg((g2>g1)::int)*100 sl from z group by 1 order by 1""").round(1).to_string())
print('band on g1 for g2 v g3');print(q("""with z as (select *,ntile(4) over (order by g1) b from w where fy in (2022,2023) and g1>0 and g2>0 and g3>0)
   select b,min(g1) lo,max(g1) hi,count(*) n,median(g2) m2,median(g3) m3,avg((g3<g2)::int)*100 f,avg((g3>g2)::int)*100 sl from z group by 1 order by 1""").round(1).to_string())
print('exact c shape 2022-23');print(q("select c,count(*) n,median(g1) m1,median(g2) m2,median(g3) m3,median(g4) m4,median(g5) m5 from w where fy in (2022,2023) and c in (4,5,6) group by 1 order by 1").round(1).to_string())
print('sign test 2022+');print(q("select count(*) n,avg((g2<g1)::int)*100 f21,avg((g2>g1)::int)*100 s21,avg((g3<g2)::int)*100 f32,avg((g3>g2)::int)*100 s32,avg((g3<g1)::int)*100 f31,avg((g3>g1)::int)*100 s31 from w where fy>=2022 and g1>0 and g2>0 and g3>0").round(1).to_string())
# drift at fixed stay number
yr=q("select s,y,avg(ret) r,count(*) n from st where y between 2021 and 2024 and dn<=%d group by 1,2"%CAP); yr['h']=-np.log(1-yr.r)
for sv,x in yr.groupby('s'):
    b=np.polyfit(x.y,np.log(x.h),1)[0]; print('drift s',sv,round(100*b,2))
