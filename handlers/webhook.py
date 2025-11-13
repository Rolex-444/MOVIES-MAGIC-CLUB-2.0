from handlers.commands import cmd_start, cmd_test, cmd_ping, cmd_info
from handlers.admin import (
    cmd_addmovie, cmd_cancel, cmd_listmovies,
    handle_upload_steps, is_user_uploading
)
from handlers.search import search_movies
from config import ADMIN_IDS

async def process_webhook(update):
    """Process incoming webhook update"""
    if "message" not in update:
        return {"ok": True}
    
    msg = update["message"]
    user_id = msg["from"]["id"]
    chat_id = msg["chat"]["id"]
    
    # Check if user is in upload process (admin)
    if is_user_uploading(user_id):
        await handle_upload_steps(msg, user_id, chat_id)
        return {"ok": True}
    
    # Handle commands
    if "text" in msg and msg["text"].startswith("/"):
        command = msg["text"].split()[0].replace("/", "").lower()
        
        # Public commands
        if command == "start":
            await cmd_start(msg, user_id, chat_id)
        elif command == "test":
            await cmd_test(msg, user_id, chat_id)
        elif command == "ping":
            await cmd_ping(msg, user_id, chat_id)
        elif command == "info":
            await cmd_info(msg, user_id, chat_id)
        
        # Admin commands
        elif user_id in ADMIN_IDS:
            if command == "addmovie":
                await cmd_addmovie(msg, user_id, chat_id)
            elif command == "cancel":
                await cmd_cancel(msg, user_id, chat_id)
            elif command == "listmovies":
                await cmd_listmovies(msg, user_id, chat_id)
    
    # Handle text messages (movie search)
    elif "text" in msg:
        query = msg["text"].strip()
        # Search for movies
        await search_movies(msg, user_id, chat_id, query)
    
    return {"ok": True}
    
