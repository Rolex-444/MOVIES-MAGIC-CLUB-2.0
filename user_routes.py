from fastapi import Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from database import get_database
from bson import ObjectId
from config import REQUEST_GROUP
import urllib.parse

templates = Jinja2Templates(directory="templates")
db = get_database()

# ============================================
# HOMEPAGE
# ============================================

async def homepage(request: Request):
    """Main homepage with all sections"""
    
    # Get latest movies for carousel (10 newest)
    latest_movies = await db.movies.find().sort("_id", -1).limit(10).to_list(length=10)
    
    # Get trending movies (most viewed in last 7 days)
    trending_movies = await db.movies.find().sort("views", -1).limit(10).to_list(length=10)
    
    # Get movies by language
    tamil_movies = await db.movies.find({"language": "Tamil"}).sort("_id", -1).limit(10).to_list(length=10)
    hindi_movies = await db.movies.find({"language": "Hindi"}).sort("_id", -1).limit(10).to_list(length=10)
    telugu_movies = await db.movies.find({"language": "Telugu"}).sort("_id", -1).limit(10).to_list(length=10)
    
    # Get movies by genre
    action_movies = await db.movies.find({"genres": "Action"}).sort("_id", -1).limit(10).to_list(length=10)
    drama_movies = await db.movies.find({"genres": "Drama"}).sort("_id", -1).limit(10).to_list(length=10)
    comedy_movies = await db.movies.find({"genres": "Comedy"}).sort("_id", -1).limit(10).to_list(length=10)
    
    # Get total counts
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
        "total_movies": total_movies
    })

# ============================================
# MOVIE DETAIL PAGE
# ============================================

async def movie_detail(request: Request, movie_id: str):
    """Show single movie detail page"""
    
    try:
        # Get movie from database
        movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        
        if not movie:
            return RedirectResponse("/")
        
        # Increment view count
        await db.movies.update_one(
            {"_id": ObjectId(movie_id)},
            {"$inc": {"views": 1}}
        )
        
        # Get related movies (same language or genre)
        related_movies = await db.movies.find({
            "$or": [
                {"language": movie.get("language")},
                {"genres": {"$in": movie.get("genres", [])}}
            ],
            "_id": {"$ne": ObjectId(movie_id)}
        }).limit(6).to_list(length=6)
        
        return templates.TemplateResponse("movie_detail.html", {
            "request": request,
            "movie": movie,
            "related_movies": related_movies
        })
        
    except Exception as e:
        print(f"Error loading movie: {e}")
        return RedirectResponse("/")

# ============================================
# SEARCH PAGE
# ============================================

async def search_movies(request: Request, q: str = Query("")):
    """Search movies"""
    
    if not q:
        return RedirectResponse("/")
    
    # Search in database (title, case-insensitive)
    movies = await db.movies.find({
        "title": {"$regex": q, "$options": "i"}
    }).to_list(length=50)
    
    if not movies:
        # No results - show request page
        return templates.TemplateResponse("search_no_results.html", {
            "request": request,
            "query": q,
            "request_url": f"{REQUEST_GROUP}?text=🎬 Movie Request: {urllib.parse.quote(q)}"
        })
    
    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "query": q,
        "movies": movies,
        "count": len(movies)
    })

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
