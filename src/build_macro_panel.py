"""
build_macro_panel.py — Economic and survey baseline (project brief, section 1).

Inputs
  Perceptual_Bias_Data.xlsx      course-supplied series (PRIMARY for the four required measures)
  data/raw/fred/*.csv            FRED controls and cross-checks (downloaded by collect_fred_alfred.py)
  data/raw/alfred/*_all_vintages.csv   real-time vintages of UNRATE, PCEPI, GDPC1
  data/raw/michigan/RB_*.xls     Michigan Surveys of Consumers historical tables
  data/raw/michigan/manual_additions.csv  sub-indices for months not yet in the archive tables

Outputs (data/processed/)
  macro_monthly.csv       monthly panel 1978-01 .. latest, final-vintage data + controls + Michigan tables
  realtime_panel.csv      what was known on the 15th of each month (2009-02 ..): latest released
                          unemployment, PCE inflation, GDP growth, with reference periods and lags
  gdp_revisions.csv       advance vs. latest estimate of quarterly real GDP growth
  excel_vs_fred_check.csv cross-check of the course spreadsheet against FRED
  data_notes.md           provenance, timing rules and anomalies found
"""
import os, re, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'data', 'raw')
OUT = os.path.join(ROOT, 'data', 'processed')
os.makedirs(OUT, exist_ok=True)
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
notes = []


def note(s):
    notes.append(s); print('NOTE:', s)


# ----------------------------------------------------------------------------------
# 1. Course spreadsheet (primary source for the four required measures)
# ----------------------------------------------------------------------------------
xl = pd.read_excel(os.path.join(ROOT, 'Perceptual_Bias_Data.xlsx'), header=0)
def series_from(xl, dcol, vcol, name):
    s = xl[[dcol, vcol]].dropna()
    s.columns = ['date', name]
    s['date'] = pd.to_datetime(s['date']).dt.to_period('M')
    return s.set_index('date')[name].sort_index()

ics_x = series_from(xl, xl.columns[3], xl.columns[4], 'ics')
unrate_x = series_from(xl, xl.columns[0], xl.columns[1], 'unrate')
pce_x = series_from(xl, xl.columns[7], xl.columns[8], 'pce_yoy')
gdp_x = series_from(xl, xl.columns[10], xl.columns[11], 'gdp_qoq_ann')  # indexed by quarter-end month
note(f'Spreadsheet: ICS {ics_x.index.min()}..{ics_x.index.max()} ({len(ics_x)} obs); '
     f'UNRATE {unrate_x.index.min()}..{unrate_x.index.max()} ({len(unrate_x)} obs, missing months: '
     f'{[str(p) for p in pd.period_range(unrate_x.index.min(), unrate_x.index.max(), freq="M").difference(unrate_x.index)]}); '
     f'PCE YoY {pce_x.index.min()}..{pce_x.index.max()}; GDP QoQ ann. {gdp_x.index.min()}..{gdp_x.index.max()} ({len(gdp_x)} quarters)')

# ----------------------------------------------------------------------------------
# 2. FRED
# ----------------------------------------------------------------------------------
def fred(sid):
    df = pd.read_csv(os.path.join(RAW, 'fred', f'{sid}.csv'))
    df['date'] = pd.to_datetime(df['date'])
    df[sid] = pd.to_numeric(df[sid], errors='coerce')
    return df.set_index('date')[sid]

F = {sid: fred(sid) for sid in ['UMCSENT', 'MICH', 'UNRATE', 'U6RATE', 'PAYEMS', 'PCEPI', 'PCEPILFE', 'CPIAUCSL', 'CPIUFDSL',
                                 'CUSR0000SEHA', 'GASREGW', 'GDPC1', 'A229RX0', 'DSPIC96', 'PSAVERT', 'TDSP', 'MORTGAGE30US',
                                 'MSPUS', 'USEPUINDXM', 'FEDFUNDS', 'LES1252881600Q', 'RSXFS', 'USREC', 'SP500']}

def to_month(s, how='mean'):
    s = s.dropna()
    g = s.groupby(s.index.to_period('M'))
    return g.mean() if how == 'mean' else g.last()

m = pd.DataFrame(index=pd.period_range('1978-01', max(ics_x.index.max(), pd.Period(dt.date.today().strftime('%Y-%m'), freq='M')), freq='M'))
m.index.name = 'month'
m['ics'] = ics_x
m['unrate'] = unrate_x
m['pce_yoy'] = pce_x
# quarterly GDP growth from the spreadsheet, kept ONLY in the quarter-end month (never interpolated)
m['gdp_qoq_ann_q'] = gdp_x
for sid in ['UMCSENT', 'MICH', 'UNRATE', 'U6RATE', 'PAYEMS', 'PCEPI', 'PCEPILFE', 'CPIAUCSL', 'CPIUFDSL', 'CUSR0000SEHA',
            'A229RX0', 'DSPIC96', 'PSAVERT', 'USEPUINDXM', 'FEDFUNDS', 'RSXFS', 'USREC']:
    m[sid.lower()] = to_month(F[sid], 'last')
for sid in ['GASREGW', 'MORTGAGE30US', 'SP500']:
    m[sid.lower()] = to_month(F[sid], 'mean')
# quarterly series: value stored in each month of the quarter (quarter-average/level data), flagged
for sid in ['GDPC1', 'TDSP', 'MSPUS', 'LES1252881600Q']:
    q = F[sid].dropna()
    q.index = q.index.to_period('Q')
    mm = pd.Series({p: q.get(p.asfreq('Q')) for p in m.index})
    m[sid.lower() + '_qlevel'] = mm

# derived
m['pce_yoy_fred'] = 100 * (m['pcepi'] / m['pcepi'].shift(12) - 1)
m['core_pce_yoy'] = 100 * (m['pcepilfe'] / m['pcepilfe'].shift(12) - 1)
m['cpi_yoy'] = 100 * (m['cpiaucsl'] / m['cpiaucsl'].shift(12) - 1)
m['food_cpi_yoy'] = 100 * (m['cpiufdsl'] / m['cpiufdsl'].shift(12) - 1)
m['rent_cpi_yoy'] = 100 * (m['cusr0000seha'] / m['cusr0000seha'].shift(12) - 1)
m['cum_price_3y'] = 100 * (m['cpiaucsl'] / m['cpiaucsl'].shift(36) - 1)          # 3-year cumulative inflation
base = m.loc['2020-01', 'cpiaucsl']
m['cum_price_since_2020'] = 100 * (m['cpiaucsl'] / base - 1)                        # price level vs Jan-2020
m['real_dpi_pc_yoy'] = 100 * (m['a229rx0'] / m['a229rx0'].shift(12) - 1)
m['payroll_chg_k'] = m['payems'].diff()
m['u6_u3_gap'] = m['u6rate'] - m['unrate']
m['gas_yoy'] = 100 * (m['gasregw'] / m['gasregw'].shift(12) - 1)
m['sp500_yoy'] = 100 * (m['sp500'] / m['sp500'].shift(12) - 1)
# housing affordability proxy: annual payment on an 80% LTV 30-yr loan at MSPUS / nominal DPI per capita
r = m['mortgage30us'] / 100 / 12
pay = 0.8 * m['mspus_qlevel'] * r / (1 - (1 + r) ** (-360)) * 12
nominal_dpi_pc = m['a229rx0'] * m['pcepi'] / 100
m['mortgage_pay_to_income'] = 100 * pay / nominal_dpi_pc
# GDP growth two ways from FRED levels (quarterly, stored in quarter-end month only)
g = F['GDPC1'].dropna(); g.index = g.index.to_period('Q')
gq = pd.DataFrame({'gdp_qoq_ann_fred': 100 * ((g / g.shift(1)) ** 4 - 1), 'gdp_yoy_fred': 100 * (g / g.shift(4) - 1)})
gq.index = [p.asfreq('M', 'end') for p in gq.index]
m = m.join(gq)
m['gdp_latest_q_qoq_ann'] = m['gdp_qoq_ann_q'].ffill()   # for descriptive charts only (flagged); models use realtime panel

# ----------------------------------------------------------------------------------
# 3. Michigan tables
# ----------------------------------------------------------------------------------
def mich_table(tbl, cols):
    df = pd.read_excel(os.path.join(RAW, 'michigan', f'RB_{tbl}.xls'), header=None)
    first = next(i for i in range(len(df)) if str(df.iloc[i, 0]).strip() in MONTHS)
    d = df.iloc[first:].copy()
    d = d[d[0].astype(str).str.strip().isin(MONTHS)]
    idx = pd.PeriodIndex([pd.Period(f'{int(y)}-{MONTHS.index(str(mo).strip()) + 1:02d}', freq='M') for mo, y in zip(d[0], d[1])])
    out = pd.DataFrame(index=idx)
    for j, c in enumerate(cols):
        if c:
            out[c] = pd.to_numeric(d.iloc[:, 2 + j].values, errors='coerce')
    out = out[~out.index.duplicated(keep='last')]
    return out

mich = {
    '1a': ['um_ics', 'um_cases'],
    '1b': ['um_current', 'um_pf_current', 'um_buying_durables', 'um_expected', 'um_pf_expected', 'um_bus12', 'um_bus5y'],
    '2n': ['ics_inc_bottom', 'ics_inc_middle', 'ics_inc_top', 'cur_inc_bottom', 'cur_inc_middle', 'cur_inc_top', 'exp_inc_bottom', 'exp_inc_middle', 'exp_inc_top'],
    '3n': ['ics_age_18_34', 'ics_age_35_54', 'ics_age_55p', 'cur_age_18_34', 'cur_age_35_54', 'cur_age_55p', 'exp_age_18_34', 'exp_age_35_54', 'exp_age_55p'],
    '4n': ['ics_edu_hs', 'ics_edu_somecoll', 'ics_edu_college', 'cur_edu_hs', 'cur_edu_somecoll', 'cur_edu_college', 'exp_edu_hs', 'exp_edu_somecoll', 'exp_edu_college'],
    '5a': ['ics_reg_ne', 'ics_reg_nc', 'ics_reg_s', 'ics_reg_w', 'cur_reg_ne', 'cur_reg_nc', 'cur_reg_s', 'cur_reg_w', 'exp_reg_ne', 'exp_reg_nc', 'exp_reg_s', 'exp_reg_w'],
    '5b': ['ics_dem', 'ics_ind', 'ics_rep', 'cur_dem', 'cur_ind', 'cur_rep', 'exp_dem', 'exp_ind', 'exp_rep'],
    '6': ['pf_better', 'pf_same', 'pf_worse', None, None, 'pf_relative', None],
    '23': ['news_favorable', 'news_unfavorable', 'news_none', 'news_relative'],
    '24': ['newsf_govt', 'newsf_emp', 'newsf_demand', 'newsf_lowprice', 'newsf_credit', 'newsf_stocks', 'newsf_trade',
           'newsu_govt', 'newsu_unemp', 'newsu_lowdemand', 'newsu_highprice', 'newsu_tightcredit', 'newsu_energy', 'newsu_stocks', 'newsu_trade'],
    '25': ['bus_better', 'bus_same', 'bus_worse', None, None, 'bus_relative', None],
    '30': ['unemp_exp_less', 'unemp_exp_same', 'unemp_exp_more', None, None, 'unemp_exp_relative', None],
    '32': [None, None, None, None, None, None, None, None, None, None, None, 'px_exp_median', 'px_exp_p25', 'px_exp_p75', None, 'px_exp_mean', None, None],
    '34': ['govpol_good', 'govpol_fair', 'govpol_poor', None, None, 'govpol_relative', None],
}
for tbl, cols in mich.items():
    t = mich_table(tbl, cols)
    m = m.join(t, how='left')
    print(f'Michigan table {tbl}: {t.index.min()}..{t.index.max()} ({len(t)} rows)')

# manual additions (months published in press releases but not yet in the archive tables)
man_fn = os.path.join(RAW, 'michigan', 'manual_additions.csv')
if os.path.exists(man_fn):
    man = pd.read_csv(man_fn)
    for _, row in man.iterrows():
        p = pd.Period(row['month'], freq='M')
        for c in man.columns:
            if c in ('month', 'source'):
                continue
            if pd.notna(row[c]) and (c not in m.columns or pd.isna(m.loc[p, c]) if p in m.index else True):
                m.loc[p, c] = row[c]
    note(f'Manual Michigan additions applied for months {man["month"].tolist()} (sources listed in manual_additions.csv)')

# ----------------------------------------------------------------------------------
# 4. Cross-check spreadsheet vs FRED
# ----------------------------------------------------------------------------------
chk = pd.DataFrame({'ics_excel': m['ics'], 'umcsent_fred': m['umcsent'], 'unrate_excel': m['unrate'], 'unrate_fred': m['unrate'] * 0 + to_month(F['UNRATE'], 'last'),
                    'pce_yoy_excel': m['pce_yoy'], 'pce_yoy_fred': m['pce_yoy_fred'], 'gdp_excel': m['gdp_qoq_ann_q'], 'gdp_fred': m['gdp_qoq_ann_fred']})
chk['unrate_fred'] = to_month(F['UNRATE'], 'last')
chk['d_ics'] = chk['ics_excel'] - chk['umcsent_fred']
chk['d_unrate'] = chk['unrate_excel'] - chk['unrate_fred']
chk['d_pce'] = chk['pce_yoy_excel'] - chk['pce_yoy_fred']
chk['d_gdp'] = chk['gdp_excel'] - chk['gdp_fred']
chk.to_csv(os.path.join(OUT, 'excel_vs_fred_check.csv'))
for c, tol in [('d_ics', 0.05), ('d_unrate', 0.05), ('d_pce', 0.05), ('d_gdp', 0.15)]:
    bad = chk[c].dropna()
    bad = bad[bad.abs() > tol]
    note(f'{c}: {len(bad)} months differ from FRED by more than {tol} (largest: {bad.abs().max() if len(bad) else 0:.2f}); '
         + (f'examples {[(str(i), round(v, 2)) for i, v in bad.tail(5).items()]}' if len(bad) else 'all consistent'))
last_fred_gdp = F['GDPC1'].dropna().index.max()
note(f'Spreadsheet GDP extends to {gdp_x.index.max()} but FRED/BEA real GDP is published only through quarter ending {last_fred_gdp.date()}: '
     'the spreadsheet value for the latest quarter predates the BEA advance estimate (scheduled 2026-10-29) and is treated as NOT available '
     'in real time; it is excluded from all real-time predictions.')
note(f'FRED UMCSENT ends {F["UMCSENT"].dropna().index.max().date()}; the spreadsheet adds the September final and the October 2026 preliminary reading (46.3).')

# ----------------------------------------------------------------------------------
# 5. Real-time panel from ALFRED vintages (what was known on the 15th of each month)
# ----------------------------------------------------------------------------------
def load_vintages(sid):
    v = pd.read_csv(os.path.join(RAW, 'alfred', f'{sid}_all_vintages.csv'))
    v['date'] = pd.to_datetime(v['date']); v['vintage'] = pd.to_datetime(v['vintage'])
    v['value'] = pd.to_numeric(v['value'], errors='coerce')
    return v

V = {sid: load_vintages(sid) for sid in ['UNRATE', 'PCEPI', 'GDPC1']}
rows = []
for vint in sorted(V['UNRATE']['vintage'].unique()):
    vint = pd.Timestamp(vint)
    month = vint.to_period('M')
    rec = {'month': month, 'vintage_date': vint.date()}
    u = V['UNRATE'][V['UNRATE']['vintage'] == vint].dropna(subset=['value']).sort_values('date')
    if len(u):
        rec['unrate_rt'] = u['value'].iloc[-1]; rec['unrate_ref'] = u['date'].iloc[-1].to_period('M')
        rec['unrate_lag_m'] = (month - rec['unrate_ref']).n
    p = V['PCEPI'][V['PCEPI']['vintage'] == vint].dropna(subset=['value']).sort_values('date').set_index('date')['value']
    if len(p) > 12:
        last = p.index[-1]; prev = last - pd.DateOffset(years=1)
        if prev in p.index:
            rec['pce_yoy_rt'] = 100 * (p.iloc[-1] / p.loc[prev] - 1); rec['pce_ref'] = last.to_period('M'); rec['pce_lag_m'] = (month - rec['pce_ref']).n
    gd = V['GDPC1'][V['GDPC1']['vintage'] == vint].dropna(subset=['value']).sort_values('date').set_index('date')['value']
    if len(gd) > 4:
        rec['gdp_qoq_ann_rt'] = 100 * ((gd.iloc[-1] / gd.iloc[-2]) ** 4 - 1)
        rec['gdp_yoy_rt'] = 100 * (gd.iloc[-1] / gd.iloc[-5] - 1)
        rec['gdp_ref_q'] = gd.index[-1].to_period('Q'); rec['gdp_lag_m'] = (month - gd.index[-1].to_period('M')).n
    rows.append(rec)
rt = pd.DataFrame(rows).set_index('month')
rt = rt[~rt.index.duplicated(keep='last')]
rt.to_csv(os.path.join(OUT, 'realtime_panel.csv'))
note(f'Real-time panel: {rt.index.min()}..{rt.index.max()}; typical lags (months): unemployment {rt["unrate_lag_m"].median():.0f}, '
     f'PCE {rt["pce_lag_m"].median():.0f}, GDP {rt["gdp_lag_m"].median():.0f}. Months with unusual lags (release delays): '
     f'{[str(i) for i, r_ in rt.iterrows() if r_["unrate_lag_m"] > 1 or r_["pce_lag_m"] > 2]}')

# GDP revisions: advance (first vintage containing the quarter) vs latest
adv = []
gd_all = V['GDPC1'].dropna(subset=['value'])
for q, grp in gd_all.groupby('date'):
    grp = grp.sort_values('vintage')
    first_v = grp['vintage'].iloc[0]
    g_first = gd_all[gd_all['vintage'] == first_v].sort_values('date').set_index('date')['value']
    g_last = gd_all[gd_all['vintage'] == grp['vintage'].iloc[-1]].sort_values('date').set_index('date')['value']
    prev = q - pd.DateOffset(months=3)
    if prev in g_first.index and prev in g_last.index and q >= pd.Timestamp('2009-01-01'):
        adv.append({'quarter': q.to_period('Q'), 'first_vintage': first_v.date(), 'growth_first_est': 100 * ((g_first[q] / g_first[prev]) ** 4 - 1),
                    'growth_latest': 100 * ((g_last[q] / g_last[prev]) ** 4 - 1)})
rev = pd.DataFrame(adv); rev['revision'] = rev['growth_latest'] - rev['growth_first_est']
rev.to_csv(os.path.join(OUT, 'gdp_revisions.csv'), index=False)
note(f'GDP revisions 2009+: mean absolute revision (first vintage in our monthly grid vs latest) = {rev["revision"].abs().mean():.2f} pp; largest {rev["revision"].abs().max():.2f} pp')

# ----------------------------------------------------------------------------------
# 6. Save
# ----------------------------------------------------------------------------------
m.to_csv(os.path.join(OUT, 'macro_monthly.csv'))
with open(os.path.join(OUT, 'data_notes.md'), 'w') as f:
    f.write('# Data notes (auto-generated by build_macro_panel.py on %s)\n\n' % dt.date.today())
    f.write('## Timing rules\n* Prediction date for month t = the 15th of month t (close to the Michigan preliminary release).\n'
            '* Unemployment for month t-1 is released on the first Friday of month t; PCE prices for month t-2 at the end of month t-1; '
            'GDP advance estimate about four weeks after quarter end. The real-time panel uses ALFRED vintages dated the 15th of each month, '
            'so delays (e.g., the 2025 and 2026 shutdowns) and revisions are reflected automatically.\n'
            '* Quarterly GDP is never interpolated to months: the model uses the latest published quarterly growth rate as of the prediction date.\n\n## Findings\n')
    for n in notes:
        f.write(f'* {n}\n')
print('Saved macro_monthly.csv', m.shape, 'realtime_panel.csv', rt.shape)
