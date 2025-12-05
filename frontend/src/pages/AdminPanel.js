import { useEffect, useState } from "react";
import axios from "axios";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import "@/styles/AdminPanel.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminPanel = () => {
  const [settings, setSettings] = useState(null);
  const [announcements, setAnnouncements] = useState([]);
  const [quranVerses, setQuranVerses] = useState([]);
  const [financialReports, setFinancialReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const [settingsRes, announcementsRes, versesRes, reportsRes] = await Promise.all([
        axios.get(`${API}/settings`),
        axios.get(`${API}/announcements?active_only=false`),
        axios.get(`${API}/quran-verses?active_only=false`),
        axios.get(`${API}/financial-reports`)
      ]);

      setSettings(settingsRes.data);
      setAnnouncements(announcementsRes.data);
      setQuranVerses(versesRes.data);
      setFinancialReports(reportsRes.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching data:", error);
      toast.error("Gagal memuat data");
      setLoading(false);
    }
  };

  // Settings handlers
  const updateSettings = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/settings`, settings);
      toast.success("Pengaturan berhasil diperbarui!");
    } catch (error) {
      console.error("Error updating settings:", error);
      toast.error("Gagal memperbarui pengaturan");
    }
  };

  // Announcement handlers
  const addAnnouncement = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newAnnouncement = {
      text: formData.get("text"),
      priority: parseInt(formData.get("priority") || "1"),
      active: true
    };

    try {
      await axios.post(`${API}/announcements`, newAnnouncement);
      toast.success("Pengumuman berhasil ditambahkan!");
      fetchAllData();
      e.target.reset();
    } catch (error) {
      console.error("Error adding announcement:", error);
      toast.error("Gagal menambahkan pengumuman");
    }
  };

  const deleteAnnouncement = async (id) => {
    try {
      await axios.delete(`${API}/announcements/${id}`);
      toast.success("Pengumuman berhasil dihapus!");
      fetchAllData();
    } catch (error) {
      console.error("Error deleting announcement:", error);
      toast.error("Gagal menghapus pengumuman");
    }
  };

  // Quran verse handlers
  const addQuranVerse = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newVerse = {
      arabic: formData.get("arabic"),
      translation: formData.get("translation"),
      reference: formData.get("reference"),
      active: true
    };

    try {
      await axios.post(`${API}/quran-verses`, newVerse);
      toast.success("Ayat berhasil ditambahkan!");
      fetchAllData();
      e.target.reset();
    } catch (error) {
      console.error("Error adding verse:", error);
      toast.error("Gagal menambahkan ayat");
    }
  };

  const deleteQuranVerse = async (id) => {
    try {
      await axios.delete(`${API}/quran-verses/${id}`);
      toast.success("Ayat berhasil dihapus!");
      fetchAllData();
    } catch (error) {
      console.error("Error deleting verse:", error);
      toast.error("Gagal menghapus ayat");
    }
  };

  // Financial report handlers
  const addFinancialReport = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const newReport = {
      title: formData.get("title"),
      amount: parseFloat(formData.get("amount")),
      period: formData.get("period"),
      description: formData.get("description") || ""
    };

    try {
      await axios.post(`${API}/financial-reports`, newReport);
      toast.success("Laporan keuangan berhasil ditambahkan!");
      fetchAllData();
      e.target.reset();
    } catch (error) {
      console.error("Error adding report:", error);
      toast.error("Gagal menambahkan laporan");
    }
  };

  const deleteFinancialReport = async (id) => {
    try {
      await axios.delete(`${API}/financial-reports/${id}`);
      toast.success("Laporan berhasil dihapus!");
      fetchAllData();
    } catch (error) {
      console.error("Error deleting report:", error);
      toast.error("Gagal menghapus laporan");
    }
  };

  if (loading) {
    return (
      <div className="admin-loading" data-testid="admin-loading">
        <div className="loading-spinner"></div>
        <p>Memuat panel admin...</p>
      </div>
    );
  }

  return (
    <div className="admin-container" data-testid="admin-container">
      <Toaster />
      
      <div className="admin-header">
        <h1 className="admin-title" data-testid="admin-title">Admin Tampilan Masjid</h1>
        <Button 
          onClick={() => window.open('/display', '_blank')}
          data-testid="view-display-btn"
        >
          Lihat Tampilan
        </Button>
      </div>

      <Tabs defaultValue="settings" className="admin-tabs">
        <TabsList className="admin-tabs-list">
          <TabsTrigger value="settings" data-testid="tab-settings">Pengaturan</TabsTrigger>
          <TabsTrigger value="announcements" data-testid="tab-announcements">Pengumuman</TabsTrigger>
          <TabsTrigger value="quran" data-testid="tab-quran">Ayat Al-Quran</TabsTrigger>
          <TabsTrigger value="financial" data-testid="tab-financial">Keuangan</TabsTrigger>
        </TabsList>

        {/* Settings Tab */}
        <TabsContent value="settings">
          <Card>
            <CardHeader>
              <CardTitle>Pengaturan Masjid</CardTitle>
              <CardDescription>Konfigurasi perhitungan waktu sholat dan pengaturan tampilan</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={updateSettings} className="settings-form">
                <div className="form-group">
                  <Label htmlFor="mosque_name">Nama Masjid</Label>
                  <Input
                    id="mosque_name"
                    data-testid="input-mosque-name"
                    value={settings?.mosque_name || ""}
                    onChange={(e) => setSettings({...settings, mosque_name: e.target.value})}
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <Label htmlFor="latitude">Latitude</Label>
                    <Input
                      id="latitude"
                      type="number"
                      step="0.000001"
                      data-testid="input-latitude"
                      value={settings?.latitude || ""}
                      onChange={(e) => setSettings({...settings, latitude: parseFloat(e.target.value)})}
                    />
                  </div>
                  <div className="form-group">
                    <Label htmlFor="longitude">Longitude</Label>
                    <Input
                      id="longitude"
                      type="number"
                      step="0.000001"
                      data-testid="input-longitude"
                      value={settings?.longitude || ""}
                      onChange={(e) => setSettings({...settings, longitude: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <Label htmlFor="timezone">Zona Waktu</Label>
                  <Input
                    id="timezone"
                    data-testid="input-timezone"
                    value={settings?.timezone || ""}
                    onChange={(e) => setSettings({...settings, timezone: e.target.value})}
                    placeholder="contoh: Asia/Jakarta"
                  />
                </div>

                <div className="form-group">
                  <Label htmlFor="background_image">URL Gambar Latar Belakang</Label>
                  <Input
                    id="background_image"
                    data-testid="input-background"
                    value={settings?.background_image || ""}
                    onChange={(e) => setSettings({...settings, background_image: e.target.value})}
                  />
                </div>

                <Button type="submit" className="submit-btn" data-testid="save-settings-btn">
                  Simpan Pengaturan
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Announcements Tab */}
        <TabsContent value="announcements">
          <Card>
            <CardHeader>
              <CardTitle>Pengumuman</CardTitle>
              <CardDescription>Kelola pengumuman masjid</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={addAnnouncement} className="add-form">
                <div className="form-group">
                  <Label htmlFor="ann_text">Teks Pengumuman</Label>
                  <Textarea
                    id="ann_text"
                    name="text"
                    data-testid="input-announcement-text"
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="ann_priority">Prioritas (1-5)</Label>
                  <Input
                    id="ann_priority"
                    name="priority"
                    type="number"
                    min="1"
                    max="5"
                    defaultValue="1"
                    data-testid="input-announcement-priority"
                  />
                </div>
                <Button type="submit" data-testid="add-announcement-btn">Tambah Pengumuman</Button>
              </form>

              <div className="items-list">
                {announcements.map((ann) => (
                  <div key={ann.id} className="item-card" data-testid={`announcement-item-${ann.id}`}>
                    <div className="item-content">
                      <p>{ann.text}</p>
                      <span className="item-meta">Prioritas: {ann.priority}</span>
                    </div>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => deleteAnnouncement(ann.id)}
                      data-testid={`delete-announcement-${ann.id}`}
                    >
                      Hapus
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quran Verses Tab */}
        <TabsContent value="quran">
          <Card>
            <CardHeader>
              <CardTitle>Ayat Al-Quran</CardTitle>
              <CardDescription>Kelola ayat Al-Quran untuk ditampilkan</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={addQuranVerse} className="add-form">
                <div className="form-group">
                  <Label htmlFor="verse_arabic">Teks Arab</Label>
                  <Textarea
                    id="verse_arabic"
                    name="arabic"
                    data-testid="input-verse-arabic"
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="verse_translation">Terjemahan</Label>
                  <Textarea
                    id="verse_translation"
                    name="translation"
                    data-testid="input-verse-translation"
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="verse_reference">Referensi (contoh: Surah Al-Baqarah 2:255)</Label>
                  <Input
                    id="verse_reference"
                    name="reference"
                    data-testid="input-verse-reference"
                    required
                  />
                </div>
                <Button type="submit" data-testid="add-verse-btn">Tambah Ayat</Button>
              </form>

              <div className="items-list">
                {quranVerses.map((verse) => (
                  <div key={verse.id} className="item-card" data-testid={`verse-item-${verse.id}`}>
                    <div className="item-content">
                      <p className="arabic-text">{verse.arabic}</p>
                      <p>{verse.translation}</p>
                      <span className="item-meta">{verse.reference}</span>
                    </div>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => deleteQuranVerse(verse.id)}
                      data-testid={`delete-verse-${verse.id}`}
                    >
                      Hapus
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Financial Tab */}
        <TabsContent value="financial">
          <Card>
            <CardHeader>
              <CardTitle>Laporan Keuangan</CardTitle>
              <CardDescription>Kelola informasi keuangan masjid</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={addFinancialReport} className="add-form">
                <div className="form-group">
                  <Label htmlFor="fin_title">Judul</Label>
                  <Input
                    id="fin_title"
                    name="title"
                    data-testid="input-financial-title"
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="fin_amount">Jumlah (Rp)</Label>
                  <Input
                    id="fin_amount"
                    name="amount"
                    type="number"
                    step="0.01"
                    data-testid="input-financial-amount"
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="fin_period">Periode</Label>
                  <Input
                    id="fin_period"
                    name="period"
                    data-testid="input-financial-period"
                    placeholder="contoh: Januari 2025"
                    required
                  />
                </div>
                <div className="form-group">
                  <Label htmlFor="fin_description">Keterangan</Label>
                  <Textarea
                    id="fin_description"
                    name="description"
                    data-testid="input-financial-description"
                  />
                </div>
                <Button type="submit" data-testid="add-financial-btn">Tambah Laporan</Button>
              </form>

              <div className="items-list">
                {financialReports.map((report) => (
                  <div key={report.id} className="item-card" data-testid={`financial-item-${report.id}`}>
                    <div className="item-content">
                      <h4>{report.title}</h4>
                      <p className="amount">Rp {report.amount.toLocaleString()}</p>
                      <span className="item-meta">{report.period}</span>
                      {report.description && <p className="description">{report.description}</p>}
                    </div>
                    <Button 
                      variant="destructive" 
                      size="sm"
                      onClick={() => deleteFinancialReport(report.id)}
                      data-testid={`delete-financial-${report.id}`}
                    >
                      Hapus
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AdminPanel;