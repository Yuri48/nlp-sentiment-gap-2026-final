"""
collect_gdelt.py — Build the news-headline corpus from the GDELT DOC 2.0 API.

Design (documented in README.md, section "Corpus"):
  * Unit of observation: a news ARTICLE HEADLINE (title) + URL + source domain + GDELT
    "seendate" (time GDELT first saw the article). We do NOT collect full text.
  * Source panel: 49 named US outlets, grouped into 6 query groups (3 national, 3 local).
    Exact-domain matching (domainis:) so that e.g. arabic.cnn.com is excluded.
  * Topic filter: the article full text must match the economic topic query below
    (GDELT searches full text, so headlines may be tangential; a headline keyword
    filter and the LLM relevance flag are applied downstream).
  * Coverage: 2017-01-01 .. today (GDELT DOC API full-text coverage starts Jan 2017).
  * Sampling: GDELT returns at most 250 records per query.  To obtain COMPLETE coverage
    of the matched set rather than a truncated sample, windows start at 7 days and are
    bisected recursively whenever a response hits the 250-record cap (down to 1 day).
  * Rate limit: GDELT asks for <= 1 request / 5 s.  We space calls 6 s apart and back
    off on throttle messages.
  * Resumable: finished windows are logged to data/raw/gdelt/_done.txt; raw responses
    are appended to data/raw/gdelt/articles.jsonl.

Usage:
  python src/collect_gdelt.py [--start 2017-01-01] [--end 2026-10-15] [--groups N1,N2,...]
"""
import argparse, json, os, sys, time, datetime as dt, urllib.parse
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw', 'gdelt')
os.makedirs(RAW, exist_ok=True)
OUT = os.path.join(RAW, 'articles.jsonl')
DONE = os.path.join(RAW, '_done.txt')
LOG = os.path.join(RAW, '_calls.log')

BASE = 'https://api.gdeltproject.org/api/v2/doc/doc'
UA = 'NLP-final-project corpus collector (academic; contact via course)'

TOPIC = ('(economy OR inflation OR prices OR unemployment OR jobs OR layoffs OR recession '
         'OR wages OR tariffs OR "interest rates" OR "cost of living")')

# ---- Source panel -----------------------------------------------------------------
# Audience-ideology / bias labels come from the README (Pew 2014/2020 audience profiles,
# AllSides media-bias chart, Ad Fontes).  They are used only for stratification.
GROUPS = {
    'N1': ['apnews.com', 'reuters.com', 'cnn.com', 'foxnews.com', 'nbcnews.com',
           'cbsnews.com', 'abcnews.go.com', 'usatoday.com'],
    'N2': ['nytimes.com', 'wsj.com', 'washingtonpost.com', 'cnbc.com', 'foxbusiness.com',
           'marketwatch.com', 'nypost.com', 'bloomberg.com'],
    'N3': ['huffpost.com', 'breitbart.com', 'dailycaller.com', 'washingtonexaminer.com',
           'thehill.com', 'politico.com', 'newsweek.com', 'msnbc.com', 'ms.now'],
    'L1': ['chicagotribune.com', 'freep.com', 'detroitnews.com', 'cleveland.com',
           'jsonline.com', 'startribune.com', 'dispatch.com', 'post-gazette.com'],
    'L2': ['ajc.com', 'tampabay.com', 'miamiherald.com', 'dallasnews.com',
           'houstonchronicle.com', 'azcentral.com', 'reviewjournal.com', 'charlotteobserver.com'],
    'L3': ['latimes.com', 'sfchronicle.com', 'seattletimes.com', 'denverpost.com',
           'oregonlive.com', 'inquirer.com', 'bostonglobe.com', 'kansascity.com'],
}


def build_query(group):
    doms = ' OR '.join(f'domainis:{d}' for d in GROUPS[group])
    return f'{TOPIC} sourcelang:english ({doms})'


def fmt(d):
    return d.strftime('%Y%m%d%H%M%S')


def log(msg):
    line = f'{dt.datetime.now().isoformat(timespec="seconds")} {msg}'
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


_last_call = 0.0


def gdelt_call(query, start, end, maxrecords=250, retries=6):
    """One artlist call. Returns list of article dicts. Enforces 6s spacing."""
    global _last_call
    params = {'query': query, 'mode': 'artlist', 'maxrecords': maxrecords, 'sort': 'datedesc',
              'format': 'json', 'startdatetime': fmt(start), 'enddatetime': fmt(end)}
    for attempt in range(retries):
        wait = 6.0 - (time.time() - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()
        try:
            r = requests.get(BASE, params=params, headers={'User-Agent': UA}, timeout=60)
            txt = r.text
            if txt.startswith('Please limit') or r.status_code == 429:
                log(f'THROTTLED (attempt {attempt}) -> sleeping 30s')
                time.sleep(30)
                continue
            if not txt.strip():
                return []  # GDELT returns empty body when nothing matches
            data = json.loads(txt)
            return data.get('articles', [])
        except (json.JSONDecodeError, requests.RequestException) as e:
            log(f'ERROR {type(e).__name__}: {str(e)[:120]} (attempt {attempt}) -> sleeping 20s')
            time.sleep(20)
    log('GIVING UP on window ' + fmt(start) + '-' + fmt(end))
    return None


def collect_window(group, start, end, out_f, depth=0):
    """Adaptive bisection: if the 250 cap binds and window > 1 day, split."""
    arts = gdelt_call(build_query(group), start, end)
    if arts is None:
        return 0, 1
    n, calls = len(arts), 1
    if n >= 250 and (end - start) > dt.timedelta(days=1):
        mid = start + (end - start) / 2
        mid = mid.replace(hour=0, minute=0, second=0, microsecond=0) if (end - start) > dt.timedelta(days=2) else mid
        if mid <= start or mid >= end:
            mid = start + (end - start) / 2
        log(f'  cap hit ({n}) in {group} {start.date()}..{end.date()} -> split at {mid}')
        n1, c1 = collect_window(group, start, mid, out_f, depth + 1)
        n2, c2 = collect_window(group, mid, end, out_f, depth + 1)
        return n1 + n2, calls + c1 + c2
    for a in arts:
        a['_group'] = group
        a['_win_start'] = fmt(start)
        a['_win_end'] = fmt(end)
        out_f.write(json.dumps(a, ensure_ascii=False) + '\n')
    out_f.flush()
    return n, calls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2017-01-01')
    ap.add_argument('--end', default=dt.date.today().isoformat())
    ap.add_argument('--groups', default=','.join(GROUPS))
    ap.add_argument('--window-days', type=int, default=7)
    args = ap.parse_args()
    groups = args.groups.split(',')
    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end)
    done = set()
    if os.path.exists(DONE):
        done = set(l.strip() for l in open(DONE))
    # windows, most recent first (monitoring window is the priority)
    windows = []
    w_end = end
    while w_end > start:
        w_start = max(start, w_end - dt.timedelta(days=args.window_days))
        windows.append((w_start, w_end))
        w_end = w_start
    log(f'{len(windows)} windows x {len(groups)} groups; {len(done)} already done')
    total = 0
    with open(OUT, 'a', encoding='utf-8') as out_f:
        for (ws, we) in windows:
            for g in groups:
                key = f'{g}|{fmt(ws)}|{fmt(we)}'
                if key in done:
                    continue
                n, calls = collect_window(g, ws, we, out_f)
                total += n
                with open(DONE, 'a') as f:
                    f.write(key + '\n')
                log(f'{g} {ws.date()}..{we.date()}: {n} articles in {calls} call(s); total {total}')
    log('FINISHED')


if __name__ == '__main__':
    main()
