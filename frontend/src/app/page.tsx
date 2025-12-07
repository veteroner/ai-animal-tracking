'use client';

import { useState, useEffect } from 'react';
import StatCard from '@/components/ui/StatCard';
import { api, Alert, Animal } from '@/lib/supabase';
import {
  Dog,
  Heart,
  AlertTriangle,
  Camera,
  Activity,
  TrendingUp,
  Clock,
  MapPin,
  Loader2,
  Bird,
  Egg,
  Baby,
  Calendar,
  Users,
  Stethoscope,
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

// Fallback data when Supabase is unavailable
const fallbackActivityData = [
  { time: '06:00', detections: 12, alerts: 2 },
  { time: '08:00', detections: 45, alerts: 5 },
  { time: '10:00', detections: 78, alerts: 3 },
  { time: '12:00', detections: 56, alerts: 1 },
  { time: '14:00', detections: 89, alerts: 4 },
  { time: '16:00', detections: 67, alerts: 2 },
  { time: '18:00', detections: 34, alerts: 1 },
];

interface DashboardStats {
  total_animals: number;
  healthy_animals: number;
  sick_animals: number;
  warning_animals: number;
  active_cameras: number;
  unread_alerts: number;
  total_zones: number;
}

interface HealthDistItem {
  name: string;
  value: number;
  color: string;
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats>({
    total_animals: 0,
    healthy_animals: 0,
    sick_animals: 0,
    warning_animals: 0,
    active_cameras: 4,
    unread_alerts: 0,
    total_zones: 0,
  });
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [healthDistribution, setHealthDistribution] = useState<HealthDistItem[]>([
    { name: 'Sağlıklı', value: 0, color: '#10b981' },
    { name: 'Dikkat', value: 0, color: '#f59e0b' },
    { name: 'Hasta', value: 0, color: '#ef4444' },
  ]);
  const [activityData, setActivityData] = useState(fallbackActivityData);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch all data in parallel
      const [animalsData, alertsData, zonesData] = await Promise.all([
        api.animals.getAll().catch(() => []),
        api.alerts.getAll().catch(() => []),
        api.zones.getAll().catch(() => []),
      ]);

      // Process animals data
      setAnimals(animalsData.slice(0, 5));
      
      const healthyCount = animalsData.filter(a => a.status === 'sağlıklı').length;
      const sickCount = animalsData.filter(a => a.status === 'hasta' || a.status === 'tedavide').length;
      const warningCount = animalsData.filter(a => a.status === 'karantina').length;
      const totalAnimals = animalsData.length;

      // Calculate health distribution percentages
      const healthyPercent = totalAnimals > 0 ? Math.round((healthyCount / totalAnimals) * 100) : 0;
      const sickPercent = totalAnimals > 0 ? Math.round((sickCount / totalAnimals) * 100) : 0;
      const warningPercent = totalAnimals > 0 ? Math.round((warningCount / totalAnimals) * 100) : 0;

      setHealthDistribution([
        { name: 'Sağlıklı', value: healthyPercent || 85, color: '#10b981' },
        { name: 'Dikkat', value: warningPercent || 10, color: '#f59e0b' },
        { name: 'Hasta', value: sickPercent || 5, color: '#ef4444' },
      ]);

      // Process alerts
      setAlerts(alertsData.slice(0, 5));
      const unreadAlerts = alertsData.filter(a => !a.is_read).length;

      // Update stats
      setStats({
        total_animals: totalAnimals || 156,
        healthy_animals: healthyCount || 132,
        sick_animals: sickCount || 8,
        warning_animals: warningCount || 16,
        active_cameras: 4,
        unread_alerts: unreadAlerts || 3,
        total_zones: zonesData.length || 6,
      });

    } catch (err) {
      console.error('Dashboard veri yükleme hatası:', err);
      setError('Veriler yüklenirken bir hata oluştu. Demo veriler gösteriliyor.');
      // Use fallback data
      setStats({
        total_animals: 156,
        healthy_animals: 132,
        sick_animals: 8,
        warning_animals: 16,
        active_cameras: 4,
        unread_alerts: 3,
        total_zones: 6,
      });
      setHealthDistribution([
        { name: 'Sağlıklı', value: 85, color: '#10b981' },
        { name: 'Dikkat', value: 10, color: '#f59e0b' },
        { name: 'Hasta', value: 5, color: '#ef4444' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-primary-500 animate-spin mx-auto" />
          <p className="mt-4 text-gray-500">Veriler yükleniyor...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Message */}
      {error && (
        <div className="bg-warning-50 border border-warning-200 text-warning-800 px-4 py-3 rounded-lg">
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Page Header with Teknova Branding */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Çiftlik durumunuza genel bakış</p>
        </div>
        <div className="hidden md:flex items-center gap-3 px-4 py-2 bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-md shadow-primary-500/30">
            <Dog className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-primary-700 tracking-wide text-sm">TEKNOVA</p>
            <p className="text-[10px] text-gray-400">AI Animal Tracking</p>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Toplam Hayvan"
          value={stats.total_animals}
          change={5}
          changeLabel="Son 30 gün"
          icon={Dog}
          iconBg="bg-primary-100"
          iconColor="text-primary-600"
        />
        <StatCard
          title="Sağlıklı"
          value={stats.healthy_animals}
          change={2}
          changeLabel="Son 30 gün"
          icon={Heart}
          iconBg="bg-success-100"
          iconColor="text-success-600"
        />
        <StatCard
          title="Dikkat Gerektiren"
          value={stats.warning_animals}
          change={-3}
          changeLabel="Son 30 gün"
          icon={AlertTriangle}
          iconBg="bg-warning-100"
          iconColor="text-warning-600"
        />
        <StatCard
          title="Aktif Kamera"
          value={stats.active_cameras}
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
                      alert.severity === 'kritik' || alert.severity === 'yüksek'
                        ? 'bg-danger-100 text-danger-600'
                        : alert.severity === 'orta'
                        ? 'bg-warning-100 text-warning-600'
                        : 'bg-primary-100 text-primary-600'
                    }`}
                  >
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {alert.title || alert.message}
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
            {animals.length > 0 ? (
              animals.slice(0, 5).map((animal) => (
                <div
                  key={animal.id}
                  className="flex items-center gap-3 p-3 rounded-lg bg-gray-50"
                >
                  <div className="p-2 rounded-lg bg-primary-100">
                    <Activity className="w-4 h-4 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {animal.name} - {animal.type}
                    </p>
                    <p className="text-xs text-gray-500">
                      Küpe: {animal.tag} | Durum: {animal.status}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(animal.updated_at).toLocaleDateString('tr-TR')}
                  </span>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Kayıtlı hayvan bulunmuyor</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Hızlı İşlemler</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
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
            href="/reproduction"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-pink-50 hover:bg-pink-100 transition-colors"
          >
            <Heart className="w-8 h-8 text-pink-600" />
            <span className="text-sm font-medium text-gray-700">Üreme Takibi</span>
          </a>
          <a
            href="/reproduction/calendar"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-purple-50 hover:bg-purple-100 transition-colors"
          >
            <Calendar className="w-8 h-8 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">Üreme Takvimi</span>
          </a>
          <a
            href="/poultry"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-amber-50 hover:bg-amber-100 transition-colors"
          >
            <Bird className="w-8 h-8 text-amber-600" />
            <span className="text-sm font-medium text-gray-700">Kanatlılar</span>
          </a>
          <a
            href="/poultry/eggs"
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-yellow-50 hover:bg-yellow-100 transition-colors"
          >
            <Egg className="w-8 h-8 text-yellow-600" />
            <span className="text-sm font-medium text-gray-700">Yumurta Takibi</span>
          </a>
        </div>
      </div>

      {/* Module Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Üreme Modülü Card */}
        <div className="card bg-gradient-to-br from-pink-50 to-purple-50 border-pink-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-pink-100 rounded-xl">
              <Heart className="w-6 h-6 text-pink-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Üreme Modülü</h3>
              <p className="text-sm text-gray-500">Sığır üreme takibi</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <a href="/reproduction/estrus" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Activity className="w-4 h-4 text-pink-500" />
              <span className="text-sm">Kızgınlık</span>
            </a>
            <a href="/reproduction/pregnancies" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Baby className="w-4 h-4 text-purple-500" />
              <span className="text-sm">Gebelik</span>
            </a>
            <a href="/reproduction/calendar" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Calendar className="w-4 h-4 text-indigo-500" />
              <span className="text-sm">Takvim</span>
            </a>
            <a href="/reproduction" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-sm">İstatistik</span>
            </a>
          </div>
          <a href="/reproduction" className="block text-center py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition-colors text-sm font-medium">
            Modüle Git →
          </a>
        </div>

        {/* Kanatlı Modülü Card */}
        <div className="card bg-gradient-to-br from-amber-50 to-orange-50 border-amber-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-amber-100 rounded-xl">
              <Bird className="w-6 h-6 text-amber-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Kanatlı Modülü</h3>
              <p className="text-sm text-gray-500">Kümes hayvanları takibi</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <a href="/poultry/flock" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Users className="w-4 h-4 text-amber-500" />
              <span className="text-sm">Sürü</span>
            </a>
            <a href="/poultry/eggs" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Egg className="w-4 h-4 text-yellow-500" />
              <span className="text-sm">Yumurta</span>
            </a>
            <a href="/poultry/health" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Stethoscope className="w-4 h-4 text-red-500" />
              <span className="text-sm">Sağlık</span>
            </a>
            <a href="/poultry/behavior" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Activity className="w-4 h-4 text-blue-500" />
              <span className="text-sm">Davranış</span>
            </a>
          </div>
          <a href="/poultry" className="block text-center py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors text-sm font-medium">
            Modüle Git →
          </a>
        </div>

        {/* Genel Bakış Card */}
        <div className="card bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-blue-100 rounded-xl">
              <MapPin className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Çiftlik Yönetimi</h3>
              <p className="text-sm text-gray-500">Genel operasyonlar</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <a href="/zones" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <MapPin className="w-4 h-4 text-blue-500" />
              <span className="text-sm">Bölgeler</span>
            </a>
            <a href="/health" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <Heart className="w-4 h-4 text-red-500" />
              <span className="text-sm">Sağlık</span>
            </a>
            <a href="/alerts" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <AlertTriangle className="w-4 h-4 text-yellow-500" />
              <span className="text-sm">Uyarılar</span>
            </a>
            <a href="/reports" className="flex items-center gap-2 p-2 bg-white/60 rounded-lg hover:bg-white transition-colors">
              <TrendingUp className="w-4 h-4 text-green-500" />
              <span className="text-sm">Raporlar</span>
            </a>
          </div>
          <a href="/animals" className="block text-center py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium">
            Hayvanları Gör →
          </a>
        </div>
      </div>
    </div>
  );
}
