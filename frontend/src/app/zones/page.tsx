'use client';

import { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import {
  MapPin,
  Plus,
  Edit,
  Trash2,
  Users,
  AlertTriangle,
  Home,
  Droplets,
  Wheat,
  Shield,
  Loader2,
  Navigation,
  RefreshCw,
} from 'lucide-react';
import { api, isSupabaseConfigured, Zone as SupabaseZone } from '@/lib/supabase';

// Harita bileşenini dinamik olarak yükle (SSR devre dışı)
const ZoneMap = dynamic(() => import('@/components/map/ZoneMap'), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-gray-100 rounded-xl flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        <p className="text-gray-500">Harita yükleniyor...</p>
      </div>
    </div>
  ),
});

interface Zone {
  id: number;
  name: string;
  zone_type: string;
  animal_count: number;
  capacity: number;
  status: 'normal' | 'warning' | 'danger';
  description?: string;
  coordinates: [number, number];
  radius?: number;
}

// Zone type mappings from Supabase
const mapZoneType = (type: string): string => {
  const map: Record<string, string> = {
    'otlak': 'grazing',
    'ahır': 'shelter',
    'karantina': 'restricted',
    'sulak': 'water',
  };
  return map[type] || 'grazing';
};

const zoneTypeConfig = {
  grazing: { icon: Wheat, label: 'Otlak', color: 'text-success-600', bg: 'bg-success-100' },
  shelter: { icon: Home, label: 'Barınak', color: 'text-primary-600', bg: 'bg-primary-100' },
  water: { icon: Droplets, label: 'Su Kaynağı', color: 'text-blue-600', bg: 'bg-blue-100' },
  feeding: { icon: Wheat, label: 'Yem Alanı', color: 'text-warning-600', bg: 'bg-warning-100' },
  restricted: { icon: Shield, label: 'Yasak Bölge', color: 'text-danger-600', bg: 'bg-danger-100' },
};

const statusConfig = {
  normal: { label: 'Normal', color: 'text-success-600', bg: 'bg-success-100' },
  warning: { label: 'Dikkat', color: 'text-warning-600', bg: 'bg-warning-100' },
  danger: { label: 'Tehlike', color: 'text-danger-600', bg: 'bg-danger-100' },
};

// Kullanıcı konumuna göre demo bölgeler oluştur
const createDemoZonesAroundLocation = (lat: number, lng: number): Zone[] => {
  return [
    { id: 1, name: 'Ana Otlak', zone_type: 'grazing', animal_count: 45, capacity: 60, status: 'normal', description: 'Günlük otlatma alanı', coordinates: [lat + 0.001, lng + 0.001], radius: 80 },
    { id: 2, name: 'Ahır 1', zone_type: 'shelter', animal_count: 32, capacity: 40, status: 'normal', description: 'Ana barınak', coordinates: [lat - 0.0008, lng - 0.001], radius: 40 },
    { id: 3, name: 'Ahır 2', zone_type: 'shelter', animal_count: 28, capacity: 30, status: 'warning', description: 'Yavru barınağı', coordinates: [lat - 0.0005, lng + 0.0015], radius: 35 },
    { id: 4, name: 'Su Kaynağı', zone_type: 'water', animal_count: 12, capacity: 20, status: 'normal', description: 'Ana su deposu', coordinates: [lat + 0.0012, lng - 0.0008], radius: 25 },
    { id: 5, name: 'Yem Deposu', zone_type: 'feeding', animal_count: 8, capacity: 15, status: 'normal', description: 'Yem dağıtım noktası', coordinates: [lat - 0.001, lng + 0.0005], radius: 30 },
    { id: 6, name: 'Tehlikeli Bölge', zone_type: 'restricted', animal_count: 3, capacity: 0, status: 'danger', description: 'Yasak bölge - inşaat alanı', coordinates: [lat + 0.0015, lng + 0.002], radius: 60 },
  ];
};

export default function ZonesPage() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [locationStatus, setLocationStatus] = useState<'loading' | 'found' | 'error' | 'denied'>('loading');

  // Kullanıcı konumu bulunduğunda
  const handleUserLocationFound = useCallback((lat: number, lng: number) => {
    setUserLocation([lat, lng]);
    setLocationStatus('found');
    
    // Supabase yoksa kullanıcı konumuna göre demo bölgeler oluştur
    if (!isSupabaseConfigured()) {
      setZones(createDemoZonesAroundLocation(lat, lng));
    }
  }, []);

  useEffect(() => {
    const loadZones = async () => {
      try {
        setLoading(true);
        setError(null);

        if (!isSupabaseConfigured()) {
          // Konum alınana kadar varsayılan bölgeler göster
          // Konum alındığında handleUserLocationFound ile güncellenecek
          setZones([
            { id: 1, name: 'Ana Otlak', zone_type: 'grazing', animal_count: 45, capacity: 60, status: 'normal', description: 'Günlük otlatma alanı', coordinates: [39.9350, 32.8610], radius: 80 },
            { id: 2, name: 'Ahır 1', zone_type: 'shelter', animal_count: 32, capacity: 40, status: 'normal', description: 'Ana barınak', coordinates: [39.9320, 32.8580], radius: 40 },
            { id: 3, name: 'Ahır 2', zone_type: 'shelter', animal_count: 28, capacity: 30, status: 'warning', description: 'Yavru barınağı', coordinates: [39.9330, 32.8560], radius: 35 },
            { id: 4, name: 'Su Kaynağı', zone_type: 'water', animal_count: 12, capacity: 20, status: 'normal', description: 'Ana su deposu', coordinates: [39.9340, 32.8620], radius: 25 },
            { id: 5, name: 'Yem Deposu', zone_type: 'feeding', animal_count: 8, capacity: 15, status: 'normal', description: 'Yem dağıtım noktası', coordinates: [39.9310, 32.8600], radius: 30 },
            { id: 6, name: 'Tehlikeli Bölge', zone_type: 'restricted', animal_count: 3, capacity: 0, status: 'danger', description: 'Yasak bölge - inşaat alanı', coordinates: [39.9360, 32.8550], radius: 60 },
          ]);
          return;
        }

        const supabaseZones = await api.zones.getAll();
        
        // Map Supabase zones to component format
        const mappedZones: Zone[] = supabaseZones.map((z: SupabaseZone, index: number) => {
          const occupancy = z.capacity > 0 ? z.current_count / z.capacity : 0;
          let status: 'normal' | 'warning' | 'danger' = 'normal';
          if (occupancy > 0.9) status = 'danger';
          else if (occupancy > 0.7) status = 'warning';

          // Get center of polygon coordinates
          const coords = z.coordinates || [];
          const lat = coords.length > 0 ? coords.reduce((sum, c) => sum + c.lat, 0) / coords.length : 39.9334 + (index * 0.003);
          const lng = coords.length > 0 ? coords.reduce((sum, c) => sum + c.lng, 0) / coords.length : 32.8597 + (index * 0.002);

          return {
            id: parseInt(z.id) || index + 1,
            name: z.name,
            zone_type: mapZoneType(z.type),
            animal_count: z.current_count || 0,
            capacity: z.capacity || 50,
            status,
            coordinates: [lat, lng] as [number, number],
            radius: 40,
          };
        });

        setZones(mappedZones.length > 0 ? mappedZones : [
          { id: 1, name: 'Ana Otlak', zone_type: 'grazing', animal_count: 0, capacity: 60, status: 'normal', coordinates: [39.9350, 32.8610], radius: 80 },
        ]);
      } catch (err) {
        console.error('Error loading zones:', err);
        setError('Bölgeler yüklenemedi');
        // Fallback to demo data
        setZones([
          { id: 1, name: 'Ana Otlak', zone_type: 'grazing', animal_count: 45, capacity: 60, status: 'normal', coordinates: [39.9350, 32.8610], radius: 80 },
        ]);
      } finally {
        setLoading(false);
      }
    };

    loadZones();
  }, []);

  const totalAnimals = zones.reduce((sum, z) => sum + z.animal_count, 0);
  const totalCapacity = zones.filter(z => z.zone_type !== 'restricted').reduce((sum, z) => sum + z.capacity, 0);
  const warningZones = zones.filter(z => z.status !== 'normal').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bölge Haritası</h1>
          <p className="text-gray-500 mt-1">{zones.length} bölge tanımlı</p>
        </div>
        
        <button className="btn-primary flex items-center gap-2 w-fit">
          <Plus className="w-5 h-5" />
          Yeni Bölge
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-gray-900">{zones.length}</p>
          <p className="text-sm text-gray-500">Toplam Bölge</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-primary-600">{totalAnimals}</p>
          <p className="text-sm text-gray-500">Toplam Hayvan</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-success-600">
            {Math.round((totalAnimals / totalCapacity) * 100)}%
          </p>
          <p className="text-sm text-gray-500">Doluluk Oranı</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-warning-600">{warningZones}</p>
          <p className="text-sm text-gray-500">Uyarılı Bölge</p>
        </div>
      </div>

      {/* Map */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Bölge Haritası</h2>
          <div className="flex items-center gap-2">
            {locationStatus === 'loading' && (
              <span className="text-sm text-gray-500 flex items-center gap-1">
                <Loader2 className="w-4 h-4 animate-spin" />
                Konum alınıyor...
              </span>
            )}
            {locationStatus === 'found' && userLocation && (
              <span className="text-sm text-green-600 flex items-center gap-1">
                <Navigation className="w-4 h-4" />
                Konumunuz bulundu
              </span>
            )}
            {locationStatus === 'error' && (
              <span className="text-sm text-yellow-600 flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" />
                Konum alınamadı
              </span>
            )}
          </div>
        </div>
        <ZoneMap 
          zones={zones} 
          center={userLocation || [39.9334, 32.8597]} 
          zoom={userLocation ? 17 : 16}
          showUserLocation={true}
          onUserLocationFound={handleUserLocationFound}
        />
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500 ring-2 ring-blue-200" />
            <span className="text-gray-600">Konumunuz</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-gray-600">Otlak</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span className="text-gray-600">Barınak</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-cyan-500" />
            <span className="text-gray-600">Su Kaynağı</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span className="text-gray-600">Yem Alanı</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-gray-600">Yasak Bölge</span>
          </div>
        </div>
      </div>

      {/* Zones Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {zones.map((zone) => {
          const typeConfig = zoneTypeConfig[zone.zone_type as keyof typeof zoneTypeConfig] || zoneTypeConfig.grazing;
          const status = statusConfig[zone.status];
          const Icon = typeConfig.icon;
          const occupancy = zone.capacity > 0 ? Math.round((zone.animal_count / zone.capacity) * 100) : 0;
          
          return (
            <div key={zone.id} className="card-hover">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3">
                  <div className={`p-3 rounded-xl ${typeConfig.bg}`}>
                    <Icon className={`w-5 h-5 ${typeConfig.color}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{zone.name}</h3>
                    <p className="text-sm text-gray-500">{typeConfig.label}</p>
                  </div>
                </div>
                <span className={`badge ${status.bg} ${status.color}`}>
                  {status.label}
                </span>
              </div>
              
              {zone.description && (
                <p className="text-sm text-gray-600 mb-4">{zone.description}</p>
              )}
              
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Hayvan Sayısı</span>
                  <span className="font-medium">{zone.animal_count} / {zone.capacity || '-'}</span>
                </div>
                
                {zone.capacity > 0 && (
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-500">Doluluk</span>
                      <span className={`font-medium ${occupancy > 90 ? 'text-danger-600' : occupancy > 70 ? 'text-warning-600' : 'text-success-600'}`}>
                        {occupancy}%
                      </span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all ${
                          occupancy > 90 ? 'bg-danger-500' : occupancy > 70 ? 'bg-warning-500' : 'bg-success-500'
                        }`}
                        style={{ width: `${Math.min(occupancy, 100)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
              
              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
                <button className="flex-1 btn-secondary text-sm py-1.5">
                  <Edit className="w-4 h-4 inline mr-1" />
                  Düzenle
                </button>
                <button className="p-2 rounded-lg hover:bg-danger-50 text-gray-400 hover:text-danger-600">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
