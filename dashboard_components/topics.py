import streamlit as st
from background.description_ai import get_ai_library_profile, get_library_dna

import plotly.graph_objects as go
import streamlit as st

def render_library_soul(profile_json):
    st.markdown(f"### Your Reader Summary: **{profile_json['persona']}**")
    st.write(f"*{profile_json['era_summary']}*")
    
    st.divider()
    
    col_vibe, col_mood = st.columns(2)
    
    with col_vibe:
        st.write("#### Common Themes in your Reads")
        for theme in profile_json['themes']:
            st.info(theme)

    with col_mood:
        # Use our Radar Chart function here
        render_mood_radar(profile_json['moods'])

def render_mood_radar(mood_scores):
    """
    Renders a Plotly Radar Chart based on a dictionary of mood scores.
    Expected input: {"Cozy": 85, "Dark": 20, "Tense": 40, "Cerebral": 90}
    """
    if not mood_scores:
        st.warning("No mood data to display.")
        return

    # 1. Prepare data categories and values
    categories = list(mood_scores.keys())
    values = list(mood_scores.values())

    # 2. Close the radar loop (repeat the first category/value at the end)
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    # 3. Create the Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name='Library Mood',
        line=dict(color='#008080', width=2), # Your Teal color
        fillcolor='rgba(0, 128, 128, 0.3)', # Transparent Teal
        marker=dict(size=8)
    ))

    # 4. Final Layout Styling
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100], # AI scores are 0-100
                tickfont=dict(size=10),
                gridcolor="#eeeeee"
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#333"),
                rotation=90, # Starts the first label at the top
                direction="clockwise"
            ),
            bgcolor="rgba(0,0,0,0)" # Transparent background
        ),
        showlegend=False,
        margin=dict(t=40, b=40, l=60, r=60),
        height=350
    )

    st.plotly_chart(fig, use_container_width=True)
    
            
def render_ai_insights(filtered_df):
    st.subheader("Library Themes and Vibes")

    # 1. Create a unique 'fingerprint' of the current data
    # This ensures that if the data changes, we know we need a new analysis
    current_data_hash = len(filtered_df) 

    # 2. Check if we already have a saved analysis for this data
    if "ai_profile" not in st.session_state or st.session_state.get("last_data_hash") != current_data_hash:
        
        # Display a button so the AI call isn't "automatic" (saves credits)
        if st.button("Generate/Update AI Analysis"):
            with st.spinner("Gemini is reading your library's DNA..."):
                # Run the distillation and AI call
                dna = get_library_dna(filtered_df)
                profile = get_ai_library_profile(dna)
                
                if profile:
                    # Save to session state
                    st.session_state.ai_profile = profile
                    st.session_state.last_data_hash = current_data_hash
                    st.rerun() # Refresh to show the results
        else:
            st.info("Click the button above to generate a deep AI analysis of these books.")
            return

    # 3. If we reach here, we have a profile in state!
    if "ai_profile" in st.session_state:
        profile = st.session_state.ai_profile
        
        # Display the results using the UI functions we built
        render_library_soul(profile)