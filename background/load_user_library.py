import pandas as pd
from background.supabase_setup import supabase_setup, get_current_user_id

def load_user_library():
    supabase = supabase_setup()
    user_id = get_current_user_id()
    
    if not user_id:
        return pd.DataFrame() 

    response = supabase.table("user_books") \
        .select("*, books(*)") \
        .eq("user_id", user_id) \
        .execute()
    
    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)
    
    book_details = pd.json_normalize(df['books'])
    df = pd.concat([df.drop(columns=['books']), book_details], axis=1)
    
    return df