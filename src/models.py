"""
models.py — Association analysis (project brief, section 4): three nested models, chronological
out-of-sample evaluation, lag selection, autocorrelation-robust inference, multiple-testing
control, content-level negativity-asymmetry tests, lead-lag / reverse-causality checks,
partisan and demographic breakdowns, and the survey-mode check.

Models (y = Michigan ICS, monthly, real-time economic regressors):
  M1  econ only:            y_t = a + b'E_t + e_t                       (E = u, pi, g; see econ_baseline.py)
  M2  + media:              y_t = a + b'E_t + c'MEDIA_t + e_t
  M3  + controls:           y_t = a + b'E_t + c'MEDIA_t + d'CONTROLS_t + e_t
Two frameworks are reported: (i) static levels, (ii) dynamic with y_{t-1} (incremental predictive
content).  OOS: expanding window, one-step-ahead, from OOS_START (default 2021-01).
Outputs: data/processed/models_summary.md, model_forecasts.csv, figures/fig4..fig8.
"""
import os, sys, warnings, itertools, datetime as dt
import numpy as np, pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import grangercausalitytests
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed'); FIG = os.path.join(ROOT, 'figures')
OOS_START = sys.argv[1] if len(sys.argv) > 1 else '2021-01'
macro = pd.read_csv(os.path.join(OUT, 'macro_monthly.csv'), index_col=0); macro.index = pd.PeriodIndex(macro.index, freq='M')
X = pd.read_csv(os.path.join(OUT, 'econ_regressors.csv'), index_col=0); X.index = pd.PeriodIndex(X.index, freq='M')
pred = pd.read_csv(os.path.join(OUT, 'econ_baseline_predictions.csv'), index_col=0); pred.index = pd.PeriodIndex(pred.index, freq='M')
media = pd.read_csv(os.path.join(OUT, 'media_monthly.csv'), index_col=0); media.index = pd.PeriodIndex(media.index, freq='M')
L = [f'# Models: association and predictive content ({dt.date.today()}; OOS from {OOS_START})\n']

# ------------------------------------------------------------------------------------------
# 1. Assemble monthly frame (2017-01 .. latest)
# ------------------------------------------------------------------------------------------
D = pd.DataFrame(index=pd.period_range('2017-01', macro.index.max(), freq='M'))
D['y'] = macro['ics']; D['y_cur'] = macro['um_current']; D['y_exp'] = macro['um_expected']
for c in ['u', 'pi', 'g']:
    D[c] = X[c]
D['gap_econ'] = pred['ics__gap']; D['yhat_econ'] = pred['ics__yhat']
MEDIA_ALL = {  # candidate media variables (name -> column); the PRIMARY pre-registered variable is llm_news_tone
    'llm_news_tone': 'LLM tone, news sample', 'llm_news_neg_share': 'LLM negative share, news', 'llm_news_emotional2_share': 'LLM alarmist-wording share',
    'llm_news_topic_prices_up': 'LLM salience: rising/high prices', 'llm_news_topic_jobs_loss': 'LLM salience: job losses', 'llm_news_topic_recession': 'LLM salience: recession',
    'llm_news_frame_level_share': 'LLM framing: price level (among price items)', 'llm_news_frame_household_share': 'LLM framing: household experience',
    'llm_news_blame_share': 'LLM political blame share', 'news_finbert_tone': 'FinBERT tone, full corpus', 'news_gdelt_tone': 'GDELT dictionary tone, full corpus',
    'news_vader_tone': 'VADER tone, full corpus', 'news_kwshare_prices': 'keyword salience: prices (full corpus)', 'llm_social_tone': 'LLM tone, Bluesky sample',
    'social_twroberta_tone': 'Twitter-RoBERTa tone, all posts'}
MIN_MONTHS = int(os.environ.get('MEDIA_MIN_MONTHS', 24))
MEDIA_ALL = {k: v for k, v in MEDIA_ALL.items() if k in media.columns and media[k].notna().sum() >= MIN_MONTHS}
if not MEDIA_ALL:
    print(f'No media variable has >= {MIN_MONTHS} months of data yet; models.py needs more labelled months (set MEDIA_MIN_MONTHS to lower the threshold).'); sys.exit(0)
for k in MEDIA_ALL:
    D[k] = media[k]
PRIMARY = 'llm_news_tone' if 'llm_news_tone' in MEDIA_ALL else ('news_finbert_tone' if 'news_finbert_tone' in MEDIA_ALL else list(MEDIA_ALL)[0])
# controls with publication-lag alignment (final data; documented limitation)
D['cum_price_3y'] = macro['cum_price_3y'].shift(1)
D['real_dpi_pc_yoy'] = macro['real_dpi_pc_yoy'].shift(2)
D['gas_price'] = macro['gasregw']
D['mortgage_pay_to_income'] = macro['mortgage_pay_to_income'].ffill().shift(1)   # latest known quarter carried forward
D['u6_u3_gap'] = macro['u6_u3_gap'].shift(1)
D['log_epu'] = np.log(macro['usepuindxm'])
D['sp500_yoy'] = macro['sp500_yoy'].shift(1)
D['debt_service'] = macro['tdsp_qlevel'].ffill().shift(6)
D['rep_president'] = ((D.index >= pd.Period('2017-02', 'M')) & (D.index <= pd.Period('2021-01', 'M')) | (D.index >= pd.Period('2025-02', 'M'))).astype(int)
D['web_mode'] = (D.index >= pd.Period('2024-07', 'M')).astype(int)
CONTROLS = ['cum_price_3y', 'real_dpi_pc_yoy', 'gas_price', 'mortgage_pay_to_income', 'u6_u3_gap', 'log_epu', 'sp500_yoy', 'rep_president', 'web_mode']
ECON = ['u', 'pi', 'g']
N_MEDIA = int(D[[c for c in MEDIA_ALL]].notna().any(axis=1).sum())
SHORT = N_MEDIA < 36
if SHORT:
    CONTROLS = ['cum_price_3y', 'real_dpi_pc_yoy', 'gas_price', 'log_epu']   # reduced set for the short media sample
HACL = 2 if SHORT else 6
D.to_csv(os.path.join(OUT, 'model_frame.csv'))
L.append(f'Media variables available (>= 24 months): {", ".join(MEDIA_ALL)}. Primary pre-specified media variable: **{PRIMARY}**.\n')

def hac(y, Xd, lags=None):
    lags = HACL if lags is None else lags
    return sm.OLS(y, sm.add_constant(Xd, has_constant='add')).fit(cov_type='HAC', cov_kwds={'maxlags': lags})

# ------------------------------------------------------------------------------------------
# 2. Lag selection for the primary media variable (static, in-sample, BIC)
# ------------------------------------------------------------------------------------------
sel = []
for lag in [0, 1, 2]:
    d = D[['y'] + ECON].copy(); d['m'] = D[PRIMARY].shift(lag); d = d.dropna()
    f = sm.OLS(d['y'], sm.add_constant(d[ECON + ['m']])).fit()
    sel.append({'lag': lag, 'n': int(f.nobs), 'BIC': f.bic, 'AIC': f.aic, 'coef_media': f.params['m']})
sel = pd.DataFrame(sel); BEST_LAG = int(sel.loc[sel['BIC'].idxmin(), 'lag'])
if SHORT:
    BEST_LAG = 0
L.append(f'Media months available: {N_MEDIA}. ' + ('**Short-sample regime** (< 36 months): contemporaneous media (lag 0), reduced control set, HAC(2); out-of-sample comparisons are skipped and all association estimates are preliminary.\n' if SHORT else '') )
L.append('## Lag selection (primary media variable, static model)\n' + sel.round(2).to_markdown(index=False) + f'\n\nLag used: {BEST_LAG}' + (' (fixed at 0 in the short-sample regime; BIC on so few months is not informative)' if SHORT else ' (selected by BIC)') + '.\n')
D['media_primary'] = D[PRIMARY].shift(BEST_LAG)

# ------------------------------------------------------------------------------------------
# 3. In-sample estimates: M1, M2, M3 (static and dynamic), HAC(6)
# ------------------------------------------------------------------------------------------
def fit_models(dyn=False, target='y'):
    d = D.copy(); d['ylag'] = d[target].shift(1)
    base = ECON + (['ylag'] if dyn else [])
    specs = {'M1 econ': base, 'M2 +media': base + ['media_primary'], 'M3 +controls': base + ['media_primary'] + CONTROLS}
    res, fits = {}, {}
    cols = sorted(set(sum(specs.values(), [])))
    dd = d[[target] + cols].dropna()
    for name, cols_ in specs.items():
        f = hac(dd[target], dd[cols_]); fits[name] = f
        res[name] = pd.Series({**{k: f'{f.params[k]:.3f} ({f.tvalues[k]:.1f})' for k in f.params.index}, 'R2': f'{f.rsquared:.3f}', 'adjR2': f'{f.rsquared_adj:.3f}', 'n': f'{int(f.nobs)}', 'resid_SD': f'{np.sqrt(f.mse_resid):.2f}'})
    return pd.DataFrame(res), fits, dd

for dyn in [False, True]:
    tab, fits, dd = fit_models(dyn)
    L.append(f'## In-sample estimates, {"dynamic (with y_t-1)" if dyn else "static levels"}, {dd.index.min()}..{dd.index.max()} — coefficient (HAC t-stat)\n' + tab.to_markdown() + '\n')

# ------------------------------------------------------------------------------------------
# 4. Out-of-sample: expanding window, one-step-ahead
# ------------------------------------------------------------------------------------------
def oos(cols, target='y', start=OOS_START, dyn=False, min_train=30):
    d = D.copy(); d['ylag'] = d[target].shift(1)
    cols = cols + (['ylag'] if dyn else [])
    dd = d[[target] + cols].dropna()
    out = []
    for t in dd.loc[start:].index:
        tr = dd.loc[:t - 1]
        if len(tr) < min_train:
            continue
        f = sm.OLS(tr[target], sm.add_constant(tr[cols])).fit()
        yh = float(f.predict(sm.add_constant(dd.loc[[t], cols], has_constant='add')).iloc[0])
        out.append({'month': t, 'y': dd.loc[t, target], 'yhat': yh})
    if not out:
        o = pd.DataFrame(columns=['y', 'yhat', 'e']); o.index.name = 'month'; return o
    o = pd.DataFrame(out).set_index('month'); o['e'] = o['y'] - o['yhat']
    return o

def dm_test(e1, e2, h=1):
    """Diebold-Mariano (squared loss), HAC variance; negative stat => model 2 better."""
    d = (e1 ** 2 - e2 ** 2).dropna()
    if len(d) < 12:
        return np.nan, np.nan
    f = sm.OLS(d, np.ones(len(d))).fit(cov_type='HAC', cov_kwds={'maxlags': max(1, int(len(d) ** (1 / 3)))})
    return float(f.tvalues.iloc[0]), float(f.pvalues.iloc[0])

def cw_test(e_small, e_big, yh_small, yh_big):
    """Clark-West (2007) adjusted MSPE test for nested models; positive => larger model better."""
    f_ = (e_small ** 2 - (e_big ** 2 - (yh_small - yh_big) ** 2)).dropna()
    if len(f_) < 12:
        return np.nan, np.nan
    f = sm.OLS(f_, np.ones(len(f_))).fit(cov_type='HAC', cov_kwds={'maxlags': max(1, int(len(f_) ** (1 / 3)))})
    return float(f.tvalues.iloc[0]), float(f.pvalues.iloc[0] / 2)

forecasts = {}
for dyn in [False, True]:
    tag = 'dynamic' if dyn else 'static'
    o1 = oos(ECON, dyn=dyn); o2 = oos(ECON + ['media_primary'], dyn=dyn); o3 = oos(ECON + ['media_primary'] + CONTROLS, dyn=dyn)
    common = o1.index.intersection(o2.index).intersection(o3.index)
    if len(common) < 12:
        L.append(f'## Out-of-sample accuracy ({tag}): fewer than 12 common OOS months available ({len(common)}); skipped.\n'); forecasts[tag] = pd.DataFrame(columns=['y', 'M1', 'M2', 'M3']); continue
    o1, o2, o3 = o1.loc[common], o2.loc[common], o3.loc[common]
    forecasts[tag] = pd.DataFrame({'y': o1['y'], 'M1': o1['yhat'], 'M2': o2['yhat'], 'M3': o3['yhat']})
    rows = []
    for name, o in [('M1 econ', o1), ('M2 +media', o2), ('M3 +controls', o3)]:
        for per, (a, b) in {'all': (common.min(), common.max()), '2021-2024': ('2021-01', '2024-12'), '2025-2026': ('2025-01', '2026-12')}.items():
            s = o.loc[a:b]
            if len(s):
                rows.append({'model': name, 'period': per, 'n': len(s), 'RMSE': np.sqrt((s['e'] ** 2).mean()), 'MAE': s['e'].abs().mean(), 'mean_error': s['e'].mean()})
    acc = pd.DataFrame(rows).pivot(index='model', columns='period', values=['RMSE', 'MAE']).round(2)
    dm21 = dm_test(o1['e'], o2['e']); dm32 = dm_test(o2['e'], o3['e']); dm31 = dm_test(o1['e'], o3['e'])
    cw21 = cw_test(o1['e'], o2['e'], o1['yhat'], o2['yhat']); cw32 = cw_test(o2['e'], o3['e'], o2['yhat'], o3['yhat'])
    L.append(f'## Out-of-sample accuracy ({tag}), expanding window from {common.min()} to {common.max()}\n' + acc.to_markdown() + '\n\n'
             f'Diebold-Mariano (HAC) M2 vs M1: t = {dm21[0]:.2f} (p = {dm21[1]:.3f}); M3 vs M2: t = {dm32[0]:.2f} (p = {dm32[1]:.3f}); M3 vs M1: t = {dm31[0]:.2f} (p = {dm31[1]:.3f}). '
             f'Negative t favours the larger model.  Clark-West (nested) M2 vs M1: t = {cw21[0]:.2f} (p = {cw21[1]:.3f}); M3 vs M2: t = {cw32[0]:.2f} (p = {cw32[1]:.3f}).\n')
fc = pd.concat(forecasts, axis=1); fc.columns = [f'{a}_{b}' for a, b in fc.columns]; fc.to_csv(os.path.join(OUT, 'model_forecasts.csv'))

# ------------------------------------------------------------------------------------------
# 4b. Two-step association: sentiment gap (from the long-sample economic model) on each media measure
# ------------------------------------------------------------------------------------------
rows = []
for k, lab in MEDIA_ALL.items():
    dd = pd.concat([D['gap_econ'].rename('gap'), D[k].rename('m')], axis=1).dropna()
    if len(dd) < 8:
        continue
    f = hac(dd['gap'], dd[['m']])
    sd = dd['m'].std()
    rows.append({'media variable': k, 'n': int(f.nobs), 'corr': dd['gap'].corr(dd['m']), 'coef (pts per 1 s.d.)': f.params['m'] * sd, 't_HAC': f.tvalues['m'], 'p': f.pvalues['m'], 'R2': f.rsquared})
gm = pd.DataFrame(rows)
if len(gm):
    p_ = gm['p'].values; order = np.argsort(p_); holm = np.empty(len(p_)); running = 0
    for rank, idx in enumerate(order):
        running = max(running, (len(p_) - rank) * p_[idx]); holm[idx] = min(1, running)
    gm['p_holm'] = holm
    L.append('## Two-step association: sentiment gap on each media measure (HAC; coefficient per one s.d. of the media measure; Holm-adjusted p across measures)\n' + gm.round(3).sort_values('p').to_markdown(index=False) + '\n')
    gm.to_csv(os.path.join(OUT, 'gap_on_media.csv'), index=False)

# ------------------------------------------------------------------------------------------
# 5. Which media variable? one-at-a-time additions to M1 with Holm correction (static + dynamic)
# ------------------------------------------------------------------------------------------
rows = []
for dyn in [False, True]:
    d = D.copy(); d['ylag'] = d['y'].shift(1)
    base = ECON + (['ylag'] if dyn else [])
    for k, lab in MEDIA_ALL.items():
        for lag in [0, 1]:
            dd = d[['y'] + base].copy(); dd['m'] = d[k].shift(lag); dd = dd.dropna()
            if len(dd) < 30:
                continue
            f = hac(dd['y'], dd[base + ['m']])
            o1 = oos(base[:3], dyn=dyn); o2 = oos(base[:3] + [k], dyn=dyn) if lag == 0 else None
            if lag == 1:
                D[f'{k}_l1'] = D[k].shift(1); o2 = oos(base[:3] + [f'{k}_l1'], dyn=dyn)
            cm = o1.index.intersection(o2.index)
            rows.append({'framework': 'dynamic' if dyn else 'static', 'variable': k, 'lag': lag, 'n': int(f.nobs), 'coef': f.params['m'], 't_HAC': f.tvalues['m'], 'p': f.pvalues['m'],
                         'R2_M1': hac(dd['y'], dd[base]).rsquared, 'R2_M2': f.rsquared,
                         'OOS_RMSE_M1': np.sqrt((o1.loc[cm, 'e'] ** 2).mean()) if len(cm) else np.nan, 'OOS_RMSE_M2': np.sqrt((o2.loc[cm, 'e'] ** 2).mean()) if len(cm) else np.nan})
mt = pd.DataFrame(rows)
if len(mt):
    for fw, g in mt.groupby('framework'):
        p = g['p'].values; order = np.argsort(p); holm = np.empty(len(p))
        m_ = len(p)
        running = 0
        for rank, idx in enumerate(order):
            running = max(running, (m_ - rank) * p[idx]); holm[idx] = min(1, running)
        mt.loc[g.index, 'p_holm'] = holm
    mt['OOS_gain_pct'] = 100 * (1 - mt['OOS_RMSE_M2'] / mt['OOS_RMSE_M1'])
    L.append('## Media variables one at a time (added to M1); Holm-adjusted p-values within framework\n' + mt.round(3).sort_values(['framework', 'p']).to_markdown(index=False) + '\n')
    mt.to_csv(os.path.join(OUT, 'media_variable_screen.csv'), index=False)

# ------------------------------------------------------------------------------------------
# 6. Content-level negativity asymmetry: media tone vs positive and negative data changes
# ------------------------------------------------------------------------------------------
A = pd.DataFrame(index=D.index)
for c in ECON:
    ch = D[c].diff()
    A[f'd{c}_pos'] = ch.clip(lower=0); A[f'd{c}_neg'] = ch.clip(upper=0)
asym_rows = []
for k in [PRIMARY, 'llm_news_neg_share', 'news_finbert_tone', 'news_gdelt_tone', 'llm_news_topic_prices_up', 'llm_news_topic_jobs_loss', 'llm_social_tone']:
    if k not in D:
        continue
    dd = pd.concat([D[k].rename('m'), A], axis=1).dropna()
    if len(dd) < 30:
        continue
    f = hac(dd['m'], dd[A.columns])
    for c in ECON:
        # H0 symmetry: coef on positive change = coef on negative change
        R = np.zeros(len(f.params)); R[list(f.params.index).index(f'd{c}_pos')] = 1; R[list(f.params.index).index(f'd{c}_neg')] = -1
        w = f.wald_test(R, use_f=False)
        asym_rows.append({'media': k, 'driver': c, 'n': int(f.nobs), 'coef_worsening': f.params[f'd{c}_pos' if c != 'g' else f'd{c}_neg'], 'coef_improving': f.params[f'd{c}_neg' if c != 'g' else f'd{c}_pos'],
                          'wald_p_symmetry': float(np.squeeze(w.pvalue))})
asym = pd.DataFrame(asym_rows)
if len(asym):
    L.append('## Content-level negativity asymmetry (monthly media measure on positive vs negative changes in real-time data)\n'
             'For u and pi, "worsening" = increase; for g, "worsening" = decrease. Symmetric response => no negativity asymmetry in coverage.\n' + asym.round(3).to_markdown(index=False) + '\n')
    asym.to_csv(os.path.join(OUT, 'asymmetry_tests.csv'), index=False)

# ------------------------------------------------------------------------------------------
# 7. Lead-lag and reverse causality
# ------------------------------------------------------------------------------------------
ll_rows = []
for k in [PRIMARY, 'news_finbert_tone', 'llm_social_tone']:
    if k not in D:
        continue
    for tgt in ['y', 'gap_econ', 'mich_news_unfavorable']:
        s = media['mich_news_unfavorable'] if tgt == 'mich_news_unfavorable' else D[tgt]
        dd = pd.concat([D[k].rename('m'), s.rename('t')], axis=1).dropna()
        if len(dd) < 30:
            continue
        xc = {lag: dd['m'].corr(dd['t'].shift(-lag)) for lag in range(-6, 7)}   # corr(media_t, target_{t+lag})
        ll_rows.append({'media': k, 'target': tgt, 'n': len(dd), **{f'lead{lag:+d}': v for lag, v in xc.items()}})
        # Granger tests on first differences, lags by BIC (max 3)
        dz = dd.diff().dropna()
        try:
            gm = grangercausalitytests(dz[['t', 'm']], maxlag=3, verbose=False)   # does m Granger-cause t?
            gr = grangercausalitytests(dz[['m', 't']], maxlag=3, verbose=False)   # does t Granger-cause m?
            ll_rows[-1]['granger_media->target_p(min over lags 1-3)'] = min(gm[l][0]['ssr_ftest'][1] for l in gm)
            ll_rows[-1]['granger_target->media_p(min over lags 1-3)'] = min(gr[l][0]['ssr_ftest'][1] for l in gr)
        except Exception:
            pass
ll = pd.DataFrame(ll_rows)
if len(ll):
    L.append('## Lead-lag cross-correlations corr(media_t, target_{t+k}) and Granger tests (first differences)\n' + ll.round(2).to_markdown(index=False) + '\n')
    ll.to_csv(os.path.join(OUT, 'leadlag.csv'), index=False)

# ------------------------------------------------------------------------------------------
# 8. Partisan, income, age, survey-mode breakdowns of the gap
# ------------------------------------------------------------------------------------------
G = pd.DataFrame(index=D.index); G['yhat'] = D['yhat_econ']
for c in ['ics_dem', 'ics_ind', 'ics_rep', 'ics_inc_bottom', 'ics_inc_middle', 'ics_inc_top', 'ics_age_18_34', 'ics_age_35_54', 'ics_age_55p']:
    G[f'gap_{c}'] = macro[c] - G['yhat']
G['gap_all'] = D['gap_econ']
per_tab = G.groupby(pd.Series(np.select([G.index < pd.Period('2021-02', 'M'), G.index < pd.Period('2025-02', 'M')], ['2017-01..2021-01 (Trump I)', '2021-02..2025-01 (Biden)'], '2025-02.. (Trump II)'), index=G.index)).mean().round(1)
L.append('## Average sentiment gap (actual minus economic-only prediction) by group and presidential period\n' + per_tab.T.to_markdown() + '\n')
mode = D[['gap_econ', 'web_mode']].dropna()
f = hac(mode['gap_econ'], mode[['web_mode']])
L.append(f'## Survey-mode check\nRegressing the gap on a web-mode dummy (2024-07 onward), 2017+: coefficient {f.params["web_mode"]:+.1f} pts (HAC t = {f.tvalues["web_mode"]:.1f}). '
         'This conflates the mode change with everything else that changed after mid-2024, so it is an upper bound on the mode effect; the Briefing Book estimate is about -9 points.\n')
G.to_csv(os.path.join(OUT, 'gap_by_group.csv'))

open(os.path.join(OUT, 'models_summary.md'), 'w').write('\n'.join(L))

# ------------------------------------------------------------------------------------------
# 9. Figures
# ------------------------------------------------------------------------------------------
f_ = forecasts['static']
if len(f_):
  idx = f_.index.to_timestamp()
  fig, ax = plt.subplots(figsize=(11, 4.5))
  ax.plot(idx, f_['y'], color='black', lw=1.8, label='Actual ICS')
  for c, col in [('M1', '#08519c'), ('M2', '#e6550d'), ('M3', '#31a354')]:
      ax.plot(idx, f_[c], lw=1.3, label={'M1': 'M1 economic only', 'M2': 'M2 + media', 'M3': 'M3 + media + controls'}[c], color=col)
  ax.set_title('One-step-ahead out-of-sample forecasts (static, expanding window)'); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig4_model_comparison.png'), dpi=160); plt.close(fig)

fig, ax1 = plt.subplots(figsize=(11, 4.5)); ax2 = ax1.twinx()
dd = D[['gap_econ', PRIMARY]].dropna(); i2 = dd.index.to_timestamp()
ax1.plot(i2, dd['gap_econ'], color='#cb181d', lw=1.6, label='Sentiment gap (left)'); ax2.plot(i2, dd[PRIMARY], color='#08519c', lw=1.3, label=f'{PRIMARY} (right)')
ax1.set_ylabel('gap, index points'); ax2.set_ylabel('media tone'); ax1.axhline(0, color='grey', lw=0.6)
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels(); ax1.legend(h1 + h2, l1 + l2, fontsize=8, loc='lower left')
ax1.set_title('Sentiment gap and media tone'); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig5_media_vs_gap.png'), dpi=160); plt.close(fig)

if len(asym):
    a = asym[asym['media'] == PRIMARY]
    fig, ax = plt.subplots(figsize=(7, 3.6)); xx = np.arange(len(a))
    ax.bar(xx - 0.2, a['coef_worsening'], 0.4, label='response to worsening data', color='#cb181d'); ax.bar(xx + 0.2, a['coef_improving'], 0.4, label='response to improving data', color='#238b45')
    ax.set_xticks(xx); ax.set_xticklabels([{'u': 'unemployment', 'pi': 'inflation', 'g': 'GDP growth'}[d] for d in a['driver']]); ax.axhline(0, color='black', lw=0.7)
    ax.set_title(f'Asymmetry of {PRIMARY} to data changes (p-values for symmetry: ' + ', '.join(f'{p:.2f}' for p in a['wald_p_symmetry']) + ')', fontsize=9); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig6_asymmetry.png'), dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 4.5)); gi = G.index.to_timestamp()
for c, col in [('gap_ics_dem', '#2166ac'), ('gap_ics_ind', '#7f7f7f'), ('gap_ics_rep', '#b2182b'), ('gap_all', 'black')]:
    ax.plot(gi, G[c], color=col, lw=1.4 if c != 'gap_all' else 2, label=c.replace('gap_ics_', '').replace('gap_', '').upper())
for x in ['2017-01-20', '2021-01-20', '2025-01-20']:
    ax.axvline(pd.Timestamp(x), color='grey', ls=':', lw=1)
ax.axhline(0, color='grey', lw=0.6); ax.set_title('Sentiment gap by party identification (same economic-only prediction)'); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig7_partisan.png'), dpi=160); plt.close(fig)

if len(ll):
    r = ll[(ll['media'] == PRIMARY) & (ll['target'] == 'y')]
    if len(r):
        fig, ax = plt.subplots(figsize=(7, 3.4)); lags = list(range(-6, 7))
        ax.bar(lags, [r.iloc[0][f'lead{l:+d}'] for l in lags], color='#6baed6'); ax.axhline(0, color='black', lw=0.7)
        ax.set_xlabel('k (months): corr(media_t, ICS_{t+k}); k>0 media leads'); ax.set_title('Lead-lag correlation, media tone vs ICS'); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig8_leadlag.png'), dpi=160); plt.close(fig)
print('\n'.join(L))
