'use client';

import { useState } from 'react';
import {
  AlertTriangle,
  Filter,
  Bell,
  MapPin,
  Thermometer,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';

interface Alert {
  id: number;
  animal_id?: number;
  animal_tag?: string;
  alert_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  status: 'active' | 'acknowledged' | 'resolved';
  created_at: string;
}

const mockAlerts: Alert[] = [
  { id: 1, animal_id: 1, animal_tag: 'TR-001', alert_type: 'health', severity: 'high', message: 'Anormal vücut sıcaklığı tespit edildi (40.5°C)', status: 'active', created_at: '2024-12-02T10:30:00' },
  { id: 2, animal_id: 3, animal_tag: 'TR-003', alert_type: 'behavior', severity: 'medium', message: 'Anormal hareket paterni tespit edildi', status: 'active', created_at: '2024-12-02T10:15:00' },
  { id: 3, alert_type: 'zone', severity: 'critical', message: '3 hayvan tehlikeli bölgeye girdi', status: 'active', created_at: '2024-12-02T09:45:00' },
  { id: 4, animal_id: 5, animal_tag: 'TR-005', alert_type: 'health', severity: 'high', message: 'Hayvan 24 saattir yem yemedi', status: 'acknowledged', created_at: '2024-12-01T18:00:00' },
  { id: 5, alert_type: 'system', severity: 'low', message: 'Kamera 2 bağlantısı zayıf', status: 'resolved', created_at: '2024-12-01T14:00:00' },
  { id: 6, animal_id: 2, animal_tag: 'TR-002', alert_type: 'behavior', severity: 'medium', message: 'Sürüden ayrılma davranışı', status: 'resolved', created_at: '2024-12-01T11:00:00' },
];

const severityConfig = {
  low: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Düşük' },
  medium: { bg: 'bg-warning-100', text: 'text-warning-600', label: 'Orta' },
  high: { bg: 'bg-danger-100', text: 'text-danger-600', label: 'Yüksek' },
  critical: { bg: 'bg-danger-200', text: 'text-danger-700', label: 'Kritik' },
};

const typeConfig = {
  health: { icon: Thermometer, label: 'Sağlık' },
  behavior: { icon: Activity, label: 'Davranış' },
  zone: { icon: MapPin, label: 'Bölge' },
  system: { icon: Bell, label: 'Sistem' },
};

const statusConfig = {
  active: { bg: 'bg-danger-100', text: 'text-danger-600', label: 'Aktif' },
  acknowledged: { bg: 'bg-warning-100', text: 'text-warning-600', label: 'İnceleniyor' },
  resolved: { bg: 'bg-success-100', text: 'text-success-600', label: 'Çözüldü' },
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const filteredAlerts = alerts.filter(alert => {
    const matchesSeverity = filterSeverity === 'all' || alert.severity === filterSeverity;
    const matchesStatus = filterStatus === 'all' || alert.status === filterStatus;
    return matchesSeverity && matchesStatus;
  });

  const updateStatus = (id: number, status: Alert['status']) => {
    setAlerts(alerts.map(a => a.id === id ? { ...a, status } : a));
  };

  const activeCount = alerts.filter(a => a.status === 'active').length;
  const criticalCount = alerts.filter(a => a.severity === 'critical' && a.status === 'active').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Uyarılar</h1>
          <p className="text-gray-500 mt-1">{activeCount} aktif uyarı</p>
        </div>
        
        {criticalCount > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 bg-danger-100 text-danger-700 rounded-lg">
            <AlertTriangle className="w-5 h-5" />
            <span className="font-medium">{criticalCount} kritik uyarı!</span>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-danger-600">{alerts.filter(a => a.status === 'active').length}</p>
          <p className="text-sm text-gray-500">Aktif</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-warning-600">{alerts.filter(a => a.status === 'acknowledged').length}</p>
          <p className="text-sm text-gray-500">İnceleniyor</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-success-600">{alerts.filter(a => a.status === 'resolved').length}</p>
          <p className="text-sm text-gray-500">Çözüldü</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-gray-900">{alerts.length}</p>
          <p className="text-sm text-gray-500">Toplam</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="sm:w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Önem Derecesi</label>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="input"
            >
              <option value="all">Tümü</option>
              <option value="critical">Kritik</option>
              <option value="high">Yüksek</option>
              <option value="medium">Orta</option>
              <option value="low">Düşük</option>
            </select>
          </div>
          <div className="sm:w-48">
            <label className="block text-sm font-medium text-gray-700 mb-1">Durum</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input"
            >
              <option value="all">Tümü</option>
              <option value="active">Aktif</option>
              <option value="acknowledged">İnceleniyor</option>
              <option value="resolved">Çözüldü</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3">
        {filteredAlerts.length === 0 ? (
          <div className="card text-center py-12">
            <AlertTriangle className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Uyarı bulunmuyor</p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const severity = severityConfig[alert.severity];
            const type = typeConfig[alert.alert_type as keyof typeof typeConfig] || typeConfig.system;
            const status = statusConfig[alert.status];
            const Icon = type.icon;
            
            return (
              <div key={alert.id} className={`card border-l-4 ${severity.bg.replace('100', '300')}`}>
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-xl ${severity.bg}`}>
                    <Icon className={`w-5 h-5 ${severity.text}`} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className={`badge ${severity.bg} ${severity.text}`}>
                        {severity.label}
                      </span>
                      <span className="badge bg-gray-100 text-gray-600">
                        {type.label}
                      </span>
                      <span className={`badge ${status.bg} ${status.text}`}>
                        {status.label}
                      </span>
                      {alert.animal_tag && (
                        <span className="text-sm text-gray-500">
                          Hayvan: {alert.animal_tag}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-gray-900 font-medium">{alert.message}</p>
                    
                    <div className="flex items-center gap-4 mt-3">
                      <div className="flex items-center gap-1 text-sm text-gray-500">
                        <Clock className="w-4 h-4" />
                        {new Date(alert.created_at).toLocaleString('tr-TR')}
                      </div>
                    </div>
                  </div>
                  
                  {/* Actions */}
                  <div className="flex flex-col gap-2">
                    {alert.status === 'active' && (
                      <button
                        onClick={() => updateStatus(alert.id, 'acknowledged')}
                        className="btn-secondary text-sm py-1.5 px-3"
                      >
                        İncele
                      </button>
                    )}
                    {alert.status === 'acknowledged' && (
                      <button
                        onClick={() => updateStatus(alert.id, 'resolved')}
                        className="btn-primary text-sm py-1.5 px-3"
                      >
                        Çözüldü
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
