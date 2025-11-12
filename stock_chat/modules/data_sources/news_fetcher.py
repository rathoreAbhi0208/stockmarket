import requests
from typing import List, Dict
from datetime import datetime

class GoogleNewsFetcher:
    """
    Fetches news from GNews API (https://gnews.io/)
    API key included - ready to use!
    Free tier: 100 requests/day
    """
    def __init__(self, api_key: str = "6cd5257fe153c5558f44376216e7b57c"):
        self.api_key = api_key
        self.base_url = "https://gnews.io/api/v4/search"
        self.country = 'in'  # India
        self.language = 'en'  # English
        self.max_results = 10
    
    def fetch(self, company_name: str, ticker: str = None) -> List[Dict]:
        """
        Fetch news articles from GNews API
        
        Parameters:
        - company_name: Name of the company (e.g., "Reliance Industries")
        - ticker: Stock ticker (optional, not used for search but kept for compatibility)
        
        Returns:
        - List of news articles with title, source, date, url, and description
        """
        try:
            # Build a more robust search query. Including the ticker symbol alongside
            # the company name helps the GNews API find relevant stock market news
            # more reliably, especially for large, well-known companies.
            search_query = f'"{company_name}" OR {ticker}'
            
            params = {
                "q": search_query,
                "lang": self.language,
                "country": self.country,
                "max": self.max_results,
                "apikey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = data.get('articles', [])
            
            result = []
            for article in articles:
                # Parse the published date
                pub_date = article.get('publishedAt', '')
                try:
                    # GNews returns ISO format like "2024-11-04T10:30:00Z"
                    date_obj = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                except:
                    formatted_date = datetime.now().strftime("%Y-%m-%d")
                
                result.append({
                    "title": article.get('title', 'No title'),
                    "source": article.get('source', {}).get('name', 'GNews'),
                    "date": formatted_date,
                    "url": article.get('url', '#'),
                    "description": article.get('description', '')[:200]
                })
            
            print(f"✓ Fetched {len(result)} articles for {company_name}")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"✗ API key invalid or quota exceeded")
            else:
                print(f"✗ HTTP Error: {e}")
            return []
        except Exception as e:
            print(f"✗ Error fetching news: {e}")
            return []
    
    def fetch_multiple(self, companies: List[Dict[str, str]]) -> Dict[str, List[Dict]]:
        """
        Fetch news for multiple companies
        
        Parameters:
        - companies: List of dicts with 'name' and 'ticker' keys
          Example: [{"name": "Reliance Industries", "ticker": "RELIANCE"}]
        
        Returns:
        - Dictionary with company names as keys and news articles as values
        """
        results = {}
        for company in companies:
            company_name = company.get('name', company.get('ticker', 'Unknown'))
            ticker = company.get('ticker', '')
            
            print(f"\nFetching news for: {company_name}")
            articles = self.fetch(company_name, ticker)
            results[company_name] = articles
        
        return results


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


# Example usage
if __name__ == "__main__":
    # Initialize with default API key (already included)
    fetcher = GoogleNewsFetcher()
    
    # Example 1: Fetch news for a single company
    print("="*70)
    print("Example 1: Single Company")
    print("="*70)
    news = fetcher.fetch("Reliance Industries", "RELIANCE.NS")
    
    for idx, article in enumerate(news, 1):
        print(f"\n{idx}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Date: {article['date']}")
        print(f"   URL: {article['url']}")
    
    # Example 2: Fetch news for multiple companies
    print("\n" + "="*70)
    print("Example 2: Multiple Companies")
    print("="*70)
    
    companies = [
        {"name": "Reliance Industries", "ticker": "RELIANCE.NS"},
        {"name": "TCS", "ticker": "TCS.NS"},
        {"name": "Infosys", "ticker": "INFY.NS"}
    ]
    
    all_news = fetcher.fetch_multiple(companies)
    
    for company, articles in all_news.items():
        print(f"\n📰 {company}: {len(articles)} articles found")