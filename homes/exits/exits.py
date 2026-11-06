"""Listing exits and joins in ten cities, December 2025 to September 2026."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
d = pd.read_csv(H / 'ten_city_exits.csv'); n = d.exits.sum()
R['exit_listings'] = n; R['exit_stock'] = d.stock.sum(); R['exit_pct'] = 100 * n / d.stock.sum(); R['exit_annualised_pct'] = 100 * (1 - (1 - n / d.stock.sum()) ** (12 / 9)); R['join_listings'] = d.entries.sum(); R['join_pct'] = 100 * d.entries.sum() / d.stock.sum()
w_ = d.exits / n; R['host_gone_pct'] = 100 * (d.host_gone * w_).sum(); R['replaced_pct'] = 100 * (d.repl * w_).sum(); R['leavers_active_pct'] = 100 * (d.act_exit * w_).sum()
save(__file__, R)
fig = plt.figure(figsize=(9, 4.2)); titled(fig, 'A quarter of listings left ten cities in nine months, and most hosts left the city with them', 'Exits as a share of December 2025 stock, by city')
ax = fig.add_axes([0.16, 0.12, 0.8, 0.7]); t = d.assign(x=100 * d.exits / d.stock).sort_values('x'); ax.barh(t.city.str.replace('-', ' ').str.title(), t.x, color=NAVY, height=.62)
for i, x in enumerate(t.x): ax.text(x + .4, i, f'{x:.1f}%', va='center', fontsize=8.5)
ax.axvline(R['exit_pct'], color=RED, lw=1, ls='--'); ax.set_xlim(0, 40); ax.set_xlabel('Share of listings gone, %')
callout(ax, f"All ten cities {R['exit_pct']:.1f}%", .80, .12)
finish(fig, __file__, 'exits.png')
