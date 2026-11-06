"""The five disclosed lines that would break the pick, each against the trigger set on 6 November 2026.

Every value comes from the 10-Q filed 5 November 2026. A line is breached once its reading passes the trigger on
the failure side and its test has gone live, and this script fails when that happens, so the repo reports it.
"""
import datetime as dt, pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
w = pd.read_csv(H / 'watch_lines.csv')
w['headroom_pct'] = np.where(w.fail_side == 'below', 100 * (w.value - w.trigger) / w.trigger, 100 * (w.trigger - w.value) / w.trigger)
w['live'] = pd.to_datetime(w.live_from) <= pd.Timestamp(dt.date.today())
w['breached'] = w.live & (w.headroom_pct < 0)
w = w.sort_values('headroom_pct').reset_index(drop=True)

R['watch_lines'] = len(w)
R['watch_breached'] = int(w.breached.sum())
R['watch_live'] = int(w.live.sum())
R['watch_closest_headroom_pct'] = float(w.headroom_pct.min())
for r in w.itertuples():
    R['headroom_' + r.short.lower().replace(' ', '_')] = r.headroom_pct
save(__file__, R)

CAP = 25.0
live = w[w.live]
near = live.iloc[0]
fig = plt.figure(figsize=(9, 4.4))
ttl = f'\\${near.trigger:g}' if near.unit == '$' else f'{near.trigger:g}{near.unit}'
titled(fig, f'{near.short} has {near.headroom_pct:.1f}% of headroom to its {ttl} trigger, the least of the {len(live)} live lines',
       'Distance from each disclosed reading to the trigger that would break the pick, as a share of the trigger. Readings from the 10-Q filed 5 November 2026')
ax = fig.add_axes([0.25, 0.20, 0.71, 0.57])
y = np.arange(len(w))[::-1]
for yy, r in zip(y, w.itertuples()):
    c = RED if r.breached else (GREY if not r.live else (BLUE if r.headroom_pct < 5 else NAVY))
    shown = min(r.headroom_pct, CAP)
    ax.barh(yy, shown, color=c, height=0.55)
    edge = 'floor' if r.fail_side == 'below' else 'ceiling'
    tail = f', {r.headroom_pct:.0f}% off the scale' if r.headroom_pct > CAP else ''
    pre, post = ('\\$', '') if r.unit == '$' else ('', r.unit)
    ax.text(shown + 0.5, yy, f'{pre}{r.value:g}{post} against a {pre}{r.trigger:g}{post} {edge}{tail}', va='center', fontsize=8.5, color=INK)
ax.axvline(0, color='#888888', lw=1)
ax.set_yticks(y, w.short)
ax.set_xlim(-2, CAP * 1.9)
ax.set_xticks([0, 5, 10, 15, 20, 25], ['0', '5', '10', '15', '20', '25+'])
ax.set_xlabel('Headroom to the trigger, % of the trigger')
fig.text(0.25, 0.035, 'Grey: Airbnb has until the end of FY2026 before this test runs', color=RED, fontsize=9, fontweight='bold')
finish(fig, __file__, 'watch.png')

if R['watch_breached']:
    hit = ', '.join(w[w.breached].short)
    sys.exit(f'FAIL {R["watch_breached"]} watch line(s) breached: {hit}')
