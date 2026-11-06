"""EBITDA effect of a one per cent move in each term of the note's identity.

    EBITDA = N x [(G x t) - V] - M - F

N nights booked, G GBV per night, t take rate, V cost of revenue plus support before stock pay per night,
M brand and performance marketing, F the balance to reported Adjusted EBITDA. Inputs are the FY24 and FY25 10-Ks,
the 10-Qs filed 6 Aug 2025, 6 Nov 2025, 6 Aug 2026 and 5 Nov 2026. TTM is the fiscal year plus this year's stub less last year's.
Block 1 uses each period's own terms. Block 2 holds N at the 2026 run rate and keeps M and F in dollars, as the identity does.
Run rate is nine months of 2026 plus Q4 2025 grown at the nine-month growth rate.
Variant rows carry what the identity leaves out: payment cost on GBV, and marketing that scales with nights.
The actual_move block multiplies each term's real change by the one per cent effect, so ranks there are moves and not elasticities.
"""
import csv, os, sys
sys.path.insert(0, os.path.expanduser('~/Downloads/ABNB/operating_leverage/_scripts'))
from inputs import A, Y
O = os.path.expanduser('~/Downloads/ABNB/audit/')
PAY = 0.02   # merchant fees and chargebacks per added GBV: 1.92%, 1.72%, 2.03%, 1.98%, 1.84% in FY22 to H1 26
K = ('n', 'gbv', 'rev', 'cogs', 'ops', 'm', 'e')
FY24 = dict(zip(K, (491.5, 81784, 11102, 1878, 1282 - 90, 1455, 4041))); FY25 = dict(zip(K, (533.0, 91273, 12241, 2086, 1327 - 90, 1595, 4297)))
H24 = dict(zip(K, (257.7, 44138, 4890, 986, 623 - 43, 754, 1318))); H25 = dict(zip(K, (277.5, 47962, 5368, 1050, 635 - 44, 824, 1460))); H26 = dict(zip(K, (304.5, 56434, 6286, 1214, 687 - 63, 1091, 1780)))
N24 = dict(zip(K, (380.5, 64223, 8622, 1451, 992 - 65, 1086, 3276))); N25 = dict(zip(K, (411.1, 70855, 9463, 1599, 1000 - 66, 1204, 3511))); N26 = dict(zip(K, (459.5, 84149, 11155, 1865, 1080 - 96, 1562, 4289)))
ttm = lambda fy, new, old: {k: fy[k] + new[k] - old[k] for k in K}
P = {'FY24': FY24, 'FY25': FY25, 'TTM Q2 25': ttm(FY24, H25, H24), 'TTM Q2 26': ttm(FY25, H26, H25), 'TTM Q3 25': ttm(FY24, N25, N24), 'TTM Q3 26': ttm(FY25, N26, N25)}
RUN = N26['n'] + (FY25['n'] - N25['n']) * N26['n'] / N25['n']


def terms(p, n=None):
    N = n or p['n']; G = p['gbv'] / p['n']; t = p['rev'] / p['gbv']; V = (p['cogs'] + p['ops']) / p['n']; M = p['m']
    F = p['rev'] - p['cogs'] - p['ops'] - M - p['e']
    return dict(N=N, G=G, t=t, V=V, M=M, F=F, E=N * (G * t - V) - M - F)


def fx(T):
    r = T['N'] * T['G'] * T['t']; v = T['N'] * T['V']
    return {'N nights': (r - v) / 100, 'G GBV per night': r / 100, 't take rate': r / 100, 'V variable cost per night': -v / 100, 'M marketing': -T['M'] / 100, 'F fixed cost': -T['F'] / 100}


def ranks(e):
    o = sorted(set(round(abs(x), 6) for x in e.values()), reverse=True); seen = {}
    pos = 1
    for x in o:
        seen[x] = pos; pos += sum(round(abs(v), 6) == x for v in e.values())
    return {k: seen[round(abs(v), 6)] for k, v in e.items()}


VAL = {'N nights': 'N', 'G GBV per night': 'G', 't take rate': 't', 'V variable cost per night': 'V', 'M marketing': 'M', 'F fixed cost': 'F'}
rows = []


def put(block, per, T):
    e = fx(T); r = ranks(e)
    for k, v in e.items():
        rows.append(dict(block=block, period=per, term=k, term_value=round(T[VAL[k]], 4), base_ebitda_usd_m=round(T['E'], 1), effect_of_1pct_usd_m=round(v, 1), effect_pct_of_ebitda=round(100 * v / T['E'], 2) if T['E'] > 0 else '', rank_abs=r[k], note=''))
    g = T['N'] * T['G'] * (T['t'] - PAY) / 100; n = (T['N'] * (T['G'] * T['t'] - T['V']) - T['M']) / 100
    w = dict(e); w['G GBV per night'] = g; w['N nights'] = n; rv = ranks(w)
    for k, v, nt in (('G with 2% payment cost', g, 'G rise also raises merchant fees'), ('N with marketing per night', n, 'Marketing scales with nights')):
        key = 'G GBV per night' if k.startswith('G') else 'N nights'
        rows.append(dict(block=block, period=per, term=k, term_value='', base_ebitda_usd_m=round(T['E'], 1), effect_of_1pct_usd_m=round(v, 1), effect_pct_of_ebitda=round(100 * v / T['E'], 2) if T['E'] > 0 else '', rank_abs=rv[key], note=nt + '. Rank is with both variants applied.'))


COL = ('FY25', 'TTM Q2 26', 'TTM Q3 26')
for c in COL: put('1 as reported', c, terms(P[c]))
for c in COL: put('2 nights at 2026 run rate', c, terms(P[c], RUN))
for i, y in enumerate(Y):
    if y < 2019 or y > 2024: continue
    a = {k: A[k][i] for k in ('nights', 'gbv', 'rev', 'cogs', 'ops', 'sbc_ops', 'bp', 'ebitda')}
    put('3 year check', f'FY{y % 100}', terms(dict(n=a['nights'], gbv=a['gbv'], rev=a['rev'], cogs=a['cogs'], ops=a['ops'] - a['sbc_ops'], m=a['bp'], e=a['ebitda'])))
for new, old in (('FY25', 'FY24'), ('TTM Q2 26', 'TTM Q2 25'), ('TTM Q3 26', 'TTM Q3 25')):
    a, b = terms(P[old]), terms(P[new]); e = fx(a); mv = {k: 100 * (b[VAL[k]] / a[VAL[k]] - 1) for k in e}; ef = {k: e[k] * mv[k] for k in e}; r = ranks(ef)
    for k in e:
        rows.append(dict(block='4 actual move', period=f'{new} vs {old}', term=k, term_value=round(mv[k], 2), base_ebitda_usd_m=round(a['E'], 1), effect_of_1pct_usd_m=round(ef[k], 1), effect_pct_of_ebitda=round(100 * ef[k] / a['E'], 2), rank_abs=r[k], note='term_value is the actual % change, effect column is that change x the one per cent effect'))
    rows.append(dict(block='4 actual move', period=f'{new} vs {old}', term='Reported EBITDA change', term_value='', base_ebitda_usd_m=round(a['E'], 1), effect_of_1pct_usd_m=round(b['E'] - a['E'], 1), effect_pct_of_ebitda=round(100 * (b['E'] / a['E'] - 1), 2), rank_abs='', note='Differs from the sum of terms by cross effects'))
with open(O + 'sensitivity_grid.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
t = terms(FY25); assert abs(t['E'] - 4297) < .01 and abs(t['V'] - 6.2348) < .01 and abs(t['F'] - 3026) < .5
print('run rate', round(RUN, 1), {c: {k: round(v, 4) for k, v in terms(P[c]).items()} for c in COL})
import pandas as pd
d = pd.DataFrame(rows); pd.set_option('display.width', 200, 'display.max_rows', 200)
for b in ('1 as reported', '2 nights at 2026 run rate', '3 year check', '4 actual move'):
    x = d[d.block == b]
    print(b); print(x.pivot_table(index='term', columns='period', values='effect_of_1pct_usd_m', sort=False).round(1).to_string()); print(x.pivot_table(index='term', columns='period', values='rank_abs', sort=False, aggfunc='first').to_string())
    if b[0] in '12': print(x.pivot_table(index='term', columns='period', values='effect_pct_of_ebitda', sort=False).round(2).to_string())
    if b[0] == '4': print(x[x.term_value != ''].pivot(index='term', columns='period', values='term_value').to_string())
