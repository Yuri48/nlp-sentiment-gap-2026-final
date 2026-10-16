"""
econ_baseline.py — Economic-only model of consumer sentiment and the sentiment gap.

Model (levels, static):  ICS_t = a + b1*U_t^rt + b2*pi_t^rt + b3*g_t^rt + e_t
  U_t^rt  = latest unemployment rate known on the 15th of month t (normally month t-1)
  pi_t^rt = latest headline PCE inflation, y/y, known on the 15th of t (normally month t-2)
  g_t^rt  = latest quarterly real GDP growth (q/q annualised) known on the 15th of t
For 2009-02 onward these come from ALFRED vintages (true real time); before that from final
data with the same publication lags ("pseudo real time").  Quarterly GDP is never interpolated.

Outputs (data/processed/):
  econ_baseline_predictions.csv  actual, expanding-window OOS prediction (2010-01..), parametric
                                 and empirical 80/95% prediction intervals, gap, standardised gap
  econ_baseline_coefs.csv        coefficient paths (expanding and 15-year rolling windows)
  econ_baseline_summary.md       estimates, fit, OOS accuracy by period, gap decomposition
  figures/fig1_ics_vs_model.png, fig2_gap.png, fig3_coef_stability.png
"""
import os, warnings, datetime as dt
import numpy as np, pandas as pd
import statsmodels.api as sm
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed'); FIG = os.path.join(ROOT, 'figures')
os.makedirs(FIG, exist_ok=True)
m = pd.read_csv(os.path.join(OUT, 'macro_monthly.csv'), index_col=0); m.index = pd.PeriodIndex(m.index, freq='M')
rt = pd.read_csv(os.path.join(OUT, 'realtime_panel.csv'), index_col=0); rt.index = pd.PeriodIndex(rt.index, freq='M')

# --- regressors ---------------------------------------------------------------------
X = pd.DataFrame(index=m.index)
X['u_pseudo'] = m['unrate'].shift(1)                      # month t-1 value, released first Friday of t
X['pi_pseudo'] = m['pce_yoy_fred'].shift(2)               # headline PCE y/y for t-2 (released end of t-1)
X['pi_core_pseudo'] = m['pce_yoy'].shift(2)               # course spreadsheet series (= core PCE y/y)
X['g_pseudo'] = m['gdp_qoq_ann_q'].shift(2).ffill()       # latest quarter whose end-month <= t-2 (advance estimate out)
X['u_rt'] = rt['unrate_rt']; X['pi_rt'] = rt['pce_yoy_rt']; X['g_rt'] = rt['gdp_qoq_ann_rt']
X['u'] = X['u_rt'].where(X['u_rt'].notna(), X['u_pseudo'])
X['pi'] = X['pi_rt'].where(X['pi_rt'].notna(), X['pi_pseudo'])
X['g'] = X['g_rt'].where(X['g_rt'].notna(), X['g_pseudo'])
X['realtime'] = X['u_rt'].notna()
X.to_csv(os.path.join(OUT, 'econ_regressors.csv'))
REG = ['u', 'pi', 'g']
TARGETS = {'ics': 'Index of Consumer Sentiment', 'um_current': 'Current Economic Conditions', 'um_expected': 'Consumer Expectations'}
lines = [f'# Economic-only baseline (econ_baseline.py, {dt.date.today()})\n']
preds_all = {}

def hac_fit(y, Xd, lags=12):
    Xc = sm.add_constant(Xd)
    return sm.OLS(y, Xc).fit(cov_type='HAC', cov_kwds={'maxlags': lags})

for tgt, name in TARGETS.items():
    d = pd.concat([m[tgt].rename('y'), X[REG]], axis=1).dropna()
    d = d['1978-01':]
    # (a) full-sample and pre-2020 in-sample fits
    full = hac_fit(d['y'], d[REG])
    pre = hac_fit(d.loc[:'2019-12', 'y'], d.loc[:'2019-12', REG])
    lines.append(f'\n## {name} ({tgt})\n\n### In-sample estimates (HAC, 12 lags)\n')
    tab = pd.DataFrame({'coef_1978-2026': full.params, 'se': full.bse, 'coef_1978-2019': pre.params, 'se_pre': pre.bse}).round(3)
    lines.append(tab.to_markdown() + f'\n\nR² full sample = {full.rsquared:.3f} (n={int(full.nobs)}); R² 1978-2019 = {pre.rsquared:.3f}; residual SD = {np.sqrt(full.mse_resid):.2f} / {np.sqrt(pre.mse_resid):.2f}\n')
    # (b) fixed pre-2020 coefficients projected forward
    d['yhat_pre2020'] = pre.predict(sm.add_constant(d[REG]))
    # (c) expanding-window real-time OOS from 2010-01
    rows = []
    for t in d.loc['2010-01':].index:
        train = d.loc[:t - 1]
        fit = sm.OLS(train['y'], sm.add_constant(train[REG])).fit()
        xt = sm.add_constant(d.loc[[t], REG], has_constant='add')
        pr = fit.get_prediction(xt)
        sf = pr.summary_frame(alpha=0.05); sf80 = pr.summary_frame(alpha=0.20)
        rows.append({'month': t, 'y': d.loc[t, 'y'], 'yhat': float(sf['mean'].iloc[0]),
                     'pi95_lo': float(sf['obs_ci_lower'].iloc[0]), 'pi95_hi': float(sf['obs_ci_upper'].iloc[0]),
                     'pi80_lo': float(sf80['obs_ci_lower'].iloc[0]), 'pi80_hi': float(sf80['obs_ci_upper'].iloc[0]),
                     'b_const': fit.params['const'], 'b_u': fit.params['u'], 'b_pi': fit.params['pi'], 'b_g': fit.params['g'], 'n_train': int(fit.nobs)})
    p = pd.DataFrame(rows).set_index('month')
    p['gap'] = p['y'] - p['yhat']
    # empirical intervals from past OOS errors (expanding, needs >= 24 errors)
    e = p['gap']
    p['emp80_lo'] = p['yhat'] + e.expanding(24).quantile(0.10).shift(1); p['emp80_hi'] = p['yhat'] + e.expanding(24).quantile(0.90).shift(1)
    p['emp95_lo'] = p['yhat'] + e.expanding(24).quantile(0.025).shift(1); p['emp95_hi'] = p['yhat'] + e.expanding(24).quantile(0.975).shift(1)
    p['gap_z'] = p['gap'] / e.expanding(24).std().shift(1)
    p['yhat_pre2020'] = d['yhat_pre2020']; p['gap_pre2020'] = p['y'] - p['yhat_pre2020']
    p['realtime'] = X.loc[p.index, 'realtime']
    preds_all[tgt] = p
    # accuracy
    def acc(s):
        return pd.Series({'RMSE': np.sqrt((s['gap'] ** 2).mean()), 'MAE': s['gap'].abs().mean(), 'mean_gap': s['gap'].mean(), 'n': len(s)})
    per = pd.DataFrame({'2010-2019': acc(p.loc['2010-01':'2019-12']), '2020-2021': acc(p.loc['2020-01':'2021-12']),
                        '2022-2024': acc(p.loc['2022-01':'2024-12']), '2025-2026': acc(p.loc['2025-01':]), 'all 2010-2026': acc(p)}).T.round(2)
    lines.append('\n### Out-of-sample accuracy (expanding window, real-time regressors)\n' + per.to_markdown() + '\n')
    cover = ((p['y'] >= p['pi95_lo']) & (p['y'] <= p['pi95_hi'])).mean()
    cover80 = ((p['y'] >= p['pi80_lo']) & (p['y'] <= p['pi80_hi'])).mean()
    lines.append(f'\nCoverage of parametric 95% / 80% prediction intervals 2010-2026: {cover:.2f} / {cover80:.2f} (nominal 0.95 / 0.80); '
                 f'intervals are too narrow because errors are strongly autocorrelated (AR(1) of gap = {e.autocorr():.2f}); empirical intervals are also reported.\n')
    # gap decomposition 2022-2026: raw deviation from 1978-2019 mean, explained by each regressor
    mu = d.loc[:'2019-12', ['y'] + REG].mean()
    for per_name, (a, b) in {'2022-2023': ('2022-01', '2023-12'), '2024': ('2024-01', '2024-12'), '2025': ('2025-01', '2025-12'), '2026 (Jan-Oct)': ('2026-01', '2026-10')}.items():
        seg = d.loc[a:b]
        if not len(seg):
            continue
        raw = seg['y'].mean() - mu['y']
        contrib = {r: pre.params[r] * (seg[r].mean() - mu[r]) for r in REG}
        gap_avg = p.loc[a:b, 'gap'].mean()
        lines.append(f'* {per_name}: ICS {raw:+.1f} pts vs 1978-2019 mean; explained by unemployment {contrib["u"]:+.1f}, inflation {contrib["pi"]:+.1f}, GDP {contrib["g"]:+.1f} '
                     f'(pre-2020 coefficients); unexplained real-time gap (expanding model) {gap_avg:+.1f} pts')
    # (d) rolling 15-year coefficient paths
    roll = []
    for t in d.loc['1995-01':].index:
        w = d.loc[t - 180 + 1:t]
        f = sm.OLS(w['y'], sm.add_constant(w[REG])).fit()
        roll.append({'month': t, **{f'r_{k}': v for k, v in f.params.items()}})
    roll = pd.DataFrame(roll).set_index('month')
    if tgt == 'ics':
        coefs = p[['b_const', 'b_u', 'b_pi', 'b_g', 'n_train']].join(roll, how='outer')
        coefs.to_csv(os.path.join(OUT, 'econ_baseline_coefs.csv'))
        # robustness: core-PCE (spreadsheet) instead of headline; pseudo real time instead of ALFRED
        for lab, cols in {'core PCE (spreadsheet series) instead of headline': ['u', 'pi_core_pseudo', 'g'], 'pseudo real-time regressors (final data, publication lags)': ['u_pseudo', 'pi_pseudo', 'g_pseudo']}.items():
            dd = pd.concat([m['ics'].rename('y'), X[cols]], axis=1).dropna()['1978-01':]
            errs = []
            for t in dd.loc['2010-01':].index:
                tr = dd.loc[:t - 1]; f = sm.OLS(tr['y'], sm.add_constant(tr[cols])).fit()
                errs.append(dd.loc[t, 'y'] - float(f.predict(sm.add_constant(dd.loc[[t], cols], has_constant='add')).iloc[0]))
            errs = pd.Series(errs, index=dd.loc['2010-01':].index)
            lines.append(f'* Robustness — {lab}: OOS RMSE 2010-2026 = {np.sqrt((errs**2).mean()):.2f}; mean gap 2025-2026 = {errs.loc["2025-01":].mean():+.1f}')

pred = pd.concat({k: v for k, v in preds_all.items()}, axis=1)
pred.columns = [f'{a}__{b}' for a, b in pred.columns]
pred.to_csv(os.path.join(OUT, 'econ_baseline_predictions.csv'))
open(os.path.join(OUT, 'econ_baseline_summary.md'), 'w').write('\n'.join(lines))

# --- figures ------------------------------------------------------------------------
p = preds_all['ics']; idx = p.index.to_timestamp()
fig, ax = plt.subplots(figsize=(11, 5))
ax.fill_between(idx, p['emp95_lo'], p['emp95_hi'], color='#9ecae1', alpha=0.35, label='95% empirical PI')
ax.fill_between(idx, p['emp80_lo'], p['emp80_hi'], color='#6baed6', alpha=0.35, label='80% empirical PI')
ax.plot(idx, p['yhat'], color='#08519c', lw=1.6, label='Economic-only model (real-time, expanding window)')
ax.plot(idx, p['y'], color='black', lw=1.6, label='Michigan ICS (actual)')
ax.axvline(pd.Timestamp('2024-07-01'), color='grey', ls=':', lw=1); ax.text(pd.Timestamp('2024-07-15'), ax.get_ylim()[1] - 4, 'web-only\nsurvey', fontsize=8, color='grey')
ax.set_title('Consumer sentiment vs. economic-only model prediction'); ax.set_ylabel('Index (1966Q1=100)'); ax.legend(loc='lower left', fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig1_ics_vs_model.png'), dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 4))
ax.bar(idx, p['gap'], width=25, color=np.where(p['gap'] < 0, '#cb181d', '#238b45'))
ax.axhline(0, color='black', lw=0.8); ax.set_title('Sentiment gap = actual ICS − economic-only out-of-sample prediction'); ax.set_ylabel('index points')
fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig2_gap.png'), dpi=160); plt.close(fig)

c = pd.read_csv(os.path.join(OUT, 'econ_baseline_coefs.csv'), index_col=0); c.index = pd.PeriodIndex(c.index, freq='M').to_timestamp()
fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
for ax, (k, lab) in zip(axes, [('u', 'Unemployment rate'), ('pi', 'PCE inflation (y/y)'), ('g', 'Real GDP growth (q/q ann.)')]):
    ax.plot(c.index, c[f'b_{k}'], label='expanding window', color='#08519c'); ax.plot(c.index, c[f'r_{k}'], label='15-year rolling', color='#e6550d')
    ax.axhline(0, color='grey', lw=0.6); ax.set_title(lab, fontsize=10)
axes[0].legend(fontsize=8); fig.suptitle('Coefficient stability, economic-only model'); fig.tight_layout(); fig.savefig(os.path.join(FIG, 'fig3_coef_stability.png'), dpi=160); plt.close(fig)
print('\n'.join(lines))
