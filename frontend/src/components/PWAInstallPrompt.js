import React, { useState, useEffect } from 'react';

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showInstallButton, setShowInstallButton] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [showManualInstructions, setShowManualInstructions] = useState(false);

  useEffect(() => {
    // Check if app is already installed (standalone mode)
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true);
      console.log('[PWA] App is running in standalone mode (installed)');
      return;
    }

    // Check if running as installed PWA
    if (window.navigator.standalone === true) {
      setIsInstalled(true);
      console.log('[PWA] App is running as standalone (iOS)');
      return;
    }

    // Always show install button if not installed
    setShowInstallButton(true);

    // Listen for beforeinstallprompt event
    const handleBeforeInstallPrompt = (e) => {
      console.log('[PWA] beforeinstallprompt event fired');
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallButton(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Listen for app installed event
    const handleAppInstalled = () => {
      setIsInstalled(true);
      setShowInstallButton(false);
      setDeferredPrompt(null);
      console.log('[PWA] App was installed successfully');
    };

    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (deferredPrompt) {
      // Use native install prompt
      console.log('[PWA] Showing native install prompt');
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`[PWA] User response: ${outcome}`);
      
      if (outcome === 'accepted') {
        setShowInstallButton(false);
      }
      setDeferredPrompt(null);
    } else {
      // Show manual instructions
      console.log('[PWA] No deferred prompt, showing manual instructions');
      setShowManualInstructions(true);
    }
  };

  const detectBrowser = () => {
    const ua = navigator.userAgent;
    if (/Chrome/i.test(ua) && !/Edge|Edg/i.test(ua)) return 'chrome';
    if (/Edge|Edg/i.test(ua)) return 'edge';
    if (/Safari/i.test(ua) && !/Chrome/i.test(ua)) return 'safari';
    if (/Firefox/i.test(ua)) return 'firefox';
    return 'other';
  };

  const getInstallInstructions = () => {
    const browser = detectBrowser();
    
    const instructions = {
      chrome: [
        '1. Klik ikon menu (⋮) di kanan atas browser',
        '2. Pilih "Install App" atau "Add to Home Screen"',
        '3. Klik "Install" pada popup yang muncul'
      ],
      edge: [
        '1. Klik ikon menu (⋯) di kanan atas browser',
        '2. Pilih "Apps" → "Install this site as an app"',
        '3. Klik "Install" pada popup yang muncul'
      ],
      safari: [
        '1. Tap ikon Share (kotak dengan panah ke atas)',
        '2. Scroll dan pilih "Add to Home Screen"',
        '3. Tap "Add" di pojok kanan atas'
      ],
      firefox: [
        '1. Firefox tidak mendukung PWA install otomatis',
        '2. Gunakan Chrome atau Edge untuk install',
        '3. Atau bookmark halaman ini untuk akses cepat'
      ],
      other: [
        '1. Buka di Chrome atau Edge untuk install',
        '2. Atau gunakan menu browser untuk bookmark',
        '3. Pilih "Add to Home Screen" jika tersedia'
      ]
    };
    
    return instructions[browser] || instructions.other;
  };

  // Don't show if already installed
  if (isInstalled) {
    return null;
  }

  // Don't show on admin page
  if (window.location.pathname.includes('/admin')) {
    return null;
  }

  return (
    <>
      {/* Floating Install Button */}
      {showInstallButton && (
        <button
          onClick={handleInstallClick}
          style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            background: 'linear-gradient(135deg, #22C55E 0%, #16A34A 100%)',
            color: 'white',
            border: 'none',
            borderRadius: '50px',
            padding: '12px 20px',
            fontSize: '14px',
            fontWeight: 'bold',
            cursor: 'pointer',
            boxShadow: '0 4px 15px rgba(34, 197, 94, 0.4)',
            zIndex: 10000,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'transform 0.2s, box-shadow 0.2s'
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.transform = 'scale(1.05)';
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(34, 197, 94, 0.5)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 4px 15px rgba(34, 197, 94, 0.4)';
          }}
        >
          <span style={{ fontSize: '18px' }}>📲</span>
          Install App
        </button>
      )}

      {/* Manual Instructions Modal */}
      {showManualInstructions && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10001,
            padding: '20px'
          }}
          onClick={() => setShowManualInstructions(false)}
        >
          <div
            style={{
              background: '#1E293B',
              borderRadius: '16px',
              padding: '24px',
              maxWidth: '400px',
              width: '100%',
              color: 'white'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
              <span style={{ fontSize: '32px' }}>🕌</span>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px' }}>Cara Install Aplikasi</h3>
                <p style={{ margin: '4px 0 0', opacity: 0.7, fontSize: '13px' }}>
                  {detectBrowser() === 'chrome' && 'Google Chrome'}
                  {detectBrowser() === 'edge' && 'Microsoft Edge'}
                  {detectBrowser() === 'safari' && 'Safari'}
                  {detectBrowser() === 'firefox' && 'Firefox'}
                  {detectBrowser() === 'other' && 'Browser Anda'}
                </p>
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              {getInstallInstructions().map((step, index) => (
                <div
                  key={index}
                  style={{
                    padding: '12px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px',
                    marginBottom: '8px',
                    fontSize: '14px'
                  }}
                >
                  {step}
                </div>
              ))}
            </div>

            <div style={{ 
              padding: '12px', 
              background: 'rgba(34, 197, 94, 0.2)', 
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '13px'
            }}>
              💡 <strong>Tip:</strong> Setelah install, aplikasi bisa berjalan fullscreen dan offline!
            </div>

            <button
              onClick={() => setShowManualInstructions(false)}
              style={{
                width: '100%',
                padding: '12px',
                background: '#22C55E',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: 'bold',
                cursor: 'pointer',
                fontSize: '14px'
              }}
            >
              Mengerti
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default PWAInstallPrompt;
