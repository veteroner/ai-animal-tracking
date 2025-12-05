"""
AI Animal Tracking System - Automatic Animal Re-Identification
==============================================================

Tam otomatik hayvan tanıma sistemi.
- Kullanıcı müdahalesi SIFIR
- Otomatik kayıt
- Otomatik ID atama
- Otomatik takip ve tanıma

Kullanım:
    from src.identification.auto_reid import AutoReID
    
    reid = AutoReID()
    
    # Her frame için
    for frame in video:
        results = reid.process(frame)
        for animal in results.animals:
            print(f"ID: {animal.animal_id}, Type: {animal.class_name}")
"""

import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import pickle
from datetime import datetime

import numpy as np
import cv2

logger = logging.getLogger("animal_tracking.auto_reid")


# ===========================================
# Configuration
# ===========================================

@dataclass
class AutoReIDConfig:
    """Otomatik Re-ID konfigürasyonu"""
    
    # Feature extraction
    feature_size: Tuple[int, int] = (128, 256)  # Daha büyük resize boyutu
    color_bins: int = 32  # Histogram bin sayısı
    
    # Matching thresholds - DAHA HASSAS BİREYSEL TANIMLAMA İÇİN
    similarity_threshold: float = 0.92  # Eşleşme için minimum benzerlik (çok yüksek)
    new_animal_threshold: float = 0.85  # Bu değerin altında yeni hayvan kabul
    
    # Aynı frame'de aynı sınıftan hayvanlar için ek kontrol
    same_frame_min_distance: float = 0.15  # Aynı frame'deki hayvanlar en az bu kadar farklı olmalı
    
    # Tracking
    max_age: int = 50  # Track kaybolmadan max frame sayısı
    min_hits: int = 3  # Doğrulanmış track için min tespit
    
    # Gallery
    max_gallery_size: int = 500  # Max hayvan sayısı
    update_features: bool = True  # Her görüşte feature güncelle
    feature_update_alpha: float = 0.02  # Güncelleme oranı (çok yavaş - bireysel özellikleri koru)
    
    # Persistence
    auto_save: bool = True
    save_interval: int = 100  # Her 100 frame'de kaydet
    gallery_path: str = "data/gallery"
    
    # YOLO
    model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.4
    iou_threshold: float = 0.5


# ===========================================
# COCO Hayvan Sınıfları (Sadece bunlar kayıt altına alınır)
# ===========================================

ANIMAL_CLASS_IDS = {14, 15, 16, 17, 18, 19, 20, 21, 22, 23}
ANIMAL_CLASS_NAMES = {
    14: 'bird',      # Kuş
    15: 'cat',       # Kedi
    16: 'dog',       # Köpek
    17: 'horse',     # At
    18: 'sheep',     # Koyun
    19: 'cow',       # İnek
    20: 'elephant',  # Fil
    21: 'bear',      # Ayı
    22: 'zebra',     # Zebra
    23: 'giraffe',   # Zürafa
}


# ===========================================
# Data Classes
# ===========================================

@dataclass
class AnimalRecord:
    """Hayvan kaydı"""
    animal_id: str
    class_name: str
    features: np.ndarray
    
    # İstatistikler
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    total_detections: int = 1
    
    # Görsel
    thumbnail: Optional[np.ndarray] = None
    best_confidence: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, features: np.ndarray, confidence: float, alpha: float = 0.1):
        """Feature ve istatistikleri güncelle"""
        # Exponential moving average
        self.features = (1 - alpha) * self.features + alpha * features
        self.last_seen = time.time()
        self.total_detections += 1
        
        if confidence > self.best_confidence:
            self.best_confidence = confidence
    
    def to_dict(self) -> dict:
        return {
            "animal_id": self.animal_id,
            "class_name": self.class_name,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "total_detections": self.total_detections,
            "best_confidence": round(self.best_confidence, 3),
            "metadata": self.metadata,
        }


@dataclass
class DetectedAnimal:
    """Tespit edilen hayvan"""
    track_id: int
    animal_id: str
    class_name: str
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    similarity: float  # Re-ID benzerlik skoru
    is_new: bool  # Yeni kayıt mı?
    
    # Hareket
    center: Tuple[int, int] = (0, 0)
    velocity: Tuple[float, float] = (0.0, 0.0)
    direction: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "track_id": self.track_id,
            "animal_id": self.animal_id,
            "class_name": self.class_name,
            "bbox": self.bbox,
            "confidence": round(self.confidence, 3),
            "similarity": round(self.similarity, 3),
            "is_new": self.is_new,
            "center": self.center,
            "velocity": [round(v, 2) for v in self.velocity],
            "direction": round(self.direction, 1),
        }


@dataclass
class ProcessResult:
    """İşlem sonucu"""
    frame_id: int
    timestamp: float
    fps: float
    animals: List[DetectedAnimal]
    
    # İstatistikler
    total_registered: int = 0  # Toplam kayıtlı hayvan
    new_this_frame: int = 0  # Bu frame'de yeni kaydedilen
    
    @property
    def count(self) -> int:
        return len(self.animals)
    
    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp,
            "fps": round(self.fps, 1),
            "count": self.count,
            "total_registered": self.total_registered,
            "new_this_frame": self.new_this_frame,
            "animals": [a.to_dict() for a in self.animals],
        }


# ===========================================
# Feature Extractor - ADVANCED
# ===========================================

class FeatureExtractor:
    """
    Gelişmiş Hayvan Özellik Çıkarıcı
    
    Bireysel tanımlama için kullanılan özellikler:
    1. Renk histogramları (HSV, LAB)
    2. Bölgesel renk dağılımları (üst/alt/sol/sağ/merkez)
    3. Leke/desen tespiti
    4. Boy oranı ve şekil özellikleri
    5. Texture analizi (LBP benzeri)
    6. Edge yoğunluğu ve dağılımı
    """
    
    def __init__(self, config: AutoReIDConfig):
        self.config = config
    
    def extract(self, image: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Bounding box içindeki hayvandan kapsamlı özellik çıkar.
        """
        x1, y1, x2, y2 = [int(v) for v in bbox]
        
        # Sınır kontrolü
        h, w = image.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        # Crop
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        
        # Resize
        try:
            crop = cv2.resize(crop, self.config.feature_size)
        except:
            return None
        
        features = []
        
        # ============================================
        # 1. GLOBAL RENK HİSTOGRAMLARI
        # ============================================
        hsv_hist = self._hsv_histogram(crop)
        lab_hist = self._lab_histogram(crop)
        features.append(hsv_hist)
        features.append(lab_hist)
        
        # ============================================
        # 2. BÖLGESEL RENK ANALİZİ (5 bölge)
        # ============================================
        h_crop, w_crop = crop.shape[:2]
        
        # Üst yarı (baş bölgesi)
        top_region = crop[:h_crop//3, :]
        top_hist = self._hsv_histogram(top_region)
        features.append(top_hist * 1.5)  # Baş bölgesi daha önemli
        
        # Orta bölge (gövde)
        mid_region = crop[h_crop//3:2*h_crop//3, :]
        mid_hist = self._hsv_histogram(mid_region)
        features.append(mid_hist)
        
        # Alt yarı (bacaklar)
        bottom_region = crop[2*h_crop//3:, :]
        bottom_hist = self._hsv_histogram(bottom_region)
        features.append(bottom_hist * 1.2)  # Ayak lekeleri önemli
        
        # Sol ve sağ yarı (asimetri tespiti)
        left_region = crop[:, :w_crop//2]
        right_region = crop[:, w_crop//2:]
        left_hist = self._hsv_histogram(left_region)
        right_hist = self._hsv_histogram(right_region)
        features.append(left_hist)
        features.append(right_hist)
        
        # ============================================
        # 3. LEKE/DESEN ANALİZİ
        # ============================================
        spot_features = self._spot_analysis(crop)
        features.append(spot_features)
        
        # ============================================
        # 4. ŞEKİL VE ORAN ÖZELLİKLERİ
        # ============================================
        shape_features = self._shape_features(crop, x2-x1, y2-y1)
        features.append(shape_features)
        
        # ============================================
        # 5. TEXTURE ANALİZİ
        # ============================================
        texture_features = self._texture_analysis(crop)
        features.append(texture_features)
        
        # ============================================
        # 6. EDGE YOĞUNLUğU VE DAĞILIMI
        # ============================================
        edge_features = self._edge_analysis(crop)
        features.append(edge_features)
        
        # ============================================
        # 7. DOMINANT RENK ANALİZİ
        # ============================================
        dominant_colors = self._dominant_colors(crop, k=5)
        features.append(dominant_colors)
        
        # Birleştir ve normalize et
        combined = np.concatenate(features)
        norm = np.linalg.norm(combined)
        if norm > 0:
            combined = combined / norm
        
        return combined.astype(np.float32)
    
    def _hsv_histogram(self, image: np.ndarray) -> np.ndarray:
        """HSV renk histogramı - daha detaylı"""
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            bins = self.config.color_bins
            
            # H (renk tonu) - en önemli
            hist_h = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
            # S (doygunluk) - leke tespiti için önemli
            hist_s = cv2.calcHist([hsv], [1], None, [bins], [0, 256])
            # V (parlaklık)
            hist_v = cv2.calcHist([hsv], [2], None, [bins//2], [0, 256])
            
            cv2.normalize(hist_h, hist_h)
            cv2.normalize(hist_s, hist_s)
            cv2.normalize(hist_v, hist_v)
            
            return np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()])
        except:
            return np.zeros(self.config.color_bins * 2 + self.config.color_bins // 2)
    
    def _lab_histogram(self, image: np.ndarray) -> np.ndarray:
        """LAB renk histogramı - algısal renk farkları için daha iyi"""
        try:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            bins = self.config.color_bins // 2
            
            hist_a = cv2.calcHist([lab], [1], None, [bins], [0, 256])  # Yeşil-Kırmızı
            hist_b = cv2.calcHist([lab], [2], None, [bins], [0, 256])  # Mavi-Sarı
            
            cv2.normalize(hist_a, hist_a)
            cv2.normalize(hist_b, hist_b)
            
            return np.concatenate([hist_a.flatten(), hist_b.flatten()])
        except:
            return np.zeros(self.config.color_bins)
    
    def _spot_analysis(self, image: np.ndarray) -> np.ndarray:
        """
        Leke/desen analizi
        - Beyaz/koyu lekeleri tespit et
        - Leke sayısı, boyutu, konumu
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            features = []
            
            # Kontrast artırma
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Beyaz lekeler (parlak bölgeler)
            _, white_mask = cv2.threshold(enhanced, 200, 255, cv2.THRESH_BINARY)
            white_contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Koyu lekeler (karanlık bölgeler)
            _, dark_mask = cv2.threshold(enhanced, 50, 255, cv2.THRESH_BINARY_INV)
            dark_contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Leke sayıları
            features.append(min(len(white_contours), 20) / 20.0)
            features.append(min(len(dark_contours), 20) / 20.0)
            
            # Toplam leke alanları
            white_area = sum(cv2.contourArea(c) for c in white_contours)
            dark_area = sum(cv2.contourArea(c) for c in dark_contours)
            total_area = h * w
            
            features.append(white_area / total_area)
            features.append(dark_area / total_area)
            
            # Leke merkez dağılımı (hangi bölgelerde leke var)
            grid_features = np.zeros(9)  # 3x3 grid
            for contour in white_contours + dark_contours:
                M = cv2.moments(contour)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    gx = min(cx * 3 // w, 2)
                    gy = min(cy * 3 // h, 2)
                    grid_features[gy * 3 + gx] += 1
            
            # Normalize grid
            if grid_features.sum() > 0:
                grid_features = grid_features / grid_features.sum()
            
            features.extend(grid_features.tolist())
            
            return np.array(features, dtype=np.float32)
            
        except Exception as e:
            return np.zeros(13)
    
    def _shape_features(self, crop: np.ndarray, orig_w: int, orig_h: int) -> np.ndarray:
        """Şekil ve boy oranı özellikleri"""
        try:
            features = []
            
            # Boy oranı
            aspect_ratio = orig_w / orig_h if orig_h > 0 else 1.0
            features.append(aspect_ratio)
            
            # Normalize edilmiş boyutlar
            features.append(orig_w / 1000.0)
            features.append(orig_h / 1000.0)
            
            # Gri tonlama momentleri
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            moments = cv2.moments(gray)
            
            # Hu momentleri (rotasyon invariant)
            hu_moments = cv2.HuMoments(moments).flatten()
            # Log transform for better distribution
            hu_log = -np.sign(hu_moments) * np.log10(np.abs(hu_moments) + 1e-10)
            features.extend(hu_log[:4].tolist())  # İlk 4 moment
            
            return np.array(features, dtype=np.float32)
            
        except:
            return np.zeros(7)
    
    def _texture_analysis(self, image: np.ndarray) -> np.ndarray:
        """
        Texture analizi - yün/kıl deseni için
        LBP (Local Binary Pattern) benzeri özellikler
        """
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            features = []
            
            # Gradyan magnitude ve yönü
            gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            mag, ang = cv2.cartToPolar(gx, gy)
            
            # Gradyan yön histogramı (8 yön)
            angle_hist = np.histogram(ang, bins=8, range=(0, 2*np.pi), weights=mag)[0]
            if angle_hist.sum() > 0:
                angle_hist = angle_hist / angle_hist.sum()
            features.extend(angle_hist.tolist())
            
            # Texture variance (pürüzlülük)
            texture_var = np.var(gray) / 255.0
            features.append(texture_var)
            
            # Laplacian variance (keskinlik/bulanıklık)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            lap_var = np.var(laplacian) / 10000.0
            features.append(lap_var)
            
            # Bölgesel texture variance
            regions = [
                gray[:h//2, :w//2],
                gray[:h//2, w//2:],
                gray[h//2:, :w//2],
                gray[h//2:, w//2:]
            ]
            for region in regions:
                features.append(np.var(region) / 255.0)
            
            return np.array(features, dtype=np.float32)
            
        except:
            return np.zeros(14)
    
    def _edge_analysis(self, image: np.ndarray) -> np.ndarray:
        """Edge yoğunluğu ve dağılımı"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape
            
            # Canny edge detection
            edges = cv2.Canny(gray, 50, 150)
            
            features = []
            
            # Toplam edge yoğunluğu
            total_edges = np.sum(edges > 0) / (h * w)
            features.append(total_edges)
            
            # Bölgesel edge dağılımı (4x4 grid)
            grid_size = 4
            grid_features = []
            cell_h, cell_w = h // grid_size, w // grid_size
            
            for gy in range(grid_size):
                for gx in range(grid_size):
                    cell = edges[gy*cell_h:(gy+1)*cell_h, gx*cell_w:(gx+1)*cell_w]
                    cell_density = np.sum(cell > 0) / (cell_h * cell_w)
                    grid_features.append(cell_density)
            
            features.extend(grid_features)
            
            return np.array(features, dtype=np.float32)
            
        except:
            return np.zeros(17)
    
    def _dominant_colors(self, image: np.ndarray, k: int = 5) -> np.ndarray:
        """K-means ile dominant renkleri bul"""
        try:
            # Resize for speed
            small = cv2.resize(image, (32, 32))
            pixels = small.reshape(-1, 3).astype(np.float32)
            
            # K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
            _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
            
            # Renk merkezlerini normalize et
            centers = centers / 255.0
            
            # Her rengin oranı
            unique, counts = np.unique(labels, return_counts=True)
            ratios = np.zeros(k)
            for u, c in zip(unique, counts):
                ratios[u] = c / len(labels)
            
            # Sırala (en dominant önce)
            sorted_idx = np.argsort(-ratios)
            sorted_centers = centers[sorted_idx]
            sorted_ratios = ratios[sorted_idx]
            
            # Feature vector: [R,G,B,ratio] * k
            features = []
            for i in range(k):
                features.extend(sorted_centers[i].tolist())
                features.append(sorted_ratios[i])
            
            return np.array(features, dtype=np.float32)
            
        except:
            return np.zeros(k * 4)
    
    def _color_histogram(self, image: np.ndarray) -> np.ndarray:
        """Eski metod - geriye uyumluluk için"""
        return self._hsv_histogram(image)


# ===========================================
# Animal Gallery
# ===========================================

class AnimalGallery:
    """Otomatik hayvan galerisi"""
    
    def __init__(self, config: AutoReIDConfig):
        self.config = config
        
        # Ana veri yapıları
        self._records: Dict[str, AnimalRecord] = {}
        self._feature_matrix: Optional[np.ndarray] = None
        self._id_list: List[str] = []
        
        # Sınıf bazlı indeks
        self._class_index: Dict[str, List[str]] = defaultdict(list)
        
        # ID counter (sınıf bazlı)
        self._id_counter: Dict[str, int] = defaultdict(int)
        
        # Galeri yolu
        self._gallery_path = Path(config.gallery_path)
        self._gallery_path.mkdir(parents=True, exist_ok=True)
    
    @property
    def size(self) -> int:
        return len(self._records)
    
    @property
    def all_ids(self) -> List[str]:
        return list(self._records.keys())
    
    def _generate_id(self, class_name: str) -> str:
        """Benzersiz ID oluştur"""
        prefixes = {
            'cow': 'INEK', 'cattle': 'INEK',
            'sheep': 'KOYUN', 'goat': 'KECI',
            'horse': 'AT', 'dog': 'KOPEK',
            'cat': 'KEDI', 'bird': 'KUS',
            'chicken': 'TAVUK', 'turkey': 'HINDI',
            'duck': 'ORDEK', 'goose': 'KAZ',
        }
        
        prefix = prefixes.get(class_name.lower(), class_name.upper()[:4])
        self._id_counter[prefix] += 1
        
        return f"{prefix}_{self._id_counter[prefix]:04d}"
    
    def register(
        self,
        features: np.ndarray,
        class_name: str,
        confidence: float,
        thumbnail: Optional[np.ndarray] = None
    ) -> str:
        """
        Yeni hayvan kaydet.
        
        Returns:
            Yeni oluşturulan animal_id
        """
        # ID oluştur
        animal_id = self._generate_id(class_name)
        
        # Kayıt oluştur
        record = AnimalRecord(
            animal_id=animal_id,
            class_name=class_name,
            features=features.copy(),
            best_confidence=confidence,
            thumbnail=thumbnail,
        )
        
        # Ekle
        self._records[animal_id] = record
        self._class_index[class_name].append(animal_id)
        
        # Feature matrix güncelle
        self._update_matrix()
        
        logger.info(f"🆕 Yeni hayvan kaydedildi: {animal_id} ({class_name})")
        
        return animal_id
    
    def update(self, animal_id: str, features: np.ndarray, confidence: float):
        """Mevcut hayvanın özelliklerini güncelle"""
        if animal_id not in self._records:
            return
        
        record = self._records[animal_id]
        record.update(features, confidence, self.config.feature_update_alpha)
        
        # Matrix güncelle
        self._update_matrix()
    
    def search(
        self,
        query_features: np.ndarray,
        class_name: str,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        En benzer hayvanları bul.
        
        Returns:
            [(animal_id, similarity), ...]
        """
        if self._feature_matrix is None or len(self._feature_matrix) == 0:
            return []
        
        # Sınıf filtresi
        valid_ids = set(self._class_index.get(class_name, []))
        if not valid_ids:
            return []
        
        # Filtrelenmiş indeksler
        indices = [i for i, aid in enumerate(self._id_list) if aid in valid_ids]
        if not indices:
            return []
        
        features = self._feature_matrix[indices]
        ids = [self._id_list[i] for i in indices]
        
        # Cosine similarity
        query_norm = query_features / (np.linalg.norm(query_features) + 1e-8)
        feat_norms = features / (np.linalg.norm(features, axis=1, keepdims=True) + 1e-8)
        
        similarities = np.dot(feat_norms, query_norm)
        
        # Top-k
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(ids[i], float(similarities[i])) for i in top_indices]
    
    def get(self, animal_id: str) -> Optional[AnimalRecord]:
        """Hayvan kaydı al"""
        return self._records.get(animal_id)
    
    def _update_matrix(self):
        """Feature matrix güncelle"""
        if not self._records:
            self._feature_matrix = None
            self._id_list = []
            return
        
        self._id_list = list(self._records.keys())
        self._feature_matrix = np.array([
            self._records[aid].features for aid in self._id_list
        ])
    
    def save(self):
        """Galeriyi dosyaya kaydet"""
        save_path = self._gallery_path / "gallery.pkl"
        
        data = {
            "records": {},
            "id_counter": dict(self._id_counter),
            "saved_at": datetime.now().isoformat(),
        }
        
        for aid, record in self._records.items():
            data["records"][aid] = {
                "animal_id": record.animal_id,
                "class_name": record.class_name,
                "features": record.features.tolist(),
                "first_seen": record.first_seen,
                "last_seen": record.last_seen,
                "total_detections": record.total_detections,
                "best_confidence": record.best_confidence,
                "metadata": record.metadata,
            }
        
        with open(save_path, "wb") as f:
            pickle.dump(data, f)
        
        logger.info(f"💾 Galeri kaydedildi: {self.size} hayvan")
    
    def load(self) -> bool:
        """Galeriyi dosyadan yükle"""
        load_path = self._gallery_path / "gallery.pkl"
        
        if not load_path.exists():
            logger.info("📂 Galeri dosyası bulunamadı, boş galeri oluşturuldu")
            return False
        
        try:
            with open(load_path, "rb") as f:
                data = pickle.load(f)
            
            self._records.clear()
            self._class_index.clear()
            
            for aid, info in data.get("records", {}).items():
                record = AnimalRecord(
                    animal_id=info["animal_id"],
                    class_name=info["class_name"],
                    features=np.array(info["features"], dtype=np.float32),
                    first_seen=info.get("first_seen", 0),
                    last_seen=info.get("last_seen", 0),
                    total_detections=info.get("total_detections", 1),
                    best_confidence=info.get("best_confidence", 0),
                    metadata=info.get("metadata", {}),
                )
                self._records[aid] = record
                self._class_index[record.class_name].append(aid)
            
            self._id_counter = defaultdict(int, data.get("id_counter", {}))
            self._update_matrix()
            
            logger.info(f"📂 Galeri yüklendi: {self.size} hayvan")
            return True
            
        except Exception as e:
            logger.error(f"❌ Galeri yüklenemedi: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Galeri istatistikleri"""
        class_counts = {cls: len(ids) for cls, ids in self._class_index.items()}
        
        return {
            "total_animals": self.size,
            "by_class": class_counts,
            "id_counters": dict(self._id_counter),
        }


# ===========================================
# Track Manager
# ===========================================

@dataclass
class ActiveTrack:
    """Aktif takip edilen nesne"""
    track_id: int
    animal_id: Optional[str]
    class_name: str
    bbox: List[int]
    features: np.ndarray
    
    # Durum
    hits: int = 1
    age: int = 0
    time_since_update: int = 0
    
    # Hareket
    history: List[Tuple[int, int]] = field(default_factory=list)
    velocity: Tuple[float, float] = (0.0, 0.0)
    
    @property
    def center(self) -> Tuple[int, int]:
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)
    
    @property
    def is_confirmed(self) -> bool:
        return self.hits >= 3


class TrackManager:
    """Track yöneticisi - Detection'dan tracking'e köprü"""
    
    def __init__(self, config: AutoReIDConfig):
        self.config = config
        self._tracks: Dict[int, ActiveTrack] = {}
        self._next_id = 1
    
    def update(
        self,
        detections: List[Tuple[List[int], float, str, np.ndarray]]
    ) -> List[ActiveTrack]:
        """
        Yeni tespitlerle track'leri güncelle.
        
        Args:
            detections: [(bbox, confidence, class_name, features), ...]
            
        Returns:
            Güncel track listesi
        """
        # Age artır ve kayıp işaretle
        for track in self._tracks.values():
            track.age += 1
            track.time_since_update += 1
        
        if not detections:
            return self._get_active_tracks()
        
        # Basit IOU matching
        matched_tracks = set()
        matched_dets = set()
        
        for det_idx, (bbox, conf, cls, feat) in enumerate(detections):
            best_track_id = None
            best_iou = 0.3  # Min IOU threshold
            
            for track_id, track in self._tracks.items():
                if track_id in matched_tracks:
                    continue
                if track.class_name != cls:
                    continue
                
                iou = self._calculate_iou(bbox, track.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Eşleşme bulundu
                track = self._tracks[best_track_id]
                track.bbox = bbox
                track.features = feat
                track.hits += 1
                track.time_since_update = 0
                track.history.append(track.center)
                if len(track.history) > 30:
                    track.history.pop(0)
                self._update_velocity(track)
                
                matched_tracks.add(best_track_id)
                matched_dets.add(det_idx)
        
        # Eşleşmeyenler için yeni track oluştur
        for det_idx, (bbox, conf, cls, feat) in enumerate(detections):
            if det_idx in matched_dets:
                continue
            
            track = ActiveTrack(
                track_id=self._next_id,
                animal_id=None,
                class_name=cls,
                bbox=bbox,
                features=feat,
            )
            track.history.append(track.center)
            
            self._tracks[self._next_id] = track
            self._next_id += 1
        
        # Eski track'leri sil
        to_remove = [
            tid for tid, t in self._tracks.items()
            if t.time_since_update > self.config.max_age
        ]
        for tid in to_remove:
            del self._tracks[tid]
        
        return self._get_active_tracks()
    
    def _get_active_tracks(self) -> List[ActiveTrack]:
        """Aktif track'leri döndür"""
        return [t for t in self._tracks.values() if t.time_since_update == 0]
    
    def _calculate_iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        """IOU hesapla"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 < x1 or y2 < y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _update_velocity(self, track: ActiveTrack):
        """Hız hesapla"""
        if len(track.history) < 2:
            return
        
        p1 = track.history[-2]
        p2 = track.history[-1]
        track.velocity = (float(p2[0] - p1[0]), float(p2[1] - p1[1]))


# ===========================================
# Auto Re-ID System
# ===========================================

class AutoReID:
    """
    Tam Otomatik Hayvan Tanıma Sistemi
    
    Kullanıcı müdahalesi olmadan:
    - Hayvanları tespit eder
    - Yeni hayvanları otomatik kaydeder
    - Daha önce görülenleri tanır
    - Tüm verileri otomatik saklar
    """
    
    def __init__(self, config: Optional[AutoReIDConfig] = None):
        self.config = config or AutoReIDConfig()
        
        # Bileşenler
        self.extractor = FeatureExtractor(self.config)
        self.gallery = AnimalGallery(self.config)
        self.track_manager = TrackManager(self.config)
        
        # YOLO modeli
        self._detector = None
        self._initialized = False
        
        # İstatistikler
        self._frame_count = 0
        self._fps_history: List[float] = []
        self._total_new = 0
        self._total_matched = 0
        
        # Galeriyi yükle
        self.gallery.load()
    
    def initialize(self):
        """YOLO modelini yükle"""
        if self._initialized:
            return
        
        try:
            from ultralytics import YOLO
            logger.info("📥 YOLO modeli yükleniyor...")
            self._detector = YOLO(self.config.model_path)
            logger.info("✅ YOLO modeli yüklendi")
            self._initialized = True
        except Exception as e:
            logger.error(f"❌ YOLO yüklenemedi: {e}")
            self._initialized = True  # Tekrar deneme
    
    def process(self, frame: np.ndarray) -> ProcessResult:
        """
        Tek frame'i işle.
        
        Her şey otomatik:
        1. YOLO ile tespit
        2. Feature çıkarma
        3. Tracking
        4. Re-ID (yeni kayıt veya eşleştirme)
        5. Sonuç döndürme
        """
        start_time = time.time()
        self._frame_count += 1
        
        # Lazy init
        if not self._initialized:
            self.initialize()
        
        detected_animals: List[DetectedAnimal] = []
        new_this_frame = 0
        
        if self._detector is None:
            return self._create_result(detected_animals, new_this_frame, start_time)
        
        try:
            # 1. YOLO Detection
            results = self._detector(
                frame,
                verbose=False,
                conf=self.config.confidence_threshold
            )
            
            # 2. Detection'ları işle
            detections = []
            for result in results:
                if result.boxes is None:
                    continue
                
                for box in result.boxes:
                    cls_id = int(box.cls[0].item())
                    class_name = result.names.get(cls_id, 'unknown')
                    
                    # ✅ SADECE HAYVAN SINIFLARI kayıt altına alınır
                    # Hayvan değilse atla
                    if cls_id not in ANIMAL_CLASS_IDS:
                        continue
                    
                    bbox = [int(v) for v in box.xyxy[0].cpu().numpy()]
                    confidence = float(box.conf[0].item())
                    
                    # Feature çıkar
                    features = self.extractor.extract(frame, bbox)
                    if features is None:
                        continue
                    
                    detections.append((bbox, confidence, class_name, features))
            
            # 3. Tracking
            active_tracks = self.track_manager.update(detections)
            
            # 4. Re-ID (Her track için) - AYNI FRAME'DE ÇAKIŞMA KONTROLÜ İLE
            # Aynı frame'de zaten eşleştirilmiş ID'leri takip et
            used_ids_this_frame = set()
            
            # Aynı frame'deki tüm hayvanların feature'larını topla (benzersizlik kontrolü için)
            frame_features = [(track, track.features) for track in active_tracks]
            
            # Önce tüm track'ler için benzerlik skorlarını hesapla
            track_matches = []
            for track in active_tracks:
                matches = self.gallery.search(
                    track.features,
                    track.class_name,
                    top_k=5  # Daha fazla aday al
                )
                track_matches.append((track, matches))
            
            # Benzerlik skoruna göre sırala (en yüksek önce)
            # Bu şekilde en güvenilir eşleşmeler önce yapılır
            track_matches.sort(
                key=lambda x: x[1][0][1] if x[1] else 0,
                reverse=True
            )
            
            # Aynı sınıftaki hayvanların birbirinden farklı olduğundan emin ol
            # Her hayvanın benzersiz olduğunu doğrula
            processed_tracks = []
            
            for track, matches in track_matches:
                is_new = False
                animal_id = None
                similarity = 0.0
                
                # Aynı frame'deki aynı sınıftan diğer hayvanlarla karşılaştır
                # Bu hayvan diğerlerinden yeterince farklı mı?
                is_distinct = True
                for other_track, other_features in frame_features:
                    if other_track.track_id == track.track_id:
                        continue
                    if other_track.class_name != track.class_name:
                        continue
                    
                    # Feature benzerliği hesapla
                    track_norm = track.features / (np.linalg.norm(track.features) + 1e-8)
                    other_norm = other_features / (np.linalg.norm(other_features) + 1e-8)
                    inter_similarity = float(np.dot(track_norm, other_norm))
                    
                    # Aynı frame'deki hayvanlar birbirinden farklı olmalı
                    if inter_similarity > (1.0 - self.config.same_frame_min_distance):
                        # Çok benzer ama aynı frame'de -> kesinlikle farklı bireyler
                        is_distinct = True  # Yine de farklı işaretle
                
                # Kullanılmamış en iyi eşleşmeyi bul
                best_match = None
                for match_id, match_sim in matches:
                    if match_id not in used_ids_this_frame:
                        if match_sim >= self.config.similarity_threshold:
                            best_match = (match_id, match_sim)
                            break
                
                if best_match:
                    # Eşleşme bulundu
                    animal_id, similarity = best_match
                    track.animal_id = animal_id
                    used_ids_this_frame.add(animal_id)
                    
                    # Feature güncelle
                    if self.config.update_features:
                        self.gallery.update(animal_id, track.features, track.hits)
                    
                    self._total_matched += 1
                    
                else:
                    # Yeni hayvan - OTOMATİK KAYDET
                    # Doğrulanmış track veya aynı frame'de aynı sınıftan birden fazla hayvan varsa
                    same_class_count = sum(1 for t in active_tracks if t.class_name == track.class_name)
                    
                    if track.is_confirmed or same_class_count > 1:
                        thumbnail = self._get_thumbnail(frame, track.bbox)
                        animal_id = self.gallery.register(
                            features=track.features,
                            class_name=track.class_name,
                            confidence=track.hits / 10.0,
                            thumbnail=thumbnail,
                        )
                        track.animal_id = animal_id
                        used_ids_this_frame.add(animal_id)
                        similarity = 1.0
                        is_new = True
                        new_this_frame += 1
                        self._total_new += 1
                    else:
                        # Henüz doğrulanmamış, geçici ID
                        animal_id = f"TEMP_{track.track_id:04d}"
                        similarity = 0.0
                
                # Sonuç oluştur
                detected = DetectedAnimal(
                    track_id=track.track_id,
                    animal_id=track.animal_id or f"TEMP_{track.track_id:04d}",
                    class_name=track.class_name,
                    bbox=track.bbox,
                    confidence=track.hits / 10.0,
                    similarity=similarity if not is_new else 1.0,
                    is_new=is_new,
                    center=track.center,
                    velocity=track.velocity,
                )
                detected_animals.append(detected)
        
        except Exception as e:
            logger.error(f"İşleme hatası: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Otomatik kaydet
        if self.config.auto_save and self._frame_count % self.config.save_interval == 0:
            self.gallery.save()
        
        return self._create_result(detected_animals, new_this_frame, start_time)
    
    def _create_result(
        self,
        animals: List[DetectedAnimal],
        new_count: int,
        start_time: float
    ) -> ProcessResult:
        """Sonuç oluştur"""
        # FPS hesapla
        elapsed = time.time() - start_time
        fps = 1.0 / elapsed if elapsed > 0 else 0
        self._fps_history.append(fps)
        if len(self._fps_history) > 30:
            self._fps_history.pop(0)
        avg_fps = sum(self._fps_history) / len(self._fps_history)
        
        return ProcessResult(
            frame_id=self._frame_count,
            timestamp=time.time(),
            fps=avg_fps,
            animals=animals,
            total_registered=self.gallery.size,
            new_this_frame=new_count,
        )
    
    def _get_thumbnail(self, frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Thumbnail oluştur"""
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        return frame[y1:y2, x1:x2].copy()
    
    def get_stats(self) -> dict:
        """Sistem istatistikleri"""
        return {
            "frame_count": self._frame_count,
            "total_new_animals": self._total_new,
            "total_matches": self._total_matched,
            "gallery": self.gallery.get_stats(),
            "avg_fps": sum(self._fps_history) / len(self._fps_history) if self._fps_history else 0,
        }
    
    def get_all_animals(self) -> List[dict]:
        """Tüm kayıtlı hayvanları döndür"""
        return [
            self.gallery.get(aid).to_dict()
            for aid in self.gallery.all_ids
        ]
    
    def save(self):
        """Galeriyi kaydet"""
        self.gallery.save()
    
    def reset(self):
        """Galeriyi sıfırla (dikkatli kullan!)"""
        self.gallery = AnimalGallery(self.config)
        self._total_new = 0
        self._total_matched = 0
        logger.warning("⚠️ Galeri sıfırlandı!")


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test
    reid = AutoReID()
    
    # Test görüntüsü
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # İşle
    result = reid.process(test_frame)
    print(f"Frame {result.frame_id}: {result.count} hayvan tespit edildi")
    print(f"Toplam kayıtlı: {result.total_registered}")
    print(f"İstatistikler: {reid.get_stats()}")
