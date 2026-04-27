import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import numpy as np

def genre_bar(filtered_df):
    st.subheader("By Genre")
    chart_data = filtered_df.copy()
    chart_data['subgenre'] = chart_data['subgenre'].fillna("Other/Misc")
    
    counts = chart_data.groupby(['genre', 'subgenre']).size().reset_index(name='Books')

    fig = px.bar(
        counts, 
        x="Books", 
        y="genre", 
        color="subgenre",
        orientation='h',
        text_auto=True,  
    )

    # 4. Styling the "Ugly" parts out
    fig.update_layout(
        barmode='stack',
        xaxis_title="Number of Books Read",
        yaxis_title="",
        showlegend=True,
        bargap=0.1, 
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

def genre_pie(filtered_df):
    type_counts = filtered_df['genre'].value_counts().reset_index()
    type_counts.columns = ['Genre', 'Count']

    fig_pie = px.pie(
        type_counts, 
        values='Count', 
        names='Genre',
        hole=0.4, 
    )

    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        height=350
    )

    st.plotly_chart(fig_pie, use_container_width=True)
