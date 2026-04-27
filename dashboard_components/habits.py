import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import numpy as np

def source_metrics(filtered_df):
    st.subheader("Books by Source")
    if filtered_df.empty or 'source' not in filtered_df.columns:
        st.warning("No source data available.")
        return

    source_counts = filtered_df['source'].value_counts().reset_index()
    source_counts.columns = ['Source', 'Count']

    fig = px.pie(
        source_counts, 
        values='Count', 
        names='Source', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))

    st.plotly_chart(fig, use_container_width=True)

def get_weight_class(pages):
    if pages < 150:
        return "Short (less than 150)"
    elif 150 <= pages < 450:
        return "Standard (150-450)"
    elif 450 <= pages < 700:
        return "Big (450-700)"
    else:
        return "Tome (700+)"
    


def book_size_analysis(filtered_df):
    if filtered_df.empty or 'pages' not in filtered_df.columns:
        st.warning("No page data available.")
        return

    # Apply the weight classes
    filtered_df['size_category'] = filtered_df['pages'].apply(get_weight_class)
    
    # Sort order so the chart flows from Short to Tome
    size_order = ["Short (less than 150)", "Standard (150-450)", "Big (450-700)", "Tome (700+)"]

    # 1. Distribution Bar Chart
    size_counts = filtered_df['size_category'].value_counts().reindex(size_order).fillna(0).reset_index()
    size_counts.columns = ['Category', 'Count']

    fig = px.bar(
        size_counts, 
        x='Category', 
        y='Count',
        title="",
        
        color='Category',
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    
    fig_hist = px.histogram(
        filtered_df,
        x="pages", 
        nbins=20, 
        title="Frequency of Page Counts",
        labels={'pages': 'Page Count'},
        color_discrete_sequence=['#9467bd']
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.plotly_chart(fig_hist, use_container_width=True)