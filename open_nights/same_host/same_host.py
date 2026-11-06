"""Homes of the same host, shared against not shared. Per-host moments are enough for the host fixed-effect slope and host-clustered errors."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
from math import erf, sqrt
d = pd.read_csv(H / 'host_moments.csv'); V = ['y', 'shared', 'log_bedrooms', 'capacity']
def fit(t):
    M = np.zeros((len(t), 4, 4))
    for i, a in enumerate(V):
        for j, b in enumerate(V):
            if j >= i: M[:, i, j] = t[f'{a}*{b}'].values; M[:, j, i] = M[:, i, j]
    T = M.sum(0); b = np.linalg.solve(T[1:, 1:], T[1:, 0]); Ai = np.linalg.inv(T[1:, 1:]); sc = M[:, 1:, 0] - M[:, 1:, 1:] @ b; G = len(t); N = t.homes.sum(); K = G + 3
    cov = Ai @ (sc.T @ sc) @ Ai * (G / (G - 1)) * ((N - 1) / (N - K)); se = sqrt(cov[0, 0]); p = 2 * (1 - .5 * (1 + erf(abs(b[0] / se) / sqrt(2))))
    return b[0], se, p, G, N
out = {}
for m in ('seattle', 'san_diego'):
    for o in ('open_nights', 'airbnb_nights'):
        b, se, p, G, N = fit(d[(d.market == m) & (d.outcome == o)]); out[m, o] = (b, se); R[f'{m}_{o}_coef'] = b; R[f'{m}_{o}_se'] = se; R[f'{m}_{o}_p'] = p; R[f'{m}_{o}_hosts'] = G; R[f'{m}_{o}_homes'] = N
save(__file__, R)
fig = plt.figure(figsize=(9, 4)); titled(fig, 'Shared homes hold 20 to 28 more open nights with no clear change in Airbnb nights', 'Same host, shared against not shared, nights a year, 95% intervals')
ax = fig.add_axes([0.08, 0.13, 0.89, 0.67]); lab = ['Seattle\nopen nights', 'San Diego\nopen nights', 'Seattle\nAirbnb nights', 'San Diego\nAirbnb nights']; k = [('seattle', 'open_nights'), ('san_diego', 'open_nights'), ('seattle', 'airbnb_nights'), ('san_diego', 'airbnb_nights')]
v = [out[x][0] for x in k]; e = [1.96 * out[x][1] for x in k]; ax.bar(lab, v, color=[NAVY, NAVY, BLUE, BLUE], width=.55, yerr=e, error_kw=dict(lw=.9, capsize=3)); ax.axhline(0, color='#888888', lw=.7)
for i, x in enumerate(v): ax.text(i + .3, x, f'{x:+.1f}', va='center', fontsize=9)
ax.set_xlim(-.5, 3.7); ax.set_ylabel('Difference, nights')
finish(fig, __file__, 'same_host.png')
