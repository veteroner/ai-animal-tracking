"""
Tespit Repository - Veritabanı işlemleri
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func


class DetectionRepository:
    """Tespit veritabanı işlemleri"""
    
    def __init__(self, session: Session):
        self.session = session
        
    def create(self, detection_data: Dict[str, Any]) -> Dict[str, Any]:
        """Yeni tespit kaydı oluştur"""
        from ..models import Detection
        
        detection = Detection(
            animal_id=detection_data.get('animal_id'),
            camera_id=detection_data.get('camera_id'),
            timestamp=detection_data.get('timestamp', datetime.utcnow()),
            confidence=detection_data.get('confidence', 0.0),
            bbox_x=detection_data.get('bbox_x'),
            bbox_y=detection_data.get('bbox_y'),
            bbox_width=detection_data.get('bbox_width'),
            bbox_height=detection_data.get('bbox_height'),
            class_name=detection_data.get('class_name'),
            track_id=detection_data.get('track_id'),
            frame_number=detection_data.get('frame_number'),
            metadata=detection_data.get('metadata', {})
        )
        
        self.session.add(detection)
        self.session.commit()
        self.session.refresh(detection)
        
        return self._to_dict(detection)
        
    def create_batch(self, detections: List[Dict[str, Any]]) -> int:
        """Toplu tespit kaydı oluştur"""
        from ..models import Detection
        
        detection_objects = []
        for det_data in detections:
            detection = Detection(
                animal_id=det_data.get('animal_id'),
                camera_id=det_data.get('camera_id'),
                timestamp=det_data.get('timestamp', datetime.utcnow()),
                confidence=det_data.get('confidence', 0.0),
                bbox_x=det_data.get('bbox_x'),
                bbox_y=det_data.get('bbox_y'),
                bbox_width=det_data.get('bbox_width'),
                bbox_height=det_data.get('bbox_height'),
                class_name=det_data.get('class_name'),
                track_id=det_data.get('track_id'),
                frame_number=det_data.get('frame_number'),
                metadata=det_data.get('metadata', {})
            )
            detection_objects.append(detection)
            
        self.session.bulk_save_objects(detection_objects)
        self.session.commit()
        
        return len(detection_objects)
        
    def get_by_id(self, detection_id: int) -> Optional[Dict[str, Any]]:
        """ID ile tespit getir"""
        from ..models import Detection
        
        detection = self.session.query(Detection).filter(
            Detection.id == detection_id
        ).first()
        return self._to_dict(detection) if detection else None
        
    def get_by_animal(self, animal_id: int, 
                      start_time: datetime = None,
                      end_time: datetime = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Hayvana göre tespitleri getir"""
        from ..models import Detection
        
        query = self.session.query(Detection).filter(
            Detection.animal_id == animal_id
        )
        
        if start_time:
            query = query.filter(Detection.timestamp >= start_time)
        if end_time:
            query = query.filter(Detection.timestamp <= end_time)
            
        detections = query.order_by(
            Detection.timestamp.desc()
        ).limit(limit).all()
        
        return [self._to_dict(d) for d in detections]
        
    def get_by_camera(self, camera_id: str,
                      start_time: datetime = None,
                      end_time: datetime = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Kameraya göre tespitleri getir"""
        from ..models import Detection
        
        query = self.session.query(Detection).filter(
            Detection.camera_id == camera_id
        )
        
        if start_time:
            query = query.filter(Detection.timestamp >= start_time)
        if end_time:
            query = query.filter(Detection.timestamp <= end_time)
            
        detections = query.order_by(
            Detection.timestamp.desc()
        ).limit(limit).all()
        
        return [self._to_dict(d) for d in detections]
        
    def get_recent(self, hours: int = 24, limit: int = 1000) -> List[Dict[str, Any]]:
        """Son X saatteki tespitleri getir"""
        from ..models import Detection
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        detections = self.session.query(Detection).filter(
            Detection.timestamp >= cutoff_time
        ).order_by(
            Detection.timestamp.desc()
        ).limit(limit).all()
        
        return [self._to_dict(d) for d in detections]
        
    def get_hourly_counts(self, date: datetime = None) -> Dict[int, int]:
        """Saatlik tespit sayılarını getir"""
        from ..models import Detection
        
        if date is None:
            date = datetime.utcnow().date()
            
        start_time = datetime.combine(date, datetime.min.time())
        end_time = start_time + timedelta(days=1)
        
        results = self.session.query(
            func.extract('hour', Detection.timestamp).label('hour'),
            func.count(Detection.id).label('count')
        ).filter(
            and_(
                Detection.timestamp >= start_time,
                Detection.timestamp < end_time
            )
        ).group_by(
            func.extract('hour', Detection.timestamp)
        ).all()
        
        return {int(r.hour): r.count for r in results}
        
    def get_daily_counts(self, days: int = 7) -> Dict[str, int]:
        """Günlük tespit sayılarını getir"""
        from ..models import Detection
        
        start_time = datetime.utcnow() - timedelta(days=days)
        
        results = self.session.query(
            func.date(Detection.timestamp).label('date'),
            func.count(Detection.id).label('count')
        ).filter(
            Detection.timestamp >= start_time
        ).group_by(
            func.date(Detection.timestamp)
        ).all()
        
        return {str(r.date): r.count for r in results}
        
    def get_animal_detection_counts(self) -> Dict[int, int]:
        """Hayvan bazlı tespit sayıları"""
        from ..models import Detection
        
        results = self.session.query(
            Detection.animal_id,
            func.count(Detection.id).label('count')
        ).filter(
            Detection.animal_id.isnot(None)
        ).group_by(
            Detection.animal_id
        ).all()
        
        return {r.animal_id: r.count for r in results}
        
    def delete_old(self, days: int = 30) -> int:
        """Eski tespitleri sil"""
        from ..models import Detection
        
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        deleted = self.session.query(Detection).filter(
            Detection.timestamp < cutoff_time
        ).delete()
        
        self.session.commit()
        
        return deleted
        
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """İstatistikleri getir"""
        from ..models import Detection
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        total = self.session.query(func.count(Detection.id)).filter(
            Detection.timestamp >= cutoff_time
        ).scalar()
        
        avg_confidence = self.session.query(func.avg(Detection.confidence)).filter(
            Detection.timestamp >= cutoff_time
        ).scalar() or 0
        
        unique_animals = self.session.query(
            func.count(func.distinct(Detection.animal_id))
        ).filter(
            Detection.timestamp >= cutoff_time
        ).scalar()
        
        by_class = self.session.query(
            Detection.class_name,
            func.count(Detection.id)
        ).filter(
            Detection.timestamp >= cutoff_time
        ).group_by(Detection.class_name).all()
        
        return {
            'total_detections': total,
            'average_confidence': float(avg_confidence),
            'unique_animals': unique_animals,
            'by_class': {c: cnt for c, cnt in by_class if c}
        }
        
    def _to_dict(self, detection) -> Dict[str, Any]:
        """Model'i dictionary'e çevir"""
        if not detection:
            return {}
            
        return {
            'id': detection.id,
            'animal_id': detection.animal_id,
            'camera_id': detection.camera_id,
            'timestamp': detection.timestamp.isoformat() if detection.timestamp else None,
            'confidence': detection.confidence,
            'bbox': {
                'x': detection.bbox_x,
                'y': detection.bbox_y,
                'width': detection.bbox_width,
                'height': detection.bbox_height
            },
            'class_name': detection.class_name,
            'track_id': detection.track_id,
            'frame_number': detection.frame_number,
            'metadata': detection.metadata
        }
