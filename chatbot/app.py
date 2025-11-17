import streamlit as st
import re
from per_client import chat_with_perplexity

# Cache the chat_with_perplexity function to avoid repeated API calls for the same prompt
@st.cache_data(ttl=3600, show_spinner=False) # Cache results for 1 hour (3600 seconds)
def cached_chat_with_perplexity(prompt: str, api_key: str):
    return chat_with_perplexity(prompt, api_key)

st.set_page_config(
    page_title="🇮🇳 Indian Stock Market Assistant",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# Header
st.title("🇮🇳 Indian Stock Market Assistant")
# st.caption("Powered by Perplexity AI • Real-Time Data")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    api_key_input = st.text_input(
        "API Key",
        value=st.session_state.api_key,
        type="password",
        key="api_key_input"
    )
    
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
    
    st.divider()
    
    st.header("💡 Quick Queries")
    
    quick_queries = {
        "Reliance Price": "Reliance Industries current stock price",
        "TCS News": "TCS latest news today",
        "HDFC Results": "HDFC Bank latest quarterly results",
        "Infosys vs TCS": "Compare Infosys and TCS today",
        "Nifty 50": "Nifty 50 index today",
        "Adani Update": "Adani stocks news this week"
    }
    
    for label, query in quick_queries.items():
        if st.button(label, key=label, use_container_width=True):
            st.session_state.pending_query = query
            st.rerun()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True, key="clear_btn"):
            st.session_state.chat_history = []
            st.rerun()
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_btn"):
            st.rerun()

# Main area
if len(st.session_state.chat_history) == 0:
    st.info("👋 Ask me anything about Indian stocks! Try the quick queries on the left or type below.")

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"]) # Citations are already stripped from content

# Process pending query from sidebar
if hasattr(st.session_state, 'pending_query'):
    query = st.session_state.pending_query
    del st.session_state.pending_query

    st.session_state.chat_history.append({"role": "user", "content": query})

    with st.chat_message("assistant"):
        thinking_message = st.empty()  # Create an empty container
        with st.spinner("🔍 Searching..."):
            result = cached_chat_with_perplexity(query, st.session_state.api_key)
            st.markdown(result['text'])
            
            if result.get('citations'):
                with st.expander("📎 Sources", expanded=False):
                    st.markdown(result['text'])
            else:
                st.markdown(result['text'])

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": result['text']
            })

# Chat input
if prompt := st.chat_input("Ask about any Indian stock...", key="chat_input_main"):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        thinking_message = st.empty()  # Create an empty container
        with st.spinner("🔍 Searching..."):
            result = cached_chat_with_perplexity(prompt, st.session_state.api_key)
            # Remove citation markers like [1], [2], etc. from the text
            clean_text = re.sub(r'\[\d+\]', '', result['text'])
            st.markdown(clean_text)

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": clean_text
            })

    st.rerun()

# # Footer
# st.divider()
# st.caption("⚠️ For informational purposes only • Not financial advice")