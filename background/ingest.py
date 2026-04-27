import pandas as pd
import streamlit as st
from supabase import create_client


SUPABASE_URL = st.secrets['SUPABASE_URL']
SUPABASE_KEY = st.secrets['SUPABASE_KEY']
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
USER_ID = st.secrets['CURRENT_USER_ID']

def ingest_data(file_path):
    df = pd.read_excel(file_path)
    df = df.where(pd.notnull(df), None)
    print(f"Starting ingestion of {len(df)} rows...")

    for index, row in df.iterrows():
        try:

            book_metadata = {
                "title": str(row['Title']).strip(),
                "author": str(row['Author']).strip(),
                "genre": row['Genre'],
                "subgenre": row['Subgenre'],
                "pages": int(row['Pages']) if pd.notnull(row['Pages']) else None,
                "author_gender": row['Gender']
            }

            book_res = supabase.table("books").upsert(
                book_metadata, on_conflict="title, author"
            ).execute()
            
            db_book_id = book_res.data[0]['id']

            user_log = {
                "user_id": USER_ID,
                "book_id": db_book_id,
                "rating": int(row['Rating']) if pd.notnull(row['Rating']) else None,
                "read_date": row['Date'].isoformat() if pd.notnull(row['Date']) and hasattr(row['Date'], 'isoformat') else None,                
                "review_text": row['Review'],
                "source": row['Source'],
                "reread": bool(row['Reread']) if pd.notnull(row['Reread']) else False,
                "status": "read" 
            }

            supabase.table("user_books").upsert(
                user_log, on_conflict="user_id, book_id, read_date"
            ).execute()

            print(f"✅ Success: {row['Title']} ({row['Date']})")

        except Exception as e:
            print(f"❌ Error on row {index} ({row['Title']}): {e}")

if __name__ == "__main__":
    ingest_data("book_log.xlsx")