from fastapi import FastAPI
import uvicorn
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS, MONGO_URI
from database import get_database

app = FastAPI()
db = get_database()

# Pyrogram client - MUCH FASTER!
bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True  # No session file needed
)

# ============================================
# BOT COMMANDS - INSTANT RESPONSE!
# ============================================

@bot.on_message(filters.command("start"))
async def start(client, message):
    """Start command - FAST!"""
    user_id = message.from_user.id
    is_admin = user_id in ADMIN_IDS
    
    if is_admin:
        text = (
            "🎬 **Movie Bot - Admin**\n\n"
            "✅ Bot online\n"
            "✅ Fast responses!\n\n"
            "/addmovie - Add movie\n"
            "/test - Test bot"
        )
    else:
        text = "🎬 **Movie Bot**\n\nType movie name to search!"
    
    await message.reply_text(text)

@bot.on_message(filters.command("test"))
async def test(client, message):
    """Test command"""
    total = await db.movies.count_documents({})
    await message.reply_text(
        f"✅ **Test**\n\n"
        f"🤖 Bot: Online\n"
        f"🎬 Movies: {total}\n"
        f"👤 ID: `{message.from_user.id}`"
    )

@bot.on_message(filters.command("ping"))
async def ping(client, message):
    """Ping command"""
    await message.reply_text("🏓 Pong! Super fast!")

@bot.on_message(filters.text & filters.private & ~filters.command(["start", "test", "ping"]))
async def search(client, message):
    """Search movies - INSTANT!"""
    query = message.text.strip()
    print(f"🔍 Search: {query}")
    
    movies = await db.search_movies(query)
    
    if not movies:
        await message.reply_text(f"😕 No results for: `{query}`")
        return
    
    # Show first movie
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
    
    await message.reply_photo(
        photo=movie['poster_file_id'],
        caption=caption,
        reply_markup=buttons
    )
    print(f"✅ Sent: {movie['title']}")

# ============================================
# FASTAPI ROUTES
# ============================================

@app.get("/")
@app.get("/health")
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
    
