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

AI-powered animal detection and re-identification system.

## Features
- 🔍 Real-time animal detection (YOLOv8)
- 🆔 Automatic individual identification (Re-ID)
- 📊 Animal gallery management
- 🐑 Supports: Cow, Sheep, Horse, Dog, Cat, Bird, etc.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/v1/detection/process-frame` | POST | Process image (multipart/form-data) |
| `/api/v1/detection/gallery` | GET | Get all registered animals |
| `/api/v1/detection/reset` | POST | Reset gallery |

## Usage

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
    print(f"  - {animal['animal_id']}: {animal['class_name']}")
```

## Developed by
**Teknova** - AI Solutions for Agriculture
