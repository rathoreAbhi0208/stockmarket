import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from data_fetcher import fetch_data
from indicators import calculate_all_indicators
from strategies import evaluate_15m_strategy, evaluate_5m_strategy, evaluate_3m_strategy
from config import IST_TZ

class LiveDataStream:
    """Manages live data streaming for multiple symbols and timeframes"""
    
    def __init__(self):
        self.data_cache: Dict[str, Dict[int, pd.DataFrame]] = {}
        self.last_fetch: Dict[str, Dict[int, datetime]] = {}
    
    async def get_live_candle(self, symbol: str, interval: int) -> Optional[pd.DataFrame]:
        """
        Fetch the latest candle for a symbol at given interval
        Returns only new data since last fetch
        """
        try:
            now = datetime.now(IST_TZ)
            
            # Initialize cache for symbol if not exists
            if symbol not in self.data_cache:
                self.data_cache[symbol] = {}
                self.last_fetch[symbol] = {}
            
            # Check if we need to fetch (based on interval)
            last_time = self.last_fetch[symbol].get(interval)
            
            if last_time:
                time_diff = (now - last_time).total_seconds() / 60
                if time_diff < interval:
                    # Not time yet for new candle
                    return None
            
            # Fetch last 100 candles to ensure we have enough data for indicators
            end_time = now
            start_time = now - timedelta(days=2)  # Get 2 days of data
            
            df = fetch_data(symbol, interval, start_time, end_time)
            
            if df.empty:
                return None
            
            # Calculate indicators
            df = calculate_all_indicators(df)
            
            # Evaluate strategy based on timeframe
            if interval == 15:
                df = evaluate_15m_strategy(df)
            elif interval == 5:
                df = evaluate_5m_strategy(df)
            elif interval == 3:
                df = evaluate_3m_strategy(df)
            
            # Store in cache
            self.data_cache[symbol][interval] = df
            self.last_fetch[symbol][interval] = now
            
            # Return only the latest candle
            return df.tail(1)
            
        except Exception as e:
            print(f"Error fetching live data for {symbol} {interval}m: {e}")
            return None
    
    async def get_multi_timeframe_signal(self, symbol: str, timeframes: list = [15, 5, 3]):
        """
        Get confluence signal across multiple timeframes
        Returns the latest multi-timeframe analysis
        """
        signals = {}
        latest_data = {}
        
        for tf in timeframes:
            candle = await self.get_live_candle(symbol, tf)
            if candle is not None and not candle.empty:
                latest = candle.iloc[-1]
                signal_col = f'Signal_{tf}m'
                signals[signal_col] = latest.get(signal_col, 'HOLD')
                latest_data[f'{tf}m'] = {
                    'timestamp': str(latest.name),
                    'open': float(latest['Open']),
                    'high': float(latest['High']),
                    'low': float(latest['Low']),
                    'close': float(latest['Close']),
                    'volume': int(latest['Volume']),
                    'signal': latest.get(signal_col, 'HOLD')
                }
        
        # Calculate confluence
        if signals:
            all_buy = all(sig == 'BUY' for sig in signals.values())
            all_sell = all(sig == 'SELL' for sig in signals.values())
            
            if all_buy:
                final_signal = 'BUY'
            elif all_sell:
                final_signal = 'SELL'
            else:
                final_signal = 'HOLD'
        else:
            final_signal = 'HOLD'
        
        return {
            'final_signal': final_signal,
            'timeframe_signals': signals,
            'latest_data': latest_data,
            'timestamp': datetime.now(IST_TZ).isoformat()
        }

# Global instance
live_stream = LiveDataStream()