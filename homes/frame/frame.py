"""Recounts the 16,150,130-id frame and each snapshot from the presence patterns, and reads the 12-month sitemap filter."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
p = pd.read_csv(H / 'presence_patterns.csv'); snaps = [c for c in p.columns if c != 'ids']
R['frame_union_ids'] = p.ids.sum(); R['frame_nov_2026_ids'] = p.loc[p['202611'] == 1, 'ids'].sum(); R['frame_absent_ids'] = R['frame_union_ids'] - R['frame_nov_2026_ids']
per = {s: int(p.loc[p[s] == 1, 'ids'].sum()) for s in snaps}; R['frame_snapshots'] = len(snaps); R['frame_in_one_snapshot_only'] = p.loc[p[snaps].sum(1) == 1, 'ids'].sum()
c = pd.read_csv(H / 'cliff.csv').set_index('g').p
R['sitemap_inclusion_month_11'] = 100 * c[11]; R['sitemap_inclusion_month_13'] = 100 * c[13]
s = pd.read_csv(H / 'steady_inclusion.csv'); t = s[s.b >= 202508]; R['steady_inclusion_low'] = 100 * t.inc_b.min(); R['steady_inclusion_high'] = 100 * t.inc_b.max()
save(__file__, R)
fig = plt.figure(figsize=(9, 4.2)); titled(fig, 'Ten snapshots hold 16.15m ids, and 6.93m remain in the November 2026 sitemap', 'Ids in each sitemap or Wayback snapshot, millions')
ax = fig.add_axes([0.07, 0.13, 0.9, 0.68]); lab = [f'{k[4:]}/{k[2:4]}' for k in per]; v = [x / 1e6 for x in per.values()]
ax.bar(lab, v, color=[BLUE] * 9 + [NAVY], width=.65)
for i, x in enumerate(v): ax.text(i, x + .15, f'{x:.2f}', ha='center', fontsize=8.5)
ax.set_ylabel('Ids, millions'); ax.set_ylim(0, max(v) * 1.28); callout(ax, 'Files before August 2025 cover 75% to 99% of the index', .01, .98)
finish(fig, __file__, 'frame.png')
