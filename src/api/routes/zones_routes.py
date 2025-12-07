"""
Bölge API Routes
"""

from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/zones", tags=["Bölgeler"])


# Demo veriler
demo_zones = [
    {
        "id": 1,
        "name": "Ana Otlak",
        "zone_type": "grazing",
        "animal_count": 45,
        "capacity": 60,
        "status": "normal",
        "description": "Günlük otlatma alanı",
        "coordinates": [39.9334, 32.8597],
        "radius": 80
    },
    {
        "id": 2,
        "name": "Ahır 1",
        "zone_type": "shelter",
        "animal_count": 32,
        "capacity": 40,
        "status": "normal",
        "description": "Ana barınak",
        "coordinates": [39.9320, 32.8580],
        "radius": 40
    },
    {
        "id": 3,
        "name": "Ahır 2",
        "zone_type": "shelter",
        "animal_count": 28,
        "capacity": 30,
        "status": "warning",
        "description": "Yavru barınağı",
        "coordinates": [39.9340, 32.8610],
        "radius": 35
    },
    {
        "id": 4,
        "name": "Su Kaynağı",
        "zone_type": "water",
        "animal_count": 12,
        "capacity": 20,
        "status": "normal",
        "description": "Ana su deposu",
        "coordinates": [39.9350, 32.8590],
        "radius": 25
    },
    {
        "id": 5,
        "name": "Yem Deposu",
        "zone_type": "feeding",
        "animal_count": 8,
        "capacity": 15,
        "status": "normal",
        "description": "Yem dağıtım noktası",
        "coordinates": [39.9325, 32.8605],
        "radius": 30
    },
    {
        "id": 6,
        "name": "Tehlikeli Bölge",
        "zone_type": "restricted",
        "animal_count": 3,
        "capacity": 0,
        "status": "danger",
        "description": "Yasak bölge - inşaat alanı",
        "coordinates": [39.9360, 32.8620],
        "radius": 60
    }
]


@router.get("/stats")
async def get_zones_stats() -> Dict:
    """Bölge istatistikleri"""
    total_animals = sum(z["animal_count"] for z in demo_zones)
    total_capacity = sum(z["capacity"] for z in demo_zones)
    warnings = len([z for z in demo_zones if z["status"] != "normal"])
    
    return {
        "total_zones": len(demo_zones),
        "total_animals": total_animals,
        "total_capacity": total_capacity,
        "warnings": warnings
    }


@router.get("")
async def get_zones() -> List[Dict]:
    """Tüm bölgeleri listele"""
    return demo_zones


@router.get("/{zone_id}")
async def get_zone(zone_id: int) -> Dict:
    """Belirli bir bölgeyi getir"""
    for zone in demo_zones:
        if zone["id"] == zone_id:
            return zone
    raise HTTPException(status_code=404, detail="Bölge bulunamadı")


@router.post("")
async def create_zone(zone: Dict) -> Dict:
    """Yeni bölge oluştur"""
    new_id = max(z["id"] for z in demo_zones) + 1
    new_zone = {
        "id": new_id,
        **zone
    }
    demo_zones.append(new_zone)
    return new_zone


@router.put("/{zone_id}")
async def update_zone(zone_id: int, zone: Dict) -> Dict:
    """Bölge güncelle"""
    for i, z in enumerate(demo_zones):
        if z["id"] == zone_id:
            demo_zones[i] = {"id": zone_id, **zone}
            return demo_zones[i]
    raise HTTPException(status_code=404, detail="Bölge bulunamadı")


@router.delete("/{zone_id}")
async def delete_zone(zone_id: int) -> Dict:
    """Bölge sil"""
    for i, z in enumerate(demo_zones):
        if z["id"] == zone_id:
            deleted = demo_zones.pop(i)
            return {"message": "Bölge silindi", "zone": deleted}
    raise HTTPException(status_code=404, detail="Bölge bulunamadı")


@router.get("/{zone_id}/animals")
async def get_zone_animals(zone_id: int) -> Dict:
    """Bölgedeki hayvanları listele"""
    for zone in demo_zones:
        if zone["id"] == zone_id:
            return {
                "zone_id": zone_id,
                "zone_name": zone["name"],
                "animals": [
                    {"id": 1, "tag": "TR-001", "name": "Sarıkız"},
                    {"id": 2, "tag": "TR-002", "name": "Karabaş"},
                    {"id": 3, "tag": "TR-003", "name": "Benekli"},
                ]
            }
    raise HTTPException(status_code=404, detail="Bölge bulunamadı")
