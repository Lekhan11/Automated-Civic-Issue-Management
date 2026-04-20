"""
Seed script to populate district -> zone (taluk) -> area (village) hierarchy.
Run with: python -m app.seed_areas

Each district has zones (taluks), and each zone has areas (revenue villages).
Ward numbers are auto-incremented per zone (starting from 1).
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.data import DISTRICTS_DATA


async def seed_areas():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

    await db.areas.create_index([("name", 1), ("district", 1), ("zone", 1)], unique=True)
    await db.areas.create_index([("zone", 1)])
    await db.areas.create_index([("district", 1)])

    # Drop old areas without district field (legacy Bangalore data)
    old_areas = await db.areas.count_documents({"district": {"$exists": False}})
    if old_areas > 0:
        await db.areas.delete_many({"district": {"$exists": False}})
        print(f"Removed {old_areas} old area records without district field")

    now = datetime.utcnow()
    created = 0
    skipped = 0

    for district_name, district_data in DISTRICTS_DATA.items():
        # Remove old records for this district (handles re-seeding)
        old = await db.areas.count_documents({"district": district_name})
        if old > 0:
            await db.areas.delete_many({"district": district_name})
            print(f"Cleared {old} existing records for {district_name}")

        ward_counter = {}

        for zone_name, villages in district_data["zones"].items():
            ward_counter[zone_name] = 0
            for village_name in villages:
                ward_counter[zone_name] += 1
                area_doc = {
                    "name": village_name,
                    "ward_number": ward_counter[zone_name],
                    "zone": zone_name,
                    "district": district_name,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }
                try:
                    await db.areas.insert_one(area_doc)
                    created += 1
                except Exception as e:
                    if "duplicate key" in str(e):
                        skipped += 1
                    else:
                        raise

        zones = list(district_data["zones"].keys())
        village_count = sum(len(v) for v in district_data["zones"].values())
        print(f"{district_name}: {village_count} villages across {len(zones)} zones")
        print(f"  Zones: {', '.join(zones)}")

    total = await db.areas.count_documents({"is_active": True})
    all_districts = await db.areas.distinct("district", {"is_active": True})

    print(f"\nTotal areas: {total}")
    print(f"Districts: {', '.join(sorted(all_districts))}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_areas())
