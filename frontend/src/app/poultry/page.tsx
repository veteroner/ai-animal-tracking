'use client';

import { useState, useEffect } from 'react';
import {
  Bird,
  Search,
  Plus,
  Filter,
  MoreVertical,
  Heart,
  Calendar,
  Weight,
  Edit,
  Trash2,
  Eye,
  Loader2,
} from 'lucide-react';
import { api, isSupabaseConfigured, Poultry as SupabasePoultry } from '@/lib/supabase';

interface Poultry {
  id: number;
  tag_id: string;
  name?: string;
  poultry_type: string;
  breed?: string;
  hatch_date?: string;
  gender: string;
  weight?: number;
  health_status: string;
  coop_id?: number;
  coop_name?: string;
}

const healthStatusColors = {
  healthy: { bg: 'bg-success-100', text: 'text-success-600', label: 'Sağlıklı' },
  warning: { bg: 'bg-warning-100', text: 'text-warning-600', label: 'Dikkat' },
  sick: { bg: 'bg-danger-100', text: 'text-danger-600', label: 'Hasta' },
};

const poultryTypeLabels: Record<string, string> = {
  chicken: 'Tavuk',
  rooster: 'Horoz',
  turkey: 'Hindi',
  duck: 'Ördek',
  goose: 'Kaz',
  quail: 'Bıldırcın',
  tavuk: 'Tavuk',
  hindi: 'Hindi',
  ördek: 'Ördek',
  kaz: 'Kaz',
};

// Map Supabase bird type to component type
const mapBirdType = (type: string): string => {
  const map: Record<string, string> = {
    'tavuk': 'chicken',
    'hindi': 'turkey',
    'ördek': 'duck',
    'kaz': 'goose',
  };
  return map[type] || type;
};

// Map Supabase status to component status
const mapPoultryStatus = (status: string): string => {
  const map: Record<string, string> = {
    'aktif': 'healthy',
    'karantina': 'warning',
    'tedavide': 'sick',
  };
  return map[status] || 'healthy';
};

export default function PoultryPage() {
  const [poultry, setPoultry] = useState<Poultry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedPoultry, setSelectedPoultry] = useState<Poultry | null>(null);

  useEffect(() => {
    loadPoultry();
  }, []);

  const loadPoultry = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!isSupabaseConfigured()) {
        // Demo data when Supabase is not configured
        setPoultry([
          { id: 1, tag_id: 'K-001', name: 'Sarı', poultry_type: 'chicken', breed: 'Rhode Island Red', gender: 'female', health_status: 'healthy', weight: 2.5, coop_name: 'Kümes 1', hatch_date: '2024-03-15' },
          { id: 2, tag_id: 'K-002', poultry_type: 'chicken', breed: 'Leghorn', gender: 'female', health_status: 'healthy', weight: 2.2, coop_name: 'Kümes 1', hatch_date: '2024-03-10' },
          { id: 3, tag_id: 'K-003', name: 'Horoz', poultry_type: 'rooster', breed: 'Rhode Island Red', gender: 'male', health_status: 'healthy', weight: 3.8, coop_name: 'Kümes 1', hatch_date: '2024-02-20' },
          { id: 4, tag_id: 'K-004', poultry_type: 'turkey', breed: 'Bronze', gender: 'male', health_status: 'warning', weight: 8.5, coop_name: 'Kümes 2', hatch_date: '2024-01-10' },
          { id: 5, tag_id: 'K-005', poultry_type: 'duck', breed: 'Pekin', gender: 'female', health_status: 'healthy', weight: 3.2, coop_name: 'Kümes 3', hatch_date: '2024-04-01' },
          { id: 6, tag_id: 'K-006', poultry_type: 'goose', breed: 'Toulouse', gender: 'female', health_status: 'sick', weight: 5.5, coop_name: 'Kümes 3', hatch_date: '2024-02-15' },
        ]);
        return;
      }

      const supabasePoultry = await api.poultry.getAll();

      // Map Supabase poultry to component format
      const mappedPoultry: Poultry[] = supabasePoultry.map((p: SupabasePoultry, index: number) => ({
        id: parseInt(p.id) || index + 1,
        tag_id: `K-${String(index + 1).padStart(3, '0')}`,
        poultry_type: mapBirdType(p.bird_type),
        breed: p.breed,
        gender: 'female',
        health_status: mapPoultryStatus(p.status),
        weight: p.avg_weight,
        coop_name: p.coop_name,
      }));

      setPoultry(mappedPoultry.length > 0 ? mappedPoultry : [
        { id: 1, tag_id: 'K-001', poultry_type: 'chicken', gender: 'female', health_status: 'healthy', coop_name: 'Kümes 1' },
      ]);
    } catch (err) {
      console.error('Error loading poultry:', err);
      setError('Kanatlılar yüklenemedi');
      setPoultry([
        { id: 1, tag_id: 'K-001', poultry_type: 'chicken', gender: 'female', health_status: 'healthy', coop_name: 'Demo Kümes' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredPoultry = poultry.filter(p => {
    const matchesSearch = 
      p.tag_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (p.name?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
    const matchesType = filterType === 'all' || p.poultry_type === filterType;
    const matchesStatus = filterStatus === 'all' || p.health_status === filterStatus;
    return matchesSearch && matchesType && matchesStatus;
  });

  const uniqueTypes = Array.from(new Set(poultry.map((p: Poultry) => p.poultry_type)));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kanatlılar</h1>
          <p className="text-gray-500 mt-1">Toplam {poultry.length} kanatlı kayıtlı</p>
        </div>
        
        <a href="/poultry/new" className="btn-primary flex items-center gap-2 w-fit">
          <Plus className="w-5 h-5" />
          Yeni Kanatlı
        </a>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-gray-900">{poultry.length}</p>
          <p className="text-sm text-gray-500">Toplam</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-success-600">
            {poultry.filter(p => p.health_status === 'healthy').length}
          </p>
          <p className="text-sm text-gray-500">Sağlıklı</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-warning-600">
            {poultry.filter(p => p.health_status === 'warning').length}
          </p>
          <p className="text-sm text-gray-500">Dikkat</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-danger-600">
            {poultry.filter(p => p.health_status === 'sick').length}
          </p>
          <p className="text-sm text-gray-500">Hasta</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Küpe no veya isim ara..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          
          <div className="sm:w-48">
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="input"
            >
              <option value="all">Tüm Türler</option>
              {uniqueTypes.map(type => (
                <option key={type} value={type}>
                  {poultryTypeLabels[type] || type}
                </option>
              ))}
            </select>
          </div>
          
          <div className="sm:w-48">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input"
            >
              <option value="all">Tüm Durumlar</option>
              <option value="healthy">Sağlıklı</option>
              <option value="warning">Dikkat</option>
              <option value="sick">Hasta</option>
            </select>
          </div>
        </div>
      </div>

      {/* Poultry Grid */}
      {filteredPoultry.length === 0 ? (
        <div className="card text-center py-12">
          <Bird className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Kanatlı bulunamadı</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPoultry.map((p) => {
            const status = healthStatusColors[p.health_status as keyof typeof healthStatusColors] 
              || healthStatusColors.healthy;
            
            return (
              <div key={p.id} className="card-hover group">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-3">
                    <div className={`p-3 rounded-xl ${status.bg}`}>
                      <Bird className={`w-6 h-6 ${status.text}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {p.name || p.tag_id}
                      </h3>
                      <p className="text-sm text-gray-500">{p.tag_id}</p>
                    </div>
                  </div>
                  
                  <div className="relative">
                    <button
                      onClick={() => setSelectedPoultry(selectedPoultry?.id === p.id ? null : p)}
                      className="p-1.5 rounded-lg hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <MoreVertical className="w-5 h-5 text-gray-400" />
                    </button>
                    
                    {selectedPoultry?.id === p.id && (
                      <div className="absolute right-0 top-8 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                        <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                          <Eye className="w-4 h-4" />
                          Görüntüle
                        </button>
                        <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
                          <Edit className="w-4 h-4" />
                          Düzenle
                        </button>
                        <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-danger-600 hover:bg-danger-50">
                          <Trash2 className="w-4 h-4" />
                          Sil
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span className={`badge ${status.bg} ${status.text}`}>
                      {status.label}
                    </span>
                    <span className="text-gray-300">•</span>
                    <span>{poultryTypeLabels[p.poultry_type] || p.poultry_type}</span>
                    {p.breed && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span>{p.breed}</span>
                      </>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    {p.weight && (
                      <div className="flex items-center gap-1">
                        <Weight className="w-4 h-4" />
                        <span>{p.weight} kg</span>
                      </div>
                    )}
                    {p.coop_name && (
                      <div className="flex items-center gap-1">
                        <Bird className="w-4 h-4" />
                        <span>{p.coop_name}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
