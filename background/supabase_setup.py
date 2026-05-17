import os
import streamlit as st
from supabase import create_client

def supabase_setup():
    # Check Streamlit Cloud secrets first, fall back to local environment variables
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        # This will print directly to your Streamlit App screen if keys are missing
        st.error("🔒 Missing Supabase Credentials! Check your Streamlit Secrets.")
        st.stop()
        
    return create_client(url, key)

def get_current_user_id():
    # If you are using a hardcoded user ID for testing or a session state
    # Make sure it's accessible here
    return st.session_state.get("user_id") or os.getenv("USER_ID")