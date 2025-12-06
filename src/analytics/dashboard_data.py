"""
Dashboard Veri Sağlayıcı Modülü
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum


class WidgetType(Enum):
    """Dashboard widget türleri"""
    STAT_CARD = "stat_card"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    TABLE = "table"
    MAP = "map"
    LIVE_FEED = "live_feed"
    ALERT_LIST = "alert_list"
    GAUGE = "gauge"
    HEATMAP = "heatmap"


@dataclass
class StatCard:
    """İstatistik kartı verisi"""
    title: str
    value: Any
    unit: str = ""
    change: float = 0.0
    change_period: str = "son 24 saat"
    icon: str = ""
    color: str = "blue"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ChartData:
    """Grafik verisi"""
    title: str
    chart_type: str
    labels: List[str]
    datasets: List[Dict[str, Any]]
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}
            
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AlertItem:
    """Uyarı öğesi"""
    id: str
    title: str
    message: str
    severity: str  # info, warning, error, critical
    timestamp: datetime
    animal_id: Optional[str] = None
    is_read: bool = False
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class DashboardDataProvider:
    """Dashboard veri sağlayıcı sınıfı"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(seconds=30)
        
    def get_overview_stats(self, data_source: Dict[str, Any] = None) -> List[StatCard]:
        """Genel bakış istatistiklerini getir"""
        if data_source is None:
            data_source = {}
            
        stats = [
            StatCard(
                title="Toplam Hayvan",
                value=data_source.get('total_animals', 0),
                icon="🐄",
                color="blue"
            ),
            StatCard(
                title="Aktif Kamera",
                value=data_source.get('active_cameras', 0),
                icon="📹",
                color="green"
            ),
            StatCard(
                title="Bugünkü Tespitler",
                value=data_source.get('detections_today', 0),
                change=data_source.get('detection_change', 0),
                icon="🔍",
                color="purple"
            ),
            StatCard(
                title="Ortalama Sağlık",
                value=f"{data_source.get('avg_health_score', 0):.1f}",
                unit="%",
                change=data_source.get('health_change', 0),
                icon="❤️",
                color="red"
            ),
            StatCard(
                title="Aktif Uyarılar",
                value=data_source.get('active_alerts', 0),
                icon="⚠️",
                color="orange"
            ),
            StatCard(
                title="Sistem FPS",
                value=data_source.get('current_fps', 0),
                unit="fps",
                icon="⚡",
                color="cyan"
            )
        ]
        
        return stats
        
    def get_activity_chart(self, hourly_data: Dict[int, int] = None) -> ChartData:
        """Saatlik aktivite grafiği"""
        if hourly_data is None:
            hourly_data = {i: 0 for i in range(24)}
            
        labels = [f"{i:02d}:00" for i in range(24)]
        values = [hourly_data.get(i, 0) for i in range(24)]
        
        return ChartData(
            title="Saatlik Aktivite",
            chart_type="line",
            labels=labels,
            datasets=[{
                'label': 'Tespit Sayısı',
                'data': values,
                'borderColor': '#3498db',
                'backgroundColor': 'rgba(52, 152, 219, 0.1)',
                'fill': True
            }],
            options={
                'responsive': True,
                'plugins': {
                    'legend': {'display': False}
                }
            }
        )
        
    def get_behavior_distribution(self, behavior_counts: Dict[str, int] = None) -> ChartData:
        """Davranış dağılımı pasta grafiği"""
        if behavior_counts is None:
            behavior_counts = {}
            
        # Türkçe davranış etiketleri
        behavior_labels = {
            'eating': 'Yeme',
            'walking': 'Yürüme',
            'resting': 'Dinlenme',
            'drinking': 'Su İçme',
            'running': 'Koşma',
            'standing': 'Ayakta Durma',
            'lying': 'Yatma',
            'grazing': 'Otlama'
        }
        
        labels = [behavior_labels.get(k, k) for k in behavior_counts.keys()]
        values = list(behavior_counts.values())
        
        colors = [
            '#3498db', '#e74c3c', '#2ecc71', '#f39c12',
            '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
        ]
        
        return ChartData(
            title="Davranış Dağılımı",
            chart_type="pie",
            labels=labels,
            datasets=[{
                'data': values,
                'backgroundColor': colors[:len(values)]
            }]
        )
        
    def get_health_overview(self, health_data: List[Dict] = None) -> ChartData:
        """Sağlık durumu bar grafiği"""
        if health_data is None:
            health_data = []
            
        # Sağlık skorlarını kategorilere ayır
        categories = {
            'Mükemmel (90-100)': 0,
            'İyi (70-89)': 0,
            'Orta (50-69)': 0,
            'Dikkat (30-49)': 0,
            'Kritik (0-29)': 0
        }
        
        for animal in health_data:
            score = animal.get('health_score', 0)
            if score >= 90:
                categories['Mükemmel (90-100)'] += 1
            elif score >= 70:
                categories['İyi (70-89)'] += 1
            elif score >= 50:
                categories['Orta (50-69)'] += 1
            elif score >= 30:
                categories['Dikkat (30-49)'] += 1
            else:
                categories['Kritik (0-29)'] += 1
                
        return ChartData(
            title="Sağlık Durumu Dağılımı",
            chart_type="bar",
            labels=list(categories.keys()),
            datasets=[{
                'label': 'Hayvan Sayısı',
                'data': list(categories.values()),
                'backgroundColor': ['#27ae60', '#2ecc71', '#f1c40f', '#e67e22', '#e74c3c']
            }]
        )
        
    def get_weekly_trend(self, daily_data: Dict[str, int] = None) -> ChartData:
        """Haftalık trend grafiği"""
        if daily_data is None:
            daily_data = {}
            
        # Son 7 gün
        dates = []
        values = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            dates.append(date[-5:])  # MM-DD formatı
            values.append(daily_data.get(date, 0))
            
        return ChartData(
            title="Haftalık Tespit Trendi",
            chart_type="line",
            labels=dates,
            datasets=[{
                'label': 'Günlük Tespit',
                'data': values,
                'borderColor': '#9b59b6',
                'tension': 0.4
            }]
        )
        
    def get_animal_table_data(self, animals: List[Dict] = None) -> Dict[str, Any]:
        """Hayvan tablosu verisi"""
        if animals is None:
            animals = []
            
        columns = [
            {'key': 'id', 'label': 'ID', 'sortable': True},
            {'key': 'name', 'label': 'İsim', 'sortable': True},
            {'key': 'species', 'label': 'Tür', 'sortable': True},
            {'key': 'health_score', 'label': 'Sağlık', 'sortable': True},
            {'key': 'current_behavior', 'label': 'Davranış', 'sortable': False},
            {'key': 'last_seen', 'label': 'Son Görülme', 'sortable': True},
            {'key': 'status', 'label': 'Durum', 'sortable': True}
        ]
        
        rows = []
        for animal in animals:
            rows.append({
                'id': animal.get('id', ''),
                'name': animal.get('name', 'İsimsiz'),
                'species': animal.get('species', 'Bilinmiyor'),
                'health_score': animal.get('health_score', 0),
                'current_behavior': animal.get('current_behavior', '-'),
                'last_seen': animal.get('last_seen', '-'),
                'status': animal.get('status', 'active')
            })
            
        return {
            'title': 'Hayvan Listesi',
            'columns': columns,
            'rows': rows,
            'total': len(rows)
        }
        
    def get_recent_alerts(self, alerts: List[AlertItem] = None, limit: int = 10) -> List[Dict]:
        """Son uyarıları getir"""
        if alerts is None:
            return []
            
        sorted_alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        return [alert.to_dict() for alert in sorted_alerts[:limit]]
        
    def get_camera_status(self, cameras: List[Dict] = None) -> List[Dict]:
        """Kamera durumlarını getir"""
        if cameras is None:
            cameras = []
            
        return [{
            'id': cam.get('id', ''),
            'name': cam.get('name', 'Kamera'),
            'status': cam.get('status', 'offline'),
            'fps': cam.get('fps', 0),
            'resolution': cam.get('resolution', ''),
            'last_frame': cam.get('last_frame', None)
        } for cam in cameras]
        
    def get_zone_activity(self, zone_data: Dict[str, int] = None) -> ChartData:
        """Bölge aktivite verisi"""
        if zone_data is None:
            zone_data = {}
            
        return ChartData(
            title="Bölge Aktivitesi",
            chart_type="bar",
            labels=list(zone_data.keys()),
            datasets=[{
                'label': 'Ziyaret Sayısı',
                'data': list(zone_data.values()),
                'backgroundColor': '#3498db'
            }]
        )
        
    def get_full_dashboard(self, data_source: Dict[str, Any] = None) -> Dict[str, Any]:
        """Tam dashboard verisi"""
        if data_source is None:
            data_source = {}
            
        return {
            'stats': [s.to_dict() for s in self.get_overview_stats(data_source)],
            'activity_chart': self.get_activity_chart(
                data_source.get('hourly_activity')
            ).to_dict(),
            'behavior_chart': self.get_behavior_distribution(
                data_source.get('behavior_counts')
            ).to_dict(),
            'health_chart': self.get_health_overview(
                data_source.get('health_data')
            ).to_dict(),
            'weekly_trend': self.get_weekly_trend(
                data_source.get('daily_detections')
            ).to_dict(),
            'animal_table': self.get_animal_table_data(
                data_source.get('animals')
            ),
            'recent_alerts': self.get_recent_alerts(
                data_source.get('alerts')
            ),
            'camera_status': self.get_camera_status(
                data_source.get('cameras')
            ),
            'last_updated': datetime.now().isoformat()
        }
        
    def get_live_stats(self, tracking_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Canlı istatistikler (WebSocket için)"""
        if tracking_data is None:
            tracking_data = {}
            
        return {
            'timestamp': datetime.now().isoformat(),
            'fps': tracking_data.get('fps', 0),
            'active_tracks': tracking_data.get('active_tracks', 0),
            'detections_per_second': tracking_data.get('dps', 0),
            'processing_time_ms': tracking_data.get('processing_time', 0),
            'memory_usage_mb': tracking_data.get('memory_mb', 0),
            'gpu_usage_percent': tracking_data.get('gpu_percent', 0)
        }
