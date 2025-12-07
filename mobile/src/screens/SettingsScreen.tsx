import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { API_BASE_URL } from '../config/api';

// Simple storage helper (in production use AsyncStorage)
const storage = {
  data: {} as Record<string, string>,
  async getItem(key: string) { return this.data[key] || null; },
  async setItem(key: string, value: string) { this.data[key] = value; },
  async clear() { this.data = {}; },
};

interface Settings {
  notifications: {
    enabled: boolean;
    alerts: boolean;
    health: boolean;
    feeding: boolean;
    reproduction: boolean;
  };
  display: {
    darkMode: boolean;
    language: string;
    temperatureUnit: string;
  };
  sync: {
    autoSync: boolean;
    syncInterval: number;
  };
  security: {
    biometric: boolean;
    autoLock: boolean;
    lockTimeout: number;
  };
}

const defaultSettings: Settings = {
  notifications: {
    enabled: true,
    alerts: true,
    health: true,
    feeding: true,
    reproduction: true,
  },
  display: {
    darkMode: true,
    language: 'tr',
    temperatureUnit: 'celsius',
  },
  sync: {
    autoSync: true,
    syncInterval: 30,
  },
  security: {
    biometric: false,
    autoLock: false,
    lockTimeout: 5,
  },
};

export default function SettingsScreen() {
  const [settings, setSettings] = useState<Settings>(defaultSettings);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const savedSettings = await storage.getItem('app_settings');
      if (savedSettings) {
        setSettings(JSON.parse(savedSettings));
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async (newSettings: Settings) => {
    try {
      setSaving(true);
      await storage.setItem('app_settings', JSON.stringify(newSettings));
      setSettings(newSettings);
    } catch (error) {
      console.error('Error saving settings:', error);
      Alert.alert('Hata', 'Ayarlar kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (category: keyof Settings, key: string, value: any) => {
    const newSettings = {
      ...settings,
      [category]: {
        ...settings[category],
        [key]: value,
      },
    };
    saveSettings(newSettings);
  };

  const resetSettings = () => {
    Alert.alert(
      'Ayarları Sıfırla',
      'Tüm ayarlar varsayılan değerlere döndürülecek. Emin misiniz?',
      [
        { text: 'İptal', style: 'cancel' },
        { text: 'Sıfırla', style: 'destructive', onPress: () => saveSettings(defaultSettings) },
      ]
    );
  };

  const clearCache = () => {
    Alert.alert(
      'Önbelleği Temizle',
      'Uygulama önbelleği temizlenecek. Emin misiniz?',
      [
        { text: 'İptal', style: 'cancel' },
        { 
          text: 'Temizle', 
          style: 'destructive', 
          onPress: async () => {
            try {
              await storage.clear();
              Alert.alert('Başarılı', 'Önbellek temizlendi');
            } catch (error) {
              Alert.alert('Hata', 'Önbellek temizlenemedi');
            }
          }
        },
      ]
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3b82f6" />
        <Text style={styles.loadingText}>Ayarlar yükleniyor...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Bildirim Ayarları */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔔 Bildirim Ayarları</Text>
        
        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Bildirimleri Etkinleştir</Text>
            <Text style={styles.settingDescription}>Tüm uygulama bildirimleri</Text>
          </View>
          <Switch
            value={settings.notifications.enabled}
            onValueChange={(value) => updateSetting('notifications', 'enabled', value)}
            trackColor={{ false: '#374151', true: '#22c55e' }}
            thumbColor="#ffffff"
          />
        </View>

        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Uyarı Bildirimleri</Text>
            <Text style={styles.settingDescription}>Acil durumlar ve kritik uyarılar</Text>
          </View>
          <Switch
            value={settings.notifications.alerts}
            onValueChange={(value) => updateSetting('notifications', 'alerts', value)}
            trackColor={{ false: '#374151', true: '#22c55e' }}
            thumbColor="#ffffff"
            disabled={!settings.notifications.enabled}
          />
        </View>

        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Sağlık Bildirimleri</Text>
            <Text style={styles.settingDescription}>Veteriner kontrolleri ve tedaviler</Text>
          </View>
          <Switch
            value={settings.notifications.health}
            onValueChange={(value) => updateSetting('notifications', 'health', value)}
            trackColor={{ false: '#374151', true: '#22c55e' }}
            thumbColor="#ffffff"
            disabled={!settings.notifications.enabled}
          />
        </View>

        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Yemleme Bildirimleri</Text>
            <Text style={styles.settingDescription}>Yem takibi ve hatırlatmalar</Text>
          </View>
          <Switch
            value={settings.notifications.feeding}
            onValueChange={(value) => updateSetting('notifications', 'feeding', value)}
            trackColor={{ false: '#374151', true: '#22c55e' }}
            thumbColor="#ffffff"
            disabled={!settings.notifications.enabled}
          />
        </View>

        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Üreme Bildirimleri</Text>
            <Text style={styles.settingDescription}>Kızgınlık ve doğum takibi</Text>
          </View>
          <Switch
            value={settings.notifications.reproduction}
            onValueChange={(value) => updateSetting('notifications', 'reproduction', value)}
            trackColor={{ false: '#374151', true: '#22c55e' }}
            thumbColor="#ffffff"
            disabled={!settings.notifications.enabled}
          />
        </View>
      </View>

      {/* Görünüm Ayarları */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🎨 Görünüm</Text>
        
        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Karanlık Mod</Text>
            <Text style={styles.settingDescription}>Koyu tema kullan</Text>
          </View>
          <Switch
            value={settings.display.darkMode}
            onValueChange={(value) => updateSetting('display', 'darkMode', value)}
            trackColor={{ false: '#374151', true: '#3b82f6' }}
            thumbColor="#ffffff"
          />
        </View>

        <TouchableOpacity style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Dil</Text>
            <Text style={styles.settingDescription}>Uygulama dili</Text>
          </View>
          <View style={styles.settingValue}>
            <Text style={styles.settingValueText}>Türkçe</Text>
            <Text style={styles.chevron}>›</Text>
          </View>
        </TouchableOpacity>

        <TouchableOpacity style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Sıcaklık Birimi</Text>
            <Text style={styles.settingDescription}>Görüntüleme tercihi</Text>
          </View>
          <View style={styles.settingValue}>
            <Text style={styles.settingValueText}>Celsius (°C)</Text>
            <Text style={styles.chevron}>›</Text>
          </View>
        </TouchableOpacity>
      </View>

      {/* Senkronizasyon Ayarları */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔄 Senkronizasyon</Text>
        
        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Otomatik Senkronizasyon</Text>
            <Text style={styles.settingDescription}>Verileri otomatik senkronize et</Text>
          </View>
          <Switch
            value={settings.sync.autoSync}
            onValueChange={(value) => updateSetting('sync', 'autoSync', value)}
            trackColor={{ false: '#374151', true: '#3b82f6' }}
            thumbColor="#ffffff"
          />
        </View>

        <TouchableOpacity style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Senkronizasyon Aralığı</Text>
            <Text style={styles.settingDescription}>Otomatik güncelleme sıklığı</Text>
          </View>
          <View style={styles.settingValue}>
            <Text style={styles.settingValueText}>{settings.sync.syncInterval} dakika</Text>
            <Text style={styles.chevron}>›</Text>
          </View>
        </TouchableOpacity>
      </View>

      {/* Güvenlik Ayarları */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔐 Güvenlik</Text>
        
        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Biyometrik Giriş</Text>
            <Text style={styles.settingDescription}>Parmak izi veya yüz tanıma</Text>
          </View>
          <Switch
            value={settings.security.biometric}
            onValueChange={(value) => updateSetting('security', 'biometric', value)}
            trackColor={{ false: '#374151', true: '#3b82f6' }}
            thumbColor="#ffffff"
          />
        </View>

        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Otomatik Kilitleme</Text>
            <Text style={styles.settingDescription}>Boşta kaldığında kilitle</Text>
          </View>
          <Switch
            value={settings.security.autoLock}
            onValueChange={(value) => updateSetting('security', 'autoLock', value)}
            trackColor={{ false: '#374151', true: '#3b82f6' }}
            thumbColor="#ffffff"
          />
        </View>
      </View>

      {/* Sunucu Ayarları */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🌐 Sunucu</Text>
        
        <View style={styles.serverInfo}>
          <Text style={styles.serverLabel}>API Adresi</Text>
          <Text style={styles.serverValue}>{API_BASE_URL}</Text>
        </View>
      </View>

      {/* Eylemler */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>⚙️ Diğer</Text>
        
        <TouchableOpacity style={styles.actionButton} onPress={clearCache}>
          <Text style={styles.actionButtonText}>🗑️ Önbelleği Temizle</Text>
        </TouchableOpacity>

        <TouchableOpacity style={[styles.actionButton, styles.dangerButton]} onPress={resetSettings}>
          <Text style={[styles.actionButtonText, styles.dangerText]}>🔄 Ayarları Sıfırla</Text>
        </TouchableOpacity>
      </View>

      {/* Uygulama Bilgileri */}
      <View style={styles.appInfo}>
        <Text style={styles.appName}>🐄 Hayvan Takip Sistemi</Text>
        <Text style={styles.appVersion}>Versiyon 1.0.0</Text>
        <Text style={styles.appCopyright}>© 2024 Teknova</Text>
      </View>

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
  section: {
    marginTop: 16,
    marginHorizontal: 16,
    backgroundColor: '#1f2937',
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#374151',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#9ca3af',
    padding: 16,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '500',
  },
  settingDescription: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 2,
  },
  settingValue: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  settingValueText: {
    fontSize: 14,
    color: '#9ca3af',
    marginRight: 8,
  },
  chevron: {
    fontSize: 20,
    color: '#6b7280',
  },
  serverInfo: {
    padding: 16,
  },
  serverLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginBottom: 4,
  },
  serverValue: {
    fontSize: 14,
    color: '#3b82f6',
    fontFamily: 'monospace',
  },
  actionButton: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#374151',
  },
  actionButtonText: {
    fontSize: 16,
    color: '#ffffff',
    textAlign: 'center',
  },
  dangerButton: {
    borderBottomWidth: 0,
  },
  dangerText: {
    color: '#ef4444',
  },
  appInfo: {
    alignItems: 'center',
    padding: 32,
  },
  appName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 8,
  },
  appVersion: {
    fontSize: 14,
    color: '#9ca3af',
    marginBottom: 4,
  },
  appCopyright: {
    fontSize: 12,
    color: '#6b7280',
  },
});
