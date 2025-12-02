# 🚀 Hızlı Başlangıç Rehberi

## İlk Adımlar (5 Dakika)

### 1. Ortamı Hazırla

```bash
# Proje dizinine git
cd /Users/onerozbey/Desktop/ai_goruntu_isleme

# Virtual environment oluştur
python3 -m venv venv

# Aktifleştir
source venv/bin/activate

# Bağımlılıkları yükle
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. İlk Testi Yap

```bash
# Webcam ile tespit
python src/main.py --camera 0

# veya video dosyası ile
python src/main.py --camera /path/to/video.mp4
```

### 3. Telefon Kamerası Kullanmak İçin

1. Telefonuna "IP Webcam" uygulamasını yükle (Android)
2. Uygulamayı aç ve "Start server" a tıkla
3. Gösterilen IP adresini kullan:

```bash
python src/main.py --camera "http://192.168.1.XXX:8080/video"
```

---

## Proje Yapısı Özeti

```
ai_goruntu_isleme/
├── config/           # Ayar dosyaları
├── src/              # Ana kod
│   ├── main.py       # Giriş noktası ⭐
│   ├── core/         # Yardımcı modüller
│   ├── camera/       # Kamera yönetimi
│   ├── detection/    # YOLO tespit
│   ├── tracking/     # DeepSORT takip
│   └── api/          # REST API
├── models/           # AI modelleri
├── data/             # Veri dosyaları
├── docs/             # Dokümantasyon
└── scripts/          # Yardımcı scriptler
```

---

## Geliştirme Yol Haritası

| Faz | Süre | Durum |
|-----|------|-------|
| 1. Temel Altyapı | 2 hafta | ✅ Tamamlandı |
| 2. Kamera Entegrasyonu | 1.5 hafta | 🔄 Başlangıç |
| 3. Nesne Tespiti (YOLO) | 1.5 hafta | ⏳ |
| 4. Takip (DeepSORT) | 2 hafta | ⏳ |
| 5. Davranış Analizi | 2 hafta | ⏳ |

---

## Önemli Dosyalar

- `PROJE_PLANI.md` - Detaylı plan ve checklist
- `README.md` - Proje tanıtımı
- `docs/INSTALLATION.md` - Kurulum kılavuzu
- `docs/USER_GUIDE.md` - Kullanım kılavuzu
- `docs/API.md` - API dokümantasyonu
- `docs/TRAINING.md` - Model eğitim kılavuzu

---

## Sonraki Adımlar

1. ✅ Proje yapısı oluşturuldu
2. 🔜 Bağımlılıkları yükle: `pip install -r requirements.txt`
3. 🔜 Webcam ile test et: `python src/main.py --camera 0`
4. 🔜 Telefon kamerasını dene
5. 🔜 Kamera modülünü genişlet
6. 🔜 Takip sistemini ekle

---

İyi kodlamalar! 🎉
