"""Rebuilds the viewable-listing estimate from the census share inside the sitemap and the live share of ids outside it."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
u = pd.read_csv(H / 'universe_size.csv').set_index('stat').v
p, live, frame = u.p_ia_in_sitemap_raw, u.frameb_live, u.frame
padj = p / (p + (1 - p) * live); R['viewable_adjusted_share'] = 100 * padj; R['viewable_unweighted_m'] = frame / padj / 1e6
R['viewable_weighted_m'] = u.viewable_weighted / 1e6; R['viewable_lo_m'] = u.lo / 1e6; R['viewable_hi_m'] = u.hi / 1e6
lo, hi = wilson(440, 499); R['outside_live_pct'] = 100 * 440 / 499; R['outside_live_lo'] = 100 * lo; R['outside_live_hi'] = 100 * hi
f = pd.read_csv(H / 'frame_profile.csv').set_index('m'); R['guest_favorite_inside'] = f.sm['Guest Favorite']; R['guest_favorite_outside'] = f.fb['Guest Favorite']
save(__file__, R)
fig = plt.figure(figsize=(9, 4.2)); titled(fig, 'About 10.47m listings are viewable against 6.93m in the sitemap', 'Pages inside and outside the sitemap, share with each trait, 95% intervals')
ax = fig.add_axes([0.2, 0.12, 0.76, 0.7]); t = f.index[::-1]; yy = np.arange(len(t))
ax.barh(yy + .19, f.sm[t], height=.36, color=NAVY, xerr=[f.sm[t] - f.sm_lo[t], f.sm_hi[t] - f.sm[t]], error_kw=dict(lw=.8), label='Inside the sitemap, 1,489 pages')
ax.barh(yy - .19, f.fb[t], height=.36, color=BLUE, xerr=[f.fb[t] - f.fb_lo[t], f.fb_hi[t] - f.fb[t]], error_kw=dict(lw=.8), label='Outside the sitemap, 440 live pages')
ax.set_yticks(yy, t); ax.set_xlabel('Share of pages, %'); ax.legend(frameon=False, loc='lower right', fontsize=8.5); ax.set_xlim(0, 100)
finish(fig, __file__, 'viewable.png')
