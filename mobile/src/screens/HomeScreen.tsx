import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { API_BASE_URL } from '../config/api';
import { GalleryStats } from '../types';

interface ServerStatus {
  connected: boolean;
  message: string;
}

export default function HomeScreen() {
  const [serverStatus, setServerStatus] = useState<ServerStatus>({
    connected: false,
    message: 'Bağlanıyor...',
  });
  const [stats, setStats] = useState<GalleryStats | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const checkServer = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      
      if (response.ok) {
        setServerStatus({ connected: true, message: 'Bağlı' });
        // Galeri istatistiklerini al
        fetchStats();
      } else {
        setServerStatus({ connected: false, message: 'Sunucu yanıt vermiyor' });
      }
    } catch (error) {
      setServerStatus({ connected: false, message: 'Bağlantı hatası' });
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/gallery`);
      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
      }
    } catch (error) {
      console.log('Stats fetch error:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await checkServer();
    setRefreshing(false);
  };

  useEffect(() => {
    checkServer();
    const interval = setInterval(checkServer, 10000); // 10 saniyede bir kontrol
    return () => clearInterval(interval);
  }, []);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>🐄 AI Hayvan Takip</Text>
        <Text style={styles.subtitle}>Otomatik Tanıma Sistemi</Text>
      </View>

      {/* Server Status */}
      <View style={[styles.card, serverStatus.connected ? styles.cardSuccess : styles.cardError]}>
        <View style={styles.statusRow}>
          <Text style={styles.statusIcon}>
            {serverStatus.connected ? '🟢' : '🔴'}
          </Text>
          <View>
            <Text style={styles.cardTitle}>Sunucu Durumu</Text>
            <Text style={styles.cardSubtitle}>{serverStatus.message}</Text>
          </View>
        </View>
        <Text style={styles.serverUrl}>{API_BASE_URL}</Text>
      </View>

      {/* Stats Cards */}
      {stats && (
        <>
          <View style={styles.statsGrid}>
            <View style={[styles.statCard, { backgroundColor: '#22c55e' }]}>
              <Text style={styles.statNumber}>{stats.total_animals}</Text>
              <Text style={styles.statLabel}>Kayıtlı Hayvan</Text>
            </View>
            <View style={[styles.statCard, { backgroundColor: '#3b82f6' }]}>
              <Text style={styles.statNumber}>
                {Object.keys(stats.by_class).length}
              </Text>
              <Text style={styles.statLabel}>Tür Çeşidi</Text>
            </View>
          </View>

          {/* Animals by Class */}
          {Object.keys(stats.by_class).length > 0 && (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Türlere Göre Dağılım</Text>
              {Object.entries(stats.by_class).map(([className, count]) => (
                <View key={className} style={styles.classRow}>
                  <Text style={styles.className}>{className}</Text>
                  <Text style={styles.classCount}>{count}</Text>
                </View>
              ))}
            </View>
          )}
        </>
      )}

      {/* Quick Actions */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Hızlı İşlemler</Text>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionIcon}>📷</Text>
          <Text style={styles.actionText}>Kamerayı Başlat</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.actionButton}>
          <Text style={styles.actionIcon}>📋</Text>
          <Text style={styles.actionText}>Hayvan Listesi</Text>
        </TouchableOpacity>
      </View>

      {/* Info */}
      <View style={[styles.card, styles.infoCard]}>
        <Text style={styles.infoTitle}>ℹ️ Nasıl Çalışır?</Text>
        <Text style={styles.infoText}>
          1. Kamera sekmesine gidin{'\n'}
          2. Hayvanları kameraya gösterin{'\n'}
          3. Sistem otomatik olarak tespit eder{'\n'}
          4. Yeni hayvanlar otomatik kayıt edilir{'\n'}
          5. Daha önce görülen hayvanlar tanınır
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
    paddingTop: 8,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: '#9ca3af',
  },
  card: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  cardSuccess: {
    borderLeftWidth: 4,
    borderLeftColor: '#22c55e',
  },
  cardError: {
    borderLeftWidth: 4,
    borderLeftColor: '#ef4444',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 14,
    color: '#9ca3af',
  },
  serverUrl: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 8,
    fontFamily: 'monospace',
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statLabel: {
    fontSize: 14,
    color: '#ffffff',
    opacity: 0.9,
    marginTop: 4,
  },
  classRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  className: {
    fontSize: 14,
    color: '#d1d5db',
    textTransform: 'capitalize',
  },
  classCount: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#22c55e',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  actionIcon: {
    fontSize: 20,
    marginRight: 12,
  },
  actionText: {
    fontSize: 14,
    color: '#ffffff',
    fontWeight: '600',
  },
  infoCard: {
    backgroundColor: '#1e3a5f',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#60a5fa',
    marginBottom: 8,
  },
  infoText: {
    fontSize: 14,
    color: '#93c5fd',
    lineHeight: 22,
  },
});
