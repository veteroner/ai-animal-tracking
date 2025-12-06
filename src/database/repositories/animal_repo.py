"""
Hayvan Repository - Veritabanı işlemleri
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_


class AnimalRepository:
    """Hayvan veritabanı işlemleri"""
    
    def __init__(self, session: Session):
        self.session = session
        
    def create(self, animal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni hayvan kaydı oluştur"""
        from ..models import Animal
        
        # Model'deki gerçek alan isimlerini kullan
        animal = Animal(
            id=animal_data.get('id'),
            class_name=animal_data.get('class_name', animal_data.get('species', 'unknown')),
            name=animal_data.get('name'),
            tag=animal_data.get('tag'),
            color=animal_data.get('color'),
            markings=animal_data.get('markings'),
            health_status=animal_data.get('health_status', 'unknown'),
            bcs_score=animal_data.get('bcs_score'),
            notes=animal_data.get('notes'),
            extra_data=animal_data.get('metadata', animal_data.get('extra_data', {}))
        )
        
        self.session.add(animal)
        self.session.commit()
        self.session.refresh(animal)
        
        return self._to_dict(animal)
        
    def get_by_id(self, animal_id: str) -> Optional[Dict[str, Any]]:
        """ID ile hayvan getir"""
        from ..models import Animal
        
        animal = self.session.query(Animal).filter(Animal.id == animal_id).first()
        return self._to_dict(animal) if animal else None
        
    def get_by_class(self, class_name: str) -> List[Dict[str, Any]]:
        """Sınıfa göre hayvanları getir"""
        from ..models import Animal
        
        animals = self.session.query(Animal).filter(
            Animal.class_name == class_name
        ).all()
        return [self._to_dict(a) for a in animals]
        
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Tüm hayvanları getir"""
        from ..models import Animal
        
        animals = self.session.query(Animal).offset(skip).limit(limit).all()
        return [self._to_dict(a) for a in animals]
        
    def get_by_species(self, species: str) -> List[Dict[str, Any]]:
        """Türe göre hayvanları getir (class_name ile eşleştirilir)"""
        from ..models import Animal
        
        animals = self.session.query(Animal).filter(
            Animal.class_name == species
        ).all()
        return [self._to_dict(a) for a in animals]
        
    def get_recent(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Son X saatte görülen hayvanları getir"""
        from ..models import Animal
        from datetime import datetime, timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        animals = self.session.query(Animal).filter(
            Animal.last_seen_at >= cutoff
        ).all()
        return [self._to_dict(a) for a in animals]
        
    def update(self, animal_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Hayvan güncelle"""
        from ..models import Animal
        
        animal = self.session.query(Animal).filter(Animal.id == animal_id).first()
        if not animal:
            return None
            
        for key, value in update_data.items():
            if hasattr(animal, key):
                setattr(animal, key, value)
                
        animal.updated_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(animal)
        
        return self._to_dict(animal)
        
    def update_health_status(self, animal_id: str, health_status: str) -> bool:
        """Sağlık durumunu güncelle"""
        from ..models import Animal
        
        animal = self.session.query(Animal).filter(Animal.id == animal_id).first()
        if not animal:
            return False
            
        animal.health_status = health_status
        animal.updated_at = datetime.utcnow()
        self.session.commit()
        
        return True
        
    def update_last_seen(self, animal_id: str) -> bool:
        """Son görülme zamanını güncelle"""
        from ..models import Animal
        
        animal = self.session.query(Animal).filter(Animal.id == animal_id).first()
        if not animal:
            return False
            
        animal.last_seen_at = datetime.utcnow()
        animal.total_detections = (animal.total_detections or 0) + 1
        self.session.commit()
        
        return True
        
    def delete(self, animal_id: str) -> bool:
        """Hayvan sil"""
        from ..models import Animal
        
        animal = self.session.query(Animal).filter(Animal.id == animal_id).first()
        if not animal:
            return False
            
        self.session.delete(animal)
        self.session.commit()
        
        return True
        
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Hayvan ara"""
        from ..models import Animal
        
        search_pattern = f"%{query}%"
        animals = self.session.query(Animal).filter(
            or_(
                Animal.name.ilike(search_pattern),
                Animal.id.ilike(search_pattern),
                Animal.class_name.ilike(search_pattern),
                Animal.tag.ilike(search_pattern)
            )
        ).all()
        
        return [self._to_dict(a) for a in animals]
        
    def get_statistics(self) -> Dict[str, Any]:
        """İstatistikleri getir"""
        from ..models import Animal
        from sqlalchemy import func
        
        total = self.session.query(func.count(Animal.id)).scalar() or 0
        
        class_counts = self.session.query(
            Animal.class_name,
            func.count(Animal.id)
        ).group_by(Animal.class_name).all()
        
        return {
            'total_animals': total,
            'by_class': {c: cnt for c, cnt in class_counts if c}
        }
        
    def _to_dict(self, animal) -> Dict[str, Any]:
        """Model'i dictionary'e çevir"""
        if not animal:
            return {}
            
        return {
            'id': animal.id,
            'name': getattr(animal, 'name', None),
            'class_name': getattr(animal, 'class_name', None),
            'tag': getattr(animal, 'tag', None),
            'color': getattr(animal, 'color', None),
            'health_status': getattr(animal, 'health_status', None),
            'bcs_score': getattr(animal, 'bcs_score', None),
            'first_seen_at': animal.first_seen_at.isoformat() if getattr(animal, 'first_seen_at', None) else None,
            'last_seen_at': animal.last_seen_at.isoformat() if getattr(animal, 'last_seen_at', None) else None,
            'total_detections': getattr(animal, 'total_detections', 0),
            'created_at': animal.created_at.isoformat() if getattr(animal, 'created_at', None) else None,
            'updated_at': animal.updated_at.isoformat() if getattr(animal, 'updated_at', None) else None,
            'notes': getattr(animal, 'notes', None)
        }
