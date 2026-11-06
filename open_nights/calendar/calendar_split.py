"""The 12.5% as a sum across host size and open days, from the same Seattle cells as homes/overlap."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
c = pd.read_csv(H.parents[1] / 'homes/overlap/seattle_home_cells.csv'); c['small'] = c.host_size.isin(['1', '2 to 5'])
N = c.homes.sum(); total = 0; rows = []
for small, over, key, lab in ((True, 0, 'small_low', '1 to 5 homes,\nopen up to 240 days'), (True, 1, 'small_high', '1 to 5 homes,\nopen over 240 days'), (False, 0, 'large_low', '6 or more homes,\nopen up to 240 days'), (False, 1, 'large_high', '6 or more homes,\nopen over 240 days')):
    t = c[(c.small == small) & (c.open_over_240 == over)]; n = t.homes.sum(); k = t[t.on_booking == 1].homes.sum(); lo, hi = wilson(k, n)
    R[f'cal_{key}_share'] = 100 * n / N; R[f'cal_{key}_rate'] = 100 * k / n; R[f'cal_{key}_lo'] = 100 * lo; R[f'cal_{key}_hi'] = 100 * hi; R[f'cal_{key}_points'] = 100 * k / N; R[f'cal_{key}_floor'] = 100 * t.floor_homes.sum() / n; total += 100 * k / N; rows.append((lab, 100 * n / N, 100 * k / n, lo * 100, hi * 100))
R['cal_sum_of_points'] = total
save(__file__, R)
fig = plt.figure(figsize=(9, 4.1)); titled(fig, 'Overlap runs from 5.5% to 37.1%, and the largest, most open group supplies 4.8 of the 12.5 points', 'Seattle homes found on Booking.com by host size and open days, 95% intervals')
ax = fig.add_axes([0.08, 0.17, 0.89, 0.63]); v = [r_[2] for r_ in rows]; ax.bar([r_[0] for r_ in rows], v, color=[BLUE, BLUE, NAVY, NAVY], width=.58, yerr=[[r_[2] - r_[3] for r_ in rows], [r_[4] - r_[2] for r_ in rows]], error_kw=dict(lw=.9, capsize=3))
for i, r_ in enumerate(rows): ax.text(i, r_[4] + 1, f'{r_[2]:.1f}%, {r_[1]:.1f}% of homes', ha='center', fontsize=9)
ax.set_ylim(0, 48); ax.set_ylabel('Found on Booking.com, %')
finish(fig, __file__, 'calendar_split.png')
