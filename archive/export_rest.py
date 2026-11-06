"""Builds the committed tables for conversion/, contribution/ and cost/. Card panel and Compustat values leave this script only as ratios; Google cell counts stay out."""
import json, os, shutil, sys
import duckdb, numpy as np, pandas as pd
A = os.path.expanduser('~/Downloads/ABNB/'); R = A + 'airbnb-case-evidence/'; D = A + 'audit/'; MECH = A + 'altdata/reframe/mech/'
num = lambda s: pd.to_numeric(s, errors='coerce')
cp = lambda s, d: shutil.copy(s, R + d)

# review depth: matched homes as market x site sums
m = pd.read_pickle(A + 'altdata/reframe/direct/matched_rows.pkl')
for c in ['r_reviews', 'number_of_reviews', 'number_of_reviews_ltm']: m[c] = num(m[c])
x = m[(m.hit == True) & (m.ab_n == 1) & m.number_of_reviews.notna()].copy(); x['r'] = x.r_reviews.fillna(0)
g = x.groupby(['market', 'site']).apply(lambda t: pd.Series(dict(homes=len(t), airbnb_reviews=t.number_of_reviews.sum(), rival_reviews=t.r.sum(), airbnb_ahead=(t.number_of_reviews > t.r).sum(), last_12m_beats_rival_lifetime=(t.number_of_reviews_ltm > t.r).sum())), include_groups=False).reset_index()
g.to_csv(R + 'conversion/review_depth/matched_home_sums.csv', index=False); print(g)
cp(MECH + 'same_home_coldstart.csv', 'conversion/review_depth/same_home_coldstart.csv')
for f in ('exit_by_depth.csv', 'same_host_depth.csv', 'rebuild_months.csv'): cp(MECH + f, 'conversion/review_content/' + f)
cp(A + 'altdata/equations/conv_by_trust.csv', 'conversion/review_content/conv_by_trust.csv'); cp(A + 'altdata/out/s6_exit_by_rating.csv', 'conversion/review_content/exit_by_rating.csv')
cp(MECH + 'support_return.csv', 'conversion/review_content/support_return.csv')

# stay ladder: the selection model needs only stay number x tenure cells
g_ = f'{D}_ladder/g.parquet'; k = duckdb.connect(); k.execute("set memory_limit='9GB'; set threads=4"); CAP = 9764 - 730
k.execute(f"create temp table st as select reviewer,dn,seq,c,fdn,ndn,dn-pdn gap,y,year(date '2000-01-01'+cast(fdn as int)) fy from '{g_}'")
k.execute("""create temp table tr as with a as (select reviewer,dn,fdn,fy,sum(case when gap is null or gap>14 then 1 else 0 end) over (partition by reviewer order by dn,seq) tn from st),
   b as (select reviewer,tn,min(dn) dn,max(dn) dl,min(fdn) fdn,min(fy) fy from a group by 1,2)
   select reviewer,tn seq,dl dn,fdn,fy,lead(dn) over w ndn,count(*) over (partition by reviewer) c,year(date '2000-01-01'+cast(dl as int)) y from b window w as (partition by reviewer order by tn)""")
sel = pd.read_csv(D + '_ladder/sel.csv'); print(sel['sample'].tolist()); out = []
for lab, tbl, lo, ylo in [('stays, first seen 2022+', 'st', 2022, 2022), ('trips, first seen 2022+', 'tr', 2022, 2022), ('stays, first seen 2019+, stays 2022-24', 'st', 2019, 2022), ('trips, first seen 2019+, stays 2022-24', 'tr', 2019, 2022), ('stays, all history, stays 2022-24', 'st', 0, 2022), ('stays, all history, stays 2019-24', 'st', 0, 2019)]:
    d = k.execute(f"""select least(seq,12) k,floor((dn-fdn)/91.0) tq,count(*) n,sum((ndn is not null and ndn-dn<=730 and ndn>dn)::int) r,avg((dn-fdn)/365.25) t from {tbl} where fy>={lo} and y>={ylo} and y<=2024 and dn<={CAP} group by 1,2""").df()
    d = d[d.n > 0]; d.insert(0, 'sample', lab); out.append(d); print(lab, d.n.sum())
pd.concat(out).to_csv(R + 'conversion/stay_ladder/selection_cells.csv', index=False, float_format='%.8g')
for s, d in (('stay_ladder_refit.csv', 'stay_ladder_refit.csv'), ('stay_ladder_refit_tests.csv', 'stay_ladder_tests.csv'), ('_ladder/sel.csv', 'selection_fits_as_run.csv'), ('_ladder/fe.csv', 'same_guest_gaps.csv'), ('_ladder/review_loss.csv', 'review_loss.csv')): cp(D + s, 'conversion/stay_ladder/' + d)

# card panel: ratios only. n0 and all spend levels are dropped
for f in ('card_ratios.csv', 'card_ratio_pairs.csv', 'card_older_group.csv'): cp(D + f, 'conversion/card_panel/' + f)
c = pd.read_csv(A + 'altdata/reframe/direct/cohort_cells.csv'); c = c[(c.age >= 3) & c.BRAND_NAME.isin(['AIRBNB', 'VRBO', 'EXPEDIA', 'BOOKING.COM'])]
c.pivot_table(index=['f', 'age'], columns='BRAND_NAME', values='sh').reset_index().rename(columns={'f': 'start_month', 'AIRBNB': 'airbnb_active_pct', 'VRBO': 'vrbo_active_pct', 'EXPEDIA': 'expedia_active_pct', 'BOOKING.COM': 'booking_active_pct'}).to_csv(R + 'conversion/card_panel/matched_group_shares.csv', index=False, float_format='%.6f')
q = pd.read_csv(A + 'altdata/out/ce_cohort_quarterly.csv').drop(columns=['new_q3']); q.to_csv(R + 'conversion/card_panel/active_share_by_quarter.csv', index=False)
pd.DataFrame([('first month', 0.8677), ('months 1 to 6 after', 1.5119)], columns=['window', 'airbnb_over_vrbo_spend_per_customer']).to_csv(R + 'conversion/card_panel/spend_ratio_vrbo.csv', index=False)

# location and Lisbon price: summaries only
cp(D + 'gmp_cells.csv', 'conversion/location/gmp_cells.csv'); cp(A + 'price_map/out/location_r2.csv', 'conversion/location/location_r2.csv')
t = pd.read_csv(A + 'price_map/out/t1_lisbon.csv')
s = t.groupby('bed').agg(homes=('ratio', 'size'), median_ratio_two_rooms=('ratio', 'median'), share_cheaper=('ratio', lambda v: (v < 1).mean()), median_ratio_cheapest_quarter=('ratio4', 'median')).reset_index(); s.to_csv(R + 'conversion/hotel_price/lisbon_ratio_by_bedrooms.csv', index=False, float_format='%.4f'); print(s, t.ratio.median(), (t.ratio < 1).mean(), t.ratio4.median())
pd.DataFrame([dict(homes=len(t), median_ratio_two_rooms=t.ratio.median(), share_cheaper=(t.ratio < 1).mean())]).to_csv(R + 'conversion/hotel_price/lisbon_ratio_all.csv', index=False, float_format='%.4f')

# nights split
f = json.load(open(A + 'nights/data/final.json')); import ast
br = f['br'] if isinstance(f['br'], dict) else ast.literal_eval(f['br'])
pd.DataFrame([dict(term=k, change_2023_to_2025_pct=v['chg']) for k, v in br.items() if isinstance(v, dict) and 'chg' in v]).to_csv(R + 'conversion/nights_split/terms.csv', index=False, float_format='%.6f')
cp(A + 'nights/data/identity.csv', 'conversion/nights_split/account_identity.csv')

# public filing inputs, typed from the 10-K and 10-Q files
sys.path.insert(0, A + 'operating_leverage/_scripts'); import inputs as I
rows = [dict(company='Airbnb', line=k, period=f'FY{y}', value=v) for k, vs in I.A.items() for y, v in zip(I.Y, vs) if v is not None]
rows += [dict(company='Airbnb', line=k, period=p, value=v) for k, vs in I.H.items() for p, v in zip(('H1 2025', 'H1 2026'), vs)]
for nm, d in (('Booking', I.B), ('Expedia', I.E_)):
    rows += [dict(company=nm, line=k, period=f'FY{y}', value=v) for k, vs in d.items() if k != 'y' for y, v in zip(d['y'], vs) if v is not None]
L = pd.DataFrame(rows)
for d in ('contribution/equation', 'contribution/take_rate', 'contribution/sensitivity', 'cost/net_take', 'cost/added_nights'): L.to_csv(R + d + '/filing_lines.csv', index=False)
print(L.groupby('company').line.unique().to_dict())
cp(D + 'nine_takerate.csv', 'contribution/take_rate/take_rate_grid.csv'); cp(D + 'sensitivity_grid.csv', 'contribution/sensitivity/sensitivity_grid.csv'); cp(D + 'replacement_test.csv', 'contribution/replacement/replacement_test.csv')
cp(D + 'per100_peers.csv', 'cost/per_100/per100_lines.csv'); cp(D + 'per100_gap_split.csv', 'cost/per_100/gap_split.csv')

# nine models: Compustat levels removed, ratios kept
n = pd.read_csv(D + 'nine_frame.csv').drop(columns=['revt', 'oiadp', 'emp', 'fundq_oi_gap_usd_m', 'data_source'], errors='ignore'); n.to_csv(R + 'cost/nine_models/nine_frame_ratios.csv', index=False)
p = pd.read_csv(D + 'five_perunit.csv'); p = p[[c for c in p.columns if not c.endswith('_usd_m') and c != 'physical_units_m']]; p.to_csv(R + 'cost/nine_models/five_perunit_ratios.csv', index=False)
cp(A + 'price_map/out/nine_growth.csv', 'cost/nine_models/nine_growth.csv')
