import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { API_BASE_URL } from '../config/api';

interface HealthRecord {
  id: number;
  animal_id: number;
  animal_tag: string;
  animal_name?: string;
  check_date: string;
  health_status: string;
  temperature?: number;
  weight?: number;
  symptoms?: string;
  diagnosis?: string;
  treatment?: string;
  notes?: string;
  vet_name?: string;
}

interface HealthStats {
  total_records: number;
  healthy_count: number;
  warning_count: number;
  sick_count: number;
  recent_checkups: number;
}

const statusColors = {
  healthy: { bg: '#dcfce7', text: '#16a34a', label: 'Sağlıklı' },
  warning: { bg: '#fef3c7', text: '#d97706', label: 'Dikkat' },
  sick: { bg: '#fee2e2', text: '#dc2626', label: 'Hasta' },
};

export default function HealthScreen() {
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [stats, setStats] = useState<HealthStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadStats(), loadRecords()]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        // Demo data
        setStats({
          total_records: 48,
          healthy_count: 35,
          warning_count: 8,
          sick_count: 5,
          recent_checkups: 12,
        });
      }
    } catch (error) {
      console.error('Error loading stats:', error);
      setStats({
        total_records: 48,
        healthy_count: 35,
        warning_count: 8,
        sick_count: 5,
        recent_checkups: 12,
      });
    }
  };

  const loadRecords = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health/records`);
      if (response.ok) {
        const data = await response.json();
        setRecords(data);
      } else {
        // Demo data
        setRecords([
          { id: 1, animal_id: 1, animal_tag: 'TR-001', animal_name: 'Sarıkız', check_date: '2024-12-02', health_status: 'healthy', temperature: 38.5, weight: 452, notes: 'Rutin kontrol, sağlık durumu iyi', vet_name: 'Dr. Ahmet Yılmaz' },
          { id: 2, animal_id: 2, animal_tag: 'TR-002', animal_name: 'Karabaş', check_date: '2024-12-01', health_status: 'warning', temperature: 39.8, weight: 518, symptoms: 'Hafif öksürük', diagnosis: 'Üst solunum yolu enfeksiyonu şüphesi', treatment: 'Antibiyotik tedavisi başlandı', vet_name: 'Dr. Ahmet Yılmaz' },
          { id: 3, animal_id: 5, animal_tag: 'TR-005', check_date: '2024-11-30', health_status: 'sick', temperature: 40.2, weight: 68, symptoms: 'İştahsızlık, halsizlik', diagnosis: 'Parazit enfeksiyonu', treatment: 'Antiparaziter ilaç verildi', vet_name: 'Dr. Fatma Demir' },
          { id: 4, animal_id: 3, animal_tag: 'TR-003', animal_name: 'Benekli', check_date: '2024-11-28', health_status: 'healthy', temperature: 38.3, weight: 382, notes: 'Aşı yapıldı', vet_name: 'Dr. Fatma Demir' },
          { id: 5, animal_id: 4, animal_tag: 'TR-004', check_date: '2024-11-25', health_status: 'healthy', temperature: 39.0, weight: 66, notes: 'Genel sağlık kontrolü', vet_name: 'Dr. Ahmet Yılmaz' },
        ]);
      }
    } catch (error) {
      console.error('Error loading records:', error);
      setRecords([
        { id: 1, animal_id: 1, animal_tag: 'TR-001', animal_name: 'Sarıkız', check_date: '2024-12-02', health_status: 'healthy', temperature: 38.5, weight: 452, notes: 'Rutin kontrol' },
      ]);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const filteredRecords = records.filter(record => {
    const matchesSearch = record.animal_tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.animal_name?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || record.health_status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  const getStatusConfig = (status: string) => {
    return statusColors[status as keyof typeof statusColors] || statusColors.healthy;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#22c55e" />
        <Text style={styles.loadingText}>Sağlık kayıtları yükleniyor...</Text>
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
        <View style={[styles.statCard, { backgroundColor: '#dcfce7' }]}>
          <Text style={[styles.statValue, { color: '#16a34a' }]}>{stats?.healthy_count || 0}</Text>
          <Text style={styles.statLabel}>Sağlıklı</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#fef3c7' }]}>
          <Text style={[styles.statValue, { color: '#d97706' }]}>{stats?.warning_count || 0}</Text>
          <Text style={styles.statLabel}>Dikkat</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#fee2e2' }]}>
          <Text style={[styles.statValue, { color: '#dc2626' }]}>{stats?.sick_count || 0}</Text>
          <Text style={styles.statLabel}>Hasta</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#dbeafe' }]}>
          <Text style={[styles.statValue, { color: '#2563eb' }]}>{stats?.recent_checkups || 0}</Text>
          <Text style={styles.statLabel}>Son Kontrol</Text>
        </View>
      </View>

      {/* Arama ve Filtre */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Hayvan ara..."
          placeholderTextColor="#9ca3af"
          value={searchTerm}
          onChangeText={setSearchTerm}
        />
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterContainer}>
        {['all', 'healthy', 'warning', 'sick'].map(status => (
          <TouchableOpacity
            key={status}
            style={[
              styles.filterButton,
              filterStatus === status && styles.filterButtonActive
            ]}
            onPress={() => setFilterStatus(status)}
          >
            <Text style={[
              styles.filterButtonText,
              filterStatus === status && styles.filterButtonTextActive
            ]}>
              {status === 'all' ? 'Tümü' : getStatusConfig(status).label}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Kayıt Listesi */}
      <View style={styles.recordsContainer}>
        <Text style={styles.sectionTitle}>Sağlık Kayıtları ({filteredRecords.length})</Text>
        
        {filteredRecords.map(record => {
          const statusConfig = getStatusConfig(record.health_status);
          return (
            <TouchableOpacity key={record.id} style={styles.recordCard}>
              <View style={styles.recordHeader}>
                <View style={styles.animalInfo}>
                  <Text style={styles.animalTag}>{record.animal_tag}</Text>
                  {record.animal_name && (
                    <Text style={styles.animalName}>{record.animal_name}</Text>
                  )}
                </View>
                <View style={[styles.statusBadge, { backgroundColor: statusConfig.bg }]}>
                  <Text style={[styles.statusText, { color: statusConfig.text }]}>
                    {statusConfig.label}
                  </Text>
                </View>
              </View>

              <View style={styles.recordDetails}>
                <View style={styles.detailRow}>
                  <Text style={styles.detailLabel}>📅 Tarih:</Text>
                  <Text style={styles.detailValue}>{record.check_date}</Text>
                </View>
                {record.temperature && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>🌡️ Sıcaklık:</Text>
                    <Text style={styles.detailValue}>{record.temperature}°C</Text>
                  </View>
                )}
                {record.weight && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>⚖️ Ağırlık:</Text>
                    <Text style={styles.detailValue}>{record.weight} kg</Text>
                  </View>
                )}
                {record.vet_name && (
                  <View style={styles.detailRow}>
                    <Text style={styles.detailLabel}>👨‍⚕️ Veteriner:</Text>
                    <Text style={styles.detailValue}>{record.vet_name}</Text>
                  </View>
                )}
              </View>

              {(record.symptoms || record.diagnosis || record.treatment || record.notes) && (
                <View style={styles.recordNotes}>
                  {record.symptoms && (
                    <Text style={styles.noteText}>💊 Belirtiler: {record.symptoms}</Text>
                  )}
                  {record.diagnosis && (
                    <Text style={styles.noteText}>🔍 Tanı: {record.diagnosis}</Text>
                  )}
                  {record.treatment && (
                    <Text style={styles.noteText}>💉 Tedavi: {record.treatment}</Text>
                  )}
                  {record.notes && (
                    <Text style={styles.noteText}>📝 Not: {record.notes}</Text>
                  )}
                </View>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Yeni Kayıt Ekle Butonu */}
      <TouchableOpacity 
        style={styles.addButton}
        onPress={() => Alert.alert('Bilgi', 'Yeni sağlık kaydı ekleme özelliği yakında eklenecek')}
      >
        <Text style={styles.addButtonText}>+ Yeni Sağlık Kaydı</Text>
      </TouchableOpacity>

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
  searchContainer: {
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  searchInput: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 14,
    color: '#ffffff',
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#374151',
  },
  filterContainer: {
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#1f2937',
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#374151',
  },
  filterButtonActive: {
    backgroundColor: '#22c55e',
    borderColor: '#22c55e',
  },
  filterButtonText: {
    color: '#9ca3af',
    fontSize: 14,
  },
  filterButtonTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
  recordsContainer: {
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  recordCard: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  recordHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  animalInfo: {
    flex: 1,
  },
  animalTag: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  animalName: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  recordDetails: {
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    marginBottom: 4,
  },
  detailLabel: {
    fontSize: 14,
    color: '#9ca3af',
    width: 100,
  },
  detailValue: {
    fontSize: 14,
    color: '#ffffff',
    flex: 1,
  },
  recordNotes: {
    backgroundColor: '#111827',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
  },
  noteText: {
    fontSize: 13,
    color: '#d1d5db',
    marginBottom: 4,
  },
  addButton: {
    backgroundColor: '#22c55e',
    marginHorizontal: 16,
    marginTop: 16,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  addButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});
