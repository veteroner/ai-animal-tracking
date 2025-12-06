"""
Rapor Oluşturma Modülü
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import os


class ReportType(Enum):
    """Rapor türleri"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"
    HEALTH = "health"
    BEHAVIOR = "behavior"
    ACTIVITY = "activity"


class ReportFormat(Enum):
    """Rapor formatları"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"


@dataclass
class ReportConfig:
    """Rapor konfigürasyonu"""
    report_type: ReportType
    format: ReportFormat
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    animal_ids: Optional[List[str]] = None
    include_charts: bool = True
    include_summary: bool = True


@dataclass
class ReportSection:
    """Rapor bölümü"""
    title: str
    content: Any
    section_type: str = "text"  # text, table, chart, summary


class ReportGenerator:
    """Rapor oluşturucu sınıfı"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_report(self, config: ReportConfig, data: Dict[str, Any]) -> str:
        """Rapor oluştur ve dosya yolunu döndür"""
        report_data = self._build_report(config, data)
        
        if config.format == ReportFormat.JSON:
            return self._generate_json_report(report_data, config)
        elif config.format == ReportFormat.CSV:
            return self._generate_csv_report(report_data, config)
        elif config.format == ReportFormat.HTML:
            return self._generate_html_report(report_data, config)
        else:
            raise ValueError(f"Desteklenmeyen format: {config.format}")
            
    def _build_report(self, config: ReportConfig, data: Dict[str, Any]) -> Dict[str, Any]:
        """Rapor verisi oluştur"""
        report = {
            'metadata': {
                'report_type': config.report_type.value,
                'generated_at': datetime.now().isoformat(),
                'start_date': config.start_date.isoformat() if config.start_date else None,
                'end_date': config.end_date.isoformat() if config.end_date else None
            },
            'sections': []
        }
        
        # Özet bölümü
        if config.include_summary:
            summary = self._generate_summary(data)
            report['sections'].append({
                'title': 'Özet',
                'type': 'summary',
                'content': summary
            })
            
        # Rapor türüne göre bölümler ekle
        if config.report_type == ReportType.DAILY:
            report['sections'].extend(self._generate_daily_sections(data))
        elif config.report_type == ReportType.WEEKLY:
            report['sections'].extend(self._generate_weekly_sections(data))
        elif config.report_type == ReportType.HEALTH:
            report['sections'].extend(self._generate_health_sections(data))
        elif config.report_type == ReportType.BEHAVIOR:
            report['sections'].extend(self._generate_behavior_sections(data))
        elif config.report_type == ReportType.ACTIVITY:
            report['sections'].extend(self._generate_activity_sections(data))
            
        return report
        
    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Özet istatistikleri oluştur"""
        return {
            'total_animals': data.get('total_animals', 0),
            'total_detections': data.get('total_detections', 0),
            'active_cameras': data.get('active_cameras', 0),
            'alerts_count': data.get('alerts_count', 0),
            'average_health_score': data.get('average_health_score', 0),
            'most_common_behavior': data.get('most_common_behavior', 'N/A')
        }
        
    def _generate_daily_sections(self, data: Dict[str, Any]) -> List[Dict]:
        """Günlük rapor bölümleri"""
        sections = []
        
        # Saatlik aktivite
        sections.append({
            'title': 'Saatlik Aktivite Dağılımı',
            'type': 'chart',
            'chart_type': 'bar',
            'content': data.get('hourly_activity', {})
        })
        
        # Hayvan bazlı özet
        sections.append({
            'title': 'Hayvan Aktivite Özeti',
            'type': 'table',
            'columns': ['Hayvan ID', 'Tespit Sayısı', 'Aktif Süre', 'Ana Davranış'],
            'content': data.get('animal_summary', [])
        })
        
        # Uyarılar
        sections.append({
            'title': 'Günün Uyarıları',
            'type': 'list',
            'content': data.get('daily_alerts', [])
        })
        
        return sections
        
    def _generate_weekly_sections(self, data: Dict[str, Any]) -> List[Dict]:
        """Haftalık rapor bölümleri"""
        sections = []
        
        # Günlük trend
        sections.append({
            'title': 'Haftalık Aktivite Trendi',
            'type': 'chart',
            'chart_type': 'line',
            'content': data.get('daily_trend', {})
        })
        
        # Davranış analizi
        sections.append({
            'title': 'Haftalık Davranış Analizi',
            'type': 'chart',
            'chart_type': 'pie',
            'content': data.get('behavior_distribution', {})
        })
        
        # Sağlık değişimleri
        sections.append({
            'title': 'Sağlık Değişimleri',
            'type': 'table',
            'columns': ['Hayvan ID', 'Başlangıç Skoru', 'Bitiş Skoru', 'Değişim'],
            'content': data.get('health_changes', [])
        })
        
        return sections
        
    def _generate_health_sections(self, data: Dict[str, Any]) -> List[Dict]:
        """Sağlık raporu bölümleri"""
        sections = []
        
        # Genel sağlık durumu
        sections.append({
            'title': 'Genel Sağlık Durumu',
            'type': 'chart',
            'chart_type': 'gauge',
            'content': data.get('overall_health', {})
        })
        
        # Risk altındaki hayvanlar
        sections.append({
            'title': 'Risk Altındaki Hayvanlar',
            'type': 'table',
            'columns': ['Hayvan ID', 'Sağlık Skoru', 'Risk Faktörleri', 'Öneri'],
            'content': data.get('at_risk_animals', [])
        })
        
        # Anormallikler
        sections.append({
            'title': 'Tespit Edilen Anormallikler',
            'type': 'list',
            'content': data.get('anomalies', [])
        })
        
        return sections
        
    def _generate_behavior_sections(self, data: Dict[str, Any]) -> List[Dict]:
        """Davranış raporu bölümleri"""
        sections = []
        
        # Davranış dağılımı
        sections.append({
            'title': 'Davranış Dağılımı',
            'type': 'chart',
            'chart_type': 'pie',
            'content': data.get('behavior_distribution', {})
        })
        
        # Davranış zaman analizi
        sections.append({
            'title': 'Zaman Bazlı Davranış Analizi',
            'type': 'chart',
            'chart_type': 'heatmap',
            'content': data.get('behavior_timeline', {})
        })
        
        # Anormal davranışlar
        sections.append({
            'title': 'Anormal Davranış Tespitleri',
            'type': 'table',
            'columns': ['Tarih/Saat', 'Hayvan ID', 'Davranış', 'Açıklama'],
            'content': data.get('abnormal_behaviors', [])
        })
        
        return sections
        
    def _generate_activity_sections(self, data: Dict[str, Any]) -> List[Dict]:
        """Aktivite raporu bölümleri"""
        sections = []
        
        # Aktivite haritası
        sections.append({
            'title': 'Aktivite Haritası',
            'type': 'chart',
            'chart_type': 'heatmap',
            'content': data.get('activity_map', {})
        })
        
        # Hareket analizi
        sections.append({
            'title': 'Hareket Analizi',
            'type': 'table',
            'columns': ['Hayvan ID', 'Toplam Mesafe', 'Ortalama Hız', 'Aktif Süre'],
            'content': data.get('movement_stats', [])
        })
        
        return sections
        
    def _generate_json_report(self, report_data: Dict, config: ReportConfig) -> str:
        """JSON rapor oluştur"""
        filename = self._generate_filename(config, 'json')
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
            
        return filepath
        
    def _generate_csv_report(self, report_data: Dict, config: ReportConfig) -> str:
        """CSV rapor oluştur"""
        filename = self._generate_filename(config, 'csv')
        filepath = os.path.join(self.output_dir, filename)
        
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Metadata
            writer.writerow(['Rapor Türü', report_data['metadata']['report_type']])
            writer.writerow(['Oluşturulma', report_data['metadata']['generated_at']])
            writer.writerow([])
            
            # Bölümler
            for section in report_data['sections']:
                writer.writerow([section['title']])
                if section['type'] == 'table' and 'columns' in section:
                    writer.writerow(section['columns'])
                    for row in section.get('content', []):
                        writer.writerow(row if isinstance(row, list) else list(row.values()))
                writer.writerow([])
                
        return filepath
        
    def _generate_html_report(self, report_data: Dict, config: ReportConfig) -> str:
        """HTML rapor oluştur"""
        filename = self._generate_filename(config, 'html')
        filepath = os.path.join(self.output_dir, filename)
        
        html_content = self._build_html_template(report_data)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        return filepath
        
    def _build_html_template(self, report_data: Dict) -> str:
        """HTML şablonu oluştur"""
        html = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hayvan Takip Raporu</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .metadata { background: #ecf0f1; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #3498db; color: white; }
        tr:hover { background: #f5f5f5; }
        .summary-card { display: inline-block; background: #3498db; color: white; padding: 20px; margin: 10px; border-radius: 8px; min-width: 150px; text-align: center; }
        .summary-card h3 { margin: 0; font-size: 24px; }
        .summary-card p { margin: 5px 0 0 0; opacity: 0.9; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }
        .alert-warning { background: #f39c12; color: white; }
        .alert-danger { background: #e74c3c; color: white; }
        .alert-info { background: #3498db; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🐄 Hayvan Takip Sistemi Raporu</h1>
        <div class="metadata">
            <strong>Rapor Türü:</strong> {report_type} | 
            <strong>Oluşturulma:</strong> {generated_at}
        </div>
""".format(
            report_type=report_data['metadata']['report_type'],
            generated_at=report_data['metadata']['generated_at']
        )
        
        # Bölümleri ekle
        for section in report_data['sections']:
            html += f"<h2>{section['title']}</h2>"
            
            if section['type'] == 'summary':
                html += '<div class="summary-cards">'
                for key, value in section['content'].items():
                    html += f'<div class="summary-card"><h3>{value}</h3><p>{key}</p></div>'
                html += '</div>'
                
            elif section['type'] == 'table':
                html += '<table><thead><tr>'
                for col in section.get('columns', []):
                    html += f'<th>{col}</th>'
                html += '</tr></thead><tbody>'
                for row in section.get('content', []):
                    html += '<tr>'
                    if isinstance(row, list):
                        for cell in row:
                            html += f'<td>{cell}</td>'
                    elif isinstance(row, dict):
                        for cell in row.values():
                            html += f'<td>{cell}</td>'
                    html += '</tr>'
                html += '</tbody></table>'
                
            elif section['type'] == 'list':
                html += '<ul>'
                for item in section.get('content', []):
                    html += f'<li>{item}</li>'
                html += '</ul>'
                
        html += """
    </div>
</body>
</html>
"""
        return html
        
    def _generate_filename(self, config: ReportConfig, extension: str) -> str:
        """Dosya adı oluştur"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"report_{config.report_type.value}_{timestamp}.{extension}"
        
    def generate_daily_report(self, data: Dict[str, Any], format: ReportFormat = ReportFormat.HTML) -> str:
        """Günlük rapor oluştur (kısa yol)"""
        config = ReportConfig(
            report_type=ReportType.DAILY,
            format=format,
            start_date=datetime.now().replace(hour=0, minute=0, second=0),
            end_date=datetime.now()
        )
        return self.generate_report(config, data)
        
    def generate_weekly_report(self, data: Dict[str, Any], format: ReportFormat = ReportFormat.HTML) -> str:
        """Haftalık rapor oluştur (kısa yol)"""
        config = ReportConfig(
            report_type=ReportType.WEEKLY,
            format=format,
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now()
        )
        return self.generate_report(config, data)
