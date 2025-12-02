# 🎓 Model Eğitim Kılavuzu

Bu dokümanda özel hayvan tespit modeli eğitimi anlatılmaktadır.

---

## 📋 Genel Bakış

YOLOv8 modelini kendi veri setinizle fine-tune ederek:
- Belirli hayvan türlerini daha iyi tespit edebilir
- Özel ortam koşullarına uyum sağlayabilir
- Yeni sınıflar ekleyebilirsiniz

---

## 📁 Veri Seti Hazırlığı

### Klasör Yapısı

```
data/datasets/
├── images/
│   ├── train/
│   │   ├── image_001.jpg
│   │   ├── image_002.jpg
│   │   └── ...
│   ├── val/
│   │   ├── image_101.jpg
│   │   └── ...
│   └── test/
│       └── ...
├── labels/
│   ├── train/
│   │   ├── image_001.txt
│   │   ├── image_002.txt
│   │   └── ...
│   ├── val/
│   │   └── ...
│   └── test/
│       └── ...
└── dataset.yaml
```

### YOLO Label Formatı

Her görüntü için aynı isimde `.txt` dosyası:

```
# class_id x_center y_center width height
# Tüm değerler 0-1 arasında normalize edilmiş

0 0.5 0.5 0.3 0.4
1 0.2 0.7 0.15 0.25
```

### Dataset YAML Dosyası

```yaml
# data/datasets/dataset.yaml

path: /path/to/data/datasets
train: images/train
val: images/val
test: images/test

# Sınıflar
names:
  0: cow
  1: sheep
  2: goat
  3: horse

# Sınıf sayısı
nc: 4
```

---

## 🖼️ Veri Toplama

### 1. Video'dan Frame Çıkarma

```python
import cv2
import os

def extract_frames(video_path, output_dir, interval=30):
    """
    Video'dan belirli aralıklarla frame çıkarır.
    
    Args:
        video_path: Video dosya yolu
        output_dir: Çıktı klasörü
        interval: Kaç frame'de bir kaydet
    """
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % interval == 0:
            filename = f"frame_{saved_count:06d}.jpg"
            cv2.imwrite(os.path.join(output_dir, filename), frame)
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    print(f"Saved {saved_count} frames")

# Kullanım
extract_frames("video.mp4", "data/datasets/images/raw", interval=30)
```

### 2. Canlı Kameradan Kayıt

```python
import cv2
import time

def capture_training_images(camera_source, output_dir, num_images=100, interval=2):
    """
    Kameradan eğitim görüntüleri toplar.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(camera_source)
    count = 0
    
    print("Press 's' to save, 'q' to quit")
    
    while count < num_images:
        ret, frame = cap.read()
        if not ret:
            continue
        
        cv2.imshow("Capture", frame)
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('s'):
            filename = f"capture_{count:04d}.jpg"
            cv2.imwrite(os.path.join(output_dir, filename), frame)
            print(f"Saved: {filename}")
            count += 1
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
```

---

## 🏷️ Veri Etiketleme

### Önerilen Araçlar

1. **LabelImg** - Basit ve ücretsiz
   ```bash
   pip install labelImg
   labelImg
   ```

2. **CVAT** - Web tabanlı, gelişmiş özellikler
   ```bash
   docker run -p 8080:8080 cvat/server
   ```

3. **Roboflow** - Online, otomatik augmentation
   - https://roboflow.com

### LabelImg Kullanımı

1. LabelImg'i açın
2. "Open Dir" ile görüntü klasörünü seçin
3. "Change Save Dir" ile label klasörünü seçin
4. Format olarak "YOLO" seçin
5. Her görüntü için:
   - 'w' tuşu ile dikdörtgen çizin
   - Sınıf seçin
   - Kaydedin (Ctrl+S)

### Etiketleme İpuçları

- **Tutarlılık:** Aynı nesneyi her zaman aynı şekilde etiketleyin
- **Tüm Nesneler:** Görüntüdeki tüm hedef nesneleri etiketleyin
- **Sıkı Bounding Box:** Nesneyi sıkıca sarın, fazla boşluk bırakmayın
- **Zor Örnekler:** Kısmen görünen, kalabalık, belirsiz nesneleri dahil edin

---

## 🔄 Veri Augmentation

### Otomatik Augmentation

```python
# config/model_config.yaml

training:
  augmentation:
    enabled: true
    horizontal_flip: true
    vertical_flip: false
    rotation: 15
    scale: [0.8, 1.2]
    brightness: 0.2
    contrast: 0.2
    mosaic: true
    mixup: 0.1
```

### Manuel Augmentation

```python
import albumentations as A
import cv2

transform = A.Compose([
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(p=0.5),
    A.Rotate(limit=15, p=0.5),
    A.GaussNoise(p=0.3),
    A.Blur(blur_limit=3, p=0.2),
], bbox_params=A.BboxParams(format='yolo'))

# Kullanım
image = cv2.imread("image.jpg")
bboxes = [[0.5, 0.5, 0.3, 0.4, 0]]  # YOLO format + class

transformed = transform(image=image, bboxes=bboxes)
aug_image = transformed['image']
aug_bboxes = transformed['bboxes']
```

---

## 🚀 Model Eğitimi

### Basit Eğitim

```python
from ultralytics import YOLO

# Pretrained model yükle
model = YOLO('yolov8n.pt')

# Eğit
results = model.train(
    data='data/datasets/dataset.yaml',
    epochs=100,
    imgsz=640,
    batch=16,
    name='animal_detector'
)
```

### Gelişmiş Eğitim

```python
from ultralytics import YOLO

model = YOLO('yolov8s.pt')

results = model.train(
    # Veri
    data='data/datasets/dataset.yaml',
    
    # Eğitim parametreleri
    epochs=150,
    patience=30,  # Early stopping
    batch=16,
    imgsz=640,
    
    # Optimizer
    optimizer='AdamW',
    lr0=0.001,
    lrf=0.01,  # Final learning rate
    momentum=0.9,
    weight_decay=0.0005,
    
    # Augmentation
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=15,
    translate=0.1,
    scale=0.5,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.1,
    
    # Diğer
    device='auto',
    workers=8,
    project='runs/train',
    name='animal_detector_v1',
    exist_ok=False,
    pretrained=True,
    verbose=True,
    save=True,
    save_period=10,
)
```

### Komut Satırından Eğitim

```bash
yolo train \
    data=data/datasets/dataset.yaml \
    model=yolov8s.pt \
    epochs=100 \
    imgsz=640 \
    batch=16 \
    name=animal_detector
```

---

## 📊 Model Değerlendirme

### Validasyon

```python
from ultralytics import YOLO

model = YOLO('runs/train/animal_detector/weights/best.pt')

# Validasyon
metrics = model.val(data='data/datasets/dataset.yaml')

print(f"mAP50: {metrics.box.map50:.4f}")
print(f"mAP50-95: {metrics.box.map:.4f}")
print(f"Precision: {metrics.box.p:.4f}")
print(f"Recall: {metrics.box.r:.4f}")
```

### Test Görüntüleri ile Test

```python
# Tek görüntü
results = model.predict('test_image.jpg', conf=0.5)

# Klasör
results = model.predict('data/datasets/images/test/', conf=0.5, save=True)
```

### Confusion Matrix

```python
# Validasyon sonrası otomatik oluşturulur
# runs/train/animal_detector/confusion_matrix.png
```

---

## 💾 Model Export

### ONNX Export

```python
from ultralytics import YOLO

model = YOLO('runs/train/animal_detector/weights/best.pt')

# ONNX export
model.export(format='onnx', dynamic=True, simplify=True)
```

### TensorRT Export (NVIDIA GPU)

```python
model.export(format='engine', device=0, half=True)
```

### Diğer Formatlar

```python
# CoreML (iOS/macOS)
model.export(format='coreml')

# TensorFlow Lite (Mobile)
model.export(format='tflite')

# OpenVINO (Intel)
model.export(format='openvino')
```

---

## 📈 Eğitim İzleme

### TensorBoard

```bash
# Eğitim sırasında
tensorboard --logdir runs/train

# Tarayıcıda aç
# http://localhost:6006
```

### Weights & Biases

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

# W&B ile eğitim
model.train(
    data='dataset.yaml',
    epochs=100,
    project='animal-tracking',
    name='experiment-1'
)
```

---

## 🔧 Hiperparametre Ayarlama

### Otomatik Tuning

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')

# Ray Tune ile hyperparameter search
model.tune(
    data='data/datasets/dataset.yaml',
    epochs=30,
    iterations=50,
    optimizer='AdamW',
    plots=True,
    save=True
)
```

### Manuel Deneyler

```python
experiments = [
    {'lr0': 0.001, 'batch': 16},
    {'lr0': 0.0001, 'batch': 16},
    {'lr0': 0.001, 'batch': 32},
]

for i, params in enumerate(experiments):
    model = YOLO('yolov8n.pt')
    model.train(
        data='dataset.yaml',
        epochs=50,
        name=f'exp_{i}',
        **params
    )
```

---

## 📝 En İyi Uygulamalar

### Veri

1. **En az 500-1000 görüntü** sınıf başına
2. **%80/%10/%10** train/val/test oranı
3. **Çeşitlilik:** Farklı açılar, ışık, arka plan
4. **Dengeleme:** Sınıflar arası dengesizliği giderin

### Eğitim

1. **Pretrained model** ile başlayın
2. **Düşük learning rate** (0.001 veya altı)
3. **Early stopping** kullanın
4. **Augmentation** mutlaka uygulayın
5. **Batch size:** GPU belleğine göre maksimize edin

### Değerlendirme

1. **Test seti** eğitimde hiç kullanılmamalı
2. **mAP50-95** ana metrik olarak kullanın
3. **Confusion matrix** analiz edin
4. **Gerçek ortamda** test edin

---

## 🐛 Sorun Giderme

### Overfitting

- Daha fazla veri toplayın
- Augmentation artırın
- Dropout/regularization ekleyin
- Daha küçük model kullanın

### Underfitting

- Daha büyük model kullanın
- Daha uzun eğitin
- Learning rate ayarlayın

### Düşük Doğruluk

- Veri kalitesini kontrol edin
- Etiketleme hatalarını düzeltin
- Sınıf dengesizliğini giderin

### CUDA Bellek Hatası

- Batch size azaltın
- Görüntü boyutunu küçültün
- Gradient checkpointing kullanın

---

## 📚 Kaynaklar

- [Ultralytics Docs](https://docs.ultralytics.com/)
- [YOLOv8 GitHub](https://github.com/ultralytics/ultralytics)
- [Roboflow Blog](https://blog.roboflow.com/)
- [Papers With Code - Object Detection](https://paperswithcode.com/task/object-detection)
