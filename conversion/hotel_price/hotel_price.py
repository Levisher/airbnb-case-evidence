"""Lisbon homes against hotel rooms on the same dates, as ratios by bedroom count."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
b = pd.read_csv(H / 'lisbon_ratio_by_bedrooms.csv').set_index('bed'); a = pd.read_csv(H / 'lisbon_ratio_all.csv').iloc[0]
R['two_bed_vs_two_rooms'] = b.median_ratio_two_rooms[2]; R['three_bed_vs_two_rooms'] = b.median_ratio_two_rooms[3]; R['three_bed_vs_three_rooms'] = b.median_ratio_two_rooms[3] * 2 / 3
R['all_homes_vs_two_rooms'] = a.median_ratio_two_rooms; R['all_homes_cheaper_pct'] = 100 * a.share_cheaper; R['two_bed_homes'] = b.homes[2]; R['three_bed_homes'] = b.homes[3]; R['lisbon_homes'] = a.homes
c = pd.read_csv(H / 'lisbon_cheapest_quarter.csv').iloc[0]; R['vs_cheapest_quarter'] = c.median_ratio; R['cheaper_than_cheapest_quarter_pct'] = c.share_of_homes_cheaper_pct
save(__file__, R)
fig = plt.figure(figsize=(9, 3.8)); titled(fig, 'Lisbon two-bedroom homes for four cost 0.85x two hotel rooms on the same dates', 'Median home price over the price of two hotel rooms within 1 km, 12 to 15 March 2027')
ax = fig.add_axes([0.08, 0.14, 0.89, 0.64]); t = b.loc[[2, 3]]; lab = [f'{int(i)} bedrooms, {int(n)} homes' for i, n in zip(t.index, t.homes)]; ax.bar(lab, t.median_ratio_two_rooms, color=NAVY, width=.45)
for i, q in enumerate(t.median_ratio_two_rooms): ax.text(i, q - .07, f'{q:.2f}x', ha='center', fontsize=10, color='white')
ax.axhline(1, color=RED, lw=1, ls='--'); ax.set_ylim(0, 1.25); ax.set_ylabel('Home over two rooms')
finish(fig, __file__, 'hotel_price.png')
