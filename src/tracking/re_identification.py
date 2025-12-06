"""
Re-Identification Module
Hayvan yeniden tanıma (Re-ID) sistemi
"""

import numpy as np
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from collections import defaultdict
import cv2

logger = logging.getLogger(__name__)


@dataclass
class ReIDConfig:
    """Re-ID konfigürasyonu"""
    model_path: Optional[str] = None
    embedding_dim: int = 512
    similarity_threshold: float = 0.7
    gallery_size: int = 100         # Her ID için maksimum örnek
    min_samples_for_match: int = 3  # Eşleşme için minimum örnek
    use_augmentation: bool = True
    device: str = "auto"


@dataclass 
class AnimalIdentity:
    """Hayvan kimlik bilgisi"""
    id: int
    embeddings: List[np.ndarray] = field(default_factory=list)
    best_image: Optional[np.ndarray] = None
    best_score: float = 0.0
    first_seen: int = 0             # Frame number
    last_seen: int = 0
    total_appearances: int = 0
    metadata: dict = field(default_factory=dict)
    
    def add_embedding(self, embedding: np.ndarray, max_size: int = 100) -> None:
        """Embedding ekle"""
        self.embeddings.append(embedding)
        if len(self.embeddings) > max_size:
            self.embeddings.pop(0)
    
    def get_mean_embedding(self) -> np.ndarray:
        """Ortalama embedding"""
        if not self.embeddings:
            return np.zeros(512)
        return np.mean(self.embeddings, axis=0)


class FeatureExtractor:
    """
    Görünüm özelliği çıkarıcı
    ResNet veya EfficientNet tabanlı
    """
    
    def __init__(self, config: ReIDConfig):
        """
        Args:
            config: Re-ID konfigürasyonu
        """
        self.config = config
        self._model = None
        self._device = None
        self._initialized = False
        self._transform = None
    
    def load_model(self) -> bool:
        """Feature extraction modelini yükle"""
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
            
            # Model yükle
            if self.config.model_path:
                self._model = torch.load(self.config.model_path, map_location=self._device)
            else:
                # Default: ResNet50 pretrained
                self._model = models.resnet50(pretrained=True)
                # Son FC katmanını kaldır
                self._model = torch.nn.Sequential(*list(self._model.children())[:-1])
            
            self._model = self._model.to(self._device)
            self._model.eval()
            
            # Transform
            self._transform = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            self._initialized = True
            logger.info(f"Feature extractor yüklendi ({self._device})")
            return True
            
        except Exception as e:
            logger.error(f"Feature extractor yükleme hatası: {e}")
            return False
    
    def extract(self, image: np.ndarray) -> np.ndarray:
        """
        Görüntüden feature çıkar
        
        Args:
            image: BGR görüntü
            
        Returns:
            Feature vector (normalized)
        """
        if not self._initialized:
            # Basit HOG features (fallback)
            return self._extract_hog(image)
        
        try:
            import torch
            
            # RGB'ye çevir
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Transform
            tensor = self._transform(image_rgb)
            tensor = tensor.unsqueeze(0).to(self._device)
            
            # Feature çıkar
            with torch.no_grad():
                features = self._model(tensor)
                features = features.squeeze().cpu().numpy()
            
            # Normalize
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
                features = features.squeeze().cpu().numpy()
            
            # Normalize
            features = features / (np.linalg.norm(features, axis=1, keepdims=True) + 1e-8)
            
            return list(features)
            
        except Exception as e:
            logger.error(f"Batch feature extraction hatası: {e}")
            return [self._extract_hog(img) for img in images]
    
    def _extract_hog(self, image: np.ndarray) -> np.ndarray:
        """Basit HOG feature extraction (fallback)"""
        # Resize
        image = cv2.resize(image, (64, 128))
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # HOG descriptor
        win_size = (64, 128)
        block_size = (16, 16)
        block_stride = (8, 8)
        cell_size = (8, 8)
        nbins = 9
        
        hog = cv2.HOGDescriptor(win_size, block_size, block_stride, cell_size, nbins)
        features = hog.compute(gray)
        
        # Normalize
        features = features.flatten()
        features = features / (np.linalg.norm(features) + 1e-8)
        
        # Boyutu ayarla
        if len(features) < self.config.embedding_dim:
            features = np.pad(features, (0, self.config.embedding_dim - len(features)))
        else:
            features = features[:self.config.embedding_dim]
        
        return features
    
    def release(self) -> None:
        """Kaynakları serbest bırak"""
        self._model = None
        self._initialized = False


class ReIDMatcher:
    """
    Re-ID eşleştirme sınıfı
    Gallery tabanlı kimlik eşleştirme
    """
    
    def __init__(self, config: ReIDConfig):
        """
        Args:
            config: Re-ID konfigürasyonu
        """
        self.config = config
        self._gallery: Dict[int, AnimalIdentity] = {}
        self._next_id = 1
    
    @property
    def gallery(self) -> Dict[int, AnimalIdentity]:
        """Kimlik galerisi"""
        return self._gallery
    
    def register(
        self,
        embedding: np.ndarray,
        image: Optional[np.ndarray] = None,
        frame_id: int = 0,
        metadata: dict = None
    ) -> int:
        """
        Yeni kimlik kaydet
        
        Args:
            embedding: Feature vector
            image: İlişkili görüntü
            frame_id: Frame numarası
            metadata: Ek bilgiler
            
        Returns:
            Yeni kimlik ID'si
        """
        identity = AnimalIdentity(
            id=self._next_id,
            embeddings=[embedding],
            best_image=image,
            best_score=1.0,
            first_seen=frame_id,
            last_seen=frame_id,
            total_appearances=1,
            metadata=metadata or {}
        )
        
        self._gallery[self._next_id] = identity
        self._next_id += 1
        
        logger.debug(f"Yeni kimlik kaydedildi: {identity.id}")
        return identity.id
    
    def match(
        self,
        embedding: np.ndarray,
        top_k: int = 1
    ) -> List[Tuple[int, float]]:
        """
        Embedding ile eşleşen kimlikleri bul
        
        Args:
            embedding: Query feature vector
            top_k: Döndürülecek eşleşme sayısı
            
        Returns:
            [(identity_id, similarity_score), ...]
        """
        if not self._gallery:
            return []
        
        scores = []
        
        for identity_id, identity in self._gallery.items():
            # Ortalama embedding ile karşılaştır
            gallery_embedding = identity.get_mean_embedding()
            similarity = self._cosine_similarity(embedding, gallery_embedding)
            scores.append((identity_id, similarity))
        
        # Benzerliğe göre sırala
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Eşik üstündeki eşleşmeleri döndür
        matches = [
            (id, score) for id, score in scores[:top_k]
            if score >= self.config.similarity_threshold
        ]
        
        return matches
    
    def update(
        self,
        identity_id: int,
        embedding: np.ndarray,
        image: Optional[np.ndarray] = None,
        frame_id: int = 0
    ) -> bool:
        """
        Mevcut kimliği güncelle
        
        Args:
            identity_id: Kimlik ID'si
            embedding: Yeni feature vector
            image: Yeni görüntü
            frame_id: Frame numarası
            
        Returns:
            Başarılı ise True
        """
        if identity_id not in self._gallery:
            return False
        
        identity = self._gallery[identity_id]
        identity.add_embedding(embedding, self.config.gallery_size)
        identity.last_seen = frame_id
        identity.total_appearances += 1
        
        # En iyi görüntüyü güncelle
        if image is not None:
            # Basit kalite skoru (keskinlik tabanlı)
            score = self._image_quality_score(image)
            if score > identity.best_score:
                identity.best_image = image
                identity.best_score = score
        
        return True
    
    def match_or_register(
        self,
        embedding: np.ndarray,
        image: Optional[np.ndarray] = None,
        frame_id: int = 0,
        metadata: dict = None
    ) -> Tuple[int, bool]:
        """
        Eşleştir veya yeni kayıt oluştur
        
        Returns:
            (identity_id, is_new)
        """
        matches = self.match(embedding)
        
        if matches:
            identity_id = matches[0][0]
            self.update(identity_id, embedding, image, frame_id)
            return identity_id, False
        else:
            identity_id = self.register(embedding, image, frame_id, metadata)
            return identity_id, True
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Cosine benzerliği"""
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot / (norm1 * norm2)
    
    def _image_quality_score(self, image: np.ndarray) -> float:
        """Görüntü kalite skoru (keskinlik)"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        return laplacian.var()
    
    def get_identity(self, identity_id: int) -> Optional[AnimalIdentity]:
        """Kimlik bilgisi al"""
        return self._gallery.get(identity_id)
    
    def remove_identity(self, identity_id: int) -> bool:
        """Kimliği sil"""
        if identity_id in self._gallery:
            del self._gallery[identity_id]
            return True
        return False
    
    def merge_identities(self, id1: int, id2: int) -> bool:
        """
        İki kimliği birleştir
        
        Args:
            id1: Hedef kimlik (kalacak)
            id2: Kaynak kimlik (silinecek)
            
        Returns:
            Başarılı ise True
        """
        if id1 not in self._gallery or id2 not in self._gallery:
            return False
        
        identity1 = self._gallery[id1]
        identity2 = self._gallery[id2]
        
        # Embedding'leri birleştir
        identity1.embeddings.extend(identity2.embeddings)
        
        # En iyi görüntüyü kontrol et
        if identity2.best_score > identity1.best_score:
            identity1.best_image = identity2.best_image
            identity1.best_score = identity2.best_score
        
        # Tarihleri güncelle
        identity1.first_seen = min(identity1.first_seen, identity2.first_seen)
        identity1.last_seen = max(identity1.last_seen, identity2.last_seen)
        identity1.total_appearances += identity2.total_appearances
        
        # id2'yi sil
        del self._gallery[id2]
        
        logger.info(f"Kimlikler birleştirildi: {id2} -> {id1}")
        return True
    
    def save_gallery(self, path: str) -> bool:
        """Galeriyi kaydet"""
        try:
            import pickle
            
            data = {
                "next_id": self._next_id,
                "gallery": {}
            }
            
            for id, identity in self._gallery.items():
                data["gallery"][id] = {
                    "id": identity.id,
                    "embeddings": [e.tolist() for e in identity.embeddings],
                    "best_score": identity.best_score,
                    "first_seen": identity.first_seen,
                    "last_seen": identity.last_seen,
                    "total_appearances": identity.total_appearances,
                    "metadata": identity.metadata
                }
            
            with open(path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Galeri kaydedildi: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Galeri kaydetme hatası: {e}")
            return False
    
    def load_gallery(self, path: str) -> bool:
        """Galeriyi yükle"""
        try:
            import pickle
            
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self._next_id = data["next_id"]
            self._gallery.clear()
            
            for id, identity_data in data["gallery"].items():
                identity = AnimalIdentity(
                    id=identity_data["id"],
                    embeddings=[np.array(e) for e in identity_data["embeddings"]],
                    best_score=identity_data["best_score"],
                    first_seen=identity_data["first_seen"],
                    last_seen=identity_data["last_seen"],
                    total_appearances=identity_data["total_appearances"],
                    metadata=identity_data["metadata"]
                )
                self._gallery[int(id)] = identity
            
            logger.info(f"Galeri yüklendi: {path} ({len(self._gallery)} kimlik)")
            return True
            
        except Exception as e:
            logger.error(f"Galeri yükleme hatası: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """Galeri istatistikleri"""
        if not self._gallery:
            return {"total_identities": 0}
        
        total_embeddings = sum(len(i.embeddings) for i in self._gallery.values())
        avg_appearances = sum(i.total_appearances for i in self._gallery.values()) / len(self._gallery)
        
        return {
            "total_identities": len(self._gallery),
            "total_embeddings": total_embeddings,
            "avg_embeddings_per_id": total_embeddings / len(self._gallery),
            "avg_appearances": avg_appearances,
            "next_id": self._next_id
        }
    
    def clear(self) -> None:
        """Galeriyi temizle"""
        self._gallery.clear()
        self._next_id = 1
        logger.info("Galeri temizlendi")
