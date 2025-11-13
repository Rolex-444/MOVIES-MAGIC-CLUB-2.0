from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

class Database:
    def __init__(self, mongo_uri):
        """Initialize MongoDB connection"""
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client.moviebot
        self.movies = self.db.movies
        self.users = self.db.users
        print("✅ Database connected")
    
    async def add_movie(self, movie_data):
        """Add new movie to database"""
        movie_data['added_at'] = datetime.now()
        movie_data['views'] = 0
        result = await self.movies.insert_one(movie_data)
        print(f"✅ Movie added: {movie_data['title']}")
        return result.inserted_id
    
    async def search_movies(self, query):
        """Search movies by title"""
        results = await self.movies.find({
            "title": {"$regex": query, "$options": "i"}
        }).limit(10).to_list(length=10)
        return results
    
    async def get_all_movies(self, limit=100):
        """Get all movies"""
        movies = await self.movies.find().sort("added_at", -1).limit(limit).to_list(length=limit)
        return movies
    
    async def get_movie_by_id(self, movie_id):
        """Get single movie by ID"""
        return await self.movies.find_one({"_id": movie_id})
    
    async def delete_movie(self, movie_id):
        """Delete movie"""
        result = await self.movies.delete_one({"_id": movie_id})
        return result.deleted_count
    
    async def add_user(self, user_id, username, first_name):
        """Track user activity"""
        await self.users.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "username": username,
                    "first_name": first_name,
                    "last_active": datetime.now()
                },
                "$setOnInsert": {
                    "joined_at": datetime.now(),
                    "total_searches": 0
                }
            },
            upsert=True
        )

# Initialize database (will be used in main.py)
def get_database(mongo_uri):
    return Database(mongo_uri)
