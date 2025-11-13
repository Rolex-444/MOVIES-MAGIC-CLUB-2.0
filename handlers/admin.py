from utils.helpers import send_message, send_photo
from config import ADMIN_IDS
from database import get_database

db = get_database()

# State storage for upload wizard
upload_states = {}

async def cmd_addmovie(msg, user_id, chat_id):
    """Start movie upload wizard"""
    upload_states[user_id] = {
        "step": "title",
        "data": {},
        "chat_id": chat_id
    }
    text = (
        "🎬 **Movie Upload Wizard**\n\n"
        "📝 **Step 1/8:** Send movie title\n\n"
        "Example: `Pushpa 2: The Rule`\n\n"
        "💡 Type /cancel to stop"
    )
    await send_message(chat_id, text)
    print(f"✅ Upload started by user {user_id}")

async def cmd_cancel(msg, user_id, chat_id):
    """Cancel upload process"""
    if user_id in upload_states:
        del upload_states[user_id]
        await send_message(chat_id, "❌ Upload cancelled")
        print(f"❌ Upload cancelled by user {user_id}")
    else:
        await send_message(chat_id, "No active upload process")

async def cmd_listmovies(msg, user_id, chat_id):
    """List all movies"""
    movies = await db.get_all_movies(limit=20)
    
    if not movies:
        await send_message(chat_id, "📭 No movies yet!\n\nUse /addmovie to add your first movie.")
        return
    
    text = "🎬 **Recent Movies**\n\n"
    for i, movie in enumerate(movies, 1):
        text += f"{i}. **{movie['title']}** ({movie['year']}) - {movie.get('quality', 'HD')}\n"
    
    text += f"\n📊 Total: {len(movies)} movies"
    await send_message(chat_id, text)

async def handle_upload_steps(msg, user_id, chat_id):
    """Handle each step of movie upload wizard"""
    state = upload_states[user_id]
    step = state["step"]
    data = state["data"]
    
    try:
        if step == "title":
            data["title"] = msg["text"]
            state["step"] = "year"
            await send_message(chat_id, "📅 **Step 2/8:** Send release year\n\nExample: `2024`")
        
        elif step == "year":
            year = int(msg["text"])
            if year < 1900 or year > 2030:
                await send_message(chat_id, "❌ Invalid year. Try again:")
                return
            data["year"] = year
            state["step"] = "genres"
            await send_message(chat_id, "🎭 **Step 3/8:** Send genres (comma-separated)\n\nExample: `Action, Drama`")
        
        elif step == "genres":
            data["genres"] = [g.strip() for g in msg["text"].split(",")]
            state["step"] = "quality"
            await send_message(chat_id, "📺 **Step 4/8:** Send quality\n\nExample: `1080p`")
        
        elif step == "quality":
            data["quality"] = msg["text"]
            state["step"] = "lulu_link"
            await send_message(chat_id, "🎬 **Step 5/8:** Send Lulu Stream link\n\nExample: `https://lulustream.com/v/xyz`")
        
        elif step == "lulu_link":
            if not msg["text"].startswith("http"):
                await send_message(chat_id, "❌ Invalid URL. Try again:")
                return
            data["lulu_link"] = msg["text"]
            state["step"] = "ht_link"
            await send_message(chat_id, "⬇️ **Step 6/8:** Send HTFileSharing link\n\nExample: `https://htfilesharing.com/file/abc`")
        
        elif step == "ht_link":
            if not msg["text"].startswith("http"):
                await send_message(chat_id, "❌ Invalid URL. Try again:")
                return
            data["ht_link"] = msg["text"]
            state["step"] = "poster"
            await send_message(chat_id, "🖼️ **Step 7/8:** Send poster image")
        
        elif step == "poster":
            if "photo" in msg:
                data["poster_file_id"] = msg["photo"][-1]["file_id"]
                state["step"] = "description"
                await send_message(chat_id, "📝 **Step 8/8:** Send description (2-3 lines)")
            else:
                await send_message(chat_id, "❌ Please send an image")
        
        elif step == "description":
            data["description"] = msg["text"]
            
            # Save to database
            movie_doc = {
                "title": data["title"],
                "year": data["year"],
                "genres": data["genres"],
                "quality": data["quality"],
                "lulu_stream_link": data["lulu_link"],
                "htfilesharing_link": data["ht_link"],
                "poster_file_id": data["poster_file_id"],
                "description": data["description"],
                "added_by": user_id
            }
            
            movie_id = await db.add_movie(movie_doc)
            
            # Send confirmation
            caption = (
                f"✅ **Movie Added!**\n\n"
                f"🎬 **{data['title']}** ({data['year']})\n"
                f"🎭 {', '.join(data['genres'])}\n"
                f"📺 {data['quality']}\n\n"
                f"📝 {data['description']}\n\n"
                f"🆔 ID: `{movie_id}`"
            )
            await send_photo(chat_id, data["poster_file_id"], caption)
            
            del upload_states[user_id]
            print(f"✅ Movie added: {data['title']}")
    
    except ValueError as e:
        await send_message(chat_id, f"❌ Invalid input. Try again:")
    except Exception as e:
        await send_message(chat_id, f"❌ Error: {str(e)}\n\nType /cancel")
        print(f"❌ Error: {e}")

def is_user_uploading(user_id):
    """Check if user is in upload process"""
    return user_id in upload_states
    
