from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS, SECRET_KEY
from database import get_database
# Add to existing imports
from user_routes import (
    homepage,
    movie_detail,
    search_movies,
    browse_language,
    browse_genre
)


app = FastAPI()
db = get_database()

# Add session middleware for admin login
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Pyrogram client
bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ============================================
# BOT COMMANDS (KEEP YOUR EXISTING BOT CODE)
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
            "/test - Test bot"
        )
    else:
        text = "🎬 **Movie Magic Club**\n\nType movie name to search!"
    
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

# ... (KEEP ALL YOUR OTHER BOT COMMANDS)

# ============================================
# MOVIE SEARCH (EXISTING CODE)
# ============================================

@bot.on_message(filters.text & filters.private & ~filters.command(["start", "test", "addmovie", "listmovies", "cancel"]))
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
# FASTAPI ROUTES (Health Check)
# ============================================

@app.get("/")
@app.head("/")
@app.get("/health")
@app.head("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "movie-bot"}

# ============================================
# ADMIN ROUTES (Import from admin_routes.py)
# ============================================

from admin_routes import (
    admin_login_page,
    admin_login_post,
    admin_logout,
    admin_dashboard,
    admin_add_movie_page,
    admin_add_movie_post,
    admin_movies_page,
    admin_delete_movie
)

# Admin Login
@app.get("/admin", response_class=HTMLResponse)
async def get_admin_login(request: Request):
    return await admin_login_page(request)

@app.post("/admin/login")
async def post_admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    return await admin_login_post(request, username, password)

@app.get("/admin/logout")
async def get_admin_logout(request: Request):
    return await admin_logout(request)

# Admin Dashboard
@app.get("/admin/dashboard", response_class=HTMLResponse)
async def get_admin_dashboard(request: Request):
    return await admin_dashboard(request)

# Add Movie
@app.get("/admin/add-movie", response_class=HTMLResponse)
async def get_admin_add_movie(request: Request):
    return await admin_add_movie_page(request)

@app.post("/admin/add-movie")
async def post_admin_add_movie(
    request: Request,
    title: str = Form(...),
    year: int = Form(...),
    genres: str = Form(...),
    quality: str = Form(...),
    description: str = Form(...),
    lulu_link: str = Form(...),
    ht_link: str = Form(...),
    poster: UploadFile = File(...)
):
    return await admin_add_movie_post(request, title, year, genres, quality, description, lulu_link, ht_link, poster)

# View All Movies
@app.get("/admin/movies", response_class=HTMLResponse)
async def get_admin_movies(request: Request):
    return await admin_movies_page(request)

# Delete Movie
@app.post("/admin/delete-movie/{movie_id}")
async def post_admin_delete_movie(request: Request, movie_id: str):
    return await admin_delete_movie(request, movie_id)

# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup():
    """Start Pyrogram bot"""
    await bot.start()
    print("✅ Pyrogram bot started - FAST MODE!")
    print("✅ Admin dashboard: /admin")
    print("🔌 Listening on port 8080")

@app.on_event("shutdown")
async def shutdown():
    """Stop Pyrogram bot"""
    await bot.stop()
    print("✅ Bot stopped")
        
