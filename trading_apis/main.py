from fastapi import FastAPI, Query, HTTPException
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from config import IST_TZ, AVAILABLE_INDICATORS, AVAILABLE_OPERATORS
from models import StrategyRequest
from data_fetcher import fetch_and_process, combine_timeframes
from strategies import evaluate_conditions, evaluate_multi_timeframe_conditions
from utils import parse_time_params

app = FastAPI(
    title="Unified Trading Strategy API",
    description="Multi-timeframe analysis and custom strategy builder",
    version="2.0.0"
)

# ============================================================================
# Root and Info Endpoints
# ============================================================================

@app.get("/")
def read_root():
    return {
        "message": "Unified Trading Strategy API",
        "version": "2.0.0",
        "endpoints": {
            "/strategy_3min": "GET - Multi-timeframe confluence strategy (3m, 5m, 15m)",
            "/custom_strategy": "POST - Build and test custom strategy with per-indicator timeframes",
            "/indicators": "GET - List available indicators and operators",
            "/health": "GET - API health check"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(IST_TZ).isoformat()
    }

@app.get("/indicators")
def list_indicators():
    """List all available indicators and operators"""
    return {
        "indicators": AVAILABLE_INDICATORS,
        "operators": AVAILABLE_OPERATORS,
        "example_conditions": [
            {"indicator": "RSI", "operator": ">", "value": 70, "timeframe": 15},
            {"indicator": "CLOSE", "operator": "crosses_above", "value": "SMA_20", "timeframe": 5},
            {"indicator": "MACD", "operator": ">", "value": "SIGNAL_LINE", "timeframe": 3},
            {"indicator": "BB_WIDTH", "operator": "<", "value": 10, "timeframe": 15},
            {"indicator": "VOLUME_RATIO", "operator": ">", "value": 1.5, "timeframe": 5}
        ]
    }

# ============================================================================
# Multi-Timeframe Strategy Endpoint
# ============================================================================

@app.get("/strategy_3min")
def get_multi_timeframe_strategy(
    symbol: str = Query(default="RELIANCE.NS", description="Stock symbol"),
    start_time: str = Query(default=None, description="Start time 'YYYY-MM-DD HH:mm' IST"),
    end_time: str = Query(default=None, description="End time 'YYYY-MM-DD HH:mm' IST")
):
    """
    Multi-timeframe confluence strategy using 15m, 5m, and 3m timeframes
    """
    try:
        print(f"\nProcessing multi-timeframe request for {symbol}")
        
        start_dt = None
        end_dt = None
        custom_time_range = False
        
        if start_time and end_time:
            start_dt, end_dt = parse_time_params(start_time, end_time)
            end_dt = end_dt + timedelta(minutes=1)
            custom_time_range = True
            print(f"Using custom time range: {start_dt} to {end_dt} IST")
        
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")
        
        # Fetch and combine timeframes
        timeframes_to_fetch = [15, 5, 3]
        result = combine_timeframes(symbol, timeframes_to_fetch, start_dt, end_dt)
        
        if result.empty:
            time_range_msg = (
                f"between {start_time} and {end_time}" if custom_time_range
                else "for the requested period"
            )
            return {
                "symbol": symbol,
                "interval": "3m",
                "timezone": "Asia/Kolkata (IST)",
                "timeframes_used": [f"{tf}m" for tf in timeframes_to_fetch],
                "data": [],
                "message": f"No data available {time_range_msg}"
            }
        
        final_result = result.reset_index()
        
        # Ensure required columns exist
        columns_to_keep = ['Signal_15m', 'Signal_5m', 'Signal_3m']
        for col in columns_to_keep:
            if col not in final_result.columns:
                final_result[col] = 'HOLD'
        
        # Generate final signal based on confluence
        buy_confluence = (
            (final_result['Signal_15m'] == 'BUY') &
            (final_result['Signal_5m'] == 'BUY') &
            (final_result['Signal_3m'] == 'BUY')
        )
        
        sell_confluence = (
            (final_result['Signal_15m'] == 'SELL') &
            (final_result['Signal_5m'] == 'SELL') &
            (final_result['Signal_3m'] == 'SELL')
        )
        
        final_result['Final_Signal'] = np.select(
            [buy_confluence, sell_confluence],
            ['BUY', 'SELL'],
            default='HOLD'
        )
        
        # Sort and format
        final_result = final_result.sort_values('datetime', ascending=False)
        final_result['datetime'] = final_result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        final_columns = ['datetime', 'Signal_15m', 'Signal_5m', 'Signal_3m', 'Final_Signal']
        
        # Count signals
        signal_counts = final_result['Final_Signal'].value_counts().to_dict()
        
        return {
            "symbol": symbol,
            "interval": "3m",
            "timezone": "Asia/Kolkata (IST)",
            "timeframes_used": [f"{tf}m" for tf in timeframes_to_fetch],
            "signal_summary": {
                "total_candles": len(final_result),
                "buy_signals": signal_counts.get('BUY', 0),
                "sell_signals": signal_counts.get('SELL', 0),
                "hold_signals": signal_counts.get('HOLD', 0)
            },
            "data": final_result[final_columns].to_dict(orient="records"),
            "message": f"Successfully retrieved multi-timeframe data for {symbol}" + (
                f" between {start_time} and {end_time}" if custom_time_range
                else ""
            )
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# ============================================================================
# Custom Strategy Builder Endpoint with Multi-Timeframe Support
# ============================================================================

@app.post("/custom_strategy")
def build_custom_strategy(request: StrategyRequest):
    """
    Build and evaluate a custom trading strategy with per-indicator timeframes
    
    Example:
    {
        "symbol": "RELIANCE.NS",
        "interval": 3,
        "buy_rules": [
            {"indicator": "RSI", "operator": ">", "value": 50, "timeframe": 15},
            {"indicator": "MACD", "operator": ">", "value": "SIGNAL_LINE", "timeframe": 3}
        ],
        "sell_rules": [
            {"indicator": "RSI", "operator": "<", "value": 50, "timeframe": 15},
            {"indicator": "MACD", "operator": "<", "value": "SIGNAL_LINE", "timeframe": 3}
        ]
    }
    """
    try:
        start_dt = None
        end_dt = None
        
        if request.start_time and request.end_time:
            start_dt, end_dt = parse_time_params(request.start_time, request.end_time)
        
        # Collect all unique timeframes from conditions
        timeframes_needed = {request.interval}  # Base interval
        
        for condition in request.buy_rules + request.sell_rules:
            if condition.timeframe:
                timeframes_needed.add(condition.timeframe)
        
        timeframes_list = sorted(list(timeframes_needed))
        print(f"Timeframes needed: {timeframes_list}")
        
        # If only base timeframe is needed, use simple fetch
        if len(timeframes_needed) == 1:
            df = fetch_and_process(request.symbol, request.interval, start_dt, end_dt)
            
            if df.empty:
                raise HTTPException(
                    status_code=404,
                    detail="No data available for the specified parameters"
                )
            
            # Evaluate buy and sell conditions on base timeframe
            buy_signals = evaluate_conditions(df, request.buy_rules)
            sell_signals = evaluate_conditions(df, request.sell_rules)
            
        else:
            # Multi-timeframe approach: fetch and combine all timeframes
            combined_df = combine_timeframes(request.symbol, timeframes_list, start_dt, end_dt)
            
            if combined_df.empty:
                raise HTTPException(
                    status_code=404,
                    detail="No data available for the specified parameters"
                )
            
            # Evaluate conditions with timeframe-specific logic
            buy_signals = evaluate_multi_timeframe_conditions(combined_df, request.buy_rules, timeframes_list)
            sell_signals = evaluate_multi_timeframe_conditions(combined_df, request.sell_rules, timeframes_list)
            
            df = combined_df
        
        # Generate signals
        df['Signal'] = 'HOLD'
        df.loc[buy_signals, 'Signal'] = 'BUY'
        df.loc[sell_signals, 'Signal'] = 'SELL'
        
        # Prepare response
        result = df.reset_index()
        result = result.sort_values('datetime', ascending=False)
        result['datetime'] = result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Select output columns
        output_columns = ['datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Signal']
        
        # Add indicator columns that were used in conditions
        used_indicators = set()
        for condition in request.buy_rules + request.sell_rules:
            timeframe_suffix = f"_{condition.timeframe}m" if condition.timeframe and len(timeframes_needed) > 1 else ""
            used_indicators.add(condition.indicator.upper() + timeframe_suffix)
            if isinstance(condition.value, str):
                used_indicators.add(condition.value.upper() + timeframe_suffix)
        
        for indicator in used_indicators:
            if indicator in result.columns and indicator not in output_columns:
                output_columns.append(indicator)
        
        # Count signals
        signal_counts = result['Signal'].value_counts().to_dict()
        
        # Build strategy description
        buy_conditions_desc = []
        for c in request.buy_rules:
            tf_str = f" [{c.timeframe}m]" if c.timeframe else ""
            buy_conditions_desc.append(f"{c.indicator}{tf_str} {c.operator} {c.value}")
        
        sell_conditions_desc = []
        for c in request.sell_rules:
            tf_str = f" [{c.timeframe}m]" if c.timeframe else ""
            sell_conditions_desc.append(f"{c.indicator}{tf_str} {c.operator} {c.value}")
        
        return {
            "symbol": request.symbol,
            "interval": f"{request.interval}m",
            "timezone": "Asia/Kolkata (IST)",
            "timeframes_used": [f"{tf}m" for tf in timeframes_list],
            "strategy": {
                "buy_conditions": buy_conditions_desc,
                "sell_conditions": sell_conditions_desc
            },
            "signal_summary": {
                "total_candles": len(result),
                "buy_signals": signal_counts.get('BUY', 0),
                "sell_signals": signal_counts.get('SELL', 0),
                "hold_signals": signal_counts.get('HOLD', 0)
            },
            "data": result[output_columns].to_dict(orient="records"),
            "message": f"Strategy evaluated successfully on {len(result)} candles using {len(timeframes_list)} timeframe(s)"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)