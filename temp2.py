import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import requests

def fetch_and_print_data(symbol: str, exchange: str, interval: Interval, n_bars: int = 100):
    """
    Fetches historical data from TradingView using tvdatafeed and prints the DataFrame.

    Args:
        symbol (str): The stock symbol (e.g., 'RELIANCE').
        exchange (str): The exchange where the stock is traded (e.g., 'NSE').
        interval (Interval): The timeframe for the data (e.g., Interval.in_1_hour).
        n_bars (int): The number of historical bars to fetch.
    """
    # Initialize TvDatafeed
    tv = TvDatafeed()

    print(f"Fetching {n_bars} bars for {symbol} on {exchange} with interval {interval.value}...")

    try:
        # Fetch historical data
        df = tv.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            n_bars=n_bars
        )

        if df is not None and not df.empty:
            print(f"Successfully fetched {len(df)} data points.")
            print("\n--- DataFrame Head ---")
            print(df.head())
            print("\n--- DataFrame Tail ---")
            print(df.tail())
            print("\n--- DataFrame Info ---")
            df.info()
        else:
            print("No data was returned for the given parameters.")

    except Exception as e:
        print(f"An error occurred while fetching data: {e}")



def fetch_fmp_data(symbol: str, interval: str = "15min", apikey: str = "YOUR_API_KEY"):
    """
    Fetch OHLCV data from Financial Modeling Prep (FMP) API.
    
    Parameters:
        symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
        interval (str): Time interval ('1min', '5min', '15min', '30min', '1hour', '4hour', '1day')
        apikey (str): Your FMP API key.
        
    Returns:
        pd.DataFrame: Historical OHLCV data with datetime index.
    """
    url = f"https://financialmodelingprep.com/api/v3/historical-chart/{interval}/{symbol}?apikey={apikey}"
    
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"FMP API Error {response.status_code}: {response.text}")
    
    data = response.json()
    if not data:
        raise ValueError(f"No data returned for symbol: {symbol}")
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Rename columns to match your existing code
    df.rename(columns={
        'date': 'Datetime',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)
    
    # Convert datetime and sort
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    # df['Datetime'] = df['Datetime'].dt.tz_localize('UTC')

    # # Step 2: Convert to IST
    # df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')
    
    df = df.sort_values('Datetime').reset_index(drop=True)
    
    return df


if __name__ == "__main__":
    
    # print("--- Example 1: Fetching data for RELIANCE on NSE (15-minute interval) ---")
    # fetch_and_print_data(symbol='RELIANCE', exchange='NSE', interval=Interval.in_15_minute, n_bars=50)
    # print("\n" + "="*80 + "\n")

    df = fetch_fmp_data("RELIANCE.NS", "15min", apikey="pNfPaAqCCLW5TIyeNfmbJ9CaocjvSfNb")
    print(df.tail())
    
