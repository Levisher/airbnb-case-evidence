"""Airbnb, a manager (Vacasa) and a lessee (Sonder) on a per-100 basis, from three 10-Ks for 2024."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
d = pd.read_csv(H / 'per100_lines.csv'); bad = (100 * d.usd_m / d.denominator_usd_m - d.per_100).abs().max(); R['per_100_largest_rounding_gap'] = bad; assert bad < .006
v = lambda c, b, l: float(d[(d.company == c) & (d.basis == b) & (d.line_item == l)].per_100.iloc[0])
G, V_ = 'per $100 of GBV', 'per $100 of revenue'
R['airbnb_marketing'] = v('Airbnb', G, 'sales_and_marketing'); R['vacasa_marketing'] = v('Vacasa', G, 'sales_and_marketing'); R['sonder_marketing_revenue_basis'] = v('Sonder', V_, 'sales_and_marketing')
R['airbnb_kept'] = v('Airbnb', G, 'left_after_direct_and_support'); R['vacasa_kept'] = v('Vacasa', G, 'left_after_direct_and_support'); R['sonder_kept_revenue_basis'] = v('Sonder', V_, 'left_after_direct_and_support')
R['sonder_loss_revenue_basis'] = v('Sonder', V_, 'operating_income_before_special_lines')
for t in ('10%', '14%', '20%'): R[f'sonder_loss_bookings_tax_{t[:2]}'] = v('Sonder', f'per $100 of estimated bookings, tax {t}', 'operating_income_before_special_lines')
s = pd.read_csv(H / 'gap_split.csv'); g = s[s.section == 'gap_airbnb_less_sonder'].set_index('item')
R['gap_total'] = g.per_100['total gap, GAAP operating income']; R['gap_marketing_share'] = 100 * g.share_of_gap['sales and marketing']; R['gap_overhead_share'] = 100 * g.share_of_gap['remaining overhead gap']; R['gap_rescue_share'] = 100 * (g.share_of_gap['non-recurring professional fees'] + g.share_of_gap['impairment, integration, restructuring']); R['gap_property_line_share'] = 100 * g.share_of_gap['property line: left after direct and support']; R['gap_tax_debt_share'] = 100 * g.share_of_gap['VAT and bad debt increases']
save(__file__, R)
fig = plt.figure(figsize=(9, 4.2)); titled(fig, r"About a third of Sonder's \$32.51 gap to Airbnb is sales and marketing", 'Gap in operating income per $100, Airbnb on GBV against Sonder on revenue, FY2024'.replace('$', r'\$'))
ax = fig.add_axes([0.29, 0.13, 0.68, 0.68]); t = g.drop('total gap, GAAP operating income').per_100.sort_values(); lab = {'property line: left after direct and support': 'Left after direct cost and support', 'sales and marketing': 'Sales and marketing', 'non-recurring professional fees': 'Rescue: professional fees', 'impairment, integration, restructuring': 'Rescue: impairment, restructuring', 'VAT and bad debt increases': 'VAT and bad debt', 'remaining overhead gap': 'Remaining overhead'}
ax.barh([lab[i] for i in t.index], t.values, color=[RED if i == 'sales and marketing' else BLUE for i in t.index], height=.6)
for i, x in enumerate(t.values): ax.text(x + .15, i, rf'\${x:.2f}', va='center', fontsize=9)
ax.set_xlim(0, 13.5); ax.set_xlabel(r'Dollars per \$100')
finish(fig, __file__, 'per_100.png')
