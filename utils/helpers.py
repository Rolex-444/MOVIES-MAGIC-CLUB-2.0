import aiohttp
from config import BOT_TOKEN

# Global session - reused for all requests
_session = None

async def get_session():
    """Get or create persistent aiohttp session"""
    global _session
    if _session is None or _session.closed:
        timeout = aiohttp.ClientTimeout(total=10)
        _session = aiohttp.ClientSession(timeout=timeout)
    return _session

async def send_message(chat_id, text, parse_mode="Markdown"):
    """Send text message via Bot API - FAST"""
    session = await get_session()
    try:
        async with session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
        ) as response:
            return await response.json()
    except Exception as e:
        print(f"❌ Send message error: {e}")
        return None

async def send_photo(chat_id, photo, caption, parse_mode="Markdown", reply_markup=None):
    """Send photo with caption via Bot API - FAST"""
    session = await get_session()
    try:
        payload = {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
            
        async with session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
            json=payload
        ) as response:
            return await response.json()
    except Exception as e:
        print(f"❌ Send photo error: {e}")
        return None

async def set_webhook(webhook_url):
    """Set Telegram webhook"""
    session = await get_session()
    try:
        async with session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={"url": webhook_url}
        ) as response:
            return await response.json()
    except Exception as e:
        print(f"❌ Set webhook error: {e}")
        return None

async def close_session():
    """Close aiohttp session on shutdown"""
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None
        
