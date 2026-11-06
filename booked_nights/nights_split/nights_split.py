"""Nights = guests x trips per guest x nights per trip, and the split of 2025 bookings growth between new and existing accounts."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
t = pd.read_csv(H / 'terms.csv').set_index('term').change_2023_to_2025_pct; i = pd.read_csv(H / 'account_identity.csv').set_index('y')
R['guests_change'] = t['guests']; R['trips_change'] = t['trips']; R['nights_per_trip_change'] = t['npb']; R['nights_change'] = 100 * ((1 + t['guests'] / 100) * (1 + t['trips'] / 100) * (1 + t['npb'] / 100) - 1)
R['new_account_points_2025'] = i.intake_pct_prior[2025]; R['growth_points_2025'] = i.growth[2025]; R['existing_points_2025'] = i.base_chg[2025]; R['existing_points_2023'] = i.base_chg[2023]
save(__file__, R)
fig = plt.figure(figsize=(9, 3.9)); titled(fig, 'Existing accounts added 7.0, 2.0 and 0.8 points of bookings growth as new accounts carried the rest', 'Points of bookings growth from accounts opened that year and from existing accounts')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.66]); y = i.index.astype(str); ax.bar(y, i.intake_pct_prior, color=NAVY, width=.5, label='New accounts'); ax.bar(y, i.base_chg, bottom=i.intake_pct_prior, color=BLUE, width=.5, label='Existing accounts')
for k, (a, b) in enumerate(zip(i.intake_pct_prior, i.base_chg)): ax.text(k, a / 2, f'{a:.1f}', ha='center', va='center', color='white', fontsize=9.5); ax.text(k + .28, a + b / 2, f'{b:.1f}', va='center', fontsize=9.5)
ax.set_ylim(0, 22); ax.set_ylabel('Points of growth'); ax.legend(frameon=False, loc='upper right', fontsize=9)
finish(fig, __file__, 'nights_split.png')
