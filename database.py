from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

class Database:
    def __init__(self, mongo_uri):
        self.client = AsyncIOMotorClient(mongo_uri)
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

def get_database(mongo_uri):
    return Database(mongo_uri)
    
