# 🐄 AI Animal Tracking and Behavior Analysis System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![YOLOv8](https://img.shields.io/badge/YOLO-v8-green.svg)](https://ultralytics.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.123+-orange.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Çiftlik hayvanlarının gerçek zamanlı tespiti, takibi, davranış analizi ve sağlık izleme sistemi.

## 🌟 Özellikler

- 🎯 **Gerçek Zamanlı Tespit**: YOLOv8 ile hayvan tespiti
- 🔍 **Nesne Takibi**: ByteTrack ile sürekli takip
- 🏷️ **Benzersiz Kimlik**: Her hayvana ID atama ve Re-ID
- 🐾 **Davranış Analizi**: Yeme, yürüme, dinlenme tespiti
- 🏥 **Sağlık İzleme**: Vücut kondisyon skoru, topallama tespiti
- 📊 **Analitik**: Detaylı raporlar ve trendler
- 🔔 **Akıllı Uyarılar**: Kritik durumlar için otomatik bildirim
- 🌐 **Web Dashboard**: Streamlit ile modern arayüz
- 📱 **Mobil Destek**: Telefon kamerası entegrasyonu
- 🔌 **REST API**: FastAPI ile 60+ endpoint

## 📦 Modüller

| Modül | Durum | Açıklama |
|-------|-------|----------|
| `src/camera` | ✅ | Multi-kamera yönetimi, frame buffer |
| `src/detection` | ✅ | YOLOv8 hayvan tespiti |
| `src/tracking` | ✅ | ByteTrack nesne takibi |
| `src/identification` | ✅ | Benzersiz hayvan kimliği |
| `src/behavior` | ✅ | Davranış analizi |
| `src/health` | ✅ | Sağlık izleme (BCS, topallık) |
| `src/feeding` | ✅ | Yem takibi ve tüketim tahmini |
| `src/database` | ✅ | SQLAlchemy ORM (8 tablo) |
| `src/alerts` | ✅ | Uyarı sistemi |
| `src/pipeline` | ✅ | Entegre işlem hattı |
| `src/api` | ✅ | FastAPI REST API (67 endpoint) |
| `src/ui` | ✅ | Streamlit dashboard |
| `src/export` | ✅ | CSV/JSON/Excel export, webhook |
| `src/notifications` | ✅ | Bildirim sistemi |

## 🚀 Hızlı Başlangıç

### Gereksinimler

- Python 3.9+
- pip
- Webcam veya IP kamera
- (Opsiyonel) Apple Silicon MPS veya NVIDIA GPU

### Kurulum

```bash
# 1. Repository'yi klonlayın
git clone <repo-url>
cd ai_goruntu_isleme

# 2. Virtual environment oluşturun
python -m venv venv
source venv/bin/activate  # macOS/Linux
# veya
.\venv\Scripts\activate  # Windows

# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### İlk Çalıştırma

```bash
# Webcam ile hızlı demo
python demo.py

# veya belirli bir kamera ile
python demo.py --source 0

# IP kamera ile
python src/main.py --camera "rtsp://192.168.1.100:554/stream"

# Telefon kamerası ile (IP Webcam uygulaması)
python src/main.py --camera "http://192.168.1.100:8080/video"
```

## 📁 Proje Yapısı

```
ai_goruntu_isleme/
├── config/              # Konfigürasyon dosyaları
├── src/                 # Kaynak kodları
│   ├── core/           # Çekirdek modüller
│   ├── camera/         # Kamera yönetimi
│   ├── detection/      # Nesne tespiti (YOLO)
│   ├── tracking/       # Nesne takibi (DeepSORT)
│   ├── identification/ # Hayvan kimlik sistemi
│   ├── behavior/       # Davranış analizi
│   ├── health/         # Sağlık izleme
│   ├── api/            # REST API
│   └── database/       # Veritabanı
├── web/                # Web arayüzü
├── models/             # AI modelleri
├── data/               # Veri dizini
├── tests/              # Testler
├── docker/             # Docker dosyaları
└── docs/               # Dokümantasyon
```

## 📖 Dokümantasyon

- [Proje Planı](PROJE_PLANI.md) - Detaylı proje planı ve checklist
- [Kurulum Kılavuzu](docs/INSTALLATION.md)
- [API Dokümantasyonu](docs/API.md)
- [Kullanıcı Kılavuzu](docs/USER_GUIDE.md)
- [Model Eğitimi](docs/TRAINING.md)

## 🔧 Konfigürasyon

### Kamera Ayarları

```yaml
# config/camera_config.yaml
cameras:
  - id: "cam_01"
    name: "Ana Kamera"
    source: 0  # Webcam index veya URL
    resolution: [1280, 720]
    fps: 30
```

### Model Ayarları

```yaml
# config/model_config.yaml
detection:
  model: "yolov8n.pt"
  confidence: 0.5
  device: "auto"  # auto, cpu, cuda

tracking:
  algorithm: "deepsort"
  max_age: 30
  min_hits: 3
```

## 🎥 Desteklenen Kameralar

| Tür | Protokol | Örnek |
|-----|----------|-------|
| USB Webcam | V4L2/DirectShow | `0`, `1`, `2` |
| IP Kamera | RTSP | `rtsp://ip:554/stream` |
| IP Kamera | HTTP | `http://ip:8080/video` |
| Telefon | IP Webcam | `http://ip:8080/video` |
| Telefon | DroidCam | `http://ip:4747/video` |

## 📊 API Endpoints

```
# Kameralar
GET  /api/cameras          # Kamera listesi
POST /api/cameras          # Kamera ekle

# Hayvanlar
GET  /api/animals          # Hayvan listesi
GET  /api/animals/{id}     # Hayvan detayı
POST /api/animals          # Hayvan ekle

# Tespit ve Takip
GET  /api/detections       # Tespit verileri
GET  /api/behaviors        # Davranış verileri
GET  /api/health/{id}      # Sağlık durumu

# Yem Takibi
GET  /api/feeding/zones    # Yemlik bölgeleri
GET  /api/feeding/sessions # Beslenme seansları
GET  /api/feeding/stats    # Tüketim istatistikleri

# Analitik ve Export
GET  /api/analytics        # Analitik veriler
POST /api/export/csv       # CSV export
POST /api/export/json      # JSON export
POST /api/webhooks         # Webhook ayarla
```

## 🐳 Docker ile Çalıştırma

### Hızlı Başlangıç (Docker)

```bash
# Development modunda çalıştır
docker-compose up -d

# API'ye erişim: http://localhost:8000
# Dashboard'a erişim: http://localhost:8501
```

### Production Modu

```bash
# PostgreSQL ve Redis ile production
docker-compose --profile production up -d

# Sadece API (production build)
docker build -t animal-tracking:latest .
docker run -p 8000:8000 -v ./data:/app/data animal-tracking:latest
```

### Docker Komutları

```bash
# Build
docker-compose build

# Çalıştır
docker-compose up -d

# Logları izle
docker-compose logs -f api

# Durdur
docker-compose down

# Temizle
docker-compose down -v --rmi all
```

## 🧪 Test

```bash
# Unit testler
pytest tests/unit/

# Integration testler
pytest tests/integration/

# Tüm testler
pytest
```

## 📈 Performans

| Metrik | Hedef | Durum |
|--------|-------|-------|
| Tespit FPS | ≥15 | 🔄 |
| Tespit Doğruluğu | ≥85% | 🔄 |
| Takip Doğruluğu | ≥80% | 🔄 |
| API Yanıt Süresi | <200ms | 🔄 |

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'feat: Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 📞 İletişim

Sorularınız için issue açabilirsiniz.

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!
