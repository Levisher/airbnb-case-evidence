"""The equation of the case, rebuilt from filed lines: EBITDA = nights x (GBV per night x take rate - variable cost) - marketing - fixed cost."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
g, terms = filing_lines(); a = terms('FY2025'); b = terms('FY2022')
R['nights_m'] = a['N']; R['gbv_per_night'] = a['G']; R['take_rate_pct'] = 100 * a['t']; R['variable_per_night'] = a['V']; R['marketing_m'] = a['M']; R['fixed_m'] = a['F']; R['ebitda_m'] = a['E']
R['identity_gap_m'] = a['N'] * (a['G'] * a['t'] - a['V']) - a['M'] - a['F'] - a['E']
R['rev_per_night'] = a['G'] * a['t']; R['marketing_per_night'] = a['M'] / a['N']; R['fixed_per_night'] = a['F'] / a['N']; R['ebitda_per_night'] = a['E'] / a['N']; R['contribution_per_night'] = R['rev_per_night'] - a['V']; R['contribution_after_marketing'] = R['contribution_per_night'] - R['marketing_per_night']
e0 = b['E'] / b['N']; dN = a['N'] - b['N']
R['bridge_total_m'] = a['E'] - b['E']; R['bridge_nights_m'] = dN * e0; R['bridge_rev_m'] = a['N'] * (a['G'] * a['t'] - b['G'] * b['t']); R['bridge_variable_m'] = -a['N'] * (a['V'] - b['V']); R['bridge_marketing_m'] = -a['N'] * (a['M'] / a['N'] - b['M'] / b['N']); R['bridge_fixed_m'] = -a['N'] * (a['F'] / a['N'] - b['F'] / b['N'])
R['bridge_sum_m'] = R['bridge_nights_m'] + R['bridge_rev_m'] + R['bridge_variable_m'] + R['bridge_marketing_m'] + R['bridge_fixed_m']; R['bridge_nights_share_pct'] = 100 * R['bridge_nights_m'] / R['bridge_total_m']
save(__file__, R)
fig = plt.figure(figsize=(9, 4)); titled(fig, r'Each 2025 night left \$8.06 of EBITDA after \$22.97 of revenue', 'Airbnb, dollars a night, FY2025')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.68]); lab = ['Revenue', 'Variable cost', 'Marketing', 'Fixed cost', 'EBITDA']; v = [R['rev_per_night'], -a['V'], -R['marketing_per_night'], -R['fixed_per_night'], R['ebitda_per_night']]; run = 0
for i, (l_, x) in enumerate(zip(lab, v)):
    bot = 0 if i in (0, 4) else run + x; ax.bar(i, abs(x), bottom=bot, color=NAVY if i in (0, 4) else BLUE, width=.58); ax.text(i, bot + abs(x) + .4, rf'\${abs(x):.2f}', ha='center', fontsize=9.5); run = x if i == 0 else run + x
ax.set_xticks(range(5), lab); ax.set_ylim(0, 27); ax.set_ylabel('Dollars a night')
finish(fig, __file__, 'equation.png')
