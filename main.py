from pyrogram import Client, filters
from pyrogram.types import Message
from fastapi import FastAPI, Request
import uvicorn
import os
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

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy", "bot": "movie-bot", "port": 8080}

@app.post(f"/webhook/{BOT_TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = await bot.parse_update(data)
    await bot.handle_update(update)
    return {"ok": True}

@bot.on_message(filters.command("start"))
async def start(client, message):
    is_admin = message.from_user.id in ADMIN_IDS
    if is_admin:
        await message.reply(
            "🎬 **Movie Bot - Admin**\n\n"
            "✅ Deployed on Koyeb\n"
            "✅ Port 8080\n"
            "✅ Webhook active\n\n"
            "Commands:\n"
            "/test - Test bot\n"
            "/ping - Check status"
        )
    else:
        await message.reply("🎬 **Movie Bot**\n\n✅ Bot is working!")

@bot.on_message(filters.command("test"))
async def test(client, message):
    await message.reply(
        f"✅ **Test Results**\n\n"
        f"🤖 Bot: Online\n"
        f"🔌 Port: 8080\n"
        f"💾 Database: Connected\n"
        f"👤 Your ID: {message.from_user.id}\n"
        f"💬 Chat: {message.chat.type}"
    )

@bot.on_message(filters.command("ping"))
async def ping(client, message):
    await message.reply("🏓 Pong! Bot is running on Koyeb!")

@app.on_event("startup")
async def startup():
    await bot.start()
    webhook_url = f"{WEBHOOK_URL}/webhook/{BOT_TOKEN}"
    await bot.set_webhook(webhook_url)
    print(f"✅ Bot started with webhook: {webhook_url}")
    print(f"🔌 Listening on port 8080")

@app.on_event("shutdown")
async def shutdown():
    await bot.stop()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"🚀 Starting Movie Bot on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
        
