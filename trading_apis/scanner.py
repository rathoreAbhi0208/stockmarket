import asyncio
from datetime import datetime
import json
import requests
import uuid
from typing import List, Dict, Optional

from config import IST_TZ
from models import Condition
from strategies import evaluate_multi_timeframe_conditions
from data_fetcher import combine_timeframes


class StockScanner:
    """
    A background scanner to run a strategy across multiple symbols and send alerts.
    """
    def __init__(self, strategy: Dict, timeframes: List[int], scanner_id: str, manager):
        self.strategy = strategy
        self.timeframes = sorted(list(set(timeframes)))
        self.symbols: List[str] = []
        self.is_running = False
        self.buy_conditions = [Condition(**rule) for rule in strategy.get('buy_rules', [])]
        self.sell_conditions = [Condition(**rule) for rule in strategy.get('sell_rules', [])]
        self.scanner_id = scanner_id
        self.manager = manager # WebSocket connection manager

    def _fetch_nse_symbols(self) -> List[str]:
        """
        Fetches a list of NSE symbols from a predefined JSON source.
        In a real-world scenario, this might come from an API or a database.
        """
        try:
            # Using the JSON file referenced in your blade template
            url = "https://basilstar.com/data/nse_bse_symbols.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            all_symbols = response.json()
            
            # Filter for NSE stocks and add major indices
            nse_symbols = [s['symbol'] for s in all_symbols if s['symbol'].endswith('.NS')]
            indices = ['NIFTY', 'BANKNIFTY']
            
            print(f"Loaded {len(nse_symbols)} NSE symbols and {len(indices)} indices.")
            return nse_symbols + indices
        except Exception as e:
            print(f"❌ Could not fetch symbol list: {e}. Using a fallback list.")
            return ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'NIFTY', 'BANKNIFTY']

    async def _evaluate_symbol(self, symbol: str):
        """
        Fetches data for a single symbol, evaluates the strategy, and sends an alert if a signal is found.
        """
        try:
            # Fetch data for the required timeframes. We don't need a long history for live scanning.
            df = combine_timeframes(symbol, self.timeframes, start_time=None, end_time=None)

            if df.empty:
                return

            # --- Evaluate Buy and Sell Conditions ---
            buy_signals = evaluate_multi_timeframe_conditions(df, self.buy_conditions, self.timeframes)
            sell_signals = evaluate_multi_timeframe_conditions(df, self.sell_conditions, self.timeframes)

            df['Signal'] = 'HOLD'
            df.loc[buy_signals, 'Signal'] = 'BUY'
            df.loc[sell_signals, 'Signal'] = 'SELL'

            latest = df.iloc[-1]
            signal = latest['Signal']

            # If a BUY or SELL signal is generated on the latest candle
            if signal in ['BUY', 'SELL']:
                print(f"✅ Alert! {symbol} -> {signal}")
                alert_message = {
                    "type": "scanner_alert",
                    "symbol": symbol,
                    "signal": signal,
                    "price": latest['Close'],
                    "timestamp": str(latest.name),
                    "strategy_name": self.strategy.get("name", "Custom Strategy")
                }
                # Broadcast the alert to all clients connected to this specific scanner_id
                await self.manager.send_to_symbol(self.scanner_id, alert_message)

        except Exception as e:
            # Errors are expected (e.g., bad data for a symbol), so we just log it and continue
            print(f"⚠️ Error processing symbol {symbol}: {e}")

    async def run(self):
        """
        The main loop for the scanner. It periodically fetches symbols and evaluates them.
        """
        print(f"🚀 Starting stock scanner for ID: {self.scanner_id}...")
        self.is_running = True
        self.symbols = self._fetch_nse_symbols()

        while self.is_running:
            print(f"\n--- Running new scan cycle at {IST_TZ.localize(datetime.now()).strftime('%Y-%m-%d %H:%M:%S')} ---")
            
            # Create tasks for all symbols to be evaluated concurrently
            tasks = [self._evaluate_symbol(symbol) for symbol in self.symbols]
            
            # Run tasks in batches to avoid overwhelming the system and data provider
            batch_size = 20
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i + batch_size]
                await asyncio.gather(*batch)
                # A small delay between batches can help with rate limiting
                await asyncio.sleep(1)

            print("--- Scan cycle complete. Waiting for next interval... ---")
            # Wait for 3 minutes before the next full scan cycle
            await asyncio.sleep(180)

    def stop(self):
        """Stops the scanner loop."""
        self.is_running = False
        print(f"🛑 Stopping stock scanner for ID: {self.scanner_id}...")


class ScannerManager:
    """
    Manages the lifecycle of multiple dynamic StockScanner instances.
    """
    def __init__(self, connection_manager):
        self.scanners: Dict[str, StockScanner] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        self.connection_manager = connection_manager

    def start_new_scanner(self, strategy: Dict) -> str:
        """
        Creates, starts, and returns the ID of a new scanner instance.
        """
        # Collect all unique timeframes from conditions
        timeframes_needed = set()
        for rule in strategy.get('buy_rules', []) + strategy.get('sell_rules', []):
            if rule.get('timeframe'):
                timeframes_needed.add(rule['timeframe'])
        
        if not timeframes_needed:
            raise ValueError("Strategy must have at least one rule with a timeframe.")

        scanner_id = str(uuid.uuid4())
        scanner = StockScanner(
            strategy=strategy,
            timeframes=list(timeframes_needed),
            scanner_id=scanner_id,
            manager=self.connection_manager
        )
        self.scanners[scanner_id] = scanner
        
        # Run the scanner in a background task
        task = asyncio.create_task(scanner.run())
        self.tasks[scanner_id] = task
        return scanner_id

    def stop_scanner(self, scanner_id: str) -> bool:
        """
        Stops a running scanner task by its ID.
        """
        if scanner_id in self.scanners and scanner_id in self.tasks:
            scanner = self.scanners[scanner_id]
            task = self.tasks[scanner_id]
            
            scanner.stop()  # Set the running flag to False
            task.cancel()   # Cancel the asyncio task
            return True
        return False