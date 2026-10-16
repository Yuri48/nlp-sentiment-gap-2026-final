"""
eval_labels.py — Inter-annotator agreement, adjudication support, and classifier performance
against the human gold standard.

Reads labeling/human_label_sample.xlsx (sheets annotator_A, annotator_B, adjudicated).
  * If both annotator sheets are filled: percent agreement and Cohen's kappa for every
    single-label field, Krippendorff's alpha (Jaccard distance) for `topics`, and a list of
    disagreements -> labeling/disagreements.csv (for the adjudication meeting).
  * If the adjudicated sheet is filled (or, failing that, items where A and B agree): accuracy,
    macro-F1, per-class precision/recall for the LLM and every baseline, by kind and source type
    -> labeling/ai_performance.md
  * If no human labels exist yet: prints a notice and writes only the machine-vs-machine comparison.
"""
import os, sys, itertools, json
import numpy as np, pandas as pd
from sklearn.metrics import cohen_kappa_score, accuracy_score, f1_score, classification_report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABDIR = os.path.join(ROOT, 'labeling'); OUT = os.path.join(ROOT, 'data', 'processed')
xl = pd.ExcelFile(os.path.join(LABDIR, 'human_label_sample.xlsx'))
A = xl.parse('annotator_A'); B = xl.parse('annotator_B'); ADJ = xl.parse('adjudicated')
machine = pd.read_csv(os.path.join(LABDIR, '_machine_labels.csv'))
SINGLE = ['relevant', 'tone', 'emotional', 'frame_level_rate', 'frame_scope', 'frame_time', 'numeric_claim', 'attribution_actor', 'attribution_valence', 'post_type']

def filled(df):
    return int(sum(1 for v in df['relevant'] if pd.notna(v) and str(v).strip() not in ('', 'nan', 'None', '<NA>')))

def krippendorff_alpha_sets(a, b):
    """Krippendorff's alpha for set-valued labels with Jaccard distance (two coders)."""
    pairs = [(set(str(x).split(';')) - {''}, set(str(y).split(';')) - {''}) for x, y in zip(a, b)]
    pairs = [(x, y) for x, y in pairs if x or y]
    if len(pairs) < 2:
        return np.nan
    def d(x, y):
        return 1 - len(x & y) / len(x | y) if (x | y) else 0
    Do = np.mean([d(x, y) for x, y in pairs])
    allv = [v for p in pairs for v in p]
    De = np.mean([d(x, y) for x, y in itertools.combinations(allv, 2)])
    return 1 - Do / De if De else np.nan

lines = ['# Human labeling evaluation\n']
nA, nB = filled(A), filled(B)
lines.append(f'Rows coded: annotator A {nA}/{len(A)}, annotator B {nB}/{len(B)}, adjudicated {filled(ADJ)}/{len(ADJ)}\n')
gold = None
if nA >= 50 and nB >= 50:
    both = A.merge(B, on='item_id', suffixes=('_A', '_B'))
    both = both[both['relevant_A'].notna() & both['relevant_B'].notna()]
    rows = []
    for f in SINGLE:
        a = both[f'{f}_A'].astype(str).str.strip().str.lower(); b = both[f'{f}_B'].astype(str).str.strip().str.lower()
        if f != 'relevant':
            mask = (both['relevant_A'].astype(float) == 1) & (both['relevant_B'].astype(float) == 1)
            a, b = a[mask], b[mask]
        if len(a) < 10:
            continue
        rows.append({'field': f, 'n': len(a), 'percent_agreement': (a == b).mean(), 'cohen_kappa': cohen_kappa_score(a, b)})
    rel = (both['relevant_A'].astype(float) == 1) & (both['relevant_B'].astype(float) == 1)
    rows.append({'field': 'topics (Krippendorff alpha, Jaccard)', 'n': int(rel.sum()), 'percent_agreement': np.nan, 'cohen_kappa': krippendorff_alpha_sets(both.loc[rel, 'topics_A'], both.loc[rel, 'topics_B'])})
    agree = pd.DataFrame(rows).round(3)
    lines.append('## Inter-annotator agreement\n' + agree.to_markdown(index=False) + '\n')
    dis = both[(both['tone_A'].astype(str) != both['tone_B'].astype(str)) | (both['relevant_A'].astype(str) != both['relevant_B'].astype(str))]
    dis[['row_A', 'item_id', 'text_A', 'relevant_A', 'relevant_B', 'tone_A', 'tone_B', 'emotional_A', 'emotional_B']].to_csv(os.path.join(LABDIR, 'disagreements.csv'), index=False)
    lines.append(f'Disagreements on relevant/tone: {len(dis)} rows -> labeling/disagreements.csv (resolve in the adjudication meeting).\n')
    if filled(ADJ) >= 50:
        gold = ADJ
        lines.append('Gold standard = adjudicated sheet.\n')
    else:
        gold = both[both['tone_A'].astype(str) == both['tone_B'].astype(str)].rename(columns=lambda c: c[:-2] if c.endswith('_A') else c)
        lines.append(f'Adjudicated sheet not filled: using the {len(gold)} items where A and B agree on tone as provisional gold.\n')
else:
    lines.append('**Human labels pending.** Both annotator sheets need at least 50 coded rows for agreement statistics. '
                 'Until then no AI-vs-human performance can be reported; the machine-vs-machine comparison is in data/processed/baseline_report.md.\n')
if gold is not None:
    g = gold[['item_id', 'kind', 'source', 'relevant', 'tone']].copy()
    g['relevant'] = g['relevant'].astype(float); g['tone'] = pd.to_numeric(g['tone'], errors='coerce')
    m = g.merge(machine[['item_id', 'relevant', 'tone']].rename(columns={'relevant': 'llm_relevant', 'tone': 'llm_tone'}), on='item_id', how='left')
    base = pd.read_parquet(os.path.join(OUT, 'baseline_scores.parquet'))
    m = m.merge(base[['item_id'] + [c for c in base.columns if c.endswith('_class')]], on='item_id', how='left')
    news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))[['item_id', 'source_type', 'source_lean']]
    m = m.merge(news, on='item_id', how='left'); m['source_type'] = m['source_type'].fillna('social')
    lines.append('## AI performance against gold labels\n### Relevance (LLM)\n')
    mm = m.dropna(subset=['relevant', 'llm_relevant'])
    lines.append(f'accuracy = {accuracy_score(mm["relevant"], mm["llm_relevant"]):.3f}, macro-F1 = {f1_score(mm["relevant"], mm["llm_relevant"], average="macro"):.3f} (n={len(mm)})\n')
    rel = m[(m['relevant'] == 1) & m['tone'].notna()]
    res = []
    for c in ['llm_tone', 'gdelt_class', 'vader_class', 'finbert_class', 'twroberta_class', 'tfidf_lr_class']:
        if c not in rel:
            continue
        for grp_name, grp in [('all', rel)] + list(rel.groupby('kind')) + list(rel.groupby('source_type')):
            sub = grp.dropna(subset=[c])
            if len(sub) < 10:
                continue
            res.append({'classifier': c, 'group': grp_name, 'n': len(sub), 'accuracy': accuracy_score(sub['tone'].astype(int), sub[c].astype(int)), 'macro_F1': f1_score(sub['tone'].astype(int), sub[c].astype(int), average='macro')})
    lines.append('### Tone, by classifier and group\n' + pd.DataFrame(res).round(3).to_markdown(index=False) + '\n')
    sub = rel.dropna(subset=['llm_tone'])
    lines.append('### LLM tone per-class report\n```\n' + classification_report(sub['tone'].astype(int), sub['llm_tone'].astype(int), digits=3) + '```\n')
open(os.path.join(LABDIR, 'ai_performance.md'), 'w').write('\n'.join(lines))
print('\n'.join(lines))
