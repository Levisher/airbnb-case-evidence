"""Take rate grid for Airbnb. FY25 and TTM Q2 26 from ABNB_Operating_Leverage_Workings_20261105.xlsx (ABNB Annual tab), TTM Q3 26 from the Q3 26 10-Q.
Contribution per night is revenue less cost of revenue less support before stock pay, the term in nights x (GBV per night x take - variable cost) - marketing - fixed.
A take move is points of GBV at constant GBV per night, so it adds ADR x points to revenue per night and no payment cost.
Per-night basis: marketing scales with nights, so a lost night also saves its marketing.
    (1 - loss) x (c + dR - M(1+m)) = c - M
Dollar basis: marketing dollars stay when nights leave.
    (1 - loss) x (c + dR) - M(1+m) = c - M"""
import json,os
import openpyxl,pandas as pd
B=os.path.expanduser('~/Downloads/ABNB/')
m=json.load(open(B+'operating_leverage/out/map.json')); R,col=m['R'],m['col']
A=openpyxl.load_workbook(B+'operating_leverage/ABNB_Operating_Leverage_Workings_20261105.xlsx',data_only=True)['ABNB Annual']
g=lambda k,c:float(A[f'{col[c]}{R[k]}'].value)
# TTM Q3 26 = FY25 + 9M 26 - 9M 25, from the 10-Q filed 5 Nov 2026. Q3 26 nights are rounded to 155m in that filing.
Q3=dict(nights=533.0+(304.5+155)-(277.5+133.6),gbv=91273+84149-70855,rev=12241+11155-9463,cogs=2086+1865-1599,opsx=(1327-90)+(1080-96)-(1000-66),bp=1595+1562-1204)
rows=[]
for c in ('FY25','TTM Q2 26','TTM Q3 26'):
    if c=='TTM Q3 26':
        N=Q3['nights']; adr=Q3['gbv']/N; tk=Q3['rev']/Q3['gbv']; rpn=Q3['rev']/N; cor,sup,M=Q3['cogs']/N,Q3['opsx']/N,Q3['bp']/N
    else:
        N,adr,tk=g('nights',c),g('adr',c),g('take',c); rpn=g('rpn',c)
        cor,sup,M=g('cogs',c)/N,g('opsx',c)/N,g('bp',c)/N
    con=rpn-cor-sup
    for pts in (0.5,1.0,1.5):
        dR=adr*pts/100
        for mk in (0.0,0.10,0.25):
            base=con-M; new=con+dR-M*(1+mk)
            rows.append(dict(period=c,nights_m=N,adr_usd=adr,take_rate=tk,rev_per_night_usd=rpn,cost_of_revenue_per_night_usd=cor,support_per_night_usd=sup,contribution_per_night_usd=con,marketing_per_night_usd=M,contribution_after_marketing_usd=base,
                take_move_pts=pts,new_take_rate=tk+pts/100,added_rev_per_night_usd=dR,marketing_rise=mk,added_marketing_per_night_usd=M*mk,net_gain_per_night_usd=dR-M*mk,new_contribution_after_marketing_usd=new,
                breakeven_night_loss=1-base/new,breakeven_nights_lost_m=N*(1-base/new),breakeven_night_loss_marketing_dollars_fixed=1-(con+M*mk)/(con+dR),
                implied_elasticity_if_guest_pays=(1-base/new)/(pts/100),marketing_rise_that_cancels_move=dR/M))
o=pd.DataFrame(rows); o.to_csv(B+'reverse_eng/nine_takerate.csv',index=False,float_format='%.4f'); print(len(o),'rows')
