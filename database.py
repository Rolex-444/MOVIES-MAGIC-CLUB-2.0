from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import logging
from config import MONGO_URI, FREE_VIDEO_LIMIT, VERIFY_TOKEN_TIMEOUT

logger = logging.getLogger(__name__)

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client.moviebot
        self.movies = self.db.movies
        self.users = self.db.users
        print("✅ Database connected")
    
    # Movie methods
    async def add_movie(self, movie_data):
        movie_data['added_at'] = datetime.now(IST)
        movie_data['views'] = 0
        result = await self.movies.insert_one(movie_data)
        return result.inserted_id
    
    async def search_movies(self, query):
        results = await self.movies.find({
            "title": {"$regex": query, "$options": "i"}
        }).limit(10).to_list(length=10)
        return results
    
    async def get_all_movies(self, limit=100):
        movies = await self.movies.find().sort("added_at", -1).limit(limit).to_list(length=limit)
        return movies
    
    async def get_movie_by_id(self, movie_id):
        from bson import ObjectId
        return await self.movies.find_one({"_id": ObjectId(movie_id)})
    
    # User verification methods
    def get_today_start(self):
        """Get today's 12:00 AM IST"""
        now_ist = datetime.now(IST)
        return now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    
    async def get_user_data(self, user_id: int) -> Optional[Dict]:
        """Get user data, create if doesn't exist"""
        user = await self.users.find_one({"user_id": user_id})
        if not user:
            now_ist = datetime.now(IST)
            new_user = {
                "user_id": user_id,
                "joined_date": now_ist,
                "video_attempts": 0,
                "is_verified": False,
                "verify_token": None,
                "token_expiry": None,
                "verify_expiry": None,
                "last_reset": now_ist
            }
            await self.users.insert_one(new_user)
            logger.info(f"✅ Created new user: {user_id}")
            return new_user
        return user
    
    async def reset_daily_attempts_if_needed(self, user_id: int):
        """Reset attempts if new day"""
        user_data = await self.get_user_data(user_id)
        if not user_data:
            return
        
        last_reset = user_data.get('last_reset')
        if not last_reset or last_reset < self.get_today_start():
            now_ist = datetime.now(IST)
            await self.users.update_one(
                {"user_id": user_id},
                {"$set": {"video_attempts": 0, "last_reset": now_ist}}
            )
            logger.info(f"🔄 Reset attempts for user {user_id}")
    
    async def can_user_watch_movie(self, user_id: int) -> bool:
        """Check if user can watch movies"""
        await self.reset_daily_attempts_if_needed(user_id)
        user_data = await self.get_user_data(user_id)
        
        if not user_data:
            return False
        
        # Check if verified
        if user_data.get("is_verified"):
            verify_expiry = user_data.get("verify_expiry")
            if verify_expiry:
                now_ist = datetime.now(IST)
                if now_ist < verify_expiry:
                    return True
                else:
                    # Verification expired
                    await self.users.update_one(
                        {"user_id": user_id},
                        {"$set": {"is_verified": False, "verify_expiry": None}}
                    )
        
        # Check free limit
        return user_data.get("video_attempts", 0) < FREE_VIDEO_LIMIT
    
    async def increment_video_attempts(self, user_id: int) -> bool:
        """Increment video attempts"""
        await self.reset_daily_attempts_if_needed(user_id)
        result = await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {"video_attempts": 1}}
        )
        return result.modified_count > 0
    
    async def needs_verification(self, user_id: int) -> bool:
        """Check if user needs verification"""
        await self.reset_daily_attempts_if_needed(user_id)
        user_data = await self.get_user_data(user_id)
        
        if not user_data:
            return False
        
        # Check if verified
        if user_data.get("is_verified"):
            verify_expiry = user_data.get("verify_expiry")
            if verify_expiry and datetime.now(IST) < verify_expiry:
                return False
        
        return user_data.get("video_attempts", 0) >= FREE_VIDEO_LIMIT
    
    async def set_verification_token(self, user_id: int, token: str) -> bool:
        """Set verification token"""
        now_ist = datetime.now(IST)
        expiry = now_ist + timedelta(seconds=VERIFY_TOKEN_TIMEOUT)
        result = await self.users.update_one(
            {"user_id": user_id},
            {"$set": {"verify_token": token, "token_expiry": expiry}}
        )
        return result.modified_count > 0
    
    async def verify_token(self, token: str) -> Optional[int]:
        """Verify token and return user_id"""
        now_ist = datetime.now(IST)
        user = await self.users.find_one({
            "verify_token": token,
            "token_expiry": {"$gt": now_ist}
        })
        
        if user:
            verify_expiry = now_ist + timedelta(seconds=VERIFY_TOKEN_TIMEOUT)
            await self.users.update_one(
                {"user_id": user["user_id"]},
                {"$set": {
                    "is_verified": True,
                    "verify_expiry": verify_expiry,
                    "verify_token": None,
                    "token_expiry": None
                }}
            )
            return user["user_id"]
        
        return None
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """Get user statistics"""
        await self.reset_daily_attempts_if_needed(user_id)
        user_data = await self.get_user_data(user_id)
        
        if not user_data:
            return {}
        
        return {
            "video_attempts": user_data.get("video_attempts", 0),
            "is_verified": user_data.get("is_verified", False),
            "joined_date": user_data.get("joined_date"),
            "last_reset": user_data.get("last_reset")
        }

# Singleton instance
_db_instance = None

def get_database():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
        
