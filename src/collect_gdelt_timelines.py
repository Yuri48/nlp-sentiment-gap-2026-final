"""
collect_gdelt_timelines.py — Full-coverage daily tone and volume series from the GDELT DOC 2.0 API
timeline modes (one call per query/mode spanning 2017-01-01 .. today).

Unlike artlist (which is capped at 250 records and throttled for bulk use), timeline modes
summarise ALL matching articles GDELT monitored, so they provide an independent, un-sampled
dictionary-tone and salience benchmark for the sliced GKG corpus:
  timelinetone    daily average GDELT tone of matching articles
  timelinevolraw  daily number of matching articles and total monitored articles (salience = share)
Queries: topic terms restricted to US sources, and 'economy' / 'inflation' restricted to each
named outlet group (domainis: lists, which the API accepts with a single search term).
Output: data/raw/gdelt_timelines/<slug>.json and timelines_daily.csv (long format).
"""
import os, sys, json, time, re, datetime as dt
import requests, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect_gdelt import GROUPS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw', 'gdelt_timelines'); os.makedirs(RAW, exist_ok=True)
BASE = 'https://api.gdeltproject.org/api/v2/doc/doc'
TOPICS = ['inflation', 'prices', 'unemployment', 'layoffs', 'jobs', 'recession', 'economy', 'tariffs', '"interest rates"', '"cost of living"', 'wages', '"gas prices"', '"grocery prices"']
queries = {f'topic_{re.sub(r"[^a-z]", "", t)}': f'{t} sourcecountry:US' for t in TOPICS}
for g, doms in GROUPS.items():
    dl = ' OR '.join(f'domainis:{d}' for d in doms)
    queries[f'group_{g}_economy'] = f'economy ({dl})'
    queries[f'group_{g}_inflation'] = f'inflation ({dl})'
rows = []
for slug, q in queries.items():
    for mode in ['timelinetone', 'timelinevolraw']:
        fn = os.path.join(RAW, f'{slug}__{mode}.json')
        if os.path.exists(fn):
            d = json.load(open(fn))
        else:
            d = None
            for attempt in range(12):
                time.sleep(10)
                try:
                    r = requests.get(BASE, params={'query': q, 'mode': mode, 'format': 'json', 'startdatetime': '20170101000000', 'enddatetime': dt.date.today().strftime('%Y%m%d') + '235959'}, timeout=120)
                except requests.RequestException as e:
                    print(f'{slug} {mode}: network error {type(e).__name__}; sleeping 60s', flush=True); time.sleep(60); continue
                if r.text.startswith('{'):
                    d = r.json(); json.dump(d, open(fn, 'w')); break
                print(f'{slug} {mode}: throttled/invalid (attempt {attempt}); sleeping 150s', flush=True); time.sleep(150)
            if d is None:
                print(f'FAILED {slug} {mode}', flush=True); continue
        for series in d.get('timeline', []):
            for pt in series.get('data', []):
                rows.append({'slug': slug, 'query': q, 'mode': mode, 'series': series.get('series'), 'date': pt['date'][:8], 'value': pt.get('value'), 'norm': pt.get('norm')})
        print(f'{slug} {mode}: {sum(len(s.get("data", [])) for s in d.get("timeline", []))} points', flush=True)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(RAW, 'timelines_daily.csv'), index=False)
print('saved', df.shape)
