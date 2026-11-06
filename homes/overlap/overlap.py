"""Seattle floor, match and ceiling from aggregate cells and the row ledger, plus the both-rivals reading."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
c = pd.read_csv(H / 'seattle_home_cells.csv'); rows = pd.read_csv(H / 'seattle_booking_rows.csv').set_index('item').rows; b = pd.read_csv(H / 'both_rivals_cells.csv')
N = c.homes.sum(); match = c[c.on_booking == 1].homes.sum(); floor = c.floor_homes.sum()
unk, miss, gap = rows['Rows with no licence number'], rows['Keyed rows absent from the Airbnb file'], rows['Reported rows outside the used set']
ceil = match + unk + gap; widest = ceil + miss; R['seattle_homes'] = N; R['seattle_floor_homes'] = floor; R['seattle_match_homes'] = match; R['seattle_ceiling_homes'] = ceil
R['seattle_floor_pct'] = 100 * floor / N; R['seattle_match_pct'] = 100 * match / N; R['seattle_ceiling_pct'] = 100 * ceil / N; R['seattle_absent_pct'] = 100 - R['seattle_match_pct']; R['seattle_absent_low_pct'] = 100 - R['seattle_ceiling_pct']; R['seattle_widest_homes'] = widest; R['seattle_widest_pct'] = 100 * widest / N; R['seattle_absent_widest_pct'] = 100 - R['seattle_widest_pct']; R['seattle_absent_high_pct'] = 100 - R['seattle_floor_pct']

R['seattle_booking_rows_used'] = rows['Rows used after hotel and market filters']; R['seattle_booking_keyed_rate'] = 100 * rows['Keyed rows found in the Airbnb file'] / rows['Rows with a licence number']; R['seattle_booking_all_rows_floor'] = 100 * rows['Keyed rows found in the Airbnb file'] / rows['Rows used after hotel and market filters']
h = c.groupby('host_size', sort=False).apply(lambda t: pd.Series(dict(homes=t.homes.sum(), on=t[t.on_booking == 1].homes.sum(), fl=t.floor_homes.sum(), n=t.estimated_nights.sum())), include_groups=False)
for k, r_ in h.iterrows():
    key = 'host_' + str(k).replace(' ', '_'); lo, hi = wilson(r_.on, r_.homes); R[key + '_pct'] = 100 * r_.on / r_.homes; R[key + '_lo'] = 100 * lo; R[key + '_hi'] = 100 * hi; R[key + '_floor'] = 100 * r_.fl / r_.homes; R[key + '_nights_share'] = 100 * r_.n / h.n.sum()
s = b[b.market == 'seattle']; neither = s[s.on_either_rival == 0]; vo = s[(s.on_booking == 0) & (s.on_either_rival == 1)]; reach = 0.358
R['seattle_neither_pct'] = 100 * neither.homes.sum() / s.homes.sum(); R['seattle_neither_nights_pct'] = 100 * neither.estimated_nights.sum() / s.estimated_nights.sum()
R['seattle_neither_scaled_pct'] = 100 * (neither.homes.sum() - vo.homes.sum() * (1 / reach - 1)) / s.homes.sum(); R['seattle_neither_nights_scaled_pct'] = 100 * (neither.estimated_nights.sum() - vo.estimated_nights.sum() * (1 / reach - 1)) / s.estimated_nights.sum()
d = b[b.market == 'san_diego']; nd = d[d.on_either_rival == 0]; vd = d[(d.on_booking == 0) & (d.on_either_rival == 1)]
R['san_diego_neither_pct'] = 100 * nd.homes.sum() / d.homes.sum(); R['san_diego_neither_scaled_pct'] = 100 * (nd.homes.sum() - vd.homes.sum() * (1 / .104 - 1)) / d.homes.sum()
save(__file__, R)
fig = plt.figure(figsize=(9, 3.9)); titled(fig, 'Seattle overlap with Booking.com reads as a band from 10.5% to 17.9% of licensed homes', 'Licensed Airbnb whole homes with a licence number also on Booking.com, of 4,538')
ax = fig.add_axes([0.28, 0.15, 0.68, 0.6]); lab = ['Floor, one home per row', 'Home-level match', 'Ceiling, unkeyed and unread rows', 'Plus 15 rows with a key Airbnb lacks'][::-1]; v = [R['seattle_widest_pct'], R['seattle_ceiling_pct'], R['seattle_match_pct'], R['seattle_floor_pct']]; n = [widest, ceil, match, floor]
ax.barh(lab, v, color=['#EEEEEE', GREY, NAVY, BLUE], height=.58)
for i, (x, q) in enumerate(zip(v, n)): ax.text(x + .25, i, f'{x:.1f}%, {q:,.0f} homes', va='center', fontsize=9)
ax.set_xlim(0, 26); ax.set_xlabel('Share of homes, %')
finish(fig, __file__, 'overlap.png')
