"""
Görüntü Depolama Modülü

Snapshot, thumbnail ve görüntü yönetimi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum
import hashlib
import shutil


class ImageFormat(Enum):
    """Görüntü formatları"""
    JPEG = "jpg"
    PNG = "png"
    WEBP = "webp"


class ImageType(Enum):
    """Görüntü türleri"""
    SNAPSHOT = "snapshot"
    THUMBNAIL = "thumbnail"
    DETECTION = "detection"
    PROFILE = "profile"
    ANNOTATION = "annotation"


@dataclass
class ImageMetadata:
    """Görüntü metadata"""
    image_id: str
    filename: str
    filepath: str
    image_type: ImageType
    timestamp: datetime
    camera_id: Optional[str] = None
    animal_id: Optional[str] = None
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    format: ImageFormat = ImageFormat.JPEG
    quality: int = 85
    has_detections: bool = False
    detection_data: Optional[Dict] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def file_size_kb(self) -> float:
        return self.file_size_bytes / 1024
    
    @property
    def resolution(self) -> str:
        return f"{self.width}x{self.height}"
    
    def to_dict(self) -> Dict:
        return {
            "image_id": self.image_id,
            "filename": self.filename,
            "filepath": self.filepath,
            "image_type": self.image_type.value,
            "timestamp": self.timestamp.isoformat(),
            "camera_id": self.camera_id,
            "animal_id": self.animal_id,
            "resolution": self.resolution,
            "file_size_kb": round(self.file_size_kb, 2),
            "format": self.format.value,
            "has_detections": self.has_detections,
            "tags": self.tags
        }


class ImageStorage:
    """Görüntü depolama yöneticisi"""
    
    def __init__(self, base_path: str = "data/images", config: Optional[Dict] = None):
        self.base_path = Path(base_path)
        self.config = config or {}
        
        # Dizinleri oluştur
        self.base_path.mkdir(parents=True, exist_ok=True)
        for img_type in ImageType:
            (self.base_path / img_type.value).mkdir(exist_ok=True)
        
        # Görüntü kayıtları
        self.images: Dict[str, ImageMetadata] = {}
        
        # Ayarlar
        self.default_format = ImageFormat(self.config.get("format", "jpg"))
        self.default_quality = self.config.get("quality", 85)
        self.max_storage_gb = self.config.get("max_storage_gb", 10)
        
        # Thumbnail boyutları
        self.thumbnail_size = self.config.get("thumbnail_size", (320, 240))
        
        # Sayaç
        self._image_counter = 0
    
    def _generate_image_id(self) -> str:
        self._image_counter += 1
        return f"IMG_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._image_counter}"
    
    def _get_storage_path(self, image_type: ImageType, date: datetime) -> Path:
        """Tarih bazlı depolama yolu"""
        date_folder = date.strftime("%Y/%m/%d")
        path = self.base_path / image_type.value / date_folder
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def save_image(self, image_data: bytes, image_type: ImageType,
                  camera_id: Optional[str] = None,
                  animal_id: Optional[str] = None,
                  timestamp: Optional[datetime] = None,
                  format: Optional[ImageFormat] = None,
                  tags: Optional[List[str]] = None,
                  detection_data: Optional[Dict] = None) -> ImageMetadata:
        """Görüntü kaydet"""
        timestamp = timestamp or datetime.now()
        format = format or self.default_format
        
        image_id = self._generate_image_id()
        
        # Dosya adı ve yolu
        filename = f"{image_id}.{format.value}"
        storage_path = self._get_storage_path(image_type, timestamp)
        filepath = storage_path / filename
        
        # Dosyaya yaz
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Boyut bilgisi
        file_size = len(image_data)
        
        # Metadata oluştur
        metadata = ImageMetadata(
            image_id=image_id,
            filename=filename,
            filepath=str(filepath.absolute()),
            image_type=image_type,
            timestamp=timestamp,
            camera_id=camera_id,
            animal_id=animal_id,
            file_size_bytes=file_size,
            format=format,
            quality=self.default_quality,
            has_detections=detection_data is not None,
            detection_data=detection_data,
            tags=tags or []
        )
        
        self.images[image_id] = metadata
        return metadata
    
    def save_snapshot(self, image_data: bytes, camera_id: str,
                     timestamp: Optional[datetime] = None,
                     tags: Optional[List[str]] = None) -> ImageMetadata:
        """Snapshot kaydet"""
        return self.save_image(
            image_data=image_data,
            image_type=ImageType.SNAPSHOT,
            camera_id=camera_id,
            timestamp=timestamp,
            tags=tags
        )
    
    def save_detection_image(self, image_data: bytes, camera_id: str,
                            detection_data: Dict,
                            animal_id: Optional[str] = None,
                            timestamp: Optional[datetime] = None) -> ImageMetadata:
        """Tespit görüntüsü kaydet"""
        return self.save_image(
            image_data=image_data,
            image_type=ImageType.DETECTION,
            camera_id=camera_id,
            animal_id=animal_id,
            timestamp=timestamp,
            detection_data=detection_data,
            tags=["detection"]
        )
    
    def save_animal_profile(self, image_data: bytes, animal_id: str,
                           timestamp: Optional[datetime] = None) -> ImageMetadata:
        """Hayvan profil görüntüsü kaydet"""
        return self.save_image(
            image_data=image_data,
            image_type=ImageType.PROFILE,
            animal_id=animal_id,
            timestamp=timestamp,
            tags=["profile"]
        )
    
    def get_image(self, image_id: str) -> Optional[ImageMetadata]:
        """Görüntü metadata al"""
        return self.images.get(image_id)
    
    def get_image_data(self, image_id: str) -> Optional[bytes]:
        """Görüntü verisini al"""
        metadata = self.images.get(image_id)
        if not metadata:
            return None
        
        try:
            with open(metadata.filepath, 'rb') as f:
                return f.read()
        except:
            return None
    
    def get_images_by_animal(self, animal_id: str,
                            image_type: Optional[ImageType] = None,
                            limit: int = 50) -> List[ImageMetadata]:
        """Hayvana göre görüntüleri al"""
        images = [img for img in self.images.values() if img.animal_id == animal_id]
        
        if image_type:
            images = [img for img in images if img.image_type == image_type]
        
        return sorted(images, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_images_by_camera(self, camera_id: str,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            limit: int = 100) -> List[ImageMetadata]:
        """Kameraya göre görüntüleri al"""
        images = [img for img in self.images.values() if img.camera_id == camera_id]
        
        if start_date:
            images = [img for img in images if img.timestamp >= start_date]
        if end_date:
            images = [img for img in images if img.timestamp <= end_date]
        
        return sorted(images, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_images_by_type(self, image_type: ImageType,
                          limit: int = 100) -> List[ImageMetadata]:
        """Türe göre görüntüleri al"""
        images = [img for img in self.images.values() if img.image_type == image_type]
        return sorted(images, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def get_detection_images(self, start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None,
                            limit: int = 100) -> List[ImageMetadata]:
        """Tespit görüntülerini al"""
        images = [img for img in self.images.values() if img.has_detections]
        
        if start_date:
            images = [img for img in images if img.timestamp >= start_date]
        if end_date:
            images = [img for img in images if img.timestamp <= end_date]
        
        return sorted(images, key=lambda x: x.timestamp, reverse=True)[:limit]
    
    def delete_image(self, image_id: str, delete_file: bool = True) -> bool:
        """Görüntü sil"""
        if image_id not in self.images:
            return False
        
        metadata = self.images[image_id]
        
        if delete_file:
            try:
                Path(metadata.filepath).unlink(missing_ok=True)
            except:
                pass
        
        del self.images[image_id]
        return True
    
    def cleanup_old_images(self, days: int = 7,
                          image_types: Optional[List[ImageType]] = None) -> int:
        """Eski görüntüleri temizle"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        images_to_delete = []
        for img in self.images.values():
            if img.timestamp < cutoff:
                if image_types is None or img.image_type in image_types:
                    images_to_delete.append(img.image_id)
        
        for image_id in images_to_delete:
            if self.delete_image(image_id, delete_file=True):
                deleted_count += 1
        
        return deleted_count
    
    def get_storage_usage(self) -> Dict:
        """Depolama kullanımı"""
        total_size = sum(img.file_size_bytes for img in self.images.values())
        
        by_type = {}
        for img_type in ImageType:
            type_images = [img for img in self.images.values() if img.image_type == img_type]
            by_type[img_type.value] = {
                "count": len(type_images),
                "size_mb": round(sum(img.file_size_bytes for img in type_images) / (1024**2), 2)
            }
        
        return {
            "total_images": len(self.images),
            "total_size_mb": round(total_size / (1024**2), 2),
            "by_type": by_type,
            "max_storage_gb": self.max_storage_gb
        }
    
    def get_summary(self) -> Dict:
        """Depolama özeti"""
        storage_usage = self.get_storage_usage()
        
        cameras = set(img.camera_id for img in self.images.values() if img.camera_id)
        animals = set(img.animal_id for img in self.images.values() if img.animal_id)
        
        return {
            **storage_usage,
            "unique_cameras": len(cameras),
            "unique_animals": len(animals),
            "images_with_detections": sum(1 for img in self.images.values() if img.has_detections)
        }
