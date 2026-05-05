"""
Seed script to populate district -> zone (taluk) -> area (village) hierarchy.
Geocodes each village to get center coordinates for distance-based area assignment.
Run with: python -m app.seed_areas
"""
import asyncio
import json
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.data import DISTRICTS_DATA

GEOCODE_CACHE_FILE = os.path.join(os.path.dirname(__file__), "data", "geocode_cache.json")


async def geocode_village(village_name: str, zone_name: str, district_name: str, cache: dict) -> dict | None:
    """Geocode a village using Nominatim. Returns {'lat': float, 'lon': float} or None."""
    cache_key = f"{village_name}, {zone_name}, {district_name}"
    if cache_key in cache:
        return cache[cache_key]

    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent=settings.nominatim_user_agent)

    search_queries = [
        f"{village_name}, {zone_name}, {district_name}, Tamil Nadu, India",
        f"{village_name}, {district_name}, Tamil Nadu, India",
        f"{village_name}, Tamil Nadu, India",
    ]

    for query in search_queries:
        try:
            location = await asyncio.to_thread(geolocator.geocode, query, timeout=10)
            if location:
                result = {"lat": location.latitude, "lon": location.longitude}
                cache[cache_key] = result
                return result
        except Exception:
            pass
        await asyncio.sleep(1)  # Nominatim usage policy: max 1 req/sec

    cache[cache_key] = None
    return None


def load_geocode_cache() -> dict:
    if os.path.exists(GEOCODE_CACHE_FILE):
        with open(GEOCODE_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_geocode_cache(cache: dict):
    os.makedirs(os.path.dirname(GEOCODE_CACHE_FILE), exist_ok=True)
    with open(GEOCODE_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


async def seed_areas():
    client = AsyncIOMotorClient("mongodb://localhost:27030")
    db = client[settings.database_name]

    await db.areas.create_index([("name", 1), ("district", 1), ("zone", 1)], unique=True)
    await db.areas.create_index([("zone", 1)])
    await db.areas.create_index([("district", 1)])

    # Drop old areas without district field (legacy data)
    old_areas = await db.areas.count_documents({"district": {"$exists": False}})
    if old_areas > 0:
        await db.areas.delete_many({"district": {"$exists": False}})
        print(f"Removed {old_areas} old area records without district field")

    cache = load_geocode_cache()
    now = datetime.utcnow()
    created = 0
    skipped = 0
    geocoded = 0
    geocode_failed = 0

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

                # Geocode the village
                coords = await geocode_village(village_name, zone_name, district_name, cache)

                area_doc = {
                    "name": village_name,
                    "ward_number": ward_counter[zone_name],
                    "zone": zone_name,
                    "district": district_name,
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                }

                if coords:
                    area_doc["location"] = {
                        "type": "Point",
                        "coordinates": [coords["lon"], coords["lat"]],
                    }
                    geocoded += 1
                else:
                    geocode_failed += 1

                try:
                    await db.areas.insert_one(area_doc)
                    created += 1
                except Exception as e:
                    if "duplicate key" in str(e):
                        skipped += 1
                    else:
                        raise

                if created % 50 == 0:
                    print(f"  Progress: {created} areas created, {geocoded} geocoded, {geocode_failed} failed")
                    save_geocode_cache(cache)

        zones = list(district_data["zones"].keys())
        village_count = sum(len(v) for v in district_data["zones"].values())
        print(f"{district_name}: {village_count} villages across {len(zones)} zones")
        print(f"  Zones: {', '.join(zones)}")

    # Save cache after completion
    save_geocode_cache(cache)

    # Create 2dsphere index for geospatial queries
    await db.areas.create_index([("location", "2dsphere")])

    total = await db.areas.count_documents({"is_active": True})
    with_location = await db.areas.count_documents({"is_active": True, "location": {"$exists": True}})
    all_districts = await db.areas.distinct("district", {"is_active": True})

    print(f"\nTotal areas: {total}")
    print(f"Areas with coordinates: {with_location}/{total}")
    print(f"Geocode failures: {geocode_failed}")
    print(f"Districts: {', '.join(sorted(all_districts))}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_areas())
