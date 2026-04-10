"""
Seed script to populate Tamil Nadu districts and zones (taluks).
Run with: python -m app.seed_areas

Each entry represents a taluk/zone within a district.
Ward numbers are auto-incremented per zone (starting from 1).
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

# Tamil Nadu: 38 districts with their taluks
TAMIL_NADU_DISTRICTS = {
    "Ariyalur": ["Ariyalur", "Udayarpalayam", "Andimadam", "Jayankondam"],
    "Chengalpattu": ["Chengalpattu", "Tambaram", "Pallavaram", "Sholinganallur", "Tiruporur", "Maduranthakam", "Cheyyur"],
    "Chennai": ["Egmore", "Fort Tondiarpet", "Mambalam", "T. Nagar", "Velachery", "Anna Nagar", "Perambur", "Tiruvottiyur", "Alandur", "Poonamallee", "Sholavaramanallur", "Madhavaram"],
    "Coimbatore": ["Coimbatore North", "Coimbatore South", "Sulur", "Mettupalayam", "Pollachi", "Valparai", "Karamadai", "Perianaickenpalayam"],
    "Cuddalore": ["Cuddalore", "Panruti", "Virudhachalam", "Chidambaram", "Kattumannarkoil", "Srimushnam"],
    "Dharmapuri": ["Dharmapuri", "Harur", "Palacode", "Pennagaram", "Pappireddipatti"],
    "Dindigul": ["Dindigul", "Vedasandur", "Natham", "Oddanchatram", "Athoor", "Gundupatti"],
    "Erode": ["Erode", "Gobichettipalayam", "Bhavani", "Perundurai", "Sathyamangalam", "Anthiyur", "Kundadam"],
    "Kanchipuram": ["Kanchipuram", "Sriperumbudur", "Uthiramerur", "Tiruvallur", "Wallajabad", "Maduranthakam"],
    "Kanyakumari": ["Nagercoil", "Padmanabhapuram", "Colachel", "Thuckalay", "Vilavancode", "Killiyoor", "Agasteeswaram"],
    "Karur": ["Karur", "Kulithalai", "Krishnarayapuram", "Aravakurichi", "Thogamalai"],
    "Krishnagiri": ["Krishnagiri", "Hosur", "Denkanikottai", "Uthagamandalam", "Pochampalli", "Sulagiri", "Bargur"],
    "Madurai": ["Madurai North", "Madurai South", "Melur", "Vadipatti", "Usilampatti", "Peraiyur", "Tirumangalam", "Kallikudi"],
    "Nagapattinam": ["Nagapattinam", "Mayiladuthurai", "Sirkazhi", "Kumbakonam", "Vedaranyam", "Tharangambadi"],
    "Namakkal": ["Namakkal", "Rasipuram", "Tiruchengode", "Paramathi Velur", "Kumarapalayam", "Puduchatram"],
    "Nilgiris": ["Udhagamandalam", "Coonoor", "Kotagiri", "Kundanad", "Gudalur", "Pandalur"],
    "Perambalur": ["Perambalur", "Kunnam", "Veppanthattai", "Alathur", "Rainfall", "Pennadam"],
    "Pudukkottai": ["Pudukkottai", "Aranthangi", "Illuppur", "Karambakudi", "Manamelkudi", "Thirumayam", "Avudayarkovil"],
    "Ramanathapuram": ["Ramanathapuram", "Rameswaram", "Paramakudi", "Sivaganga", "Tiruvadanai", "Kadaladi"],
    "Ranipet": ["Arakkonam", "Ranipet", "Walajah", "Nemili", "Cheyyar", "Kalavai", "Timiri"],
    "Salem": ["Salem", "Attur", "Omalur", "Mettur", "Sankari", "Yercaud", "Gangavalli", "Vazhapadi"],
    "Sivagangai": ["Sivagangai", "Karaikudi", "Devakottai", "Manamadurai", "Tirupathur", "Ilayankudi"],
    "Tenkasi": ["Tenkasi", "Shencottai", "Alangulam", "Sankarankovil", "Kadayanallur", "Veerakeralamputhur"],
    "Thanjavur": ["Thanjavur", "Kumbakonam", "Orathanadu", "Pattukottai", "Peravurani", "Budalur", "Thiruvonam"],
    "Theni": ["Theni", "Bodinayakanur", "Periyakulam", "Uthamapalayam", "Andipatti", "Cumbum"],
    "Thoothukudi": ["Thoothukudi", "Tiruchendur", "Srivaikundam", "Ettayapuram", "Sathankulam", "Ottapidaram", "Vilathikulam"],
    "Tiruchirappalli": ["Tiruchirappalli", "Lalgudi", "Manapparai", "Musiri", "Thottiam", "Thuraiyur", "Manachanallur", "Srirangam"],
    "Tirunelveli": ["Tirunelveli", "Palayamkottai", "Ambasamudram", "Tenkasi", "Sankarankovil", "Nanguneri", "Radhapuram"],
    "Tiruvallur": ["Tiruvallur", "Poonamallee", "Avadi", "Thiruverkadu", "Gummidipoondi", "Minjur", "Pattabiram"],
    "Tiruvannamalai": ["Tiruvannamalai", "Cheyyar", "Polur", "Chengam", "Kalasapakkam", "Arani"],
    "Tiruvarur": ["Tiruvarur", "Kumbakonam", "Nannilam", "Needamangalam", "Mannargudi", "Kodavasal"],
    "Vellore": ["Vellore", "Katpadi", "Gudiyatham", "Ambur", "Vaniyambadi", "Tirupattur", "Anaicut", "Kaveripakkam"],
    "Viluppuram": ["Viluppuram", "Rasipuram", "Tirukkovilur", "Tittakudi", "Ulundurpettai", "Vanur", "Marakkanam"],
    "Virudhunagar": ["Virudhunagar", "Sivakasi", "Rajapalayam", "Aruppukkottai", "Tiruchuli", "Kariapatti"],
}


async def seed_areas():
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]

    await db.areas.create_index([("name", 1), ("district", 1), ("zone", 1)], unique=True)
    await db.areas.create_index([("zone", 1)])
    await db.areas.create_index([("district", 1)])

    # Drop old Bangalore areas if any (they won't have district field)
    old_areas = await db.areas.count_documents({"district": {"$exists": False}})
    if old_areas > 0:
        await db.areas.delete_many({"district": {"$exists": False}})
        print(f"Removed {old_areas} old area records without district field")

    created = 0
    updated = 0
    ward_counter = {}

    for district, zones in TAMIL_NADU_DISTRICTS.items():
        for zone in zones:
            ward_counter[(district, zone)] = ward_counter.get((district, zone), 0) + 1
            ward_num = ward_counter[(district, zone)]

            result = await db.areas.update_one(
                {"name": zone, "district": district},
                {"$set": {
                    "name": zone,
                    "ward_number": ward_num,
                    "zone": zone,
                    "district": district,
                    "is_active": True,
                    "updated_at": __import__("datetime").datetime.utcnow(),
                }, "$setOnInsert": {
                    "created_at": __import__("datetime").datetime.utcnow(),
                }},
                upsert=True,
            )
            if result.upserted_id:
                created += 1
            else:
                updated += 1

    total = await db.areas.count_documents({"is_active": True})
    district_count = await db.areas.distinct("district", {"is_active": True})

    print(f"Areas seeded: {created} created, {updated} updated")
    print(f"Total areas: {total}")
    print(f"Districts: {len(district_count)}")
    print(f"Districts: {', '.join(sorted(district_count))}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_areas())
