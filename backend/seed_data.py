"""
Seed initial data for mosque display system
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone
import uuid

async def seed_database():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("🌱 Seeding database...")
    
    # Seed Announcements
    announcements = [
        {
            "id": str(uuid.uuid4()),
            "text": "Juma'ah Prayer starts at 1:00 PM this Friday. Please arrive early.",
            "priority": 3,
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Ramadan Night: Special Taraweeh prayers will be held every night at 8:30 PM",
            "priority": 2,
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "text": "Islamic Studies Class for children every Saturday at 9:00 AM",
            "priority": 1,
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.announcements.delete_many({})
    await db.announcements.insert_many(announcements)
    print(f"✓ Added {len(announcements)} announcements")
    
    # Seed Quran Verses
    quran_verses = [
        {
            "id": str(uuid.uuid4()),
            "arabic": "اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ",
            "translation": "Allah - there is no deity except Him, the Ever-Living, the Sustainer of existence.",
            "reference": "Surah Al-Baqarah 2:255 (Ayat al-Kursi)",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "arabic": "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
            "translation": "Our Lord, give us in this world good and in the Hereafter good and protect us from the punishment of the Fire.",
            "reference": "Surah Al-Baqarah 2:201",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "arabic": "إِنَّ مَعَ الْعُسْرِ يُسْرًا",
            "translation": "Indeed, with hardship comes ease.",
            "reference": "Surah Ash-Sharh 94:6",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "arabic": "فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ",
            "translation": "So remember Me; I will remember you. And be grateful to Me and do not deny Me.",
            "reference": "Surah Al-Baqarah 2:152",
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.quran_verses.delete_many({})
    await db.quran_verses.insert_many(quran_verses)
    print(f"✓ Added {len(quran_verses)} Quran verses")
    
    # Seed Financial Reports
    financial_reports = [
        {
            "id": str(uuid.uuid4()),
            "title": "Monthly Donations",
            "amount": 25450.00,
            "period": "November 2025",
            "description": "Total donations received from congregation",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Utility Expenses",
            "amount": 3200.00,
            "period": "November 2025",
            "description": "Electricity, water, and maintenance",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Zakat Collection",
            "amount": 18750.00,
            "period": "November 2025",
            "description": "Zakat funds collected and distributed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.financial_reports.delete_many({})
    await db.financial_reports.insert_many(financial_reports)
    print(f"✓ Added {len(financial_reports)} financial reports")
    
    # Seed default mosque settings
    default_settings = {
        "id": str(uuid.uuid4()),
        "mosque_name": "Masjid Al-Noor",
        "latitude": 3.139,
        "longitude": 101.6869,
        "timezone": "Asia/Kuala_Lumpur",
        "calculation_method": "ISNA",
        "iqomah_delays": {
            "fajr": 15,
            "dhuhr": 10,
            "asr": 10,
            "maghrib": 5,
            "isha": 10
        },
        "theme": "midnight",
        "background_image": "",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.mosque_settings.delete_many({})
    await db.mosque_settings.insert_one(default_settings)
    print("✓ Added default mosque settings")
    
    print("\\n✅ Database seeded successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
