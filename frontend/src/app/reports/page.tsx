'use client';

import { useState } from 'react';
import {
  FileText,
  Download,
  Calendar,
  Filter,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  Activity,
  Printer,
  Mail,
  Clock,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart as RePieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  Legend,
} from 'recharts';

interface Report {
  id: string;
  name: string;
  type: 'günlük' | 'haftalık' | 'aylık' | 'özel';
  generatedAt: string;
  size: string;
  status: 'hazır' | 'oluşturuluyor' | 'hata';
}

const monthlyData = [
  { ay: 'Oca', hayvan: 245, sağlık: 12, alarm: 5 },
  { ay: 'Şub', hayvan: 252, sağlık: 8, alarm: 3 },
  { ay: 'Mar', hayvan: 260, sağlık: 15, alarm: 7 },
  { ay: 'Nis', hayvan: 268, sağlık: 10, alarm: 4 },
  { ay: 'May', hayvan: 275, sağlık: 6, alarm: 2 },
  { ay: 'Haz', hayvan: 282, sağlık: 9, alarm: 6 },
];

const healthDistribution = [
  { name: 'Sağlıklı', value: 85, color: '#22c55e' },
  { name: 'Tedavi Altında', value: 8, color: '#eab308' },
  { name: 'Kritik', value: 3, color: '#ef4444' },
  { name: 'Karantina', value: 4, color: '#8b5cf6' },
];

const animalTypes = [
  { tip: 'İnek', sayı: 120, renk: '#3b82f6' },
  { tip: 'Boğa', sayı: 25, renk: '#8b5cf6' },
  { tip: 'Buzağı', sayı: 45, renk: '#22c55e' },
  { tip: 'Düve', sayı: 38, renk: '#f59e0b' },
  { tip: 'Tosun', sayı: 18, renk: '#ef4444' },
];

const recentReports: Report[] = [
  {
    id: '1',
    name: 'Günlük Aktivite Raporu',
    type: 'günlük',
    generatedAt: '2024-01-15 09:00',
    size: '2.4 MB',
    status: 'hazır',
  },
  {
    id: '2',
    name: 'Haftalık Sağlık Özeti',
    type: 'haftalık',
    generatedAt: '2024-01-14 18:00',
    size: '5.8 MB',
    status: 'hazır',
  },
  {
    id: '3',
    name: 'Aylık Üretim Raporu',
    type: 'aylık',
    generatedAt: '2024-01-01 00:00',
    size: '12.3 MB',
    status: 'hazır',
  },
  {
    id: '4',
    name: 'Özel Analiz Raporu',
    type: 'özel',
    generatedAt: '2024-01-15 10:30',
    size: '-',
    status: 'oluşturuluyor',
  },
];

const reportTemplates = [
  { id: 'daily', name: 'Günlük Aktivite', icon: Clock, description: 'Günlük hayvan hareketleri ve aktiviteleri' },
  { id: 'health', name: 'Sağlık Raporu', icon: Activity, description: 'Sağlık durumu ve tedavi istatistikleri' },
  { id: 'production', name: 'Üretim Raporu', icon: BarChart3, description: 'Süt, et ve yumurta üretim verileri' },
  { id: 'financial', name: 'Mali Rapor', icon: TrendingUp, description: 'Gelir, gider ve karlılık analizi' },
];

export default function ReportsPage() {
  const [dateRange, setDateRange] = useState('thisMonth');
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  const getStatusBadge = (status: Report['status']) => {
    const styles = {
      hazır: 'bg-green-100 text-green-800',
      oluşturuluyor: 'bg-yellow-100 text-yellow-800',
      hata: 'bg-red-100 text-red-800',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getTypeBadge = (type: Report['type']) => {
    const styles = {
      günlük: 'bg-blue-100 text-blue-800',
      haftalık: 'bg-purple-100 text-purple-800',
      aylık: 'bg-indigo-100 text-indigo-800',
      özel: 'bg-gray-100 text-gray-800',
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[type]}`}>
        {type.charAt(0).toUpperCase() + type.slice(1)}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Raporlar</h1>
          <p className="text-gray-500">Çiftlik verilerinizi analiz edin ve raporlayın</p>
        </div>
        <div className="flex gap-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
          >
            <option value="today">Bugün</option>
            <option value="thisWeek">Bu Hafta</option>
            <option value="thisMonth">Bu Ay</option>
            <option value="lastMonth">Geçen Ay</option>
            <option value="thisYear">Bu Yıl</option>
            <option value="custom">Özel Tarih</option>
          </select>
          <button className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
            <FileText className="w-5 h-5" />
            Yeni Rapor
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Toplam Hayvan</p>
              <p className="text-2xl font-bold text-gray-900">282</p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">+7 bu ay</p>
        </div>
        
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Sağlık Olayları</p>
              <p className="text-2xl font-bold text-gray-900">9</p>
            </div>
            <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
              <Activity className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <p className="text-sm text-red-600 mt-2">+3 bu hafta</p>
        </div>
        
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Aktif Alarmlar</p>
              <p className="text-2xl font-bold text-gray-900">6</p>
            </div>
            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
              <TrendingDown className="w-6 h-6 text-red-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 mt-2">-2 dün</p>
        </div>
        
        <div className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Oluşturulan Rapor</p>
              <p className="text-2xl font-bold text-gray-900">24</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <FileText className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">Bu ay</p>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Aylık Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="ay" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey="hayvan"
                name="Toplam Hayvan"
                stroke="#3b82f6"
                fill="#3b82f680"
              />
              <Area
                type="monotone"
                dataKey="sağlık"
                name="Sağlık Olayı"
                stroke="#eab308"
                fill="#eab30880"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Health Distribution */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Sağlık Dağılımı</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RePieChart>
              <Pie
                data={healthDistribution}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              >
                {healthDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </RePieChart>
          </ResponsiveContainer>
        </div>

        {/* Animal Types Bar Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 lg:col-span-2">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Hayvan Türlerine Göre Dağılım</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={animalTypes}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tip" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="sayı" name="Sayı" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                {animalTypes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.renk} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Report Templates */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Rapor Şablonları</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {reportTemplates.map((template) => (
            <button
              key={template.id}
              onClick={() => setSelectedTemplate(template.id)}
              className={`p-4 rounded-xl border-2 transition-all text-left ${
                selectedTemplate === template.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <template.icon className={`w-8 h-8 mb-3 ${
                selectedTemplate === template.id ? 'text-primary-600' : 'text-gray-400'
              }`} />
              <h4 className="font-medium text-gray-900">{template.name}</h4>
              <p className="text-sm text-gray-500 mt-1">{template.description}</p>
            </button>
          ))}
        </div>
        {selectedTemplate && (
          <div className="mt-4 flex gap-3">
            <button className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700 transition-colors">
              <FileText className="w-5 h-5" />
              Rapor Oluştur
            </button>
            <button className="flex items-center gap-2 border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors">
              <Calendar className="w-5 h-5" />
              Zamanlı Rapor
            </button>
          </div>
        )}
      </div>

      {/* Recent Reports */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Son Raporlar</h3>
            <button className="flex items-center gap-2 text-primary-600 hover:text-primary-700">
              <Filter className="w-4 h-4" />
              Filtrele
            </button>
          </div>
        </div>
        <div className="divide-y divide-gray-100">
          {recentReports.map((report) => (
            <div key={report.id} className="p-4 flex items-center justify-between hover:bg-gray-50">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-gray-600" />
                </div>
                <div>
                  <h4 className="font-medium text-gray-900">{report.name}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    {getTypeBadge(report.type)}
                    <span className="text-sm text-gray-500">{report.generatedAt}</span>
                    <span className="text-sm text-gray-400">•</span>
                    <span className="text-sm text-gray-500">{report.size}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {getStatusBadge(report.status)}
                {report.status === 'hazır' && (
                  <div className="flex gap-2">
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="İndir">
                      <Download className="w-5 h-5 text-gray-600" />
                    </button>
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="Yazdır">
                      <Printer className="w-5 h-5 text-gray-600" />
                    </button>
                    <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors" title="E-posta">
                      <Mail className="w-5 h-5 text-gray-600" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
