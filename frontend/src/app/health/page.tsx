'use client';

import { useState } from 'react';
import {
  Activity,
  Plus,
  Calendar,
  Thermometer,
  Weight,
  Pill,
  FileText,
  Search,
  Filter,
} from 'lucide-react';

interface HealthRecord {
  id: number;
  animal_id: number;
  animal_tag: string;
  animal_name?: string;
  check_date: string;
  health_status: string;
  temperature?: number;
  weight?: number;
  symptoms?: string;
  diagnosis?: string;
  treatment?: string;
  notes?: string;
  vet_name?: string;
}

const mockRecords: HealthRecord[] = [
  { id: 1, animal_id: 1, animal_tag: 'TR-001', animal_name: 'Sarıkız', check_date: '2024-12-02', health_status: 'healthy', temperature: 38.5, weight: 452, notes: 'Rutin kontrol, sağlık durumu iyi', vet_name: 'Dr. Ahmet Yılmaz' },
  { id: 2, animal_id: 2, animal_tag: 'TR-002', animal_name: 'Karabaş', check_date: '2024-12-01', health_status: 'warning', temperature: 39.8, weight: 518, symptoms: 'Hafif öksürük', diagnosis: 'Üst solunum yolu enfeksiyonu şüphesi', treatment: 'Antibiyotik tedavisi başlandı', vet_name: 'Dr. Ahmet Yılmaz' },
  { id: 3, animal_id: 5, animal_tag: 'TR-005', check_date: '2024-11-30', health_status: 'sick', temperature: 40.2, weight: 68, symptoms: 'İştahsızlık, halsizlik', diagnosis: 'Parazit enfeksiyonu', treatment: 'Antiparaziter ilaç verildi', vet_name: 'Dr. Fatma Demir' },
  { id: 4, animal_id: 3, animal_tag: 'TR-003', animal_name: 'Benekli', check_date: '2024-11-28', health_status: 'healthy', temperature: 38.3, weight: 382, notes: 'Aşı yapıldı', vet_name: 'Dr. Fatma Demir' },
  { id: 5, animal_id: 4, animal_tag: 'TR-004', check_date: '2024-11-25', health_status: 'healthy', temperature: 39.0, weight: 66, notes: 'Genel sağlık kontrolü', vet_name: 'Dr. Ahmet Yılmaz' },
];

const statusConfig = {
  healthy: { bg: 'bg-success-100', text: 'text-success-600', label: 'Sağlıklı' },
  warning: { bg: 'bg-warning-100', text: 'text-warning-600', label: 'Dikkat' },
  sick: { bg: 'bg-danger-100', text: 'text-danger-600', label: 'Hasta' },
};

export default function HealthPage() {
  const [records, setRecords] = useState<HealthRecord[]>(mockRecords);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [showForm, setShowForm] = useState(false);

  const filteredRecords = records.filter(record => {
    const matchesSearch = 
      record.animal_tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (record.animal_name?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false);
    const matchesStatus = filterStatus === 'all' || record.health_status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sağlık Kayıtları</h1>
          <p className="text-gray-500 mt-1">Toplam {records.length} kayıt</p>
        </div>
        
        <button 
          onClick={() => setShowForm(true)}
          className="btn-primary flex items-center gap-2 w-fit"
        >
          <Plus className="w-5 h-5" />
          Yeni Kayıt
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="card text-center">
          <p className="text-3xl font-bold text-success-600">
            {records.filter(r => r.health_status === 'healthy').length}
          </p>
          <p className="text-sm text-gray-500">Sağlıklı</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-warning-600">
            {records.filter(r => r.health_status === 'warning').length}
          </p>
          <p className="text-sm text-gray-500">Dikkat</p>
        </div>
        <div className="card text-center">
          <p className="text-3xl font-bold text-danger-600">
            {records.filter(r => r.health_status === 'sick').length}
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
              placeholder="Hayvan ara..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
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

      {/* Records List */}
      <div className="space-y-4">
        {filteredRecords.length === 0 ? (
          <div className="card text-center py-12">
            <Activity className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Sağlık kaydı bulunamadı</p>
          </div>
        ) : (
          filteredRecords.map((record) => {
            const status = statusConfig[record.health_status as keyof typeof statusConfig] || statusConfig.healthy;
            
            return (
              <div key={record.id} className="card">
                <div className="flex flex-col lg:flex-row lg:items-start gap-4">
                  {/* Header */}
                  <div className="flex items-start gap-3 lg:w-48">
                    <div className={`p-3 rounded-xl ${status.bg}`}>
                      <Activity className={`w-5 h-5 ${status.text}`} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {record.animal_name || record.animal_tag}
                      </h3>
                      <p className="text-sm text-gray-500">{record.animal_tag}</p>
                      <span className={`badge ${status.bg} ${status.text} mt-2`}>
                        {status.label}
                      </span>
                    </div>
                  </div>
                  
                  {/* Details */}
                  <div className="flex-1 grid grid-cols-2 sm:grid-cols-4 gap-4">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      <div>
                        <p className="text-xs text-gray-500">Tarih</p>
                        <p className="text-sm font-medium">
                          {new Date(record.check_date).toLocaleDateString('tr-TR')}
                        </p>
                      </div>
                    </div>
                    
                    {record.temperature && (
                      <div className="flex items-center gap-2">
                        <Thermometer className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-xs text-gray-500">Sıcaklık</p>
                          <p className="text-sm font-medium">{record.temperature}°C</p>
                        </div>
                      </div>
                    )}
                    
                    {record.weight && (
                      <div className="flex items-center gap-2">
                        <Weight className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-xs text-gray-500">Ağırlık</p>
                          <p className="text-sm font-medium">{record.weight} kg</p>
                        </div>
                      </div>
                    )}
                    
                    {record.vet_name && (
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-400" />
                        <div>
                          <p className="text-xs text-gray-500">Veteriner</p>
                          <p className="text-sm font-medium">{record.vet_name}</p>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Additional Info */}
                {(record.symptoms || record.diagnosis || record.treatment || record.notes) && (
                  <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
                    {record.symptoms && (
                      <p className="text-sm"><span className="text-gray-500">Belirtiler:</span> {record.symptoms}</p>
                    )}
                    {record.diagnosis && (
                      <p className="text-sm"><span className="text-gray-500">Tanı:</span> {record.diagnosis}</p>
                    )}
                    {record.treatment && (
                      <p className="text-sm"><span className="text-gray-500">Tedavi:</span> {record.treatment}</p>
                    )}
                    {record.notes && (
                      <p className="text-sm"><span className="text-gray-500">Notlar:</span> {record.notes}</p>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
