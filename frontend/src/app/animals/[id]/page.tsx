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
  Weight,
  Activity,
  Thermometer,
  Syringe,
  FileText,
  Camera,
  AlertTriangle,
  Clock,
  Tag,
  Info,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface Animal {
  id: string;
  name: string;
  tag: string;
  type: string;
  breed: string;
  gender: 'erkek' | 'dişi';
  birthDate: string;
  weight: number;
  status: 'sağlıklı' | 'hasta' | 'tedavide' | 'karantina';
  zone: string;
  lastSeen: string;
  image: string;
  mother?: string;
  father?: string;
  notes: string;
}

interface HealthRecord {
  id: string;
  date: string;
  type: 'muayene' | 'aşı' | 'tedavi' | 'kontrol';
  description: string;
  vet: string;
  result: string;
}

interface WeightHistory {
  date: string;
  weight: number;
}

// Mock data
const mockAnimal: Animal = {
  id: '1',
  name: 'Sarıkız',
  tag: 'TR-001-2023',
  type: 'İnek',
  breed: 'Holstein',
  gender: 'dişi',
  birthDate: '2021-03-15',
  weight: 485,
  status: 'sağlıklı',
  zone: 'Otlak A',
  lastSeen: '5 dakika önce',
  image: '/api/placeholder/400/300',
  mother: 'Benekli (TR-089-2018)',
  father: 'Karabaş (TR-045-2017)',
  notes: 'Süt verimi yüksek, günde ortalama 28 litre. Sakin mizaçlı.',
};

const mockHealthRecords: HealthRecord[] = [
  {
    id: '1',
    date: '2024-01-10',
    type: 'muayene',
    description: 'Rutin sağlık kontrolü',
    vet: 'Dr. Ahmet Yılmaz',
    result: 'Sağlıklı',
  },
  {
    id: '2',
    date: '2023-12-15',
    type: 'aşı',
    description: 'Şap aşısı',
    vet: 'Dr. Ahmet Yılmaz',
    result: 'Tamamlandı',
  },
  {
    id: '3',
    date: '2023-11-20',
    type: 'tedavi',
    description: 'Antibiyotik tedavisi - solunum yolu enfeksiyonu',
    vet: 'Dr. Fatma Demir',
    result: 'İyileşti',
  },
  {
    id: '4',
    date: '2023-10-05',
    type: 'kontrol',
    description: 'Gebelik kontrolü',
    vet: 'Dr. Ahmet Yılmaz',
    result: 'Gebe değil',
  },
];

const mockWeightHistory: WeightHistory[] = [
  { date: 'Ağu', weight: 420 },
  { date: 'Eyl', weight: 435 },
  { date: 'Eki', weight: 450 },
  { date: 'Kas', weight: 465 },
  { date: 'Ara', weight: 478 },
  { date: 'Oca', weight: 485 },
];

export default function AnimalDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [healthRecords, setHealthRecords] = useState<HealthRecord[]>([]);
  const [activeTab, setActiveTab] = useState<'overview' | 'health' | 'history'>('overview');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulating API call
    setTimeout(() => {
      setAnimal(mockAnimal);
      setHealthRecords(mockHealthRecords);
      setLoading(false);
    }, 500);
  }, [params.id]);

  const getStatusColor = (status: Animal['status']) => {
    const colors = {
      sağlıklı: 'bg-green-100 text-green-800',
      hasta: 'bg-red-100 text-red-800',
      tedavide: 'bg-yellow-100 text-yellow-800',
      karantina: 'bg-purple-100 text-purple-800',
    };
    return colors[status];
  };

  const getRecordTypeIcon = (type: HealthRecord['type']) => {
    const icons = {
      muayene: Activity,
      aşı: Syringe,
      tedavi: Heart,
      kontrol: FileText,
    };
    const Icon = icons[type];
    return <Icon className="w-5 h-5" />;
  };

  const getRecordTypeColor = (type: HealthRecord['type']) => {
    const colors = {
      muayene: 'bg-blue-100 text-blue-600',
      aşı: 'bg-green-100 text-green-600',
      tedavi: 'bg-red-100 text-red-600',
      kontrol: 'bg-purple-100 text-purple-600',
    };
    return colors[type];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!animal) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900">Hayvan bulunamadı</h2>
        <p className="text-gray-500 mt-2">Bu ID ile kayıtlı hayvan yok.</p>
        <Link href="/animals" className="text-primary-600 hover:underline mt-4 inline-block">
          Hayvanlara Dön
        </Link>
      </div>
    );
  }

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
              <h1 className="text-2xl font-bold text-gray-900">{animal.name}</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(animal.status)}`}>
                {animal.status.charAt(0).toUpperCase() + animal.status.slice(1)}
              </span>
            </div>
            <p className="text-gray-500 flex items-center gap-2 mt-1">
              <Tag className="w-4 h-4" />
              {animal.tag}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
            <Camera className="w-5 h-5" />
            Kameradan İzle
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            <Edit className="w-5 h-5" />
            Düzenle
          </button>
          <button className="flex items-center gap-2 px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors">
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', name: 'Genel Bakış', icon: Info },
            { id: 'health', name: 'Sağlık Kayıtları', icon: Heart },
            { id: 'history', name: 'Geçmiş', icon: Clock },
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
          {/* Main Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Weight className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Ağırlık</p>
                    <p className="text-lg font-semibold">{animal.weight} kg</p>
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
                    <p className="text-lg font-semibold">2 yıl 10 ay</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <MapPin className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Bölge</p>
                    <p className="text-lg font-semibold">{animal.zone}</p>
                  </div>
                </div>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <Clock className="w-5 h-5 text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Son Görülme</p>
                    <p className="text-lg font-semibold">{animal.lastSeen}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Weight Chart */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Ağırlık Geçmişi</h3>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={mockWeightHistory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis domain={['dataMin - 20', 'dataMax + 20']} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="weight"
                    name="Ağırlık (kg)"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: '#3b82f6' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Details */}
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Detaylar</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Tür</p>
                  <p className="font-medium">{animal.type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Irk</p>
                  <p className="font-medium">{animal.breed}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Cinsiyet</p>
                  <p className="font-medium capitalize">{animal.gender}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Doğum Tarihi</p>
                  <p className="font-medium">{new Date(animal.birthDate).toLocaleDateString('tr-TR')}</p>
                </div>
                {animal.mother && (
                  <div>
                    <p className="text-sm text-gray-500">Anne</p>
                    <p className="font-medium text-primary-600">{animal.mother}</p>
                  </div>
                )}
                {animal.father && (
                  <div>
                    <p className="text-sm text-gray-500">Baba</p>
                    <p className="font-medium text-primary-600">{animal.father}</p>
                  </div>
                )}
              </div>
              {animal.notes && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <p className="text-sm text-gray-500">Notlar</p>
                  <p className="mt-1">{animal.notes}</p>
                </div>
              )}
            </div>
          </div>

          {/* Side Info */}
          <div className="space-y-6">
            {/* Photo */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center">
                <Camera className="w-12 h-12 text-gray-400" />
              </div>
              <p className="text-sm text-gray-500 text-center mt-2">Son kamera görüntüsü</p>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">Hızlı İşlemler</h3>
              <div className="space-y-2">
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <Activity className="w-5 h-5 text-blue-600" />
                  <span>Sağlık Kaydı Ekle</span>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <Weight className="w-5 h-5 text-green-600" />
                  <span>Ağırlık Güncelle</span>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <Syringe className="w-5 h-5 text-purple-600" />
                  <span>Aşı Kaydı Ekle</span>
                </button>
                <button className="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left">
                  <MapPin className="w-5 h-5 text-yellow-600" />
                  <span>Bölge Değiştir</span>
                </button>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <h3 className="font-semibold text-gray-900 mb-3">Son Aktivite</h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm">Otlak A&apos;ya giriş</p>
                    <p className="text-xs text-gray-500">5 dakika önce</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm">Su noktası ziyareti</p>
                    <p className="text-xs text-gray-500">1 saat önce</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm">Ahırdan çıkış</p>
                    <p className="text-xs text-gray-500">3 saat önce</p>
                  </div>
                </div>
              </div>
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
            {healthRecords.map((record) => (
              <div key={record.id} className="p-4 flex items-start gap-4">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${getRecordTypeColor(record.type)}`}>
                  {getRecordTypeIcon(record.type)}
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

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Hareket Geçmişi</h3>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
            <div className="space-y-6">
              {[
                { date: 'Bugün 09:45', event: 'Otlak A bölgesine giriş yaptı', type: 'location' },
                { date: 'Bugün 07:30', event: 'Sabah yemi verildi', type: 'feed' },
                { date: 'Bugün 06:15', event: 'Ahırdan çıkış', type: 'exit' },
                { date: 'Dün 18:00', event: 'Akşam sağımı tamamlandı', type: 'milk' },
                { date: 'Dün 17:30', event: 'Ahıra giriş', type: 'entry' },
                { date: 'Dün 12:00', event: 'Su kaynağı ziyareti', type: 'water' },
              ].map((item, index) => (
                <div key={index} className="flex gap-4 items-start pl-8 relative">
                  <div className="absolute left-2.5 w-3 h-3 bg-primary-500 rounded-full border-2 border-white"></div>
                  <div>
                    <p className="text-sm text-gray-500">{item.date}</p>
                    <p className="font-medium">{item.event}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
