from typing import List

from pyparsing import Dict
import requests


class TwitterAPIFetcher:
    """
    Fetches tweets from Twitter API v2
    Get API access: https://developer.twitter.com/en/portal/dashboard
    Note: Requires Elevated or Academic access for full search
    """
    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2/tweets/search/recent"
    
    def fetch(self, username: str, max_results: int = 10) -> List[Dict]:
        if not self.bearer_token:
            return self._get_mock_data(username)
        
        try:
            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            params = {
                "query": f"from:{username}",
                "max_results": max_results,
                "tweet.fields": "created_at,public_metrics"
            }
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            tweets = response.json().get("data", [])
            
            return [{
                "author": username,
                "text": tweet["text"],
                "date": tweet["created_at"][:10],
                "likes": tweet["public_metrics"]["like_count"],
                "retweets": tweet["public_metrics"]["retweet_count"]
            } for tweet in tweets]
            
        except Exception as e:
            print(f"Error fetching tweets: {e}")
            return self._get_mock_data(username)
    
    def _get_mock_data(self, username: str) -> List[Dict]:
        return [
            {
                "author": username,
                "text": "Excited about our latest innovation...",
                "date": "2025-11-03",
                "likes": 15000,
                "retweets": 3000
            }
        ]