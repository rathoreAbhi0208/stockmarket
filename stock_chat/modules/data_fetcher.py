from typing import Dict, List, Optional
from modules.data_sources.news_fetcher import NewsAPIFetcher, FinnhubNewsFetcher, GoogleNewsFetcher
from modules.data_sources.twitter_fetcher import TwitterAPIFetcher
from modules.data_sources.fundamental_fetcher import AlphaVantageFetcher, YahooFinanceFetcher
import requests
from datetime import datetime

FMP_API_KEY = "pNfPaAqCCLW5TIyeNfmbJ9CaocjvSfNb"

# Common Indian stock tickers with company names
INDIAN_STOCKS = {
    'TCS': 'Tata Consultancy Services',
    'INFY': 'Infosys',
    'RELIANCE': 'Reliance Industries',
    'HDFCBANK': 'HDFC Bank',
    'ICICIBANK': 'ICICI Bank',
    'HINDUNILVR': 'Hindustan Unilever',
    'ITC': 'ITC Limited',
    'SBIN': 'State Bank of India',
    'BHARTIARTL': 'Bharti Airtel',
    'KOTAKBANK': 'Kotak Mahindra Bank',
    'LT': 'Larsen & Toubro',
    'AXISBANK': 'Axis Bank',
    'ASIANPAINT': 'Asian Paints',
    'MARUTI': 'Maruti Suzuki',
    'TITAN': 'Titan Company',
    'BAJFINANCE': 'Bajaj Finance',
    'SUNPHARMA': 'Sun Pharmaceutical',
    'WIPRO': 'Wipro',
    'TECHM': 'Tech Mahindra',
    'HCLTECH': 'HCL Technologies',
    'ULTRACEMCO': 'UltraTech Cement',
    'NESTLEIND': 'Nestle India'
}

class StockDataFetcher:
    """Unified interface for all data sources"""
    
    def __init__(self, config):
        self.config = config
        
        # Initialize data sources
        self.news_fetcher = NewsAPIFetcher(None)
        self.google_news = GoogleNewsFetcher()  # No API key needed!
        self.twitter_fetcher = TwitterAPIFetcher(None)
        self.alpha_vantage = AlphaVantageFetcher(config.alpha_vantage_key)
        self.yahoo_finance = YahooFinanceFetcher()
    
    def _is_indian_stock(self, ticker: str) -> bool:
        """Check if ticker is likely an Indian stock"""
        ticker_upper = ticker.upper().replace('.NS', '').replace('.BO', '')
        return ticker_upper in INDIAN_STOCKS
    
    def _get_company_name(self, ticker: str) -> str:
        """Get full company name for Indian stocks"""
        ticker_upper = ticker.upper().replace('.NS', '').replace('.BO', '')
        return INDIAN_STOCKS.get(ticker_upper, ticker)
    
    def get_fundamental_data(self, ticker: str) -> Dict:
        """Fetch fundamental analysis data with smart ticker detection"""
        
        # Determine the correct ticker format for Yahoo Finance
        if '.' in ticker:
            yahoo_ticker = ticker.upper()
        elif self._is_indian_stock(ticker):
            yahoo_ticker = f"{ticker.upper()}.NS"
            print(f"Detected Indian stock: {ticker} → {yahoo_ticker}")
        else:
            yahoo_ticker = ticker.upper()
            print(f"Using ticker as-is: {yahoo_ticker}")

        # Try Yahoo Finance first
        data = self.yahoo_finance.fetch_overview(yahoo_ticker)
        
        # If Yahoo fails and it's Indian stock, try Alpha Vantage
        if ("error" in data or not data) and self._is_indian_stock(ticker):
            print(f"Yahoo failed for {yahoo_ticker}, trying Alpha Vantage")
            data = self.alpha_vantage.fetch_overview(ticker.upper())
        
        return data
    
    def get_latest_news(self, ticker: str, company_name: str, news_api_key: str, finnhub_api_key: str) -> List[Dict]:
        """Fetch latest news using Google News (free, no API key needed)"""
        
        # Get proper company name for better search results
        is_indian = self._is_indian_stock(ticker)
        if is_indian:
            search_name = self._get_company_name(ticker)
            print(f"Searching Google News for: {ticker} → {search_name}")
        else:
            search_name = company_name if company_name != "Apple Inc." else ticker.upper()
        
        # Use Google News as primary source (works for all stocks)
        news = self.google_news.fetch(search_name, ticker)
        
        # Optionally add NewsAPI if user has configured it
        if news_api_key:
            self.news_fetcher.api_key = news_api_key
            news_articles = self.news_fetcher.fetch(ticker, search_name)
            news.extend(news_articles)
        
        # Remove duplicates and sort by date
        seen = set()
        unique_news = []
        for article in news:
            if article["title"] not in seen:
                seen.add(article["title"])
                unique_news.append(article)
        
        if not unique_news:
            return [{
                "title": f"No recent news found for {search_name}",
                "source": "Google News",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "url": "#",
                "description": "Try checking back later for updates."
            }]
        
        return sorted(unique_news, key=lambda x: x["date"], reverse=True)[:10]
    
    def get_earnings_commentary(self, ticker: str, quarter: Optional[str]) -> Dict:
        """Fetch earnings call transcript from Financial Modeling Prep API."""
        
        # Check if it's an Indian stock
        is_indian = self._is_indian_stock(ticker)
        
        if is_indian:
            company_name = self._get_company_name(ticker)
            return {
                "error": f"Earnings transcripts not available for {company_name} ({ticker})",
                "note": "Indian Stock Limitation",
                "suggestion": "Try checking the company's investor relations website or search for earnings news instead.",
                "alternative": f"You can ask: 'What's the latest news about {ticker} earnings?'"
            }
        
        # For US stocks, proceed with FMP API
        now = datetime.now()
        year = now.year
        
        if not quarter:
            current_quarter = (now.month - 1) // 3 + 1
            last_quarter_num = current_quarter - 1
            if last_quarter_num == 0:
                last_quarter_num = 4
                year -= 1
            quarter = f"Q{last_quarter_num}"

        quarter_num = int(quarter.replace("Q", ""))

        url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{ticker}"
        params = {
            "year": year,
            "quarter": quarter_num,
            "apikey": FMP_API_KEY
        }

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()

            if not data or len(data) == 0:
                # Try previous year if current year doesn't have data
                params["year"] = year - 1
                response = requests.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                if not data or len(data) == 0:
                    return {
                        "error": f"No transcript found for {ticker} {year} {quarter}.",
                        "suggestion": f"Try different quarters: 'Q4 {year-1} earnings' or 'Q3 {year-1} earnings'"
                    }
            
            return data[0]
        except Exception as e:
            return {
                "error": f"Could not fetch earnings transcript: {str(e)}",
                "suggestion": "Try a different quarter or check if the ticker symbol is correct for US stocks."
            }
    
    def get_leader_tweets(self, username: str) -> List[Dict]:
        """Fetch tweets from company leader"""
        return self.twitter_fetcher.fetch(username)