"""
Bildirim API Routes
"""

from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/notifications", tags=["Bildirimler"])


# Demo veriler
demo_notifications = [
    {
        "id": "1",
        "title": "Acil Sağlık Uyarısı",
        "message": "TR-005 kodlu hayvan için acil veteriner müdahalesi gerekiyor",
        "type": "alert",
        "timestamp": "2024-12-02T10:30:00",
        "read": False,
        "priority": "high"
    },
    {
        "id": "2",
        "title": "Kızgınlık Tespiti",
        "message": "TR-012 kodlu inek kızgınlık belirtileri gösteriyor",
        "type": "reproduction",
        "timestamp": "2024-12-02T09:15:00",
        "read": False,
        "priority": "medium"
    },
    {
        "id": "3",
        "title": "Yemleme Hatırlatması",
        "message": "Ahır 2 için öğle yemlemesi zamanı",
        "type": "feeding",
        "timestamp": "2024-12-02T12:00:00",
        "read": True,
        "priority": "low"
    },
    {
        "id": "4",
        "title": "Aşı Zamanı",
        "message": "5 hayvan için şap aşısı zamanı geldi",
        "type": "health",
        "timestamp": "2024-12-01T14:00:00",
        "read": True,
        "priority": "medium"
    },
    {
        "id": "5",
        "title": "Sistem Güncellemesi",
        "message": "Yeni özellikler eklendi",
        "type": "system",
        "timestamp": "2024-12-01T08:00:00",
        "read": True,
        "priority": "low"
    },
    {
        "id": "6",
        "title": "Doğum Yaklaşıyor",
        "message": "TR-008 için tahmini doğum tarihi 3 gün içinde",
        "type": "reproduction",
        "timestamp": "2024-11-30T16:00:00",
        "read": True,
        "priority": "high"
    }
]


@router.get("")
async def get_notifications(
    type: Optional[str] = Query(None, description="Bildirim tipi filtresi"),
    unread_only: bool = Query(False, description="Sadece okunmamış bildirimler")
) -> List[Dict]:
    """Tüm bildirimleri listele"""
    result = demo_notifications.copy()
    
    if type:
        result = [n for n in result if n["type"] == type]
    
    if unread_only:
        result = [n for n in result if not n["read"]]
    
    return result


@router.get("/stats")
async def get_notification_stats() -> Dict:
    """Bildirim istatistikleri"""
    unread = len([n for n in demo_notifications if not n["read"]])
    by_type = {}
    for n in demo_notifications:
        by_type[n["type"]] = by_type.get(n["type"], 0) + 1
    
    return {
        "total": len(demo_notifications),
        "unread": unread,
        "by_type": by_type
    }


@router.get("/{notification_id}")
async def get_notification(notification_id: str) -> Dict:
    """Belirli bir bildirimi getir"""
    for notification in demo_notifications:
        if notification["id"] == notification_id:
            return notification
    raise HTTPException(status_code=404, detail="Bildirim bulunamadı")


@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str) -> Dict:
    """Bildirimi okundu olarak işaretle"""
    for notification in demo_notifications:
        if notification["id"] == notification_id:
            notification["read"] = True
            return {"message": "Bildirim okundu olarak işaretlendi", "notification": notification}
    raise HTTPException(status_code=404, detail="Bildirim bulunamadı")


@router.put("/read-all")
async def mark_all_as_read() -> Dict:
    """Tüm bildirimleri okundu olarak işaretle"""
    for notification in demo_notifications:
        notification["read"] = True
    return {"message": "Tüm bildirimler okundu olarak işaretlendi"}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str) -> Dict:
    """Bildirimi sil"""
    for i, notification in enumerate(demo_notifications):
        if notification["id"] == notification_id:
            deleted = demo_notifications.pop(i)
            return {"message": "Bildirim silindi", "notification": deleted}
    raise HTTPException(status_code=404, detail="Bildirim bulunamadı")


@router.delete("")
async def clear_all_notifications() -> Dict:
    """Tüm bildirimleri sil"""
    demo_notifications.clear()
    return {"message": "Tüm bildirimler silindi"}
