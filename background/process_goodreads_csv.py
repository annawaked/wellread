import pandas as pd
import time 
from background.supabase_setup import supabase_setup, get_current_user_id
from background.fetch_book_metadata import fetch_book_metadata

def process_goodreads_csv(file, progress_bar=None):
    supabase = supabase_setup()
    user_id = get_current_user_id()
    
    if not user_id:
        return {"success": False, "message": "No user logged in."}

    # 1. Load the CSV and define total_books
    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        total_books = len(df) # Defined here for the progress bar
    except Exception as e:
        return {"success": False, "message": f"Error reading CSV: {e}"}
    
    success_count = 0
    skipped_count = 0
    errors = []

    # Get existing books for this user to prevent duplicates
    existing_user_books = supabase.table("user_books").select("book_id").eq("user_id", user_id).execute()
    existing_ids = {item['book_id'] for item in existing_user_books.data}

    # 2. Loop through the books
    for i, (index, row) in enumerate(df.iterrows()):
        try:
            title = str(row['Title']).strip()
            author = str(row['Author']).strip()

            # Update progress bar if provided
            if progress_bar:
                progress_bar.progress((i + 1) / total_books, text=f"Importing {i+1}/{total_books}: {title[:30]}...")

            # 3. Duplicate Check
            book_check = supabase.table("books").select("id").eq("title", title).eq("author", author).execute()
            if book_check.data and book_check.data[0]['id'] in existing_ids:
                skipped_count += 1
                continue

            # 4. SAFE AUTO-FETCH METADATA (Try/Except handles the Quota Error)
            meta = None
            try:
                meta = fetch_book_metadata(title, author)
                time.sleep(1) # Slow down to avoid hitting limits too fast
            except Exception:
                # If Google blocks us, we continue without 'meta'
                pass 

            # 5. Prepare Global Book Data
            pages = int(row['Number of Pages']) if pd.notna(row['Number of Pages']) and row['Number of Pages'] > 0 else (meta.get('pages', 0) if meta else 0)
            raw_pub = row['Original Publication Year'] if pd.notna(row['Original Publication Year']) else row['Year Published']
            pub_year = int(raw_pub) if pd.notna(raw_pub) else (meta.get('pub_year', 0) if meta else 0)
            
            book_data = {
                "title": title,
                "author": author,
                "pages": pages,
                "pub_year": pub_year,
                "thumbnail_url": meta.get('thumbnail') if meta else None,
                "genre": meta.get('genre') if meta and meta.get('genre') else "Fiction",
            }

            # 6. Upsert into 'books' table (global)
            book_res = supabase.table("books").upsert(book_data, on_conflict="title, author").execute()
            if not book_res.data:
                continue
            db_book_id = book_res.data[0]['id']

            # 7. Prepare and Log Personal Data
            gr_shelf = str(row['Exclusive Shelf']).lower()
            status_map = {'read': 'read', 'currently-reading': 'Currently Reading', 'to-read': 'TBR'}

            log_data = {
                "user_id": user_id,
                "book_id": db_book_id,
                "status": status_map.get(gr_shelf, 'read'),
                "rating": int(row['My Rating']) if row['My Rating'] > 0 else 0,
                "review_text": str(row['My Review']) if pd.notna(row['My Review']) else "",
                "read_date": pd.to_datetime(row['Date Read']).isoformat() if pd.notna(row['Date Read']) else None,
                "date_started": pd.to_datetime(row['Date Added']).isoformat() if pd.notna(row['Date Added']) else None,
            }

            supabase.table("user_books").insert(log_data).execute()
            success_count += 1
            
        except Exception as e:
            errors.append(f"Error with {row.get('Title', 'Unknown')}: {str(e)}")
            
    return {
        "success": True, 
        "counts": {
            "new": success_count, 
            "skipped": skipped_count,
            "errors": errors,
        }
    }

