'use client';

import { useState, useEffect } from 'react';
import StatCard from '@/components/ui/StatCard';
import { getSystemStats, getAlerts, getRecentDetections, type SystemStats, type Alert, type Detection } from '@/lib/api';
import {
  Dog,
  Heart,
  AlertTriangle,
  Camera,
  Activity,
  TrendingUp,
  Clock,
  MapPin,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

// Mock data for charts (will be replaced with real API data)
const activityData = [
  { time: '06:00', detections: 12, alerts: 2 },
  { time: '08:00', detections: 45, alerts: 5 },
  { time: '10:00', detections: 78, alerts: 3 },
  { time: '12:00', detections: 56, alerts: 1 },
  { time: '14:00', detections: 89, alerts: 4 },
  { time: '16:00', detections: 67, alerts: 2 },
  { time: '18:00', detections: 34, alerts: 1 },
];

const healthDistribution = [
  { name: 'Sağlıklı', value: 85, color: '#10b981' },
  { name: 'Dikkat', value: 10, color: '#f59e0b' },
  { name: 'Hasta', value: 5, color: '#ef4444' },
];

export default function Dashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [recentDetections, setRecentDetections] = useState<Detection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, alertsRes, detectionsRes] = await Promise.all([
          getSystemStats().catch(() => ({ data: null })),
          getAlerts(true).catch(() => ({ data: [] })),
          getRecentDetections(5).catch(() => ({ data: [] })),
        ]);

        if (statsRes.data) setStats(statsRes.data);
        if (alertsRes.data) setAlerts(alertsRes.data);
        if (detectionsRes.data) setRecentDetections(detectionsRes.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Default stats if API is not available
  const displayStats = stats || {
    total_animals: 156,
    healthy_animals: 132,
    sick_animals: 8,
    warning_animals: 16,
    active_cameras: 4,
    unread_alerts: 3,
    total_zones: 6,
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Çiftlik durumunuza genel bakış</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Toplam Hayvan"
          value={displayStats.total_animals}
          change={5}
          changeLabel="Son 30 gün"
          icon={Dog}
          iconBg="bg-primary-100"
          iconColor="text-primary-600"
        />
        <StatCard
          title="Sağlıklı"
          value={displayStats.healthy_animals}
          change={2}
          changeLabel="Son 30 gün"
          icon={Heart}
          iconBg="bg-success-100"
          iconColor="text-success-600"
        />
        <StatCard
          title="Dikkat Gerektiren"
          value={displayStats.warning_animals}
          change={-3}
          changeLabel="Son 30 gün"
          icon={AlertTriangle}
          iconBg="bg-warning-100"
          iconColor="text-warning-600"
        />
        <StatCard
          title="Aktif Kamera"
          value={displayStats.active_cameras}
          icon={Camera}
          iconBg="bg-gray-100"
          iconColor="text-gray-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Chart */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Günlük Aktivite</h2>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-primary-500" />
                <span className="text-gray-600">Tespit</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-warning-500" />
                <span className="text-gray-600">Uyarı</span>
              </div>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="time" stroke="#9ca3af" fontSize={12} />
                <YAxis stroke="#9ca3af" fontSize={12} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="detections"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="alerts"
                  stroke="#f59e0b"
                  fill="#f59e0b"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Health Distribution */}
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Sağlık Dağılımı</h2>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={healthDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {healthDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {healthDistribution.map((item) => (
              <div key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-gray-600">{item.name}</span>
                </div>
                <span className="font-medium text-gray-900">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Alerts */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Son Uyarılar</h2>
            <a href="/alerts" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              Tümünü Gör
            </a>
          </div>
          <div className="space-y-3">
            {alerts.length > 0 ? (
              alerts.slice(0, 5).map((alert) => (
                <div
                  key={alert.id}
                  className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <div
                    className={`p-2 rounded-lg ${
                      alert.severity === 'high'
                        ? 'bg-danger-100 text-danger-600'
                        : alert.severity === 'medium'
                        ? 'bg-warning-100 text-warning-600'
                        : 'bg-primary-100 text-primary-600'
                    }`}
                  >
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {alert.message}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(alert.created_at).toLocaleString('tr-TR')}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Aktif uyarı bulunmuyor</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Son Aktiviteler</h2>
            <a href="/animals" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
              Tümünü Gör
            </a>
          </div>
          <div className="space-y-3">
            {recentDetections.length > 0 ? (
              recentDetections.map((detection) => (
                <div
                  key={detection.id}
                  className="flex items-center gap-3 p-3 rounded-lg bg-gray-50"
                >
                  <div className="p-2 rounded-lg bg-primary-100">
                    <Activity className="w-4 h-4 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {detection.class_name} tespit edildi
                    </p>
                    <p className="text-xs text-gray-500">
                      Güven: {(detection.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(detection.detection_time).toLocaleTimeString('tr-TR')}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Son aktivite bulunmuyor</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Hızlı İşlemler</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <a
            href="/camera"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <Camera className="w-8 h-8 text-primary-600" />
            <span className="text-sm font-medium text-gray-700">Canlı İzle</span>
          </a>
          <a
            href="/animals/new"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <Dog className="w-8 h-8 text-success-600" />
            <span className="text-sm font-medium text-gray-700">Hayvan Ekle</span>
          </a>
          <a
            href="/health/new"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <Heart className="w-8 h-8 text-danger-600" />
            <span className="text-sm font-medium text-gray-700">Sağlık Kaydı</span>
          </a>
          <a
            href="/zones"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors"
          >
            <MapPin className="w-8 h-8 text-warning-600" />
            <span className="text-sm font-medium text-gray-700">Bölge Haritası</span>
          </a>
        </div>
      </div>
    </div>
  );
}
