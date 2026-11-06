"""What survives the past-demand test: review scores against bookings, exits, the price premium and the time to rebuild a record."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
t = pd.read_csv(H / 'conv_by_trust.csv'); R['conv_lowest_fifth_pct'] = 100 * t.booked.iloc[0] / t.open.iloc[0]; R['conv_highest_fifth_pct'] = 100 * t.booked.iloc[-1] / t.open.iloc[-1]; R['conv_fifth_homes'] = t.n.sum()
e = pd.read_csv(H / 'exit_by_rating.csv').set_index('rb'); R['exit_below_4_5_pct'] = 100 * e.gone['<4.5']; R['exit_4_8_to_4_9_pct'] = 100 * e.gone['4.8-4.9']; R['exit_rating_homes'] = e.n.sum()
x = pd.read_csv(H / 'exit_by_depth.csv').set_index('dep'); R['exit_100_plus_reviews_pct'] = x['std+age']['100+']; R['exit_5_to_19_reviews_pct'] = x['std+age']['5 to 19']; R['exit_depth_homes'] = x.n.sum()
p = pd.read_csv(H / 'same_host_depth.csv').set_index('b'); R['price_premium_50_plus_pct'] = p.price_vs_low['50+']
b = pd.read_csv(H / 'rebuild_months.csv'); b.columns = ['reviews', 'pct_ever', 'median_months_all', 'quarter_months']; R['months_to_25_reviews'] = b.set_index('reviews').median_months_all[25]
save(__file__, R)
fig = plt.figure(figsize=(9, 4)); titled(fig, 'The highest-scoring fifth books 51.8% of open nights against 34.0% for the lowest', 'Booked share of open nights by record-score fifth, and nine-month exits by rating')
ax = fig.add_axes([0.07, 0.14, 0.42, 0.66]); v = 100 * t.booked / t.open; ax.bar(['Lowest', '2', '3', '4', 'Highest'], v, color=[BLUE] * 4 + [NAVY], width=.62)
for i, q in enumerate(v): ax.text(i, q + 1, f'{q:.1f}', ha='center', fontsize=8.5)
ax.set_ylim(0, 62); ax.set_ylabel('Booked share of open nights, %'); ax.set_xlabel('Record-score fifth')
ax2 = fig.add_axes([0.57, 0.14, 0.41, 0.66]); ee = e.reset_index(); ax2.bar(ee.rb, 100 * ee.gone, color=NAVY, width=.62)
for i, q in enumerate(100 * ee.gone): ax2.text(i, q + .6, f'{q:.1f}', ha='center', fontsize=8.5)
ax2.set_ylim(0, 31); ax2.set_ylabel('Left within nine months, %'); ax2.set_xlabel('Rating band'); ax2.tick_params(axis='x', labelsize=8)
finish(fig, __file__, 'review_content.png')
