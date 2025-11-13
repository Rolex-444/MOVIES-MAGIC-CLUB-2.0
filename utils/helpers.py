import aiohttp
import asyncio
from config import BOT_TOKEN

async def send_message(chat_id, text, parse_mode="Markdown"):
    """Send text message - WITH RETRY"""
    for attempt in range(2):  # Try twice
        try:
            timeout = aiohttp.ClientTimeout(total=30)  # Increased to 30 seconds
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode
                    }
                ) as response:
                    result = await response.json()
                    print(f"✅ Message sent ({response.status})")
                    return result
        except asyncio.TimeoutError:
            print(f"⚠️ Timeout attempt {attempt + 1}/2")
            if attempt == 0:
                await asyncio.sleep(1)  # Wait 1 sec before retry
                continue
            print(f"❌ Message timeout after retries")
            return None
        except Exception as e:
            print(f"❌ Send error: {type(e).__name__}: {str(e)}")
            return None

async def send_photo(chat_id, photo, caption, parse_mode="Markdown", reply_markup=None):
    """Send photo - WITH RETRY"""
    for attempt in range(2):
        try:
            payload = {
                "chat_id": chat_id,
                "photo": photo,
                "caption": caption,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                    json=payload
                ) as response:
                    result = await response.json()
                    print(f"✅ Photo sent ({response.status})")
                    return result
        except asyncio.TimeoutError:
            print(f"⚠️ Photo timeout attempt {attempt + 1}/2")
            if attempt == 0:
                await asyncio.sleep(1)
                continue
            print(f"❌ Photo timeout after retries")
            return None
        except Exception as e:
            print(f"❌ Photo error: {type(e).__name__}: {str(e)}")
            return None

async def set_webhook(webhook_url):
    """Set webhook"""
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
                json={"url": webhook_url}
            ) as response:
                return await response.json()
    except Exception as e:
        print(f"❌ Webhook error: {type(e).__name__}")
        return None

async def close_session():
    """Dummy for compatibility"""
    pass
                
