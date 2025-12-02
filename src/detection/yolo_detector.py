"""
AI Animal Tracking System - YOLO Detector
==========================================

YOLOv8 tabanlı nesne/hayvan algılama modülü.
"""

import time
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import cv2

try:
    from ultralytics import YOLO
    from ultralytics.engine.results import Results
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None
    Results = None


logger = logging.getLogger("animal_tracking.detection")


# ===========================================
# COCO Dataset Hayvan Sınıfları
# ===========================================

COCO_ANIMAL_CLASSES = {
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
}

# Kanatlı hayvan sınıfları (COCO'da sadece bird var, özel model için genişletilebilir)
POULTRY_CLASSES = {
    14: "bird",  # Genel kuş - tavuk/hindi/kaz olarak yorumlanabilir
}

# Türkçe karşılıklar
ANIMAL_NAMES_TR = {
    "bird": "Kuş/Kanatlı",
    "cat": "Kedi",
    "dog": "Köpek",
    "horse": "At",
    "sheep": "Koyun",
    "cow": "İnek",
    "elephant": "Fil",
    "bear": "Ayı",
    "zebra": "Zebra",
    "giraffe": "Zürafa",
}

# Tüm COCO sınıfları (80 sınıf)
COCO_CLASSES = {
    0: "person", 1: "bicycle", 2: "car", 3: "motorcycle", 4: "airplane",
    5: "bus", 6: "train", 7: "truck", 8: "boat", 9: "traffic light",
    10: "fire hydrant", 11: "stop sign", 12: "parking meter", 13: "bench",
    14: "bird", 15: "cat", 16: "dog", 17: "horse", 18: "sheep",
    19: "cow", 20: "elephant", 21: "bear", 22: "zebra", 23: "giraffe",
    24: "backpack", 25: "umbrella", 26: "handbag", 27: "tie", 28: "suitcase",
    29: "frisbee", 30: "skis", 31: "snowboard", 32: "sports ball", 33: "kite",
    34: "baseball bat", 35: "baseball glove", 36: "skateboard", 37: "surfboard",
    38: "tennis racket", 39: "bottle", 40: "wine glass", 41: "cup", 42: "fork",
    43: "knife", 44: "spoon", 45: "bowl", 46: "banana", 47: "apple",
    48: "sandwich", 49: "orange", 50: "broccoli", 51: "carrot", 52: "hot dog",
    53: "pizza", 54: "donut", 55: "cake", 56: "chair", 57: "couch",
    58: "potted plant", 59: "bed", 60: "dining table", 61: "toilet", 62: "tv",
    63: "laptop", 64: "mouse", 65: "remote", 66: "keyboard", 67: "cell phone",
    68: "microwave", 69: "oven", 70: "toaster", 71: "sink", 72: "refrigerator",
    73: "book", 74: "clock", 75: "vase", 76: "scissors", 77: "teddy bear",
    78: "hair drier", 79: "toothbrush",
}


# ===========================================
# Data Classes
# ===========================================

@dataclass
class DetectorConfig:
    """Dedektör konfigürasyonu"""
    model_path: str = "yolov8n.pt"  # nano model (hızlı)
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    max_detections: int = 100
    device: str = "auto"  # auto, cpu, cuda, mps
    half_precision: bool = False  # FP16
    image_size: int = 640
    only_animals: bool = True  # Sadece hayvan sınıfları
    animal_classes: List[int] = field(default_factory=lambda: list(COCO_ANIMAL_CLASSES.keys()))


@dataclass
class Detection:
    """Tek bir tespit sonucu"""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]  # center_x, center_y
    area: int
    
    # Opsiyonel
    mask: Optional[np.ndarray] = None  # Segmentasyon maskesi
    keypoints: Optional[np.ndarray] = None  # Pose keypoints
    track_id: Optional[int] = None  # Tracking ID
    
    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]
    
    @property
    def is_animal(self) -> bool:
        return self.class_id in COCO_ANIMAL_CLASSES
    
    @property
    def class_name_tr(self) -> str:
        return ANIMAL_NAMES_TR.get(self.class_name, self.class_name)
    
    def to_dict(self) -> dict:
        """Dictionary'e dönüştür"""
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "class_name_tr": self.class_name_tr,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox,
            "center": self.center,
            "area": self.area,
            "width": self.width,
            "height": self.height,
            "is_animal": self.is_animal,
            "track_id": self.track_id,
        }


@dataclass
class DetectionResult:
    """Tespit sonuçları"""
    detections: List[Detection]
    frame_id: int
    timestamp: float
    inference_time: float  # ms
    image_size: Tuple[int, int]  # width, height
    
    # Orijinal YOLO results (opsiyonel)
    raw_results: Optional[Any] = None
    
    @property
    def count(self) -> int:
        return len(self.detections)
    
    @property
    def animal_count(self) -> int:
        return sum(1 for d in self.detections if d.is_animal)
    
    @property
    def animals(self) -> List[Detection]:
        return [d for d in self.detections if d.is_animal]
    
    def filter_by_class(self, class_name: str) -> List[Detection]:
        """Sınıfa göre filtrele"""
        return [d for d in self.detections if d.class_name == class_name]
    
    def filter_by_confidence(self, min_confidence: float) -> List[Detection]:
        """Güven skoruna göre filtrele"""
        return [d for d in self.detections if d.confidence >= min_confidence]
    
    def to_dict(self) -> dict:
        """Dictionary'e dönüştür"""
        return {
            "count": self.count,
            "animal_count": self.animal_count,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "inference_time_ms": round(self.inference_time, 2),
            "image_size": self.image_size,
            "detections": [d.to_dict() for d in self.detections],
        }


# ===========================================
# YOLO Detector Class
# ===========================================

class YOLODetector:
    """
    YOLOv8 tabanlı nesne/hayvan dedektörü.
    
    Kullanım:
        detector = YOLODetector(model_path="yolov8n.pt")
        result = detector.detect(frame)
        
        for detection in result.detections:
            print(f"{detection.class_name}: {detection.confidence:.2f}")
    """
    
    # Model boyutları ve açıklamaları
    MODEL_VARIANTS = {
        "yolov8n": "Nano - En hızlı, en küçük (3.2M params)",
        "yolov8s": "Small - Hızlı ve dengeli (11.2M params)",
        "yolov8m": "Medium - Orta hız ve doğruluk (25.9M params)",
        "yolov8l": "Large - Yüksek doğruluk (43.7M params)",
        "yolov8x": "Extra Large - En yüksek doğruluk (68.2M params)",
    }
    
    def __init__(self, config: Optional[DetectorConfig] = None, **kwargs):
        """
        Args:
            config: DetectorConfig nesnesi
            **kwargs: Config parametreleri (config yoksa kullanılır)
        """
        if not ULTRALYTICS_AVAILABLE:
            raise ImportError(
                "ultralytics paketi yüklü değil. "
                "Yüklemek için: pip install ultralytics"
            )
        
        # Config
        if config is None:
            config = DetectorConfig(**kwargs)
        self.config = config
        
        # Model
        self._model: Optional[Any] = None
        self._device: str = ""
        self._frame_id: int = 0
        
        # İstatistikler
        self._total_inferences: int = 0
        self._total_inference_time: float = 0.0
        self._total_detections: int = 0
        
        # Modeli yükle
        self._load_model()
    
    def _load_model(self):
        """Modeli yükle"""
        logger.info(f"Loading YOLO model: {self.config.model_path}")
        
        try:
            self._model = YOLO(self.config.model_path)
            
            # Device belirle
            self._device = self._determine_device()
            
            logger.info(f"Model loaded successfully on device: {self._device}")
            logger.info(f"Model classes: {len(self._model.names)}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _determine_device(self) -> str:
        """Çalıştırılacak cihazı belirle"""
        device = self.config.device.lower()
        
        if device == "auto":
            # Otomatik cihaz seçimi
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    return "mps"  # Apple Silicon
            except ImportError:
                pass
            return "cpu"
        
        return device
    
    @property
    def model(self) -> Any:
        """YOLO model nesnesi"""
        if self._model is None:
            raise RuntimeError("Model not loaded")
        return self._model
    
    @property
    def class_names(self) -> Dict[int, str]:
        """Model sınıf isimleri"""
        return self.model.names
    
    @property
    def statistics(self) -> dict:
        """İstatistikler"""
        avg_time = (
            self._total_inference_time / self._total_inferences
            if self._total_inferences > 0 else 0
        )
        return {
            "total_inferences": self._total_inferences,
            "total_inference_time_ms": round(self._total_inference_time, 2),
            "average_inference_time_ms": round(avg_time, 2),
            "total_detections": self._total_detections,
            "fps": round(1000 / avg_time, 1) if avg_time > 0 else 0,
            "device": self._device,
        }
    
    def detect(
        self,
        image: np.ndarray,
        confidence: Optional[float] = None,
        classes: Optional[List[int]] = None,
    ) -> DetectionResult:
        """
        Görüntüde nesne tespiti yap.
        
        Args:
            image: BGR formatında görüntü (HxWxC)
            confidence: Minimum güven skoru (None = config değeri)
            classes: Tespit edilecek sınıf ID'leri (None = config değeri)
            
        Returns:
            DetectionResult
        """
        if image is None or len(image.shape) != 3:
            return DetectionResult(
                detections=[],
                frame_id=self._frame_id,
                timestamp=time.time(),
                inference_time=0,
                image_size=(0, 0),
            )
        
        self._frame_id += 1
        start_time = time.time()
        
        # Parametreler
        conf = confidence or self.config.confidence_threshold
        
        if classes is None:
            if self.config.only_animals:
                classes = self.config.animal_classes
            else:
                classes = None
        
        # YOLO inference
        results = self.model.predict(
            source=image,
            conf=conf,
            iou=self.config.iou_threshold,
            device=self._device,
            half=self.config.half_precision,
            imgsz=self.config.image_size,
            max_det=self.config.max_detections,
            classes=classes,
            verbose=False,
        )
        
        # Inference süresi
        inference_time = (time.time() - start_time) * 1000  # ms
        
        # Sonuçları parse et
        detections = self._parse_results(results[0] if results else None)
        
        # İstatistikleri güncelle
        self._total_inferences += 1
        self._total_inference_time += inference_time
        self._total_detections += len(detections)
        
        return DetectionResult(
            detections=detections,
            frame_id=self._frame_id,
            timestamp=time.time(),
            inference_time=inference_time,
            image_size=(image.shape[1], image.shape[0]),
            raw_results=results[0] if results else None,
        )
    
    def _parse_results(self, results: Optional[Any]) -> List[Detection]:
        """YOLO sonuçlarını parse et"""
        if results is None or results.boxes is None:
            return []
        
        detections = []
        boxes = results.boxes
        
        for i in range(len(boxes)):
            # Bounding box
            xyxy = boxes.xyxy[i].cpu().numpy().astype(int)
            x1, y1, x2, y2 = xyxy
            
            # Sınıf ve güven
            class_id = int(boxes.cls[i].cpu().numpy())
            confidence = float(boxes.conf[i].cpu().numpy())
            class_name = self.class_names.get(class_id, f"class_{class_id}")
            
            # Merkez ve alan
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            area = (x2 - x1) * (y2 - y1)
            
            # Track ID (varsa)
            track_id = None
            if boxes.id is not None:
                track_id = int(boxes.id[i].cpu().numpy())
            
            detection = Detection(
                class_id=class_id,
                class_name=class_name,
                confidence=confidence,
                bbox=(x1, y1, x2, y2),
                center=(center_x, center_y),
                area=area,
                track_id=track_id,
            )
            
            detections.append(detection)
        
        return detections
    
    def draw_detections(
        self,
        image: np.ndarray,
        result: DetectionResult,
        show_labels: bool = True,
        show_confidence: bool = True,
        show_track_id: bool = True,
        color: Optional[Tuple[int, int, int]] = None,
        thickness: int = 2,
        font_scale: float = 0.6,
    ) -> np.ndarray:
        """
        Tespitleri görüntü üzerine çiz.
        
        Args:
            image: Orijinal görüntü
            result: DetectionResult
            show_labels: Sınıf isimlerini göster
            show_confidence: Güven skorunu göster
            show_track_id: Track ID göster
            color: Kutu rengi (None = sınıfa göre renk)
            thickness: Çizgi kalınlığı
            font_scale: Font boyutu
            
        Returns:
            Çizilmiş görüntü
        """
        output = image.copy()
        
        # Sınıf renkleri
        class_colors = self._generate_class_colors()
        
        for det in result.detections:
            x1, y1, x2, y2 = det.bbox
            
            # Renk
            box_color = color or class_colors.get(det.class_id, (0, 255, 0))
            
            # Bounding box çiz
            cv2.rectangle(output, (x1, y1), (x2, y2), box_color, thickness)
            
            # Label
            if show_labels or show_confidence or show_track_id:
                label_parts = []
                
                if show_track_id and det.track_id is not None:
                    label_parts.append(f"ID:{det.track_id}")
                
                if show_labels:
                    label_parts.append(det.class_name_tr)
                
                if show_confidence:
                    label_parts.append(f"{det.confidence:.2f}")
                
                label = " ".join(label_parts)
                
                # Label arka planı
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
                )
                
                cv2.rectangle(
                    output,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width + 5, y1),
                    box_color,
                    -1
                )
                
                # Label text
                cv2.putText(
                    output,
                    label,
                    (x1 + 2, y1 - baseline - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA,
                )
        
        return output
    
    def _generate_class_colors(self) -> Dict[int, Tuple[int, int, int]]:
        """Sınıflar için renkler oluştur"""
        colors = {}
        np.random.seed(42)
        
        for class_id in range(80):  # COCO 80 sınıf
            colors[class_id] = tuple(np.random.randint(0, 255, 3).tolist())
        
        # Hayvan sınıfları için sabit renkler
        colors[14] = (255, 165, 0)   # bird - orange
        colors[15] = (255, 192, 203) # cat - pink
        colors[16] = (139, 69, 19)   # dog - brown
        colors[17] = (128, 0, 128)   # horse - purple
        colors[18] = (255, 255, 255) # sheep - white
        colors[19] = (0, 0, 0)       # cow - black
        colors[20] = (128, 128, 128) # elephant - gray
        colors[21] = (165, 42, 42)   # bear - dark brown
        colors[22] = (0, 0, 0)       # zebra - black
        colors[23] = (255, 215, 0)   # giraffe - gold
        
        return colors
    
    def track(
        self,
        image: np.ndarray,
        tracker: str = "bytetrack",
        persist: bool = True,
    ) -> DetectionResult:
        """
        Görüntüde nesne tespiti ve tracking yap.
        
        Args:
            image: BGR formatında görüntü
            tracker: Tracker tipi (bytetrack, botsort)
            persist: Track'leri kalıcı tut
            
        Returns:
            DetectionResult (track_id'ler dahil)
        """
        self._frame_id += 1
        start_time = time.time()
        
        # Classes
        classes = self.config.animal_classes if self.config.only_animals else None
        
        # YOLO tracking
        results = self.model.track(
            source=image,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            device=self._device,
            half=self.config.half_precision,
            imgsz=self.config.image_size,
            max_det=self.config.max_detections,
            classes=classes,
            tracker=f"{tracker}.yaml",
            persist=persist,
            verbose=False,
        )
        
        inference_time = (time.time() - start_time) * 1000
        
        detections = self._parse_results(results[0] if results else None)
        
        self._total_inferences += 1
        self._total_inference_time += inference_time
        self._total_detections += len(detections)
        
        return DetectionResult(
            detections=detections,
            frame_id=self._frame_id,
            timestamp=time.time(),
            inference_time=inference_time,
            image_size=(image.shape[1], image.shape[0]),
            raw_results=results[0] if results else None,
        )
    
    def reset_tracker(self):
        """Tracker'ı sıfırla"""
        if self._model is not None:
            self._model.predictor = None
    
    def warmup(self, image_size: Tuple[int, int] = (640, 640)):
        """
        Model warm-up (ilk inference hızlandırma).
        
        Args:
            image_size: Warm-up görüntü boyutu
        """
        logger.info("Warming up model...")
        dummy_image = np.zeros((*image_size, 3), dtype=np.uint8)
        self.detect(dummy_image)
        logger.info("Warmup complete")


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    # Dedektör oluştur
    detector = YOLODetector(
        model_path="yolov8n.pt",
        confidence_threshold=0.5,
        only_animals=False,  # Test için tüm sınıflar
    )
    
    # Warmup
    detector.warmup()
    
    # Webcam'den test
    cap = cv2.VideoCapture(0)
    
    print("\nPress 'q' to quit, 'a' for animals only")
    animals_only = False
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Tespit
            if animals_only:
                result = detector.detect(frame)
            else:
                result = detector.detect(frame, classes=None)
            
            # Çiz
            output = detector.draw_detections(frame, result)
            
            # FPS ve bilgi
            cv2.putText(
                output,
                f"FPS: {1000/result.inference_time:.1f} | Detections: {result.count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )
            
            cv2.imshow("YOLO Detection Test", output)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('a'):
                animals_only = not animals_only
                print(f"Animals only: {animals_only}")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # İstatistikler
        print("\n=== Statistics ===")
        for key, value in detector.statistics.items():
            print(f"{key}: {value}")
