"""Review stock on licence-matched homes, from market and site sums."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
d = pd.read_csv(H / 'matched_home_sums.csv'); three = d[d.market != 'lisbon']
for s in ('booking', 'vrbo'):
    t = three[three.site == s]; a = d[d.site == s]
    R[f'{s}_review_share'] = 100 * t.airbnb_reviews.sum() / (t.airbnb_reviews.sum() + t.rival_reviews.sum()); R[f'{s}_review_share_with_lisbon'] = 100 * a.airbnb_reviews.sum() / (a.airbnb_reviews.sum() + a.rival_reviews.sum())
    R[f'{s}_per_100_airbnb'] = 100 * t.rival_reviews.sum() / t.airbnb_reviews.sum(); R[f'{s}_homes_four_markets'] = a.homes.sum()
    R[f'{s}_last_12m_beats_lifetime'] = 100 * a.last_12m_beats_rival_lifetime.sum() / a.homes.sum(); R[f'{s}_last_12m_beats_lifetime_three_markets'] = 100 * t.last_12m_beats_rival_lifetime.sum() / t.homes.sum()
    R[f'{s}_airbnb_ahead'] = 100 * a.airbnb_ahead.sum() / a.homes.sum()
c = pd.read_csv(H / 'same_home_coldstart.csv'); u = c[(c.site == 'booking') & (c.age == 'under 1')].iloc[0]
R['new_homes_booking_under_3_pct'] = u['rv_under3%']; R['new_homes_airbnb_under_3_pct'] = u['ab_under3%']; R['new_homes_booking_sample'] = u.homes
save(__file__, R)
fig = plt.figure(figsize=(9, 4.1)); titled(fig, 'Airbnb holds 90.3% of reviews on matched homes, and 80.9% once Lisbon is added', 'Airbnb share of combined reviews on licence-matched homes, by market')
ax = fig.add_axes([0.14, 0.13, 0.82, 0.68]); t = d.assign(s=100 * d.airbnb_reviews / (d.airbnb_reviews + d.rival_reviews)); p = t.pivot(index='market', columns='site', values='s').loc[['seattle', 'san_diego', 'hawaii', 'lisbon']]; yy = np.arange(4)[::-1]
ax.barh(yy + .19, p.booking, height=.36, color=NAVY, label='Against Booking.com'); ax.barh(yy - .19, p.vrbo, height=.36, color=BLUE, label='Against Vrbo')
for y_, a, b in zip(yy, p.booking, p.vrbo): ax.text(a + .8, y_ + .19, f'{a:.1f}%', va='center', fontsize=8.5); ax.text(b + .8, y_ - .19, f'{b:.1f}%', va='center', fontsize=8.5)
ax.axvline(50, color='#888888', lw=.7, ls=':'); ax.set_yticks(yy, [x.replace('_', ' ').title() for x in p.index]); ax.set_xlim(0, 112); ax.set_xlabel('Airbnb share of combined reviews, %'); ax.legend(frameon=False, loc='lower right', fontsize=8.5)
finish(fig, __file__, 'review_depth.png')
