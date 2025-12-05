import { useState, useEffect } from "react";
import "@/styles/PreviewPage.css";

const PreviewPage = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  
  const refreshDisplay = () => {
    setRefreshKey(prev => prev + 1);
  };

  useEffect(() => {
    // Auto refresh every 5 seconds
    const interval = setInterval(() => {
      refreshDisplay();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="preview-container" data-testid="preview-container">
      <div className="preview-header">
        <h1>Preview Panel Pengaturan & Display</h1>
        <button onClick={refreshDisplay} className="refresh-btn">
          🔄 Refresh Display
        </button>
      </div>
      
      <div className="preview-content">
        {/* Left Side - Admin Panel */}
        <div className="preview-admin">
          <div className="panel-label">Panel Admin</div>
          <iframe 
            src="/admin"
            title="Admin Panel"
            className="admin-iframe"
          />
        </div>
        
        {/* Right Side - Display Preview */}
        <div className="preview-display">
          <div className="panel-label">Display Preview (4K TV)</div>
          <iframe 
            key={refreshKey}
            src="/display"
            title="Display Preview"
            className="display-iframe"
          />
        </div>
      </div>
      
      <div className="preview-footer">
        <div className="info-box">
          <strong>Cara Menggunakan:</strong>
          <ol>
            <li>Ubah pengaturan di Panel Admin (kiri)</li>
            <li>Klik "Simpan Pengaturan"</li>
            <li>Display Preview (kanan) akan otomatis refresh dalam 5 detik</li>
            <li>Atau klik tombol "🔄 Refresh Display" untuk refresh manual</li>
          </ol>
        </div>
        
        <div className="info-box">
          <strong>Tips:</strong>
          <ul>
            <li>Gunakan untuk preview perubahan tema (Gelap/Cerah)</li>
            <li>Test perubahan nama masjid, alamat, dan logo</li>
            <li>Cek pengaturan waktu iqomah</li>
            <li>Preview sebelum tampil di TV 4K</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PreviewPage;
