"""
Seed script to create initial super admin.
Run with: python -m app.seed
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash


async def seed_super_admin():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

    # Check if super admin already exists
    existing = await db.users.find_one({"role": "super_admin"})
    if existing:
        print("Super admin already exists:")
        print(f"  Email: {existing['email']}")
        client.close()
        return

    # Create super admin
    super_admin = {
        "email": "admin@civicfix.com",
        "name": "Super Admin",
        "phone": "+91-9876543210",
        "hashed_password": get_password_hash("admin123"),
        "role": "super_admin",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(super_admin)
    print("Super admin created successfully!")
    print(f"  ID: {result.inserted_id}")
    print(f"  Email: admin@civicfix.com")
    print(f"  Password: admin123")
    print("\nPlease change the password after first login!")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_super_admin())