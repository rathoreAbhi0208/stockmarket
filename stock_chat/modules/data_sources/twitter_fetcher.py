# modules/twitter_fetcher.py
from typing import List, Dict, Optional
import requests


class TwitterAPIFetcher:
    """
    Fetches tweets from Twitter API v2 using the bearer token you provide.
    - Uses /2/users/by/username/:username to resolve user id
    - Then uses /2/users/:id/tweets to get recent tweets
    """

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token
        self.user_lookup_url = "https://api.twitter.com/2/users/by/username/{}"
        self.user_tweets_url = "https://api.twitter.com/2/users/{}/tweets"

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def fetch(self, username: str, max_results: int = 10, exclude_replies: bool = True, exclude_retweets: bool = True) -> List[Dict]:
        """
        Fetch recent tweets for a username.
        Returns a list of dicts: {author, text, date, likes, retweets}
        """
        if not self.bearer_token:
            return self._get_mock_data(username)

        try:
            # Resolve user id
            user_resp = requests.get(self.user_lookup_url.format(username), headers=self._headers(), timeout=10)
            user_resp.raise_for_status()
            user_data = user_resp.json().get("data")
            if not user_data or "id" not in user_data:
                print(f"⚠️ Could not resolve user id for @{username}")
                return []

            user_id = user_data["id"]

            # Prepare params
            params = {
                "max_results": max(5, min(100, int(max_results))),  # clamp between 5-100
                "tweet.fields": "created_at,public_metrics",
            }

            # Twitter API v2 supports `exclude` param to skip retweets/replies
            excludes = []
            if exclude_retweets:
                excludes.append("retweets")
            if exclude_replies:
                excludes.append("replies")
            if excludes:
                params["exclude"] = ",".join(excludes)

            tweets_resp = requests.get(self.user_tweets_url.format(user_id), headers=self._headers(), params=params, timeout=10)
            tweets_resp.raise_for_status()

            tweets_data = tweets_resp.json().get("data", [])
            tweets = []
            for t in tweets_data:
                tweets.append({
                    "author": username,
                    "text": t.get("text", ""),
                    "date": (t.get("created_at") or "")[:10],
                    "likes": t.get("public_metrics", {}).get("like_count", 0),
                    "retweets": t.get("public_metrics", {}).get("retweet_count", 0),
                })

            return tweets

        except requests.exceptions.RequestException as e:
            print(f"❌ Network or API error: {e}")
            return self._get_mock_data(username)
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")
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

# Quick local test (only when run directly)
if __name__ == "__main__":
    # Replace with a real token for quick local test
    BEARER = "AAAAAAAAAAAAAAAAAAAAAAKM5QEAAAAAB6r0C7tIlwqPZUT2L3W1I4TToT0%3DAInWz4J9tRZ4HvnjuZ1RV2hyqQf4wGUseGWI8Cuj0mvniWfU5B"
    fetcher = TwitterAPIFetcher(BEARER)
    sample = fetcher.fetch("elonmusk", max_results=5)
    for t in sample:
        print(t)