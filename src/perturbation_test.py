"""
perturbation_test.py — Does changing political names or source labels alter the classification of
otherwise identical text?  (project brief, section 3)

  python src/perturbation_test.py make   -> writes data/processed/llm/in/pert_####.json batches containing
                                           the ORIGINAL item and its perturbed variants (shuffled, new ids)
  python src/perturbation_test.py eval   -> compares labels across variants -> data/processed/perturbation_report.md

Variants (applied to relevant LLM-labelled items that contain a political name or to all items for the
source-label test):
  name_swap     Trump <-> Biden (and administration/White House references) swapped
  src_left      item shown as coming from a left-leaning outlet (source field = 'huffpost.com')
  src_right     item shown as coming from a right-leaning outlet (source field = 'foxnews.com')
  src_wire      item shown as coming from a wire service (source field = 'apnews.com')
Because the prompt tells the coder to ignore the source, any systematic change under src_* variants is a
classifier bias; changes under name_swap that flip attribution_actor are expected (the actor changed) but
changes in tone / emotional are not.
"""
import os, re, sys, json, glob
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed'); LLM = os.path.join(OUT, 'llm')
SEED = 20261014
SWAP = [(r'\bTrump\b', '\x00A'), (r'\bBiden\b', '\x00B'), (r'\bTrump\'s\b', '\x00A\'s'), (r'\bBiden\'s\b', '\x00B\'s')]

def name_swap(t):
    t2 = re.sub(r'\bTrump\b', '\x00A', t); t2 = re.sub(r'\bBiden\b', 'Trump', t2); t2 = t2.replace('\x00A', 'Biden')
    t2 = re.sub(r'\bRepublicans?\b', '\x00R', t2); t2 = re.sub(r'\bDemocrats?\b', 'Republicans', t2); t2 = t2.replace('\x00R', 'Democrats')
    t2 = re.sub(r'\bGOP\b', 'Democratic Party', t2)
    return t2

def make():
    lab = pd.read_parquet(os.path.join(OUT, 'labels_llm.parquet'))
    news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))[['item_id', 'text', 'domain', 'date']]
    soc = pd.read_parquet(os.path.join(OUT, 'social_items.parquet'))[['item_id', 'text', 'date']].assign(domain='bluesky')
    items = pd.concat([news, soc]).merge(lab[lab['relevant'] == 1][['item_id', 'kind']], on='item_id')
    rng = np.random.default_rng(SEED)
    pol = items[items['text'].str.contains(r'\b(?:Trump|Biden|Republican|Democrat|GOP)', regex=True)]
    pol = pol.sample(min(80, len(pol)), random_state=SEED)
    src = items[items['kind'] == 'news'].sample(min(80, len(items[items['kind'] == 'news'])), random_state=SEED + 1)
    rows = []
    for r in pol.itertuples():
        rows.append({'id': f'p_{r.item_id}_orig', 'kind': r.kind, 'source': r.domain, 'date': str(r.date), 'text': r.text, '_base': r.item_id, '_variant': 'original'})
        rows.append({'id': f'p_{r.item_id}_swap', 'kind': r.kind, 'source': r.domain, 'date': str(r.date), 'text': name_swap(r.text), '_base': r.item_id, '_variant': 'name_swap'})
    for r in src.itertuples():
        for v, s in [('original', r.domain), ('src_left', 'huffpost.com'), ('src_right', 'foxnews.com'), ('src_wire', 'apnews.com')]:
            rows.append({'id': f'p_{r.item_id}_{v}', 'kind': 'news', 'source': s, 'date': str(r.date), 'text': r.text, '_base': r.item_id, '_variant': v})
    df = pd.DataFrame(rows).sample(frac=1, random_state=SEED)
    df[['id', '_base', '_variant']].to_csv(os.path.join(LLM, 'pert_manifest.csv'), index=False)
    for i in range(0, len(df), 40):
        chunk = df.iloc[i:i + 40]
        json.dump([{k: r[k] for k in ['id', 'kind', 'source', 'date', 'text']} for _, r in chunk.iterrows()], open(os.path.join(LLM, 'in', f'pert_{i // 40 + 1:04d}.json'), 'w'), ensure_ascii=False, indent=0)
    print(f'{len(df)} perturbation items in {(len(df) - 1) // 40 + 1} batches ({len(pol)} name-swap pairs, {len(src)} source-label quadruples)')

def evaluate():
    man = pd.read_csv(os.path.join(LLM, 'pert_manifest.csv'))
    labs = []
    for fn in sorted(glob.glob(os.path.join(LLM, 'out', 'pert_*.json'))):
        try:
            labs.extend(json.load(open(fn)))
        except Exception as e:
            print('bad', fn, e)
    lab = pd.DataFrame(labs).merge(man, on='id')
    lines = ['# Perturbation tests (classifier robustness)\n', f'Labelled variants: {len(lab)} of {len(man)}\n']
    base = lab[lab['_variant'] == 'original'].drop_duplicates('_base').set_index('_base')
    for v in ['name_swap', 'src_left', 'src_right', 'src_wire']:
        sub = lab[lab['_variant'] == v].drop_duplicates('_base').set_index('_base')
        common = sub.index.intersection(base.index)
        if not len(common):
            continue
        res = {'n_pairs': len(common)}
        for f in ['relevant', 'tone', 'emotional', 'frame_scope', 'attribution_actor', 'attribution_valence']:
            a = base.loc[common, f].astype(str); b = sub.loc[common, f].astype(str)
            res[f'flip_rate_{f}'] = float((a != b).mean())
        ta = pd.to_numeric(base.loc[common, 'tone'], errors='coerce'); tb = pd.to_numeric(sub.loc[common, 'tone'], errors='coerce')
        res['mean_tone_change'] = float((tb - ta).mean())
        lines.append(f'## {v}\n' + pd.Series(res).round(3).to_markdown() + '\n')
        if v == 'name_swap':
            ct = pd.crosstab(base.loc[common, 'attribution_actor'].astype(str), sub.loc[common, 'attribution_actor'].astype(str))
            lines.append('Attribution actor, original (rows) vs swapped (columns) — a clean swap moves trump_admin <-> biden_admin:\n' + ct.to_markdown() + '\n')
    open(os.path.join(OUT, 'perturbation_report.md'), 'w').write('\n'.join(lines))
    print('\n'.join(lines))

if __name__ == '__main__':
    (make if sys.argv[1] == 'make' else evaluate)()
