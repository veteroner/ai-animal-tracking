# src/api/services/database_service.py
"""
Database Service - Handles all database operations.

Provides a clean interface for CRUD operations on animals,
detections, behaviors, health records and alerts.

Uses SQLAlchemy models from src.database.models.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Singleton database service.
    
    Usage:
        db = DatabaseService.get_instance()
        db.initialize("sqlite:///data/tracking.db")
        
        animal = db.create_animal(animal_id="DOG_001", class_name="dog")
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._engine = None
        self._Session = None
        self._is_ready = False
        
        # Auto-initialize with default database
        self.initialize()
        
        logger.info("DatabaseService initialized")
    
    @classmethod
    def get_instance(cls) -> 'DatabaseService':
        """Get singleton instance."""
        return cls()
    
    @property
    def is_ready(self) -> bool:
        """Check if database is ready."""
        return self._is_ready
    
    def initialize(self, database_url: str = "sqlite:///data/tracking.db"):
        """Initialize database connection and create tables."""
        import os
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Create data directory
        os.makedirs("data", exist_ok=True)
        
        # Create engine
        self._engine = create_engine(database_url, echo=False)
        self._Session = sessionmaker(bind=self._engine)
        
        # Import and create tables
        from src.database.models import Base
        Base.metadata.create_all(self._engine)
        
        self._is_ready = True
        logger.info(f"Database initialized: {database_url}")
    
    @contextmanager
    def get_session(self):
        """Get database session context manager."""
        if not self._is_ready:
            raise RuntimeError("Database not initialized")
        
        session = self._Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    # ===========================================
    # Animal Operations
    # ===========================================
    
    def create_animal(
        self,
        animal_id: str,
        class_name: str,
        name: Optional[str] = None,
        tag: Optional[str] = None,
        **kwargs
    ):
        """Create a new animal."""
        from src.database.models import Animal
        
        with self.get_session() as session:
            animal = Animal(
                id=animal_id,
                class_name=class_name,
                name=name,
                tag=tag,
                color=kwargs.get("color"),
                markings=kwargs.get("markings"),
                health_status="unknown",
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow()
            )
            session.add(animal)
            session.flush()
            
            # Detach from session for return
            session.expunge(animal)
            return animal
    
    def get_animal(self, animal_id: str):
        """Get animal by ID."""
        from src.database.models import Animal
        
        with self.get_session() as session:
            animal = session.query(Animal).filter(
                Animal.id == animal_id
            ).first()
            
            if animal:
                session.expunge(animal)
            return animal
    
    def get_animal_by_unique_id(self, unique_id: str):
        """Get animal by unique ID (same as get_animal for this model)."""
        return self.get_animal(unique_id)
    
    def get_all_animals(self, limit: int = 1000) -> List:
        """Get all animals."""
        from src.database.models import Animal
        
        with self.get_session() as session:
            animals = session.query(Animal).limit(limit).all()
            
            for a in animals:
                session.expunge(a)
            return animals
    
    def update_animal(self, animal_id: str, **kwargs):
        """Update animal data."""
        from src.database.models import Animal
        
        with self.get_session() as session:
            animal = session.query(Animal).filter(
                Animal.id == animal_id
            ).first()
            
            if not animal:
                return None
            
            for key, value in kwargs.items():
                if hasattr(animal, key) and value is not None:
                    setattr(animal, key, value)
            
            animal.updated_at = datetime.utcnow()
            session.flush()
            session.expunge(animal)
            return animal
    
    def update_animal_seen(self, animal_id: str):
        """Update animal last seen timestamp."""
        from src.database.models import Animal
        
        with self.get_session() as session:
            animal = session.query(Animal).filter(
                Animal.id == animal_id
            ).first()
            
            if animal:
                animal.last_seen_at = datetime.utcnow()
                animal.total_detections = (animal.total_detections or 0) + 1
    
    def delete_animal(self, animal_id: str) -> bool:
        """Delete an animal."""
        from src.database.models import Animal
        
        with self.get_session() as session:
            animal = session.query(Animal).filter(
                Animal.id == animal_id
            ).first()
            
            if not animal:
                return False
            
            session.delete(animal)
            return True
    
    # ===========================================
    # Detection Operations
    # ===========================================
    
    def create_detection(
        self,
        class_name: str,
        confidence: float,
        bbox_x1: int,
        bbox_y1: int,
        bbox_x2: int,
        bbox_y2: int,
        animal_id: Optional[str] = None,
        camera_id: Optional[str] = None,
        track_id: Optional[int] = None,
        frame_id: Optional[int] = None
    ):
        """Create a detection record."""
        from src.database.models import Detection
        
        center_x = (bbox_x1 + bbox_x2) // 2
        center_y = (bbox_y1 + bbox_y2) // 2
        
        with self.get_session() as session:
            detection = Detection(
                animal_id=animal_id,
                camera_id=camera_id,
                class_name=class_name,
                confidence=confidence,
                bbox_x1=bbox_x1,
                bbox_y1=bbox_y1,
                bbox_x2=bbox_x2,
                bbox_y2=bbox_y2,
                center_x=center_x,
                center_y=center_y,
                track_id=track_id,
                frame_id=frame_id,
                detected_at=datetime.utcnow()
            )
            session.add(detection)
            session.flush()
            
            session.expunge(detection)
            return detection
    
    def get_detections_for_animal(
        self,
        animal_id: str,
        limit: int = 100
    ) -> List:
        """Get detections for an animal."""
        from src.database.models import Detection
        
        with self.get_session() as session:
            detections = session.query(Detection).filter(
                Detection.animal_id == animal_id
            ).order_by(Detection.detected_at.desc()).limit(limit).all()
            
            for d in detections:
                session.expunge(d)
            return detections
    
    def get_recent_detections(self, limit: int = 100) -> List:
        """Get recent detections."""
        from src.database.models import Detection
        
        with self.get_session() as session:
            detections = session.query(Detection).order_by(
                Detection.detected_at.desc()
            ).limit(limit).all()
            
            for d in detections:
                session.expunge(d)
            return detections
    
    # ===========================================
    # Behavior Operations
    # ===========================================
    
    def create_behavior(
        self,
        animal_id: str,
        behavior: str,
        confidence: float = 0.0,
        camera_id: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        location_x: Optional[int] = None,
        location_y: Optional[int] = None
    ):
        """Create a behavior log entry."""
        from src.database.models import BehaviorLog
        
        with self.get_session() as session:
            behavior_log = BehaviorLog(
                animal_id=animal_id,
                camera_id=camera_id,
                behavior=behavior,
                confidence=confidence,
                started_at=datetime.utcnow(),
                duration_seconds=duration_seconds,
                location_x=location_x,
                location_y=location_y
            )
            session.add(behavior_log)
            session.flush()
            
            session.expunge(behavior_log)
            return behavior_log
    
    def get_behaviors_for_animal(
        self,
        animal_id: str,
        limit: int = 100
    ) -> List:
        """Get behaviors for an animal."""
        from src.database.models import BehaviorLog
        
        with self.get_session() as session:
            behaviors = session.query(BehaviorLog).filter(
                BehaviorLog.animal_id == animal_id
            ).order_by(BehaviorLog.started_at.desc()).limit(limit).all()
            
            for b in behaviors:
                session.expunge(b)
            return behaviors
    
    def get_recent_behaviors(self, limit: int = 100) -> List:
        """Get recent behaviors."""
        from src.database.models import BehaviorLog
        
        with self.get_session() as session:
            behaviors = session.query(BehaviorLog).order_by(
                BehaviorLog.started_at.desc()
            ).limit(limit).all()
            
            for b in behaviors:
                session.expunge(b)
            return behaviors
    
    # ===========================================
    # Health Record Operations
    # ===========================================
    
    def create_health_record(
        self,
        animal_id: str,
        status: str,
        bcs_score: Optional[float] = None,
        lameness_score: Optional[int] = None,
        activity_score: Optional[float] = None,
        notes: Optional[str] = None,
        metrics: Optional[Dict] = None
    ):
        """Create a health record."""
        from src.database.models import HealthRecord
        
        with self.get_session() as session:
            record = HealthRecord(
                animal_id=animal_id,
                status=status,
                bcs_score=bcs_score,
                lameness_score=lameness_score,
                activity_score=activity_score,
                notes=notes,
                metrics=metrics,
                recorded_at=datetime.utcnow()
            )
            session.add(record)
            session.flush()
            
            session.expunge(record)
            return record
    
    def get_health_records_for_animal(
        self,
        animal_id: str,
        limit: int = 100
    ) -> List:
        """Get health records for an animal."""
        from src.database.models import HealthRecord
        
        with self.get_session() as session:
            records = session.query(HealthRecord).filter(
                HealthRecord.animal_id == animal_id
            ).order_by(HealthRecord.recorded_at.desc()).limit(limit).all()
            
            for r in records:
                session.expunge(r)
            return records
    
    # ===========================================
    # Alert Operations
    # ===========================================
    
    def create_alert(
        self,
        alert_type: str,
        severity: str,
        title: str,
        message: str,
        animal_id: Optional[str] = None,
        camera_id: Optional[str] = None,
        extra_data: Optional[Dict] = None
    ):
        """Create an alert."""
        from src.database.models import Alert
        
        with self.get_session() as session:
            alert = Alert(
                animal_id=animal_id,
                camera_id=camera_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                extra_data=extra_data,
                created_at=datetime.utcnow()
            )
            session.add(alert)
            session.flush()
            
            session.expunge(alert)
            return alert
    
    def get_alerts_for_animal(
        self,
        animal_id: str,
        limit: int = 100
    ) -> List:
        """Get alerts for an animal."""
        from src.database.models import Alert
        
        with self.get_session() as session:
            alerts = session.query(Alert).filter(
                Alert.animal_id == animal_id
            ).order_by(Alert.created_at.desc()).limit(limit).all()
            
            for a in alerts:
                session.expunge(a)
            return alerts
    
    def get_unread_alerts(self, limit: int = 100) -> List:
        """Get unread alerts."""
        from src.database.models import Alert
        
        with self.get_session() as session:
            alerts = session.query(Alert).filter(
                Alert.is_read == False
            ).order_by(Alert.created_at.desc()).limit(limit).all()
            
            for a in alerts:
                session.expunge(a)
            return alerts
    
    def mark_alert_read(self, alert_id: int) -> bool:
        """Mark an alert as read."""
        from src.database.models import Alert
        
        with self.get_session() as session:
            alert = session.query(Alert).filter(
                Alert.id == alert_id
            ).first()
            
            if not alert:
                return False
            
            alert.is_read = True
            return True
    
    def resolve_alert(self, alert_id: int, resolved_by: Optional[str] = None) -> bool:
        """Resolve an alert."""
        from src.database.models import Alert
        
        with self.get_session() as session:
            alert = session.query(Alert).filter(
                Alert.id == alert_id
            ).first()
            
            if not alert:
                return False
            
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            return True
    
    # ===========================================
    # Statistics
    # ===========================================
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        from src.database.models import Animal, Detection, BehaviorLog, HealthRecord, Alert
        
        with self.get_session() as session:
            return {
                "animals": session.query(Animal).count(),
                "detections": session.query(Detection).count(),
                "behaviors": session.query(BehaviorLog).count(),
                "health_records": session.query(HealthRecord).count(),
                "alerts": session.query(Alert).count(),
                "unread_alerts": session.query(Alert).filter(Alert.is_read == False).count()
            }
