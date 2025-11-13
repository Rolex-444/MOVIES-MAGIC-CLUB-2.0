from fastapi import FastAPI, Request
import uvicorn
import os
from config import WEBHOOK_URL
from database import get_database
from handlers.webhook import process_webhook
from utils.helpers import set_webhook

app = FastAPI()
db = get_database()

# Support GET and HEAD for health check
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

@app.on_event("startup")
async def startup():
    """Initialize bot"""
    print("✅ Bot initialized")
    
    if WEBHOOK_URL:
        from config import BOT_TOKEN
        base_url = WEBHOOK_URL.rstrip('/')
        webhook_url = f"{base_url}/webhook/{BOT_TOKEN}"
        result = await set_webhook(webhook_url)
        
        if result.get("ok"):
            print(f"✅ Webhook set: {webhook_url}")
        else:
            print(f"⚠️ Webhook failed: {result}")
    
    print("🔌 Listening on port 8080")

@app.on_event("shutdown")
async def shutdown():
    print("✅ Bot stopped")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print("🚀 Starting Movie Bot")
    uvicorn.run(app, host="0.0.0.0", port=port)
        
