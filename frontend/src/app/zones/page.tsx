'use client';

import { useState } from 'react';
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
} from 'lucide-react';

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

const mockZones: Zone[] = [
  { id: 1, name: 'Ana Otlak', zone_type: 'grazing', animal_count: 45, capacity: 60, status: 'normal', description: 'Günlük otlatma alanı', coordinates: [39.9350, 32.8610], radius: 80 },
  { id: 2, name: 'Ahır 1', zone_type: 'shelter', animal_count: 32, capacity: 40, status: 'normal', description: 'Ana barınak', coordinates: [39.9320, 32.8580], radius: 40 },
  { id: 3, name: 'Ahır 2', zone_type: 'shelter', animal_count: 28, capacity: 30, status: 'warning', description: 'Yavru barınağı', coordinates: [39.9330, 32.8560], radius: 35 },
  { id: 4, name: 'Su Kaynağı', zone_type: 'water', animal_count: 12, capacity: 20, status: 'normal', description: 'Ana su deposu', coordinates: [39.9340, 32.8620], radius: 25 },
  { id: 5, name: 'Yem Deposu', zone_type: 'feeding', animal_count: 8, capacity: 15, status: 'normal', description: 'Yem dağıtım noktası', coordinates: [39.9310, 32.8600], radius: 30 },
  { id: 6, name: 'Tehlikeli Bölge', zone_type: 'restricted', animal_count: 3, capacity: 0, status: 'danger', description: 'Yasak bölge - inşaat alanı', coordinates: [39.9360, 32.8550], radius: 60 },
];

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

export default function ZonesPage() {
  const [zones, setZones] = useState<Zone[]>(mockZones);

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
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Bölge Haritası</h2>
        <ZoneMap 
          zones={zones} 
          center={[39.9334, 32.8597]} 
          zoom={16} 
        />
        <div className="mt-4 flex flex-wrap gap-4 text-sm">
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
