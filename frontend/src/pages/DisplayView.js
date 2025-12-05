import { useEffect, useState } from "react";
import axios from "axios";
import Marquee from "react-fast-marquee";
import moment from "moment-hijri";
import "@/styles/DisplayView.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DisplayView = () => {
  const [prayerTimes, setPrayerTimes] = useState(null);
  const [announcements, setAnnouncements] = useState([]);
  const [quranVerses, setQuranVerses] = useState([]);
  const [currentVerse, setCurrentVerse] = useState(0);
  const [financialReports, setFinancialReports] = useState([]);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [settings, setSettings] = useState(null);
  const [countdown, setCountdown] = useState({ hours: 0, minutes: 0, seconds: 0 });
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [password, setPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [weather, setWeather] = useState(null);

  // Fetch all data
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  // Update current time
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Rotate Quran verses
  useEffect(() => {
    if (quranVerses.length > 0) {
      const interval = setInterval(() => {
        setCurrentVerse((prev) => (prev + 1) % quranVerses.length);
      }, 15000); // Change verse every 15 seconds
      return () => clearInterval(interval);
    }
  }, [quranVerses]);

  // Calculate countdown
  useEffect(() => {
    if (prayerTimes && prayerTimes.time_until_next !== undefined) {
      const interval = setInterval(() => {
        const now = new Date();
        const totalSeconds = prayerTimes.time_until_next * 60 - (now.getSeconds());
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        setCountdown({ hours, minutes, seconds });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [prayerTimes]);

  // Handle settings icon click (3 clicks to show password modal)
  useEffect(() => {
    let clickCount = 0;
    let clickTimer = null;

    const handleKeyPress = (e) => {
      if (e.key === 's' || e.key === 'S') {
        clickCount++;
        
        if (clickCount === 1) {
          clickTimer = setTimeout(() => {
            clickCount = 0;
          }, 2000);
        }

        if (clickCount === 3) {
          clearTimeout(clickTimer);
          clickCount = 0;
          setShowPasswordModal(true);
        }
      }
    };

    window.addEventListener('keypress', handleKeyPress);
    return () => {
      window.removeEventListener('keypress', handleKeyPress);
      if (clickTimer) clearTimeout(clickTimer);
    };
  }, []);

  const verifyPassword = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/verify-password`, { password });
      if (response.data.success) {
        window.location.href = '/admin';
      }
    } catch (error) {
      setPasswordError("Password salah. Silakan coba lagi.");
      setPassword("");
    }
  };

  const fetchData = async () => {
    try {
      const [timesRes, announcementsRes, versesRes, reportsRes, settingsRes, weatherRes] = await Promise.all([
        axios.get(`${API}/prayer-times`),
        axios.get(`${API}/announcements`),
        axios.get(`${API}/quran-verses`),
        axios.get(`${API}/financial-reports`),
        axios.get(`${API}/settings`),
        axios.get(`${API}/weather`)
      ]);

      setPrayerTimes(timesRes.data);
      setAnnouncements(announcementsRes.data);
      setQuranVerses(versesRes.data);
      setFinancialReports(reportsRes.data);
      setSettings(settingsRes.data);
      setWeather(weatherRes.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
  };

  const getPrayerArray = () => [
    { name: "Imsya", time: prayerTimes?.imsya, iqomah: null },
    { name: "Subuh", time: prayerTimes?.fajr, iqomah: prayerTimes?.iqomah_times?.fajr },
    { name: "Syuruq", time: prayerTimes?.syuruq, iqomah: null },
    { name: "Dzuhur", time: prayerTimes?.dhuhr, iqomah: prayerTimes?.iqomah_times?.dhuhr },
    { name: "Ashar", time: prayerTimes?.asr, iqomah: prayerTimes?.iqomah_times?.asr },
    { name: "Maghrib", time: prayerTimes?.maghrib, iqomah: prayerTimes?.iqomah_times?.maghrib },
    { name: "Isya", time: prayerTimes?.isha, iqomah: prayerTimes?.iqomah_times?.isha }
  ];

  if (!prayerTimes) {
    return (
      <div className="loading-screen" data-testid="loading-screen">
        <div className="loading-spinner"></div>
        <p>Memuat...</p>
      </div>
    );
  }

  const theme = settings?.theme || "midnight";
  
  return (
    <div className={`display-container theme-${theme}`} data-testid="display-container">
      {/* Background */}
      {settings?.background_image && (
        <div 
          className="background-overlay"
          style={{ backgroundImage: `url(${settings.background_image})` }}
        />
      )}

      {/* Main Grid */}
      <div className="display-grid">
        {/* Mosque Info Header */}
        <div className="mosque-info-header" data-testid="mosque-info-header">
          {settings?.mosque_logo && (
            <img src={settings.mosque_logo} alt="Logo Masjid" className="mosque-logo" />
          )}
          <div className="mosque-details">
            <h1 className="mosque-name">{settings?.mosque_name || "Masjid Al-Noor"}</h1>
            <p className="mosque-address">{settings?.mosque_address || ""}</p>
          </div>
        </div>

        {/* Header - Date & Time */}
        <div className="header-section" data-testid="header-section">
          <div className="date-time-card">
            <div className="current-time" data-testid="current-time">
              {currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
            </div>
            <div className="dates" data-testid="dates">
              <div className="gregorian-date">{prayerTimes.gregorian_date}</div>
              <div className="hijri-date">{prayerTimes.hijri_date}</div>
            </div>
          </div>
        </div>

        {/* Next Prayer Countdown */}
        <div className="countdown-section" data-testid="countdown-section">
          <div className="countdown-card">
            <div className="countdown-label">
              {prayerTimes.is_iqomah_countdown ? "WAKTU IQOMAH" : "SHOLAT BERIKUTNYA"}
            </div>
            <div className="next-prayer-name" data-testid="next-prayer-name">
              {prayerTimes.next_prayer?.toUpperCase()}
            </div>
            <div className="countdown-timer" data-testid="countdown-timer">
              <span className="countdown-number">{String(countdown.hours).padStart(2, '0')}</span>
              <span className="countdown-separator">:</span>
              <span className="countdown-number">{String(countdown.minutes).padStart(2, '0')}</span>
              <span className="countdown-separator">:</span>
              <span className="countdown-number">{String(countdown.seconds).padStart(2, '0')}</span>
            </div>
            <div className="countdown-sublabel">
              {prayerTimes.is_iqomah_countdown ? "hingga Iqomah" : "hingga Adzan"}
            </div>
          </div>
        </div>

        {/* Prayer Times Grid */}
        <div className="prayer-times-section" data-testid="prayer-times-section">
          {getPrayerArray().map((prayer, idx) => (
            <div 
              key={idx}
              className={`prayer-card ${
                prayer.name.toLowerCase() === prayerTimes.next_prayer ? 'active' : ''
              }`}
              data-testid={`prayer-card-${prayer.name.toLowerCase()}`}
            >
              <div className="prayer-name">{prayer.name}</div>
              <div className="prayer-time">{prayer.time}</div>
              {prayer.iqomah && (
                <div className="iqomah-time">Iqomah: {prayer.iqomah}</div>
              )}
            </div>
          ))}
        </div>

        {/* Quran Verse */}
        {quranVerses.length > 0 && (
          <div className="quran-section" data-testid="quran-section">
            <div className="quran-card">
              <div className="quran-arabic">{quranVerses[currentVerse]?.arabic}</div>
              <div className="quran-translation">{quranVerses[currentVerse]?.translation}</div>
              <div className="quran-reference">{quranVerses[currentVerse]?.reference}</div>
            </div>
          </div>
        )}

        {/* Financial Report */}
        {financialReports.length > 0 && (
          <div className="financial-section" data-testid="financial-section">
            <div className="financial-card">
              <div className="financial-title">Laporan Keuangan</div>
              {financialReports[0] && (
                <>
                  <div className="financial-item" data-testid="financial-item-0">
                    <div className="financial-label">Saldo Pekan Lalu</div>
                    <div className="financial-amount">Rp {financialReports[0].saldo_pekan_lalu?.toLocaleString('id-ID')}</div>
                  </div>
                  <div className="financial-item" data-testid="financial-item-1">
                    <div className="financial-label">Infaq Pekan Ini</div>
                    <div className="financial-amount positive">Rp {financialReports[0].infaq_pekan_ini?.toLocaleString('id-ID')}</div>
                  </div>
                  <div className="financial-item" data-testid="financial-item-2">
                    <div className="financial-label">Pengeluaran</div>
                    <div className="financial-amount negative">Rp {financialReports[0].pengeluaran?.toLocaleString('id-ID')}</div>
                  </div>
                  <div className="financial-item financial-total" data-testid="financial-item-3">
                    <div className="financial-label">Saldo Pekan Ini</div>
                    <div className="financial-amount">Rp {financialReports[0].saldo_pekan_ini?.toLocaleString('id-ID')}</div>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Mecca Live Stream */}
        <div className="mecca-section" data-testid="mecca-section">
          <div className="mecca-card">
            <div className="mecca-label">Makkah Live</div>
            <img 
              src="https://images.unsplash.com/photo-1542521148-51306e7ffc1e?q=85&w=1920&auto=format&fit=crop"
              alt="Mecca"
              className="mecca-image"
            />
          </div>
        </div>
      </div>

      {/* Announcements Ticker */}
      {announcements.length > 0 && (
        <div className="announcements-ticker" data-testid="announcements-ticker">
          <Marquee speed={50} gradient={false}>
            {announcements.map((ann, idx) => (
              <span key={idx} className="announcement-text">
                {ann.text} &nbsp;&nbsp;&nbsp;•&nbsp;&nbsp;&nbsp;
              </span>
            ))}
          </Marquee>
        </div>
      )}

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="password-modal-overlay" data-testid="password-modal" onClick={() => setShowPasswordModal(false)}>
          <div className="password-modal" onClick={(e) => e.stopPropagation()}>
            <h2>Akses Panel Admin</h2>
            <p>Tekan tombol 'S' 3x untuk membuka panel ini</p>
            <form onSubmit={verifyPassword}>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan password"
                autoFocus
                data-testid="password-input"
              />
              {passwordError && <p className="error-message">{passwordError}</p>}
              <div className="modal-buttons">
                <button type="submit" data-testid="submit-password-btn">Masuk</button>
                <button type="button" onClick={() => {
                  setShowPasswordModal(false);
                  setPassword("");
                  setPasswordError("");
                }} data-testid="cancel-password-btn">Batal</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default DisplayView;