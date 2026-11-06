"""What each added night kept from FY2022 to FY2025, the fixed-cost hurdle, and the same reading for H1 2026."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
g, terms = filing_lines(); a = terms('FY2025'); b = terms('FY2022'); A = lambda l, p: g('Airbnb', l, p)
dn = a['N'] - b['N']; R['added_nights_m'] = dn; R['revenue_per_added_night'] = (a['rev'] - b['rev']) / dn
after = (a['rev'] - a['v'] - a['M']) - (b['rev'] - b['v'] - b['M']); R['after_marketing_per_added_night'] = after / dn; R['added_revenue_kept_pct'] = 100 * after / (a['rev'] - b['rev']); R['marketing_per_added_night'] = (a['M'] - b['M']) / dn
clean = lambda p: A('oi', p) + A('restr', p) + A('reserves', p) + A('acq', p); R['clean_income_per_added_night'] = (clean('FY2025') - clean('FY2022')) / dn
B = lambda l, y: g('Booking', l, f'FY{y}'); bdn = B('nights', 2025) - B('nights', 2022); bc = lambda y: B('oi', y) + B('imp', y)
R['booking_revenue_per_added_night'] = (B('rev', 2025) - B('rev', 2022)) / bdn; R['booking_clean_per_added_night'] = (bc(2025) - bc(2022)) / bdn
dg = a['gbv'] - b['gbv']; bg = B('gb', 2025) - B('gb', 2022); R['added_marketing_per_100'] = 100 * (a['M'] - b['M']) / dg; R['booking_added_marketing_per_100'] = 100 * (B('mkt', 2025) - B('mkt', 2022)) / bg
R['added_after_marketing_per_100'] = 100 * (a['rev'] - b['rev'] - (a['M'] - b['M'])) / dg; R['booking_added_after_marketing_per_100'] = 100 * (B('rev', 2025) - B('rev', 2022) - (B('mkt', 2025) - B('mkt', 2022))) / bg
h5, h6 = terms_h = [{k: A(k, p) for k in ('nights', 'rev', 'cogs', 'ops', 'sbc_ops', 'bp')} for p in ('H1 2025', 'H1 2026')]
hn = h6['nights'] - h5['nights']; R['h1_marketing_per_added_night'] = (h6['bp'] - h5['bp']) / hn
ha = lambda h: h['rev'] - h['cogs'] - h['ops'] + h['sbc_ops'] - h['bp']; R['h1_added_revenue_kept_pct'] = 100 * (ha(h6) - ha(h5)) / (h6['rev'] - h5['rev'])
R['fixed_growth_pct'] = 100 * ((a['F'] / b['F']) ** (1 / 3) - 1); R['nights_growth_pct'] = 100 * ((a['N'] / b['N']) ** (1 / 3) - 1)
c = (a['rev'] - a['v'] - a['M']) / a['N']; R['breakeven_nights_m'] = a['F'] / c; R['fixed_share_pct'] = 100 * R['breakeven_nights_m'] / a['N']; R['nights_growth_needed_pct'] = R['fixed_growth_pct'] * R['fixed_share_pct'] / 100; R['growth_above_breakeven_pts'] = R['nights_growth_pct'] - R['nights_growth_needed_pct']
save(__file__, R)
fig = plt.figure(figsize=(9, 4.2)); titled(fig, r'Each added night left Airbnb \$5.18 of clean income against \$11.51 at Booking', r'FY2022 to FY2025, dollars per added night')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.68]); lab = ['Revenue', 'Clean operating income']; x = np.arange(2); w_ = .34; v1 = [R['revenue_per_added_night'], R['clean_income_per_added_night']]; v2 = [R['booking_revenue_per_added_night'], R['booking_clean_per_added_night']]
ax.bar(x - w_ / 2, v1, w_, color=NAVY, label='Airbnb'); ax.bar(x + w_ / 2, v2, w_, color=BLUE, label='Booking')
for i in x: ax.text(i - w_ / 2, v1[i] + .5, rf'\${v1[i]:.2f}', ha='center', fontsize=9.5); ax.text(i + w_ / 2, v2[i] + .5, rf'\${v2[i]:.2f}', ha='center', fontsize=9.5)
ax.set_xticks(x, lab); ax.set_ylim(0, 36); ax.set_ylabel('Dollars per added night'); ax.legend(frameon=False, loc='upper right', fontsize=9)
finish(fig, __file__, 'added_nights.png')
