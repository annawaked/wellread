import requests
import streamlit as st 
import google.generativeai as genai



books_api_key = st.secrets['GOOGLE_BOOKS_API_KEY']
@st.cache_data(show_spinner="Searching Google Books...", ttl=3600) 

def fetch_book_metadata(title, author):
    clean_title = title.strip().replace(" ", "+")
    clean_author = author.strip().replace(" ", "+")
    
    url = (
        f"https://www.googleapis.com/books/v1/volumes?"
        f"q=intitle:{clean_title}+inauthor:{clean_author}"
        f"&key={books_api_key}"
    )
    
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        
        if "error" in data:
            st.sidebar.error(f"Google API Error: {data['error']['message']}")
            return None

        if "items" in data:
            volume_info = data["items"][0].get("volumeInfo", {})
    
            raw_title = volume_info.get("title", title).strip()
            raw_author = ", ".join(volume_info.get("authors", [author])).strip()
            
            raw_categories = volume_info.get("categories", [])
            primary_category = raw_categories[0]
            category_str = " ".join(raw_categories).lower()
            
            pub_year = volume_info.get("publishedDate", "")
            
            

            # 2. Check for Non-Fiction indicators FIRST
            nonfiction_indicators = [
                "biography", "autobiography", "memoir", "science", "history", 
                "sociology", "true crime", "medical", "nature", "survival", "essays"
            ]

            if any(word in category_str for word in nonfiction_indicators):
                genre = "Non-Fiction"
            elif "fiction" in category_str:
                genre = "Fiction"
            else:
                genre = "Non-Fiction"

            ai_subgenre = classify_subgenre_with_ai(raw_title, raw_author, genre)

            return {
                "title": raw_title.title(),
                "author":raw_author.title(),
                "pages": volume_info.get("pageCount", 0),
                "genre": genre,
                "subgenre": ai_subgenre,
                "description": volume_info.get("description", ""),
                "pub_year": pub_year, 
                "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail"), 
            }
        return None
        
    except Exception as e:
        st.sidebar.error(f"Connection Error: {e}")
        return None
    
def smart_title(text):
    if not text: return ""
    minor_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with'}
    words = text.lower().split()
    # Capitalize the first word; capitalize others only if they aren't "minor"
    res = [words[0].capitalize()] + [
        w if w in minor_words else w.capitalize() for w in words[1:]
    ]
    return " ".join(res)

def classify_subgenre_with_ai(title, author, genre):
    from background.options import fiction_subgenres, nonfiction_subgenres
    
    valid_options = fiction_subgenres() if genre == "Fiction" else nonfiction_subgenres()
    options_string = ", ".join(valid_options)

    # We tell Gemini EXACTLY what key to use in the JSON
    prompt = f"""
    Act as a librarian. Classify '{title}' by {author} into ONE of these:
    [{options_string}]
    
    Return JSON only: {{"subgenre": "Chosen Category"}}
    """

    try:
        model = genai.GenerativeModel(
            model_name='gemini-3-flash-preview', 
            generation_config={"response_mime_type": "application/json"}
        )
        
        response = model.generate_content(prompt)
        
        import json
        res_json = json.loads(response.text)
        ai_choice = res_json.get("subgenre")

        # DEBUG: Check your terminal to see what the AI actually picked!
        print(f"DEBUG: AI picked '{ai_choice}' for {title}")

        # Strict check against your options.py list
        if ai_choice in valid_options:
            return ai_choice
        
        # If the AI hallucinated a subgenre not in your list, 
        # try a case-insensitive match as a backup
        for option in valid_options:
            if ai_choice and ai_choice.lower() == option.lower():
                return option
                
        return None
    
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None