import time
from background.supabase_setup import supabase_setup
from background.fetch_book_metadata import fetch_book_metadata

supabase = supabase_setup()

def backfill():
    # 1. Fetch all books that have an empty or null description
    # We use .is_('description', 'null') or .eq('description', '') depending on your DB
    response = supabase.table("books").select("id, title, author").or_("description.is.null,description.eq.''").execute()
    books_to_fix = response.data

    if not books_to_fix:
        print("✅ All books already have dates!")
        return

    print(f"found {len(books_to_fix)} books needing pub date...")

    for book in books_to_fix:
        print(f"Refetching: {book['title']} by {book['author']}...")
        
        # 2. Call your existing Google Books function
        meta = fetch_book_metadata(book['title'], book['author'])
        
        if meta and meta.get('publishedDate'):
            # 3. Update only the description for this specific book ID
            supabase.table("books").update({
                "pub_date": meta['publishedDate']
            }).eq("id", book['id']).execute()
            print(f"  -- Success!")
        else:
            print(f"  -- No date found on Google Books.")

        # 4. Respect the Google API rate limit (don't spam them!)
        time.sleep(1)

if __name__ == "__main__":
    backfill()