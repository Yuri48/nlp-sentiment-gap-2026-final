"""
make_llm_batches.py — Draw the stratified sample of items to be labelled by the LLM and write
batch files for the classifier (src/classify_llm.py or the Claude Code sub-agent runner).

Sampling (seed 20261014, reproducible):
  News: per month, up to N_NEWS headlines with an economic keyword in the title, stratified by
        source type (named national panel, named local panel, other national, other local/other)
        in proportion 40/25/20/15, newest-first ties broken at random.  N_NEWS = 60 for
        2017-01..2025-12 and 150 for 2026-01 onward (monitoring window).
  Social: per month, up to N_SOC posts, N_SOC = 40 for 2023-07..2025-12 and 100 for 2026,
        stratified across the 9 collection queries.
Batches of 40 items -> data/processed/llm/in/batch_####.json; manifest.csv lists item->batch.
Re-running adds only NEW months/items (existing batch assignments are preserved).
"""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed'); LLM = os.path.join(OUT, 'llm'); IN = os.path.join(LLM, 'in')
os.makedirs(IN, exist_ok=True); os.makedirs(os.path.join(LLM, 'out'), exist_ok=True)
SEED = 20261014
BATCH = 40
rng = np.random.default_rng(SEED)

news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))
news = news[news['kw_title'] & (news['source_type'] != 'foreign')].copy()
# only months whose collection is complete (every scheduled GKG slice for the month is in _done.txt)
import datetime as dt
done = set(l.strip() for l in open(os.path.join(ROOT, 'data', 'raw', 'gkg', '_done.txt')))
def month_complete(mstr):
    y, mo = int(mstr[:4]), int(mstr[5:7]); d = dt.date(y, mo, 1); today = dt.date.today()
    while d.month == mo and d <= today:
        if d.year >= 2026: sl = ['143000', '203000']
        elif d.year >= 2024: sl = ['143000']
        elif d.year >= 2020: sl = ['143000'] if d.toordinal() % 2 == 0 else []
        else: sl = ['150000'] if d.toordinal() % 3 == 0 else []
        if any(d.strftime('%Y%m%d') + x not in done for x in sl):
            return False
        d += dt.timedelta(days=1)
    return True
complete = {mth for mth in news['month'].unique() if month_complete(mth)}
news = news[news['month'].isin(complete)]
print('complete news months:', sorted(complete))
soc_fn = os.path.join(OUT, 'social_items.parquet')
soc = pd.read_parquet(soc_fn) if os.path.exists(soc_fn) else pd.DataFrame()

man_fn = os.path.join(LLM, 'manifest.csv')
manifest = pd.read_csv(man_fn) if os.path.exists(man_fn) else pd.DataFrame(columns=['item_id', 'kind', 'month', 'batch'])
already = set(manifest['item_id'])

def n_news(month):
    return 150 if month >= '2026-01' else 60

def n_soc(month):
    return 100 if month >= '2026-01' else 40

STRATA = {'national': 0.40, 'local': 0.25, 'national_other': 0.20, 'local_other': 0.075, 'other': 0.075}
already_by_month = manifest.groupby(['kind', 'month']).size().to_dict() if len(manifest) else {}
sel = []
for month, g in news.groupby('month'):
    n = n_news(month) - already_by_month.get(('news', month), 0)
    if n <= 0:
        continue
    g = g[~g['item_id'].isin(already)]
    if len(g) <= n:
        sel.append(g); continue
    parts = []
    for st, w in STRATA.items():
        gg = g[g['source_type'] == st]
        k = min(len(gg), int(round(n * w)))
        if k:
            parts.append(gg.sample(k, random_state=int(rng.integers(1e9))))
    chosen = pd.concat(parts) if parts else g.iloc[0:0]
    short = n - len(chosen)
    if short > 0:
        rest = g[~g['item_id'].isin(chosen['item_id'])]
        chosen = pd.concat([chosen, rest.sample(min(short, len(rest)), random_state=int(rng.integers(1e9)))])
    sel.append(chosen)
news_sel = pd.concat(sel) if sel else news.iloc[0:0]
news_sel = news_sel.assign(kind='news', source=news_sel['domain'], date_str=news_sel['date'].astype(str))

soc_sel = soc.iloc[0:0]
if len(soc):
    parts = []
    soc_done = set(l.strip() for l in open(os.path.join(ROOT, 'data', 'raw', 'bluesky', '_done.txt')))
    soc_weeks = sorted({k.split('|')[1] for k in soc_done})
    for month, g in soc.groupby('month'):
        if month < '2023-07':
            continue
        # a social month is complete when a collected window starts on/before the 1st of the month
        if not any(w <= f'{month}-01' for w in soc_weeks):
            continue
        n = n_soc(month) - already_by_month.get(('social', month), 0)
        if n <= 0:
            continue
        g = g[~g['item_id'].isin(already)]
        if len(g) <= n:
            parts.append(g); continue
        per_q = max(1, n // g['query'].nunique())
        chosen = g.groupby('query', group_keys=False).apply(lambda x: x.sample(min(len(x), per_q), random_state=int(rng.integers(1e9))))
        short = n - len(chosen)
        if short > 0:
            rest = g[~g['item_id'].isin(chosen['item_id'])]
            chosen = pd.concat([chosen, rest.sample(min(short, len(rest)), random_state=int(rng.integers(1e9)))])
        parts.append(chosen)
    if parts:
        soc_sel = pd.concat(parts)
        soc_sel = soc_sel.assign(kind='social', source='bluesky', date_str=soc_sel['date'].astype(str))

items = pd.concat([news_sel[['item_id', 'kind', 'source', 'date_str', 'text', 'month']], soc_sel[['item_id', 'kind', 'source', 'date_str', 'text', 'month']]]) if len(soc_sel) else news_sel[['item_id', 'kind', 'source', 'date_str', 'text', 'month']]
items = items.sample(frac=1, random_state=SEED)   # shuffle so batches mix months/sources (prevents order effects)
start_batch = int(manifest['batch'].max()) + 1 if len(manifest) else 1
new_rows = []
for i in range(0, len(items), BATCH):
    b = start_batch + i // BATCH
    chunk = items.iloc[i:i + BATCH]
    payload = [{'id': r.item_id, 'kind': r.kind, 'source': r.source, 'date': r.date_str, 'text': r.text} for r in chunk.itertuples()]
    with open(os.path.join(IN, f'batch_{b:04d}.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=0)
    for r in chunk.itertuples():
        new_rows.append({'item_id': r.item_id, 'kind': r.kind, 'month': r.month, 'batch': b})
manifest = pd.concat([manifest, pd.DataFrame(new_rows)], ignore_index=True)
manifest.to_csv(man_fn, index=False)
print(f'New items: {len(new_rows)} ({(items["kind"]=="news").sum()} news, {(items["kind"]=="social").sum()} social) in batches {start_batch}..{start_batch + max(0, (len(items)-1)//BATCH)}; manifest total {len(manifest)}')
