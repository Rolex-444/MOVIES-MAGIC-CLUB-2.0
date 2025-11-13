from utils.helpers import send_message
from config import ADMIN_IDS
from database import get_database

db = get_database()

async def cmd_start(msg, user_id, chat_id):
    """Handle /start command"""
    is_admin = user_id in ADMIN_IDS
    if is_admin:
        text = (
            "🎬 **Movie Bot - Admin Panel**\n\n"
            "✅ Bot online\n"
            "✅ Database connected\n\n"
            "**Admin Commands:**\n"
            "/addmovie - Add new movie\n"
            "/listmovies - View all movies\n"
            "/test - Test bot\n"
            "/ping - Check status\n"
            "/info - Bot info"
        )
    else:
        text = (
            "🎬 **Movie Bot**\n\n"
            "✅ Bot is online!\n\n"
            "Type movie name to search..."
        )
    await send_message(chat_id, text)

async def cmd_test(msg, user_id, chat_id):
    """Handle /test command"""
    total_movies = await db.movies.count_documents({})
    text = (
        f"✅ **Test Results**\n\n"
        f"🤖 Bot: Online\n"
        f"🔌 Port: 8080\n"
        f"📡 Webhook: Active\n"
        f"💾 Database: Connected\n"
        f"🎬 Movies: {total_movies}\n"
        f"👤 Your ID: `{user_id}`\n"
        f"💬 Chat: {msg['chat']['type']}"
    )
    await send_message(chat_id, text)

async def cmd_ping(msg, user_id, chat_id):
    """Handle /ping command"""
    await send_message(chat_id, "🏓 Pong! Bot is running!")

async def cmd_info(msg, user_id, chat_id):
    """Handle /info command"""
    text = (
        "ℹ️ **Bot Information**\n\n"
        "🔧 Framework: FastAPI\n"
        "🌐 Hosting: Koyeb\n"
        "🔌 Port: 8080\n"
        "📡 Mode: Webhook\n"
        "💾 Database: MongoDB\n"
        "🐍 Python: 3.11"
    )
    await send_message(chat_id, text)
