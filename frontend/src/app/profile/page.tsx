'use client';

import { useState } from 'react';
import {
  User,
  Mail,
  Phone,
  MapPin,
  Building,
  Camera,
  Save,
  Key,
  Shield,
  Bell,
} from 'lucide-react';

interface UserProfile {
  name: string;
  email: string;
  phone: string;
  role: string;
  farm_name: string;
  location: string;
  avatar?: string;
  created_at: string;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile>({
    name: 'Admin Kullanıcı',
    email: 'admin@ciftlik.com',
    phone: '+90 555 123 4567',
    role: 'Çiftlik Yöneticisi',
    farm_name: 'Örnek Çiftlik',
    location: 'Ankara, Türkiye',
    created_at: '2024-01-01',
  });

  const [isEditing, setIsEditing] = useState(false);
  const [editedProfile, setEditedProfile] = useState(profile);
  const [showPasswordModal, setShowPasswordModal] = useState(false);

  const handleSave = () => {
    setProfile(editedProfile);
    setIsEditing(false);
    alert('Profil güncellendi!');
  };

  const handleCancel = () => {
    setEditedProfile(profile);
    setIsEditing(false);
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profil</h1>
        <p className="text-gray-500 mt-1">Kişisel bilgilerinizi yönetin</p>
      </div>

      {/* Profile Card */}
      <div className="card">
        <div className="flex flex-col sm:flex-row items-start gap-6">
          {/* Avatar */}
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-primary-100 flex items-center justify-center">
              {profile.avatar ? (
                <img src={profile.avatar} alt="Avatar" className="w-full h-full rounded-full object-cover" />
              ) : (
                <User className="w-12 h-12 text-primary-600" />
              )}
            </div>
            <button className="absolute bottom-0 right-0 p-2 bg-white rounded-full shadow-lg border border-gray-200 hover:bg-gray-50">
              <Camera className="w-4 h-4 text-gray-600" />
            </button>
          </div>

          {/* Info */}
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-gray-900">{profile.name}</h2>
            <p className="text-gray-500">{profile.role}</p>
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <Building className="w-4 h-4" />
                {profile.farm_name}
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4" />
                {profile.location}
              </div>
            </div>
          </div>

          {/* Edit Button */}
          <div>
            {!isEditing ? (
              <button
                onClick={() => setIsEditing(true)}
                className="btn-primary"
              >
                Düzenle
              </button>
            ) : (
              <div className="flex gap-2">
                <button onClick={handleCancel} className="btn-secondary">
                  İptal
                </button>
                <button onClick={handleSave} className="btn-primary flex items-center gap-2">
                  <Save className="w-4 h-4" />
                  Kaydet
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Personal Information */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Kişisel Bilgiler</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ad Soyad
            </label>
            {isEditing ? (
              <input
                type="text"
                value={editedProfile.name}
                onChange={(e) => setEditedProfile({ ...editedProfile, name: e.target.value })}
                className="input"
              />
            ) : (
              <p className="text-gray-900">{profile.name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              E-posta
            </label>
            {isEditing ? (
              <input
                type="email"
                value={editedProfile.email}
                onChange={(e) => setEditedProfile({ ...editedProfile, email: e.target.value })}
                className="input"
              />
            ) : (
              <p className="text-gray-900">{profile.email}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Telefon
            </label>
            {isEditing ? (
              <input
                type="tel"
                value={editedProfile.phone}
                onChange={(e) => setEditedProfile({ ...editedProfile, phone: e.target.value })}
                className="input"
              />
            ) : (
              <p className="text-gray-900">{profile.phone}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rol
            </label>
            <p className="text-gray-900">{profile.role}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Çiftlik Adı
            </label>
            {isEditing ? (
              <input
                type="text"
                value={editedProfile.farm_name}
                onChange={(e) => setEditedProfile({ ...editedProfile, farm_name: e.target.value })}
                className="input"
              />
            ) : (
              <p className="text-gray-900">{profile.farm_name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Konum
            </label>
            {isEditing ? (
              <input
                type="text"
                value={editedProfile.location}
                onChange={(e) => setEditedProfile({ ...editedProfile, location: e.target.value })}
                className="input"
              />
            ) : (
              <p className="text-gray-900">{profile.location}</p>
            )}
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Güvenlik</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary-100">
                <Key className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Şifre</p>
                <p className="text-sm text-gray-500">Son değişiklik: 30 gün önce</p>
              </div>
            </div>
            <button
              onClick={() => setShowPasswordModal(true)}
              className="btn-secondary"
            >
              Değiştir
            </button>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success-100">
                <Shield className="w-5 h-5 text-success-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">İki Faktörlü Doğrulama</p>
                <p className="text-sm text-gray-500">Hesabınızı daha güvenli hale getirin</p>
              </div>
            </div>
            <button className="btn-secondary">
              Etkinleştir
            </button>
          </div>
        </div>
      </div>

      {/* Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-6">Son Aktiviteler</h3>
        
        <div className="space-y-4">
          <div className="flex items-center gap-4 text-sm">
            <div className="w-2 h-2 rounded-full bg-success-500" />
            <span className="text-gray-500">Bugün 14:00</span>
            <span className="text-gray-900">Sisteme giriş yapıldı</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="w-2 h-2 rounded-full bg-primary-500" />
            <span className="text-gray-500">Bugün 10:30</span>
            <span className="text-gray-900">Yeni hayvan eklendi (TR-007)</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="w-2 h-2 rounded-full bg-warning-500" />
            <span className="text-gray-500">Dün 16:45</span>
            <span className="text-gray-900">Sağlık kaydı güncellendi</span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="w-2 h-2 rounded-full bg-primary-500" />
            <span className="text-gray-500">Dün 09:00</span>
            <span className="text-gray-900">Sisteme giriş yapıldı</span>
          </div>
        </div>
      </div>

      {/* Account Info */}
      <div className="card bg-gray-50">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500">Hesap oluşturulma tarihi</p>
            <p className="font-medium text-gray-900">
              {new Date(profile.created_at).toLocaleDateString('tr-TR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>
          <button className="text-danger-600 hover:text-danger-700 text-sm font-medium">
            Hesabı Sil
          </button>
        </div>
      </div>

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Şifre Değiştir</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mevcut Şifre
                </label>
                <input type="password" className="input" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Yeni Şifre
                </label>
                <input type="password" className="input" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Yeni Şifre (Tekrar)
                </label>
                <input type="password" className="input" />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowPasswordModal(false)}
                className="flex-1 btn-secondary"
              >
                İptal
              </button>
              <button
                onClick={() => {
                  setShowPasswordModal(false);
                  alert('Şifre değiştirildi!');
                }}
                className="flex-1 btn-primary"
              >
                Kaydet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
