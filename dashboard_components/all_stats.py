import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import numpy as np

def metrics(filtered_df):
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Books", len(filtered_df))
    col2.metric("Pages Read", f"{int(filtered_df['pages'].sum()):,}")
    col3.metric("Number of Authors", filtered_df['author'].nunique())
    col4.metric("Avg Rating", round(filtered_df['rating'].mean(), 1))

    st.divider()

def line_chart(filtered_df):
    st.subheader("Timeline")
    if not filtered_df['read_date'].isnull().all():
        chart_data = filtered_df.set_index('read_date').resample('ME').size().reset_index()
        chart_data.columns = ['Date', 'Books']
    
        chart_data = chart_data.sort_values('Date')
        
        chart_data['Month Year'] = chart_data['Date'].dt.strftime('%b %Y')
        
        chart_data['Month Year'] = pd.Categorical(
            chart_data['Month Year'], 
            categories=chart_data['Month Year'].unique(), 
            ordered=True
        )
        st.line_chart(chart_data, x="Month Year", x_label="Month", y="Books", y_label="Books Read")
