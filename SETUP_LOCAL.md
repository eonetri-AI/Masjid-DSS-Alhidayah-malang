# 🚀 Panduan Setup Aplikasi Digital Signage Masjid di Local

Panduan lengkap untuk menjalankan aplikasi ini di komputer local Anda.

---

## 📋 Requirements (Yang Dibutuhkan)

### 1. **Software yang Wajib Diinstall**

#### A. Python 3.11+
- **Download**: https://www.python.org/downloads/
- **Versi Minimum**: Python 3.11
- **Check instalasi**: 
  ```bash
  python3 --version
  # atau
  python --version
  ```

#### B. Node.js 18+ & Yarn
- **Node.js Download**: https://nodejs.org/
- **Versi Minimum**: Node.js 18.x atau 20.x
- **Check instalasi**:
  ```bash
  node --version
  ```
- **Install Yarn** (package manager):
  ```bash
  npm install -g yarn
  ```
- **Check Yarn**:
  ```bash
  yarn --version
  ```
c
#### C. MongoDB
- **Download**: https://www.mongodb.com/try/download/community
- **Versi Minimum**: MongoDB 5.x atau 6.x
- **Alternative**: Gunakan MongoDB Atlas (cloud) - https://www.mongodb.com/cloud/atlas
- **Check instalasi**:
  ```bash
  mongod --version
  ```

---

## 📁 Struktur Project

```
/app/
├── backend/
│   ├── server.py           # Main FastAPI application
│   ├── requirements.txt    # Python dependencies
│   ├── seed_data.py        # Initial data seeding
│   └── .env                # Backend environment variables
├── frontend/
│   ├── src/
│   │   ├── pages/          # React pages
│   │   └── styles/         # CSS styles
│   ├── package.json        # Node dependencies
│   └── .env                # Frontend environment variables
└── uploads/                # File upload directory
```

---

## 🛠️ Langkah-Langkah Setup

### **Step 1: Clone/Download Project**

Download project ke komputer Anda, misalnya ke folder `C:\mosque-signage` (Windows) atau `~/mosque-signage` (Mac/Linux).

---

### **Step 2: Setup MongoDB**

#### Opsi A: MongoDB Local
1. Jalankan MongoDB service:
   ```bash
   # Windows (di Command Prompt sebagai Administrator):
   net start MongoDB
   
   # Mac/Linux:
   sudo systemctl start mongod
   # atau
   brew services start mongodb-community
   ```

2. Database akan berjalan di: `mongodb://localhost:27017`

#### Opsi B: MongoDB Atlas (Cloud - Gratis)
1. Buat account di https://www.mongodb.com/cloud/atlas
2. Buat cluster gratis (Free Tier)
3. Dapatkan connection string, contoh:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/mosque_db
   ```
4. Whitelist IP address Anda (atau gunakan `0.0.0.0/0` untuk development)

---

### **Step 3: Setup Backend (Python/FastAPI)**

1. **Masuk ke folder backend**:
   ```bash
   cd backend
   ```

2. **Buat virtual environment** (opsional tapi recommended):
   ```bash
   # Windows:
   python -m venv venv
   venv\Scripts\activate
   
   # Mac/Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables**:
   
   Edit file `backend/.env`:
   ```env
   # Untuk MongoDB Local:
   MONGO_URL="mongodb://localhost:27017"
   DB_NAME="mosque_signage"
   CORS_ORIGINS="*"
   
   # Untuk MongoDB Atlas (jika pakai cloud):
   # MONGO_URL="mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/mosque_signage"
   # DB_NAME="mosque_signage"
   # CORS_ORIGINS="*"
   ```

5. **Seed initial data** (data awal):
   ```bash
   python seed_data.py
   ```

6. **Jalankan backend server**:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8001 --reload
   ```

   Backend akan berjalan di: **http://localhost:8001**

7. **Test backend**:
   Buka browser: http://localhost:8001/docs
   (Akan muncul Swagger API documentation)

---

### **Step 4: Setup Frontend (React)**

1. **Buka terminal baru**, masuk ke folder frontend:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   yarn install
   ```

3. **Setup environment variables**:
   
   Edit file `frontend/.env`:
   ```env
   REACT_APP_BACKEND_URL=http://localhost:8001
   WDS_SOCKET_PORT=3000
   REACT_APP_ENABLE_VISUAL_EDITS=false
   ENABLE_HEALTH_CHECK=false
   ```

4. **Jalankan frontend server**:
   ```bash
   yarn start
   ```

   Frontend akan berjalan di: **http://localhost:3000**

5. **Buka aplikasi**:
   - **Display View**: http://localhost:3000/display
   - **Admin Panel**: http://localhost:3000/admin
   - **Preview Mode**: http://localhost:3000/preview

---

## 🔑 Default Credentials

**Password Admin Panel**: `admin123`

Untuk mengakses admin panel, tekan tombol **'S'** 3x di halaman display, atau langsung akses:
- http://localhost:3000/admin
- http://localhost:3000/preview

---

## 📦 Dependencies Summary

### Backend Python (requirements.txt):
- **FastAPI**: Web framework
- **Motor**: Async MongoDB driver
- **Uvicorn**: ASGI server
- **httpx**: HTTP client untuk external APIs
- **python-dotenv**: Environment variables
- **pydantic**: Data validation
- Dan 80+ package pendukung lainnya

### Frontend React (package.json):
- **React 19**: UI framework
- **React Router**: Routing
- **Axios**: HTTP client
- **Radix UI**: UI components
- **Tailwind CSS**: Styling
- **moment-hijri**: Hijri calendar
- Dan 50+ package pendukung lainnya

---

## 🌐 API External yang Digunakan

Aplikasi ini menggunakan API eksternal berikut (tidak perlu API key):

1. **Aladhan API**: Prayer times calculation
   - https://aladhan.com/prayer-times-api

2. **Open-Meteo API**: Weather forecast (FREE, no API key)
   - https://open-meteo.com/

3. **BMKG API**: Indonesian weather & earthquake data
   - https://data.bmkg.go.id/

---

## 📂 Folder Upload

Buat folder untuk file uploads (logo, background):

```bash
# Di root project
mkdir uploads
```

Atau folder akan otomatis dibuat saat first upload.

---

## 🚨 Troubleshooting

### Problem: MongoDB tidak bisa connect
**Solusi**:
- Pastikan MongoDB service sudah running
- Check connection string di `backend/.env`
- Coba: `mongo` atau `mongosh` di terminal untuk test connection

### Problem: Port sudah digunakan
**Solusi**:
- Backend (8001): Ubah port di command: `uvicorn server:app --port 8002`
- Frontend (3000): Kill process atau ubah di `package.json`

### Problem: Module not found
**Solusi**:
```bash
# Backend:
pip install -r requirements.txt --force-reinstall

# Frontend:
rm -rf node_modules yarn.lock
yarn install
```

### Problem: CORS Error
**Solusi**:
- Pastikan `REACT_APP_BACKEND_URL` di frontend/.env sama dengan URL backend
- Pastikan `CORS_ORIGINS="*"` di backend/.env

---

## 💻 Menjalankan di Production

### Backend Production:
```bash
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
```

### Frontend Production:
```bash
# Build production
yarn build

# Serve dengan static server
npx serve -s build -l 3000
```

---

## 🎯 Quick Start Commands

**Jalankan semua dalam 3 terminal berbeda:**

```bash
# Terminal 1 - MongoDB (jika local)
mongod

# Terminal 2 - Backend
cd backend
source venv/bin/activate  # atau venv\Scripts\activate di Windows
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3 - Frontend
cd frontend
yarn start
```

**Akses aplikasi**: http://localhost:3000/display

---

## 📱 Demo Mode

Untuk testing tampilan peringatan bencana:
```
http://localhost:3000/display?demo=true
```

---

## 🔧 Development Tools

Recommended tools untuk development:

1. **VS Code** - Code editor
2. **Postman** - API testing
3. **MongoDB Compass** - MongoDB GUI
4. **React DevTools** - Browser extension
5. **Python Extension for VS Code**

---

## 📖 Additional Documentation

- `/app/DISASTER_WARNING_DOCS.md` - Dokumentasi sistem peringatan bencana
- `/app/TEST_DISASTER_WARNING.md` - Test report lengkap
- `/app/DEMO_MODE_INSTRUCTIONS.md` - Panduan demo mode
- `/app/test_result.md` - Testing protocol

---

## 💡 Tips

1. **Development Mode**: Gunakan `--reload` untuk hot reload
2. **Seed Data**: Jalankan `seed_data.py` untuk reset ke data awal
3. **API Docs**: http://localhost:8001/docs untuk explore API
4. **Browser**: Gunakan Chrome/Firefox untuk best experience
5. **4K Display**: Aplikasi sudah optimized untuk TV 4K (1920x1080+)

---

## 🆘 Support

Jika mengalami masalah:
1. Check error di terminal (backend/frontend)
2. Check browser console (F12)
3. Lihat log MongoDB
4. Pastikan semua services running

---

## ✅ Checklist Setup

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Yarn installed
- [ ] MongoDB running (local atau Atlas)
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Frontend dependencies installed (`yarn install`)
- [ ] Environment variables configured (`.env` files)
- [ ] Seed data executed (`python seed_data.py`)
- [ ] Backend running on port 8001
- [ ] Frontend running on port 3000
- [ ] Can access http://localhost:3000/display

---

**🎉 Selamat! Aplikasi Digital Signage Masjid siap digunakan!**

Untuk pertanyaan atau issue, silakan dokumentasikan error message dan screenshot.
