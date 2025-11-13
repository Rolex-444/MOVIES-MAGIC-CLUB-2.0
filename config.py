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

# Shortlink configuration
SHORTLINK_API = os.getenv("SHORTLINK_API", "")
SHORTLINK_URL = os.getenv("SHORTLINK_URL", "")

# Verification limits
FREE_VIDEO_LIMIT = 3  # Free movies before verification
VERIFY_TOKEN_TIMEOUT = 604800  # 7 days in seconds

# Bot username (for verification links)
BOT_USERNAME = os.getenv("BOT_USERNAME", "")

print("✅ Config loaded")
