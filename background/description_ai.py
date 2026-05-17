import google.generativeai as genai
import streamlit as st
import json

def get_library_dna(filtered_df):
    """Converts a DataFrame into a condensed string for AI analysis."""
    dna_segments = []
    
    # We only need the top 50-70 books to get a statistically perfect 'vibe'
    sample_df = filtered_df.head(75) 

    for _, row in sample_df.iterrows():
        title = row.get('title', 'Unknown')
        author = row.get('author', 'Unknown')
        # Clean the description: remove newlines and truncate
        gist = str(row.get('description', ''))[:120].replace('\n', ' ').strip()
        
        dna_segments.append(f"• {title} ({author}): {gist}...")

    return "\n".join(dna_segments)


def get_ai_library_profile(library_dna):
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    model = genai.GenerativeModel(
        model_name='gemini-3-flash-preview',
        generation_config={"response_mime_type": "application/json"}
    )
    
    
    prompt = f"""
    You are a world-class literary analyst. Analyze this 'Library DNA':
    
    {library_dna}
    
    1. Identify the 'Thematic Gravity': 5 deep themes that connect these books.
    2. Score these 4 Moods (0-100): Cozy, Dark, Tense, Lighthearted.
    3. Determine the 'Reader Persona': A 3-word title (e.g., 'The Melancholic Voyager').
    4. Current 'Reading Era': A 1-sentence summary of the user's current intellectual phase.

    Return ONLY JSON:
    {{
      "themes": ["theme1", "theme2", "theme3", "theme4", "theme5"],
      "moods": {{"Cozy": 0, "Dark": 0, "Tense": 0, "Lighthearted": 0}},
      "persona": "3-word-title",
      "era_summary": "One sentence summary."
    }}
    """    
    try:
        ai_response = model.generate_content(prompt)
        
        # Check if the response actually has text
        if ai_response.text:
            return json.loads(ai_response.text)
        else:
            st.error("AI returned an empty response.")
            return None
            
    except Exception as e:
        st.error(f"AI Analysis Error: {e}")
        return None