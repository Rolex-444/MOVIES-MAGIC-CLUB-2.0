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

# Admin Dashboard Credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-12345-change-this")

# --- Shortlink Verification Settings ---
SHORTLINK_URL = "https://yourshortlinkservice.com"   # e.g. https://gplinks.co (required)
SHORTLINK_API = "your_api_key_here"                  # your service API key

VERIFICATION_FREE_LIMIT = 3         # Free movie accesses per user per day
VERIFICATION_RESET_HOUR = 0         # Hour (0 = midnight, 24hr format)
VERIFICATION_PERIOD_HOURS = 24      # After verifying, how long should unlimited access last
VERIFICATION_TUTORIAL_LINK = "https://t.me/Sr_Movie_Links/52"  # Your tutorial link


# Request Group Link (NEW - Phase 2)
REQUEST_GROUP = "https://t.me/movies_magic_club3"

print("✅ Config loaded")
