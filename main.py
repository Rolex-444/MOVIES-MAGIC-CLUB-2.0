from fastapi import FastAPI, Request
import uvicorn
import os
import asyncio
from config import WEBHOOK_URL
from database import get_database
from handlers.webhook import process_webhook

app = FastAPI()
db = get_database()

@app.get("/")
@app.head("/")
@app.get("/health")
@app.head("/health")
async def health():
    return {"status": "healthy", "bot": "movie-bot"}

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    """Handle Telegram webhook"""
    try:
        update = await request.json()
        return await process_webhook(update)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return {"ok": False, "error": str(e)}

async def set_webhook_background():
    """Set webhook in background (non-blocking)"""
    await asyncio.sleep(2)  # Wait for server to start
    
    if WEBHOOK_URL:
        try:
            from config import BOT_TOKEN
            import aiohttp
            
            base_url = WEBHOOK_URL.rstrip('/')
            webhook_url = f"{base_url}/webhook/{BOT_TOKEN}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                    json={"url": webhook_url},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result = await response.json()
                    if result.get("ok"):
                        print(f"✅ Webhook set: {webhook_url}")
                    else:
                        print(f"⚠️ Webhook failed: {result}")
        except Exception as e:
            print(f"⚠️ Webhook setup error: {e}")

@app.on_event("startup")
async def startup():
    """Initialize bot - NON-BLOCKING"""
    print("✅ Bot initialized")
    print("🔌 Listening on port 8080")
    
    # Set webhook in background task (don't await it!)
    asyncio.create_task(set_webhook_background())

@app.on_event("shutdown")
async def shutdown():
    print("✅ Bot stopped")

# This runs with uvicorn command
