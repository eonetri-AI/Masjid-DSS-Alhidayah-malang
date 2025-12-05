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
from hijri_converter import Hijri, Gregorian
import pytz
import httpx

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
    mosque_address: str = "Jl. Contoh No. 123, Kota Malang"
    mosque_logo: str = ""
    latitude: float = 3.139
    longitude: float = 101.6869
    timezone: str = "Asia/Kuala_Lumpur"
    calculation_method: str = "ISNA"
    imsya_offset: int = 10
    iqomah_delays: Dict[str, int] = Field(default_factory=lambda: {
        "fajr": 15,
        "dhuhr": 10,
        "asr": 10,
        "maghrib": 5,
        "isha": 10
    })
    theme: str = "midnight"
    background_image: str = ""
    admin_password: str = "admin123"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MosqueSettingsUpdate(BaseModel):
    mosque_name: Optional[str] = None
    mosque_address: Optional[str] = None
    mosque_logo: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    calculation_method: Optional[str] = None
    imsya_offset: Optional[int] = None
    iqomah_delays: Optional[Dict[str, int]] = None
    theme: Optional[str] = None
    background_image: Optional[str] = None
    admin_password: Optional[str] = None

class PasswordVerify(BaseModel):
    password: str

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
    is_iqomah_countdown: bool
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
    saldo_pekan_lalu: float = 0.0
    infaq_pekan_ini: float = 0.0
    pengeluaran: float = 0.0
    saldo_pekan_ini: float = 0.0
    period: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FinancialReportCreate(BaseModel):
    saldo_pekan_lalu: float
    infaq_pekan_ini: float
    pengeluaran: float
    period: str = ""

# ============== PRAYER TIMES SERVICE ==============

async def calculate_prayer_times_aladhan(latitude: float, longitude: float, tz_str: str, method: str = "ISNA", imsya_offset: int = 10) -> Dict:
    """Calculate prayer times using Aladhan API"""
    try:
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        
        # Method mapping
        method_map = {
            "ISNA": 2,  # Islamic Society of North America
            "MWL": 3,   # Muslim World League
            "EGYPTIAN": 5,  # Egyptian General Authority
            "KARACHI": 1,   # University of Islamic Sciences, Karachi
            "MAKKAH": 4,    # Umm Al-Qura University, Makkah
            "TEHRAN": 7     # Institute of Geophysics, University of Tehran
        }
        
        method_num = method_map.get(method, 2)
        
        # Call Aladhan API
        url = f"http://api.aladhan.com/v1/timings/{int(now.timestamp())}"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "method": method_num,
            "school": 0  # Shafi (for Indonesia)
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if data.get("code") == 200:
            timings = data["data"]["timings"]
            
            # Extract prayer times
            fajr_time = timings["Fajr"][:5]  # Get HH:MM only
            sunrise_time = timings["Sunrise"][:5]
            dhuhr_time = timings["Dhuhr"][:5]
            asr_time = timings["Asr"][:5]
            maghrib_time = timings["Maghrib"][:5]
            isha_time = timings["Isha"][:5]
            
            # Calculate Imsya
            fajr_dt = datetime.strptime(fajr_time, "%H:%M")
            imsya_dt = fajr_dt - timedelta(minutes=imsya_offset)
            imsya_time = imsya_dt.strftime("%H:%M")
            
            # Convert Gregorian to Hijri
            hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
            hijri_str = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}"
            
            logging.info(f"Aladhan API: Fajr {fajr_time}, Dhuhr {dhuhr_time}, Maghrib {maghrib_time}")
            
            return {
                "fajr": fajr_time,
                "imsya": imsya_time,
                "sunrise": sunrise_time,
                "dhuhr": dhuhr_time,
                "asr": asr_time,
                "maghrib": maghrib_time,
                "isha": isha_time,
                "gregorian_date": now.strftime("%A, %d %B %Y"),
                "hijri_date": hijri_str,
                "current_time": now.strftime("%H:%M:%S")
            }
        else:
            raise Exception("Aladhan API returned error")
            
    except Exception as e:
        logging.error(f"Error fetching prayer times from Aladhan API: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to default times
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
        
        fajr_dt = datetime.strptime("04:30", "%H:%M")
        imsya_dt = fajr_dt - timedelta(minutes=imsya_offset)
        imsya_time = imsya_dt.strftime("%H:%M")
        
        return {
            "fajr": "04:30",
            "imsya": imsya_time,
            "sunrise": "05:45",
            "dhuhr": "11:45",
            "asr": "15:15",
            "maghrib": "17:45",
            "isha": "19:00",
            "gregorian_date": now.strftime("%A, %d %B %Y"),
            "hijri_date": f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}",
            "current_time": now.strftime("%H:%M:%S")
        }

def get_next_prayer_info(prayer_times: Dict, iqomah_delays: Dict[str, int]) -> Dict:
    """Calculate next prayer and time remaining, or iqomah countdown if within prayer time"""
    prayer_names = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    
    # Parse current time with full datetime
    current_str = prayer_times["current_time"]  # Format: HH:MM:SS
    now_dt = datetime.strptime(current_str, "%H:%M:%S")
    today = datetime.today().date()
    now_full = datetime.combine(today, now_dt.time())
    
    # Check if we're in iqomah period (between adhan and iqomah)
    for prayer in prayer_names:
        try:
            adhan_str = prayer_times[prayer]  # Format: HH:MM
            adhan_time = datetime.strptime(adhan_str, "%H:%M").time()
            adhan_dt = datetime.combine(today, adhan_time)
            
            delay = iqomah_delays.get(prayer, 10)
            iqomah_dt = adhan_dt + timedelta(minutes=delay)
            
            # If current time is between adhan and iqomah
            if adhan_dt <= now_full < iqomah_dt:
                diff_seconds = (iqomah_dt - now_full).total_seconds()
                return {
                    "prayer": prayer,
                    "minutes_until": max(0, int(diff_seconds / 60)),
                    "seconds_until": max(0, int(diff_seconds)),
                    "is_iqomah_countdown": True
                }
        except Exception as e:
            logging.error(f"Error checking iqomah for {prayer}: {e}")
            continue
    
    # Otherwise find next prayer (adhan countdown)
    for prayer in prayer_names:
        try:
            prayer_str = prayer_times[prayer]
            prayer_time = datetime.strptime(prayer_str, "%H:%M").time()
            prayer_dt = datetime.combine(today, prayer_time)
            
            if prayer_dt > now_full:
                diff_seconds = (prayer_dt - now_full).total_seconds()
                return {
                    "prayer": prayer,
                    "minutes_until": max(0, int(diff_seconds / 60)),
                    "seconds_until": max(0, int(diff_seconds)),
                    "is_iqomah_countdown": False
                }
        except Exception as e:
            logging.error(f"Error checking prayer {prayer}: {e}")
            continue
    
    # If no prayer found today, next is Fajr tomorrow
    try:
        fajr_str = prayer_times["fajr"]
        fajr_time = datetime.strptime(fajr_str, "%H:%M").time()
        tomorrow = today + timedelta(days=1)
        fajr_tomorrow = datetime.combine(tomorrow, fajr_time)
        diff_seconds = (fajr_tomorrow - now_full).total_seconds()
        
        return {
            "prayer": "fajr",
            "minutes_until": max(0, int(diff_seconds / 60)),
            "seconds_until": max(0, int(diff_seconds)),
            "is_iqomah_countdown": False
        }
    except Exception:
        return {
            "prayer": "fajr",
            "minutes_until": 0,
            "seconds_until": 0,
            "is_iqomah_countdown": False
        }

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
    
    # Calculate prayer times using Aladhan API
    times = await calculate_prayer_times_aladhan(
        settings["latitude"],
        settings["longitude"],
        settings["timezone"],
        settings["calculation_method"],
        settings.get("imsya_offset", 10)
    )
    
    # Get next prayer info
    prayer_info = get_next_prayer_info(times, settings["iqomah_delays"])
    
    # Calculate iqomah times
    iqomah_times = {}
    for prayer in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
        adhan_time = datetime.strptime(times[prayer], "%H:%M")
        delay = settings["iqomah_delays"].get(prayer, 10)
        iqomah_time = adhan_time + timedelta(minutes=delay)
        iqomah_times[prayer] = iqomah_time.strftime("%H:%M")
    
    return PrayerTimesResponse(
        fajr=times["fajr"],
        imsya=times["imsya"],
        syuruq=times["sunrise"],
        dhuhr=times["dhuhr"],
        asr=times["asr"],
        maghrib=times["maghrib"],
        isha=times["isha"],
        gregorian_date=times["gregorian_date"],
        hijri_date=times["hijri_date"],
        next_prayer=prayer_info["prayer"],
        time_until_next=prayer_info["minutes_until"],
        is_iqomah_countdown=prayer_info["is_iqomah_countdown"],
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
    """Create new financial report with automatic calculation"""
    # Calculate Saldo Pekan Ini automatically
    saldo_pekan_ini = report.saldo_pekan_lalu + report.infaq_pekan_ini - report.pengeluaran
    
    new_report = FinancialReport(
        **report.model_dump(),
        saldo_pekan_ini=saldo_pekan_ini
    )
    report_dict = new_report.model_dump()
    report_dict["created_at"] = report_dict["created_at"].isoformat()
    
    # Delete old report and insert new one (keep only latest)
    await financial_reports_collection.delete_many({})
    await financial_reports_collection.insert_one(report_dict)
    return new_report

@api_router.delete("/financial-reports/{report_id}")
async def delete_financial_report(report_id: str):
    """Delete financial report"""
    result = await financial_reports_collection.delete_one({"id": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"success": True}

# Password verification endpoint
@api_router.post("/verify-password")
async def verify_password(data: PasswordVerify):
    """Verify admin password"""
    settings = await settings_collection.find_one({}, {"_id": 0})
    if not settings:
        settings = MosqueSettings().model_dump()
    
    stored_password = settings.get("admin_password", "admin123")
    
    if data.password == stored_password:
        return {"success": True, "message": "Password verified"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")

# Weather API endpoint
@api_router.get("/weather")
async def get_weather():
    """Get current weather"""
    try:
        settings = await settings_collection.find_one({}, {"_id": 0})
        if not settings:
            settings = MosqueSettings().model_dump()
        
        lat = settings["latitude"]
        lon = settings["longitude"]
        
        # Using OpenWeatherMap free API
        api_key = "895284fb2d2c50a520ea537456963d9c"  # Free demo key
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "lang": "id"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if response.status_code == 200:
            return {
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "wind_speed": data["wind"]["speed"]
            }
        else:
            raise HTTPException(status_code=500, detail="Weather API error")
            
    except Exception as e:
        logging.error(f"Error fetching weather: {e}")
        # Return default weather data
        return {
            "temperature": 28,
            "feels_like": 30,
            "humidity": 75,
            "description": "berawan",
            "icon": "02d",
            "wind_speed": 2.5
        }

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