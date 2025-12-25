import { BrowserRouter, Routes, Route } from "react-router-dom";
import DisplayView from "./pages/DisplayView";
import AdminPanel from "./pages/AdminPanel";
import PreviewPage from "./pages/PreviewPage";
import PWAInstallPrompt from "./components/PWAInstallPrompt";
import "@/App.css";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DisplayView />} />
          <Route path="/display" element={<DisplayView />} />
          <Route path="/admin" element={<AdminPanel />} />
          <Route path="/preview" element={<PreviewPage />} />
        </Routes>
      </BrowserRouter>
      <PWAInstallPrompt />
    </div>
  );
}

export default App;