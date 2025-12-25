// Service Worker for Mosque Digital Signage PWA
// Version 1.0.0

const CACHE_VERSION = 'mosque-signage-v1.0.0';
const RUNTIME_CACHE = 'mosque-runtime-v1';
const API_CACHE = 'mosque-api-v1';

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/display',
  '/admin',
  '/preview',
  '/static/css/main.chunk.css',
  '/static/js/main.chunk.js',
  '/static/js/bundle.js',
  '/manifest.json',
  '/icon-192x192.png',
  '/icon-512x512.png',
  '/icon-192x192.svg',
  '/icon-512x512.svg'
];

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/prayer-times',
  '/api/settings',
  '/api/announcements',
  '/api/quran-verses',
  '/api/financial-reports',
  '/api/weather',
  '/api/weather-forecast',
  '/api/disaster-warnings'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => {
      console.log('[ServiceWorker] Caching static assets');
      return cache.addAll(STATIC_ASSETS.map(url => new Request(url, { cache: 'reload' })))
        .catch((error) => {
          console.error('[ServiceWorker] Cache addAll error:', error);
          // Don't fail installation if some assets fail to cache
          return Promise.resolve();
        });
    }).then(() => {
      console.log('[ServiceWorker] Skip waiting');
      return self.skipWaiting();
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_VERSION && 
              cacheName !== RUNTIME_CACHE && 
              cacheName !== API_CACHE) {
            console.log('[ServiceWorker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[ServiceWorker] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome extensions
  if (url.protocol === 'chrome-extension:') {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleAPIRequest(request));
    return;
  }

  // Handle static assets and pages
  event.respondWith(handleStaticRequest(request));
});

// Handle API requests with Network-First strategy
async function handleAPIRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first
    const networkResponse = await fetch(request);
    
    if (networkResponse && networkResponse.ok) {
      // Cache successful API responses
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
      return networkResponse;
    }
    
    // If network fails, try cache
    return await caches.match(request) || createOfflineResponse(url.pathname);
    
  } catch (error) {
    console.log('[ServiceWorker] Network request failed, trying cache:', url.pathname);
    
    // Return cached version
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline fallback data
    return createOfflineResponse(url.pathname);
  }
}

// Handle static requests with Cache-First strategy
async function handleStaticRequest(request) {
  try {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // If not in cache, fetch from network
    const networkResponse = await fetch(request);
    
    if (networkResponse && networkResponse.ok) {
      // Cache the new resource
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
    
  } catch (error) {
    console.log('[ServiceWorker] Fetch failed for:', request.url);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/display');
    }
    
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable'
    });
  }
}

// Create offline fallback responses for API endpoints
function createOfflineResponse(endpoint) {
  const offlineData = getOfflineFallbackData(endpoint);
  
  return new Response(JSON.stringify(offlineData), {
    status: 200,
    statusText: 'OK (Offline)',
    headers: {
      'Content-Type': 'application/json',
      'X-Offline': 'true'
    }
  });
}

// Offline fallback data for API endpoints
function getOfflineFallbackData(endpoint) {
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();
  
  // Default prayer times (fallback)
  if (endpoint.includes('/prayer-times')) {
    return {
      fajr: '04:30',
      syuruq: '05:45',
      dhuhr: '12:00',
      asr: '15:15',
      maghrib: '18:00',
      isha: '19:15',
      imsya: '04:20',
      next_prayer: 'dhuhr',
      is_iqomah_countdown: false,
      iqomah_times: {
        fajr: '04:40',
        dhuhr: '12:10',
        asr: '15:25',
        maghrib: '18:05',
        isha: '19:25'
      },
      date_gregorian: now.toLocaleDateString('id-ID'),
      date_hijri: 'Offline Mode',
      offline: true
    };
  }
  
  // Settings fallback
  if (endpoint.includes('/settings')) {
    return {
      mosque_name: 'MASJID AL HIDAYAH',
      mosque_address: 'Offline Mode',
      city_name: 'Malang',
      latitude: -7.9666,
      longitude: 112.6326,
      theme: 'midnight',
      font_size: 'normal',
      use_manual_prayer_times: false,
      offline: true
    };
  }
  
  // Weather fallback
  if (endpoint.includes('/weather-forecast')) {
    const hourlyForecast = {};
    for (let i = 0; i < 24; i++) {
      hourlyForecast[i] = {
        temperature: 27,
        humidity: 75,
        precipitation: 0,
        weather_code: 1,
        description: 'Cerah Berawan',
        icon: '🌤️',
        source: 'Offline'
      };
    }
    return {
      success: true,
      forecast: hourlyForecast,
      offline: true
    };
  }
  
  if (endpoint.includes('/weather')) {
    return {
      temperature: 27,
      humidity: 75,
      description: 'Cerah Berawan',
      source: 'Offline',
      offline: true
    };
  }
  
  // Announcements fallback
  if (endpoint.includes('/announcements')) {
    return [{
      text: 'Aplikasi dalam mode offline. Data mungkin tidak terbaru.',
      offline: true
    }];
  }
  
  // Quran verses fallback
  if (endpoint.includes('/quran-verses')) {
    return [{
      arabic: 'إِنَّ مَعَ ٱلْعُسْرِ يُسْرًا',
      translation: 'Sesungguhnya bersama kesulitan ada kemudahan',
      surah: 'Al-Insyirah',
      ayah: 6,
      offline: true
    }];
  }
  
  // Financial reports fallback
  if (endpoint.includes('/financial-reports')) {
    return [{
      saldo_pekan_lalu: 0,
      infaq_pekan_ini: 0,
      pengeluaran: 0,
      saldo_pekan_ini: 0,
      offline: true
    }];
  }
  
  // Disaster warnings fallback
  if (endpoint.includes('/disaster-warnings')) {
    return {
      has_warning: false,
      message: 'Mode offline - data peringatan tidak tersedia',
      offline: true
    };
  }
  
  return { offline: true, message: 'Data tidak tersedia' };
}

// Background sync for API updates
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);
  
  if (event.tag === 'sync-prayer-times') {
    event.waitUntil(syncPrayerTimes());
  }
});

// Sync prayer times in background
async function syncPrayerTimes() {
  try {
    const response = await fetch('/api/prayer-times');
    if (response.ok) {
      const cache = await caches.open(API_CACHE);
      cache.put('/api/prayer-times', response);
      console.log('[ServiceWorker] Prayer times synced');
    }
  } catch (error) {
    console.error('[ServiceWorker] Sync failed:', error);
  }
}

// Message handler for commands from client
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);
  
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data.type === 'CACHE_UPDATE') {
    event.waitUntil(updateCache());
  }
  
  if (event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(clearAllCaches());
  }
});

// Update cache manually
async function updateCache() {
  const cache = await caches.open(API_CACHE);
  const promises = API_ENDPOINTS.map(endpoint => 
    fetch(endpoint).then(response => {
      if (response.ok) {
        return cache.put(endpoint, response);
      }
    }).catch(() => {})
  );
  await Promise.all(promises);
  console.log('[ServiceWorker] Cache updated');
}

// Clear all caches
async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map(name => caches.delete(name)));
  console.log('[ServiceWorker] All caches cleared');
}

console.log('[ServiceWorker] Loaded');
