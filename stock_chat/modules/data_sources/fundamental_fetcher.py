from pyparsing import Dict
import requests


class AlphaVantageFetcher:
    """
    Fetches fundamental data from Alpha Vantage
    Get free API key: https://www.alphavantage.co/support/#api-key
    Free tier: 25 requests/day
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def fetch_overview(self, ticker: str) -> Dict:
        if not self.api_key:
            return self._get_mock_data(ticker)
        
        try:
            params = {
                "function": "OVERVIEW",
                "symbol": ticker,
                "apikey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                "ticker": ticker,
                "pe_ratio": data.get("PERatio", "N/A"),
                "market_cap": data.get("MarketCapitalization", "N/A"),
                "revenue": data.get("RevenueTTM", "N/A"),
                "profit_margin": data.get("ProfitMargin", "N/A"),
                "roe": data.get("ReturnOnEquityTTM", "N/A"),
                "debt_to_equity": data.get("DebtToEquity", "N/A"),
                "dividend_yield": data.get("DividendYield", "N/A")
            }
            
        except Exception as e:
            print(f"Error fetching fundamentals: {e}")
            return self._get_mock_data(ticker)
    
    def _get_mock_data(self, ticker: str) -> Dict:
        return {
            "ticker": ticker,
            "pe_ratio": "15.4",
            "market_cap": "$500B",
            "revenue": "$100B",
            "profit_margin": "25%",
            "roe": "30%",
            "debt_to_equity": "0.45",
            "dividend_yield": "0.5%",
            "note": "Using mock data. Add Alpha Vantage API key for real data."
        }


class YahooFinanceFetcher:
    """
    Fetches data from Yahoo Finance (via yfinance library)
    No API key needed - free to use
    Install: pip install yfinance
    """
    def __init__(self):
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            self.yf = None
    
    def fetch_overview(self, ticker: str) -> Dict:
        if not self.yf:
            return {"error": "yfinance not installed. Run: pip install yfinance"}
        
        try:
            stock = self.yf.Ticker(ticker)
            info = stock.info
            
            return {
                "ticker": ticker,
                "pe_ratio": info.get("trailingPE", "N/A"),
                "market_cap": info.get("marketCap", "N/A"),
                "revenue": info.get("totalRevenue", "N/A"),
                "profit_margin": info.get("profitMargins", "N/A"),
                "roe": info.get("returnOnEquity", "N/A"),
                "debt_to_equity": info.get("debtToEquity", "N/A"),
                "dividend_yield": info.get("dividendYield", "N/A")
            }
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance data: {e}")
            return {"error": str(e)}

