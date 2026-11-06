"""What the Google layer adds. Cell counts stay out under the Google terms, so this script starts from market summaries and cannot rerun the regressions."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
g = pd.read_csv(H / 'gmp_cells.csv').set_index('market')
R['cells_1km'] = g.cells_1km_covered.sum(); R['aggregate_calls'] = g.aggregate_calls_logged.sum(); R['routes_elements_first_layer'] = g.routes_elements_1km_layer.sum(); R['routes_elements_total'] = g.routes_elements_total.sum(); R['routes_elements_pct_of_tier'] = 100 * R['routes_elements_total'] / g.routes_free_tier_monthly.iloc[0]; R['aggregate_pct_of_tier'] = 100 * R['aggregate_calls'] / g.aggregate_free_tier_monthly.iloc[0]
R['aggregate_failed'] = g.aggregate_failed_after_retries.sum()
for m in g.index:
    k = m.lower().replace(' ', '_'); R[f'no_hotel_{k}'] = g.no_google_hotel_700m_pct_of_homes[m]; R[f'no_osm_hotel_{k}'] = g.no_osm_hotel_700m_pct[m]; R[f'r2_gain_{k}'] = g.r2_gain_pts_over_property[m]; R[f'r2_gain_neigh_{k}'] = g.r2_gain_pts_over_neighbourhood[m]; R[f'heldout_gain_{k}'] = g.heldout_gain_pts_added_to_neighbourhood[m]
save(__file__, R)
fig = plt.figure(figsize=(9, 4)); titled(fig, 'Google location adds under 1 point over neighbourhood, except on Maui', 'R-squared gain in points, over property fields and over neighbourhood, and held out')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.68]); x = np.arange(4); w_ = .26
for i, (c_, lab, col) in enumerate((('r2_gain_pts_over_property', 'Over property fields', GREY), ('r2_gain_pts_over_neighbourhood', 'Over neighbourhood', BLUE), ('heldout_gain_pts_added_to_neighbourhood', 'Held out, over neighbourhood', NAVY))):
    ax.bar(x + (i - 1) * w_, g[c_], width=w_, color=col, label=lab)
    for a, b in zip(x + (i - 1) * w_, g[c_]): ax.text(a, max(b, 0) + .15, f'{b:.1f}', ha='center', fontsize=8.5)
ax.axhline(0, color='#888888', lw=.7); ax.set_xticks(x, g.index); ax.set_ylabel('R-squared gain, points'); ax.set_ylim(-1, 11.5); ax.legend(frameon=False, loc='upper right', fontsize=8.5)
finish(fig, __file__, 'location.png')
