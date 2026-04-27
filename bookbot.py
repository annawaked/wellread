import streamlit as st
from streamlit import session_state as state
from background.recommendations import get_recommendations
from background.supabase_setup import get_current_user_id

def bookbot():
    st.title("Book Bot")
    st.write("The WellRead Book Bot has analyzed your library...")
    USE_REAL_AI = True 


    gen, refresh = st.columns ([4,1])
    with gen:
        if st.button("Generate Recommendations"):
            with st.spinner("Analyzing your library..."):
                if not USE_REAL_AI:
                    state.ai_data = {
                        "taste_summary": "This is a mock summary for testing.",
                        "books": [
                            {"title": "Test Book ", "author": "Author A", "reason": "Test reason", "vibe": "Spooky"},
                            {"title": "Test Book ex", "author": "Author B", "reason": "Test reason", "vibe": "Cozy"}
                        ]
                    }
                else:
                    try:
                        user_id = get_current_user_id()
                        state.ai_data = get_recommendations(user_id)

                    except Exception as e:
                        st.error(f"AI Error: {e}")
    with refresh:
        if st.button(label= "",
                    icon= ':material/autorenew:',
                    help="Clear cache and refresh"):
            st.cache_data.clear()
            st.rerun()   

    if "ai_data" in state:
        res = state.ai_data
        st.info(res['taste_summary'])

        st.markdown("### Suggested Reads")
        selected_books = []
        
        for i, book in enumerate(res['books']):
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{book['title']}**")
                    st.caption(f"by {book['author']} | Vibe: {book['vibe']}")
                    st.write(book['reason'])
                with col2:
                    # Individual "Add to Queue" check
                    if st.checkbox("Select", key=f"book_{i}"):
                        selected_books.append(book)

        if selected_books:
            if st.button(f"Add {len(selected_books)} to your Want to Read Library",):
                state.book_queue = selected_books
                
                first_book = state.book_queue.pop(0)
                state.title = first_book['title']
                state.author = first_book['author']
                state.status = "TBR"
                state.current_page = "Add"
                st.rerun()