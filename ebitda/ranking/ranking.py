"""Ranks every term of the equation by how far a 1% move shifts EBITDA. FY2025 is rebuilt from filed lines, and the year to Q3 2026 is read from the grid."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
g, terms = filing_lines(); a = terms('FY2025'); r = a['rev']; v = a['v']; E = a['E']
R['one_pct_take'] = 100 * r / 100 / E; R['one_pct_gbv_per_night'] = R['one_pct_take']; R['one_pct_nights'] = 100 * (r - v) / 100 / E
R['one_pct_variable'] = 100 * v / 100 / E; R['one_pct_fixed'] = 100 * a['F'] / 100 / E; R['one_pct_marketing'] = 100 * a['M'] / 100 / E
R['one_pct_gbv_after_payment_cost'] = 100 * (r / 100 - .02 * a['gbv'] / 100) / E
t = pd.read_csv(H / 'sensitivity_grid.csv'); q = t[t.period == 'TTM Q3 26'].set_index('term').effect_pct_of_ebitda.abs()
R['ttm_take'] = q['t take rate']; R['ttm_nights'] = q['N nights']; R['ttm_variable'] = q['V variable cost per night']; R['ttm_fixed'] = q['F fixed cost']; R['ttm_marketing'] = q['M marketing']; R['fy25_nights_marketing_per_night'] = t[(t.period == 'FY25') & (t.term == 'N with marketing per night')].effect_pct_of_ebitda.iloc[0]
save(__file__, R)
fig = plt.figure(figsize=(9, 4.3)); titled(fig, 'A 1% move in price or fee shifts EBITDA 2.85%, volume 2.08% and each cost line under 0.8%', 'Size of the change in FY2025 EBITDA from a 1% move in one term')
ax = fig.add_axes([0.3, 0.12, 0.66, 0.7]); lab = ['Marketing', 'Fixed cost', 'Variable cost', 'Conversion', 'Open nights', 'Homes', 'GBV per night (price)', 'Take rate (fee)']
x = [R['one_pct_marketing'], R['one_pct_fixed'], R['one_pct_variable']] + [R['one_pct_nights']] * 3 + [R['one_pct_take']] * 2
ax.barh(lab, x, color=[GREY] * 3 + [BLUE] * 3 + [NAVY] * 2, height=.62)
for i, q_ in enumerate(x): ax.text(q_ + .04, i, f'{q_:.2f}%', va='center', fontsize=9)
ax.set_xlim(0, 3.4); ax.set_xlabel('Effect on EBITDA, %')
finish(fig, __file__, 'ranking.png')
