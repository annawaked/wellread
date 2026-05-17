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
                    failed_books = []
                    success_count = 0

                    for i, (idx, row) in enumerate(to_fix.iterrows()):
                        t = str(row['title']).strip()
                        a = str(row['author']).strip()

                        meta = fetch_book_metadata(t, a)

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

                    st.success(f"Done! Updated {success_count} books.")

                    if failed_books:
                        with st.expander("⚠️ View books that could not be updated"):
                            for book in failed_books:
                                st.write(f"- {book}")

                    st.cache_data.clear()

                else:
                    st.info("No books missing publication years.")

    df = df.sort_values(by='read_date', ascending=False)

    # ---------------- RIGHT PANEL STATE ----------------
    if "selected_book" not in state:
        state.selected_book = None

    # ---------------- LAYOUT ----------------
    left, right = st.columns([3, 1])

    # ---------------- LEFT: TABLE ----------------
    with left:

        if state.edit_mode:
            st.info("Directly edit dates and pages. Changes are highlighted until saved.")

            edit_cols = ['id', 'title', 'author', 'date_started', 'read_date', 'pages', 'pub_year']

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
                lambda x: "DNF" if x['status'] == 'DNF'
                else f"{int(x['rating'])} ⭐",
                axis=1
            )

            cols = [
                'thumbnail_url', 'title', 'author',
                'genre', 'subgenre', 'rating_display',
                'date_started', 'read_date', 'review_text'
            ]

            search, submit, clear = st.columns([3, 1, 1])

            with search:
                state.search_query = st.text_input(
                    label="Search by title, author or genre"
                ).lower()

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
                        width="medium",
                        help="Book Cover Thumbnail"
                    ),
                    "rating_display": st.column_config.TextColumn("Rating"),
                    "date_started": st.column_config.DateColumn("Started", format="YYYY-MM-DD"),
                    "read_date": st.column_config.DateColumn("Finished", format="YYYY-MM-DD")
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
                state.selected_book = df.reset_index(drop=True).iloc[selected_index]
            if not event.selection.rows:
                state.selected_book = None
    # ---------------- RIGHT: DETAIL PANEL ----------------
    with right:
        st.subheader("Book Details")

        if state.selected_book is None:
            st.info("Select a book to view details")
        else:
            book = state.selected_book

            st.image(book.get("thumbnail_url"))
            st.write(f"### {book['title']}")
            st.write(f"**Author:** {book['author']}")
            st.write(f"**Genre:** {book.get('genre', '')}")
            st.write(f"**Subgenre:** {book.get('subgenre', '')}")
            st.write(f"**Pages:** {book.get('pages', '')}")
            st.write(f"**Published:** {book.get('pub_year', '')}")

            st.divider()

            if st.button("✏️ Edit"):
                state.from_tbr_id = book['id']
                state.title = book['title']
                state.author = book['author']
                state.pages_val = book.get('pages', 0)
                state.genre = book.get('genre')
                state.subgenre = book.get('subgenre')
                state.rating = book.get('rating', 0)
                state.review = book.get('review_text', "")
                state.date_started = book.get('date_started')
                state.date_read = book.get('read_date')
                state.thumbnail = book.get('thumbnail_url')
                state.pub_year = book.get('pub_year', 0)

                state.current_page = "Add"
                st.rerun()

            if st.button("🗑️ Delete", type="primary"):
                supabase.table("user_books").delete().eq("id", book['id']).execute()
                st.cache_data.clear()
                state.selected_book = None
                st.rerun()