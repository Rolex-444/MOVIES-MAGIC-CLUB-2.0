import aiohttp
from config import BOT_TOKEN

# Reuse session instead of creating new one each time
_session = None

async def get_session():
    """Get or create aiohttp session"""
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session

async def send_message(chat_id, text, parse_mode="Markdown"):
    """Send text message via Bot API"""
    session = await get_session()
    await session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
    )

async def send_photo(chat_id, photo, caption, parse_mode="Markdown"):
    """Send photo with caption via Bot API"""
    session = await get_session()
    await session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        json={
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": parse_mode
        }
    )

async def set_webhook(webhook_url):
    """Set Telegram webhook"""
    session = await get_session()
    async with session.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
        json={"url": webhook_url}
    ) as response:
        return await response.json()

async def close_session():
    """Close aiohttp session"""
    global _session
    if _session and not _session.closed:
        await _session.close()
    
