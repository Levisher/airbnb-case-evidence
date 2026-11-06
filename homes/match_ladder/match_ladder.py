"""Hidden-key test. Keys were hidden on known pairs to see what the coordinate and attribute rungs recover, and the true twin removed to see what they pick anyway."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
d = pd.read_csv(H / 'match_ladder.csv'); op = d[d.radius_source.str.startswith('operating')]; n = op[op.rung == 'rung2_nearest']
R['ladder_coord_recovered_low'] = d[d.rung == 'rung2_nearest'].recovered_pct.min(); R['ladder_coord_recovered_high'] = d[d.rung == 'rung2_nearest'].recovered_pct.max()
R['ladder_coord_false_pick_low'] = d[d.rung == 'rung2_nearest'].placebo_false_pct.min(); R['ladder_coord_false_pick_high'] = d[d.rung == 'rung2_nearest'].placebo_false_pct.max()
a = d[d.rung.isin(['rung3_beds_nearest', 'rung3_beds_cap_nearest'])]; R['ladder_attribute_recovered_low'] = a.recovered_pct.min(); R['ladder_attribute_recovered_high'] = a.recovered_pct.max(); R['ladder_attribute_false_pick_low'] = a.placebo_false_pct.min(); R['ladder_attribute_false_pick_high'] = a.placebo_false_pct.max()
u = d[d.rung.isin(['rung3_beds_unique', 'rung3_beds_cap_unique'])]; R['ladder_unique_recovered_low'] = u.recovered_pct.min(); R['ladder_unique_recovered_high'] = u.recovered_pct.max(); R['ladder_unique_false_pick_low'] = u.placebo_false_pct.min(); R['ladder_unique_false_pick_high'] = u.placebo_false_pct.max()
s = d[(d.market == 'seattle') & (d.rival == 'booking') & (d.rung == 'rung2_nearest') & d.radius_source.str.startswith('own')].iloc[0]
R['seattle_coord_recovered'] = 100 * s.recovered / s.known_pairs; R['seattle_coord_known_pairs'] = s.known_pairs; R['seattle_coord_false_pick'] = s.placebo_false_pct; R['seattle_unkeyed_pick_pct'] = 100 * s.unkeyed_picked / s.unkeyed_rows
st = d[(d.market == 'seattle') & (d.rival == 'booking') & (d.rung == 'rung3_beds_unique')].implied_true_share_of_unkeyed_pct; R['seattle_implied_true_low'] = st.min(); R['seattle_implied_true_high'] = st.max()
save(__file__, R)
fig = plt.figure(figsize=(9, 4.4)); titled(fig, 'Coordinates find 33% to 67% of true twins and pick a home nine times in ten when none exists', 'Nearest-home rung at the operating radius, keys hidden, by market and rival')
ax = fig.add_axes([0.2, 0.22, 0.76, 0.59]); lab = (n.market.str.replace('_', ' ').str.title() + ', ' + n.rival.str.title()).values; yy = np.arange(len(n))
ax.barh(yy + .19, n.placebo_false_pct, height=.36, color=RED, label='Home picked with the true twin removed'); ax.barh(yy - .19, n.recovered_pct, height=.36, color=NAVY, label='True twin found')
for i, (a_, b_) in enumerate(zip(n.placebo_false_pct, n.recovered_pct)): ax.text(a_ + .8, i + .19, f'{a_:.1f}%', va='center', fontsize=8.5); ax.text(b_ + .8, i - .19, f'{b_:.1f}%', va='center', fontsize=8.5)
ax.set_yticks(yy, lab); ax.set_xlim(0, 112); ax.set_xlabel('Share of rows, %'); ax.legend(frameon=False, loc='upper center', bbox_to_anchor=(.5, -.15), ncol=2, fontsize=8.5)
finish(fig, __file__, 'match_ladder.png')
