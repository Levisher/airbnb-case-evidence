"""Net take, marketing per $100 and the search share of visits. Peers come from their own filed lines."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
g, terms = filing_lines(); a = terms('FY2025')
R['airbnb_take'] = 100 * a['t']; R['airbnb_marketing_per_100'] = 100 * a['M'] / a['gbv']; R['airbnb_net_take'] = R['airbnb_take'] - R['airbnb_marketing_per_100']; R['airbnb_total_sm_per_100'] = 100 * g('Airbnb', 'sm', 'FY2025') / a['gbv']
for c, k in (('Booking', 'booking'), ('Expedia', 'expedia')):
    gb, rev, mk = [g(c, x, 'FY2025') for x in ('gb', 'rev', 'mkt')]; R[f'{k}_take'] = 100 * rev / gb; R[f'{k}_marketing_per_100'] = 100 * mk / gb; R[f'{k}_net_take'] = R[f'{k}_take'] - R[f'{k}_marketing_per_100']
l = pd.read_csv(H / 'later_spend_per_100.csv').set_index('brand').iloc[:, 0]
for b_, k in (('Airbnb', 'airbnb'), ('Booking', 'booking'), ('Expedia', 'expedia')): R[f'{k}_first_year_take'] = R[f'{k}_net_take'] * (1 + l[b_] / 100)
s = pd.read_csv(H / 'search_share.csv').set_index('brand').iloc[:, 0]; R['search_share_airbnb'] = s['Airbnb']; R['search_share_booking'] = s['Booking']; R['search_share_expedia'] = s['Expedia']
a_ = pd.read_csv(H / 'ads_hand_coded.csv').set_index('brand'); R['airbnb_ads_trip_or_brand'] = a_.trip_or_brand['Airbnb']; R['airbnb_ads'] = a_.ads['Airbnb']; R['vrbo_ads_listing_feed'] = a_.listing_feed['Vrbo']; R['vrbo_ads'] = a_.ads['Vrbo']
save(__file__, R)
fig = plt.figure(figsize=(9, 4)); titled(fig, 'Airbnb nets 11.66% of bookings after marketing against 10.06% at Booking and 6.17% at Expedia', r'FY2025, dollars per \$100 of bookings')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.68]); b = ['Airbnb', 'Booking', 'Expedia']; k = [x.lower() for x in b]; n = [R[f'{x}_net_take'] for x in k]; m = [R[f'{x}_marketing_per_100'] for x in k]
ax.bar(b, n, color=NAVY, width=.5, label='Net take'); ax.bar(b, m, bottom=n, color=BLUE, width=.5, label='Marketing')
for i, (x, y) in enumerate(zip(n, m)): ax.text(i, x / 2, f'{x:.2f}', ha='center', va='center', color='white', fontsize=10); ax.text(i, x + y / 2, f'{y:.2f}', ha='center', va='center', fontsize=10)
ax.set_ylim(0, 17.5); ax.set_ylabel(r'Dollars per \$100'); ax.legend(frameon=False, ncol=2, loc='upper right', fontsize=9)
finish(fig, __file__, 'net_take.png')
