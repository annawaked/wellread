import streamlit as st 
import pandas as pd 
from dashboard_components.all_stats import metrics, line_chart
from dashboard_components.genre import genre_bar, genre_pie
from dashboard_components.author import author_cards, author_quadrant_chart, author_diversity_chart
from dashboard_components.habits import source_metrics, book_size_analysis
from dashboard_components.topics import render_ai_insights
from dashboard_components.publication import pub_rating_correlation, book_age, publication_dates
from background.get_data import load_data
from background.load_user_library import load_user_library
from datetime import datetime

def dashboard_setup():

    st.set_page_config(page_title="WellRead", layout="wide")

    df = load_user_library()

    # GUARD CLAUSE: If no data, show a message and stop execution
    if df is None or df.empty:
        st.title("WellRead Dashboard")
        st.info("👋 Welcome to WellRead! Your dashboard is empty because you haven't logged any books yet.")
        st.write("Head over to the **Import** page to sync your Goodreads data or add a book manually.")
        if st.button("Go to Import"):
            st.switch_page("account.py") # Ensure this path matches your file structure
        st.stop() # CRITICAL: This prevents the crash below
    # st.set_page_config(page_title="WellRead", layout="wide")

    # df = load_user_library()

    if df is not None and not df.empty:
        df = df.loc[:, ~df.columns.duplicated()].copy()

    df = df[df['status'] == 'read'].copy()
    df['read_date'] = pd.to_datetime(df['read_date'], errors='coerce')

    years = df['read_date'].dt.year.dropna().unique()
    year_options = ["All Time"] + sorted([int(y) for y in years], reverse=True)


    title, picker = st.columns([4,1])
    with title:
        st.title("WellRead Dashboard")
    with picker:
        selected_year = st.selectbox("Select Year", year_options,)

    # Filter dataframe
    if selected_year == "All Time":
        filtered_df = df.copy()
    else:
        filtered_df = df[
            (df['read_date'] >= pd.Timestamp(f"{selected_year}-01-01")) &
            (df['read_date'] <= pd.Timestamp(f"{selected_year}-12-31"))
        ]
    
    return filtered_df

def dashboard_layout():
    filtered_df = dashboard_setup()
    line, bar, author, habits, topics, pub = st.tabs(["Timeline", "Genre", "Authors", "Reading Habits", "Topics", "Book Age"])

    with line:
        metrics(filtered_df)
        line_chart(filtered_df)
    with bar:
        genre_bar(filtered_df)
        genre_pie(filtered_df)
    with author: 
        author_cards(filtered_df)
        author_quadrant_chart(filtered_df)
        author_diversity_chart(filtered_df)
    with habits:
        source_metrics(filtered_df)
        book_size_analysis(filtered_df)
    with topics:
        render_ai_insights(filtered_df)
    with pub:

        book_age(filtered_df)
        publication_dates(filtered_df)
        pub_rating_correlation(filtered_df)