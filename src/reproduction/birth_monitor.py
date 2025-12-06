"""
Doğum İzleme Modülü
===================
Aktif doğum sürecini gerçek zamanlı izler.

Özellikler:
- Doğum aşamalarını takip
- Güç doğum (dystocia) tespiti
- Yavru kaydı oluşturma
- Veteriner uyarısı
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class BirthStage(Enum):
    """Doğum aşamaları"""
    NONE = "none"
    STAGE_1 = "stage_1"        # Hazırlık - Serviks açılması
    STAGE_2 = "stage_2"        # Aktif doğum - Yavru çıkışı
    STAGE_3 = "stage_3"        # Plasenta atılması
    COMPLETED = "completed"    # Tamamlandı
    COMPLICATED = "complicated"  # Komplikasyon


class BirthType(Enum):
    """Doğum tipi"""
    NORMAL = "normal"
    ASSISTED = "müdahaleli"
    CESAREAN = "sezaryen"


class ComplicationType(Enum):
    """Komplikasyon tipleri"""
    NONE = "none"
    DYSTOCIA = "dystocia"           # Güç doğum
    PROLONGED = "prolonged"          # Uzamış doğum
    MALPRESENTATION = "malpresentation"  # Yanlış pozisyon
    RETAINED_PLACENTA = "retained_placenta"  # Plasenta tutulması
    PROLAPSE = "prolapse"            # Uterus prolapsusu


@dataclass
class BirthEvent:
    """Doğum olayı veri yapısı"""
    id: str
    mother_id: str
    pregnancy_id: Optional[str]
    birth_date: datetime
    offspring_count: int = 1
    offspring_ids: List[str] = field(default_factory=list)
    birth_type: BirthType = BirthType.NORMAL
    birth_weight: Optional[float] = None
    complications: Optional[ComplicationType] = None
    vet_assisted: bool = False
    vet_name: Optional[str] = None
    ai_predicted_at: Optional[datetime] = None
    ai_detected_at: Optional[datetime] = None
    prediction_accuracy_hours: Optional[float] = None
    notes: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class ActiveBirth:
    """Aktif doğum izleme"""
    animal_id: str
    started_at: datetime
    current_stage: BirthStage = BirthStage.STAGE_1
    stage_1_start: Optional[datetime] = None
    stage_2_start: Optional[datetime] = None
    stage_3_start: Optional[datetime] = None
    contractions_count: int = 0
    last_contraction: Optional[datetime] = None
    pushing_detected: bool = False
    offspring_visible: bool = False
    alert_sent: bool = False


class BirthMonitor:
    """
    Doğum İzleme Sınıfı
    
    Aktif doğum sürecini gerçek zamanlı izler.
    """
    
    # Aşama süreleri (dakika) - Sığır için
    STAGE_DURATION_CATTLE = {
        BirthStage.STAGE_1: (120, 360),   # 2-6 saat
        BirthStage.STAGE_2: (30, 120),    # 30 dk - 2 saat
        BirthStage.STAGE_3: (30, 480),    # 30 dk - 8 saat
    }
    
    # Aşama süreleri (dakika) - Koyun için
    STAGE_DURATION_SHEEP = {
        BirthStage.STAGE_1: (60, 180),    # 1-3 saat
        BirthStage.STAGE_2: (30, 60),     # 30-60 dk
        BirthStage.STAGE_3: (30, 180),    # 30 dk - 3 saat
    }
    
    # Güç doğum alarm eşikleri (dakika)
    DYSTOCIA_THRESHOLD = {
        'cattle': {
            'stage_1': 360,    # 6 saat
            'stage_2': 90,     # 1.5 saat
            'no_progress': 30  # 30 dakika ilerleme yok
        },
        'sheep': {
            'stage_1': 180,    # 3 saat
            'stage_2': 60,     # 1 saat
            'no_progress': 20  # 20 dakika ilerleme yok
        }
    }
    
    def __init__(self, animal_type: str = 'cattle'):
        self.animal_type = animal_type
        self.active_births: Dict[str, ActiveBirth] = {}
        self.completed_births: Dict[str, BirthEvent] = {}
        self.behavior_buffer: Dict[str, List[Dict]] = {}
        
    def start_monitoring(
        self,
        animal_id: str,
        pregnancy_id: Optional[str] = None,
        ai_predicted_at: Optional[datetime] = None
    ) -> ActiveBirth:
        """
        Doğum izlemeyi başlatır.
        
        Args:
            animal_id: Anne hayvan kimliği
            pregnancy_id: Gebelik kaydı kimliği
            ai_predicted_at: AI tahmin zamanı
        """
        now = datetime.now()
        
        active_birth = ActiveBirth(
            animal_id=animal_id,
            started_at=now,
            current_stage=BirthStage.STAGE_1,
            stage_1_start=now
        )
        
        self.active_births[animal_id] = active_birth
        self.behavior_buffer[animal_id] = []
        
        return active_birth
    
    def analyze_frame(
        self,
        animal_id: str,
        frame: np.ndarray,
        detections: List[Dict],
        timestamp: datetime
    ) -> Optional[Dict]:
        """
        Frame'i analiz ederek doğum sürecini izler.
        
        Args:
            animal_id: Hayvan kimliği
            frame: Video frame'i
            detections: YOLO tespit sonuçları
            timestamp: Frame zamanı
            
        Returns:
            Doğum durumu güncellemesi
        """
        if animal_id not in self.active_births:
            return None
        
        active = self.active_births[animal_id]
        
        # Davranış analizi
        behaviors = self._analyze_birth_behaviors(animal_id, frame, detections)
        self.behavior_buffer[animal_id].append({
            'timestamp': timestamp,
            'behaviors': behaviors
        })
        
        # Aşama güncellemesi
        stage_update = self._update_stage(animal_id, behaviors, timestamp)
        
        # Komplikasyon kontrolü
        complication = self._check_complications(animal_id, timestamp)
        
        result = {
            'animal_id': animal_id,
            'current_stage': active.current_stage.value,
            'duration_minutes': (timestamp - active.started_at).total_seconds() / 60,
            'behaviors': behaviors,
            'complication': complication.value if complication else None
        }
        
        if stage_update:
            result['stage_update'] = stage_update
        
        if complication and not active.alert_sent:
            result['alert'] = {
                'type': 'dystocia_risk',
                'severity': 'critical',
                'message': f'Güç doğum riski: {complication.value}'
            }
            active.alert_sent = True
        
        return result
    
    def _analyze_birth_behaviors(
        self,
        animal_id: str,
        frame: np.ndarray,
        detections: List[Dict]
    ) -> Dict:
        """
        Doğum davranışlarını analiz eder.
        """
        behaviors = {
            'lying': False,           # Yatıyor mu
            'contracting': False,     # Kasılma var mı
            'pushing': False,         # Iteliyor mu
            'straining': False,       # Zorlanıyor mu
            'offspring_visible': False,  # Yavru görünüyor mu
            'standing_attempts': 0    # Kalkma denemeleri
        }
        
        # Hayvanı bul
        target = None
        for det in detections:
            if det.get('id') == animal_id:
                target = det
                break
        
        if not target:
            return behaviors
        
        # Pozisyon analizi
        pose = target.get('pose', {})
        bbox = target.get('bbox', [0, 0, 0, 0])
        
        # Yatma tespiti
        aspect_ratio = (bbox[2] - bbox[0]) / max(bbox[3] - bbox[1], 1)
        behaviors['lying'] = aspect_ratio > 1.5
        
        # Kasılma tespiti (pozisyon değişikliği)
        if len(self.behavior_buffer.get(animal_id, [])) > 2:
            recent = self.behavior_buffer[animal_id][-3:]
            position_variance = self._calculate_position_variance(recent)
            behaviors['contracting'] = position_variance > 0.1
        
        # Itme tespiti (karın hareketi)
        behaviors['pushing'] = behaviors['contracting'] and behaviors['lying']
        
        # Yavru görünürlüğü (yeni nesne tespiti)
        for det in detections:
            det_type = det.get('type', '').lower()
            if 'calf' in det_type or 'lamb' in det_type or 'buzağı' in det_type:
                behaviors['offspring_visible'] = True
                break
        
        return behaviors
    
    def _update_stage(
        self,
        animal_id: str,
        behaviors: Dict,
        timestamp: datetime
    ) -> Optional[str]:
        """
        Doğum aşamasını günceller.
        """
        active = self.active_births[animal_id]
        previous_stage = active.current_stage
        
        # Stage 1 -> Stage 2 geçişi
        if active.current_stage == BirthStage.STAGE_1:
            if behaviors.get('pushing') or behaviors.get('straining'):
                active.current_stage = BirthStage.STAGE_2
                active.stage_2_start = timestamp
                active.pushing_detected = True
                return f"Stage 1 -> Stage 2 ({(timestamp - active.stage_1_start).total_seconds() / 60:.0f} dk)"
        
        # Stage 2 -> Stage 3 geçişi
        elif active.current_stage == BirthStage.STAGE_2:
            if behaviors.get('offspring_visible'):
                active.offspring_visible = True
            
            # Yavru çıktı ve anne ayağa kalktı
            if active.offspring_visible and not behaviors.get('lying'):
                active.current_stage = BirthStage.STAGE_3
                active.stage_3_start = timestamp
                return f"Stage 2 -> Stage 3 ({(timestamp - active.stage_2_start).total_seconds() / 60:.0f} dk)"
        
        # Stage 3 tamamlanma (plasenta atıldı)
        elif active.current_stage == BirthStage.STAGE_3:
            stage_3_duration = (timestamp - active.stage_3_start).total_seconds() / 60
            thresholds = self.STAGE_DURATION_CATTLE if self.animal_type == 'cattle' else self.STAGE_DURATION_SHEEP
            
            # Normal süre içinde tamamlandı varsay
            if stage_3_duration > thresholds[BirthStage.STAGE_3][0]:
                return "Stage 3 devam ediyor"
        
        return None
    
    def _check_complications(
        self,
        animal_id: str,
        timestamp: datetime
    ) -> Optional[ComplicationType]:
        """
        Komplikasyon kontrolü yapar.
        """
        active = self.active_births[animal_id]
        thresholds = self.DYSTOCIA_THRESHOLD[self.animal_type]
        
        # Stage 1 uzaması
        if active.current_stage == BirthStage.STAGE_1:
            duration = (timestamp - active.stage_1_start).total_seconds() / 60
            if duration > thresholds['stage_1']:
                return ComplicationType.PROLONGED
        
        # Stage 2 uzaması (güç doğum)
        elif active.current_stage == BirthStage.STAGE_2:
            if active.stage_2_start:
                duration = (timestamp - active.stage_2_start).total_seconds() / 60
                if duration > thresholds['stage_2']:
                    return ComplicationType.DYSTOCIA
        
        # Stage 3 uzaması (plasenta tutulması)
        elif active.current_stage == BirthStage.STAGE_3:
            if active.stage_3_start:
                duration = (timestamp - active.stage_3_start).total_seconds() / 60
                stage_thresholds = self.STAGE_DURATION_CATTLE if self.animal_type == 'cattle' else self.STAGE_DURATION_SHEEP
                if duration > stage_thresholds[BirthStage.STAGE_3][1]:
                    return ComplicationType.RETAINED_PLACENTA
        
        return None
    
    def complete_birth(
        self,
        animal_id: str,
        offspring_count: int = 1,
        offspring_ids: Optional[List[str]] = None,
        birth_type: BirthType = BirthType.NORMAL,
        birth_weight: Optional[float] = None,
        complications: Optional[str] = None,
        vet_assisted: bool = False,
        vet_name: Optional[str] = None,
        notes: str = ""
    ) -> Optional[BirthEvent]:
        """
        Doğumu tamamlar ve kayıt oluşturur.
        """
        if animal_id not in self.active_births:
            return None
        
        active = self.active_births[animal_id]
        now = datetime.now()
        
        # Tahmin doğruluğunu hesapla
        accuracy = None
        if hasattr(active, 'ai_predicted_at') and active.ai_predicted_at:
            accuracy = abs((now - active.ai_predicted_at).total_seconds() / 3600)
        
        birth_event = BirthEvent(
            id=f"dogum-{animal_id}-{uuid.uuid4().hex[:8]}",
            mother_id=animal_id,
            pregnancy_id=getattr(active, 'pregnancy_id', None),
            birth_date=now,
            offspring_count=offspring_count,
            offspring_ids=offspring_ids or [],
            birth_type=birth_type,
            birth_weight=birth_weight,
            complications=ComplicationType(complications) if complications else None,
            vet_assisted=vet_assisted,
            vet_name=vet_name,
            ai_detected_at=active.started_at,
            prediction_accuracy_hours=accuracy,
            notes=notes
        )
        
        self.completed_births[birth_event.id] = birth_event
        
        # Aktif izlemeyi kaldır
        del self.active_births[animal_id]
        if animal_id in self.behavior_buffer:
            del self.behavior_buffer[animal_id]
        
        return birth_event
    
    def register_offspring(
        self,
        birth_id: str,
        offspring_id: str,
        weight: Optional[float] = None,
        gender: Optional[str] = None
    ) -> bool:
        """
        Yavru kaydı ekler.
        """
        if birth_id not in self.completed_births:
            return False
        
        birth = self.completed_births[birth_id]
        if offspring_id not in birth.offspring_ids:
            birth.offspring_ids.append(offspring_id)
        
        return True
    
    def get_active_births(self) -> List[Dict]:
        """
        Aktif doğumları döndürür.
        """
        now = datetime.now()
        result = []
        
        for animal_id, active in self.active_births.items():
            duration = (now - active.started_at).total_seconds() / 60
            result.append({
                'animal_id': animal_id,
                'started_at': active.started_at.isoformat(),
                'current_stage': active.current_stage.value,
                'duration_minutes': duration,
                'pushing_detected': active.pushing_detected,
                'offspring_visible': active.offspring_visible,
                'alert_sent': active.alert_sent
            })
        
        return result
    
    def get_birth_statistics(self) -> Dict:
        """
        Doğum istatistiklerini döndürür.
        """
        births = list(self.completed_births.values())
        
        if not births:
            return {
                'total_births': 0,
                'normal_rate': 0,
                'assisted_rate': 0,
                'avg_duration_minutes': 0
            }
        
        normal = len([b for b in births if b.birth_type == BirthType.NORMAL])
        assisted = len([b for b in births if b.birth_type == BirthType.ASSISTED])
        cesarean = len([b for b in births if b.birth_type == BirthType.CESAREAN])
        
        return {
            'total_births': len(births),
            'normal_count': normal,
            'assisted_count': assisted,
            'cesarean_count': cesarean,
            'normal_rate': normal / len(births) * 100,
            'assisted_rate': assisted / len(births) * 100,
            'cesarean_rate': cesarean / len(births) * 100,
            'active_births': len(self.active_births)
        }
    
    @staticmethod
    def _calculate_position_variance(recent_behaviors: List[Dict]) -> float:
        """Pozisyon değişkenliğini hesaplar."""
        if len(recent_behaviors) < 2:
            return 0.0
        
        positions = [b.get('position', (0, 0)) for b in recent_behaviors]
        if all(p == (0, 0) for p in positions):
            return 0.0
        
        x_var = np.var([p[0] for p in positions])
        y_var = np.var([p[1] for p in positions])
        
        return (x_var + y_var) / 2


# Test için örnek kullanım
if __name__ == "__main__":
    monitor = BirthMonitor(animal_type='cattle')
    
    # Doğum izlemeyi başlat
    active = monitor.start_monitoring(
        animal_id='inek-001',
        pregnancy_id='gebelik-001'
    )
    
    print(f"Doğum izleme başladı: {active.animal_id}")
    print(f"Başlangıç zamanı: {active.started_at}")
    print(f"Mevcut aşama: {active.current_stage.value}")
    
    # Simüle frame analizi
    test_detections = [
        {'id': 'inek-001', 'bbox': [100, 100, 300, 200], 'pose': {'lying': True}}
    ]
    
    result = monitor.analyze_frame(
        animal_id='inek-001',
        frame=np.zeros((480, 640, 3)),
        detections=test_detections,
        timestamp=datetime.now()
    )
    
    if result:
        print(f"Analiz sonucu: {result}")
    
    # İstatistikler
    stats = monitor.get_birth_statistics()
    print(f"İstatistikler: {stats}")
