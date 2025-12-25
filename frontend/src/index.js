import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import * as serviceWorkerRegistration from './serviceWorkerRegistration';

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

// Register service worker for PWA
serviceWorkerRegistration.register({
  onSuccess: () => {
    console.log('[PWA] Content is cached for offline use.');
  },
  onUpdate: (registration) => {
    console.log('[PWA] New version available! Please refresh.');
    // Automatically update service worker
    if (registration && registration.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' });
      window.location.reload();
    }
  },
});

// Request persistent storage
serviceWorkerRegistration.requestPersistentStorage();

// Setup offline listener
serviceWorkerRegistration.setupOfflineListener(
  () => console.log('[PWA] Connection restored'),
  () => console.log('[PWA] Connection lost - running offline')
);
