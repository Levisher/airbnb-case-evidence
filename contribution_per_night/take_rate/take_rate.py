"""What a point of take rate is worth and how many nights it can lose. A break-even, with no measured demand response behind it."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
g, terms = filing_lines(); a = terms('FY2025'); c = (a['rev'] - a['v']) / a['N']; d = a['G'] / 100
R['point_of_take_per_night'] = d; R['contribution_per_night'] = c; R['breakeven_note_pct'] = 100 * d / (c + d)
t = pd.read_csv(H / 'take_rate_grid.csv'); q = t[(t.take_move_pts == 1) & (t.marketing_rise == 0)].set_index('period')
R['breakeven_marketing_per_night_low_pct'] = 100 * q.breakeven_night_loss.min(); R['breakeven_marketing_per_night_high_pct'] = 100 * q.breakeven_night_loss.max(); R['breakeven_marketing_fixed_low_pct'] = 100 * q.breakeven_night_loss_marketing_dollars_fixed.min(); R['breakeven_marketing_fixed_high_pct'] = 100 * q.breakeven_night_loss_marketing_dollars_fixed.max()
R['take_2024_pct'] = 100 * g('Airbnb', 'rev', 'FY2024') / g('Airbnb', 'gbv', 'FY2024'); R['take_2025_pct'] = 100 * a['t']; R['take_ttm_q2_26_pct'] = 100 * q.take_rate['TTM Q2 26'] * (1 if q.take_rate['TTM Q2 26'] < 1 else .01); R['take_ttm_q3_26_pct'] = 100 * q.take_rate['TTM Q3 26'] * (1 if q.take_rate['TTM Q3 26'] < 1 else .01)
save(__file__, R)
fig = plt.figure(figsize=(9, 3.9)); titled(fig, 'A point of take rate pays until nights fall 9.3%, and reported take rate has fallen', 'Implied take rate, revenue over GBV')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.67]); lab = ['FY2024', 'FY2025', 'Year to Q2 2026', 'Year to Q3 2026']; v = [R['take_2024_pct'], R['take_2025_pct'], R['take_ttm_q2_26_pct'], R['take_ttm_q3_26_pct']]
ax.plot(lab, v, '-o', color=NAVY, lw=2)
for i, x in enumerate(v): ax.text(i, x + .035, f'{x:.2f}%', ha='center', fontsize=9.5)
ax.set_ylim(13.0, 13.75); ax.set_ylabel('Take rate, %')
finish(fig, __file__, 'take_rate.png')
