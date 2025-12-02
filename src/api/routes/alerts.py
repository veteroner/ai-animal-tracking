# src/api/routes/alerts.py
"""Alert routes for AI Animal Tracking System API."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ============ Pydantic Models ============

class AlertTypeEnum(str, Enum):
    """Alert type enumeration."""
    HEALTH_CRITICAL = "health_critical"
    HEALTH_WARNING = "health_warning"
    LAMENESS_DETECTED = "lameness_detected"
    LOW_BCS = "low_bcs"
    HIGH_BCS = "high_bcs"
    ABNORMAL_BEHAVIOR = "abnormal_behavior"
    INACTIVITY = "inactivity"
    EXCESSIVE_ACTIVITY = "excessive_activity"
    ISOLATION = "isolation"
    AGGRESSION = "aggression"
    ZONE_ENTRY = "zone_entry"
    ZONE_EXIT = "zone_exit"
    RESTRICTED_ZONE = "restricted_zone"
    GEOFENCE_BREACH = "geofence_breach"
    COUNT_LOW = "count_low"
    COUNT_HIGH = "count_high"
    MISSING_ANIMAL = "missing_animal"
    NEW_ANIMAL = "new_animal"
    CAMERA_OFFLINE = "camera_offline"
    CAMERA_ONLINE = "camera_online"
    PROCESSING_ERROR = "processing_error"
    STORAGE_WARNING = "storage_warning"
    CUSTOM = "custom"


class AlertSeverityEnum(str, Enum):
    """Alert severity enumeration."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertRuleCreate(BaseModel):
    """Model for creating an alert rule."""
    id: str = Field(..., description="Unique rule ID")
    name: str = Field(..., description="Rule name")
    alert_type: AlertTypeEnum
    severity: AlertSeverityEnum
    enabled: bool = True
    conditions: Dict[str, Any] = Field(default_factory=dict)
    threshold_value: Optional[float] = None
    threshold_duration: Optional[float] = None
    cooldown_seconds: float = 300.0
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    target_cameras: Optional[List[str]] = None
    target_animals: Optional[List[str]] = None
    target_species: Optional[List[str]] = None
    notification_channels: List[str] = ["log"]


class AlertRuleUpdate(BaseModel):
    """Model for updating an alert rule."""
    name: Optional[str] = None
    enabled: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    threshold_value: Optional[float] = None
    threshold_duration: Optional[float] = None
    cooldown_seconds: Optional[float] = None
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    notification_channels: Optional[List[str]] = None


class AlertRuleResponse(BaseModel):
    """Response model for alert rule."""
    id: str
    name: str
    alert_type: str
    severity: str
    enabled: bool
    conditions: Dict[str, Any]
    threshold_value: Optional[float]
    threshold_duration: Optional[float]
    cooldown_seconds: float
    schedule_start: Optional[str]
    schedule_end: Optional[str]
    notification_channels: List[str]
    trigger_count: int
    last_triggered: Optional[str]


class AlertResponse(BaseModel):
    """Response model for alert notification."""
    id: str
    rule_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    details: Dict[str, Any]
    camera_id: Optional[str]
    animal_id: Optional[str]
    timestamp: str
    acknowledged: bool
    acknowledged_at: Optional[str]
    acknowledged_by: Optional[str]
    resolved: bool
    resolved_at: Optional[str]


class AlertTriggerRequest(BaseModel):
    """Request model for triggering an alert."""
    rule_id: str
    title: str
    message: str
    details: Optional[Dict[str, Any]] = None
    camera_id: Optional[str] = None
    animal_id: Optional[str] = None


class AlertAcknowledgeRequest(BaseModel):
    """Request model for acknowledging an alert."""
    acknowledged_by: Optional[str] = None


class WebhookConfig(BaseModel):
    """Webhook configuration model."""
    name: str
    url: str
    headers: Optional[Dict[str, str]] = None


class AlertStatistics(BaseModel):
    """Alert statistics response."""
    total: int
    unacknowledged: int
    unresolved: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    rules: Dict[str, Any]


# ============ Mock Alert Manager ============
# In production, this would be injected via dependency injection

_mock_alerts: List[Dict[str, Any]] = []
_mock_rules: Dict[str, Dict[str, Any]] = {
    "health_critical": {
        "id": "health_critical",
        "name": "Critical Health Alert",
        "alert_type": "health_critical",
        "severity": "critical",
        "enabled": True,
        "conditions": {"health_score": {"lt": 30}},
        "threshold_value": 30.0,
        "threshold_duration": None,
        "cooldown_seconds": 600,
        "schedule_start": None,
        "schedule_end": None,
        "notification_channels": ["log"],
        "trigger_count": 0,
        "last_triggered": None
    },
    "health_warning": {
        "id": "health_warning",
        "name": "Health Warning",
        "alert_type": "health_warning",
        "severity": "warning",
        "enabled": True,
        "conditions": {"health_score": {"lt": 60}},
        "threshold_value": 60.0,
        "threshold_duration": None,
        "cooldown_seconds": 1800,
        "schedule_start": None,
        "schedule_end": None,
        "notification_channels": ["log"],
        "trigger_count": 0,
        "last_triggered": None
    },
    "lameness_detected": {
        "id": "lameness_detected",
        "name": "Lameness Detected",
        "alert_type": "lameness_detected",
        "severity": "warning",
        "enabled": True,
        "conditions": {"lameness_score": {"gt": 2}},
        "threshold_value": 2.0,
        "threshold_duration": None,
        "cooldown_seconds": 3600,
        "schedule_start": None,
        "schedule_end": None,
        "notification_channels": ["log"],
        "trigger_count": 0,
        "last_triggered": None
    },
    "camera_offline": {
        "id": "camera_offline",
        "name": "Camera Offline",
        "alert_type": "camera_offline",
        "severity": "critical",
        "enabled": True,
        "conditions": {},
        "threshold_value": None,
        "threshold_duration": None,
        "cooldown_seconds": 300,
        "schedule_start": None,
        "schedule_end": None,
        "notification_channels": ["log"],
        "trigger_count": 0,
        "last_triggered": None
    }
}


# ============ Alert Rules Endpoints ============

@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    enabled_only: bool = Query(False, description="Return only enabled rules")
):
    """List all alert rules."""
    rules = list(_mock_rules.values())
    if enabled_only:
        rules = [r for r in rules if r["enabled"]]
    return rules


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(rule_id: str):
    """Get a specific alert rule."""
    if rule_id not in _mock_rules:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
    return _mock_rules[rule_id]


@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(rule: AlertRuleCreate):
    """Create a new alert rule."""
    if rule.id in _mock_rules:
        raise HTTPException(status_code=400, detail=f"Rule already exists: {rule.id}")
    
    rule_data = {
        "id": rule.id,
        "name": rule.name,
        "alert_type": rule.alert_type.value,
        "severity": rule.severity.value,
        "enabled": rule.enabled,
        "conditions": rule.conditions,
        "threshold_value": rule.threshold_value,
        "threshold_duration": rule.threshold_duration,
        "cooldown_seconds": rule.cooldown_seconds,
        "schedule_start": rule.schedule_start,
        "schedule_end": rule.schedule_end,
        "notification_channels": rule.notification_channels,
        "trigger_count": 0,
        "last_triggered": None
    }
    _mock_rules[rule.id] = rule_data
    return rule_data


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: str, update: AlertRuleUpdate):
    """Update an alert rule."""
    if rule_id not in _mock_rules:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
    
    rule = _mock_rules[rule_id]
    update_data = update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if value is not None:
            rule[key] = value
    
    return rule


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule."""
    if rule_id not in _mock_rules:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
    
    del _mock_rules[rule_id]
    return {"message": f"Rule deleted: {rule_id}"}


@router.post("/rules/{rule_id}/enable")
async def enable_alert_rule(rule_id: str):
    """Enable an alert rule."""
    if rule_id not in _mock_rules:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
    
    _mock_rules[rule_id]["enabled"] = True
    return {"message": f"Rule enabled: {rule_id}"}


@router.post("/rules/{rule_id}/disable")
async def disable_alert_rule(rule_id: str):
    """Disable an alert rule."""
    if rule_id not in _mock_rules:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
    
    _mock_rules[rule_id]["enabled"] = False
    return {"message": f"Rule disabled: {rule_id}"}


# ============ Alerts Endpoints ============

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[AlertSeverityEnum] = None,
    alert_type: Optional[AlertTypeEnum] = None,
    camera_id: Optional[str] = None,
    animal_id: Optional[str] = None,
    unacknowledged_only: bool = False,
    unresolved_only: bool = False
):
    """List alerts with optional filters."""
    alerts = _mock_alerts.copy()
    
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity.value]
    if alert_type:
        alerts = [a for a in alerts if a["alert_type"] == alert_type.value]
    if camera_id:
        alerts = [a for a in alerts if a.get("camera_id") == camera_id]
    if animal_id:
        alerts = [a for a in alerts if a.get("animal_id") == animal_id]
    if unacknowledged_only:
        alerts = [a for a in alerts if not a["acknowledged"]]
    if unresolved_only:
        alerts = [a for a in alerts if not a["resolved"]]
    
    return alerts[-limit:]


@router.get("/recent", response_model=List[AlertResponse])
async def get_recent_alerts(
    count: int = Query(10, ge=1, le=100)
):
    """Get most recent alerts."""
    return _mock_alerts[-count:]


@router.get("/unacknowledged", response_model=List[AlertResponse])
async def get_unacknowledged_alerts():
    """Get all unacknowledged alerts."""
    return [a for a in _mock_alerts if not a["acknowledged"]]


@router.get("/unresolved", response_model=List[AlertResponse])
async def get_unresolved_alerts():
    """Get all unresolved alerts."""
    return [a for a in _mock_alerts if not a["resolved"]]


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str):
    """Get a specific alert by ID."""
    for alert in _mock_alerts:
        if alert["id"] == alert_id:
            return alert
    raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")


@router.post("/trigger", response_model=AlertResponse, status_code=201)
async def trigger_alert(request: AlertTriggerRequest):
    """Manually trigger an alert."""
    if request.rule_id not in _mock_rules and request.rule_id != "ad_hoc":
        raise HTTPException(status_code=404, detail=f"Rule not found: {request.rule_id}")
    
    import uuid
    
    rule = _mock_rules.get(request.rule_id, {
        "alert_type": "custom",
        "severity": "info"
    })
    
    alert = {
        "id": str(uuid.uuid4()),
        "rule_id": request.rule_id,
        "alert_type": rule.get("alert_type", "custom"),
        "severity": rule.get("severity", "info"),
        "title": request.title,
        "message": request.message,
        "details": request.details or {},
        "camera_id": request.camera_id,
        "animal_id": request.animal_id,
        "timestamp": datetime.now().isoformat(),
        "acknowledged": False,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "resolved": False,
        "resolved_at": None
    }
    
    _mock_alerts.append(alert)
    
    # Update rule trigger count
    if request.rule_id in _mock_rules:
        _mock_rules[request.rule_id]["trigger_count"] += 1
        _mock_rules[request.rule_id]["last_triggered"] = alert["timestamp"]
    
    return alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(alert_id: str, request: AlertAcknowledgeRequest):
    """Acknowledge an alert."""
    for alert in _mock_alerts:
        if alert["id"] == alert_id:
            alert["acknowledged"] = True
            alert["acknowledged_at"] = datetime.now().isoformat()
            alert["acknowledged_by"] = request.acknowledged_by
            return alert
    raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    for alert in _mock_alerts:
        if alert["id"] == alert_id:
            alert["resolved"] = True
            alert["resolved_at"] = datetime.now().isoformat()
            return alert
    raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")


@router.post("/acknowledge-all")
async def acknowledge_all_alerts(request: AlertAcknowledgeRequest):
    """Acknowledge all unacknowledged alerts."""
    count = 0
    for alert in _mock_alerts:
        if not alert["acknowledged"]:
            alert["acknowledged"] = True
            alert["acknowledged_at"] = datetime.now().isoformat()
            alert["acknowledged_by"] = request.acknowledged_by
            count += 1
    return {"message": f"Acknowledged {count} alerts"}


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert from history."""
    global _mock_alerts
    initial_count = len(_mock_alerts)
    _mock_alerts = [a for a in _mock_alerts if a["id"] != alert_id]
    
    if len(_mock_alerts) == initial_count:
        raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")
    
    return {"message": f"Alert deleted: {alert_id}"}


# ============ Statistics Endpoints ============

@router.get("/statistics/summary", response_model=AlertStatistics)
async def get_alert_statistics():
    """Get alert statistics."""
    by_type: Dict[str, int] = {}
    by_severity: Dict[str, int] = {}
    
    for alert in _mock_alerts:
        alert_type = alert["alert_type"]
        severity = alert["severity"]
        
        by_type[alert_type] = by_type.get(alert_type, 0) + 1
        by_severity[severity] = by_severity.get(severity, 0) + 1
    
    return {
        "total": len(_mock_alerts),
        "unacknowledged": sum(1 for a in _mock_alerts if not a["acknowledged"]),
        "unresolved": sum(1 for a in _mock_alerts if not a["resolved"]),
        "by_type": by_type,
        "by_severity": by_severity,
        "rules": {
            "total": len(_mock_rules),
            "enabled": sum(1 for r in _mock_rules.values() if r["enabled"]),
            "triggered_total": sum(r["trigger_count"] for r in _mock_rules.values())
        }
    }


# ============ Notification Channels Endpoints ============

@router.get("/channels")
async def list_notification_channels():
    """List available notification channels."""
    return {
        "channels": ["log", "webhook", "callback"],
        "configured": ["log"]
    }


@router.post("/channels/webhook")
async def add_webhook_channel(config: WebhookConfig):
    """Add a webhook notification channel."""
    return {
        "message": f"Webhook channel added: {config.name}",
        "url": config.url
    }


@router.delete("/channels/{channel_name}")
async def remove_notification_channel(channel_name: str):
    """Remove a notification channel."""
    if channel_name == "log":
        raise HTTPException(status_code=400, detail="Cannot remove default log channel")
    return {"message": f"Channel removed: {channel_name}"}


# ============ Export/Import Endpoints ============

@router.get("/config/export")
async def export_alert_config():
    """Export alert configuration."""
    return {
        "rules": list(_mock_rules.values()),
        "channels": ["log"]
    }


@router.post("/config/import")
async def import_alert_config(config: Dict[str, Any]):
    """Import alert configuration."""
    imported = 0
    for rule_data in config.get("rules", []):
        rule_id = rule_data.get("id")
        if rule_id:
            _mock_rules[rule_id] = rule_data
            imported += 1
    return {"message": f"Imported {imported} rules"}
