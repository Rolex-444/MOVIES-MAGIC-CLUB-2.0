from fastapi import Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from bson import ObjectId
import io  # kept if you later re-enable posters

from database import get_database
from config import ADMIN_USERNAME, ADMIN_PASSWORD

templates = Jinja2Templates(directory="templates")
db = get_database()

# ============================================
# ADMIN LOGIN
# ============================================

async def admin_login_page(request: Request):
    """Show admin login page"""
    return templates.TemplateResponse("admin_login.html", {"request": request})


async def admin_login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    """Handle admin login"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse("/admin/dashboard", status_code=302)

    return templates.TemplateResponse(
        "admin_login.html",
        {
            "request": request,
            "error": "Invalid username or password",
        },
    )


async def admin_logout(request: Request):
    """Admin logout"""
    request.session.clear()
    return RedirectResponse("/admin", status_code=302)


# ============================================
# ADMIN DASHBOARD / MOVIE LIST
# ============================================

async def admin_dashboard(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/admin")

    total_movies = await db.movies.count_documents({})

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {
            "request": request,
            "total_movies": total_movies,
        },
    )


async def admin_movies_page(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/admin")

    movies = await db.movies.find().sort("created_at", -1).to_list(length=200)

    return templates.TemplateResponse(
        "admin_movies.html",
        {
            "request": request,
            "movies": movies,
        },
    )


# ============================================
# ADD MOVIE (NO POSTER UPLOAD)
# ============================================

async def admin_add_movie_page(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse("/admin")

    return templates.TemplateResponse("admin_add_movie.html", {"request": request})


async def admin_add_movie_post(
    request: Request,
    title: str = Form(...),
    year: str = Form(...),
    language: str = Form(...),
    quality: str = Form(...),
    genres: str = Form(""),
    description: str = Form(""),
    lulu_link: str = Form(""),
    ht_link: str = Form(""),
    poster: UploadFile = File(None),
):
    if not request.session.get("admin"):
        return RedirectResponse("/admin")

    try:
        # Poster upload is disabled for now:
        poster_file_id = None

        movie_doc = {
            "title": title.strip(),
            "year": year.strip(),
            "language": language.strip(),
            "quality": quality.strip(),
            "genres": [g.strip() for g in genres.split(",") if g.strip()],
            "description": description.strip(),
            "lulu_link": lulu_link.strip(),
            "ht_link": ht_link.strip(),
            "poster_file_id": poster_file_id,
        }

        await db.movies.insert_one(movie_doc)

        return RedirectResponse("/admin/movies", status_code=302)

    except Exception as e:
        return templates.TemplateResponse(
            "admin_add_movie.html",
            {
                "request": request,
                "error": f"Error: {e}",
                "form_title": title,
                "form_year": year,
                "form_language": language,
                "form_quality": quality,
                "form_genres": genres,
                "form_description": description,
                "form_lulu_link": lulu_link,
                "form_ht_link": ht_link,
            },
        )


# ============================================
# DELETE MOVIE
# ============================================

async def admin_delete_movie(request: Request, movie_id: str):
    if not request.session.get("admin"):
        return RedirectResponse("/admin")

    try:
        await db.movies.delete_one({"_id": ObjectId(movie_id)})
    except Exception:
        pass

    return RedirectResponse("/admin/movies", status_code=302)
    
