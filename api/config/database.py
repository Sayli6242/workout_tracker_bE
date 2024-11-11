from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "your_mongodb_uri")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.mydatabase_db
