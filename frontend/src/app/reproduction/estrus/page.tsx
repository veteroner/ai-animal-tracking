'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, EstrusDetection } from '@/lib/supabase';

export default function EstrusPage() {
  const [estrusDetections, setEstrusDetections] = useState<EstrusDetection[]>([]);
  const [filter, setFilter] = useState<'all' | 'detected' | 'confirmed' | 'bred'>('all');
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await api.estrus.getAll();
      setEstrusDetections(data);
    } catch (error) {
      console.error('Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDetections = estrusDetections.filter(e => {
    if (filter === 'all') return true;
    return e.status === filter;
  });

  const handleConfirm = async (id: string) => {
    try {
      await api.estrus.confirm(id);
      await loadData();
    } catch (error) {
      console.error('Onaylama hatası:', error);
    }
  };

  const handleMarkBred = async (id: string) => {
    try {
      await api.estrus.markBred(id);
      await loadData();
    } catch (error) {
      console.error('İşaretleme hatası:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      detected: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      confirmed: 'bg-green-100 text-green-800 border-green-300',
      bred: 'bg-blue-100 text-blue-800 border-blue-300',
      missed: 'bg-gray-100 text-gray-800 border-gray-300',
      false_positive: 'bg-red-100 text-red-800 border-red-300',
    };
    
    const labels: Record<string, string> = {
      detected: '🔍 Tespit Edildi',
      confirmed: '✅ Onaylandı',
      bred: '🐂 Tohumlandı',
      missed: '❌ Kaçırıldı',
      false_positive: '⚠️ Yanlış Pozitif',
    };

    return (
      <span className={`px-3 py-1 rounded-full text-sm border ${styles[status] || styles.detected}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getBehaviorIcon = (behavior: string) => {
    const icons: Record<string, string> = {
      mounting: '🔝',
      standing_heat: '🧍',
      activity_increase: '🏃',
      restlessness: '😰',
      tail_raising: '📍',
      social_interaction: '👥',
    };
    return icons[behavior] || '•';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600"></div>
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
          <h1 className="text-3xl font-bold text-gray-900 mt-2">🔥 Kızgınlık Takibi</h1>
          <p className="text-gray-600">Kızgınlık tespitleri ve tohumlama zamanlaması</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="bg-pink-600 text-white px-4 py-2 rounded-lg hover:bg-pink-700 flex items-center space-x-2"
        >
          <span>+ Yeni Tespit</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-2">
        {(['all', 'detected', 'confirmed', 'bred'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-lg transition-colors ${
              filter === f
                ? 'bg-pink-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {f === 'all' ? 'Tümü' : 
             f === 'detected' ? 'Tespit Edildi' :
             f === 'confirmed' ? 'Onaylı' : 'Tohumlandı'}
            <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-sm">
              {f === 'all' ? estrusDetections.length : estrusDetections.filter(e => e.status === f).length}
            </span>
          </button>
        ))}
      </div>

      {/* Detections List */}
      {filteredDetections.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl shadow">
          <span className="text-6xl">🔍</span>
          <h3 className="mt-4 text-xl font-semibold text-gray-700">Kızgınlık tespiti bulunamadı</h3>
          <p className="text-gray-500 mt-2">Henüz bu kategoride tespit yok</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredDetections.map((estrus) => (
            <div key={estrus.id} className="bg-white rounded-xl shadow p-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                {/* Animal Info */}
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center">
                    <span className="text-3xl">🐄</span>
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">{estrus.animal_id}</h3>
                    <p className="text-gray-500">
                      Tespit: {new Date(estrus.detection_time).toLocaleString('tr-TR')}
                    </p>
                    {getStatusBadge(estrus.status)}
                  </div>
                </div>

                {/* Confidence & Breeding Window */}
                <div className="flex flex-col md:flex-row gap-4 md:items-center">
                  <div className="text-center px-4">
                    <div className="text-2xl font-bold text-pink-600">
                      %{(estrus.confidence * 100).toFixed(0)}
                    </div>
                    <div className="text-sm text-gray-500">Güven</div>
                  </div>
                  
                  {estrus.optimal_breeding_start && (
                    <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-2">
                      <div className="text-sm text-green-600 font-medium">Optimal Tohumlama</div>
                      <div className="text-sm">
                        {new Date(estrus.optimal_breeding_start).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                        {' - '}
                        {new Date(estrus.optimal_breeding_end).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  {estrus.status === 'detected' && (
                    <button
                      onClick={() => handleConfirm(estrus.id)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      ✓ Onayla
                    </button>
                  )}
                  {(estrus.status === 'detected' || estrus.status === 'confirmed') && (
                    <button
                      onClick={() => handleMarkBred(estrus.id)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                    >
                      🐂 Tohumlandı
                    </button>
                  )}
                </div>
              </div>

              {/* Behaviors */}
              {estrus.behaviors && Object.keys(estrus.behaviors).length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-500 mb-2">Tespit Edilen Davranışlar:</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(estrus.behaviors).map(([behavior, score]) => (
                      <span
                        key={behavior}
                        className="px-3 py-1 bg-gray-100 rounded-full text-sm flex items-center space-x-1"
                      >
                        <span>{getBehaviorIcon(behavior)}</span>
                        <span>{behavior.replace(/_/g, ' ')}</span>
                        {typeof score === 'number' && score > 0 && (
                          <span className="text-pink-600 font-medium">({(score * 100).toFixed(0)}%)</span>
                        )}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              {estrus.notes && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm text-gray-500">Notlar:</p>
                  <p className="text-gray-700">{estrus.notes}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add Modal (simplified) */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-bold mb-4">Yeni Kızgınlık Tespiti</h2>
            <p className="text-gray-500 mb-4">
              Bu özellik AI tarafından otomatik tespit edilir. Manuel kayıt eklemek için lütfen hayvan sayfasından girin.
            </p>
            <button
              onClick={() => setShowAddModal(false)}
              className="w-full py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
            >
              Kapat
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
