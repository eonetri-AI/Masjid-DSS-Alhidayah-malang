# 🎭 Demo Mode - Simulasi Peringatan Bencana

## Cara Menggunakan Demo Mode

Demo mode memungkinkan Anda melihat tampilan sistem peringatan bencana tanpa harus menunggu gempa atau cuaca ekstrim yang sebenarnya.

### Mengaktifkan Demo Mode

#### 1. **Display View**
```
URL: http://localhost:3000/display?demo=true
```
Atau di production:
```
URL: https://your-domain.com/display?demo=true
```

#### 2. **Preview Page**
```
URL: http://localhost:3000/preview?demo=true
```

### Apa yang Ditampilkan di Demo Mode?

Demo mode akan menampilkan **3 peringatan simulasi**:

#### 🔴 Peringatan Gempa Bumi
- **Magnitude**: M5.8
- **Lokasi**: 25 km Barat Daya Malang
- **Waktu**: 09 Des 2025 10:45:30 WIB
- **Jarak**: 25 km dari lokasi Anda
- **Kedalaman**: 10 km
- **Potensi**: Tidak berpotensi tsunami
- **Icon**: ⚠️
- **Warna**: Banner merah dengan animasi pulse

#### 🟠 Peringatan Cuaca Ekstrim #1
- **Kondisi**: Hujan Lebat
- **Lokasi**: Malang
- **Pesan**: Waspadai Hujan Lebat di wilayah Malang
- **Icon**: 🌧️
- **Warna**: Banner orange/kuning dengan animasi pulse

#### 🟠 Peringatan Cuaca Ekstrim #2
- **Kondisi**: Hujan Petir
- **Lokasi**: Malang
- **Pesan**: Waspadai Hujan Petir di wilayah Malang
- **Icon**: 🌧️
- **Warna**: Banner orange/kuning dengan animasi pulse

### Mode Normal (Tanpa Demo)

#### Display Normal
```
URL: http://localhost:3000/display
```

Dalam mode normal, sistem akan:
- ✅ Menampilkan peringatan gempa **hanya jika** ada gempa dalam radius relevan (sesuai magnitude)
- ✅ Menampilkan peringatan cuaca ekstrim **hanya jika** terdeteksi cuaca ekstrim di wilayah masjid
- ✅ Tidak menampilkan banner jika tidak ada peringatan

### Screenshot Demo Mode

Lihat hasil screenshot di:
```
/tmp/display_all_warnings.png
```

Screenshot menunjukkan:
- ✅ 3 banner peringatan ditampilkan berurutan
- ✅ Styling berbeda untuk gempa (merah) dan cuaca (kuning)
- ✅ Semua informasi detail ditampilkan dengan jelas
- ✅ Animasi pulse dan shake berfungsi
- ✅ Icons tepat (⚠️ untuk gempa, 🌧️ untuk cuaca)
- ✅ Layout responsif dan mudah dibaca

### Technical Details

#### Backend Implementation
File: `/app/backend/server.py`

```python
@api_router.get("/disaster-warnings")
async def get_disaster_warnings(demo: bool = False):
    """Get disaster warnings from BMKG with location filtering"""
    
    # Demo mode for testing UI
    if demo:
        return {
            "has_warning": True,
            "warnings": [
                # ... demo data ...
            ]
        }
    
    # Normal mode - real BMKG data with filtering
    # ...
```

#### Frontend Implementation
File: `/app/frontend/src/pages/DisplayView.js`

```javascript
const fetchData = async () => {
  // Check if demo mode is enabled via URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const demoMode = urlParams.get('demo') === 'true';
  
  // Fetch warnings with demo parameter if enabled
  const warningRes = await axios.get(
    `${API}/disaster-warnings${demoMode ? '?demo=true' : ''}`
  );
  // ...
}
```

### Use Cases

1. **Testing/Development**: Verify UI tanpa menunggu kejadian nyata
2. **Demo untuk User**: Tunjukkan fitur kepada pengurus masjid
3. **Training**: Latihan memahami sistem peringatan
4. **Screenshot/Documentation**: Ambil gambar untuk panduan

### Notes

- ⚠️ Demo mode **HANYA untuk testing/preview**
- ⚠️ **JANGAN** gunakan demo mode di production/TV display yang sesungguhnya
- ✅ Mode normal akan otomatis filter berdasarkan lokasi nyata
- ✅ Demo mode dapat diaktifkan/dinonaktifkan dengan mudah via URL

### Menonaktifkan Demo Mode

Cukup hapus `?demo=true` dari URL:
```
Dari: http://localhost:3000/display?demo=true
Ke:   http://localhost:3000/display
```

Atau refresh halaman tanpa query parameter.

---

**Dibuat**: 9 Desember 2025  
**Untuk**: Simulasi & Testing Sistem Peringatan Bencana
