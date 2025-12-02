'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Edit,
  Trash2,
  Heart,
  Calendar,
  MapPin,
  Activity,
  Thermometer,
  Syringe,
  FileText,
  Camera,
  AlertTriangle,
  Clock,
  Tag,
  Info,
  Egg,
  Bird,
  Sun,
  Moon,
  Droplets,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts';

interface Poultry {
  id: string;
  coopId: string;
  coopName: string;
  birdType: 'tavuk' | 'hindi' | 'ördek' | 'kaz';
  breed: string;
  count: number;
  age: number; // hafta
  status: 'aktif' | 'karantina' | 'tedavide';
  avgWeight: number; // gram
  feedConsumption: number; // kg/gün
  waterConsumption: number; // litre/gün
  mortality: number; // %
  lastInspection: string;
  temperature: number;
  humidity: number;
  lightHours: number;
  notes: string;
}

interface EggProduction {
  date: string;
  total: number;
  cracked: number;
  dirty: number;
}

interface HealthRecord {
  id: string;
  date: string;
  type: 'muayene' | 'aşı' | 'tedavi' | 'dezenfeksiyon';
  description: string;
  vet: string;
  result: string;
}

// Mock data
const mockPoultry: Poultry = {
  id: '1',
  coopId: 'COOP-001',
  coopName: 'Kümes A - Yumurtacı',
  birdType: 'tavuk',
  breed: 'Lohmann Brown',
  count: 2500,
  age: 28,
  status: 'aktif',
  avgWeight: 1850,
  feedConsumption: 275,
  waterConsumption: 450,
  mortality: 0.8,
  lastInspection: '2024-01-15 08:30',
  temperature: 22,
  humidity: 65,
  lightHours: 16,
  notes: 'Verimlilik yüksek, yumurta kalitesi iyi. Günlük ortalama %92 verim.',
};

const mockEggProduction: EggProduction[] = [
  { date: 'Pzt', total: 2280, cracked: 45, dirty: 23 },
  { date: 'Sal', total: 2310, cracked: 38, dirty: 28 },
  { date: 'Çar', total: 2295, cracked: 42, dirty: 19 },
  { date: 'Per', total: 2320, cracked: 35, dirty: 22 },
  { date: 'Cum', total: 2275, cracked: 48, dirty: 31 },
  { date: 'Cmt', total: 2305, cracked: 40, dirty: 25 },
  { date: 'Paz', total: 2290, cracked: 37, dirty: 20 },
];

const mockHealthRecords: HealthRecord[] = [
  {
    id: '1',
    date: '2024-01-15',
    type: 'muayene',
    description: 'Haftalık rutin kontrol',
    vet: 'Dr. Mehmet Kaya',
    result: 'Sağlıklı',
  },
  {
    id: '2',
    date: '2024-01-10',
    type: 'dezenfeksiyon',
    description: 'Kümes dezenfeksiyonu',
    vet: 'Personel',
    result: 'Tamamlandı',
  },
  {
    id: '3',
    date: '2024-01-01',
    type: 'aşı',
    description: 'Newcastle aşısı',
    vet: 'Dr. Mehmet Kaya',
    result: 'Başarılı',
  },
];

export default function PoultryDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [poultry, setPoultry] = useState<Poultry | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'production' | 'health'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setPoultry(mockPoultry);
      setLoading(false);
    }, 500);
  }, [params.id]);

  const getStatusColor = (status: Poultry['status']) => {
    const colors = {
      aktif: 'bg-green-100 text-green-800',
      karantina: 'bg-purple-100 text-purple-800',
      tedavide: 'bg-yellow-100 text-yellow-800',
    };
    return colors[status];
  };

  const getBirdTypeIcon = (type: Poultry['birdType']) => {
    return Bird; // Can be extended for different bird types
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!poultry) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Kümes bulunamadı</h2>
        <p className="text-gray-500 mt-2">Bu ID ile kayıtlı kümes yok.</p>
        <Link href="/poultry" className="text-primary-600 hover:underline mt-4 inline-block">
          Kanatlılara Dön
        </Link>
      </div>
    );
  }

  const BirdIcon = getBirdTypeIcon(poultry.birdType);
  const productionRate = ((mockEggProduction.reduce((a, b) => a + b.total, 0) / 7) / poultry.count * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">{poultry.coopName}</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(poultry.status)}`}>
                {poultry.status.charAt(0).toUpperCase() + poultry.status.slice(1)}
              </span>
            </div>
            <p className="text-gray-500 flex items-center gap-2 mt-1">
              <Tag className="w-4 h-4" />
              {poultry.coopId} • {poultry.breed}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <Camera className="w-5 h-5" />
            Canlı İzle
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Edit className="w-5 h-5" />
            Düzenle
          </button>
        </div>
      </div>

      {/* Environment Alert */}
      {(poultry.temperature < 18 || poultry.temperature > 25 || poultry.humidity < 50 || poultry.humidity > 70) && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-yellow-800">Çevre Koşulları Uyarısı</p>
            <p className="text-sm text-yellow-700 mt-1">
              {poultry.temperature < 18 && 'Sıcaklık çok düşük. '}
              {poultry.temperature > 25 && 'Sıcaklık çok yüksek. '}
              {poultry.humidity < 50 && 'Nem çok düşük. '}
              {poultry.humidity > 70 && 'Nem çok yüksek. '}
              Lütfen kontrol ediniz.
            </p>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', name: 'Genel Bakış', icon: Info },
            { id: 'production', name: 'Üretim', icon: Egg },
            { id: 'health', name: 'Sağlık', icon: Heart },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <BirdIcon className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Kuş Sayısı</p>
                    <p className="text-lg font-semibold">{poultry.count.toLocaleString()}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Calendar className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Yaş</p>
                    <p className="text-lg font-semibold">{poultry.age} hafta</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <Egg className="w-5 h-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Verimlilik</p>
                    <p className="text-lg font-semibold">%{productionRate}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                    <Activity className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Ölüm Oranı</p>
                    <p className="text-lg font-semibold">%{poultry.mortality}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Environment Conditions */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Çevre Koşulları</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="w-16 h-16 mx-auto bg-orange-100 rounded-full flex items-center justify-center mb-2">
                    <Thermometer className="w-8 h-8 text-orange-600" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{poultry.temperature}°C</p>
                  <p className="text-sm text-gray-500">Sıcaklık</p>
                  <p className="text-xs text-gray-400 mt-1">İdeal: 18-25°C</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 mx-auto bg-blue-100 rounded-full flex items-center justify-center mb-2">
                    <Droplets className="w-8 h-8 text-blue-600" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">%{poultry.humidity}</p>
                  <p className="text-sm text-gray-500">Nem</p>
                  <p className="text-xs text-gray-400 mt-1">İdeal: %50-70</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 mx-auto bg-yellow-100 rounded-full flex items-center justify-center mb-2">
                    <Sun className="w-8 h-8 text-yellow-600" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{poultry.lightHours}s</p>
                  <p className="text-sm text-gray-500">Aydınlatma</p>
                  <p className="text-xs text-gray-400 mt-1">İdeal: 14-16 saat</p>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-2">
                    <Activity className="w-8 h-8 text-green-600" />
                  </div>
                  <p className="text-2xl font-bold text-gray-900">{poultry.avgWeight}g</p>
                  <p className="text-sm text-gray-500">Ort. Ağırlık</p>
                  <p className="text-xs text-gray-400 mt-1">Hedef: 1800-2000g</p>
                </div>
              </div>
            </div>

            {/* Consumption Stats */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Tüketim Bilgileri</h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-500">Günlük Yem Tüketimi</span>
                    <span className="font-semibold">{poultry.feedConsumption} kg</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-500 h-2 rounded-full"
                      style={{ width: `${(poultry.feedConsumption / 300) * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    Kuş başı: {(poultry.feedConsumption / poultry.count * 1000).toFixed(0)}g
                  </p>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-gray-500">Günlük Su Tüketimi</span>
                    <span className="font-semibold">{poultry.waterConsumption} L</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(poultry.waterConsumption / 500) * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">
                    Kuş başı: {(poultry.waterConsumption / poultry.count * 1000).toFixed(0)}ml
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Side Content */}
          <div className="space-y-6">
            {/* Camera Preview */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
                <Camera className="w-12 h-12 text-gray-400" />
              </div>
              <p className="text-sm text-gray-500 text-center mt-2">Canlı kamera görüntüsü</p>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">Hızlı İşlemler</h3>
              <div className="space-y-2">
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <Egg className="w-5 h-5 text-yellow-600" />
                  <span>Yumurta Kaydı</span>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <Activity className="w-5 h-5 text-blue-600" />
                  <span>Sağlık Kontrolü</span>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <Syringe className="w-5 h-5 text-purple-600" />
                  <span>Aşı Kaydı</span>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <FileText className="w-5 h-5 text-green-600" />
                  <span>Rapor Oluştur</span>
                </button>
              </div>
            </div>

            {/* Notes */}
            {poultry.notes && (
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <h3 className="font-semibold text-gray-900 mb-2">Notlar</h3>
                <p className="text-sm text-gray-600">{poultry.notes}</p>
                <p className="text-xs text-gray-400 mt-2">
                  Son kontrol: {new Date(poultry.lastInspection).toLocaleString('tr-TR')}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Production Tab */}
      {activeTab === 'production' && (
        <div className="space-y-6">
          {/* Production Chart */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Haftalık Yumurta Üretimi</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={mockEggProduction}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="total" name="Toplam" fill="#22c55e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="cracked" name="Kırık" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="dirty" name="Kirli" fill="#eab308" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Production Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500">Haftalık Toplam</p>
              <p className="text-2xl font-bold text-green-600">
                {mockEggProduction.reduce((a, b) => a + b.total, 0).toLocaleString()}
              </p>
              <p className="text-xs text-gray-400 mt-1">yumurta</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500">Günlük Ortalama</p>
              <p className="text-2xl font-bold text-blue-600">
                {Math.round(mockEggProduction.reduce((a, b) => a + b.total, 0) / 7).toLocaleString()}
              </p>
              <p className="text-xs text-gray-400 mt-1">yumurta/gün</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500">Kırık Oranı</p>
              <p className="text-2xl font-bold text-red-600">
                %{((mockEggProduction.reduce((a, b) => a + b.cracked, 0) / mockEggProduction.reduce((a, b) => a + b.total, 0)) * 100).toFixed(1)}
              </p>
              <p className="text-xs text-gray-400 mt-1">haftalık</p>
            </div>
            <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
              <p className="text-sm text-gray-500">Verimlilik</p>
              <p className="text-2xl font-bold text-purple-600">%{productionRate}</p>
              <p className="text-xs text-gray-400 mt-1">ortalama</p>
            </div>
          </div>
        </div>
      )}

      {/* Health Tab */}
      {activeTab === 'health' && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900">Sağlık Kayıtları</h3>
            <button className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
              <Heart className="w-5 h-5" />
              Kayıt Ekle
            </button>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 divide-y divide-gray-100">
            {mockHealthRecords.map((record) => (
              <div key={record.id} className="p-4 flex items-start gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  record.type === 'muayene' ? 'bg-blue-100 text-blue-600' :
                  record.type === 'aşı' ? 'bg-green-100 text-green-600' :
                  record.type === 'tedavi' ? 'bg-red-100 text-red-600' :
                  'bg-purple-100 text-purple-600'
                }`}>
                  {record.type === 'muayene' && <Activity className="w-5 h-5" />}
                  {record.type === 'aşı' && <Syringe className="w-5 h-5" />}
                  {record.type === 'tedavi' && <Heart className="w-5 h-5" />}
                  {record.type === 'dezenfeksiyon' && <Droplets className="w-5 h-5" />}
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{record.description}</p>
                      <p className="text-sm text-gray-500">{record.vet}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-500">
                        {new Date(record.date).toLocaleDateString('tr-TR')}
                      </p>
                      <span className="inline-block mt-1 px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs">
                        {record.result}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
