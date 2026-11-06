"""Replacement test. Needed share on the $948 host take against what each alternative delivers, in a review-count form and in forms that use no review counts.
Writes replacement_test.csv. Needed = host take / (host take + fee saved). Delivered = bookings or revenue per 100 on Airbnb."""
import sys,os,json,csv,numpy as np,pandas as pd
B=os.path.expanduser('~/Downloads/ABNB'); os.chdir(B)
sys.path.insert(0,f'{B}/rival_overlap/04_analysis/scripts')
import ro_common as r
from ro_overlap_lib import air
num=lambda s:pd.to_numeric(s,errors='coerce')
TAKE,GROSS,FEE=948.0,1378.0,.155
ALT={'Vrbo':.12,'Booking':.15,'Own site':.029}
need={a:100*TAKE/(TAKE+(FEE-f)*GROSS) for a,f in ALT.items()}
saved={a:(FEE-f)*GROSS for a,f in ALT.items()}
rows=[]
def add(alt,form,measure,pop,val,same,reviews,src,note='',hi=None):
    n=need[alt]; rows.append(dict(alternative=alt,host_fee_pct=100*ALT[alt],fee_saved_per_stay=round(saved[alt],0),host_take=TAKE,replacement_needed_pct=round(n,1),
      delivered_form=form,delivered_measure=measure,population=pop,delivered_per_100_airbnb=round(val,1),delivered_high=(round(hi,1) if hi is not None else ''),
      shortfall_points=round(n-val,1),growth_needed_on_current_pct=round(100*n/val,0) if val>0 else '',meets_needed='Yes' if val>=n else ('Only at high end' if hi is not None and hi>=n else 'No'),
      same_homes=same,uses_review_counts=reviews,source=src,note=note))
# review proxy
m=pd.read_pickle('altdata/reframe/direct/matched_rows.pkl')
for c in ['r_reviews','number_of_reviews']: m[c]=num(m[c])
x=m[(m.hit==True)&(m.ab_n==1)&m.number_of_reviews.notna()].copy(); x['r']=x.r_reviews.fillna(0)
S={'booking':'Booking','vrbo':'Vrbo'}
for s,a in S.items():
    z=x[x.site==s]; y=z[z.market!='lisbon']
    add(a,'Review proxy','Reviews on licence-matched homes, as filed','San Diego, Seattle, Hawaii',100*y.r.sum()/y.number_of_reviews.sum(),'Yes','Yes','matched_rows, Inside Airbnb Sep 2026, rival pull 5 Nov 2026',f'{len(y)} homes, Lisbon left out')
    add(a,'Review proxy','Same, Lisbon included','Four markets',100*z.r.sum()/z.number_of_reviews.sum(),'Yes','Yes','matched_rows',f'{len(z)} homes')
    add(a,'Review proxy','Same, median home','San Diego, Seattle, Hawaii',100*(y.r/y.number_of_reviews.replace(0,np.nan)).median(),'Yes','Yes','matched_rows','Median of home ratios')
    for mk,g in z.groupby('market'):
        add(a,'Review proxy','Same, one market',mk,100*g.r.sum()/g.number_of_reviews.sum(),'Yes','Yes','matched_rows',f'{len(g)} homes')
add('Own site','Review proxy','Same-host repeat stays, as filed','Ten cities',2.0,'No','Yes','findings, same-host repeat 1.69% to 2.28% of 2025 stays','Measures repeat stays on Airbnb, with no own-site bookings in it')
# second measure: channel bookings and revenue
mix={r0[0]:r0[1:] for r0 in json.load(open('valuechain/tables.json'))['MIX']['rows'][1:]}
K='KeyData Q2 2026 via RedAwning, Sep 2026'
R26,V26=(51,43),(20,23); D26=(21,29); O26=(8,5); D25=(25,36); A25=(47,36)
for i,lab in enumerate(['reservations','revenue']):
    add('Vrbo','Channel share',f'{lab.title()} on Vrbo, Q2 2026','US professionally managed homes',100*V26[i]/R26[i],'Same managers, home level unknown','No',K,'Before the 29 Oct fee change')
    add('Booking','Channel share',f'{lab.title()} on all other channels, Q2 2026, a ceiling for Booking','US professionally managed homes',100*O26[i]/R26[i],'Same managers, home level unknown','No',K,'All other, by subtraction, so Booking is at or below this')
    add('Own site','Channel share',f'Direct {lab}, Q2 2026','US professionally managed homes',100*D26[i]/R26[i],'Same managers, home level unknown','No',K,'Airbnb direct links may count as Airbnb')
    add('Own site','Channel share',f'Direct {lab}, Q2 2025','US professionally managed homes',100*D25[i]/A25[i],'Same managers, home level unknown','No',K,'Before the single fee')
# filings on identical units
add('Booking','Filing','Sonder 2024 revenue, Booking against Airbnb, lowest and highest ordering','Sonder units worldwide',100*12/22,'Yes','No','Sonder 10-K FY2024','Three agencies at 22%, 17%, 12%, unnamed',hi=100*22/12)
add('Own site','Filing','Sonder 2024 direct revenue 45.8% against Airbnb at 22% to 12%','Sonder units worldwide',100*45.8/22,'Yes','No','Sonder 10-K FY2024','Includes corporate and sales staff bookings',hi=100*45.8/12)
add('Own site','Filing','Vacasa 2024 direct GBV 30% against Airbnb at 42.4% to 35%','Vacasa homes',100*30/42.4,'Yes','No','Vacasa 10-K FY2024; Airbnb share is the audit estimate','Airbnb share estimated, not disclosed',hi=100*30/35)
# card panel
d=pd.read_csv('altdata/marketing/card/monthly_brand_spend.csv'); p=d[d.m>='2025-03'].pivot_table(index='m',columns='b',values='sp',aggfunc='sum'); s=p.sum()
add('Vrbo','Card spend','Vrbo spend, Mar 2025 to Feb 2026','US card panel, all homes',100*s['VRBO']/s['AIRBNB'],'No','No','card panel, ratio only','Market level')
add('Booking','Card spend','Booking.com spend, Mar 2025 to Feb 2026, includes hotels','US card panel',100*s['BOOKING.COM']/s['AIRBNB'],'No','No','card panel, ratio only','Pay-at-property guests are missing')
add('Own site','Card spend','Vacasa, Evolve, AvantStay and Sonder spend, Mar 2025 to Feb 2026','US card panel',100*sum(s[b] for b in ['VACASA','EVOLVE VACATION RENTAL','AVANTSTAY','SONDER'])/s['AIRBNB'],'No','No','card panel, ratio only','Direct brands only, a floor for own sites')
# calendar: forward booked nights on the Airbnb calendar, same host, rival-listed against not listed
cal=[]
for mk in ['seattle','san_diego']:
    a=air(mk); dd=pd.read_csv(r.P+f'02_interim/candidate_pairs/{mk}_rung1.csv'); dd=dd[~dd.type.astype(str).str.contains('hotel|hostel|resort',case=False)]
    K2=set()
    for v in dd['keys'].dropna(): K2|=set(str(v).split('|'))
    e=a[a.elig&(a.k.str.len()>0)].copy(); e['any']=[len(set(k)&K2)>0 for k in e.k]
    e['f']=365-num(e.availability_365); e['f90']=90-num(e.availability_90); e['h']=e.host_id
    g=e.groupby('h')['any'].transform('nunique')==2; z=e[g].dropna(subset=['f','f90'])
    for col,lab in (('f','365'),('f90','90')):
        t=z.groupby(['h','any'])[col].mean().unstack(); w=z.groupby('h').size()
        diff=(t[True]-t[False]); base=t[False]
        cal.append(dict(market=mk,window=lab,hosts=len(t),homes=len(z),listed=(t[True]*w).sum()/w.sum(),unlisted=(base*w).sum()/w.sum()))
c=pd.DataFrame(cal); print(c.round(1).to_string())
for r0 in c[c.window=='365'].itertuples():
    add('Vrbo','Calendar','Blocked forward nights, rival-listed against unlisted homes of the same host, change per 100',r0.market,100*(r0.listed-r0.unlisted)/r0.unlisted,'Same host','No','Inside Airbnb calendar, keyed rival rows',f'{r0.homes} homes, {r0.hosts} hosts. Booking and Vrbo pooled. Hosts list open homes on rivals, so this is biased low')
o=pd.DataFrame(rows)
o.loc[o.delivered_form=='Calendar','alternative']='Vrbo and Booking pooled'
o.loc[o.delivered_form=='Calendar','host_fee_pct']=''; o.loc[o.delivered_form=='Calendar','fee_saved_per_stay']=''
o.loc[o.delivered_form=='Calendar','replacement_needed_pct']=round(need['Vrbo'],1)
sens=[('Vrbo at 8%, before 29 Oct',.08,''),('Own site with 5% marketing',.079,'Marketing rate is an assumption'),('Host take $600',None,'Vrbo at 12%, higher running costs, assumption'),('Own site, host take $600',None,'2.9% card cost, higher running costs, assumption')]
ext=[]
for lab,f,nt in sens:
    tk=TAKE if f is not None else 600.0; ff=f if f is not None else (.029 if 'Own' in lab else .12)
    sv=(FEE-ff)*GROSS
    ext.append(dict(alternative=lab,host_fee_pct=round(100*ff,1),fee_saved_per_stay=round(sv,0),host_take=tk,replacement_needed_pct=round(100*tk/(tk+sv),1),delivered_form='Needed sensitivity',note=nt))
o=pd.concat([o,pd.DataFrame(ext)],ignore_index=True); o.to_csv(f'{B}/audit/replacement_test.csv',index=False)
pd.set_option('display.width',230,'display.max_colwidth',62,'display.max_rows',80)
print(o[['alternative','delivered_form','delivered_measure','population','delivered_per_100_airbnb','delivered_high','shortfall_points','growth_needed_on_current_pct','meets_needed']].to_string())
print(need,saved)
