from gnews import GNews
from typing import List, Dict
from datetime import datetime

class GoogleNewsFetcher:
    """
    Fetches news from Google News using gnews library
    No API key needed - completely free!
    
    Installation: pip install gnews
    """
    def __init__(self):
        self.gnews = GNews(
            language='en',
            country='IN',  # Set to India for better Indian stock coverage
            period='7d',    # Last 7 days
            max_results=10
        )
    
    def fetch(self, company_name: str, ticker: str) -> List[Dict]:
        """Fetch news articles from Google News"""
        try:
            # Search using company name for better results
            search_query = f"{company_name} stock"
            articles = self.gnews.get_news(search_query)
            
            result = []
            for article in articles:
                # Parse the published date
                pub_date = article.get('published date', '')
                try:
                    # GNews returns dates like "Mon, 04 Nov 2024 10:30:00 GMT"
                    date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except:
                    formatted_date = datetime.now().strftime("%Y-%m-%d")
                
                result.append({
                    "title": article.get('title', 'No title'),
                    "source": article.get('publisher', {}).get('title', 'Google News'),
                    "date": formatted_date,
                    "url": article.get('url', '#'),
                    "description": article.get('description', '')[:200]
                })
            
            return result
            
        except Exception as e:
            print(f"Error fetching Google News: {e}")
            return []


class NewsAPIFetcher:
    """
    Fetches news from NewsAPI (https://newsapi.org/)
    Get free API key: https://newsapi.org/register
    Free tier: 100 requests/day
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2/everything"
    
    def fetch(self, ticker: str, company_name: str, days: int = 7) -> List[Dict]:
        if not self.api_key:
            return []
        
        try:
            from datetime import timedelta
            import requests
            
            params = {
                "q": f"{company_name} OR {ticker}",
                "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            articles = response.json().get("articles", [])
            
            return [{
                "title": article["title"],
                "source": article["source"]["name"],
                "date": article["publishedAt"][:10],
                "url": article["url"],
                "description": article.get("description", "")
            } for article in articles[:10]]
            
        except Exception as e:
            print(f"Error fetching NewsAPI: {e}")
            return []


class FinnhubNewsFetcher:
    """
    Fetches news from Finnhub (https://finnhub.io/)
    Note: Limited coverage for Indian stocks
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://finnhub.io/api/v1/company-news"
    
    def fetch(self, ticker: str, days: int = 7) -> List[Dict]:
        if not self.api_key:
            return []
        
        try:
            import requests
            from datetime import timedelta
            
            from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")
            
            params = {
                "symbol": ticker,
                "from": from_date,
                "to": to_date,
                "token": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 403:
                return []
            
            response.raise_for_status()
            articles = response.json()
            
            if not articles:
                return []
            
            return [{
                "title": article["headline"],
                "source": article["source"],
                "date": datetime.fromtimestamp(article["datetime"]).strftime("%Y-%m-%d"),
                "url": article["url"],
                "description": article.get("summary", "")
            } for article in articles[:10]]
            
        except Exception as e:
            print(f"Error fetching Finnhub news: {e}")
            return []