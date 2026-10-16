"""
collect_gkg.py — News corpus from GDELT 2.0 Global Knowledge Graph (GKG) 15-minute files.

Why this source: the GDELT DOC API throttles sustained querying (documented in README), while
the raw GKG files are static downloads (http://data.gdeltproject.org/gdeltv2/<timestamp>.gkg.csv.zip,
one file every 15 minutes since Feb 2015).  Each record is one article GDELT crawled in that
window, with source domain, URL, themes, locations, the GDELT dictionary tone (V2Tone) and,
from 2020 onward, the page title.

Sampling design (documented, systematic):
  * Two 15-minute slices per day for 2026-01-01 .. today (monitoring window): 14:30 UTC (10:30 ET,
    after the 08:30 data releases are digested) and 20:30 UTC (16:30 ET, after the market close).
  * One 14:30 UTC slice per day for 2024-01-01 .. 2025-12-31.
  * One 14:30 UTC slice every second day for 2020-01-01 .. 2023-12-31.
  * One 15:00 UTC slice every third day for 2017-01-01 .. 2019-12-31, where no page titles exist
    and the headline is reconstructed from the URL slug (flagged title_source = 'url_slug').
    (The thinner schedule for older years was forced by download bandwidth; it is systematic,
    not selective, and is recorded per item through the timestamp.)
  * Unit of observation = article headline (title) + URL + domain + crawl time.  No full text.
Filters applied at collection time (everything else is discarded):
  * English-language source (TranslationInfo empty).
  * Economy-related: any GKG theme starting with ECON_, or containing UNEMPLOYMENT / INFLATION /
    RECESSION, or a headline matching the economic keyword regex.
  * US relevance: the article mentions a US location (V1 Locations contains '#US#') or the
    domain is in the named outlet panel (collect_gdelt.GROUPS).
  * Press-release wires, stock-spam and aggregator domains are excluded (BLOCKLIST).
Outputs: data/raw/gkg/items_YYYY-MM.jsonl, data/raw/gkg/_done.txt (resumable), _calls.log.
"""
import argparse, csv, io, json, os, re, sys, time, zipfile, datetime as dt
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from collect_gdelt import GROUPS  # named outlet panel

RAW = os.path.join(ROOT, 'data', 'raw', 'gkg')
os.makedirs(RAW, exist_ok=True)
DONE = os.path.join(RAW, '_done.txt')
LOG = os.path.join(RAW, '_calls.log')
csv.field_size_limit(10 ** 9)
PANEL = {d for g in GROUPS.values() for d in g}
TITLE_RE = re.compile(r'<PAGE_TITLE>(.*?)</PAGE_TITLE>', re.S)
KW = re.compile(r'\b(econom\w*|inflation|prices?|unemploy\w*|jobs?|jobless|layoffs?|hiring|recession|wages?|tariffs?|'
                r'interest rates?|fed|federal reserve|gdp|cost of living|mortgage\w*|housing|rent|gas prices?|gasoline|'
                r'consumers?|paychecks?|groceries|grocery|inflationary|stagflation|downturn|slowdown|payrolls?)\b', re.I)
BLOCKLIST = {'prnewswire.com', 'businesswire.com', 'globenewswire.com', 'pr-inside.com', 'prweb.com', 'accesswire.com',
             'tickerreport.com', 'wkrb13.com', 'etfdailynews.com', 'themarketsdaily.com', 'dailypolitical.com', 'marketbeat.com',
             'americanbankingnews.com', 'baseballnewssource.com', 'thelincolnianonline.com', 'modernreaders.com', 'zacks.com',
             'seekingalpha.com', 'investorplace.com', 'fool.com', 'benzinga.com', 'einnews.com', 'newswire.ca', 'newsfilecorp.com',
             'openpr.com', 'streetinsider.com', 'marketscreener.com', 'tipranks.com', 'investing.com', 'fxstreet.com', 'dailyfx.com',
             'forexlive.com', 'investinglive.com', 'yahoo.com', 'msn.com', 'news.google.com', 'tennesseedaily.com', 'freshplaza.com',
             'investmentnews.com', 'patriotpost.us', 'moonofalabama.org', 'pafoa.org', 'hellenicshippingnews.com', 'kitco.com'}
ECON_THEME = re.compile(r'(^|;)(ECON_[A-Z_]+|UNEMPLOYMENT|[A-Z_0-9]*INFLATION[A-Z_]*|[A-Z_0-9]*RECESSION[A-Z_]*)(,|;|$)')


def log(msg):
    line = f'{dt.datetime.now().isoformat(timespec="seconds")} {msg}'
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def slug_title(url):
    """Reconstruct a headline from a URL slug (pre-2020 files have no titles)."""
    path = re.sub(r'^https?://[^/]+/', '', url)
    path = re.sub(r'\?.*$', '', path)
    segs = [s for s in path.split('/') if s]
    if not segs:
        return ''
    cand = max(segs, key=len)
    cand = re.sub(r'\.(html?|php|aspx?)$', '', cand)
    words = [w for w in re.split(r'[-_]+', cand) if w and not w.isdigit()]
    if len(words) < 4:
        return ''
    return ' '.join(words)


def process_file(ts):
    url = f'https://data.gdeltproject.org/gdeltv2/{ts}.gkg.csv.zip'
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 404:
                return None, 0, 0
            r.raise_for_status()
            break
        except Exception as e:
            log(f'ERROR {ts} attempt {attempt}: {str(e)[:100]}'); time.sleep(10 * (attempt + 1))
    else:
        return None, 0, 0
    try:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        raw = z.read(z.namelist()[0]).decode('latin-1')
    except Exception as e:
        log(f'ZIP ERROR {ts}: {e}'); return None, 0, 0
    items, n = [], 0
    for row in csv.reader(io.StringIO(raw), delimiter='\t'):
        if len(row) < 27:
            continue
        n += 1
        if row[25] != '':          # translated (non-English) source
            continue
        dom = row[3].lower()
        if dom in BLOCKLIST or dom.endswith('.blogspot.com'):
            continue
        in_panel = dom in PANEL
        us_loc = '#US#' in row[9]
        if not (in_panel or us_loc):
            continue
        m = TITLE_RE.search(row[26])
        title = m.group(1).strip() if m else ''
        title_source = 'page_title'
        if not title:
            title = slug_title(row[4]); title_source = 'url_slug'
        if not title:
            continue
        econ_theme = bool(ECON_THEME.search(row[7]))
        kw_hit = bool(KW.search(title))
        if not (econ_theme or kw_hit):
            continue
        tone = row[15].split(',')
        try:
            tone_v = [float(x) for x in tone[:7]]
        except ValueError:
            tone_v = [None] * 7
        themes = sorted({t for t in row[7].split(';') if t.startswith('ECON_') or 'UNEMPLOY' in t or 'INFLATION' in t or 'RECESSION' in t})
        items.append({'gkg_id': row[0], 'datetime': row[1], 'domain': dom, 'url': row[4], 'title': title, 'title_source': title_source,
                      'in_panel': in_panel, 'us_loc': us_loc, 'econ_theme': econ_theme, 'kw_hit': kw_hit, 'themes': themes,
                      'tone': tone_v[0], 'tone_pos': tone_v[1], 'tone_neg': tone_v[2], 'polarity': tone_v[3], 'wordcount': tone_v[6]})
    return items, n, len(r.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2017-01-01'); ap.add_argument('--end', default=dt.date.today().isoformat())
    args = ap.parse_args()
    start = dt.date.fromisoformat(args.start)
    end = dt.date.fromisoformat(args.end)
    done = set(l.strip() for l in open(DONE)) if os.path.exists(DONE) else set()
    day = end
    total = 0
    while day >= start:
        # schedule: 2 slices/day in 2026; 1/day 2024-2025; 1 every 2nd day 2020-2023; 1 every 3rd day 2017-2019
        if day.year >= 2026:
            slices = ['143000', '203000']
        elif day.year >= 2024:
            slices = ['143000']
        elif day.year >= 2020:
            slices = ['143000'] if day.toordinal() % 2 == 0 else []
        else:
            slices = ['150000'] if day.toordinal() % 3 == 0 else []
        for sl in slices:
            ts = day.strftime('%Y%m%d') + sl
            if ts in done:
                continue
            items, n, nbytes = process_file(ts)
            if items is None:
                log(f'{ts}: missing/failed');
                with open(DONE, 'a') as f: f.write(ts + '\n')
                continue
            fn = os.path.join(RAW, f'items_{day.strftime("%Y-%m")}.jsonl')
            with open(fn, 'a', encoding='utf-8') as f:
                for it in items:
                    f.write(json.dumps(it, ensure_ascii=False) + '\n')
            with open(DONE, 'a') as f:
                f.write(ts + '\n')
            total += len(items)
            log(f'{ts}: {n} records, kept {len(items)} ({nbytes/1e6:.1f} MB); total kept {total}')
            time.sleep(0.3)
        day -= dt.timedelta(days=1)
    log('FINISHED')


if __name__ == '__main__':
    main()
