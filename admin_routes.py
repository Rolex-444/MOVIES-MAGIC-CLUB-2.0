from fastapi import Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional
from bson import ObjectId
import base64
from config import ADMIN_USERNAME, ADMIN_PASSWORD, ADMIN_IDS
from database import get_database

templates = Jinja2Templates(directory="templates")
db = get_database()

# ============================================
# ADMIN AUTHENTICATION
# ============================================

def check_admin_auth(request: Request):
    """Check if admin is logged in"""
    return request.session.get("admin_logged_in", False)

# ============================================
# ADMIN LOGIN ROUTES
# ============================================

async def admin_login_page(request: Request):
    """Show admin login page"""
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": None,
        "success": None
    })

async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle admin login"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["admin_logged_in"] = True
        return RedirectResponse("/admin/dashboard", status_code=302)
    else:
        return templates.TemplateResponse("admin_login.html", {
            "request": request,
            "error": "❌ Invalid username or password!",
            "success": None
        })

async def admin_logout(request: Request):
    """Logout admin"""
    request.session.clear()
    return RedirectResponse("/admin", status_code=302)

# ============================================
# ADMIN DASHBOARD
# ============================================

async def admin_dashboard(request: Request):
    """Main dashboard page"""
    if not check_admin_auth(request):
        return RedirectResponse("/admin", status_code=302)
    
    # Get statistics
    total_movies = await db.movies.count_documents({})
    total_users = await db.users.count_documents({})
    total_views = 0
    
    # Get all movies to calculate total views
    movies = await db.movies.find().to_list(length=None)
    for movie in movies:
        total_views += movie.get('views', 0)
    
    # Get recent movies (last 5)
    recent_movies = await db.movies.find().sort("_id", -1).limit(5).to_list(length=5)
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_movies": total_movies,
        "total_users": total_users,
        "total_views": total_views,
        "recent_movies": recent_movies
    })

# ============================================
# ADD MOVIE
# ============================================

async def admin_add_movie_page(request: Request):
    """Show add movie form"""
    if not check_admin_auth(request):
        return RedirectResponse("/admin", status_code=302)
    
    return templates.TemplateResponse("admin_add_movie.html", {
        "request": request,
        "success": None,
        "error": None
    })

async def admin_add_movie_post(
    request: Request,
    title: str = Form(...),
    year: int = Form(...),
    language: str = Form(...),  # NEW: Language field
    genres: str = Form(...),
    quality: str = Form(...),
    description: str = Form(...),
    lulu_link: str = Form(...),
    ht_link: str = Form(...),
    poster: UploadFile = File(...)
):
    """Handle add movie form submission"""
    if not check_admin_auth(request):
        return RedirectResponse("/admin", status_code=302)
    
    try:
        # Read poster image
        poster_data = await poster.read()
        
        # Upload to Telegram to get file_id (using bot)
        from main import bot
        from io import BytesIO
        
        # Get admin ID from ADMIN_IDS
        admin_id = ADMIN_IDS[0] if ADMIN_IDS else 0
        
        # Send photo to admin to get file_id
        sent_message = await bot.send_photo(
            chat_id=admin_id,
            photo=BytesIO(poster_data),
            caption=f"Poster for: {title} ({language})"
        )
        
        # Get file_id directly (Pyrogram 2.x)
        poster_file_id = sent_message.photo.file_id
        
        # Parse genres
        genres_list = [g.strip() for g in genres.split(",")]
        
        # Create movie document
        movie_doc = {
            "title": title,
            "year": year,
            "language": language,  # NEW: Save language
            "genres": genres_list,
            "quality": quality,
            "description": description,
            "lulu_stream_link": lulu_link,
            "htfilesharing_link": ht_link,
            "poster_file_id": poster_file_id,
            "views": 0,
            "added_by": "admin"
        }
        
        # Save to database
        result = await db.movies.insert_one(movie_doc)
        
        print(f"✅ Movie added: {title} ({language}) - ID: {result.inserted_id}")
        
        return templates.TemplateResponse("admin_add_movie.html", {
            "request": request,
            "success": f"✅ Movie '{title}' ({language}) added successfully!",
            "error": None
        })
        
    except Exception as e:
        print(f"❌ Error adding movie: {e}")
        import traceback
        traceback.print_exc()
        return templates.TemplateResponse("admin_add_movie.html", {
            "request": request,
            "success": None,
            "error": f"❌ Error: {str(e)}"
        })

# ============================================
# VIEW ALL MOVIES
# ============================================

async def admin_movies_page(request: Request):
    """View all movies page"""
    if not check_admin_auth(request):
        return RedirectResponse("/admin", status_code=302)
    
    # Get all movies
    movies = await db.movies.find().sort("_id", -1).to_list(length=None)
    
    return templates.TemplateResponse("admin_movies.html", {
        "request": request,
        "movies": movies
    })

# ============================================
# DELETE MOVIE
# ============================================

async def admin_delete_movie(request: Request, movie_id: str):
    """Delete a movie"""
    if not check_admin_auth(request):
        return JSONResponse({"success": False, "error": "Not authenticated"})
    
    try:
        # Delete from database
        result = await db.movies.delete_one({"_id": ObjectId(movie_id)})
        
        if result.deleted_count > 0:
            print(f"✅ Movie deleted: {movie_id}")
            return JSONResponse({"success": True, "message": "Movie deleted!"})
        else:
            return JSONResponse({"success": False, "error": "Movie not found"})
            
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return JSONResponse({"success": False, "error": str(e)})
        
