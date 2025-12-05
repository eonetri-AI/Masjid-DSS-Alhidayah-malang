import { BrowserRouter, Routes, Route } from "react-router-dom";
import DisplayView from "./pages/DisplayView";
import AdminPanel from "./pages/AdminPanel";
import "@/App.css";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<DisplayView />} />
          <Route path="/display" element={<DisplayView />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;