"""The 54-task map against outside checks. Every count comes from the audit file, which keeps the filed rating, the check, its source and the corrected rating."""
import pathlib, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from evidence import *

H = here(__file__); R = {}
t = pd.read_csv(H / 'task_map_audit.csv')
R['task_count'] = len(t); R['task_role_fail'] = (t.role_verdict == 'Fails').sum(); R['task_role_survive'] = (t.role_verdict == 'Survives').sum()
for b in ('Done', 'Partly', 'No role'):
    R[f'task_filed_{b.lower().replace(" ", "_")}'] = (t.role_bucket_as_filed == b).sum(); R[f'task_corrected_{b.lower().replace(" ", "_")}'] = (t.role_bucket_corrected == b).sum()
for k in ('Fact', 'Definition', 'Coded against Airbnb'):
    R['task_fail_' + k.split()[0].lower()] = (t.failure_kind == k).sum()
R['task_automation_fail'] = (t.automation_verdict == 'Fails').sum(); R['task_automation_survive'] = (t.automation_verdict == 'Survives').sum(); R['task_automation_no_check'] = (t.automation_verdict == 'No usable check').sum()
R['task_does_or_shares'] = R['task_corrected_done'] + R['task_corrected_partly']; R['task_second_coder_automation_disputes'] = (t.automation_verdict != t.second_coder_automation_verdict).sum(); R['task_moved_done_to_partly'] = ((t.role_bucket_as_filed == 'Done') & (t.role_bucket_corrected == 'Partly')).sum()
save(__file__, R)
fig = plt.figure(figsize=(9, 3.9)); titled(fig, '16 of 54 role ratings failed an outside check, and tasks Airbnb does outright fall from 21 to 8', 'Airbnb role across the 54 tasks of running a listing, as filed and after outside checks')
ax = fig.add_axes([0.1, 0.26, 0.86, 0.5]); L = ['As filed', 'After checks'][::-1]; a = [R['task_corrected_done'], R['task_filed_done']]; b = [R['task_corrected_partly'], R['task_filed_partly']]; c = [R['task_corrected_no_role'], R['task_filed_no_role']]
ax.barh(L, a, color=NAVY, height=.55, label='Does the task'); ax.barh(L, b, left=a, color=BLUE, height=.55, label='Shares it'); ax.barh(L, c, left=np.add(a, b), color=GREY, height=.55, label='No role')
for i in range(2):
    ax.text(a[i] / 2, i, f'{a[i]:.0f}', ha='center', va='center', color='white', fontsize=10); ax.text(a[i] + b[i] / 2, i, f'{b[i]:.0f}', ha='center', va='center', fontsize=10); ax.text(a[i] + b[i] + c[i] / 2, i, f'{c[i]:.0f}', ha='center', va='center', fontsize=10)
ax.set_xlim(0, 54); ax.set_xlabel('Tasks'); ax.legend(frameon=False, ncol=3, loc='upper center', bbox_to_anchor=(.5, -.24), fontsize=8.5)
finish(fig, __file__, 'task_map.png')
