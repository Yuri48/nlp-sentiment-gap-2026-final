"""
collect_fred_alfred.py — Macro controls (FRED) and real-time data vintages (ALFRED).

* FRED series are downloaded as CSV from fredgraph.csv (no API key needed); each file is
  stamped with the download date so provenance is explicit.
* ALFRED vintages: for the three core indicators (UNRATE, PCEPI, GDPC1) we download the
  data AS IT WAS KNOWN on the 15th of every month from 2009-01 to today.  This lets the
  economic-only model use only information available at each prediction date and lets us
  measure GDP revisions (advance vs. latest estimate).
"""
import os, time, datetime as dt, io
import requests, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRED_DIR = os.path.join(ROOT, 'data', 'raw', 'fred')
ALF_DIR = os.path.join(ROOT, 'data', 'raw', 'alfred')
os.makedirs(FRED_DIR, exist_ok=True); os.makedirs(ALF_DIR, exist_ok=True)
UA = 'NLP-course-research/0.1'

FRED_SERIES = {
    # id: (description, frequency, units, source agency)
    'UMCSENT': ('University of Michigan: Consumer Sentiment (headline index)', 'M', 'Index 1966Q1=100', 'UMich via FRED'),
    'MICH': ('University of Michigan: 1-year inflation expectation (median)', 'M', 'percent', 'UMich via FRED'),
    'UNRATE': ('Civilian unemployment rate U-3, SA', 'M', 'percent', 'BLS'),
    'U6RATE': ('Total unemployed + marginally attached + part-time for economic reasons (U-6), SA', 'M', 'percent', 'BLS'),
    'PAYEMS': ('Total nonfarm payroll employment, SA', 'M', 'thousands', 'BLS'),
    'PCEPI': ('PCE price index, SA', 'M', 'Index 2017=100', 'BEA'),
    'PCEPILFE': ('PCE price index excluding food and energy, SA', 'M', 'Index 2017=100', 'BEA'),
    'CPIAUCSL': ('CPI-U all items, SA', 'M', 'Index 1982-84=100', 'BLS'),
    'CPIUFDSL': ('CPI-U food, SA', 'M', 'Index 1982-84=100', 'BLS'),
    'CUSR0000SEHA': ('CPI-U rent of primary residence, SA', 'M', 'Index 1982-84=100', 'BLS'),
    'GASREGW': ('US regular all formulations gasoline price', 'W', 'dollars per gallon', 'EIA'),
    'GDPC1': ('Real GDP, SAAR', 'Q', 'billions of chained 2017 dollars', 'BEA'),
    'A229RX0': ('Real disposable personal income per capita', 'M', 'chained 2017 dollars', 'BEA'),
    'DSPIC96': ('Real disposable personal income', 'M', 'billions chained 2017 dollars', 'BEA'),
    'PSAVERT': ('Personal saving rate', 'M', 'percent', 'BEA'),
    'TDSP': ('Household debt service payments as % of disposable income', 'Q', 'percent', 'Federal Reserve'),
    'MORTGAGE30US': ('30-year fixed mortgage rate', 'W', 'percent', 'Freddie Mac'),
    'MSPUS': ('Median sales price of houses sold', 'Q', 'dollars', 'Census/HUD'),
    'USEPUINDXM': ('Economic Policy Uncertainty index (Baker-Bloom-Davis), monthly', 'M', 'index', 'policyuncertainty.com via FRED'),
    'FEDFUNDS': ('Effective federal funds rate', 'M', 'percent', 'Federal Reserve'),
    'LES1252881600Q': ('Median usual weekly real earnings, full-time wage & salary workers', 'Q', '1982-84 dollars', 'BLS'),
    'RSXFS': ('Advance retail sales ex food services', 'M', 'millions of dollars', 'Census'),
    'USREC': ('NBER recession indicator', 'M', '0/1', 'NBER via FRED'),
    'SP500': ('S&P 500 index (daily)', 'D', 'index', 'S&P via FRED'),
}

ALFRED_SERIES = ['UNRATE', 'PCEPI', 'GDPC1', 'PAYEMS']


def get_fred(sid):
    r = requests.get('https://fred.stlouisfed.org/graph/fredgraph.csv', params={'id': sid}, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ['date', sid]
    return df


def get_alfred(sid, vintage):
    r = requests.get('https://alfred.stlouisfed.org/graph/alfredgraph.csv', params={'id': sid, 'vintage_date': vintage}, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ['date', 'value']
    df['vintage'] = vintage
    return df


def main():
    stamp = dt.date.today().isoformat()
    meta = []
    for sid, (desc, freq, units, src) in FRED_SERIES.items():
        try:
            df = get_fred(sid)
            df.to_csv(os.path.join(FRED_DIR, f'{sid}.csv'), index=False)
            meta.append({'series_id': sid, 'description': desc, 'frequency': freq, 'units': units, 'source': src,
                         'n_obs': int(df[sid].notna().sum()), 'first': df['date'].iloc[0], 'last': df['date'].iloc[-1],
                         'downloaded': stamp, 'url': f'https://fred.stlouisfed.org/series/{sid}'})
            print(f'FRED {sid}: {len(df)} rows, last {df["date"].iloc[-1]}', flush=True)
        except Exception as e:
            print(f'FRED {sid} FAILED: {e}', flush=True)
        time.sleep(0.5)
    pd.DataFrame(meta).to_csv(os.path.join(FRED_DIR, '_provenance.csv'), index=False)

    # ALFRED vintages, 15th of each month
    vintages = pd.date_range('2009-01-15', dt.date.today(), freq='MS') + pd.Timedelta(days=14)
    vintages = [v.date().isoformat() for v in vintages if v.date() <= dt.date.today()]
    # also today's vintage
    vintages.append(dt.date.today().isoformat())
    for sid in ALFRED_SERIES:
        frames = []
        for v in vintages:
            fn = os.path.join(ALF_DIR, f'{sid}_{v}.csv')
            if os.path.exists(fn):
                frames.append(pd.read_csv(fn)); continue
            for attempt in range(4):
                try:
                    df = get_alfred(sid, v); df.to_csv(fn, index=False); frames.append(df); break
                except Exception as e:
                    print(f'ALFRED {sid} {v} attempt {attempt} failed: {e}', flush=True); time.sleep(5)
            time.sleep(0.4)
        allv = pd.concat(frames, ignore_index=True)
        allv.to_csv(os.path.join(ALF_DIR, f'{sid}_all_vintages.csv'), index=False)
        print(f'ALFRED {sid}: {len(vintages)} vintages, {len(allv)} rows', flush=True)
    print('FINISHED')


if __name__ == '__main__':
    main()
