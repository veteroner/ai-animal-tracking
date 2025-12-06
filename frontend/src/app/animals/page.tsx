'use client';

import { useState, useEffect } from 'react';
import {
  Dog,
  Search,
  Filter,
  Plus,
  MoreVertical,
  Heart,
  AlertTriangle,
  Calendar,
  Weight,
  MapPin,
  Edit,
  Trash2,
  Eye,
} from 'lucide-react';
import { api, isSupabaseConfigured, Animal as SupabaseAnimal } from '@/lib/supabase';

interface Animal {
  id: number;
  tag_id: string;
  name?: string;
  species: string;
  breed: string;
  gender: string;
  health_status: string;
  weight: number;
  birth_date?: string;
  created_at: string;
}

const healthStatusColors = {
  healthy: { bg: 'bg-success-100', text: 'text-success-600', label: 'Sağlıklı' },
  warning: { bg: 'bg-warning-100', text: 'text-warning-600', label: 'Dikkat' },
  sick: { bg: 'bg-danger-100', text: 'text-danger-600', label: 'Hasta' },
  critical: { bg: 'bg-danger-100', text: 'text-danger-600', label: 'Kritik' },
};

// Map Supabase status to component status
const mapHealthStatus = (status: string): string => {
  const map: Record<string, string> = {
    'sağlıklı': 'healthy',
    'hasta': 'sick',
    'tedavide': 'warning',
    'karantina': 'critical',
  };
  return map[status] || 'healthy';
};

export default function AnimalsPage() {
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterSpecies, setFilterSpecies] = useState<string>('all');
  const [selectedAnimal, setSelectedAnimal] = useState<Animal | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<number | null>(null);

  useEffect(() => {
    fetchAnimals();
  }, []);

  const fetchAnimals = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!isSupabaseConfigured()) {
        // Demo data when Supabase is not configured
        setAnimals([
          { id: 1, tag_id: 'TR-001', name: 'Sarıkız', species: 'cattle', breed: 'Simental', gender: 'female', health_status: 'healthy', weight: 450, created_at: '2024-01-15' },
          { id: 2, tag_id: 'TR-002', name: 'Karabaş', species: 'cattle', breed: 'Holstein', gender: 'male', health_status: 'warning', weight: 520, created_at: '2024-01-10' },
          { id: 3, tag_id: 'TR-003', name: 'Benekli', species: 'cattle', breed: 'Jersey', gender: 'female', health_status: 'healthy', weight: 380, created_at: '2024-02-01' },
          { id: 4, tag_id: 'TR-004', species: 'sheep', breed: 'Merinos', gender: 'female', health_status: 'healthy', weight: 65, created_at: '2024-02-15' },
          { id: 5, tag_id: 'TR-005', species: 'sheep', breed: 'Kıvırcık', gender: 'male', health_status: 'sick', weight: 70, created_at: '2024-01-20' },
          { id: 6, tag_id: 'TR-006', name: 'Pamuk', species: 'goat', breed: 'Saanen', gender: 'female', health_status: 'healthy', weight: 45, created_at: '2024-03-01' },
        ]);
        return;
      }

      const supabaseAnimals = await api.animals.getAll();
      
      // Map Supabase animals to component format
      const mappedAnimals: Animal[] = supabaseAnimals.map((a: SupabaseAnimal, index: number) => ({
        id: parseInt(a.id) || index + 1,
        tag_id: a.tag || `TR-${String(index + 1).padStart(3, '0')}`,
        name: a.name,
        species: a.type || 'cattle',
        breed: a.breed || 'Bilinmiyor',
        gender: a.gender === 'erkek' ? 'male' : 'female',
        health_status: mapHealthStatus(a.status),
        weight: a.weight || 0,
        birth_date: a.birth_date,
        created_at: a.created_at,
      }));

      setAnimals(mappedAnimals.length > 0 ? mappedAnimals : [
        { id: 1, tag_id: 'TR-001', name: 'Örnek Hayvan', species: 'cattle', breed: 'Simental', gender: 'female', health_status: 'healthy', weight: 450, created_at: new Date().toISOString() },
      ]);
    } catch (err) {
      console.error('Error fetching animals:', err);
      setError('Hayvanlar yüklenemedi');
      // Fallback to demo data
      setAnimals([
        { id: 1, tag_id: 'TR-001', name: 'Sarıkız', species: 'cattle', breed: 'Simental', gender: 'female', health_status: 'healthy', weight: 450, created_at: '2024-01-15' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      // Delete from local state
      setAnimals(animals.filter(a => a.id !== id));
      setShowDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting animal:', error);
    }
  };

  const filteredAnimals = animals.filter(animal => {
    const matchesSearch = 
      animal.tag_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (animal.name?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
    const matchesStatus = filterStatus === 'all' || animal.health_status === filterStatus;
    const matchesSpecies = filterSpecies === 'all' || animal.species === filterSpecies;
    return matchesSearch && matchesStatus && matchesSpecies;
  });

  const uniqueSpecies = Array.from(new Set(animals.map((a: Animal) => a.species)));

  const getSpeciesLabel = (species: string) => {
    const labels: Record<string, string> = {
      cattle: 'Sığır',
      sheep: 'Koyun',
      goat: 'Keçi',
      horse: 'At',
    };
    return labels[species] || species;
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Hayvanlar</h1>
          <p className="text-gray-500 mt-1">Toplam {animals.length} hayvan kayıtlı</p>
        </div>
        
        <a href="/animals/new" className="btn-primary flex items-center gap-2 w-fit">
          <Plus className="w-5 h-5" />
          Yeni Hayvan
        </a>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
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
          
          {/* Status Filter */}
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
          
          {/* Species Filter */}
          <div className="sm:w-48">
            <select
              value={filterSpecies}
              onChange={(e) => setFilterSpecies(e.target.value)}
              className="input"
            >
              <option value="all">Tüm Türler</option>
              {uniqueSpecies.map(species => (
                <option key={species} value={species}>
                  {getSpeciesLabel(species)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Animals Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-gray-200" />
                <div className="flex-1">
                  <div className="h-5 bg-gray-200 rounded w-24 mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-32" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : filteredAnimals.length === 0 ? (
        <div className="card text-center py-12">
          <Dog className="w-12 h-12 mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">Hayvan bulunamadı</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAnimals.map((animal) => {
            const status = healthStatusColors[animal.health_status as keyof typeof healthStatusColors] 
              || healthStatusColors.healthy;
            
            return (
              <div key={animal.id} className="card-hover group">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-3">
                    <div className={`p-3 rounded-xl ${status.bg}`}>
                      <Dog className={`w-6 h-6 ${status.text}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {animal.name || animal.tag_id}
                      </h3>
                      <p className="text-sm text-gray-500">{animal.tag_id}</p>
                    </div>
                  </div>
                  
                  {/* Actions Menu */}
                  <div className="relative">
                    <button
                      onClick={() => setSelectedAnimal(selectedAnimal?.id === animal.id ? null : animal)}
                      className="p-1.5 rounded-lg hover:bg-gray-100 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <MoreVertical className="w-5 h-5 text-gray-400" />
                    </button>
                    
                    {selectedAnimal?.id === animal.id && (
                      <div className="absolute right-0 top-8 w-40 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                        <a
                          href={`/animals/${animal.id}`}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        >
                          <Eye className="w-4 h-4" />
                          Görüntüle
                        </a>
                        <a
                          href={`/animals/${animal.id}/edit`}
                          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        >
                          <Edit className="w-4 h-4" />
                          Düzenle
                        </a>
                        <button
                          onClick={() => setShowDeleteConfirm(animal.id)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-danger-600 hover:bg-danger-50"
                        >
                          <Trash2 className="w-4 h-4" />
                          Sil
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Info */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span className={`badge ${status.bg} ${status.text}`}>
                      {status.label}
                    </span>
                    <span className="text-gray-300">•</span>
                    <span>{getSpeciesLabel(animal.species)}</span>
                    {animal.breed && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span>{animal.breed}</span>
                      </>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    {animal.weight && (
                      <div className="flex items-center gap-1">
                        <Weight className="w-4 h-4" />
                        <span>{animal.weight} kg</span>
                      </div>
                    )}
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      <span>
                        {animal.birth_date 
                          ? new Date(animal.birth_date).toLocaleDateString('tr-TR')
                          : 'Bilinmiyor'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Delete Confirmation */}
                {showDeleteConfirm === animal.id && (
                  <div className="mt-4 p-3 bg-danger-50 rounded-lg border border-danger-200">
                    <p className="text-sm text-danger-700 mb-3">
                      Bu hayvanı silmek istediğinize emin misiniz?
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleDelete(animal.id)}
                        className="btn-danger text-sm py-1.5 px-3"
                      >
                        Sil
                      </button>
                      <button
                        onClick={() => setShowDeleteConfirm(null)}
                        className="btn-secondary text-sm py-1.5 px-3"
                      >
                        İptal
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Stats Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-gray-900">{animals.length}</p>
          <p className="text-sm text-gray-500">Toplam</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-success-600">
            {animals.filter(a => a.health_status === 'healthy').length}
          </p>
          <p className="text-sm text-gray-500">Sağlıklı</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-warning-600">
            {animals.filter(a => a.health_status === 'warning').length}
          </p>
          <p className="text-sm text-gray-500">Dikkat</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-danger-600">
            {animals.filter(a => a.health_status === 'sick').length}
          </p>
          <p className="text-sm text-gray-500">Hasta</p>
        </div>
      </div>
    </div>
  );
}
