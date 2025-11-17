from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import pytz
import requests
from datetime import datetime, timedelta

app = FastAPI(title="Dynamic Strategy Builder API")

# --- Configuration ---
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3/historical-chart"
FMP_API_KEY = "84y12ovhukWyiW2v1MjL4bxx8TXskGOb"

# --- Pydantic Models ---
class Condition(BaseModel):
    """Single condition for strategy evaluation"""
    indicator: str = Field(..., description="Indicator name (e.g., RSI, MACD, BB_UPPER)")
    operator: str = Field(..., description="Comparison operator: >, <, >=, <=, ==, crosses_above, crosses_below")
    value: float | str = Field(..., description="Value to compare against (number or another indicator name)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "indicator": "RSI",
                "operator": ">",
                "value": 70
            }
        }

class StrategyRule(BaseModel):
    """Complete strategy rule with multiple conditions"""
    signal_type: str = Field(..., description="Signal type: BUY or SELL")
    conditions: List[Condition] = Field(..., description="List of conditions (all must be true)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "signal_type": "BUY",
                "conditions": [
                    {"indicator": "RSI", "operator": ">", "value": 50},
                    {"indicator": "MACD", "operator": "crosses_above", "value": "SIGNAL_LINE"}
                ]
            }
        }

class StrategyRequest(BaseModel):
    """Complete strategy request"""
    symbol: str = Field(..., description="Stock symbol (e.g., RELIANCE.NS)")
    interval: int = Field(default=5, description="Timeframe in minutes (1, 3, 5, 15, 30, 60)")
    buy_rules: List[Condition] = Field(..., description="Conditions for BUY signal")
    sell_rules: List[Condition] = Field(..., description="Conditions for SELL signal")
    start_time: Optional[str] = Field(None, description="Start time 'YYYY-MM-DD HH:mm' IST")
    end_time: Optional[str] = Field(None, description="End time 'YYYY-MM-DD HH:mm' IST")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "RELIANCE.NS",
                "interval": 5,
                "buy_rules": [
                    {"indicator": "RSI", "operator": ">", "value": 50},
                    {"indicator": "CLOSE", "operator": ">", "value": "BB_UPPER"}
                ],
                "sell_rules": [
                    {"indicator": "RSI", "operator": "<", "value": 50},
                    {"indicator": "CLOSE", "operator": "<", "value": "BB_LOWER"}
                ]
            }
        }

# --- Indicator Calculation Functions ---
def calculate_all_indicators(df):
    """Calculate all available technical indicators"""
    df = df.copy()
    close = df['Close'].astype(float)
    high = df['High'].astype(float)
    low = df['Low'].astype(float)
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
    df['STOCH_K'] = 100 * ((close - low14) / (high14 - low14))
    df['STOCH_D'] = df['STOCH_K'].rolling(window=3).mean()
    
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
    
    tr = true_range
    atr = pd.Series(tr).rolling(14).mean()
    
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    
    dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    df['ADX'] = dx.rolling(14).mean()
    df['PLUS_DI'] = plus_di
    df['MINUS_DI'] = minus_di
    
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

def evaluate_operator(series1, operator, series2):
    """Evaluate comparison between two series or series and value"""
    if operator == '>':
        return series1 > series2
    elif operator == '<':
        return series1 < series2
    elif operator == '>=':
        return series1 >= series2
    elif operator == '<=':
        return series1 <= series2
    elif operator == '==':
        return series1 == series2
    elif operator == 'crosses_above':
        return (series1.shift(1) <= series2.shift(1)) & (series1 > series2)
    elif operator == 'crosses_below':
        return (series1.shift(1) >= series2.shift(1)) & (series1 < series2)
    else:
        raise ValueError(f"Unsupported operator: {operator}")

def evaluate_conditions(df, conditions: List[Condition]):
    """Evaluate a list of conditions and return boolean series"""
    if not conditions:
        return pd.Series([False] * len(df), index=df.index)
    
    results = []
    
    for condition in conditions:
        indicator_name = condition.indicator.upper()
        
        # Check if indicator exists
        if indicator_name not in df.columns:
            raise ValueError(f"Indicator '{indicator_name}' not found. Available: {', '.join(df.columns)}")
        
        series1 = df[indicator_name]
        
        # Determine if value is another indicator or a number
        if isinstance(condition.value, str):
            value_upper = condition.value.upper()
            if value_upper not in df.columns:
                raise ValueError(f"Indicator '{value_upper}' not found")
            series2 = df[value_upper]
        else:
            series2 = float(condition.value)
        
        # Evaluate the condition
        result = evaluate_operator(series1, condition.operator, series2)
        results.append(result)
    
    # Combine all conditions with AND logic
    combined = results[0]
    for result in results[1:]:
        combined = combined & result
    
    return combined

def fetch_data(symbol: str, interval: int, start_time=None, end_time=None):
    """Fetch data from FMP API"""
    ist_tz = pytz.timezone("Asia/Kolkata")
    
    clean_symbol = symbol.replace(".BSE", ".NS") if ".BSE" in symbol else symbol
    
    interval_map = {
        1: "1min",
        3: "1min",
        5: "5min",
        15: "15min",
        30: "30min",
        60: "1hour"
    }
    
    fmp_interval = interval_map.get(interval)
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
        df['datetime'] = df['datetime'].dt.tz_localize(ist_tz)
    else:
        df['datetime'] = df['datetime'].dt.tz_convert(ist_tz)
    
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

# --- API Routes ---
@app.get("/")
def read_root():
    return {
        "message": "Dynamic Strategy Builder API",
        "endpoints": {
            "/strategy": "POST - Build and test custom strategy",
            "/indicators": "GET - List available indicators"
        }
    }

@app.get("/indicators")
def list_indicators():
    """List all available indicators and operators"""
    return {
        "indicators": [
            "OPEN", "HIGH", "LOW", "CLOSE", "VOLUME",
            "EMA_5", "EMA_9", "EMA_12", "EMA_20", "EMA_26", "EMA_50", "EMA_200",
            "SMA_5", "SMA_9", "SMA_20", "SMA_50", "SMA_200",
            "RSI",
            "MACD", "SIGNAL_LINE", "MACD_HIST",
            "BB_UPPER", "BB_MIDDLE", "BB_LOWER", "BB_WIDTH",
            "STOCH_K", "STOCH_D",
            "ATR", "ADX", "PLUS_DI", "MINUS_DI",
            "VOLUME_SMA", "VOLUME_RATIO",
            "CHANGE_PCT"
        ],
        "operators": [
            ">", "<", ">=", "<=", "==",
            "crosses_above", "crosses_below"
        ],
        "example_conditions": [
            {"indicator": "RSI", "operator": ">", "value": 70},
            {"indicator": "CLOSE", "operator": "crosses_above", "value": "SMA_20"},
            {"indicator": "MACD", "operator": ">", "value": "SIGNAL_LINE"},
            {"indicator": "BB_WIDTH", "operator": "<", "value": 10},
            {"indicator": "VOLUME_RATIO", "operator": ">", "value": 1.5}
        ]
    }

@app.post("/strategy")
def build_strategy(request: StrategyRequest):
    """
    Build and evaluate a custom trading strategy
    
    Example request body:
    {
        "symbol": "RELIANCE.NS",
        "interval": 5,
        "buy_rules": [
            {"indicator": "RSI", "operator": ">", "value": 50},
            {"indicator": "CLOSE", "operator": "crosses_above", "value": "SMA_20"}
        ],
        "sell_rules": [
            {"indicator": "RSI", "operator": "<", "value": 50},
            {"indicator": "CLOSE", "operator": "crosses_below", "value": "SMA_20"}
        ]
    }
    """
    try:
        ist_tz = pytz.timezone('Asia/Kolkata')
        
        # Parse time parameters
        start_dt = None
        end_dt = None
        
        if request.start_time and request.end_time:
            start_dt = pd.Timestamp(request.start_time, tz=ist_tz)
            end_dt = pd.Timestamp(request.end_time, tz=ist_tz)
            
            if end_dt <= start_dt:
                raise HTTPException(status_code=400, detail="end_time must be after start_time")
            
            if (end_dt - start_dt) > timedelta(days=5):
                raise HTTPException(status_code=400, detail="Time range cannot exceed 5 days")
        
        # Fetch data
        df = fetch_data(request.symbol, request.interval, start_dt, end_dt)
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data available for the specified parameters")
        
        # Calculate indicators
        df = calculate_all_indicators(df)
        
        # Evaluate buy and sell conditions
        buy_signals = evaluate_conditions(df, request.buy_rules)
        sell_signals = evaluate_conditions(df, request.sell_rules)
        
        # Generate signals
        df['Signal'] = 'HOLD'
        df.loc[buy_signals, 'Signal'] = 'BUY'
        df.loc[sell_signals, 'Signal'] = 'SELL'
        
        # Prepare response
        result = df.reset_index()
        result = result.sort_values('datetime', ascending=False)
        result['datetime'] = result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Select relevant columns for output
        output_columns = ['datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Signal']
        
        # Add indicator columns that were used in conditions
        used_indicators = set()
        for condition in request.buy_rules + request.sell_rules:
            used_indicators.add(condition.indicator.upper())
            if isinstance(condition.value, str):
                used_indicators.add(condition.value.upper())
        
        for indicator in used_indicators:
            if indicator in result.columns and indicator not in output_columns:
                output_columns.append(indicator)
        
        # Count signals
        signal_counts = result['Signal'].value_counts().to_dict()
        
        return {
            "symbol": request.symbol,
            "interval": f"{request.interval}m",
            "timezone": "Asia/Kolkata (IST)",
            "strategy": {
                "buy_conditions": [
                    f"{c.indicator} {c.operator} {c.value}" for c in request.buy_rules
                ],
                "sell_conditions": [
                    f"{c.indicator} {c.operator} {c.value}" for c in request.sell_rules
                ]
            },
            "signal_summary": {
                "total_candles": len(result),
                "buy_signals": signal_counts.get('BUY', 0),
                "sell_signals": signal_counts.get('SELL', 0),
                "hold_signals": signal_counts.get('HOLD', 0)
            },
            "data": result[output_columns].to_dict(orient="records"),
            "message": f"Strategy evaluated successfully on {len(result)} candles"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)