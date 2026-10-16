"""
merge_llm_outputs.py — Validate every LLM output batch against the coding scheme and merge the
labels with the item manifest.

Outputs: data/processed/labels_llm.parquet, data/processed/llm/validation_report.md
Invalid records (bad keys / values) are listed, kept out of the labels, and their batches are
flagged for re-run.
"""
import glob, json, os, re
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed'); LLM = os.path.join(OUT, 'llm')
TOPICS = {'jobs_loss', 'jobs_gain', 'prices_up', 'prices_down', 'growth', 'recession', 'rates', 'housing', 'wages_income', 'tariffs_trade', 'markets', 'gov_policy', 'other_econ'}
ALLOWED = {'relevant': {0, 1}, 'tone': {-1, 0, 1}, 'emotional': {0, 1, 2},
           'frame_level_rate': {'level', 'rate', 'both', 'na'}, 'frame_scope': {'national', 'household', 'both', 'na'},
           'frame_time': {'current', 'forecast', 'both', 'na'}, 'numeric_claim': {0, 1},
           'attribution_actor': {'trump_admin', 'biden_admin', 'congress_republicans', 'congress_democrats', 'federal_reserve', 'corporations', 'foreign_trade_partners', 'other', 'none'},
           'attribution_valence': {'credit', 'blame', 'neutral_mention', 'none'},
           'post_type': {'personal_experience', 'opinion', 'news_share', 'other', 'na'}}
manifest = pd.read_csv(os.path.join(LLM, 'manifest.csv'))
rows, problems, missing_batches = [], [], []
for fn in sorted(glob.glob(os.path.join(LLM, 'in', 'batch_*.json'))):
    b = int(re.search(r'(\d+)', os.path.basename(fn)).group(1))
    out_fn = fn.replace('/in/', '/out/')
    if not os.path.exists(out_fn):
        missing_batches.append(b); continue
    try:
        arr = json.load(open(out_fn, encoding='utf-8'))
    except Exception as e:
        problems.append((b, 'unreadable', str(e)[:80])); continue
    ids_in = [x['id'] for x in json.load(open(fn, encoding='utf-8'))]
    got = {x.get('id'): x for x in arr if isinstance(x, dict)}
    for iid in ids_in:
        x = got.get(iid)
        if x is None:
            problems.append((b, iid, 'missing id')); continue
        rec = {'item_id': iid, 'batch': b}
        ok = True
        rel = x.get('relevant')
        if rel not in (0, 1):
            problems.append((b, iid, f'relevant={rel!r}')); continue
        rec['relevant'] = int(rel)
        if rel == 1:
            for k, allowed in ALLOWED.items():
                v = x.get(k)
                if k == 'post_type' and v is None:
                    v = 'na'
                if isinstance(v, float) and v.is_integer():
                    v = int(v)
                if v not in allowed:
                    problems.append((b, iid, f'{k}={v!r}')); ok = False; break
                rec[k] = v
            if not ok:
                continue
            tp = x.get('topics') or []
            tp = [t for t in tp if t in TOPICS]
            if not tp:
                problems.append((b, iid, 'no valid topic')); continue
            rec['topics'] = ';'.join(sorted(set(tp)))
            claims = x.get('claims') or []
            rec['claims'] = json.dumps([c for c in claims if isinstance(c, dict) and 'indicator' in c and 'value' in c])
            rec['evidence'] = str(x.get('evidence', ''))[:120]
        rows.append(rec)
labels = pd.DataFrame(rows)
labels = labels.merge(manifest[['item_id', 'kind', 'month']], on='item_id', how='left')
labels.to_parquet(os.path.join(OUT, 'labels_llm.parquet'), index=False)
with open(os.path.join(LLM, 'validation_report.md'), 'w') as f:
    f.write(f'# LLM label validation\n\n* Items in manifest: {len(manifest)}\n* Labelled and valid: {len(labels)}\n* Invalid records: {len(problems)}\n'
            f'* Batches without output: {missing_batches[:50]}{" ..." if len(missing_batches) > 50 else ""} ({len(missing_batches)})\n\n')
    if len(labels):
        f.write('## Distribution\n')
        f.write(labels.groupby('kind')['relevant'].agg(['count', 'mean']).rename(columns={'mean': 'share_relevant'}).to_markdown() + '\n\n')
        rl = labels[labels['relevant'] == 1]
        if len(rl):
            f.write(pd.crosstab(rl['kind'], rl['tone'], normalize='index').round(3).to_markdown() + '\n\n')
            f.write(pd.crosstab(rl['kind'], rl['emotional'], normalize='index').round(3).to_markdown() + '\n\n')
    if problems:
        f.write('## Problems (first 100)\n')
        for p in problems[:100]:
            f.write(f'* batch {p[0]}: {p[1]} — {p[2]}\n')
print(open(os.path.join(LLM, 'validation_report.md')).read())
