from fastapi import FastAPI
import uvicorn
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS, MONGO_URI
from database import get_database

app = FastAPI()
db = get_database()

# Pyrogram client
bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# Upload state storage
upload_states = {}

# ============================================
# BOT COMMANDS
# ============================================

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    """Start command"""
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    if is_admin:
        text = (
            "🎬 **Movie Bot - Admin**\n\n"
            "✅ Super fast responses!\n\n"
            "**Commands:**\n"
            "/addmovie - Add new movie\n"
            "/listmovies - View all movies\n"
            "/cancel - Cancel upload\n"
            "/test - Test bot"
        )
    else:
        text = "🎬 **Movie Bot**\n\nType movie name to search!"
    
    await message.reply_text(text)

@bot.on_message(filters.command("test") & filters.private)
async def test(client, message):
    """Test command"""
    total = await db.movies.count_documents({})
    await message.reply_text(
        f"✅ **Test**\n\n"
        f"🤖 Bot: Online\n"
        f"⚡ Mode: Pyrogram FAST\n"
        f"🎬 Movies: {total}\n"
        f"👤 ID: `{message.from_user.id}`"
    )

@bot.on_message(filters.command("ping") & filters.private)
async def ping(client, message):
    """Ping command"""
    await message.reply_text("🏓 Pong! Lightning fast!")

# ============================================
# ADMIN - ADD MOVIE WIZARD
# ============================================

@bot.on_message(filters.command("addmovie") & filters.private)
async def addmovie(client, message):
    """Start movie upload wizard"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.reply_text("❌ Admin only!")
        return
    
    upload_states[user_id] = {
        "step": "title",
        "data": {}
    }
    
    await message.reply_text(
        "🎬 **Movie Upload Wizard**\n\n"
        "📝 **Step 1/8:** Send movie title\n\n"
        "Example: `Pushpa 2`\n\n"
        "💡 /cancel to stop"
    )
    print(f"✅ Upload started by {user_id}")

@bot.on_message(filters.command("cancel") & filters.private)
async def cancel(client, message):
    """Cancel upload"""
    user_id = message.from_user.id
    
    if user_id in upload_states:
        del upload_states[user_id]
        await message.reply_text("❌ Upload cancelled")
        print(f"❌ Upload cancelled by {user_id}")
    else:
        await message.reply_text("No active upload")

@bot.on_message(filters.command("listmovies") & filters.private)
async def listmovies(client, message):
    """List all movies"""
    user_id = message.from_user.id
    
    if user_id not in ADMIN_IDS:
        await message.reply_text("❌ Admin only!")
        return
    
    movies = await db.get_all_movies(limit=20)
    
    if not movies:
        await message.reply_text("📭 No movies yet!\n\nUse /addmovie to add first movie")
        return
    
    text = "🎬 **Recent Movies**\n\n"
    for i, movie in enumerate(movies, 1):
        text += f"{i}. **{movie['title']}** ({movie['year']}) - {movie.get('quality', 'HD')}\n"
    
    text += f"\n📊 Total: {len(movies)}"
    await message.reply_text(text)

# ============================================
# UPLOAD WIZARD HANDLER
# ============================================

@bot.on_message(filters.private & ~filters.command(["start", "test", "ping", "addmovie", "cancel", "listmovies"]))
async def handle_messages(client, message):
    """Handle upload steps or search"""
    user_id = message.from_user.id
    
    # Check if in upload mode
    if user_id in upload_states:
        await handle_upload_step(client, message)
    else:
        # Regular search
        await search_movie(client, message)

async def handle_upload_step(client, message):
    """Process upload wizard steps"""
    user_id = message.from_user.id
    state = upload_states[user_id]
    step = state["step"]
    data = state["data"]
    
    try:
        if step == "title":
            data["title"] = message.text
            state["step"] = "year"
            await message.reply_text("📅 **Step 2/8:** Year\n\nExample: `2024`")
        
        elif step == "year":
            year = int(message.text)
            if year < 1900 or year > 2030:
                await message.reply_text("❌ Invalid year. Try again:")
                return
            data["year"] = year
            state["step"] = "genres"
            await message.reply_text("🎭 **Step 3/8:** Genres (comma-separated)\n\nExample: `Action, Drama`")
        
        elif step == "genres":
            data["genres"] = [g.strip() for g in message.text.split(",")]
            state["step"] = "quality"
            await message.reply_text("📺 **Step 4/8:** Quality\n\nExample: `1080p`")
        
        elif step == "quality":
            data["quality"] = message.text
            state["step"] = "lulu_link"
            await message.reply_text("🎬 **Step 5/8:** Lulu Stream link\n\nExample: `https://lulustream.com/v/xyz`")
        
        elif step == "lulu_link":
            if not message.text.startswith("http"):
                await message.reply_text("❌ Invalid URL. Try again:")
                return
            data["lulu_link"] = message.text
            state["step"] = "ht_link"
            await message.reply_text("⬇️ **Step 6/8:** HTFileSharing link\n\nExample: `https://htfilesharing.com/file/abc`")
        
        elif step == "ht_link":
            if not message.text.startswith("http"):
                await message.reply_text("❌ Invalid URL. Try again:")
                return
            data["ht_link"] = message.text
            state["step"] = "poster"
            await message.reply_text("🖼️ **Step 7/8:** Send poster image")
        
        elif step == "poster":
            if message.photo:
                data["poster_file_id"] = message.photo.file_id
                state["step"] = "description"
                await message.reply_text("📝 **Step 8/8:** Description (2-3 lines)")
            else:
                await message.reply_text("❌ Please send an image")
        
        elif step == "description":
            data["description"] = message.text
            
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
                f"🆔 ID: `{movie_id}`\n"
                f"✨ Movie is live!"
            )
            
            await message.reply_photo(
                photo=data["poster_file_id"],
                caption=caption
            )
            
            del upload_states[user_id]
            print(f"✅ Movie added: {data['title']}")
    
    except ValueError as e:
        await message.reply_text(f"❌ Invalid input. Try again:")
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}\n\nType /cancel")
        print(f"❌ Upload error: {e}")

# ============================================
# MOVIE SEARCH
# ============================================

async def search_movie(client, message):
    """Search and show movie"""
    query = message.text.strip()
    print(f"🔍 Search: {query}")
    
    movies = await db.search_movies(query)
    
    if not movies:
        await message.reply_text(f"😕 No results for: `{query}`")
        return
    
    movie = movies[0]
    caption = (
        f"🎬 **{movie['title']}** ({movie.get('year', 'N/A')})\n\n"
        f"🎭 {', '.join(movie.get('genres', []))}\n"
        f"📺 {movie.get('quality', 'HD')}\n\n"
        f"📝 {movie.get('description', 'No description')}"
    )
    
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 Watch", url=movie['lulu_stream_link']),
            InlineKeyboardButton("⬇️ Download", url=movie['htfilesharing_link'])
        ]
    ])
    
    # Try with poster
    try:
        await message.reply_photo(
            photo=movie['poster_file_id'],
            caption=caption,
            reply_markup=buttons
        )
        print(f"✅ Sent with poster: {movie['title']}")
    except Exception as e:
        print(f"⚠️ Poster failed: {e}")
        # Send without poster BUT WITH BUTTONS!
        await message.reply_text(
            caption,
            reply_markup=buttons
        )
        print(f"✅ Sent without poster: {movie['title']}")
            
        
# ============================================
# FASTAPI
# ============================================

@app.get("/")
@app.head("/")
@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "healthy", "bot": "movie-bot"}

@app.on_event("startup")
async def startup():
    """Start Pyrogram bot"""
    await bot.start()
    print("✅ Pyrogram bot started - FAST MODE!")
    print("🔌 Listening on port 8080")

@app.on_event("shutdown")
async def shutdown():
    """Stop Pyrogram bot"""
    await bot.stop()
    print("✅ Bot stopped")
        
