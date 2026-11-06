"""Reruns the conversion regression from neighbourhood moment tables.

y = log(1 + English reviews in 2026), within city x neighbourhood x bedroom cells, errors clustered on 271 neighbourhoods.
With demeaned data, X'X and X'y by neighbourhood are enough for coefficients, clustered errors, R2 and Shapley shares, so no home row is needed.
"""
import itertools, math, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__)


class Moments:
    def __init__(self, name):
        d = pd.read_csv(H / name); self.n = d.homes.values; self.G = len(d); self.N = int(d.homes.sum())
        pairs = [c.split('*') for c in d.columns[2:]]
        self.v = list(dict.fromkeys(p[0] for p in pairs)) + [pairs[-1][1]]; self.v = list(dict.fromkeys(self.v)); ix = {x: i for i, x in enumerate(self.v)}
        self.M = np.zeros((self.G, len(self.v), len(self.v)))
        for c, (a, b) in zip(d.columns[2:], pairs):
            self.M[:, ix[a], ix[b]] = d[c].values; self.M[:, ix[b], ix[a]] = d[c].values
        self.ix = ix

    def fit(self, y, xs):
        """OLS on demeaned data with the statsmodels cluster correction."""
        i = [self.ix[x] for x in xs]; j = self.ix[y]; T = self.M.sum(0); A = T[np.ix_(i, i)]; b = np.linalg.solve(A, T[i, j]); Ai = np.linalg.inv(A)
        sc = self.M[:, i, j] - self.M[:, i, :][:, :, i] @ b; S = sc.T @ sc; K = len(xs)
        V = Ai @ S @ Ai * (self.G / (self.G - 1)) * ((self.N - 1) / (self.N - K)); se = np.sqrt(np.diag(V))
        r2 = (T[i, j] @ b) / T[j, j]
        return dict(zip(xs, b)), dict(zip(xs, se)), r2


def shapley(M, ix, y):
    def r2(s):
        if not s: return 0.
        A = M[np.ix_(s, s)]; b = M[s, y]; return float(b @ np.linalg.solve(A, b) / M[y, y])
    n = len(ix); out = []
    for v in ix:
        o = [u for u in ix if u != v]; t = 0.
        for q in range(n):
            for c in itertools.combinations(o, q):
                t += math.factorial(q) * math.factorial(n - q - 1) / math.factorial(n) * (r2(list(c) + [v]) - r2(list(c)))
        out.append(t)
    return np.array(out)


def shapley_boot(m, xs, B=300, seed=7):
    cols = ['y'] + xs; i = [m.ix[c] for c in cols]; Ms = m.M[:, i, :][:, :, i]
    pt = shapley(Ms.sum(0), list(range(1, len(cols))), 0); rng = np.random.default_rng(seed); bs = []
    for _ in range(B):
        w = np.bincount(rng.integers(0, m.G, m.G), minlength=m.G)
        bs.append(shapley(np.tensordot(w, Ms, 1), list(range(1, len(cols))), 0))
    bs = np.array(bs); s = 100 * bs / bs.sum(1, keepdims=True)
    return 100 * pt / pt.sum(), np.percentile(s, 2.5, axis=0), np.percentile(s, 97.5, axis=0)


m = Moments('moments_all_homes.csv'); R = {}
X0 = ['ln0', 'bad_l', 'bad_h', 'lp', 'lo']; X1 = X0[1:]; X2 = X0 + ['lf']
b0, s0, r0 = m.fit('y', X0); b1, s1, r1 = m.fit('y', X1); b2, s2, r2 = m.fit('y', X2); _, _, r2d = m.fit('y', X2[1:])
R['conv_coef_original'] = b0['ln0']; R['conv_coef_original_lo'] = b0['ln0'] - 1.96 * s0['ln0']; R['conv_coef_original_hi'] = b0['ln0'] + 1.96 * s0['ln0']
R['conv_coef_absorbed'] = b2['ln0']; R['conv_coef_absorbed_lo'] = b2['ln0'] - 1.96 * s2['ln0']; R['conv_coef_absorbed_hi'] = b2['ln0'] + 1.96 * s2['ln0']
R['conv_r2_original'] = r0; R['conv_r2_added_original'] = r0 - r1; R['conv_r2_added_absorbed'] = r2 - r2d
R['conv_homes'] = m.N
R['bad_stays_coef'] = b2['bad_l']; R['bad_stays_lo'] = b2['bad_l'] - 1.96 * s2['bad_l']; R['bad_stays_hi'] = b2['bad_l'] + 1.96 * s2['bad_l']

# split-sample instrument: the control is odd-month 2025 reviews, the instrument even-month 2025 reviews
W = X0 + ['lfo']; Z = X0 + ['lfe']; iw = [m.ix[x] for x in W]; iz = [m.ix[x] for x in Z]; jy = m.ix['y']; T = m.M.sum(0)
Pi = np.linalg.solve(T[np.ix_(iz, iz)], T[np.ix_(iz, iw)]); Q = Pi.T @ T[np.ix_(iz, iw)]; biv = np.linalg.solve(Q, Pi.T @ T[iz, jy])
sc = (m.M[:, iz, jy] - m.M[:, iz, :][:, :, iw] @ biv) @ Pi; A = np.linalg.inv(Pi.T @ T[np.ix_(iz, iz)] @ Pi); se_iv = np.sqrt(np.diag(A @ (sc.T @ sc) @ A))
R['conv_coef_split_iv'] = biv[0]; R['conv_coef_split_iv_lo'] = biv[0] - 1.96 * se_iv[0]; R['conv_coef_split_iv_hi'] = biv[0] + 1.96 * se_iv[0]

# outcome that owes nothing to reviews: forward blocked nights
c = Moments('moments_calendar.csv'); bc0, sc0, _ = c.fit('unav', X0); bc2, sc2, rc2 = c.fit('unav', X2)
R['calendar_coef_original'] = bc0['ln0']; R['calendar_coef_absorbed'] = bc2['ln0']; R['calendar_absorbed_lo'] = bc2['ln0'] - 1.96 * sc2['ln0']; R['calendar_absorbed_hi'] = bc2['ln0'] + 1.96 * sc2['ln0']
R['calendar_share_surviving'] = 100 * bc2['ln0'] / bc0['ln0']; R['calendar_r2'] = rc2

band = {}
for nm, lab, fn in (('3_to_5', '3 to 5', 'moments_band_3_to_5.csv'), ('6_to_25', '6 to 25', 'moments_band_6_to_25.csv'), ('26_to_100', '26 to 100', 'moments_band_26_to_100.csv'), ('over_100', 'over 100', 'moments_band_over_100.csv')):
    q = Moments(fn); bq0, _, _ = q.fit('y', X0); bq, sq, _ = q.fit('y', X2); band[lab] = (bq0['ln0'], bq['ln0'], sq['ln0']); R[f'conv_band_{nm}'] = bq['ln0']

# conversion gaps implied by the review ratio
for rival, a, b in (('booking', 90.3, 9.7), ('vrbo', 61.7, 38.3)):
    ratio = a / b
    R[f'gap_{rival}_original'] = ratio ** 0.34
    R[f'gap_{rival}_absorbed'] = ratio ** b2['ln0']; R[f'gap_{rival}_absorbed_lo'] = ratio ** R['conv_coef_absorbed_lo']; R[f'gap_{rival}_absorbed_hi'] = ratio ** R['conv_coef_absorbed_hi']

sh, lo, hi = shapley_boot(m, X0)
R['shapley_prior_reviews_original'] = sh[0]; R['shapley_prior_lo'] = lo[0]; R['shapley_prior_hi'] = hi[0]
sh2, lo2, hi2 = shapley_boot(m, X2)
R['shapley_prior_reviews_absorbed'] = sh2[0]; R['shapley_past_demand_absorbed'] = sh2[-1]
save(__file__, R)

fig = plt.figure(figsize=(9, 4.6)); titled(fig, 'The review coefficient falls from 0.346 to 0.029 once past demand is absorbed', '89,546 homes, within city, neighbourhood and bedroom cells, errors clustered on 271 neighbourhoods, 95% intervals')
ax = fig.add_axes([0.08, 0.14, 0.40, 0.68])
labels = ['Original', 'Past demand\nabsorbed', 'Split-sample\ninstrument']; v = [R['conv_coef_original'], R['conv_coef_absorbed'], R['conv_coef_split_iv']]
l = [R['conv_coef_original_lo'], R['conv_coef_absorbed_lo'], R['conv_coef_split_iv_lo']]; h = [R['conv_coef_original_hi'], R['conv_coef_absorbed_hi'], R['conv_coef_split_iv_hi']]
ax.bar(labels, v, color=[GREY, NAVY, BLUE], width=.6); ax.errorbar(labels, v, yerr=[np.array(v) - l, np.array(h) - v], fmt='none', ecolor=INK, capsize=3, lw=.9); ax.axhline(0, color='#888888', lw=.7)
for i, x in enumerate(v):
    ax.text(i + .33, x, f'{x:.3f}', va='center', fontsize=9, color=INK)
ax.set_xlim(-.5, 2.9); ax.set_ylim(-.22, .42); ax.set_ylabel('Coefficient on log prior reviews')
ax2 = fig.add_axes([0.58, 0.14, 0.39, 0.68]); ks = list(band); y = [band[k][1] for k in ks]; e = [1.96 * band[k][2] for k in ks]
ax2.bar(ks, y, color=NAVY, width=.6); ax2.errorbar(ks, y, yerr=e, fmt='none', ecolor=INK, capsize=3, lw=.9); ax2.axhline(0, color='#888888', lw=.7); ax2.set_xlabel('Prior reviews on the home'); ax2.set_ylabel('Coefficient, past demand absorbed')
callout(ax2, 'Any effect appears only on deep homes', .03, .97)
finish(fig, __file__, 'review_effect.png')
