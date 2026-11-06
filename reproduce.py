"""Runs every study from the committed tables, compares each result with figures.csv, and fails on any file no claim reaches.

python reproduce.py            run all studies, fail on any mismatch
python reproduce.py --table    also rewrite the status table in README.md from figures.csv
"""
import csv, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parent
TERMS = ('ebitda', 'booked_nights', 'homes', 'open_nights', 'conversion', 'contribution_per_night', 'marketing', 'fixed_cost')
ORDER = {'dropped': 0, 'weakened': 1, 'holding': 2}


def studies():
    for t in TERMS:
        for p in sorted((ROOT / t).glob('*/*.py')):
            yield p


def run():
    bad = []
    for p in studies():
        r = subprocess.run([sys.executable, p.name], cwd=p.parent, capture_output=True, text=True)
        print(f"{'ok ' if r.returncode == 0 else 'FAIL'} {p.relative_to(ROOT)}")
        if r.returncode:
            bad.append(str(p.relative_to(ROOT))); print(r.stderr[-800:])
    return bad


def compare():
    rows = list(csv.DictReader(open(ROOT / 'figures.csv', encoding='utf-8'))); miss = []; n = 0
    cache = {}
    for r in rows:
        if not r['figure_id']:
            continue
        f = ROOT / r['folder']
        if f not in cache:
            cache[f] = {x['figure_id']: float(x['value']) for p in f.glob('*_results.csv') for x in csv.DictReader(open(p))}
        v = cache[f].get(r['figure_id']); n += 1
        if v is None or abs(v - float(r['expected'])) > float(r['tolerance']) + 1e-9:
            miss.append((r['folder'], r['figure_id'], r['expected'], v))
    return n, len(rows), miss


def table():
    rows = list(csv.DictReader(open(ROOT / 'figures.csv', encoding='utf-8')))
    out = ['| Term | Holding | Weakened | Dropped |', '|---|---|---|---|']
    n = lambda t, st: sum(r['status'] == st and (t is None or r['term'] == t) for r in rows)
    for t in TERMS:
        out.append(f"| [{t}]({t}/) | {n(t, 'holding')} | {n(t, 'weakened')} | {n(t, 'dropped')} |")
    out.append(f"| **All** | **{n(None, 'holding')}** | **{n(None, 'weakened')}** | **{n(None, 'dropped')}** |")
    s = (ROOT / 'README.md').read_text(encoding='utf-8'); a, b = '<!-- table start -->', '<!-- table end -->'
    (ROOT / 'README.md').write_text(s[:s.index(a) + len(a)] + '\n' + '\n'.join(out) + '\n' + s[s.index(b):], encoding='utf-8')


def orphans():
    """Every file must be reachable from a claim: a figure row, a script that reads it, or a term README that shows it."""
    rows = list(csv.DictReader(open(ROOT / 'figures.csv', encoding='utf-8'))); bad = []
    folders = {r['folder'] for r in rows}; code = ''.join(p.read_text() for p in studies())
    for r in rows:
        if r['claim'] not in '123' or r['status'] not in ORDER or r['term'] not in TERMS:
            bad.append(('untagged figure', r['figure']))
    for t in TERMS:
        note = (ROOT / t / 'README.md').read_text(encoding='utf-8')
        for p in (ROOT / t).rglob('*'):
            rel = str(p.relative_to(ROOT))
            if p.is_dir() or '__pycache__' in rel or p.name.endswith('_results.csv') or p.name == 'README.md':
                continue
            if p.suffix == '.py' and str(p.parent.relative_to(ROOT)) not in folders:
                bad.append(('script serves no figure', rel))
            if p.suffix == '.csv' and p.name not in code:
                bad.append(('table read by no script', rel))
            if p.suffix in ('.png', '.md') and p.name not in note:
                bad.append(('file not shown in the term README', rel))
    return bad


if __name__ == '__main__':
    failed = run(); n, total, miss = compare(); loose = orphans()
    if '--table' in sys.argv:
        table()
    print(f'\n{n} figures checked against figures.csv, {total - n} cited or logged with no rerun')
    for m in miss:
        print('MISMATCH', m)
    for m in loose:
        print('LOOSE', m)
    print('PASS' if not failed and not miss and not loose else 'FAIL')
    sys.exit(1 if failed or miss or loose else 0)
