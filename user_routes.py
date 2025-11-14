from fastapi import Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_database
from bson import ObjectId
from config import REQUEST_GROUP

# -------------------------------
# Shortlink Verification Imports
# -------------------------------
import pytz
from datetime import datetime, timedelta
from verification import create_universal_shortlink, generate_verify_token
from config import (
    VERIFICATION_FREE_LIMIT,
    VERIFICATION_PERIOD_HOURS,
    VERIFICATION_RESET_HOUR,
    VERIFICATION_TUTORIAL_LINK,
)

db = get_database()
templates = Jinja2Templates(directory="templates")

def get_user_id(request: Request):
    user_id = request.session.get("telegram_user_id")
    if user_id:
        return str(user_id)
    return request.cookies.get("sessionid") or request.client.host

def today_midnight():
    now = datetime.now(pytz.UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)

async def check_verification(request: Request, movie_id: str = None):
    user_id = get_user_id(request)
    now = datetime.now(pytz.UTC)
    row = await db.verif_users.find_one({"user_id": user_id})

    if not row or row.get("last_reset", datetime.min.replace(tzinfo=pytz.UTC)) < today_midnight():
        await db.verif_users.update_one(
            {"user_id": user_id},
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
        await db.verif_users.update_one({"user_id": user_id}, {"$inc": {"count": 1}})
        return True, None

    verify_token = generate_verify_token()
    scheme = request.url.scheme or "https"
    host = request.url.hostname or "localhost"
    redirect_url = f"{scheme}://{host}/verified?uid={user_id}&token={verify_token}"
    shortlink_url = create_universal_shortlink(redirect_url)
    await db.verif_tokens.insert_one(
        {
            "user_id": user_id,
            "token": verify_token,
            "created": now,
            "expires": now + timedelta(hours=VERIFICATION_PERIOD_HOURS),
        }
    )
    return False, shortlink_url

# =========================================
# HOMEPAGE - NO VERIFICATION REQUIRED HERE
# =========================================
async def homepage(request: Request):
    """Main homepage with all sections"""
    latest_movies = await db.movies.find().sort("_id", -1).limit(10).to_list(length=10)
    trending_movies = await db.movies.find().sort("views", -1).limit(10).to_list(length=10)
    tamil_movies = await db.movies.find({"language": "Tamil"}).sort("_id", -1).limit(10).to_list(length=10)
    hindi_movies = await db.movies.find({"language": "Hindi"}).sort("_id", -1).limit(10).to_list(length=10)
    telugu_movies = await db.movies.find({"language": "Telugu"}).sort("_id", -1).limit(10).to_list(length=10)
    action_movies = await db.movies.find({"genres": "Action"}).sort("_id", -1).limit(10).to_list(length=10)
    drama_movies = await db.movies.find({"genres": "Drama"}).sort("_id", -1).limit(10).to_list(length=10)
    comedy_movies = await db.movies.find({"genres": "Comedy"}).sort("_id", -1).limit(10).to_list(length=10)
    total_movies = await db.movies.count_documents({})
    return templates.TemplateResponse("index.html", {
        "request": request,
        "latest_movies": latest_movies,
        "trending_movies": trending_movies,
        "tamil_movies": tamil_movies,
        "hindi_movies": hindi_movies,
        "telugu_movies": telugu_movies,
        "action_movies": action_movies,
        "drama_movies": drama_movies,
        "comedy_movies": comedy_movies,
        "total_movies": total_movies,
    })

# =========================================
# MOVIE DETAIL PAGE (PROTECTED)
# =========================================
async def movie_detail(request: Request, movie_id: str):
    allowed, shortlink_url = await check_verification(request, movie_id)
    if not allowed:
        return templates.TemplateResponse("verification_page.html", {"request": request, "shortlink_url": shortlink_url})
    try:
        movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if not movie:
            return RedirectResponse("/")
        await db.movies.update_one({"_id": ObjectId(movie_id)}, {"$inc": {"views": 1}})
        related_movies = await db.movies.find(
            {"$or": [
                {"language": movie.get("language")},
                {"genres": {"$in": movie.get("genres", [])}}
            ],
            "_id": {"$ne": ObjectId(movie_id)}
        }).limit(6).to_list(length=6)
        return templates.TemplateResponse("movie_detail.html", {
            "request": request,
            "movie": movie,
            "related_movies": related_movies,
        })
    except Exception as e:
        print(f"Error loading movie: {e}")
        return RedirectResponse("/")

# =========================================
# SEARCH PAGE (PROTECTED)
# =========================================
async def search_movies(request: Request, q: str = Query("")):
    allowed, shortlink_url = await check_verification(request)
    if not allowed:
        return templates.TemplateResponse("verification_page.html", {"request": request, "shortlink_url": shortlink_url})
    if not q:
        return RedirectResponse("/")
    movies = await db.movies.find({"title": {"$regex": q, "$options": "i"}}).to_list(length=20)
    return templates.TemplateResponse("search.html", {"request": request, "movies": movies, "query": q})

# =========================================
# VERIFICATION CALLBACK ROUTE
# =========================================
async def verified_callback(request: Request, uid: str, token: str):
    now = datetime.now(pytz.UTC)
    row = await db.verif_tokens.find_one({"user_id": uid, "token": token})
    if not row or row.get("expires") < now:
        return HTMLResponse("<h1>Verification expired. Please verify again!</h1>", status_code=400)
    await db.verif_users.update_one(
        {"user_id": uid},
        {"$set": {"verified": True, "count": VERIFICATION_FREE_LIMIT, "last_reset": today_midnight()}},
        upsert=True,
    )
    await db.verif_tokens.delete_many({"user_id": uid})
    request.session["telegram_user_id"] = uid
    return RedirectResponse("/")
    
# ============================================
# BROWSE BY LANGUAGE
# ============================================

async def browse_language(request: Request, language: str):
    """Browse movies by language"""
    
    movies = await db.movies.find({"language": language}).sort("_id", -1).to_list(length=100)
    
    return templates.TemplateResponse("browse.html", {
        "request": request,
        "title": f"{language} Movies",
        "movies": movies,
        "count": len(movies),
        "filter_type": "language",
        "filter_value": language
    })

# ============================================
# BROWSE BY GENRE
# ============================================

async def browse_genre(request: Request, genre: str):
    """Browse movies by genre"""
    
    movies = await db.movies.find({"genres": genre}).sort("_id", -1).to_list(length=100)
    
    return templates.TemplateResponse("browse.html", {
        "request": request,
        "title": f"{genre} Movies",
        "movies": movies,
        "count": len(movies),
        "filter_type": "genre",
        "filter_value": genre
    })
