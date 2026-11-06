# Stage 1: one row per stay (review) with gap, lifetime count, first date, past-only frequency. Rebuilds ABNB/audit/_ladder/g.parquet
import duckdb,os
B=os.path.expanduser('~/Downloads/ABNB')
k=duckdb.connect(f'{B}/altdata/abnb.duckdb',read_only=True); k.execute("set memory_limit='10GB'; set threads=4")
mx=k.execute("select max(dn) from s").fetchone()[0]; print('max dn',mx)
D19=6940  # 2019-01-01, dn counts days from 2000-01-01
k.execute(f"""copy (
 select reviewer,review_id,listing_id,city,dn,y,mo,seq,host_id,
   lead(dn) over w ndn, lead(city) over w nc, lag(dn) over w pdn,
   count(*) over (partition by reviewer) c,
   min(dn) over (partition by reviewer) fdn,
   sum(case when dn<{D19} then 1 else 0 end) over (partition by reviewer) pre
 from s window w as (partition by reviewer order by dn,review_id)
) to '{B}/audit/_ladder/g.parquet' (format parquet)""")
print(k.execute(f"select count(*),count(distinct reviewer) from '{B}/audit/_ladder/g.parquet'").fetchall())
