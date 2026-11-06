"""Bookings a rival must replace for a lower fee to pay, against what each channel delivers today. Delivered is income hosts already earn, so it cannot show recapture."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
TAKE, GROSS, FEE = 948.0, 1378.0, .155
for f, k in ((.12, 'vrbo'), (.15, 'booking'), (.029, 'own_site')):
    s = (FEE - f) * GROSS; R[f'fee_saved_{k}'] = s; R[f'needed_{k}'] = 100 * TAKE / (TAKE + s)
R['needed_vrbo_at_8pct'] = 100 * TAKE / (TAKE + (FEE - .08) * GROSS)
c = pd.read_csv(H / 'channel_shares.csv').set_index('channel')
for k, ch in (('vrbo', 'Vrbo'), ('own_site', 'Direct'), ('booking_max', 'All other')):
    R[f'delivered_{k}'] = 100 * c.reservations_q2_2026[ch] / c.reservations_q2_2026['Airbnb']; R[f'delivered_revenue_{k}'] = 100 * c.revenue_q2_2026[ch] / c.revenue_q2_2026['Airbnb']
R['direct_revenue_q2_2025'] = 100 * c.revenue_q2_2025['Direct'] / c.revenue_q2_2025['Airbnb']
d = pd.read_csv(H / 'replacement_test.csv'); m = d[d.delivered_measure == 'Same, one market']
for a, k in (('Vrbo', 'vrbo'), ('Booking', 'booking')):
    t = m[m.alternative == a]; R[f'review_delivered_low_{k}'] = t.delivered_per_100_airbnb.min(); R[f'review_delivered_high_{k}'] = t.delivered_per_100_airbnb.max()
save(__file__, R)
fig = plt.figure(figsize=(9, 4.1)); titled(fig, 'Every channel sits below the share of bookings a host would need to replace', 'US managed homes, Q2 2026 reservations per 100 on Airbnb, against the replacement share needed')
ax = fig.add_axes([0.16, 0.13, 0.81, 0.68]); lab = ['Own site', 'Booking.com, at most', 'Vrbo'][::-1]; need = [R['needed_own_site'], R['needed_booking'], R['needed_vrbo']][::-1]; got = [R['delivered_own_site'], R['delivered_booking_max'], R['delivered_vrbo']][::-1]; yy = np.arange(3)
ax.barh(yy + .19, need, height=.36, color=GREY, label='Needed'); ax.barh(yy - .19, got, height=.36, color=NAVY, label='Delivered')
for y_, a, b in zip(yy, need, got): ax.text(a + 1, y_ + .19, f'{a:.1f}', va='center', fontsize=9); ax.text(b + 1, y_ - .19, f'{b:.1f}', va='center', fontsize=9)
ax.set_yticks(yy, lab); ax.set_xlim(0, 122); ax.set_xlabel('Per 100 Airbnb reservations'); ax.legend(frameon=False, loc='lower right', fontsize=9)
finish(fig, __file__, 'replacement.png')
