"""
Animal ID Manager
Hayvan kimlik yönetimi sistemi
"""

import logging
import uuid
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AnimalType(Enum):
    """Hayvan türleri"""
    COW = "cow"
    SHEEP = "sheep"
    GOAT = "goat"
    HORSE = "horse"
    PIG = "pig"
    CHICKEN = "chicken"
    DOG = "dog"
    CAT = "cat"
    OTHER = "other"


class AnimalGender(Enum):
    """Hayvan cinsiyeti"""
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


@dataclass
class AnimalProfile:
    """Hayvan profil bilgisi"""
    id: str
    animal_type: AnimalType
    name: Optional[str] = None
    gender: AnimalGender = AnimalGender.UNKNOWN
    birth_date: Optional[datetime] = None
    tag_number: Optional[str] = None  # Kulak küpesi vb.
    color: Optional[str] = None
    weight: Optional[float] = None
    
    # Görsel tanımlama
    visual_id: Optional[int] = None  # Re-ID sistem ID'si
    primary_image_path: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)
    
    # İstatistikler
    total_detections: int = 0
    last_seen: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Dictionary'e çevir"""
        return {
            "id": self.id,
            "animal_type": self.animal_type.value,
            "name": self.name,
            "gender": self.gender.value,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "tag_number": self.tag_number,
            "color": self.color,
            "weight": self.weight,
            "visual_id": self.visual_id,
            "primary_image_path": self.primary_image_path,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "total_detections": self.total_detections,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AnimalProfile':
        """Dictionary'den oluştur"""
        return cls(
            id=data["id"],
            animal_type=AnimalType(data["animal_type"]),
            name=data.get("name"),
            gender=AnimalGender(data.get("gender", "unknown")),
            birth_date=datetime.fromisoformat(data["birth_date"]) if data.get("birth_date") else None,
            tag_number=data.get("tag_number"),
            color=data.get("color"),
            weight=data.get("weight"),
            visual_id=data.get("visual_id"),
            primary_image_path=data.get("primary_image_path"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            metadata=data.get("metadata", {}),
            total_detections=data.get("total_detections", 0),
            last_seen=datetime.fromisoformat(data["last_seen"]) if data.get("last_seen") else None
        )


class AnimalIDManager:
    """
    Hayvan kimlik yönetim sınıfı
    """
    
    def __init__(self, data_dir: str = "data/animals"):
        """
        Args:
            data_dir: Veri dizini
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._animals: Dict[str, AnimalProfile] = {}
        self._visual_id_map: Dict[int, str] = {}  # visual_id -> animal_id
        self._tag_map: Dict[str, str] = {}        # tag_number -> animal_id
        
        # Veritabanını yükle
        self._load_database()
    
    def _load_database(self) -> None:
        """Veritabanını dosyadan yükle"""
        db_path = self.data_dir / "animals.json"
        
        if db_path.exists():
            try:
                with open(db_path, 'r') as f:
                    data = json.load(f)
                
                for animal_data in data.get("animals", []):
                    profile = AnimalProfile.from_dict(animal_data)
                    self._animals[profile.id] = profile
                    
                    if profile.visual_id:
                        self._visual_id_map[profile.visual_id] = profile.id
                    
                    if profile.tag_number:
                        self._tag_map[profile.tag_number] = profile.id
                
                logger.info(f"{len(self._animals)} hayvan profili yüklendi")
                
            except Exception as e:
                logger.error(f"Veritabanı yükleme hatası: {e}")
    
    def _save_database(self) -> None:
        """Veritabanını dosyaya kaydet"""
        db_path = self.data_dir / "animals.json"
        
        try:
            data = {
                "animals": [p.to_dict() for p in self._animals.values()],
                "updated_at": datetime.now().isoformat()
            }
            
            with open(db_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Veritabanı kaydedildi")
            
        except Exception as e:
            logger.error(f"Veritabanı kaydetme hatası: {e}")
    
    def create_animal(
        self,
        animal_type: AnimalType,
        name: Optional[str] = None,
        tag_number: Optional[str] = None,
        **kwargs
    ) -> AnimalProfile:
        """
        Yeni hayvan profili oluştur
        
        Args:
            animal_type: Hayvan türü
            name: Hayvan adı
            tag_number: Kulak küpesi numarası
            **kwargs: Ek profil bilgileri
            
        Returns:
            Oluşturulan profil
        """
        # Benzersiz ID oluştur
        animal_id = str(uuid.uuid4())[:8]
        
        # Tag kontrolü
        if tag_number and tag_number in self._tag_map:
            raise ValueError(f"Bu tag numarası zaten kullanımda: {tag_number}")
        
        profile = AnimalProfile(
            id=animal_id,
            animal_type=animal_type,
            name=name,
            tag_number=tag_number,
            **kwargs
        )
        
        self._animals[animal_id] = profile
        
        if tag_number:
            self._tag_map[tag_number] = animal_id
        
        self._save_database()
        logger.info(f"Yeni hayvan oluşturuldu: {animal_id} ({animal_type.value})")
        
        return profile
    
    def get_animal(self, animal_id: str) -> Optional[AnimalProfile]:
        """ID ile hayvan profili al"""
        return self._animals.get(animal_id)
    
    def get_by_visual_id(self, visual_id: int) -> Optional[AnimalProfile]:
        """Görsel ID ile hayvan profili al"""
        animal_id = self._visual_id_map.get(visual_id)
        if animal_id:
            return self._animals.get(animal_id)
        return None
    
    def get_by_tag(self, tag_number: str) -> Optional[AnimalProfile]:
        """Kulak küpesi ile hayvan profili al"""
        animal_id = self._tag_map.get(tag_number)
        if animal_id:
            return self._animals.get(animal_id)
        return None
    
    def update_animal(
        self,
        animal_id: str,
        **updates
    ) -> Optional[AnimalProfile]:
        """
        Hayvan profilini güncelle
        
        Args:
            animal_id: Hayvan ID'si
            **updates: Güncellenecek alanlar
            
        Returns:
            Güncellenmiş profil veya None
        """
        profile = self._animals.get(animal_id)
        if not profile:
            return None
        
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        
        # Index güncelle
        if "visual_id" in updates:
            # Eski mapping'i kaldır
            old_vid = None
            for vid, aid in self._visual_id_map.items():
                if aid == animal_id:
                    old_vid = vid
                    break
            if old_vid:
                del self._visual_id_map[old_vid]
            
            # Yeni mapping ekle
            if updates["visual_id"]:
                self._visual_id_map[updates["visual_id"]] = animal_id
        
        if "tag_number" in updates:
            # Eski tag'i kaldır
            old_tag = None
            for tag, aid in self._tag_map.items():
                if aid == animal_id:
                    old_tag = tag
                    break
            if old_tag:
                del self._tag_map[old_tag]
            
            # Yeni tag ekle
            if updates["tag_number"]:
                self._tag_map[updates["tag_number"]] = animal_id
        
        self._save_database()
        return profile
    
    def delete_animal(self, animal_id: str) -> bool:
        """Hayvan profilini sil"""
        profile = self._animals.get(animal_id)
        if not profile:
            return False
        
        # Index'lerden kaldır
        if profile.visual_id and profile.visual_id in self._visual_id_map:
            del self._visual_id_map[profile.visual_id]
        
        if profile.tag_number and profile.tag_number in self._tag_map:
            del self._tag_map[profile.tag_number]
        
        del self._animals[animal_id]
        self._save_database()
        
        logger.info(f"Hayvan silindi: {animal_id}")
        return True
    
    def link_visual_id(self, animal_id: str, visual_id: int) -> bool:
        """
        Görsel ID'yi hayvan profiliyle ilişkilendir
        
        Args:
            animal_id: Hayvan profil ID'si
            visual_id: Re-ID sistem tarafından atanan ID
            
        Returns:
            Başarılı ise True
        """
        profile = self._animals.get(animal_id)
        if not profile:
            return False
        
        # Önceki ilişkiyi kontrol et
        if visual_id in self._visual_id_map:
            existing_id = self._visual_id_map[visual_id]
            if existing_id != animal_id:
                logger.warning(f"Visual ID zaten başka bir hayvana bağlı: {existing_id}")
                return False
        
        profile.visual_id = visual_id
        self._visual_id_map[visual_id] = animal_id
        profile.updated_at = datetime.now()
        
        self._save_database()
        return True
    
    def record_detection(
        self,
        animal_id: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Tespit kaydı ekle"""
        profile = self._animals.get(animal_id)
        if profile:
            profile.total_detections += 1
            profile.last_seen = timestamp or datetime.now()
    
    def list_animals(
        self,
        animal_type: Optional[AnimalType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AnimalProfile]:
        """
        Hayvanları listele
        
        Args:
            animal_type: Filtre için hayvan türü
            limit: Maksimum sonuç sayısı
            offset: Başlangıç indeksi
            
        Returns:
            Hayvan profilleri listesi
        """
        animals = list(self._animals.values())
        
        if animal_type:
            animals = [a for a in animals if a.animal_type == animal_type]
        
        # Sırala (son görülme zamanına göre)
        animals.sort(key=lambda x: x.last_seen or datetime.min, reverse=True)
        
        return animals[offset:offset + limit]
    
    def search_animals(
        self,
        query: str,
        fields: List[str] = None
    ) -> List[AnimalProfile]:
        """
        Hayvan ara
        
        Args:
            query: Arama sorgusu
            fields: Aranacak alanlar (varsayılan: name, tag_number)
            
        Returns:
            Eşleşen profiller
        """
        if fields is None:
            fields = ["name", "tag_number"]
        
        query = query.lower()
        results = []
        
        for profile in self._animals.values():
            for field in fields:
                value = getattr(profile, field, None)
                if value and query in str(value).lower():
                    results.append(profile)
                    break
        
        return results
    
    def get_statistics(self) -> dict:
        """İstatistikleri al"""
        type_counts = {}
        for profile in self._animals.values():
            t = profile.animal_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total_animals": len(self._animals),
            "by_type": type_counts,
            "with_visual_id": len(self._visual_id_map),
            "with_tag": len(self._tag_map)
        }
    
    def export_to_csv(self, path: str) -> bool:
        """CSV'ye export et"""
        try:
            import csv
            
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'id', 'animal_type', 'name', 'tag_number', 'gender',
                    'color', 'weight', 'total_detections', 'last_seen'
                ])
                writer.writeheader()
                
                for profile in self._animals.values():
                    writer.writerow({
                        'id': profile.id,
                        'animal_type': profile.animal_type.value,
                        'name': profile.name,
                        'tag_number': profile.tag_number,
                        'gender': profile.gender.value,
                        'color': profile.color,
                        'weight': profile.weight,
                        'total_detections': profile.total_detections,
                        'last_seen': profile.last_seen.isoformat() if profile.last_seen else ''
                    })
            
            logger.info(f"CSV export tamamlandı: {path}")
            return True
            
        except Exception as e:
            logger.error(f"CSV export hatası: {e}")
            return False
