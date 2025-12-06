"""
Üreme API Routes
================
FastAPI üreme modülü endpoint'leri
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


router = APIRouter(prefix="/api/reproduction", tags=["reproduction"])


# === Pydantic Models ===

class BreedingMethod(str, Enum):
    natural = "doğal"
    ai = "suni_tohumlama"
    et = "embriyo_transferi"


class EstrusStatus(str, Enum):
    detected = "detected"
    confirmed = "confirmed"
    bred = "bred"
    missed = "missed"
    false_positive = "false_positive"


class PregnancyStatus(str, Enum):
    active = "aktif"
    delivered = "doğum_yaptı"
    aborted = "düşük"
    cancelled = "iptal"


class BirthType(str, Enum):
    normal = "normal"
    assisted = "müdahaleli"
    cesarean = "sezaryen"


# Request/Response Models

class EstrusDetectionCreate(BaseModel):
    animal_id: str
    detection_time: Optional[datetime] = None
    behaviors: Dict[str, float] = Field(default_factory=dict)
    confidence: float = Field(ge=0, le=1)
    notes: Optional[str] = None


class EstrusDetectionResponse(BaseModel):
    id: str
    animal_id: str
    detection_time: datetime
    behaviors: Dict[str, float]
    confidence: float
    optimal_breeding_start: Optional[datetime]
    optimal_breeding_end: Optional[datetime]
    status: EstrusStatus
    notified: bool
    notes: Optional[str]
    created_at: datetime


class PregnancyCreate(BaseModel):
    animal_id: str
    breeding_date: date
    sire_id: Optional[str] = None
    breeding_method: BreedingMethod = BreedingMethod.natural
    notes: Optional[str] = None


class PregnancyResponse(BaseModel):
    id: str
    animal_id: str
    breeding_date: date
    expected_birth_date: date
    actual_birth_date: Optional[date]
    sire_id: Optional[str]
    breeding_method: BreedingMethod
    pregnancy_confirmed: bool
    confirmation_date: Optional[date]
    confirmation_method: Optional[str]
    status: PregnancyStatus
    notes: Optional[str]
    created_at: datetime


class PregnancyConfirm(BaseModel):
    confirmation_method: str = Field(..., description="manual, ultrasound, blood_test, observation")
    confirmation_date: Optional[date] = None


class BirthCreate(BaseModel):
    mother_id: str
    pregnancy_id: Optional[str] = None
    birth_date: Optional[datetime] = None
    offspring_count: int = 1
    offspring_ids: List[str] = Field(default_factory=list)
    birth_type: BirthType = BirthType.normal
    birth_weight: Optional[float] = None
    complications: Optional[str] = None
    vet_assisted: bool = False
    vet_name: Optional[str] = None
    notes: Optional[str] = None


class BirthResponse(BaseModel):
    id: str
    mother_id: str
    pregnancy_id: Optional[str]
    birth_date: datetime
    offspring_count: int
    offspring_ids: List[str]
    birth_type: BirthType
    birth_weight: Optional[float]
    complications: Optional[str]
    vet_assisted: bool
    vet_name: Optional[str]
    ai_predicted_at: Optional[datetime]
    ai_detected_at: Optional[datetime]
    prediction_accuracy_hours: Optional[float]
    notes: Optional[str]
    created_at: datetime


class BreedingRecordCreate(BaseModel):
    female_id: str
    male_id: Optional[str] = None
    breeding_date: Optional[date] = None
    breeding_method: BreedingMethod = BreedingMethod.natural
    technician_name: Optional[str] = None
    semen_batch: Optional[str] = None
    estrus_detection_id: Optional[str] = None
    notes: Optional[str] = None


class BreedingRecordResponse(BaseModel):
    id: str
    female_id: str
    male_id: Optional[str]
    breeding_date: date
    breeding_method: BreedingMethod
    technician_name: Optional[str]
    semen_batch: Optional[str]
    estrus_detection_id: Optional[str]
    success: Optional[bool]
    pregnancy_id: Optional[str]
    notes: Optional[str]
    created_at: datetime


class ReproductionStats(BaseModel):
    total_estrus_detections: int
    active_pregnancies: int
    total_births: int
    conception_rate: float
    avg_calving_interval: float
    pending_pregnancy_checks: int


# === In-Memory Storage (Supabase'e bağlanana kadar) ===

estrus_db: Dict[str, Dict] = {}
pregnancies_db: Dict[str, Dict] = {}
births_db: Dict[str, Dict] = {}
breeding_db: Dict[str, Dict] = {}


# === Estrus Endpoints ===

@router.get("/estrus", response_model=List[EstrusDetectionResponse])
async def get_estrus_detections(
    animal_id: Optional[str] = None,
    status: Optional[EstrusStatus] = None,
    limit: int = Query(default=50, le=100)
):
    """Kızgınlık tespitlerini listeler."""
    results = list(estrus_db.values())
    
    if animal_id:
        results = [r for r in results if r['animal_id'] == animal_id]
    if status:
        results = [r for r in results if r['status'] == status.value]
    
    return results[:limit]


@router.post("/estrus", response_model=EstrusDetectionResponse)
async def create_estrus_detection(data: EstrusDetectionCreate):
    """Yeni kızgınlık tespiti kaydeder."""
    import uuid
    
    now = datetime.now()
    detection_time = data.detection_time or now
    
    # Optimal tohumlama penceresini hesapla (12-18 saat sonra)
    from datetime import timedelta
    optimal_start = detection_time + timedelta(hours=12)
    optimal_end = detection_time + timedelta(hours=18)
    
    record = {
        'id': f"estrus-{data.animal_id}-{uuid.uuid4().hex[:8]}",
        'animal_id': data.animal_id,
        'detection_time': detection_time,
        'behaviors': data.behaviors,
        'confidence': data.confidence,
        'optimal_breeding_start': optimal_start,
        'optimal_breeding_end': optimal_end,
        'status': EstrusStatus.detected.value,
        'notified': False,
        'notes': data.notes,
        'created_at': now
    }
    
    estrus_db[record['id']] = record
    return record


@router.patch("/estrus/{estrus_id}/confirm")
async def confirm_estrus(estrus_id: str):
    """Kızgınlık tespitini onaylar."""
    if estrus_id not in estrus_db:
        raise HTTPException(status_code=404, detail="Kızgınlık tespiti bulunamadı")
    
    estrus_db[estrus_id]['status'] = EstrusStatus.confirmed.value
    return {"success": True, "status": "confirmed"}


@router.patch("/estrus/{estrus_id}/bred")
async def mark_estrus_bred(estrus_id: str):
    """Tohumlama yapıldı olarak işaretler."""
    if estrus_id not in estrus_db:
        raise HTTPException(status_code=404, detail="Kızgınlık tespiti bulunamadı")
    
    estrus_db[estrus_id]['status'] = EstrusStatus.bred.value
    return {"success": True, "status": "bred"}


# === Pregnancy Endpoints ===

@router.get("/pregnancies", response_model=List[PregnancyResponse])
async def get_pregnancies(
    animal_id: Optional[str] = None,
    status: Optional[PregnancyStatus] = None,
    due_within_days: Optional[int] = None,
    limit: int = Query(default=50, le=100)
):
    """Gebelikleri listeler."""
    results = list(pregnancies_db.values())
    
    if animal_id:
        results = [r for r in results if r['animal_id'] == animal_id]
    if status:
        results = [r for r in results if r['status'] == status.value]
    if due_within_days:
        from datetime import timedelta
        cutoff = date.today() + timedelta(days=due_within_days)
        results = [r for r in results if r['expected_birth_date'] <= cutoff]
    
    return results[:limit]


@router.post("/pregnancies", response_model=PregnancyResponse)
async def create_pregnancy(data: PregnancyCreate):
    """Yeni gebelik kaydı oluşturur."""
    import uuid
    from datetime import timedelta
    
    now = datetime.now()
    
    # Beklenen doğum tarihi (sığır: 283 gün)
    expected_birth = data.breeding_date + timedelta(days=283)
    
    record = {
        'id': f"gebelik-{data.animal_id}-{uuid.uuid4().hex[:8]}",
        'animal_id': data.animal_id,
        'breeding_date': data.breeding_date,
        'expected_birth_date': expected_birth,
        'actual_birth_date': None,
        'sire_id': data.sire_id,
        'breeding_method': data.breeding_method.value,
        'pregnancy_confirmed': False,
        'confirmation_date': None,
        'confirmation_method': None,
        'status': PregnancyStatus.active.value,
        'notes': data.notes,
        'created_at': now
    }
    
    pregnancies_db[record['id']] = record
    return record


@router.patch("/pregnancies/{pregnancy_id}/confirm")
async def confirm_pregnancy(pregnancy_id: str, data: PregnancyConfirm):
    """Gebeliği onaylar."""
    if pregnancy_id not in pregnancies_db:
        raise HTTPException(status_code=404, detail="Gebelik kaydı bulunamadı")
    
    pregnancies_db[pregnancy_id]['pregnancy_confirmed'] = True
    pregnancies_db[pregnancy_id]['confirmation_method'] = data.confirmation_method
    pregnancies_db[pregnancy_id]['confirmation_date'] = data.confirmation_date or date.today()
    
    return {"success": True, "message": "Gebelik onaylandı"}


@router.patch("/pregnancies/{pregnancy_id}/complete")
async def complete_pregnancy(pregnancy_id: str, birth_date: date):
    """Gebeliği tamamlar (doğum yapıldı)."""
    if pregnancy_id not in pregnancies_db:
        raise HTTPException(status_code=404, detail="Gebelik kaydı bulunamadı")
    
    pregnancies_db[pregnancy_id]['status'] = PregnancyStatus.delivered.value
    pregnancies_db[pregnancy_id]['actual_birth_date'] = birth_date
    
    return {"success": True, "status": "delivered"}


# === Birth Endpoints ===

@router.get("/births", response_model=List[BirthResponse])
async def get_births(
    mother_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=50, le=100)
):
    """Doğum kayıtlarını listeler."""
    results = list(births_db.values())
    
    if mother_id:
        results = [r for r in results if r['mother_id'] == mother_id]
    if start_date:
        results = [r for r in results if r['birth_date'].date() >= start_date]
    if end_date:
        results = [r for r in results if r['birth_date'].date() <= end_date]
    
    return results[:limit]


@router.post("/births", response_model=BirthResponse)
async def create_birth(data: BirthCreate):
    """Yeni doğum kaydı oluşturur."""
    import uuid
    
    now = datetime.now()
    
    record = {
        'id': f"dogum-{data.mother_id}-{uuid.uuid4().hex[:8]}",
        'mother_id': data.mother_id,
        'pregnancy_id': data.pregnancy_id,
        'birth_date': data.birth_date or now,
        'offspring_count': data.offspring_count,
        'offspring_ids': data.offspring_ids,
        'birth_type': data.birth_type.value,
        'birth_weight': data.birth_weight,
        'complications': data.complications,
        'vet_assisted': data.vet_assisted,
        'vet_name': data.vet_name,
        'ai_predicted_at': None,
        'ai_detected_at': None,
        'prediction_accuracy_hours': None,
        'notes': data.notes,
        'created_at': now
    }
    
    births_db[record['id']] = record
    
    # İlgili gebeliği güncelle
    if data.pregnancy_id and data.pregnancy_id in pregnancies_db:
        pregnancies_db[data.pregnancy_id]['status'] = PregnancyStatus.delivered.value
        pregnancies_db[data.pregnancy_id]['actual_birth_date'] = record['birth_date'].date()
    
    return record


# === Breeding Record Endpoints ===

@router.get("/breeding", response_model=List[BreedingRecordResponse])
async def get_breeding_records(
    female_id: Optional[str] = None,
    male_id: Optional[str] = None,
    method: Optional[BreedingMethod] = None,
    limit: int = Query(default=50, le=100)
):
    """Çiftleştirme kayıtlarını listeler."""
    results = list(breeding_db.values())
    
    if female_id:
        results = [r for r in results if r['female_id'] == female_id]
    if male_id:
        results = [r for r in results if r['male_id'] == male_id]
    if method:
        results = [r for r in results if r['breeding_method'] == method.value]
    
    return results[:limit]


@router.post("/breeding", response_model=BreedingRecordResponse)
async def create_breeding_record(data: BreedingRecordCreate):
    """Yeni çiftleştirme kaydı oluşturur."""
    import uuid
    
    now = datetime.now()
    
    record = {
        'id': f"ciftlesme-{data.female_id}-{uuid.uuid4().hex[:8]}",
        'female_id': data.female_id,
        'male_id': data.male_id,
        'breeding_date': data.breeding_date or date.today(),
        'breeding_method': data.breeding_method.value,
        'technician_name': data.technician_name,
        'semen_batch': data.semen_batch,
        'estrus_detection_id': data.estrus_detection_id,
        'success': None,
        'pregnancy_id': None,
        'notes': data.notes,
        'created_at': now
    }
    
    breeding_db[record['id']] = record
    
    # İlgili kızgınlık tespitini güncelle
    if data.estrus_detection_id and data.estrus_detection_id in estrus_db:
        estrus_db[data.estrus_detection_id]['status'] = EstrusStatus.bred.value
    
    return record


@router.patch("/breeding/{breeding_id}/success")
async def mark_breeding_success(breeding_id: str, success: bool, pregnancy_id: Optional[str] = None):
    """Çiftleştirme sonucunu kaydeder."""
    if breeding_id not in breeding_db:
        raise HTTPException(status_code=404, detail="Çiftleştirme kaydı bulunamadı")
    
    breeding_db[breeding_id]['success'] = success
    if pregnancy_id:
        breeding_db[breeding_id]['pregnancy_id'] = pregnancy_id
    
    return {"success": True, "breeding_success": success}


# === Analytics Endpoints ===

@router.get("/analytics/summary", response_model=ReproductionStats)
async def get_reproduction_summary():
    """Üreme özet istatistiklerini döndürür."""
    
    # Aktif gebelikler
    active_pregnancies = len([
        p for p in pregnancies_db.values()
        if p['status'] == PregnancyStatus.active.value
    ])
    
    # Başarılı çiftleştirmeler
    confirmed = [b for b in breeding_db.values() if b['success'] is not None]
    successful = [b for b in confirmed if b['success'] is True]
    conception_rate = len(successful) / len(confirmed) * 100 if confirmed else 0
    
    # Gebelik kontrolü bekleyenler
    from datetime import timedelta
    check_date = date.today() - timedelta(days=35)
    pending_checks = len([
        b for b in breeding_db.values()
        if b['success'] is None and b['breeding_date'] <= check_date
    ])
    
    return ReproductionStats(
        total_estrus_detections=len(estrus_db),
        active_pregnancies=active_pregnancies,
        total_births=len(births_db),
        conception_rate=round(conception_rate, 1),
        avg_calving_interval=365,  # Placeholder
        pending_pregnancy_checks=pending_checks
    )


@router.get("/analytics/timeline")
async def get_reproduction_timeline(days: int = 30):
    """Son X günlük üreme olaylarının zaman çizelgesi."""
    from datetime import timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    
    events = []
    
    # Kızgınlıklar
    for e in estrus_db.values():
        if e['detection_time'] >= cutoff:
            events.append({
                'type': 'estrus',
                'date': e['detection_time'],
                'animal_id': e['animal_id'],
                'details': f"Kızgınlık tespit (güven: {e['confidence']*100:.0f}%)"
            })
    
    # Çiftleştirmeler
    for b in breeding_db.values():
        breeding_dt = datetime.combine(b['breeding_date'], datetime.min.time())
        if breeding_dt >= cutoff:
            events.append({
                'type': 'breeding',
                'date': breeding_dt,
                'animal_id': b['female_id'],
                'details': f"Çiftleştirme ({b['breeding_method']})"
            })
    
    # Doğumlar
    for b in births_db.values():
        if b['birth_date'] >= cutoff:
            events.append({
                'type': 'birth',
                'date': b['birth_date'],
                'animal_id': b['mother_id'],
                'details': f"Doğum ({b['offspring_count']} yavru)"
            })
    
    # Tarihe göre sırala
    events.sort(key=lambda x: x['date'], reverse=True)
    
    return events


@router.get("/analytics/due-soon")
async def get_due_soon(days: int = 7):
    """Yakında doğum yapacak hayvanları listeler."""
    from datetime import timedelta
    
    today = date.today()
    cutoff = today + timedelta(days=days)
    
    due = [
        {
            'pregnancy_id': p['id'],
            'animal_id': p['animal_id'],
            'expected_date': p['expected_birth_date'],
            'days_remaining': (p['expected_birth_date'] - today).days,
            'confirmed': p['pregnancy_confirmed']
        }
        for p in pregnancies_db.values()
        if p['status'] == PregnancyStatus.active.value
        and today <= p['expected_birth_date'] <= cutoff
    ]
    
    due.sort(key=lambda x: x['days_remaining'])
    return due


@router.get("/analytics/breeding-calendar")
async def get_breeding_calendar(year: int, month: int):
    """Belirli ay için çiftleştirme takvimi."""
    events = []
    
    for b in breeding_db.values():
        if b['breeding_date'].year == year and b['breeding_date'].month == month:
            events.append({
                'date': b['breeding_date'].isoformat(),
                'type': 'breeding',
                'animal_id': b['female_id'],
                'method': b['breeding_method'],
                'success': b['success']
            })
    
    for e in estrus_db.values():
        if e['detection_time'].year == year and e['detection_time'].month == month:
            events.append({
                'date': e['detection_time'].date().isoformat(),
                'type': 'estrus',
                'animal_id': e['animal_id'],
                'confidence': e['confidence']
            })
    
    return events
