import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS").split(",")]
MONGO_URI = os.getenv("MONGO_URI")

print("✅ Config loaded")
