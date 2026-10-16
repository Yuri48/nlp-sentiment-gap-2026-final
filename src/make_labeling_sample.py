"""
make_labeling_sample.py — Stratified sample of 320 items for two independent human annotators.

Strata (news 240 / social 80):
  * news: period (2017-2019 slug-titles 10%, 2020-2024 40%, 2025 20%, 2026 30%) x source type
    (named national 40%, named local 20%, other national 20%, other local/other 20%); within cell,
    LLM tone class balanced (-1/0/+1) so that minority classes are evaluable.
  * social: 2023-2025 40% / 2026 60%, LLM tone balanced.
Items are drawn from the LLM-labelled sample so that AI performance can be computed per class.
Writes labeling/human_label_sample.xlsx with sheets: README, annotator_A, annotator_B, adjudicated
(all label columns empty, machine labels hidden in a separate protected file labeling/_machine_labels.csv).
"""
import os, sys, numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed'); LABDIR = os.path.join(ROOT, 'labeling')
SEED = 20261014; rng = np.random.default_rng(SEED)
lab = pd.read_parquet(os.path.join(OUT, 'labels_llm.parquet'))
news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))
soc = pd.read_parquet(os.path.join(OUT, 'social_items.parquet'))
ln = lab[lab['kind'] == 'news'].merge(news[['item_id', 'domain', 'source_type', 'date', 'text', 'title_source']], on='item_id')
ls = lab[lab['kind'] == 'social'].merge(soc[['item_id', 'date', 'text']], on='item_id')
ln['period'] = pd.cut(pd.to_datetime(ln['date']).dt.year, [2016, 2019, 2024, 2025, 2026], labels=['2017-2019', '2020-2024', '2025', '2026'])
ls['period'] = np.where(pd.to_datetime(ls['date']).dt.year >= 2026, '2026', '2023-2025')
ln['stype'] = ln['source_type'].replace({'local_other': 'other', 'other': 'other'})
ln['tone_cls'] = ln['tone'].fillna(9).astype(int)   # 9 = not relevant
ls['tone_cls'] = ls['tone'].fillna(9).astype(int)

def draw(df, n, strata_w, cls_col='tone_cls'):
    out = []
    for key, w in strata_w.items():
        sub = df
        for col, val in key:
            sub = sub[sub[col] == val]
        k = int(round(n * w))
        if not len(sub) or k == 0:
            continue
        # balance tone classes within the cell (relevant -1/0/+1 and a few irrelevant)
        per = {-1: 0.32, 0: 0.28, 1: 0.28, 9: 0.12}
        parts = []
        for c, pw in per.items():
            s = sub[sub[cls_col] == c]
            kk = min(len(s), int(round(k * pw)))
            if kk:
                parts.append(s.sample(kk, random_state=int(rng.integers(1e9))))
        ch = pd.concat(parts) if parts else sub.iloc[0:0]
        short = k - len(ch)
        if short > 0:
            rest = sub[~sub['item_id'].isin(ch['item_id'])]
            if len(rest):
                ch = pd.concat([ch, rest.sample(min(short, len(rest)), random_state=int(rng.integers(1e9)))])
        out.append(ch)
    return pd.concat(out) if out else df.iloc[0:0]

PER_W = {'2017-2019': 0.10, '2020-2024': 0.40, '2025': 0.20, '2026': 0.30}
ST_W = {'national': 0.40, 'local': 0.20, 'national_other': 0.20, 'other': 0.20}
strata = {((('period', p), ('stype', s))): pw * sw for p, pw in PER_W.items() for s, sw in ST_W.items()}
news_s = draw(ln, 240, strata)
soc_s = draw(ls, 80, {(('period', '2023-2025'),): 0.4, (('period', '2026'),): 0.6})
def top_up(sel, pool, target):
    # strata that do not exist yet (e.g. years not collected) leave the sample short: fill from the remaining pool, tone-balanced
    short = target - len(sel)
    if short <= 0:
        return sel
    rest = pool[~pool['item_id'].isin(sel['item_id'])]
    parts = []
    for c, pw in {-1: 0.32, 0: 0.28, 1: 0.28, 9: 0.12}.items():
        sub = rest[rest['tone_cls'] == c]
        k = min(len(sub), int(round(short * pw)))
        if k:
            parts.append(sub.sample(k, random_state=int(rng.integers(1e9))))
    add = pd.concat(parts) if parts else rest.iloc[0:0]
    if len(add) < short:
        more = rest[~rest['item_id'].isin(add['item_id'])]
        add = pd.concat([add, more.sample(min(short - len(add), len(more)), random_state=int(rng.integers(1e9)))])
    return pd.concat([sel, add])
news_s = top_up(news_s, ln, 240); soc_s = top_up(soc_s, ls, 80)
sample = pd.concat([news_s.assign(kind='news', source=news_s['domain']), soc_s.assign(kind='social', source='bluesky')])
sample = sample.sample(frac=1, random_state=SEED).reset_index(drop=True)
sample['row'] = np.arange(1, len(sample) + 1)
cols = ['row', 'item_id', 'kind', 'source', 'date', 'text']
label_cols = ['relevant', 'tone', 'emotional', 'topics', 'frame_level_rate', 'frame_scope', 'frame_time', 'numeric_claim', 'claims', 'attribution_actor', 'attribution_valence', 'post_type', 'evidence', 'notes']
sheet = sample[cols].copy()
for c in label_cols:
    sheet[c] = ''
os.makedirs(LABDIR, exist_ok=True)
readme = pd.DataFrame({'Instructions': [
    'Two annotators code ALL rows independently in their own sheet (annotator_A / annotator_B). Do not discuss items until both sheets are complete.',
    'Read labeling/LABELING_GUIDE.md and prompts/coding_scheme.md first. Code relevant first; if 0 leave the rest blank.',
    'Allowed values: relevant 0/1; tone -1/0/1; emotional 0/1/2; topics codes separated by ";"; frame_level_rate level/rate/both/na; frame_scope national/household/both/na; frame_time current/forecast/both/na; numeric_claim 0/1; claims indicator=value@period; attribution_actor (see guide); attribution_valence credit/blame/neutral_mention/none; post_type (social only).',
    'After both are done run: python src/eval_labels.py  -> agreement statistics and list of disagreements for adjudication.',
    'Fill the adjudicated sheet during the adjudication meeting (copy the agreed label for every disagreement; agreed labels can be copied by the script).',
    f'Sample: {len(news_s)} news headlines + {len(soc_s)} social posts, stratified by period, source type and machine tone class (seed {SEED}).']})
with pd.ExcelWriter(os.path.join(LABDIR, 'human_label_sample.xlsx')) as xw:
    readme.to_excel(xw, sheet_name='README', index=False)
    sheet.to_excel(xw, sheet_name='annotator_A', index=False)
    sheet.to_excel(xw, sheet_name='annotator_B', index=False)
    sheet.to_excel(xw, sheet_name='adjudicated', index=False)
sample[['row', 'item_id', 'kind', 'source', 'date', 'period', 'relevant', 'tone', 'emotional', 'topics', 'frame_level_rate', 'frame_scope', 'frame_time', 'numeric_claim', 'claims', 'attribution_actor', 'attribution_valence', 'post_type']].to_csv(os.path.join(LABDIR, '_machine_labels.csv'), index=False)
print(f'Wrote {len(sample)} items: news by period/stype:\n', pd.crosstab(news_s['period'], news_s['stype']), '\nsocial by period:', soc_s['period'].value_counts().to_dict(), '\ntone classes:', sample['tone_cls'].value_counts().to_dict())
