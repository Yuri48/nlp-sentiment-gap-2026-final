"""
build_dashboard.py — Updateable monitoring dashboard (project brief, section 5).

Reads the processed outputs and writes dashboard/index.html (self-contained; plotly.js embedded).
Re-run the pipeline (run_all.sh) and this script whenever new data arrive; everything on the page is
generated from data/processed/*.csv, nothing is hard-coded.
Panels: 1 sentiment vs economic-model prediction with uncertainty; 2 sentiment gap (overall and by
party); 3 media tone / salience / framing / calibration; 4 economic releases, real-time indicators and
events; 5 source composition, missingness and model performance.
"""
import os, json, datetime as dt
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed'); DASH = os.path.join(ROOT, 'dashboard'); os.makedirs(DASH, exist_ok=True)
def rd(fn, period=True):
    p = os.path.join(OUT, fn)
    if not os.path.exists(p):
        return pd.DataFrame()
    d = pd.read_csv(p, index_col=0)
    if period:
        d.index = pd.PeriodIndex(d.index, freq='M').to_timestamp()
    return d
macro = rd('macro_monthly.csv'); pred = rd('econ_baseline_predictions.csv'); media = rd('media_monthly.csv'); fc = rd('model_forecasts.csv'); gaps = rd('gap_by_group.csv')
rt = rd('realtime_panel.csv'); events = pd.read_csv(os.path.join(ROOT, 'data', 'raw', 'events_timeline.csv'))
news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))
START = pd.Timestamp('2017-01-01'); CUTOFF = dt.date.today().isoformat()
figs = {}
C = {'actual': '#111111', 'model': '#1f77b4', 'band': 'rgba(31,119,180,0.18)', 'neg': '#d62728', 'pos': '#2ca02c', 'grey': '#888888'}

# ---- Panel 1: sentiment vs prediction ----------------------------------------------------
p = pred.loc[START:]
f = go.Figure()
f.add_trace(go.Scatter(x=p.index, y=p['ics__emp95_hi'], line=dict(width=0), showlegend=False, hoverinfo='skip'))
f.add_trace(go.Scatter(x=p.index, y=p['ics__emp95_lo'], fill='tonexty', fillcolor='rgba(31,119,180,0.12)', line=dict(width=0), name='95% empirical PI'))
f.add_trace(go.Scatter(x=p.index, y=p['ics__emp80_hi'], line=dict(width=0), showlegend=False, hoverinfo='skip'))
f.add_trace(go.Scatter(x=p.index, y=p['ics__emp80_lo'], fill='tonexty', fillcolor=C['band'], line=dict(width=0), name='80% empirical PI'))
f.add_trace(go.Scatter(x=p.index, y=p['ics__yhat'], name='Economic-only model (real-time, OOS)', line=dict(color=C['model'], width=2)))
f.add_trace(go.Scatter(x=p.index, y=p['ics__y'], name='Michigan ICS', line=dict(color=C['actual'], width=2.5)))
m_ = macro.loc[START:]
f.add_trace(go.Scatter(x=m_.index, y=m_['um_current'], name='Current conditions', line=dict(color='#9467bd', width=1, dash='dot'), visible='legendonly'))
f.add_trace(go.Scatter(x=m_.index, y=m_['um_expected'], name='Expectations', line=dict(color='#ff7f0e', width=1, dash='dot'), visible='legendonly'))
f.add_vline(x=pd.Timestamp('2024-07-01'), line=dict(color=C['grey'], dash='dot')); f.add_annotation(x=pd.Timestamp('2024-07-01'), y=1, yref='paper', text='web-only survey', showarrow=False, font=dict(size=10, color=C['grey']), xanchor='left')
f.add_vline(x=pd.Timestamp('2026-11-03'), line=dict(color='#aaa', dash='dash')); f.add_annotation(x=pd.Timestamp('2026-11-03'), y=0.02, yref='paper', text='midterms', showarrow=False, font=dict(size=10, color=C['grey']), xanchor='right')
f.update_layout(title='1. Consumer sentiment and its economic-model prediction (with uncertainty)', height=420, legend=dict(orientation='h', y=-0.15), margin=dict(l=40, r=20, t=50, b=40), yaxis_title='Index (1966Q1 = 100)')
figs['p1'] = f

# ---- Panel 2: the gap --------------------------------------------------------------------
f = go.Figure()
f.add_trace(go.Bar(x=p.index, y=p['ics__gap'], name='Gap: ICS − prediction', marker_color=np.where(p['ics__gap'] < 0, C['neg'], C['pos'])))
if len(gaps):
    g_ = gaps.loc[START:]
    for c, col, nm in [('gap_ics_dem', '#2166ac', 'Democrats'), ('gap_ics_ind', '#7f7f7f', 'Independents'), ('gap_ics_rep', '#b2182b', 'Republicans')]:
        if c in g_:
            f.add_trace(go.Scatter(x=g_.index, y=g_[c], name=f'Gap, {nm}', line=dict(color=col, width=1.5), visible='legendonly'))
    for c, nm in [('gap_ics_inc_bottom', 'Bottom income tercile'), ('gap_ics_inc_top', 'Top income tercile'), ('gap_ics_age_18_34', 'Age 18-34'), ('gap_ics_age_55p', 'Age 55+')]:
        if c in g_:
            f.add_trace(go.Scatter(x=g_.index, y=g_[c], name=f'Gap, {nm}', line=dict(width=1, dash='dot'), visible='legendonly'))
f.add_hline(y=0, line=dict(color='black', width=1))
f.update_layout(title='2. Sentiment gap (unexplained by unemployment, inflation and GDP) — click legend for party / income / age', height=380, legend=dict(orientation='h', y=-0.2), margin=dict(l=40, r=20, t=50, b=40), yaxis_title='index points')
figs['p2'] = f

# ---- Panel 3: media measures --------------------------------------------------------------
md = media.loc[START:] if len(media) else pd.DataFrame()
f = make_subplots(rows=2, cols=2, subplot_titles=('Tone (−1..+1): LLM sample vs baselines', 'Salience: share of headlines by topic (LLM)', 'Framing shares (LLM)', 'Factual calibration and alarmist wording'), vertical_spacing=0.14, horizontal_spacing=0.08)
def add(col, name, r, c, **kw):
    if len(md) and col in md and md[col].notna().any():
        f.add_trace(go.Scatter(x=md.index, y=md[col], name=name, mode='lines+markers', marker=dict(size=4), **kw), row=r, col=c)
add('llm_news_tone', 'LLM news tone', 1, 1, line=dict(color=C['model'], width=2))
add('llm_social_tone', 'LLM Bluesky tone', 1, 1, line=dict(color='#17becf', width=1.5))
add('news_finbert_tone', 'FinBERT (full corpus)', 1, 1, line=dict(color='#ff7f0e', width=1, dash='dot'))
add('news_gdelt_tone', 'GDELT tone/5 (full corpus)', 1, 1, line=dict(color='#7f7f7f', width=1, dash='dot'))
if len(md) and 'news_gdelt_tone' in md:
    f.data[-1].y = md['news_gdelt_tone'] / 5
for t, col in [('prices_up', C['neg']), ('prices_down', C['pos']), ('jobs_loss', '#e377c2'), ('jobs_gain', '#bcbd22'), ('recession', '#8c564b'), ('tariffs_trade', '#9467bd'), ('rates', '#17becf')]:
    add(f'llm_news_topic_{t}', t, 1, 2, line=dict(color=col, width=1.5), stackgroup=None)
add('llm_news_frame_level_share', 'price LEVEL (among price items)', 2, 1, line=dict(color=C['neg'], width=2))
add('llm_news_frame_household_share', 'household experience', 2, 1, line=dict(color='#9467bd', width=1.5))
add('llm_news_frame_forecast_share', 'forecast / expectations', 2, 1, line=dict(color='#8c564b', width=1.5))
add('news_claims_accurate_share', 'numeric claims accurate', 2, 2, line=dict(color=C['pos'], width=2))
add('news_claims_wrong_share', 'numeric claims wrong', 2, 2, line=dict(color=C['neg'], width=1.5))
add('llm_news_emotional2_share', 'alarmist wording share', 2, 2, line=dict(color='#ff7f0e', width=1.5))
add('llm_news_blame_share', 'political blame share', 2, 2, line=dict(color='#7f7f7f', width=1.5))
f.update_layout(title='3. Media measures (LLM-labelled sample; baselines on the full corpus)', height=640, margin=dict(l=40, r=20, t=70, b=40), legend=dict(orientation='h', y=-0.08, font=dict(size=10)))
figs['p3'] = f

# ---- Panel 4: releases, real-time indicators, events --------------------------------------
r_ = rt.loc[START:] if len(rt) else pd.DataFrame()
f = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06, subplot_titles=('Unemployment rate as known on the 15th (ALFRED vintage)', 'Headline PCE inflation y/y as known on the 15th', 'Latest quarterly real GDP growth (q/q ann.) as known on the 15th'))
if len(r_):
    f.add_trace(go.Scatter(x=r_.index, y=r_['unrate_rt'], name='unemployment (real-time)', line=dict(color=C['model'])), row=1, col=1)
    f.add_trace(go.Scatter(x=r_.index, y=r_['pce_yoy_rt'], name='PCE inflation (real-time)', line=dict(color=C['neg'])), row=2, col=1)
    f.add_trace(go.Scatter(x=r_.index, y=r_['gdp_qoq_ann_rt'], name='GDP growth (real-time)', line=dict(color=C['pos'])), row=3, col=1)
    f.add_trace(go.Scatter(x=m_.index, y=m_['core_pce_yoy'], name='core PCE (course spreadsheet)', line=dict(color='#ff7f0e', dash='dot', width=1)), row=2, col=1)
ev = events.copy(); ev['date'] = pd.to_datetime(ev['date'])
ev = ev[ev['date'] >= START]
for _, e in ev.iterrows():
    f.add_vline(x=e['date'], line=dict(color='rgba(0,0,0,0.25)', width=1, dash='dot'))
f.add_trace(go.Scatter(x=ev['date'], y=[float(r_['unrate_rt'].max()) if len(r_) else 1.0] * len(ev), mode='markers', marker=dict(symbol='triangle-down', size=9, color='#444'),
                       text=[f"{d.date()} [{c}] {t}" for d, c, t in zip(ev['date'], ev['category'], ev['event'])], hoverinfo='text', name='events (hover)'), row=1, col=1)
f.update_layout(title='4. Economic releases, real-time indicator values and major events (hover the markers)', height=620, margin=dict(l=40, r=20, t=70, b=40), legend=dict(orientation='h', y=-0.06, font=dict(size=10)))
figs['p4'] = f

# ---- Panel 5: composition, missingness, performance ---------------------------------------
nk = news[(news['kw_title']) & (news['source_type'] != 'foreign')]
comp = nk.groupby([pd.to_datetime(nk['month']).dt.to_period('M').dt.to_timestamp(), 'source_type']).size().unstack(fill_value=0)
f = make_subplots(rows=1, cols=3, subplot_titles=('Headline supply by source type (unique, keyword-relevant)', 'Labelled items per month and share relevant', 'Rolling 12-month OOS RMSE by model'), horizontal_spacing=0.07)
for st in ['national', 'local', 'national_other', 'local_other', 'other']:
    if st in comp:
        f.add_trace(go.Bar(x=comp.index, y=comp[st], name=st), row=1, col=1)
if len(md) and 'llm_news_n_labelled' in md:
    f.add_trace(go.Bar(x=md.index, y=md['llm_news_n_labelled'], name='news labelled', marker_color=C['model']), row=1, col=2)
    if 'llm_social_n_labelled' in md:
        f.add_trace(go.Bar(x=md.index, y=md['llm_social_n_labelled'], name='posts labelled', marker_color='#17becf'), row=1, col=2)
    f.add_trace(go.Scatter(x=md.index, y=md['llm_news_share_relevant'] * md['llm_news_n_labelled'].max(), name='share relevant (scaled)', line=dict(color='#ff7f0e')), row=1, col=2)
if len(fc):
    for mdl, col in [('static_M1', C['model']), ('static_M2', '#ff7f0e'), ('static_M3', C['pos'])]:
        if mdl in fc:
            e = (fc['static_y'] - fc[mdl]) ** 2
            f.add_trace(go.Scatter(x=fc.index, y=np.sqrt(e.rolling(12).mean()), name=mdl.replace('static_', '') + {'M1': ' econ', 'M2': ' +media', 'M3': ' +controls'}[mdl[-2:]], line=dict(color=col)), row=1, col=3)
f.update_layout(barmode='stack', title='5. Source composition, labelling coverage / missingness, and model performance', height=400, margin=dict(l=40, r=20, t=70, b=40), legend=dict(orientation='h', y=-0.2, font=dict(size=10)))
figs['p5'] = f

# ---- Status table ------------------------------------------------------------------------
last_ics = macro['ics'].dropna(); last_gap = pred['ics__gap'].dropna()
status = {
    'Data cutoff': CUTOFF, 'Latest ICS': f'{last_ics.iloc[-1]:.1f} ({last_ics.index[-1]:%b %Y}, preliminary if current month)',
    'Economic-model prediction': f'{pred["ics__yhat"].dropna().iloc[-1]:.1f} (80% PI {pred["ics__emp80_lo"].dropna().iloc[-1]:.0f}–{pred["ics__emp80_hi"].dropna().iloc[-1]:.0f})',
    'Sentiment gap': f'{last_gap.iloc[-1]:+.1f} pts ({last_gap.index[-1]:%b %Y}); 12-month mean {last_gap.iloc[-12:].mean():+.1f}',
    'LLM news tone, latest month': (f'{media["llm_news_tone"].dropna().iloc[-1]:+.2f} ({media["llm_news_tone"].dropna().index[-1]:%b %Y}, n={int(media["llm_news_n_relevant"].dropna().iloc[-1])})' if len(media) and 'llm_news_tone' in media and media['llm_news_tone'].notna().any() else 'pending'),
    'Headlines in corpus': f'{len(news):,} unique ({news["month"].min()} to {news["month"].max()})',
    'Next scheduled inputs': 'Michigan final Oct (Oct 23); FOMC (Oct 28); BEA Q3 GDP advance + Sept PCE (Oct 29); Oct jobs report (Nov 6); election Nov 3',
}
rows = ''.join(f'<tr><th>{k}</th><td>{v}</td></tr>' for k, v in status.items())
html_parts = [pio.to_html(figs[k], include_plotlyjs=(k == 'p1'), full_html=False, config={'displaylogo': False}) for k in ['p1', 'p2', 'p3', 'p4', 'p5']]
page = f"""<!doctype html><html><head><meta charset='utf-8'><title>Sentiment gap monitor</title>
<style>body{{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0 auto;max-width:1250px;padding:16px;color:#222}}
h1{{font-size:22px;margin:4px 0}} .sub{{color:#666;font-size:13px;margin-bottom:12px}} table.status{{border-collapse:collapse;font-size:13px;margin-bottom:14px}}
table.status th{{text-align:left;padding:3px 10px 3px 0;color:#444;white-space:nowrap}} table.status td{{padding:3px 0}} .note{{font-size:12px;color:#555;background:#f6f6f6;padding:8px;border-radius:6px;margin:10px 0}}</style></head><body>
<h1>Consumer sentiment, economic fundamentals and economic news — pre-election monitor</h1>
<div class='sub'>Generated {dt.datetime.now():%Y-%m-%d %H:%M} by <code>src/build_dashboard.py</code>. Everything is computed from <code>data/processed/</code>; re-run <code>run_all.sh</code> to update after new releases.</div>
<table class='status'>{rows}</table>
<div class='note'><b>Reading guide.</b> The gap is actual sentiment minus the out-of-sample prediction of an economic-only model (unemployment, headline PCE inflation, real GDP growth, all as known on the 15th of each month). A negative gap is unexplained pessimism under that model — not evidence of perceptual bias by itself. Media measures are content-supply measures (what was published), not exposure. Michigan moved to web-only interviewing in July 2024; an independent estimate puts the level effect near −9 points.</div>
{''.join(html_parts)}
<div class='note'><b>Update plan.</b> After each Michigan release: (1) add the new ICS/components to <code>data/raw/michigan/manual_additions.csv</code> or refresh the archive tables, (2) run the collectors for the new weeks, (3) run <code>run_all.sh</code>. The prediction for month t uses only data published by the 15th of t; GDP enters only when the BEA advance estimate is out (Q3 2026: Oct 29).</div>
</body></html>"""
open(os.path.join(DASH, 'index.html'), 'w', encoding='utf-8').write(page)
print('dashboard written:', os.path.join(DASH, 'index.html'), f'{os.path.getsize(os.path.join(DASH, "index.html"))/1e6:.1f} MB')
