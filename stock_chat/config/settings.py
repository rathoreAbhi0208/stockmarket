from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Application configuration"""
    ticker: str = "AAPL"
    company_name: str = "Apple Inc."
    
    # API Keys
    llm_api_key: Optional[str] = None
    llm_model: str = "gpt-3.5-turbo"
    news_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    alpha_vantage_key: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    twitter_username: Optional[str] = None
    
    # API Endpoints
    openai_base_url: str = "https://api.openai.com/v1/chat/completions"
    anthropic_base_url: str = "https://api.anthropic.com/v1/messages"