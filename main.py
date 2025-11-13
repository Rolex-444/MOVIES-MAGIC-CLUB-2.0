from pyrogram import Client, filters
from pyrogram.types import Message
from config import BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS, MONGO_URI
from database import get_database

# Initialize bot
print("🚀 Starting Movie Bot...")

app = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize database
db = get_database(MONGO_URI)

print("✅ Bot initialized")
print(f"👮 Admin IDs: {ADMIN_IDS}")

# ============================================
# BASIC COMMANDS (For Testing)
# ============================================

@app.on_message(filters.command("start") & filters.private)
async def start_command(client: Client, message: Message):
    """Start command - Welcome message"""
    await message.reply(
        "🎬 **Welcome to Movie Bot!**\n\n"
        "✅ Bot is working!\n"
        "✅ Database connected!\n\n"
        "👨‍💼 **Admin Commands:**\n"
        "/test - Test bot\n"
        "/ping - Check if bot is alive\n\n"
        "More features coming soon..."
    )
    print(f"✅ /start command from {message.from_user.first_name}")

@app.on_message(filters.command("test"))
async def test_command(client: Client, message: Message):
    """Test command - Check if bot works"""
    await message.reply(
        "✅ **Bot is working perfectly!**\n\n"
        f"👤 Your name: {message.from_user.first_name}\n"
        f"🆔 Your ID: {message.from_user.id}\n"
        f"💬 Chat type: {message.chat.type}\n\n"
        "Everything is operational! 🚀"
    )
    print(f"✅ /test command from {message.from_user.first_name}")

@app.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    """Ping command - Check bot response time"""
    await message.reply("🏓 Pong! Bot is alive and responding!")
    print(f"✅ /ping command from {message.from_user.first_name}")

@app.on_message(filters.command("admin") & filters.user(ADMIN_IDS))
async def admin_command(client: Client, message: Message):
    """Admin-only command"""
    await message.reply(
        "👨‍💼 **Admin Panel**\n\n"
        "✅ You are verified as admin!\n\n"
        "Available admin commands:\n"
        "• /addmovie - Add new movie (coming in next step)\n"
        "• /listmovies - View all movies (coming in next step)\n"
        "• /stats - View statistics (coming in next step)"
    )
    print(f"✅ Admin access verified for {message.from_user.first_name}")

# ============================================
# BOT START
# ============================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🎬 MOVIE BOT STARTING...")
    print("="*50 + "\n")
    
    print("📡 Mode: LOCAL TESTING (Polling)")
    print("💡 Tip: Press Ctrl+C to stop\n")
    
    # Run bot with polling (for local testing)
    app.run()
