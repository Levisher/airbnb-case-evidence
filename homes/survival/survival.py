"""Survival by vintage. Each cell applies the live share of its sampled ids to the ids absent in November 2026, and ids still in the sitemap count in full."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
s = pd.read_csv(H / 'sampled_ids.csv'); g = pd.read_csv(H / 'ids_by_year_group.csv'); f = pd.read_csv(H / 'ids_by_first_snapshot.csv')
R['survival_sampled_ids'] = len(s); k = int(s.live.sum()); lo, hi = wilson(len(s) - k, len(s)); R['withdrawn_pct'] = 100 * (1 - k / len(s)); R['withdrawn_lo'] = 100 * lo; R['withdrawn_hi'] = 100 * hi
absent = g.absent.sum(); R['no_longer_viewable_pooled_m'] = absent * (1 - k / len(s)) / 1e6
rng = np.random.default_rng(3); tot = []; ks = [int(s[s.id_year_group == x].live.sum()) for x in g.id_year_group]; ns = [int((s.id_year_group == x).sum()) for x in g.id_year_group]
for _ in range(20000):
    gone = 0
    for a, kk, n in zip(g.absent, ks, ns): gone += a * (1 - rng.beta(kk + .5, n - kk + .5))
    tot.append(gone)
R['no_longer_viewable_lo_m'], R['no_longer_viewable_hi_m'] = [float(np.percentile(tot, q)) / 1e6 for q in (2.5, 97.5)]
rows = []
def cell(lab, ever, now, kk, n, key):
    ab = ever - now; l, h = wilson(kk, n); v = 100 * (now + ab * kk / n) / ever; a, b = 100 * (now + ab * l) / ever, 100 * (now + ab * h) / ever
    rows.append((lab, kk, n, v, a, b)); R[f'{key}_share'] = v; R[f'{key}_lo'] = a; R[f'{key}_hi'] = b; R[f'{key}_live'] = kk; R[f'{key}_n'] = n
for r_, kk, n in zip(g.itertuples(), ks, ns): cell('Ids dated ' + r_.id_year_group.replace('Before', 'before'), r_.ever, r_.now, kk, n, 'cell_' + r_.id_year_group.replace(' ', '_').lower())
for r_ in f.itertuples():
    t = s[s.first_snapshot == r_.first_snapshot]
    if len(t): cell(f'First seen {str(r_.first_snapshot)[4:]}/{str(r_.first_snapshot)[2:4]}', r_.ever, r_.in_nov_2026, int(t.live.sum()), len(t), f'first_{r_.first_snapshot}')
for key, age in (('cell_2023', 3.35), ('cell_2024', 2.35)):
    R[f'{key}_yearly_loss'] = 100 * (1 - (R[f'{key}_share'] / 100) ** (1 / age)); R[f'{key}_yearly_loss_lo'] = 100 * (1 - (R[f'{key}_hi'] / 100) ** (1 / age)); R[f'{key}_yearly_loss_hi'] = 100 * (1 - (R[f'{key}_lo'] / 100) ** (1 / age))
pd.DataFrame(rows, columns=['cell', 'live', 'sampled', 'viewable_pct', 'low', 'high']).round(1).to_csv(H / 'survival_cells.csv', index=False)
save(__file__, R)
fig = plt.figure(figsize=(9, 5.2)); titled(fig, 'Survival cells rest on 3 to 204 sampled ids, and four first-seen cells are too thin to quote', 'Share of ids still viewable, 95% interval on the sampled live share, with live of sampled ids beside each cell')
ax = fig.add_axes([0.24, 0.1, 0.72, 0.74]); yy = np.arange(len(rows))[::-1]
col = [RED if r_[2] < 20 else (BLUE if r_[1] <= 7 else NAVY) for r_ in rows]
for y_, r_, c_ in zip(yy, rows, col):
    ax.plot([r_[4], r_[5]], [y_, y_], color=c_, lw=2); ax.plot(r_[3], y_, 'o', color=c_, ms=5); ax.text(94, y_, f'{r_[1]} of {r_[2]}', va='center', ha='right', fontsize=8.5, color=INK)
ax.set_yticks(yy, [r_[0] for r_ in rows]); ax.set_xlim(30, 95); ax.set_xlabel('Still viewable, %')
callout(ax, 'Red cells: under 20 sampled ids, do not quote\nPale cells: 7 or fewer live ids', .30, .985)
finish(fig, __file__, 'survival.png')
