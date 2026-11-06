"""Per-unit line for the five companies that pass on volume and take rate, FY23 to FY25.
Revenue and oiadp: Compustat (EBAY, ETSY, CART from the supplement, ABNB and PYPL from valuechain/fin, where they already sit).
Volume: nine_frame.csv. Physical units, GAAP cost lines, stock pay and capex: filing panel in Consumer_Internet_Models/data.
Dollar volume makes revenue per unit the same number as take rate, so per $100 of volume is the common base and physical units are carried beside it."""
import json,os,re
import numpy as np,pandas as pd
B=os.path.expanduser('~/Downloads/ABNB/'); K=os.path.expanduser('~/Downloads/Consumer_Internet_Models/data/')
FIVE=['ABNB','EBAY','ETSY','PYPL','CART']; Y=[2023,2024,2025]
f=pd.read_csv(B+'reverse_eng/nine_frame.csv'); f=f[f.tic.isin(FIVE)]
assert sorted(f.tic.unique())==sorted(FIVE) and f.groupby('tic').size().eq(3).all() and set(f.fyear)==set(Y)
TAKE={'ABNB':'implied, revenue / GBV','EBAY':'implied, revenue / GMV','ETSY':'disclosed revenue take rate','PYPL':'implied, revenue / TPV','CART':'implied, revenue / GTV'}
UNIT={'ABNB':('nights booked','nights'),'PYPL':('payment transactions','txns'),'CART':('orders','orders')}
LINES={'ABNB':{'direct':['Cost of revenue'],'support':['Operations and support'],'marketing':['Sales and marketing'],'product':['Product development'],'ga':['General and administrative']},
'EBAY':{'direct':['Cost of net revenues','Transaction losses'],'marketing':['Sales and marketing'],'product':['Product development'],'ga':['General and administrative'],'special':['Amortization of acquired intangible assets']},
'ETSY':{'direct':['Cost of revenue'],'marketing':['Marketing'],'product':['Product development'],'ga':['General and administrative'],'special':['Asset impairment charges']},
'PYPL':{'direct':['Transaction expense','Transaction and credit losses'],'support':['Customer support and operations'],'marketing':['Sales and marketing'],'product':['Technology and development'],'ga':['General and administrative'],'special':['Restructuring and other']},
'CART':{'direct':['Cost of revenue'],'support':['Operations and support'],'marketing':['Sales and marketing'],'product':['Research and development'],'ga':['General and administrative']}}
OI={'ABNB':'Income from operations','EBAY':'Income from operations','ETSY':'Income from operations','PYPL':'Operating income','CART':'Income (loss) from operations'}
SBC={'ABNB':'Stock-based compensation expense','EBAY':'Stock-based compensation','ETSY':'Stock-based compensation expense','PYPL':'Stock-based compensation','CART':'Stock-based compensation expense'}
CAPEX={'EBAY':['Purchases of property and equipment'],'ETSY':['Purchases of property and equipment','Website and app development'],'PYPL':['Purchases of property and equipment'],'CART':['Purchases of property and equipment, including capitalized internal-use software']}
def panel(T):
    d=pd.read_csv(f'{K}{T}/long.csv'); d=d[(d.dur>=11)&d.end.str.endswith('12-31')].copy(); d['y']=d.end.str[:4].astype(int)
    return d[d.y.isin(Y)].sort_values('filed').drop_duplicates(['stmt','label','y'],keep='last')
def val(d,stmt,lab,y):
    x=d[(d.stmt==stmt)&(d.label==lab)&(d.y==y)].val
    return float(x.iloc[0]) if len(x) else 0.0
rows=[]
for T in FIVE:
    d=panel(T); k=json.load(open(f'{K}{T}/kpi.json'))
    for y in Y:
        r=f[(f.tic==T)&(f.fyear==y)].iloc[0]; rev,oi,vol=r.revt,r.oiadp,r.volume_fy; g=val(d,'is',OI[T],y)
        o=dict(tic=T,fyear=y,volume_measure=r.volume_measure.split(' (')[0],volume_usd_m=vol,revenue_usd_m=rev,oiadp_usd_m=oi,gaap_oi_usd_m=g,take_rate=rev/vol,take_rate_basis=TAKE[T])
        o['rev_per_100_volume']=rev/vol*100; o['oiadp_per_100_volume']=oi/vol*100; o['gaap_oi_per_100_volume']=g/vol*100
        o['gap_per_100_volume']=o['rev_per_100_volume']-o['oiadp_per_100_volume']; o['gaap_gap_per_100_volume']=o['rev_per_100_volume']-o['gaap_oi_per_100_volume']
        o['gap_share_of_revenue']=1-oi/rev; o['gaap_gap_share_of_revenue']=1-g/rev
        if T in UNIT:
            n,key=UNIT[T]; ps=[f'{y}Q{i}' for i in (1,2,3,4)]
            u=k[key][f'FY{y}'] if T=='ABNB' else sum(k[key][p] for p in ps)
            if T=='ABNB': u=sum(k[key][p] for p in ps)
            o.update(physical_unit=n,physical_units_m=u,rev_per_physical_unit=rev/u,oiadp_per_physical_unit=oi/u,gap_per_physical_unit=(rev-oi)/u,volume_per_physical_unit=vol/u)
        tot=0
        for grp,ls in LINES[T].items():
            v=sum(val(d,'is',l,y) for l in ls); tot+=v; o['cost_'+grp+'_per_100']=v/vol*100; o['cost_'+grp+'_pct_rev']=v/rev
        o['gaap_recon_usd_m']=rev-tot-g      # must be zero
        s=val(d,'cf',SBC[T],y); o['stock_pay_usd_m']=s; o['stock_pay_per_100']=s/vol*100; o['stock_pay_pct_rev']=s/rev
        o['oiadp_margin_before_stock_pay']=(oi+s)/rev
        cap={2023:47.0,2024:34.0,2025:33.0}[y] if T=='ABNB' else -sum(val(d,'cf',l,y) for l in CAPEX[T])
        o['capex_usd_m']=cap; o['capex_pct_rev']=cap/rev if cap else np.nan
        rows.append(o)
o=pd.DataFrame(rows)
assert o.gaap_recon_usd_m.abs().max()<1.5,o[['tic','fyear','gaap_recon_usd_m']]
o.to_csv(B+'reverse_eng/five_perunit.csv',index=False,float_format='%.4f')
print(len(o),'rows')
