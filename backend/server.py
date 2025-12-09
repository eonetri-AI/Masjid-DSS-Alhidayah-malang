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
import locale

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
    city_name: str = "Malang"
    latitude: float = 3.139
    longitude: float = 101.6869
    timezone: str = "Asia/Kuala_Lumpur"
    calculation_method: str = "ISNA"
    use_manual_times: bool = False
    manual_prayer_times: Optional[Dict[str, str]] = None
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
    makkah_embed_url: str = ""
    font_size: str = "large"
    admin_password: str = "admin123"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MosqueSettingsUpdate(BaseModel):
    mosque_name: Optional[str] = None
    mosque_address: Optional[str] = None
    mosque_logo: Optional[str] = None
    city_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    calculation_method: Optional[str] = None
    use_manual_times: Optional[bool] = None
    manual_prayer_times: Optional[Dict[str, str]] = None
    imsya_offset: Optional[int] = None
    iqomah_delays: Optional[Dict[str, int]] = None
    theme: Optional[str] = None
    background_image: Optional[str] = None
    makkah_embed_url: Optional[str] = None
    font_size: Optional[str] = None
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

# ============== HELPER FUNCTIONS ==============

def format_date_indonesian(dt: datetime) -> str:
    """Format date in Indonesian"""
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    
    day_name = days[dt.weekday()]
    day = dt.day
    month_name = months[dt.month - 1]
    year = dt.year
    
    return f"{day_name}, {day} {month_name} {year}"

# ============== PRAYER TIMES SERVICE ==============

async def calculate_prayer_times_muslimsalat(latitude: float, longitude: float, tz_str: str, imsya_offset: int = 10):
    """Calculate prayer times using MuslimSalat API (accurate for Indonesia)"""
    try:
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        
        # MuslimSalat API - more accurate for Southeast Asia
        url = "https://muslimsalat.com/daily.json"
        params = {
            "latitude": latitude,
            "longitude": longitude
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if data.get("items"):
            items = data["items"][0]  # Get today's timings
            
            # Extract prayer times (24h format)
            fajr_time = items["fajr"]
            sunrise_time = items["shurooq"]
            dhuhr_time = items["dhuhr"]
            asr_time = items["asr"]
            maghrib_time = items["maghrib"]
            isha_time = items["isha"]
            
            # Calculate Imsya
            fajr_dt = datetime.strptime(fajr_time, "%H:%M")
            imsya_dt = fajr_dt - timedelta(minutes=imsya_offset)
            imsya_time = imsya_dt.strftime("%H:%M")
            
            # Convert Gregorian to Hijri
            hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
            hijri_str = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}"
            
            logging.info(f"MuslimSalat API: Fajr {fajr_time}, Dhuhr {dhuhr_time}, Maghrib {maghrib_time}")
            
            return {
                "fajr": fajr_time,
                "imsya": imsya_time,
                "sunrise": sunrise_time,
                "dhuhr": dhuhr_time,
                "asr": asr_time,
                "maghrib": maghrib_time,
                "isha": isha_time,
                "gregorian_date": format_date_indonesian(now),
                "hijri_date": hijri_str,
                "current_time": now.strftime("%H:%M:%S")
            }
        else:
            raise Exception(f"MuslimSalat API error: {data}")
            
    except Exception as e:
        logging.error(f"Error with MuslimSalat API, falling back to Aladhan: {e}")
        # Fallback to Aladhan
        return await calculate_prayer_times_aladhan(latitude, longitude, tz_str, "MAKKAH", imsya_offset)

async def calculate_prayer_times_aladhan(latitude: float, longitude: float, tz_str: str, method: str = "ISNA", imsya_offset: int = 10) -> Dict:
    """Calculate prayer times using Aladhan API (fallback)"""
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
            "TEHRAN": 7,    # Institute of Geophysics, University of Tehran
            "KEMENAG": 11   # Kementerian Agama RI (best for Indonesia)
        }
        
        method_num = method_map.get(method, 11)  # Default to Kemenag for Indonesia
        
        # Call Aladhan API with custom parameters for Indonesia
        # Using timingsByCity endpoint for better accuracy
        date_str = now.strftime("%d-%m-%Y")
        url = "https://api.aladhan.com/v1/timings"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "method": method_num,
            "school": 0  # Shafi (for Indonesia)
        }
        
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(f"{url}/{date_str}", params=params)
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
                "gregorian_date": format_date_indonesian(now),
                "hijri_date": hijri_str,
                "current_time": now.strftime("%H:%M:%S")
            }
        else:
            raise Exception(f"Aladhan API error: {data}")
            
    except Exception as e:
        logging.error(f"Error calculating prayer times: {e}")
        # Return default times as fallback
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
        hijri_str = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}"
        
        return {
            "fajr": "04:30",
            "imsya": "04:20",
            "sunrise": "05:45",
            "dhuhr": "11:45",
            "asr": "15:15",
            "maghrib": "17:45",
            "isha": "19:00",
            "gregorian_date": format_date_indonesian(now),
            "hijri_date": hijri_str,
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
    
    # Check if using manual times
    if settings.get("use_manual_times") and settings.get("manual_prayer_times"):
        # Use manual prayer times
        manual_times = settings["manual_prayer_times"]
        tz = pytz.timezone(settings["timezone"])
        now = datetime.now(tz)
        
        # Calculate Imsya from Fajr
        fajr_time = manual_times.get("fajr", "04:30")
        fajr_dt = datetime.strptime(fajr_time, "%H:%M")
        imsya_offset = settings.get("imsya_offset", 10)
        imsya_dt = fajr_dt - timedelta(minutes=imsya_offset)
        imsya_time = imsya_dt.strftime("%H:%M")
        
        # Convert Gregorian to Hijri
        hijri_date = Gregorian(now.year, now.month, now.day).to_hijri()
        hijri_str = f"{hijri_date.day} {hijri_date.month_name()} {hijri_date.year}"
        
        times = {
            "fajr": manual_times.get("fajr", "04:30"),
            "imsya": imsya_time,
            "sunrise": manual_times.get("sunrise", "05:45"),
            "dhuhr": manual_times.get("dhuhr", "11:45"),
            "asr": manual_times.get("asr", "15:15"),
            "maghrib": manual_times.get("maghrib", "17:45"),
            "isha": manual_times.get("isha", "19:00"),
            "gregorian_date": format_date_indonesian(now),
            "hijri_date": hijri_str,
            "current_time": now.strftime("%H:%M:%S")
        }
        logging.info("Using manual prayer times")
    else:
        # Calculate prayer times using Aladhan API with Kemenag method
        times = await calculate_prayer_times_aladhan(
            settings["latitude"],
            settings["longitude"],
            settings["timezone"],
            "KEMENAG",  # Use Kemenag method for Indonesia
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

# City coordinates endpoint
@api_router.get("/cities")
async def get_cities():
    """Get list of cities with coordinates"""
    cities = {
        "Jakarta": {"lat": -6.2088, "lon": 106.8456, "tz": "Asia/Jakarta"},
        "Bandung": {"lat": -6.9175, "lon": 107.6191, "tz": "Asia/Jakarta"},
        "Yogyakarta": {"lat": -7.7956, "lon": 110.3695, "tz": "Asia/Jakarta"},
        "Solo": {"lat": -7.5505, "lon": 110.8283, "tz": "Asia/Jakarta"},
        "Semarang": {"lat": -6.9932, "lon": 110.4203, "tz": "Asia/Jakarta"},
        "Surabaya": {"lat": -7.2575, "lon": 112.7521, "tz": "Asia/Jakarta"},
        "Malang": {"lat": -7.9666, "lon": 112.6326, "tz": "Asia/Jakarta"},
        "Kediri": {"lat": -7.8167, "lon": 112.0167, "tz": "Asia/Jakarta"},
        "Jombang": {"lat": -7.5458, "lon": 112.2333, "tz": "Asia/Jakarta"},
        "Blitar": {"lat": -8.0983, "lon": 112.1681, "tz": "Asia/Jakarta"},
        "Madiun": {"lat": -7.6298, "lon": 111.5239, "tz": "Asia/Jakarta"},
        "Ponorogo": {"lat": -7.8664, "lon": 111.4625, "tz": "Asia/Jakarta"},
        "Pasuruan": {"lat": -7.6453, "lon": 112.9075, "tz": "Asia/Jakarta"},
        "Probolinggo": {"lat": -7.7543, "lon": 113.2159, "tz": "Asia/Jakarta"},
        "Jember": {"lat": -8.1724, "lon": 113.6997, "tz": "Asia/Jakarta"},
        "Banyuwangi": {"lat": -8.2193, "lon": 114.3675, "tz": "Asia/Jakarta"}
    }
    return cities

# File upload endpoint
from fastapi import UploadFile, File
import base64

@api_router.post("/upload-file")
async def upload_file(file: UploadFile = File(...)):
    """Upload file and return base64 data URL"""
    try:
        contents = await file.read()
        base64_encoded = base64.b64encode(contents).decode('utf-8')
        
        # Determine mime type
        mime_type = file.content_type or "image/png"
        
        # Return as data URL
        data_url = f"data:{mime_type};base64,{base64_encoded}"
        
        return {
            "success": True,
            "data_url": data_url,
            "filename": file.filename,
            "size": len(contents)
        }
    except Exception as e:
        logging.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Weather API endpoint
@api_router.get("/weather")
async def get_weather():
    """Get weather data from BMKG Open Data"""
    try:
        # Get location from settings
        settings = await settings_collection.find_one()
        if not settings:
            raise HTTPException(status_code=404, detail="Settings not found")
        
        city_name = settings.get("city_name", "Malang")
        lat = settings.get("latitude", -7.9666)
        lon = settings.get("longitude", 112.6326)
        
        # Map cities to BMKG province codes
        province_codes = {
            "Jakarta": "31",
            "Bandung": "32",
            "Yogyakarta": "34",
            "Semarang": "33",
            "Surabaya": "35",
            "Malang": "35",
            "Denpasar": "51",
            "Makassar": "73",
            "Medan": "12",
            "Palembang": "16",
            "Pontianak": "61",
            "Banjarmasin": "63",
            "Balikpapan": "64",
            "Manado": "71",
            "Pekanbaru": "14",
            "Banyuwangi": "35"
        }
        
        province_code = province_codes.get(city_name, "35")
        
        # Try BMKG Digital Forecast API
        url = f"https://data.bmkg.go.id/DataMKG/MEWS/DigitalForecast/DigitalForecast-{get_province_name(province_code)}.xml"
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(url)
                
                if response.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    
                    # Find matching city/area
                    for area in root.findall(".//area"):
                        area_desc = area.get("description", "").lower()
                        
                        if city_name.lower() in area_desc or area_desc in city_name.lower():
                            # Get temperature parameter
                            temp_param = area.find(".//parameter[@id='t']")
                            humidity_param = area.find(".//parameter[@id='hu']")
                            weather_param = area.find(".//parameter[@id='weather']")
                            
                            temp = 28
                            humidity = 75
                            weather_desc = "Cerah Berawan"
                            
                            if temp_param is not None:
                                timerange = temp_param.find("timerange")
                                if timerange is not None:
                                    values = timerange.findall("value")
                                    if values:
                                        temp = int(float(values[0].text))
                            
                            if humidity_param is not None:
                                timerange = humidity_param.find("timerange")
                                if timerange is not None:
                                    values = timerange.findall("value")
                                    if values:
                                        humidity = int(float(values[0].text))
                            
                            if weather_param is not None:
                                timerange = weather_param.find("timerange")
                                if timerange is not None:
                                    values = timerange.findall("value")
                                    if values:
                                        weather_code = int(values[0].text)
                                        weather_desc = get_bmkg_weather_description(weather_code)
                            
                            logging.info(f"BMKG Weather: {city_name} - {temp}°C, {weather_desc}")
                            
                            return {
                                "temperature": temp,
                                "humidity": humidity,
                                "description": weather_desc,
                                "source": "BMKG"
                            }
            except Exception as xml_error:
                logging.warning(f"BMKG XML API error: {xml_error}")
        
        # Fallback to Open-Meteo API (free, reliable, no API key needed)
        try:
            logging.info(f"Trying Open-Meteo API fallback for {city_name}")
            open_meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(open_meteo_url)
                
                if response.status_code == 200:
                    data = response.json()
                    current = data.get("current_weather", {})
                    
                    temp = int(current.get("temperature", 28))
                    weather_code = current.get("weathercode", 0)
                    
                    # Convert WMO weather code to description
                    weather_desc = get_wmo_weather_description(weather_code)
                    
                    logging.info(f"Open-Meteo Weather: {city_name} - {temp}°C, {weather_desc}")
                    
                    return {
                        "temperature": temp,
                        "humidity": 75,  # Open-Meteo doesn't provide humidity in free tier
                        "description": weather_desc,
                        "source": "Open-Meteo"
                    }
        except Exception as meteo_error:
            logging.warning(f"Open-Meteo API error: {meteo_error}")
        
        # Last resort fallback
        return {
            "temperature": 28,
            "humidity": 75,
            "description": "Tidak Ada Data",
            "source": "Fallback"
        }
            
    except Exception as e:
        logging.error(f"Error fetching BMKG weather: {e}")
        return {
            "temperature": 28,
            "humidity": 75,
            "description": "Cerah Berawan",
            "source": "BMKG"
        }

def get_province_name(code: str) -> str:
    """Get province name for BMKG API"""
    provinces = {
        "11": "Aceh",
        "12": "SumateraUtara",
        "13": "SumateraBarat",
        "14": "Riau",
        "15": "Jambi",
        "16": "SumateraSelatan",
        "17": "Bengkulu",
        "18": "Lampung",
        "19": "KepulauanBangkaBelitung",
        "21": "KepulauanRiau",
        "31": "DKIJakarta",
        "32": "JawaBarat",
        "33": "JawaTengah",
        "34": "DIYogyakarta",
        "35": "JawaTimur",
        "36": "Banten",
        "51": "Bali",
        "52": "NusaTenggaraBarat",
        "53": "NusaTenggaraTimur",
        "61": "KalimantanBarat",
        "62": "KalimantanTengah",
        "63": "KalimantanSelatan",
        "64": "KalimantanTimur",
        "65": "KalimantanUtara",
        "71": "SulawesiUtara",
        "72": "SulawesiTengah",
        "73": "SulawesiSelatan",
        "74": "SulawesiTenggara",
        "75": "Gorontalo",
        "76": "SulawesiBarat",
        "81": "Maluku",
        "82": "MalukuUtara",
        "91": "PapuaBarat",
        "94": "Papua"
    }
    return provinces.get(code, "JawaTimur")

def get_bmkg_weather_description(code: int) -> str:
    """Convert BMKG weather code to description"""
    weather_codes = {
        0: "Cerah",
        1: "Cerah Berawan",
        2: "Cerah Berawan",
        3: "Berawan",
        4: "Berawan Tebal",
        5: "Udara Kabur",
        10: "Asap",
        45: "Kabut",
        60: "Hujan Ringan",
        61: "Hujan Sedang",
        63: "Hujan Lebat",
        80: "Hujan Lokal",
        95: "Hujan Petir",
        97: "Hujan Petir"
    }
    return weather_codes.get(code, "Cerah Berawan")

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth (in kilometers)
    """
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def parse_gempa_coordinates(coord_str: str) -> tuple:
    """
    Parse BMKG earthquake coordinates string
    Format examples: "-7.26,107.89" or "7.26 LS,107.89 BT"
    """
    try:
        # Remove directional indicators and clean string
        coord_str = coord_str.replace(" LS", "").replace(" LU", "")
        coord_str = coord_str.replace(" BT", "").replace(" BB", "")
        coord_str = coord_str.strip()
        
        # Split by comma
        parts = coord_str.split(",")
        if len(parts) == 2:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            return (lat, lon)
    except Exception as e:
        logging.error(f"Error parsing coordinates '{coord_str}': {e}")
    
    return None

@api_router.get("/disaster-warnings")
async def get_disaster_warnings(demo: bool = False):
    """Get disaster warnings from BMKG with location filtering"""
    
    # Demo mode for testing UI
    if demo:
        return {
            "has_warning": True,
            "warnings": [
                {
                    "type": "gempa",
                    "title": "PERINGATAN GEMPA BUMI",
                    "magnitude": "5.8",
                    "depth": "10 km",
                    "location": "25 km Barat Daya Malang",
                    "time": "09 Des 2025 10:45:30 WIB",
                    "distance": "25 km dari lokasi Anda",
                    "potential": "Tidak berpotensi tsunami"
                },
                {
                    "type": "cuaca",
                    "title": "PERINGATAN CUACA EKSTRIM",
                    "condition": "Hujan Lebat",
                    "location": "Malang",
                    "message": "Waspadai Hujan Lebat di wilayah Malang"
                },
                {
                    "type": "cuaca",
                    "title": "PERINGATAN CUACA EKSTRIM",
                    "condition": "Hujan Petir",
                    "location": "Malang",
                    "message": "Waspadai Hujan Petir di wilayah Malang"
                }
            ]
        }
    
    try:
        # Get mosque location from settings
        settings = await settings_collection.find_one({}, {"_id": 0})
        if not settings:
            mosque_lat = -7.9666  # Default Malang
            mosque_lon = 112.6326
        else:
            mosque_lat = settings.get("latitude", -7.9666)
            mosque_lon = settings.get("longitude", 112.6326)
        
        warnings = []
        
        # 1. Check for earthquake warnings
        gempa_url = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(gempa_url)
                
                if response.status_code == 200:
                    data = response.json()
                    gempa = data.get("Infogempa", {}).get("gempa", {})
                    
                    if gempa:
                        magnitude_str = gempa.get("Magnitude", "0")
                        try:
                            magnitude = float(magnitude_str)
                        except:
                            magnitude = 0.0
                        
                        # Parse earthquake coordinates
                        coord_str = gempa.get("Coordinates", "")
                        gempa_coords = parse_gempa_coordinates(coord_str)
                        
                        if gempa_coords:
                            gempa_lat, gempa_lon = gempa_coords
                            distance_km = haversine_distance(mosque_lat, mosque_lon, gempa_lat, gempa_lon)
                            
                            # Filter based on magnitude and distance
                            show_warning = False
                            if magnitude >= 5.5 and distance_km <= 500:
                                show_warning = True  # Large earthquake within 500km
                            elif magnitude >= 4.5 and distance_km <= 300:
                                show_warning = True  # Medium earthquake within 300km
                            elif magnitude >= 3.5 and distance_km <= 100:
                                show_warning = True  # Small earthquake nearby
                            
                            if show_warning:
                                warnings.append({
                                    "type": "gempa",
                                    "title": "PERINGATAN GEMPA BUMI",
                                    "magnitude": magnitude_str,
                                    "depth": gempa.get("Kedalaman", ""),
                                    "location": gempa.get("Wilayah", ""),
                                    "time": gempa.get("Tanggal", "") + " " + gempa.get("Jam", ""),
                                    "potential": gempa.get("Potensi", ""),
                                    "distance": f"{int(distance_km)} km dari lokasi Anda"
                                })
                                logging.info(f"Earthquake warning: M{magnitude} at {distance_km:.1f}km")
                        else:
                            # If can't parse coordinates, show if magnitude is significant
                            if magnitude >= 5.5:
                                warnings.append({
                                    "type": "gempa",
                                    "title": "PERINGATAN GEMPA BUMI",
                                    "magnitude": magnitude_str,
                                    "depth": gempa.get("Kedalaman", ""),
                                    "location": gempa.get("Wilayah", ""),
                                    "time": gempa.get("Tanggal", "") + " " + gempa.get("Jam", ""),
                                    "potential": gempa.get("Potensi", ""),
                                    "distance": ""
                                })
            except Exception as gempa_error:
                logging.warning(f"Error fetching earthquake data: {gempa_error}")
        
        # 2. Check for extreme weather warnings
        try:
            city_name = settings.get("city_name", "Malang") if settings else "Malang"
            
            # Map cities to BMKG province codes
            province_codes = {
                "Jakarta": "31", "Bandung": "32", "Yogyakarta": "34", "Semarang": "33",
                "Surabaya": "35", "Malang": "35", "Denpasar": "51", "Makassar": "73",
                "Medan": "12", "Palembang": "16", "Pontianak": "61", "Banjarmasin": "63",
                "Balikpapan": "64", "Manado": "71", "Pekanbaru": "14", "Banyuwangi": "35"
            }
            
            province_code = province_codes.get(city_name, "35")
            weather_url = f"https://data.bmkg.go.id/DataMKG/MEWS/DigitalForecast/DigitalForecast-{get_province_name(province_code)}.xml"
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(weather_url)
                
                if response.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    
                    # Find matching city/area
                    for area in root.findall(".//area"):
                        area_desc = area.get("description", "").lower()
                        
                        if city_name.lower() in area_desc or area_desc in city_name.lower():
                            # Check for extreme weather conditions
                            weather_param = area.find(".//parameter[@id='weather']")
                            
                            if weather_param is not None:
                                timerange = weather_param.find("timerange")
                                if timerange is not None:
                                    values = timerange.findall("value")
                                    if values:
                                        weather_code = int(values[0].text)
                                        
                                        # Extreme weather codes: 61, 63, 95, 97 (heavy rain, thunderstorm)
                                        extreme_weather = {
                                            61: "Hujan Sedang",
                                            63: "Hujan Lebat",
                                            95: "Hujan Petir",
                                            97: "Hujan Petir Kuat"
                                        }
                                        
                                        if weather_code in extreme_weather:
                                            warnings.append({
                                                "type": "cuaca",
                                                "title": "PERINGATAN CUACA EKSTRIM",
                                                "condition": extreme_weather[weather_code],
                                                "location": city_name,
                                                "message": f"Waspadai {extreme_weather[weather_code]} di wilayah {city_name}"
                                            })
                                            logging.info(f"Weather warning: {extreme_weather[weather_code]} in {city_name}")
                            break
        except Exception as weather_error:
            logging.warning(f"Error checking extreme weather: {weather_error}")
        
        # Return warnings
        if warnings:
            return {
                "has_warning": True,
                "warnings": warnings
            }
        else:
            return {
                "has_warning": False,
                "message": "Tidak ada peringatan bencana saat ini"
            }
            
    except Exception as e:
        logging.error(f"Error fetching disaster warnings: {e}")
        return {
            "has_warning": False,
            "message": "Tidak dapat mengambil data peringatan"
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