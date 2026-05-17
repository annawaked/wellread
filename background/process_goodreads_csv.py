import pandas as pd
from background.supabase_setup import supabase_setup, get_current_user_id
from background.fetch_book_metadata import fetch_book_metadata
from background.fetch_book_metadata import classify_subgenre_with_ai
from background.options import fiction_subgenres, nonfiction_subgenres


def map_to_subgenre(title, author, genre):
    valid_options = fiction_subgenres() if genre == "Fiction" else nonfiction_subgenres()

    try:
        result = classify_subgenre_with_ai(title, author, genre)

        if result in valid_options:
            return result

        if result:
            for opt in valid_options:
                if result.lower() == opt.lower():
                    return opt

    except Exception:
        pass

    return None


def process_goodreads_csv(file, progress_bar=None):
    supabase = supabase_setup()
    user_id = get_current_user_id()

    if not user_id:
        return {"success": False, "message": "No user logged in."}

    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()
        total_books = len(df)
    except Exception as e:
        return {"success": False, "message": f"Error reading CSV: {e}"}

    success_count = 0
    skipped_count = 0
    errors = []

    # ---------------------------------------------------
    # 🔥 BATCH LOAD EXISTING BOOKS (BIG SPEED IMPROVEMENT)
    # ---------------------------------------------------
    existing_books = supabase.table("books") \
        .select("id, title, author") \
        .execute()

    existing_map = {
        (b["title"].strip().lower(), b["author"].strip().lower()): b["id"]
        for b in (existing_books.data or [])
    }

    for i, (index, row) in enumerate(df.iterrows()):
        try:
            title = str(row['Title']).strip()
            author = str(row['Author']).strip()

            if progress_bar:
                progress_bar.progress(
                    (i + 1) / total_books,
                    text=f"Importing {i+1}/{total_books}: {title[:30]}..."
                )

            key = (title.lower(), author.lower())

            # ----------------------------
            # FAST DUPLICATE CHECK (NO DB CALL)
            # ----------------------------
            if key in existing_map:
                skipped_count += 1
                continue

            # ----------------------------
            # GOOGLE BOOKS METADATA (KEEP THIS)
            # ----------------------------
            meta = None
            try:
                meta = fetch_book_metadata(title, author)
            except Exception:
                meta = None

            # ----------------------------
            # BASIC DATA
            # ----------------------------
            pages = int(row['Number of Pages']) if pd.notna(row['Number of Pages']) and row['Number of Pages'] > 0 else (meta.get('pages', 0) if meta else 0)

            raw_pub = row['Original Publication Year'] if pd.notna(row['Original Publication Year']) else row['Year Published']
            pub_year = int(raw_pub) if pd.notna(raw_pub) else (meta.get('pub_year', 0) if meta else 0)

            # ----------------------------
            # FIXED GENRE (you control system)
            # ----------------------------
            genre = "Fiction"

            # ----------------------------
            # SUBGENRE (AI ONLY WHEN NEEDED)
            # ----------------------------
            subgenre = map_to_subgenre(title, author, genre)

            # ----------------------------
            # BOOK UPSERT
            # ----------------------------
            book_data = {
                "title": title,
                "author": author,
                "pages": pages,
                "pub_year": pub_year,
                "thumbnail_url": meta.get('thumbnail') if meta else None,
                "genre": genre,
                "subgenre": subgenre
            }

            book_res = supabase.table("books") \
                .upsert(book_data, on_conflict="title, author") \
                .execute()

            if not book_res.data:
                continue

            db_book_id = book_res.data[0]['id']

            # ----------------------------
            # USER LOG
            # ----------------------------
            gr_shelf = str(row['Exclusive Shelf']).lower()
            status_map = {
                'read': 'read',
                'currently-reading': 'Currently Reading',
                'to-read': 'TBR'
            }

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