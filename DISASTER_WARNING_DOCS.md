# Dokumentasi Sistem Peringatan Bencana

## Overview
Sistem peringatan bencana yang terintegrasi dengan BMKG untuk menampilkan peringatan gempa bumi dan cuaca ekstrim yang **relevan dengan lokasi masjid**.

## Fitur Utama

### 1. Peringatan Gempa Bumi (Location-Based)
Sistem menggunakan **location filtering** untuk hanya menampilkan gempa yang relevan dengan lokasi masjid.

#### Kriteria Peringatan:
- **Gempa Besar (M ≥ 5.5)**: Ditampilkan jika jarak ≤ 500 km dari masjid
- **Gempa Sedang (M ≥ 4.5)**: Ditampilkan jika jarak ≤ 300 km dari masjid  
- **Gempa Kecil (M ≥ 3.5)**: Ditampilkan jika jarak ≤ 100 km dari masjid

#### Informasi yang Ditampilkan:
- Magnitude (kekuatan gempa)
- Lokasi/wilayah gempa
- Kedalaman
- Waktu kejadian
- Jarak dari lokasi masjid
- Potensi tsunami (jika ada)

### 2. Peringatan Cuaca Ekstrim (Location-Based)
Sistem mendeteksi cuaca ekstrim dari data BMKG untuk kota/wilayah masjid.

#### Kondisi yang Diperingatkan:
- **Hujan Sedang** (Code 61)
- **Hujan Lebat** (Code 63)
- **Hujan Petir** (Code 95)
- **Hujan Petir Kuat** (Code 97)

#### Informasi yang Ditampilkan:
- Jenis cuaca ekstrim
- Lokasi wilayah
- Pesan peringatan

## Teknologi

### Backend (`/api/disaster-warnings`)
```python
# Fungsi utama:
1. haversine_distance() - Menghitung jarak geografis menggunakan formula Haversine
2. parse_gempa_coordinates() - Parse koordinat dari format BMKG
3. get_disaster_warnings() - Endpoint API dengan filtering berdasarkan lokasi
```

#### Sumber Data:
- **Gempa**: `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json`
- **Cuaca**: `https://data.bmkg.go.id/DataMKG/MEWS/DigitalForecast/DigitalForecast-{Provinsi}.xml`

### Frontend
- **Component**: `DisplayView.js`
- **Styling**: `DisplayView.css`
- **Multiple warnings**: Mendukung tampilan simultan untuk gempa dan cuaca

#### Tampilan Visual:
- Banner merah untuk peringatan gempa bumi
- Banner kuning/orange untuk peringatan cuaca ekstrim
- Animasi pulse dan shake untuk menarik perhatian
- Layout responsif dan mudah dibaca

## Contoh Kasus Penggunaan

### Skenario 1: Gempa Jauh (TIDAK DITAMPILKAN)
```
Masjid: Malang, Jawa Timur (-7.97, 112.63)
Gempa: Tanimbar, Maluku (M5.4, -6.62, 131.16)
Jarak: 2048 km
Status: ❌ TIDAK DITAMPILKAN (terlalu jauh)
```

### Skenario 2: Gempa Dekat (DITAMPILKAN)
```
Masjid: Malang, Jawa Timur (-7.97, 112.63)
Gempa: Dekat Malang (M5.6, -6.5, 112.0)
Jarak: 177 km
Status: ✅ DITAMPILKAN (gempa besar dalam radius 500km)
```

### Skenario 3: Cuaca Ekstrim Lokal (DITAMPILKAN)
```
Masjid: Malang, Jawa Timur
Cuaca: Hujan Lebat di Malang
Status: ✅ DITAMPILKAN (cuaca ekstrim di wilayah masjid)
```

## Testing

### Unit Test Location Filtering
Jalankan test script:
```bash
python3 /tmp/test_disaster_filtering.py
```

### Manual Test
```bash
# Check disaster warnings endpoint
curl http://localhost:8001/api/disaster-warnings | python3 -m json.tool

# Check current BMKG earthquake data
curl https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json | python3 -m json.tool
```

## Known Issues

### BMKG Weather XML API
- **Issue**: XML parsing error pada beberapa file BMKG
- **Error**: `mismatched tag: line 30, column 2`
- **Impact**: Cuaca ekstrim mungkin tidak terdeteksi untuk beberapa provinsi
- **Workaround**: Logic sudah diimplementasi, akan berfungsi ketika BMKG memperbaiki format XML
- **Status**: Cuaca normal tetap berfungsi via endpoint `/api/weather`

### Earthquake Data Availability
- **Dependency**: Bergantung pada ketersediaan API BMKG
- **Update Frequency**: Data gempa terbaru dari BMKG (real-time)

## Konfigurasi

### Mengubah Threshold Jarak
Edit file `/app/backend/server.py`:
```python
# Line ~875-880 dalam fungsi get_disaster_warnings()
if magnitude >= 5.5 and distance_km <= 500:  # Ubah nilai 500
    show_warning = True
elif magnitude >= 4.5 and distance_km <= 300:  # Ubah nilai 300
    show_warning = True
elif magnitude >= 3.5 and distance_km <= 100:  # Ubah nilai 100
    show_warning = True
```

### Mengubah Kriteria Cuaca Ekstrim
Edit file `/app/backend/server.py`:
```python
# Line ~920-925
extreme_weather = {
    61: "Hujan Sedang",
    63: "Hujan Lebat",
    95: "Hujan Petir",
    97: "Hujan Petir Kuat"
    # Tambah code lain jika diperlukan
}
```

## API Response Format

### Response dengan Peringatan
```json
{
  "has_warning": true,
  "warnings": [
    {
      "type": "gempa",
      "title": "PERINGATAN GEMPA BUMI",
      "magnitude": "5.6",
      "depth": "10 km",
      "location": "150 km BaratLaut Malang",
      "time": "09 Des 2025 10:30:15 WIB",
      "distance": "177 km dari lokasi Anda",
      "potential": "Tidak berpotensi tsunami"
    },
    {
      "type": "cuaca",
      "title": "PERINGATAN CUACA EKSTRIM",
      "condition": "Hujan Lebat",
      "location": "Malang",
      "message": "Waspadai Hujan Lebat di wilayah Malang"
    }
  ]
}
```

### Response Tanpa Peringatan
```json
{
  "has_warning": false,
  "message": "Tidak ada peringatan bencana saat ini"
}
```

## Maintenance

### Log Monitoring
```bash
# Backend logs
tail -f /var/log/supervisor/backend.*.log | grep -i "warning\|earthquake\|weather"

# Check for errors
grep "Error fetching disaster warnings" /var/log/supervisor/backend.err.log
```

### Debug Mode
Untuk melihat detail filtering:
```bash
# Lihat log backend untuk informasi jarak dan keputusan filtering
tail -f /var/log/supervisor/backend.err.log | grep "Earthquake warning"
```

## Future Improvements

1. **Database Caching**: Cache data gempa untuk mengurangi API calls
2. **Historical Data**: Simpan riwayat peringatan bencana
3. **Notification System**: Push notification untuk peringatan bencana
4. **Multiple Source**: Integrasi dengan sumber data lain selain BMKG
5. **Customizable Radius**: Admin panel untuk mengatur threshold jarak dari UI
6. **Weather Warning Types**: Tambah jenis peringatan (banjir, longsor, angin kencang)

## Credits

- **Data Source**: Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)
- **Distance Calculation**: Haversine Formula
- **Integration**: Emergent AI Platform

---

**Last Updated**: 9 Desember 2025
**Version**: 1.0.0
