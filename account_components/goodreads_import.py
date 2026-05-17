import streamlit as st
from background.process_goodreads_csv import process_goodreads_csv

def render_import_section():
    st.divider()
    with st.expander("📥 Import Library from Goodreads"):
        st.info("Upload your Goodreads export CSV. We'll skip books you've already added." \
        "Warning! This may take awhile, so go ahead and open a new book while you wait")
        
        file = st.file_uploader("Upload CSV", type="csv", label_visibility="collapsed")
        
        if file and st.button("Start Sync", use_container_width=True):
            progress_text = "Starting import... Keep this tab open!"
            my_bar = st.progress(0, text=progress_text)
            
            with st.spinner("Enriching metadata..."):
                result = process_goodreads_csv(file, progress_bar=my_bar)
            
                my_bar.empty() 
                  
                if result["success"]:
                    counts = result["counts"]
                    st.success(f"Done! Added {counts['new']} new books.")
                    if counts['skipped'] > 0:
                        st.caption(f"Skipped {counts['skipped']} books already in your library.")
                    
                    if counts['errors']:
                        with st.expander("View individual errors"):
                            for err in counts['errors']:
                                st.write(f"❌ {err}")
                    
                    st.cache_data.clear()
                    st.balloons()
                else:
                    st.error(result["message"])