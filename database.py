from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from config import MONGO_URI

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client.moviebot
        self.movies = self.db.movies
        self.users = self.db.users
        print("✅ Database connected")
    
    async def add_movie(self, movie_data):
        movie_data['added_at'] = datetime.now()
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

# Singleton instance
_db_instance = None

def get_database():
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
    
