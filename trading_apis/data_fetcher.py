import pandas as pd
import requests
from typing import Optional, List
from config import FMP_BASE_URL, FMP_API_KEY, IST_TZ, INTERVAL_MAP
from indicators import calculate_all_indicators
from strategies import evaluate_15m_strategy, evaluate_5m_strategy, evaluate_3m_strategy

def fetch_data(symbol: str, interval: int, start_time=None, end_time=None):
    """Fetch data from FMP API"""
    # Map common index names to their FMP API ticker format
    index_map = {
        'NIFTY': '^NSEI',           # Nifty 50
        'BANKNIFTY': '^NSEBANK',    # Nifty Bank
    }
    symbol_upper = symbol.upper()

    clean_symbol = index_map.get(symbol_upper, symbol)

    fmp_interval = INTERVAL_MAP.get(interval)
    if not fmp_interval:
        raise ValueError(f"Unsupported interval: {interval}m")
    
    url = f"{FMP_BASE_URL}/{fmp_interval}/{clean_symbol}?apikey={FMP_API_KEY}"
    
    if start_time and end_time:
        from_date = start_time.strftime('%Y-%m-%d')
        to_date = end_time.strftime('%Y-%m-%d')
        url += f"&from={from_date}&to={to_date}"
    
    print(f"Fetching from FMP: {url}")
    resp = requests.get(url)
    
    if resp.status_code != 200:
        raise ValueError(f"FMP API error: {resp.text}")
    
    data = resp.json()
    if not data:
        raise ValueError(f"No data returned from FMP for {symbol}")
    
    df = pd.DataFrame(data)
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'date': 'datetime'
    }, inplace=True)
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    if df['datetime'].dt.tz is None:
        df['datetime'] = df['datetime'].dt.tz_localize(IST_TZ)
    else:
        df['datetime'] = df['datetime'].dt.tz_convert(IST_TZ)
    
    df = df.sort_values('datetime').set_index('datetime')
    
    if interval == 3:
        df = (
            df.resample('3min')
              .agg({'Open': 'first', 'High': 'max', 'Low': 'min',
                    'Close': 'last', 'Volume': 'sum'})
              .dropna()
        )
    
    if start_time and end_time:
        df = df.loc[start_time:end_time]
    
    return df.dropna().sort_index()

def fetch_and_process(symbol: str, interval: int, start_time=None, end_time=None):
    """Fetch data and calculate indicators"""
    df = fetch_data(symbol, interval, start_time, end_time)
    df = calculate_all_indicators(df)
    return df

def combine_timeframes(symbol: str, timeframes: List[int], start_time=None, end_time=None):
    """Combine multiple timeframes for multi-timeframe analysis"""
    dfs = {}
    
    for tf in timeframes:
        try:
            df = fetch_and_process(symbol, tf, start_time, end_time)
            if df.empty:
                continue
            
            # Evaluate signals based on timeframe
            if tf == 15:
                df = evaluate_15m_strategy(df)
            elif tf == 5:
                df = evaluate_5m_strategy(df)
            elif tf == 3:
                df = evaluate_3m_strategy(df)
            
            dfs[tf] = df
        except ValueError as e:
            print(f"Could not process timeframe {tf}m for {symbol}: {e}")
            continue
    
    if not dfs:
        return pd.DataFrame()
    
    # Align to lowest timeframe
    min_tf = min(timeframes)
    if min_tf not in dfs:
        return pd.DataFrame()
    
    combined = dfs[min_tf].copy()
    
    for tf, df in dfs.items():
        if tf != min_tf:
            combined = pd.merge_asof(
                left=combined.sort_index(),
                right=df.sort_index(),
                left_index=True,
                right_index=True,
                direction='backward',
                suffixes=('', f'_{tf}')
            )
    
    return combined.ffill().bfill()