"""
Anormallik Tespit Modülü
Hayvan davranışlarında ve sağlığında anormallikleri tespit eder
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from scipy import stats


class AnomalyType(Enum):
    """Anormallik tipleri"""
    BEHAVIOR = "behavior"
    ACTIVITY = "activity"
    FEEDING = "feeding"
    MOVEMENT = "movement"
    HEALTH = "health"


class AnomalySeverity(Enum):
    """Anormallik şiddeti"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Anomaly:
    """Anormallik kaydı"""
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    score: float  # 0-1 (1 = kesinlikle anormal)
    description: str
    detected_at: datetime
    animal_id: str
    baseline_value: Optional[float] = None
    current_value: Optional[float] = None
    deviation: Optional[float] = None
    recommendations: List[str] = None


class AnomalyDetector:
    """
    Çok katmanlı anormallik tespit sistemi
    
    Yöntemler:
    - Statistical (z-score, IQR)
    - Threshold-based
    - Pattern-based
    - Trend-based
    """
    
    def __init__(
        self,
        z_score_threshold: float = 2.5,
        sensitivity: str = 'medium'  # 'low', 'medium', 'high'
    ):
        self.z_score_threshold = z_score_threshold
        self.sensitivity = sensitivity
        
        # Baseline verileri
        self.baselines: Dict[str, Dict] = {}
        
        # Tespit edilen anormallikler
        self.detected_anomalies: Dict[str, List[Anomaly]] = {}
        
        # Sensitivity'ye göre eşikleri ayarla
        self._set_sensitivity_thresholds()
    
    def _set_sensitivity_thresholds(self):
        """Sensitivity seviyesine göre eşikleri ayarla"""
        thresholds = {
            'low': {
                'z_score': 3.0,
                'iqr_multiplier': 2.0,
                'percent_change': 0.4
            },
            'medium': {
                'z_score': 2.5,
                'iqr_multiplier': 1.5,
                'percent_change': 0.3
            },
            'high': {
                'z_score': 2.0,
                'iqr_multiplier': 1.2,
                'percent_change': 0.2
            }
        }
        
        self.thresholds = thresholds[self.sensitivity]
    
    def update_baseline(
        self,
        animal_id: str,
        metric_name: str,
        values: List[float]
    ):
        """
        Baseline verilerini güncelle
        
        Args:
            animal_id: Hayvan kimliği
            metric_name: Metrik adı (örn: 'eating_duration', 'velocity')
            values: Geçmiş değerler
        """
        if animal_id not in self.baselines:
            self.baselines[animal_id] = {}
        
        if len(values) < 10:
            return  # Yeterli veri yok
        
        # İstatistik hesapla
        self.baselines[animal_id][metric_name] = {
            'mean': np.mean(values),
            'std': np.std(values),
            'median': np.median(values),
            'q25': np.percentile(values, 25),
            'q75': np.percentile(values, 75),
            'iqr': np.percentile(values, 75) - np.percentile(values, 25),
            'min': np.min(values),
            'max': np.max(values),
            'n_samples': len(values)
        }
    
    def detect_statistical_anomaly(
        self,
        animal_id: str,
        metric_name: str,
        current_value: float,
        method: str = 'z_score'
    ) -> Optional[Anomaly]:
        """
        İstatistiksel anormallik tespiti
        
        Args:
            animal_id: Hayvan kimliği
            metric_name: Metrik adı
            current_value: Mevcut değer
            method: 'z_score' veya 'iqr'
        
        Returns:
            Anomaly: Tespit edilen anormallik veya None
        """
        # Baseline kontrolü
        if animal_id not in self.baselines or \
           metric_name not in self.baselines[animal_id]:
            return None
        
        baseline = self.baselines[animal_id][metric_name]
        
        if method == 'z_score':
            # Z-score yöntemi
            mean = baseline['mean']
            std = baseline['std']
            
            if std == 0:
                return None
            
            z_score = abs((current_value - mean) / std)
            
            if z_score > self.thresholds['z_score']:
                severity = self._calculate_severity(z_score, 'z_score')
                
                return Anomaly(
                    anomaly_type=AnomalyType.ACTIVITY,
                    severity=severity,
                    score=min(z_score / 5.0, 1.0),
                    description=f'{metric_name} anormal: Z-score={z_score:.2f}',
                    detected_at=datetime.now(),
                    animal_id=animal_id,
                    baseline_value=mean,
                    current_value=current_value,
                    deviation=z_score,
                    recommendations=self._get_recommendations(metric_name, current_value, mean)
                )
        
        elif method == 'iqr':
            # IQR (Interquartile Range) yöntemi
            q25 = baseline['q25']
            q75 = baseline['q75']
            iqr = baseline['iqr']
            
            lower_bound = q25 - self.thresholds['iqr_multiplier'] * iqr
            upper_bound = q75 + self.thresholds['iqr_multiplier'] * iqr
            
            if current_value < lower_bound or current_value > upper_bound:
                deviation = min(
                    abs(current_value - lower_bound),
                    abs(current_value - upper_bound)
                ) / iqr
                
                severity = self._calculate_severity(deviation, 'iqr')
                
                return Anomaly(
                    anomaly_type=AnomalyType.ACTIVITY,
                    severity=severity,
                    score=min(deviation / 3.0, 1.0),
                    description=f'{metric_name} IQR dışında',
                    detected_at=datetime.now(),
                    animal_id=animal_id,
                    baseline_value=baseline['median'],
                    current_value=current_value,
                    deviation=deviation,
                    recommendations=self._get_recommendations(metric_name, current_value, baseline['median'])
                )
        
        return None
    
    def detect_threshold_anomaly(
        self,
        animal_id: str,
        metric_name: str,
        current_value: float,
        min_threshold: Optional[float] = None,
        max_threshold: Optional[float] = None
    ) -> Optional[Anomaly]:
        """
        Eşik tabanlı anormallik tespiti
        
        Args:
            animal_id: Hayvan kimliği
            metric_name: Metrik adı
            current_value: Mevcut değer
            min_threshold: Minimum eşik
            max_threshold: Maximum eşik
        """
        if min_threshold is not None and current_value < min_threshold:
            deviation = (min_threshold - current_value) / min_threshold
            severity = self._calculate_severity(deviation, 'threshold')
            
            return Anomaly(
                anomaly_type=AnomalyType.HEALTH,
                severity=severity,
                score=min(deviation, 1.0),
                description=f'{metric_name} minimum eşiğin altında',
                detected_at=datetime.now(),
                animal_id=animal_id,
                baseline_value=min_threshold,
                current_value=current_value,
                deviation=deviation,
                recommendations=[f'{metric_name} değerini artırın', 'Veteriner kontrolü önerilir']
            )
        
        if max_threshold is not None and current_value > max_threshold:
            deviation = (current_value - max_threshold) / max_threshold
            severity = self._calculate_severity(deviation, 'threshold')
            
            return Anomaly(
                anomaly_type=AnomalyType.HEALTH,
                severity=severity,
                score=min(deviation, 1.0),
                description=f'{metric_name} maximum eşiğin üstünde',
                detected_at=datetime.now(),
                animal_id=animal_id,
                baseline_value=max_threshold,
                current_value=current_value,
                deviation=deviation,
                recommendations=[f'{metric_name} değerini azaltın', 'Nedeni araştırın']
            )
        
        return None
    
    def detect_trend_anomaly(
        self,
        animal_id: str,
        metric_name: str,
        recent_values: List[float],
        window_size: int = 7
    ) -> Optional[Anomaly]:
        """
        Trend tabanlı anormallik tespiti
        
        Sürekli artış veya azalış trendlerini tespit eder
        """
        if len(recent_values) < window_size:
            return None
        
        # Son N değer
        values = recent_values[-window_size:]
        
        # Linear regression
        x = np.arange(len(values))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # R² değeri (trend gücü)
        r_squared = r_value ** 2
        
        # Güçlü trend ve istatistiksel olarak anlamlı mı?
        if r_squared > 0.7 and p_value < 0.05:
            # Slope'un büyüklüğü
            mean_value = np.mean(values)
            relative_slope = abs(slope) / mean_value if mean_value != 0 else 0
            
            if relative_slope > 0.1:  # %10+ değişim
                direction = "artış" if slope > 0 else "azalış"
                
                severity = self._calculate_severity(relative_slope * 10, 'trend')
                
                return Anomaly(
                    anomaly_type=AnomalyType.HEALTH,
                    severity=severity,
                    score=min(relative_slope * 5, 1.0),
                    description=f'{metric_name} sürekli {direction} trendi',
                    detected_at=datetime.now(),
                    animal_id=animal_id,
                    baseline_value=values[0],
                    current_value=values[-1],
                    deviation=relative_slope,
                    recommendations=[
                        f'{direction} trendini izleyin',
                        'Neden olabilecek faktörleri araştırın'
                    ]
                )
        
        return None
    
    def detect_behavioral_anomaly(
        self,
        animal_id: str,
        behavior_data: Dict
    ) -> List[Anomaly]:
        """
        Davranışsal anormallikleri tespit et
        
        Args:
            behavior_data: {
                'eating_duration': float,
                'drinking_count': int,
                'movement_ratio': float,
                'patterns': {...}
            }
        """
        anomalies = []
        
        # Yeme süresi
        eating_duration = behavior_data.get('eating_duration', 0)
        if eating_duration < 300:  # 5 dk'dan az
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.FEEDING,
                severity=AnomalySeverity.HIGH,
                score=0.8,
                description='Çok düşük yeme süresi',
                detected_at=datetime.now(),
                animal_id=animal_id,
                current_value=eating_duration,
                recommendations=[
                    'Diş ve ağız kontrolü',
                    'Yem kalitesini kontrol edin',
                    'Hastalık belirtileri araştırın'
                ]
            ))
        
        # İçme sıklığı
        drinking_count = behavior_data.get('drinking_count', 0)
        if drinking_count == 0:
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.FEEDING,
                severity=AnomalySeverity.CRITICAL,
                score=1.0,
                description='İçme aktivitesi yok',
                detected_at=datetime.now(),
                animal_id=animal_id,
                current_value=0,
                recommendations=[
                    'ACİL: Su erişimini kontrol edin',
                    'Dehidrasyon belirtileri araştırın',
                    'Veteriner kontrolü şart'
                ]
            ))
        
        # Hareket oranı
        movement_ratio = behavior_data.get('movement_ratio', 0)
        if movement_ratio < 0.05:  # %5'ten az aktif
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.MOVEMENT,
                severity=AnomalySeverity.MEDIUM,
                score=0.7,
                description='Aşırı hareketsizlik',
                detected_at=datetime.now(),
                animal_id=animal_id,
                current_value=movement_ratio,
                recommendations=[
                    'Topallama kontrolü',
                    'Ağrı belirtileri',
                    'Yorgunluk nedenleri'
                ]
            ))
        
        # Anormal paternler
        patterns = behavior_data.get('patterns', {})
        if patterns.get('is_pacing'):
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.BEHAVIOR,
                severity=AnomalySeverity.MEDIUM,
                score=0.6,
                description='Gidip gelme davranışı (pacing)',
                detected_at=datetime.now(),
                animal_id=animal_id,
                recommendations=[
                    'Stres faktörlerini azaltın',
                    'Ortam zenginleştirme',
                    'Sıkıntı nedenleri araştırın'
                ]
            ))
        
        if patterns.get('is_circling'):
            anomalies.append(Anomaly(
                anomaly_type=AnomalyType.BEHAVIOR,
                severity=AnomalySeverity.HIGH,
                score=0.85,
                description='Dairesel hareket (circling)',
                detected_at=datetime.now(),
                animal_id=animal_id,
                recommendations=[
                    'Nörolojik kontrol',
                    'Kulak enfeksiyonu kontrolü',
                    'Veteriner muayenesi acil'
                ]
            ))
        
        return anomalies
    
    def _calculate_severity(
        self,
        deviation: float,
        method: str
    ) -> AnomalySeverity:
        """Sapma büyüklüğüne göre şiddet hesapla"""
        if method == 'z_score':
            if deviation > 4.0:
                return AnomalySeverity.CRITICAL
            elif deviation > 3.0:
                return AnomalySeverity.HIGH
            elif deviation > 2.5:
                return AnomalySeverity.MEDIUM
            else:
                return AnomalySeverity.LOW
        
        elif method == 'iqr':
            if deviation > 3.0:
                return AnomalySeverity.CRITICAL
            elif deviation > 2.0:
                return AnomalySeverity.HIGH
            elif deviation > 1.5:
                return AnomalySeverity.MEDIUM
            else:
                return AnomalySeverity.LOW
        
        elif method == 'threshold' or method == 'trend':
            if deviation > 0.5:
                return AnomalySeverity.CRITICAL
            elif deviation > 0.3:
                return AnomalySeverity.HIGH
            elif deviation > 0.2:
                return AnomalySeverity.MEDIUM
            else:
                return AnomalySeverity.LOW
        
        return AnomalySeverity.LOW
    
    def _get_recommendations(
        self,
        metric_name: str,
        current: float,
        baseline: float
    ) -> List[str]:
        """Metrik ve sapma yönüne göre öneriler"""
        recommendations = []
        
        if current < baseline:
            recommendations.append(f'{metric_name} normalin altında')
            if 'eating' in metric_name.lower():
                recommendations.extend([
                    'Diş ve ağız sağlığı kontrolü',
                    'Yem kalitesini gözden geçirin'
                ])
            elif 'movement' in metric_name.lower():
                recommendations.extend([
                    'Topallama tespiti yapın',
                    'Eklem sağlığını kontrol edin'
                ])
        else:
            recommendations.append(f'{metric_name} normalin üstünde')
            if 'resting' in metric_name.lower():
                recommendations.extend([
                    'Aşırı yorgunluk nedenleri',
                    'Hastalık belirtileri araştırın'
                ])
        
        recommendations.append('Veteriner kontrolü önerilir')
        
        return recommendations
    
    def get_anomaly_summary(
        self,
        animal_id: str,
        hours: int = 24
    ) -> Dict:
        """
        Son N saatteki anormallik özeti
        
        Returns:
            Dict: {
                'total_count': int,
                'by_severity': {...},
                'by_type': {...},
                'recent_anomalies': [...]
            }
        """
        if animal_id not in self.detected_anomalies:
            return {
                'total_count': 0,
                'by_severity': {},
                'by_type': {},
                'recent_anomalies': []
            }
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            a for a in self.detected_anomalies[animal_id]
            if a.detected_at >= cutoff
        ]
        
        # Şiddete göre grup
        by_severity = {}
        for anomaly in recent:
            severity = anomaly.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Tipe göre grup
        by_type = {}
        for anomaly in recent:
            atype = anomaly.anomaly_type.value
            by_type[atype] = by_type.get(atype, 0) + 1
        
        return {
            'total_count': len(recent),
            'by_severity': by_severity,
            'by_type': by_type,
            'recent_anomalies': [
                {
                    'type': a.anomaly_type.value,
                    'severity': a.severity.value,
                    'description': a.description,
                    'score': a.score,
                    'detected_at': a.detected_at.isoformat()
                }
                for a in recent[-10:]  # Son 10
            ]
        }
