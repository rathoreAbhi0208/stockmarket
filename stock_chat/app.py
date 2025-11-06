import streamlit as st
from modules.data_fetcher import StockDataFetcher
from modules.llm_analyzer import LLMAnalyzer
from modules.intent_parser import IntentParser
from modules.ui_components import render_sidebar, render_chat_interface
from config.settings import Config

st.set_page_config(
    page_title="Stock Analysis Chat",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_stock" not in st.session_state:
    st.session_state.selected_stock = ""

def main():
    # Sidebar
    config = render_sidebar()
    
    # Main chat interface
    render_chat_interface(config)

if __name__ == "__main__":
    main()