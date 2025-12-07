import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { API_BASE_URL } from '../config/api';

interface Report {
  id: string;
  name: string;
  type: string;
  generatedAt: string;
  size: string;
  status: string;
}

interface ReportStats {
  total_reports: number;
  daily_reports: number;
  weekly_reports: number;
  monthly_reports: number;
}

const monthlyData = [
  { ay: 'Oca', hayvan: 245, saglik: 12, alarm: 5 },
  { ay: 'Şub', hayvan: 252, saglik: 8, alarm: 3 },
  { ay: 'Mar', hayvan: 260, saglik: 15, alarm: 7 },
  { ay: 'Nis', hayvan: 268, saglik: 10, alarm: 4 },
  { ay: 'May', hayvan: 275, saglik: 6, alarm: 2 },
  { ay: 'Haz', hayvan: 282, saglik: 9, alarm: 6 },
];

const healthDistribution = [
  { name: 'Sağlıklı', value: 85, color: '#22c55e' },
  { name: 'Tedavi Altında', value: 8, color: '#eab308' },
  { name: 'Kritik', value: 3, color: '#ef4444' },
  { name: 'Karantina', value: 4, color: '#8b5cf6' },
];

export default function ReportsScreen() {
  const [reports, setReports] = useState<Report[]>([]);
  const [stats, setStats] = useState<ReportStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'reports'>('overview');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadStats(), loadReports()]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/reports/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        setStats({
          total_reports: 156,
          daily_reports: 30,
          weekly_reports: 52,
          monthly_reports: 12,
        });
      }
    } catch (error) {
      setStats({
        total_reports: 156,
        daily_reports: 30,
        weekly_reports: 52,
        monthly_reports: 12,
      });
    }
  };

  const loadReports = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/reports/list`);
      if (response.ok) {
        const data = await response.json();
        setReports(data);
      } else {
        setReports([
          { id: '1', name: 'Günlük Aktivite Raporu', type: 'günlük', generatedAt: '2024-12-02 09:00', size: '2.4 MB', status: 'hazır' },
          { id: '2', name: 'Haftalık Sağlık Özeti', type: 'haftalık', generatedAt: '2024-12-01 18:00', size: '5.8 MB', status: 'hazır' },
          { id: '3', name: 'Aylık Üretim Raporu', type: 'aylık', generatedAt: '2024-12-01 00:00', size: '12.3 MB', status: 'hazır' },
          { id: '4', name: 'Özel Analiz Raporu', type: 'özel', generatedAt: '2024-12-02 10:30', size: '-', status: 'oluşturuluyor' },
        ]);
      }
    } catch (error) {
      setReports([
        { id: '1', name: 'Günlük Aktivite Raporu', type: 'günlük', generatedAt: '2024-12-02 09:00', size: '2.4 MB', status: 'hazır' },
        { id: '2', name: 'Haftalık Sağlık Özeti', type: 'haftalık', generatedAt: '2024-12-01 18:00', size: '5.8 MB', status: 'hazır' },
      ]);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'hazır': return '#22c55e';
      case 'oluşturuluyor': return '#eab308';
      case 'hata': return '#ef4444';
      default: return '#9ca3af';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'günlük': return '#3b82f6';
      case 'haftalık': return '#8b5cf6';
      case 'aylık': return '#22c55e';
      case 'özel': return '#f59e0b';
      default: return '#9ca3af';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Raporlar yükleniyor...</Text>
      </View>
    );
  }

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* İstatistik Kartları */}
      <View style={styles.statsContainer}>
        <View style={[styles.statCard, { backgroundColor: '#dbeafe' }]}>
          <Text style={[styles.statValue, { color: '#2563eb' }]}>{stats?.total_reports || 0}</Text>
          <Text style={styles.statLabel}>Toplam Rapor</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#dcfce7' }]}>
          <Text style={[styles.statValue, { color: '#16a34a' }]}>{stats?.daily_reports || 0}</Text>
          <Text style={styles.statLabel}>Günlük</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#f3e8ff' }]}>
          <Text style={[styles.statValue, { color: '#7c3aed' }]}>{stats?.weekly_reports || 0}</Text>
          <Text style={styles.statLabel}>Haftalık</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#fef3c7' }]}>
          <Text style={[styles.statValue, { color: '#d97706' }]}>{stats?.monthly_reports || 0}</Text>
          <Text style={styles.statLabel}>Aylık</Text>
        </View>
      </View>

      {/* Tab Seçimi */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'overview' && styles.tabButtonActive]}
          onPress={() => setActiveTab('overview')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'overview' && styles.tabButtonTextActive]}>
            📊 Genel Bakış
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'reports' && styles.tabButtonActive]}
          onPress={() => setActiveTab('reports')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'reports' && styles.tabButtonTextActive]}>
            📄 Raporlar
          </Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'overview' ? (
        <>
          {/* Aylık Trend */}
          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>📈 Aylık Trend</Text>
            <View style={styles.chartContainer}>
              {monthlyData.map((item, index) => (
                <View key={index} style={styles.barContainer}>
                  <View style={styles.barWrapper}>
                    <View 
                      style={[styles.bar, { height: item.hayvan / 3, backgroundColor: '#3b82f6' }]} 
                    />
                  </View>
                  <Text style={styles.barLabel}>{item.ay}</Text>
                </View>
              ))}
            </View>
            <View style={styles.legend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: '#3b82f6' }]} />
                <Text style={styles.legendText}>Hayvan Sayısı</Text>
              </View>
            </View>
          </View>

          {/* Sağlık Dağılımı */}
          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>🏥 Sağlık Durumu Dağılımı</Text>
            <View style={styles.pieChartContainer}>
              {healthDistribution.map((item, index) => (
                <View key={index} style={styles.pieItem}>
                  <View style={[styles.pieColor, { backgroundColor: item.color }]} />
                  <Text style={styles.pieLabel}>{item.name}</Text>
                  <Text style={styles.pieValue}>%{item.value}</Text>
                </View>
              ))}
            </View>
          </View>
        </>
      ) : (
        <>
          {/* Rapor Listesi */}
          <View style={styles.reportsContainer}>
            <Text style={styles.sectionTitle}>Son Raporlar</Text>
            
            {reports.map(report => (
              <TouchableOpacity key={report.id} style={styles.reportCard}>
                <View style={styles.reportHeader}>
                  <View style={[styles.typeBadge, { backgroundColor: getTypeColor(report.type) + '20' }]}>
                    <Text style={[styles.typeText, { color: getTypeColor(report.type) }]}>
                      {report.type.toUpperCase()}
                    </Text>
                  </View>
                  <View style={[styles.statusDot, { backgroundColor: getStatusColor(report.status) }]} />
                </View>
                
                <Text style={styles.reportName}>{report.name}</Text>
                
                <View style={styles.reportDetails}>
                  <Text style={styles.reportDetail}>📅 {report.generatedAt}</Text>
                  <Text style={styles.reportDetail}>📦 {report.size}</Text>
                </View>

                <View style={styles.reportActions}>
                  <TouchableOpacity style={styles.actionButton}>
                    <Text style={styles.actionButtonText}>📥 İndir</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={[styles.actionButton, styles.actionButtonSecondary]}>
                    <Text style={styles.actionButtonTextSecondary}>👁️ Görüntüle</Text>
                  </TouchableOpacity>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          {/* Rapor Oluştur */}
          <TouchableOpacity style={styles.generateButton}>
            <Text style={styles.generateButtonText}>+ Yeni Rapor Oluştur</Text>
          </TouchableOpacity>
        </>
      )}

      <View style={{ height: 100 }} />
    </ScrollView>
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
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: 12,
    color: '#374151',
    marginTop: 4,
  },
  tabContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 16,
    gap: 12,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#1f2937',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#374151',
  },
  tabButtonActive: {
    backgroundColor: '#3b82f6',
    borderColor: '#3b82f6',
  },
  tabButtonText: {
    color: '#9ca3af',
    fontSize: 14,
    fontWeight: '600',
  },
  tabButtonTextActive: {
    color: '#ffffff',
  },
  chartCard: {
    backgroundColor: '#1f2937',
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  chartContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'flex-end',
    height: 120,
  },
  barContainer: {
    alignItems: 'center',
  },
  barWrapper: {
    height: 100,
    justifyContent: 'flex-end',
  },
  bar: {
    width: 30,
    borderRadius: 4,
    minHeight: 10,
  },
  barLabel: {
    color: '#9ca3af',
    fontSize: 12,
    marginTop: 8,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  legendText: {
    color: '#9ca3af',
    fontSize: 12,
  },
  pieChartContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  pieItem: {
    width: '48%',
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
    backgroundColor: '#111827',
    padding: 12,
    borderRadius: 8,
  },
  pieColor: {
    width: 16,
    height: 16,
    borderRadius: 4,
    marginRight: 8,
  },
  pieLabel: {
    color: '#9ca3af',
    fontSize: 12,
    flex: 1,
  },
  pieValue: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  reportsContainer: {
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  reportCard: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  typeBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  typeText: {
    fontSize: 10,
    fontWeight: '700',
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  reportName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 8,
  },
  reportDetails: {
    flexDirection: 'row',
    gap: 16,
    marginBottom: 12,
  },
  reportDetail: {
    color: '#9ca3af',
    fontSize: 13,
  },
  reportActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    backgroundColor: '#3b82f6',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  actionButtonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#374151',
  },
  actionButtonText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600',
  },
  actionButtonTextSecondary: {
    color: '#9ca3af',
    fontSize: 14,
    fontWeight: '600',
  },
  generateButton: {
    backgroundColor: '#3b82f6',
    marginHorizontal: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  generateButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
