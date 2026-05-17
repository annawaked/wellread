import requests
import streamlit as st
import google.generativeai as genai

# --- CONFIGURE KEYS ---
books_api_key = st.secrets.get("GOOGLE_BOOKS_API_KEY")
genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))


@st.cache_data(show_spinner="Searching Google Books...", ttl=300)
def fetch_book_metadata(title, author):
    if not title or not author:
        return None

    params = {
        "q": f"intitle:{title} inauthor:{author}",
        "key": books_api_key
    }

    try:
        response = requests.get(
            "https://www.googleapis.com/books/v1/volumes",
            params=params,
            timeout=5
        )

        # --- DEBUG LOGGING (check Streamlit logs) ---
        print("STATUS:", response.status_code)
        print("RESPONSE TEXT:", response.text[:500])

        if response.status_code != 200:
            st.error(f"HTTP Error: {response.status_code}")
            st.write(response.text)
            return None

        data = response.json()

        if "error" in data:
            st.error(f"Google API Error: {data['error']}")
            return None

        if "items" not in data or not data["items"]:
            return None

        volume_info = data["items"][0].get("volumeInfo", {})

        # --- SAFE FIELD EXTRACTION ---
        raw_title = volume_info.get("title", title).strip()
        raw_author = ", ".join(volume_info.get("authors", [author])).strip()

        raw_categories = volume_info.get("categories", [])
        primary_category = raw_categories[0] if raw_categories else ""
        category_str = " ".join(raw_categories).lower()

        pub_year = volume_info.get("publishedDate", "")

        # --- GENRE LOGIC ---
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

        # --- AI SUBGENRE ---
        ai_subgenre = classify_subgenre_with_ai(raw_title, raw_author, genre)

        return {
            "title": smart_title(raw_title),
            "author": smart_title(raw_author),
            "pages": volume_info.get("pageCount", 0),
            "genre": genre,
            "subgenre": ai_subgenre,
            "description": volume_info.get("description", ""),
            "pub_year": pub_year,
            "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail"),
        }

    except Exception as e:
        st.error(f"Connection/Error: {e}")
        print("EXCEPTION:", e)
        return None


def smart_title(text):
    if not text:
        return ""

    minor_words = {
        'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor',
        'on', 'at', 'to', 'from', 'by', 'of', 'in', 'with'
    }

    words = text.lower().split()
    if not words:
        return ""

    result = [words[0].capitalize()] + [
        w if w in minor_words else w.capitalize()
        for w in words[1:]
    ]

    return " ".join(result)


def classify_subgenre_with_ai(title, author, genre):
    from background.options import fiction_subgenres, nonfiction_subgenres
    import json

    valid_options = fiction_subgenres() if genre == "Fiction" else nonfiction_subgenres()
    options_string = ", ".join(valid_options)

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

        res_json = json.loads(response.text)
        ai_choice = res_json.get("subgenre")

        print(f"DEBUG: AI picked '{ai_choice}' for {title}")

        if ai_choice in valid_options:
            return ai_choice

        # Case-insensitive fallback
        for option in valid_options:
            if ai_choice and ai_choice.lower() == option.lower():
                return option

        return None

    except Exception as e:
        st.error(f"AI Error: {e}")
        print("AI EXCEPTION:", e)
        return None