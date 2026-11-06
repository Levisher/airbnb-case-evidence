"""Turns the home-level regression frame into neighbourhood-level moment tables, so conversion/review_effect reruns with no home rows published.
Needs files that stay outside this repository. Kept as the record of how the committed tables were made."""
import duckdb, glob, os, re, sys
import numpy as np, pandas as pd
os.chdir(os.path.expanduser('~/Downloads/ABNB'))
OUT = os.path.expanduser('~/Downloads/ABNB/airbnb-case-evidence/conversion/review_effect/')
os.makedirs(OUT, exist_ok=True)
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
cal = pd.concat(post).groupby('id').a90.mean().rename('a90').reset_index(); cal['id'] = cal.id.astype('float64')
z = z.merge(cal, on='id', how='left'); z['unav'] = 100 * (1 - z.a90 / 90)
z['lf'] = np.log1p(z.n25); z['lfo'] = np.log1p(z.n25o); z['lfe'] = np.log1p(z.n25e)
z['age'] = (2026 * 12 + 1 - z.first_m).clip(lower=1); z['lage'] = np.log(z.age); z['lrate'] = z.ln0 - z.lage
z['ha'] = np.log1p(z.n26o); z['hb'] = np.log1p(z.n26e)
G = ['city', 'neighbourhood_cleansed', 'br']; z['cl'] = pd.factorize(z.city + '|' + z.neighbourhood_cleansed)[0]
def export(df, cols, name):
    d = df[cols] - df.groupby(G)[cols].transform('mean'); A = d.values; cl = df.cl.values
    nC = int(z.cl.max()) + 1; M = np.zeros((nC, len(cols), len(cols))); np.add.at(M, cl, A[:, :, None] * A[:, None, :]); n = np.bincount(cl, minlength=nC)
    iu = np.triu_indices(len(cols)); o = pd.DataFrame(M[:, iu[0], iu[1]], columns=[f'{cols[i]}*{cols[j]}' for i, j in zip(*iu)])
    o.insert(0, 'homes', n); o.insert(0, 'neighbourhood_index', range(nC)); o = o[o.homes > 0]
    o.to_csv(OUT + name, index=False, float_format='%.15g'); print(name, o.shape, int(n.sum()))
X = ['y', 'ln0', 'bad_l', 'bad_h', 'lp', 'lo', 'lf', 'lfo', 'lfe', 'lage', 'lrate']
export(z, X + ['ha', 'hb'], 'moments_all_homes.csv')
c = z[z.unav.notna()]; export(c, ['unav', 'ln0', 'bad_l', 'bad_h', 'lp', 'lo', 'lf'], 'moments_calendar.csv')
for lo_, hi, nm in ((3, 5, '3_to_5'), (6, 25, '6_to_25'), (26, 100, '26_to_100'), (101, 10**6, 'over_100')):
    export(z[(z.n0 >= lo_) & (z.n0 <= hi)], ['y', 'ln0', 'bad_l', 'bad_h', 'lp', 'lo', 'lf'], f'moments_band_{nm}.csv')
print('cells', z.groupby(G).ngroups, 'neighbourhoods', z.cl.nunique())
