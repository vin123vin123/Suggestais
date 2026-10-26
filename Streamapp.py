import streamlit as st
from openai import OpenAI
import httpx
import sqlite3
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Free AI Chatbot + DB", page_icon="🤖")
st.title("🤖 Free AI Assistant with Database")

# 2. FETCH KEY FROM TOML SECRETS
# This looks for the key in your local TOML file, or the Cloud Dashboard settings.
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    st.error("🔑 API Key missing! Please add 'OPENROUTER_API_KEY' to your Streamlit secrets.")
    st.stop()

# [Keep your Database helper functions init_db(), save_message_to_db(), etc. here...]

# 3. Updated Sidebar Configuration (No more manual text input needed!)
with st.sidebar:
    st.header("Configuration")
    st.success("🔒 API Key loaded securely from Secrets.")
    st.info("System Route: openrouter/free")
    
    st.header("Database Controls")
    if st.button("🗑️ Clear Saved History", type="primary"):
        # clear_db() function logic...
        st.session_state.messages = []
        st.rerun()

# [The rest of your chat logic and st.write_stream remains exactly the same...]
