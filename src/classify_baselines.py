"""
classify_baselines.py — Dictionary and conventional-classifier baselines for TONE.

Baselines (all produce a 3-class tone in {-1, 0, +1} plus a continuous score):
  1. GDELT V2Tone (news only): article-level dictionary tone computed by GDELT over the FULL
     article text; class = sign with a +/-1.0 dead band (documented choice, tuned on nothing).
  2. VADER (Hutto & Gilbert 2014) compound score on the headline / post text; class thresholds
     +/-0.05 (the authors' convention).
  3. FinBERT (ProsusAI/finbert; BERT fine-tuned on Financial PhraseBank) — a conventional
     supervised transformer classifier for financial news tone.  Applied to headlines and posts.
  4. Twitter-RoBERTa (cardiffnlp/twitter-roberta-base-sentiment-latest) — a conventional
     classifier trained on tweets; applied to posts and headlines.
  5. TF-IDF + logistic regression trained on the LLM labels (5-fold cross-validated), the
     cheapest "train-your-own" conventional classifier.
Outputs: data/processed/baseline_scores.parquet (one row per item scored), baseline_report.md.

Items scored: every non-foreign headline with an economic keyword in the title and every post,
so monthly indices can be built from the FULL corpus for baselines 1-4, and from the LLM sample
for the LLM.  Runs on Apple MPS / CUDA when available, else CPU.
"""
import os, re, json, sys, time, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed')
MODE = sys.argv[1] if len(sys.argv) > 1 else 'all'   # 'fast' = skip transformers

news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))
news = news[news['kw_title'] & (news['source_type'] != 'foreign')]
soc = pd.read_parquet(os.path.join(OUT, 'social_items.parquet')) if os.path.exists(os.path.join(OUT, 'social_items.parquet')) else pd.DataFrame()
items = pd.concat([news[['item_id', 'month', 'text', 'tone']].assign(kind='news'),
                   soc[['item_id', 'month', 'text']].assign(kind='social', tone=np.nan)], ignore_index=True)
print(f'{len(items):,} items to score ({(items.kind=="news").sum():,} news, {(items.kind=="social").sum():,} social)', flush=True)

# 1. GDELT tone
items['gdelt_tone'] = items['tone']
items['gdelt_class'] = np.where(items['gdelt_tone'] > 1.0, 1, np.where(items['gdelt_tone'] < -1.0, -1, 0))
items.loc[items['gdelt_tone'].isna(), 'gdelt_class'] = np.nan

# 2. VADER
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
sia = SentimentIntensityAnalyzer()
t0 = time.time()
items['vader'] = [sia.polarity_scores(t)['compound'] for t in items['text']]
items['vader_class'] = np.where(items['vader'] >= 0.05, 1, np.where(items['vader'] <= -0.05, -1, 0))
print(f'VADER done in {time.time()-t0:.0f}s', flush=True)

# incremental: reuse transformer scores for items already scored in a previous run
prev_fn = os.path.join(OUT, 'baseline_scores.parquet')
prev = pd.read_parquet(prev_fn) if os.path.exists(prev_fn) else pd.DataFrame()
have = set(prev['item_id']) if len(prev) and 'finbert_class' in prev else set()
if MODE != 'fast':
    import torch
    from transformers import pipeline
    device = 'mps' if torch.backends.mps.is_available() else ('cuda' if torch.cuda.is_available() else 'cpu')
    print('device', device, flush=True)
    def run_pipe(model, texts, label_map, bs=64):
        clf = pipeline('text-classification', model=model, device=device, truncation=True, max_length=96)
        out = []
        for i in range(0, len(texts), bs):
            res = clf(list(texts[i:i + bs]), batch_size=bs)
            out.extend([(label_map[r['label'].lower()], r['score']) for r in res])
            if (i // bs) % 50 == 0:
                print(f'  {model}: {i}/{len(texts)}', flush=True)
        return out
    new = items[~items['item_id'].isin(have)]
    print(f'{len(new):,} items need transformer scores ({len(have):,} cached)', flush=True)
    texts = new['text'].str.slice(0, 300).tolist()
    t0 = time.time()
    fb = run_pipe('ProsusAI/finbert', texts, {'positive': 1, 'negative': -1, 'neutral': 0}) if len(texts) else []
    tw = run_pipe('cardiffnlp/twitter-roberta-base-sentiment-latest', texts, {'positive': 1, 'negative': -1, 'neutral': 0}) if len(texts) else []
    scored = pd.DataFrame({'item_id': new['item_id'].values, 'finbert_class': [c for c, _ in fb], 'finbert_conf': [s for _, s in fb],
                           'twroberta_class': [c for c, _ in tw], 'twroberta_conf': [s for _, s in tw]})
    if len(have):
        scored = pd.concat([prev[['item_id', 'finbert_class', 'finbert_conf', 'twroberta_class', 'twroberta_conf']], scored], ignore_index=True).drop_duplicates('item_id')
    items = items.merge(scored, on='item_id', how='left')
    print(f'transformers done in {time.time()-t0:.0f}s', flush=True)

# 5. TF-IDF + logistic regression trained on LLM labels (if available)
lab_fn = os.path.join(OUT, 'labels_llm.parquet')
report = [f'# Baseline classifiers ({dt.date.today()})\n', f'Items scored: {len(items):,}\n']
if os.path.exists(lab_fn):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import cross_val_predict, StratifiedKFold
    from sklearn.metrics import classification_report, f1_score, accuracy_score
    lab = pd.read_parquet(lab_fn)
    lab = lab[lab['relevant'] == 1].merge(items[['item_id', 'text', 'kind']], on='item_id')
    if len(lab) >= 200:
        vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        Xl = vec.fit_transform(lab['text']); yl = lab['tone'].astype(int)
        lr = LogisticRegression(max_iter=2000, C=3.0, class_weight='balanced')
        cv = StratifiedKFold(5, shuffle=True, random_state=20261014)
        pred_cv = cross_val_predict(lr, Xl, yl, cv=cv)
        report.append(f'## TF-IDF + logistic regression (5-fold CV on {len(lab):,} LLM-labelled relevant items)\n'
                      f'accuracy = {accuracy_score(yl, pred_cv):.3f}, macro-F1 = {f1_score(yl, pred_cv, average="macro"):.3f}\n\n```\n'
                      + classification_report(yl, pred_cv, digits=3) + '```\n')
        lr.fit(Xl, yl)
        items['tfidf_lr_class'] = lr.predict(vec.transform(items['text']))
        # for the labelled items themselves use the CROSS-VALIDATED prediction (otherwise agreement is in-sample)
        cvmap = dict(zip(lab['item_id'], pred_cv))
        items['tfidf_lr_class'] = [cvmap.get(i, c) for i, c in zip(items['item_id'], items['tfidf_lr_class'])]
        # agreement of each baseline with the LLM on the labelled set (NOT a gold standard; see human labels)
        comp = items.merge(lab[['item_id', 'tone']].rename(columns={'tone': 'llm_tone'}), on='item_id')
        rows = []
        for c in ['gdelt_class', 'vader_class', 'finbert_class', 'twroberta_class', 'tfidf_lr_class']:
            if c in comp:
                sub = comp.dropna(subset=[c])
                for kind, g in [('all', sub)] + list(sub.groupby('kind')):
                    rows.append({'baseline': c, 'kind': kind, 'n': len(g), 'agreement_with_LLM': accuracy_score(g['llm_tone'], g[c].astype(int)),
                                 'macroF1_vs_LLM': f1_score(g['llm_tone'], g[c].astype(int), average='macro')})
        report.append('## Agreement with LLM tone (LLM is the reference here; human gold labels pending)\n' + pd.DataFrame(rows).round(3).to_markdown(index=False) + '\n')
items.drop(columns=['tone', 'text']).to_parquet(os.path.join(OUT, 'baseline_scores.parquet'), index=False)
report.append('## Class shares by baseline\n' + pd.DataFrame({c: items[c].value_counts(normalize=True).round(3) for c in items.columns if c.endswith('_class')}).to_markdown() + '\n')
open(os.path.join(OUT, 'baseline_report.md'), 'w').write('\n'.join(report))
print('\n'.join(report))
