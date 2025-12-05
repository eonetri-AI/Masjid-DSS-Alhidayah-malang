from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
from islamic_times.islamic_times import ITLocation
from hijri_converter import Hijri, Gregorian
import pytz

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collections
settings_collection = db.get_collection("mosque_settings")
announcements_collection = db.get_collection("announcements")
quran_verses_collection = db.get_collection("quran_verses")
financial_reports_collection = db.get_collection("financial_reports")

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# ============== MODELS ==============

class MosqueSettings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mosque_name: str = "Masjid Al-Noor"
    latitude: float = 3.139
    longitude: float = 101.6869
    timezone: str = "Asia/Kuala_Lumpur"
    calculation_method: str = "ISNA"
    iqomah_delays: Dict[str, int] = Field(default_factory=lambda: {
        "fajr": 15,
        "dhuhr": 10,
        "asr": 10,
        "maghrib": 5,
        "isha": 10
    })
    theme: str = "midnight"
    background_image: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MosqueSettingsUpdate(BaseModel):
    mosque_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    calculation_method: Optional[str] = None
    iqomah_delays: Optional[Dict[str, int]] = None
    theme: Optional[str] = None
    background_image: Optional[str] = None

class PrayerTimesResponse(BaseModel):
    fajr: str
    imsya: str
    syuruq: str
    dhuhr: str
    asr: str
    maghrib: str
    isha: str
    gregorian_date: str
    hijri_date: str
    next_prayer: str
    time_until_next: int
    iqomah_times: Dict[str, str]

class Announcement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    priority: int = 1
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnnouncementCreate(BaseModel):
    text: str
    priority: int = 1
    active: bool = True

class QuranVerse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    arabic: str
    translation: str
    reference: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class QuranVerseCreate(BaseModel):
    arabic: str
    translation: str
    reference: str
    active: bool = True

class FinancialReport(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    amount: float
    period: str
    description: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FinancialReportCreate(BaseModel):
    title: str
    amount: float
    period: str
    description: str = ""

# ============== PRAYER TIMES SERVICE ==============

def calculate_prayer_times(latitude: float, longitude: float, tz_str: str, method: str = "ISNA") -> Dict:
    """Calculate prayer times using islamic_times library"""
    try:
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        
        # Create location object
        location = ITLocation(
            latitude=latitude,
            longitude=longitude,
            elevation=0,
            date=now,
            method=method
        )
        
        # Get prayer times
        prayer_times = location.prayer_times()
        
        # Convert Gregorian to Hijri
        hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
        hijri_str = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}"
        
        # Format times properly
        def format_time(time_str):
            if isinstance(time_str, str):
                return time_str
            return "00:00"
        
        return {
            "fajr": format_time(prayer_times.get("fajr", "05:30")),
            "sunrise": format_time(prayer_times.get("sunrise", "07:00")),
            "dhuhr": format_time(prayer_times.get("zuhr", "13:00")),
            "asr": format_time(prayer_times.get("asr", "16:30")),
            "maghrib": format_time(prayer_times.get("maghrib", "19:15")),
            "isha": format_time(prayer_times.get("isha", "20:30")),
            "gregorian_date": now.strftime("%A, %d %B %Y"),
            "hijri_date": hijri_str,
            "current_time": now.strftime("%H:%M:%S")
        }
    except Exception as e:
        logging.error(f"Error calculating prayer times: {e}")
        import traceback
        traceback.print_exc()
        # Return default times if calculation fails
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
        return {
            "fajr": "04:30",
            "sunrise": "05:45",
            "dhuhr": "11:45",
            "asr": "15:15",
            "maghrib": "17:45",
            "isha": "19:00",
            "gregorian_date": now.strftime("%A, %d %B %Y"),
            "hijri_date": f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}",
            "current_time": now.strftime("%H:%M:%S")
        }

def get_next_prayer_info(prayer_times: Dict, iqomah_delays: Dict[str, int]) -> tuple:
    """Calculate next prayer and time remaining"""
    from datetime import datetime, timedelta
    
    prayer_names = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    current_time = datetime.strptime(prayer_times["current_time"], "%H:%M:%S").time()
    
    for prayer in prayer_names:
        prayer_time = datetime.strptime(prayer_times[prayer], "%H:%M").time()
        if prayer_time > current_time:
            # Calculate minutes until prayer
            now_dt = datetime.combine(datetime.today(), current_time)
            prayer_dt = datetime.combine(datetime.today(), prayer_time)
            diff = (prayer_dt - now_dt).total_seconds() / 60
            return prayer, int(diff)
    
    # If no prayer found today, next is Fajr tomorrow
    return "fajr", 0

# ============== API ENDPOINTS ==============

# Settings endpoints
@api_router.get("/settings", response_model=MosqueSettings)
async def get_settings():
    """Get mosque settings"""
    settings = await settings_collection.find_one({}, {"_id": 0})
    if not settings:
        # Return default settings
        default_settings = MosqueSettings()
        return default_settings
    return MosqueSettings(**settings)

@api_router.put("/settings")
async def update_settings(settings_update: MosqueSettingsUpdate):
    """Update mosque settings"""
    # Get current settings
    current = await settings_collection.find_one({}, {"_id": 0})
    
    if current:
        # Update existing
        update_data = settings_update.model_dump(exclude_none=True)
        update_data["updated_at"] = datetime.now(timezone.utc)
        await settings_collection.update_one({}, {"$set": update_data})
    else:
        # Create new
        new_settings = MosqueSettings(**settings_update.model_dump(exclude_none=True))
        settings_dict = new_settings.model_dump()
        settings_dict["updated_at"] = settings_dict["updated_at"].isoformat()
        await settings_collection.insert_one(settings_dict)
    
    return {"success": True, "message": "Settings updated"}

# Prayer times endpoint
@api_router.get("/prayer-times", response_model=PrayerTimesResponse)
async def get_prayer_times():
    """Get current prayer times"""
    # Get settings
    settings = await settings_collection.find_one({}, {"_id": 0})
    if not settings:
        settings = MosqueSettings().model_dump()
    
    # Calculate prayer times
    times = calculate_prayer_times(
        settings["latitude"],
        settings["longitude"],
        settings["timezone"],
        settings["calculation_method"]
    )
    
    # Get next prayer
    next_prayer, time_until = get_next_prayer_info(times, settings["iqomah_delays"])
    
    # Calculate iqomah times
    iqomah_times = {}
    for prayer in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
        adhan_time = datetime.strptime(times[prayer], "%H:%M")
        delay = settings["iqomah_delays"].get(prayer, 10)
        iqomah_time = adhan_time + timedelta(minutes=delay)
        iqomah_times[prayer] = iqomah_time.strftime("%H:%M")
    
    return PrayerTimesResponse(
        fajr=times["fajr"],
        imsya=times["fajr"],  # Imsya typically same as Fajr
        syuruq=times["sunrise"],
        dhuhr=times["dhuhr"],
        asr=times["asr"],
        maghrib=times["maghrib"],
        isha=times["isha"],
        gregorian_date=times["gregorian_date"],
        hijri_date=times["hijri_date"],
        next_prayer=next_prayer,
        time_until_next=time_until,
        iqomah_times=iqomah_times
    )

# Announcements endpoints
@api_router.get("/announcements", response_model=List[Announcement])
async def get_announcements(active_only: bool = True):
    """Get all announcements"""
    query = {"active": True} if active_only else {}
    announcements = await announcements_collection.find(query, {"_id": 0}).sort("priority", -1).to_list(100)
    return [Announcement(**ann) for ann in announcements]

@api_router.post("/announcements", response_model=Announcement)
async def create_announcement(announcement: AnnouncementCreate):
    """Create new announcement"""
    new_ann = Announcement(**announcement.model_dump())
    ann_dict = new_ann.model_dump()
    ann_dict["created_at"] = ann_dict["created_at"].isoformat()
    await announcements_collection.insert_one(ann_dict)
    return new_ann

@api_router.delete("/announcements/{announcement_id}")
async def delete_announcement(announcement_id: str):
    """Delete announcement"""
    result = await announcements_collection.delete_one({"id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"success": True}

# Quran verses endpoints
@api_router.get("/quran-verses", response_model=List[QuranVerse])
async def get_quran_verses(active_only: bool = True):
    """Get all Quran verses"""
    query = {"active": True} if active_only else {}
    verses = await quran_verses_collection.find(query, {"_id": 0}).to_list(100)
    return [QuranVerse(**v) for v in verses]

@api_router.post("/quran-verses", response_model=QuranVerse)
async def create_quran_verse(verse: QuranVerseCreate):
    """Create new Quran verse"""
    new_verse = QuranVerse(**verse.model_dump())
    verse_dict = new_verse.model_dump()
    verse_dict["created_at"] = verse_dict["created_at"].isoformat()
    await quran_verses_collection.insert_one(verse_dict)
    return new_verse

@api_router.delete("/quran-verses/{verse_id}")
async def delete_quran_verse(verse_id: str):
    """Delete Quran verse"""
    result = await quran_verses_collection.delete_one({"id": verse_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Verse not found")
    return {"success": True}

# Financial reports endpoints
@api_router.get("/financial-reports", response_model=List[FinancialReport])
async def get_financial_reports():
    """Get all financial reports"""
    reports = await financial_reports_collection.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [FinancialReport(**r) for r in reports]

@api_router.post("/financial-reports", response_model=FinancialReport)
async def create_financial_report(report: FinancialReportCreate):
    """Create new financial report"""
    new_report = FinancialReport(**report.model_dump())
    report_dict = new_report.model_dump()
    report_dict["created_at"] = report_dict["created_at"].isoformat()
    await financial_reports_collection.insert_one(report_dict)
    return new_report

@api_router.delete("/financial-reports/{report_id}")
async def delete_financial_report(report_id: str):
    """Delete financial report"""
    result = await financial_reports_collection.delete_one({"id": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"success": True}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()