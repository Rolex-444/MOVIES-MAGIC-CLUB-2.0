# database.py

from motor.motor_asyncio import AsyncIOMotorClient
import logging

from config import MONGO_URI

logger = logging.getLogger(__name__)

_client = None
_db = None


def get_database():
    """
    Return a singleton Motor database instance.

    Usage in your code:

        from database import get_database
        db = get_database()

        db.movies         # movie documents
        db.users          # Telegram users
        db.verif_users    # daily limit + verified status
        db.verif_tokens   # shortlink verification tokens
    """
    global _client, _db

    if _db is None:
        if not MONGO_URI:
            raise RuntimeError("MONGO_URI is not set in environment or config.py")

        # Create the MongoDB client
        _client = AsyncIOMotorClient(MONGO_URI)

        # Use a single database; rename "moviebot" if you like
        _db = _client.get_database("moviebot")

        # Ensure main collections exist on first use
        _db.movies
        _db.users
        _db.verif_users
        _db.verif_tokens

        logger.info("✅ MongoDB connected and database 'moviebot' is ready")

    return _db
    
