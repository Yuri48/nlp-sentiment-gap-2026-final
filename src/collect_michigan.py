"""
collect_michigan.py — Download University of Michigan Surveys of Consumers tables.

The Surveys of Consumers data archive (https://data.sca.isr.umich.edu/tables.php) publishes
Excel tables.  Download links carry a per-session key, so we parse the page each run.
Tables used (variant RB = historical monthly series, see README):
  1a  Index of Consumer Sentiment               1b  Components (ICS, Current, Expected)
  2n  ICS/Current/Expected by income tercile    3n  by age        4n  by education
  5a  by region                                 5b  by political party
  23  News heard of recent changes in business conditions (favorable/unfavorable)
  24  News items heard (specific items: prices, unemployment, government, ...)
  32  Expected change in prices next year       34  Opinions about government's economic policy
"""
import os, re, html, time, datetime as dt, sys
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'data', 'raw', 'michigan')
os.makedirs(OUT, exist_ok=True)
BASE = 'https://data.sca.isr.umich.edu/'
UA = 'Mozilla/5.0 NLP-course-research'
TABLES = ['1a', '1b', '2n', '3n', '4n', '5a', '5b', '6', '23', '24', '25', '30', '32', '34']
VARIANTS = sys.argv[1].split(',') if len(sys.argv) > 1 else ['RB']

s = requests.Session(); s.headers['User-Agent'] = UA
page = s.get(BASE + 'tables.php', timeout=60).text
links = re.findall(r'data-docname="([A-Z]+) ([0-9a-z]+)" href="(get-table\.php\?[^"]+f=xls[^"]*)"', page)
print('links found', len(links))
# column headings (to document what YB/BB/GB/RB mean)
heads = re.findall(r'<div class="grid_2 tables_heading">\s*(.*?)\s*</div>', page, flags=re.S)
print('headings:', [re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', h))).strip() for h in heads])
for variant, tbl, href in links:
    if tbl not in TABLES or variant not in VARIANTS:
        continue
    url = BASE + html.unescape(href)
    fn = os.path.join(OUT, f'{variant}_{tbl}.xls')
    r = s.get(url, timeout=60, headers={'Referer': BASE + 'tables.php'})
    open(fn, 'wb').write(r.content)
    print(variant, tbl, r.status_code, len(r.content), r.headers.get('content-type'), flush=True)
    time.sleep(1.0)
open(os.path.join(OUT, '_downloaded.txt'), 'w').write(dt.date.today().isoformat() + '\n')
