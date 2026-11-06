"""Refit the conversion regression on the 89,546-home sample: within city x neighbourhood x bedroom cells, errors clustered on 271 neighbourhoods.

y = log(1 + English reviews in 2026). Models:
  original        y on prior reviews, bad stays, host bad stays, price, open nights
  no_prior        the same without prior reviews
  demand_absorbed original plus log(1 + 2025 reviews), the year before the window
Robustness: split_iv instruments odd-month 2025 reviews with even-month reviews to remove count noise;
age_rate splits prior reviews exactly into age and reviews per month; calendar swaps the outcome for forward unavailable nights,
which owes nothing to reviews. Shapley shares use exact subset R2, intervals come from resampling neighbourhoods.
"""
import duckdb, glob, itertools, math, os, re
import numpy as np, pandas as pd, statsmodels.api as sm
os.chdir(os.path.expanduser('~/Downloads/ABNB'))
num = lambda s: pd.to_numeric(s, errors='coerce')
z = pd.read_parquet('price_map/out/conv_base.parquet')
k = duckdb.connect('altdata/abnb.duckdb', read_only=True); k.execute("set memory_limit='10GB'")
yr = k.execute("""select listing_id id, sum((y=2025)::int) n25, sum((y=2025 and mo%2=1)::int) n25o, sum((y=2025 and mo%2=0)::int) n25e,
  sum((y=2026 and mo%2=1)::int) n26o, sum((y=2026 and mo%2=0)::int) n26e, sum((y<=2024)::int) nold, min(case when y<=2025 then y*12+mo end) first_m
  from s where eng group by 1""").df()
for c_ in yr.columns: yr[c_] = pd.to_numeric(yr[c_], errors='coerce').astype('float64')
z['id'] = z.id.astype('float64'); z = z.merge(yr, on='id', how='left')
assert len(z) == 89546 and z.n25.notna().all()
post = []
for f in glob.glob('altdata/raw/listings_*.parquet'):
    if re.search(r'_2026-(03|06|09)-', f):
        a = pd.read_parquet(f, columns=['id', 'availability_90']); a['id'] = num(a.id.astype(str)); a['a90'] = num(a.availability_90); post.append(a[['id', 'a90']])
cal = pd.concat(post).groupby('id').a90.mean().rename('a90').reset_index()
cal['id'] = cal.id.astype('float64')
z = z.merge(cal, on='id', how='left')
z['unav'] = 100 * (1 - z.a90 / 90)
z['lf'] = np.log1p(z.n25); z['lfo'] = np.log1p(z.n25o); z['lfe'] = np.log1p(z.n25e)
z['age'] = (2026 * 12 + 1 - z.first_m).clip(lower=1); z['lage'] = np.log(z.age); z['lrate'] = z.ln0 - z.lage
G = ['city', 'neighbourhood_cleansed', 'br']; z['cl'] = pd.factorize(z.city + '|' + z.neighbourhood_cleansed)[0]
print('homes', len(z), 'neighbourhoods', z.cl.nunique(), 'cells', z.groupby(G).ngroups)
def dm(df, cols):
    return df[cols] - df.groupby(G)[cols].transform('mean')
BASE = {'ln0': 'Prior reviews', 'bad_l': 'Bad stays', 'bad_h': 'Host bad stays', 'lp': 'Price', 'lo': 'Open nights'}
EXTRA = {'lf': 'Past demand, 2025 reviews', 'lage': 'Listing age', 'lrate': 'Reviews per month to 2025', 'lfo': 'Past demand, odd-month 2025 reviews'}
NAME = {**BASE, **EXTRA}
D = dm(z, ['y', 'ln0', 'bad_l', 'bad_h', 'lp', 'lo', 'lf', 'lfo', 'lfe', 'lage', 'lrate'])
def fit(d, y, xs):
    return sm.OLS(d[y], d[xs]).fit(cov_type='cluster', cov_kwds={'groups': d['cl']})
D['cl'] = z.cl.values
def shap(M, ix, y_ix):
    """Exact Shapley on R2 from a moment matrix."""
    def r2(s):
        if not s: return 0.
        A = M[np.ix_(s, s)]; b = M[s, y_ix]; return float(b @ np.linalg.solve(A, b) / M[y_ix, y_ix])
    n = len(ix); out = []
    for v in ix:
        o = [u for u in ix if u != v]; t = 0.
        for q in range(n):
            for c in itertools.combinations(o, q):
                t += math.factorial(q) * math.factorial(n - q - 1) / math.factorial(n) * (r2(list(c) + [v]) - r2(list(c)))
        out.append(t)
    return np.array(out)
def boot(xs, y='y', B=300, seed=7):
    cols = [y] + xs; A = D[cols].values; cl = D.cl.values; nC = cl.max() + 1
    Ms = np.zeros((nC, len(cols), len(cols)))
    np.add.at(Ms, cl, A[:, :, None] * A[:, None, :])
    pt = shap(Ms.sum(0), list(range(1, len(cols))), 0); rng = np.random.default_rng(seed); bs = []
    for _ in range(B):
        w = np.bincount(rng.integers(0, nC, nC), minlength=nC)
        bs.append(shap(np.tensordot(w, Ms, 1), list(range(1, len(cols))), 0))
    return pt, np.array(bs)
rows = []
def add(model, r, xs, note=''):
    pt, bs = boot(xs); tot = pt.sum(); sh = 100 * pt / tot; s = 100 * bs / bs.sum(1, keepdims=True)
    for i, x in enumerate(xs):
        rows.append(dict(model=model, variable=NAME[x], coef=r.params[x], cluster_se=r.bse[x], t=r.tvalues[x], ci_low=r.params[x] - 1.96 * r.bse[x], ci_high=r.params[x] + 1.96 * r.bse[x],
                         shapley_r2=pt[i], shapley_share_pct=sh[i], share_ci_low=np.percentile(s[:, i], 2.5), share_ci_high=np.percentile(s[:, i], 97.5), model_r2=tot, n=int(r.nobs), note=note))
X0 = list(BASE)
r0 = fit(D, 'y', X0); add('original', r0, X0, 'Reproduces the note')
X1 = [x for x in X0 if x != 'ln0']; r1 = fit(D, 'y', X1); add('no_prior', r1, X1, 'Prior reviews dropped')
X2 = X0 + ['lf']; r2_ = fit(D, 'y', X2); add('demand_absorbed', r2_, X2, 'Past demand absorbed by 2025 reviews')
X3 = ['lage', 'lrate', 'bad_l', 'bad_h', 'lp', 'lo']; r3 = fit(D, 'y', X3); add('age_rate', r3, X3, 'Prior reviews = age x reviews per month')
# split-sample IV: control is odd-month 2025 reviews, instrument is even-month 2025 reviews
ex = X0; W = D[ex + ['lfo']].values; Zm = D[ex + ['lfe']].values; yv = D.y.values
Pz = Zm @ np.linalg.solve(Zm.T @ Zm, Zm.T @ W); b = np.linalg.solve(Pz.T @ W, Pz.T @ yv); e = yv - W @ b
A = np.linalg.inv(Pz.T @ Pz); S = np.zeros((W.shape[1],) * 2)
sc = pd.DataFrame(Pz * e[:, None]).groupby(D.cl.values).sum().values; S = sc.T @ sc
se = np.sqrt(np.diag(A @ S @ A)); fs = sm.OLS(D.lfo, D[ex + ['lfe']]).fit()
for i, x in enumerate(ex + ['lfo']):
    rows.append(dict(model='split_iv', variable=NAME[x], coef=b[i], cluster_se=se[i], t=b[i] / se[i], ci_low=b[i] - 1.96 * se[i], ci_high=b[i] + 1.96 * se[i], model_r2=1 - (e @ e) / (yv @ yv), n=len(yv),
                     note=f'Even-month 2025 reviews instrument odd-month. First-stage t {fs.tvalues["lfe"]:.0f}'))
# outcome that owes nothing to reviews
c = z[z.unav.notna()].copy(); Dc = dm(c, ['unav', 'ln0', 'bad_l', 'bad_h', 'lp', 'lo', 'lf']); Dc['cl'] = c.cl.values
for m, xs in (('calendar_original', X0), ('calendar_demand_absorbed', X2)):
    r = fit(Dc, 'unav', xs)
    for x in xs:
        rows.append(dict(model=m, variable=NAME[x], coef=r.params[x], cluster_se=r.bse[x], t=r.tvalues[x], ci_low=r.params[x] - 1.96 * r.bse[x], ci_high=r.params[x] + 1.96 * r.bse[x], model_r2=r.rsquared, n=int(r.nobs),
                         note='Outcome is forward unavailable share of next 90 nights, percentage points, mean of Mar, Jun, Sep 2026 snapshots. Includes host blocks'))
for m, xs in (('calendar_no_open_nights', [x for x in X0 if x != 'lo']), ('calendar_absorbed_no_open_nights', [x for x in X2 if x != 'lo'])):
    r = fit(Dc, 'unav', xs)
    for x in xs:
        rows.append(dict(model=m, variable=NAME[x], coef=r.params[x], cluster_se=r.bse[x], t=r.tvalues[x], ci_low=r.params[x] - 1.96 * r.bse[x], ci_high=r.params[x] + 1.96 * r.bse[x], model_r2=r.rsquared, n=int(r.nobs),
                         note='Open nights removed, because availability_365 and availability_90 share a calendar'))
print('mean unav', z.unav.mean().round(2), 'iqr within', (Dc.ln0.quantile(.75) - Dc.ln0.quantile(.25)).round(3))
# does the stock matter where reviews are thin
for lo_, hi in ((3, 5), (6, 25), (26, 100), (101, 10**6)):
    m_ = (z.n0 >= lo_) & (z.n0 <= hi); dd = dm(z[m_], ['y', 'ln0', 'bad_l', 'bad_h', 'lp', 'lo', 'lf']); dd['cl'] = z.cl[m_].values
    for nm, xs in (('band_original', X0), ('band_demand_absorbed', X2)):
        r = fit(dd, 'y', xs)
        rows.append(dict(model=nm, variable=f'Prior reviews, {lo_} to {hi}', coef=r.params['ln0'], cluster_se=r.bse['ln0'], t=r.tvalues['ln0'], ci_low=r.params['ln0'] - 1.96 * r.bse['ln0'], ci_high=r.params['ln0'] + 1.96 * r.bse['ln0'], model_r2=r.rsquared, n=int(r.nobs), note='Homes in this prior-review band only'))
# what prior reviews add last
for nm, full, drop in (('increment_original', X0, X1), ('increment_absorbed', X2, [x for x in X2 if x != 'ln0'])):
    a_ = sm.OLS(D.y, D[full]).fit().rsquared; b_ = sm.OLS(D.y, D[drop]).fit().rsquared
    rows.append(dict(model=nm, variable='R2 added by prior reviews entered last', coef=a_ - b_, model_r2=a_, n=len(z), note=f'R2 without prior reviews {b_:.4f}'))
# noise ceiling: split-half reliability of the outcome within cells
h = dm(z.assign(a=np.log1p(z.n26o), b=np.log1p(z.n26e)), ['a', 'b']); rel = np.corrcoef(h.a, h.b)[0, 1]; sb = 2 * rel / (1 + rel)
h2 = dm(z.assign(a=z.lfo, b=z.lfe), ['a', 'b']); rel2 = np.corrcoef(h2.a, h2.b)[0, 1]; sb2 = 2 * rel2 / (1 + rel2)
rows.append(dict(model='noise_ceiling', variable='Split-half reliability of 2026 reviews, Spearman-Brown', coef=sb, model_r2=r0.rsquared, n=len(z), note=f'Odd against even months within cells, r {rel:.3f}. Explained share of reliable variation {r0.rsquared / sb:.3f}'))
rows.append(dict(model='noise_ceiling', variable='Split-half reliability of 2025 reviews, Spearman-Brown', coef=sb2, n=len(z), note=f'r {rel2:.3f}'))
o = pd.DataFrame(rows); o.to_csv('reverse_eng/conversion_refit.csv', index=False)
pd.set_option('display.width', 220, 'display.max_columns', 30, 'display.max_colwidth', 44)
print(o[['model', 'variable', 'coef', 'cluster_se', 't', 'shapley_share_pct', 'share_ci_low', 'share_ci_high', 'model_r2', 'n']].round(3).to_string())
print(o[o.model.isin(['noise_ceiling', 'split_iv'])].note.drop_duplicates().to_string())
print('corr within', D[['ln0', 'lf', 'lage', 'lrate']].corr().round(3).to_string())
print('iqr', (D.ln0.quantile(.75) - D.ln0.quantile(.25)).round(3), 'unav missing', z.unav.isna().sum(), 'n25==0', (z.n25 == 0).mean().round(3))
