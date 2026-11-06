"""Coverage of the 385-record design: rows reached, keyed rates and how far census and rival weights move each rate."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
d = pd.read_csv(H / 'sampling_audit.csv')
for r_ in d.itertuples():
    k = f'{r_.market}_{r_.rival}'; R[k + '_rate'] = 100 * r_.joined_rows / r_.keyed_rows; R[k + '_reach'] = r_.share_of_reported_total_pct; R[k + '_low'] = r_.joined_pct_low; R[k + '_high'] = r_.joined_pct_high
R['lowest_reach'] = d.share_of_reported_total_pct.min(); R['directional_rows'] = d.overlap_status.str.lower().str.contains('directional').sum()
save(__file__, R)
fig = plt.figure(figsize=(9, 4.6)); titled(fig, 'Lisbon and Hawaii Booking.com rates drop to directional, with reach under 5% of reported rows', 'Keyed rival rows found on Airbnb, range under census and rival weights, with share of the reported total reached')
ax = fig.add_axes([0.2, 0.12, 0.76, 0.7]); t = d.sort_values('share_of_reported_total_pct').reset_index(drop=True); yy = np.arange(len(t))
for y_, r_ in zip(yy, t.itertuples()):
    c_ = RED if 'irectional' in str(r_.overlap_status) else NAVY; ax.plot([r_.joined_pct_low, r_.joined_pct_high], [y_, y_], color=c_, lw=2.5); ax.plot(100 * r_.joined_rows / r_.keyed_rows, y_, 'o', color=c_, ms=5); ax.text(106, y_, f'{r_.share_of_reported_total_pct:.1f}% reached', va='center', ha='right', fontsize=8.5)
ax.set_yticks(yy, (t.market.str.replace('_', ' ').str.title() + ', ' + t.rival.str.title())); ax.set_xlim(55, 107); ax.set_xlabel('Keyed rows found on Airbnb, %')
finish(fig, __file__, 'sampling.png')
