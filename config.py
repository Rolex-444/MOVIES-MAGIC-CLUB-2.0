import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")

# Admin configuration
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS").split(",")]

# Database configuration
MONGO_URI = os.getenv("MONGO_URI")

# Print config status (for debugging)
print("✅ Configuration loaded")
print(f"   Bot Token: {BOT_TOKEN[:10]}...")
print(f"   Admin IDs: {ADMIN_IDS}")
print(f"   MongoDB: {'Connected' if MONGO_URI else 'Not configured'}")
