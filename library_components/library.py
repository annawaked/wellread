from background.get_data import load_data
import streamlit as st 
import pandas as pd 
from streamlit import session_state as state 
from background.fetch_book_metadata import fetch_book_metadata

def table(supabase, df):
    df = df.loc[:, ~df.columns.duplicated()].copy()

    df['date_started'] = pd.to_datetime(df['date_started'], errors='coerce')
    df['read_date'] = pd.to_datetime(df['read_date'], errors='coerce')

    df = df[df['status'].isin(['read', 'DNF'])]
    title_col, edit_col = st.columns([4, 1])
    with title_col:
        st.subheader("My Library")

    with edit_col:
            # Toggle for Bulk Edit Mode
            if "edit_mode" not in state:
                state.edit_mode = False
            
            if st.button("Bulk Edit" if not state.edit_mode else "Cancel", use_container_width=True):
                state.edit_mode = not state.edit_mode
                st.rerun()

            if state.edit_mode: 
               if st.button("Sync Publication Years"):
                    to_fix = df[(df['pub_year'].isna()) | (df['pub_year'] == 0)].copy()
                    
                    if not to_fix.empty:
                        progress_bar = st.progress(0)
                        failed_books = []  # List to track the ones that didn't work
                        success_count = 0
                        
                        for i, (idx, row) in enumerate(to_fix.iterrows()):
                            t = str(row['title']).strip()
                            a = str(row['author']).strip()
                            
                            meta = fetch_book_metadata(t, a)
                            
                            # Use the 'pub_year' key returned by your fetch function
                            if meta and meta.get('pub_year'):
                                try:
                                    raw_date = str(meta['pub_year'])
                                    clean_year = int(raw_date[:4])
                                    
                                    supabase.table("books").update({
                                        "pub_year": clean_year
                                    }).eq("id", row['id']).execute()
                                    
                                    success_count += 1
                                except:
                                    failed_books.append(f"{t} (Date formatting error)")
                            else:
                                failed_books.append(f"{t} by {a} (Not found on Google)")
                            
                            progress_bar.progress((i + 1) / len(to_fix))
                            
                        # --- Final Report ---
                        st.success(f"Done! Updated {success_count} books.")
                        
                        if failed_books:
                            with st.expander("⚠️ View books that could not be updated"):
                                for book in failed_books:
                                    st.write(f"- {book}")
                        
                        st.cache_data.clear()
                        # st.rerun() # Refresh to show new data
                    else:
                        st.info("No books missing publication years.")



    df = df.sort_values(by= 'read_date', ascending= False)


    if state.edit_mode:
        st.info("Directly edit dates and pages. Changes are highlighted until saved.")
        
        # ADD 'pub_year' TO THIS LIST
        edit_cols = ['id', 'title', 'author', 'date_started', 'read_date', 'pages', 'pub_year']
        
        # Display the Editor
        edited_df = st.data_editor(
            df[edit_cols],
            key="bulk_editor",
            column_config={
                "id": None, 
                "title": st.column_config.TextColumn("Title", disabled=True),
                "author": st.column_config.TextColumn("Author", disabled=True),
                "date_started": st.column_config.DateColumn("Date Started"),
                "read_date": st.column_config.DateColumn("Date Finished"),
                "pages": st.column_config.NumberColumn("Pages", min_value=0),
                "pub_year": st.column_config.NumberColumn("Year", format="%d") 
            },
            hide_index=True,
            use_container_width=True
        )

        if st.button("💾 Save All Changes", type="primary"):
            original_compare = df[edit_cols].reset_index(drop=True)
            edited_compare = edited_df.reset_index(drop=True)
            
            diff = (original_compare != edited_compare).any(axis=1)
            changes = edited_compare[diff]

            if not changes.empty:
                    with st.spinner(f"Syncing updates..."):
                        for _, row in changes.iterrows():
                            supabase.table("user_books").update({
                                "date_started": str(row['date_started']) if row['date_started'] else None,
                                "read_date": str(row['read_date']) if row['read_date'] else None,
                                "pages": int(row['pages']) if row['pages'] else 0
                            }).eq("id", row['id']).execute()

                            target_book_id = row.get('book_id') or row.get('id')
                            supabase.table("books").update({
                                "pub_year": int(row['pub_year']) if row['pub_year'] else 0
                            }).eq("id", target_book_id).execute()


    else:


        df['rating_display'] = df.apply(
            lambda x: "DNF" if x['status'] == 'DNF' else f"{int(x['rating'])} ⭐", 
            axis=1
    )

        cols = ['thumbnail_url', 'title', 'author', 'genre','subgenre', 'rating_display','date_started', 'read_date', 'review_text']
        

        search, submit, clear = st.columns([3,1,1])
        with search: 
            state.search_query = st.text_input(label= "Search by title, author or genre").lower()

        with submit:
            if st.button("Search"):
                df = df[
                    df['title'].str.lower().str.contains(state.search_query) |
                    df['author'].str.lower().str.contains(state.search_query) |
                    df['subgenre'].str.lower().str.contains(state.search_query)
                ]
                state.search_query = ""
        
        with clear:
            if st.button("Clear"):
                state.search_query = ""
        

        df = df.sort_values(by='read_date', ascending=False)


        def column_config(): 
            return {
                    "id": None,
                    "thumbnail_url": st.column_config.ImageColumn(
                        "Cover", 
                        width= "medium",
                        help="Book Cover Thumbnail"
                    ),
                    "rating_display": st.column_config.TextColumn(
                        "Rating"
                    ),
                    "date_started": st.column_config.DateColumn(
                        "Started", format="YYYY-MM-DD"
                    ),
                    "read_date": st.column_config.DateColumn(
                        "Finished", format="YYYY-MM-DD")
                }

        event = st.dataframe(
            df[cols],
            use_container_width=True,
            column_config=column_config(),
            hide_index=True,
            on_select="rerun", 
            selection_mode="single-row",
            height=1200,
            row_height=200,
        )
        if event.selection.rows:
            selected_index = event.selection.rows[0]
            selected_row = df.iloc[selected_index]
            
            # Open the dialog with the full row data
            manage_book_dialog(supabase, selected_row.to_dict())

    @st.dialog("Manage Book")
    def manage_book_dialog(supabase, book_entry):
        st.write(f"### {book_entry['title']}")
        
        if book_entry.get('status') == 'read':
            st.write("What would you like to do with this entry?")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Edit Entry", use_container_width=True):
                    state.from_tbr_id = book_entry['id']
                    state.title = book_entry['title']
                    state.author = book_entry['author']
                    state.pages_val = book_entry.get('pages', 0)
                    state.genre = book_entry.get('genre')
                    state.subgenre = book_entry.get('subgenre')
                    state.rating = book_entry.get('rating', 0)
                    state.review = book_entry.get('review_text', "")
                    state.date_started = book_entry.get('date_started')
                    state.date_read = book_entry.get('read_date')
                    state.thumbnail = book_entry.get('thumbnail_url')
                    state.source = book_entry.get('source')
                    state.reread = book_entry.get('is_reread', False)
                    state.pub_year = book_entry.get('pub_year', 0)

                    state.current_page = "Add"
                    st.rerun()
            
            with c2:
                if st.button("🗑️ Delete", type="primary", use_container_width=True):
                    supabase.table("user_books").delete().eq("id", book_entry['id']).execute()
                    st.cache_data.clear()
                    st.rerun()
    