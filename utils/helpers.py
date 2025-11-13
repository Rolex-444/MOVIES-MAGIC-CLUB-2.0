import aiohttp
from config import BOT_TOKEN

async def send_message(chat_id, text, parse_mode="Markdown"):
    """Send text message via Bot API"""
    async with aiohttp.ClientSession() as session:
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
    async with aiohttp.ClientSession() as session:
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
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
            json={"url": webhook_url}
        ) as response:
            return await response.json()
