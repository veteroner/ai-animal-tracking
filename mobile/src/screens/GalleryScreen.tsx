import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { API_BASE_URL } from '../config/api';
import { GalleryAnimal, GalleryStats } from '../types';

export default function GalleryScreen() {
  const [animals, setAnimals] = useState<GalleryAnimal[]>([]);
  const [stats, setStats] = useState<GalleryStats | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchGallery = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/gallery`);
      if (response.ok) {
        const data = await response.json();
        setAnimals(data.animals || []);
        setStats(data.stats);
      }
    } catch (error) {
      console.log('Gallery fetch error:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchGallery();
    setRefreshing(false);
  };

  useEffect(() => {
    fetchGallery();
    const interval = setInterval(fetchGallery, 5000); // 5 saniyede bir güncelle
    return () => clearInterval(interval);
  }, [fetchGallery]);

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getClassEmoji = (className: string) => {
    const emojis: Record<string, string> = {
      cow: '🐄',
      cattle: '🐄',
      sheep: '🐑',
      goat: '🐐',
      horse: '🐴',
      dog: '🐕',
      cat: '🐱',
      bird: '🐦',
      chicken: '🐔',
      turkey: '🦃',
      duck: '🦆',
      elephant: '🐘',
      bear: '🐻',
      zebra: '🦓',
      giraffe: '🦒',
    };
    return emojis[className.toLowerCase()] || '🐾';
  };

  const resetGallery = () => {
    Alert.alert(
      'Galeriyi Sıfırla',
      'Tüm kayıtlı hayvanlar silinecek. Emin misiniz?',
      [
        { text: 'İptal', style: 'cancel' },
        {
          text: 'Sıfırla',
          style: 'destructive',
          onPress: async () => {
            try {
              await fetch(`${API_BASE_URL}/reset`, { method: 'POST' });
              setAnimals([]);
              setStats(null);
              Alert.alert('Başarılı', 'Galeri sıfırlandı');
            } catch (error) {
              Alert.alert('Hata', 'Galeri sıfırlanamadı');
            }
          },
        },
      ]
    );
  };

  const renderAnimal = ({ item }: { item: GalleryAnimal }) => (
    <View style={styles.animalCard}>
      <View style={styles.animalHeader}>
        <Text style={styles.animalEmoji}>{getClassEmoji(item.class_name)}</Text>
        <View style={styles.animalInfo}>
          <Text style={styles.animalId}>{item.animal_id}</Text>
          <Text style={styles.animalClass}>{item.class_name}</Text>
        </View>
        <View style={styles.confidenceBadge}>
          <Text style={styles.confidenceText}>
            %{(item.best_confidence * 100).toFixed(0)}
          </Text>
        </View>
      </View>
      
      <View style={styles.animalDetails}>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>İlk Görülme:</Text>
          <Text style={styles.detailValue}>{formatDate(item.first_seen)}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Son Görülme:</Text>
          <Text style={styles.detailValue}>{formatDate(item.last_seen)}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Toplam Tespit:</Text>
          <Text style={styles.detailValue}>{item.total_detections} kez</Text>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Stats Header */}
      {stats && (
        <View style={styles.statsHeader}>
          <View style={styles.statBox}>
            <Text style={styles.statNumber}>{stats.total_animals}</Text>
            <Text style={styles.statLabel}>Toplam</Text>
          </View>
          {Object.entries(stats.by_class).slice(0, 3).map(([cls, count]) => (
            <View key={cls} style={styles.statBox}>
              <Text style={styles.statNumber}>{count}</Text>
              <Text style={styles.statLabel}>{cls}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Reset Button */}
      <TouchableOpacity style={styles.resetButton} onPress={resetGallery}>
        <Text style={styles.resetButtonText}>🗑️ Galeriyi Sıfırla</Text>
      </TouchableOpacity>

      {/* Animal List */}
      <FlatList
        data={animals}
        keyExtractor={(item) => item.animal_id}
        renderItem={renderAnimal}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>📭</Text>
            <Text style={styles.emptyText}>
              {loading ? 'Yükleniyor...' : 'Henüz kayıtlı hayvan yok'}
            </Text>
            <Text style={styles.emptySubtext}>
              Kamera sekmesinden hayvan tespiti yapın
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
  statsHeader: {
    flexDirection: 'row',
    backgroundColor: '#1f2937',
    padding: 12,
    justifyContent: 'space-around',
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  statBox: {
    alignItems: 'center',
    minWidth: 60,
  },
  statNumber: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#22c55e',
  },
  statLabel: {
    fontSize: 11,
    color: '#9ca3af',
    marginTop: 2,
    textTransform: 'capitalize',
  },
  resetButton: {
    backgroundColor: '#374151',
    margin: 12,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  resetButtonText: {
    color: '#f87171',
    fontSize: 14,
    fontWeight: '600',
  },
  listContent: {
    padding: 12,
    paddingTop: 0,
  },
  animalCard: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#22c55e',
  },
  animalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  animalEmoji: {
    fontSize: 36,
    marginRight: 12,
  },
  animalInfo: {
    flex: 1,
  },
  animalId: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  animalClass: {
    fontSize: 13,
    color: '#9ca3af',
    textTransform: 'capitalize',
    marginTop: 2,
  },
  confidenceBadge: {
    backgroundColor: '#22c55e',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  confidenceText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  animalDetails: {
    backgroundColor: '#111827',
    borderRadius: 8,
    padding: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  detailLabel: {
    fontSize: 13,
    color: '#9ca3af',
  },
  detailValue: {
    fontSize: 13,
    color: '#ffffff',
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
