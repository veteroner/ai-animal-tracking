'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  MapPin,
  Plus,
  RefreshCw,
  ChevronRight,
  Settings,
  Users,
  Utensils,
  Droplets,
  Moon,
  Egg,
  Wind,
  Home,
  ShieldAlert,
  Thermometer,
  Edit,
  Trash2,
} from 'lucide-react';
import { api, isSupabaseConfigured, CoopZone, Coop } from '@/lib/supabase';

const zoneTypeInfo: Record<string, { label: string; icon: typeof MapPin; color: string; bgColor: string }> = {
  feeder: { label: 'Yemlik', icon: Utensils, color: 'text-green-600', bgColor: 'bg-green-100' },
  waterer: { label: 'Suluk', icon: Droplets, color: 'text-blue-600', bgColor: 'bg-blue-100' },
  roost: { label: 'Tünek', icon: Moon, color: 'text-purple-600', bgColor: 'bg-purple-100' },
  nest_box: { label: 'Yumurtlama Kutusu', icon: Egg, color: 'text-pink-600', bgColor: 'bg-pink-100' },
  dust_bath: { label: 'Toz Banyosu', icon: Wind, color: 'text-amber-600', bgColor: 'bg-amber-100' },
  free_range: { label: 'Serbest Alan', icon: Home, color: 'text-teal-600', bgColor: 'bg-teal-100' },
  brooder: { label: 'Civciv Bölümü', icon: Thermometer, color: 'text-orange-600', bgColor: 'bg-orange-100' },
  quarantine: { label: 'Karantina', icon: ShieldAlert, color: 'text-red-600', bgColor: 'bg-red-100' },
};

export default function PoultryZonesPage() {
  const [coops, setCoops] = useState<Coop[]>([]);
  const [zones, setZones] = useState<CoopZone[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCoop, setSelectedCoop] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      if (!isSupabaseConfigured()) {
        // Demo verileri
        setCoops([
          { id: 'coop-001', name: 'Ana Kümes', location: 'Çiftlik Merkezi - Bina 1', capacity: 200, coop_type: 'layer', is_active: true, created_at: '', updated_at: '' },
          { id: 'coop-002', name: 'Broiler Kümesi', location: 'Çiftlik Merkezi - Bina 2', capacity: 500, coop_type: 'broiler', is_active: true, created_at: '', updated_at: '' },
          { id: 'coop-003', name: 'Civciv Kümesi', location: 'Çiftlik Merkezi - Bina 3', capacity: 100, coop_type: 'standard', is_active: true, created_at: '', updated_at: '' },
        ]);
        
        setZones([
          { id: 'zone-001', coop_id: 'coop-001', zone_type: 'feeder', name: 'Ana Yemlik', bbox_x1: 100, bbox_y1: 100, bbox_x2: 300, bbox_y2: 200, capacity: 40, current_count: 25, is_active: true, created_at: '' },
          { id: 'zone-002', coop_id: 'coop-001', zone_type: 'waterer', name: 'Suluk 1', bbox_x1: 350, bbox_y1: 100, bbox_x2: 450, bbox_y2: 180, capacity: 20, current_count: 8, is_active: true, created_at: '' },
          { id: 'zone-003', coop_id: 'coop-001', zone_type: 'waterer', name: 'Suluk 2', bbox_x1: 500, bbox_y1: 100, bbox_x2: 600, bbox_y2: 180, capacity: 20, current_count: 5, is_active: true, created_at: '' },
          { id: 'zone-004', coop_id: 'coop-001', zone_type: 'roost', name: 'Tünek Alanı', bbox_x1: 100, bbox_y1: 300, bbox_x2: 600, bbox_y2: 450, capacity: 60, current_count: 45, is_active: true, created_at: '' },
          { id: 'zone-005', coop_id: 'coop-001', zone_type: 'nest_box', name: 'Yumurtlama Kutuları', bbox_x1: 650, bbox_y1: 100, bbox_x2: 800, bbox_y2: 300, capacity: 20, current_count: 12, is_active: true, created_at: '' },
          { id: 'zone-006', coop_id: 'coop-001', zone_type: 'dust_bath', name: 'Toz Banyosu', bbox_x1: 100, bbox_y1: 500, bbox_x2: 250, bbox_y2: 600, capacity: 15, current_count: 4, is_active: true, created_at: '' },
          { id: 'zone-007', coop_id: 'coop-002', zone_type: 'feeder', name: 'Broiler Yemlik 1', bbox_x1: 100, bbox_y1: 100, bbox_x2: 400, bbox_y2: 200, capacity: 80, current_count: 55, is_active: true, created_at: '' },
          { id: 'zone-008', coop_id: 'coop-002', zone_type: 'feeder', name: 'Broiler Yemlik 2', bbox_x1: 450, bbox_y1: 100, bbox_x2: 750, bbox_y2: 200, capacity: 80, current_count: 48, is_active: true, created_at: '' },
          { id: 'zone-009', coop_id: 'coop-002', zone_type: 'waterer', name: 'Broiler Suluk', bbox_x1: 200, bbox_y1: 250, bbox_x2: 600, bbox_y2: 350, capacity: 50, current_count: 22, is_active: true, created_at: '' },
          { id: 'zone-010', coop_id: 'coop-003', zone_type: 'brooder', name: 'Civciv Isıtma Alanı', bbox_x1: 100, bbox_y1: 100, bbox_x2: 400, bbox_y2: 300, capacity: 50, current_count: 30, is_active: true, created_at: '' },
        ]);
        
        setLoading(false);
        return;
      }

      const [coopsData, zonesData] = await Promise.all([
        api.coops.getAll(),
        api.coopZones.getAll(),
      ]);
      
      setCoops(coopsData);
      setZones(zonesData);
    } catch (error) {
      console.error('Error loading zones data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredZones = selectedCoop === 'all' 
    ? zones 
    : zones.filter(z => z.coop_id === selectedCoop);

  const getOccupancyColor = (current: number, capacity: number) => {
    const rate = capacity > 0 ? current / capacity : 0;
    if (rate >= 0.9) return 'text-red-600';
    if (rate >= 0.7) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getOccupancyBgColor = (current: number, capacity: number) => {
    const rate = capacity > 0 ? current / capacity : 0;
    if (rate >= 0.9) return 'bg-red-500';
    if (rate >= 0.7) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/poultry" className="hover:text-foreground">Kanatlı</Link>
            <ChevronRight className="w-4 h-4" />
            <span>Bölge Yönetimi</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">📍 Kümes Bölge Yönetimi</h1>
          <p className="text-muted-foreground mt-1">Kümes bölgelerini tanımla ve doluluk durumunu izle</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-muted transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Yenile
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
            <Plus className="w-4 h-4" />
            Bölge Ekle
          </button>
        </div>
      </div>

      {/* Kümes Seçici */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setSelectedCoop('all')}
          className={`px-4 py-2 rounded-lg transition-colors ${
            selectedCoop === 'all' 
              ? 'bg-primary text-primary-foreground' 
              : 'bg-muted hover:bg-muted/80'
          }`}
        >
          Tüm Kümesler
        </button>
        {coops.map((coop) => (
          <button
            key={coop.id}
            onClick={() => setSelectedCoop(coop.id)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              selectedCoop === coop.id 
                ? 'bg-primary text-primary-foreground' 
                : 'bg-muted hover:bg-muted/80'
            }`}
          >
            {coop.name}
          </button>
        ))}
      </div>

      {/* Bölge Özeti */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        {Object.entries(zoneTypeInfo).map(([type, info]) => {
          const count = filteredZones.filter(z => z.zone_type === type).length;
          const Icon = info.icon;
          
          return (
            <div key={type} className="bg-card rounded-xl border p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className={`p-1.5 rounded-lg ${info.bgColor}`}>
                  <Icon className={`w-4 h-4 ${info.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold">{count}</div>
              <div className="text-xs text-muted-foreground truncate">{info.label}</div>
            </div>
          );
        })}
      </div>

      {/* Bölge Listesi */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredZones.map((zone) => {
          const info = zoneTypeInfo[zone.zone_type] || { label: zone.zone_type, icon: MapPin, color: 'text-gray-600', bgColor: 'bg-gray-100' };
          const Icon = info.icon;
          const occupancyRate = zone.capacity > 0 ? (zone.current_count / zone.capacity) * 100 : 0;
          const coop = coops.find(c => c.id === zone.coop_id);
          
          return (
            <div key={zone.id} className="bg-card rounded-xl border p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-lg ${info.bgColor}`}>
                    <Icon className={`w-6 h-6 ${info.color}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold">{zone.name}</h3>
                    <p className="text-sm text-muted-foreground">{info.label}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button className="p-1 hover:bg-muted rounded">
                    <Edit className="w-4 h-4 text-muted-foreground" />
                  </button>
                  <button className="p-1 hover:bg-muted rounded">
                    <Settings className="w-4 h-4 text-muted-foreground" />
                  </button>
                </div>
              </div>
              
              {/* Doluluk */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Doluluk</span>
                  <span className={`font-medium ${getOccupancyColor(zone.current_count, zone.capacity)}`}>
                    {zone.current_count} / {zone.capacity}
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${getOccupancyBgColor(zone.current_count, zone.capacity)} transition-all`}
                    style={{ width: `${Math.min(occupancyRate, 100)}%` }}
                  />
                </div>
                <div className="text-xs text-muted-foreground text-right">
                  %{occupancyRate.toFixed(0)} dolu
                </div>
              </div>
              
              {/* Kümes */}
              <div className="flex items-center justify-between pt-4 border-t text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Home className="w-4 h-4" />
                  <span>{coop?.name || 'Bilinmeyen'}</span>
                </div>
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Users className="w-4 h-4" />
                  <span>{zone.current_count}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Kümes Bilgileri */}
      <div className="bg-card rounded-xl border">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Kümes Bilgileri</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Kümes</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Konum</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Tip</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Kapasite</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Bölge Sayısı</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Durum</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {coops.map((coop) => {
                const coopZones = zones.filter(z => z.coop_id === coop.id);
                
                return (
                  <tr key={coop.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-primary/10 rounded-lg">
                          <Home className="w-5 h-5 text-primary" />
                        </div>
                        <span className="font-medium">{coop.name}</span>
                      </div>
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">{coop.location || '-'}</td>
                    <td className="p-4">
                      <span className="px-2 py-1 bg-muted rounded-full text-xs">
                        {coop.coop_type === 'layer' ? 'Yumurtacı' : 
                         coop.coop_type === 'broiler' ? 'Etlik' : 
                         coop.coop_type === 'breeder' ? 'Damızlık' : 'Standart'}
                      </span>
                    </td>
                    <td className="p-4 text-center">{coop.capacity}</td>
                    <td className="p-4 text-center">{coopZones.length}</td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        coop.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                      }`}>
                        {coop.is_active ? 'Aktif' : 'Pasif'}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button className="p-1 hover:bg-muted rounded">
                          <Edit className="w-4 h-4 text-muted-foreground" />
                        </button>
                        <button className="p-1 hover:bg-muted rounded">
                          <Settings className="w-4 h-4 text-muted-foreground" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
