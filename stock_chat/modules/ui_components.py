from typing import Dict, List, Optional
import streamlit as st
from config.settings import Config
from modules.data_fetcher import StockDataFetcher
from modules.llm_analyzer import LLMAnalyzer
from modules.intent_parser import IntentParser

def render_sidebar() -> Config:
    """Render sidebar and return configuration"""
    with st.sidebar:
        st.title("📈 Stock Analysis")
        
        st.divider()
        
        # Show what's FREE
        with st.expander("🟢 Active Free Features", expanded=True):
            st.success("✅ Fundamentals (Yahoo Finance)")
            st.success("✅ Latest News (Google News)")
            st.success("✅ Earnings Transcripts (FMP)")
            st.info("💡 No API keys needed! Just enter a ticker and start asking questions.")
        
        # Optional AI enhancement
        with st.expander("🤖 AI Analysis (Optional)", expanded=False):
            st.warning("⚠️ All major AI providers now require payment details")
            
            ai_option = st.radio(
                "Choose AI Option:",
                ["None (Use Free Data Only)", 
                 "Local LLM (Ollama - Free)", 
                 "OpenAI (Requires Payment)",
                 "Anthropic (Requires Payment)"]
            )
            
            if ai_option == "None (Use Free Data Only)":
                st.success("✅ Using free data sources - no AI analysis")
                llm_api_key = None
                llm_model = None
                
            elif ai_option == "Local LLM (Ollama - Free)":
                st.info("""
                **Setup Ollama (One-time):**
                1. Install: `curl -fsSL https://ollama.com/install.sh | sh`
                2. Run: `ollama pull llama2`
                3. Start: `ollama serve`
                4. Use endpoint: http://localhost:11434
                """)
                llm_api_key = "local"
                llm_model = "ollama-llama2"
                
            elif ai_option == "OpenAI (Requires Payment)":
                st.warning("💳 Requires payment details + $5 minimum")
                llm_api_key = st.text_input("OpenAI API Key", type="password", key="openai_key")
                llm_model = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4-turbo-preview"])
                
            else:  # Anthropic
                st.warning("💳 Requires payment details (but gives $5 credit)")
                llm_api_key = st.text_input("Anthropic API Key", type="password", key="anthropic_key")
                llm_model = st.selectbox("Model", ["claude-3-5-sonnet-20240620"])
        
        # Other optional features
        with st.expander("📰 Additional News Sources (Optional)"):
            st.info("💡 Google News works great by default!")
            news_api_key = st.text_input("NewsAPI Key", type="password", 
                help="Optional: https://newsapi.org/")
            finnhub_key = st.text_input("Finnhub Key", type="password",
                help="Optional: https://finnhub.io/")
        
        with st.expander("📊 Alternative Data Sources (Optional)"):
            st.info("💡 Yahoo Finance works great by default!")
            alpha_key = st.text_input("Alpha Vantage Key", type="password",
                help="Optional: https://www.alphavantage.co/")
        
        with st.expander("🐦 Twitter/Social Media (Optional)"):
            st.info("💡 Track CEO/company social media posts")
            twitter_token = st.text_input("Twitter Bearer Token", type="password",
                help="Optional: Requires Twitter Developer account - https://developer.twitter.com/")
            twitter_username = st.text_input("CEO/Company Username", value="",
                placeholder="e.g., elonmusk, tim_cook",
                help="Twitter username to track (without @)")
            
            if twitter_token and twitter_username:
                st.success(f"✅ Tracking @{twitter_username}")
        
        st.divider()
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
        
        return Config(
            ticker=None, # No longer needed from sidebar
            company_name=None, # No longer needed from sidebar
            llm_api_key=llm_api_key,
            llm_model=llm_model,
            news_api_key=news_api_key or None,
            finnhub_api_key=finnhub_key or None,
            alpha_vantage_key=alpha_key or None,
            twitter_bearer_token=twitter_token or None,
            twitter_username=twitter_username or None
        )


def render_chat_interface(config: Config):
    """Render main chat interface"""
    
    # Welcome banner
    if len(st.session_state.messages) == 0:
        st.info("""
        🎯 **Welcome to Stock Analysis Chat!**
        
        Try asking:
        - "Show me the fundamentals for RELIANCE"
        - "What's the latest news for INFY?"
        - "Q3 earnings commentary for TCS"
        - "What's the P/E ratio and market cap for HDFCBANK?"
        
        💡 All features work without any API keys!
        """)
    
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about the stock..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Fetching data..."):
                response = process_query(prompt, config)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})


def process_query(prompt: str, config: Config) -> str:
    """Process user query and generate response"""
    fetcher = StockDataFetcher(config)
    intent = IntentParser.parse(prompt)
    
    ticker = intent.get("ticker")
    suggestion = intent.get("suggestion")
    
    if not ticker:
        if suggestion:
            return f"""Did you mean **{suggestion}**?

Please try your query again with the suggested ticker. For example:
- "Show fundamentals for **{suggestion}**"
"""
        else:
            return """**I can help you analyze stocks!** 📊

Please include a stock ticker in your query. For example:
- "Show fundamentals for **RELIANCE**"
- "Latest news for **TCS**"
"""
    
    data = None
    response = ""
    company_name = fetcher._get_company_name(ticker)

    # Fetch data based on intent
    if intent["type"] == "fundamental":
        data = fetcher.get_fundamental_data(ticker)
        response = format_fundamental_response(data, ticker, company_name)
        
    elif intent["type"] == "news":
        data = fetcher.get_latest_news(
            ticker=ticker,
            company_name=company_name,
            news_api_key=config.news_api_key,
            finnhub_api_key=config.finnhub_api_key
        )
        response = format_news_response(data, ticker)
        
    elif intent["type"] == "earnings":
        data = fetcher.get_earnings_commentary(ticker, intent.get("quarter"))
        response = format_earnings_response(data, ticker)
        
    elif intent["type"] == "tweets":
        if not config.twitter_username:
            return "⚠️ Please provide a Twitter username in the sidebar under the 'Twitter/Social Media' section."
        
        data = fetcher.get_leader_tweets(config.twitter_username)
        response = format_tweets_response(data, config.twitter_username)
    else:
        # General query or unclear intent
        response = f"""**I can help you analyze {ticker}!** 📊

**Available Commands:**

📊 **Fundamentals**
- "Show fundamentals"
- "What's the P/E ratio?"
- "Market cap and revenue"

📰 **News** 
- "Latest news"
- "Recent headlines"
- "What's happening with {ticker}?"

🗣️ **Earnings**
- "Q3 earnings commentary" (US stocks only)
- "Latest earnings call"
- "Recent earnings news" (Works for all stocks)

🐦 **Social Media** (Optional - needs Twitter API)
- "Show recent tweets"
- "What's the CEO saying?"
- Configure in sidebar → Twitter section

💡 **Pro tip:** All data features work without any API keys - completely free!
"""
    
    # Add AI analysis if configured
    if config.llm_api_key and config.llm_model and data:
        should_analyze = (
            (isinstance(data, dict) and "error" not in data) or
            (isinstance(data, list) and len(data) > 0)
        )
        
        if should_analyze:
            ai_response = add_ai_analysis(prompt, data, config)
            if ai_response:
                response += f"\n\n{ai_response}"
    
    return response


def add_ai_analysis(prompt: str, data: Dict, config: Config) -> str:
    """Add AI analysis if available"""
    try:
        # Check for Ollama
        if config.llm_model and "ollama" in config.llm_model.lower():
            return call_ollama(prompt, data)
        
        # Check for paid APIs
        analyzer = LLMAnalyzer(config)
        llm_insight = analyzer.analyze_with_context(prompt, data)
        
        if llm_insight and not llm_insight.startswith("⚠️"):
            return f"---\n\n**🤖 AI Analysis:**\n\n{llm_insight}"
        else:
            return ""
            
    except Exception as e:
        return f"\n\n⚠️ AI analysis failed: {str(e)}"


def call_ollama(prompt: str, data: Dict) -> str:
    """Call local Ollama LLM"""
    try:
        import requests
        import json
        
        system_msg = "You are a financial analyst. Provide clear insights based on the data."
        user_msg = f"Query: {prompt}\n\nData: {json.dumps(data, indent=2)[:5000]}"
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": f"{system_msg}\n\n{user_msg}",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return f"---\n\n**🤖 AI Analysis (Local):**\n\n{result['response']}"
        else:
            return "\n\n⚠️ Ollama not running. Start with: `ollama serve`"
            
    except Exception as e:
        return f"\n\n⚠️ Ollama error: {str(e)}\n\nMake sure Ollama is installed and running."


def format_fundamental_response(data: Dict, ticker: str, company_name: str) -> str:
    """Format fundamental data with insights"""
    if "error" in data:
        return f"⚠️ **Error:** {data['error']}"
    
    response = f"""## 📊 {ticker} - Fundamental Analysis
**{company_name}**

---

### Key Metrics

| Metric | Value |
|--------|-------|
| **P/E Ratio** | {data.get('pe_ratio', 'N/A')} |
| **Market Cap** | {format_large_number(data.get('market_cap', 'N/A'))} |
| **Revenue (TTM)** | {format_large_number(data.get('revenue', 'N/A'))} |
| **Profit Margin** | {format_percentage(data.get('profit_margin', 'N/A'))} |
| **ROE** | {format_percentage(data.get('roe', 'N/A'))} |
| **Debt/Equity** | {data.get('debt_to_equity', 'N/A')} |
| **Dividend Yield** | {format_percentage(data.get('dividend_yield', 'N/A'))} |

---

### Quick Insights

"""
    
    # Add some basic insights
    try:
        pe = float(data.get('pe_ratio', 0))
        if pe > 0 and pe < 15:
            response += "- 💰 **Value Play:** P/E ratio suggests potential undervaluation\n"
        elif pe > 30:
            response += "- 🚀 **Growth Premium:** High P/E indicates growth expectations\n"
    except:
        pass
    
    try:
        margin = float(str(data.get('profit_margin', '0')).replace('%', ''))
        if margin > 20:
            response += "- 📈 **Strong Margins:** Above 20% profit margin\n"
    except:
        pass
    
    if data.get('note'):
        response += f"\n💡 *{data['note']}*"
    
    return response


def format_news_response(articles: List[Dict], ticker: str) -> str:
    """Format news with better structure"""
    if not articles:
        return f"⚠️ No recent news found for {ticker}"
    
    response = f"""## 📰 Latest News: {ticker}

---

"""
    
    for i, article in enumerate(articles[:6], 1):
        response += f"### {i}. {article['title']}\n\n"
        response += f"📅 {article['date']} | 📰 {article['source']}\n\n"
        
        if article.get('description'):
            response += f"{article['description'][:180]}...\n\n"
        
        if article.get('url') and article['url'] != '#':
            response += f"[Read more →]({article['url']})\n\n"
        
        response += "---\n\n"
    
    return response


def format_earnings_response(data: Dict, ticker: str) -> str:
    """Format earnings commentary"""
    if "error" in data:
        return f"⚠️ **Error:** {data['error']}\n\n💡 {data.get('suggestion', '')}"

    # Handle news commentary for Indian stocks
    if data.get("type") == "commentary":
        articles = data.get("articles", [])
        response = f"## 🗣️ Earnings Commentary: {ticker}\n\n"
        response += "Here are the top news articles related to recent earnings:\n\n---\n\n"
        for i, article in enumerate(articles, 1):
            response += f"### {i}. {article['title']}\n\n"
            pub_date = article.get('published', 'N/A')
            if pub_date and ' ' in pub_date:
                pub_date = pub_date.split(' ')[0] # Clean up date
            
            response += f"📅 {pub_date} | 📰 {article.get('source', 'N/A')}\n\n"
            
            if article.get('link') and article['link'] != '#':
                response += f"[Read more →]({article['link']})\n\n"
            
            response += "---\n\n"
        return response

    # Handle transcript for US stocks
    elif data.get("type") == "transcript":
        content = data.get('content', '')
        quarter = data.get('quarter', 'N/A')
        year = data.get('year', 'N/A')
        
        # Extract key points (first 2000 chars)
        preview = content[:2000] if len(content) > 2000 else content
        
        response = f"""## 🗣️ Earnings Call Transcript: {ticker} Q{quarter} {year}

---

{preview}

{'...' if len(content) > 2000 else ''}

---

💡 **This is {'a preview of' if len(content) > 2000 else ''} the earnings call transcript from Financial Modeling Prep.**
"""
        return response

    return "⚠️ Could not format the earnings response. The data structure was not recognized."


def format_tweets_response(tweets: List[Dict], username: str) -> str:
    """Formats tweets into a markdown string."""
    if not tweets:
        return f"⚠️ No recent tweets found for **@{username}**. This could be due to an invalid username or API key."

    response = f"## 🐦 Latest Tweets from @{username}\n\n---\n\n"

    for tweet in tweets:
        text = tweet.get('text', 'No content')
        date = tweet.get('date', 'N/A')
        likes = tweet.get('likes', 0)
        retweets = tweet.get('retweets', 0)

        response += f"**📝 Tweet:**\n\n"
        response += f"> {text.replace('\n', '\n> ')}\n\n"
        response += f"📅 **Date:** {date}\n"
        response += f"❤️ **Likes:** {likes} | 🔁 **Retweets:** {retweets}\n\n"
        response += "---\n\n"
    
    return response


def format_large_number(value):
    """Format large numbers nicely"""
    if isinstance(value, (int, float)):
        if value >= 1_000_000_000_000:
            return f"${value/1_000_000_000_000:.2f}T"
        elif value >= 1_000_000_000:
            return f"${value/1_000_000_000:.2f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.2f}M"
    return value


def format_percentage(value):
    """Format percentage values"""
    if isinstance(value, (int, float)):
        return f"{value*100:.2f}%" if value < 1 else f"{value:.2f}%"
    return value