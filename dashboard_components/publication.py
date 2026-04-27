import plotly.express as px
import streamlit as st
from datetime import date 

def publication_dates(filtered_df):
    st.subheader("⏳ The Chronology of your Shelves")
    

    # Create Era Buckets
    def get_era(year):
        # Handle NaNs, Nones, and zeros all at once
        try:
            year = int(year)
        except (ValueError, TypeError):
            return "Unknown"

        if year <= 0: return "Unknown"
        
        # Categories
        if year >= 2020: return "Modern (2020s)"
        if year >= 2000: return "Contemporary (2000-2019)"
        if year >= 1950: return "Mid-Century (1950-1999)"
        if year >= 1900: return "Early 20th Cent."
        if year >= 1837: return "Victorian (1837-1901)"
        
        # This only triggers if a valid year is actually < 1837
        return "Pre-Victorian / Historical"

    filtered_df['era'] = filtered_df['pub_year'].apply(get_era)
    era_counts = filtered_df['era'].value_counts().reset_index()
    era_counts.columns = ['Era', 'Count']

    # 1. Era Distribution Pie/Donut Chart
    fig_era = px.pie(
        era_counts, 
        values='Count', 
        names='Era',
        hole=0.5,
        color_discrete_sequence=["#386641", "#6A994E", "#A7C957", "#E9EDC9", "#F2E8CF"],
        title="Library by Era"
    )
    
    fig_era.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#1B261E",
        font_family="serif"
    )

    # 2. Year-by-Year Histogram
    fig_hist = px.histogram(
        filtered_df, 
        x="pub_year",
        nbins=40,
        title="Publication Timeline",
        labels={'pub_year': 'Year Published', 'count': 'Books'},
        color_discrete_sequence=["#6A994E"]
    )

    fig_hist.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title_font_family="serif"),
        yaxis=dict(showgrid=True, gridcolor="#E9EDC9"),
        font_color="#1B261E"
    )

    # Display in two columns
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_era, use_container_width=True)
    with col2:
        st.plotly_chart(fig_hist, use_container_width=True)

def book_age(filtered_df):
    avg_pub_year = int(filtered_df['pub_year'].mean())
    current_year = date.today().year

    st.metric(
        label="Average Book Age", 
        value=f"{current_year - avg_pub_year} years old",
        delta=f"Avg. Year: {avg_pub_year}",
        delta_color="normal"
    )

def pub_rating_correlation(filtered_df):
    # Filter out 0/NaN so they don't appear at the start of the timeline
    clean_df = filtered_df[filtered_df['pub_year'] > 0]
    
    fig_corr = px.scatter(
        clean_df, 
        x="pub_year", 
        y="rating", 
        trendline="ols", 
        hover_name="title", # See which book is which!
        color="rating",
        color_continuous_scale=["#E9EDC9", "#386641"],
        title="Rating vs. Publication Year"
    )
    
    # Add a Range Slider so you can zoom in on the modern cluster
    fig_corr.update_layout(
        xaxis=dict(
            rangeslider=dict(visible=True),
            type="linear"
        )
    )
    st.plotly_chart(fig_corr, use_container_width=True)