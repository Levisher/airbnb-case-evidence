"""Return by stay number, and how much of the rise a selection-only model reproduces. The fit runs on stay number x tenure cells."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
from scipy.optimize import minimize
l = pd.read_csv(H / 'stay_ladder_refit.csv'); l5 = l.iloc[:5]
for i, r_ in l5.iterrows(): R[f'ladder_stay_{i + 1}'] = r_.ret
R['ladder_stays'] = l.stays.sum()
c = pd.read_csv(H / 'selection_cells.csv')
def fit(d, free):
    kk, t, n, r = d.k.values, d.t.values, d.n.values, d.r.values
    def nll(p):
        a0, al = np.exp(p[0]), np.exp(p[1]); de = p[2] if free else 0.0
        pr = np.clip(1 - ((al + t) / (al + t + 2)) ** (a0 + (1 + de) * (kk - 1)), 1e-9, 1 - 1e-9); return -(r * np.log(pr) + (n - r) * np.log(1 - pr)).sum()
    best = None
    for st in ([0, 2, 0], [0.3, 1, 0.3], [-0.5, 3, 0.5], [0.2, 4, -0.3]):
        o = minimize(nll, st, method='Nelder-Mead', options=dict(maxiter=4000, xatol=1e-4, fatol=1e-3))
        if best is None or o.fun < best.fun: best = o
    p = best.x; return np.exp(p[0]), np.exp(p[1]), (p[2] if free else 0.0)
def ladder(d, a0, al, de):
    x = d[d.k <= 6].copy(); x['p'] = 1 - ((al + x.t) / (al + x.t + 2)) ** (a0 + (1 + de) * (x.k - 1))
    return x.groupby('k').apply(lambda z: (z.p * z.n).sum() / z.n.sum() * 100, include_groups=False)
d = c[c['sample'] == 'stays, all history, stays 2019-24']; obs = d[d.k <= 6].groupby('k').apply(lambda z: z.r.sum() / z.n.sum() * 100, include_groups=False)
a0, al, de = fit(d, True); b0, bl, _ = fit(d, False); pS = ladder(d, a0, al, 0.0); pC = ladder(d, b0, bl, 0.0); rise = obs[5] - obs[1]
R['selection_only_share_stays'] = 100 * (pC[5] - pC[1]) / rise; R['selection_free_fit_share_stays'] = 100 * (pS[5] - pS[1]) / rise
t = pd.read_csv(H / 'stay_ladder_tests.csv'); g = lambda m, q: float(t[(t.metric == m) & (t.group == q)].value.iloc[0])
R['selection_free_fit_share_trips'] = g('Share of stay 1 to 5 rise left at delta 0 in the free fit', 'trips'); R['selection_only_share_trips'] = g('Share of stay 1 to 5 rise reproduced, selection-only refit', 'trips')
f = pd.read_csv(H / 'same_guest_gaps.csv').set_index('sample'); a = f.loc['all stays']; n = f.loc['stays, first seen 2022+']; R['gap_fall_pooled_pct'] = -a.guestfe_pos3; R['gap_fall_first_seen_2022_pct'] = -n.guestfe_pos3; R['gap_first_days'] = a.med1; R['gap_second_days'] = a.med2; R['gap_third_days'] = a.med3
R['later_freq_fixed_stay_5'] = l.later_freq_fixed_2021_22.iloc[4]; R['raw_2021_22_stay_5'] = l.raw_2021_22.iloc[4]
p = pd.read_csv(H / 'repeat_paths.csv').iloc[0]; R['repeat_other_host_pct'] = 100 * p.other_host / p.repeats; R['repeat_other_city_pct'] = 100 * p.other_city / p.repeats; R['repeat_stays'] = p.stays
save(__file__, R)
fig = plt.figure(figsize=(9, 4.3)); titled(fig, 'Selection alone reproduces about 87% of the rise in return from stay 1 to stay 5', '24-month return by stay number, observed against a model where no stay changes the guest')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.68]); x = np.arange(1, 6); ax.plot(x, obs[:5].values, '-o', color=NAVY, lw=2, label='Observed'); ax.plot(x, pC[:5].values, '--o', color=RED, lw=1.5, label='Selection only')
for i in x: ax.text(i, obs[i] + 2.6, f'{obs[i]:.1f}%', ha='center', fontsize=8.5, color=NAVY); ax.text(i + .05, pC[i] - 4.6, f'{pC[i]:.1f}%', ha='left', fontsize=8.5, color=RED)
ax.set_xticks(x, [f'Stay {i}' for i in x]); ax.set_ylim(0, 72); ax.set_xlim(.7, 5.4); ax.set_ylabel('Returned within 24 months, %'); ax.legend(frameon=False, loc='upper left', fontsize=9)
finish(fig, __file__, 'stay_ladder.png')
