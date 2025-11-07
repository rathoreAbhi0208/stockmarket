from typing import Dict


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
        elif any(w in query_lower for w in ["earnings", "commentary", "quarter", "results", "transcript"]):
            intent["type"] = "earnings"
            # Extract quarter if mentioned
            for q in ["q1", "q2", "q3", "q4"]:
                if q in query_lower:
                    intent["quarter"] = q.upper()
                    break
        
        # Check for Twitter/social media keywords
        elif any(w in query_lower for w in ["tweet", "twitter", "social", "ceo", "posts", "saying"]):
            intent["type"] = "tweets"
        
        return intent