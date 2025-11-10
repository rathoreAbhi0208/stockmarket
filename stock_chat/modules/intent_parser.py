from typing import Dict
import re

# Import from data_fetcher to get the list of known stocks
from modules.data_fetcher import INDIAN_STOCKS

class IntentParser:
    """Parse user intent from queries"""
    
    @staticmethod
    def _find_ticker(query: str) -> str | None:
        """Find a known stock ticker in the query string."""
        query_upper = query.upper()
        # Check for word boundaries to avoid matching parts of words
        for ticker in INDIAN_STOCKS.keys():
            # \b is a word boundary in regex
            if re.search(r'\b' + ticker + r'\b', query_upper):
                return ticker
        return None

    @staticmethod
    def parse(query: str) -> Dict:
        query_lower = query.lower()
        
        # Find the ticker in the query first
        ticker = IntentParser._find_ticker(query)

        intent = {
            "type": "general",
            "ticker": ticker,
            "quarter": None,
            "username": None
        }

        if not ticker: # If no ticker is found, no need to check for other intents
            return intent

        # Check for fundamental analysis keywords
        if any(w in query_lower for w in ["fundamental", "financials", "ratios", "p/e", "pe ratio", 
                                            "market cap", "revenue", "profit margin", "roe", "debt"]):
            intent["type"] = "fundamental"
        
        # Check for news keywords
        elif any(w in query_lower for w in ["news", "latest", "headlines", "recent", "happening"]):
            intent["type"] = "news"
        
        # Check for earnings keywords
        elif any(w in query_lower for w in ["earning", "earnings", "commentary", "quarter", "results", "transcript"]):
            intent["type"] = "earnings"
            # Use regex to find quarter mentions like "Q2", "q1", "2nd quarter"
            match = re.search(r'(q[1-4])|(1st|2nd|3rd|4th)\s+quarter', query_lower)
            if match:
                quarter_map = {"1st": "Q1", "2nd": "Q2", "3rd": "Q3", "4th": "Q4"}
                quarter_str = match.group(1) or match.group(2) # "q2" or "2nd"
                intent["quarter"] = quarter_map.get(quarter_str, quarter_str.upper())
        
        # Check for Twitter/social media keywords
        elif any(w in query_lower for w in ["tweet", "twitter", "social", "ceo", "posts", "saying"]):
            intent["type"] = "tweets"
        
        return intent