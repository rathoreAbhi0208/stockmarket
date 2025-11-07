import json

from pyparsing import Dict
import requests

class LLMAnalyzer:
    """Handles LLM integration with multiple providers"""
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.llm_api_key
        self.model = config.llm_model
    
    def analyze_with_context(self, query: str, context_data: Dict) -> str:
        """Send query to LLM with context"""
        
        if not self.api_key:
            return "⚠️ LLM API key not configured. Add your API key in the sidebar."
        
        # Choose provider based on model
        if "gpt" in self.model.lower():
            return self._call_openai(query, context_data)
        elif "claude" in self.model.lower():
            return self._call_anthropic(query, context_data)
        else:
            return self._call_custom(query, context_data)
    
    def _call_openai(self, query: str, context_data: Dict) -> str:
        """Call OpenAI API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            system_prompt = """You are a financial analyst. Analyze stock data and provide clear insights."""
            user_prompt = f"Query: {query}\n\nData:\n{json.dumps(context_data, indent=2)}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7
            }
            
            response = requests.post(
                self.config.openai_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            return f"Error calling OpenAI: {str(e)}"
    
    def _call_anthropic(self, query: str, context_data: Dict) -> str:
        """Call Anthropic Claude API"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            prompt = f"Query: {query}\n\nData:\n{json.dumps(context_data, indent=2)}"
            
            payload = {
                "model": self.model,
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = requests.post(
                self.config.anthropic_base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"]
            
        except Exception as e:
            return f"Error calling Anthropic: {str(e)}"
    
    def _call_custom(self, query: str, context_data: Dict) -> str:
        """Call custom/local LLM endpoint"""
        return "Custom LLM integration - implement your endpoint here"