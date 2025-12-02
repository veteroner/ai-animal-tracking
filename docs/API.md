# 🔌 API Dokümantasyonu

AI Animal Tracking System REST API dokümantasyonu.

## 📍 Base URL

```
http://localhost:8000/api/v1
```

## 🔐 Kimlik Doğrulama

API şu anda açık erişimlidir. Üretim ortamı için JWT authentication eklenecektir.

```http
Authorization: Bearer <token>
```

---

## 📋 Endpoints

### Health Check

#### GET /health

Sistem sağlık durumunu döndürür.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-01T14:30:00.000Z",
  "version": "0.1.0",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "redis": "healthy",
    "model": "loaded"
  }
}
```

---

### Kameralar

#### GET /api/v1/cameras

Tüm kameraları listeler.

**Response:**
```json
{
  "cameras": [
    {
      "id": "cam_01",
      "name": "Ana Kamera",
      "source": "0",
      "status": "active",
      "resolution": "1280x720",
      "fps": 30,
      "created_at": "2024-12-01T10:00:00.000Z"
    }
  ],
  "total": 1
}
```

#### POST /api/v1/cameras

Yeni kamera ekler.

**Request:**
```json
{
  "name": "Ahır Kamerası",
  "source": "rtsp://192.168.1.100:554/stream1",
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "fps": 25
}
```

**Response:**
```json
{
  "id": "cam_02",
  "name": "Ahır Kamerası",
  "status": "created"
}
```

#### GET /api/v1/cameras/{camera_id}

Belirli kameranın detaylarını döndürür.

#### DELETE /api/v1/cameras/{camera_id}

Kamerayı siler.

#### GET /api/v1/cameras/{camera_id}/stream

Kamera stream URL'ini döndürür.

---

### Hayvanlar

#### GET /api/v1/animals

Tüm hayvanları listeler.

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| species | string | Tür filtresi (cow, sheep, horse) |
| status | string | Durum filtresi (healthy, warning, critical) |
| page | int | Sayfa numarası |
| limit | int | Sayfa başına kayıt |

**Response:**
```json
{
  "animals": [
    {
      "id": "animal_001",
      "name": "Sarıkız",
      "species": "cow",
      "tag_id": "TR123456",
      "status": "healthy",
      "bcs_score": 3.2,
      "last_seen": "2024-12-01T14:25:00.000Z",
      "last_behavior": "eating",
      "thumbnail_url": "/api/v1/animals/animal_001/thumbnail"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20
}
```

#### POST /api/v1/animals

Yeni hayvan kaydı oluşturur.

**Request:**
```json
{
  "name": "Sarıkız",
  "species": "cow",
  "tag_id": "TR123456",
  "birth_date": "2022-03-15",
  "notes": "Damızlık inek"
}
```

#### GET /api/v1/animals/{animal_id}

Hayvan detaylarını döndürür.

**Response:**
```json
{
  "id": "animal_001",
  "name": "Sarıkız",
  "species": "cow",
  "tag_id": "TR123456",
  "status": "healthy",
  "birth_date": "2022-03-15",
  "bcs_score": 3.2,
  "bcs_history": [
    {"date": "2024-11-01", "score": 3.0},
    {"date": "2024-12-01", "score": 3.2}
  ],
  "daily_stats": {
    "eating_duration": 360,
    "walking_distance": 2.5,
    "resting_duration": 480
  },
  "health_alerts": [],
  "last_seen": "2024-12-01T14:25:00.000Z",
  "created_at": "2024-01-15T08:00:00.000Z"
}
```

#### PUT /api/v1/animals/{animal_id}

Hayvan bilgilerini günceller.

#### DELETE /api/v1/animals/{animal_id}

Hayvan kaydını siler.

#### GET /api/v1/animals/{animal_id}/behaviors

Hayvanın davranış geçmişini döndürür.

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| start_date | datetime | Başlangıç tarihi |
| end_date | datetime | Bitiş tarihi |
| behavior_type | string | Davranış tipi filtresi |

**Response:**
```json
{
  "animal_id": "animal_001",
  "behaviors": [
    {
      "timestamp": "2024-12-01T14:00:00.000Z",
      "type": "eating",
      "duration": 1200,
      "location": {"x": 150, "y": 200},
      "confidence": 0.92
    }
  ],
  "summary": {
    "eating": 3600,
    "walking": 1800,
    "resting": 7200
  }
}
```

#### GET /api/v1/animals/{animal_id}/health

Hayvanın sağlık geçmişini döndürür.

---

### Tespitler

#### GET /api/v1/detections

Tespit kayıtlarını listeler.

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| camera_id | string | Kamera filtresi |
| animal_id | string | Hayvan filtresi |
| start_time | datetime | Başlangıç zamanı |
| end_time | datetime | Bitiş zamanı |
| min_confidence | float | Minimum güven skoru |

**Response:**
```json
{
  "detections": [
    {
      "id": "det_001",
      "timestamp": "2024-12-01T14:30:00.000Z",
      "camera_id": "cam_01",
      "animal_id": "animal_001",
      "bbox": [100, 150, 300, 400],
      "confidence": 0.95,
      "class": "cow"
    }
  ],
  "total": 1250
}
```

#### GET /api/v1/detections/realtime

WebSocket endpoint - Gerçek zamanlı tespitler.

---

### Davranışlar

#### GET /api/v1/behaviors

Davranış kayıtlarını listeler.

**Response:**
```json
{
  "behaviors": [
    {
      "id": "beh_001",
      "animal_id": "animal_001",
      "type": "eating",
      "start_time": "2024-12-01T14:00:00.000Z",
      "end_time": "2024-12-01T14:20:00.000Z",
      "duration": 1200,
      "zone_id": "feeding_zone"
    }
  ]
}
```

#### GET /api/v1/behaviors/summary

Davranış özeti.

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| period | string | Periyot (day, week, month) |

---

### Analitik

#### GET /api/v1/analytics/dashboard

Dashboard verileri.

**Response:**
```json
{
  "total_animals": 45,
  "active_cameras": 4,
  "today_detections": 12580,
  "alerts_count": 3,
  "behavior_distribution": {
    "eating": 35,
    "resting": 40,
    "walking": 20,
    "other": 5
  },
  "health_status": {
    "healthy": 42,
    "warning": 2,
    "critical": 1
  },
  "activity_timeline": [
    {"hour": 0, "activity_level": 15},
    {"hour": 1, "activity_level": 10}
  ]
}
```

#### GET /api/v1/analytics/trends

Trend analizi.

**Query Parameters:**
| Parametre | Tip | Açıklama |
|-----------|-----|----------|
| metric | string | Metrik (activity, feeding, health) |
| period | string | Periyot (week, month, year) |
| animal_id | string | Hayvan filtresi (opsiyonel) |

---

### Dışa Aktarma

#### POST /api/v1/export/csv

CSV formatında veri dışa aktarır.

**Request:**
```json
{
  "data_type": "detections",
  "start_date": "2024-11-01",
  "end_date": "2024-12-01",
  "animal_ids": ["animal_001", "animal_002"]
}
```

**Response:**
```json
{
  "file_url": "/api/v1/export/download/export_20241201_143000.csv",
  "expires_at": "2024-12-02T14:30:00.000Z"
}
```

#### POST /api/v1/export/json

JSON formatında veri dışa aktarır.

#### GET /api/v1/export/download/{filename}

Export dosyasını indirir.

---

### Uyarılar

#### GET /api/v1/alerts

Uyarı listesi.

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert_001",
      "animal_id": "animal_003",
      "type": "health",
      "severity": "warning",
      "message": "Aktivite düşüşü tespit edildi",
      "created_at": "2024-12-01T10:00:00.000Z",
      "acknowledged": false
    }
  ]
}
```

#### POST /api/v1/alerts/{alert_id}/acknowledge

Uyarıyı onaylar.

---

## 🔄 WebSocket API

### Gerçek Zamanlı Tespitler

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/detections');

ws.onmessage = (event) => {
  const detection = JSON.parse(event.data);
  console.log('New detection:', detection);
};
```

**Message Format:**
```json
{
  "type": "detection",
  "data": {
    "timestamp": "2024-12-01T14:30:00.000Z",
    "camera_id": "cam_01",
    "detections": [
      {
        "animal_id": "animal_001",
        "bbox": [100, 150, 300, 400],
        "confidence": 0.95,
        "class": "cow"
      }
    ]
  }
}
```

### Uyarı Bildirimleri

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/alerts');
```

---

## 📝 Hata Kodları

| Kod | Açıklama |
|-----|----------|
| 200 | Başarılı |
| 201 | Oluşturuldu |
| 400 | Geçersiz istek |
| 401 | Yetkisiz |
| 403 | Yasak |
| 404 | Bulunamadı |
| 409 | Çakışma |
| 422 | Validasyon hatası |
| 429 | Rate limit aşıldı |
| 500 | Sunucu hatası |

**Hata Response Formatı:**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid input data",
  "details": {
    "field": "email",
    "reason": "Invalid format"
  }
}
```

---

## 📊 Rate Limiting

- **Varsayılan:** 100 istek/dakika
- **Aşıldığında:** 429 Too Many Requests

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701443400
```

---

## 🔗 SDK ve Örnekler

### Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Hayvan listesi
response = requests.get(f"{BASE_URL}/animals")
animals = response.json()

# Yeni hayvan ekle
new_animal = {
    "name": "Sarıkız",
    "species": "cow",
    "tag_id": "TR123456"
}
response = requests.post(f"{BASE_URL}/animals", json=new_animal)
```

### JavaScript

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Hayvan listesi
const response = await fetch(`${BASE_URL}/animals`);
const animals = await response.json();

// Gerçek zamanlı tespitler
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/detections`);
ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

### cURL

```bash
# Health check
curl http://localhost:8000/health

# Hayvan listesi
curl http://localhost:8000/api/v1/animals

# Yeni hayvan ekle
curl -X POST http://localhost:8000/api/v1/animals \
  -H "Content-Type: application/json" \
  -d '{"name":"Sarıkız","species":"cow","tag_id":"TR123456"}'
```
