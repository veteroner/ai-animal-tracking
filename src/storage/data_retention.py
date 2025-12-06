"""
Veri Saklama Politikası Modülü

Veri tutma, arşivleme ve temizleme yönetimi.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from pathlib import Path
from enum import Enum
import shutil
import os


class DataCategory(Enum):
    """Veri kategorileri"""
    VIDEO = "video"
    IMAGE = "image"
    LOG = "log"
    ANALYTICS = "analytics"
    DETECTION = "detection"
    BACKUP = "backup"


class RetentionAction(Enum):
    """Saklama aksiyonu"""
    KEEP = "keep"
    ARCHIVE = "archive"
    DELETE = "delete"


@dataclass
class RetentionPolicy:
    """Saklama politikası"""
    category: DataCategory
    retention_days: int
    archive_days: Optional[int] = None  # None = arşivleme yok
    priority: int = 0  # Yüksek = önemli, silinmez
    compress_on_archive: bool = True
    delete_after_archive: bool = True
    
    def get_action(self, age_days: int) -> RetentionAction:
        """Yaşa göre aksiyon belirle"""
        if self.priority > 5:  # Yüksek öncelik = hiç silme
            return RetentionAction.KEEP
        
        if self.archive_days and age_days >= self.archive_days:
            if self.delete_after_archive and age_days >= self.retention_days:
                return RetentionAction.DELETE
            return RetentionAction.ARCHIVE
        
        if age_days >= self.retention_days:
            return RetentionAction.DELETE
        
        return RetentionAction.KEEP


@dataclass
class RetentionStats:
    """Saklama istatistikleri"""
    category: DataCategory
    total_items: int = 0
    kept_items: int = 0
    archived_items: int = 0
    deleted_items: int = 0
    freed_bytes: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "category": self.category.value,
            "total_items": self.total_items,
            "kept_items": self.kept_items,
            "archived_items": self.archived_items,
            "deleted_items": self.deleted_items,
            "freed_mb": round(self.freed_bytes / (1024**2), 2)
        }


@dataclass
class CleanupResult:
    """Temizlik sonucu"""
    timestamp: datetime
    stats: Dict[str, RetentionStats]
    total_freed_bytes: int
    errors: List[str] = field(default_factory=list)
    
    @property
    def total_freed_mb(self) -> float:
        return self.total_freed_bytes / (1024**2)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_freed_mb": round(self.total_freed_mb, 2),
            "stats": {k: v.to_dict() for k, v in self.stats.items()},
            "errors": self.errors
        }


class DataRetentionManager:
    """Veri saklama yöneticisi"""
    
    def __init__(self, base_path: str = "data", config: Optional[Dict] = None):
        self.base_path = Path(base_path)
        self.config = config or {}
        
        # Arşiv dizini
        self.archive_path = self.base_path / "archive"
        self.archive_path.mkdir(parents=True, exist_ok=True)
        
        # Varsayılan politikalar
        self.policies: Dict[DataCategory, RetentionPolicy] = {}
        self._setup_default_policies()
        
        # Temizlik geçmişi
        self.cleanup_history: List[CleanupResult] = []
    
    def _setup_default_policies(self):
        """Varsayılan politikaları oluştur"""
        default_policies = {
            DataCategory.VIDEO: RetentionPolicy(
                category=DataCategory.VIDEO,
                retention_days=30,
                archive_days=14,
                compress_on_archive=False
            ),
            DataCategory.IMAGE: RetentionPolicy(
                category=DataCategory.IMAGE,
                retention_days=7,
                archive_days=None
            ),
            DataCategory.LOG: RetentionPolicy(
                category=DataCategory.LOG,
                retention_days=90,
                archive_days=30,
                compress_on_archive=True
            ),
            DataCategory.ANALYTICS: RetentionPolicy(
                category=DataCategory.ANALYTICS,
                retention_days=365,
                archive_days=90,
                priority=3
            ),
            DataCategory.DETECTION: RetentionPolicy(
                category=DataCategory.DETECTION,
                retention_days=14,
                archive_days=7
            ),
            DataCategory.BACKUP: RetentionPolicy(
                category=DataCategory.BACKUP,
                retention_days=30,
                archive_days=None,
                priority=5
            )
        }
        
        # Config'den override
        for cat_name, config_data in self.config.get("policies", {}).items():
            try:
                category = DataCategory(cat_name)
                if category in default_policies:
                    for key, value in config_data.items():
                        if hasattr(default_policies[category], key):
                            setattr(default_policies[category], key, value)
            except:
                pass
        
        self.policies = default_policies
    
    def set_policy(self, policy: RetentionPolicy):
        """Politika ayarla"""
        self.policies[policy.category] = policy
    
    def get_policy(self, category: DataCategory) -> Optional[RetentionPolicy]:
        """Politika al"""
        return self.policies.get(category)
    
    def evaluate_item(self, category: DataCategory,
                     created_date: datetime) -> RetentionAction:
        """Öğeyi değerlendir"""
        policy = self.policies.get(category)
        if not policy:
            return RetentionAction.KEEP
        
        age_days = (datetime.now() - created_date).days
        return policy.get_action(age_days)
    
    def run_cleanup(self, dry_run: bool = False) -> CleanupResult:
        """Temizlik çalıştır"""
        stats = {}
        total_freed = 0
        errors = []
        
        # Kategori dizinlerini işle
        category_paths = {
            DataCategory.VIDEO: self.base_path / "videos",
            DataCategory.IMAGE: self.base_path / "images",
            DataCategory.LOG: self.base_path / "logs",
            DataCategory.ANALYTICS: self.base_path / "analytics",
            DataCategory.DETECTION: self.base_path / "detections",
            DataCategory.BACKUP: self.base_path / "backups"
        }
        
        for category, path in category_paths.items():
            if not path.exists():
                continue
            
            cat_stats = RetentionStats(category=category)
            policy = self.policies.get(category)
            
            if not policy:
                continue
            
            try:
                # Dosyaları tara
                for file_path in self._get_files_recursive(path):
                    cat_stats.total_items += 1
                    
                    # Dosya yaşını hesapla
                    try:
                        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        age_days = (datetime.now() - mtime).days
                        action = policy.get_action(age_days)
                        
                        if action == RetentionAction.KEEP:
                            cat_stats.kept_items += 1
                        
                        elif action == RetentionAction.ARCHIVE:
                            if not dry_run:
                                self._archive_file(file_path, category, policy.compress_on_archive)
                            cat_stats.archived_items += 1
                        
                        elif action == RetentionAction.DELETE:
                            file_size = file_path.stat().st_size
                            if not dry_run:
                                file_path.unlink()
                            cat_stats.deleted_items += 1
                            cat_stats.freed_bytes += file_size
                            total_freed += file_size
                    
                    except Exception as e:
                        errors.append(f"{file_path}: {str(e)}")
            
            except Exception as e:
                errors.append(f"Kategori {category.value}: {str(e)}")
            
            stats[category.value] = cat_stats
        
        result = CleanupResult(
            timestamp=datetime.now(),
            stats=stats,
            total_freed_bytes=total_freed,
            errors=errors
        )
        
        if not dry_run:
            self.cleanup_history.append(result)
        
        return result
    
    def _get_files_recursive(self, path: Path) -> List[Path]:
        """Dizindeki dosyaları recursive olarak al"""
        files = []
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    files.append(item)
        except:
            pass
        return files
    
    def _archive_file(self, file_path: Path, category: DataCategory,
                     compress: bool = True):
        """Dosyayı arşivle"""
        # Arşiv yolu oluştur
        relative_path = file_path.relative_to(self.base_path)
        archive_dest = self.archive_path / relative_path
        archive_dest.parent.mkdir(parents=True, exist_ok=True)
        
        if compress:
            # Gzip ile sıkıştır
            import gzip
            compressed_path = archive_dest.with_suffix(archive_dest.suffix + '.gz')
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # Direkt kopyala
            shutil.copy2(file_path, archive_dest)
    
    def cleanup_archives(self, days: int = 365) -> int:
        """Eski arşivleri temizle"""
        cutoff = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        for file_path in self._get_files_recursive(self.archive_path):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    file_path.unlink()
                    deleted_count += 1
            except:
                pass
        
        return deleted_count
    
    def get_storage_analysis(self) -> Dict:
        """Depolama analizi"""
        analysis = {
            "base_path": str(self.base_path),
            "categories": {},
            "total_size_gb": 0,
            "archive_size_gb": 0
        }
        
        category_paths = {
            DataCategory.VIDEO: self.base_path / "videos",
            DataCategory.IMAGE: self.base_path / "images",
            DataCategory.LOG: self.base_path / "logs",
            DataCategory.ANALYTICS: self.base_path / "analytics",
            DataCategory.DETECTION: self.base_path / "detections"
        }
        
        total_size = 0
        
        for category, path in category_paths.items():
            if path.exists():
                files = self._get_files_recursive(path)
                size = sum(f.stat().st_size for f in files)
                
                # Yaş dağılımı
                age_distribution = {"0-7_days": 0, "7-30_days": 0, "30+_days": 0}
                for f in files:
                    mtime = datetime.fromtimestamp(f.stat().st_mtime)
                    age = (datetime.now() - mtime).days
                    if age <= 7:
                        age_distribution["0-7_days"] += 1
                    elif age <= 30:
                        age_distribution["7-30_days"] += 1
                    else:
                        age_distribution["30+_days"] += 1
                
                analysis["categories"][category.value] = {
                    "file_count": len(files),
                    "size_mb": round(size / (1024**2), 2),
                    "retention_days": self.policies[category].retention_days if category in self.policies else None,
                    "age_distribution": age_distribution
                }
                total_size += size
        
        # Arşiv boyutu
        archive_files = self._get_files_recursive(self.archive_path)
        archive_size = sum(f.stat().st_size for f in archive_files)
        
        analysis["total_size_gb"] = round(total_size / (1024**3), 2)
        analysis["archive_size_gb"] = round(archive_size / (1024**3), 2)
        
        return analysis
    
    def get_cleanup_recommendations(self) -> List[Dict]:
        """Temizlik önerileri"""
        recommendations = []
        analysis = self.get_storage_analysis()
        
        for cat_name, cat_data in analysis.get("categories", {}).items():
            try:
                category = DataCategory(cat_name)
                policy = self.policies.get(category)
                
                if not policy:
                    continue
                
                old_files = cat_data.get("age_distribution", {}).get("30+_days", 0)
                total_files = cat_data.get("file_count", 0)
                
                if total_files > 0 and old_files / total_files > 0.3:
                    recommendations.append({
                        "category": cat_name,
                        "message": f"{old_files} dosya 30 günden eski",
                        "action": "cleanup",
                        "estimated_savings_mb": round(cat_data.get("size_mb", 0) * 0.3, 2)
                    })
                
                if cat_data.get("size_mb", 0) > 1000:  # 1GB üzeri
                    recommendations.append({
                        "category": cat_name,
                        "message": "Kategori boyutu 1GB'ı aştı",
                        "action": "review",
                        "current_size_mb": cat_data.get("size_mb", 0)
                    })
            except:
                pass
        
        return recommendations
    
    def get_summary(self) -> Dict:
        """Özet bilgi"""
        analysis = self.get_storage_analysis()
        
        return {
            "total_storage_gb": analysis.get("total_size_gb", 0),
            "archive_storage_gb": analysis.get("archive_size_gb", 0),
            "category_count": len(analysis.get("categories", {})),
            "policies_configured": len(self.policies),
            "last_cleanup": self.cleanup_history[-1].timestamp.isoformat() if self.cleanup_history else None,
            "recommendations": len(self.get_cleanup_recommendations())
        }
