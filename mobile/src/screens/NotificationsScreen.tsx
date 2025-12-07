import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { API_BASE_URL } from '../config/api';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: string;
  timestamp: string;
  read: boolean;
  priority: string;
  data?: any;
}

const typeConfig: Record<string, { icon: string; color: string; label: string }> = {
  alert: { icon: '🚨', color: '#ef4444', label: 'Uyarı' },
  health: { icon: '🏥', color: '#22c55e', label: 'Sağlık' },
  feeding: { icon: '🌾', color: '#f59e0b', label: 'Yemleme' },
  reproduction: { icon: '🐄', color: '#8b5cf6', label: 'Üreme' },
  system: { icon: '⚙️', color: '#3b82f6', label: 'Sistem' },
  info: { icon: 'ℹ️', color: '#06b6d4', label: 'Bilgi' },
};

const demoNotifications: Notification[] = [
  { id: '1', title: 'Acil Sağlık Uyarısı', message: 'TR-005 kodlu hayvan için acil veteriner müdahalesi gerekiyor', type: 'alert', timestamp: '2024-12-02T10:30:00', read: false, priority: 'high' },
  { id: '2', title: 'Kızgınlık Tespiti', message: 'TR-012 kodlu inek kızgınlık belirtileri gösteriyor', type: 'reproduction', timestamp: '2024-12-02T09:15:00', read: false, priority: 'medium' },
  { id: '3', title: 'Yemleme Hatırlatması', message: 'Ahır 2 için öğle yemlemesi zamanı', type: 'feeding', timestamp: '2024-12-02T12:00:00', read: true, priority: 'low' },
  { id: '4', title: 'Aşı Zamanı', message: '5 hayvan için şap aşısı zamanı geldi', type: 'health', timestamp: '2024-12-01T14:00:00', read: true, priority: 'medium' },
  { id: '5', title: 'Sistem Güncellemesi', message: 'Yeni özellikler eklendi', type: 'system', timestamp: '2024-12-01T08:00:00', read: true, priority: 'low' },
  { id: '6', title: 'Doğum Yaklaşıyor', message: 'TR-008 için tahmini doğum tarihi 3 gün içinde', type: 'reproduction', timestamp: '2024-11-30T16:00:00', read: true, priority: 'high' },
];

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    loadNotifications();
  }, []);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/notifications`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data);
      } else {
        setNotifications(demoNotifications);
      }
    } catch (error) {
      setNotifications(demoNotifications);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadNotifications();
    setRefreshing(false);
  };

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const getTypeConfig = (type: string) => {
    return typeConfig[type] || typeConfig.info;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 60) return `${minutes} dakika önce`;
    if (hours < 24) return `${hours} saat önce`;
    if (days < 7) return `${days} gün önce`;
    return date.toLocaleDateString('tr-TR');
  };

  const filteredNotifications = filter === 'all' 
    ? notifications 
    : filter === 'unread'
    ? notifications.filter(n => !n.read)
    : notifications.filter(n => n.type === filter);

  const unreadCount = notifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Bildirimler yükleniyor...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Üst Bar */}
      <View style={styles.header}>
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle}>Bildirimler</Text>
          {unreadCount > 0 && (
            <View style={styles.badge}>
              <Text style={styles.badgeText}>{unreadCount}</Text>
            </View>
          )}
        </View>
        <View style={styles.headerActions}>
          <TouchableOpacity style={styles.headerButton} onPress={markAllAsRead}>
            <Text style={styles.headerButtonText}>Tümünü Oku</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton} onPress={clearAll}>
            <Text style={styles.headerButtonText}>Temizle</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Filtreler */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterContainer}>
        {[
          { key: 'all', label: 'Tümü' },
          { key: 'unread', label: 'Okunmamış' },
          { key: 'alert', label: '🚨 Uyarı' },
          { key: 'health', label: '🏥 Sağlık' },
          { key: 'reproduction', label: '🐄 Üreme' },
          { key: 'feeding', label: '🌾 Yemleme' },
        ].map(f => (
          <TouchableOpacity
            key={f.key}
            style={[styles.filterButton, filter === f.key && styles.filterButtonActive]}
            onPress={() => setFilter(f.key)}
          >
            <Text style={[styles.filterButtonText, filter === f.key && styles.filterButtonTextActive]}>
              {f.label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Bildirim Listesi */}
      <ScrollView 
        style={styles.listContainer}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {filteredNotifications.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>📭</Text>
            <Text style={styles.emptyText}>Bildirim bulunamadı</Text>
          </View>
        ) : (
          filteredNotifications.map(notification => {
            const config = getTypeConfig(notification.type);
            return (
              <TouchableOpacity 
                key={notification.id}
                style={[
                  styles.notificationCard,
                  !notification.read && styles.unreadCard
                ]}
                onPress={() => markAsRead(notification.id)}
              >
                <View style={styles.notificationHeader}>
                  <View style={styles.notificationTypeContainer}>
                    <Text style={styles.notificationIcon}>{config.icon}</Text>
                    <View style={[styles.typeBadge, { backgroundColor: config.color + '20' }]}>
                      <Text style={[styles.typeText, { color: config.color }]}>
                        {config.label}
                      </Text>
                    </View>
                  </View>
                  {!notification.read && <View style={styles.unreadDot} />}
                </View>

                <Text style={styles.notificationTitle}>{notification.title}</Text>
                <Text style={styles.notificationMessage}>{notification.message}</Text>
                
                <View style={styles.notificationFooter}>
                  <Text style={styles.notificationTime}>
                    🕒 {formatTimestamp(notification.timestamp)}
                  </Text>
                  {notification.priority === 'high' && (
                    <View style={styles.priorityBadge}>
                      <Text style={styles.priorityText}>⚡ Yüksek Öncelik</Text>
                    </View>
                  )}
                </View>
              </TouchableOpacity>
            );
          })
        )}

        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#111827',
  },
  loadingText: {
    color: '#9ca3af',
    marginTop: 12,
    fontSize: 14,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  headerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  badge: {
    backgroundColor: '#ef4444',
    borderRadius: 12,
    minWidth: 24,
    height: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 8,
  },
  badgeText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#1f2937',
    borderRadius: 8,
  },
  headerButtonText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  filterContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  filterButton: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1f2937',
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#374151',
  },
  filterButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  filterButtonText: {
    color: '#9ca3af',
    fontSize: 13,
  },
  filterButtonTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
  listContainer: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyIcon: {
    fontSize: 60,
    marginBottom: 16,
  },
  emptyText: {
    color: '#9ca3af',
    fontSize: 16,
  },
  notificationCard: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  unreadCard: {
    backgroundColor: '#1e3a5f',
    borderColor: '#3b82f6',
  },
  notificationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  notificationTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  notificationIcon: {
    fontSize: 20,
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  typeText: {
    fontSize: 11,
    fontWeight: '600',
  },
  unreadDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#3b82f6',
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  notificationMessage: {
    fontSize: 14,
    color: '#9ca3af',
    lineHeight: 20,
    marginBottom: 8,
  },
  notificationFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  notificationTime: {
    fontSize: 12,
    color: '#6b7280',
  },
  priorityBadge: {
    backgroundColor: '#ef444420',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
  },
  priorityText: {
    color: '#ef4444',
    fontSize: 11,
    fontWeight: '600',
  },
});
