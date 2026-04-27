import streamlit as st
import json
import google.generativeai as genai 
from background.supabase_setup import supabase_setup
@st.cache_data(ttl=86400)
def get_recommendations(user_id):
    supabase = supabase_setup()
    

    unrated = supabase.table("user_books").select(
            "status, review_text, books(title, author, genre)"
        ).eq("user_id", user_id).execute().data

    #get 2 and 3 stars for all history
    fine = supabase.table("user_books").select(
            "rating, status, review_text, books(title, author, genre)"
        ).eq("user_id", user_id).or_("rating.eq.2, rating.eq.3").execute().data


    #get books four stars or more as favorites
    favs = supabase.table("user_books").select(
            "rating, review_text, books(title, author, genre)"
        ).eq("user_id", user_id).gte("rating", 4).execute().data

    #get dnfs or one stars as hateorites
    hates = supabase.table("user_books").select(
            "rating, status, review_text, books(title, author, genre)"
        ).eq("user_id", user_id).or_("status.eq.dnf, rating.eq.1").execute().data

    if not favs:
        return "You haven't rated enough books highly. Log some 4 or 5-star reads so I can learn your taste."

    fine_list = [f"- {f['books']['title']} by {f['books']['author']} ({f['books']['genre']}): {f['review_text']}" for f in fine]
    fav_list = [f"- {f['books']['title']} by {f['books']['author']} ({f['books']['genre']}): {f['review_text']}" for f in favs]

    hate_list = []
    for h in hates:
        label = "DNF" if h['status'] == 'dnf' else "1 Star"
        hate_list.append(f"- {h['books']['title']} [{label}]: {h['review_text']}")
    
    
    unrated_list = [f"- {f['books']['title']} by {f['books']['author']} ({f['books']['genre']}): {f['review_text']}" for f in unrated]

    
    
    
    #reader profile
    fine_context = "\n".join(fine_list)
    fav_context = "\n".join(fav_list)
    hated_context = "\n".join(hate_list) if hate_list else "None logged yet."
    unrated_context = "\n".join(unrated_list)


    prompt = f"""
    You are an expert personal librarian. 
    Based on the following history, summarize the user's taste and suggest 5 new books.

    Favorites: {fav_context}
    Hates: {hated_context}
    Mid-tier: {fine_context}
    Yet to be read but want to: {unrated_context}

    Return your response EXCLUSIVELY in the following JSON format:
    {{
        "taste_summary": "A short, serious paragraph about their aesthetic and preferences.",
        "books": [
            {{
                "title": "Book Title",
                "author": "Author Name",
                "reason": "Why this matches their specific past reviews.",
                "vibe": "e.g. Dark & Gritty"
            }}
        ]
    }}
    """

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # Use JSON mode for reliability
    model = genai.GenerativeModel(
        model_name='gemini-3-flash-preview',
        generation_config={"response_mime_type": "application/json"}
    )
    
    ai_response = model.generate_content(prompt)
    return json.loads(ai_response.text) # Return a dictionary, not a string
    # prompt = f"""
    # You are an expert personal librarian with deep knowledge of all literary genres.
    # First, summarize the user's reading taste based the following reading history.
    # Then, based on the following reading history and preferences, suggest 5 books the user should read next. 
    
    # These are the user's favorite books (recommend more like these, with similar vibes):
    # {fav_context}
    
    # These are books the user hated. (Styles to avoid at all costs. Consider why they hated in the review_text)
    # {hated_context}

    # These are books the user rated 2 or 3 stars.
    # {fine_context}

    # For each recommendation:
    # 1. Provide the Title and Author.
    # 2. Explain *specifically* why it matches their taste based on their previous high ratings or reviews.
    # 3. Categorize it by "Vibe" (e.g., 'Dark & Gritty', 'Whimsical & Light').
    
    # Keep the tone serious yet encouraging. NEVER suggest books already in the history list.
    # """

    # #configure gemini
    # genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

    # try:
    #     model = genai.GenerativeModel('gemini-3-flash-preview')
    #     ai_response = model.generate_content(prompt)
    # except Exception:
    #     model = genai.GenerativeModel('gemini-2.5-flash')
    #     ai_response = model.generate_content(prompt)


    # ai_response = model.generate_content(prompt)
    # return ai_response.text