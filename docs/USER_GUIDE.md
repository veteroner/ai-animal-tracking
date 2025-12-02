# 📖 Kullanıcı Kılavuzu

Bu dokümanda AI Animal Tracking System'in kullanımı anlatılmaktadır.

---

## 🚀 Hızlı Başlangıç

### Temel Kullanım

```bash
# Virtual environment'ı aktifleştirin
source venv/bin/activate

# Webcam ile başlatın
python src/main.py --camera 0
```

### Telefon Kamerası ile

```bash
# IP Webcam uygulamasını telefonunuzda başlatın
# IP adresini kullanın
python src/main.py --camera "http://192.168.1.100:8080/video"
```

---

## ⌨️ Klavye Kısayolları

| Tuş | İşlev |
|-----|-------|
| `q` | Uygulamayı kapat |
| `s` | Snapshot kaydet |
| `r` | FPS sayacını sıfırla |
| `p` | Durakla/Devam et |
| `+` | Confidence artır |
| `-` | Confidence azalt |

---

## 🎛️ Komut Satırı Parametreleri

### Temel Parametreler

```bash
python src/main.py [OPTIONS]

Parametreler:
  --camera, -c       Kamera kaynağı (varsayılan: 0)
  --model, -m        YOLO model ismi (varsayılan: yolov8n.pt)
  --confidence       Tespit eşiği (varsayılan: 0.5)
  --no-display       Video gösterimini kapat
  --save-video, -s   Video kaydet
  --output, -o       Çıkış dosya yolu
  --log-level        Log seviyesi (DEBUG, INFO, WARNING, ERROR)
```

### Örnekler

```bash
# Yüksek doğruluklu tespit
python src/main.py --camera 0 --model yolov8m.pt --confidence 0.7

# Video kaydet
python src/main.py --camera 0 --save-video --output output.mp4

# Headless mod (sunucu için)
python src/main.py --camera 0 --no-display --save-video

# Debug modu
python src/main.py --camera 0 --log-level DEBUG
```

---

## 📹 Kamera Kaynakları

### USB Webcam
```bash
# İlk webcam
python src/main.py --camera 0

# İkinci webcam
python src/main.py --camera 1
```

### Video Dosyası
```bash
python src/main.py --camera path/to/video.mp4
```

### IP Kamera (RTSP)
```bash
python src/main.py --camera "rtsp://user:pass@192.168.1.100:554/stream1"
```

### HTTP Stream
```bash
# IP Webcam (Android)
python src/main.py --camera "http://192.168.1.100:8080/video"

# DroidCam
python src/main.py --camera "http://192.168.1.100:4747/video"
```

---

## 🎯 YOLO Model Seçimi

| Model | Boyut | Hız | Doğruluk | Kullanım Alanı |
|-------|-------|-----|----------|----------------|
| yolov8n | 6.3 MB | ⚡⚡⚡ | ⭐⭐ | Gerçek zamanlı, düşük donanım |
| yolov8s | 22.4 MB | ⚡⚡ | ⭐⭐⭐ | Dengeli performans |
| yolov8m | 52.0 MB | ⚡ | ⭐⭐⭐⭐ | Yüksek doğruluk |
| yolov8l | 83.7 MB | 🐢 | ⭐⭐⭐⭐⭐ | Maksimum doğruluk |
| yolov8x | 136.7 MB | 🐢🐢 | ⭐⭐⭐⭐⭐ | En yüksek doğruluk |

### Öneriler
- **Ev testi için:** yolov8n (en hızlı)
- **Dengeli kullanım:** yolov8s
- **Üretim ortamı:** yolov8m veya yolov8l

---

## 🖥️ Web Arayüzü

### API Sunucusunu Başlatma

```bash
# Geliştirme modu
python -m uvicorn src.api.main:app --reload

# Üretim modu
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Erişim Noktaları

- **Ana Sayfa:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 📊 Tespit Edilen Hayvanlar

Sistem varsayılan olarak aşağıdaki COCO sınıflarını tespit eder:

| ID | İngilizce | Türkçe |
|----|-----------|--------|
| 14 | bird | Kuş |
| 15 | cat | Kedi |
| 16 | dog | Köpek |
| 17 | horse | At |
| 18 | sheep | Koyun |
| 19 | cow | İnek |

---

## 📁 Çıktı Dosyaları

### Dosya Konumları

```
data/
├── videos/          # Kaydedilen videolar
│   └── output_20231201_143022.mp4
├── snapshots/       # Anlık görüntüler
│   └── snapshot_20231201_143100.jpg
└── exports/         # Dışa aktarılan veriler
    └── detections_20231201.csv
```

### Video Kayıt Formatı

- **Format:** MP4 (H.264)
- **Codec:** mp4v
- **Çözünürlük:** Kaynak kamera ile aynı
- **FPS:** Kaynak kamera ile aynı

---

## ⚙️ Konfigürasyon Dosyaları

### Kamera Ayarları (`config/camera_config.yaml`)

```yaml
cameras:
  - id: "cam_01"
    name: "Ana Kamera"
    source: 0
    resolution:
      width: 1280
      height: 720
    fps: 30
```

### Model Ayarları (`config/model_config.yaml`)

```yaml
detection:
  model_name: "yolov8n.pt"
  confidence_threshold: 0.5
  device: "auto"
  
tracking:
  algorithm: "deepsort"
  max_age: 70
  min_hits: 3
```

---

## 🐛 Sorun Giderme

### Düşük FPS

1. Daha küçük model kullanın: `--model yolov8n.pt`
2. Çözünürlüğü düşürün
3. GPU kullanımını kontrol edin

### Tespit Yapılmıyor

1. Confidence değerini düşürün: `--confidence 0.3`
2. Işık koşullarını kontrol edin
3. Kamera odağını kontrol edin

### Kamera Bağlanmıyor

1. Kamera index'ini kontrol edin
2. IP adresini doğrulayın
3. Firewall ayarlarını kontrol edin

### Bellek Hatası

1. Video buffer boyutunu azaltın
2. Batch size'ı düşürün
3. Daha küçük model kullanın

---

## 📊 Performans İpuçları

### Genel Optimizasyonlar

1. **GPU Kullanın:** NVIDIA GPU ile 3-5x hız artışı
2. **Doğru Model:** İhtiyaca göre model seçin
3. **Çözünürlük:** 720p genellikle yeterli
4. **FPS:** 15-30 fps yeterli olabilir

### macOS (Apple Silicon)

```bash
# MPS (Metal Performance Shaders) kullanımı
# Otomatik tespit edilir, .env'de:
MODEL_DEVICE=mps
```

### NVIDIA GPU

```bash
# CUDA kullanımı
MODEL_DEVICE=cuda

# Belirli GPU
MODEL_DEVICE=cuda:0
```

---

## 📚 Sonraki Adımlar

1. [API Dokümantasyonu](API.md) - REST API kullanımı
2. [Model Eğitimi](TRAINING.md) - Özel model eğitimi
3. [Proje Planı](../PROJE_PLANI.md) - Geliştirme yol haritası
