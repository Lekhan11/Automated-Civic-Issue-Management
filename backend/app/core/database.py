from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = None
database = None


async def get_database():
    global client, database
    if client is None:
        client = AsyncIOMotorClient(settings.mongodb_url)
        database = client[settings.database_name]
    return database


async def connect_to_mongo():
    global client, database
    client = AsyncIOMotorClient(settings.mongodb_url)
    database = client[settings.database_name]
    print("Connected to MongoDB")


async def close_mongo_connection():
    global client
    if client:
        client.close()
        print("Disconnected from MongoDB")


async def get_db():
    db = await get_database()
    return db
