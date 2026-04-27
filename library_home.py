import streamlit as st
from library_components.library import table as library
from library_components.tbr import tbr_tab
from library_components.currently_reading import currently
from background.load_user_library import load_user_library

def library_layout(supabase):

    df = load_user_library()

    tab1, tab2, tab3= st.tabs(["Library","Currently Reading", "TBR"])


    with tab1:
        library(supabase,df)
    with tab2:
        currently(supabase,df)
    with tab3:
        tbr_tab(supabase,df)


