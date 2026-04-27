import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 
import numpy as np

def author_cards(filtered_df):
    st.subheader("Most Read Authors")


    author_stats = filtered_df.groupby('author').agg(
        total_books=('title', 'count'),
        avg_rating=('rating', 'mean'),
        best_book=('title', lambda x: filtered_df.loc[x.index].sort_values('rating', ascending=False).iloc[0]['title'])
    ).sort_values(by='total_books', ascending=False).head(3) 

    cols = st.columns(3)
    
    for i, (author, row) in enumerate(author_stats.iterrows()):
        with cols[i]:
            st.markdown(f"### {author}")
            st.metric("Books Read", int(row['total_books']))
            st.metric("Avg Rating", f"{row['avg_rating']:.1f} ⭐")
            
            st.info(f"**Top Pick:**\n\n_{row['best_book']}_")
            st.divider()

    st.write("#### Author Consistency: Quantity vs. Quality")
    author_all = filtered_df.groupby('author').agg({'title':'count', 'rating':'mean'}).reset_index()
    author_all.columns = ['Author', 'Books Read', 'Avg Rating']



def author_quadrant_chart(filtered_df):
    st.subheader("Author Affinity Map")

    if filtered_df.empty:
        st.info("No data available to map authors.")
        return

    author_stats = filtered_df.groupby('author').agg(
        books_read=('title', 'count'),
        avg_rating=('rating', 'mean')
    ).reset_index()


    author_stats['plot_x'] = author_stats['books_read'] + np.random.uniform(-0.15, 0.15, len(author_stats))
    author_stats['plot_y'] = author_stats['avg_rating'] + np.random.uniform(-0.1, 0.1, len(author_stats))


    y_center = 3.0
    x_center = author_stats['books_read'].mean()
    
    fig = px.scatter(
        author_stats,
        x="plot_x",
        y="plot_y",
        hover_name="author",
        hover_data={
            "plot_x": False, 
            "plot_y": False, 
            "books_read": True, 
            "avg_rating": ":.2f"
        },
        size="books_read",
        color="avg_rating",
        color_continuous_scale="RdYlGn", 
        range_x=[0, author_stats['books_read'].max() + 1],
        range_y=[0.5, 5.5]
    )


    fig.add_vline(x=x_center, line_dash="dash", line_color="rgba(100,100,100,0.5)", line_width=2)
    fig.add_hline(y=y_center, line_dash="dash", line_color="rgba(100,100,100,0.5)", line_width=2)

    fig.add_annotation(x=0.95, y=0.95, text="<b>Reliable Favorites</b>", showarrow=False, xref="paper", yref="paper", font=dict(color="green", size=12))
    fig.add_annotation(x=0.05, y=0.95, text="<b>Hidden Gems</b>", showarrow=False, xref="paper", yref="paper", font=dict(color="blue", size=12))
    fig.add_annotation(x=0.05, y=0.05, text="<b>Never Again</b>", showarrow=False, xref="paper", yref="paper", font=dict(color="red", size=12))
    fig.add_annotation(x=0.95, y=0.05, text="<b>Guilty Pleasures</b>", showarrow=False, xref="paper", yref="paper", font=dict(color="orange", size=12))

    fig.update_layout(
        plot_bgcolor='white',
        xaxis=dict(title="Books Read", showgrid=False, zeroline=False),
        yaxis=dict(title="Average Rating", showgrid=False, zeroline=False),
        margin=dict(l=20, r=20, t=20, b=20),
        height=600,
        coloraxis_showscale=False,
    )

    st.plotly_chart(fig, use_container_width=True)
    
    st.caption(f"Showing {len(author_stats)} unique authors. Center crosshair based on library average ({x_center:.1f} books, 3.0 rating).")

import plotly.express as px
import streamlit as st

def author_diversity_chart(filtered_df):
    if filtered_df.empty or 'author_gender' not in filtered_df.columns:
        st.warning("No gender data available for authors.")
        return

    display_df = filtered_df.copy()
    gender_map = {'m': 'Male', 'f': 'Female', 'other/unknown': 'Other/Unknown'}
    display_df['author_gender'] = display_df['author_gender'].map(gender_map)

    fig_gender = px.pie(
        display_df, 
        names='author_gender', 
        title="Author Gender Distribution",
        hole=0.5,
        color_discrete_map={'Male': '#1f77b4', 'Female': '#e377c2', 'Other/Unknown': '#7f7f7f'}
    )
    fig_gender.update_traces(textinfo='percent+label')

    st.plotly_chart(fig_gender, use_container_width=True)
