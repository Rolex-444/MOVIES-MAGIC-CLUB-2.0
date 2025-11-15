import os
from dotenv import load_dotenv

load_dotenv()

# =========================
# BOT/TELEGRAM CONFIG
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# List of admin user IDs (comma-separated in .env)
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS").split(",")]

# =========================
# DATABASE/MONGO CONFIG
# =========================

MONGO_URI = os.getenv("MONGO_URI")

# =========================
# ADMIN DASHBOARD LOGIN
# =========================

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-12345-change-this")

# =========================
# SHORTLINK VERIFICATION SYSTEM CONFIG
# =========================

# Shortlink provider settings (change for your service!)
SHORTLINK_URL = os.getenv("SHORTLINK_URL", "https://yourshortlinkservice.com")
SHORTLINK_API = os.getenv("SHORTLINK_API", "your_api_key_here")

# How many free movies per user per day before verification is needed
VERIFICATION_FREE_LIMIT = int(os.getenv("VERIFICATION_FREE_LIMIT", "3"))

# At what hour to reset (0 = midnight, 24hr format, UTC)
VERIFICATION_RESET_HOUR = int(os.getenv("VERIFICATION_RESET_HOUR", "0"))

# How long the verification unlock is valid (hours)
VERIFICATION_PERIOD_HOURS = int(os.getenv("VERIFICATION_PERIOD_HOURS", "24"))

# Tutorial/help button for users
VERIFICATION_TUTORIAL_LINK = os.getenv(
    "VERIFICATION_TUTORIAL_LINK",
    "https://t.me/Sr_Movie_Links/52"
)
VERIFICATION_TUTORIAL_NAME = os.getenv(
    "VERIFICATION_TUTORIAL_NAME",
    "HOW TO VERIFY"
)

# Enable/disable verification system globally (set "false" to turn off)
VERIFICATION_ON = os.getenv("VERIFICATION_ON", "true").lower() == "true"

# =========================
# WEB/DEPLOYED URLS AND REQUEST GROUP
# =========================

# Your Koyeb or deployed website base URL
BASE_URL = os.getenv("BASE_URL", "https://your-app-url.koyeb.app")

# Telegram group/channel for requests
REQUEST_GROUP = os.getenv("REQUEST_GROUP", "https://t.me/movies_magic_club3")

print("✅ Config loaded")
