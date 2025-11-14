from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os

from config import BOT_TOKEN, API_ID, API_HASH, REQUEST_GROUP
from database import get_database
from verification import create_universal_shortlink, generate_verify_token
from config import (
    VERIFICATION_FREE_LIMIT,
    VERIFICATION_PERIOD_HOURS,
    VERIFICATION_RESET_HOUR,
    VERIFICATION_TUTORIAL_LINK,
)
import pytz
from datetime import datetime, timedelta

from user_routes import (
    homepage, movie_detail, search_movies, browse_language, browse_genre
    # Add other routes as needed
)

app = FastAPI()
db = get_database()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# === Pyrogram Bot ===
bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

def today_midnight():
    now = datetime.now(pytz.UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)

async def bot_check_verification(user_id):
    now = datetime.now(pytz.UTC)
    row = await db.verif_users.find_one({"user_id": str(user_id)})

    if not row or row.get("last_reset", datetime.min.replace(tzinfo=pytz.UTC)) < today_midnight():
        await db.verif_users.update_one(
            {"user_id": str(user_id)},
            {"$set": {"count": 0, "verified": False, "last_reset": today_midnight()}},
            upsert=True,
        )
        count = 0
        verified = False
    else:
        count = row.get("count", 0)
        verified = row.get("verified", False)

    if verified:
        return True, None

    if count < VERIFICATION_FREE_LIMIT:
        await db.verif_users.update_one({"user_id": str(user_id)}, {"$inc": {"count": 1}})
        return True, None

    verify_token = generate_verify_token()
    redirect_url = f"https://your-app-url/verified?uid={user_id}&token={verify_token}"
    shortlink_url = create_universal_shortlink(redirect_url)
    await db.verif_tokens.insert_one(
        {
            "user_id": str(user_id),
            "token": verify_token,
            "created": now,
            "expires": now + timedelta(hours=VERIFICATION_PERIOD_HOURS),
        }
    )
    return False, shortlink_url

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    welcome_text = (
        "🎬 **Welcome to Movie Magic Club!**\n\n"
        "🔍 Type any movie name to search\n"
        "🌐 Or tap the button below to browse all\n"
        "👥 Join our Movie Club Group\n\n"
        "Happy Watching!"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Browse Movies", web_app=WebAppInfo(url="https://your-app-url"))],
        [InlineKeyboardButton("👥 Join Group", url=REQUEST_GROUP)]
    ])
    await message.reply_text(welcome_text, reply_markup=buttons)

@bot.on_message(filters.text & filters.private & ~filters.command(["start"]))
async def search_movie(client, message):
    user_id = message.from_user.id
    allowed, shortlink_url = await bot_check_verification(user_id)
    if not allowed:
        btns = InlineKeyboardMarkup([
            [InlineKeyboardButton("✓ Verify to Continue", url=shortlink_url)],
            [InlineKeyboardButton("📖 HOW TO VERIFY", url=VERIFICATION_TUTORIAL_LINK)]
        ])
        await message.reply_text(
            "IT JUST ONE PAGE.\nONCE YOU COMPLETE THE VERIFICATION YOU ACCESS MY BOT AFTER 24 HOURS.",
            reply_markup=btns
        )
        return

    query = message.text.strip()
    movies = await db.movies.find({"title": {"$regex": query, "$options": "i"}}).to_list(length=10)
    if not movies:
        await message.reply_text("❌ No movies found. Try another name!")
        return

    for movie in movies:
        title = movie.get("title")
        year = movie.get("year", "")
        language = movie.get("language", "")
        genres = ", ".join(movie.get("genres", []))
        quality = movie.get("quality", "")
        description = movie.get("description", "")
        poster_file_id = movie.get("poster_file_id")
        lulu_stream = movie.get("lulu_stream_link")
        htfilesharing = movie.get("htfilesharing_link")
        movie_url = f"https://your-app-url/movie/{movie['_id']}"

        caption = (
            f"🎬 **{title}** {f'({year})' if year else ''}\n"
            f"🗣️ Language: {language}\n"
            f"🎭 Genre: {genres}\n"
            f"📺 Quality: {quality}\n"
            f"📝 {description[:120]}{'...' if len(description) > 120 else ''}\n"
        )
        btns = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("▶️ Watch", url=lulu_stream or movie_url),
                InlineKeyboardButton("⬇️ Download", url=htfilesharing or movie_url)
            ],
            [
                InlineKeyboardButton("🌐 View on Website", web_app=WebAppInfo(url=movie_url))
            ]
        ])
        if poster_file_id:
            await message.reply_photo(poster_file_id, caption=caption, reply_markup=btns)
        else:
            await message.reply_text(caption, reply_markup=btns)

        await db.movies.update_one({"_id": movie["_id"]}, {"$inc": {"views": 1}})

@app.on_event("startup")
async def on_startup():
    await bot.start()

@app.on_event("shutdown")
async def on_shutdown():
    await bot.stop()

# Register user routes
app.add_api_route("/", homepage, methods=["GET"])
app.add_api_route("/movie/{movie_id}", movie_detail, methods=["GET"])
app.add_api_route("/search", search_movies, methods=["GET"])
app.add_api_route("/language/{language}", browse_language, methods=["GET"])
app.add_api_route("/genre/{genre}", browse_genre, methods=["GET"])

# === ADMIN DASHBOARD ROUTE (NEW) ===
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8080)), log_level="info")
                      
