import time
from background.supabase_setup import supabase_setup
from background.fetch_book_metadata import fetch_book_metadata

def bulk_fix_covers():
    supabase = supabase_setup()
    
    # 1. Fetch books that are missing covers
    # Note: Adjust column names if yours are 'thumbnail_url' or 'thumbnail_url'
    res = supabase.table("books").select("id, title, author").or_("thumbnail_url.is.null, thumbnail_url.eq.''").execute()
    books_to_fix = res.data

    if not books_to_fix:
        print("✅ All books already have covers!")
        return

    print(f"🔍 Found {len(books_to_fix)} books missing covers. Starting update...")

    for book in books_to_fix:
        print(f"Updating: {book['title']} by {book['author']}...")
        
        # 2. Call your existing metadata function
        meta = fetch_book_metadata(book['title'], book['author'])
        
        if meta and meta.get('thumbnail'):
            new_url = meta.get('thumbnail')
            
            # 3. Update Supabase
            supabase.table("books").update({"thumbnail_url": new_url}).eq("id", book['id']).execute()
            print(f" ✨ Success!")
        else:
            print(f" ❌ No cover found.")
        
        # 4. Respect API limits (slight pause)
        time.sleep(1)

    print("🏁 Done!")

if __name__ == "__main__":
    bulk_fix_covers()