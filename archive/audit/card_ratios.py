"""Card panel readings as ratios inside one panel, with bias directions and attrition flags.

Source is the card panel customer return table (ratios only). No counts or spend levels leave this
script. Attrition is calibrated on saturated brands, where nearly every panellist shops monthly, so a closed
group's fall there is close to panel loss. Common attrition scales every brand alike and cancels in a ratio
between brands, so a gap can only come from attrition if one brand's customers leave the panel faster. The
band is therefore the full attrition over the reading window, loaded on one brand alone.
Writes card_ratios.csv (one row per brand), card_ratio_pairs.csv (all brand pairs), card_older_group.csv.
"""
import csv, itertools, os, duckdb, numpy as np, pandas as pd
H = os.path.expanduser('~/Downloads/'); O = H + 'ABNB/audit/'
G = H + 'card_panel_extract/**/*.parquet'
B = {'AIRBNB': 'Airbnb', 'BOOKING.COM': 'Booking', 'EXPEDIA': 'Expedia', 'VRBO': 'Vrbo', 'HILTON HOTELS': 'Hilton', 'MARRIOTT': 'Marriott'}
FLOOR = ['WALMART (EX FUEL)', 'TARGET', 'COSTCO (EX FUEL)']
STRESS_BR = ['AMAZON MARKETPLACE', "MCDONALD'S", 'WALGREENS']
c = duckdb.connect()
q = ','.join("'" + x.replace("'", "''") + "'" for x in list(B) + FLOOR + STRESS_BR)
d = c.execute(f"""select BRAND_NAME b,FIRST_SHOP_PERIOD f,FIRST_SHOP_PERIOD_COUNT::INT a,INDIVIDUAL_COUNT n,PERIOD p,PERIOD_TYPE pt,SPEND_AMOUNT s,TRANS_COUNT t
 from read_parquet('{G}',hive_partitioning=false) where BRAND_NAME in ({q})""").df()
m = d[d.pt == 'MONTH']; qt = d[d.pt == 'CAL_QTR']
allb = c.execute(f"""select BRAND_NAME b,
 sum(case when PERIOD='2025M07' and FIRST_SHOP_PERIOD<'2024M07' then INDIVIDUAL_COUNT else 0 end) o25,
 sum(case when PERIOD='2026M07' and FIRST_SHOP_PERIOD<'2024M07' then INDIVIDUAL_COUNT else 0 end) o26,
 sum(case when PERIOD='2025M07' then INDIVIDUAL_COUNT else 0 end) t25, sum(case when PERIOD='2026M07' then INDIVIDUAL_COUNT else 0 end) t26,
 sum(case when FIRST_SHOP_PERIOD_COUNT=0 then INDIVIDUAL_COUNT else 0 end) nw, sum(INDIVIDUAL_COUNT) al, sum(TRANS_COUNT) tr, sum(SPEND_AMOUNT) sp
 from read_parquet('{G}',hive_partitioning=false) where PERIOD_TYPE='MONTH' group by 1""").df()
allb['chg'] = allb.o26 / allb.o25 - 1; allb['tot'] = allb.t26 / allb.t25 - 1; allb['tk'] = allb.sp / allb.tr; allb['a0'] = allb.nw / allb.al; allb['act'] = allb.al / 13


def older(b): return float(allb[allb.b == b].chg.iloc[0])


att = -np.mean([older(x) for x in FLOOR]); stress = -min(older(x) for x in STRESS_BR)
entry = float(allb[allb.b == 'WALMART (EX FUEL)'].a0.iloc[0]); entry_s = entry * stress / att
R = {}
for b, nm in B.items():
    x = m[(m.b == b) & (m.f == '2025M07')]; n0 = x[x.a == 0].n.sum(); s0 = x[x.a == 0].s.sum(); w = x[(x.a >= 3) & (x.a <= 12)]
    y = qt[(qt.b == b) & (qt.f == '2025Q3')].set_index('p'); r3 = y.n['2026Q2'] / y.n['2025Q3']
    z = m[m.b == b]
    R[nm] = dict(active_3q=100 * r3, months_3_12=100 * w.n.sum() / n0, later_spend=100 * w.s.sum() / s0, new_share=100 * z[z.a == 0].n.sum() / z.n.sum(), se3=100 * (r3 * (1 - r3) / y.n['2025Q3']) ** .5)
T = {'active_3q': 9, 'months_3_12': 7.5, 'later_spend': 7.5}
band = lambda rate, t: 1 - (1 - rate) ** (t / 12)
LBL = {'active_3q': 'share_new_group_active_3q_later_pct', 'months_3_12': 'active_months_per_100_m3_12', 'later_spend': 'later_spend_pct_first_month', 'new_share': 'new_share_of_monthly_actives_pct'}
DIR = {
 'Airbnb': dict(active_3q='attrition down, common to all brands; pay-later down, charges move nearer the stay and can fall after the quarter; wallet down, PayPal and pay-over-time checkouts hide the merchant',
   months_3_12='attrition down, common; pay-later mixed, split charges add months and deferred charges leave the window; wallet down',
   later_spend='attrition down, common; pay-later mixed, deferral moves spend past month 12 and split payment moves first-month spend later; wallet down',
   new_share='attrition up, panel entrants look new; pay-later up slightly, first charge comes later for a returning guest gap; wallet up, a hidden repeat guest reappears as new'),
 'Booking': dict(active_3q='attrition down, common; pay-later none at Booking, but pay-at-property charges miss the merchant, so strongly down; wallet down',
   months_3_12='attrition down, common; pay-at-property strongly down; wallet down', later_spend='attrition down, common; pay-at-property strongly down; wallet down',
   new_share='attrition up; pay-at-property strongly up, old customers enter as new when a merchant-of-record stay appears; wallet up'),
 'Expedia': dict(active_3q='attrition down, common; pay-later small, some pay-at-hotel; wallet down', months_3_12='attrition down, common; pay-later small; wallet down', later_spend='attrition down, common; pay-later small; wallet down', new_share='attrition up; pay-later small; wallet up'),
 'Vrbo': dict(active_3q='attrition down, common; split payment up, second charge can land in a later quarter; wallet down', months_3_12='attrition down, common; split payment up, second charge adds an active month with no new trip; wallet down', later_spend='attrition down, common; split payment up, second charge counts as later spend; wallet down', new_share='attrition up, large for a low-frequency brand; split payment small; wallet up'),
 'Hilton': dict(active_3q='attrition down, common; charged at stay, no timing lag; wallet small, chain also splits across sub-brands, down', months_3_12='attrition down, common; charged at stay; sub-brand split down', later_spend='attrition down, common; charged at stay; sub-brand split down', new_share='attrition up, large for a low-frequency brand; sub-brand split up'),
 'Marriott': dict(active_3q='attrition down, common; charged at stay, no timing lag; wallet small, chain also splits across sub-brands, down', months_3_12='attrition down, common; charged at stay; sub-brand split down', later_spend='attrition down, common; charged at stay; sub-brand split down', new_share='attrition up, large for a low-frequency brand; sub-brand split up')}


def flag(k, x, y):
    """Could attrition loaded on one brand alone produce the gap between x and y."""
    if k == 'new_share':
        px, py = R[x]['months_3_12'] / 1000, R[y]['months_3_12'] / 1000
        gap = abs(R[x][k] - R[y][k]); bc = abs(100 * entry / px - 100 * entry / py); bs = abs(100 * entry_s / px - 100 * entry_s / py)
        return gap, bc, bs, ('yes' if bc >= gap else 'stress only' if bs >= gap else 'no')
    hi, lo = max(R[x][k], R[y][k]), min(R[x][k], R[y][k])
    gap = hi / lo - 1; bc = band(att, T[k]) / (1 - band(att, T[k])); bs = band(stress, T[k]) / (1 - band(stress, T[k]))
    return gap * 100, bc * 100, bs * 100, ('yes' if bc >= gap else 'stress only' if bs >= gap else 'no')


rows = []
for nm in B.values():
    r = {'brand': nm}
    for k, l in LBL.items():
        r[l] = round(R[nm][k], 1); r[l + '_bias_direction'] = DIR[nm][k]
        r[l + '_attrition_flag_vs_airbnb'] = 'base brand' if nm == 'Airbnb' else flag(k, 'Airbnb', nm)[3]
    r['attrition_flags_other_pairs'] = '; '.join(f"{y if x == nm else x} on {k}: {flag(k, x, y)[3]}" for x, y in itertools.combinations(B.values(), 2) if nm in (x, y) and 'Airbnb' not in (x, y) for k in LBL if flag(k, x, y)[3] != 'no') or 'none'
    r['panel'] = 'card panel return table, Jul 2025 to Jul 2026, ratios only'
    r['definitions'] = 'active_3q: Q3 2025 new group active in Q2 2026. Months 3-12 and later spend: Jul 2025 new group. New share: age 0 people over all people, 13 months.'
    r['direction_basis'] = 'Expected direction from how each brand charges. Measured only for attrition.'
    rows.append(r)
with open(O + 'card_ratios.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
P = []
for x, y in itertools.combinations(B.values(), 2):
    for k, l in LBL.items():
        g, bc, bs, fl = flag(k, x, y)
        P.append(dict(brand_a=x, brand_b=y, reading=l, value_a=round(R[x][k], 1), value_b=round(R[y][k], 1), gap=round(g, 1), gap_unit='points' if k == 'new_share' else 'percent of lower', attrition_band=round(bc, 1), stress_band=round(bs, 1), flag=fl))
pd.DataFrame(P).to_csv(O + 'card_ratio_pairs.csv', index=False)
print(f'attrition {att:.4f} stress {stress:.4f} entry {entry:.5f} stress entry {entry_s:.5f}')
print(pd.DataFrame(R).T.round(2).to_string())
pp = pd.DataFrame(P); print(pp.flag.value_counts().to_dict()); print(pp[pp.flag != 'no'].to_string(index=False))
print(pp[pp.brand_a == 'Airbnb'][['brand_b', 'reading', 'gap', 'attrition_band', 'stress_band', 'flag']].to_string(index=False))
# older group test
base = allb[(allb.o25 >= 300) & np.isfinite(allb.chg)].copy()
A = older('AIRBNB')
tick = base[(base.tk >= 300) & (base.act >= 3000)]; tick2 = base[(base.tk >= 200) & (base.act >= 3000)]
L = []
def add(s, v, n=''): L.append(dict(test=s, value=round(v, 2) if isinstance(v, float) else v, note=n))
for b, nm in {**B, **{x: x.title() for x in FLOOR}}.items():
    add(f'{nm}: people first seen before Jul 2024, Jul 2025 to Jul 2026, %', 100 * older(b)); add(f'{nm}: all active people, Jul 2025 to Jul 2026, %', 100 * float(allb[allb.b == b].tot.iloc[0]))
add('Attrition floor, mean of Walmart, Target, Costco, %', -100 * att, 'High-frequency brands')
add('Share of the 10.5% that the floor explains, %', 100 * att / -A)
add('All brands: median change, %', 100 * float(base.chg.median()), f'{len(base)} brands with a usable base')
add('All brands: share of brands doing worse than Airbnb, %', 100 * float((base.chg < A).mean()))
add('Ticket $300 plus: median change, %', 100 * float(tick.chg.median()), f'{len(tick)} brands')
add('Ticket $300 plus: share doing worse than Airbnb, %', 100 * float((tick.chg < A).mean()))
add('Ticket $200 plus: median change, %', 100 * float(tick2.chg.median()), f'{len(tick2)} brands')
add('Ticket $200 plus: share doing worse than Airbnb, %', 100 * float((tick2.chg < A).mean()))
for b, nm in {'AIRBNB': 'Airbnb', 'EXPEDIA': 'Expedia', 'VRBO': 'Vrbo', 'BOOKING.COM': 'Booking', 'HILTON HOTELS': 'Hilton', 'MARRIOTT': 'Marriott', 'WALMART (EX FUEL)': 'Walmart'}.items():
    z = m[(m.b == b) & (m.f < '2024M07')]; z = z.assign(y=z.f.str[:4])
    t = z[z.p.isin(['2025M07', '2026M07'])].groupby(['y', 'p'])[['n', 's', 't']].sum().unstack('p')
    for y in t.index:
        add(f'{nm}: first seen {y}, people change %', 100 * float(t.loc[y, ('n', '2026M07')] / t.loc[y, ('n', '2025M07')] - 1))
    tt = z[z.p.isin(['2025M07', '2026M07'])].groupby('p')[['n', 's', 't']].sum()
    add(f'{nm}: older group spend change %', 100 * float(tt.s['2026M07'] / tt.s['2025M07'] - 1)); add(f'{nm}: older group transactions per active change %', 100 * float((tt.t['2026M07'] / tt.n['2026M07']) / (tt.t['2025M07'] / tt.n['2025M07']) - 1)); add(f'{nm}: older group spend per transaction change %', 100 * float((tt.s['2026M07'] / tt.t['2026M07']) / (tt.s['2025M07'] / tt.t['2025M07']) - 1))
bt = pd.read_csv(H + 'ABNB/altdata/out/backtest_yoy.csv').dropna(subset=['card_tx']); bt['gap'] = bt.card_tx - bt.nights
for _, r_ in bt.iterrows(): add(f"Airbnb card transactions YoY less reported nights YoY, {r_.p}, points", float(r_.gap), 'Reserve Now, Pay Later launched at the start of Q3 2025')
add('Mean gap, Q1 2024 to Q2 2025, points', float(bt[bt.p < '2025Q3'].gap.mean())); add('Mean gap, Q3 and Q4 2025, points', float(bt[bt.p >= '2025Q3'].gap.mean()))
pd.DataFrame(L).to_csv(O + 'card_older_group.csv', index=False)
print(pd.DataFrame(L).to_string(index=False, max_colwidth=60))
for b in ('KLARNA', 'AFFIRM', 'PAYPAL', 'AFTERPAY', 'VENMO'):
    x = allb[allb.b.str.contains(b)]; print(x[['b', 'chg', 'tot']].round(3).head(4).to_string(header=False))
