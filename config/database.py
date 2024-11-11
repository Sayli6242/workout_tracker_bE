# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

# Use Motor for async operations
client = AsyncIOMotorClient("mongodb+srv://Sayli1603:7410744850@cluster1.cjimyhw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
db = client.mydatabase_db