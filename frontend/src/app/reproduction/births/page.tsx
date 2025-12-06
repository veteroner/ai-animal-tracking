'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, Birth } from '@/lib/supabase';

export default function BirthsPage() {
  const [births, setBirths] = useState<Birth[]>([]);
  const [filter, setFilter] = useState<'all' | 'normal' | 'müdahaleli' | 'sezaryen'>('all');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newBirth, setNewBirth] = useState({
    mother_id: '',
    birth_date: '',
    offspring_count: 1,
    birth_type: 'normal' as 'normal' | 'müdahaleli' | 'sezaryen',
    vet_assisted: false,
    notes: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await api.births.getAll();
      setBirths(data);
    } catch (error) {
      console.error('Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredBirths = births.filter(b => {
    if (filter === 'all') return true;
    return b.birth_type === filter;
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.births.create({
        mother_id: newBirth.mother_id,
        birth_date: newBirth.birth_date,
        offspring_count: newBirth.offspring_count,
        offspring_ids: [],
        birth_type: newBirth.birth_type,
        vet_assisted: newBirth.vet_assisted,
        notes: newBirth.notes || undefined
      });
      setShowAddModal(false);
      setNewBirth({
        mother_id: '',
        birth_date: '',
        offspring_count: 1,
        birth_type: 'normal',
        vet_assisted: false,
        notes: ''
      });
      await loadData();
    } catch (error) {
      console.error('Kayıt hatası:', error);
    }
  };

  const getBirthTypeBadge = (type: string) => {
    const styles: Record<string, string> = {
      normal: 'bg-green-100 text-green-800 border-green-300',
      müdahaleli: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      sezaryen: 'bg-red-100 text-red-800 border-red-300',
    };
    
    const labels: Record<string, string> = {
      normal: '✅ Normal Doğum',
      müdahaleli: '⚠️ Müdahaleli',
      sezaryen: '🏥 Sezaryen',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm border ${styles[type] || styles.normal}`}>
        {labels[type] || type}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
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
          <h1 className="text-3xl font-bold text-gray-900 mt-2">🐣 Doğum Kayıtları</h1>
          <p className="text-gray-600">Doğum geçmişi ve yeni doğumlar</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <span>+ Yeni Doğum</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Toplam Doğum</div>
          <div className="text-2xl font-bold text-blue-600">{births.length}</div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Normal Doğum</div>
          <div className="text-2xl font-bold text-green-600">
            {births.filter(b => b.birth_type === 'normal').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Müdahaleli</div>
          <div className="text-2xl font-bold text-yellow-600">
            {births.filter(b => b.birth_type === 'müdahaleli').length}
          </div>
        </div>
        <div className="bg-white rounded-xl shadow p-4">
          <div className="text-sm text-gray-500">Sezaryen</div>
          <div className="text-2xl font-bold text-red-600">
            {births.filter(b => b.birth_type === 'sezaryen').length}
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2">
        {(['all', 'normal', 'müdahaleli', 'sezaryen'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === f
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {f === 'all' ? 'Tümü' : 
             f === 'normal' ? 'Normal' :
             f === 'müdahaleli' ? 'Müdahaleli' : 'Sezaryen'}
          </button>
        ))}
      </div>

      {/* Births List */}
      {filteredBirths.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow">
          <span className="text-6xl">🐣</span>
          <h3 className="mt-4 text-xl font-semibold text-gray-700">Doğum kaydı bulunamadı</h3>
          <p className="text-gray-500 mt-2">Henüz bu kategoride kayıt yok</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredBirths.map((birth) => (
            <div key={birth.id} className="bg-white rounded-xl shadow p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Mother Info */}
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-3xl">🐄</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Anne: {birth.mother_id}</h3>
                    <p className="text-gray-500">
                      Doğum: {new Date(birth.birth_date).toLocaleDateString('tr-TR')}
                    </p>
                    {getBirthTypeBadge(birth.birth_type)}
                  </div>
                </div>

                {/* Offspring Info */}
                <div className="flex flex-col md:flex-row gap-4 md:items-center">
                  <div className="text-center px-6 py-3 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">
                      {birth.offspring_count}
                    </div>
                    <div className="text-sm text-gray-500">Yavru</div>
                  </div>
                  
                  {birth.birth_weight && (
                    <div className="text-center px-4">
                      <div className="text-lg font-semibold">{birth.birth_weight} kg</div>
                      <div className="text-sm text-gray-500">Doğum Ağırlığı</div>
                    </div>
                  )}

                  {birth.vet_assisted && (
                    <span className="px-3 py-1 bg-orange-100 text-orange-800 rounded-full text-sm">
                      👨‍⚕️ Veteriner Eşlik Etti
                    </span>
                  )}
                </div>
              </div>

              {/* AI Prediction Info */}
              {birth.ai_predicted_at && (
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full">
                      🤖 AI Tahmini: {new Date(birth.ai_predicted_at).toLocaleDateString('tr-TR')}
                    </span>
                    {birth.prediction_accuracy_hours !== undefined && (
                      <span className="text-gray-500">
                        Doğruluk: {birth.prediction_accuracy_hours < 24 
                          ? `${birth.prediction_accuracy_hours} saat`
                          : `${Math.round(birth.prediction_accuracy_hours / 24)} gün`
                        } fark
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Complications */}
              {birth.complications && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-red-600 font-medium">⚠️ Komplikasyonlar:</p>
                  <p className="text-gray-700">{birth.complications}</p>
                </div>
              )}

              {/* Notes */}
              {birth.notes && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-500">Notlar:</p>
                  <p className="text-gray-700">{birth.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Yeni Doğum Kaydı</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Anne Hayvan ID</label>
                <input
                  type="text"
                  value={newBirth.mother_id}
                  onChange={(e) => setNewBirth({...newBirth, mother_id: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doğum Tarihi</label>
                <input
                  type="date"
                  value={newBirth.birth_date}
                  onChange={(e) => setNewBirth({...newBirth, birth_date: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Yavru Sayısı</label>
                <input
                  type="number"
                  min="1"
                  value={newBirth.offspring_count}
                  onChange={(e) => setNewBirth({...newBirth, offspring_count: parseInt(e.target.value)})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Doğum Tipi</label>
                <select
                  value={newBirth.birth_type}
                  onChange={(e) => setNewBirth({...newBirth, birth_type: e.target.value as typeof newBirth.birth_type})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="normal">Normal Doğum</option>
                  <option value="müdahaleli">Müdahaleli</option>
                  <option value="sezaryen">Sezaryen</option>
                </select>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="vet_assisted"
                  checked={newBirth.vet_assisted}
                  onChange={(e) => setNewBirth({...newBirth, vet_assisted: e.target.checked})}
                  className="rounded border-gray-300"
                />
                <label htmlFor="vet_assisted" className="text-sm text-gray-700">Veteriner eşlik etti</label>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notlar</label>
                <textarea
                  value={newBirth.notes}
                  onChange={(e) => setNewBirth({...newBirth, notes: e.target.value})}
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
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
                  className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
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
