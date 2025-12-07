import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { API_BASE_URL } from '../config/api';

interface PoultryStats {
  total_birds: number;
  total_coops: number;
  today_eggs: number;
  average_production: number;
  healthy_percentage: number;
}

interface Coop {
  id: string;
  name: string;
  bird_count: number;
  capacity: number;
  today_eggs: number;
  health_status: 'good' | 'warning' | 'critical';
  temperature: number;
  humidity: number;
}

interface EggProduction {
  date: string;
  count: number;
  broken: number;
  quality_a: number;
  quality_b: number;
}

export default function PoultryScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'coops' | 'eggs'>('overview');
  const [stats, setStats] = useState<PoultryStats | null>(null);
  const [coops, setCoops] = useState<Coop[]>([]);
  const [eggHistory, setEggHistory] = useState<EggProduction[]>([]);

  const fetchData = async () => {
    try {
      // Fetch stats
      const statsRes = await fetch(`${API_BASE_URL}/api/v1/poultry/stats`);
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }

      // Fetch coops
      const coopsRes = await fetch(`${API_BASE_URL}/api/v1/poultry/coops`);
      if (coopsRes.ok) {
        const data = await coopsRes.json();
        setCoops(data.coops || []);
      }

      // Fetch egg production history
      const eggsRes = await fetch(`${API_BASE_URL}/api/v1/poultry/eggs/history`);
      if (eggsRes.ok) {
        const data = await eggsRes.json();
        setEggHistory(data.history || []);
      }
    } catch (error) {
      console.error('Error fetching poultry data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    setRefreshing(false);
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'good':
        return '#22c55e';
      case 'warning':
        return '#f59e0b';
      case 'critical':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getHealthText = (status: string) => {
    switch (status) {
      case 'good':
        return 'İyi';
      case 'warning':
        return 'Dikkat';
      case 'critical':
        return 'Kritik';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#f59e0b" />
        <Text style={styles.loadingText}>Yükleniyor...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>🐔 Kanatlı Modülü</Text>
        <Text style={styles.subtitle}>Kümes hayvanları takip sistemi</Text>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#f59e0b' }]}>
          <Text style={styles.statIcon}>🐔</Text>
          <Text style={styles.statValue}>{stats?.total_birds || 0}</Text>
          <Text style={styles.statLabel}>Toplam Kanatlı</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#3b82f6' }]}>
          <Text style={styles.statIcon}>🏠</Text>
          <Text style={styles.statValue}>{stats?.total_coops || 0}</Text>
          <Text style={styles.statLabel}>Kümes</Text>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#eab308' }]}>
          <Text style={styles.statIcon}>🥚</Text>
          <Text style={styles.statValue}>{stats?.today_eggs || 0}</Text>
          <Text style={styles.statLabel}>Bugün Yumurta</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#22c55e' }]}>
          <Text style={styles.statIcon}>💚</Text>
          <Text style={styles.statValue}>{stats?.healthy_percentage || 0}%</Text>
          <Text style={styles.statLabel}>Sağlıklı</Text>
        </View>
      </View>

      {/* Tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'overview' && styles.activeTab]}
          onPress={() => setActiveTab('overview')}
        >
          <Text style={[styles.tabText, activeTab === 'overview' && styles.activeTabText]}>
            📊 Genel
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'coops' && styles.activeTab]}
          onPress={() => setActiveTab('coops')}
        >
          <Text style={[styles.tabText, activeTab === 'coops' && styles.activeTabText]}>
            🏠 Kümesler
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'eggs' && styles.activeTab]}
          onPress={() => setActiveTab('eggs')}
        >
          <Text style={[styles.tabText, activeTab === 'eggs' && styles.activeTabText]}>
            🥚 Yumurta
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {activeTab === 'overview' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Hızlı Bakış</Text>
          
          <View style={styles.overviewCard}>
            <Text style={styles.overviewTitle}>🎯 Günlük Hedef</Text>
            <View style={styles.progressContainer}>
              <View style={styles.progressBar}>
                <View 
                  style={[
                    styles.progressFill, 
                    { width: `${Math.min((stats?.today_eggs || 0) / (stats?.average_production || 100) * 100, 100)}%` }
                  ]} 
                />
              </View>
              <Text style={styles.progressText}>
                {stats?.today_eggs || 0} / {stats?.average_production || 0} yumurta
              </Text>
            </View>
          </View>

          <View style={styles.featureGrid}>
            <View style={styles.featureCard}>
              <Text style={styles.featureIcon}>🔍</Text>
              <Text style={styles.featureTitle}>Davranış Analizi</Text>
              <Text style={styles.featureDesc}>AI ile sürü davranışı izleme</Text>
            </View>
            <View style={styles.featureCard}>
              <Text style={styles.featureIcon}>🌡️</Text>
              <Text style={styles.featureTitle}>Çevre İzleme</Text>
              <Text style={styles.featureDesc}>Sıcaklık ve nem takibi</Text>
            </View>
            <View style={styles.featureCard}>
              <Text style={styles.featureIcon}>💉</Text>
              <Text style={styles.featureTitle}>Sağlık Takibi</Text>
              <Text style={styles.featureDesc}>Hastalık tespiti</Text>
            </View>
            <View style={styles.featureCard}>
              <Text style={styles.featureIcon}>📈</Text>
              <Text style={styles.featureTitle}>Üretim Analizi</Text>
              <Text style={styles.featureDesc}>Yumurta verimi takibi</Text>
            </View>
          </View>
        </View>
      )}

      {activeTab === 'coops' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Kümes Listesi</Text>
          {coops.length > 0 ? (
            coops.map((coop) => (
              <View key={coop.id} style={styles.coopCard}>
                <View style={styles.coopHeader}>
                  <Text style={styles.coopName}>{coop.name}</Text>
                  <View style={[styles.healthBadge, { backgroundColor: getHealthColor(coop.health_status) }]}>
                    <Text style={styles.healthText}>{getHealthText(coop.health_status)}</Text>
                  </View>
                </View>
                
                <View style={styles.coopStats}>
                  <View style={styles.coopStat}>
                    <Text style={styles.coopStatIcon}>🐔</Text>
                    <Text style={styles.coopStatValue}>{coop.bird_count}/{coop.capacity}</Text>
                    <Text style={styles.coopStatLabel}>Kapasite</Text>
                  </View>
                  <View style={styles.coopStat}>
                    <Text style={styles.coopStatIcon}>🥚</Text>
                    <Text style={styles.coopStatValue}>{coop.today_eggs}</Text>
                    <Text style={styles.coopStatLabel}>Bugün</Text>
                  </View>
                  <View style={styles.coopStat}>
                    <Text style={styles.coopStatIcon}>🌡️</Text>
                    <Text style={styles.coopStatValue}>{coop.temperature}°C</Text>
                    <Text style={styles.coopStatLabel}>Sıcaklık</Text>
                  </View>
                  <View style={styles.coopStat}>
                    <Text style={styles.coopStatIcon}>💧</Text>
                    <Text style={styles.coopStatValue}>{coop.humidity}%</Text>
                    <Text style={styles.coopStatLabel}>Nem</Text>
                  </View>
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🏠</Text>
              <Text style={styles.emptyText}>Henüz kümes kaydı yok</Text>
            </View>
          )}
        </View>
      )}

      {activeTab === 'eggs' && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Yumurta Üretim Geçmişi</Text>
          {eggHistory.length > 0 ? (
            eggHistory.map((day, index) => (
              <View key={index} style={styles.eggCard}>
                <View style={styles.eggHeader}>
                  <Text style={styles.eggDate}>
                    📅 {new Date(day.date).toLocaleDateString('tr-TR')}
                  </Text>
                  <Text style={styles.eggTotal}>{day.count} yumurta</Text>
                </View>
                <View style={styles.eggDetails}>
                  <View style={styles.eggDetail}>
                    <Text style={styles.eggDetailLabel}>A Kalite</Text>
                    <Text style={styles.eggDetailValue}>{day.quality_a}</Text>
                  </View>
                  <View style={styles.eggDetail}>
                    <Text style={styles.eggDetailLabel}>B Kalite</Text>
                    <Text style={styles.eggDetailValue}>{day.quality_b}</Text>
                  </View>
                  <View style={styles.eggDetail}>
                    <Text style={styles.eggDetailLabel}>Kırık</Text>
                    <Text style={[styles.eggDetailValue, { color: '#ef4444' }]}>{day.broken}</Text>
                  </View>
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🥚</Text>
              <Text style={styles.emptyText}>Henüz üretim kaydı yok</Text>
            </View>
          )}
        </View>
      )}

      {/* AI Features */}
      <View style={styles.aiSection}>
        <Text style={styles.aiTitle}>🧠 AI Özellikleri</Text>
        <View style={styles.aiFeatures}>
          <Text style={styles.aiFeature}>✅ Sürü davranış analizi</Text>
          <Text style={styles.aiFeature}>✅ Hastalık erken tespiti</Text>
          <Text style={styles.aiFeature}>✅ Yumurta kalite tahmini</Text>
          <Text style={styles.aiFeature}>✅ Anormal hareket algılama</Text>
          <Text style={styles.aiFeature}>✅ Kümes ortam optimizasyonu</Text>
        </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#111827',
  },
  loadingText: {
    color: '#9ca3af',
    marginTop: 12,
  },
  header: {
    alignItems: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  subtitle: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  statCard: {
    flex: 1,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  statIcon: {
    fontSize: 24,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 4,
    marginBottom: 16,
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#f59e0b',
  },
  tabText: {
    color: '#9ca3af',
    fontWeight: '600',
    fontSize: 13,
  },
  activeTabText: {
    color: '#ffffff',
  },
  section: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  overviewCard: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  overviewTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 12,
  },
  progressContainer: {
    gap: 8,
  },
  progressBar: {
    height: 12,
    backgroundColor: '#4b5563',
    borderRadius: 6,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#22c55e',
    borderRadius: 6,
  },
  progressText: {
    color: '#9ca3af',
    fontSize: 13,
    textAlign: 'center',
  },
  featureGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  featureCard: {
    width: '47%',
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  featureIcon: {
    fontSize: 28,
    marginBottom: 8,
  },
  featureTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  featureDesc: {
    fontSize: 11,
    color: '#9ca3af',
    textAlign: 'center',
  },
  coopCard: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  coopHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  coopName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  healthBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  healthText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  coopStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  coopStat: {
    alignItems: 'center',
  },
  coopStatIcon: {
    fontSize: 20,
    marginBottom: 4,
  },
  coopStatValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  coopStatLabel: {
    fontSize: 10,
    color: '#9ca3af',
  },
  eggCard: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  eggHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  eggDate: {
    fontSize: 14,
    color: '#9ca3af',
  },
  eggTotal: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#eab308',
  },
  eggDetails: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  eggDetail: {
    alignItems: 'center',
  },
  eggDetailLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 4,
  },
  eggDetailValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  emptyState: {
    alignItems: 'center',
    padding: 24,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
    opacity: 0.5,
  },
  emptyText: {
    color: '#9ca3af',
    fontSize: 16,
  },
  aiSection: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#f59e0b',
  },
  aiTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  aiFeatures: {
    gap: 8,
  },
  aiFeature: {
    color: '#d1d5db',
    fontSize: 14,
  },
});
