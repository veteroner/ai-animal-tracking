"""
Doğum Tahmin Modülü
===================
Gebelik takibi ve doğum tarihini tahmin eder.

Özellikler:
- Beklenen doğum tarihi hesaplama
- Pre-partum davranış analizi
- Doğum öncesi uyarılar (24 saat, 12 saat, 6 saat)
"""

import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class PregnancyStatus(Enum):
    """Gebelik durumu"""
    ACTIVE = "aktif"
    DELIVERED = "doğum_yaptı"
    ABORTED = "düşük"
    CANCELLED = "iptal"


class BreedingMethod(Enum):
    """Çiftleştirme yöntemi"""
    NATURAL = "doğal"
    AI = "suni_tohumlama"
    ET = "embriyo_transferi"


class ConfirmationMethod(Enum):
    """Gebelik onay yöntemi"""
    MANUAL = "manual"
    ULTRASOUND = "ultrasound"
    BLOOD_TEST = "blood_test"
    OBSERVATION = "observation"


@dataclass
class Pregnancy:
    """Gebelik kaydı veri yapısı"""
    id: str
    animal_id: str
    breeding_date: date
    expected_birth_date: date
    actual_birth_date: Optional[date] = None
    sire_id: Optional[str] = None
    breeding_method: BreedingMethod = BreedingMethod.NATURAL
    pregnancy_confirmed: bool = False
    confirmation_date: Optional[date] = None
    confirmation_method: Optional[ConfirmationMethod] = None
    status: PregnancyStatus = PregnancyStatus.ACTIVE
    notes: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class PrePartumIndicators:
    """Doğum öncesi göstergeler"""
    restlessness_score: float = 0.0      # Huzursuzluk (yatıp kalkma)
    isolation_score: float = 0.0          # Sürüden ayrılma
    tail_raising_frequency: int = 0       # Kuyruk kaldırma sıklığı
    nesting_behavior: bool = False        # Yuva yapma (koyunlarda)
    udder_development: float = 0.0        # Meme gelişimi
    vulva_changes: float = 0.0            # Vulva değişiklikleri
    appetite_change: float = 0.0          # İştah değişikliği
    

class BirthPredictor:
    """
    Doğum Tahmin Sınıfı
    
    Gebelik takibi ve doğum tarihini tahmin eder.
    """
    
    # Gebelik süresi (gün)
    GESTATION_PERIOD = {
        'cattle': 283,    # Sığır: ~283 gün (9 ay 10 gün)
        'sheep': 150,     # Koyun: ~150 gün (5 ay)
        'goat': 150       # Keçi: ~150 gün (5 ay)
    }
    
    # Gebelik süresi varyasyonu (gün, +/-)
    GESTATION_VARIANCE = {
        'cattle': 10,     # +/- 10 gün
        'sheep': 5,       # +/- 5 gün
        'goat': 5         # +/- 5 gün
    }
    
    # Pre-partum davranış başlangıcı (doğumdan önce, saat)
    PRE_PARTUM_ONSET = {
        'cattle': 24,     # 24 saat önce
        'sheep': 12,      # 12 saat önce
        'goat': 12        # 12 saat önce
    }
    
    def __init__(self, animal_type: str = 'cattle'):
        self.animal_type = animal_type
        self.pregnancies: Dict[str, Pregnancy] = {}
        self.pre_partum_indicators: Dict[str, List[PrePartumIndicators]] = {}
        
    def create_pregnancy(
        self,
        animal_id: str,
        breeding_date: date,
        sire_id: Optional[str] = None,
        breeding_method: BreedingMethod = BreedingMethod.NATURAL,
        notes: str = ""
    ) -> Pregnancy:
        """
        Yeni gebelik kaydı oluşturur.
        
        Args:
            animal_id: Dişi hayvan kimliği
            breeding_date: Çiftleşme/tohumlama tarihi
            sire_id: Erkek hayvan kimliği
            breeding_method: Çiftleşme yöntemi
            notes: Notlar
            
        Returns:
            Oluşturulan gebelik kaydı
        """
        # Beklenen doğum tarihini hesapla
        gestation_days = self.GESTATION_PERIOD[self.animal_type]
        expected_birth = breeding_date + timedelta(days=gestation_days)
        
        pregnancy = Pregnancy(
            id=f"gebelik-{animal_id}-{uuid.uuid4().hex[:8]}",
            animal_id=animal_id,
            breeding_date=breeding_date,
            expected_birth_date=expected_birth,
            sire_id=sire_id,
            breeding_method=breeding_method,
            notes=notes
        )
        
        self.pregnancies[pregnancy.id] = pregnancy
        return pregnancy
    
    def confirm_pregnancy(
        self,
        pregnancy_id: str,
        method: ConfirmationMethod,
        confirmation_date: Optional[date] = None
    ) -> bool:
        """
        Gebeliği onaylar.
        
        Args:
            pregnancy_id: Gebelik kimliği
            method: Onay yöntemi
            confirmation_date: Onay tarihi
            
        Returns:
            Başarılı ise True
        """
        if pregnancy_id not in self.pregnancies:
            return False
        
        pregnancy = self.pregnancies[pregnancy_id]
        pregnancy.pregnancy_confirmed = True
        pregnancy.confirmation_method = method
        pregnancy.confirmation_date = confirmation_date or date.today()
        
        return True
    
    def update_expected_birth(
        self,
        pregnancy_id: str,
        new_date: date,
        reason: str = ""
    ) -> bool:
        """
        Beklenen doğum tarihini günceller.
        
        Ultrason sonucu veya veteriner değerlendirmesiyle.
        """
        if pregnancy_id not in self.pregnancies:
            return False
        
        pregnancy = self.pregnancies[pregnancy_id]
        old_date = pregnancy.expected_birth_date
        pregnancy.expected_birth_date = new_date
        
        if reason:
            pregnancy.notes += f"\n[{date.today()}] Doğum tarihi güncellendi: {old_date} -> {new_date}. Sebep: {reason}"
        
        return True
    
    def analyze_pre_partum(
        self,
        animal_id: str,
        indicators: PrePartumIndicators,
        timestamp: datetime
    ) -> Optional[Dict]:
        """
        Pre-partum davranışları analiz eder.
        
        Args:
            animal_id: Hayvan kimliği
            indicators: Davranış göstergeleri
            timestamp: Zaman damgası
            
        Returns:
            Doğum tahmin bilgisi
        """
        # Göstergeleri kaydet
        if animal_id not in self.pre_partum_indicators:
            self.pre_partum_indicators[animal_id] = []
        self.pre_partum_indicators[animal_id].append(indicators)
        
        # Aktif gebelik var mı?
        pregnancy = self._get_active_pregnancy(animal_id)
        if not pregnancy:
            return None
        
        # Beklenen doğuma kaç gün var?
        days_to_birth = (pregnancy.expected_birth_date - date.today()).days
        
        # Erken doğum riski değerlendirmesi
        risk_score = self._calculate_birth_risk(animal_id, indicators)
        
        result = {
            'animal_id': animal_id,
            'pregnancy_id': pregnancy.id,
            'expected_birth_date': pregnancy.expected_birth_date.isoformat(),
            'days_remaining': days_to_birth,
            'risk_score': risk_score,
            'indicators': {
                'restlessness': indicators.restlessness_score,
                'isolation': indicators.isolation_score,
                'tail_raising': indicators.tail_raising_frequency,
                'nesting': indicators.nesting_behavior,
                'udder_development': indicators.udder_development
            }
        }
        
        # Doğum yaklaşıyor uyarısı
        if risk_score > 0.7 or days_to_birth <= 1:
            result['alert'] = 'imminent'  # Yakın doğum
            result['estimated_hours'] = self._estimate_hours_to_birth(animal_id, indicators)
        elif risk_score > 0.5 or days_to_birth <= 3:
            result['alert'] = 'soon'  # Yakında
        elif days_to_birth <= 7:
            result['alert'] = 'week'  # Bu hafta
        
        return result
    
    def _calculate_birth_risk(
        self,
        animal_id: str,
        current: PrePartumIndicators
    ) -> float:
        """
        Doğum yakınlık riskini hesaplar.
        
        Returns:
            0-1 arası risk skoru (1 = doğum çok yakın)
        """
        history = self.pre_partum_indicators.get(animal_id, [])
        
        # Ağırlıklı skorlama
        weights = {
            'restlessness': 0.25,
            'isolation': 0.25,
            'tail_raising': 0.15,
            'nesting': 0.15,
            'udder_development': 0.10,
            'appetite_change': 0.10
        }
        
        score = 0.0
        score += weights['restlessness'] * current.restlessness_score
        score += weights['isolation'] * current.isolation_score
        score += weights['tail_raising'] * min(current.tail_raising_frequency / 10, 1.0)
        score += weights['nesting'] * (1.0 if current.nesting_behavior else 0.0)
        score += weights['udder_development'] * current.udder_development
        score += weights['appetite_change'] * abs(current.appetite_change)
        
        # Trend analizi (son 6 saat)
        if len(history) >= 6:
            recent = history[-6:]
            trend_restlessness = np.mean([h.restlessness_score for h in recent])
            trend_isolation = np.mean([h.isolation_score for h in recent])
            
            # Artan trend = daha yüksek risk
            if trend_restlessness > 0.5 and trend_isolation > 0.5:
                score *= 1.3  # %30 artış
        
        return min(score, 1.0)
    
    def _estimate_hours_to_birth(
        self,
        animal_id: str,
        indicators: PrePartumIndicators
    ) -> int:
        """
        Doğuma kalan tahmini saat.
        """
        # Davranış yoğunluğuna göre tahmin
        if indicators.restlessness_score > 0.8 and indicators.isolation_score > 0.8:
            return 6  # 6 saat içinde
        elif indicators.restlessness_score > 0.6:
            return 12  # 12 saat içinde
        else:
            return 24  # 24 saat içinde
    
    def _get_active_pregnancy(self, animal_id: str) -> Optional[Pregnancy]:
        """Hayvanın aktif gebeliğini döndürür."""
        for pregnancy in self.pregnancies.values():
            if (pregnancy.animal_id == animal_id and 
                pregnancy.status == PregnancyStatus.ACTIVE):
                return pregnancy
        return None
    
    def get_due_soon(self, days: int = 7) -> List[Pregnancy]:
        """
        Yakında doğum yapacak gebelikleri döndürür.
        
        Args:
            days: Kaç gün içinde doğum beklenenler
        """
        today = date.today()
        cutoff = today + timedelta(days=days)
        
        return [
            p for p in self.pregnancies.values()
            if p.status == PregnancyStatus.ACTIVE
            and today <= p.expected_birth_date <= cutoff
        ]
    
    def get_overdue(self) -> List[Pregnancy]:
        """
        Zamanı geçmiş gebelikleri döndürür.
        """
        today = date.today()
        variance = self.GESTATION_VARIANCE[self.animal_type]
        
        return [
            p for p in self.pregnancies.values()
            if p.status == PregnancyStatus.ACTIVE
            and (today - p.expected_birth_date).days > variance
        ]
    
    def complete_pregnancy(
        self,
        pregnancy_id: str,
        birth_date: date,
        status: PregnancyStatus = PregnancyStatus.DELIVERED
    ) -> bool:
        """
        Gebeliği tamamlar (doğum yapıldı).
        """
        if pregnancy_id not in self.pregnancies:
            return False
        
        pregnancy = self.pregnancies[pregnancy_id]
        pregnancy.actual_birth_date = birth_date
        pregnancy.status = status
        
        return True
    
    def get_statistics(self) -> Dict:
        """
        Gebelik istatistiklerini döndürür.
        """
        all_pregnancies = list(self.pregnancies.values())
        active = [p for p in all_pregnancies if p.status == PregnancyStatus.ACTIVE]
        delivered = [p for p in all_pregnancies if p.status == PregnancyStatus.DELIVERED]
        aborted = [p for p in all_pregnancies if p.status == PregnancyStatus.ABORTED]
        
        # Ortalama gebelik süresi (doğum yapanlar için)
        gestation_lengths = []
        for p in delivered:
            if p.actual_birth_date:
                length = (p.actual_birth_date - p.breeding_date).days
                gestation_lengths.append(length)
        
        avg_gestation = np.mean(gestation_lengths) if gestation_lengths else 0
        
        return {
            'total': len(all_pregnancies),
            'active': len(active),
            'delivered': len(delivered),
            'aborted': len(aborted),
            'success_rate': len(delivered) / len(all_pregnancies) * 100 if all_pregnancies else 0,
            'avg_gestation_days': avg_gestation,
            'due_this_week': len(self.get_due_soon(7)),
            'overdue': len(self.get_overdue())
        }


# Test için örnek kullanım
if __name__ == "__main__":
    predictor = BirthPredictor(animal_type='cattle')
    
    # Gebelik kaydı oluştur
    pregnancy = predictor.create_pregnancy(
        animal_id='inek-001',
        breeding_date=date(2024, 3, 1),
        sire_id='boga-001',
        breeding_method=BreedingMethod.NATURAL
    )
    
    print(f"Gebelik oluşturuldu: {pregnancy.id}")
    print(f"Beklenen doğum: {pregnancy.expected_birth_date}")
    
    # Pre-partum analizi
    indicators = PrePartumIndicators(
        restlessness_score=0.7,
        isolation_score=0.5,
        tail_raising_frequency=5
    )
    
    result = predictor.analyze_pre_partum('inek-001', indicators, datetime.now())
    if result:
        print(f"Analiz sonucu: {result}")
    
    # İstatistikler
    stats = predictor.get_statistics()
    print(f"İstatistikler: {stats}")
