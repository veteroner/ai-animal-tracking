'use client';

import { useState } from 'react';
import {
  Settings,
  Camera,
  Bell,
  Shield,
  Database,
  Wifi,
  Save,
  RefreshCw,
} from 'lucide-react';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    // Kamera Ayarları
    cameraResolution: '1280x720',
    cameraFps: 30,
    autoDetection: true,
    detectionConfidence: 0.7,
    
    // Bildirim Ayarları
    emailNotifications: true,
    pushNotifications: true,
    smsNotifications: false,
    alertThreshold: 'medium',
    
    // Sistem Ayarları
    language: 'tr',
    timezone: 'Europe/Istanbul',
    autoBackup: true,
    backupFrequency: 'daily',
    
    // Güvenlik
    sessionTimeout: 30,
    twoFactorAuth: false,
  });

  const handleChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = () => {
    // API call to save settings
    alert('Ayarlar kaydedildi!');
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Ayarlar</h1>
        <p className="text-gray-500 mt-1">Sistem yapılandırması ve tercihler</p>
      </div>

      {/* Camera Settings */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-primary-100">
            <Camera className="w-5 h-5 text-primary-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Kamera Ayarları</h2>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Çözünürlük
            </label>
            <select
              value={settings.cameraResolution}
              onChange={(e) => handleChange('cameraResolution', e.target.value)}
              className="input"
            >
              <option value="640x480">640x480</option>
              <option value="1280x720">1280x720 (HD)</option>
              <option value="1920x1080">1920x1080 (Full HD)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Kare Hızı (FPS)
            </label>
            <select
              value={settings.cameraFps}
              onChange={(e) => handleChange('cameraFps', parseInt(e.target.value))}
              className="input"
            >
              <option value={15}>15 FPS</option>
              <option value={30}>30 FPS</option>
              <option value={60}>60 FPS</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tespit Güven Eşiği
            </label>
            <input
              type="range"
              min="0.3"
              max="0.9"
              step="0.1"
              value={settings.detectionConfidence}
              onChange={(e) => handleChange('detectionConfidence', parseFloat(e.target.value))}
              className="w-full"
            />
            <p className="text-sm text-gray-500 mt-1">{(settings.detectionConfidence * 100).toFixed(0)}%</p>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Otomatik Tespit</p>
              <p className="text-sm text-gray-500">Kamera açıldığında AI tespiti başlat</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoDetection}
                onChange={(e) => handleChange('autoDetection', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-warning-100">
            <Bell className="w-5 h-5 text-warning-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Bildirim Ayarları</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-gray-900">E-posta Bildirimleri</p>
              <p className="text-sm text-gray-500">Önemli uyarıları e-posta ile al</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.emailNotifications}
                onChange={(e) => handleChange('emailNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-gray-900">Push Bildirimleri</p>
              <p className="text-sm text-gray-500">Tarayıcı bildirimleri</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.pushNotifications}
                onChange={(e) => handleChange('pushNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-gray-900">SMS Bildirimleri</p>
              <p className="text-sm text-gray-500">Kritik uyarılar için SMS</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.smsNotifications}
                onChange={(e) => handleChange('smsNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Uyarı Eşiği
            </label>
            <select
              value={settings.alertThreshold}
              onChange={(e) => handleChange('alertThreshold', e.target.value)}
              className="input"
            >
              <option value="low">Düşük - Tüm uyarılar</option>
              <option value="medium">Orta - Önemli uyarılar</option>
              <option value="high">Yüksek - Sadece kritik</option>
            </select>
          </div>
        </div>
      </div>

      {/* System Settings */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-gray-100">
            <Database className="w-5 h-5 text-gray-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Sistem Ayarları</h2>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Dil
            </label>
            <select
              value={settings.language}
              onChange={(e) => handleChange('language', e.target.value)}
              className="input"
            >
              <option value="tr">Türkçe</option>
              <option value="en">English</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Saat Dilimi
            </label>
            <select
              value={settings.timezone}
              onChange={(e) => handleChange('timezone', e.target.value)}
              className="input"
            >
              <option value="Europe/Istanbul">İstanbul (UTC+3)</option>
              <option value="Europe/London">Londra (UTC+0)</option>
              <option value="America/New_York">New York (UTC-5)</option>
            </select>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Otomatik Yedekleme</p>
              <p className="text-sm text-gray-500">Veritabanını otomatik yedekle</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoBackup}
                onChange={(e) => handleChange('autoBackup', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Yedekleme Sıklığı
            </label>
            <select
              value={settings.backupFrequency}
              onChange={(e) => handleChange('backupFrequency', e.target.value)}
              className="input"
              disabled={!settings.autoBackup}
            >
              <option value="hourly">Saatlik</option>
              <option value="daily">Günlük</option>
              <option value="weekly">Haftalık</option>
            </select>
          </div>
        </div>
      </div>

      {/* Security Settings */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-danger-100">
            <Shield className="w-5 h-5 text-danger-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Güvenlik</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Oturum Zaman Aşımı (dakika)
            </label>
            <input
              type="number"
              value={settings.sessionTimeout}
              onChange={(e) => handleChange('sessionTimeout', parseInt(e.target.value))}
              className="input"
              min={5}
              max={120}
            />
          </div>
          
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="font-medium text-gray-900">İki Faktörlü Doğrulama</p>
              <p className="text-sm text-gray-500">Ek güvenlik katmanı ekle</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.twoFactorAuth}
                onChange={(e) => handleChange('twoFactorAuth', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end gap-3">
        <button className="btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          Sıfırla
        </button>
        <button onClick={handleSave} className="btn-primary flex items-center gap-2">
          <Save className="w-4 h-4" />
          Kaydet
        </button>
      </div>
    </div>
  );
}
