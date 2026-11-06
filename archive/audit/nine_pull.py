"""Compustat rows for the seven case companies missing from valuechain/fin. Same filters as valuechain/_scripts/wrds_pull.py, written to separate files so the original pull stays untouched."""
import psycopg2,os,time,csv
os.environ['PGGSSENCMODE']='disable'
con=None
for i in range(3):
    try:
        con=psycopg2.connect(host='wrds-pgdata.wharton.upenn.edu',port=9737,dbname='wrds',sslmode='require',connect_timeout=45,gssencmode='disable'); print('connected'); break
    except Exception as e: print('fail',str(e)[:90]); time.sleep(3)
if not con: raise SystemExit('WRDS unreachable')
T=['EBAY','ETSY','W','SNAP','PINS','ROKU','CART']
cur=con.cursor()
cur.execute("""select tic,conm,datadate,fyear,revt,oiadp,ni,emp,curcd,mkvalt from comp.funda where tic = any(%s) and datadate>='2022-01-01' and indfmt='INDL' and datafmt='STD' and popsrc='D' and consol='C' order by tic,datadate""",(T,))
R=cur.fetchall(); w=csv.writer(open('nine_supplement_funda.csv','w')); w.writerow(['tic','conm','datadate','fyear','revt','oiadp','ni','emp','curcd','mkvalt']); w.writerows(R); print('funda',len(R),sorted({r[0] for r in R}))
cur.execute("""select tic,conm,datadate,fyearq,fqtr,rdq,revtq,oiadpq,xsgaq,curcdq from comp.fundq where tic = any(%s) and datadate>='2021-01-01' and indfmt='INDL' and datafmt='STD' and popsrc='D' and consol='C' order by tic,datadate""",(T,))
R=cur.fetchall(); w=csv.writer(open('nine_supplement_fundq.csv','w')); w.writerow(['tic','conm','datadate','fyearq','fqtr','rdq','revtq','oiadpq','xsgaq','curcdq']); w.writerows(R); print('fundq',len(R),sorted({r[0] for r in R}))
con.close()
