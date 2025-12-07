'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, EstrusDetection, Pregnancy, Birth, BreedingRecord } from '@/lib/supabase';

export default function ReproductionPage() {
  const [stats, setStats] = useState({
    activeEstrus: 0,
    activePregnancies: 0,
    dueSoon: 0,
    totalBirths: 0,
    pendingBreedings: 0,
  });
  const [recentEstrus, setRecentEstrus] = useState<EstrusDetection[]>([]);
  const [upcomingBirths, setUpcomingBirths] = useState<Pregnancy[]>([]);
  const [recentBirths, setRecentBirths] = useState<Birth[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsData, estrusData, pregnanciesData, birthsData] = await Promise.all([
        api.reproductionStats.getSummary(),
        api.estrus.getActive(),
        api.pregnancies.getDueSoon(14),
        api.births.getAll(),
      ]);

      setStats(statsData);
      setRecentEstrus(estrusData.slice(0, 5));
      setUpcomingBirths(pregnanciesData.slice(0, 5));
      setRecentBirths(birthsData.slice(0, 5));
    } catch (error) {
      console.error('Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'detected': return 'bg-yellow-100 text-yellow-800';
      case 'confirmed': return 'bg-green-100 text-green-800';
      case 'bred': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getBirthTypeColor = (type: string) => {
    switch (type) {
      case 'normal': return 'bg-green-100 text-green-800';
      case 'müdahaleli': return 'bg-yellow-100 text-yellow-800';
      case 'sezaryen': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
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
          <h1 className="text-3xl font-bold text-gray-900">🐄 Üreme Takip Sistemi</h1>
          <p className="text-gray-600">Kızgınlık, gebelik ve doğum takibi</p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Link href="/reproduction/estrus" className="bg-gradient-to-r from-pink-500 to-rose-500 rounded-xl p-6 text-white hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-pink-100">Aktif Kızgınlık</p>
              <p className="text-3xl font-bold">{stats.activeEstrus}</p>
            </div>
            <span className="text-4xl">🔥</span>
          </div>
        </Link>

        <Link href="/reproduction/pregnancies" className="bg-gradient-to-r from-purple-500 to-indigo-500 rounded-xl p-6 text-white hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100">Aktif Gebelik</p>
              <p className="text-3xl font-bold">{stats.activePregnancies}</p>
            </div>
            <span className="text-4xl">🐄✨</span>
          </div>
        </Link>

        <div className="bg-gradient-to-r from-orange-500 to-amber-500 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100">Yakında Doğum</p>
              <p className="text-3xl font-bold">{stats.dueSoon}</p>
            </div>
            <span className="text-4xl">🐮🍼</span>
          </div>
        </div>

        <Link href="/reproduction/births" className="bg-gradient-to-r from-green-500 to-emerald-500 rounded-xl p-6 text-white hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100">Toplam Doğum</p>
              <p className="text-3xl font-bold">{stats.totalBirths}</p>
            </div>
            <span className="text-4xl">🐮🐄</span>
          </div>
        </Link>

        <Link href="/reproduction/breeding" className="bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl p-6 text-white hover:shadow-lg transition-shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100">Bekleyen Sonuç</p>
              <p className="text-3xl font-bold">{stats.pendingBreedings}</p>
            </div>
            <span className="text-4xl">🐂🐄</span>
          </div>
        </Link>
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Link href="/reproduction/estrus" className="bg-white rounded-xl p-4 shadow hover:shadow-md transition-shadow flex items-center space-x-3">
          <span className="text-2xl">🔥</span>
          <div>
            <p className="font-semibold">Kızgınlık Takvimi</p>
            <p className="text-sm text-gray-500">Tespitler ve tohumlama</p>
          </div>
        </Link>
        <Link href="/reproduction/pregnancies" className="bg-white rounded-xl p-4 shadow hover:shadow-md transition-shadow flex items-center space-x-3">
          <span className="text-2xl">🐄</span>
          <div>
            <p className="font-semibold">Gebelik Takibi</p>
            <p className="text-sm text-gray-500">Aktif gebelikler</p>
          </div>
        </Link>
        <Link href="/reproduction/births" className="bg-white rounded-xl p-4 shadow hover:shadow-md transition-shadow flex items-center space-x-3">
          <span className="text-2xl">🐣</span>
          <div>
            <p className="font-semibold">Doğum Kayıtları</p>
            <p className="text-sm text-gray-500">Yavru kaydı</p>
          </div>
        </Link>
        <Link href="/reproduction/breeding" className="bg-white rounded-xl p-4 shadow hover:shadow-md transition-shadow flex items-center space-x-3">
          <span className="text-2xl">🐂</span>
          <div>
            <p className="font-semibold">Çiftleştirme</p>
            <p className="text-sm text-gray-500">Kayıtlar ve performans</p>
          </div>
        </Link>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Estrus */}
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">🔥 Aktif Kızgınlıklar</h2>
            <Link href="/reproduction/estrus" className="text-pink-600 hover:underline text-sm">
              Tümünü Gör →
            </Link>
          </div>
          
          {recentEstrus.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-4xl">🔍</span>
              <p className="mt-2">Aktif kızgınlık tespiti yok</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentEstrus.map((estrus) => (
                <div key={estrus.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">{estrus.animal_id}</p>
                    <p className="text-sm text-gray-500">
                      Güven: {(estrus.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(estrus.status)}`}>
                      {estrus.status === 'detected' ? 'Tespit Edildi' : 
                       estrus.status === 'confirmed' ? 'Onaylandı' : 
                       estrus.status === 'bred' ? 'Tohumlandı' : estrus.status}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(estrus.detection_time).toLocaleDateString('tr-TR')}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming Births */}
        <div className="bg-white rounded-xl shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">⏰ Yaklaşan Doğumlar</h2>
            <Link href="/reproduction/pregnancies" className="text-purple-600 hover:underline text-sm">
              Tümünü Gör →
            </Link>
          </div>
          
          {upcomingBirths.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-4xl">📅</span>
              <p className="mt-2">Yakında doğum beklenen hayvan yok</p>
            </div>
          ) : (
            <div className="space-y-3">
              {upcomingBirths.map((pregnancy) => {
                const daysLeft = Math.ceil((new Date(pregnancy.expected_birth_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24));
                return (
                  <div key={pregnancy.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div>
                      <p className="font-medium">{pregnancy.animal_id}</p>
                      <p className="text-sm text-gray-500">
                        {pregnancy.pregnancy_confirmed ? '✅ Onaylı' : '⏳ Onay Bekliyor'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${daysLeft <= 3 ? 'text-red-600' : daysLeft <= 7 ? 'text-orange-600' : 'text-green-600'}`}>
                        {daysLeft} gün
                      </p>
                      <p className="text-xs text-gray-500">
                        {new Date(pregnancy.expected_birth_date).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Births */}
        <div className="bg-white rounded-xl shadow p-6 lg:col-span-2">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">🐣 Son Doğumlar</h2>
            <Link href="/reproduction/births" className="text-green-600 hover:underline text-sm">
              Tümünü Gör →
            </Link>
          </div>
          
          {recentBirths.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <span className="text-4xl">🐮</span>
              <p className="mt-2">Henüz doğum kaydı yok</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentBirths.map((birth) => (
                <div key={birth.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{birth.mother_id}</p>
                      <p className="text-sm text-gray-500">
                        {new Date(birth.birth_date).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${getBirthTypeColor(birth.birth_type)}`}>
                      {birth.birth_type}
                    </span>
                  </div>
                  <div className="mt-3 flex items-center space-x-4 text-sm">
                    <span>🐣 {birth.offspring_count} yavru</span>
                    {birth.birth_weight && <span>⚖️ {birth.birth_weight} kg</span>}
                    {birth.vet_assisted && <span>👨‍⚕️ Veteriner</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
