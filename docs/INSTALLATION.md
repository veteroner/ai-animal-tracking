# 📥 Kurulum Kılavuzu

Bu dokümanda AI Animal Tracking System'in kurulumu adım adım anlatılmaktadır.

## 📋 Gereksinimler

### Yazılım Gereksinimleri

| Yazılım | Minimum Versiyon | Önerilen |
|---------|------------------|----------|
| Python | 3.10 | 3.11+ |
| pip | 21.0 | En güncel |
| Git | 2.30 | En güncel |

### Donanım Gereksinimleri

#### Minimum (Test için)
- **CPU:** Intel Core i5 / Apple M1
- **RAM:** 8 GB
- **Disk:** 20 GB boş alan
- **Kamera:** 720p webcam

#### Önerilen (Üretim için)
- **CPU:** Intel Core i7 / Apple M2 Pro
- **RAM:** 16 GB+
- **GPU:** NVIDIA GTX 1060+ (4GB VRAM)
- **Disk:** 100 GB+ SSD
- **Kamera:** 1080p @ 30fps

---

## 🚀 Hızlı Kurulum (macOS/Linux)

```bash
# 1. Repository'yi klonlayın
git clone <repo-url>
cd ai_goruntu_isleme

# 2. Kurulum scriptini çalıştırın
chmod +x scripts/setup_environment.sh
./scripts/setup_environment.sh
```

---

## 📝 Manuel Kurulum

### 1. Python Ortamı

```bash
# Python versiyonunu kontrol edin
python3 --version  # 3.10+ olmalı

# Virtual environment oluşturun
python3 -m venv venv

# Aktifleştirin
source venv/bin/activate  # macOS/Linux
# veya
.\venv\Scripts\activate  # Windows
```

### 2. Bağımlılıkları Yükleyin

```bash
# pip'i güncelleyin
pip install --upgrade pip

# Ana bağımlılıkları yükleyin
pip install -r requirements.txt

# (Opsiyonel) Geliştirici bağımlılıkları
pip install -r requirements-dev.txt
```

### 3. Konfigürasyon

```bash
# .env dosyasını oluşturun
cp .env.example .env

# Düzenleyin
nano .env  # veya tercih ettiğiniz editör
```

### 4. AI Modellerini İndirin

```bash
# YOLO modellerini indirin
python scripts/download_models.py

# veya spesifik modeller için
python scripts/download_models.py --models yolov8n yolov8s yolov8m
```

### 5. Veritabanı (Opsiyonel)

SQLite (varsayılan) kullanıyorsanız ek kurulum gerekmez.

PostgreSQL için:
```bash
# PostgreSQL kurun (macOS)
brew install postgresql
brew services start postgresql

# Veritabanı oluşturun
createdb animal_tracking

# .env'de ayarlayın
# DATABASE_URL=postgresql://user:password@localhost:5432/animal_tracking
```

---

## 🎥 Kamera Kurulumu

### USB Webcam

Ek kurulum gerektirmez. Doğrudan kullanılabilir:
```bash
python src/main.py --camera 0
```

### Telefon Kamerası (Android)

1. **IP Webcam** uygulamasını yükleyin:
   - [Google Play Store](https://play.google.com/store/apps/details?id=com.pas.webcam)

2. Uygulamayı başlatın ve "Start server" a tıklayın

3. IP adresini not edin (örn: `http://192.168.1.100:8080`)

4. Bağlanın:
   ```bash
   python src/main.py --camera "http://192.168.1.100:8080/video"
   ```

### Telefon Kamerası (iOS)

1. **DroidCam** veya benzeri uygulamayı kullanın

2. IP adresi ve port'u kontrol edin

3. Bağlanın:
   ```bash
   python src/main.py --camera "http://192.168.1.100:4747/video"
   ```

### IP Kamera (RTSP)

```bash
python src/main.py --camera "rtsp://username:password@192.168.1.100:554/stream1"
```

---

## 🐳 Docker Kurulumu

### Docker ile Çalıştırma

```bash
# Build
cd docker
docker-compose build

# Çalıştır
docker-compose up -d

# Logları izle
docker-compose logs -f app
```

### GPU Desteği ile

```bash
# NVIDIA Container Toolkit kurulu olmalı
docker build -f docker/Dockerfile.gpu -t animal_tracking:gpu .

# GPU ile çalıştır
docker run --gpus all -p 8000:8000 animal_tracking:gpu
```

---

## ✅ Kurulum Doğrulama

### 1. Python Ortamını Test Edin

```bash
python -c "
import sys
print(f'Python: {sys.version}')

import cv2
print(f'OpenCV: {cv2.__version__}')

import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.cuda.is_available()}')

from ultralytics import YOLO
print('Ultralytics: OK')
"
```

### 2. Kamerayı Test Edin

```bash
# Webcam testi
python src/main.py --camera 0
```

### 3. API'yi Test Edin

```bash
# API'yi başlatın
python -m uvicorn src.api.main:app --reload

# Başka terminalde test edin
curl http://localhost:8000/health
```

---

## 🔧 Sorun Giderme

### OpenCV Kurulum Hataları

```bash
# macOS
brew install opencv

# Ubuntu/Debian
sudo apt-get install libopencv-dev python3-opencv
```

### CUDA Bulunamadı

```bash
# NVIDIA driver kontrol
nvidia-smi

# PyTorch'u CUDA ile yeniden yükle
pip uninstall torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Kamera Açılmıyor

1. Kamera izinlerini kontrol edin (macOS: System Preferences > Security & Privacy > Camera)
2. Başka uygulamanın kamerayı kullandığından emin olun
3. Kamera index'ini kontrol edin (0, 1, 2...)

### Port Kullanımda

```bash
# Portu kullanan process'i bulun
lsof -i :8000

# veya farklı port kullanın
python -m uvicorn src.api.main:app --port 8080
```

---

## 📚 Sonraki Adımlar

1. [Kullanıcı Kılavuzu](USER_GUIDE.md) - Sistem kullanımı
2. [API Dokümantasyonu](API.md) - API endpoints
3. [Model Eğitimi](TRAINING.md) - Özel model eğitimi

---

## 📞 Destek

Sorunlarınız için GitHub Issues kullanabilirsiniz.
