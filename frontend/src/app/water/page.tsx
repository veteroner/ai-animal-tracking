'use client';

import { useState, useEffect } from 'react';
import {
  Droplets,
  Plus,
  Thermometer,
  Activity,
  AlertTriangle,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import { api, isSupabaseConfigured, WaterSource as SupabaseWaterSource } from '@/lib/supabase';

interface WaterSource {
  id: number;
  name: string;
  location: string;
  capacity: number;
  current_level: number;
  temperature?: number;
  quality: 'good' | 'moderate' | 'poor';
  last_check: string;
  status: 'active' | 'maintenance' | 'inactive';
}

const qualityConfig = {
  good: { label: 'İyi', color: 'text-success-600', bg: 'bg-success-100' },
  moderate: { label: 'Orta', color: 'text-warning-600', bg: 'bg-warning-100' },
  poor: { label: 'Kötü', color: 'text-danger-600', bg: 'bg-danger-100' },
};

const statusConfig = {
  active: { label: 'Aktif', color: 'text-success-600', bg: 'bg-success-100' },
  maintenance: { label: 'Bakımda', color: 'text-warning-600', bg: 'bg-warning-100' },
  inactive: { label: 'Pasif', color: 'text-gray-600', bg: 'bg-gray-100' },
};

// Map Supabase status to component status/quality
const mapWaterStatus = (status: string): { status: 'active' | 'maintenance' | 'inactive'; quality: 'good' | 'moderate' | 'poor' } => {
  const map: Record<string, { status: 'active' | 'maintenance' | 'inactive'; quality: 'good' | 'moderate' | 'poor' }> = {
    'aktif': { status: 'active', quality: 'good' },
    'düşük': { status: 'active', quality: 'moderate' },
    'kritik': { status: 'active', quality: 'poor' },
    'bakımda': { status: 'maintenance', quality: 'moderate' },
  };
  return map[status] || { status: 'active', quality: 'good' };
};

export default function WaterPage() {
  const [sources, setSources] = useState<WaterSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWaterSources();
  }, []);

  const loadWaterSources = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!isSupabaseConfigured()) {
        // Demo data when Supabase is not configured
        setSources([
          { id: 1, name: 'Ana Su Deposu', location: 'Merkez', capacity: 10000, current_level: 7500, temperature: 15, quality: 'good', last_check: '2024-12-02', status: 'active' },
          { id: 2, name: 'Otlak Sulağı 1', location: 'Kuzey Otlak', capacity: 2000, current_level: 1200, temperature: 18, quality: 'good', last_check: '2024-12-02', status: 'active' },
          { id: 3, name: 'Otlak Sulağı 2', location: 'Güney Otlak', capacity: 2000, current_level: 400, temperature: 20, quality: 'moderate', last_check: '2024-12-01', status: 'active' },
          { id: 4, name: 'Ahır Suluğu', location: 'Ahır 1', capacity: 500, current_level: 450, quality: 'good', last_check: '2024-12-02', status: 'active' },
          { id: 5, name: 'Yedek Depo', location: 'Depo Alanı', capacity: 5000, current_level: 5000, quality: 'good', last_check: '2024-11-30', status: 'maintenance' },
        ]);
        return;
      }

      const supabaseWater = await api.water.getAll();

      // Map Supabase water sources to component format
      const mappedSources: WaterSource[] = supabaseWater.map((w: SupabaseWaterSource, index: number) => {
        const statusQuality = mapWaterStatus(w.status);
        return {
          id: parseInt(w.id) || index + 1,
          name: w.name,
          location: w.type || 'Merkez',
          capacity: w.capacity || 1000,
          current_level: w.current_level || 0,
          quality: statusQuality.quality,
          last_check: w.last_cleaned || new Date().toISOString().split('T')[0],
          status: statusQuality.status,
        };
      });

      setSources(mappedSources.length > 0 ? mappedSources : [
        { id: 1, name: 'Ana Su Deposu', location: 'Merkez', capacity: 10000, current_level: 7500, quality: 'good', last_check: new Date().toISOString().split('T')[0], status: 'active' },
      ]);
    } catch (err) {
      console.error('Error loading water sources:', err);
      setError('Su kaynakları yüklenemedi');
      setSources([
        { id: 1, name: 'Demo Depo', location: 'Merkez', capacity: 5000, current_level: 2500, quality: 'good', last_check: new Date().toISOString().split('T')[0], status: 'active' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const totalCapacity = sources.reduce((sum, s) => sum + s.capacity, 0);
  const totalCurrent = sources.reduce((sum, s) => sum + s.current_level, 0);
  const lowLevelCount = sources.filter(s => (s.current_level / s.capacity) < 0.3).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Su Kaynakları</h1>
          <p className="text-gray-500 mt-1">{sources.length} kaynak tanımlı</p>
        </div>
        
        <button className="btn-primary flex items-center gap-2 w-fit">
          <Plus className="w-5 h-5" />
          Yeni Kaynak
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-primary-600">
            {Math.round(totalCurrent / 1000)}k L
          </p>
          <p className="text-sm text-gray-500">Mevcut Su</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-gray-900">
            {Math.round(totalCapacity / 1000)}k L
          </p>
          <p className="text-sm text-gray-500">Toplam Kapasite</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-success-600">
            {Math.round((totalCurrent / totalCapacity) * 100)}%
          </p>
          <p className="text-sm text-gray-500">Doluluk Oranı</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-warning-600">{lowLevelCount}</p>
          <p className="text-sm text-gray-500">Düşük Seviye</p>
        </div>
      </div>

      {/* Water Sources Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {sources.map((source) => {
          const quality = qualityConfig[source.quality];
          const status = statusConfig[source.status];
          const levelPercent = Math.round((source.current_level / source.capacity) * 100);
          const isLow = levelPercent < 30;
          
          return (
            <div key={source.id} className="card-hover">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className={`p-3 rounded-xl ${isLow ? 'bg-warning-100' : 'bg-primary-100'}`}>
                    <Droplets className={`w-5 h-5 ${isLow ? 'text-warning-600' : 'text-primary-600'}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{source.name}</h3>
                    <p className="text-sm text-gray-500">{source.location}</p>
                  </div>
                </div>
                <span className={`badge ${status.bg} ${status.color}`}>
                  {status.label}
                </span>
              </div>
              
              {/* Water Level */}
              <div className="mb-4">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-500">Su Seviyesi</span>
                  <span className={`font-medium ${isLow ? 'text-warning-600' : 'text-primary-600'}`}>
                    {source.current_level.toLocaleString()} / {source.capacity.toLocaleString()} L
                  </span>
                </div>
                <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full transition-all ${
                      isLow ? 'bg-warning-500' : 'bg-primary-500'
                    }`}
                    style={{ width: `${levelPercent}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-1 text-right">{levelPercent}%</p>
              </div>
              
              {/* Details */}
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-gray-400" />
                  <div>
                    <p className="text-gray-500">Kalite</p>
                    <p className={`font-medium ${quality.color}`}>{quality.label}</p>
                  </div>
                </div>
                {source.temperature && (
                  <div className="flex items-center gap-2">
                    <Thermometer className="w-4 h-4 text-gray-400" />
                    <div>
                      <p className="text-gray-500">Sıcaklık</p>
                      <p className="font-medium">{source.temperature}°C</p>
                    </div>
                  </div>
                )}
              </div>
              
              <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-400">
                Son kontrol: {new Date(source.last_check).toLocaleDateString('tr-TR')}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
