import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Platform,
  Dimensions,
  Alert,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { API_BASE_URL } from '../config/api';

interface Zone {
  id: number;
  name: string;
  zone_type: string;
  animal_count: number;
  capacity: number;
  status: string;
  description?: string;
  coordinates: [number, number];
  radius?: number;
}

interface ZoneStats {
  total_zones: number;
  total_animals: number;
  total_capacity: number;
  warnings: number;
}

const zoneTypeConfig: Record<string, { icon: string; label: string; color: string }> = {
  grazing: { icon: '🌾', label: 'Otlak', color: '#22c55e' },
  shelter: { icon: '🏠', label: 'Barınak', color: '#3b82f6' },
  water: { icon: '💧', label: 'Su Kaynağı', color: '#06b6d4' },
  feeding: { icon: '🌾', label: 'Yem Alanı', color: '#f59e0b' },
  restricted: { icon: '⚠️', label: 'Yasak Bölge', color: '#ef4444' },
};

const statusConfig: Record<string, { label: string; color: string }> = {
  normal: { label: 'Normal', color: '#22c55e' },
  warning: { label: 'Dikkat', color: '#eab308' },
  danger: { label: 'Tehlike', color: '#ef4444' },
};

const demoZones: Zone[] = [
  { id: 1, name: 'Ana Otlak', zone_type: 'grazing', animal_count: 45, capacity: 60, status: 'normal', description: 'Günlük otlatma alanı', coordinates: [39.9334, 32.8597], radius: 80 },
  { id: 2, name: 'Ahır 1', zone_type: 'shelter', animal_count: 32, capacity: 40, status: 'normal', description: 'Ana barınak', coordinates: [39.9320, 32.8580], radius: 40 },
  { id: 3, name: 'Ahır 2', zone_type: 'shelter', animal_count: 28, capacity: 30, status: 'warning', description: 'Yavru barınağı', coordinates: [39.9340, 32.8610], radius: 35 },
  { id: 4, name: 'Su Kaynağı', zone_type: 'water', animal_count: 12, capacity: 20, status: 'normal', description: 'Ana su deposu', coordinates: [39.9350, 32.8590], radius: 25 },
  { id: 5, name: 'Yem Deposu', zone_type: 'feeding', animal_count: 8, capacity: 15, status: 'normal', description: 'Yem dağıtım noktası', coordinates: [39.9325, 32.8605], radius: 30 },
  { id: 6, name: 'Tehlikeli Bölge', zone_type: 'restricted', animal_count: 3, capacity: 0, status: 'danger', description: 'Yasak bölge - inşaat alanı', coordinates: [39.9360, 32.8620], radius: 60 },
];

export default function ZonesScreen() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [stats, setStats] = useState<ZoneStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'map' | 'list'>('list');
  const [selectedZone, setSelectedZone] = useState<Zone | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([loadStats(), loadZones()]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/zones/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        const totalAnimals = demoZones.reduce((sum, z) => sum + z.animal_count, 0);
        const totalCapacity = demoZones.reduce((sum, z) => sum + z.capacity, 0);
        const warnings = demoZones.filter(z => z.status !== 'normal').length;
        setStats({
          total_zones: demoZones.length,
          total_animals: totalAnimals,
          total_capacity: totalCapacity,
          warnings,
        });
      }
    } catch (error) {
      const totalAnimals = demoZones.reduce((sum, z) => sum + z.animal_count, 0);
      const totalCapacity = demoZones.reduce((sum, z) => sum + z.capacity, 0);
      const warnings = demoZones.filter(z => z.status !== 'normal').length;
      setStats({
        total_zones: demoZones.length,
        total_animals: totalAnimals,
        total_capacity: totalCapacity,
        warnings,
      });
    }
  };

  const loadZones = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/zones`);
      if (response.ok) {
        const data = await response.json();
        setZones(data);
      } else {
        setZones(demoZones);
      }
    } catch (error) {
      setZones(demoZones);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getZoneTypeConfig = (type: string) => {
    return zoneTypeConfig[type] || zoneTypeConfig.grazing;
  };

  const getStatusConfig = (status: string) => {
    return statusConfig[status] || statusConfig.normal;
  };

  const generateMapHtml = () => {
    const center = zones.length > 0 ? zones[0].coordinates : [39.9334, 32.8597];
    
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <style>
          body { margin: 0; padding: 0; }
          #map { width: 100%; height: 100vh; }
        </style>
      </head>
      <body>
        <div id="map"></div>
        <script>
          var map = L.map('map').setView([${center[0]}, ${center[1]}], 16);
          
          L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
          }).addTo(map);

          var zones = ${JSON.stringify(zones)};
          
          zones.forEach(function(zone) {
            var color = zone.status === 'danger' ? '#ef4444' : 
                       zone.status === 'warning' ? '#eab308' : '#22c55e';
            
            L.circle([zone.coordinates[0], zone.coordinates[1]], {
              color: color,
              fillColor: color,
              fillOpacity: 0.3,
              radius: zone.radius || 50
            }).addTo(map)
            .bindPopup('<b>' + zone.name + '</b><br>' + zone.description);
          });
        </script>
      </body>
      </html>
    `;
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Bölgeler yükleniyor...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* İstatistik Kartları */}
      <ScrollView 
        horizontal 
        showsHorizontalScrollIndicator={false} 
        style={styles.statsScroll}
        contentContainerStyle={styles.statsContainer}
      >
        <View style={[styles.statCard, { backgroundColor: '#dbeafe' }]}>
          <Text style={[styles.statValue, { color: '#2563eb' }]}>{stats?.total_zones || 0}</Text>
          <Text style={styles.statLabel}>Toplam Bölge</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#dcfce7' }]}>
          <Text style={[styles.statValue, { color: '#16a34a' }]}>{stats?.total_animals || 0}</Text>
          <Text style={styles.statLabel}>Hayvan</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#f3e8ff' }]}>
          <Text style={[styles.statValue, { color: '#7c3aed' }]}>{stats?.total_capacity || 0}</Text>
          <Text style={styles.statLabel}>Kapasite</Text>
        </View>
        <View style={[styles.statCard, { backgroundColor: '#fef3c7' }]}>
          <Text style={[styles.statValue, { color: '#d97706' }]}>{stats?.warnings || 0}</Text>
          <Text style={styles.statLabel}>Uyarı</Text>
        </View>
      </ScrollView>

      {/* Tab Seçimi */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'list' && styles.tabButtonActive]}
          onPress={() => setActiveTab('list')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'list' && styles.tabButtonTextActive]}>
            📋 Liste
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabButton, activeTab === 'map' && styles.tabButtonActive]}
          onPress={() => setActiveTab('map')}
        >
          <Text style={[styles.tabButtonText, activeTab === 'map' && styles.tabButtonTextActive]}>
            🗺️ Harita
          </Text>
        </TouchableOpacity>
      </View>

      {activeTab === 'map' ? (
        <View style={styles.mapContainer}>
          <WebView
            source={{ html: generateMapHtml() }}
            style={styles.map}
            scrollEnabled={false}
            javaScriptEnabled={true}
          />
        </View>
      ) : (
        <ScrollView
          style={styles.listContainer}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
          {zones.map(zone => {
            const typeConfig = getZoneTypeConfig(zone.zone_type);
            const status = getStatusConfig(zone.status);
            const occupancy = zone.capacity > 0 ? Math.round((zone.animal_count / zone.capacity) * 100) : 0;

            return (
              <TouchableOpacity 
                key={zone.id} 
                style={styles.zoneCard}
                onPress={() => setSelectedZone(zone)}
              >
                <View style={styles.zoneHeader}>
                  <View style={styles.zoneInfo}>
                    <Text style={styles.zoneIcon}>{typeConfig.icon}</Text>
                    <View>
                      <Text style={styles.zoneName}>{zone.name}</Text>
                      <Text style={[styles.zoneType, { color: typeConfig.color }]}>
                        {typeConfig.label}
                      </Text>
                    </View>
                  </View>
                  <View style={[styles.statusBadge, { backgroundColor: status.color + '20' }]}>
                    <Text style={[styles.statusText, { color: status.color }]}>
                      {status.label}
                    </Text>
                  </View>
                </View>

                {zone.description && (
                  <Text style={styles.zoneDescription}>{zone.description}</Text>
                )}

                <View style={styles.zoneStats}>
                  <View style={styles.zoneStat}>
                    <Text style={styles.zoneStatValue}>{zone.animal_count}</Text>
                    <Text style={styles.zoneStatLabel}>Hayvan</Text>
                  </View>
                  <View style={styles.zoneStat}>
                    <Text style={styles.zoneStatValue}>{zone.capacity}</Text>
                    <Text style={styles.zoneStatLabel}>Kapasite</Text>
                  </View>
                  <View style={styles.zoneStat}>
                    <Text style={[
                      styles.zoneStatValue,
                      { color: occupancy > 90 ? '#ef4444' : occupancy > 70 ? '#eab308' : '#22c55e' }
                    ]}>
                      %{occupancy}
                    </Text>
                    <Text style={styles.zoneStatLabel}>Doluluk</Text>
                  </View>
                </View>

                {/* Doluluk Bar */}
                <View style={styles.progressContainer}>
                  <View style={styles.progressBar}>
                    <View 
                      style={[
                        styles.progressFill, 
                        { 
                          width: `${Math.min(occupancy, 100)}%`,
                          backgroundColor: occupancy > 90 ? '#ef4444' : occupancy > 70 ? '#eab308' : '#22c55e'
                        }
                      ]} 
                    />
                  </View>
                </View>
              </TouchableOpacity>
            );
          })}

          {/* Yeni Bölge Ekle */}
          <TouchableOpacity 
            style={styles.addButton}
            onPress={() => Alert.alert('Bilgi', 'Yeni bölge ekleme özelliği yakında eklenecek')}
          >
            <Text style={styles.addButtonText}>+ Yeni Bölge Ekle</Text>
          </TouchableOpacity>

          <View style={{ height: 100 }} />
        </ScrollView>
      )}
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
  statsScroll: {
    maxHeight: 100,
  },
  statsContainer: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
  },
  statCard: {
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    minWidth: 90,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  statLabel: {
    fontSize: 11,
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
  mapContainer: {
    flex: 1,
    margin: 16,
    borderRadius: 12,
    overflow: 'hidden',
  },
  map: {
    flex: 1,
  },
  listContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  zoneCard: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  zoneHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  zoneInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  zoneIcon: {
    fontSize: 28,
  },
  zoneName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  zoneType: {
    fontSize: 12,
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  zoneDescription: {
    color: '#9ca3af',
    fontSize: 13,
    marginBottom: 12,
  },
  zoneStats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
  },
  zoneStat: {
    alignItems: 'center',
  },
  zoneStatValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  zoneStatLabel: {
    fontSize: 11,
    color: '#9ca3af',
    marginTop: 2,
  },
  progressContainer: {
    marginTop: 4,
  },
  progressBar: {
    height: 6,
    backgroundColor: '#374151',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  addButton: {
    backgroundColor: '#3b82f6',
    marginTop: 8,
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
