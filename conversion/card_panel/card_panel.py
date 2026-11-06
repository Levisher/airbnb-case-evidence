"""Ratios within one card panel, never levels. No customer count or spend level is in this folder."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
r = pd.read_csv(H / 'card_ratios.csv').set_index('brand')
for b in r.index:
    k = b.lower(); R[f'active_3q_{k}'] = r.share_new_group_active_3q_later_pct[b]; R[f'active_months_{k}'] = r.active_months_per_100_m3_12[b]; R[f'later_spend_{k}'] = r.later_spend_pct_first_month[b]; R[f'new_share_{k}'] = r.new_share_of_monthly_actives_pct[b]
g = pd.read_csv(H / 'matched_group_shares.csv').dropna(subset=['airbnb_active_pct', 'vrbo_active_pct']); R['matched_groups'] = len(g); R['matched_groups_airbnb_ahead'] = (g.airbnb_active_pct > g.vrbo_active_pct).sum()
a = g.groupby('age')[['airbnb_active_pct', 'vrbo_active_pct']].mean(); q = a.airbnb_active_pct / a.vrbo_active_pct; R['matched_ratio_low'] = q.min(); R['matched_ratio_high'] = q.max()
s = pd.read_csv(H / 'spend_ratio_vrbo.csv').set_index('window').iloc[:, 0]; R['spend_ratio_first_month'] = s['first month']; R['spend_ratio_later'] = s['months 1 to 6 after']
o = pd.read_csv(H / 'card_older_group.csv'); R['older_group_change_pct'] = o.value.iloc[0]
save(__file__, R)
fig = plt.figure(figsize=(9, 4)); titled(fig, 'Airbnb keeps 13.3% of a new group active after three quarters, ahead of every brand tested', 'Share of a new-customer group active three quarters later, ratio within one card panel')
ax = fig.add_axes([0.13, 0.13, 0.84, 0.68]); t = r.share_new_group_active_3q_later_pct.sort_values(); ax.barh(t.index, t.values, color=[RED if i == 'Booking' else (NAVY if i == 'Airbnb' else BLUE) for i in t.index], height=.62)
for i, x in enumerate(t.values): ax.text(x + .15, i, f'{x:.1f}%', va='center', fontsize=9)
ax.set_xlim(0, 16.5); ax.set_xlabel('Active three quarters later, %'); callout(ax, 'Booking.com is not comparable: pay-at-property\nguests never reach the panel', .985, .42, ha='right')
finish(fig, __file__, 'card_panel.png')
