from fastapi import Request, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from bson import ObjectId
import urllib.parse
from datetime import datetime, timedelta

from database import get_database
from config import REQUEST_GROUP

# NEW: imports for verification
from config import (
    BASE_URL,
    VERIFICATION_TUTORIAL_LINK,
    VERIFICATION_TUTORIAL_NAME,
    VERIFICATION_PERIOD_HOURS,
)

from verification_checker import check_user_access
from verification import create_universal_shortlink, generate_verify_token

templates = Jinja2Templates(directory="templates")
db = get_database()

# ============================================
# HOMEPAGE
# ============================================


async def homepage(request: Request):
    """Main homepage with all sections"""
    latest_movies = (
        await db.movies.find()
        .sort("_id", -1)
        .limit(10)
        .to_list(length=10)
    )
    trending_movies = (
        await db.movies.find()
        .sort("views", -1)
        .limit(10)
        .to_list(length=10)
    )
    tamil_movies = (
        await db.movies.find({"language": "Tamil"})
        .sort("_id", -1)
        .limit(10)
        .to_list(length=10)
    )
    hindi_movies = (
        await db.movies.find({"language": "Hindi"})
        .sort("_id", -1)
        .limit(10)
        .to_list(length=10)
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "latest_movies": latest_movies,
            "trending_movies": trending_movies,
            "tamil_movies": tamil_movies,
            "hindi_movies": hindi_movies,
            "request_group": REQUEST_GROUP,
        },
    )


# ============================================
# MOVIE DETAIL (with verification)
# ============================================


async def movie_detail(request: Request, movie_id: str):
    """Movie detail page with player"""
    movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not movie:
        return HTMLResponse("Movie not found", status_code=404)

    # Verification check for website users
    user_id = str(request.client.host)

    access = await check_user_access(user_id, db)
    if not access["allowed"] and access["need_verification"]:
        # Generate verification token + shortlink
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

        return templates.TemplateResponse(
            "verify_page.html",
            {
                "request": request,
                "shortlink_url": shortlink_url,
                "tutorial_name": VERIFICATION_TUTORIAL_NAME,
                "tutorial_link": VERIFICATION_TUTORIAL_LINK,
            },
        )

    # If allowed, render movie detail page
    return templates.TemplateResponse(
        "movie_detail.html",
        {
            "request": request,
            "movie": movie,
        },
    )


# ============================================
# WATCH / DOWNLOAD REDIRECTS
# ============================================


async def watch_movie(request: Request, movie_id: str):
    """Redirect user to the movie watch/stream link."""
    movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    # Try multiple possible field names
    watch_link = (
        movie.get("watch_link")
        or movie.get("watch_url")
        or movie.get("stream_link")
        or movie.get("lulu_link")
    )
    if not watch_link:
        raise HTTPException(
            status_code=404,
            detail="Watch link not configured for this movie",
        )

    return RedirectResponse(url=watch_link, status_code=302)


async def download_movie(request: Request, movie_id: str):
    """Redirect user to the movie download link."""
    movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    download_link = (
        movie.get("download_link")
        or movie.get("download_url")
        or movie.get("ht_link")
    )
    if not download_link:
        raise HTTPException(
            status_code=404,
            detail="Download link not configured for this movie",
        )

    return RedirectResponse(url=download_link, status_code=302)


# ============================================
# SEARCH PAGE
# ============================================


async def search_movies(request: Request, q: str = Query("")):
    """Search movies"""
    if not q:
        return RedirectResponse("/")

    # Search in database (title, case-insensitive)
    movies = await db.movies.find(
        {"title": {"$regex": q, "$options": "i"}}
    ).to_list(length=50)

    if not movies:
        # No results - show request page
        return templates.TemplateResponse(
            "search_no_results.html",
            {
                "request": request,
                "query": q,
                "request_url": f"{REQUEST_GROUP}?text=🎬 Movie Request: {urllib.parse.quote(q)}",
            },
        )

    return templates.TemplateResponse(
        "search_results.html",
        {
            "request": request,
            "query": q,
            "movies": movies,
            "count": len(movies),
        },
    )


# ============================================
# BROWSE BY LANGUAGE
# ============================================


async def browse_language(request: Request, language: str):
    """Browse movies by language"""
    movies = (
        await db.movies.find({"language": language})
        .sort("_id", -1)
        .to_list(length=100)
    )

    return templates.TemplateResponse(
        "browse.html",
        {
            "request": request,
            "title": f"{language} Movies",
            "movies": movies,
            "count": len(movies),
            "filter_type": "language",
            "filter_value": language,
        },
    )


# ============================================
# BROWSE BY GENRE
# ============================================


async def browse_genre(request: Request, genre: str):
    """Browse movies by genre"""
    movies = (
        await db.movies.find({"genres": genre})
        .sort("_id", -1)
        .to_list(length=100)
    )

    return templates.TemplateResponse(
        "browse.html",
        {
            "request": request,
            "title": f"{genre} Movies",
            "movies": movies,
            "count": len(movies),
            "filter_type": "genre",
            "filter_value": genre,
        },
    )
