"""
Detector Base
Temel detector sınıfı - tüm detector'lar için abstract base class
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any
from dataclasses import dataclass, field
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DetectorType(Enum):
    """Detector türleri"""
    YOLO = "yolo"
    FASTER_RCNN = "faster_rcnn"
    SSD = "ssd"
    DETR = "detr"
    CUSTOM = "custom"


@dataclass
class Detection:
    """Tespit sonucu veri sınıfı"""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None
    features: Optional[np.ndarray] = None
    metadata: dict = field(default_factory=dict)
    
    @property
    def center(self) -> Tuple[int, int]:
        """Bounding box merkezi"""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property
    def width(self) -> int:
        """Bounding box genişliği"""
        return self.bbox[2] - self.bbox[0]
    
    @property
    def height(self) -> int:
        """Bounding box yüksekliği"""
        return self.bbox[3] - self.bbox[1]
    
    @property
    def area(self) -> int:
        """Bounding box alanı"""
        return self.width * self.height
    
    def to_dict(self) -> dict:
        """Dictionary'e çevir"""
        return {
            "bbox": self.bbox,
            "confidence": self.confidence,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "track_id": self.track_id,
            "center": self.center,
            "width": self.width,
            "height": self.height,
            "area": self.area,
            "metadata": self.metadata
        }


@dataclass
class DetectorConfig:
    """Detector konfigürasyonu"""
    model_path: str
    confidence_threshold: float = 0.5
    nms_threshold: float = 0.4
    max_detections: int = 100
    device: str = "auto"  # auto, cpu, cuda, mps
    classes: Optional[List[int]] = None  # Sadece belirli sınıfları tespit et
    input_size: Tuple[int, int] = (640, 640)
    half_precision: bool = False  # FP16 kullan
    batch_size: int = 1


class DetectorBase(ABC):
    """
    Temel Detector sınıfı
    Tüm detector implementasyonları bu sınıftan türetilir
    """
    
    def __init__(self, config: DetectorConfig):
        """
        Args:
            config: Detector konfigürasyonu
        """
        self.config = config
        self._model = None
        self._device = None
        self._classes = {}
        self._initialized = False
        
        # İstatistikler
        self._stats = {
            "total_detections": 0,
            "total_frames": 0,
            "avg_inference_time": 0.0,
            "last_inference_time": 0.0
        }
    
    @property
    def is_initialized(self) -> bool:
        """Model yüklenmiş mi?"""
        return self._initialized
    
    @property
    def stats(self) -> dict:
        """İstatistikler"""
        return self._stats.copy()
    
    @property
    def classes(self) -> dict:
        """Sınıf isimleri"""
        return self._classes
    
    @abstractmethod
    def load_model(self) -> bool:
        """
        Modeli yükle
        
        Returns:
            Başarılı ise True
        """
        pass
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Frame üzerinde nesne tespiti yap
        
        Args:
            frame: Giriş frame'i (BGR format)
            
        Returns:
            Tespit listesi
        """
        pass
    
    @abstractmethod
    def detect_batch(self, frames: List[np.ndarray]) -> List[List[Detection]]:
        """
        Birden fazla frame üzerinde tespit yap
        
        Args:
            frames: Frame listesi
            
        Returns:
            Her frame için tespit listesi
        """
        pass
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Frame'i model girişi için hazırla
        
        Args:
            frame: Ham frame
            
        Returns:
            İşlenmiş frame
        """
        # Boyutlandır
        if self.config.input_size:
            import cv2
            frame = cv2.resize(frame, self.config.input_size)
        
        return frame
    
    def postprocess(self, detections: List[Detection]) -> List[Detection]:
        """
        Tespit sonuçlarını işle
        
        Args:
            detections: Ham tespitler
            
        Returns:
            İşlenmiş tespitler
        """
        # Confidence filtresi
        filtered = [d for d in detections if d.confidence >= self.config.confidence_threshold]
        
        # Sınıf filtresi
        if self.config.classes:
            filtered = [d for d in filtered if d.class_id in self.config.classes]
        
        # Maksimum tespit sayısı
        if len(filtered) > self.config.max_detections:
            filtered.sort(key=lambda x: x.confidence, reverse=True)
            filtered = filtered[:self.config.max_detections]
        
        return filtered
    
    def apply_nms(
        self,
        detections: List[Detection],
        iou_threshold: float = None
    ) -> List[Detection]:
        """
        Non-Maximum Suppression uygula
        
        Args:
            detections: Tespitler
            iou_threshold: IoU eşik değeri
            
        Returns:
            NMS sonrası tespitler
        """
        if not detections:
            return []
        
        if iou_threshold is None:
            iou_threshold = self.config.nms_threshold
        
        # Bounding box'ları ve confidence'ları çıkar
        boxes = np.array([d.bbox for d in detections])
        scores = np.array([d.confidence for d in detections])
        
        # NMS uygula
        indices = self._nms(boxes, scores, iou_threshold)
        
        return [detections[i] for i in indices]
    
    def _nms(
        self,
        boxes: np.ndarray,
        scores: np.ndarray,
        iou_threshold: float
    ) -> List[int]:
        """
        Non-Maximum Suppression implementasyonu
        
        Args:
            boxes: Bounding box'lar (N, 4)
            scores: Confidence skorları (N,)
            iou_threshold: IoU eşik değeri
            
        Returns:
            Seçilen indeksler
        """
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            
            inter = w * h
            iou = inter / (areas[i] + areas[order[1:]] - inter)
            
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return keep
    
    def warmup(self, iterations: int = 3) -> None:
        """
        Model warmup (ilk inference'ları hızlandırmak için)
        
        Args:
            iterations: Warmup iterasyon sayısı
        """
        if not self._initialized:
            logger.warning("Model yüklenmemiş, warmup yapılamıyor")
            return
        
        dummy_frame = np.zeros((*self.config.input_size, 3), dtype=np.uint8)
        
        for _ in range(iterations):
            self.detect(dummy_frame)
        
        logger.info(f"Model warmup tamamlandı ({iterations} iterasyon)")
    
    def get_device(self) -> str:
        """Kullanılacak cihazı belirle"""
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
    
    def release(self) -> None:
        """Kaynakları serbest bırak"""
        self._model = None
        self._initialized = False
        logger.info("Detector kaynakları serbest bırakıldı")
    
    def __enter__(self):
        """Context manager giriş"""
        self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager çıkış"""
        self.release()


def calculate_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """
    İki bounding box arasındaki IoU'yu hesapla
    
    Args:
        box1: İlk box (x1, y1, x2, y2)
        box2: İkinci box (x1, y1, x2, y2)
        
    Returns:
        IoU değeri
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])
    
    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area
