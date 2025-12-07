"""
Rapor API Routes
"""

from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/reports", tags=["Raporlar"])


# Demo veriler
demo_reports = [
    {
        "id": "1",
        "name": "Günlük Aktivite Raporu",
        "type": "günlük",
        "generatedAt": "2024-12-02 09:00",
        "size": "2.4 MB",
        "status": "hazır"
    },
    {
        "id": "2",
        "name": "Haftalık Sağlık Özeti",
        "type": "haftalık",
        "generatedAt": "2024-12-01 18:00",
        "size": "5.8 MB",
        "status": "hazır"
    },
    {
        "id": "3",
        "name": "Aylık Üretim Raporu",
        "type": "aylık",
        "generatedAt": "2024-12-01 00:00",
        "size": "12.3 MB",
        "status": "hazır"
    },
    {
        "id": "4",
        "name": "Özel Analiz Raporu",
        "type": "özel",
        "generatedAt": "2024-12-02 10:30",
        "size": "-",
        "status": "oluşturuluyor"
    }
]


@router.get("/stats")
async def get_report_stats() -> Dict:
    """Rapor istatistikleri"""
    return {
        "total_reports": 156,
        "daily_reports": 30,
        "weekly_reports": 52,
        "monthly_reports": 12
    }


@router.get("/list")
async def get_reports_list(
    type: Optional[str] = Query(None, description="Rapor tipi filtresi"),
    status: Optional[str] = Query(None, description="Durum filtresi")
) -> List[Dict]:
    """Rapor listesi"""
    result = demo_reports.copy()
    
    if type:
        result = [r for r in result if r["type"] == type]
    
    if status:
        result = [r for r in result if r["status"] == status]
    
    return result


@router.get("")
async def get_reports() -> List[Dict]:
    """Tüm raporlar"""
    return demo_reports


@router.get("/{report_id}")
async def get_report(report_id: str) -> Dict:
    """Belirli bir raporu getir"""
    for report in demo_reports:
        if report["id"] == report_id:
            return report
    raise HTTPException(status_code=404, detail="Rapor bulunamadı")


@router.post("/generate")
async def generate_report(
    report_type: str = Query(..., description="Rapor tipi"),
    name: str = Query(..., description="Rapor adı")
) -> Dict:
    """Yeni rapor oluştur"""
    new_report = {
        "id": str(len(demo_reports) + 1),
        "name": name,
        "type": report_type,
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "size": "-",
        "status": "oluşturuluyor"
    }
    demo_reports.append(new_report)
    return new_report


@router.get("/monthly-data")
async def get_monthly_data() -> List[Dict]:
    """Aylık trend verisi"""
    return [
        {"ay": "Oca", "hayvan": 245, "saglik": 12, "alarm": 5},
        {"ay": "Şub", "hayvan": 252, "saglik": 8, "alarm": 3},
        {"ay": "Mar", "hayvan": 260, "saglik": 15, "alarm": 7},
        {"ay": "Nis", "hayvan": 268, "saglik": 10, "alarm": 4},
        {"ay": "May", "hayvan": 275, "saglik": 6, "alarm": 2},
        {"ay": "Haz", "hayvan": 282, "saglik": 9, "alarm": 6}
    ]


@router.get("/health-distribution")
async def get_health_distribution() -> List[Dict]:
    """Sağlık durumu dağılımı"""
    return [
        {"name": "Sağlıklı", "value": 85, "color": "#22c55e"},
        {"name": "Tedavi Altında", "value": 8, "color": "#eab308"},
        {"name": "Kritik", "value": 3, "color": "#ef4444"},
        {"name": "Karantina", "value": 4, "color": "#8b5cf6"}
    ]


@router.delete("/{report_id}")
async def delete_report(report_id: str) -> Dict:
    """Raporu sil"""
    for i, report in enumerate(demo_reports):
        if report["id"] == report_id:
            deleted = demo_reports.pop(i)
            return {"message": "Rapor silindi", "report": deleted}
    raise HTTPException(status_code=404, detail="Rapor bulunamadı")
