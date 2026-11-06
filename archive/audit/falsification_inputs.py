"""Numbers behind falsification.md, recomputed from the terms in sensitivity_grid.py and filing lines."""
import math, os, runpy, duckdb
g = runpy.run_path(os.path.expanduser('~/Downloads/ABNB/audit/sensitivity_grid.py'), run_name='x') if False else None
import importlib.util, io, contextlib
sp = importlib.util.spec_from_file_location('sg', os.path.expanduser('~/Downloads/ABNB/audit/sensitivity_grid.py')); m = importlib.util.module_from_spec(sp)
with contextlib.redirect_stdout(io.StringIO()): sp.loader.exec_module(m)
P, terms, fx = m.P, m.terms, m.fx
nt = lambda p: 100 * (p['rev'] / p['gbv'] - p['m'] / p['gbv'])
FY23 = dict(rev=9917, gbv=73252, m=1208)
print('net take FY23', round(nt(FY23), 2), {k: round(nt(P[k]), 2) for k in ('FY24', 'FY25', 'TTM Q2 26', 'TTM Q3 25', 'TTM Q3 26')})
print('take', {k: round(100 * P[k]['rev'] / P[k]['gbv'], 2) for k in ('FY25', 'TTM Q2 26', 'TTM Q3 26')}, 'mkt rate', {k: round(100 * P[k]['m'] / P[k]['gbv'], 2) for k in ('FY25', 'TTM Q2 26', 'TTM Q3 26')})
print('Booking net take FY24, FY25', round(100 * (23739 - 7278) / 165580, 2), round(100 * (26917 - 8186) / 186107, 2))
q = {'Q1': ((1091 - 579) / 156.2, (824 - 446) / 143.1), 'Q2': (579 / 148.3, 446 / 134.4), 'Q3': (471 / 155.0, 380 / 133.6), '9M': (1562 / 459.5, 1204 / 411.1)}
print('mkt per night YoY', {k: (round(a, 2), round(b, 2), round(100 * (a / b - 1), 1)) for k, (a, b) in q.items()})
print('years at 16.1% to 26.8%, 53.5%', round(math.log(1.2677) / math.log(1.161), 2), round(math.log(1.5354) / math.log(1.161), 2))
a, b = P['TTM Q3 25'], P['TTM Q3 26']; T = terms(b); e = fx(T)
print('TTM Q3 26 terms', {k: round(v, 3) for k, v in T.items()}, 'mkt per night', round(T['M'] / T['N'], 2), '53.5% level', round(T['M'] / T['N'] * 1.5354, 2), '26.8% level', round(T['M'] / T['N'] * 1.2677, 2))
print('mkt per added night TTM', round((b['m'] - a['m']) / (b['n'] - a['n']), 2), 'contribution 9M', round((11155 - 1865 - 984) / 459.5, 2))
A = terms(a); mv = {k: 100 * (T[k] / A[k] - 1) for k in 'NGtVMF'}; print('moves', {k: round(v, 2) for k, v in mv.items()})
names = {'G': 'G GBV per night', 't': 't take rate', 'V': 'V variable cost per night', 'M': 'M marketing', 'F': 'F fixed cost'}
eff = {k: e[names[k]] * mv[k] for k in names}; print({k: round(v) for k, v in eff.items()})
n1 = -sum(eff.values()) / e['N nights']; n0 = -(sum(eff.values()) - eff['G']) / e['N nights']
print('nights growth to hold EBITDA flat: price repeats', round(n1, 1), 'price flat', round(n0, 1))
print('EBITDA margin', {k: round(100 * P[k]['e'] / P[k]['rev'], 1) for k in ('FY25', 'TTM Q3 25', 'TTM Q3 26')})
print('F per night', {k: round(terms(P[k])['F'] / P[k]['n'], 2) for k in ('FY25', 'TTM Q3 25', 'TTM Q3 26')})
rev = 11155 + 3250; gbv = 84149 + 20419 * 1.15; print('FY26 take at guide midpoint, Q4 GBV +15%', round(100 * rev / gbv, 2))
c = duckdb.connect(); G = os.path.expanduser('~/card_panel_extract/**/*.parquet')
d = c.execute(f"select BRAND_NAME b,PERIOD p,sum(INDIVIDUAL_COUNT) n from read_parquet('{G}',hive_partitioning=false) where PERIOD_TYPE='CAL_QTR' and FIRST_SHOP_PERIOD='2025Q3' and BRAND_NAME in ('AIRBNB','EBAY','ETSY','WAYFAIR.COM','INSTACART','EXPEDIA') group by 1,2").df().pivot(index='b', columns='p', values='n')
print((100 * d['2026Q2'] / d['2025Q3']).round(1).to_dict())
