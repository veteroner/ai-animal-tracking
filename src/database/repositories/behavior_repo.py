"""
Davranış Repository - Veritabanı işlemleri
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func


class BehaviorRepository:
    """Davranış veritabanı işlemleri"""
    
    def __init__(self, session: Session):
        self.session = session
        
    def create(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni davranış kaydı oluştur"""
        from ..models import BehaviorRecord
        
        behavior = BehaviorRecord(
            animal_id=behavior_data.get('animal_id'),
            behavior_type=behavior_data.get('behavior_type'),
            confidence=behavior_data.get('confidence', 0.0),
            start_time=behavior_data.get('start_time', datetime.utcnow()),
            end_time=behavior_data.get('end_time'),
            duration_seconds=behavior_data.get('duration_seconds'),
            zone_id=behavior_data.get('zone_id'),
            camera_id=behavior_data.get('camera_id'),
            metadata=behavior_data.get('metadata', {})
        )
        
        self.session.add(behavior)
        self.session.commit()
        self.session.refresh(behavior)
        
        return self._to_dict(behavior)
        
    def create_batch(self, behaviors: List[Dict[str, Any]]) -> int:
        """Toplu davranış kaydı oluştur"""
        from ..models import BehaviorRecord
        
        behavior_objects = []
        for beh_data in behaviors:
            behavior = BehaviorRecord(
                animal_id=beh_data.get('animal_id'),
                behavior_type=beh_data.get('behavior_type'),
                confidence=beh_data.get('confidence', 0.0),
                start_time=beh_data.get('start_time', datetime.utcnow()),
                end_time=beh_data.get('end_time'),
                duration_seconds=beh_data.get('duration_seconds'),
                zone_id=beh_data.get('zone_id'),
                camera_id=beh_data.get('camera_id'),
                metadata=beh_data.get('metadata', {})
            )
            behavior_objects.append(behavior)
            
        self.session.bulk_save_objects(behavior_objects)
        self.session.commit()
        
        return len(behavior_objects)
        
    def get_by_id(self, behavior_id: int) -> Optional[Dict[str, Any]]:
        """ID ile davranış getir"""
        from ..models import BehaviorRecord
        
        behavior = self.session.query(BehaviorRecord).filter(
            BehaviorRecord.id == behavior_id
        ).first()
        return self._to_dict(behavior) if behavior else None
        
    def get_by_animal(self, animal_id: int,
                      start_time: datetime = None,
                      end_time: datetime = None,
                      behavior_type: str = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Hayvana göre davranışları getir"""
        from ..models import BehaviorRecord
        
        query = self.session.query(BehaviorRecord).filter(
            BehaviorRecord.animal_id == animal_id
        )
        
        if start_time:
            query = query.filter(BehaviorRecord.start_time >= start_time)
        if end_time:
            query = query.filter(BehaviorRecord.start_time <= end_time)
        if behavior_type:
            query = query.filter(BehaviorRecord.behavior_type == behavior_type)
            
        behaviors = query.order_by(
            BehaviorRecord.start_time.desc()
        ).limit(limit).all()
        
        return [self._to_dict(b) for b in behaviors]
        
    def get_by_type(self, behavior_type: str,
                    start_time: datetime = None,
                    end_time: datetime = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Davranış türüne göre getir"""
        from ..models import BehaviorRecord
        
        query = self.session.query(BehaviorRecord).filter(
            BehaviorRecord.behavior_type == behavior_type
        )
        
        if start_time:
            query = query.filter(BehaviorRecord.start_time >= start_time)
        if end_time:
            query = query.filter(BehaviorRecord.start_time <= end_time)
            
        behaviors = query.order_by(
            BehaviorRecord.start_time.desc()
        ).limit(limit).all()
        
        return [self._to_dict(b) for b in behaviors]
        
    def get_recent(self, hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """Son X saatteki davranışları getir"""
        from ..models import BehaviorRecord
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        behaviors = self.session.query(BehaviorRecord).filter(
            BehaviorRecord.start_time >= cutoff_time
        ).order_by(
            BehaviorRecord.start_time.desc()
        ).limit(limit).all()
        
        return [self._to_dict(b) for b in behaviors]
        
    def get_behavior_distribution(self, 
                                   animal_id: int = None,
                                   hours: int = 24) -> Dict[str, int]:
        """Davranış dağılımını getir"""
        from ..models import BehaviorRecord
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.session.query(
            BehaviorRecord.behavior_type,
            func.count(BehaviorRecord.id).label('count')
        ).filter(
            BehaviorRecord.start_time >= cutoff_time
        )
        
        if animal_id:
            query = query.filter(BehaviorRecord.animal_id == animal_id)
            
        results = query.group_by(BehaviorRecord.behavior_type).all()
        
        return {r.behavior_type: r.count for r in results if r.behavior_type}
        
    def get_behavior_duration_stats(self, 
                                     behavior_type: str,
                                     hours: int = 24) -> Dict[str, float]:
        """Davranış süre istatistikleri"""
        from ..models import BehaviorRecord
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = self.session.query(
            func.avg(BehaviorRecord.duration_seconds).label('avg'),
            func.min(BehaviorRecord.duration_seconds).label('min'),
            func.max(BehaviorRecord.duration_seconds).label('max'),
            func.sum(BehaviorRecord.duration_seconds).label('total')
        ).filter(
            and_(
                BehaviorRecord.behavior_type == behavior_type,
                BehaviorRecord.start_time >= cutoff_time,
                BehaviorRecord.duration_seconds.isnot(None)
            )
        ).first()
        
        return {
            'average_duration': float(result.avg or 0),
            'min_duration': float(result.min or 0),
            'max_duration': float(result.max or 0),
            'total_duration': float(result.total or 0)
        }
        
    def get_hourly_behavior_pattern(self, 
                                     animal_id: int,
                                     days: int = 7) -> Dict[int, Dict[str, int]]:
        """Saatlik davranış paterni"""
        from ..models import BehaviorRecord
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        results = self.session.query(
            func.extract('hour', BehaviorRecord.start_time).label('hour'),
            BehaviorRecord.behavior_type,
            func.count(BehaviorRecord.id).label('count')
        ).filter(
            and_(
                BehaviorRecord.animal_id == animal_id,
                BehaviorRecord.start_time >= cutoff_time
            )
        ).group_by(
            func.extract('hour', BehaviorRecord.start_time),
            BehaviorRecord.behavior_type
        ).all()
        
        pattern = {}
        for r in results:
            hour = int(r.hour)
            if hour not in pattern:
                pattern[hour] = {}
            pattern[hour][r.behavior_type] = r.count
            
        return pattern
        
    def get_anomalous_behaviors(self, threshold_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Anormal davranışları getir"""
        from ..models import BehaviorRecord
        
        behaviors = self.session.query(BehaviorRecord).filter(
            BehaviorRecord.confidence < threshold_confidence
        ).order_by(
            BehaviorRecord.start_time.desc()
        ).limit(100).all()
        
        return [self._to_dict(b) for b in behaviors]
        
    def update_end_time(self, behavior_id: int, end_time: datetime = None) -> bool:
        """Davranış bitiş zamanını güncelle"""
        from ..models import BehaviorRecord
        
        behavior = self.session.query(BehaviorRecord).filter(
            BehaviorRecord.id == behavior_id
        ).first()
        
        if not behavior:
            return False
            
        if end_time is None:
            end_time = datetime.utcnow()
            
        behavior.end_time = end_time
        if behavior.start_time:
            behavior.duration_seconds = (end_time - behavior.start_time).total_seconds()
            
        self.session.commit()
        
        return True
        
    def delete_old(self, days: int = 30) -> int:
        """Eski kayıtları sil"""
        from ..models import BehaviorRecord
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        deleted = self.session.query(BehaviorRecord).filter(
            BehaviorRecord.start_time < cutoff_time
        ).delete()
        
        self.session.commit()
        
        return deleted
        
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """İstatistikleri getir"""
        from ..models import BehaviorRecord
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        total = self.session.query(func.count(BehaviorRecord.id)).filter(
            BehaviorRecord.start_time >= cutoff_time
        ).scalar()
        
        avg_confidence = self.session.query(func.avg(BehaviorRecord.confidence)).filter(
            BehaviorRecord.start_time >= cutoff_time
        ).scalar() or 0
        
        unique_animals = self.session.query(
            func.count(func.distinct(BehaviorRecord.animal_id))
        ).filter(
            BehaviorRecord.start_time >= cutoff_time
        ).scalar()
        
        distribution = self.get_behavior_distribution(hours=hours)
        
        return {
            'total_behaviors': total,
            'average_confidence': float(avg_confidence),
            'unique_animals': unique_animals,
            'distribution': distribution
        }
        
    def _to_dict(self, behavior) -> Dict[str, Any]:
        """Model'i dictionary'e çevir"""
        if not behavior:
            return {}
            
        return {
            'id': behavior.id,
            'animal_id': behavior.animal_id,
            'behavior_type': behavior.behavior_type,
            'confidence': behavior.confidence,
            'start_time': behavior.start_time.isoformat() if behavior.start_time else None,
            'end_time': behavior.end_time.isoformat() if behavior.end_time else None,
            'duration_seconds': behavior.duration_seconds,
            'zone_id': behavior.zone_id,
            'camera_id': behavior.camera_id,
            'metadata': behavior.metadata
        }
