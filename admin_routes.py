from fastapi import Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_database
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from bson import ObjectId
from pyrogram import Client
from config import BOT_TOKEN, API_ID, API_HASH

templates = Jinja2Templates(directory="templates")
db = get_database()

# Initialize bot for uploading posters
bot = Client("poster_uploader", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# ============================================
# ADMIN LOGIN
# ============================================

async def admin_login_page(request: Request):
    """Show admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request})

async def admin_login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    """Handle admin login"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse("/admin/dashboard", status_code=302)
    
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "error": "Invalid credentials!"
    })

async def admin_logout(request: Request):
    """Logout admin"""
    request.session.clear()
    return RedirectResponse("/admin")

# ============================================
# ADMIN DASHBOARD
# ============================================

async def admin_dashboard(request: Request):
    """Show admin dashboard"""
    if not request.session.get("admin"):
        return RedirectResponse("/admin")
    
    # Get stats
    total_movies = await db.movies.count_documents({})
    total_users = await db.users.count_documents({})
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "total_movies": total_movies,
        "total_users": total_users
    })

# ============================================
# ADD MOVIE
# ============================================

async def admin_add_movie_page(request: Request):
    """Show add movie page"""
    if not request.session.get("admin"):
        return RedirectResponse("/admin")
    
    return templates.TemplateResponse("admin_add_movie.html", {"request": request})

async def admin_add_movie_post(
    request: Request,
    title: str = Form(...),
    year: int = Form(...),
    language: str = Form(...),
    quality: str = Form(...),
    genres: str = Form(...),
    description: str = Form(...),
    lulu_link: str = Form(...),
    ht_link: str = Form(...),
    poster: UploadFile = File(...)
):
    """Handle add movie form submission"""
    if not request.session.get("admin"):
        return RedirectResponse("/admin")
    
    try:
        # Upload poster to Telegram
        await bot.start()
        
        # Read poster file
        poster_content = await poster.read()
        
        # Upload to Telegram and get file_id
        message = await bot.send_photo(
            chat_id="me",  # Send to saved messages
            photo=poster_content,
            caption=f"Poster for {title}"
        )
        
        poster_file_id = message.photo.file_id
        
        await bot.stop()
        
        # Parse genres
        genres_list = [g.strip() for g in genres.split(",")]
        
        # Insert movie into database
        movie_data = {
            "title": title,
            "year": year,
            "language": language,
            "quality": quality,
            "genres": genres_list,
            "description": description,
            "lulu_stream_link": lulu_link,
            "htfilesharing_link": ht_link,
            "poster_file_id": poster_file_id,
            "views": 0
        }
        
        await db.movies.insert_one(movie_data)
        
        return templates.TemplateResponse("admin_add_movie.html", {
            "request": request,
            "success": f"✅ Movie '{title}' added successfully!"
        })
        
    except Exception as e:
        return templates.TemplateResponse("admin_add_movie.html", {
            "request": request,
            "error": f"❌ Error: {str(e)}"
        })

# ============================================
# VIEW ALL MOVIES
# ============================================

async def admin_movies_page(request: Request):
    """Show all movies"""
    if not request.session.get("admin"):
        return RedirectResponse("/admin")
    
    # Get all movies
    movies = await db.movies.find().sort("_id", -1).to_list(length=100)
    
    return templates.TemplateResponse("admin_movies.html", {
        "request": request,
        "movies": movies
    })

# ============================================
# DELETE MOVIE
# ============================================

async def admin_delete_movie(request: Request, movie_id: str):
    """Delete a movie"""
    if not request.session.get("admin"):
        return RedirectResponse("/admin")
    
    try:
        await db.movies.delete_one({"_id": ObjectId(movie_id)})
        return RedirectResponse("/admin/movies", status_code=302)
    except:
        return RedirectResponse("/admin/movies", status_code=302)
    
