'use client';

import { Bell, Search, User, LogOut } from 'lucide-react';
import { useState } from 'react';

export default function Header() {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Hayvan ara (küpe no, isim)..."
            className="w-full pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <Bell className="w-5 h-5 text-gray-600" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full" />
          </button>
          
          {showNotifications && (
            <div className="absolute right-0 top-12 w-80 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
              <div className="px-4 py-2 border-b border-gray-100">
                <h3 className="font-semibold text-gray-900">Bildirimler</h3>
              </div>
              <div className="max-h-80 overflow-y-auto">
                <NotificationItem
                  title="Sağlık Uyarısı"
                  message="TR-001 numaralı hayvanda anormal davranış tespit edildi"
                  time="5 dk önce"
                  type="warning"
                />
                <NotificationItem
                  title="Bölge İhlali"
                  message="3 hayvan tehlikeli bölgeye girdi"
                  time="15 dk önce"
                  type="danger"
                />
                <NotificationItem
                  title="Günlük Rapor"
                  message="Günlük sağlık raporu hazır"
                  time="1 saat önce"
                  type="info"
                />
              </div>
              <div className="px-4 py-2 border-t border-gray-100">
                <a href="/notifications" className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                  Tümünü gör
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative">
          <button
            onClick={() => setShowProfile(!showProfile)}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <User className="w-5 h-5 text-primary-600" />
            </div>
            <div className="hidden sm:block text-left">
              <p className="text-sm font-medium text-gray-900">Admin</p>
              <p className="text-xs text-gray-500">Çiftlik Yöneticisi</p>
            </div>
          </button>

          {showProfile && (
            <div className="absolute right-0 top-12 w-48 bg-white rounded-xl shadow-lg border border-gray-200 py-2 z-50">
              <a
                href="/profile"
                className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <User className="w-4 h-4" />
                Profil
              </a>
              <button
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-danger-600 hover:bg-danger-50"
              >
                <LogOut className="w-4 h-4" />
                Çıkış Yap
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

interface NotificationItemProps {
  title: string;
  message: string;
  time: string;
  type: 'info' | 'warning' | 'danger';
}

function NotificationItem({ title, message, time, type }: NotificationItemProps) {
  const colors = {
    info: 'bg-primary-100 text-primary-600',
    warning: 'bg-warning-100 text-warning-600',
    danger: 'bg-danger-100 text-danger-600',
  };

  return (
    <div className="px-4 py-3 hover:bg-gray-50 cursor-pointer">
      <div className="flex gap-3">
        <div className={`w-2 h-2 rounded-full mt-2 ${colors[type].split(' ')[0]}`} />
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-900">{title}</p>
          <p className="text-xs text-gray-500 mt-0.5">{message}</p>
          <p className="text-xs text-gray-400 mt-1">{time}</p>
        </div>
      </div>
    </div>
  );
}
