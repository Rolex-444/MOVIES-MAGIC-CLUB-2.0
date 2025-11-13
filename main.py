from fastapi import FastAPI, Request
import uvicorn
import os
import asyncio
from config import WEBHOOK_URL
from database import get_database
from handlers.webhook import process_webhook

app = FastAPI()

# Initialize database
db = get_database()

@app.get("/")
@app.head("/")
@app.get("/health")
@app.head("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "movie-bot"}

@app.post("/webhook/{token}")
async def webhook(token: str, request: Request):
    """Handle Telegram webhook updates"""
    try:
        update = await request.json()
        return await process_webhook(update)
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

async def set_webhook_background():
    """Set webhook in background (non-blocking)"""
    await asyncio.sleep(3)  # Wait for server to start
    
    if WEBHOOK_URL:
        try:
            from config import BOT_TOKEN
            from utils.helpers import set_webhook
            
            base_url = WEBHOOK_URL.rstrip('/')
            webhook_url = f"{base_url}/webhook/{BOT_TOKEN}"
            
            result = await set_webhook(webhook_url)
            
            if result and result.get("ok"):
                print(f"✅ Webhook set: {webhook_url}")
            else:
                print(f"⚠️ Webhook failed: {result}")
        except Exception as e:
            print(f"⚠️ Webhook setup error: {e}")

@app.on_event("startup")
async def startup():
    """Initialize bot on startup - NON-BLOCKING"""
    print("✅ Bot initialized")
    print("🔌 Listening on port 8080")
    
    # Set webhook in background task (non-blocking)
    asyncio.create_task(set_webhook_background())

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    try:
        from utils.helpers import close_session
        await close_session()
        print("✅ Bot stopped gracefully")
    except Exception as e:
        print(f"⚠️ Shutdown error: {e}")
                
