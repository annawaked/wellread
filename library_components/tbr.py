import streamlit as st 
from background.supabase_setup import get_current_user_id
import streamlit as st
import pandas as pd
from datetime import date
from background.get_data import load_data
from streamlit import session_state as state
import streamlit as st
import pandas as pd
from datetime import date
from background.get_data import load_data
import streamlit as st
from datetime import date

@st.dialog("Manage Book")
def manage_tbr_dialog(supabase, book_entry):
    st.write(f"### {book_entry['title']}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Start Reading","✅ Mark as Read", "❌ DNF", "🗑️ Remove"])
    with tab1: 
        st.write("Ready to start?")
        if st.button("Start Reading Now!", type="primary", use_container_width=True):
            supabase.table("user_books").update({
                "status": "Currently Reading",
                "date_started": date.today().isoformat()
            }).eq("id", book_entry['id']).execute()
            
            st.cache_data.clear()
            st.success("Moved to Currently Reading!")
            st.rerun()
            
    with tab2:
        st.info("This will take you to the Add Book page to log your final review and rating.")
       
        if st.button("Go to Review Form", use_container_width=True):
            state.title = book_entry['title']
            state.author = book_entry['author']
            state.status = "read" 
            state.from_tbr_id = book_entry['id']
            
            state.current_page = "Add"            
            st.rerun()

    with tab3:
        st.write("Moving this to DNF (Did Not Finish)?")
        dnf_reason = st.text_area("Why are you stopping?", placeholder="Not for me / Boring / Poorly written...")
        if st.button("Move to DNF", type="primary", use_container_width=True):
            supabase.table("user_books").update({
                "status": "DNF",
                "review_text": f"DNF Reason: {dnf_reason}"
            }).eq("id", book_entry['id']).execute()
            st.cache_data.clear()

            st.rerun()

    with tab4:
        st.warning("This will permanently remove the book from your TBR list.")
        if st.button("Confirm Delete", type="primary", use_container_width=True):
            supabase.table("user_books").delete().eq("id", book_entry['id']).execute()
            st.cache_data.clear()
            st.rerun()

def tbr_tab(supabase, df):
    st.subheader("My TBR List")
    
    df.columns = pd.io.common.dedup_names(df.columns, is_unique=False)
    
    df = df[df['status'].str.upper() == 'TBR'].copy().reset_index(drop=True)
    if df.empty:
        st.info("Your TBR list is empty.")
        return

    df['read_date_dt'] = pd.to_datetime(df['read_date']).dt.date
    today = date.today()
    # df['Days on Shelf'] = df['read_date_dt'].apply(lambda x: (today - x).days)
    
    cols_to_show = ['id', 'thumbnail_url', 'title', 'author', 'genre', 'read_date']    
    
    final_display_df = df.loc[:, ~df.columns.duplicated()][cols_to_show]
    
    event = st.dataframe(
        final_display_df,
        use_container_width=True,
        column_config={
            "id": None,
            "thumbnail_url": st.column_config.ImageColumn("Cover"),
            "read_date": st.column_config.DateColumn("Added On"),
            # "Days on Shelf": st.column_config.NumberColumn("Days on Shelf", format="%d days")
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        height= 1200,
        row_height= 200,
    )

    if event.selection.rows:
        selected_index = event.selection.rows[0]
        selected_row = df.iloc[selected_index]
        
        manage_tbr_dialog(supabase, selected_row.to_dict())

import streamlit as st
import pandas as pd
from datetime import date
from streamlit import session_state as state

@st.dialog("Manage Book")
def manage_tbr_dialog(supabase, book_entry):
    st.write(f"### {book_entry['title']}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Start Reading","✅ Mark as Read", "❌ DNF", "🗑️ Remove"])
    with tab1: 
        st.write("Ready to start?")
        if st.button("Start Reading Now!", type="primary", use_container_width=True):
            # book_entry['id'] here must be the user_books table ID
            supabase.table("user_books").update({
                "status": "Currently Reading",
                "date_started": date.today().isoformat()
            }).eq("id", book_entry['id']).execute()
            
            st.cache_data.clear()
            st.success("Moved to Currently Reading!")
            st.rerun()
            
    with tab2:
        st.info("This will take you to the Add Book page to log your final review and rating.")
        if st.button("Go to Review Form", use_container_width=True):
            state.title = book_entry['title']
            state.author = book_entry['author']
            state.status = "read" 
            state.from_tbr_id = book_entry['id']
            state.current_page = "Add"            
            st.rerun()

    with tab3:
        st.write("Moving this to DNF (Did Not Finish)?")
        dnf_reason = st.text_area("Why are you stopping?", placeholder="Not for me / Boring / Poorly written...")
        if st.button("Move to DNF", type="primary", use_container_width=True):
            supabase.table("user_books").update({
                "status": "DNF",
                "review_text": f"DNF Reason: {dnf_reason}"
            }).eq("id", book_entry['id']).execute()
            st.cache_data.clear()
            st.rerun()

    with tab4:
        st.warning("This will permanently remove the book from your TBR list.")
        if st.button("Confirm Delete", type="primary", use_container_width=True):
            supabase.table("user_books").delete().eq("id", book_entry['id']).execute()
            st.cache_data.clear()
            st.rerun()

def tbr_tab(supabase, df):
    st.subheader("My TBR List")
    
    # --- FIX: REMOVE DUPLICATE COLUMNS ---
    # This keeps the first 'id' (from user_books) and drops the others
    df = df.loc[:, ~df.columns.duplicated()].copy()
    
    df = df[df['status'].str.upper() == 'TBR'].copy().reset_index(drop=True)
    if df.empty:
        st.info("Your TBR list is empty.")
        return

    # Convert dates safely
    df['read_date_dt'] = pd.to_datetime(df['read_date']).dt.date
    
    cols = ['id', 'thumbnail_url', 'title', 'author', 'genre', 'read_date']
    
    # We slice only the columns we need for the table
    display_df = df[cols]
    
    event = st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "id": None, # Hides the ID column from the user
            "thumbnail_url": st.column_config.ImageColumn("Cover"),
            "read_date": st.column_config.DateColumn("Added On"),
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        height=1200,
        row_height=200,
    )

    if event.selection.rows:
        selected_index = event.selection.rows[0]
        selected_row = df.iloc[selected_index]
        manage_tbr_dialog(supabase, selected_row.to_dict())