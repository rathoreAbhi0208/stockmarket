from fastapi import FastAPI, Query, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import List, Dict
import asyncio
import json

from pydantic import BaseModel
from live_data_fetcher import live_stream
from config import IST_TZ, AVAILABLE_INDICATORS, AVAILABLE_OPERATORS
from models import StrategyRequest, Condition
from data_fetcher import fetch_and_process, combine_timeframes
from strategies import evaluate_multi_timeframe_conditions
from scanner import ScannerManager
from utils import parse_time_params

app = FastAPI(
    title="Unified Trading Strategy API",
    description="Multi-timeframe analysis and custom strategy builder",
    version="2.0.0"
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, symbol: str):
        await websocket.accept()
        if symbol not in self.active_connections:
            self.active_connections[symbol] = []
        self.active_connections[symbol].append(websocket)
    
    def disconnect(self, websocket: WebSocket, symbol: str):
        if symbol in self.active_connections:
            self.active_connections[symbol].remove(websocket)
    
    async def send_to_symbol(self, symbol: str, message: dict):
        """Send message to all clients subscribed to a symbol"""
        if symbol in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[symbol]:
                try:
                    await connection.send_json(message)
                except:
                    dead_connections.append(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[symbol].remove(conn)

manager = ConnectionManager()

# --- Initialize the Dynamic Scanner Manager ---
scanner_manager = ScannerManager(connection_manager=manager)



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
        
        # Automatically append .NS for Indian stocks if not present
        common_indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        symbol_upper = symbol.upper()
        if not symbol_upper.endswith(('.NS', '.BSE')) and symbol_upper not in common_indices:
            symbol = f"{symbol}.NS"

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
    """
    try:
        start_dt = None
        end_dt = None
        
        if request.start_time and request.end_time:
            start_dt, end_dt = parse_time_params(request.start_time, request.end_time)
        
        # Automatically append .NS for Indian stocks if not present
        common_indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        symbol_upper = request.symbol.upper()
        if not symbol_upper.endswith(('.NS', '.BSE')) and symbol_upper not in common_indices:
            request.symbol = f"{request.symbol}.NS"

        # Collect all unique timeframes from conditions
        timeframes_needed = {request.interval}  # Base interval
        
        for condition in request.buy_rules + request.sell_rules:
            if condition.timeframe:
                timeframes_needed.add(condition.timeframe)
        
        timeframes_list = sorted(list(timeframes_needed))
        print(f"Timeframes needed: {timeframes_list}")
        
        # Fetch and combine timeframes
        combined_df = combine_timeframes(request.symbol, timeframes_list, start_dt, end_dt)
        
        if combined_df.empty:
            raise HTTPException(
                status_code=404,
                detail="No data available for the specified parameters"
            )
        
        # Group conditions by timeframe
        buy_conditions_by_tf = {}
        sell_conditions_by_tf = {}
        
        for condition in request.buy_rules:
            tf = condition.timeframe if condition.timeframe else request.interval
            if tf not in buy_conditions_by_tf:
                buy_conditions_by_tf[tf] = []
            buy_conditions_by_tf[tf].append(condition)
        
        for condition in request.sell_rules:
            tf = condition.timeframe if condition.timeframe else request.interval
            if tf not in sell_conditions_by_tf:
                sell_conditions_by_tf[tf] = []
            sell_conditions_by_tf[tf].append(condition)
        
        # Evaluate each timeframe independently
        timeframe_signals = {}
        
        for tf in timeframes_list:
            # Get conditions for this timeframe
            buy_conds = buy_conditions_by_tf.get(tf, [])
            sell_conds = sell_conditions_by_tf.get(tf, [])
            
            # Evaluate conditions for this timeframe
            if buy_conds:
                buy_signals_tf = evaluate_multi_timeframe_conditions(
                    combined_df, buy_conds, timeframes_list
                )
            else:
                buy_signals_tf = pd.Series([False] * len(combined_df), index=combined_df.index)
            
            if sell_conds:
                sell_signals_tf = evaluate_multi_timeframe_conditions(
                    combined_df, sell_conds, timeframes_list
                )
            else:
                sell_signals_tf = pd.Series([False] * len(combined_df), index=combined_df.index)
            
            # Create signal column for this timeframe
            signal_col = f'Signal_{tf}m'
            combined_df[signal_col] = 'HOLD'
            combined_df.loc[buy_signals_tf, signal_col] = 'BUY'
            combined_df.loc[sell_signals_tf, signal_col] = 'SELL'
            
            timeframe_signals[tf] = signal_col
        
        # Apply confluence logic: all timeframes must agree
        buy_confluence = pd.Series([True] * len(combined_df), index=combined_df.index)
        sell_confluence = pd.Series([True] * len(combined_df), index=combined_df.index)
        
        for signal_col in timeframe_signals.values():
            buy_confluence &= (combined_df[signal_col] == 'BUY')
            sell_confluence &= (combined_df[signal_col] == 'SELL')
        
        # Generate final signal
        combined_df['Signal'] = 'HOLD'
        combined_df.loc[buy_confluence, 'Signal'] = 'BUY'
        combined_df.loc[sell_confluence, 'Signal'] = 'SELL'
        
        # Prepare response
        result = combined_df.reset_index()
        result = result.sort_values('datetime', ascending=False)
        result['datetime'] = result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Select output columns - include per-timeframe signals
        output_columns = ['datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
        
        # Add per-timeframe signal columns
        for signal_col in timeframe_signals.values():
            if signal_col in result.columns:
                output_columns.append(signal_col)
        
        # Add final signal
        output_columns.append('Signal')
        
        # Add indicator columns that were used in conditions
        used_indicators = set()
        for condition in request.buy_rules + request.sell_rules:
            timeframe_suffix = f"_{condition.timeframe}" if condition.timeframe and len(timeframes_needed) > 1 else ""
            used_indicators.add(condition.indicator.upper() + timeframe_suffix)
            if isinstance(condition.value, str):
                used_indicators.add(condition.value.upper() + timeframe_suffix)
        
        for indicator in used_indicators:
            if indicator in result.columns and indicator not in output_columns:
                output_columns.append(indicator)
        
        # Count signals
        signal_counts = result['Signal'].value_counts().to_dict()
        
        # Count per-timeframe signals
        tf_signal_counts = {}
        for tf, signal_col in timeframe_signals.items():
            tf_counts = result[signal_col].value_counts().to_dict()
            tf_signal_counts[f"{tf}m"] = {
                "buy": tf_counts.get('BUY', 0),
                "sell": tf_counts.get('SELL', 0),
                "hold": tf_counts.get('HOLD', 0)
            }
        
        # Identify numerical columns
        numerical_cols = result.select_dtypes(include=np.number).columns

        # Replace non-finite values with None in numerical columns
        result[numerical_cols] = result[numerical_cols].replace([np.inf, -np.inf, np.nan], None)

        # Build strategy description
        strategy_by_tf = {}
        for tf in timeframes_list:
            buy_conds = buy_conditions_by_tf.get(tf, [])


            sell_conds = sell_conditions_by_tf.get(tf, [])
            
            buy_desc = [f"{c.indicator} {c.operator} {c.value}" for c in buy_conds]
            sell_desc = [f"{c.indicator} {c.operator} {c.value}" for c in sell_conds]
            
            strategy_by_tf[f"{tf}m"] = {
                "buy_conditions": buy_desc,
                "sell_conditions": sell_desc
            }
        
        return {
            "symbol": request.symbol,
            "interval": f"{request.interval}m",
            "timezone": "Asia/Kolkata (IST)",
            "timeframes_used": [f"{tf}m" for tf in timeframes_list],
            "strategy_by_timeframe": strategy_by_tf,
            "signal_summary": {
                "total_candles": len(result),
                "final_buy_signals": signal_counts.get('BUY', 0),
                "final_sell_signals": signal_counts.get('SELL', 0),
                "final_hold_signals": signal_counts.get('HOLD', 0),
                "per_timeframe": tf_signal_counts
            },
            "data": result[output_columns].to_dict(orient="records"),
            "message": f"Strategy evaluated with confluence across {len(timeframes_list)} timeframe(s). Final signal requires all timeframes to agree."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    

# # ============================================================================
# # Live Strategy WebSocket Endpoint
# # ============================================================================

@app.websocket("/ws/live_strategy_3min/{symbol}")
async def websocket_live_strategy(websocket: WebSocket, symbol: str):
    """
    Live multi-timeframe strategy WebSocket
    
    Usage:
    ws://localhost:8000/ws/live_strategy_3min/NIFTY
    """
    # Automatically append .NS for Indian stocks
    common_indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
    symbol_upper = symbol.upper()
    if not symbol_upper.endswith(('.NS', '.BSE')) and symbol_upper not in common_indices:
        symbol = f"{symbol}.NS"
    
    await manager.connect(websocket, symbol)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "symbol": symbol,
            "message": "Connected to live strategy stream",
            "timeframes": ["15m", "5m", "3m"]
        })
        
        # Continuous loop to send updates
        while True:
            try:
                # Get latest multi-timeframe signal
                result = await live_stream.get_multi_timeframe_signal(
                    symbol, 
                    timeframes=[15, 5, 3]
                )
                
                if result['latest_data']:
                    # Send update to client
                    await websocket.send_json({
                        "type": "signal_update",
                        "symbol": symbol,
                        "timestamp": result['timestamp'],
                        "final_signal": result['final_signal'],
                        "signals": result['timeframe_signals'],
                        "data": result['latest_data']
                    })
                    
                    # If there's a BUY/SELL signal, send alert
                    if result['final_signal'] in ['BUY', 'SELL']:
                        await websocket.send_json({
                            "type": "alert",
                            "symbol": symbol,
                            "signal": result['final_signal'],
                            "timestamp": result['timestamp'],
                            "message": f"🚨 {result['final_signal']} Signal Generated!"
                        })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing data: {str(e)}"
                })
            
            # Wait before next update (check every 30 seconds)
            await asyncio.sleep(30)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, symbol)
        print(f"Client disconnected from {symbol}")

# ============================================================================
# Live Custom Strategy WebSocket
# ============================================================================

@app.websocket("/ws/live_custom_strategy")
async def websocket_live_custom_strategy(websocket: WebSocket):
    """
    Live custom strategy with dynamic rules
    
    Client sends strategy config, receives live updates
    """
    await websocket.accept()
    
    try:
        # Receive strategy configuration
        config = await websocket.receive_json()
        
        symbol = config.get('symbol', 'NIFTY')
        interval = config.get('interval', 3)
        buy_rules = config.get('buy_rules', [])
        sell_rules = config.get('sell_rules', [])
        
        # Automatically append .NS
        common_indices = ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        symbol_upper = symbol.upper()
        if not symbol_upper.endswith(('.NS', '.BSE')) and symbol_upper not in common_indices:
            symbol = f"{symbol}.NS"
        
        await websocket.send_json({
            "type": "strategy_loaded",
            "symbol": symbol,
            "interval": interval,
            "message": "Custom strategy loaded, monitoring live data..."
        })
        
        # Import here to avoid circular imports
        from models import Condition
        from strategies import evaluate_multi_timeframe_conditions
        from data_fetcher import combine_timeframes
        
        # Parse conditions
        buy_conditions = [Condition(**rule) for rule in buy_rules]
        sell_conditions = [Condition(**rule) for rule in sell_rules]
        
        # Collect timeframes
        timeframes_needed = {interval}
        for rule in buy_rules + sell_rules:
            if rule.get('timeframe'):
                timeframes_needed.add(rule['timeframe'])
        timeframes_list = sorted(list(timeframes_needed))
        
        while True:
            try:
                # Fetch live data for all needed timeframes
                now = datetime.now(IST_TZ)
                start_time = now - timedelta(days=2)
                
                combined_df = combine_timeframes(symbol, timeframes_list, start_time, now)
                
                if not combined_df.empty:
                    # Group conditions by timeframe
                    buy_conditions_by_tf = {}
                    sell_conditions_by_tf = {}
                    
                    for cond in buy_conditions:
                        tf = cond.timeframe if cond.timeframe else interval
                        if tf not in buy_conditions_by_tf:
                            buy_conditions_by_tf[tf] = []
                        buy_conditions_by_tf[tf].append(cond)
                    
                    for cond in sell_conditions:
                        tf = cond.timeframe if cond.timeframe else interval
                        if tf not in sell_conditions_by_tf:
                            sell_conditions_by_tf[tf] = []
                        sell_conditions_by_tf[tf].append(cond)
                    
                    # Evaluate each timeframe
                    timeframe_signals = {}
                    for tf in timeframes_list:
                        buy_conds = buy_conditions_by_tf.get(tf, [])
                        sell_conds = sell_conditions_by_tf.get(tf, [])
                        
                        if buy_conds:
                            buy_sig = evaluate_multi_timeframe_conditions(
                                combined_df, buy_conds, timeframes_list
                            )
                        else:
                            buy_sig = pd.Series([False] * len(combined_df), index=combined_df.index)
                        
                        if sell_conds:
                            sell_sig = evaluate_multi_timeframe_conditions(
                                combined_df, sell_conds, timeframes_list
                            )
                        else:
                            sell_sig = pd.Series([False] * len(combined_df), index=combined_df.index)
                        
                        signal_col = f'Signal_{tf}m'
                        combined_df[signal_col] = 'HOLD'
                        combined_df.loc[buy_sig, signal_col] = 'BUY'
                        combined_df.loc[sell_sig, signal_col] = 'SELL'
                        
                        timeframe_signals[tf] = signal_col
                    
                    # Confluence
                    buy_confluence = pd.Series([True] * len(combined_df), index=combined_df.index)
                    sell_confluence = pd.Series([True] * len(combined_df), index=combined_df.index)
                    
                    for sig_col in timeframe_signals.values():
                        buy_confluence &= (combined_df[sig_col] == 'BUY')
                        sell_confluence &= (combined_df[sig_col] == 'SELL')
                    
                    combined_df['Signal'] = 'HOLD'
                    combined_df.loc[buy_confluence, 'Signal'] = 'BUY'
                    combined_df.loc[sell_confluence, 'Signal'] = 'SELL'
                    
                    # Get latest
                    latest = combined_df.iloc[-1]
                    
                    # Build response
                    tf_signals = {}
                    for tf, sig_col in timeframe_signals.items():
                        tf_signals[f"{tf}m"] = latest.get(sig_col, 'HOLD')
                    
                    await websocket.send_json({
                        "type": "signal_update",
                        "symbol": symbol,
                        "timestamp": str(latest.name),
                        "final_signal": latest['Signal'],
                        "timeframe_signals": tf_signals,
                        "price": {
                            "open": float(latest['Open']),
                            "high": float(latest['High']),
                            "low": float(latest['Low']),
                            "close": float(latest['Close']),
                            "volume": int(latest['Volume'])
                        }
                    })
                    
                    # Alert on BUY/SELL
                    if latest['Signal'] in ['BUY', 'SELL']:
                        await websocket.send_json({
                            "type": "alert",
                            "symbol": symbol,
                            "signal": latest['Signal'],
                            "timestamp": str(latest.name),
                            "message": f"🚨 {latest['Signal']} Signal!"
                        })
                
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error: {str(e)}"
                })
            
            # Check every 30 seconds
            await asyncio.sleep(30)
    
    except WebSocketDisconnect:
        print("Custom strategy client disconnected")

# ============================================================================
# Dynamic Scanner Endpoints
# ============================================================================

class ScannerStrategyRequest(BaseModel):
    name: str = "Dynamic Scanner"
    buy_rules: List[Condition]
    sell_rules: List[Condition]

@app.post("/scanner/start")
async def start_dynamic_scanner(strategy_request: ScannerStrategyRequest):
    """
    Starts a new NSE-wide scanner with a dynamically provided strategy.
    Returns a unique scanner_id to listen for alerts.
    """
    try:
        scanner_id = scanner_manager.start_new_scanner(strategy_request.dict())
        return {
            "message": "Scanner started successfully!",
            "scanner_id": scanner_id,
            "websocket_url": f"/ws/scanner/alerts/{scanner_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scanner: {e}")

@app.post("/scanner/stop/{scanner_id}")
async def stop_dynamic_scanner(scanner_id: str):
    """
    Stops a running dynamic scanner by its ID.
    """
    if scanner_manager.stop_scanner(scanner_id):
        return {"message": f"Scanner {scanner_id} stopped successfully."}
    else:
        raise HTTPException(status_code=404, detail=f"Scanner with ID {scanner_id} not found.")

@app.websocket("/ws/scanner/alerts/{scanner_id}")
async def websocket_scanner_alerts(websocket: WebSocket, scanner_id: str):
    """
    Connect here with a scanner_id to receive alerts for a specific dynamic strategy.
    """
    await manager.connect(websocket, scanner_id)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": f"Connected to scanner {scanner_id}. Waiting for alerts..."
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, scanner_id)
        print(f"Client disconnected from scanner {scanner_id}.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)