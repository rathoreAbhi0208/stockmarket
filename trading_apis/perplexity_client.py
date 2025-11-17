import requests
from typing import Dict
import re

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
        "temperature": 0.1,
        "max_tokens": 250,
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
                'text': f"❌ API Error: {response.status_code}",
                'citations': [],
                'error': True
            }
        
        result = response.json()
        raw_text = result['choices'][0]['message']['content']
        
        # Clean up the text
        cleaned_text = clean_response(raw_text)
        
        return {
            'text': cleaned_text,
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


def clean_response(text: str) -> str:
    """
    Cleans up the response by removing citation numbers, extra formatting, and organizing into clean bullet points.
    """
    # Remove citation numbers like [1], [2], etc.
    text = re.sub(r'\[\d+\]', '', text)
    
    # Remove ** bold markers
    text = text.replace('**', '')
    
    # Split into lines and process
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Remove leading dashes if present
            line = line.lstrip('- ')
            # Add bullet point if it's not empty
            if line:
                cleaned_lines.append(f"• {line}")
    
    # Join with actual newlines (will be displayed properly when printed)
    return '\n'.join(cleaned_lines)


# Test the function
result = chat_with_perplexity("TCS news", "xyz.....")
# Print with proper line breaks
print(result['text'])
print("\n" + "="*50)
print(f"Citations: {len(result['citations'])} sources")
