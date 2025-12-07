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

interface EstrusDetection {
  id: string;
  animal_id: string;
  animal_name: string;
  detection_date: string;
  confidence: number;
  signs: string[];
  status: 'detected' | 'confirmed' | 'inseminated';
}

interface Pregnancy {
  id: string;
  animal_id: string;
  animal_name: string;
  breeding_date: string;
  expected_birth: string;
  days_pregnant: number;
  status: 'pregnant' | 'confirmed' | 'given_birth';
}

interface ReproductionStats {
  total_estrus: number;
  total_pregnancies: number;
  success_rate: number;
  upcoming_births: number;
}

export default function ReproductionScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'estrus' | 'pregnancy'>('estrus');
  const [stats, setStats] = useState<ReproductionStats | null>(null);
  const [estrusDetections, setEstrusDetections] = useState<EstrusDetection[]>([]);
  const [pregnancies, setPregnancies] = useState<Pregnancy[]>([]);

  const fetchData = async () => {
    try {
      // Fetch stats
      const statsRes = await fetch(`${API_BASE_URL}/api/v1/reproduction/stats`);
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }

      // Fetch estrus detections
      const estrusRes = await fetch(`${API_BASE_URL}/api/v1/reproduction/estrus`);
      if (estrusRes.ok) {
        const data = await estrusRes.json();
        setEstrusDetections(data.detections || []);
      }

      // Fetch pregnancies
      const pregRes = await fetch(`${API_BASE_URL}/api/v1/reproduction/pregnancies`);
      if (pregRes.ok) {
        const data = await pregRes.json();
        setPregnancies(data.pregnancies || []);
      }
    } catch (error) {
      console.error('Error fetching reproduction data:', error);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'detected':
        return '#f59e0b';
      case 'confirmed':
        return '#22c55e';
      case 'inseminated':
        return '#3b82f6';
      case 'pregnant':
        return '#8b5cf6';
      case 'given_birth':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'detected':
        return 'Tespit Edildi';
      case 'confirmed':
        return 'Onaylandı';
      case 'inseminated':
        return 'Tohumlandı';
      case 'pregnant':
        return 'Gebe';
      case 'given_birth':
        return 'Doğum Yaptı';
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#ec4899" />
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
        <Text style={styles.title}>🐄 Üreme Takibi</Text>
        <Text style={styles.subtitle}>Kızgınlık ve gebelik yönetimi</Text>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#ec4899' }]}>
          <Text style={styles.statIcon}>🔥</Text>
          <Text style={styles.statValue}>{stats?.total_estrus || 0}</Text>
          <Text style={styles.statLabel}>Kızgınlık</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#8b5cf6' }]}>
          <Text style={styles.statIcon}>🤰</Text>
          <Text style={styles.statValue}>{stats?.total_pregnancies || 0}</Text>
          <Text style={styles.statLabel}>Gebelik</Text>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#22c55e' }]}>
          <Text style={styles.statIcon}>📈</Text>
          <Text style={styles.statValue}>{stats?.success_rate || 0}%</Text>
          <Text style={styles.statLabel}>Başarı Oranı</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#f59e0b' }]}>
          <Text style={styles.statIcon}>👶</Text>
          <Text style={styles.statValue}>{stats?.upcoming_births || 0}</Text>
          <Text style={styles.statLabel}>Yaklaşan Doğum</Text>
        </View>
      </View>

      {/* Tabs */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'estrus' && styles.activeTab]}
          onPress={() => setActiveTab('estrus')}
        >
          <Text style={[styles.tabText, activeTab === 'estrus' && styles.activeTabText]}>
            🔥 Kızgınlık
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'pregnancy' && styles.activeTab]}
          onPress={() => setActiveTab('pregnancy')}
        >
          <Text style={[styles.tabText, activeTab === 'pregnancy' && styles.activeTabText]}>
            🐄 Gebelik
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {activeTab === 'estrus' ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Kızgınlık Tespitleri</Text>
          {estrusDetections.length > 0 ? (
            estrusDetections.map((detection) => (
              <View key={detection.id} style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>{detection.animal_name}</Text>
                  <View style={[styles.statusBadge, { backgroundColor: getStatusColor(detection.status) }]}>
                    <Text style={styles.statusText}>{getStatusText(detection.status)}</Text>
                  </View>
                </View>
                <Text style={styles.cardDate}>
                  📅 {new Date(detection.detection_date).toLocaleDateString('tr-TR')}
                </Text>
                <View style={styles.confidenceBar}>
                  <View style={[styles.confidenceFill, { width: `${detection.confidence}%` }]} />
                </View>
                <Text style={styles.confidenceText}>Güven: %{detection.confidence}</Text>
                {detection.signs && detection.signs.length > 0 && (
                  <View style={styles.signs}>
                    <Text style={styles.signsLabel}>Belirtiler:</Text>
                    <Text style={styles.signsText}>{detection.signs.join(', ')}</Text>
                  </View>
                )}
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🔍</Text>
              <Text style={styles.emptyText}>Henüz kızgınlık tespiti yok</Text>
            </View>
          )}
        </View>
      ) : (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Gebelik Takibi</Text>
          {pregnancies.length > 0 ? (
            pregnancies.map((pregnancy) => (
              <View key={pregnancy.id} style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>{pregnancy.animal_name}</Text>
                  <View style={[styles.statusBadge, { backgroundColor: getStatusColor(pregnancy.status) }]}>
                    <Text style={styles.statusText}>{getStatusText(pregnancy.status)}</Text>
                  </View>
                </View>
                <View style={styles.pregnancyInfo}>
                  <View style={styles.infoItem}>
                    <Text style={styles.infoLabel}>Tohumlama</Text>
                    <Text style={styles.infoValue}>
                      {new Date(pregnancy.breeding_date).toLocaleDateString('tr-TR')}
                    </Text>
                  </View>
                  <View style={styles.infoItem}>
                    <Text style={styles.infoLabel}>Tahmini Doğum</Text>
                    <Text style={styles.infoValue}>
                      {new Date(pregnancy.expected_birth).toLocaleDateString('tr-TR')}
                    </Text>
                  </View>
                </View>
                <View style={styles.daysContainer}>
                  <Text style={styles.daysNumber}>{pregnancy.days_pregnant}</Text>
                  <Text style={styles.daysLabel}>gün gebe</Text>
                </View>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      { width: `${Math.min((pregnancy.days_pregnant / 283) * 100, 100)}%` },
                    ]}
                  />
                </View>
              </View>
            ))
          ) : (
            <View style={styles.emptyState}>
              <Text style={styles.emptyIcon}>🤰</Text>
              <Text style={styles.emptyText}>Henüz gebelik kaydı yok</Text>
            </View>
          )}
        </View>
      )}

      {/* AI Info */}
      <View style={styles.infoSection}>
        <Text style={styles.infoTitle}>🤖 AI Kızgınlık Tespiti</Text>
        <Text style={styles.infoText}>
          Sistem, kamera görüntülerinden otomatik olarak kızgınlık belirtilerini tespit eder:
        </Text>
        <View style={styles.infoList}>
          <Text style={styles.infoItem}>• Binme aktivitesi</Text>
          <Text style={styles.infoItem}>• Huzursuz davranış</Text>
          <Text style={styles.infoItem}>• Artan hareket</Text>
          <Text style={styles.infoItem}>• Sürüden ayrılma</Text>
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
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#ec4899',
  },
  tabText: {
    color: '#9ca3af',
    fontWeight: '600',
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
  card: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  cardDate: {
    color: '#9ca3af',
    fontSize: 13,
    marginBottom: 8,
  },
  confidenceBar: {
    height: 6,
    backgroundColor: '#4b5563',
    borderRadius: 3,
    marginBottom: 4,
  },
  confidenceFill: {
    height: '100%',
    backgroundColor: '#22c55e',
    borderRadius: 3,
  },
  confidenceText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  signs: {
    marginTop: 8,
  },
  signsLabel: {
    color: '#9ca3af',
    fontSize: 12,
  },
  signsText: {
    color: '#ffffff',
    fontSize: 13,
  },
  pregnancyInfo: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  infoItem: {
    flex: 1,
  },
  infoLabel: {
    color: '#9ca3af',
    fontSize: 12,
  },
  infoValue: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '500',
  },
  daysContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 8,
  },
  daysNumber: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#8b5cf6',
    marginRight: 8,
  },
  daysLabel: {
    color: '#9ca3af',
    fontSize: 14,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#4b5563',
    borderRadius: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#8b5cf6',
    borderRadius: 4,
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
  infoSection: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#ec4899',
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  infoText: {
    color: '#9ca3af',
    fontSize: 14,
    lineHeight: 20,
  },
  infoList: {
    marginTop: 8,
  },
});
