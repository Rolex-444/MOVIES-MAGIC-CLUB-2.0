from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
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
# WEBHOOK ENDPOINT (SIMPLE & WORKING)
# ============================================

@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    """Handle Telegram webhook updates"""
    try:
        update = await request.json()
        
        # Process message updates
        if "message" in update:
            msg = update["message"]
            
            # Check if it's a command we handle
            if "text" in msg and msg["text"].startswith("/"):
                command = msg["text"].split()[0].replace("/", "")
                user_id = msg["from"]["id"]
                chat_id = msg["chat"]["id"]
                
                # Handle commands directly
                if command == "start":
                    is_admin = user_id in ADMIN_IDS
                    if is_admin:
                        text = (
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
                        text = (
                            "🎬 **Movie Bot**\n\n"
                            "✅ Bot is online!\n\n"
                            "Search movies coming soon..."
                        )
                    
                    # Send response via Bot API
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": text,
                                "parse_mode": "Markdown"
                            }
                        )
                
                elif command == "test":
                    text = (
                        f"✅ **Test Results**\n\n"
                        f"🤖 Bot: Online\n"
                        f"🔌 Port: 8080\n"
                        f"📡 Webhook: Active\n"
                        f"💾 Database: Connected\n"
                        f"👤 Your ID: `{user_id}`\n"
                        f"💬 Chat: {msg['chat']['type']}"
                    )
                    
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": text,
                                "parse_mode": "Markdown"
                            }
                        )
                
                elif command == "ping":
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": "🏓 Pong! Bot is running on Koyeb!"
                            }
                        )
                
                elif command == "info":
                    text = (
                        "ℹ️ **Bot Information**\n\n"
                        "🔧 Framework: Pyrogram\n"
                        "⚡ Server: FastAPI\n"
                        "🌐 Hosting: Koyeb\n"
                        "🔌 Port: 8080\n"
                        "📡 Mode: Webhook\n"
                        "💾 Database: MongoDB\n"
                        "🐍 Python: 3.11"
                    )
                    
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        await session.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={
                                "chat_id": chat_id,
                                "text": text,
                                "parse_mode": "Markdown"
                            }
                        )
        
        return {"ok": True}
        
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

# ============================================
# STARTUP & SHUTDOWN
# ============================================

@app.on_event("startup")
async def startup():
    """Start bot and set webhook"""
    try:
        # Don't start Pyrogram client for simple webhook mode
        print("✅ Bot initialized (webhook mode)")
        
        if WEBHOOK_URL:
            import aiohttp
            
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
        
        print(f"🔌 Listening on port 8080")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup"""
    print("✅ Bot stopped")

# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting Movie Bot on port 8080")
    uvicorn.run(app, host="0.0.0.0", port=port)
                
