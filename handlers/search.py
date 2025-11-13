from utils.helpers import send_message, send_photo
from database import get_database

db = get_database()

async def search_movies(msg, user_id, chat_id, query):
    """Search movies by title - OPTIMIZED"""
    print(f"🔍 Searching: {query}")
    
    try:
        # Search database
        movies = await db.search_movies(query)
        
        if not movies:
            await send_message(
                chat_id,
                f"😕 No results for: `{query}`\n\nTry another name!"
            )
            return
        
        # Show first result
        movie = movies[0]
        title = movie.get('title', 'Unknown')
        year = movie.get('year', 'N/A')
        genres = ', '.join(movie.get('genres', []))
        quality = movie.get('quality', 'HD')
        description = movie.get('description', 'No description')
        poster = movie.get('poster_file_id')
        lulu_link = movie.get('lulu_stream_link')
        ht_link = movie.get('htfilesharing_link')
        
        caption = (
            f"🎬 **{title}** ({year})\n\n"
            f"🎭 {genres}\n"
            f"📺 {quality}\n\n"
            f"📝 {description}\n\n"
            f"⬇️ Choose your option:"
        )
        
        # Create buttons
        buttons = {
            "inline_keyboard": [
                [
                    {"text": "🎬 Watch", "url": lulu_link},
                    {"text": "⬇️ Download", "url": ht_link}
                ]
            ]
        }
        
        # Send movie card using helper (reuses session - FAST!)
        await send_photo(chat_id, poster, caption, reply_markup=buttons)
        
        print(f"✅ Sent: {title}")
        
    except Exception as e:
        print(f"❌ Search error: {e}")
        import traceback
        traceback.print_exc()
        
