"""
Feature Extractor
Hayvan görünüm özelliği çıkarma modülü
"""

import cv2
import numpy as np
import logging
from typing import List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FeatureExtractorConfig:
    """Feature extractor konfigürasyonu"""
    model_type: str = "resnet50"  # resnet50, efficientnet, mobilenet, hog
    model_path: Optional[str] = None
    embedding_dim: int = 512
    input_size: Tuple[int, int] = (224, 224)
    normalize: bool = True
    use_augmentation: bool = False
    device: str = "auto"


class DeepFeatureExtractor:
    """
    Deep Learning tabanlı feature extractor
    """
    
    def __init__(self, config: FeatureExtractorConfig):
        """
        Args:
            config: Extractor konfigürasyonu
        """
        self.config = config
        self._model = None
        self._device = None
        self._transform = None
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    def load_model(self) -> bool:
        """Model yükle"""
        try:
            import torch
            import torchvision.models as models
            import torchvision.transforms as transforms
            
            # Device seç
            if self.config.device == "auto":
                if torch.cuda.is_available():
                    self._device = torch.device("cuda")
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self._device = torch.device("mps")
                else:
                    self._device = torch.device("cpu")
            else:
                self._device = torch.device(self.config.device)
            
            # Model türüne göre yükle
            if self.config.model_path and Path(self.config.model_path).exists():
                self._model = torch.load(self.config.model_path, map_location=self._device)
            else:
                if self.config.model_type == "resnet50":
                    base_model = models.resnet50(pretrained=True)
                    # Son FC katmanını kaldır -> 2048-dim features
                    self._model = torch.nn.Sequential(*list(base_model.children())[:-1])
                
                elif self.config.model_type == "efficientnet":
                    base_model = models.efficientnet_b0(pretrained=True)
                    self._model = torch.nn.Sequential(*list(base_model.children())[:-1])
                
                elif self.config.model_type == "mobilenet":
                    base_model = models.mobilenet_v3_small(pretrained=True)
                    self._model = torch.nn.Sequential(*list(base_model.children())[:-1])
                
                else:
                    raise ValueError(f"Desteklenmeyen model türü: {self.config.model_type}")
            
            self._model = self._model.to(self._device)
            self._model.eval()
            
            # Transform pipeline
            self._transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize(self.config.input_size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            self._initialized = True
            logger.info(f"Feature extractor yüklendi: {self.config.model_type} ({self._device})")
            return True
            
        except ImportError:
            logger.warning("PyTorch yüklü değil, HOG features kullanılacak")
            return False
            
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            return False
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Görüntüden feature çıkar
        
        Args:
            image: BGR formatında görüntü
            
        Returns:
            Feature vektörü
        """
        if not self._initialized:
            return self._extract_hog(image)
        
        try:
            import torch
            
            # BGR -> RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Transform uygula
            tensor = self._transform(image_rgb)
            tensor = tensor.unsqueeze(0).to(self._device)
            
            # Feature çıkar
            with torch.no_grad():
                features = self._model(tensor)
                features = features.squeeze().cpu().numpy()
            
            # Normalize
            if self.config.normalize:
                features = features / (np.linalg.norm(features) + 1e-8)
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction hatası: {e}")
            return self._extract_hog(image)
    
    def extract_batch(self, images: List[np.ndarray]) -> List[np.ndarray]:
        """Batch feature extraction"""
        if not self._initialized:
            return [self._extract_hog(img) for img in images]
        
        try:
            import torch
            
            tensors = []
            for image in images:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                tensor = self._transform(image_rgb)
                tensors.append(tensor)
            
            batch = torch.stack(tensors).to(self._device)
            
            with torch.no_grad():
                features = self._model(batch)
                features = features.view(features.size(0), -1).cpu().numpy()
            
            if self.config.normalize:
                norms = np.linalg.norm(features, axis=1, keepdims=True) + 1e-8
                features = features / norms
            
            return list(features)
            
        except Exception as e:
            logger.error(f"Batch extraction hatası: {e}")
            return [self._extract_hog(img) for img in images]
    
    def _extract_hog(self, image: np.ndarray) -> np.ndarray:
        """HOG feature extraction (fallback)"""
        # Resize
        image = cv2.resize(image, (128, 256))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # HOG parametreleri
        win_size = (128, 256)
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        nbins = 9
        
        hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
        features = hog.compute(gray).flatten()
        
        # Normalize
        if self.config.normalize:
            features = features / (np.linalg.norm(features) + 1e-8)
        
        return features
    
    def release(self) -> None:
        """Kaynakları serbest bırak"""
        self._model = None
        self._initialized = False


class ColorHistogramExtractor:
    """Renk histogram özelliği çıkarıcı"""
    
    def __init__(
        self,
        bins: Tuple[int, int, int] = (8, 8, 8),
        color_space: str = "hsv"
    ):
        """
        Args:
            bins: Her kanal için bin sayısı
            color_space: Renk uzayı (hsv, lab, rgb)
        """
        self.bins = bins
        self.color_space = color_space
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """Renk histogram feature çıkar"""
        # Renk uzayı dönüşümü
        if self.color_space == "hsv":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        elif self.color_space == "lab":
            image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Histogram hesapla
        hist = cv2.calcHist(
            [image], [0, 1, 2], None,
            self.bins,
            [0, 256, 0, 256, 0, 256]
        )
        
        # Normalize
        hist = cv2.normalize(hist, hist).flatten()
        
        return hist


class TextureExtractor:
    """Doku özelliği çıkarıcı (LBP tabanlı)"""
    
    def __init__(self, num_points: int = 24, radius: int = 3):
        """
        Args:
            num_points: LBP için nokta sayısı
            radius: LBP yarıçapı
        """
        self.num_points = num_points
        self.radius = radius
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """LBP tabanlı texture feature çıkar"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Basit LBP implementasyonu
        lbp = self._compute_lbp(gray)
        
        # Histogram
        hist, _ = np.histogram(lbp, bins=256, range=(0, 256))
        hist = hist.astype(np.float32)
        hist = hist / (hist.sum() + 1e-8)
        
        return hist
    
    def _compute_lbp(self, gray: np.ndarray) -> np.ndarray:
        """Basit LBP hesapla"""
        rows, cols = gray.shape
        lbp = np.zeros_like(gray)
        
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                center = gray[i, j]
                code = 0
                code |= (gray[i-1, j-1] > center) << 7
                code |= (gray[i-1, j] > center) << 6
                code |= (gray[i-1, j+1] > center) << 5
                code |= (gray[i, j+1] > center) << 4
                code |= (gray[i+1, j+1] > center) << 3
                code |= (gray[i+1, j] > center) << 2
                code |= (gray[i+1, j-1] > center) << 1
                code |= (gray[i, j-1] > center) << 0
                lbp[i, j] = code
        
        return lbp


class CombinedFeatureExtractor:
    """Birleşik özellik çıkarıcı"""
    
    def __init__(
        self,
        use_deep: bool = True,
        use_color: bool = True,
        use_texture: bool = False,
        deep_config: FeatureExtractorConfig = None
    ):
        """
        Args:
            use_deep: Deep features kullan
            use_color: Renk histogram kullan
            use_texture: Texture features kullan
            deep_config: Deep extractor konfigürasyonu
        """
        self.extractors = []
        self.weights = []
        
        if use_deep:
            config = deep_config or FeatureExtractorConfig()
            deep_ext = DeepFeatureExtractor(config)
            deep_ext.load_model()
            self.extractors.append(("deep", deep_ext))
            self.weights.append(0.7)
        
        if use_color:
            color_ext = ColorHistogramExtractor()
            self.extractors.append(("color", color_ext))
            self.weights.append(0.2)
        
        if use_texture:
            texture_ext = TextureExtractor()
            self.extractors.append(("texture", texture_ext))
            self.weights.append(0.1)
        
        # Ağırlıkları normalize et
        total = sum(self.weights)
        self.weights = [w / total for w in self.weights]
    
    def extract(self, image: np.ndarray) -> dict:
        """
        Tüm özellikleri çıkar
        
        Returns:
            {"deep": ..., "color": ..., "texture": ..., "combined": ...}
        """
        features = {}
        combined = []
        
        for (name, extractor), weight in zip(self.extractors, self.weights):
            feat = extractor.extract(image)
            features[name] = feat
            
            # Weighted contribution
            combined.append(feat * weight)
        
        # Birleşik feature
        if combined:
            # Boyutları eşitle
            max_len = max(len(f) for f in combined)
            padded = []
            for f in combined:
                if len(f) < max_len:
                    f = np.pad(f, (0, max_len - len(f)))
                padded.append(f)
            
            features["combined"] = np.concatenate(padded)
        
        return features
    
    def compute_similarity(
        self,
        features1: dict,
        features2: dict,
        method: str = "combined"
    ) -> float:
        """
        İki feature seti arasındaki benzerliği hesapla
        
        Args:
            features1: İlk feature seti
            features2: İkinci feature seti
            method: Karşılaştırma yöntemi (combined, deep, color, texture)
            
        Returns:
            Benzerlik skoru (0-1)
        """
        if method in features1 and method in features2:
            f1 = features1[method]
            f2 = features2[method]
            return self._cosine_similarity(f1, f2)
        
        # Ağırlıklı ortalama
        similarity = 0.0
        for (name, _), weight in zip(self.extractors, self.weights):
            if name in features1 and name in features2:
                sim = self._cosine_similarity(features1[name], features2[name])
                similarity += sim * weight
        
        return similarity
    
    def _cosine_similarity(self, f1: np.ndarray, f2: np.ndarray) -> float:
        """Cosine benzerliği"""
        dot = np.dot(f1, f2)
        norm1 = np.linalg.norm(f1)
        norm2 = np.linalg.norm(f2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot / (norm1 * norm2))
