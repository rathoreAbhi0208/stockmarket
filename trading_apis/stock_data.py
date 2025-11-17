import pandas as pd
import numpy as np
import yfinance as yf

# --- Fetch sample data (15-minute candles for any stock) ---
data = yf.download("AAPL", period="5d", interval="15m")
data = data[['Open', 'High', 'Low', 'Close']]

# --- Compute EMAs ---
data['EMA_5'] = data['Close'].ewm(span=5, adjust=False).mean()
data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()
data['EMA_200'] = data['Close'].ewm(span=200, adjust=False).mean()

# --- Compute Stochastic Oscillator ---
low14 = data['Low'].rolling(window=14).min()
high14 = data['High'].rolling(window=14).max()
data['%K'] = 100 * ((data['Close'] - low14) / (high14 - low14))
data['%D'] = data['%K'].rolling(window=3).mean()

# --- Generate Crossover Signals ---
data['EMA_Signal'] = np.where(data['EMA_5'] > data['EMA_20'], 1, -1)
data['Stoch_Cross'] = np.where((data['%K'] > data['%D']), 1, -1)

# --- Combine Logic for Final Signal ---
def signal(row):
    try:
        close = float(row['Close'])
        ema_20 = float(row['EMA_20'])
        ema_200 = float(row['EMA_200'])
        stoch_cross = int(row['Stoch_Cross'])
        
        if close > ema_20 and stoch_cross == 1 and ema_200 < close:
            return "BUY"
        elif close < ema_20 and stoch_cross == -1 and ema_200 > close:
            return "SELL"
        else:
            return "HOLD"
    except:
        return "HOLD"

data['Signal'] = data.apply(signal, axis=1)

# --- Display last few rows ---
print(data[['Close', 'EMA_5', 'EMA_20', 'EMA_200', '%K', '%D', 'Signal']].tail(20))

###########################
from fastapi import FastAPI, Query
from typing import List
import pandas as pd
import numpy as np
import pytz
import requests
from tvDatafeed import TvDatafeed, Interval

# Initialize TV data feed
tv = TvDatafeed()

app = FastAPI(title="EMA Multi-Timeframe Indicator API")

# --- Indicator Calculation ---
def compute_indicators(df):
    # Create a copy of the dataframe and reset index to ensure alignment
    df = df.copy()
    
    # Calculate EMAs and SMAs
    close_series = df['Close'].astype(float)
    df['EMA_5'] = close_series.ewm(span=5, adjust=False).mean()
    df['EMA_20'] = close_series.ewm(span=20, adjust=False).mean()
    df['EMA_200'] = close_series.ewm(span=200, adjust=False).mean()
    df['SMA_9'] = close_series.rolling(window=9).mean()
    df['SMA_50'] = close_series.rolling(window=50).mean()
    
    # Calculate RSI
    delta = close_series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate MACD
    exp1 = close_series.ewm(span=12, adjust=False).mean()
    exp2 = close_series.ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
    
    # Calculate Heikin-Ashi
    df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close'])/4
    df['HA_Open'] = df['Open'].copy()
    for i in range(1, len(df)):
        df.iloc[i, df.columns.get_loc('HA_Open')] = (df.iloc[i-1, df.columns.get_loc('HA_Open')] + 
                                                    df.iloc[i-1, df.columns.get_loc('HA_Close')]) / 2
    df['HA_High'] = df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    df['HA_Low'] = df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)

    # Calculate Stochastic with aligned data
    low_series = df['Low'].astype(float)
    high_series = df['High'].astype(float)
    
    low14 = low_series.rolling(window=14).min()
    high14 = high_series.rolling(window=14).max()
    
    # Calculate %K with safe division
    df['%K'] = pd.Series(index=df.index)  # Initialize empty series with same index
    denominator = (high14 - low14)
    valid_denom = denominator != 0
    
    df.loc[valid_denom, '%K'] = 100 * ((close_series - low14) / denominator)[valid_denom]
    df.loc[~valid_denom, '%K'] = 50  # Set to middle value where denominator is zero
    
    # Calculate %D
    df['%D'] = df['%K'].rolling(window=3).mean()
    
    # Calculate Stochastic Cross with aligned data
    df['Stoch_Cross'] = 0  # Initialize with neutral value
    valid_rows = df['%K'].notna() & df['%D'].notna()
    df.loc[valid_rows, 'Stoch_Cross'] = np.where(
        df.loc[valid_rows, '%K'] > df.loc[valid_rows, '%D'],
        1, -1
    )
    
    # Forward fill any remaining NaN values
    df = df.ffill().bfill()  # Forward fill then backward fill any remaining NaNs
    
    return df

def evaluate_15m(df):
    """
    15-Minute Timeframe Strategy
    --------------------------------
    Conditions:
    1. Trend Filter: 200 EMA defines trend direction.
       - Only BUY if price > EMA_200
       - Only SELL if price < EMA_200
    2. Entry Trigger: EMA(5) crosses EMA(20)
    3. Confirmation: Stochastic crossover in same direction
    """
    
    df = df.copy()
    df['Signal_15m'] = 'HOLD'
    df['Pass_15m'] = False
    
    # --- Trend Filter ---
    # The 200-period EMA is the primary filter for the overall trend direction.
    close_above_ema200 = df['Close'] > df['EMA_200']
    close_below_ema200 = df['Close'] < df['EMA_200']
    
    # --- Trigger Conditions ---
    # A candle closes above/below the 20 EMA. We check the previous close vs the current close.
    close_crossed_above_ema20 = (df['Close'].shift(1) <= df['EMA_20'].shift(1)) & (df['Close'] > df['EMA_20'])
    close_crossed_below_ema20 = (df['Close'].shift(1) >= df['EMA_20'].shift(1)) & (df['Close'] < df['EMA_20'])

        # --- EMA Crossover 1 (Short vs Long) ---
    ema_fast = df['EMA_5']
    ema_slow = df['EMA_20']

    # Detect crossovers
    ema_cross_up = (ema_fast.shift(1) <= ema_slow.shift(1)) & (ema_fast > ema_slow)
    ema_cross_down = (ema_fast.shift(1) >= ema_slow.shift(1)) & (ema_fast < ema_slow)
    
    # Stochastic gives a crossover.
    stoch_buy_signal = df['Stoch_Cross'] == 1
    stoch_sell_signal = df['Stoch_Cross'] == -1
    
    # --- Final Buy/Sell Conditions ---
    # For a BUY, trend must be up (price > 200 EMA) and both trigger conditions must be met.
    buy_conditions = close_above_ema200 & ema_cross_up & stoch_buy_signal
    
    # For a SELL, trend must be down (price < 200 EMA) and both trigger conditions must be met.
    sell_conditions = close_below_ema200 & ema_cross_down & stoch_sell_signal
    
    df.loc[buy_conditions, 'Signal_15m'] = 'BUY'
    df.loc[sell_conditions, 'Signal_15m'] = 'SELL'
    df.loc[buy_conditions | sell_conditions, 'Pass_15m'] = True
    
    return df

def evaluate_5m(df):
    """
    5-Minute Timeframe (Momentum / Entry Filter)
    --------------------------------------------
    BUY:  SMA_9 crosses above SMA_50  AND RSI > 60
    SELL: SMA_9 crosses below SMA_50  AND RSI < 40
    """

    df = df.copy()
    df['Signal_5m'] = 'HOLD'
    df['Pass_5m'] = False
    
    # SMA Crossover conditions
    sma9_above_sma50 = df['SMA_9'] > df['SMA_50']
    
    # RSI conditions
    rsi_above_60 = df['RSI'] > 60
    rsi_below_40 = df['RSI'] < 40

    # --- Detect SMA crossovers ---
    sma_cross_up = (df['SMA_9'].shift(1) <= df['SMA_50'].shift(1)) & (df['SMA_9'] > df['SMA_50'])
    sma_cross_down = (df['SMA_9'].shift(1) >= df['SMA_50'].shift(1)) & (df['SMA_9'] < df['SMA_50'])    
    
    # Buy conditions
    buy_conditions = (sma_cross_up  & rsi_above_60)
    
    # Sell conditions
    sell_conditions = (sma_cross_down  & rsi_below_40)
    
    df.loc[buy_conditions, 'Signal_5m'] = 'BUY'
    df.loc[sell_conditions, 'Signal_5m'] = 'SELL'
    df.loc[buy_conditions | sell_conditions, 'Pass_5m'] = True
    
    return df

import pandas as pd
import numpy as np

def evaluate_3m(df):
    """
    3-Minute Timeframe (Final Confirmation/Execution)
    Strategy:
      - Uses Heikin Ashi candles, EMA(5,9), and MACD (12,26,9)
    """
    df = df.copy()
    df['Signal_3m'] = 'HOLD'
    df['Pass_3m'] = False

    # --- Compute Heikin Ashi candles ---
    df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4
    df['HA_Open'] = (df['Open'].shift(1) + df['Close'].shift(1)) / 2
    # df['HA_Open'].iloc[0] = (df['Open'].iloc[0] + df['Close'].iloc[0]) / 2
    df.loc[df.index[0], 'HA_Open'] = (df.loc[df.index[0], 'Open'] + df.loc[df.index[0], 'Close']) / 2
    df['HA_High'] = df[['High', 'HA_Open', 'HA_Close']].max(axis=1)
    df['HA_Low'] = df[['Low', 'HA_Open', 'HA_Close']].min(axis=1)

    # --- Compute EMA 5 and EMA 9 ---
    df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['EMA_9'] = df['Close'].ewm(span=9, adjust=False).mean()

    # --- Detect EMA crossover ---
    ema_cross_up = (df['EMA_5'].shift(1) <= df['EMA_9'].shift(1)) & (df['EMA_5'] > df['EMA_9'])
    ema_cross_down = (df['EMA_5'].shift(1) >= df['EMA_9'].shift(1)) & (df['EMA_5'] < df['EMA_9'])

    # --- Compute MACD ---
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']

    # --- MACD signals ---
    macd_buy = (df['MACD'] > df['Signal_Line']) & (df['MACD_Hist'] > 0)
    macd_sell = (df['MACD'] < df['Signal_Line']) & (df['MACD_Hist'] < 0)

    # --- Heikin Ashi trend ---
    ha_bullish = df['HA_Close'] > df['HA_Open']
    ha_bearish = df['HA_Close'] < df['HA_Open']

    # --- Final conditions ---
    buy_conditions = ema_cross_up & macd_buy & ha_bullish
    sell_conditions = ema_cross_down & macd_sell & ha_bearish

    # --- Mark signals ---
    df.loc[buy_conditions, 'Signal_3m'] = 'BUY'
    df.loc[sell_conditions, 'Signal_3m'] = 'SELL'
    df.loc[buy_conditions | sell_conditions, 'Pass_3m'] = True

    return df



def generate_signal(df):
    # Ensure all required columns exist and are properly aligned
    required_columns = ['Close', 'EMA_20', 'EMA_200', 'Stoch_Cross']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Convert to numeric type if needed and handle any NaN values
    for col in ['Close', 'EMA_20', 'EMA_200']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    df['Stoch_Cross'] = pd.to_numeric(df['Stoch_Cross'], errors='coerce').fillna(0)
    
    # Create aligned Series for comparison
    close_gt_ema20 = df['Close'] > df['EMA_20']
    close_gt_ema200 = df['Close'] > df['EMA_200']
    stoch_buy = df['Stoch_Cross'] == 1
    
    close_lt_ema20 = df['Close'] < df['EMA_20']
    close_lt_ema200 = df['Close'] < df['EMA_200']
    stoch_sell = df['Stoch_Cross'] == -1
    
    # Generate signals using aligned conditions
    conditions = [
        (close_gt_ema20 & close_gt_ema200 & stoch_buy),
        (close_lt_ema20 & close_lt_ema200 & stoch_sell)
    ]
    choices = ['BUY', 'SELL']
    df['Signal'] = np.select(conditions, choices, default='HOLD')
    
    return df

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3/historical-chart"
FMP_API_KEY = "84y12ovhukWyiW2v1MjL4bxx8TXskGOb"

def fetch_and_process(symbol: str, interval: int, start_time=None, end_time=None):
    """
    Fetch data from Financial Modeling Prep (FMP) API and compute indicators.
    Only for Indian stocks (.NS, .BSE) — all timestamps converted to IST.
    """

    import pytz
    from datetime import datetime

    ist_tz = pytz.timezone("Asia/Kolkata")

    # --- Clean symbol ---
    clean_symbol = symbol.replace(".BSE", ".NS") if ".BSE" in symbol else symbol

    interval_map = {
        1: "1min",
        3: "1min",   # Will resample to 3m
        5: "5min",
        15: "15min",
        30: "30min",
        60: "1hour"
    }
    fmp_interval = interval_map.get(interval)
    if not fmp_interval:
        raise ValueError(f"Unsupported interval: {interval}m")

    # --- Prepare time parameters for FMP API ---
    # FMP expects time parameters in the timezone of the exchange
    # For Indian stocks, we need to pass IST times
    url = f"{FMP_BASE_URL}/{fmp_interval}/{clean_symbol}?apikey={FMP_API_KEY}"
    
    if start_time and end_time:
        # Convert IST times to date strings for FMP API
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

    # --- Convert to DataFrame ---
    df = pd.DataFrame(data)
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'date': 'datetime'
    }, inplace=True)

    # --- Convert datetime to IST ---
    # Debug: Check what timezone FMP is actually using
    print(f"Sample raw timestamps from FMP: {df['datetime'].head(3).tolist()}")
    
    # Try parsing as naive datetime first, then localize to IST
    # FMP seems to return timestamps already in the exchange's local time
    df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Check if timestamps are timezone-aware
    if df['datetime'].dt.tz is None:
        # If naive, assume they're already in IST
        print("Timestamps are naive (no timezone), localizing to IST")
        df['datetime'] = df['datetime'].dt.tz_localize(ist_tz)
    else:
        # If aware, convert to IST
        print(f"Timestamps have timezone: {df['datetime'].dt.tz}, converting to IST")
        df['datetime'] = df['datetime'].dt.tz_convert(ist_tz)

    # --- Sort & set index ---
    df = df.sort_values('datetime').set_index('datetime')

    # --- Resample if 3min ---
    if interval == 3:
        df = (
            df.resample('3min')
              .agg({'Open': 'first', 'High': 'max', 'Low': 'min',
                    'Close': 'last', 'Volume': 'sum'})
              .dropna()
        )

    # --- Filter custom time range ---
    if start_time and end_time:
        print(f"Filtering data from {start_time} to {end_time} (IST)")
        print(f"Available data range: {df.index.min()} to {df.index.max()}")
        df = df.loc[start_time:end_time]
        print(f"After filtering: {len(df)} rows")

    # --- Compute indicators ---
    df = df.dropna().sort_index()
    df = compute_indicators(df)
    return df



# --- Final Aggregation ---
def combine_timeframes(symbol: str, timeframes: List[int], start_time=None, end_time=None):
    dfs = {}
    for tf in timeframes:
        try:
            df = fetch_and_process(symbol, tf, start_time, end_time)
            if df.empty:
                continue
            
            # Evaluate signals based on timeframe
            if tf == 15:
                df = evaluate_15m(df)
            elif tf == 5:
                df = evaluate_5m(df)
            elif tf == 3: # Assuming 3m is the execution timeframe
                df = evaluate_3m(df) # Use the execution logic for the 3m signal
            
            dfs[tf] = df
        except ValueError as e:
            print(f"Could not process timeframe {tf}m for {symbol}: {e}")
            continue

    if not dfs:
        return pd.DataFrame()
    
    # Align to lowest timeframe (smallest interval) for the desired output frequency
    min_tf = min(timeframes)
    if min_tf not in dfs: # Handle case where lowest timeframe fetch failed
        return pd.DataFrame()
        
    combined = dfs[min_tf].copy()

    for tf, df in dfs.items():
        if tf != min_tf:
            # Ensure both dataframes are sorted by index before merging
            combined = pd.merge_asof(left=combined.sort_index(), 
                                     right=df.sort_index(), 
                                     left_index=True, right_index=True,
                                     direction='backward', suffixes=('', f'_{tf}'))

    return combined.ffill().bfill()

# --- FastAPI Route ---
from fastapi import Query, HTTPException

@app.get("/indicator")
def get_indicator(
    symbol: str = Query(default="RELIANCE.NS", description="Stock symbol (e.g., RELIANCE, TCS, ITC)"),
    start_time: str = Query(default=None, description="Start time in format 'YYYY-MM-DD HH:mm' IST (optional)"),
    end_time: str = Query(default=None, description="End time in format 'YYYY-MM-DD HH:mm' IST (optional)")
):
    import pytz
    from datetime import datetime, timedelta
    
    ist_tz = pytz.timezone('Asia/Kolkata')
    print(f"\nProcessing request for {symbol} at {datetime.now(ist_tz)}")
    
    # Parse time parameters if provided
    custom_time_range = False
    start_dt = None
    end_dt = None
    
    if start_time or end_time:
        if not (start_time and end_time):
            raise HTTPException(
                status_code=400,
                detail="Both start_time and end_time must be provided if using custom time range"
            )
            
        try:
            # Parse the input times and ensure they're in IST
            start_dt = pd.Timestamp(start_time, tz=ist_tz)
            end_dt = pd.Timestamp(end_time, tz=ist_tz) + timedelta(minutes=1)
            
            # Validate time range
            if end_dt <= start_dt:
                raise HTTPException(
                    status_code=400,
                    detail="end_time must be after start_time"
                )
            
            # Check if the date range is not too large
            if (end_dt - start_dt) > timedelta(days=5):
                raise HTTPException(
                    status_code=400,
                    detail="Time range cannot exceed 5 days"
                )
                
            custom_time_range = True
            print(f"Using custom time range: {start_dt} to {end_dt} IST")
            
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use 'YYYY-MM-DD HH:mm' format (e.g., '2025-10-24 09:15')"
            )
    
    # Validate and format symbol
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol cannot be empty")
        
    # Add .NS suffix if not present for Indian stocks
    # Do not add .NS for common indices
    
    # common_indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    # if not symbol.upper().endswith('.NS') and symbol.upper() not in common_indices:
    #     symbol = f"{symbol}.NS"
    
    # try:
    # Get the data with 3-minute interval
    try:
        timeframes_to_fetch = [15, 5, 3]  # Define the timeframes for the strategy
        result = combine_timeframes(symbol, timeframes_to_fetch, start_dt, end_dt)
            
        if result.empty:
            time_range_msg = (
                f"between {start_time} and {end_time}" if custom_time_range
                else "for the last hour"
            )
            return {
                "symbol": symbol,
                "interval": "3m",
                "timezone": "Asia/Kolkata (IST/UTC+5:30)",
                "last_update": datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S IST'),
                "request_range": f"{start_time} to {end_time}" if custom_time_range else "last hour",
                "data": [],
                "message": f"No data available {time_range_msg}"
            }
            
        final_result = result.reset_index()
        
        # Ensure all required columns exist, fill with 'HOLD' if not
        columns_to_keep = ['Signal_15m', 'Signal_5m', 'Signal_3m']
        for col in columns_to_keep:
            if col not in final_result.columns:
                final_result[col] = 'HOLD'
        
        # --- Generate Final Signal based on confluence ---
        buy_confluence = (final_result['Signal_15m'] == 'BUY') & \
                         (final_result['Signal_5m'] == 'BUY') & \
                         (final_result['Signal_3m'] == 'BUY')
        
        sell_confluence = (final_result['Signal_15m'] == 'SELL') & \
                          (final_result['Signal_5m'] == 'SELL') & \
                          (final_result['Signal_3m'] == 'SELL')
                          
        final_result['Final_Signal'] = np.select([buy_confluence, sell_confluence], ['BUY', 'SELL'], default='HOLD')
                # Sort by datetime in descending order BEFORE converting to string
        final_result = final_result.sort_values('datetime', ascending=False)
        
        # Convert timestamps to IST time strings
        final_result['datetime'] = final_result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Define the columns you want in the final output
        final_columns = ['datetime', 'Signal_15m', 'Signal_5m', 'Signal_3m', 'Final_Signal']
        
        response_data = {
            "symbol": symbol,
            "timeframes_used": [f"{tf}m" for tf in timeframes_to_fetch],
            "data": final_result[final_columns].to_dict(orient="records"),
            "message": f"Successfully retrieved 3-minute data for {symbol}" + (
                f" between {start_time} and {end_time}" if custom_time_range
                else " for the last hour"
            )
        }
        return response_data
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))





