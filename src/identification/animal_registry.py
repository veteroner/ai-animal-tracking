"""
Animal Registry
Hayvan kayıt sistemi - kimlik, embedding ve profil yönetimi
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import numpy as np
import cv2

from .animal_id_manager import AnimalIDManager, AnimalProfile, AnimalType, AnimalGender
from .embedding_store import EmbeddingStore
from .feature_extractor import DeepFeatureExtractor, FeatureExtractorConfig

logger = logging.getLogger(__name__)


@dataclass
class RegistrationResult:
    """Kayıt sonucu"""
    success: bool
    animal_id: Optional[str] = None
    is_new: bool = False
    confidence: float = 0.0
    message: str = ""


@dataclass
class IdentificationResult:
    """Tanımlama sonucu"""
    identified: bool
    animal_id: Optional[str] = None
    animal_profile: Optional[AnimalProfile] = None
    confidence: float = 0.0
    candidates: List[Tuple[str, float]] = field(default_factory=list)


class AnimalRegistry:
    """
    Hayvan kayıt sistemi
    Tüm kimlik bileşenlerini koordine eder
    """
    
    def __init__(
        self,
        data_dir: str = "data",
        similarity_threshold: float = 0.75,
        auto_register: bool = False
    ):
        """
        Args:
            data_dir: Veri dizini
            similarity_threshold: Otomatik tanımlama için benzerlik eşiği
            auto_register: Tanınmayan hayvanları otomatik kaydet
        """
        self.data_dir = Path(data_dir)
        self.similarity_threshold = similarity_threshold
        self.auto_register = auto_register
        
        # Bileşenleri başlat
        self._id_manager = AnimalIDManager(str(self.data_dir / "animals"))
        self._embedding_store = EmbeddingStore(str(self.data_dir / "embeddings"))
        
        # Feature extractor
        config = FeatureExtractorConfig()
        self._feature_extractor = DeepFeatureExtractor(config)
        self._feature_extractor.load_model()
        
        # Görüntü depolama
        self._images_dir = self.data_dir / "images"
        self._images_dir.mkdir(parents=True, exist_ok=True)
        
        # İstatistikler
        self._stats = {
            "total_identifications": 0,
            "successful_identifications": 0,
            "new_registrations": 0,
            "failed_identifications": 0
        }
    
    def register_animal(
        self,
        image: np.ndarray,
        animal_type: AnimalType,
        name: Optional[str] = None,
        tag_number: Optional[str] = None,
        metadata: dict = None
    ) -> RegistrationResult:
        """
        Yeni hayvan kaydet
        
        Args:
            image: Hayvan görüntüsü (BGR)
            animal_type: Hayvan türü
            name: Hayvan adı
            tag_number: Kulak küpesi numarası
            metadata: Ek bilgiler
            
        Returns:
            Kayıt sonucu
        """
        try:
            # Feature çıkar
            embedding = self._feature_extractor.extract(image)
            
            # Mevcut hayvanlarla karşılaştır
            matches = self._embedding_store.search(embedding, top_k=1, threshold=self.similarity_threshold)
            
            if matches:
                # Zaten kayıtlı olabilir
                entry_id, similarity = matches[0]
                entry = self._embedding_store.get(entry_id)
                
                if entry and entry.animal_id:
                    return RegistrationResult(
                        success=False,
                        animal_id=entry.animal_id,
                        is_new=False,
                        confidence=similarity,
                        message=f"Bu hayvan zaten kayıtlı: {entry.animal_id} (benzerlik: {similarity:.2f})"
                    )
            
            # Yeni hayvan oluştur
            profile = self._id_manager.create_animal(
                animal_type=animal_type,
                name=name,
                tag_number=tag_number,
                **(metadata or {})
            )
            
            # Embedding kaydet
            embedding_id = self._embedding_store.add(
                embedding=embedding,
                animal_id=profile.id,
                source="registration",
                quality_score=self._compute_image_quality(image)
            )
            
            # Görüntüyü kaydet
            image_path = self._save_image(image, profile.id, "primary")
            self._id_manager.update_animal(profile.id, primary_image_path=str(image_path))
            
            self._stats["new_registrations"] += 1
            
            return RegistrationResult(
                success=True,
                animal_id=profile.id,
                is_new=True,
                confidence=1.0,
                message="Hayvan başarıyla kaydedildi"
            )
            
        except Exception as e:
            logger.error(f"Kayıt hatası: {e}")
            return RegistrationResult(
                success=False,
                message=f"Kayıt hatası: {str(e)}"
            )
    
    def identify(
        self,
        image: np.ndarray,
        top_k: int = 3
    ) -> IdentificationResult:
        """
        Görüntüden hayvan tanımla
        
        Args:
            image: Hayvan görüntüsü
            top_k: Aday sayısı
            
        Returns:
            Tanımlama sonucu
        """
        self._stats["total_identifications"] += 1
        
        try:
            # Feature çıkar
            embedding = self._feature_extractor.extract(image)
            
            # Benzer embedding'leri ara
            matches = self._embedding_store.search(
                embedding,
                top_k=top_k * 2,  # Her hayvan için birden fazla embedding olabilir
                threshold=0.0
            )
            
            if not matches:
                self._stats["failed_identifications"] += 1
                return IdentificationResult(
                    identified=False,
                    message="Eşleşme bulunamadı"
                )
            
            # Hayvan bazında grupla
            animal_scores: Dict[str, List[float]] = {}
            
            for entry_id, similarity in matches:
                entry = self._embedding_store.get(entry_id)
                if entry and entry.animal_id:
                    if entry.animal_id not in animal_scores:
                        animal_scores[entry.animal_id] = []
                    animal_scores[entry.animal_id].append(similarity)
            
            if not animal_scores:
                self._stats["failed_identifications"] += 1
                return IdentificationResult(
                    identified=False,
                    message="Kayıtlı hayvan bulunamadı"
                )
            
            # En iyi eşleşmeleri hesapla
            candidates = []
            for animal_id, scores in animal_scores.items():
                avg_score = np.mean(scores)
                candidates.append((animal_id, float(avg_score)))
            
            candidates.sort(key=lambda x: x[1], reverse=True)
            candidates = candidates[:top_k]
            
            # En iyi eşleşme
            best_id, best_score = candidates[0]
            
            if best_score >= self.similarity_threshold:
                profile = self._id_manager.get_animal(best_id)
                
                # Tespit kaydı
                self._id_manager.record_detection(best_id)
                
                # Yeni embedding ekle (kalite yeterliyse)
                quality = self._compute_image_quality(image)
                if quality > 0.5:
                    self._embedding_store.add(
                        embedding=embedding,
                        animal_id=best_id,
                        source="detection",
                        quality_score=quality
                    )
                
                self._stats["successful_identifications"] += 1
                
                return IdentificationResult(
                    identified=True,
                    animal_id=best_id,
                    animal_profile=profile,
                    confidence=best_score,
                    candidates=candidates
                )
            
            # Eşik altında - otomatik kayıt?
            if self.auto_register:
                # Otomatik kayıt mantığı...
                pass
            
            self._stats["failed_identifications"] += 1
            
            return IdentificationResult(
                identified=False,
                confidence=best_score,
                candidates=candidates,
                message=f"Güvenilir eşleşme bulunamadı (en iyi: {best_score:.2f})"
            )
            
        except Exception as e:
            logger.error(f"Tanımlama hatası: {e}")
            self._stats["failed_identifications"] += 1
            return IdentificationResult(
                identified=False,
                message=f"Tanımlama hatası: {str(e)}"
            )
    
    def add_reference_image(
        self,
        animal_id: str,
        image: np.ndarray,
        set_as_primary: bool = False
    ) -> bool:
        """
        Hayvana referans görüntü ekle
        
        Args:
            animal_id: Hayvan ID'si
            image: Görüntü
            set_as_primary: Birincil görüntü olarak ayarla
            
        Returns:
            Başarılı ise True
        """
        profile = self._id_manager.get_animal(animal_id)
        if not profile:
            return False
        
        try:
            # Feature çıkar ve kaydet
            embedding = self._feature_extractor.extract(image)
            quality = self._compute_image_quality(image)
            
            self._embedding_store.add(
                embedding=embedding,
                animal_id=animal_id,
                source="manual",
                quality_score=quality
            )
            
            # Görüntüyü kaydet
            image_path = self._save_image(image, animal_id)
            
            if set_as_primary:
                self._id_manager.update_animal(animal_id, primary_image_path=str(image_path))
            
            return True
            
        except Exception as e:
            logger.error(f"Referans görüntü ekleme hatası: {e}")
            return False
    
    def get_animal(self, animal_id: str) -> Optional[AnimalProfile]:
        """Hayvan profilini al"""
        return self._id_manager.get_animal(animal_id)
    
    def list_animals(
        self,
        animal_type: Optional[AnimalType] = None,
        limit: int = 100
    ) -> List[AnimalProfile]:
        """Hayvanları listele"""
        return self._id_manager.list_animals(animal_type=animal_type, limit=limit)
    
    def search_animals(self, query: str) -> List[AnimalProfile]:
        """Hayvan ara"""
        return self._id_manager.search_animals(query)
    
    def update_animal(self, animal_id: str, **updates) -> Optional[AnimalProfile]:
        """Hayvan profilini güncelle"""
        return self._id_manager.update_animal(animal_id, **updates)
    
    def delete_animal(self, animal_id: str) -> bool:
        """Hayvanı sil"""
        # Embedding'leri sil
        entries = self._embedding_store.get_by_animal(animal_id)
        for entry in entries:
            self._embedding_store.delete(entry.id)
        
        # Profili sil
        return self._id_manager.delete_animal(animal_id)
    
    def find_similar_animals(
        self,
        animal_id: str,
        top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Benzer hayvanları bul"""
        embedding = self._embedding_store.get_animal_embedding(animal_id)
        if embedding is None:
            return []
        
        matches = self._embedding_store.search(embedding, top_k=top_k * 2)
        
        # Kendisini hariç tut ve hayvan bazında grupla
        animal_scores: Dict[str, float] = {}
        
        for entry_id, score in matches:
            entry = self._embedding_store.get(entry_id)
            if entry and entry.animal_id and entry.animal_id != animal_id:
                if entry.animal_id not in animal_scores:
                    animal_scores[entry.animal_id] = score
                else:
                    animal_scores[entry.animal_id] = max(animal_scores[entry.animal_id], score)
        
        results = sorted(animal_scores.items(), key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def _compute_image_quality(self, image: np.ndarray) -> float:
        """Görüntü kalitesi hesapla"""
        # Keskinlik (Laplacian variance)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # Normalize (0-1)
        sharpness_score = min(sharpness / 500.0, 1.0)
        
        # Boyut skoru
        h, w = image.shape[:2]
        size_score = min((h * w) / (224 * 224), 1.0)
        
        # Birleşik skor
        return 0.7 * sharpness_score + 0.3 * size_score
    
    def _save_image(
        self,
        image: np.ndarray,
        animal_id: str,
        suffix: str = None
    ) -> Path:
        """Görüntüyü kaydet"""
        animal_dir = self._images_dir / animal_id
        animal_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{suffix}.jpg" if suffix else f"{timestamp}.jpg"
        
        image_path = animal_dir / filename
        cv2.imwrite(str(image_path), image)
        
        return image_path
    
    def get_statistics(self) -> dict:
        """İstatistikleri al"""
        return {
            "registry_stats": self._stats.copy(),
            "animal_stats": self._id_manager.get_statistics(),
            "embedding_stats": self._embedding_store.get_statistics()
        }
    
    def export_gallery(self, output_dir: str) -> bool:
        """Hayvan galerisini export et"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            for profile in self._id_manager.list_animals():
                # Profil bilgisi
                profile_data = profile.to_dict()
                
                animal_dir = output_path / profile.id
                animal_dir.mkdir(parents=True, exist_ok=True)
                
                with open(animal_dir / "profile.json", 'w') as f:
                    json.dump(profile_data, f, indent=2, ensure_ascii=False)
                
                # Primary image
                if profile.primary_image_path:
                    src_path = Path(profile.primary_image_path)
                    if src_path.exists():
                        import shutil
                        shutil.copy(src_path, animal_dir / "primary.jpg")
            
            logger.info(f"Galeri export edildi: {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Galeri export hatası: {e}")
            return False
