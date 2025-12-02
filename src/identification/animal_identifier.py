"""
AI Animal Tracking System - Animal Identifier
==============================================

Benzersiz hayvan tanımlama modülü.
Re-ID (Re-Identification) için feature extraction ve matching.
"""

import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import pickle
import json

import numpy as np
import cv2

from src.detection.yolo_detector import Detection
from src.tracking.object_tracker import Track


logger = logging.getLogger("animal_tracking.identification")


# ===========================================
# Data Classes
# ===========================================

@dataclass
class IdentifierConfig:
    """Tanımlama konfigürasyonu"""
    # Feature extraction
    feature_size: int = 512
    use_color_histogram: bool = True
    use_shape_features: bool = True
    
    # Matching
    similarity_threshold: float = 0.7
    max_gallery_size: int = 100
    
    # Kayıt
    save_gallery: bool = True
    gallery_path: str = "data/gallery"


@dataclass
class AnimalFeatures:
    """Hayvan feature vektörü"""
    animal_id: str
    class_name: str
    features: np.ndarray
    color_histogram: Optional[np.ndarray] = None
    shape_features: Optional[np.ndarray] = None
    timestamp: float = field(default_factory=time.time)
    
    # Görsel
    thumbnail: Optional[np.ndarray] = None
    
    def to_dict(self) -> dict:
        return {
            "animal_id": self.animal_id,
            "class_name": self.class_name,
            "feature_size": len(self.features) if self.features is not None else 0,
            "timestamp": self.timestamp,
        }


@dataclass
class IdentificationResult:
    """Tanımlama sonucu"""
    animal_id: str
    confidence: float
    is_new: bool
    class_name: str
    features: AnimalFeatures
    
    # Eşleşme bilgisi
    matched_id: Optional[str] = None
    similarity_score: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "animal_id": self.animal_id,
            "confidence": round(self.confidence, 4),
            "is_new": self.is_new,
            "class_name": self.class_name,
            "matched_id": self.matched_id,
            "similarity_score": round(self.similarity_score, 4),
        }


# ===========================================
# Feature Extractor
# ===========================================

class FeatureExtractor:
    """
    Hayvan görüntülerinden feature çıkarır.
    
    - Color histogram
    - Shape/contour features
    - Deep features (opsiyonel, model gerekli)
    """
    
    def __init__(self, config: Optional[IdentifierConfig] = None):
        self.config = config or IdentifierConfig()
    
    def extract(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Bounding box içindeki hayvandan feature çıkar.
        
        Args:
            image: BGR görüntü
            bbox: (x1, y1, x2, y2)
            
        Returns:
            Feature vektörü
        """
        x1, y1, x2, y2 = bbox
        
        # Crop
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return np.zeros(self.config.feature_size)
        
        features = []
        
        # Color histogram
        if self.config.use_color_histogram:
            color_feat = self._extract_color_histogram(crop)
            features.append(color_feat)
        
        # Shape features
        if self.config.use_shape_features:
            shape_feat = self._extract_shape_features(crop)
            features.append(shape_feat)
        
        # Birleştir ve normalize et
        if features:
            combined = np.concatenate(features)
            # Normalize
            norm = np.linalg.norm(combined)
            if norm > 0:
                combined = combined / norm
            return combined
        
        return np.zeros(self.config.feature_size)
    
    def _extract_color_histogram(self, image: np.ndarray, bins: int = 32) -> np.ndarray:
        """Color histogram çıkar (HSV)"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # H, S, V histogramları
            hist_h = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
            hist_s = cv2.calcHist([hsv], [1], None, [bins], [0, 256])
            hist_v = cv2.calcHist([hsv], [2], None, [bins], [0, 256])
            
            # Normalize
            cv2.normalize(hist_h, hist_h)
            cv2.normalize(hist_s, hist_s)
            cv2.normalize(hist_v, hist_v)
            
            return np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()])
        except:
            return np.zeros(bins * 3)
    
    def _extract_shape_features(self, image: np.ndarray) -> np.ndarray:
        """Shape features çıkar"""
        try:
            # Grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Resize to standard size
            resized = cv2.resize(gray, (64, 64))
            
            # HOG-like features (simplified)
            gx = cv2.Sobel(resized, cv2.CV_64F, 1, 0, ksize=3)
            gy = cv2.Sobel(resized, cv2.CV_64F, 0, 1, ksize=3)
            
            # Magnitude and angle
            mag, ang = cv2.cartToPolar(gx, gy)
            
            # Histogram of gradients (simplified)
            n_bins = 9
            hist = np.zeros((4, 4, n_bins))  # 4x4 grid, 9 bins
            
            cell_h, cell_w = 16, 16
            for i in range(4):
                for j in range(4):
                    cell_mag = mag[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                    cell_ang = ang[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                    hist[i, j] = np.histogram(cell_ang, bins=n_bins, 
                                             range=(0, np.pi*2), 
                                             weights=cell_mag)[0]
            
            # Normalize
            features = hist.flatten()
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm
            
            return features
        except:
            return np.zeros(144)  # 4*4*9


# ===========================================
# Animal Gallery
# ===========================================

class AnimalGallery:
    """
    Tanınan hayvanların galeri veritabanı.
    Feature vektörlerini ve metadata'yı saklar.
    """
    
    def __init__(self, config: Optional[IdentifierConfig] = None):
        self.config = config or IdentifierConfig()
        
        # Gallery storage
        self._gallery: Dict[str, AnimalFeatures] = {}
        self._feature_matrix: Optional[np.ndarray] = None
        self._id_list: List[str] = []
        
        # Sınıf bazlı indeks
        self._class_index: Dict[str, List[str]] = defaultdict(list)
        
        # ID counter
        self._next_id: Dict[str, int] = defaultdict(lambda: 1)
    
    @property
    def size(self) -> int:
        return len(self._gallery)
    
    @property
    def animal_ids(self) -> List[str]:
        return list(self._gallery.keys())
    
    def add(self, features: AnimalFeatures) -> str:
        """
        Galeriye yeni hayvan ekle.
        
        Args:
            features: AnimalFeatures nesnesi
            
        Returns:
            Animal ID
        """
        animal_id = features.animal_id
        
        # Eğer ID yoksa oluştur
        if not animal_id:
            class_prefix = features.class_name[:3].upper()
            animal_id = f"{class_prefix}_{self._next_id[features.class_name]:04d}"
            self._next_id[features.class_name] += 1
            features.animal_id = animal_id
        
        self._gallery[animal_id] = features
        self._class_index[features.class_name].append(animal_id)
        
        # Feature matrix güncelle
        self._update_feature_matrix()
        
        logger.info(f"Added animal to gallery: {animal_id}")
        return animal_id
    
    def remove(self, animal_id: str) -> bool:
        """Galeriden hayvan sil"""
        if animal_id not in self._gallery:
            return False
        
        features = self._gallery.pop(animal_id)
        self._class_index[features.class_name].remove(animal_id)
        self._update_feature_matrix()
        
        logger.info(f"Removed animal from gallery: {animal_id}")
        return True
    
    def get(self, animal_id: str) -> Optional[AnimalFeatures]:
        """Hayvan bilgilerini al"""
        return self._gallery.get(animal_id)
    
    def get_by_class(self, class_name: str) -> List[AnimalFeatures]:
        """Sınıfa göre hayvanları al"""
        ids = self._class_index.get(class_name, [])
        return [self._gallery[aid] for aid in ids]
    
    def _update_feature_matrix(self):
        """Feature matrix'i güncelle (hızlı arama için)"""
        if not self._gallery:
            self._feature_matrix = None
            self._id_list = []
            return
        
        self._id_list = list(self._gallery.keys())
        self._feature_matrix = np.array([
            self._gallery[aid].features for aid in self._id_list
        ])
    
    def search(
        self,
        query_features: np.ndarray,
        class_name: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """
        En benzer hayvanları bul.
        
        Args:
            query_features: Query feature vektörü
            class_name: Sadece bu sınıfta ara (opsiyonel)
            top_k: En iyi k sonuç
            
        Returns:
            [(animal_id, similarity_score), ...]
        """
        if self._feature_matrix is None or len(self._feature_matrix) == 0:
            return []
        
        # Sınıf filtresi
        if class_name:
            valid_ids = set(self._class_index.get(class_name, []))
            if not valid_ids:
                return []
            
            # Filtreli arama
            indices = [i for i, aid in enumerate(self._id_list) if aid in valid_ids]
            if not indices:
                return []
            
            features = self._feature_matrix[indices]
            ids = [self._id_list[i] for i in indices]
        else:
            features = self._feature_matrix
            ids = self._id_list
        
        # Cosine similarity
        query_norm = query_features / (np.linalg.norm(query_features) + 1e-8)
        feat_norms = features / (np.linalg.norm(features, axis=1, keepdims=True) + 1e-8)
        
        similarities = np.dot(feat_norms, query_norm)
        
        # Top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = [(ids[i], float(similarities[i])) for i in top_indices]
        return results
    
    def save(self, path: Optional[str] = None):
        """Galeriyi dosyaya kaydet"""
        save_path = Path(path or self.config.gallery_path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Features kaydet
        data = {
            "gallery": {},
            "next_id": dict(self._next_id),
        }
        
        for aid, feat in self._gallery.items():
            data["gallery"][aid] = {
                "animal_id": feat.animal_id,
                "class_name": feat.class_name,
                "features": feat.features.tolist(),
                "timestamp": feat.timestamp,
            }
        
        with open(save_path / "gallery.json", "w") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Gallery saved to {save_path}")
    
    def load(self, path: Optional[str] = None) -> bool:
        """Galeriyi dosyadan yükle"""
        load_path = Path(path or self.config.gallery_path)
        
        if not (load_path / "gallery.json").exists():
            logger.warning(f"Gallery file not found: {load_path}")
            return False
        
        try:
            with open(load_path / "gallery.json", "r") as f:
                data = json.load(f)
            
            self._gallery.clear()
            self._class_index.clear()
            
            for aid, info in data.get("gallery", {}).items():
                features = AnimalFeatures(
                    animal_id=info["animal_id"],
                    class_name=info["class_name"],
                    features=np.array(info["features"]),
                    timestamp=info.get("timestamp", 0),
                )
                self._gallery[aid] = features
                self._class_index[features.class_name].append(aid)
            
            self._next_id = defaultdict(lambda: 1, data.get("next_id", {}))
            self._update_feature_matrix()
            
            logger.info(f"Gallery loaded: {self.size} animals")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load gallery: {e}")
            return False


# ===========================================
# Animal Identifier
# ===========================================

class AnimalIdentifier:
    """
    Hayvan tanımlama ana sınıfı.
    
    Track'leri benzersiz hayvan ID'lerine eşler.
    
    Kullanım:
        identifier = AnimalIdentifier()
        
        # Her frame'de
        for track in tracking_result.tracks:
            result = identifier.identify(frame, track)
            print(f"Track {track.track_id} -> Animal {result.animal_id}")
    """
    
    def __init__(self, config: Optional[IdentifierConfig] = None):
        self.config = config or IdentifierConfig()
        
        # Bileşenler
        self.extractor = FeatureExtractor(self.config)
        self.gallery = AnimalGallery(self.config)
        
        # Track -> Animal ID mapping
        self._track_mapping: Dict[int, str] = {}
        
        # İstatistikler
        self._total_identifications: int = 0
        self._new_animals: int = 0
        self._matched_animals: int = 0
    
    @property
    def statistics(self) -> dict:
        return {
            "total_identifications": self._total_identifications,
            "new_animals": self._new_animals,
            "matched_animals": self._matched_animals,
            "gallery_size": self.gallery.size,
        }
    
    def identify(
        self,
        image: np.ndarray,
        track: Track
    ) -> IdentificationResult:
        """
        Track'i tanımla ve benzersiz ID ata.
        
        Args:
            image: BGR görüntü
            track: Track nesnesi
            
        Returns:
            IdentificationResult
        """
        self._total_identifications += 1
        
        # Daha önce eşleştirilmiş mi?
        if track.track_id in self._track_mapping:
            animal_id = self._track_mapping[track.track_id]
            existing = self.gallery.get(animal_id)
            
            if existing:
                return IdentificationResult(
                    animal_id=animal_id,
                    confidence=1.0,
                    is_new=False,
                    class_name=track.class_name,
                    features=existing,
                    matched_id=animal_id,
                    similarity_score=1.0,
                )
        
        # Feature çıkar
        features_vec = self.extractor.extract(image, track.bbox)
        
        # Thumbnail oluştur
        x1, y1, x2, y2 = track.bbox
        thumbnail = image[y1:y2, x1:x2].copy() if y2 > y1 and x2 > x1 else None
        
        # Galeride ara
        matches = self.gallery.search(
            features_vec,
            class_name=track.class_name,
            top_k=1
        )
        
        if matches and matches[0][1] >= self.config.similarity_threshold:
            # Mevcut hayvan ile eşleşti
            matched_id, similarity = matches[0]
            existing = self.gallery.get(matched_id)
            
            # Mapping güncelle
            self._track_mapping[track.track_id] = matched_id
            self._matched_animals += 1
            
            return IdentificationResult(
                animal_id=matched_id,
                confidence=similarity,
                is_new=False,
                class_name=track.class_name,
                features=existing,
                matched_id=matched_id,
                similarity_score=similarity,
            )
        else:
            # Yeni hayvan
            features = AnimalFeatures(
                animal_id="",  # Otomatik oluşturulacak
                class_name=track.class_name,
                features=features_vec,
                thumbnail=thumbnail,
            )
            
            animal_id = self.gallery.add(features)
            self._track_mapping[track.track_id] = animal_id
            self._new_animals += 1
            
            return IdentificationResult(
                animal_id=animal_id,
                confidence=1.0,
                is_new=True,
                class_name=track.class_name,
                features=features,
                similarity_score=0.0,
            )
    
    def get_animal_id(self, track_id: int) -> Optional[str]:
        """Track ID'den Animal ID al"""
        return self._track_mapping.get(track_id)
    
    def reset(self):
        """Tanımlayıcıyı sıfırla"""
        self._track_mapping.clear()
        self._total_identifications = 0
        self._new_animals = 0
        self._matched_animals = 0
        logger.info("Identifier reset (gallery preserved)")
    
    def reset_all(self):
        """Tanımlayıcı ve galeriyi sıfırla"""
        self.reset()
        self.gallery = AnimalGallery(self.config)
        logger.info("Identifier and gallery reset")
    
    def save(self, path: Optional[str] = None):
        """Galeriyi kaydet"""
        self.gallery.save(path)
    
    def load(self, path: Optional[str] = None) -> bool:
        """Galeriyi yükle"""
        return self.gallery.load(path)


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test
    config = IdentifierConfig()
    identifier = AnimalIdentifier(config)
    
    # Fake track oluştur
    class FakeTrack:
        def __init__(self, track_id, class_name, bbox):
            self.track_id = track_id
            self.class_name = class_name
            self.bbox = bbox
    
    # Test görüntüsü
    image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Track'ler oluştur
    track1 = FakeTrack(1, "dog", (100, 100, 200, 200))
    track2 = FakeTrack(2, "cat", (300, 100, 400, 200))
    track3 = FakeTrack(1, "dog", (110, 110, 210, 210))  # Aynı track, farklı pozisyon
    
    # Tanımla
    result1 = identifier.identify(image, track1)
    print(f"Track 1: {result1.animal_id} (new: {result1.is_new})")
    
    result2 = identifier.identify(image, track2)
    print(f"Track 2: {result2.animal_id} (new: {result2.is_new})")
    
    result3 = identifier.identify(image, track3)
    print(f"Track 3 (same as 1): {result3.animal_id} (new: {result3.is_new})")
    
    # İstatistikler
    print("\n=== Statistics ===")
    for k, v in identifier.statistics.items():
        print(f"{k}: {v}")
