"""First-time owners as a share of new homes. The builder of this table is lost, so this script reads the table and cannot rebuild it."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
d = pd.read_csv(H / 'new_home_owner.csv').set_index('y0'); R['new_owner_2025_pct'] = d.first_owner[2025]; R['new_owner_2025_homes'] = d.homes[2025]; R['new_owner_2024_pct'] = d.first_owner[2024]
save(__file__, R)
fig = plt.figure(figsize=(9, 3.9)); titled(fig, 'First-time owners supplied 49.1% of new homes in 2025, the lowest share since 2019', 'Share of new homes from an owner with no earlier home in the panel, by first year')
ax = fig.add_axes([0.07, 0.13, 0.9, 0.67]); ax.bar(d.index.astype(str), d.first_owner, color=[BLUE] * 6 + [NAVY], width=.62)
for i, x in enumerate(d.first_owner): ax.text(i, x + 1, f'{x:.1f}%', ha='center', fontsize=8.5)
ax.set_ylim(0, 92); ax.set_ylabel('Share of new homes, %'); callout(ax, 'Table only: the script that built it was not kept', .42, .98)
finish(fig, __file__, 'new_owners.png')
