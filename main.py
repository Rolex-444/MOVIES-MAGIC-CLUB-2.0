from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os
from datetime import datetime, timedelta

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import (
    BOT_TOKEN,
    API_ID,
    API_HASH,
    ADMIN_IDS,
    SECRET_KEY,
    REQUEST_GROUP,
    BASE_URL,
    VERIFICATION_PERIOD_HOURS,
    VERIFICATION_TUTORIAL_LINK,
    VERIFICATION_TUTORIAL_NAME,
    POSTER_CHANNEL,
)

from database import get_database

# NEW: shortlink + verification helpers
from verification import create_universal_shortlink, generate_verify_token
from verification_checker import check_user_access, mark_user_verified

# ============================================
# FASTAPI + PYROGRAM SETUP
# ============================================

app = FastAPI()
db = get_database()

# Add session middleware for admin login
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Pyrogram client (FAST MODE - No webhook)
bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)

print("✅ Pyrogram bot started - FAST MODE!")

# ============================================
# CHANNEL INITIALIZATION (TEMPORARY - REMOVE AFTER FIRST RUN)
# ============================================
async def init_channel():
    """Initialize channel by sending a test message"""
    async with Client("init-bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True) as app:
        await app.send_message(POSTER_CHANNEL, "✅ Channel initialized for poster uploads.")
        
# ============================================
# ADMIN ROUTES (Phase 1)
# ============================================

from admin_routes import (
    admin_login_page,
    admin_login_post,
    admin_logout,
    admin_dashboard,
    admin_add_movie_page,
    admin_add_movie_post,
    admin_movies_page,
    admin_delete_movie,
)

# Admin Login
app.get("/admin", response_class=HTMLResponse)(admin_login_page)
app.post("/admin", response_class=HTMLResponse)(admin_login_post)

# Admin Logout
app.get("/admin/logout")(admin_logout)

# Admin Dashboard
app.get("/admin/dashboard", response_class=HTMLResponse)(admin_dashboard)

# Add Movie
app.get("/admin/add-movie", response_class=HTMLResponse)(admin_add_movie_page)
app.post("/admin/add-movie", response_class=HTMLResponse)(admin_add_movie_post)

# View All Movies
app.get("/admin/movies", response_class=HTMLResponse)(admin_movies_page)

# Delete Movie
app.post("/admin/delete-movie/{movie_id}")(admin_delete_movie)

# ============================================
# USER WEBSITE ROUTES (Phase 2)
# ============================================

from user_routes import (
    homepage,
    movie_detail,
    search_movies,
    browse_language,
    browse_genre,
)

# Homepage
app.get("/", response_class=HTMLResponse)(homepage)

# Movie detail page
app.get("/movie/{movie_id}", response_class=HTMLResponse)(movie_detail)

# Search
app.get("/search", response_class=HTMLResponse)(search_movies)

# Browse by language
app.get("/language/{language}", response_class=HTMLResponse)(browse_language)

# Browse by genre
app.get("/genre/{genre}", response_class=HTMLResponse)(browse_genre)

# ============================================
# TELEGRAM BOT HANDLERS (Phase 3 - NO WebApp)
# ============================================

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Save user to database
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "username": username,
                "user_id": user_id,
            },
            "$setOnInsert": {"joined_at": message.date},
        },
        upsert=True,
    )

    welcome_text = (
        f"🎬 **Welcome to Movie Magic Club!**\n\n"
        f"Hi {username}! 👋\n\n"
        f"🔍 **Search any movie** by typing its name\n"
        f"🌐 **Browse all movies** on our website\n\n"
        f"💡 **Tip:** Try searching for \"Leo\" or \"Jailer\"\n"
    )

    # Simple URL buttons (no WebApp)
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🌐 Browse Website", url=BASE_URL)],
            [InlineKeyboardButton("👥 Join Group", url=REQUEST_GROUP)],
        ]
    )

    await message.reply_text(welcome_text, reply_markup=buttons)
    print(f"✅ New user: {username} (ID: {user_id})")


@bot.on_message(filters.text & filters.private & ~filters.command(["start"]))
async def search_movie(client, message):
    """Search and send movie"""
    user_id = message.from_user.id

    # ========== NEW: Shortlink verification daily limit ==========
    access = await check_user_access(user_id, db)

    if not access["allowed"] and access.get("need_verification"):
        # User exceeded free limit -> generate shortlink verification
        verify_token = generate_verify_token()
        redirect_url = f"{BASE_URL}/verified?uid={user_id}&token={verify_token}"
        shortlink_url = create_universal_shortlink(redirect_url)

        await db.verif_tokens.insert_one(
            {
                "user_id": str(user_id),
                "token": verify_token,
                "created": datetime.utcnow(),
                "expires": datetime.utcnow()
                + timedelta(hours=VERIFICATION_PERIOD_HOURS),
            }
        )

        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✅ Verify", url=shortlink_url)],
                [
                    InlineKeyboardButton(
                        VERIFICATION_TUTORIAL_NAME,
                        url=VERIFICATION_TUTORIAL_LINK,
                    )
                ],
            ]
        )

        await message.reply_text(
            "You have used today's free limit.\n"
            "Complete this verification once to unlock all movies for today.",
            reply_markup=buttons,
        )
        return
    # ========== END verification block ==========

    query = message.text.strip()
    print(f"🔍 Search: {query}")

    # Search in database (case-insensitive)
    movies = await db.movies.find(
        {"title": {"$regex": query, "$options": "i"}}
    ).to_list(length=10)

    if not movies:
        # Movie not found - show request button
        text = (
            f"😕 **Movie Not Found**\n\n"
            f"We searched for: `{query}`\n"
            f"but couldn't find it in our database.\n\n"
            f"💡 **What you can do:**\n"
            f"• Request this movie in our group\n"
            f"• Browse all available movies\n"
            f"• Try different spelling\n"
        )

        import urllib.parse

        request_url = (
            f"{REQUEST_GROUP}"
            f"?text=🎬 Movie Request: {urllib.parse.quote(query)}"
        )

        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🎬 Request Movie", url=request_url)],
                [InlineKeyboardButton("🌐 Browse All Movies", url=BASE_URL)],
            ]
        )

        await message.reply_text(text, reply_markup=buttons)
        print(f"❌ Movie not found: {query}")
        return

    # Movie found - send details
    for movie in movies:
        try:
            # Prepare movie caption
            title = movie.get("title", "Unknown")
            year = movie.get("year", "N/A")
            language = movie.get("language", "N/A")
            genres = ", ".join(movie.get("genres", []))
            quality = movie.get("quality", "N/A")
            description = movie.get("description", "No description")
            views = movie.get("views", 0)

            caption = (
                f"🎬 **{title}** ({year})\n\n"
                f"🗣️ Language: {language}\n"
                f"🎭 Genre: {genres}\n"
                f"📺 Quality: {quality}\n"
                f"👁 Views: {views}\n\n"
                f"📝 {description}\n"
            )

            # Buttons (simple URLs, no WebApp)
            movie_url = f"{BASE_URL}/movie/{movie['_id']}"
            
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "▶️ Watch", url=movie.get("lulu_stream_link")
                        ),
                        InlineKeyboardButton(
                            "⬇️ Download", url=movie.get("htfilesharing_link")
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🌐 View on Website",
                            url=movie_url
                        )
                    ],
                ]
            )

            # Send with poster
            poster_file_id = movie.get("poster_file_id")
            if poster_file_id:
                await message.reply_photo(
                    photo=poster_file_id,
                    caption=caption,
                    reply_markup=buttons,
                )
                print(f"✅ Sent with poster: {title}")
            else:
                await message.reply_text(caption, reply_markup=buttons)
                print(f"✅ Sent without poster: {title}")

            # Update view count
            await db.movies.update_one(
                {"_id": movie["_id"]},
                {"$inc": {"views": 1}},
            )

        except Exception as e:
            print(f"❌ Error sending movie: {e}")
            continue


# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup_event():
    await init_channel()
    """Start bot on startup"""
    await bot.start()
    print("✅ Admin dashboard: /admin")
    print("🔌 Listening on port 8080")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop bot on shutdown"""
    await bot.stop()
    print("🛑 Bot stopped")


# ============================================
# VERIFICATION CALLBACK ROUTE (NEW)
# ============================================

@app.get("/verified")
async def verified(request: Request, uid: str, token: str):
    """
    Called after user finishes shortlink; verifies token and unlocks for the day.
    """
    row = await db.verif_tokens.find_one({"user_id": str(uid), "token": token})

    if not row:
        return HTMLResponse("Invalid or expired verification token.", status_code=400)

    expires = row.get("expires")
    if expires and datetime.utcnow() > expires:
        return HTMLResponse("Verification token expired. Please verify again.", status_code=400)

    await mark_user_verified(uid, db)
    await db.verif_tokens.delete_one({"_id": row["_id"]})

    return RedirectResponse(url="/")


# ============================================
# ROOT ENDPOINT (Health Check)
# ============================================

@app.head("/")
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "running"}


# ============================================
# RUN SERVER
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
)
    
