"""
collect_bluesky.py — Social-media corpus from the Bluesky public AppView search API.

Design (documented in README.md):
  * Unit of observation: a public Bluesky POST (text, author handle, timestamp) with its
    engagement counts at collection time (likes, reposts, replies, quotes).
  * Endpoint: https://api.bsky.app/xrpc/app.bsky.feed.searchPosts (no authentication).
  * Queries: 9 consumer-economy terms (see QUERIES). English-language posts only.
  * Windows: weekly in 2026 (monitoring window), two-week windows 2023-04-01 .. 2025-12; sort=latest; one page of 100 posts per
    query-week.  When a week
    has more matching posts than we fetch, the sample is the LATEST posts of that week
    (documented truncation; weekly totals are therefore a lower bound on supply).
  * Pacing: 12 s between requests; HTTP 403/429 ('Request forbidden by administrative rules')
    => 3-minute sleeps (the public AppView's firewall rate-limits sustained traffic).
  * Limitations: no geography, no audience/exposure data, engagement counts are
    measured at collection time, and Bluesky's user base is not representative of
    Michigan survey respondents.  Claims are narrowed accordingly in the report.
  * Resumable via data/raw/bluesky/_done.txt; raw posts in data/raw/bluesky/posts.jsonl.
"""
import argparse, json, os, time, datetime as dt
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw', 'bluesky')
os.makedirs(RAW, exist_ok=True)
OUT = os.path.join(RAW, 'posts.jsonl')
DONE = os.path.join(RAW, '_done.txt')
LOG = os.path.join(RAW, '_calls.log')
URL = 'https://api.bsky.app/xrpc/app.bsky.feed.searchPosts'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36 NLP-course-research'

QUERIES = ['inflation', 'grocery prices', 'gas prices', 'cost of living', 'rent', 'layoffs',
           'recession', 'economy', 'tariffs']


def log(msg):
    line = f'{dt.datetime.now().isoformat(timespec="seconds")} {msg}'
    print(line, flush=True)
    with open(LOG, 'a') as f:
        f.write(line + '\n')


def fetch(q, since, until, pages):
    posts, cursor = [], None
    for p in range(pages):
        params = {'q': q, 'limit': 100, 'lang': 'en', 'sort': 'latest',
                  'since': since.strftime('%Y-%m-%dT%H:%M:%SZ'), 'until': until.strftime('%Y-%m-%dT%H:%M:%SZ')}
        if cursor:
            params['cursor'] = cursor
        for attempt in range(5):
            try:
                r = requests.get(URL, params=params, headers={'User-Agent': UA, 'Accept': 'application/json'}, timeout=40)
                if r.status_code in (429, 403):
                    wait = 180 * (attempt + 1)
                    log(f'{r.status_code} on {r.url[:160]} | hdrs={dict((k, v) for k, v in r.headers.items() if k.lower() in ("retry-after", "ratelimit-remaining", "ratelimit-reset", "server", "x-ratelimit-limit"))} | body={r.text[:160]!r} -> sleep {wait}s')
                    time.sleep(wait); continue
                r.raise_for_status()
                d = r.json()
                break
            except Exception as e:
                log(f'ERROR {type(e).__name__} {str(e)[:100]} attempt {attempt}; sleep 15'); time.sleep(15)
        else:
            return posts, True
        time.sleep(12.0)
        batch = d.get('posts', [])
        for po in batch:
            rec = po.get('record', {})
            posts.append({
                'uri': po.get('uri'), 'cid': po.get('cid'),
                'author_handle': po.get('author', {}).get('handle'),
                'author_did': po.get('author', {}).get('did'),
                'created_at': rec.get('createdAt'), 'indexed_at': po.get('indexedAt'),
                'text': rec.get('text', ''), 'langs': rec.get('langs'),
                'like_count': po.get('likeCount'), 'repost_count': po.get('repostCount'),
                'reply_count': po.get('replyCount'), 'quote_count': po.get('quoteCount'),
                'has_embed': 'embed' in rec, 'is_reply': 'reply' in rec,
                '_query': q, '_week_start': since.date().isoformat(), '_page': p,
                '_collected_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
            })
        cursor = d.get('cursor')
        if not cursor or len(batch) < 100:
            break
    return posts, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', default='2023-04-01')
    ap.add_argument('--end', default=dt.date.today().isoformat())
    args = ap.parse_args()
    start = dt.datetime.fromisoformat(args.start)
    end = dt.datetime.fromisoformat(args.end) + dt.timedelta(days=1)
    done = set(l.strip() for l in open(DONE)) if os.path.exists(DONE) else set()
    windows = []
    w_end = end
    while w_end > start:
        days = 7 if w_end > dt.datetime(2026, 1, 1) else 14     # weekly in the 2026 monitoring window, two-week windows before
        w_start = max(start, w_end - dt.timedelta(days=days))
        windows.append((w_start, w_end)); w_end = w_start
    log(f'{len(windows)} weeks x {len(QUERIES)} queries; {len(done)} done')
    total = 0
    with open(OUT, 'a', encoding='utf-8') as out_f:
        for ws, we in windows:
            pages = 1
            for q in QUERIES:
                key = f'{q}|{ws.date()}'
                if key in done:
                    continue
                posts, failed = fetch(q, ws, we, pages)
                if failed:
                    log(f'FAILED {key}'); continue
                for po in posts:
                    out_f.write(json.dumps(po, ensure_ascii=False) + '\n')
                out_f.flush(); total += len(posts)
                with open(DONE, 'a') as f:
                    f.write(key + '\n')
                log(f'{key}: {len(posts)} posts (pages={pages}); total {total}')
    log('FINISHED')


if __name__ == '__main__':
    main()
