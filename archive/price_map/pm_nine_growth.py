"""Growth above break-even for the nine case companies on one definition, FY23 to FY25, from filed XBRL lines."""
import pandas as pd
D='~/Downloads/ABNB/altdata/holistic/data/'
p=pd.read_csv(D+'peer_pnl.csv').set_index('t');a=pd.read_csv(D+'peer_annual.csv')
a=a.sort_values('filed').drop_duplicates(['t','g','y'],keep='last')
def cost(t,y):
    for g in ['CostOfRevenue','CostOfGoodsAndServicesSold']:
        x=a[(a.t==t)&(a.g==g)&(a.y==y)]
        if len(x): return x.v.iloc[0]/1e6
rows=[]
for t in ['ABNB','EBAY','ETSY','W','PYPL','SNAP','PINS','ROKU','CART','BKNG','EXPE']:
    r={}
    for y in (2023,2025):
        rev=p.loc[t,f'rev{y}'];m=p.loc[t,f'sm{y}'];m=p.loc[t,f'ad{y}'] if pd.isna(m) else m
        c=cost(t,y);op=p.loc[t,f'op{y}'];s=p.loc[t,f'sbc{y}'];s=0 if pd.isna(s) else s
        r[y]=dict(rev=rev,c=c,m=m,e=op+s)
    if r[2023]['c'] is None or r[2025]['c'] is None: rows.append(dict(t=t,note='no cost line'));continue
    f=lambda y:r[y]['rev']-r[y]['c']-r[y]['m']-r[y]['e']
    con=r[2025]['rev']-r[2025]['c']-r[2025]['m']
    g=(r[2025]['rev']/r[2023]['rev'])**.5-1;fg=(f(2025)/f(2023))**.5-1;sh=f(2025)/con
    rows.append(dict(t=t,rev_g=100*g,mkt_rev=100*r[2025]['m']/r[2025]['rev'],gross_after_mkt=100*con/r[2025]['rev'],fixed_g=100*fg,fixed_share=100*sh,needed=100*fg*sh,surplus=100*(g-fg*sh),margin=100*r[2025]['e']/r[2025]['rev']))
o=pd.DataFrame(rows).round(1);print(o.to_string());o.to_csv('~/Downloads/ABNB/price_map/out/nine_growth.csv',index=False)
