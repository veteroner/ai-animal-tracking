# src/export/exporters.py
"""
Data Exporters - Veri Dışa Aktarım
==================================

CSV, JSON ve Excel formatlarında veri export.
"""

import csv
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Temel exporter sınıfı."""
    
    def __init__(self, output_dir: str = "exports"):
        """
        Args:
            output_dir: Çıktı klasörü
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def export(
        self,
        data: Union[List[Dict], Dict],
        filename: str,
        **kwargs
    ) -> Path:
        """
        Veriyi dışa aktar.
        
        Args:
            data: Export edilecek veri
            filename: Dosya adı (uzantısız)
            
        Returns:
            Oluşturulan dosya yolu
        """
        pass
    
    def generate_filename(
        self,
        prefix: str,
        extension: str,
        timestamp: bool = True
    ) -> str:
        """Zaman damgalı dosya adı oluştur."""
        if timestamp:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"{prefix}_{ts}.{extension}"
        return f"{prefix}.{extension}"


class CSVExporter(BaseExporter):
    """CSV formatında export."""
    
    def __init__(
        self,
        output_dir: str = "exports",
        delimiter: str = ",",
        encoding: str = "utf-8"
    ):
        super().__init__(output_dir)
        self.delimiter = delimiter
        self.encoding = encoding
    
    def export(
        self,
        data: List[Dict],
        filename: str,
        columns: Optional[List[str]] = None,
        timestamp: bool = True,
        **kwargs
    ) -> Path:
        """
        CSV olarak export.
        
        Args:
            data: Dict listesi
            filename: Dosya adı
            columns: Sütun sıralaması
            timestamp: Dosya adına zaman ekle
        """
        if not data:
            logger.warning("No data to export")
            return None
        
        # Dosya adı
        full_filename = self.generate_filename(filename, "csv", timestamp)
        filepath = self.output_dir / full_filename
        
        # Sütunları belirle
        if columns is None:
            columns = list(data[0].keys())
        
        # CSV yaz
        with open(filepath, "w", newline="", encoding=self.encoding) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=columns,
                delimiter=self.delimiter,
                extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Exported {len(data)} records to {filepath}")
        return filepath
    
    def export_detections(
        self,
        detections: List[Dict],
        filename: str = "detections"
    ) -> Path:
        """Detection verilerini export et."""
        columns = [
            "timestamp", "frame_id", "animal_id", "class_name",
            "confidence", "x1", "y1", "x2", "y2", "track_id"
        ]
        return self.export(detections, filename, columns=columns)
    
    def export_tracking(
        self,
        tracks: List[Dict],
        filename: str = "tracks"
    ) -> Path:
        """Tracking verilerini export et."""
        columns = [
            "track_id", "animal_id", "class_name", "start_time", "end_time",
            "duration_seconds", "total_distance", "avg_speed"
        ]
        return self.export(tracks, filename, columns=columns)
    
    def export_feeding(
        self,
        feeding_data: List[Dict],
        filename: str = "feeding"
    ) -> Path:
        """Beslenme verilerini export et."""
        columns = [
            "animal_id", "zone_id", "start_time", "end_time",
            "duration_minutes", "estimated_consumption_kg"
        ]
        return self.export(feeding_data, filename, columns=columns)


class JSONExporter(BaseExporter):
    """JSON formatında export."""
    
    def __init__(
        self,
        output_dir: str = "exports",
        indent: int = 2,
        encoding: str = "utf-8"
    ):
        super().__init__(output_dir)
        self.indent = indent
        self.encoding = encoding
    
    def export(
        self,
        data: Union[List[Dict], Dict],
        filename: str,
        timestamp: bool = True,
        pretty: bool = True,
        **kwargs
    ) -> Path:
        """
        JSON olarak export.
        
        Args:
            data: Export edilecek veri
            filename: Dosya adı
            timestamp: Dosya adına zaman ekle
            pretty: İnsan okunabilir format
        """
        # Dosya adı
        full_filename = self.generate_filename(filename, "json", timestamp)
        filepath = self.output_dir / full_filename
        
        # JSON yaz
        with open(filepath, "w", encoding=self.encoding) as f:
            indent = self.indent if pretty else None
            json.dump(data, f, indent=indent, default=str, ensure_ascii=False)
        
        record_count = len(data) if isinstance(data, list) else 1
        logger.info(f"Exported {record_count} records to {filepath}")
        return filepath
    
    def export_session_report(
        self,
        report: Dict,
        filename: str = "session_report"
    ) -> Path:
        """Session raporunu export et."""
        return self.export(report, filename)
    
    def export_daily_summary(
        self,
        summary: Dict,
        filename: str = "daily_summary"
    ) -> Path:
        """Günlük özeti export et."""
        return self.export(summary, filename)


class ExcelExporter(BaseExporter):
    """Excel formatında export (openpyxl ile)."""
    
    def __init__(self, output_dir: str = "exports"):
        super().__init__(output_dir)
        self._openpyxl = None
    
    def _ensure_openpyxl(self):
        """openpyxl yüklü mü kontrol et."""
        if self._openpyxl is None:
            try:
                import openpyxl  # type: ignore
                self._openpyxl = openpyxl
            except ImportError:
                logger.error(
                    "openpyxl is required for Excel export. "
                    "Install with: pip install openpyxl"
                )
                raise
    
    def export(
        self,
        data: Union[List[Dict], Dict[str, List[Dict]]],
        filename: str,
        timestamp: bool = True,
        sheet_name: str = "Data",
        **kwargs
    ) -> Path:
        """
        Excel olarak export.
        
        Args:
            data: Export edilecek veri
                  - List[Dict]: Tek sheet
                  - Dict[str, List[Dict]]: Çoklu sheet (key=sheet adı)
            filename: Dosya adı
            timestamp: Dosya adına zaman ekle
            sheet_name: Sheet adı (tek sheet için)
        """
        self._ensure_openpyxl()
        
        # Dosya adı
        full_filename = self.generate_filename(filename, "xlsx", timestamp)
        filepath = self.output_dir / full_filename
        
        # Workbook oluştur
        wb = self._openpyxl.Workbook()
        
        # Çoklu sheet veya tek sheet
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            # Çoklu sheet
            for idx, (name, sheet_data) in enumerate(data.items()):
                if idx == 0:
                    ws = wb.active
                    ws.title = name
                else:
                    ws = wb.create_sheet(title=name)
                self._write_sheet(ws, sheet_data)
        else:
            # Tek sheet
            ws = wb.active
            ws.title = sheet_name
            self._write_sheet(ws, data)
        
        # Kaydet
        wb.save(filepath)
        logger.info(f"Exported to {filepath}")
        return filepath
    
    def _write_sheet(self, ws, data: List[Dict]):
        """Sheet'e veri yaz."""
        if not data:
            return
        
        # Header
        columns = list(data[0].keys())
        ws.append(columns)
        
        # Data
        for row in data:
            values = [row.get(col) for col in columns]
            ws.append(values)
    
    def export_full_report(
        self,
        detections: List[Dict],
        tracks: List[Dict],
        feeding: List[Dict],
        filename: str = "full_report"
    ) -> Path:
        """Tüm verileri çoklu sheet olarak export et."""
        data = {
            "Detections": detections,
            "Tracks": tracks,
            "Feeding": feeding,
        }
        return self.export(data, filename)


class ReportGenerator:
    """Rapor oluşturucu."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.csv_exporter = CSVExporter(output_dir)
        self.json_exporter = JSONExporter(output_dir)
    
    def generate_daily_report(
        self,
        date: Optional[datetime] = None,
        detections: List[Dict] = None,
        tracks: List[Dict] = None,
        feeding: List[Dict] = None,
        health: List[Dict] = None,
    ) -> Dict[str, Path]:
        """
        Günlük rapor oluştur.
        
        Returns:
            Oluşturulan dosya yolları
        """
        date = date or datetime.now()
        date_str = date.strftime("%Y%m%d")
        
        files = {}
        
        if detections:
            files["detections"] = self.csv_exporter.export(
                detections,
                f"detections_{date_str}",
                timestamp=False
            )
        
        if tracks:
            files["tracks"] = self.csv_exporter.export(
                tracks,
                f"tracks_{date_str}",
                timestamp=False
            )
        
        if feeding:
            files["feeding"] = self.csv_exporter.export(
                feeding,
                f"feeding_{date_str}",
                timestamp=False
            )
        
        if health:
            files["health"] = self.csv_exporter.export(
                health,
                f"health_{date_str}",
                timestamp=False
            )
        
        # Özet JSON
        summary = {
            "report_date": date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "statistics": {
                "total_detections": len(detections) if detections else 0,
                "total_tracks": len(tracks) if tracks else 0,
                "feeding_sessions": len(feeding) if feeding else 0,
                "health_records": len(health) if health else 0,
            },
            "files": {k: str(v) for k, v in files.items()}
        }
        
        files["summary"] = self.json_exporter.export(
            summary,
            f"summary_{date_str}",
            timestamp=False
        )
        
        return files
