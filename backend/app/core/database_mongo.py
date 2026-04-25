from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

mongo_client: AsyncIOMotorClient = None
mongo_database = None


def get_mongo_database():
    global mongo_client, mongo_database
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(settings.mongodb_url)
        mongo_database = mongo_client[settings.database_name]
    return mongo_database


async def get_mongo_db():
    return get_mongo_database()


async def connect_to_mongo():
    global mongo_client, mongo_database
    mongo_client = AsyncIOMotorClient(settings.mongodb_url)
    mongo_database = mongo_client[settings.database_name]
    print("Connected to MongoDB")


async def close_mongo_connection():
    global mongo_client
    if mongo_client:
        mongo_client.close()
        print("Disconnected from MongoDB")
