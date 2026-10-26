import streamlit as st
from openai import OpenAI
import httpx
import sqlite3
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Free AI Chatbot + DB", page_icon="🤖")
st.title("🤖 Free AI Assistant with Database")

# 2. Secure TOML Secret Management
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    st.error("🔑 API Key missing! Please add 'OPENROUTER_API_KEY' to your Streamlit secrets.")
    st.stop()

# 3. Database Initialization & Utilities
def init_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            role TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_message_to_db(role, content):
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO messages (timestamp, role, content) VALUES (?, ?, ?)", (timestamp, role, content))
    conn.commit()
    conn.close()

def load_chat_history():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("SELECT role, content FROM messages ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def clear_db():
    conn = sqlite3.connect("chat_history.db")
    c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()

# Start the DB layout
init_db()

# 4. Sidebar Interface Controls
with st.sidebar:
    st.header("Configuration")
    st.success("🔒 API Key loaded securely from Secrets.")
    st.info("System Route: openrouter/free (Auto-selects active free models)")
    
    st.header("Database Controls")
    if st.button("🗑️ Clear Saved History", type="primary"):
        clear_db()
        st.session_state.messages = []
        st.success("Chat history cleared from database!")
        st.rerun()

# 5. Load Stored Conversations
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

# 6. Render Chat Messages on Layout
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Core Prompt Feeder & Action Framework
if prompt := st.chat_input("What is on your mind?"):
    
    # Save user message to UI state and the SQLite file
    st.session_state.messages.append({"role": "user", "content": prompt})
    save_message_to_db("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # 8. API Engine Run & Output Pipeline
    with st.chat_message("assistant"):
        try:
            http_client = httpx.Client(timeout=httpx.Timeout(45.0, connect=10.0))
            
            client = OpenAI(
                base_url="https://openrouter.ai",
                api_key=api_key,
                http_client=http_client,
                default_headers={
                    "HTTP-Referer": "http://localhost:8501", 
                    "X-Title": "Streamlit Free App"      
                }
            )
            
            response = client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True
            )
            
            # Unpacks the stream chunks safely if OpenRouter returns lists
            def response_generator():
                for chunk in response:
                    if hasattr(chunk, 'choices') and chunk.choices and len(chunk.choices) > 0:
                        first_choice = chunk.choices[0]
                        delta = first_choice.get('delta', None) if isinstance(first_choice, dict) else getattr(first_choice, 'delta', None)
                        if delta:
                            content = delta.get('content', '') if isinstance(delta, dict) else getattr(delta, 'content', '')
                            if content:
                                yield content

            # Stream out the text response live
            full_response = st.write_stream(response_generator())
            
            # Finalize entries in local memory arrays and SQL database
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            save_message_to_db("assistant", full_response)
            
        except Exception as e:
            st.error(f"Execution Error: {str(e)}")
