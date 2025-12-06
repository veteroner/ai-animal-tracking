---
title: Teknova AI Animal Tracking
emoji: 🐄
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# Teknova AI Animal Tracking 🐄

AI-powered animal detection, tracking and re-identification system for smart farming.

## 🌟 Features
- 🔍 **Real-time Detection**: YOLOv8-based animal detection
- 🆔 **Re-Identification**: Automatic individual animal recognition
- 📊 **Gallery Management**: Track and manage animal database
- 🏃 **Behavior Analysis**: Activity and movement tracking
- 🏥 **Health Monitoring**: Health status indicators
- 🐑 **Multi-species Support**: Cow, Sheep, Horse, Dog, Cat, Bird, etc.

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API documentation |
| `/health` | GET | Health check |
| `/api/v1/detection/process-frame` | POST | Process image for detection |
| `/api/v1/detection/gallery` | GET | Get registered animals |
| `/api/v1/detection/reset` | POST | Reset animal gallery |
| `/api/v1/detection/stats` | GET | Get detection statistics |

## 🚀 Quick Start

### Python Example
```python
import requests

# Process an image
with open("cow.jpg", "rb") as f:
    response = requests.post(
        "https://your-space.hf.space/api/v1/detection/process-frame",
        files={"file": f}
    )
    
result = response.json()
print(f"Detected {result['animal_count']} animals")
for animal in result['animals']:
    print(f"  - {animal['animal_id']}: {animal['class_name']} ({animal['confidence']:.2%})")
```

### JavaScript Example
```javascript
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch('https://your-space.hf.space/api/v1/detection/process-frame', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(`Detected ${result.animal_count} animals`);
```

## 🔧 Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CONFIDENCE_THRESHOLD` | 0.4 | Minimum detection confidence |
| `SIMILARITY_THRESHOLD` | 0.92 | Re-ID similarity threshold |
| `MAX_GALLERY_SIZE` | 500 | Maximum animals in gallery |

## 📦 Deployment

### HuggingFace Spaces
1. Fork this repository
2. Create a new Space with Docker SDK
3. Upload the `huggingface/` directory
4. Wait for build to complete

### Local Docker
```bash
cd huggingface
docker build -t animal-tracking .
docker run -p 7860:7860 animal-tracking
```

## 🔗 Related Projects
- **Frontend**: Next.js dashboard for visualization
- **Backend**: FastAPI server with full API
- **Mobile**: React Native mobile app

## 📊 Performance
- Detection: ~15 FPS on CPU, ~30+ FPS on GPU
- Re-ID Accuracy: >85%
- Supported formats: JPG, PNG, BMP, WebP

## 🏷️ License
MIT License - See LICENSE file

## 👨‍💻 Developed by
**Teknova** - AI Solutions for Smart Farming

🌐 [GitHub](https://github.com/veteroner/ai-animal-tracking) | 📧 Contact: teknova@example.com
