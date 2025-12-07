'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, BreedingRecord } from '@/lib/supabase';

export default function BreedingPage() {
  const [breedings, setBreedings] = useState<BreedingRecord[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'successful' | 'failed'>('all');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newBreeding, setNewBreeding] = useState({
    female_id: '',
    male_id: '',
    breeding_date: '',
    breeding_method: 'doğal' as 'doğal' | 'suni_tohumlama' | 'embriyo_transferi',
    technician_name: '',
    semen_batch: '',
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await api.breeding.getAll();
      setBreedings(data);
    } catch (error) {
      console.error('Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredBreedings = breedings.filter(b => {
    if (filter === 'all') return true;
    if (filter === 'pending') return b.success === undefined || b.success === null;
    if (filter === 'successful') return b.success === true;
    if (filter === 'failed') return b.success === false;
    return true;
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.breeding.create({
        female_id: newBreeding.female_id,
        male_id: newBreeding.male_id || undefined,
        breeding_date: newBreeding.breeding_date,
        breeding_method: newBreeding.breeding_method,
        technician_name: newBreeding.technician_name || undefined,
        semen_batch: newBreeding.semen_batch || undefined,
        notes: newBreeding.notes || undefined
      });
      setShowAddModal(false);
      setNewBreeding({
        female_id: '',
        male_id: '',
        breeding_date: '',
        breeding_method: 'doğal',
        technician_name: '',
        semen_batch: '',
        notes: ''
      });
      await loadData();
    } catch (error) {
      console.error('Kayıt hatası:', error);
    }
  };

  const getMethodBadge = (method: string) => {
    const styles: Record<string, string> = {
      doğal: 'bg-green-100 text-green-800 border-green-300',
      suni_tohumlama: 'bg-blue-100 text-blue-800 border-blue-300',
      embriyo_transferi: 'bg-purple-100 text-purple-800 border-purple-300',
    };
    
    const labels: Record<string, string> = {
      doğal: '🐂 Doğal Aşım',
      suni_tohumlama: '💉 Suni Tohumlama',
      embriyo_transferi: '🧬 Embriyo Transferi',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm border ${styles[method] || styles.doğal}`}>
        {labels[method] || method}
      </span>
    );
  };

  const getSuccessBadge = (success: boolean | undefined | null) => {
    if (success === true) {
      return <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">✅ Başarılı</span>;
    }
    if (success === false) {
      return <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm">❌ Başarısız</span>;
    }
    return <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">⏳ Beklemede</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center space-x-2">
            <Link href="/reproduction" className="text-gray-500 hover:text-gray-700">
              ← Üreme
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mt-2">🐂 Çiftleştirme Kayıtları</h1>
          <p className="text-gray-600">Tohumlama ve çiftleştirme takibi</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 flex items-center space-x-2"
        >
          <span>+ Yeni Çiftleştirme</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Toplam Kayıt</div>
          <div className="text-2xl font-bold text-indigo-600">{breedings.length}</div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Beklemede</div>
          <div className="text-2xl font-bold text-yellow-600">
            {breedings.filter(b => b.success === undefined || b.success === null).length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Başarılı</div>
          <div className="text-2xl font-bold text-green-600">
            {breedings.filter(b => b.success === true).length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Başarı Oranı</div>
          <div className="text-2xl font-bold text-blue-600">
            {breedings.filter(b => b.success !== undefined && b.success !== null).length > 0
              ? `%${Math.round(
                  (breedings.filter(b => b.success === true).length /
                    breedings.filter(b => b.success !== undefined && b.success !== null).length) * 100
                )}`
              : '-'}
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2">
        {(['all', 'pending', 'successful', 'failed'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === f
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {f === 'all' ? 'Tümü' : 
             f === 'pending' ? 'Beklemede' :
             f === 'successful' ? 'Başarılı' : 'Başarısız'}
          </button>
        ))}
      </div>

      {/* Breedings List */}
      {filteredBreedings.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow">
          <span className="text-6xl">🐂</span>
          <h3 className="mt-4 text-xl font-semibold text-gray-700">Çiftleştirme kaydı bulunamadı</h3>
          <p className="text-gray-500 mt-2">Henüz bu kategoride kayıt yok</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredBreedings.map((breeding) => (
            <div key={breeding.id} className="bg-white rounded-xl shadow p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Animal Info */}
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
                    <span className="text-3xl">🐂</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Dişi: {breeding.female_id}</h3>
                    {breeding.male_id && (
                      <p className="text-gray-600">Erkek: {breeding.male_id}</p>
                    )}
                    <p className="text-gray-500">
                      Tarih: {new Date(breeding.breeding_date).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>

                {/* Method & Status */}
                <div className="flex flex-col md:flex-row gap-4 md:items-center">
                  {getMethodBadge(breeding.breeding_method)}
                  {getSuccessBadge(breeding.success)}
                </div>
              </div>

              {/* Additional Info */}
              <div className="mt-4 pt-4 border-t grid grid-cols-2 md:grid-cols-4 gap-4">
                {breeding.technician_name && (
                  <div>
                    <p className="text-sm text-gray-500">Teknisyen</p>
                    <p className="font-medium">{breeding.technician_name}</p>
                  </div>
                )}
                {breeding.semen_batch && (
                  <div>
                    <p className="text-sm text-gray-500">Semen Batch</p>
                    <p className="font-medium">{breeding.semen_batch}</p>
                  </div>
                )}
                {breeding.estrus_detection_id && (
                  <div>
                    <p className="text-sm text-gray-500">Kızgınlık Tespiti</p>
                    <p className="font-medium text-pink-600">Bağlı</p>
                  </div>
                )}
                {breeding.pregnancy_id && (
                  <div>
                    <p className="text-sm text-gray-500">Gebelik</p>
                    <p className="font-medium text-purple-600">Oluşturuldu</p>
                  </div>
                )}
              </div>

              {/* Notes */}
              {breeding.notes && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-500">Notlar:</p>
                  <p className="text-gray-700">{breeding.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Yeni Çiftleştirme Kaydı</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Dişi Hayvan ID *</label>
                <input
                  type="text"
                  value={newBreeding.female_id}
                  onChange={(e) => setNewBreeding({...newBreeding, female_id: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Erkek Hayvan ID</label>
                <input
                  type="text"
                  value={newBreeding.male_id}
                  onChange={(e) => setNewBreeding({...newBreeding, male_id: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  placeholder="Suni tohumlama için boş bırakın"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Çiftleştirme Tarihi *</label>
                <input
                  type="date"
                  value={newBreeding.breeding_date}
                  onChange={(e) => setNewBreeding({...newBreeding, breeding_date: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Çiftleştirme Yöntemi *</label>
                <select
                  value={newBreeding.breeding_method}
                  onChange={(e) => setNewBreeding({...newBreeding, breeding_method: e.target.value as typeof newBreeding.breeding_method})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="doğal">Doğal Aşım</option>
                  <option value="suni_tohumlama">Suni Tohumlama</option>
                  <option value="embriyo_transferi">Embriyo Transferi</option>
                </select>
              </div>
              {newBreeding.breeding_method === 'suni_tohumlama' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Teknisyen Adı</label>
                    <input
                      type="text"
                      value={newBreeding.technician_name}
                      onChange={(e) => setNewBreeding({...newBreeding, technician_name: e.target.value})}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Semen Batch No</label>
                    <input
                      type="text"
                      value={newBreeding.semen_batch}
                      onChange={(e) => setNewBreeding({...newBreeding, semen_batch: e.target.value})}
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notlar</label>
                <textarea
                  value={newBreeding.notes}
                  onChange={(e) => setNewBreeding({...newBreeding, notes: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500"
                  rows={3}
                />
              </div>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
                >
                  Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
