import requests
from typing import Dict

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


def chat_with_perplexity(prompt: str, api_key: str) -> Dict:
    """
    Uses Perplexity's Sonar model with built-in web search for latest Indian stock data.
    """
    system_prompt = """You are a financial assistant for the Indian stock market.
When the user asks for news, provide a bulleted list of precise headlines.
For all other queries, give concise, data-driven answers with numbers and dates, sourcing from Economic Times."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1, # Slightly lower temperature for more focused responses
        "max_tokens": 250,  # Reduced max_tokens for faster, more concise answers
        "return_citations": True,
        "search_recency_filter": "day"
    }
    
    try:
        response = requests.post(
            PERPLEXITY_API_URL, 
            headers=headers, 
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                'text': f"API Error: {response.status_code}",
                'citations': [],
                'error': True
            }
        
        result = response.json()
        return {
            'text': result['choices'][0]['message']['content'],
            'citations': result.get('citations', []),
            'error': False
        }
    except requests.exceptions.Timeout:
        return {
            'text': "⏱️ Request timed out. Please try again.",
            'citations': [],
            'error': True
        }
    except Exception as e:
        return {
            'text': f"Error: {str(e)}",
            'citations': [],
            'error': True
        }
