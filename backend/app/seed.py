"""
Seed script to create initial district officer.
Run with: python -m app.seed
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash


async def seed_district_officer():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

    # Migrate existing super_admin to district_officer
    migration_result = await db.users.update_many(
        {"role": "super_admin"},
        {"$set": {"role": "district_officer", "updated_at": datetime.utcnow()}},
    )
    if migration_result.modified_count > 0:
        print(f"Migrated {migration_result.modified_count} super_admin(s) to district_officer")

    # Check if district officer already exists
    existing = await db.users.find_one({"role": "district_officer"})
    if existing:
        print("District officer already exists:")
        print(f"  Email: {existing['email']}")
        client.close()
        return

    # Create district officer
    district_officer = {
        "email": "admin@civicfix.com",
        "name": "District Officer",
        "phone": "+91-9876543210",
        "hashed_password": get_password_hash("admin123"),
        "role": "district_officer",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(district_officer)
    print("District officer created successfully!")
    print(f"  ID: {result.inserted_id}")
    print(f"  Email: admin@civicfix.com")
    print(f"  Password: admin123")
    print("\nPlease change the password after first login!")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_district_officer())
