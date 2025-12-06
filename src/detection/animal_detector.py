"""
Animal Detector
Hayvan özel nesne tespiti
"""

import cv2
import numpy as np
import logging
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .detector_base import DetectorBase, Detection, DetectorConfig

logger = logging.getLogger(__name__)


class AnimalClass(Enum):
    """Desteklenen hayvan sınıfları"""
    COW = "cow"
    SHEEP = "sheep"
    GOAT = "goat"
    HORSE = "horse"
    PIG = "pig"
    CHICKEN = "chicken"
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    UNKNOWN = "unknown"


# COCO veri setindeki hayvan sınıf ID'leri
COCO_ANIMAL_CLASSES = {
    15: AnimalClass.BIRD,      # bird
    16: AnimalClass.CAT,       # cat
    17: AnimalClass.DOG,       # dog
    18: AnimalClass.HORSE,     # horse
    19: AnimalClass.SHEEP,     # sheep
    20: AnimalClass.COW,       # cow
    # Ek sınıflar gerekirse eklenebilir
}

# Çiftlik hayvanları için COCO ID'leri
FARM_ANIMAL_IDS = [18, 19, 20]  # horse, sheep, cow


@dataclass
class AnimalDetectorConfig(DetectorConfig):
    """Hayvan detector konfigürasyonu"""
    farm_animals_only: bool = True
    min_confidence: float = 0.5
    track_history: bool = True
    extract_features: bool = False
    color_analysis: bool = False
    size_estimation: bool = False


@dataclass
class AnimalDetection(Detection):
    """Hayvan tespiti sonucu"""
    animal_type: AnimalClass = AnimalClass.UNKNOWN
    estimated_size: Optional[str] = None  # small, medium, large
    dominant_color: Optional[Tuple[int, int, int]] = None
    age_estimate: Optional[str] = None  # calf, adult
    health_indicators: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Dictionary'e çevir"""
        base = super().to_dict()
        base.update({
            "animal_type": self.animal_type.value,
            "estimated_size": self.estimated_size,
            "dominant_color": self.dominant_color,
            "age_estimate": self.age_estimate,
            "health_indicators": self.health_indicators
        })
        return base


class AnimalDetector:
    """
    Hayvan Tespit Sınıfı
    YOLO tabanlı hayvan tespiti ve analizi
    """
    
    def __init__(self, config: AnimalDetectorConfig):
        """
        Args:
            config: Detector konfigürasyonu
        """
        self.config = config
        self._model = None
        self._device = None
        self._initialized = False
        
        # Sınıf mapping
        self._class_map = COCO_ANIMAL_CLASSES
        
        # İstatistikler
        self._stats = {
            "total_detections": 0,
            "detections_by_class": {},
            "avg_confidence": 0.0,
            "frames_processed": 0
        }
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    def load_model(self) -> bool:
        """YOLO modelini yükle"""
        try:
            from ultralytics import YOLO
            
            self._model = YOLO(self.config.model_path)
            self._device = self._get_device()
            
            # Modeli cihaza taşı
            if self._device != "cpu":
                self._model.to(self._device)
            
            self._initialized = True
            logger.info(f"Hayvan detector modeli yüklendi: {self.config.model_path}")
            return True
            
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            return False
    
    def _get_device(self) -> str:
        """Uygun cihazı seç"""
        if self.config.device != "auto":
            return self.config.device
        
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        
        return "cpu"
    
    def detect(self, frame: np.ndarray) -> List[AnimalDetection]:
        """
        Frame üzerinde hayvan tespiti yap
        
        Args:
            frame: Giriş frame'i (BGR format)
            
        Returns:
            Hayvan tespit listesi
        """
        if not self._initialized:
            logger.error("Model yüklenmemiş")
            return []
        
        try:
            # YOLO tespiti
            results = self._model(
                frame,
                conf=self.config.min_confidence,
                classes=FARM_ANIMAL_IDS if self.config.farm_animals_only else None,
                verbose=False
            )
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                
                if boxes is None:
                    continue
                
                for i in range(len(boxes)):
                    box = boxes[i]
                    
                    # Bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    
                    # Confidence ve class
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Hayvan türü
                    animal_type = self._class_map.get(class_id, AnimalClass.UNKNOWN)
                    
                    # Tespit objesi oluştur
                    detection = AnimalDetection(
                        bbox=(x1, y1, x2, y2),
                        confidence=confidence,
                        class_id=class_id,
                        class_name=animal_type.value,
                        animal_type=animal_type
                    )
                    
                    # Ek analizler
                    if self.config.size_estimation:
                        detection.estimated_size = self._estimate_size(detection)
                    
                    if self.config.color_analysis:
                        roi = frame[y1:y2, x1:x2]
                        detection.dominant_color = self._get_dominant_color(roi)
                    
                    detections.append(detection)
            
            # İstatistikleri güncelle
            self._update_stats(detections)
            
            return detections
            
        except Exception as e:
            logger.error(f"Tespit hatası: {e}")
            return []
    
    def detect_batch(self, frames: List[np.ndarray]) -> List[List[AnimalDetection]]:
        """
        Birden fazla frame üzerinde tespit
        
        Args:
            frames: Frame listesi
            
        Returns:
            Her frame için tespit listesi
        """
        if not self._initialized:
            logger.error("Model yüklenmemiş")
            return [[] for _ in frames]
        
        all_detections = []
        
        try:
            results = self._model(
                frames,
                conf=self.config.min_confidence,
                classes=FARM_ANIMAL_IDS if self.config.farm_animals_only else None,
                verbose=False
            )
            
            for result, frame in zip(results, frames):
                frame_detections = []
                boxes = result.boxes
                
                if boxes is not None:
                    for i in range(len(boxes)):
                        box = boxes[i]
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        animal_type = self._class_map.get(class_id, AnimalClass.UNKNOWN)
                        
                        detection = AnimalDetection(
                            bbox=(x1, y1, x2, y2),
                            confidence=confidence,
                            class_id=class_id,
                            class_name=animal_type.value,
                            animal_type=animal_type
                        )
                        
                        frame_detections.append(detection)
                
                all_detections.append(frame_detections)
            
            return all_detections
            
        except Exception as e:
            logger.error(f"Batch tespit hatası: {e}")
            return [[] for _ in frames]
    
    def _estimate_size(self, detection: AnimalDetection) -> str:
        """Hayvan boyutunu tahmin et"""
        area = detection.area
        
        # Basit eşik değerleri (piksel cinsinden)
        if area < 10000:
            return "small"
        elif area < 50000:
            return "medium"
        else:
            return "large"
    
    def _get_dominant_color(self, roi: np.ndarray) -> Tuple[int, int, int]:
        """ROI'deki baskın rengi bul"""
        if roi.size == 0:
            return (0, 0, 0)
        
        # Küçük boyuta yeniden boyutlandır
        small_roi = cv2.resize(roi, (50, 50))
        
        # K-means ile dominant renk
        pixels = small_roi.reshape(-1, 3)
        pixels = np.float32(pixels)
        
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(pixels, 3, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # En yaygın cluster'ı bul
        unique, counts = np.unique(labels, return_counts=True)
        dominant_idx = unique[np.argmax(counts)]
        dominant_color = centers[dominant_idx].astype(int)
        
        return tuple(dominant_color.tolist())
    
    def _update_stats(self, detections: List[AnimalDetection]) -> None:
        """İstatistikleri güncelle"""
        self._stats["frames_processed"] += 1
        self._stats["total_detections"] += len(detections)
        
        for det in detections:
            animal_type = det.animal_type.value
            if animal_type not in self._stats["detections_by_class"]:
                self._stats["detections_by_class"][animal_type] = 0
            self._stats["detections_by_class"][animal_type] += 1
        
        if detections:
            avg_conf = sum(d.confidence for d in detections) / len(detections)
            # Running average
            n = self._stats["frames_processed"]
            self._stats["avg_confidence"] = (
                (self._stats["avg_confidence"] * (n - 1) + avg_conf) / n
            )
    
    def get_stats(self) -> dict:
        """İstatistikleri al"""
        return self._stats.copy()
    
    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[AnimalDetection],
        show_label: bool = True,
        show_confidence: bool = True,
        color: Tuple[int, int, int] = None
    ) -> np.ndarray:
        """
        Tespitleri frame üzerine çiz
        
        Args:
            frame: Giriş frame'i
            detections: Tespit listesi
            show_label: Etiket göster
            show_confidence: Confidence göster
            color: Box rengi (None ise sınıfa göre)
            
        Returns:
            Çizilmiş frame
        """
        frame = frame.copy()
        
        # Sınıf renkleri
        class_colors = {
            AnimalClass.COW: (0, 255, 0),      # Yeşil
            AnimalClass.SHEEP: (255, 255, 0),   # Cyan
            AnimalClass.GOAT: (0, 255, 255),    # Sarı
            AnimalClass.HORSE: (255, 0, 0),     # Mavi
            AnimalClass.PIG: (128, 0, 255),     # Mor
            AnimalClass.CHICKEN: (0, 165, 255), # Turuncu
            AnimalClass.DOG: (0, 128, 255),     # Turuncu
            AnimalClass.CAT: (203, 192, 255),   # Pembe
            AnimalClass.UNKNOWN: (128, 128, 128) # Gri
        }
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            box_color = color if color else class_colors.get(det.animal_type, (0, 255, 0))
            
            # Bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
            
            # Label
            if show_label or show_confidence:
                label_parts = []
                if show_label:
                    label_parts.append(det.animal_type.value)
                if show_confidence:
                    label_parts.append(f"{det.confidence:.2f}")
                if det.track_id is not None:
                    label_parts.append(f"ID:{det.track_id}")
                
                label = " ".join(label_parts)
                
                # Label arka planı
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 5, y1), box_color, -1)
                
                # Label metni
                cv2.putText(
                    frame, label, (x1 + 2, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
                )
        
        return frame
    
    def release(self) -> None:
        """Kaynakları serbest bırak"""
        self._model = None
        self._initialized = False
        logger.info("AnimalDetector kaynakları serbest bırakıldı")


class AnimalCounter:
    """Hayvan sayacı"""
    
    def __init__(self):
        self._counts: Dict[AnimalClass, int] = {}
        self._tracking_ids: set = set()
    
    def count(self, detections: List[AnimalDetection]) -> Dict[str, int]:
        """
        Tespit edilen hayvanları say
        
        Args:
            detections: Tespit listesi
            
        Returns:
            Hayvan türüne göre sayılar
        """
        counts = {}
        
        for det in detections:
            animal_type = det.animal_type.value
            if animal_type not in counts:
                counts[animal_type] = 0
            counts[animal_type] += 1
        
        return counts
    
    def count_unique(self, detections: List[AnimalDetection]) -> Dict[str, int]:
        """
        Track ID'ye göre benzersiz hayvanları say
        
        Args:
            detections: Tespit listesi
            
        Returns:
            Benzersiz hayvan sayıları
        """
        counts = {}
        seen_ids = set()
        
        for det in detections:
            if det.track_id is None or det.track_id in seen_ids:
                continue
            
            seen_ids.add(det.track_id)
            animal_type = det.animal_type.value
            
            if animal_type not in counts:
                counts[animal_type] = 0
            counts[animal_type] += 1
        
        return counts
    
    def get_total(self, detections: List[AnimalDetection]) -> int:
        """Toplam tespit sayısı"""
        return len(detections)
