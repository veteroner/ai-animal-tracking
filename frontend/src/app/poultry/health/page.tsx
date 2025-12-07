'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Activity,
  AlertTriangle,
  Heart,
  Stethoscope,
  Plus,
  RefreshCw,
  ChevronRight,
  CheckCircle,
  XCircle,
  Clock,
  Pill,
  FileText,
} from 'lucide-react';
import { api, isSupabaseConfigured, PoultryHealthRecord, PoultryRecord } from '@/lib/supabase';

const healthStatusInfo: Record<string, { label: string; color: string; icon: typeof Heart }> = {
  healthy: { label: 'Sağlıklı', color: 'bg-green-100 text-green-700', icon: Heart },
  sick: { label: 'Hasta', color: 'bg-red-100 text-red-700', icon: AlertTriangle },
  injured: { label: 'Yaralı', color: 'bg-orange-100 text-orange-700', icon: XCircle },
  molting: { label: 'Tüy Dökümü', color: 'bg-blue-100 text-blue-700', icon: Activity },
  broody: { label: 'Kuluçka', color: 'bg-purple-100 text-purple-700', icon: Clock },
  stressed: { label: 'Stresli', color: 'bg-yellow-100 text-yellow-700', icon: AlertTriangle },
};

export default function PoultryHealthPage() {
  const [records, setRecords] = useState<PoultryHealthRecord[]>([]);
  const [birds, setBirds] = useState<PoultryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    healthy: 0,
    sick: 0,
    molting: 0,
    broody: 0,
    activeAlerts: 0,
  });
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      if (!isSupabaseConfigured()) {
        // Demo verileri
        setStats({
          healthy: 145,
          sick: 3,
          molting: 12,
          broody: 5,
          activeAlerts: 2,
        });
        
        setBirds([
          { id: 'ptr-001', tag_id: 'T-001', name: 'Pamuk', poultry_type: 'chicken', health_status: 'healthy', gender: 'female', is_active: true, created_at: '', updated_at: '' },
          { id: 'ptr-005', tag_id: 'T-005', name: 'Tüylü', poultry_type: 'chicken', health_status: 'broody', gender: 'female', is_active: true, created_at: '', updated_at: '' },
          { id: 'ptr-007', tag_id: 'T-007', poultry_type: 'chicken', health_status: 'molting', gender: 'female', is_active: true, created_at: '', updated_at: '' },
          { id: 'ptr-003', tag_id: 'T-003', name: 'Benekli', poultry_type: 'chicken', health_status: 'sick', gender: 'female', is_active: true, created_at: '', updated_at: '' },
        ]);
        
        setRecords([
          { 
            id: 'h-001', 
            poultry_id: 'ptr-005', 
            health_status: 'broody', 
            symptoms: ['yumurta üzerinde oturma', 'saldırgan davranış'],
            diagnosis: 'Kuluçka davranışı',
            treatment: 'İzleme',
            recorded_at: new Date().toISOString(),
            is_resolved: false,
          },
          { 
            id: 'h-002', 
            poultry_id: 'ptr-007', 
            health_status: 'molting', 
            symptoms: ['tüy dökümü', 'yumurta üretimi durması'],
            diagnosis: 'Mevsimsel tüy değişimi',
            treatment: 'Protein takviyeli yem',
            recorded_at: new Date(Date.now() - 86400000).toISOString(),
            is_resolved: false,
          },
          { 
            id: 'h-003', 
            poultry_id: 'ptr-003', 
            health_status: 'sick', 
            symptoms: ['ishal', 'iştahsızlık'],
            diagnosis: 'Hafif sindirim sorunu',
            treatment: 'Probiyotik takviyesi',
            veterinarian: 'Dr. Veteriner',
            recorded_at: new Date(Date.now() - 172800000).toISOString(),
            is_resolved: true,
            resolved_at: new Date(Date.now() - 86400000).toISOString(),
          },
        ]);
        
        setLoading(false);
        return;
      }

      const [healthData, poultryData, dashboardStats] = await Promise.all([
        api.poultryHealth.getAll(),
        api.poultryRecords.getAll(),
        api.poultryStats.getDashboard(),
      ]);
      
      setRecords(healthData);
      setBirds(poultryData);
      setStats({
        healthy: dashboardStats.healthyBirds,
        sick: dashboardStats.sickBirds,
        molting: 0,
        broody: 0,
        activeAlerts: dashboardStats.unresolvedAlerts,
      });
    } catch (error) {
      console.error('Error loading health data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredBirds = filterStatus === 'all' 
    ? birds 
    : birds.filter(b => b.health_status === filterStatus);

  const unresolvedRecords = records.filter(r => !r.is_resolved);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Link href="/poultry" className="hover:text-foreground">Kanatlı</Link>
            <ChevronRight className="w-4 h-4" />
            <span>Sağlık İzleme</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground">🏥 Sağlık İzleme</h1>
          <p className="text-muted-foreground mt-1">Kanatlı hayvanların sağlık durumu takibi</p>
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
            Sağlık Kaydı
          </button>
        </div>
      </div>

      {/* Özet Kartlar */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <Heart className="w-5 h-5 text-green-600" />
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.healthy}</div>
              <div className="text-xs text-muted-foreground">Sağlıklı</div>
            </div>
          </div>
        </div>
        
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <AlertTriangle className="w-5 h-5 text-red-600" />
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.sick}</div>
              <div className="text-xs text-muted-foreground">Hasta</div>
            </div>
          </div>
        </div>
        
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Activity className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.molting}</div>
              <div className="text-xs text-muted-foreground">Tüy Dökümü</div>
            </div>
          </div>
        </div>
        
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.broody}</div>
              <div className="text-xs text-muted-foreground">Kuluçka</div>
            </div>
          </div>
        </div>
        
        <div className="bg-card rounded-xl border p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <Stethoscope className="w-5 h-5 text-yellow-600" />
            </div>
            <div>
              <div className="text-2xl font-bold">{stats.activeAlerts}</div>
              <div className="text-xs text-muted-foreground">Aktif Uyarı</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Aktif Sağlık Kayıtları */}
        <div className="lg:col-span-2 bg-card rounded-xl border">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Aktif Sağlık Kayıtları
            </h2>
          </div>
          <div className="divide-y">
            {unresolvedRecords.length === 0 ? (
              <div className="p-8 text-center text-muted-foreground">
                <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                <p>Aktif sağlık sorunu bulunmuyor</p>
              </div>
            ) : (
              unresolvedRecords.map((record) => {
                const bird = birds.find(b => b.id === record.poultry_id);
                const statusInfo = healthStatusInfo[record.health_status] || healthStatusInfo.sick;
                const StatusIcon = statusInfo.icon;
                
                return (
                  <div key={record.id} className="p-4 hover:bg-muted/50">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className={`p-2 rounded-lg ${statusInfo.color.split(' ')[0]}`}>
                          <StatusIcon className={`w-5 h-5 ${statusInfo.color.split(' ')[1]}`} />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{bird?.name || bird?.tag_id || record.poultry_id}</span>
                            <span className={`px-2 py-0.5 rounded-full text-xs ${statusInfo.color}`}>
                              {statusInfo.label}
                            </span>
                          </div>
                          <div className="text-sm text-muted-foreground mt-1">
                            {record.diagnosis || 'Teşhis bekleniyor'}
                          </div>
                          {record.symptoms && record.symptoms.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {record.symptoms.map((symptom, i) => (
                                <span key={i} className="px-2 py-0.5 bg-muted rounded-full text-xs">
                                  {symptom}
                                </span>
                              ))}
                            </div>
                          )}
                          {record.treatment && (
                            <div className="flex items-center gap-1 mt-2 text-sm">
                              <Pill className="w-4 h-4 text-muted-foreground" />
                              <span>{record.treatment}</span>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-right text-xs text-muted-foreground">
                        {new Date(record.recorded_at).toLocaleDateString('tr-TR')}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Sağlık Durumuna Göre */}
        <div className="bg-card rounded-xl border">
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Duruma Göre Filtrele</h2>
          </div>
          <div className="p-4 space-y-2">
            {['all', 'healthy', 'sick', 'molting', 'broody', 'stressed'].map((status) => {
              const count = status === 'all' 
                ? birds.length 
                : birds.filter(b => b.health_status === status).length;
              const info = healthStatusInfo[status];
              
              return (
                <button
                  key={status}
                  onClick={() => setFilterStatus(status)}
                  className={`w-full flex items-center justify-between p-3 rounded-lg transition-colors ${
                    filterStatus === status ? 'bg-primary/10 border border-primary' : 'bg-muted/50 hover:bg-muted'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    {status === 'all' ? (
                      <>
                        <Activity className="w-4 h-4" />
                        <span>Tümü</span>
                      </>
                    ) : (
                      <>
                        <span className={`w-3 h-3 rounded-full ${info?.color.split(' ')[0].replace('text', 'bg')}`} />
                        <span>{info?.label}</span>
                      </>
                    )}
                  </span>
                  <span className="text-sm font-medium">{count}</span>
                </button>
              );
            })}
          </div>
          
          {/* Filtrelenmiş Liste */}
          {filterStatus !== 'all' && (
            <div className="p-4 border-t">
              <h3 className="text-sm font-medium mb-3">
                {healthStatusInfo[filterStatus]?.label} Kanatlılar
              </h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {filteredBirds.map((bird) => (
                  <Link
                    key={bird.id}
                    href={`/poultry/${bird.id}`}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-muted"
                  >
                    <span className="text-sm">{bird.name || bird.tag_id}</span>
                    <ChevronRight className="w-4 h-4 text-muted-foreground" />
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Çözümlenen Kayıtlar */}
      <div className="bg-card rounded-xl border">
        <div className="p-4 border-b flex items-center justify-between">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Çözümlenen Kayıtlar
          </h2>
          <span className="text-sm text-muted-foreground">
            {records.filter(r => r.is_resolved).length} kayıt
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Hayvan</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Durum</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Teşhis</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Tedavi</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Kayıt</th>
                <th className="text-left p-4 text-sm font-medium text-muted-foreground">Çözüm</th>
              </tr>
            </thead>
            <tbody>
              {records.filter(r => r.is_resolved).map((record) => {
                const bird = birds.find(b => b.id === record.poultry_id);
                const statusInfo = healthStatusInfo[record.health_status];
                
                return (
                  <tr key={record.id} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="p-4 text-sm">{bird?.name || bird?.tag_id || record.poultry_id}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded-full text-xs ${statusInfo?.color}`}>
                        {statusInfo?.label}
                      </span>
                    </td>
                    <td className="p-4 text-sm">{record.diagnosis || '-'}</td>
                    <td className="p-4 text-sm">{record.treatment || '-'}</td>
                    <td className="p-4 text-sm text-muted-foreground">
                      {new Date(record.recorded_at).toLocaleDateString('tr-TR')}
                    </td>
                    <td className="p-4 text-sm text-muted-foreground">
                      {record.resolved_at ? new Date(record.resolved_at).toLocaleDateString('tr-TR') : '-'}
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
