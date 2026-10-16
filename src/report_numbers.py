"""
report_numbers.py — Pull the key numbers used in the report, slides and dashboard from the processed
outputs into one place (data/processed/key_numbers.md), so every quoted figure is traceable.
"""
import os, json, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed')
def rd(fn):
    p = os.path.join(OUT, fn)
    if not os.path.exists(p):
        return pd.DataFrame()
    d = pd.read_csv(p, index_col=0); d.index = pd.PeriodIndex(d.index, freq='M'); return d
L = [f'# Key numbers ({dt.datetime.now():%Y-%m-%d %H:%M})\n']
macro = rd('macro_monthly.csv'); pred = rd('econ_baseline_predictions.csv'); media = rd('media_monthly.csv'); rt = rd('realtime_panel.csv')
# --- baseline / gap ---
g = pred['ics__gap']
L.append('## Economic baseline and gap')
for per, (a, b) in {'2010-2019': ('2010-01', '2019-12'), '2022-2024': ('2022-01', '2024-12'), '2025': ('2025-01', '2025-12'), '2026 (Jan-Oct)': ('2026-01', '2026-10')}.items():
    s = g.loc[a:b]
    L.append(f'* gap {per}: mean {s.mean():+.1f}, RMSE {np.sqrt((s**2).mean()):.1f}, min {s.min():+.1f} ({s.idxmin()})')
last = pred.dropna(subset=['ics__yhat']).iloc[-1]
L.append(f'* latest month {pred.dropna(subset=["ics__yhat"]).index[-1]}: ICS {last["ics__y"]:.1f}, prediction {last["ics__yhat"]:.1f}, empirical 80% PI [{last["emp80_lo" if "emp80_lo" in last else "ics__emp80_lo"]:.1f}, {last["ics__emp80_hi"]:.1f}], gap {last["ics__gap"]:+.1f}')
for c in ['um_current', 'um_expected']:
    s = pred[f'{c}__gap'].loc['2026-01':]
    L.append(f'* {c} gap 2026 mean {s.mean():+.1f}')
L.append(f'* macro Oct-2026 real-time: u={rt["unrate_rt"].iloc[-1]:.1f} (ref {rt["unrate_ref"].iloc[-1]}), pce={rt["pce_yoy_rt"].iloc[-1]:.2f} (ref {rt["pce_ref"].iloc[-1]}), gdp={rt["gdp_qoq_ann_rt"].iloc[-1]:.1f} ({rt["gdp_ref_q"].iloc[-1]})')
L.append(f'* cum_price_since_2020 latest {macro["cum_price_since_2020"].dropna().iloc[-1]:.1f}%; cum_price_3y {macro["cum_price_3y"].dropna().iloc[-1]:.1f}%; real DPI pc yoy {macro["real_dpi_pc_yoy"].dropna().iloc[-1]:.1f}%; gas {macro["gasregw"].dropna().iloc[-1]:.2f}; mortgage {macro["mortgage30us"].dropna().iloc[-1]:.2f}; mich 1y exp {macro["mich"].dropna().iloc[-1]:.1f}')
L.append(f'* ICS by party latest ({macro["ics_dem"].dropna().index[-1]}): Dem {macro["ics_dem"].dropna().iloc[-1]:.1f}, Ind {macro["ics_ind"].dropna().iloc[-1]:.1f}, Rep {macro["ics_rep"].dropna().iloc[-1]:.1f}; income bottom/top {macro["ics_inc_bottom"].dropna().iloc[-1]:.1f}/{macro["ics_inc_top"].dropna().iloc[-1]:.1f}')
L.append(f'* Michigan news heard, latest ({macro["news_unfavorable"].dropna().index[-1]}): unfavorable {macro["news_unfavorable"].dropna().iloc[-1]:.0f}%, favorable {macro["news_favorable"].dropna().iloc[-1]:.0f}%; high-price item {macro["newsu_highprice"].dropna().iloc[-1]:.0f}%, unemployment item {macro["newsu_unemp"].dropna().iloc[-1]:.0f}%; govt policy poor {macro["govpol_poor"].dropna().iloc[-1]:.0f}%')
# --- corpus ---
if os.path.exists(os.path.join(OUT, 'corpus_summary.md')):
    cs = open(os.path.join(OUT, 'corpus_summary.md')).read().splitlines()
    L.append('## Corpus\n' + '\n'.join(l for l in cs if l.startswith('* ')))
lab = pd.read_parquet(os.path.join(OUT, 'labels_llm.parquet')) if os.path.exists(os.path.join(OUT, 'labels_llm.parquet')) else pd.DataFrame()
if len(lab):
    L.append(f'## LLM labels\n* labelled items {len(lab)} (news {(lab.kind=="news").sum()}, social {(lab.kind=="social").sum()}); months {lab.month.min()}..{lab.month.max()}')
    rel = lab[lab.relevant == 1]
    for k, gk in rel.groupby('kind'):
        L.append(f'* {k}: relevant share {lab[lab.kind==k].relevant.mean():.2f}; tone mean {gk.tone.mean():+.2f}; neg {(gk.tone==-1).mean():.2f} / neu {(gk.tone==0).mean():.2f} / pos {(gk.tone==1).mean():.2f}; alarmist (emotional=2) {(gk.emotional==2).mean():.2f}; '
                 f'household frame {gk.frame_scope.isin(["household","both"]).mean():.2f}; forecast frame {gk.frame_time.isin(["forecast","both"]).mean():.2f}; numeric claims {gk.numeric_claim.mean():.2f}; blame {(gk.attribution_valence=="blame").mean():.2f}')
        pr = gk[gk.topics.str.contains('prices_up|prices_down')]
        L.append(f'  - price items: {len(pr)}; level framing {pr.frame_level_rate.isin(["level","both"]).mean():.2f}; rate framing {pr.frame_level_rate.isin(["rate","both"]).mean():.2f}; prices_up share of all {gk.topics.str.contains("prices_up").mean():.2f} vs prices_down {gk.topics.str.contains("prices_down").mean():.2f}; jobs_loss {gk.topics.str.contains("jobs_loss").mean():.2f} vs jobs_gain {gk.topics.str.contains("jobs_gain").mean():.2f}; recession {gk.topics.str.contains("recession").mean():.2f}; tariffs {gk.topics.str.contains("tariffs_trade").mean():.2f}')
        bl = gk[gk.attribution_valence == 'blame'].attribution_actor.value_counts(normalize=True).round(2).to_dict()
        cr = gk[gk.attribution_valence == 'credit'].attribution_actor.value_counts(normalize=True).round(2).to_dict()
        L.append(f'  - blame by actor {bl}; credit by actor {cr}')
    if 'news' in set(lab.kind):
        news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))[['item_id', 'source_type', 'source_lean']]
        rn = rel[rel.kind == 'news'].merge(news, on='item_id')
        L.append('* news tone by source type: ' + rn.groupby('source_type').tone.agg(['mean', 'count']).round(2).to_dict('index').__str__())
        L.append('* news tone by lean: ' + rn.groupby('source_lean').tone.agg(['mean', 'count']).round(2).to_dict('index').__str__())
        L.append('* blame Trump admin by lean: ' + rn.assign(bt=(rn.attribution_actor == 'trump_admin') & (rn.attribution_valence == 'blame')).groupby('source_lean').bt.mean().round(3).to_dict().__str__())
        L.append('* credit Trump admin by lean: ' + rn.assign(ct=(rn.attribution_actor == 'trump_admin') & (rn.attribution_valence == 'credit')).groupby('source_lean').ct.mean().round(3).to_dict().__str__())
if len(media):
    cols = [c for c in ['llm_news_tone', 'llm_news_neg_share', 'llm_social_tone', 'news_finbert_tone', 'news_gdelt_tone', 'news_n_kw', 'news_claims_accurate_share', 'news_claims_n', 'llm_news_frame_level_share', 'llm_news_topic_prices_up', 'llm_news_emotional2_share', 'mich_news_unfavorable'] if c in media]
    L.append('## Media monthly (last 12 months)\n' + media[cols].tail(12).round(3).to_markdown())
    cl = pd.read_csv(os.path.join(OUT, 'claims_checked.csv')) if os.path.exists(os.path.join(OUT, 'claims_checked.csv')) else pd.DataFrame()
    if len(cl):
        L.append('* claims status: ' + cl.status.value_counts().to_dict().__str__() + '; by indicator: ' + cl.groupby('indicator').status.apply(lambda s: (s == 'accurate').mean()).round(2).to_dict().__str__())
        L.append('* claims accuracy by source type: ' + cl[cl.status != 'unverifiable'].groupby('source_type').status.apply(lambda s: (s == 'accurate').mean()).round(2).to_dict().__str__())
for fn in ['baseline_report.md', 'perturbation_report.md', 'models_summary.md']:
    p = os.path.join(OUT, fn)
    if os.path.exists(p):
        L.append(f'## {fn}\n' + open(p).read())
open(os.path.join(OUT, 'key_numbers.md'), 'w').write('\n'.join(L))
print('\n'.join(L[:40]))
