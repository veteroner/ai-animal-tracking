'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, Pregnancy } from '@/lib/supabase';

export default function PregnanciesPage() {
  const [pregnancies, setPregnancies] = useState<Pregnancy[]>([]);
  const [filter, setFilter] = useState<'all' | 'aktif' | 'doğum_yaptı'>('all');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newPregnancy, setNewPregnancy] = useState({
    animal_id: '',
    breeding_date: '',
    expected_birth_date: '',
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await api.pregnancies.getAll();
      setPregnancies(data);
    } catch (error) {
      console.error('Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredPregnancies = pregnancies.filter(p => {
    if (filter === 'all') return true;
    return p.status === filter;
  });

  const calculateDaysUntilDue = (dueDate: string) => {
    const now = new Date();
    const due = new Date(dueDate);
    const diffTime = due.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const calculateProgress = (breedingDate: string, dueDate: string) => {
    const breeding = new Date(breedingDate);
    const due = new Date(dueDate);
    const now = new Date();
    const totalDays = (due.getTime() - breeding.getTime()) / (1000 * 60 * 60 * 24);
    const passedDays = (now.getTime() - breeding.getTime()) / (1000 * 60 * 60 * 24);
    return Math.min(100, Math.max(0, (passedDays / totalDays) * 100));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.pregnancies.create({
        animal_id: newPregnancy.animal_id,
        breeding_date: newPregnancy.breeding_date,
        expected_birth_date: newPregnancy.expected_birth_date,
        status: 'aktif',
        breeding_method: 'doğal',
        pregnancy_confirmed: false,
        notes: newPregnancy.notes || undefined
      });
      setShowAddModal(false);
      setNewPregnancy({ animal_id: '', breeding_date: '', expected_birth_date: '', notes: '' });
      await loadData();
    } catch (error) {
      console.error('Kayıt hatası:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      aktif: 'bg-green-100 text-green-800 border-green-300',
      doğum_yaptı: 'bg-blue-100 text-blue-800 border-blue-300',
      düşük: 'bg-red-100 text-red-800 border-red-300',
      iptal: 'bg-gray-100 text-gray-800 border-gray-300',
    };
    
    const labels: Record<string, string> = {
      aktif: '🐄 Aktif Gebelik',
      doğum_yaptı: '🐮 Doğum Yaptı',
      düşük: '❌ Düşük',
      iptal: '⭕ İptal',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm border ${styles[status] || styles.aktif}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getDueDateUrgency = (daysUntil: number) => {
    if (daysUntil <= 0) return 'bg-red-500';
    if (daysUntil <= 7) return 'bg-orange-500';
    if (daysUntil <= 30) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
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
          <h1 className="text-3xl font-bold text-gray-900 mt-2">🐄 Gebelik Takibi</h1>
          <p className="text-gray-600">Aktif gebelikler ve doğum tahminleri</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center space-x-2"
        >
          <span>+ Yeni Gebelik</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Toplam Gebe</div>
          <div className="text-2xl font-bold text-purple-600">
            {pregnancies.filter(p => p.status === 'aktif').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Bu Hafta Doğum</div>
          <div className="text-2xl font-bold text-red-600">
            {pregnancies.filter(p => {
              if (p.status === 'doğum_yaptı') return false;
              const days = calculateDaysUntilDue(p.expected_birth_date);
              return days >= 0 && days <= 7;
            }).length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Bu Ay Doğum</div>
          <div className="text-2xl font-bold text-orange-600">
            {pregnancies.filter(p => {
              if (p.status === 'doğum_yaptı') return false;
              const days = calculateDaysUntilDue(p.expected_birth_date);
              return days >= 0 && days <= 30;
            }).length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Doğum Yaptı</div>
          <div className="text-2xl font-bold text-blue-600">
            {pregnancies.filter(p => p.status === 'doğum_yaptı').length}
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2">
        {(['all', 'aktif', 'doğum_yaptı'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === f
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {f === 'all' ? 'Tümü' : 
             f === 'aktif' ? 'Aktif Gebelik' : 'Doğum Yaptı'}
          </button>
        ))}
      </div>

      {/* Pregnancies List */}
      {filteredPregnancies.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow">
          <span className="text-6xl">🐄</span>
          <h3 className="mt-4 text-xl font-semibold text-gray-700">Gebelik kaydı bulunamadı</h3>
          <p className="text-gray-500 mt-2">Henüz bu kategoride kayıt yok</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredPregnancies.map((pregnancy) => {
            const daysUntil = calculateDaysUntilDue(pregnancy.expected_birth_date);
            const progress = calculateProgress(pregnancy.breeding_date, pregnancy.expected_birth_date);
            
            return (
              <div key={pregnancy.id} className="bg-white rounded-xl shadow p-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Animal Info */}
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
                      <span className="text-3xl">🐄</span>
                    </div>
                    <div>
                      <h3 className="text-lg font-bold">{pregnancy.animal_id}</h3>
                      <p className="text-gray-500">
                        Tohumlama: {new Date(pregnancy.breeding_date).toLocaleDateString('tr-TR')}
                      </p>
                      {getStatusBadge(pregnancy.status)}
                    </div>
                  </div>

                  {/* Due Date */}
                  <div className="flex flex-col md:flex-row gap-4 md:items-center">
                    {pregnancy.status !== 'doğum_yaptı' && (
                      <div className={`text-center px-6 py-3 rounded-lg text-white ${getDueDateUrgency(daysUntil)}`}>
                        <div className="text-2xl font-bold">
                          {daysUntil <= 0 ? 'BUGÜN!' : `${daysUntil} gün`}
                        </div>
                        <div className="text-sm opacity-90">Tahmini doğum</div>
                      </div>
                    )}
                    
                    <div className="text-center px-4">
                      <div className="text-sm text-gray-500">Beklenen Tarih</div>
                      <div className="font-semibold">
                        {new Date(pregnancy.expected_birth_date).toLocaleDateString('tr-TR')}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                {pregnancy.status !== 'doğum_yaptı' && (
                  <div className="mt-4">
                    <div className="flex justify-between text-sm text-gray-500 mb-1">
                      <span>Gebelik İlerlemesi</span>
                      <span>{progress.toFixed(0)}%</span>
                    </div>
                    <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-purple-600 rounded-full transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>{new Date(pregnancy.breeding_date).toLocaleDateString('tr-TR')}</span>
                      <span>{new Date(pregnancy.expected_birth_date).toLocaleDateString('tr-TR')}</span>
                    </div>
                  </div>
                )}

                {/* Pregnancy Confirmation Status */}
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center space-x-4">
                    <span className={`px-3 py-1 rounded-full text-sm ${pregnancy.pregnancy_confirmed ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {pregnancy.pregnancy_confirmed ? '✅ Gebelik Doğrulandı' : '⏳ Doğrulama Bekliyor'}
                    </span>
                    {pregnancy.confirmation_method && (
                      <span className="text-sm text-gray-500">
                        ({pregnancy.confirmation_method})
                      </span>
                    )}
                  </div>
                </div>

                {/* Notes */}
                {pregnancy.notes && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm text-gray-500">Notlar:</p>
                    <p className="text-gray-700">{pregnancy.notes}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Yeni Gebelik Kaydı</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Hayvan ID</label>
                <input
                  type="text"
                  value={newPregnancy.animal_id}
                  onChange={(e) => setNewPregnancy({...newPregnancy, animal_id: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tohumlama Tarihi</label>
                <input
                  type="date"
                  value={newPregnancy.breeding_date}
                  onChange={(e) => setNewPregnancy({...newPregnancy, breeding_date: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tahmini Doğum Tarihi</label>
                <input
                  type="date"
                  value={newPregnancy.expected_birth_date}
                  onChange={(e) => setNewPregnancy({...newPregnancy, expected_birth_date: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notlar</label>
                <textarea
                  value={newPregnancy.notes}
                  onChange={(e) => setNewPregnancy({...newPregnancy, notes: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500"
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
                  className="flex-1 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
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
