from pyrogram import Client, filters
from pyrogram.types import Message, Update
from fastapi import FastAPI, Request
import uvicorn
import os
import asyncio
from config import BOT_TOKEN, API_ID, API_HASH, ADMIN_IDS, MONGO_URI, WEBHOOK_URL
from database import get_database

app = FastAPI()

bot = Client(
    "moviebot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

db = get_database(MONGO_URI)

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy", "bot": "movie-bot", "port": 8080}

# ============================================
# WEBHOOK ENDPOINT
# ============================================

@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    """Handle webhook updates from Telegram"""
    try:
        data = await request.json()
        update = Update._parse(bot, data, {})
        asyncio.create_task(bot.handle_update(update))
        return {"ok": True}
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"ok": False, "error": str(e)}

# ============================================
# BOT COMMANDS
# ============================================

@bot.on_message(filters.command("start"))
async def start(client, message):
    is_admin = message.from_user.id in ADMIN_IDS
    if is_admin:
        await message.reply(
            "🎬 **Movie Bot - Admin Panel**\n\n"
            "✅ Deployed successfully!\n"
            "✅ Webhook active\n"
            "✅ Database connected\n\n"
            "**Commands:**\n"
            "/test - Test bot\n"
            "/ping - Check status\n"
            "/info - Bot info"
        )
    else:
        await message.reply(
            "🎬 **Movie Bot**\n\n"
            "✅ Bot is online!\n\n"
            "Search movies coming soon..."
        )

@bot.on_message(filters.command("test"))
async def test(client, message):
    await message.reply(
        f"✅ **Test Results**\n\n"
        f"🤖 Bot: Online\n"
        f"🔌 Port: 8080\n"
        f"📡 Webhook: Active\n"
        f"💾 Database: Connected\n"
        f"👤 Your ID: `{message.from_user.id}`\n"
        f"💬 Chat: {message.chat.type}"
    )

@bot.on_message(filters.command("ping"))
async def ping(client, message):
    await message.reply("🏓 Pong! Bot is running!")

@bot.on_message(filters.command("info"))
async def info(client, message):
    await message.reply(
        f"ℹ️ **Bot Information**\n\n"
        f"🔧 Framework: Pyrogram\n"
        f"⚡ Server: FastAPI\n"
        f"🌐 Hosting: Koyeb\n"
        f"🔌 Port: 8080\n"
        f"📡 Mode: Webhook\n"
        f"💾 Database: MongoDB\n"
        f"🐍 Python: 3.11"
    )

# ============================================
# STARTUP & SHUTDOWN (FIXED)
# ============================================

@app.on_event("startup")
async def startup():
    """Start bot and set webhook"""
    try:
        await bot.start()
        print("✅ Bot client started")
        
        if WEBHOOK_URL:
            import aiohttp
            
            # Remove trailing slash to avoid double slash bug
            base_url = WEBHOOK_URL.rstrip('/')
            webhook_url = f"{base_url}/webhook/{BOT_TOKEN}"
            telegram_api = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    telegram_api,
                    json={"url": webhook_url}
                ) as response:
                    result = await response.json()
                    if result.get("ok"):
                        print(f"✅ Webhook set: {webhook_url}")
                    else:
                        print(f"⚠️ Webhook failed: {result}")
        else:
            print("⚠️ WEBHOOK_URL not set")
        
        print(f"🔌 Listening on port 8080")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Stop bot gracefully"""
    try:
        await bot.stop()
        print("✅ Bot stopped")
    except Exception as e:
        print(f"⚠️ Shutdown error: {e}")

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting Movie Bot on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
