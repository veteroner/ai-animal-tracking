import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';

// Screens
import HomeScreen from '../screens/HomeScreen';
import CameraScreen from '../screens/CameraScreen';
import GalleryScreen from '../screens/GalleryScreen';
import AlertsScreen from '../screens/AlertsScreen';
import FarmMonitorScreen from '../screens/FarmMonitorScreen';
import ReproductionScreen from '../screens/ReproductionScreen';
import PoultryScreen from '../screens/PoultryScreen';
import HealthScreen from '../screens/HealthScreen';
import ReportsScreen from '../screens/ReportsScreen';
import ZonesScreen from '../screens/ZonesScreen';
import SettingsScreen from '../screens/SettingsScreen';
import NotificationsScreen from '../screens/NotificationsScreen';

const Tab = createBottomTabNavigator();

// Tab bar icon component
const TabIcon = ({ name, focused }: { name: string; focused: boolean }) => {
  const icons: Record<string, string> = {
    'Ana Sayfa': '🏠',
    'İzleme': '📡',
    'Sağlık': '🏥',
    'Üreme': '💕',
    'Kanatlı': '🐔',
    'Daha Fazla': '📋',
  };

  return (
    <View style={styles.iconContainer}>
      <Text style={[styles.icon, focused && styles.iconFocused]}>
        {icons[name] || '📋'}
      </Text>
    </View>
  );
};

// Daha Fazla Ekranı - Diğer modüllere erişim
function MoreScreen({ navigation }: any) {
  const menuItems = [
    { name: 'Hayvanlar', icon: '🐄', screen: 'Hayvanlar', description: 'Hayvan galerisi ve detayları' },
    { name: 'Kamera', icon: '📷', screen: 'Kamera', description: 'Canlı kamera izleme' },
    { name: 'Bölgeler', icon: '🗺️', screen: 'Bölgeler', description: 'Bölge haritası ve yönetimi' },
    { name: 'Raporlar', icon: '📊', screen: 'Raporlar', description: 'İstatistikler ve raporlar' },
    { name: 'Uyarılar', icon: '⚠️', screen: 'Uyarılar', description: 'Sistem uyarıları' },
    { name: 'Bildirimler', icon: '🔔', screen: 'Bildirimler', description: 'Tüm bildirimler' },
    { name: 'Ayarlar', icon: '⚙️', screen: 'Ayarlar', description: 'Uygulama ayarları' },
  ];

  return (
    <ScrollView style={styles.moreContainer}>
      <Text style={styles.moreTitle}>Tüm Modüller</Text>
      <View style={styles.menuGrid}>
        {menuItems.map((item, index) => (
          <TouchableOpacity
            key={index}
            style={styles.menuItem}
            onPress={() => navigation.navigate(item.screen)}
          >
            <Text style={styles.menuIcon}>{item.icon}</Text>
            <Text style={styles.menuName}>{item.name}</Text>
            <Text style={styles.menuDescription}>{item.description}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          tabBarIcon: ({ focused }) => (
            <TabIcon name={route.name} focused={focused} />
          ),
          tabBarActiveTintColor: '#22c55e',
          tabBarInactiveTintColor: '#6b7280',
          tabBarStyle: styles.tabBar,
          tabBarLabelStyle: styles.tabBarLabel,
          headerStyle: styles.header,
          headerTitleStyle: styles.headerTitle,
          headerTintColor: '#ffffff',
        })}
      >
        <Tab.Screen 
          name="Ana Sayfa" 
          component={HomeScreen}
          options={{ title: 'Ana Sayfa' }}
        />
        <Tab.Screen 
          name="İzleme" 
          component={FarmMonitorScreen}
          options={{ title: 'Çiftlik İzleme' }}
        />
        <Tab.Screen 
          name="Sağlık" 
          component={HealthScreen}
          options={{ title: 'Sağlık Takibi' }}
        />
        <Tab.Screen 
          name="Üreme" 
          component={ReproductionScreen}
          options={{ title: 'Üreme Takibi' }}
        />
        <Tab.Screen 
          name="Kanatlı" 
          component={PoultryScreen}
          options={{ title: 'Kanatlı Modülü' }}
        />
        <Tab.Screen 
          name="Daha Fazla" 
          component={MoreScreen}
          options={{ title: 'Daha Fazla' }}
        />
        {/* Hidden screens accessible from More */}
        <Tab.Screen 
          name="Hayvanlar" 
          component={GalleryScreen}
          options={{ 
            title: 'Hayvan Galerisi',
            tabBarButton: () => null,
          }}
        />
        <Tab.Screen 
          name="Kamera" 
          component={CameraScreen}
          options={{ 
            title: 'Canlı Kamera',
            tabBarButton: () => null,
          }}
        />
        <Tab.Screen 
          name="Bölgeler" 
          component={ZonesScreen}
          options={{ 
            title: 'Bölge Haritası',
            tabBarButton: () => null,
          }}
        />
        <Tab.Screen 
          name="Raporlar" 
          component={ReportsScreen}
          options={{ 
            title: 'Raporlar',
            tabBarButton: () => null,
          }}
        />
        <Tab.Screen 
          name="Uyarılar" 
          component={AlertsScreen}
          options={{ 
            title: 'Uyarılar',
            tabBarButton: () => null,
          }}
        />
        <Tab.Screen 
          name="Bildirimler" 
          component={NotificationsScreen}
          options={{ 
            title: 'Bildirimler',
            tabBarButton: () => null,
          }}
        />
        <Tab.Screen 
          name="Ayarlar" 
          component={SettingsScreen}
          options={{ 
            title: 'Ayarlar',
            tabBarButton: () => null,
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  tabBar: {
    backgroundColor: '#1f2937',
    borderTopColor: '#374151',
    borderTopWidth: 1,
    height: 60,
    paddingBottom: 8,
    paddingTop: 8,
  },
  tabBarLabel: {
    fontSize: 11,
    fontWeight: '600',
  },
  header: {
    backgroundColor: '#111827',
  },
  headerTitle: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 18,
  },
  iconContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: 22,
  },
  iconFocused: {
    transform: [{ scale: 1.1 }],
  },
  // More Screen Styles
  moreContainer: {
    flex: 1,
    backgroundColor: '#111827',
    padding: 16,
  },
  moreTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 20,
  },
  menuGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  menuItem: {
    width: '48%',
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#374151',
  },
  menuIcon: {
    fontSize: 32,
    marginBottom: 8,
  },
  menuName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  menuDescription: {
    fontSize: 12,
    color: '#9ca3af',
  },
});
