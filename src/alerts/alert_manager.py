# src/alerts/alert_manager.py
"""
Alert Manager for AI Animal Tracking System.

Handles:
- Real-time alert generation
- Rule-based alerting
- Alert notifications (email, SMS, webhook)
- Alert history and management
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import json
import uuid

logger = logging.getLogger(__name__)


class AlertType(Enum):
    """Types of alerts."""
    # Health Alerts
    HEALTH_CRITICAL = "health_critical"
    HEALTH_WARNING = "health_warning"
    LAMENESS_DETECTED = "lameness_detected"
    LOW_BCS = "low_bcs"
    HIGH_BCS = "high_bcs"
    
    # Behavior Alerts
    ABNORMAL_BEHAVIOR = "abnormal_behavior"
    INACTIVITY = "inactivity"
    EXCESSIVE_ACTIVITY = "excessive_activity"
    ISOLATION = "isolation"
    AGGRESSION = "aggression"
    
    # Zone Alerts
    ZONE_ENTRY = "zone_entry"
    ZONE_EXIT = "zone_exit"
    RESTRICTED_ZONE = "restricted_zone"
    GEOFENCE_BREACH = "geofence_breach"
    
    # Count Alerts
    COUNT_LOW = "count_low"
    COUNT_HIGH = "count_high"
    MISSING_ANIMAL = "missing_animal"
    NEW_ANIMAL = "new_animal"
    
    # System Alerts
    CAMERA_OFFLINE = "camera_offline"
    CAMERA_ONLINE = "camera_online"
    PROCESSING_ERROR = "processing_error"
    STORAGE_WARNING = "storage_warning"
    
    # Custom
    CUSTOM = "custom"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    id: str
    name: str
    alert_type: AlertType
    severity: AlertSeverity
    enabled: bool = True
    
    # Conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Thresholds
    threshold_value: Optional[float] = None
    threshold_duration: Optional[float] = None  # seconds
    
    # Cooldown (prevent alert spam)
    cooldown_seconds: float = 300.0  # 5 minutes default
    
    # Schedule (optional - only alert during specific times)
    schedule_start: Optional[str] = None  # HH:MM format
    schedule_end: Optional[str] = None
    
    # Target filters
    target_cameras: Optional[List[str]] = None
    target_animals: Optional[List[str]] = None
    target_species: Optional[List[str]] = None
    
    # Notification settings
    notification_channels: List[str] = field(default_factory=lambda: ["log"])
    notification_template: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class AlertNotification:
    """Alert notification instance."""
    id: str
    rule_id: str
    alert_type: AlertType
    severity: AlertSeverity
    
    # Content
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    camera_id: Optional[str] = None
    animal_id: Optional[str] = None
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    # State
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'camera_id': self.camera_id,
            'animal_id': self.animal_id,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'resolved': self.resolved
        }


class AlertHistory:
    """Stores alert history."""
    
    def __init__(self, max_size: int = 10000):
        """Initialize alert history.
        
        Args:
            max_size: Maximum number of alerts to store
        """
        self.max_size = max_size
        self.alerts: deque = deque(maxlen=max_size)
        self._lock = threading.Lock()
        
        # Indices for fast lookup
        self._by_type: Dict[AlertType, List[str]] = {}
        self._by_severity: Dict[AlertSeverity, List[str]] = {}
        self._by_camera: Dict[str, List[str]] = {}
        self._by_animal: Dict[str, List[str]] = {}
        self._unacknowledged: Set[str] = set()
        self._unresolved: Set[str] = set()
    
    def add(self, alert: AlertNotification) -> None:
        """Add an alert to history."""
        with self._lock:
            self.alerts.append(alert)
            
            # Update indices
            if alert.alert_type not in self._by_type:
                self._by_type[alert.alert_type] = []
            self._by_type[alert.alert_type].append(alert.id)
            
            if alert.severity not in self._by_severity:
                self._by_severity[alert.severity] = []
            self._by_severity[alert.severity].append(alert.id)
            
            if alert.camera_id:
                if alert.camera_id not in self._by_camera:
                    self._by_camera[alert.camera_id] = []
                self._by_camera[alert.camera_id].append(alert.id)
            
            if alert.animal_id:
                if alert.animal_id not in self._by_animal:
                    self._by_animal[alert.animal_id] = []
                self._by_animal[alert.animal_id].append(alert.id)
            
            if not alert.acknowledged:
                self._unacknowledged.add(alert.id)
            
            if not alert.resolved:
                self._unresolved.add(alert.id)
    
    def get(self, alert_id: str) -> Optional[AlertNotification]:
        """Get alert by ID."""
        with self._lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    return alert
        return None
    
    def acknowledge(self, alert_id: str, acknowledged_by: Optional[str] = None) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.acknowledged = True
                    alert.acknowledged_at = datetime.now()
                    alert.acknowledged_by = acknowledged_by
                    self._unacknowledged.discard(alert_id)
                    return True
        return False
    
    def resolve(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            for alert in self.alerts:
                if alert.id == alert_id:
                    alert.resolved = True
                    alert.resolved_at = datetime.now()
                    self._unresolved.discard(alert_id)
                    return True
        return False
    
    def get_recent(self, count: int = 100) -> List[AlertNotification]:
        """Get recent alerts."""
        with self._lock:
            return list(self.alerts)[-count:]
    
    def get_unacknowledged(self) -> List[AlertNotification]:
        """Get unacknowledged alerts."""
        with self._lock:
            return [a for a in self.alerts if a.id in self._unacknowledged]
    
    def get_unresolved(self) -> List[AlertNotification]:
        """Get unresolved alerts."""
        with self._lock:
            return [a for a in self.alerts if a.id in self._unresolved]
    
    def get_by_type(self, alert_type: AlertType) -> List[AlertNotification]:
        """Get alerts by type."""
        with self._lock:
            ids = self._by_type.get(alert_type, [])
            return [a for a in self.alerts if a.id in ids]
    
    def get_by_severity(self, severity: AlertSeverity) -> List[AlertNotification]:
        """Get alerts by severity."""
        with self._lock:
            ids = self._by_severity.get(severity, [])
            return [a for a in self.alerts if a.id in ids]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        with self._lock:
            stats = {
                'total': len(self.alerts),
                'unacknowledged': len(self._unacknowledged),
                'unresolved': len(self._unresolved),
                'by_type': {t.value: len(ids) for t, ids in self._by_type.items()},
                'by_severity': {s.value: len(ids) for s, ids in self._by_severity.items()}
            }
            return stats


class NotificationChannel(ABC):
    """Abstract notification channel."""
    
    @abstractmethod
    def send(self, alert: AlertNotification) -> bool:
        """Send notification."""
        pass


class LogNotificationChannel(NotificationChannel):
    """Log-based notification channel."""
    
    def send(self, alert: AlertNotification) -> bool:
        """Log the alert."""
        severity_map = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.ERROR,
            AlertSeverity.EMERGENCY: logging.CRITICAL
        }
        
        level = severity_map.get(alert.severity, logging.INFO)
        logger.log(level, f"[ALERT] {alert.title}: {alert.message}")
        return True


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel."""
    
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        """Initialize webhook channel.
        
        Args:
            url: Webhook URL
            headers: Optional HTTP headers
        """
        self.url = url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    def send(self, alert: AlertNotification) -> bool:
        """Send webhook notification."""
        try:
            import urllib.request
            
            data = json.dumps(alert.to_dict()).encode('utf-8')
            request = urllib.request.Request(
                self.url,
                data=data,
                headers=self.headers,
                method='POST'
            )
            
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False


class CallbackNotificationChannel(NotificationChannel):
    """Callback-based notification channel."""
    
    def __init__(self, callback: Callable[[AlertNotification], None]):
        """Initialize callback channel.
        
        Args:
            callback: Function to call with alert
        """
        self.callback = callback
    
    def send(self, alert: AlertNotification) -> bool:
        """Call the callback with alert."""
        try:
            self.callback(alert)
            return True
        except Exception as e:
            logger.error(f"Callback notification failed: {e}")
            return False


class AlertManager:
    """Manages alerts for the tracking system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize AlertManager.
        
        Args:
            config: Optional configuration
        """
        self.config = config or {}
        self.rules: Dict[str, AlertRule] = {}
        self.history = AlertHistory()
        self.channels: Dict[str, NotificationChannel] = {}
        
        # Cooldown tracking
        self._rule_last_triggered: Dict[str, datetime] = {}
        
        # Event callbacks
        self._alert_callbacks: List[Callable[[AlertNotification], None]] = []
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Background processor
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Alert queue for async processing
        self._alert_queue: deque = deque(maxlen=1000)
        
        # Setup default channels
        self._setup_default_channels()
        
        # Setup default rules
        self._setup_default_rules()
        
        logger.info("AlertManager initialized")
    
    def _setup_default_channels(self) -> None:
        """Setup default notification channels."""
        self.channels['log'] = LogNotificationChannel()
    
    def _setup_default_rules(self) -> None:
        """Setup default alert rules."""
        default_rules = [
            # Health rules
            AlertRule(
                id="health_critical",
                name="Critical Health Alert",
                alert_type=AlertType.HEALTH_CRITICAL,
                severity=AlertSeverity.CRITICAL,
                conditions={'health_score': {'lt': 30}},
                threshold_value=30.0,
                cooldown_seconds=600
            ),
            AlertRule(
                id="health_warning",
                name="Health Warning",
                alert_type=AlertType.HEALTH_WARNING,
                severity=AlertSeverity.WARNING,
                conditions={'health_score': {'lt': 60}},
                threshold_value=60.0,
                cooldown_seconds=1800
            ),
            AlertRule(
                id="lameness_detected",
                name="Lameness Detected",
                alert_type=AlertType.LAMENESS_DETECTED,
                severity=AlertSeverity.WARNING,
                conditions={'lameness_score': {'gt': 2}},
                threshold_value=2.0,
                cooldown_seconds=3600
            ),
            
            # Behavior rules
            AlertRule(
                id="inactivity",
                name="Animal Inactivity",
                alert_type=AlertType.INACTIVITY,
                severity=AlertSeverity.WARNING,
                conditions={'behavior': 'resting', 'duration_minutes': {'gt': 120}},
                threshold_duration=7200,  # 2 hours
                cooldown_seconds=3600
            ),
            AlertRule(
                id="abnormal_behavior",
                name="Abnormal Behavior Detected",
                alert_type=AlertType.ABNORMAL_BEHAVIOR,
                severity=AlertSeverity.WARNING,
                cooldown_seconds=1800
            ),
            
            # Zone rules
            AlertRule(
                id="restricted_zone",
                name="Restricted Zone Entry",
                alert_type=AlertType.RESTRICTED_ZONE,
                severity=AlertSeverity.CRITICAL,
                cooldown_seconds=60
            ),
            
            # System rules
            AlertRule(
                id="camera_offline",
                name="Camera Offline",
                alert_type=AlertType.CAMERA_OFFLINE,
                severity=AlertSeverity.CRITICAL,
                cooldown_seconds=300
            ),
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        with self._lock:
            self.rules[rule.id] = rule
            logger.debug(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        with self._lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable an alert rule."""
        with self._lock:
            if rule_id in self.rules:
                self.rules[rule_id].enabled = True
                return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable an alert rule."""
        with self._lock:
            if rule_id in self.rules:
                self.rules[rule_id].enabled = False
                return True
        return False
    
    def add_channel(self, name: str, channel: NotificationChannel) -> None:
        """Add a notification channel."""
        self.channels[name] = channel
    
    def add_webhook(self, name: str, url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """Add a webhook notification channel."""
        self.add_channel(name, WebhookNotificationChannel(url, headers))
    
    def add_callback(self, callback: Callable[[AlertNotification], None]) -> None:
        """Add an alert callback."""
        self._alert_callbacks.append(callback)
    
    def _can_trigger(self, rule: AlertRule) -> bool:
        """Check if a rule can be triggered (cooldown check)."""
        if not rule.enabled:
            return False
        
        last_triggered = self._rule_last_triggered.get(rule.id)
        if last_triggered is None:
            return True
        
        elapsed = (datetime.now() - last_triggered).total_seconds()
        return elapsed >= rule.cooldown_seconds
    
    def _check_schedule(self, rule: AlertRule) -> bool:
        """Check if current time is within rule schedule."""
        if not rule.schedule_start or not rule.schedule_end:
            return True
        
        now = datetime.now().time()
        start = datetime.strptime(rule.schedule_start, "%H:%M").time()
        end = datetime.strptime(rule.schedule_end, "%H:%M").time()
        
        if start <= end:
            return start <= now <= end
        else:  # Overnight schedule
            return now >= start or now <= end
    
    def _create_notification(
        self,
        rule: AlertRule,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        camera_id: Optional[str] = None,
        animal_id: Optional[str] = None
    ) -> AlertNotification:
        """Create an alert notification."""
        return AlertNotification(
            id=str(uuid.uuid4()),
            rule_id=rule.id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            title=title,
            message=message,
            details=details or {},
            camera_id=camera_id,
            animal_id=animal_id
        )
    
    def trigger(
        self,
        rule_id: str,
        title: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        camera_id: Optional[str] = None,
        animal_id: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Manually trigger an alert.
        
        Args:
            rule_id: Rule ID to trigger
            title: Alert title
            message: Alert message
            details: Additional details
            camera_id: Camera ID if applicable
            animal_id: Animal ID if applicable
            
        Returns:
            AlertNotification if triggered, None if cooldown active
        """
        rule = self.rules.get(rule_id)
        if not rule:
            logger.warning(f"Alert rule not found: {rule_id}")
            return None
        
        if not self._can_trigger(rule):
            logger.debug(f"Alert rule in cooldown: {rule_id}")
            return None
        
        if not self._check_schedule(rule):
            logger.debug(f"Alert rule outside schedule: {rule_id}")
            return None
        
        # Create notification
        notification = self._create_notification(
            rule, title, message, details, camera_id, animal_id
        )
        
        # Update rule state
        with self._lock:
            rule.last_triggered = datetime.now()
            rule.trigger_count += 1
            self._rule_last_triggered[rule_id] = rule.last_triggered
        
        # Add to history
        self.history.add(notification)
        
        # Send notifications
        self._send_notifications(notification, rule.notification_channels)
        
        # Call callbacks
        for callback in self._alert_callbacks:
            try:
                callback(notification)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        logger.info(f"Alert triggered: {title}")
        return notification
    
    def trigger_by_type(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        severity: Optional[AlertSeverity] = None,
        details: Optional[Dict[str, Any]] = None,
        camera_id: Optional[str] = None,
        animal_id: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Trigger an alert by type.
        
        Finds the first matching enabled rule for the alert type.
        """
        for rule in self.rules.values():
            if rule.alert_type == alert_type and rule.enabled:
                return self.trigger(
                    rule.id, title, message, details, camera_id, animal_id
                )
        
        # If no rule found, create ad-hoc alert
        notification = AlertNotification(
            id=str(uuid.uuid4()),
            rule_id="ad_hoc",
            alert_type=alert_type,
            severity=severity or AlertSeverity.INFO,
            title=title,
            message=message,
            details=details or {},
            camera_id=camera_id,
            animal_id=animal_id
        )
        
        self.history.add(notification)
        self._send_notifications(notification, ['log'])
        return notification
    
    def _send_notifications(
        self,
        notification: AlertNotification,
        channel_names: List[str]
    ) -> None:
        """Send notification to specified channels."""
        for name in channel_names:
            channel = self.channels.get(name)
            if channel:
                try:
                    channel.send(notification)
                except Exception as e:
                    logger.error(f"Failed to send notification via {name}: {e}")
    
    # Health-related alerts
    def check_health_alert(
        self,
        animal_id: str,
        health_score: float,
        camera_id: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Check and trigger health alerts."""
        if health_score < 30:
            return self.trigger(
                "health_critical",
                f"Critical Health Alert - Animal {animal_id}",
                f"Health score critically low: {health_score:.1f}%",
                details={'health_score': health_score},
                camera_id=camera_id,
                animal_id=animal_id
            )
        elif health_score < 60:
            return self.trigger(
                "health_warning",
                f"Health Warning - Animal {animal_id}",
                f"Health score low: {health_score:.1f}%",
                details={'health_score': health_score},
                camera_id=camera_id,
                animal_id=animal_id
            )
        return None
    
    def check_lameness_alert(
        self,
        animal_id: str,
        lameness_score: int,
        camera_id: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Check and trigger lameness alerts."""
        if lameness_score > 2:
            severity_text = {3: "Moderate", 4: "Severe", 5: "Critical"}
            return self.trigger(
                "lameness_detected",
                f"Lameness Detected - Animal {animal_id}",
                f"{severity_text.get(lameness_score, 'Unknown')} lameness detected (score: {lameness_score})",
                details={'lameness_score': lameness_score},
                camera_id=camera_id,
                animal_id=animal_id
            )
        return None
    
    # Behavior alerts
    def check_inactivity_alert(
        self,
        animal_id: str,
        inactivity_duration: float,
        camera_id: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Check and trigger inactivity alerts."""
        rule = self.rules.get("inactivity")
        if rule and inactivity_duration > (rule.threshold_duration or 7200):
            hours = inactivity_duration / 3600
            return self.trigger(
                "inactivity",
                f"Inactivity Alert - Animal {animal_id}",
                f"Animal has been inactive for {hours:.1f} hours",
                details={'inactivity_duration': inactivity_duration},
                camera_id=camera_id,
                animal_id=animal_id
            )
        return None
    
    def trigger_abnormal_behavior(
        self,
        animal_id: str,
        behavior: str,
        details: Optional[Dict[str, Any]] = None,
        camera_id: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Trigger abnormal behavior alert."""
        return self.trigger(
            "abnormal_behavior",
            f"Abnormal Behavior - Animal {animal_id}",
            f"Abnormal behavior detected: {behavior}",
            details=details,
            camera_id=camera_id,
            animal_id=animal_id
        )
    
    # Zone alerts
    def trigger_zone_alert(
        self,
        animal_id: str,
        zone_name: str,
        alert_type: AlertType,
        camera_id: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Trigger zone-related alert."""
        if alert_type == AlertType.RESTRICTED_ZONE:
            return self.trigger(
                "restricted_zone",
                f"Restricted Zone Entry - Animal {animal_id}",
                f"Animal entered restricted zone: {zone_name}",
                details={'zone': zone_name},
                camera_id=camera_id,
                animal_id=animal_id
            )
        return self.trigger_by_type(
            alert_type,
            f"Zone Alert - Animal {animal_id}",
            f"Zone event: {alert_type.value} - {zone_name}",
            details={'zone': zone_name},
            camera_id=camera_id,
            animal_id=animal_id
        )
    
    # System alerts
    def trigger_camera_offline(
        self,
        camera_id: str,
        reason: Optional[str] = None
    ) -> Optional[AlertNotification]:
        """Trigger camera offline alert."""
        return self.trigger(
            "camera_offline",
            f"Camera Offline - {camera_id}",
            f"Camera {camera_id} is offline" + (f": {reason}" if reason else ""),
            details={'reason': reason},
            camera_id=camera_id
        )
    
    def trigger_camera_online(
        self,
        camera_id: str
    ) -> Optional[AlertNotification]:
        """Trigger camera online alert."""
        return self.trigger_by_type(
            AlertType.CAMERA_ONLINE,
            f"Camera Online - {camera_id}",
            f"Camera {camera_id} is back online",
            severity=AlertSeverity.INFO,
            camera_id=camera_id
        )
    
    # History access
    def get_history(self) -> AlertHistory:
        """Get alert history."""
        return self.history
    
    def get_recent_alerts(self, count: int = 100) -> List[AlertNotification]:
        """Get recent alerts."""
        return self.history.get_recent(count)
    
    def get_unacknowledged(self) -> List[AlertNotification]:
        """Get unacknowledged alerts."""
        return self.history.get_unacknowledged()
    
    def acknowledge(self, alert_id: str, acknowledged_by: Optional[str] = None) -> bool:
        """Acknowledge an alert."""
        return self.history.acknowledge(alert_id, acknowledged_by)
    
    def resolve(self, alert_id: str) -> bool:
        """Resolve an alert."""
        return self.history.resolve(alert_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get alert statistics."""
        stats = self.history.get_statistics()
        stats['rules'] = {
            'total': len(self.rules),
            'enabled': sum(1 for r in self.rules.values() if r.enabled),
            'triggered_total': sum(r.trigger_count for r in self.rules.values())
        }
        return stats
    
    def get_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return list(self.rules.values())
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a specific alert rule."""
        return self.rules.get(rule_id)
    
    def export_config(self) -> Dict[str, Any]:
        """Export alert configuration."""
        return {
            'rules': [
                {
                    'id': r.id,
                    'name': r.name,
                    'alert_type': r.alert_type.value,
                    'severity': r.severity.value,
                    'enabled': r.enabled,
                    'conditions': r.conditions,
                    'threshold_value': r.threshold_value,
                    'threshold_duration': r.threshold_duration,
                    'cooldown_seconds': r.cooldown_seconds,
                    'schedule_start': r.schedule_start,
                    'schedule_end': r.schedule_end,
                    'notification_channels': r.notification_channels
                }
                for r in self.rules.values()
            ],
            'channels': list(self.channels.keys())
        }
    
    def import_config(self, config: Dict[str, Any]) -> None:
        """Import alert configuration."""
        for rule_data in config.get('rules', []):
            rule = AlertRule(
                id=rule_data['id'],
                name=rule_data['name'],
                alert_type=AlertType(rule_data['alert_type']),
                severity=AlertSeverity(rule_data['severity']),
                enabled=rule_data.get('enabled', True),
                conditions=rule_data.get('conditions', {}),
                threshold_value=rule_data.get('threshold_value'),
                threshold_duration=rule_data.get('threshold_duration'),
                cooldown_seconds=rule_data.get('cooldown_seconds', 300),
                schedule_start=rule_data.get('schedule_start'),
                schedule_end=rule_data.get('schedule_end'),
                notification_channels=rule_data.get('notification_channels', ['log'])
            )
            self.add_rule(rule)
