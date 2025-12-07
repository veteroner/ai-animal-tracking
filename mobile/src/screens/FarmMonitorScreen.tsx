import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { API_BASE_URL } from '../config/api';

interface CameraInfo {
  id: string;
  name: string;
  url: string;
  status: 'active' | 'inactive' | 'error';
  fps: number;
  total_frames: number;
  animals_detected: number;
  events_count: number;
}

interface MonitorStatus {
  is_running: boolean;
  cameras_count: number;
  active_cameras: number;
  total_detections: number;
  events_today: number;
  uptime_seconds: number;
  cameras: CameraInfo[];
}

export default function FarmMonitorScreen() {
  const [status, setStatus] = useState<MonitorStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCameraName, setNewCameraName] = useState('');
  const [newCameraUrl, setNewCameraUrl] = useState('');
  const [addingCamera, setAddingCamera] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/farm-monitor/status`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Error fetching status:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchStatus();
    setRefreshing(false);
  };

  const handleAddCamera = async () => {
    if (!newCameraName || !newCameraUrl) {
      Alert.alert('Hata', 'Lütfen kamera adı ve URL girin');
      return;
    }

    setAddingCamera(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/farm-monitor/cameras`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newCameraName,
          url: newCameraUrl,
          auto_start: true,
        }),
      });

      if (response.ok) {
        setNewCameraName('');
        setNewCameraUrl('');
        setShowAddForm(false);
        fetchStatus();
        Alert.alert('Başarılı', 'Kamera eklendi');
      } else {
        Alert.alert('Hata', 'Kamera eklenemedi');
      }
    } catch (error) {
      Alert.alert('Hata', 'Bağlantı hatası');
    } finally {
      setAddingCamera(false);
    }
  };

  const handleRemoveCamera = (cameraId: string, cameraName: string) => {
    Alert.alert(
      'Kamerayı Sil',
      `"${cameraName}" kamerasını silmek istediğinize emin misiniz?`,
      [
        { text: 'İptal', style: 'cancel' },
        {
          text: 'Sil',
          style: 'destructive',
          onPress: async () => {
            try {
              await fetch(`${API_BASE_URL}/api/v1/farm-monitor/cameras/${cameraId}`, {
                method: 'DELETE',
              });
              fetchStatus();
            } catch (error) {
              Alert.alert('Hata', 'Kamera silinemedi');
            }
          },
        },
      ]
    );
  };

  const handleStartMonitoring = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/farm-monitor/start`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchStatus();
        Alert.alert('Başarılı', 'İzleme başlatıldı');
      }
    } catch (error) {
      Alert.alert('Hata', 'İzleme başlatılamadı');
    }
  };

  const handleStopMonitoring = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/farm-monitor/stop`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchStatus();
        Alert.alert('Durduruldu', 'İzleme durduruldu');
      }
    } catch (error) {
      Alert.alert('Hata', 'İzleme durdurulamadı');
    }
  };

  const getStatusColor = (cameraStatus: string) => {
    switch (cameraStatus) {
      case 'active':
        return '#22c55e';
      case 'inactive':
        return '#6b7280';
      case 'error':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
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
        <Text style={styles.title}>🏠 Çiftlik İzleme</Text>
        <Text style={styles.subtitle}>IP kameralarınızı 7/24 AI ile izleyin</Text>
      </View>

      {/* Status Cards */}
      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: status?.is_running ? '#22c55e' : '#6b7280' }]}>
          <Text style={styles.statIcon}>{status?.is_running ? '🟢' : '⏸️'}</Text>
          <Text style={styles.statValue}>{status?.is_running ? 'Aktif' : 'Durduruldu'}</Text>
          <Text style={styles.statLabel}>Durum</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#3b82f6' }]}>
          <Text style={styles.statIcon}>📷</Text>
          <Text style={styles.statValue}>{status?.active_cameras || 0}/{status?.cameras_count || 0}</Text>
          <Text style={styles.statLabel}>Kameralar</Text>
        </View>
      </View>

      <View style={styles.statsRow}>
        <View style={[styles.statCard, { backgroundColor: '#8b5cf6' }]}>
          <Text style={styles.statIcon}>🐄</Text>
          <Text style={styles.statValue}>{status?.total_detections?.toLocaleString() || 0}</Text>
          <Text style={styles.statLabel}>Tespit</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#f59e0b' }]}>
          <Text style={styles.statIcon}>⚠️</Text>
          <Text style={styles.statValue}>{status?.events_today || 0}</Text>
          <Text style={styles.statLabel}>Bugünkü Olay</Text>
        </View>
      </View>

      {/* Control Buttons */}
      <View style={styles.controlButtons}>
        {status?.is_running ? (
          <TouchableOpacity style={[styles.controlButton, styles.stopButton]} onPress={handleStopMonitoring}>
            <Text style={styles.controlButtonText}>⏹️ İzlemeyi Durdur</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity style={[styles.controlButton, styles.startButton]} onPress={handleStartMonitoring}>
            <Text style={styles.controlButtonText}>▶️ İzlemeyi Başlat</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Cameras Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>📷 Kameralar</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setShowAddForm(!showAddForm)}
          >
            <Text style={styles.addButtonText}>{showAddForm ? '✕' : '+'} Ekle</Text>
          </TouchableOpacity>
        </View>

        {/* Add Camera Form */}
        {showAddForm && (
          <View style={styles.addForm}>
            <TextInput
              style={styles.input}
              placeholder="Kamera Adı"
              placeholderTextColor="#9ca3af"
              value={newCameraName}
              onChangeText={setNewCameraName}
            />
            <TextInput
              style={styles.input}
              placeholder="rtsp://kullanici:sifre@192.168.1.100:554/stream"
              placeholderTextColor="#9ca3af"
              value={newCameraUrl}
              onChangeText={setNewCameraUrl}
              autoCapitalize="none"
            />
            <View style={styles.formButtons}>
              <TouchableOpacity
                style={[styles.formButton, styles.cancelButton]}
                onPress={() => setShowAddForm(false)}
              >
                <Text style={styles.formButtonText}>İptal</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.formButton, styles.submitButton]}
                onPress={handleAddCamera}
                disabled={addingCamera}
              >
                {addingCamera ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.formButtonText}>Ekle</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        )}

        {/* Camera List */}
        {status?.cameras && status.cameras.length > 0 ? (
          status.cameras.map((camera) => (
            <View key={camera.id} style={styles.cameraCard}>
              <View style={styles.cameraHeader}>
                <View style={[styles.statusDot, { backgroundColor: getStatusColor(camera.status) }]} />
                <Text style={styles.cameraName}>{camera.name}</Text>
                <TouchableOpacity
                  onPress={() => handleRemoveCamera(camera.id, camera.name)}
                  style={styles.deleteButton}
                >
                  <Text style={styles.deleteButtonText}>🗑️</Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.cameraUrl} numberOfLines={1}>{camera.url}</Text>
              <View style={styles.cameraStats}>
                <Text style={styles.cameraStat}>FPS: {camera.fps}</Text>
                <Text style={styles.cameraStat}>Kare: {camera.total_frames}</Text>
                <Text style={styles.cameraStat}>Hayvan: {camera.animals_detected}</Text>
              </View>
            </View>
          ))
        ) : (
          <View style={styles.emptyState}>
            <Text style={styles.emptyIcon}>📷</Text>
            <Text style={styles.emptyText}>Henüz kamera eklenmemiş</Text>
            <Text style={styles.emptySubtext}>Yukarıdaki "Ekle" butonunu kullanın</Text>
          </View>
        )}
      </View>

      {/* AI Features */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🧠 Yapay Zeka Özellikleri</Text>
        <View style={styles.featureList}>
          {[
            '✅ Hayvan Tespiti (YOLOv8)',
            '✅ Otomatik ID Atama (Re-ID)',
            '✅ Davranış Analizi',
            '✅ Sağlık İzleme',
            '✅ Kızgınlık Tespiti',
            '✅ Doğum Algılama',
          ].map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <Text style={styles.featureText}>{feature}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* URL Examples */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📌 Örnek URL Formatları</Text>
        <View style={styles.exampleCard}>
          <Text style={styles.exampleLabel}>RTSP (IP Kamera)</Text>
          <Text style={styles.exampleUrl}>rtsp://admin:password@192.168.1.100:554/stream1</Text>
        </View>
        <View style={styles.exampleCard}>
          <Text style={styles.exampleLabel}>HTTP Stream</Text>
          <Text style={styles.exampleUrl}>http://192.168.1.100:8080/video</Text>
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
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.8)',
    marginTop: 2,
  },
  controlButtons: {
    marginBottom: 20,
  },
  controlButton: {
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  startButton: {
    backgroundColor: '#22c55e',
  },
  stopButton: {
    backgroundColor: '#ef4444',
  },
  controlButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  section: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  addButton: {
    backgroundColor: '#3b82f6',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  addButtonText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  addForm: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  input: {
    backgroundColor: '#1f2937',
    borderRadius: 8,
    padding: 12,
    color: '#ffffff',
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#4b5563',
  },
  formButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  formButton: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#4b5563',
  },
  submitButton: {
    backgroundColor: '#22c55e',
  },
  formButtonText: {
    color: '#ffffff',
    fontWeight: '600',
  },
  cameraCard: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  cameraHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginRight: 8,
  },
  cameraName: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  deleteButton: {
    padding: 4,
  },
  deleteButtonText: {
    fontSize: 18,
  },
  cameraUrl: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
  },
  cameraStats: {
    flexDirection: 'row',
    marginTop: 8,
    gap: 16,
  },
  cameraStat: {
    fontSize: 12,
    color: '#6b7280',
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
  emptySubtext: {
    color: '#6b7280',
    fontSize: 14,
    marginTop: 4,
  },
  featureList: {
    gap: 8,
  },
  featureItem: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
  },
  featureText: {
    color: '#ffffff',
    fontSize: 14,
  },
  exampleCard: {
    backgroundColor: '#374151',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  exampleLabel: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 4,
  },
  exampleUrl: {
    color: '#60a5fa',
    fontSize: 12,
    fontFamily: 'monospace',
  },
});
