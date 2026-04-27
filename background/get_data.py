import streamlit as st
import pandas as pd 
from background.supabase_setup import supabase_setup, get_current_user_id

supabase = supabase_setup()

@st.cache_data(ttl=600) 
def load_data():

    user_id = get_current_user_id()
    if not user_id:
        return pd.DataFrame()
    
    
    response = supabase.table("user_books").select(
        "id, rating, status, read_date, date_started, source, reread, review_text, books(id, title, author, genre, subgenre, pages, author_gender, thumbnail_url, pub_year, description)"
    ).execute()
    
    data = []
    # Updated load_data (The "Safe" Version)
    for record in response.data:
        book_info = record.pop('books')
        
        # We keep 'id' as it was (the user_books ID) 
        # and add a NEW specific key for the book's primary key
        book_table_id = book_info.get('id') 
        
        data.append({
            **record, 
            **book_info, 
            "book_id": book_table_id # New unique name for the book table
        })
    return pd.DataFrame(data)