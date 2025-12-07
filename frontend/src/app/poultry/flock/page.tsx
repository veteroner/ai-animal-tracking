'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Users,
  Plus,
  RefreshCw,
  ChevronRight,
  Settings,
  Heart,
  Egg,
  TrendingUp,
  TrendingDown,
  Bird,
  Calendar,
  Edit,
  Eye,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle,
  Trash2,
  Home,
} from 'lucide-react';
import { api, isSupabaseConfigured, PoultryBird, PoultryCoop, PoultryRecord } from '@/lib/supabase';

const breedInfo: Record<string, { label: string; eggColor: string }> = {
  'rhode_island_red': { label: 'Rhode Island Red', eggColor: 'Kahverengi' },
  'leghorn': { label: 'Leghorn', eggColor: 'Beyaz' },
  'sussex': { label: 'Sussex', eggColor: 'Krem' },
  'plymouth_rock': { label: 'Plymouth Rock', eggColor: 'Kahverengi' },
  'wyandotte': { label: 'Wyandotte', eggColor: 'Kahverengi' },
  'orpington': { label: 'Orpington', eggColor: 'Açık Kahve' },
  'australorp': { label: 'Australorp', eggColor: 'Kahverengi' },
  'cornish': { label: 'Cornish', eggColor: 'Kahverengi' },
  'araucana': { label: 'Araucana', eggColor: 'Mavi-Yeşil' },
  'silkie': { label: 'Silkie', eggColor: 'Krem' },
};

const statusColors: Record<string, { bg: string; text: string; label: string }> = {
  active: { bg: 'bg-green-100', text: 'text-green-700', label: 'Aktif' },
  quarantine: { bg: 'bg-red-100', text: 'text-red-700', label: 'Karantina' },
  sick: { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Hasta' },
  recovering: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'İyileşiyor' },
  sold: { bg: 'bg-gray-100', text: 'text-gray-700', label: 'Satıldı' },
  deceased: { bg: 'bg-gray-100', text: 'text-gray-500', label: 'Vefat' },
};

export default function PoultryFlockPage() {
  const [birds, setBirds] = useState<PoultryBird[]>([]);
  const [coops, setCoops] = useState<PoultryCoop[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [selectedCoop, setSelectedCoop] = useState<string>('all');
  const [selectedBird, setSelectedBird] = useState<PoultryBird | null>(null);

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
        
        setBirds([
          { id: 'bird-001', bird_id: 'PTR-001', coop_id: 'coop-001', breed: 'rhode_island_red', gender: 'female', birth_date: '2023-06-15', weight_kg: 2.8, is_active: true, health_status: 'active', egg_production_rate: 0.92, created_at: '', updated_at: '' },
          { id: 'bird-002', bird_id: 'PTR-002', coop_id: 'coop-001', breed: 'leghorn', gender: 'female', birth_date: '2023-07-20', weight_kg: 2.2, is_active: true, health_status: 'active', egg_production_rate: 0.88, created_at: '', updated_at: '' },
          { id: 'bird-003', bird_id: 'PTR-003', coop_id: 'coop-001', breed: 'sussex', gender: 'female', birth_date: '2023-05-10', weight_kg: 3.1, is_active: true, health_status: 'sick', egg_production_rate: 0.45, created_at: '', updated_at: '' },
          { id: 'bird-004', bird_id: 'PTR-004', coop_id: 'coop-001', breed: 'rhode_island_red', gender: 'male', birth_date: '2023-04-01', weight_kg: 3.8, is_active: true, health_status: 'active', created_at: '', updated_at: '' },
          { id: 'bird-005', bird_id: 'PTR-005', coop_id: 'coop-001', breed: 'plymouth_rock', gender: 'female', birth_date: '2023-08-05', weight_kg: 2.5, is_active: true, health_status: 'active', egg_production_rate: 0.85, created_at: '', updated_at: '' },
          { id: 'bird-006', bird_id: 'PTR-006', coop_id: 'coop-002', breed: 'cornish', gender: 'male', birth_date: '2024-01-10', weight_kg: 4.2, is_active: true, health_status: 'active', created_at: '', updated_at: '' },
          { id: 'bird-007', bird_id: 'PTR-007', coop_id: 'coop-002', breed: 'cornish', gender: 'male', birth_date: '2024-01-15', weight_kg: 3.9, is_active: true, health_status: 'active', created_at: '', updated_at: '' },
          { id: 'bird-008', bird_id: 'PTR-008', coop_id: 'coop-002', breed: 'cornish', gender: 'female', birth_date: '2024-02-01', weight_kg: 3.5, is_active: true, health_status: 'recovering', created_at: '', updated_at: '' },
          { id: 'bird-009', bird_id: 'PTR-009', coop_id: 'coop-003', breed: 'araucana', gender: 'female', birth_date: '2024-03-10', weight_kg: 1.2, is_active: true, health_status: 'active', created_at: '', updated_at: '' },
          { id: 'bird-010', bird_id: 'PTR-010', coop_id: 'coop-001', breed: 'wyandotte', gender: 'female', birth_date: '2023-09-20', weight_kg: 2.9, is_active: false, health_status: 'quarantine', egg_production_rate: 0.0, created_at: '', updated_at: '' },
        ]);
        
        setLoading(false);
        return;
      }

      const [coopsData, birdsData] = await Promise.all([
        api.coops.getAll(),
        api.poultryRecords.getAll(),
      ]);
      
      // Map PoultryRecord to PoultryBird format
      const mappedBirds: PoultryBird[] = birdsData.map(record => ({
        id: record.id,
        bird_id: record.tag_id || record.id,
        coop_id: record.coop_id || '',
        breed: record.breed || '',
        gender: record.gender === 'unknown' ? 'female' : record.gender,
        birth_date: record.birth_date || '',
        weight_kg: record.weight_grams ? record.weight_grams / 1000 : undefined,
        is_active: record.is_active,
        health_status: record.health_status,
        created_at: record.created_at,
        updated_at: record.updated_at,
      }));
      
      setCoops(coopsData);
      setBirds(mappedBirds);
    } catch (error) {
      console.error('Error loading flock data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateAge = (birthDate: string) => {
    const birth = new Date(birthDate);
    const now = new Date();
    const months = (now.getFullYear() - birth.getFullYear()) * 12 + (now.getMonth() - birth.getMonth());
    if (months < 12) return `${months} ay`;
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    return remainingMonths > 0 ? `${years} yıl ${remainingMonths} ay` : `${years} yıl`;
  };

  const filteredBirds = birds.filter((bird) => {
    if (searchQuery && !bird.bird_id.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (selectedStatus !== 'all' && bird.health_status !== selectedStatus) {
      return false;
    }
    if (selectedCoop !== 'all' && bird.coop_id !== selectedCoop) {
      return false;
    }
    return true;
  });

  const stats = {
    total: birds.length,
    active: birds.filter(b => b.health_status === 'active').length,
    female: birds.filter(b => b.gender === 'female').length,
    male: birds.filter(b => b.gender === 'male').length,
    sick: birds.filter(b => b.health_status === 'sick' || b.health_status === 'quarantine').length,
    avgEggRate: birds.filter(b => b.egg_production_rate).reduce((sum, b) => sum + (b.egg_production_rate || 0), 0) / birds.filter(b => b.egg_production_rate).length || 0,
    avgWeight: birds.reduce((sum, b) => sum + (b.weight_kg || 0), 0) / birds.length || 0,
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/poultry" className="hover:text-foreground">Kanatlı</Link>
            <ChevronRight className="w-4 h-4" />
            <span>Sürü Yönetimi</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">🐔 Sürü Yönetimi</h1>
          <p className="text-muted-foreground mt-1">Tüm kanatlı hayvanlarınızı yönetin ve takip edin</p>
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
            Hayvan Ekle
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-5 h-5 text-primary" />
          </div>
          <div className="text-2xl font-bold">{stats.total}</div>
          <div className="text-sm text-muted-foreground">Toplam</div>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
          </div>
          <div className="text-2xl font-bold">{stats.active}</div>
          <div className="text-sm text-muted-foreground">Aktif</div>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-2">
            <Bird className="w-5 h-5 text-pink-500" />
          </div>
          <div className="text-2xl font-bold">{stats.female}</div>
          <div className="text-sm text-muted-foreground">Dişi</div>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-2">
            <Bird className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-2xl font-bold">{stats.male}</div>
          <div className="text-sm text-muted-foreground">Erkek</div>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <div className="text-2xl font-bold">{stats.sick}</div>
          <div className="text-sm text-muted-foreground">Hasta/Karantina</div>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-2">
            <Egg className="w-5 h-5 text-yellow-500" />
          </div>
          <div className="text-2xl font-bold">%{(stats.avgEggRate * 100).toFixed(0)}</div>
          <div className="text-sm text-muted-foreground">Ort. Yumurta</div>
        </div>
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-purple-500" />
          </div>
          <div className="text-2xl font-bold">{stats.avgWeight.toFixed(1)} kg</div>
          <div className="text-sm text-muted-foreground">Ort. Ağırlık</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 min-w-[250px]">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Hayvan ID'si ile ara..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg bg-background"
          />
        </div>
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-4 py-2 border rounded-lg bg-background min-w-[150px]"
        >
          <option value="all">Tüm Durumlar</option>
          {Object.entries(statusColors).map(([key, value]) => (
            <option key={key} value={key}>{value.label}</option>
          ))}
        </select>
        <select
          value={selectedCoop}
          onChange={(e) => setSelectedCoop(e.target.value)}
          className="px-4 py-2 border rounded-lg bg-background min-w-[150px]"
        >
          <option value="all">Tüm Kümesler</option>
          {coops.map((coop) => (
            <option key={coop.id} value={coop.id}>{coop.name}</option>
          ))}
        </select>
      </div>

      {/* Bird List */}
      <div className="bg-card rounded-xl border">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold">Hayvan Listesi ({filteredBirds.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">ID</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Irk</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Cinsiyet</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Yaş</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Ağırlık</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Kümes</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Yumurta Oranı</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">Durum</th>
                <th className="text-center p-4 text-sm font-medium text-muted-foreground">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {filteredBirds.map((bird) => {
                const coop = coops.find(c => c.id === bird.coop_id);
                const status = statusColors[bird.health_status || 'active'];
                const breed = breedInfo[bird.breed] || { label: bird.breed, eggColor: '-' };
                
                return (
                  <tr key={bird.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${bird.gender === 'female' ? 'bg-pink-100' : 'bg-blue-100'}`}>
                          <Bird className={`w-5 h-5 ${bird.gender === 'female' ? 'text-pink-600' : 'text-blue-600'}`} />
                        </div>
                        <span className="font-medium">{bird.bird_id}</span>
                      </div>
                    </td>
                    <td className="p-4 text-sm">{breed.label}</td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${
                        bird.gender === 'female' ? 'bg-pink-100 text-pink-700' : 'bg-blue-100 text-blue-700'
                      }`}>
                        {bird.gender === 'female' ? 'Dişi' : 'Erkek'}
                      </span>
                    </td>
                    <td className="p-4 text-center text-sm">{calculateAge(bird.birth_date)}</td>
                    <td className="p-4 text-center text-sm">{bird.weight_kg?.toFixed(1)} kg</td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Home className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm">{coop?.name || '-'}</span>
                      </div>
                    </td>
                    <td className="p-4 text-center">
                      {bird.egg_production_rate !== undefined && bird.egg_production_rate !== null ? (
                        <div className="flex items-center justify-center gap-1">
                          <Egg className="w-4 h-4 text-yellow-500" />
                          <span className={`font-medium ${
                            bird.egg_production_rate >= 0.8 ? 'text-green-600' : 
                            bird.egg_production_rate >= 0.5 ? 'text-yellow-600' : 'text-red-600'
                          }`}>
                            %{(bird.egg_production_rate * 100).toFixed(0)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">-</span>
                      )}
                    </td>
                    <td className="p-4 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs ${status?.bg} ${status?.text}`}>
                        {status?.label || bird.health_status}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <div className="flex items-center justify-center gap-2">
                        <button 
                          onClick={() => setSelectedBird(bird)}
                          className="p-1 hover:bg-muted rounded"
                        >
                          <Eye className="w-4 h-4 text-muted-foreground" />
                        </button>
                        <button className="p-1 hover:bg-muted rounded">
                          <Edit className="w-4 h-4 text-muted-foreground" />
                        </button>
                        <button className="p-1 hover:bg-muted rounded">
                          <Heart className="w-4 h-4 text-muted-foreground" />
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

      {/* Bird Detail Modal */}
      {selectedBird && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedBird(null)}>
          <div className="bg-card rounded-xl border p-6 max-w-lg w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-lg ${selectedBird.gender === 'female' ? 'bg-pink-100' : 'bg-blue-100'}`}>
                  <Bird className={`w-8 h-8 ${selectedBird.gender === 'female' ? 'text-pink-600' : 'text-blue-600'}`} />
                </div>
                <div>
                  <h2 className="text-xl font-semibold">{selectedBird.bird_id}</h2>
                  <p className="text-muted-foreground">{breedInfo[selectedBird.breed]?.label || selectedBird.breed}</p>
                </div>
              </div>
              <button onClick={() => setSelectedBird(null)} className="p-2 hover:bg-muted rounded-lg">×</button>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-muted/50 p-3 rounded-lg">
                  <div className="text-sm text-muted-foreground">Cinsiyet</div>
                  <div className="font-medium">{selectedBird.gender === 'female' ? 'Dişi' : 'Erkek'}</div>
                </div>
                <div className="bg-muted/50 p-3 rounded-lg">
                  <div className="text-sm text-muted-foreground">Yaş</div>
                  <div className="font-medium">{calculateAge(selectedBird.birth_date)}</div>
                </div>
                <div className="bg-muted/50 p-3 rounded-lg">
                  <div className="text-sm text-muted-foreground">Ağırlık</div>
                  <div className="font-medium">{selectedBird.weight_kg?.toFixed(1)} kg</div>
                </div>
                <div className="bg-muted/50 p-3 rounded-lg">
                  <div className="text-sm text-muted-foreground">Doğum Tarihi</div>
                  <div className="font-medium">{new Date(selectedBird.birth_date).toLocaleDateString('tr-TR')}</div>
                </div>
              </div>
              
              <div className="bg-muted/50 p-3 rounded-lg">
                <div className="text-sm text-muted-foreground">Kümes</div>
                <div className="font-medium">{coops.find(c => c.id === selectedBird.coop_id)?.name || '-'}</div>
              </div>
              
              {selectedBird.egg_production_rate !== undefined && selectedBird.egg_production_rate !== null && (
                <div className="bg-muted/50 p-3 rounded-lg">
                  <div className="text-sm text-muted-foreground">Yumurta Üretim Oranı</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${
                          selectedBird.egg_production_rate >= 0.8 ? 'bg-green-500' : 
                          selectedBird.egg_production_rate >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${selectedBird.egg_production_rate * 100}%` }}
                      />
                    </div>
                    <span className="font-medium">%{(selectedBird.egg_production_rate * 100).toFixed(0)}</span>
                  </div>
                </div>
              )}
              
              <div className="flex gap-2">
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
                  <Edit className="w-4 h-4" />
                  Düzenle
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 px-4 py-2 border rounded-lg hover:bg-muted transition-colors">
                  <Heart className="w-4 h-4" />
                  Sağlık Kaydı
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
