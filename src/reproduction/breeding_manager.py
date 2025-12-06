"""
Çiftleştirme Yönetim Modülü
===========================
Çiftleştirme/tohumlama kayıtları ve üreme performansı analizi.

Özellikler:
- Çiftleştirme kaydı
- Suni tohumlama takibi
- Boğa/koç performansı
- Üreme performans metrikleri
"""

import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class BreedingMethod(Enum):
    """Çiftleştirme yöntemi"""
    NATURAL = "doğal"
    AI = "suni_tohumlama"
    ET = "embriyo_transferi"


@dataclass
class BreedingRecord:
    """Çiftleştirme kaydı veri yapısı"""
    id: str
    female_id: str
    male_id: Optional[str]
    breeding_date: date
    breeding_method: BreedingMethod = BreedingMethod.NATURAL
    technician_name: Optional[str] = None
    semen_batch: Optional[str] = None
    estrus_detection_id: Optional[str] = None
    success: Optional[bool] = None
    pregnancy_id: Optional[str] = None
    notes: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class MalePerformance:
    """Erkek hayvan üreme performansı"""
    male_id: str
    total_breedings: int = 0
    successful_breedings: int = 0
    conception_rate: float = 0.0
    avg_services_per_conception: float = 0.0
    offspring_count: int = 0


@dataclass
class FemaleReproductiveHistory:
    """Dişi hayvan üreme geçmişi"""
    female_id: str
    total_breedings: int = 0
    total_pregnancies: int = 0
    total_births: int = 0
    total_offspring: int = 0
    avg_calving_interval: float = 0.0  # Gün
    avg_days_open: float = 0.0         # Açık gün
    conception_rate: float = 0.0
    first_breeding_age: Optional[int] = None  # Gün
    last_breeding_date: Optional[date] = None


class BreedingManager:
    """
    Çiftleştirme Yönetim Sınıfı
    
    Çiftleştirme kayıtları ve üreme performansı analizi.
    """
    
    # Gebelik kontrolü için bekleme süresi (gün)
    PREGNANCY_CHECK_DAYS = {
        'cattle': 35,    # Ultrason ile
        'sheep': 30,
        'goat': 30
    }
    
    # Tekrar kızgınlık bekleme süresi (gün)
    REPEAT_HEAT_INTERVAL = {
        'cattle': 21,    # 21 günlük döngü
        'sheep': 17,     # 17 günlük döngü
        'goat': 21
    }
    
    def __init__(self, animal_type: str = 'cattle'):
        self.animal_type = animal_type
        self.breeding_records: Dict[str, BreedingRecord] = {}
        self.male_stats: Dict[str, MalePerformance] = {}
        self.female_history: Dict[str, FemaleReproductiveHistory] = {}
        
    def record_breeding(
        self,
        female_id: str,
        male_id: Optional[str] = None,
        breeding_date: Optional[date] = None,
        method: BreedingMethod = BreedingMethod.NATURAL,
        technician_name: Optional[str] = None,
        semen_batch: Optional[str] = None,
        estrus_detection_id: Optional[str] = None,
        notes: str = ""
    ) -> BreedingRecord:
        """
        Çiftleştirme kaydı oluşturur.
        
        Args:
            female_id: Dişi hayvan kimliği
            male_id: Erkek hayvan kimliği (suni tohumlamada opsiyonel)
            breeding_date: Çiftleşme tarihi
            method: Çiftleşme yöntemi
            technician_name: Teknisyen adı (suni tohumlama)
            semen_batch: Sperma parti numarası
            estrus_detection_id: Kızgınlık tespit kimliği
            notes: Notlar
            
        Returns:
            Oluşturulan kayıt
        """
        record = BreedingRecord(
            id=f"ciftlesme-{female_id}-{uuid.uuid4().hex[:8]}",
            female_id=female_id,
            male_id=male_id,
            breeding_date=breeding_date or date.today(),
            breeding_method=method,
            technician_name=technician_name,
            semen_batch=semen_batch,
            estrus_detection_id=estrus_detection_id,
            notes=notes
        )
        
        self.breeding_records[record.id] = record
        
        # İstatistikleri güncelle
        self._update_stats(record)
        
        return record
    
    def _update_stats(self, record: BreedingRecord):
        """İstatistikleri günceller."""
        # Erkek istatistikleri
        if record.male_id:
            if record.male_id not in self.male_stats:
                self.male_stats[record.male_id] = MalePerformance(male_id=record.male_id)
            self.male_stats[record.male_id].total_breedings += 1
        
        # Dişi geçmişi
        if record.female_id not in self.female_history:
            self.female_history[record.female_id] = FemaleReproductiveHistory(
                female_id=record.female_id
            )
        history = self.female_history[record.female_id]
        history.total_breedings += 1
        history.last_breeding_date = record.breeding_date
    
    def confirm_pregnancy(
        self,
        breeding_id: str,
        pregnancy_id: str
    ) -> bool:
        """
        Çiftleştirmenin gebelikle sonuçlandığını kaydeder.
        """
        if breeding_id not in self.breeding_records:
            return False
        
        record = self.breeding_records[breeding_id]
        record.success = True
        record.pregnancy_id = pregnancy_id
        
        # İstatistikleri güncelle
        if record.male_id and record.male_id in self.male_stats:
            self.male_stats[record.male_id].successful_breedings += 1
            stats = self.male_stats[record.male_id]
            stats.conception_rate = (
                stats.successful_breedings / stats.total_breedings * 100
                if stats.total_breedings > 0 else 0
            )
        
        if record.female_id in self.female_history:
            self.female_history[record.female_id].total_pregnancies += 1
        
        return True
    
    def mark_unsuccessful(self, breeding_id: str) -> bool:
        """
        Çiftleştirmeyi başarısız olarak işaretler.
        """
        if breeding_id not in self.breeding_records:
            return False
        
        self.breeding_records[breeding_id].success = False
        return True
    
    def get_pending_pregnancy_checks(self) -> List[Dict]:
        """
        Gebelik kontrolü bekleyen çiftleştirmeleri döndürür.
        """
        today = date.today()
        check_days = self.PREGNANCY_CHECK_DAYS[self.animal_type]
        
        pending = []
        for record in self.breeding_records.values():
            if record.success is None:  # Henüz sonuç girilmemiş
                days_since = (today - record.breeding_date).days
                if days_since >= check_days:
                    pending.append({
                        'breeding_id': record.id,
                        'female_id': record.female_id,
                        'breeding_date': record.breeding_date.isoformat(),
                        'days_since': days_since,
                        'check_due': True
                    })
        
        return pending
    
    def get_expected_repeat_heats(self) -> List[Dict]:
        """
        Tekrar kızgınlık beklenen hayvanları döndürür.
        
        Başarısız çiftleştirmelerden sonra beklenen tarihler.
        """
        today = date.today()
        interval = self.REPEAT_HEAT_INTERVAL[self.animal_type]
        
        expected = []
        for record in self.breeding_records.values():
            if record.success is False:  # Başarısız çiftleştirme
                # Sonraki beklenen kızgınlık tarihi
                next_heat = record.breeding_date + timedelta(days=interval)
                days_until = (next_heat - today).days
                
                if -3 <= days_until <= 3:  # +/- 3 gün tolerans
                    expected.append({
                        'female_id': record.female_id,
                        'last_breeding': record.breeding_date.isoformat(),
                        'expected_heat': next_heat.isoformat(),
                        'days_until': days_until
                    })
        
        return expected
    
    def get_male_performance(self, male_id: str) -> Optional[MalePerformance]:
        """
        Erkek hayvan performansını döndürür.
        """
        return self.male_stats.get(male_id)
    
    def get_all_male_rankings(self) -> List[Dict]:
        """
        Tüm erkek hayvanları performansa göre sıralar.
        """
        rankings = []
        for male_id, stats in self.male_stats.items():
            rankings.append({
                'male_id': male_id,
                'total_breedings': stats.total_breedings,
                'successful': stats.successful_breedings,
                'conception_rate': stats.conception_rate,
                'offspring_count': stats.offspring_count
            })
        
        # Conception rate'e göre sırala
        rankings.sort(key=lambda x: x['conception_rate'], reverse=True)
        return rankings
    
    def get_female_history(self, female_id: str) -> Optional[FemaleReproductiveHistory]:
        """
        Dişi hayvan üreme geçmişini döndürür.
        """
        return self.female_history.get(female_id)
    
    def calculate_reproductive_metrics(self) -> Dict:
        """
        Çiftlik geneli üreme performans metriklerini hesaplar.
        """
        all_records = list(self.breeding_records.values())
        
        if not all_records:
            return {
                'total_breedings': 0,
                'conception_rate': 0,
                'services_per_conception': 0,
                'ai_rate': 0,
                'natural_rate': 0
            }
        
        # Toplam çiftleştirme
        total = len(all_records)
        
        # Başarılı çiftleştirmeler
        successful = len([r for r in all_records if r.success is True])
        
        # Conception rate
        confirmed = len([r for r in all_records if r.success is not None])
        conception_rate = successful / confirmed * 100 if confirmed > 0 else 0
        
        # Services per conception
        services_per_conception = confirmed / successful if successful > 0 else 0
        
        # Yöntem dağılımı
        ai_count = len([r for r in all_records if r.breeding_method == BreedingMethod.AI])
        natural_count = len([r for r in all_records if r.breeding_method == BreedingMethod.NATURAL])
        
        return {
            'total_breedings': total,
            'successful_breedings': successful,
            'confirmed_results': confirmed,
            'pending_results': total - confirmed,
            'conception_rate': round(conception_rate, 1),
            'services_per_conception': round(services_per_conception, 2),
            'ai_count': ai_count,
            'ai_rate': round(ai_count / total * 100, 1) if total > 0 else 0,
            'natural_count': natural_count,
            'natural_rate': round(natural_count / total * 100, 1) if total > 0 else 0,
            'unique_females': len(set(r.female_id for r in all_records)),
            'unique_males': len(set(r.male_id for r in all_records if r.male_id))
        }
    
    def calculate_calving_interval(self, female_id: str, birth_dates: List[date]) -> float:
        """
        Doğum arası süreyi (calving interval) hesaplar.
        
        Args:
            female_id: Dişi hayvan kimliği
            birth_dates: Doğum tarihleri listesi
            
        Returns:
            Ortalama doğum arası gün sayısı
        """
        if len(birth_dates) < 2:
            return 0.0
        
        sorted_dates = sorted(birth_dates)
        intervals = []
        
        for i in range(1, len(sorted_dates)):
            interval = (sorted_dates[i] - sorted_dates[i-1]).days
            intervals.append(interval)
        
        avg_interval = np.mean(intervals)
        
        # Dişi geçmişini güncelle
        if female_id in self.female_history:
            self.female_history[female_id].avg_calving_interval = avg_interval
        
        return avg_interval
    
    def calculate_days_open(
        self,
        female_id: str,
        last_birth_date: date,
        conception_date: Optional[date] = None
    ) -> int:
        """
        Açık gün sayısını (days open) hesaplar.
        
        Doğumdan sonra tekrar gebe kalana kadar geçen süre.
        """
        if conception_date:
            days_open = (conception_date - last_birth_date).days
        else:
            # Henüz gebe kalmadıysa bugüne kadar
            days_open = (date.today() - last_birth_date).days
        
        # Dişi geçmişini güncelle
        if female_id in self.female_history:
            self.female_history[female_id].avg_days_open = days_open
        
        return days_open
    
    def get_breeding_calendar(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """
        Belirli tarih aralığındaki çiftleştirme takvimini döndürür.
        """
        calendar = []
        
        for record in self.breeding_records.values():
            if start_date <= record.breeding_date <= end_date:
                calendar.append({
                    'id': record.id,
                    'date': record.breeding_date.isoformat(),
                    'female_id': record.female_id,
                    'male_id': record.male_id,
                    'method': record.breeding_method.value,
                    'success': record.success,
                    'pregnancy_id': record.pregnancy_id
                })
        
        calendar.sort(key=lambda x: x['date'])
        return calendar
    
    def generate_breeding_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Dönemsel üreme raporu oluşturur.
        """
        # Dönem içi kayıtları filtrele
        period_records = [
            r for r in self.breeding_records.values()
            if start_date <= r.breeding_date <= end_date
        ]
        
        if not period_records:
            return {
                'period': f"{start_date.isoformat()} - {end_date.isoformat()}",
                'total_breedings': 0,
                'message': 'Bu dönemde çiftleştirme kaydı yok'
            }
        
        # Yöntemlere göre grupla
        by_method = {}
        for r in period_records:
            method = r.breeding_method.value
            if method not in by_method:
                by_method[method] = {'total': 0, 'successful': 0}
            by_method[method]['total'] += 1
            if r.success is True:
                by_method[method]['successful'] += 1
        
        # Aylara göre grupla
        by_month = {}
        for r in period_records:
            month_key = r.breeding_date.strftime('%Y-%m')
            if month_key not in by_month:
                by_month[month_key] = 0
            by_month[month_key] += 1
        
        return {
            'period': f"{start_date.isoformat()} - {end_date.isoformat()}",
            'total_breedings': len(period_records),
            'successful': len([r for r in period_records if r.success is True]),
            'pending': len([r for r in period_records if r.success is None]),
            'failed': len([r for r in period_records if r.success is False]),
            'by_method': by_method,
            'by_month': by_month,
            'unique_females': len(set(r.female_id for r in period_records)),
            'unique_males': len(set(r.male_id for r in period_records if r.male_id))
        }


# Test için örnek kullanım
if __name__ == "__main__":
    manager = BreedingManager(animal_type='cattle')
    
    # Çiftleştirme kaydı
    record1 = manager.record_breeding(
        female_id='inek-001',
        male_id='boga-001',
        breeding_date=date(2024, 6, 1),
        method=BreedingMethod.NATURAL
    )
    print(f"Çiftleştirme kaydı: {record1.id}")
    
    # Suni tohumlama
    record2 = manager.record_breeding(
        female_id='inek-002',
        breeding_date=date(2024, 6, 5),
        method=BreedingMethod.AI,
        technician_name='Dr. Ahmet',
        semen_batch='BATCH-2024-001'
    )
    print(f"Suni tohumlama: {record2.id}")
    
    # Gebelik onayı
    manager.confirm_pregnancy(record1.id, 'gebelik-001')
    manager.mark_unsuccessful(record2.id)
    
    # Metrikler
    metrics = manager.calculate_reproductive_metrics()
    print(f"Üreme metrikleri: {metrics}")
    
    # Erkek performansı
    male_perf = manager.get_male_performance('boga-001')
    if male_perf:
        print(f"Boğa performansı: CR={male_perf.conception_rate}%")
    
    # Bekleyen kontroller
    pending = manager.get_pending_pregnancy_checks()
    print(f"Gebelik kontrolü bekleyen: {len(pending)}")
