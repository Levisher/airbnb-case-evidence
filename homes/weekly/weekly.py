"""Supply tracked week by week against the 6,934,269 ids in the November 2026 sitemap.

The Friday run appends one row to weekly_counts.csv. This script redraws the series and fails when the live count
drifts past DRIFT_PCT of that count, or when churn passes CHURN_PCT, which marks a sitemap layout change.
"""
import datetime as dt, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

NOV_TOTAL = 6934269           # the count in homes/frame
NOV_DATE = '2026-11-04'
DRIFT_PCT, CHURN_PCT, STALE_DAYS = 5.0, 10.0, 10

H = here(__file__); R = {}
w = pd.read_csv(H / 'weekly_counts.csv').sort_values('run_date')
done = w[w.status == 'complete'].reset_index(drop=True)
if not len(done):
    sys.exit('no complete run in weekly_counts.csv')
last = done.iloc[-1]

R['weekly_runs'] = len(done)
R['weekly_total_ids'] = last.total_ids
R['weekly_vs_nov_pct'] = 100 * (last.total_ids - NOV_TOTAL) / NOV_TOTAL
R['weekly_churn_pct'] = last.churn_rate_pct
R['weekly_ids_new'] = last.ids_new
R['weekly_ids_gone'] = last.ids_gone
R['weekly_net_change_pct'] = last.net_change_pct
R['weekly_files_read'] = last.files_read
save(__file__, R)

dates = [NOV_DATE] + list(done.run_date)
totals = [NOV_TOTAL] + list(done.total_ids)
fig = plt.figure(figsize=(9, 4.6))
titled(fig, f'Supply sits {R["weekly_vs_nov_pct"]:+.2f}% from the 6,934,269 ids in the November 2026 sitemap',
       f'Unique listing ids in Airbnb\'s published sitemaps, {len(done)} complete run(s) since {NOV_DATE}, one worker and no retries')

ax = fig.add_axes([0.085, 0.15, 0.42, 0.63])
x = np.arange(len(dates))
ax.axhline(NOV_TOTAL / 1e6, color=GREY, lw=1.2)
ax.plot(x, [t / 1e6 for t in totals], color=NAVY, lw=1.8, marker='o', ms=4.5)
ax.plot(x[0], NOV_TOTAL / 1e6, 'o', color=BLUE, ms=6)
ax.set_xticks(x, [d[5:] for d in dates], fontsize=8)
ax.set_ylabel('Unique listing ids, millions')
lo, hi = min(totals) / 1e6, max(totals) / 1e6; pad = max((hi - lo) * 0.6, 0.05)
ax.set_ylim(lo - pad, hi + pad)
ax.text(x[0], NOV_TOTAL / 1e6 + pad * 0.18, 'November 2026', color=BLUE, fontsize=8.5)
callout(ax, f'{last.total_ids:,} on {last.run_date}', .02, .97)

ax2 = fig.add_axes([0.60, 0.15, 0.37, 0.63])
xb = np.arange(len(done))
ax2.bar(xb - 0.18, done.ids_new / 1e3, width=0.36, color=BLUE, label='Ids new')
ax2.bar(xb + 0.18, done.ids_gone / 1e3, width=0.36, color=NAVY, label='Ids gone')
ax2.set_xticks(xb, [str(d)[5:] for d in done.run_date], fontsize=8)
ax2.set_xlim(-0.75, max(len(done) - 0.25, 3.25))
ax2.set_ylim(0, max(done.ids_new.max(), done.ids_gone.max()) / 1e3 * 1.45)
ax2.set_ylabel('Ids, thousands')
ax2.legend(frameon=False, fontsize=8.5, loc='upper right')
callout(ax2, f'Churn {last.churn_rate_pct:.2f}% since {last.previous_run}', .02, .97)
finish(fig, __file__, 'weekly.png')

drift = abs(R['weekly_vs_nov_pct'])
if drift > DRIFT_PCT:
    sys.exit(f'FAIL supply moved {drift:.2f}% from November 2026, past the {DRIFT_PCT}% band')
if last.churn_rate_pct > CHURN_PCT:
    sys.exit(f'FAIL churn {last.churn_rate_pct:.2f}% passed {CHURN_PCT}%, check the sitemap layout before reading the count')
if last.layout_flag:
    sys.exit('FAIL the run raised its own layout flag, read the weekly log before reading the count')
age = (dt.date.today() - dt.date.fromisoformat(str(last.run_date))).days
if age > STALE_DAYS:
    sys.exit(f'FAIL the last run is {age} days old, past {STALE_DAYS}, so the Friday job has stopped')
