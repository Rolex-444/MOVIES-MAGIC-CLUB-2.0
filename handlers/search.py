from utils.helpers import send_message, send_photo
from database import get_database
from config import BOT_TOKEN
import aiohttp

db = get_database()

async def search_movies(msg, user_id, chat_id, query):
    """Search movies by title"""
    print(f"🔍 Search query: {query} from user {user_id}")
    
    # Search in database
    movies = await db.search_movies(query)
    
    if not movies:
        await send_message(
            chat_id,
            f"😕 **No results found for:** `{query}`\n\n"
            "Try another movie name or check spelling!"
        )
        return
    
    # Show results
    if len(movies) == 1:
        # Single result - show full movie card
        await show_movie_card(chat_id, movies[0], user_id)
    else:
        # Multiple results - show list
        text = f"🔍 **Found {len(movies)} movies:**\n\n"
        for i, movie in enumerate(movies, 1):
            text += f"{i}. **{movie['title']}** ({movie['year']}) - {movie.get('quality', 'HD')}\n"
        
        text += f"\n💡 Type movie name to see details"
        await send_message(chat_id, text)
        
        # Show first result automatically
        await show_movie_card(chat_id, movies[0], user_id)

async def show_movie_card(chat_id, movie, user_id):
    """Display single movie with poster and buttons"""
    
    # Check if user needs verification
    needs_verify = await db.needs_verification(user_id)
    
    if needs_verify:
        # User needs to verify first
        await show_verification_required(chat_id, user_id, movie)
        return
    
    # User can watch - show movie card
    title = movie['title']
    year = movie.get('year', 'N/A')
    genres = ', '.join(movie.get('genres', []))
    quality = movie.get('quality', 'HD')
    description = movie.get('description', 'No description available')
    poster = movie.get('poster_file_id')
    lulu_link = movie.get('lulu_stream_link')
    ht_link = movie.get('htfilesharing_link')
    
    caption = (
        f"🎬 **{title}** ({year})\n\n"
        f"🎭 **Genre:** {genres}\n"
        f"📺 **Quality:** {quality}\n\n"
        f"📝 **About:**\n{description}\n\n"
        f"👀 **Views:** {movie.get('views', 0)}\n\n"
        f"⬇️ Choose your option:"
    )
    
    # Create inline keyboard with buttons
    buttons = {
        "inline_keyboard": [
            [
                {"text": "🎬 Watch Now", "url": lulu_link},
                {"text": "⬇️ Download", "url": ht_link}
            ]
        ]
    }
    
    # Send movie card
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            json={
                "chat_id": chat_id,
                "photo": poster,
                "caption": caption,
                "parse_mode": "Markdown",
                "reply_markup": buttons
            }
        )
    
    # Increment user's view count
    await db.increment_video_attempts(user_id)
    print(f"✅ Movie card sent: {title}")

async def show_verification_required(chat_id, user_id, movie):
    """Show verification message with shortlink"""
    from utils.verification import generate_verify_token, create_universal_shortlink
    from config import BOT_USERNAME
    
    # Generate verification token
    token = generate_verify_token()
    await db.set_verification_token(user_id, token)
    
    # Create verification URL
    verify_url = f"https://t.me/{BOT_USERNAME}?start=verify_{token}"
    
    # Create shortlink
    shortlink = create_universal_shortlink(verify_url)
    
    if not shortlink:
        shortlink = verify_url
    
    # Get user stats
    stats = await db.get_user_stats(user_id)
    attempts = stats.get('video_attempts', 0)
    
    text = (
        f"🔒 **Verification Required**\n\n"
        f"You've watched **{attempts} free movies** today!\n\n"
        f"To continue watching **{movie['title']}**, please verify:\n\n"
        f"1️⃣ Click the button below\n"
        f"2️⃣ Complete the verification\n"
        f"3️⃣ Come back and watch unlimited movies!\n\n"
        f"✨ **Valid for 7 days** after verification"
    )
    
    buttons = {
        "inline_keyboard": [
            [{"text": "✅ Verify Now", "url": shortlink}],
            [{"text": "❓ Why Verification?", "callback_data": "why_verify"}]
        ]
    }
    
    async with aiohttp.ClientSession() as session:
        await session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_markup": buttons
            }
        )
    
    print(f"🔒 Verification required for user {user_id}")
