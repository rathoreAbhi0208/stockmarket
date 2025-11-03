import pandas as pd
import numpy as np

def calculate_all_indicators(df):
    """Calculate all available technical indicators"""
    df = df.copy()
    close = df['Close'].astype(float)
    high = df['High'].astype(float)
    low = df['Low'].astype(float)
    open_price = df['Open'].astype(float)
    volume = df['Volume'].astype(float)
    
    # EMAs
    for period in [5, 9, 12, 20, 26, 50, 200]:
        df[f'EMA_{period}'] = close.ewm(span=period, adjust=False).mean()
    
    # SMAs
    for period in [5, 9, 20, 50, 200]:
        df[f'SMA_{period}'] = close.rolling(window=period).mean()
    
    # RSI (14-period)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD (12, 26, 9)
    exp1 = close.ewm(span=12, adjust=False).mean()
    exp2 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['SIGNAL_LINE'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_HIST'] = df['MACD'] - df['SIGNAL_LINE']
    
    # Bollinger Bands (20-period, 2 std dev)
    df['BB_MIDDLE'] = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    df['BB_UPPER'] = df['BB_MIDDLE'] + (bb_std * 2)
    df['BB_LOWER'] = df['BB_MIDDLE'] - (bb_std * 2)
    df['BB_WIDTH'] = df['BB_UPPER'] - df['BB_LOWER']
    
    # Stochastic (14, 3, 3)
    low14 = low.rolling(window=14).min()
    high14 = high.rolling(window=14).max()
    denominator = (high14 - low14)
    df['STOCH_K'] = pd.Series(index=df.index)
    valid_denom = denominator != 0
    df.loc[valid_denom, 'STOCH_K'] = 100 * ((close - low14) / denominator)[valid_denom]
    df.loc[~valid_denom, 'STOCH_K'] = 50
    df['STOCH_D'] = df['STOCH_K'].rolling(window=3).mean()
    
    # Stochastic Cross
    df['STOCH_CROSS'] = 0
    valid_rows = df['STOCH_K'].notna() & df['STOCH_D'].notna()
    df.loc[valid_rows, 'STOCH_CROSS'] = np.where(
        df.loc[valid_rows, 'STOCH_K'] > df.loc[valid_rows, 'STOCH_D'],
        1, -1
    )
    
    # ATR (14-period)
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    df['ATR'] = pd.Series(true_range).rolling(14).mean()
    
    # ADX (14-period)
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    atr = pd.Series(true_range).rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    
    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    df['ADX'] = dx.rolling(14).mean()
    df['PLUS_DI'] = plus_di
    df['MINUS_DI'] = minus_di
    
    # Heikin-Ashi
    df['HA_CLOSE'] = (open_price + high + low + close) / 4
    df['HA_OPEN'] = open_price.copy()
    for i in range(1, len(df)):
        df.iloc[i, df.columns.get_loc('HA_OPEN')] = (
            df.iloc[i-1, df.columns.get_loc('HA_OPEN')] + 
            df.iloc[i-1, df.columns.get_loc('HA_CLOSE')]
        ) / 2
    df['HA_HIGH'] = df[['High', 'HA_OPEN', 'HA_CLOSE']].max(axis=1)
    df['HA_LOW'] = df[['Low', 'HA_OPEN', 'HA_CLOSE']].min(axis=1)
    
    # Volume indicators
    df['VOLUME_SMA'] = volume.rolling(window=20).mean()
    df['VOLUME_RATIO'] = volume / df['VOLUME_SMA']
    
    # Price change
    df['CHANGE_PCT'] = close.pct_change() * 100
    
    # OHLC shorthand
    df['OPEN'] = df['Open']
    df['HIGH'] = df['High']
    df['LOW'] = df['Low']
    df['CLOSE'] = df['Close']
    df['VOLUME'] = df['Volume']
    
    return df.ffill().bfill()