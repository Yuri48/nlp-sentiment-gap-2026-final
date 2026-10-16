"""
prepare_corpus.py — Clean, de-duplicate and classify the news (GKG) and social (Bluesky) corpora.

Outputs (data/processed/):
  news_items.parquet      one row per unique headline with source classification and month
  social_items.parquet    one row per unique Bluesky post
  corpus_summary.md       counts, source composition, duplicates, missingness, sampling notes
  source_panel.csv        the outlet panel with group / type / audience-lean labels used for stratification
"""
import glob, html, json, os, re, sys, datetime as dt
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from collect_gdelt import GROUPS
RAW = os.path.join(ROOT, 'data', 'raw'); OUT = os.path.join(ROOT, 'data', 'processed')
os.makedirs(OUT, exist_ok=True)

# ---- Outlet panel and stratification labels ---------------------------------------------
# 'lean' = audience / rating-based label used ONLY for stratification and for the cross-source
# benchmark (AllSides media bias chart 2024, Pew Research 2020 audience ideology profile).
# It is not a judgment about accuracy.  Local outlets are coded 'local' (no lean assigned).
PANEL = {}
for g, doms in GROUPS.items():
    for d in doms:
        PANEL[d] = {'group': g, 'type': 'national' if g.startswith('N') else 'local'}
LEAN = {'apnews.com': 'center', 'reuters.com': 'center', 'cnn.com': 'lean_left', 'foxnews.com': 'right', 'nbcnews.com': 'lean_left',
        'cbsnews.com': 'lean_left', 'abcnews.go.com': 'lean_left', 'usatoday.com': 'center', 'nytimes.com': 'lean_left', 'wsj.com': 'center',
        'washingtonpost.com': 'lean_left', 'cnbc.com': 'center', 'foxbusiness.com': 'lean_right', 'marketwatch.com': 'center',
        'nypost.com': 'lean_right', 'bloomberg.com': 'center', 'huffpost.com': 'left', 'breitbart.com': 'right', 'dailycaller.com': 'right',
        'washingtonexaminer.com': 'lean_right', 'thehill.com': 'center', 'politico.com': 'lean_left', 'newsweek.com': 'center',
        'msnbc.com': 'left', 'ms.now': 'left'}
EXTRA_NATIONAL = {  # noqa
    'npr.org': 'lean_left', 'pbs.org': 'lean_left', 'time.com': 'lean_left', 'theatlantic.com': 'lean_left', 'newsmax.com': 'right',
                  'washingtontimes.com': 'lean_right', 'dailywire.com': 'right', 'theepochtimes.com': 'right', 'vox.com': 'left', 'axios.com': 'center',
                  'businessinsider.com': 'lean_left', 'forbes.com': 'center', 'fortune.com': 'center', 'thedailybeast.com': 'left', 'salon.com': 'left',
                  'slate.com': 'left', 'motherjones.com': 'left', 'nationalreview.com': 'right', 'theblaze.com': 'right', 'townhall.com': 'right',
                  'foxnews.com': 'right', 'abc7.com': 'lean_left', 'cbs.com': 'lean_left', 
                  'barrons.com': 'center', 'thestreet.com': 'center',
                  'yahoo.com': 'center', 'msn.com': 'center', 'upi.com': 'center', 'newsnationnow.com': 'center', 'nationalreview.com': 'right',
                  'realclearpolitics.com': 'lean_right', 'rawstory.com': 'left', 'commondreams.org': 'left', 'zerohedge.com': 'right',
                  'wnd.com': 'right', 'oann.com': 'right', 'thefederalist.com': 'right', 'cnsnews.com': 'right', 'pjmedia.com': 'right',
                  'redstate.com': 'right', 'hotair.com': 'right', 'freebeacon.com': 'right', 'thenation.com': 'left', 'jacobin.com': 'left',
                  'truthout.org': 'left', 'alternet.org': 'left', 'dailykos.com': 'left', 'cbsnews.com': 'lean_left', 'nbcnews.com': 'lean_left',
                  'semafor.com': 'center', 'thedispatch.com': 'lean_right', 'punchbowl.news': 'center', 'rollcall.com': 'center',
                  'washingtonmonthly.com': 'left', 'spectator.org': 'right', 'americanthinker.com': 'right', 'wnd.com': 'right',
                  'kiplinger.com': 'center', 'money.com': 'center', 'bankrate.com': 'center', 'nerdwallet.com': 'center', 'cnet.com': 'center',
                  'usnews.com': 'center', 'thehill.com': 'center', }
LOCAL_TV = re.compile(r'^(k|w)[a-z]{2,3}(tv|\d{1,2}|-tv|news|radio)?\.(com|org|net|tv)$')
LOCAL_HINT = re.compile(r'(gazette|tribune|herald|times|journal|dispatch|courier|sentinel|chronicle|observer|ledger|register|press|news-|daily|'
                        r'post-|star-|sun-|bee\.|statesman|advocate|examiner|patch\.com|nola\.|cleveland|detroit|chicago|boston|philly|'
                        r'\.ky|\.oh|wral|wfaa|kare|wkyc|wsb|wxyz|wjla|wtop|king5|kiro|komo|ktla|kcra|kxan|khou|wtae|wgal|wpxi|wesh|wftv|'
                        r'fox\d+|nbc\d+|abc\d+|cbs\d+|local|wbur|wnyc|kqed|wtae|silive|lehighvalleylive|masslive|syracuse|pennlive|nj\.com|mlive|al\.com)', re.I)

FOREIGN_TLD = re.compile(r'\.(uk|au|ca|in|ie|nz|za|ng|ke|ph|sg|hk|my|pk|lk|bd|ae|qa|sa|il|tr|ru|ua|pl|de|fr|es|it|nl|be|se|no|dk|fi|ch|at|pt|gr|cz|hu|ro|bg|hr|rs|jp|kr|cn|tw|vn|th|id|br|mx|ar|cl|co|pe|ve|eu|asia|africa|ng)$', re.I)
FOREIGN_DOMAINS = {'bbc.com', 'theguardian.com', 'ft.com', 'economist.com', 'dailymail.co.uk', 'telegraph.co.uk', 'independent.co.uk', 'rappler.com', 'philstar.com', 'aljazeera.com', 'rt.com', 'sputniknews.com', 'globaltimes.cn', 'scmp.com', 'timesofindia.com', 'ndtv.com', 'hindustantimes.com', 'thehindu.com', 'news18.com', 'cbc.ca', 'globalnews.ca', 'ctvnews.ca', 'nationalpost.com', 'theglobeandmail.com', 'abc.net.au', 'news.com.au', 'smh.com.au', 'nzherald.co.nz', 'rte.ie', 'irishtimes.com', 'euronews.com', 'dw.com', 'france24.com', 'africaleader.com', 'manilatimes.net', 'bignewsnetwork.com', 'menafn.com', 'xinhuanet.com', 'yonhapnews.co.kr', 'koreaherald.com', 'japantimes.co.jp', 'thestar.com.my', 'straitstimes.com', 'channelnewsasia.com', 'gulfnews.com', 'arabnews.com', 'dailysabah.com', 'hurriyetdailynews.com', 'themoscowtimes.com', 'kyivindependent.com', 'jpost.com', 'timesofisrael.com', 'haaretz.com', 'ynetnews.com'}

def classify_domain(d):
    if d in FOREIGN_DOMAINS or FOREIGN_TLD.search(d):
        return 'foreign', 'X', 'foreign'
    if d in PANEL:
        return PANEL[d]['type'], PANEL[d]['group'], LEAN.get(d, 'local')
    if d in EXTRA_NATIONAL:
        return 'national_other', 'X', EXTRA_NATIONAL[d]
    if LOCAL_TV.match(d) or LOCAL_HINT.search(d):
        return 'local_other', 'X', 'local'
    return 'other', 'X', 'unknown'

SUFFIX_RE = re.compile(r'\s*[\|\-–—:]\s*(CNN|Fox News|Fox Business|AP News|Reuters|NBC News|CBS News|ABC News|USA TODAY|The New York Times|WSJ|'
                       r'The Washington Post|CNBC|MarketWatch|New York Post|Bloomberg|HuffPost|Breitbart|The Daily Caller|Washington Examiner|'
                       r'The Hill|POLITICO|Newsweek|MSNBC|MS NOW|Chicago Tribune|Detroit Free Press|The Detroit News|cleveland\.com|'
                       r'Star Tribune|The Columbus Dispatch|Pittsburgh Post-Gazette|The Atlanta Journal-Constitution|Tampa Bay Times|Miami Herald|'
                       r'The Dallas Morning News|Houston Chronicle|The Arizona Republic|Las Vegas Review-Journal|The Charlotte Observer|'
                       r'Los Angeles Times|San Francisco Chronicle|The Seattle Times|The Denver Post|oregonlive\.com|The Philadelphia Inquirer|'
                       r'The Boston Globe|Kansas City Star|Milwaukee Journal Sentinel|[A-Z][\w\.\s&]{2,30})\s*$')

def clean_title(t):
    t = html.unescape(t or '')
    t = re.sub(r'\s+', ' ', t).strip()
    t2 = SUFFIX_RE.sub('', t)
    if len(t2) >= 20:
        t = t2
    t = re.sub(r'^\s*(VIDEO|WATCH|LIVE|OPINION|Opinion|Analysis|ANALYSIS|Editorial|Letters?)\s*[:|\-–]\s*', '', t)
    return t.strip()

def norm_title(t):
    return re.sub(r'[^a-z0-9 ]', '', t.lower()).strip()

# ---- News ----------------------------------------------------------------------------
files = sorted(glob.glob(os.path.join(RAW, 'gkg', 'items_*.jsonl')))
rows = []
for fn in files:
    with open(fn, encoding='utf-8') as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
news = pd.DataFrame(rows)
n_raw = len(news)
news['title_clean'] = news['title'].map(clean_title)
news['title_len'] = news['title_clean'].str.len()
news = news[(news['title_len'] >= 25) & (news['title_len'] <= 300)]
junk = news['title_clean'].str.contains(r'^(?:page not found|404|access denied|subscribe|sign in|log in|privacy policy|home\b)', case=False, regex=True)
news = news[~junk]
n_after_clean = len(news)
news['datetime'] = pd.to_datetime(news['datetime'], format='%Y%m%d%H%M%S', utc=True)
news['date'] = news['datetime'].dt.tz_convert('US/Eastern').dt.date
news['month'] = pd.to_datetime(news['date']).dt.to_period('M').astype(str)
news['url_key'] = news['url'].str.lower().str.replace(r'^https?://(www\.)?', '', regex=True).str.rstrip('/')
news = news.sort_values('datetime')
news = news.drop_duplicates('url_key')
n_after_url = len(news)
news['title_norm'] = news['title_clean'].map(norm_title)
# same normalised title on the same day across any domain => wire reprint; keep first, count copies
grp = news.groupby(['title_norm', 'date'])
news['n_reprints'] = grp['url_key'].transform('count') - 1
news = news.drop_duplicates(['title_norm', 'date'])
# same title within 7 days at the same domain => republish; drop
news['week'] = pd.to_datetime(news['date']).dt.to_period('W').astype(str)
news = news.drop_duplicates(['title_norm', 'domain', 'week'])
n_after_title = len(news)
cls = news['domain'].map(classify_domain)
news['source_type'] = [c[0] for c in cls]; news['source_group'] = [c[1] for c in cls]; news['source_lean'] = [c[2] for c in cls]
KW = re.compile(r'\b(?:econom\w*|inflation\w*|prices?|unemploy\w*|jobs?|jobless|layoffs?|laid off|hiring|recession|wages?|tariffs?|interest rates?|'
                r'the fed|federal reserve|fed (?:hike|cut|rate|chair|meeting|decision|officials?)|rate (?:hike|cut)s?|gdp|cost of living|mortgage rates?|'
                r'housing (?:market|costs?|prices?|affordability)|home prices?|rents?|gas prices?|gasoline|consumer(?:s| sentiment| confidence| spending| prices)|'
                r'paychecks?|groceries|grocery|stagflation|downturn|slowdown|payrolls?|cpi|pce|retail sales|household budgets?|'
                r'minimum wage|labor market|job market|jobs report|wall street|stock market|treasury yields?|affordability)\b', re.I)
news['kw_title'] = news['title_clean'].str.contains(KW)
news['item_id'] = 'n' + news['gkg_id'].str.replace('-', '_')
keep_cols = ['item_id', 'datetime', 'date', 'month', 'domain', 'source_type', 'source_group', 'source_lean', 'in_panel', 'url', 'title_clean',
             'title_source', 'themes', 'econ_theme', 'kw_hit', 'kw_title', 'tone', 'tone_pos', 'tone_neg', 'polarity', 'wordcount', 'n_reprints', 'us_loc']
news = news[keep_cols].rename(columns={'title_clean': 'text'})
news.to_parquet(os.path.join(OUT, 'news_items.parquet'), index=False)

# ---- Social ----------------------------------------------------------------------------
soc_fn = os.path.join(RAW, 'bluesky', 'posts.jsonl')
soc = pd.DataFrame([json.loads(l) for l in open(soc_fn, encoding='utf-8')]) if os.path.exists(soc_fn) else pd.DataFrame()
if len(soc):
    s_raw = len(soc)
    soc = soc.drop_duplicates('uri')
    soc['created_at'] = pd.to_datetime(soc['created_at'], errors='coerce', utc=True)
    soc = soc.dropna(subset=['created_at'])
    soc = soc[(soc['created_at'] >= '2023-01-01') & (soc['created_at'] <= pd.Timestamp.now(tz='UTC'))]
    soc['date'] = soc['created_at'].dt.tz_convert('US/Eastern').dt.date
    soc['month'] = pd.to_datetime(soc['date']).dt.to_period('M').astype(str)
    soc['text'] = soc['text'].str.replace(r'\s+', ' ', regex=True).str.strip()
    # privacy: mask @-mentions, bare handles and DIDs of other accounts
    soc['text'] = (soc['text'].str.replace(r'@/?[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+', '@user', regex=True)
                   .str.replace(r'[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*\.bsky\.social', 'user.bsky.social', regex=True)
                   .str.replace(r'did:plc:[a-z0-9]+', 'did:plc:user', regex=True))
    soc = soc[soc['text'].str.len() >= 15]
    nolink = soc['text'].str.replace(r'https?://\S+|\S+\.(?:com|org|net|co|gov|info|news|io|us|me|tv)\S*', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
    soc = soc[(nolink.str.len() >= 20) & (nolink.str.split().str.len() >= 4)]   # drop link-only posts
    soc['has_link'] = soc['text'].str.contains(r'https?://|\.com\b|\.org\b', regex=True)
    soc['text_norm'] = soc['text'].map(norm_title)
    soc['n_copies'] = soc.groupby('text_norm')['uri'].transform('count') - 1
    soc = soc.drop_duplicates('text_norm')            # copy-pasta / bot duplicates
    soc['engagement'] = soc[['like_count', 'repost_count', 'reply_count', 'quote_count']].fillna(0).sum(axis=1)
    soc['item_id'] = 's' + soc['uri'].str.extract(r'/([a-z0-9]+)$')[0]
    soc['item_id'] = soc['item_id'].fillna(pd.Series('s' + soc.index.astype(str), index=soc.index))
    soc = soc[['item_id', 'created_at', 'date', 'month', 'text', 'like_count', 'repost_count', 'reply_count', 'quote_count', 'engagement',
               'has_link', 'has_embed', 'is_reply', 'n_copies', '_query']].rename(columns={'_query': 'query'})
    soc.to_parquet(os.path.join(OUT, 'social_items.parquet'), index=False)

# ---- Panel file and summary -----------------------------------------------------------
pd.DataFrame([{'domain': d, 'group': v['group'], 'type': v['type'], 'lean': LEAN.get(d, 'local')} for d, v in PANEL.items()]).to_csv(os.path.join(OUT, 'source_panel.csv'), index=False)
with open(os.path.join(OUT, 'corpus_summary.md'), 'w') as f:
    f.write(f'# Corpus summary (prepare_corpus.py, {dt.date.today()})\n\n## News (GDELT GKG slices)\n')
    f.write(f'* Raw records kept at collection: {n_raw:,}\n* After title cleaning / length filter: {n_after_clean:,}\n* After URL de-duplication: {n_after_url:,}\n'
            f'* After same-day wire-reprint and same-week republish removal: {n_after_title:,} unique headlines\n')
    f.write(f'* Months covered: {news["month"].min()} .. {news["month"].max()}; headlines with economic keyword in title: {int(news["kw_title"].sum()):,}\n')
    f.write(f'* Title source: {news["title_source"].value_counts().to_dict()}\n\n### Source composition (unique headlines)\n')
    f.write(news['source_type'].value_counts().to_frame('n').to_markdown() + '\n\n')
    f.write('### Named panel outlets (unique headlines)\n')
    f.write(news[news['in_panel']]['domain'].value_counts().to_frame('n').to_markdown() + '\n\n')
    f.write('### Top other domains\n' + news[~news['in_panel']]['domain'].value_counts().head(40).to_frame('n').to_markdown() + '\n\n')
    f.write('### Headlines per month (all / panel)\n')
    pm = news.groupby('month').agg(all=('item_id', 'count'), panel=('in_panel', 'sum'), kw=('kw_title', 'sum'))
    f.write(pm.to_markdown() + '\n\n')
    if len(soc):
        f.write(f'## Social (Bluesky)\n* Raw posts collected: {s_raw:,}; unique after de-duplication: {len(soc):,}\n'
                f'* Months: {soc["month"].min()} .. {soc["month"].max()}\n* Share replies: {soc["is_reply"].mean():.2f}; share with link: {soc["has_link"].mean():.2f}; '
                f'posts with >=1 copy (suspected copy-pasta/bots): {(soc["n_copies"]>0).mean():.3f}\n')
        f.write('### Posts per month and query\n' + soc.pivot_table(index='month', columns='query', values='item_id', aggfunc='count').fillna(0).astype(int).to_markdown() + '\n')
print(open(os.path.join(OUT, 'corpus_summary.md')).read()[:3000])
