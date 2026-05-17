from supabase import create_client, Client
import streamlit as st

@st.cache_resource
def supabase_setup():
    # Safe check for web secrets first, then local environment variables
    url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        # Using warning instead of st.stop() so the app frame can still load
        st.warning("🔒 Database configuration missing. Please verify API keys.")
        return None
        
    return create_client(url, key)

def get_current_user_id():
    supabase = supabase_setup()
    try:
        res = supabase.auth.get_user()
        if res and res.user:
            return res.user.id
    except Exception:
        return None
    return None

    
