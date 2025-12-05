import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import { API_BASE_URL, ENDPOINTS } from '../config/api';
import { DetectedAnimal, ProcessResult } from '../types';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const CAMERA_WIDTH = SCREEN_WIDTH;
const CAMERA_HEIGHT = SCREEN_WIDTH * (4 / 3); // 4:3 aspect ratio

export default function CameraScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [facing, setFacing] = useState<CameraType>('back');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<ProcessResult | null>(null);
  const [fps, setFps] = useState(0);
  const [totalRegistered, setTotalRegistered] = useState(0);
  
  const cameraRef = useRef<CameraView>(null);
  const processingRef = useRef(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  if (!permission) {
    return <View style={styles.container} />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionContainer}>
        <Text style={styles.permissionText}>
          Kamera izni gerekli
        </Text>
        <Text style={styles.permissionSubtext}>
          Hayvan tespiti için kamera erişimi gereklidir
        </Text>
        <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
          <Text style={styles.permissionButtonText}>İzin Ver</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const captureAndProcess = async () => {
    if (processingRef.current || !cameraRef.current) return;

    processingRef.current = true;
    setIsProcessing(true);

    try {
      // Fotoğraf çek
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.5,
        base64: true,
        exif: false,
      });

      if (!photo?.base64) {
        processingRef.current = false;
        setIsProcessing(false);
        return;
      }

      // Backend'e gönder
      const formData = new FormData();
      formData.append('file', {
        uri: photo.uri,
        type: 'image/jpeg',
        name: 'frame.jpg',
      } as any);

      const response = await fetch(ENDPOINTS.processFrame, {
        method: 'POST',
        body: formData,
        // Content-Type otomatik ayarlanır (multipart boundary ile)
      });

      if (response.ok) {
        const data: ProcessResult = await response.json();
        setResult(data);
        setFps(data.fps || 0);
        setTotalRegistered(data.total_registered || 0);
      } else {
        console.log('Response not OK:', response.status, await response.text());
      }
    } catch (error) {
      console.log('Processing error:', error);
    } finally {
      processingRef.current = false;
      setIsProcessing(false);
    }
  };

  const toggleCamera = () => {
    if (isRunning) {
      // Durdur
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setIsRunning(false);
    } else {
      // Başlat
      setIsRunning(true);
      // İlk frame'i hemen işle
      captureAndProcess();
      // Sonra interval ile devam et (1 saniyede bir)
      intervalRef.current = setInterval(captureAndProcess, 1000);
    }
  };

  const toggleFacing = () => {
    setFacing(current => (current === 'back' ? 'front' : 'back'));
  };

  const resetGallery = async () => {
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
              await fetch(ENDPOINTS.reset, { method: 'POST' });
              setTotalRegistered(0);
              setResult(null);
              Alert.alert('Başarılı', 'Galeri sıfırlandı');
            } catch (error) {
              Alert.alert('Hata', 'Galeri sıfırlanamadı');
            }
          },
        },
      ]
    );
  };

  // Bbox'ları ekrana çiz
  const renderBoundingBoxes = () => {
    if (!result?.animals) return null;

    return result.animals.map((animal, index) => {
      const [x1, y1, x2, y2] = animal.bbox;
      
      // Koordinatları ekran boyutuna ölçekle
      // Backend 640x480 çözünürlük kullanıyor varsayalım
      const scaleX = CAMERA_WIDTH / 640;
      const scaleY = CAMERA_HEIGHT / 480;
      
      const left = x1 * scaleX;
      const top = y1 * scaleY;
      const width = (x2 - x1) * scaleX;
      const height = (y2 - y1) * scaleY;

      const isNew = animal.is_new;
      const isTemp = animal.animal_id.startsWith('TEMP_');

      return (
        <View
          key={`${animal.track_id}-${index}`}
          style={[
            styles.boundingBox,
            {
              left,
              top,
              width,
              height,
              borderColor: isNew ? '#22c55e' : isTemp ? '#f59e0b' : '#3b82f6',
            },
          ]}
        >
          <View style={[
            styles.labelContainer,
            { backgroundColor: isNew ? '#22c55e' : isTemp ? '#f59e0b' : '#3b82f6' }
          ]}>
            <Text style={styles.labelText}>
              {isTemp ? '...' : animal.animal_id}
            </Text>
            {isNew && <Text style={styles.newBadge}>YENİ</Text>}
          </View>
        </View>
      );
    });
  };

  return (
    <View style={styles.container}>
      {/* Stats Bar */}
      <View style={styles.statsBar}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{result?.count || 0}</Text>
          <Text style={styles.statLabel}>Tespit</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{totalRegistered}</Text>
          <Text style={styles.statLabel}>Kayıtlı</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{fps.toFixed(1)}</Text>
          <Text style={styles.statLabel}>FPS</Text>
        </View>
        <View style={[styles.statItem, styles.statusIndicator]}>
          <View style={[
            styles.statusDot,
            { backgroundColor: isRunning ? '#22c55e' : '#ef4444' }
          ]} />
          <Text style={styles.statLabel}>{isRunning ? 'Aktif' : 'Durduruldu'}</Text>
        </View>
      </View>

      {/* Camera */}
      <View style={styles.cameraContainer}>
        <CameraView
          ref={cameraRef}
          style={styles.camera}
          facing={facing}
        >
          {/* Bounding Boxes */}
          {renderBoundingBoxes()}
          
          {/* Processing Indicator */}
          {isProcessing && (
            <View style={styles.processingOverlay}>
              <Text style={styles.processingText}>İşleniyor...</Text>
            </View>
          )}
        </CameraView>
      </View>

      {/* Detection List */}
      {result?.animals && result.animals.length > 0 && (
        <View style={styles.detectionList}>
          <Text style={styles.detectionTitle}>Tespit Edilen Hayvanlar:</Text>
          {result.animals.slice(0, 3).map((animal, index) => (
            <Text key={index} style={styles.detectionItem}>
              {animal.is_new ? '🆕 ' : '✓ '}
              {animal.animal_id} ({animal.class_name})
            </Text>
          ))}
        </View>
      )}

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity style={styles.controlButton} onPress={toggleFacing}>
          <Text style={styles.controlIcon}>🔄</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.mainButton, isRunning && styles.mainButtonActive]}
          onPress={toggleCamera}
        >
          <Text style={styles.mainButtonText}>
            {isRunning ? '⏹️ Durdur' : '▶️ Başlat'}
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity style={styles.controlButton} onPress={resetGallery}>
          <Text style={styles.controlIcon}>🗑️</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  permissionContainer: {
    flex: 1,
    backgroundColor: '#111827',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  permissionText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 8,
  },
  permissionSubtext: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
    marginBottom: 24,
  },
  permissionButton: {
    backgroundColor: '#22c55e',
    paddingHorizontal: 32,
    paddingVertical: 12,
    borderRadius: 8,
  },
  permissionButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  statsBar: {
    flexDirection: 'row',
    backgroundColor: '#1f2937',
    paddingVertical: 12,
    paddingHorizontal: 16,
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  statLabel: {
    fontSize: 11,
    color: '#9ca3af',
    marginTop: 2,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
  },
  cameraContainer: {
    flex: 1,
    overflow: 'hidden',
  },
  camera: {
    flex: 1,
  },
  boundingBox: {
    position: 'absolute',
    borderWidth: 2,
    borderRadius: 4,
  },
  labelContainer: {
    position: 'absolute',
    top: -24,
    left: -2,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  labelText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: 'bold',
  },
  newBadge: {
    color: '#ffffff',
    fontSize: 9,
    fontWeight: 'bold',
    marginLeft: 4,
    backgroundColor: '#16a34a',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: 3,
  },
  processingOverlay: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(0,0,0,0.7)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  processingText: {
    color: '#ffffff',
    fontSize: 12,
  },
  detectionList: {
    backgroundColor: '#1f2937',
    padding: 12,
  },
  detectionTitle: {
    color: '#9ca3af',
    fontSize: 12,
    marginBottom: 4,
  },
  detectionItem: {
    color: '#ffffff',
    fontSize: 13,
    paddingVertical: 2,
  },
  controls: {
    flexDirection: 'row',
    backgroundColor: '#1f2937',
    padding: 16,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  controlButton: {
    width: 50,
    height: 50,
    backgroundColor: '#374151',
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
  },
  controlIcon: {
    fontSize: 24,
  },
  mainButton: {
    backgroundColor: '#22c55e',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
  },
  mainButtonActive: {
    backgroundColor: '#ef4444',
  },
  mainButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
