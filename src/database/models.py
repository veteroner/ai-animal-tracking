"""
AI Animal Tracking System - Database Models
============================================

SQLAlchemy ORM modelleri.
SQLite (geliştirme) ve PostgreSQL (production) destekler.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, JSON, Enum as SQLEnum,
    Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum


Base = declarative_base()


# ===========================================
# Enums
# ===========================================

class AnimalClass(enum.Enum):
    """Hayvan türleri"""
    BIRD = "bird"
    CAT = "cat"
    DOG = "dog"
    HORSE = "horse"
    SHEEP = "sheep"
    COW = "cow"
    ELEPHANT = "elephant"
    BEAR = "bear"
    ZEBRA = "zebra"
    GIRAFFE = "giraffe"
    OTHER = "other"


class BehaviorTypeEnum(enum.Enum):
    """Davranış tipleri"""
    UNKNOWN = "unknown"
    STATIONARY = "stationary"
    WALKING = "walking"
    RUNNING = "running"
    EATING = "eating"
    DRINKING = "drinking"
    GRAZING = "grazing"
    RESTING = "resting"
    LYING = "lying"
    SLEEPING = "sleeping"


class HealthStatusEnum(enum.Enum):
    """Sağlık durumu"""
    HEALTHY = "healthy"
    ATTENTION = "attention"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertSeverity(enum.Enum):
    """Uyarı önem derecesi"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ===========================================
# Camera Model
# ===========================================

class Camera(Base):
    """Kamera tablosu"""
    __tablename__ = "cameras"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    source = Column(String(500), nullable=False)  # URL, index, veya dosya yolu
    camera_type = Column(String(20), default="usb")  # usb, rtsp, http, file
    
    # Ayarlar
    width = Column(Integer, default=1280)
    height = Column(Integer, default=720)
    fps = Column(Integer, default=30)
    
    # Durum
    is_enabled = Column(Boolean, default=True)
    is_streaming = Column(Boolean, default=False)
    last_frame_at = Column(DateTime, nullable=True)
    
    # Konum
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    detections = relationship("Detection", back_populates="camera")
    
    def __repr__(self):
        return f"<Camera {self.id}: {self.name}>"


# ===========================================
# Animal Model
# ===========================================

class Animal(Base):
    """Hayvan tablosu"""
    __tablename__ = "animals"
    
    id = Column(String(50), primary_key=True)  # DOG_0001, CAT_0002, vb.
    
    # Temel bilgiler
    class_name = Column(String(50), nullable=False)  # dog, cat, cow, vb.
    name = Column(String(100), nullable=True)  # Verilen isim
    tag = Column(String(50), nullable=True)  # Kulak numarası/RFID
    
    # Görsel özellikler
    color = Column(String(50), nullable=True)
    markings = Column(Text, nullable=True)  # Ayırt edici işaretler
    
    # Feature vektörü (JSON olarak)
    features = Column(JSON, nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    
    # İstatistikler
    first_seen_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    total_detections = Column(Integer, default=0)
    total_frames = Column(Integer, default=0)
    
    # Sağlık durumu
    health_status = Column(String(20), default="unknown")
    bcs_score = Column(Float, nullable=True)  # Body Condition Score
    lameness_score = Column(Integer, nullable=True)  # 1-5
    
    # Metadata
    notes = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # İlişkiler
    detections = relationship("Detection", back_populates="animal")
    behaviors = relationship("BehaviorLog", back_populates="animal")
    health_records = relationship("HealthRecord", back_populates="animal")
    alerts = relationship("Alert", back_populates="animal")
    
    # İndeksler
    __table_args__ = (
        Index("ix_animals_class_name", "class_name"),
        Index("ix_animals_last_seen", "last_seen_at"),
    )
    
    def __repr__(self):
        return f"<Animal {self.id}: {self.class_name}>"


# ===========================================
# Detection Model
# ===========================================

class Detection(Base):
    """Tespit tablosu"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # İlişkiler
    animal_id = Column(String(50), ForeignKey("animals.id"), nullable=True)
    camera_id = Column(String(50), ForeignKey("cameras.id"), nullable=True)
    
    # Tespit bilgileri
    class_name = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Bounding box
    bbox_x1 = Column(Integer, nullable=False)
    bbox_y1 = Column(Integer, nullable=False)
    bbox_x2 = Column(Integer, nullable=False)
    bbox_y2 = Column(Integer, nullable=False)
    
    # Merkez
    center_x = Column(Integer, nullable=False)
    center_y = Column(Integer, nullable=False)
    
    # Tracking
    track_id = Column(Integer, nullable=True)
    frame_id = Column(Integer, nullable=True)
    
    # Zaman
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    animal = relationship("Animal", back_populates="detections")
    camera = relationship("Camera", back_populates="detections")
    
    # İndeksler
    __table_args__ = (
        Index("ix_detections_animal_id", "animal_id"),
        Index("ix_detections_camera_id", "camera_id"),
        Index("ix_detections_detected_at", "detected_at"),
    )
    
    def __repr__(self):
        return f"<Detection {self.id}: {self.class_name} @ {self.confidence:.2f}>"


# ===========================================
# Behavior Log Model
# ===========================================

class BehaviorLog(Base):
    """Davranış kayıt tablosu"""
    __tablename__ = "behavior_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # İlişkiler
    animal_id = Column(String(50), ForeignKey("animals.id"), nullable=False)
    camera_id = Column(String(50), ForeignKey("cameras.id"), nullable=True)
    
    # Davranış bilgileri
    behavior = Column(String(50), nullable=False)  # stationary, walking, eating, vb.
    confidence = Column(Float, default=0.0)
    
    # Süre
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Konum
    location_x = Column(Integer, nullable=True)
    location_y = Column(Integer, nullable=True)
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    
    # İlişkiler
    animal = relationship("Animal", back_populates="behaviors")
    
    # İndeksler
    __table_args__ = (
        Index("ix_behavior_logs_animal_id", "animal_id"),
        Index("ix_behavior_logs_behavior", "behavior"),
        Index("ix_behavior_logs_started_at", "started_at"),
    )
    
    def __repr__(self):
        return f"<BehaviorLog {self.id}: {self.animal_id} - {self.behavior}>"


# ===========================================
# Health Record Model
# ===========================================

class HealthRecord(Base):
    """Sağlık kayıt tablosu"""
    __tablename__ = "health_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # İlişkiler
    animal_id = Column(String(50), ForeignKey("animals.id"), nullable=False)
    
    # Sağlık bilgileri
    status = Column(String(20), nullable=False)  # healthy, attention, warning, critical
    
    # Metrikler
    bcs_score = Column(Float, nullable=True)
    lameness_score = Column(Integer, nullable=True)
    activity_score = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    
    # Hareket metrikleri
    avg_speed = Column(Float, nullable=True)
    total_distance = Column(Float, nullable=True)
    stationary_ratio = Column(Float, nullable=True)
    
    # Detaylar
    notes = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)
    
    # Zaman
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    animal = relationship("Animal", back_populates="health_records")
    
    # İndeksler
    __table_args__ = (
        Index("ix_health_records_animal_id", "animal_id"),
        Index("ix_health_records_status", "status"),
        Index("ix_health_records_recorded_at", "recorded_at"),
    )
    
    def __repr__(self):
        return f"<HealthRecord {self.id}: {self.animal_id} - {self.status}>"


# ===========================================
# Alert Model
# ===========================================

class Alert(Base):
    """Uyarı tablosu"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # İlişkiler
    animal_id = Column(String(50), ForeignKey("animals.id"), nullable=True)
    camera_id = Column(String(50), ForeignKey("cameras.id"), nullable=True)
    
    # Uyarı bilgileri
    alert_type = Column(String(50), nullable=False)  # health, behavior, system
    severity = Column(String(20), nullable=False)  # info, low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Durum
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    
    # Extra data
    extra_data = Column(JSON, nullable=True)
    
    # Zaman
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # İlişkiler
    animal = relationship("Animal", back_populates="alerts")
    
    # İndeksler
    __table_args__ = (
        Index("ix_alerts_animal_id", "animal_id"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_is_read", "is_read"),
        Index("ix_alerts_created_at", "created_at"),
    )
    
    def __repr__(self):
        return f"<Alert {self.id}: {self.severity} - {self.title}>"


# ===========================================
# Session Statistics Model
# ===========================================

class SessionStats(Base):
    """Oturum istatistikleri tablosu"""
    __tablename__ = "session_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Oturum bilgileri
    session_id = Column(String(50), nullable=False, unique=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    
    # İstatistikler
    total_frames = Column(Integer, default=0)
    total_detections = Column(Integer, default=0)
    total_animals = Column(Integer, default=0)
    avg_fps = Column(Float, default=0.0)
    avg_inference_time = Column(Float, default=0.0)
    
    # Kamera bilgileri
    cameras_used = Column(JSON, nullable=True)
    
    # Metadata
    config = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<SessionStats {self.session_id}>"


# ===========================================
# Zone Model (Bölge tanımları)
# ===========================================

class Zone(Base):
    """Bölge tablosu"""
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Temel bilgiler
    name = Column(String(100), nullable=False)
    zone_type = Column(String(50), nullable=False)  # feeding, drinking, resting, restricted
    
    # Kamera
    camera_id = Column(String(50), ForeignKey("cameras.id"), nullable=True)
    
    # Koordinatlar (bounding box)
    x1 = Column(Integer, nullable=False)
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)
    
    # Ayarlar
    is_active = Column(Boolean, default=True)
    color = Column(String(20), default="#00FF00")
    
    # Metadata
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Zone {self.id}: {self.name} ({self.zone_type})>"


# ===========================================
# Database Manager
# ===========================================

class DatabaseManager:
    """Veritabanı yönetici sınıfı"""
    
    def __init__(self, database_url: str = "sqlite:///data/animal_tracking.db"):
        """
        Args:
            database_url: Veritabanı bağlantı URL'si
                - SQLite: sqlite:///path/to/db.sqlite
                - PostgreSQL: postgresql://user:pass@host:port/db
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self):
        """Tüm tabloları oluştur"""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Tüm tabloları sil"""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self):
        """Yeni session oluştur"""
        return self.SessionLocal()
    
    def __enter__(self):
        self.session = self.get_session()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        self.session.close()


# ===========================================
# Test
# ===========================================

if __name__ == "__main__":
    import os
    
    # Test veritabanı
    os.makedirs("data", exist_ok=True)
    
    db = DatabaseManager("sqlite:///data/test_animal_tracking.db")
    db.create_tables()
    
    print("✅ Database tables created successfully!")
    
    # Test kayıtları
    with db as session:
        # Kamera ekle
        camera = Camera(
            id="cam_001",
            name="Test Camera",
            source="0",
            camera_type="usb"
        )
        session.add(camera)
        
        # Hayvan ekle
        animal = Animal(
            id="DOG_0001",
            class_name="dog",
            name="Buddy"
        )
        session.add(animal)
        
        # Detection ekle
        detection = Detection(
            animal_id="DOG_0001",
            camera_id="cam_001",
            class_name="dog",
            confidence=0.95,
            bbox_x1=100, bbox_y1=100,
            bbox_x2=200, bbox_y2=200,
            center_x=150, center_y=150
        )
        session.add(detection)
        
        session.commit()
        
        print(f"✅ Test records created!")
        print(f"   Cameras: {session.query(Camera).count()}")
        print(f"   Animals: {session.query(Animal).count()}")
        print(f"   Detections: {session.query(Detection).count()}")
    
    # Temizlik
    os.remove("data/test_animal_tracking.db")
    print("✅ Test database cleaned up!")
