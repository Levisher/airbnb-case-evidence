"""Tests the frame (volume x take rate x contribution per unit, less marketing and fixed costs) on Compustat data.
Every ticker in valuechain/fin plus the seven case companies absent from it, last three fiscal years with revenue.
Bases: operating income (oiadp) per revenue dollar, revenue per employee. Writes nine_frame.csv, one row per ticker-year."""
import json,os,re
import numpy as np,pandas as pd
B=os.path.expanduser('~/Downloads/ABNB/'); K=os.path.expanduser('~/Downloads/Consumer_Internet_Models/data/')
NINE=['EBAY','ETSY','W','PYPL','SNAP','PINS','ROKU','ABNB','CART']
SWING=5.0
fa=pd.read_csv(B+'valuechain/fin/funda.csv').assign(data_source='valuechain/fin')
fq=pd.read_csv(B+'valuechain/fin/fundq.csv').assign(data_source='valuechain/fin')
sa=pd.read_csv(B+'reverse_eng/nine_supplement_funda.csv').assign(data_source='reverse_eng supplement')
sq=pd.read_csv(B+'reverse_eng/nine_supplement_fundq.csv').assign(data_source='reverse_eng supplement')
assert not set(fa.tic)&set(sa.tic)
a=pd.concat([fa,sa],ignore_index=True); q=pd.concat([fq,sq],ignore_index=True)
assert not a.duplicated(['tic','fyear']).any() and set(a.curcd.dropna())=={'USD'}
a=a[a.revt.notna()&(a.revt>0)].sort_values(['tic','fyear'])
a['op_income_per_rev_dollar']=a.oiadp/a.revt
a['rev_per_employee_usd_k']=a.revt/a.emp          # revt in $m, emp in thousands, so the ratio is $k a head
a['margin_chg_pts']=a.groupby('tic').op_income_per_rev_dollar.diff()*100
a['fy_gap']=a.groupby('tic').fyear.diff()
a.loc[a.fy_gap.ne(1),'margin_chg_pts']=np.nan
t=a.groupby('tic').tail(3).copy()
first=t.groupby('tic').fyear.transform('min')
t.loc[t.fyear==first,'margin_chg_pts']=np.nan      # change needs a prior year inside the three-year window
t['swing_gt_5pts']=t.margin_chg_pts.abs()>SWING
t['ticker_swings']=t.groupby('tic').swing_gt_5pts.transform('any')
# annual against the sum of quarters, a check that the two Compustat files agree
s=q.groupby(['tic','fyearq']).agg(qn=('fqtr','nunique'),rq=('revtq','sum'),oq=('oiadpq','sum')).reset_index()
s=s[s.qn==4].rename(columns={'fyearq':'fyear'})
t=t.merge(s[['tic','fyear','rq','oq']],on=['tic','fyear'],how='left')
t['fundq_rev_gap_pct']=(t.rq/t.revt-1)*100; t['fundq_oi_gap_usd_m']=t.oq-t.oiadp
# volume measures: name, kpi key, kind, tied revenue key
V={'EBAY':('GMV','gmv','$m','transacted value',None),'ETSY':('GMS','gms','$m','transacted value','rev_mkt'),'PYPL':('TPV','tpv','$m','transacted value','rev_txn'),'ABNB':('GBV (nights x ADR)','gbv','$m','transacted value',None),'CART':('GTV','gtv','$m','transacted value','rev_txn'),
   'W':('Orders x AOV','orders','m','units x disclosed price',None),'SNAP':('DAU x ARPU','dau','m','definitional',None),'PINS':('MAU x ARPU','mau','m','definitional',None),'ROKU':('Streaming hours','hours2','bn hours','partial','rev_plat')}
def qmap(d,k): return {p:v for p,v in d.get(k,{}).items() if re.fullmatch(r'\d{4}Q[1-4]',p)}
# Annual volume comes from quarter sums, with these exceptions. ETSY 2025 quarters were restated for the Reverb sale, so the annual figure on the reported perimeter is used.
# ABNB 2023 quarters are rounded in filings. CART FY keys in kpi.json sit two years early, so its quarter sums stay. ROKU hours sit in two keys and 2025 Q4 comes from the 145.6bn in the FY25 10-K.
FY_KEY={'ETSY','ABNB'}
rows=[]
rq=q.assign(p=q.fyearq.astype(str)+'Q'+q.fqtr.astype(str)).set_index(['tic','p']).revtq
for T,(nm,key,unit,kind,tk) in V.items():
    d=json.load(open(f'{K}{T}/kpi.json')); v=qmap(d,key); arpu=qmap(d,'arpu'); aov=qmap(d,'aov'); tv=qmap(d,tk) if tk else {}
    if T=='ROKU':
        v={**qmap(d,'hours'),**v}; v['2025Q4']=145.6-sum(v[f'2025Q{i}'] for i in (1,2,3))
    for y in sorted(t[t.tic==T].fyear):
        ps=[f'{y}Q{i}' for i in (1,2,3,4)]; ok=all(p in v for p in ps); rev=float(t[(t.tic==T)&(t.fyear==y)].revt.iloc[0])
        r=dict(tic=T,fyear=y,volume_measure=nm,volume_unit=unit,volume_tie_class=kind)
        if ok:
            vol=sum(v[p] for p in ps) if T not in('SNAP','PINS') else np.mean([v[p] for p in ps])
            if T in FY_KEY: vol=d[key][f'FY{y}']
            r['volume_fy']=vol
            if T in('SNAP','PINS') and all(p in arpu for p in ps): r['rebuilt_rev_over_reported']=sum(v[p]*arpu[p] for p in ps)/rev
            elif T=='W' and all(p in aov for p in ps): r['rebuilt_rev_over_reported']=sum(v[p]*aov[p] for p in ps)/rev
            r['rev_per_volume_unit']=rev/vol
        if tk and T in FY_KEY: r['tied_rev_share']=d[tk][f'FY{y}']/rev
        elif tv and all(p in tv for p in ps): r['tied_rev_share']=sum(tv[p] for p in ps)/rev
        rows.append(r)
    # quarterly year-on-year growth of revenue against volume
    g=[]
    for p,x in v.items():
        y,n=int(p[:4]),p[4:]; pp=f'{y-1}{n}'
        if T=='ETSY' and y==2025: continue   # restated 2025 against unrestated 2024 is a perimeter break
        if pp in v and (T,p) in rq.index and (T,pp) in rq.index and v[pp]>0: g.append((x/v[pp]-1,rq[(T,p)]/rq[(T,pp)]-1))
    g=np.array(g)
    for r in rows:
        if r['tic']==T: r['yoy_corr_rev_volume']=np.corrcoef(g[:,0],g[:,1])[0,1] if len(g)>3 else np.nan; r['yoy_corr_n']=len(g)
vt=pd.DataFrame(rows)
t=t.merge(vt,on=['tic','fyear'],how='left')
t['case_company']=t.tic.isin(NINE)
t['volume_ties_to_revenue']=t.volume_tie_class.map({'transacted value':'yes','units x disclosed price':'yes','definitional':'by definition only','partial':'part of revenue'})
c=['tic','conm','case_company','data_source','fyear','datadate','revt','oiadp','emp','op_income_per_rev_dollar','rev_per_employee_usd_k','margin_chg_pts','swing_gt_5pts','ticker_swings','volume_ties_to_revenue','volume_tie_class','volume_measure','volume_unit','volume_fy','rev_per_volume_unit','rebuilt_rev_over_reported','tied_rev_share','yoy_corr_rev_volume','yoy_corr_n','fundq_rev_gap_pct','fundq_oi_gap_usd_m']
o=t[c].sort_values(['case_company','tic','fyear'],ascending=[False,True,True])
o.to_csv(B+'reverse_eng/nine_frame.csv',index=False,float_format='%.4f')
print(len(o),'rows',o.tic.nunique(),'tickers',(o.groupby('tic').size()<3).sum(),'with fewer than three years')
