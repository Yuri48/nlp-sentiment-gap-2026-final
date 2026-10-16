"""
build_media_indices.py — Monthly media measures from the LLM labels (sample) and from the
baseline classifiers (full corpus), plus the factual-calibration check of numeric claims.

Outputs (data/processed/):
  media_monthly.csv     one row per month; columns documented in media_monthly_codebook.md
  claims_checked.csv    every numeric claim extracted by the LLM with the official value available
                        on the publication date and a status (accurate / stale / wrong / unverifiable)
  media_monthly_codebook.md
"""
import os, json, re, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'processed')
news = pd.read_parquet(os.path.join(OUT, 'news_items.parquet'))
soc = pd.read_parquet(os.path.join(OUT, 'social_items.parquet')) if os.path.exists(os.path.join(OUT, 'social_items.parquet')) else pd.DataFrame()
lab = pd.read_parquet(os.path.join(OUT, 'labels_llm.parquet'))
base = pd.read_parquet(os.path.join(OUT, 'baseline_scores.parquet')) if os.path.exists(os.path.join(OUT, 'baseline_scores.parquet')) else pd.DataFrame()
macro = pd.read_csv(os.path.join(OUT, 'macro_monthly.csv'), index_col=0); macro.index = pd.PeriodIndex(macro.index, freq='M')
codebook = []

def cb(col, desc):
    codebook.append(f'| `{col}` | {desc} |')

# ---------------------------------------------------------------------------------------
# A. LLM-labelled sample
# ---------------------------------------------------------------------------------------
ln = lab[lab['kind'] == 'news'].merge(news[['item_id', 'domain', 'source_type', 'source_lean', 'date', 'n_reprints']], on='item_id', how='left')
ls = lab[lab['kind'] == 'social'].merge(soc[['item_id', 'engagement', 'like_count', 'date']], on='item_id', how='left') if len(soc) else lab.iloc[0:0]
TOPICS = ['jobs_loss', 'jobs_gain', 'prices_up', 'prices_down', 'growth', 'recession', 'rates', 'housing', 'wages_income', 'tariffs_trade', 'markets', 'gov_policy']

def agg_llm(df, prefix):
    rel = df[df['relevant'] == 1].copy()
    g = df.groupby('month')
    out = pd.DataFrame({f'{prefix}_n_labelled': g.size(), f'{prefix}_share_relevant': g['relevant'].mean()})
    if not len(rel):
        return out
    rel['tone'] = rel['tone'].astype(float); rel['emotional'] = rel['emotional'].astype(float)
    gr = rel.groupby('month')
    out[f'{prefix}_n_relevant'] = gr.size()
    out[f'{prefix}_tone'] = gr['tone'].mean()
    out[f'{prefix}_neg_share'] = gr['tone'].apply(lambda s: (s == -1).mean())
    out[f'{prefix}_pos_share'] = gr['tone'].apply(lambda s: (s == 1).mean())
    out[f'{prefix}_emotional'] = gr['emotional'].mean()
    out[f'{prefix}_emotional2_share'] = gr['emotional'].apply(lambda s: (s == 2).mean())
    out[f'{prefix}_neg_emotional_share'] = gr.apply(lambda d: ((d['tone'] == -1) & (d['emotional'] == 2)).mean())
    for t in TOPICS:
        out[f'{prefix}_topic_{t}'] = gr['topics'].apply(lambda s: s.str.contains(t).mean())
    price = rel[rel['topics'].str.contains('prices_up|prices_down')]
    gp = price.groupby('month')
    out[f'{prefix}_frame_level_share'] = gp['frame_level_rate'].apply(lambda s: s.isin(['level', 'both']).mean())
    out[f'{prefix}_frame_rate_share'] = gp['frame_level_rate'].apply(lambda s: s.isin(['rate', 'both']).mean())
    out[f'{prefix}_frame_household_share'] = gr['frame_scope'].apply(lambda s: s.isin(['household', 'both']).mean())
    out[f'{prefix}_frame_forecast_share'] = gr['frame_time'].apply(lambda s: s.isin(['forecast', 'both']).mean())
    out[f'{prefix}_numeric_claim_share'] = gr['numeric_claim'].mean()
    out[f'{prefix}_blame_share'] = gr['attribution_valence'].apply(lambda s: (s == 'blame').mean())
    out[f'{prefix}_credit_share'] = gr['attribution_valence'].apply(lambda s: (s == 'credit').mean())
    for a in ['trump_admin', 'biden_admin', 'federal_reserve', 'corporations', 'foreign_trade_partners', 'congress_republicans', 'congress_democrats']:
        out[f'{prefix}_blame_{a}'] = gr.apply(lambda d: ((d['attribution_actor'] == a) & (d['attribution_valence'] == 'blame')).mean())
        out[f'{prefix}_credit_{a}'] = gr.apply(lambda d: ((d['attribution_actor'] == a) & (d['attribution_valence'] == 'credit')).mean())
    return out

M = agg_llm(ln, 'llm_news')
cb('llm_news_tone', 'Mean LLM tone (-1..+1) of relevant news headlines in the labelled sample')
cb('llm_news_neg_share', 'Share of relevant headlines with tone = -1 (LLM)')
cb('llm_news_emotional2_share', 'Share with emotional/alarmist wording (emotional = 2)')
cb('llm_news_topic_*', 'Share of relevant headlines mentioning each topic (selection / salience)')
cb('llm_news_frame_level_share', 'Among price headlines: share framed as price LEVEL (level or both)')
cb('llm_news_frame_household_share', 'Share framed around household experience (household or both)')
cb('llm_news_frame_forecast_share', 'Share framed as forecast/expectations (forecast or both)')
cb('llm_news_blame_<actor>', 'Share of relevant headlines blaming the actor (political attribution)')
if len(ln):
    for st in ['national', 'local', 'national_other', 'local_other']:
        sub = ln[ln['source_type'] == st]
        if len(sub):
            a = agg_llm(sub, f'llm_{st}')[[f'llm_{st}_tone', f'llm_{st}_neg_share', f'llm_{st}_n_relevant']] if (sub['relevant'] == 1).any() else None
            if a is not None:
                M = M.join(a)
    for lean in ['left', 'lean_left', 'center', 'lean_right', 'right']:
        sub = ln[ln['source_lean'] == lean]
        if len(sub) and (sub['relevant'] == 1).any():
            a = agg_llm(sub, f'llm_{lean}')
            M = M.join(a[[f'llm_{lean}_tone', f'llm_{lean}_n_relevant', f'llm_{lean}_blame_trump_admin', f'llm_{lean}_blame_biden_admin']])
    cb('llm_<source_type>_tone / llm_<lean>_tone', 'LLM tone by source type and by audience-lean stratum')
if len(ls):
    S = agg_llm(ls, 'llm_social')
    rels = ls[ls['relevant'] == 1].copy(); rels['tone'] = rels['tone'].astype(float)
    gs = rels.groupby('month')
    S['llm_social_personal_share'] = gs['post_type'].apply(lambda s: (s == 'personal_experience').mean())
    S['llm_social_newsshare_share'] = gs['post_type'].apply(lambda s: (s == 'news_share').mean())
    w = rels['engagement'].fillna(0) + 1
    S['llm_social_tone_engagement_weighted'] = rels.assign(w=w, tw=rels['tone'] * w).groupby('month').apply(lambda d: d['tw'].sum() / d['w'].sum())
    M = M.join(S, how='outer')
    cb('llm_social_tone', 'Mean LLM tone of relevant Bluesky posts (sample); _engagement_weighted weights by likes+reposts+replies+quotes+1')
    cb('llm_social_personal_share', 'Share of relevant posts that describe the author\'s own finances (household experience)')

# ---------------------------------------------------------------------------------------
# B. Full corpus (supply volume and baseline-classifier tone)
# ---------------------------------------------------------------------------------------
nk = news[news['kw_title'] & (news['source_type'] != 'foreign')]
g = nk.groupby('month')
F = pd.DataFrame({'news_n_kw': g.size(), 'news_n_panel': g['in_panel'].sum(), 'news_n_all_us': news[news['source_type'] != 'foreign'].groupby('month').size(),
                  'news_gdelt_tone': g['tone'].mean(), 'news_reprints_mean': g['n_reprints'].mean()})
KWP = {'prices': r'\b(inflation\w*|prices?|cost of living|groceries|grocery|gas prices?|gasoline|rents?)\b', 'jobs': r'\b(jobs?|unemploy\w*|layoffs?|laid off|hiring|payrolls?|jobless|labor market|job market)\b',
       'recession': r'\b(recession|downturn|slowdown|stagflation)\b', 'tariffs': r'\b(tariffs?)\b', 'rates': r'\b(interest rates?|the fed|federal reserve|rate (?:hike|cut)s?|mortgage rates?)\b'}
for k, pat in KWP.items():
    F[f'news_kwshare_{k}'] = nk['text'].str.contains(pat, case=False, regex=True).groupby(nk['month']).mean()
cb('news_n_kw', 'Number of unique US headlines with an economic keyword in the title (content SUPPLY, from the GKG slice sample)')
cb('news_gdelt_tone', 'Mean GDELT V2Tone of those articles (dictionary tone of full text, full corpus)')
cb('news_kwshare_<topic>', 'Keyword-based salience: share of economic headlines mentioning the topic (full corpus)')
if len(base):
    bn = base[base['kind'] == 'news']
    gb = bn.groupby('month')
    for c in ['finbert_class', 'twroberta_class', 'vader_class', 'tfidf_lr_class']:
        if c in bn:
            F[f'news_{c.replace("_class", "")}_tone'] = gb[c].mean()
            F[f'news_{c.replace("_class", "")}_neg_share'] = gb[c].apply(lambda s: (s == -1).mean())
    cb('news_finbert_tone / news_vader_tone / news_twroberta_tone / news_tfidf_lr_tone', 'Mean 3-class tone from each baseline classifier over the full keyword corpus')
    if len(soc):
        bs = base[base['kind'] == 'social'].merge(soc[['item_id', 'engagement', 'query']], on='item_id')
        gs = bs.groupby('month')
        for c in ['finbert_class', 'twroberta_class', 'vader_class']:
            if c in bs:
                F[f'social_{c.replace("_class", "")}_tone'] = gs[c].mean()
        w = bs['engagement'].fillna(0) + 1
        if 'twroberta_class' in bs:
            F['social_twroberta_tone_engagement_weighted'] = bs.assign(w=w, tw=bs['twroberta_class'] * w).groupby('month').apply(lambda d: d['tw'].sum() / d['w'].sum())
if len(soc):
    gsoc = soc.groupby('month')
    F['social_n_posts'] = gsoc.size(); F['social_engagement_mean'] = gsoc['engagement'].mean()
    for q in soc['query'].unique():
        F[f'social_n_{q.replace(" ", "_")}'] = soc[soc['query'] == q].groupby('month').size()
    cb('social_n_posts', 'Unique Bluesky posts collected per month (supply, capped at 100 per query-week)')
M = M.join(F, how='outer')

# ---------------------------------------------------------------------------------------
# C. Factual calibration of numeric claims
# ---------------------------------------------------------------------------------------
rt_u = pd.read_csv(os.path.join(ROOT, 'data', 'raw', 'alfred', 'UNRATE_all_vintages.csv'))
rt_u['date'] = pd.to_datetime(rt_u['date']); rt_u['vintage'] = pd.to_datetime(rt_u['vintage']); rt_u = rt_u.drop_duplicates(['date', 'vintage'])
pay_fn = os.path.join(ROOT, 'data', 'raw', 'alfred', 'PAYEMS_all_vintages.csv')
rt_p = pd.read_csv(pay_fn) if os.path.exists(pay_fn) else pd.DataFrame(columns=['date', 'value', 'vintage'])
rt_p['date'] = pd.to_datetime(rt_p['date']); rt_p['vintage'] = pd.to_datetime(rt_p['vintage']); rt_p = rt_p.drop_duplicates(['date', 'vintage'])
STATES = r'\b(Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|county|metro|statewide|Bay Area|N\.?J\.?|N\.?Y\.?|L\.?A\.?|Chicago|Houston|Dallas|Phoenix|Philadelphia|Atlanta|Miami|Seattle|Denver|Boston|Detroit|Minneapolis|Las Vegas|San Francisco|Los Angeles|Portland|Cleveland|Pittsburgh|Milwaukee|Charlotte|Tampa|Kansas City|St\. Louis|Nashville|Columbus|Baltimore|Sacramento|San Diego|Orlando|Cincinnati|Indianapolis)\b'
STATE_RE = re.compile(STATES, re.I)
fred = {s: pd.read_csv(os.path.join(ROOT, 'data', 'raw', 'fred', f'{s}.csv')) for s in ['CPIAUCSL', 'PCEPI', 'GDPC1', 'PAYEMS', 'FEDFUNDS', 'GASREGW']}
for s, d in fred.items():
    d['date'] = pd.to_datetime(d['date']); d[s] = pd.to_numeric(d[s], errors='coerce')
cpi = fred['CPIAUCSL'].set_index('date')['CPIAUCSL']; cpi_yoy = 100 * (cpi / cpi.shift(12) - 1)
pce = fred['PCEPI'].set_index('date')['PCEPI']; pce_yoy = 100 * (pce / pce.shift(12) - 1)
cpi_mom = 100 * (cpi / cpi.shift(1) - 1)
gdp = fred['GDPC1'].set_index('date')['GDPC1']; gdp_g = 100 * ((gdp / gdp.shift(1)) ** 4 - 1)
pay = fred['PAYEMS'].set_index('date')['PAYEMS'].diff()
ff = fred['FEDFUNDS'].set_index('date')['FEDFUNDS']; gas = fred['GASREGW'].set_index('date')['GASREGW']

def release_lag_days(ind):
    return {'unemployment_rate': 6, 'jobs_added': 6, 'cpi_yoy': 14, 'cpi_mom': 14, 'pce_yoy': 30, 'gdp_qoq_ann': 30, 'fed_funds': 0, 'gas_price': 0}.get(ind, 30)

def official(ind, period, pub_date):
    """Return (official value, reference period, basis) available on pub_date."""
    series = {'unemployment_rate': None, 'cpi_yoy': cpi_yoy, 'cpi_mom': cpi_mom, 'pce_yoy': pce_yoy, 'gdp_qoq_ann': gdp_g, 'jobs_added': pay, 'fed_funds': ff, 'gas_price': gas}.get(ind)
    if ind == 'jobs_added' and len(rt_p):
        # payroll claims refer to the FIRST release: use the earliest vintage that contains the reference month
        # (monthly vintages are dated the 15th, so an article on release day precedes 'its' vintage by up to two weeks)
        pp = None
        if period:
            try:
                pp = pd.Period(period, freq='M').to_timestamp()
            except Exception:
                pp = None
        if pp is None:
            # no period stated: the most recent month released on or before the article date (release ~ first Friday)
            pp = (pub_date - pd.Timedelta(days=release_lag_days(ind))).to_period('M').to_timestamp() - pd.DateOffset(months=1)
        cand = rt_p[(rt_p['date'] == pp) & rt_p['value'].notna()].sort_values('vintage')
        cand = cand[cand['vintage'] <= pub_date + pd.Timedelta(days=45)]
        if len(cand):
            v0 = cand['vintage'].iloc[0]
            vint = rt_p[rt_p['vintage'] == v0].dropna(subset=['value']).set_index('date')['value'].sort_index()
            prev = pp - pd.DateOffset(months=1)
            if prev in vint.index:
                return float(vint.loc[pp] - vint.loc[prev]), pp, 'first release (payroll vintage)'
        return None, None, None
    if ind == 'unemployment_rate':
        v = rt_u[rt_u['vintage'] <= pub_date]
        if not len(v):
            return None, None, None
        v = v[v['vintage'] == v['vintage'].max()].dropna(subset=['value']).sort_values('date')
        v = v[v['date'] <= pub_date - pd.Timedelta(days=release_lag_days(ind))]
        if period:
            try:
                pp = pd.Period(period, freq='M').to_timestamp()
                row = v[v['date'] == pp]
                if len(row):
                    return float(row['value'].iloc[-1]), pp, 'stated period (vintage as of publication)'
            except Exception:
                pass
        if not len(v):
            return None, None, None
        return float(v['value'].iloc[-1]), v['date'].iloc[-1], 'latest release at publication (vintage)'
    if series is None:
        return None, None, None
    s = series.dropna()
    if period:
        try:
            pp = pd.Period(period).to_timestamp() if 'Q' in str(period) else pd.Period(period, freq='M').to_timestamp()
            if pp in s.index:
                return float(s.loc[pp]), pp, 'stated period (latest data)'
        except Exception:
            pass
    avail = s[s.index <= pub_date - pd.Timedelta(days=release_lag_days(ind))]
    if not len(avail):
        return None, None, None
    return float(avail.iloc[-1]), avail.index[-1], 'latest release at publication (latest data)'

TOL = {'unemployment_rate': 0.2, 'cpi_yoy': 0.2, 'cpi_mom': 0.15, 'pce_yoy': 0.2, 'gdp_qoq_ann': 0.5, 'jobs_added': 50, 'fed_funds': 0.3, 'gas_price': 0.2}
rows = []
ln_t = ln.merge(news[['item_id', 'text']], on='item_id', how='left'); ls_t = ls.merge(soc[['item_id', 'text']], on='item_id', how='left') if len(ls) else ls
COLS = ['item_id', 'kind', 'month', 'date', 'claims', 'domain', 'source_type', 'text']
src = pd.concat([ln_t.assign(kind='news')[COLS], ls_t.assign(domain='bluesky', source_type='social')[COLS]]) if len(ls) else ln_t.assign(kind='news')[COLS]
for r in src.dropna(subset=['claims']).itertuples():
    try:
        claims = json.loads(r.claims)
    except Exception:
        continue
    for c in claims:
        ind = c.get('indicator'); val = c.get('value'); per = c.get('period')
        try:
            val = float(val)
        except Exception:
            continue
        if ind not in TOL or pd.isna(r.date):
            rows.append({'item_id': r.item_id, 'kind': r.kind, 'month': r.month, 'domain': r.domain, 'source_type': r.source_type, 'indicator': ind, 'claimed': val, 'period': per, 'status': 'unverifiable'}); continue
        if ind == 'jobs_added' and abs(val) >= 2000:
            val = val / 1000.0           # claims are stated in persons; official series is in thousands
        if ind in ('gas_price', 'unemployment_rate', 'jobs_added') and STATE_RE.search(str(r.text)):
            rows.append({'item_id': r.item_id, 'kind': r.kind, 'month': r.month, 'domain': r.domain, 'source_type': r.source_type, 'indicator': ind, 'claimed': val, 'period': per, 'status': 'unverifiable_local'}); continue
        pub = pd.Timestamp(r.date)
        off, ref, basis = official(ind, per, pub)
        if off is None:
            status = 'unverifiable'
        elif abs(val - off) <= TOL[ind]:
            status = 'accurate'
        else:
            # stale: matches an earlier official value within tolerance (last 24 months)
            s_ = {'unemployment_rate': rt_u[rt_u['vintage'] == rt_u['vintage'].max()].set_index('date')['value'], 'cpi_yoy': cpi_yoy, 'cpi_mom': cpi_mom, 'pce_yoy': pce_yoy, 'gdp_qoq_ann': gdp_g, 'jobs_added': pay, 'fed_funds': ff, 'gas_price': gas}[ind].dropna()
            hist = s_[(s_.index >= pub - pd.Timedelta(days=120 if ind == 'jobs_added' else 730)) & (s_.index <= pub)]
            status = 'stale' if ((hist - val).abs() <= TOL[ind]).any() else 'wrong'
        rows.append({'item_id': r.item_id, 'kind': r.kind, 'month': r.month, 'domain': r.domain, 'source_type': r.source_type, 'indicator': ind, 'claimed': val, 'period': per,
                     'official': off, 'official_ref': ref, 'basis': basis, 'abs_error': None if off is None else abs(val - off), 'status': status})
claims = pd.DataFrame(rows)
claims.to_csv(os.path.join(OUT, 'claims_checked.csv'), index=False)
if len(claims):
    ver = claims[(claims['kind'] == 'news') & claims['status'].isin(['accurate', 'stale', 'wrong'])]
    cm = ver.groupby('month')['status']
    M['news_claims_n'] = cm.size(); M['news_claims_accurate_share'] = cm.apply(lambda s: (s == 'accurate').mean())
    M['news_claims_wrong_share'] = cm.apply(lambda s: (s == 'wrong').mean()); M['news_claims_stale_share'] = cm.apply(lambda s: (s == 'stale').mean())
    cb('news_claims_accurate_share', 'Factual calibration: share of verifiable numeric claims in headlines matching the official value available at publication (tolerances in build_media_indices.py)')

# Michigan recall measure (exposure proxy) for convenience
M = M.join(macro[['news_unfavorable', 'news_favorable', 'news_relative', 'newsu_highprice', 'newsu_unemp', 'newsf_emp', 'newsf_lowprice']].rename(columns=lambda c: 'mich_' + c), how='left')
cb('mich_news_unfavorable', 'Michigan survey: % of respondents who recall hearing UNFAVORABLE business news (the only exposure/recall measure available)')
M.index.name = 'month'
M = M.sort_index()
M.to_csv(os.path.join(OUT, 'media_monthly.csv'))
with open(os.path.join(OUT, 'media_monthly_codebook.md'), 'w') as f:
    f.write('# media_monthly.csv codebook\n\n| column | definition |\n|---|---|\n' + '\n'.join(codebook) + '\n')
print(M.shape); print(M[[c for c in M.columns if c in ('llm_news_n_relevant', 'llm_news_tone', 'llm_news_neg_share', 'llm_social_tone', 'news_n_kw', 'news_gdelt_tone', 'news_finbert_tone', 'news_claims_accurate_share')]].tail(12).round(3).to_string())
