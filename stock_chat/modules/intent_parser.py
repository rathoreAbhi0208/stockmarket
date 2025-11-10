from typing import Dict
import re

class IntentParser:
    """Parse user intent from queries"""
    
    @staticmethod
    def parse(query: str, ticker: str) -> Dict:
        query_lower = query.lower()
        
        intent = {
            "type": "general",
            "ticker": ticker,
            "quarter": None,
            "username": None
        }
        
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