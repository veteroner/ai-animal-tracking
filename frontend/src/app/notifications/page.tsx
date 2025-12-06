'use client';

import { useState, useEffect } from 'react';
import {
  Bell,
  Check,
  Trash2,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Filter,
  Loader2,
} from 'lucide-react';
import { api, isSupabaseConfigured, Alert as SupabaseAlert } from '@/lib/supabase';

interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success' | 'error';
  is_read: boolean;
  created_at: string;
}

const typeConfig = {
  info: { icon: Info, bg: 'bg-primary-100', text: 'text-primary-600', border: 'border-primary-200' },
  warning: { icon: AlertTriangle, bg: 'bg-warning-100', text: 'text-warning-600', border: 'border-warning-200' },
  success: { icon: CheckCircle, bg: 'bg-success-100', text: 'text-success-600', border: 'border-success-200' },
  error: { icon: XCircle, bg: 'bg-danger-100', text: 'text-danger-600', border: 'border-danger-200' },
};

// Map alert type to notification type
const mapAlertType = (alertType: string, severity: string): 'info' | 'warning' | 'success' | 'error' => {
  if (severity === 'kritik' || severity === 'yüksek') return 'error';
  if (severity === 'orta' || alertType === 'sağlık') return 'warning';
  if (alertType === 'sistem') return 'info';
  return 'info';
};

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!isSupabaseConfigured()) {
        // Demo data when Supabase is not configured
        setNotifications([
          { id: 1, title: 'Sağlık Uyarısı', message: 'TR-001 numaralı hayvanda anormal davranış tespit edildi', type: 'warning', is_read: false, created_at: '2024-12-02T10:30:00' },
          { id: 2, title: 'Bölge İhlali', message: '3 hayvan tehlikeli bölgeye girdi', type: 'error', is_read: false, created_at: '2024-12-02T10:15:00' },
          { id: 3, title: 'Günlük Rapor', message: 'Günlük sağlık raporu hazır', type: 'info', is_read: true, created_at: '2024-12-02T09:00:00' },
          { id: 4, title: 'Aşı Hatırlatması', message: '5 hayvanın aşı zamanı geldi', type: 'warning', is_read: false, created_at: '2024-12-01T14:00:00' },
          { id: 5, title: 'Yeni Hayvan', message: 'TR-007 numaralı hayvan sisteme eklendi', type: 'success', is_read: true, created_at: '2024-12-01T11:00:00' },
          { id: 6, title: 'Sistem Güncellemesi', message: 'AI modeli başarıyla güncellendi', type: 'success', is_read: true, created_at: '2024-11-30T16:00:00' },
        ]);
        return;
      }

      const alerts = await api.alerts.getAll();

      // Map Supabase alerts to notifications
      const mappedNotifications: Notification[] = alerts.map((a: SupabaseAlert, index: number) => ({
        id: parseInt(a.id) || index + 1,
        title: a.title,
        message: a.message,
        type: mapAlertType(a.type, a.severity),
        is_read: a.is_read,
        created_at: a.created_at,
      }));

      setNotifications(mappedNotifications.length > 0 ? mappedNotifications : [
        { id: 1, title: 'Hoş Geldiniz', message: 'Sisteme başarıyla bağlandınız', type: 'success', is_read: false, created_at: new Date().toISOString() },
      ]);
    } catch (err) {
      console.error('Error loading notifications:', err);
      setError('Bildirimler yüklenemedi');
      setNotifications([
        { id: 1, title: 'Bağlantı Hatası', message: 'Bildirimler yüklenirken bir hata oluştu', type: 'error', is_read: false, created_at: new Date().toISOString() },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const filteredNotifications = filter === 'unread' 
    ? notifications.filter(n => !n.is_read)
    : notifications;

  const markAsRead = async (id: number) => {
    setNotifications(notifications.map(n => 
      n.id === id ? { ...n, is_read: true } : n
    ));
    
    if (isSupabaseConfigured()) {
      try {
        await api.alerts.markAsRead(String(id));
      } catch (err) {
        console.error('Error marking as read:', err);
      }
    }
  };

  const markAllAsRead = async () => {
    setNotifications(notifications.map(n => ({ ...n, is_read: true })));
    
    if (isSupabaseConfigured()) {
      try {
        await api.alerts.markAllAsRead();
      } catch (err) {
        console.error('Error marking all as read:', err);
      }
    }
  };

  const deleteNotification = (id: number) => {
    setNotifications(notifications.filter(n => n.id !== id));
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Bildirimler</h1>
          <p className="text-gray-500 mt-1">{unreadCount} okunmamış bildirim</p>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={markAllAsRead}
            className="btn-secondary flex items-center gap-2"
            disabled={unreadCount === 0}
          >
            <Check className="w-4 h-4" />
            Tümünü Okundu İşaretle
          </button>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'all' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Tümü ({notifications.length})
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter === 'unread' ? 'bg-primary-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          Okunmamış ({unreadCount})
        </button>
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {filteredNotifications.length === 0 ? (
          <div className="card text-center py-12">
            <Bell className="w-12 h-12 mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500">Bildirim bulunmuyor</p>
          </div>
        ) : (
          filteredNotifications.map((notification) => {
            const config = typeConfig[notification.type];
            const Icon = config.icon;
            
            return (
              <div
                key={notification.id}
                className={`card flex items-start gap-4 ${!notification.is_read ? 'border-l-4 ' + config.border : ''}`}
              >
                <div className={`p-3 rounded-xl ${config.bg}`}>
                  <Icon className={`w-5 h-5 ${config.text}`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className={`font-medium ${!notification.is_read ? 'text-gray-900' : 'text-gray-600'}`}>
                        {notification.title}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">{notification.message}</p>
                      <p className="text-xs text-gray-400 mt-2">
                        {new Date(notification.created_at).toLocaleString('tr-TR')}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-1">
                      {!notification.is_read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="p-2 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                          title="Okundu işaretle"
                        >
                          <Check className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="p-2 rounded-lg hover:bg-danger-50 text-gray-400 hover:text-danger-600"
                        title="Sil"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
