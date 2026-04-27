import streamlit as st
from background.supabase_setup import supabase_setup, get_current_user_id
from background.fetch_book_metadata import fetch_book_metadata
from streamlit import session_state as state
from background.options import sources, fiction_subgenres, nonfiction_subgenres
import time 
supabase = supabase_setup()

def add_book():
    is_from_tbr = "from_tbr_id" in state

    if "pages_val" not in state:
        state.pages_val = 0
    if "genre" not in state:
        state.genre= None
    if "thumbnail" not in state:
        state.thumbnail = None
    if "subgenre" not in state:
        state.subgenre = None
    if "source" not in state:
        state.source = None
    if "reread" not in state:
        state.reread = False
    if "review" not in state:
        state.review = None
    if "rating" not in state:
        state.rating = 0
    if "status" not in state:
        state.status = None
    if "pub_year" not in state:
        state.pub_year = 0
###
    st.subheader("Finished Your Book" if is_from_tbr else "Log a New Bok")

    status_labels = {
        "read": "Read", 
        "Currently Reading": "Currently Reading", 
        "TBR": "Want to Read"
    }

    status_options = list(status_labels.keys())

    if "book_queue" in st.session_state and len(st.session_state.book_queue) > 0:
            st.warning(f"**Queue Active:** {len(st.session_state.book_queue)} books remaining after this one.")
            if st.button("Clear Remaining Queue"):
                st.session_state.book_queue = []
                st.rerun()

    current_status = state.get("status", "read")
    try:
        current_index = status_options.index(current_status)
    except ValueError:
        current_index = 0


    status = st.radio(
        label="Reading Status",
        options= status_options,
        format_func=lambda x: status_labels.get(x),
        index= current_index,
        horizontal=True,
    )

    state.status = status 
    
    col1, col2 = st.columns([3,1])
    with col1:
        state.title = st.text_input("Title", value=state.get("title", ""))
        state.author = st.text_input("Author", value=state.get("author", ""))
        
        if st.button("Look up metadata"):
            if state.title and state.author:
                meta = fetch_book_metadata(state.title, state.author)
                if meta:
                    state.title_val = meta.get('title')
                    state.author_val = meta.get('author')
                    state.pages_val = meta.get('pages', 0)
                    state.genre = meta.get('genre')
                    state.subgenre = meta.get('subgenre')
                    state.pub_year = meta.get('pub_year', 0 )
                    state.thumbnail = meta.get('thumbnail')

                    st.success(f"Metadata loaded")
                else:
                    st.warning("No matching book found.")
            else:
                st.error("Must enter Title and Author")

    with col2:
        if state.thumbnail:
            st.image(state.thumbnail, width= 150)

    with st.container(border= True):
        metadata, thoughts = st.columns(2)
        
        with metadata:
        #pages
            state.pages = st.number_input(
                label="Pages", 
                value=int(state.get("pages_val", 0) or 0)
)
        #genre
            genre_options = ["Fiction", "Non-Fiction"]

            current_genre_index = 0
            if state.get("genre") == "Non-Fiction":
                current_genre_index = 1
          
            state.genre = st.selectbox(
                label="Genre", 
                options=genre_options,
                index=current_genre_index
            )


        #subgenre
            sub_options = fiction_subgenres() if state.genre == "Fiction" else nonfiction_subgenres()
            
            # Find where the AI-detected subgenre sits in that list
            current_sub_val = state.get("subgenre")
            try:
                sub_index = sub_options.index(current_sub_val) if current_sub_val in sub_options else None
            except ValueError:
                sub_index = None

            state.subgenre = st.selectbox(
                label="Subgenre", 
                options=sub_options,
                index=sub_index,
                placeholder="Pick a subgenre"
            )
            
           #start date
            current_start = state.get("date_started")
           
           
            state.date_started = st.date_input(label="Started Reading", 
                                                value=current_start if current_start else None,
                                                disabled=(state.status == "TBR")
                                            )                                  
            
            state.date_read = st.date_input(label= "Finished Reading", 
                                            disabled = (state.status in ("TBR", "Currently Reading")))
            state.reread = st.checkbox(label= "Re-read",
                                       disabled = (state.status == "TBR"))
            state.source = st.selectbox(label= "Source", 
                                        options= sources(),
                                        placeholder= "Choose a source",
                                        disabled = (state.status == "TBR")
                                        )
            state.gender = st.selectbox(label = "Author Gender",
                                        options = ["other/unknown", "m", "f"],
                                        )
       
       
        with thoughts:
            state.review = st.text_area(label= "Review", 
                        placeholder= "Write a review...",
                        disabled= (state.status in ("TBR", "Currently Reading"))
                        )

            stars, toggle = st.columns([3, 1])

            with toggle:
                dnf = st.toggle("DNF", value=False,  disabled = state.status in ("TBR", "Currently Reading"))

            with stars:

                star_index = st.feedback("stars", 
                                         width = 100, 
                                         disabled= (state.status in ("DNF", "TBR", "Currently Reading"))
                                         )
                
                if dnf:
                    state.status = "DNF"
                    state.rating = 0
                    state.progress = st.slider("How far did you get?", 0, 100, 
                                              value=state.get("progress", 50), 
                                              format="%d%%")
                    

                    st.caption(f"Stopped at {state.progress}%")
                    
                elif star_index is not None :
                    state.rating = star_index + 1
                    state.status = "read"



        if st.button("Save to WellRead", use_container_width=True):
            try:
                 
                current_uid = get_current_user_id()
                
                if not current_uid:
                    st.error("You must be logged in to save books!")
                    st.stop()


                raw_pub_year = state.get("pub_year", 0)

                if isinstance(raw_pub_year, str) and "-" in raw_pub_year:
                    clean_pub_year = int(raw_pub_year.split("-")[0])
                elif raw_pub_year:
                    try:
                        clean_pub_year = int(float(raw_pub_year)) # Handles "2024.0" or "2024"
                    except (ValueError, TypeError):
                        clean_pub_year = 0
                else:
                    clean_pub_year = 0

                book_data = {
                    "title": state.title.strip(),
                    "author": state.author.strip(),
                    "description": state.get("description", ""),
                    "genre": state.genre,
                    "subgenre": state.subgenre,
                    "pages": state.pages,
                    "thumbnail_url": state.thumbnail,
                    "pub_year":clean_pub_year,
                }
                
                book_res = supabase.table("books").upsert(
                    book_data, on_conflict="title, author"
                ).execute()
                
                db_book_id = book_res.data[0]['id']

                log_data = {
                    "book_id": db_book_id,
                    "user_id": current_uid,
                    "rating": state.rating,
                    "progress_percentage": state.get("progress", 100), 
                    "date_started": state.date_started.isoformat() if state.date_started else None,
                    "read_date": state.date_read.isoformat(),
                    "status": state.status,
                    "source": state.source,
                    "review_text": state.review,
                    "is_reread": state.reread
                }
                

                if is_from_tbr:
                    supabase.table("user_books").update(log_data).eq("id", state.from_tbr_id).execute()
                    
                    state.from_tbr_id = None
                    state.title = ""
                    state.author = ""
                    state.pages_val = 0
                    state.thumbnail = None
                else:
                    supabase.table("user_books").insert(log_data).execute()

                st.success(f"Saved {state.title}!")
                st.balloons()
                st.cache_data.clear() 


                if "book_queue" in state and len(state.book_queue) > 0:
                    next_book = state.book_queue.pop(0)
                    
                    state.title = next_book['title']
                    state.author = next_book['author']
                    
                    state.pages_val = 0
                    state.thumbnail = None
                    state.genre = None
                    state.subgenre = None
                    state.review = ""
                    state.status = "TBR"
                    state.rating = 0
                    
                    st.balloons()

                    st.toast(f"Book saved! Loading next: {state.title}")
                    time.sleep(1) 
                    st.rerun()
                else:
                    st.balloons()

                    keys_to_reset = [
                        "from_tbr_id", "title", "author", "pages_val", "genre", 
                        "subgenre", "thumbnail", "pub_year", "rating", "review", 
                        "source", "reread", "date_started", "progress",
                    ]
                    for key in keys_to_reset:
                        if key in state:
                            state[key] = "" if isinstance(state[key], str) else None
                    
                    time.sleep(1) 
                    st.rerun()

            except Exception as e:
                st.error(f"Save failed: {e}")

def reset_add_book_state():
    keys_to_reset = [
        "from_tbr_id", "title", "author", "pages_val", "genre", 
        "subgenre", "thumbnail", "pub_year", "rating", "review", 
        "source", "reread", "date_started", "date_read", "progress", "status"
    ]
    for key in keys_to_reset:
        if key in state:
            del state[key] 
