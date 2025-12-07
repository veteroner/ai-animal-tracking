'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Activity,
  TrendingUp,
  AlertTriangle,
  Clock,
  RefreshCw,
  ChevronRight,
  Eye,
  Search,
  Bird,
  Utensils,
  Droplets,
  Moon,
  Sun,
  Wind,
} from 'lucide-react';
import { api, isSupabaseConfigured, PoultryBehaviorLog } from '@/lib/supabase';

const behaviorInfo: Record<string, { label: string; icon: typeof Activity; color: string; isAbnormal: boolean }> = {
  feeding: { label: 'Yem Yeme', icon: Utensils, color: 'text-green-600', isAbnormal: false },
  drinking: { label: 'Su İçme', icon: Droplets, color: 'text-blue-600', isAbnormal: false },
  roosting: { label: 'Tüneme', icon: Moon, color: 'text-purple-600', isAbnormal: false },
  nesting: { label: 'Yumurtlama', icon: Bird, color: 'text-pink-600', isAbnormal: false },
  dust_bathing: { label: 'Toz Banyosu', icon: Wind, color: 'text-amber-600', isAbnormal: false },
  preening: { label: 'Tüy Temizleme', icon: Bird, color: 'text-cyan-600', isAbnormal: false },
  walking: { label: 'Yürüme', icon: Activity, color: 'text-gray-600', isAbnormal: false },
  running: { label: 'Koşma', icon: Activity, color: 'text-orange-600', isAbnormal: false },
  resting: { label: 'Dinlenme', icon: Moon, color: 'text-indigo-600', isAbnormal: false },
  foraging: { label: 'Yiyecek Arama', icon: Search, color: 'text-green-700', isAbnormal: false },
  flocking: { label: 'Sürü Hareketi', icon: Bird, color: 'text-teal-600', isAbnormal: false },
  mating: { label: 'Çiftleşme', icon: Bird, color: 'text-red-500', isAbnormal: false },
  brooding: { label: 'Kuluçka', icon: Bird, color: 'text-purple-700', isAbnormal: false },
  feather_pecking: { label: 'Tüy Gagalama', icon: AlertTriangle, color: 'text-yellow-600', isAbnormal: true },
  panic: { label: 'Panik', icon: AlertTriangle, color: 'text-red-600', isAbnormal: true },
  lethargy: { label: 'Durgunluk', icon: Clock, color: 'text-gray-500', isAbnormal: true },
  isolation: { label: 'İzolasyon', icon: Eye, color: 'text-orange-700', isAbnormal: true },
};

interface BehaviorStat {
  behavior: string;
  count: number;
  percentage: number;
}

export default function PoultryBehaviorPage() {
  const [logs, setLogs] = useState<PoultryBehaviorLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [behaviorStats, setBehaviorStats] = useState<BehaviorStat[]>([]);
  const [abnormalCount, setAbnormalCount] = useState(0);
  const [timeRange, setTimeRange] = useState<number>(24); // hours
  const [filterBehavior, setFilterBehavior] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, [timeRange]);

  const loadData = async () => {
    try {
      setLoading(true);
      
      if (!isSupabaseConfigured()) {
        // Demo verileri
        const demoLogs: PoultryBehaviorLog[] = [
          { id: 'b-1', poultry_id: 'ptr-001', behavior: 'feeding', duration_seconds: 120, intensity: 'medium', is_abnormal: false, timestamp: new Date().toISOString() },
          { id: 'b-2', poultry_id: 'ptr-002', behavior: 'drinking', duration_seconds: 30, intensity: 'low', is_abnormal: false, timestamp: new Date(Date.now() - 1800000).toISOString() },
          { id: 'b-3', poultry_id: 'ptr-003', behavior: 'dust_bathing', duration_seconds: 900, intensity: 'high', is_abnormal: false, timestamp: new Date(Date.now() - 3600000).toISOString() },
          { id: 'b-4', poultry_id: 'ptr-001', behavior: 'roosting', duration_seconds: 600, intensity: 'low', is_abnormal: false, timestamp: new Date(Date.now() - 5400000).toISOString() },
          { id: 'b-5', poultry_id: 'ptr-005', behavior: 'brooding', duration_seconds: 7200, intensity: 'high', is_abnormal: false, timestamp: new Date(Date.now() - 7200000).toISOString() },
          { id: 'b-6', poultry_id: 'ptr-002', behavior: 'foraging', duration_seconds: 450, intensity: 'medium', is_abnormal: false, timestamp: new Date(Date.now() - 9000000).toISOString() },
          { id: 'b-7', poultry_id: 'ptr-007', behavior: 'lethargy', duration_seconds: 1200, intensity: 'low', is_abnormal: true, timestamp: new Date(Date.now() - 10800000).toISOString() },
          { id: 'b-8', poultry_id: 'ptr-004', behavior: 'walking', duration_seconds: 300, intensity: 'medium', is_abnormal: false, timestamp: new Date(Date.now() - 12600000).toISOString() },
        ];
        
        setLogs(demoLogs);
        
        // İstatistikler
        const stats: BehaviorStat[] = [
          { behavior: 'feeding', count: 450, percentage: 35.2 },
          { behavior: 'resting', count: 320, percentage: 25.0 },
          { behavior: 'foraging', count: 280, percentage: 21.9 },
          { behavior: 'roosting', count: 120, percentage: 9.4 },
          { behavior: 'drinking', count: 80, percentage: 6.3 },
          { behavior: 'dust_bathing', count: 28, percentage: 2.2 },
        ];
        setBehaviorStats(stats);
        setAbnormalCount(5);
        
        setLoading(false);
        return;
      }

      const [behaviorLogs, abnormalLogs] = await Promise.all([
        api.poultryBehavior.getAll(undefined, timeRange),
        api.poultryBehavior.getAbnormal(),
      ]);
      
      setLogs(behaviorLogs);
      setAbnormalCount(abnormalLogs.length);
      
      // İstatistik hesapla
      const behaviorCounts: Record<string, number> = {};
      behaviorLogs.forEach(log => {
        behaviorCounts[log.behavior] = (behaviorCounts[log.behavior] || 0) + 1;
      });
      
      const total = behaviorLogs.length || 1;
      const stats = Object.entries(behaviorCounts)
        .map(([behavior, count]) => ({
          behavior,
          count,
          percentage: (count / total) * 100,
        }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 10);
      
      setBehaviorStats(stats);
    } catch (error) {
      console.error('Error loading behavior data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = filterBehavior === 'all' 
    ? logs 
    : filterBehavior === 'abnormal'
    ? logs.filter(l => l.is_abnormal)
    : logs.filter(l => l.behavior === filterBehavior);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}dk`;
    return `${Math.floor(seconds / 3600)}sa ${Math.floor((seconds % 3600) / 60)}dk`;
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/poultry" className="hover:text-foreground">Kanatlı</Link>
            <ChevronRight className="w-4 h-4" />
            <span>Davranış Analizi</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">📊 Davranış Analizi</h1>
          <p className="text-muted-foreground mt-1">Kanatlı hayvan davranış paternleri ve anomali tespiti</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="px-4 py-2 border rounded-lg bg-background"
          >
            <option value={6}>Son 6 Saat</option>
            <option value={12}>Son 12 Saat</option>
            <option value={24}>Son 24 Saat</option>
            <option value={48}>Son 48 Saat</option>
            <option value={168}>Son 7 Gün</option>
          </select>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-muted transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Yenile
          </button>
        </div>
      </div>

      {/* Özet Kartları */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-card rounded-xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
            <TrendingUp className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-3xl font-bold">{logs.length}</div>
          <div className="text-sm text-muted-foreground">Toplam Kayıt</div>
          <div className="text-xs text-muted-foreground mt-1">Son {timeRange} saat</div>
        </div>

        <div className="bg-card rounded-xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <Utensils className="w-6 h-6 text-green-600" />
            </div>
          </div>
          <div className="text-3xl font-bold">{behaviorStats[0]?.count || 0}</div>
          <div className="text-sm text-muted-foreground">En Yaygın</div>
          <div className="text-xs text-muted-foreground mt-1">
            {behaviorInfo[behaviorStats[0]?.behavior]?.label || '-'}
          </div>
        </div>

        <div className="bg-card rounded-xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertTriangle className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <div className="text-3xl font-bold">{abnormalCount}</div>
          <div className="text-sm text-muted-foreground">Anormal Davranış</div>
          <div className="text-xs text-muted-foreground mt-1">Dikkat gerektirir</div>
        </div>

        <div className="bg-card rounded-xl border p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <div className="text-3xl font-bold">{behaviorStats.length}</div>
          <div className="text-sm text-muted-foreground">Davranış Türü</div>
          <div className="text-xs text-muted-foreground mt-1">Tespit edildi</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Davranış Dağılımı */}
        <div className="bg-card rounded-xl border p-6">
          <h2 className="text-lg font-semibold mb-6">Davranış Dağılımı</h2>
          <div className="space-y-4">
            {behaviorStats.map((stat, index) => {
              const info = behaviorInfo[stat.behavior];
              const Icon = info?.icon || Activity;
              
              return (
                <div key={index}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${info?.color || 'text-gray-600'}`} />
                      <span className="text-sm">{info?.label || stat.behavior}</span>
                    </div>
                    <span className="text-sm font-medium">{stat.count}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${info?.isAbnormal ? 'bg-red-500' : 'bg-primary'}`}
                      style={{ width: `${stat.percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Davranış Logları */}
        <div className="lg:col-span-2 bg-card rounded-xl border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold">Son Davranış Kayıtları</h2>
            <select
              value={filterBehavior}
              onChange={(e) => setFilterBehavior(e.target.value)}
              className="px-3 py-1 text-sm border rounded-lg bg-background"
            >
              <option value="all">Tümü</option>
              <option value="abnormal">⚠️ Anormal</option>
              <option value="feeding">Yem Yeme</option>
              <option value="drinking">Su İçme</option>
              <option value="roosting">Tüneme</option>
              <option value="nesting">Yumurtlama</option>
              <option value="dust_bathing">Toz Banyosu</option>
              <option value="foraging">Yiyecek Arama</option>
            </select>
          </div>
          <div className="divide-y max-h-[400px] overflow-y-auto">
            {filteredLogs.map((log) => {
              const info = behaviorInfo[log.behavior];
              const Icon = info?.icon || Activity;
              
              return (
                <div key={log.id} className={`p-4 hover:bg-muted/50 ${log.is_abnormal ? 'bg-red-50' : ''}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${log.is_abnormal ? 'bg-red-100' : 'bg-muted'}`}>
                        <Icon className={`w-5 h-5 ${info?.color || 'text-gray-600'}`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{info?.label || log.behavior}</span>
                          {log.is_abnormal && (
                            <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-xs">
                              Anormal
                            </span>
                          )}
                          {log.intensity && (
                            <span className={`px-2 py-0.5 rounded-full text-xs ${
                              log.intensity === 'high' ? 'bg-orange-100 text-orange-700' :
                              log.intensity === 'medium' ? 'bg-blue-100 text-blue-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {log.intensity === 'high' ? 'Yüksek' : log.intensity === 'medium' ? 'Orta' : 'Düşük'}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Süre: {formatDuration(log.duration_seconds)}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-muted-foreground">
                        {new Date(log.timestamp).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(log.timestamp).toLocaleDateString('tr-TR')}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            
            {filteredLogs.length === 0 && (
              <div className="p-8 text-center text-muted-foreground">
                Kayıt bulunamadı
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Anormal Davranış Uyarısı */}
      {abnormalCount > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-800">Anormal Davranış Tespit Edildi</h3>
              <p className="text-sm text-yellow-700 mt-1">
                Son {timeRange} saat içinde {abnormalCount} adet anormal davranış kaydı oluşturuldu. 
                Bu davranışlar stres, sağlık sorunu veya çevresel faktörlerden kaynaklanıyor olabilir.
              </p>
              <div className="flex gap-2 mt-3">
                <button 
                  onClick={() => setFilterBehavior('abnormal')}
                  className="px-3 py-1 bg-yellow-200 text-yellow-800 rounded-lg text-sm hover:bg-yellow-300"
                >
                  Detayları Gör
                </button>
                <Link 
                  href="/poultry/health"
                  className="px-3 py-1 border border-yellow-300 text-yellow-800 rounded-lg text-sm hover:bg-yellow-100"
                >
                  Sağlık Sayfası
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
