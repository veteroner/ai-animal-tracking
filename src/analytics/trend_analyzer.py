"""
Trend Analizi Modülü
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np
from collections import defaultdict


class TrendDirection(Enum):
    """Trend yönü"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"


class TrendStrength(Enum):
    """Trend gücü"""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


@dataclass
class TrendResult:
    """Trend analizi sonucu"""
    metric_name: str
    direction: TrendDirection
    strength: TrendStrength
    change_percent: float
    start_value: float
    end_value: float
    average_value: float
    min_value: float
    max_value: float
    data_points: int
    anomalies: List[Dict[str, Any]] = None
    prediction: Optional[float] = None
    
    def __post_init__(self):
        if self.anomalies is None:
            self.anomalies = []


class TrendAnalyzer:
    """Trend analiz sınıfı"""
    
    def __init__(self, min_data_points: int = 5):
        self.min_data_points = min_data_points
        self.historical_data: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        
    def add_data_point(self, metric_name: str, value: float, timestamp: datetime = None) -> None:
        """Veri noktası ekle"""
        if timestamp is None:
            timestamp = datetime.now()
        self.historical_data[metric_name].append((timestamp, value))
        
    def analyze_trend(self, metric_name: str, period_days: int = 7) -> Optional[TrendResult]:
        """Belirli bir metrik için trend analizi yap"""
        data = self.historical_data.get(metric_name, [])
        
        if len(data) < self.min_data_points:
            return None
            
        # Belirtilen periyottaki verileri filtrele
        cutoff_date = datetime.now() - timedelta(days=period_days)
        filtered_data = [(ts, val) for ts, val in data if ts >= cutoff_date]
        
        if len(filtered_data) < self.min_data_points:
            filtered_data = data[-self.min_data_points:]
            
        values = [val for _, val in filtered_data]
        
        # İstatistikler
        start_value = values[0]
        end_value = values[-1]
        average_value = np.mean(values)
        min_value = min(values)
        max_value = max(values)
        
        # Değişim yüzdesi
        if start_value != 0:
            change_percent = ((end_value - start_value) / start_value) * 100
        else:
            change_percent = 0 if end_value == 0 else 100
            
        # Trend yönü ve gücü
        direction, strength = self._calculate_trend(values)
        
        # Anomali tespiti
        anomalies = self._detect_anomalies(filtered_data, values)
        
        # Basit tahmin
        prediction = self._simple_prediction(values)
        
        return TrendResult(
            metric_name=metric_name,
            direction=direction,
            strength=strength,
            change_percent=change_percent,
            start_value=start_value,
            end_value=end_value,
            average_value=average_value,
            min_value=min_value,
            max_value=max_value,
            data_points=len(filtered_data),
            anomalies=anomalies,
            prediction=prediction
        )
        
    def _calculate_trend(self, values: List[float]) -> Tuple[TrendDirection, TrendStrength]:
        """Trend yönü ve gücünü hesapla"""
        if len(values) < 2:
            return TrendDirection.STABLE, TrendStrength.NONE
            
        # Basit lineer regresyon
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        
        # Standart sapma ile normalize et
        std = np.std(values) if np.std(values) > 0 else 1
        normalized_slope = slope / std
        
        # Yön belirleme
        if abs(normalized_slope) < 0.1:
            direction = TrendDirection.STABLE
        elif normalized_slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
            
        # Dalgalanma kontrolü
        diffs = np.diff(values)
        sign_changes = np.sum(np.abs(np.diff(np.sign(diffs)))) / 2
        if sign_changes > len(values) * 0.3:
            direction = TrendDirection.FLUCTUATING
            
        # Güç belirleme
        abs_slope = abs(normalized_slope)
        if abs_slope > 0.5:
            strength = TrendStrength.STRONG
        elif abs_slope > 0.2:
            strength = TrendStrength.MODERATE
        elif abs_slope > 0.1:
            strength = TrendStrength.WEAK
        else:
            strength = TrendStrength.NONE
            
        return direction, strength
        
    def _detect_anomalies(self, data: List[Tuple[datetime, float]], values: List[float]) -> List[Dict[str, Any]]:
        """Anomalileri tespit et"""
        anomalies = []
        
        if len(values) < 3:
            return anomalies
            
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return anomalies
            
        # Z-score ile anomali tespiti
        for i, (timestamp, value) in enumerate(data):
            z_score = (value - mean) / std
            if abs(z_score) > 2:  # 2 standart sapma
                anomalies.append({
                    'timestamp': timestamp.isoformat(),
                    'value': value,
                    'z_score': z_score,
                    'type': 'high' if z_score > 0 else 'low'
                })
                
        return anomalies
        
    def _simple_prediction(self, values: List[float], steps: int = 1) -> Optional[float]:
        """Basit lineer tahmin"""
        if len(values) < 2:
            return None
            
        x = np.arange(len(values))
        slope, intercept = np.polyfit(x, values, 1)
        
        return slope * (len(values) + steps - 1) + intercept
        
    def analyze_multiple_metrics(self, metric_names: List[str], period_days: int = 7) -> Dict[str, TrendResult]:
        """Birden fazla metrik için trend analizi"""
        results = {}
        for metric in metric_names:
            result = self.analyze_trend(metric, period_days)
            if result:
                results[metric] = result
        return results
        
    def get_correlation(self, metric1: str, metric2: str) -> Optional[float]:
        """İki metrik arasındaki korelasyonu hesapla"""
        data1 = self.historical_data.get(metric1, [])
        data2 = self.historical_data.get(metric2, [])
        
        if len(data1) < self.min_data_points or len(data2) < self.min_data_points:
            return None
            
        # Ortak zaman dilimlerini bul (basitleştirilmiş)
        values1 = [val for _, val in data1[-min(len(data1), len(data2)):]]
        values2 = [val for _, val in data2[-min(len(data1), len(data2)):]]
        
        if len(values1) != len(values2):
            min_len = min(len(values1), len(values2))
            values1 = values1[:min_len]
            values2 = values2[:min_len]
            
        return float(np.corrcoef(values1, values2)[0, 1])
        
    def detect_seasonality(self, metric_name: str, period_hours: int = 24) -> Dict[str, Any]:
        """Mevsimsellik/periyodik patern tespiti"""
        data = self.historical_data.get(metric_name, [])
        
        if len(data) < period_hours * 2:
            return {'has_seasonality': False, 'reason': 'Yetersiz veri'}
            
        # Saatlik ortalamalar
        hourly_values = defaultdict(list)
        for timestamp, value in data:
            hour = timestamp.hour
            hourly_values[hour].append(value)
            
        hourly_averages = {hour: np.mean(vals) for hour, vals in hourly_values.items()}
        
        # Varyans analizi
        overall_mean = np.mean([val for _, val in data])
        between_variance = np.var(list(hourly_averages.values()))
        within_variance = np.mean([np.var(vals) if len(vals) > 1 else 0 
                                   for vals in hourly_values.values()])
        
        # F-ratio benzeri metrik
        if within_variance > 0:
            seasonality_score = between_variance / within_variance
        else:
            seasonality_score = 0
            
        return {
            'has_seasonality': seasonality_score > 1.5,
            'seasonality_score': seasonality_score,
            'hourly_pattern': hourly_averages,
            'peak_hour': max(hourly_averages, key=hourly_averages.get) if hourly_averages else None,
            'low_hour': min(hourly_averages, key=hourly_averages.get) if hourly_averages else None
        }
        
    def compare_periods(self, metric_name: str, period1_days: Tuple[int, int], 
                        period2_days: Tuple[int, int]) -> Dict[str, Any]:
        """İki dönem arasında karşılaştırma yap"""
        data = self.historical_data.get(metric_name, [])
        
        now = datetime.now()
        period1_start = now - timedelta(days=period1_days[0])
        period1_end = now - timedelta(days=period1_days[1])
        period2_start = now - timedelta(days=period2_days[0])
        period2_end = now - timedelta(days=period2_days[1])
        
        period1_values = [val for ts, val in data if period1_start <= ts <= period1_end]
        period2_values = [val for ts, val in data if period2_start <= ts <= period2_end]
        
        if not period1_values or not period2_values:
            return {'error': 'Yetersiz veri'}
            
        avg1 = np.mean(period1_values)
        avg2 = np.mean(period2_values)
        
        if avg1 != 0:
            change_percent = ((avg2 - avg1) / avg1) * 100
        else:
            change_percent = 0
            
        return {
            'period1_average': avg1,
            'period2_average': avg2,
            'change_percent': change_percent,
            'period1_data_points': len(period1_values),
            'period2_data_points': len(period2_values),
            'improved': avg2 > avg1
        }
        
    def clear_old_data(self, days_to_keep: int = 30) -> int:
        """Eski verileri temizle"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        total_removed = 0
        
        for metric_name in self.historical_data:
            original_count = len(self.historical_data[metric_name])
            self.historical_data[metric_name] = [
                (ts, val) for ts, val in self.historical_data[metric_name]
                if ts >= cutoff_date
            ]
            total_removed += original_count - len(self.historical_data[metric_name])
            
        return total_removed
