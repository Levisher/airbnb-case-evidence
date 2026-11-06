"""Weekly supply tracker on Airbnb's published sitemaps. Reads the master index and the listing-url files, nothing else.

One worker, a 9 second gap, no retries. The first 429, challenge page or bad file stops the run, keeps what was read and exits.
Fetches go through crawl4ai in HTTP mode, because its browser mode cancels .gz downloads and fetch_pages.py batches six pages,
retries in stealth and falls back to Firecrawl. The challenge test is the one in fetch_pages.py.

Exit codes: 0 complete, 2 stopped early, 3 refused to start.
"""
import asyncio, csv, datetime as dt, fcntl, gzip, json, os, pathlib, re, sys, time
import certifi
os.environ.setdefault('SSL_CERT_FILE', certifi.where())
import numpy as np
sys.path.insert(0, os.path.expanduser('~/.claude/scripts'))
from fetch_pages import CHALLENGE

ROOT = pathlib.Path(os.environ.get('WEEKLY_ROOT', pathlib.Path(__file__).resolve().parent))
WEEKS = ROOT / 'weekly'; COUNTS = ROOT / 'weekly_counts.csv'; LOG = ROOT / '_logs' / 'weekly_sitemap.log'; LOCK = ROOT / '.weekly_sitemap.lock'
NOV_FILES = pathlib.Path(os.path.expanduser('~/Downloads/ABNB/inventory/sitemap/files')); NOV_DATE = '2026-11-04'
INDEX = 'https://www.airbnb.com/sitemap-master-index.xml.gz'   # the Sitemap line in Airbnb's robots.txt
UA = 'QFS club research'
GAP = 9; NOV_TOTAL = 6934269; NOV_COUNT = 139; FLAG_PCT = 10.0
LISTING = re.compile(r'sitemap-(homes[a-z_]*)-urls-\d+\.xml\.gz$'); ROOM = re.compile(rb'/rooms/(\d+)')
FIELDS = ['run_date', 'status', 'stop_reason', 'files_listed', 'files_read', 'total_ids', 'ids_new', 'ids_gone', 'net_change', 'net_change_pct', 'churn_rate_pct',
          'file_change_pct', 'total_change_pct', 'layout_flag', 'previous_run', 'vs_nov_2026_pct', 'segments']


class Stop(Exception):
    pass


def log(msg):
    line = f'{dt.datetime.now():%Y-%m-%d %H:%M:%S} {msg}'
    print(line, flush=True); LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


class Fetcher:
    """One crawl4ai HTTP session. Every request waits out the gap first, and none is ever repeated."""
    def __init__(self, folder):
        self.folder = folder; self.last = 0.0

    async def __aenter__(self):
        from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy
        from crawl4ai.async_configs import HTTPCrawlerConfig
        self.st = AsyncHTTPCrawlerStrategy(browser_config=HTTPCrawlerConfig(method='GET', headers={'User-Agent': UA}, follow_redirects=True, downloads_path=str(self.folder)))
        await self.st.__aenter__(); return self

    async def __aexit__(self, *a):
        await self.st.__aexit__(*a)

    async def get(self, url):
        from crawl4ai import CrawlerRunConfig, CacheMode
        wait = GAP - (time.monotonic() - self.last)
        if wait > 0:
            await asyncio.sleep(wait)
        self.last = time.monotonic(); name = url.rsplit('/', 1)[-1]
        try:
            r = await self.st.crawl(url, config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=120000))
        except Exception as e:
            code = getattr(e, 'status_code', None); text = str(e)
            raise Stop('429' if code == 429 or '429' in text else f'error {code or type(e).__name__}')
        return check(self.folder / name, getattr(r, 'html', '') or '')


def check(path, html=''):
    """A good file is real gzip holding XML. Anything else is a challenge page or a broken download."""
    if not path.exists():
        raise Stop('challenge' if CHALLENGE.search(html[:3000]) else 'no file saved')
    b = path.read_bytes()
    if b[:2] != b'\x1f\x8b':
        raise Stop('challenge' if CHALLENGE.search(b[:3000].decode('utf8', 'ignore')) else 'not gzip')
    try:
        x = gzip.decompress(b)
    except Exception:
        raise Stop('truncated gzip')
    if b'<loc>' not in x:
        raise Stop('challenge' if CHALLENGE.search(x[:3000].decode('utf8', 'ignore')) else 'no urls in file')
    return x


def ids_in(x):
    return np.array(ROOM.findall(x), dtype='U20').astype(np.int64)


def week_ids(folder):
    parts = [ids_in(gzip.open(p).read()) for p in sorted(folder.glob('*.xml.gz')) if LISTING.search(p.name)]
    return np.unique(np.concatenate(parts))


def previous():
    """The last complete run, or the November 2026 pull if none exists yet. Early-stopped weeks never serve as a base."""
    rows = list(csv.DictReader(open(COUNTS))) if COUNTS.exists() else []
    done = [r for r in rows if r['status'] == 'complete']
    if done:
        r = done[-1]; return r['run_date'], WEEKS / r['run_date'], int(r['files_read']), int(r['total_ids'])
    return NOV_DATE, NOV_FILES, NOV_COUNT, NOV_TOTAL


def write_row(row):
    new = not COUNTS.exists()
    with open(COUNTS, 'a', newline='') as f:
        w = csv.DictWriter(f, FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)


async def collect(folder, fetcher_cls):
    got = {}; seg = {}; rows = 0; reason = ''; listed = 0
    try:
        async with fetcher_cls(folder) as f:
            index = await f.get(INDEX)
            urls = [u for u in re.findall(r'<loc>\s*([^<\s]+)', index.decode('utf8', 'ignore')) if LISTING.search(u)]
            listed = len(urls); log(f'index lists {listed} listing files')
            if not urls:
                raise Stop('no listing files in index')
            for u in urls:
                name = u.rsplit('/', 1)[-1]; x = await f.get(u); a = ids_in(x); fam = LISTING.search(name).group(1)
                got[name] = a; seg[fam] = seg.get(fam, 0) + len(a); rows += len(a); log(f'{name} {len(a)} rows')
    except Stop as e:
        reason = str(e); log(f'STOP {reason} after {len(got)} of {listed} files, no retry')
    return got, seg, rows, listed, reason


def pct(a, b):
    return round(100 * a / b, 4) if b else ''


def run(today=None, fetcher_cls=Fetcher):
    ROOT.mkdir(parents=True, exist_ok=True); lock = open(LOCK, 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        log('REFUSED a previous run is still going'); return 3
    date = today or dt.date.today().isoformat(); folder = WEEKS / date
    if folder.exists():
        log(f'REFUSED {folder.name} already exists, earlier files are never overwritten'); return 3
    folder.mkdir(parents=True); log(f'START {date}, one worker, {GAP} s gap')
    got, seg, rows, listed, reason = asyncio.run(collect(folder, fetcher_cls))
    base_date, base_dir, base_files, base_total = previous()
    row = dict.fromkeys(FIELDS, ''); row.update(run_date=date, status='stopped' if reason else 'complete', stop_reason=reason, files_listed=listed, files_read=len(got), previous_run=base_date, segments=json.dumps(seg))
    ids = np.unique(np.concatenate(list(got.values()))) if got else np.array([], dtype=np.int64); total = len(ids); row['total_ids'] = total
    fc = pct(listed - base_files, base_files) if listed else ''; row['file_change_pct'] = fc
    if not reason:
        old = week_ids(base_dir); new = len(np.setdiff1d(ids, old, assume_unique=True)); gone = len(np.setdiff1d(old, ids, assume_unique=True)); b = len(old)
        tc = pct(total - b, b); flag = abs(fc) > FLAG_PCT or abs(tc) > FLAG_PCT
        row.update(ids_new=new, ids_gone=gone, net_change=new - gone, net_change_pct=pct(new - gone, b), churn_rate_pct=pct(new + gone, b), total_change_pct=tc, layout_flag=int(flag), vs_nov_2026_pct=pct(total - NOV_TOTAL, NOV_TOTAL))
        log(f'net {new - gone:+,} ({row["net_change_pct"]}%), new {new:,}, gone {gone:,}, churn {row["churn_rate_pct"]}% against {base_date}')
        if flag:
            log(f'FLAG layout check: files {fc}%, total {tc}% against {base_date}. A jump this size usually marks a sitemap layout change')
        log(f'Latest total {total:,} against {NOV_TOTAL:,} in November 2026: {total - NOV_TOTAL:+,} ({row["vs_nov_2026_pct"]}%)')
    else:
        row['layout_flag'] = int(bool(fc != '' and abs(fc) > FLAG_PCT))
    write_row(row)
    log(f'END {row["status"]}, files {len(got)} of {listed}, rows {rows:,}, unique ids {total:,}, segments {row["segments"]}')
    return 2 if reason else 0


if __name__ == '__main__':
    sys.exit(run())
