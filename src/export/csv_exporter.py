"""
CSV Exporter - CSV formatında veri dışa aktarma
"""

import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import io


logger = logging.getLogger(__name__)


class CSVExporter:
    """CSV format dışa aktarıcı"""
    
    def __init__(self, output_dir: str = "data/exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def export_to_file(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        columns: List[str] = None,
        delimiter: str = ",",
        include_header: bool = True
    ) -> str:
        """Veriyi CSV dosyasına aktar"""
        if not data:
            logger.warning("Boş veri, dosya oluşturulmadı")
            return None
            
        # Sütunlar belirtilmemişse ilk satırdan al
        if columns is None:
            columns = list(data[0].keys())
            
        # Dosya yolu oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.output_dir / f"{filename}_{timestamp}.csv"
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=columns,
                    delimiter=delimiter,
                    extrasaction='ignore'
                )
                
                if include_header:
                    writer.writeheader()
                    
                writer.writerows(data)
                
            logger.info(f"CSV dosyası oluşturuldu: {filepath} ({len(data)} satır)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"CSV export hatası: {e}")
            raise
            
    def export_to_string(
        self,
        data: List[Dict[str, Any]],
        columns: List[str] = None,
        delimiter: str = ",",
        include_header: bool = True
    ) -> str:
        """Veriyi CSV string olarak döndür"""
        if not data:
            return ""
            
        if columns is None:
            columns = list(data[0].keys())
            
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=columns,
            delimiter=delimiter,
            extrasaction='ignore'
        )
        
        if include_header:
            writer.writeheader()
            
        writer.writerows(data)
        
        return output.getvalue()
        
    def export_animals(self, animals: List[Dict], include_health: bool = True) -> str:
        """Hayvan verilerini CSV olarak aktar"""
        columns = [
            'id', 'external_id', 'name', 'species', 'breed',
            'birth_date', 'gender', 'weight', 'is_active'
        ]
        
        if include_health:
            columns.extend(['health_score', 'last_seen'])
            
        return self.export_to_file(animals, "animals", columns)
        
    def export_detections(self, detections: List[Dict]) -> str:
        """Tespit verilerini CSV olarak aktar"""
        columns = [
            'id', 'animal_id', 'camera_id', 'timestamp',
            'class_name', 'confidence', 'bbox_x', 'bbox_y',
            'bbox_width', 'bbox_height', 'track_id'
        ]
        
        return self.export_to_file(detections, "detections", columns)
        
    def export_behaviors(self, behaviors: List[Dict]) -> str:
        """Davranış verilerini CSV olarak aktar"""
        columns = [
            'id', 'animal_id', 'behavior_type', 'confidence',
            'start_time', 'end_time', 'duration_seconds', 'zone_id'
        ]
        
        return self.export_to_file(behaviors, "behaviors", columns)
        
    def export_health_records(self, records: List[Dict]) -> str:
        """Sağlık kayıtlarını CSV olarak aktar"""
        columns = [
            'id', 'animal_id', 'timestamp', 'health_score',
            'body_condition_score', 'lameness_score', 'notes'
        ]
        
        return self.export_to_file(records, "health_records", columns)


# Singleton instance
csv_exporter = CSVExporter()
