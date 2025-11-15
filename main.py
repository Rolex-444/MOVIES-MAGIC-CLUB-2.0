import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

import uvicorn

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
)
from database import get_database
from verification import create_universal_shortlink, generate_verify_token
from verification_checker import check_user_access, mark_user_verified

# ============================================
# FASTAPI + DATABASE + TEMPLATES
# ============================================

app = FastAPI()
db = get_database()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ============================================
# PYROGRAM BOT CLIENT (NO WEBHOOK)
# ============================================

bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,
)

print("✅ Pyrogram bot client created (FAST MODE)")

# ============================================
# ADMIN ROUTES (import from admin_routes.py)
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

# Admin login/logout
app.get("/admin", response_class=HTMLResponse)(admin_login_page)
app.post("/admin", response_class=HTMLResponse)(admin_login_post)
app.get("/admin/logout")(admin_logout)

# Admin dashboard + movies
app.get("/admin/dashboard", response_class=HTMLResponse)(admin_dashboard)
app.get("/admin/add-movie", response_class=HTMLResponse)(admin_add_movie_page)
app.post("/admin/add-movie", response_class=HTMLResponse)(admin_add_movie_post)
app.get("/admin/movies", response_class=HTMLResponse)(admin_movies_page)
app.post("/admin/delete-movie/{movie_id}")(admin_delete_movie)

# ============================================
# USER WEBSITE ROUTES (import from user_routes.py)
# ============================================

from user_routes import (
    homepage,
    movie_detail,
    search_movies,
    browse_language,
    browse_genre,
)

app.get("/", response_class=HTMLResponse)(homepage)
app.get("/movie/{movie_id}", response_class=HTMLResponse)(movie_detail)
app.get("/search", response_class=HTMLResponse)(search_movies)
app.get("/language/{language}", response_class=HTMLResponse)(browse_language)
app.get("/genre/{genre}", response_class=HTMLResponse)(browse_genre)

# ============================================
# TELEGRAM BOT HANDLERS
# ============================================

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    """Handle /start command"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Save/Update user in DB
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
        "🎬 **Welcome to Movie Magic Club!**\n\n"
        f"Hi {username}! 👋\n\n"
        "🔍 **Search any movie** by typing its name\n"
        "🌐 **Browse all movies** on our website\n\n"
        "💡 **Tip:** Try searching for \"Leo\" or \"Jailer\"\n"
    )

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
    """Search movie and send result with poster + verification"""
    user_id = message.from_user.id
    query = message.text.strip()
    print(f"🔍 Search: {query}")

    # ========= Verification Daily Limit =========
    access = await check_user_access(user_id, db)
    if not access["allowed"] and access.get("need_verification"):
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
    # ========= End verification block =========

    # Search movies in DB
    movies = await db.movies.find(
        {"title": {"$regex": query, "$options": "i"}}
    ).to_list(length=10)

    if not movies:
        # Not found
        import urllib.parse

        text = (
            "😕 **Movie Not Found**\n\n"
            f"We searched for: `{query}`\n"
            "but couldn't find it in our database.\n\n"
            "💡 **What you can do:**\n"
            "• Request this movie in our group\n"
            "• Browse all available movies\n"
            "• Try different spelling\n"
        )

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

    # Found movies – send each
    for movie in movies:
        try:
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

            movie_url = f"{BASE_URL}/movie/{movie['_id']}"

            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "▶️ Watch", url=movie.get("lulu_link")
                        ),
                        InlineKeyboardButton(
                            "⬇️ Download", url=movie.get("ht_link")
                        ),
                    ],
                    [InlineKeyboardButton("🌐 View on Website", url=movie_url)],
                ]
            )

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

            await db.movies.update_one(
                {"_id": movie["_id"]},
                {"$inc": {"views": 1}},
            )

        except Exception as e:
            print(f"❌ Error sending movie: {e}")
            continue

# ============================================
# VERIFICATION CALLBACK ROUTE
# ============================================

@app.get("/verified")
async def verified(request: Request, uid: str, token: str):
    """Called after user finishes shortlink; verifies token and unlocks for the day."""
    row = await db.verif_tokens.find_one({"user_id": str(uid), "token": token})
    if not row:
        return HTMLResponse("Invalid or expired verification token.", status_code=400)

    expires = row.get("expires")
    if expires and datetime.utcnow() > expires:
        return HTMLResponse(
            "Verification token expired. Please verify again.", status_code=400
        )

    await mark_user_verified(uid, db)
    await db.verif_tokens.delete_one({"_id": row["_id"]})

    return RedirectResponse(url="/")

# ============================================
# HEALTH CHECK
# ============================================

@app.head("/")
@app.get("/health")
async def health_check():
    return {"status": "healthy", "bot": "running"}

# ============================================
# STARTUP & SHUTDOWN – START BOT ONLY ONCE
# ============================================

@app.on_event("startup")
async def startup_event():
    """Start Pyrogram bot once when FastAPI starts"""
    await bot.start()
    print("✅ Bot started (Pyrogram + FastAPI)")
    print("✅ Admin dashboard: /admin")
    print("🔌 Listening on port 8080")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop Pyrogram bot on shutdown"""
    await bot.stop()
    print("🛑 Bot stopped")

# ============================================
# RUN SERVER (for local/dev)
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
    
