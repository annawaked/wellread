from supabase import create_client, Client
import streamlit as st

@st.cache_resource
def supabase_setup():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_current_user_id():
    supabase = supabase_setup()
    try:
        # This is the most reliable way to check the current session
        res = supabase.auth.get_user()
        if res and res.user:
            return res.user.id
    except Exception:
        return None
    return None