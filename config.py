import os
from dotenv import load_dotenv

load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS").split(",")]
MONGO_URI = os.getenv("MONGO_URI")

# Shortlink configuration (NEW)
SHORTLINK_API = os.getenv("SHORTLINK_API", "")
SHORTLINK_URL = os.getenv("SHORTLINK_URL", "")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

# Verification limits (NEW)
FREE_VIDEO_LIMIT = int(os.getenv("FREE_VIDEO_LIMIT", 3))
VERIFY_TOKEN_TIMEOUT = int(os.getenv("VERIFY_TOKEN_TIMEOUT", 604800))  # 7 days

print("✅ Config loaded")
