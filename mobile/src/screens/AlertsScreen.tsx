import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';

interface Alert {
  id: string;
  type: 'sağlık' | 'güvenlik' | 'sistem' | 'aktivite';
  severity: 'düşük' | 'orta' | 'yüksek' | 'kritik';
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

// Demo alerts (Gerçek uygulamada backend'den gelir)
const DEMO_ALERTS: Alert[] = [
  {
    id: '1',
    type: 'aktivite',
    severity: 'orta',
    title: 'Yeni Hayvan Tespit Edildi',
    message: 'INEK_0001 sisteme kaydedildi',
    is_read: false,
    created_at: new Date().toISOString(),
  },
  {
    id: '2',
    type: 'sistem',
    severity: 'düşük',
    title: 'Sistem Başlatıldı',
    message: 'AI Hayvan Takip sistemi aktif',
    is_read: true,
    created_at: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: '3',
    type: 'güvenlik',
    severity: 'yüksek',
    title: 'Bölge İhlali',
    message: 'Bir hayvan belirlenen bölgenin dışına çıktı',
    is_read: false,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
];

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState<Alert[]>(DEMO_ALERTS);
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    // Gerçek uygulamada backend'den çekilir
    await new Promise(resolve => setTimeout(resolve, 1000));
    setRefreshing(false);
  };

  const markAsRead = (id: string) => {
    setAlerts(prev =>
      prev.map(alert =>
        alert.id === id ? { ...alert, is_read: true } : alert
      )
    );
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'kritik': return '#ef4444';
      case 'yüksek': return '#f97316';
      case 'orta': return '#eab308';
      case 'düşük': return '#22c55e';
      default: return '#6b7280';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'sağlık': return '🏥';
      case 'güvenlik': return '🔒';
      case 'sistem': return '⚙️';
      case 'aktivite': return '📊';
      default: return '📋';
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Az önce';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} dk önce`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} saat önce`;
    
    return date.toLocaleDateString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  const renderAlert = ({ item }: { item: Alert }) => (
    <TouchableOpacity
      style={[
        styles.alertCard,
        !item.is_read && styles.alertUnread,
        { borderLeftColor: getSeverityColor(item.severity) }
      ]}
      onPress={() => markAsRead(item.id)}
    >
      <View style={styles.alertHeader}>
        <Text style={styles.alertIcon}>{getTypeIcon(item.type)}</Text>
        <View style={styles.alertInfo}>
          <Text style={styles.alertTitle}>{item.title}</Text>
          <Text style={styles.alertTime}>{formatDate(item.created_at)}</Text>
        </View>
        <View style={[
          styles.severityBadge,
          { backgroundColor: getSeverityColor(item.severity) }
        ]}>
          <Text style={styles.severityText}>{item.severity}</Text>
        </View>
      </View>
      <Text style={styles.alertMessage}>{item.message}</Text>
      {!item.is_read && (
        <View style={styles.unreadDot} />
      )}
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header Stats */}
      <View style={styles.header}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{alerts.length}</Text>
          <Text style={styles.statLabel}>Toplam</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={[styles.statValue, { color: '#ef4444' }]}>{unreadCount}</Text>
          <Text style={styles.statLabel}>Okunmamış</Text>
        </View>
        <TouchableOpacity
          style={styles.markAllButton}
          onPress={() => setAlerts(prev => prev.map(a => ({ ...a, is_read: true })))}
        >
          <Text style={styles.markAllText}>Tümünü Okundu İşaretle</Text>
        </TouchableOpacity>
      </View>

      {/* Alert List */}
      <FlatList
        data={alerts}
        keyExtractor={(item) => item.id}
        renderItem={renderAlert}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🔔</Text>
            <Text style={styles.emptyText}>Uyarı yok</Text>
            <Text style={styles.emptySubtext}>
              Yeni uyarılar burada görünecek
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  header: {
    flexDirection: 'row',
    backgroundColor: '#1f2937',
    padding: 16,
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  statItem: {
    alignItems: 'center',
    marginRight: 24,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statLabel: {
    fontSize: 11,
    color: '#9ca3af',
    marginTop: 2,
  },
  markAllButton: {
    flex: 1,
    alignItems: 'flex-end',
  },
  markAllText: {
    color: '#60a5fa',
    fontSize: 13,
  },
  listContent: {
    padding: 12,
  },
  alertCard: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    position: 'relative',
  },
  alertUnread: {
    backgroundColor: '#1e3a5f',
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  alertIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  alertInfo: {
    flex: 1,
  },
  alertTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 2,
  },
  alertTime: {
    fontSize: 12,
    color: '#9ca3af',
  },
  severityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  severityText: {
    color: '#ffffff',
    fontSize: 10,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  alertMessage: {
    fontSize: 14,
    color: '#d1d5db',
    marginLeft: 36,
  },
  unreadDot: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#3b82f6',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 80,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyText: {
    fontSize: 18,
    color: '#ffffff',
    fontWeight: '600',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
  },
});
