"""Builds the committed aggregate tables for homes/ and open_nights/ from files that stay outside this repository.
No listing id, licence number, host id, coordinate or rival row leaves this script."""
import collections, json, os, shutil, sys
import duckdb, numpy as np, pandas as pd
A = os.path.expanduser('~/Downloads/ABNB/'); R = A + 'airbnb-case-evidence/'; F = A + 'inventory/final/'; D = A + 'audit/'
sys.path.insert(0, A + 'rival_overlap/04_analysis/scripts')
import ro_common as r, ro_overlap_lib as L

# frame: one row per presence pattern across the ten snapshots, so the union and every snapshot count can be recounted
c = duckdb.connect(F + 'panel.duckdb', read_only=True)
ms = [x[0] for x in c.execute('describe p').fetchall() if x[0].startswith('m2')]
pat = c.execute(f"select {','.join(f'coalesce({m}::int,0) {m}' for m in ms)},count(*) ids from p group by all").df()
pat.columns = [x[1:] if x.startswith('m2') else x for x in pat.columns]; pat.sort_values('ids', ascending=False).to_csv(R + 'homes/frame/presence_patterns.csv', index=False)
print('patterns', pat.shape, pat.ids.sum())
v = pd.read_parquet(F + 'panel_v.parquet', columns=['id', 'vy']); c2 = duckdb.connect(); c2.register('v', v); c2.execute(f"attach '{F}panel.duckdb' as pp (read_only)")
vy = c2.execute("select v.vy id_year,count(*) ever,sum(coalesce(p.m202611::int,0)) in_nov_2026 from pp.p p left join v using(id) group by 1 order by 1").df(); vy.to_csv(R + 'homes/frame/ids_by_year.csv', index=False); print(vy.tail(4))
first = c2.execute(f"select coalesce({','.join(f'case when {m} then {chr(39)}{m[1:]}{chr(39)} end' for m in ms)}) first_snapshot,count(*) ever,sum(coalesce(m202611::int,0)) in_nov_2026 from pp.p group by 1 order by 1").df(); first.to_csv(R + 'homes/survival/ids_by_first_snapshot.csv', index=False); print(first)

# survival: the 400 sampled ids with the id removed
fc = pd.read_csv(F + 'framec_rows.csv').drop_duplicates('id'); print(fc.columns.tolist())
c2.register('fc', fc[['id']]); fs = c2.execute(f"select p.id,coalesce({','.join(f'case when {m} then {chr(39)}{m[1:]}{chr(39)} end' for m in ms)}) first_snapshot from pp.p p join fc using(id)").df()
fc = fc.merge(fs, on='id', how='left'); print(fc.groupby('first_snapshot').live.agg(['sum', 'size']))
fc[['status', 'live', 'g', 'vy', 'first_snapshot', 'last']].rename(columns={'g': 'id_year_group', 'vy': 'id_year', 'last': 'last_snapshot'}).sample(frac=1, random_state=1).to_csv(R + 'homes/survival/sampled_ids.csv', index=False)
pd.read_csv(F + 'survival.csv').rename(columns={'g': 'id_year_group'})[['id_year_group', 'ever', 'now', 'absent']].to_csv(R + 'homes/survival/ids_by_year_group.csv', index=False)

# Seattle overlap cells, the same logic as audit/claim_calc.py
d = pd.read_csv(r.P + '02_interim/candidate_pairs/seattle_rung1.csv', dtype={'id': str}); d = d[~d.type.astype(str).str.contains('hotel|hostel|resort', case=False)]; B = d[d.site == 'booking'].copy()
B['kset'] = [set(str(x).split('|')) if pd.notna(x) and str(x) else set() for x in B['keys']]
cnt = collections.Counter(t for s in B.kset for t in s); S = set(cnt)
a = L.air('seattle'); e = a[a.elig & (a.k.str.len() > 0)].copy(); e['bk'] = [len(k & S) > 0 for k in e.k]
e['host'] = pd.to_numeric(e.calculated_host_listings_count, errors='coerce'); e['av'] = pd.to_numeric(e.availability_365, errors='coerce'); e['n'] = pd.to_numeric(e.estimated_occupancy_l365d, errors='coerce')
ak = collections.defaultdict(list)
for i, s in zip(e.index, e.k):
    for t in s: ak[t].append(i)
e['cap'] = 0.0
for t, vv in ak.items():
    if t in S:
        m_ = min(len(vv), cnt[t])
        for i in vv: e.loc[i, 'cap'] = max(e.loc[i, 'cap'], m_ / len(vv))
e['host_size'] = pd.cut(e.host, [0, 1, 5, 20, 1e9], labels=['1', '2 to 5', '6 to 20', '21 or more']); e['open_over_240'] = (e.av > 240).astype(int); e['on_booking'] = e.bk.astype(int)
g = e.groupby(['host_size', 'open_over_240', 'on_booking'], observed=True).agg(homes=('id', 'size'), floor_homes=('cap', 'sum'), estimated_nights=('n', 'sum')).reset_index()
g.to_csv(R + 'homes/overlap/seattle_home_cells.csv', index=False, float_format='%.6f'); print(g.homes.sum(), g[g.on_booking == 1].homes.sum(), g.floor_homes.sum())
unk = int((~B['keyed']).sum()); notreq = int((B.notreq & ~B['keyed']).sum()); miss = int((B['keyed'] & ~B.hit).sum()); gap = 801 - len(B)
rows = [('Rows Booking.com reported for Seattle', 801), ('Rows used after hotel and market filters', len(B)), ('Rows with a licence number', int(B['keyed'].sum())), ('Keyed rows found in the Airbnb file', int((B['keyed'] & B.hit).sum())), ('Keyed rows absent from the Airbnb file', miss), ('Rows with no licence number', unk), ('Unkeyed rows flagged not required', notreq), ('Reported rows outside the used set', gap), ('Of those, unread', 8), ('Of those, hotel types', 10), ('Of those, outside the market', 10), ('Distinct licence numbers joined', len({t for s in B[B['keyed'] & B.hit].kset for t in s if t in ak}))]
pd.DataFrame(rows, columns=['item', 'rows']).to_csv(R + 'homes/overlap/seattle_booking_rows.csv', index=False); print(rows)

# both rivals and same-host tests
H = pd.read_parquet(A + 'price_map/out/excl_homes.parquet'); print(H.columns.tolist())
b = H.groupby(['mkt', 'bk', 'sh']).agg(homes=('n', 'size'), estimated_nights=('n', 'sum')).reset_index().rename(columns={'mkt': 'market', 'bk': 'on_booking', 'sh': 'on_either_rival'}); b.to_csv(R + 'homes/overlap/both_rivals_cells.csv', index=False, float_format='%.3f'); print(b)
out = []
for m in ['seattle', 'san_diego']:
    aa = L.air(m)[['id', 'host_id', 'accommodates']].copy(); aa['id'] = pd.to_numeric(aa.id, errors='coerce')
    x = H[H.mkt == m].merge(aa, on='id', how='left'); x['acc'] = pd.to_numeric(x.accommodates, errors='coerce'); x['lb'] = np.log(x.bedrooms.clip(lower=1))
    y = x[x.groupby('host_id').sh.transform(lambda s: s.nunique() > 1)]
    print(m, 'hosts', y.host_id.nunique(), 'homes', len(y), 'shared', int(y.sh.sum()))
    for o in ['n', 'av']:
        z = y.dropna(subset=[o, 'lb', 'acc']); cols = [o, 'sh', 'lb', 'acc']; dm = z[cols] - z.groupby('host_id')[cols].transform('mean'); hid = pd.factorize(z.host_id)[0]
        for h in range(hid.max() + 1):
            q = dm[hid == h].values; M = q.T @ q; iu = np.triu_indices(4)
            out.append(dict(market=m, outcome={'n': 'airbnb_nights', 'av': 'open_nights'}[o], host_index=h, homes=int((hid == h).sum()), **{f'{["y","shared","log_bedrooms","capacity"][i]}*{["y","shared","log_bedrooms","capacity"][j]}': M[i, j] for i, j in zip(*iu)}))
pd.DataFrame(out).to_csv(R + 'open_nights/same_host/host_moments.csv', index=False, float_format='%.12g')

for src, dst in (('match_ladder.csv', 'homes/match_ladder/match_ladder.csv'), ('task_map_audit.csv', 'homes/task_map/task_map_audit.csv'), ('task_map_audit_second_coder.csv', 'homes/task_map/task_map_second_coder.csv')):
    shutil.copy(D + src, R + dst)
shutil.copy(A + 'altdata/reframe/mech/new_home_owner.csv', R + 'homes/new_owners/new_home_owner.csv')
shutil.copy(F + 'replacement.csv', R + 'homes/flows/ten_city_flows.csv')
for f in ('universe_size.csv', 'frame_profile.csv', 'region_mix.csv'): shutil.copy(F + f, R + 'homes/viewable/' + f)
for f in ('steady_inclusion.csv', 'cliff.csv'): shutil.copy(F + f, R + 'homes/frame/' + f)
