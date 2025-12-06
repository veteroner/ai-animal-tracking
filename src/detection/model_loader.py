"""
Model Loader
AI model yükleme ve yönetim modülü
"""

import os
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import threading
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Model türleri"""
    YOLO_DETECTION = "yolo_detection"
    YOLO_SEGMENTATION = "yolo_segmentation"
    YOLO_POSE = "yolo_pose"
    DEEPSORT_REID = "deepsort_reid"
    FEATURE_EXTRACTOR = "feature_extractor"
    BEHAVIOR_CLASSIFIER = "behavior_classifier"
    CUSTOM = "custom"


@dataclass
class ModelInfo:
    """Model bilgileri"""
    name: str
    type: ModelType
    path: str
    url: Optional[str] = None
    size_mb: Optional[float] = None
    md5_hash: Optional[str] = None
    description: str = ""
    version: str = "1.0"
    input_size: tuple = (640, 640)
    classes: Optional[list] = None


# Önceden tanımlı modeller
PREDEFINED_MODELS = {
    "yolov8n": ModelInfo(
        name="YOLOv8 Nano",
        type=ModelType.YOLO_DETECTION,
        path="models/pretrained/yolov8n.pt",
        url="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt",
        size_mb=6.2,
        description="Hızlı ve hafif YOLO modeli"
    ),
    "yolov8s": ModelInfo(
        name="YOLOv8 Small",
        type=ModelType.YOLO_DETECTION,
        path="models/pretrained/yolov8s.pt",
        url="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt",
        size_mb=22.5,
        description="Dengeli YOLO modeli"
    ),
    "yolov8m": ModelInfo(
        name="YOLOv8 Medium",
        type=ModelType.YOLO_DETECTION,
        path="models/pretrained/yolov8m.pt",
        url="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt",
        size_mb=52.0,
        description="Orta boyutlu YOLO modeli"
    ),
    "yolov8l": ModelInfo(
        name="YOLOv8 Large",
        type=ModelType.YOLO_DETECTION,
        path="models/pretrained/yolov8l.pt",
        url="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt",
        size_mb=87.7,
        description="Büyük YOLO modeli"
    ),
    "yolov8x": ModelInfo(
        name="YOLOv8 XLarge",
        type=ModelType.YOLO_DETECTION,
        path="models/pretrained/yolov8x.pt",
        url="https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt",
        size_mb=136.7,
        description="En büyük YOLO modeli"
    ),
}


class ModelLoader:
    """
    Model yükleme ve yönetim sınıfı
    """
    
    def __init__(self, models_dir: str = "models"):
        """
        Args:
            models_dir: Modellerin saklanacağı dizin
        """
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self._loaded_models: Dict[str, Any] = {}
        self._model_info: Dict[str, ModelInfo] = {}
        self._lock = threading.Lock()
        
        # Predefined modelleri kaydet
        self._model_info.update({k: v for k, v in PREDEFINED_MODELS.items()})
    
    def register_model(self, model_id: str, info: ModelInfo) -> None:
        """
        Yeni model kaydet
        
        Args:
            model_id: Model ID'si
            info: Model bilgileri
        """
        self._model_info[model_id] = info
        logger.info(f"Model kaydedildi: {model_id}")
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """Model bilgilerini al"""
        return self._model_info.get(model_id)
    
    def list_available_models(self) -> list:
        """Mevcut modelleri listele"""
        models = []
        for model_id, info in self._model_info.items():
            path = self.models_dir / info.path if not os.path.isabs(info.path) else Path(info.path)
            models.append({
                "id": model_id,
                "name": info.name,
                "type": info.type.value,
                "path": str(path),
                "exists": path.exists(),
                "size_mb": info.size_mb,
                "description": info.description
            })
        return models
    
    def download_model(
        self,
        model_id: str,
        progress_callback: Optional[Callable[[float], None]] = None,
        force: bool = False
    ) -> bool:
        """
        Modeli indir
        
        Args:
            model_id: Model ID'si
            progress_callback: İndirme ilerleme callback'i
            force: Varsa bile yeniden indir
            
        Returns:
            Başarılı ise True
        """
        info = self._model_info.get(model_id)
        if not info:
            logger.error(f"Model bulunamadı: {model_id}")
            return False
        
        if not info.url:
            logger.error(f"Model URL'i tanımlı değil: {model_id}")
            return False
        
        # Hedef yol
        target_path = self.models_dir / info.path if not os.path.isabs(info.path) else Path(info.path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Zaten var mı kontrol et
        if target_path.exists() and not force:
            logger.info(f"Model zaten mevcut: {target_path}")
            return True
        
        logger.info(f"Model indiriliyor: {model_id} -> {target_path}")
        
        try:
            response = requests.get(info.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = downloaded / total_size
                            progress_callback(progress)
            
            # MD5 kontrolü
            if info.md5_hash:
                actual_hash = self._calculate_md5(target_path)
                if actual_hash != info.md5_hash:
                    logger.error(f"MD5 hash uyuşmuyor: {actual_hash} != {info.md5_hash}")
                    target_path.unlink()
                    return False
            
            logger.info(f"Model başarıyla indirildi: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"Model indirme hatası: {e}")
            if target_path.exists():
                target_path.unlink()
            return False
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Dosyanın MD5 hash'ini hesapla"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def load_yolo_model(
        self,
        model_id: str = "yolov8n",
        device: str = "auto",
        half_precision: bool = False
    ) -> Any:
        """
        YOLO modeli yükle
        
        Args:
            model_id: Model ID'si
            device: Cihaz (auto, cpu, cuda, mps)
            half_precision: FP16 kullan
            
        Returns:
            Yüklenen model
        """
        with self._lock:
            cache_key = f"{model_id}_{device}_{half_precision}"
            
            if cache_key in self._loaded_models:
                return self._loaded_models[cache_key]
            
            info = self._model_info.get(model_id)
            if not info:
                raise ValueError(f"Model bulunamadı: {model_id}")
            
            # Model yolunu belirle
            model_path = self.models_dir / info.path if not os.path.isabs(info.path) else Path(info.path)
            
            # Model yoksa indir
            if not model_path.exists():
                if info.url:
                    logger.info(f"Model indiriliyor: {model_id}")
                    self.download_model(model_id)
                else:
                    raise FileNotFoundError(f"Model dosyası bulunamadı: {model_path}")
            
            try:
                from ultralytics import YOLO
                
                model = YOLO(str(model_path))
                
                # Cihazı belirle
                if device == "auto":
                    device = self._get_best_device()
                
                if device != "cpu":
                    model.to(device)
                
                if half_precision and device == "cuda":
                    model.half()
                
                self._loaded_models[cache_key] = model
                logger.info(f"YOLO modeli yüklendi: {model_id} ({device})")
                
                return model
                
            except Exception as e:
                logger.error(f"Model yükleme hatası: {e}")
                raise
    
    def load_torch_model(
        self,
        model_path: str,
        device: str = "auto"
    ) -> Any:
        """
        Genel PyTorch modeli yükle
        
        Args:
            model_path: Model dosya yolu
            device: Cihaz
            
        Returns:
            Yüklenen model
        """
        import torch
        
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model dosyası bulunamadı: {model_path}")
        
        if device == "auto":
            device = self._get_best_device()
        
        try:
            model = torch.load(model_path, map_location=device)
            logger.info(f"PyTorch modeli yüklendi: {model_path}")
            return model
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            raise
    
    def load_onnx_model(self, model_path: str) -> Any:
        """
        ONNX modeli yükle
        
        Args:
            model_path: Model dosya yolu
            
        Returns:
            ONNX Runtime session
        """
        import onnxruntime as ort
        
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Model dosyası bulunamadı: {model_path}")
        
        try:
            # GPU varsa kullan
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            session = ort.InferenceSession(str(path), providers=providers)
            logger.info(f"ONNX modeli yüklendi: {model_path}")
            return session
        except Exception as e:
            logger.error(f"ONNX model yükleme hatası: {e}")
            raise
    
    def _get_best_device(self) -> str:
        """En uygun cihazı belirle"""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"
    
    def unload_model(self, model_id: str) -> None:
        """Modeli bellekten kaldır"""
        with self._lock:
            keys_to_remove = [k for k in self._loaded_models if k.startswith(model_id)]
            for key in keys_to_remove:
                del self._loaded_models[key]
                logger.info(f"Model bellekten kaldırıldı: {key}")
    
    def unload_all(self) -> None:
        """Tüm modelleri bellekten kaldır"""
        with self._lock:
            self._loaded_models.clear()
            logger.info("Tüm modeller bellekten kaldırıldı")
    
    def get_model_size(self, model_path: str) -> float:
        """Model dosya boyutunu MB cinsinden al"""
        path = Path(model_path)
        if path.exists():
            return path.stat().st_size / (1024 * 1024)
        return 0.0
    
    def export_to_onnx(
        self,
        model_id: str,
        output_path: str,
        input_size: tuple = (640, 640),
        opset: int = 12
    ) -> bool:
        """
        YOLO modelini ONNX'e dönüştür
        
        Args:
            model_id: Model ID'si
            output_path: Çıktı dosya yolu
            input_size: Giriş boyutu
            opset: ONNX opset version
            
        Returns:
            Başarılı ise True
        """
        try:
            model = self.load_yolo_model(model_id)
            model.export(format='onnx', imgsz=input_size, opset=opset)
            logger.info(f"Model ONNX'e dönüştürüldü: {output_path}")
            return True
        except Exception as e:
            logger.error(f"ONNX export hatası: {e}")
            return False


class ModelCache:
    """Model önbellek yönetimi"""
    
    def __init__(self, max_memory_mb: float = 2048):
        """
        Args:
            max_memory_mb: Maksimum bellek kullanımı (MB)
        """
        self.max_memory = max_memory_mb
        self._cache: Dict[str, Any] = {}
        self._access_order: list = []
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Önbellekten model al"""
        with self._lock:
            if key in self._cache:
                # LRU güncelle
                self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key]
        return None
    
    def put(self, key: str, model: Any, size_mb: float = 0) -> None:
        """Önbelleğe model ekle"""
        with self._lock:
            # Bellek limiti kontrolü
            # Gerçek implementasyonda model boyutu hesaplanmalı
            
            if key in self._cache:
                self._access_order.remove(key)
            
            self._cache[key] = model
            self._access_order.append(key)
    
    def remove(self, key: str) -> None:
        """Önbellekten kaldır"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._access_order.remove(key)
    
    def clear(self) -> None:
        """Önbelleği temizle"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()


# Global model loader instance
_model_loader: Optional[ModelLoader] = None


def get_model_loader(models_dir: str = "models") -> ModelLoader:
    """Global model loader'ı al veya oluştur"""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader(models_dir)
    return _model_loader
