"""
Video Depolama Modülü

Video kayıt, segmentasyon ve yönetimi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum
import os
import shutil
import hashlib


class VideoFormat(Enum):
    """Video formatları"""
    MP4 = "mp4"
    AVI = "avi"
    MKV = "mkv"
    MOV = "mov"
    WEBM = "webm"


class VideoQuality(Enum):
    """Video kalitesi"""
    LOW = "480p"
    MEDIUM = "720p"
    HIGH = "1080p"
    ULTRA = "4K"


class StorageStatus(Enum):
    """Depolama durumu"""
    AVAILABLE = "available"
    FULL = "full"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class VideoMetadata:
    """Video metadata"""
    video_id: str
    filename: str
    filepath: str
    camera_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0
    file_size_bytes: int = 0
    format: VideoFormat = VideoFormat.MP4
    quality: VideoQuality = VideoQuality.MEDIUM
    fps: int = 30
    width: int = 1280
    height: int = 720
    has_detections: bool = False
    detection_count: int = 0
    thumbnail_path: Optional[str] = None
    checksum: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def file_size_mb(self) -> float:
        return self.file_size_bytes / (1024 * 1024)
    
    def to_dict(self) -> Dict:
        return {
            "video_id": self.video_id,
            "filename": self.filename,
            "filepath": self.filepath,
            "camera_id": self.camera_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "file_size_mb": round(self.file_size_mb, 2),
            "format": self.format.value,
            "quality": self.quality.value,
            "fps": self.fps,
            "resolution": f"{self.width}x{self.height}",
            "has_detections": self.has_detections,
            "detection_count": self.detection_count,
            "tags": self.tags
        }


@dataclass
class VideoSegment:
    """Video segmenti"""
    segment_id: str
    video_id: str
    start_time: float
    end_time: float
    filepath: str
    event_type: Optional[str] = None
    animal_ids: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class StorageInfo:
    """Depolama bilgisi"""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    video_count: int
    
    @property
    def used_percentage(self) -> float:
        return (self.used_bytes / self.total_bytes) * 100 if self.total_bytes > 0 else 0
    
    @property
    def status(self) -> StorageStatus:
        if self.used_percentage >= 95:
            return StorageStatus.FULL
        elif self.used_percentage >= 85:
            return StorageStatus.WARNING
        return StorageStatus.AVAILABLE
    
    def to_dict(self) -> Dict:
        return {
            "total_gb": round(self.total_bytes / (1024**3), 2),
            "used_gb": round(self.used_bytes / (1024**3), 2),
            "free_gb": round(self.free_bytes / (1024**3), 2),
            "used_percentage": round(self.used_percentage, 1),
            "video_count": self.video_count,
            "status": self.status.value
        }


class VideoStorage:
    """Video depolama yöneticisi"""
    
    def __init__(self, base_path: str = "data/videos", config: Optional[Dict] = None):
        self.base_path = Path(base_path)
        self.config = config or {}
        
        # Dizinleri oluştur
        self.base_path.mkdir(parents=True, exist_ok=True)
        (self.base_path / "raw").mkdir(exist_ok=True)
        (self.base_path / "processed").mkdir(exist_ok=True)
        (self.base_path / "segments").mkdir(exist_ok=True)
        (self.base_path / "thumbnails").mkdir(exist_ok=True)
        
        # Video kayıtları
        self.videos: Dict[str, VideoMetadata] = {}
        self.segments: Dict[str, VideoSegment] = {}
        
        # Ayarlar
        self.max_storage_gb = self.config.get("max_storage_gb", 100)
        self.segment_duration = self.config.get("segment_duration", 300)  # 5 dakika
        self.default_format = VideoFormat(self.config.get("format", "mp4"))
        self.default_quality = VideoQuality(self.config.get("quality", "720p"))
        
        # Sayaç
        self._video_counter = 0
        self._segment_counter = 0
    
    def _generate_video_id(self) -> str:
        self._video_counter += 1
        return f"VID_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._video_counter}"
    
    def _generate_segment_id(self) -> str:
        self._segment_counter += 1
        return f"SEG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._segment_counter}"
    
    def _calculate_checksum(self, filepath: str) -> str:
        """MD5 checksum hesapla"""
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def register_video(self, filepath: str, camera_id: str,
                      start_time: datetime,
                      end_time: Optional[datetime] = None,
                      tags: Optional[List[str]] = None) -> VideoMetadata:
        """Video kaydet"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Video bulunamadı: {filepath}")
        
        video_id = self._generate_video_id()
        file_size = path.stat().st_size
        
        # Format belirle
        suffix = path.suffix.lower().lstrip('.')
        try:
            video_format = VideoFormat(suffix)
        except ValueError:
            video_format = self.default_format
        
        # Süre hesapla (basitleştirilmiş)
        if end_time:
            duration = (end_time - start_time).total_seconds()
        else:
            # Dosya boyutundan tahmin (yaklaşık 1MB/dakika @ 720p)
            duration = file_size / (1024 * 1024) * 60
        
        metadata = VideoMetadata(
            video_id=video_id,
            filename=path.name,
            filepath=str(path.absolute()),
            camera_id=camera_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            file_size_bytes=file_size,
            format=video_format,
            quality=self.default_quality,
            checksum=self._calculate_checksum(filepath),
            tags=tags or []
        )
        
        self.videos[video_id] = metadata
        return metadata
    
    def create_segment(self, video_id: str, start_time: float,
                      end_time: float, event_type: Optional[str] = None,
                      animal_ids: Optional[List[str]] = None) -> Optional[VideoSegment]:
        """Video segmenti oluştur"""
        if video_id not in self.videos:
            return None
        
        video = self.videos[video_id]
        segment_id = self._generate_segment_id()
        
        # Segment dosya yolu
        segment_filename = f"{segment_id}_{event_type or 'clip'}.{video.format.value}"
        segment_path = self.base_path / "segments" / segment_filename
        
        segment = VideoSegment(
            segment_id=segment_id,
            video_id=video_id,
            start_time=start_time,
            end_time=end_time,
            filepath=str(segment_path),
            event_type=event_type,
            animal_ids=animal_ids or []
        )
        
        self.segments[segment_id] = segment
        return segment
    
    def get_video(self, video_id: str) -> Optional[VideoMetadata]:
        """Video metadata al"""
        return self.videos.get(video_id)
    
    def get_videos_by_camera(self, camera_id: str,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[VideoMetadata]:
        """Kameraya göre videoları al"""
        videos = [v for v in self.videos.values() if v.camera_id == camera_id]
        
        if start_date:
            videos = [v for v in videos if v.start_time >= start_date]
        if end_date:
            videos = [v for v in videos if v.start_time <= end_date]
        
        return sorted(videos, key=lambda x: x.start_time, reverse=True)
    
    def get_videos_by_date(self, date: datetime) -> List[VideoMetadata]:
        """Tarihe göre videoları al"""
        target_date = date.date()
        return [
            v for v in self.videos.values()
            if v.start_time.date() == target_date
        ]
    
    def search_videos(self, query: str = None,
                     camera_id: str = None,
                     has_detections: bool = None,
                     tags: List[str] = None,
                     limit: int = 50) -> List[VideoMetadata]:
        """Video ara"""
        results = list(self.videos.values())
        
        if camera_id:
            results = [v for v in results if v.camera_id == camera_id]
        
        if has_detections is not None:
            results = [v for v in results if v.has_detections == has_detections]
        
        if tags:
            results = [v for v in results if any(t in v.tags for t in tags)]
        
        if query:
            query_lower = query.lower()
            results = [v for v in results if query_lower in v.filename.lower()]
        
        return sorted(results, key=lambda x: x.start_time, reverse=True)[:limit]
    
    def delete_video(self, video_id: str, delete_file: bool = False) -> bool:
        """Video sil"""
        if video_id not in self.videos:
            return False
        
        video = self.videos[video_id]
        
        # Dosyayı sil
        if delete_file:
            try:
                Path(video.filepath).unlink(missing_ok=True)
                if video.thumbnail_path:
                    Path(video.thumbnail_path).unlink(missing_ok=True)
            except Exception:
                pass
        
        # Kayıttan sil
        del self.videos[video_id]
        
        # İlgili segmentleri sil
        segments_to_delete = [s.segment_id for s in self.segments.values() if s.video_id == video_id]
        for seg_id in segments_to_delete:
            del self.segments[seg_id]
        
        return True
    
    def get_storage_info(self) -> StorageInfo:
        """Depolama bilgisini al"""
        total, used, free = shutil.disk_usage(self.base_path)
        
        # Video sayısı
        video_count = len(self.videos)
        
        return StorageInfo(
            total_bytes=total,
            used_bytes=used,
            free_bytes=free,
            video_count=video_count
        )
    
    def cleanup_old_videos(self, days: int = 30) -> int:
        """Eski videoları temizle"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        videos_to_delete = [
            v.video_id for v in self.videos.values()
            if v.start_time < cutoff
        ]
        
        for video_id in videos_to_delete:
            if self.delete_video(video_id, delete_file=True):
                deleted_count += 1
        
        return deleted_count
    
    def get_summary(self) -> Dict:
        """Depolama özeti"""
        storage_info = self.get_storage_info()
        
        total_duration = sum(v.duration_seconds for v in self.videos.values())
        total_size = sum(v.file_size_bytes for v in self.videos.values())
        
        cameras = set(v.camera_id for v in self.videos.values())
        
        return {
            "storage": storage_info.to_dict(),
            "video_count": len(self.videos),
            "segment_count": len(self.segments),
            "total_duration_hours": round(total_duration / 3600, 2),
            "total_size_gb": round(total_size / (1024**3), 2),
            "camera_count": len(cameras),
            "videos_with_detections": sum(1 for v in self.videos.values() if v.has_detections)
        }
