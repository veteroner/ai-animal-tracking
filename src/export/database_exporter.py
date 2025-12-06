"""
Database Exporter - Veritabanı dışa aktarma
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json


logger = logging.getLogger(__name__)


class DatabaseExporter:
    """Veritabanı veri aktarıcı"""
    
    def __init__(self, session=None, output_dir: str = "data/exports"):
        self.session = session
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def set_session(self, session):
        """Veritabanı oturumunu ayarla"""
        self.session = session
        
    def export_all_animals(self) -> List[Dict]:
        """Tüm hayvanları dışa aktar"""
        if not self.session:
            logger.warning("Veritabanı oturumu ayarlanmamış")
            return []
            
        try:
            from ..database.models import Animal
            
            animals = self.session.query(Animal).all()
            return [self._animal_to_dict(a) for a in animals]
            
        except Exception as e:
            logger.error(f"Hayvan export hatası: {e}")
            return []
            
    def export_detections(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        camera_id: str = None,
        animal_id: int = None
    ) -> List[Dict]:
        """Tespitleri dışa aktar"""
        if not self.session:
            logger.warning("Veritabanı oturumu ayarlanmamış")
            return []
            
        try:
            from ..database.models import Detection
            
            query = self.session.query(Detection)
            
            if start_time:
                query = query.filter(Detection.timestamp >= start_time)
            if end_time:
                query = query.filter(Detection.timestamp <= end_time)
            if camera_id:
                query = query.filter(Detection.camera_id == camera_id)
            if animal_id:
                query = query.filter(Detection.animal_id == animal_id)
                
            detections = query.all()
            return [self._detection_to_dict(d) for d in detections]
            
        except Exception as e:
            logger.error(f"Tespit export hatası: {e}")
            return []
            
    def export_behaviors(
        self,
        start_time: datetime = None,
        end_time: datetime = None,
        animal_id: int = None,
        behavior_type: str = None
    ) -> List[Dict]:
        """Davranışları dışa aktar"""
        if not self.session:
            return []
            
        try:
            from ..database.models import BehaviorRecord
            
            query = self.session.query(BehaviorRecord)
            
            if start_time:
                query = query.filter(BehaviorRecord.start_time >= start_time)
            if end_time:
                query = query.filter(BehaviorRecord.start_time <= end_time)
            if animal_id:
                query = query.filter(BehaviorRecord.animal_id == animal_id)
            if behavior_type:
                query = query.filter(BehaviorRecord.behavior_type == behavior_type)
                
            behaviors = query.all()
            return [self._behavior_to_dict(b) for b in behaviors]
            
        except Exception as e:
            logger.error(f"Davranış export hatası: {e}")
            return []
            
    def export_health_records(
        self,
        animal_id: int = None,
        days: int = 30
    ) -> List[Dict]:
        """Sağlık kayıtlarını dışa aktar"""
        if not self.session:
            return []
            
        try:
            from ..database.models import HealthRecord
            
            query = self.session.query(HealthRecord)
            
            if animal_id:
                query = query.filter(HealthRecord.animal_id == animal_id)
                
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(HealthRecord.timestamp >= cutoff)
            
            records = query.all()
            return [self._health_to_dict(r) for r in records]
            
        except Exception as e:
            logger.error(f"Sağlık export hatası: {e}")
            return []
            
    def export_full_database(self) -> Dict[str, List[Dict]]:
        """Tüm veritabanını dışa aktar"""
        return {
            'animals': self.export_all_animals(),
            'detections': self.export_detections(),
            'behaviors': self.export_behaviors(),
            'health_records': self.export_health_records()
        }
        
    def save_to_file(
        self,
        data: Dict[str, Any],
        filename: str = None
    ) -> str:
        """Veriyi dosyaya kaydet"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"database_export_{timestamp}.json"
            
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
        logger.info(f"Veritabanı export: {filepath}")
        return str(filepath)
        
    def import_from_file(self, filepath: str) -> bool:
        """Dosyadan veri içe aktar"""
        if not self.session:
            logger.warning("Veritabanı oturumu ayarlanmamış")
            return False
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Hayvanları içe aktar
            if 'animals' in data:
                self._import_animals(data['animals'])
                
            logger.info(f"Veritabanı import başarılı: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Import hatası: {e}")
            return False
            
    def _import_animals(self, animals: List[Dict]):
        """Hayvanları içe aktar"""
        from ..database.models import Animal
        
        for animal_data in animals:
            existing = self.session.query(Animal).filter(
                Animal.external_id == animal_data.get('external_id')
            ).first()
            
            if not existing:
                animal = Animal(
                    external_id=animal_data.get('external_id'),
                    name=animal_data.get('name'),
                    species=animal_data.get('species'),
                    breed=animal_data.get('breed')
                )
                self.session.add(animal)
                
        self.session.commit()
        
    def _animal_to_dict(self, animal) -> Dict:
        """Animal model'ini dict'e çevir"""
        return {
            'id': animal.id,
            'external_id': animal.external_id,
            'name': animal.name,
            'species': animal.species,
            'breed': animal.breed,
            'birth_date': animal.birth_date.isoformat() if animal.birth_date else None,
            'gender': animal.gender,
            'weight': animal.weight,
            'health_score': animal.health_score,
            'is_active': animal.is_active,
            'created_at': animal.created_at.isoformat() if animal.created_at else None
        }
        
    def _detection_to_dict(self, detection) -> Dict:
        """Detection model'ini dict'e çevir"""
        return {
            'id': detection.id,
            'animal_id': detection.animal_id,
            'camera_id': detection.camera_id,
            'timestamp': detection.timestamp.isoformat() if detection.timestamp else None,
            'confidence': detection.confidence,
            'class_name': detection.class_name,
            'bbox_x': detection.bbox_x,
            'bbox_y': detection.bbox_y,
            'bbox_width': detection.bbox_width,
            'bbox_height': detection.bbox_height,
            'track_id': detection.track_id
        }
        
    def _behavior_to_dict(self, behavior) -> Dict:
        """Behavior model'ini dict'e çevir"""
        return {
            'id': behavior.id,
            'animal_id': behavior.animal_id,
            'behavior_type': behavior.behavior_type,
            'confidence': behavior.confidence,
            'start_time': behavior.start_time.isoformat() if behavior.start_time else None,
            'end_time': behavior.end_time.isoformat() if behavior.end_time else None,
            'duration_seconds': behavior.duration_seconds
        }
        
    def _health_to_dict(self, record) -> Dict:
        """Health record model'ini dict'e çevir"""
        return {
            'id': record.id,
            'animal_id': record.animal_id,
            'timestamp': record.timestamp.isoformat() if record.timestamp else None,
            'health_score': record.health_score,
            'body_condition_score': record.body_condition_score,
            'lameness_score': record.lameness_score,
            'notes': record.notes
        }


# Singleton instance
database_exporter = DatabaseExporter()
