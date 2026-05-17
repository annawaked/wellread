import streamlit as st
from streamlit import session_state as state
from background.supabase_setup import supabase_setup, get_current_user_id
from add import add_book, reset_add_book_state
from dashboard_home import dashboard_layout
from account import account, render_auth_forms
from bookbot import bookbot
from library_home import library_layout




supabase = supabase_setup()
user = get_current_user_id() 


if not user:
    account() 
    st.stop()

else:
    
    if "current_page" not in state:
            state.current_page = "Dashboard"

    with st.sidebar:
        st.image("WellRead.png", width=200)
        st.divider()
        
        if st.button(label="Dashboard",
                    icon= ':material/bar_chart:',
                    use_container_width=True):
            reset_add_book_state()
            state.current_page = "Dashboard"
            st.rerun()
            
        if st.button(label= 'Add New Book',
                    icon= ':material/add:',
                    use_container_width=True):
            reset_add_book_state()
            state.current_page = "Add"
            st.rerun()
            
            
        if st.button(label= 'Book Bot',
                    icon= ':material/smart_toy:',
                    use_container_width=True):
            reset_add_book_state()
            state.current_page = "Book_Bot"
            st.rerun()


        if st.button(label="My Library", 
                    icon= ':material/book_2:',
                    use_container_width=True):
            reset_add_book_state()
            state.current_page = "Library"
            st.rerun()

            
        for _ in range(10): 
                st.write("") 

        st.divider()
        if st.button(label="Account", 
                    icon= ':material/account_circle:',
                    use_container_width=True):
            reset_add_book_state()
            state.current_page = "Account"
            st.rerun()


    if state.current_page == "Dashboard":
        dashboard_layout()

    elif state.current_page == "Add":
        add_book()

    elif state.current_page == "Book_Bot":
        bookbot()

    elif state.current_page == "Account":
        account()

    elif state.current_page == "Library":
        library_layout(supabase)