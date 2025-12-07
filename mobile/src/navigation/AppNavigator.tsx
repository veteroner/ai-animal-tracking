import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { View, Text, StyleSheet } from 'react-native';

// Screens
import HomeScreen from '../screens/HomeScreen';
import CameraScreen from '../screens/CameraScreen';
import GalleryScreen from '../screens/GalleryScreen';
import AlertsScreen from '../screens/AlertsScreen';
import FarmMonitorScreen from '../screens/FarmMonitorScreen';
import ReproductionScreen from '../screens/ReproductionScreen';
import PoultryScreen from '../screens/PoultryScreen';

const Tab = createBottomTabNavigator();

// Tab bar icon component
const TabIcon = ({ name, focused }: { name: string; focused: boolean }) => {
  const icons: Record<string, string> = {
    'Ana Sayfa': '🏠',
    'İzleme': '📡',
    'Kamera': '📷',
    'Hayvanlar': '🐄',
    'Uyarılar': '🔔',
    'Üreme': '💕',
    'Kanatlı': '🐔',
  };

  return (
    <View style={styles.iconContainer}>
      <Text style={[styles.icon, focused && styles.iconFocused]}>
        {icons[name] || '📋'}
      </Text>
    </View>
  );
};

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
          options={{ title: 'AI Hayvan Takip' }}
        />
        <Tab.Screen 
          name="İzleme" 
          component={FarmMonitorScreen}
          options={{ title: 'Çiftlik İzleme' }}
        />
        <Tab.Screen 
          name="Kamera" 
          component={CameraScreen}
          options={{ title: 'Canlı Tespit' }}
        />
        <Tab.Screen 
          name="Hayvanlar" 
          component={GalleryScreen}
          options={{ title: 'Kayıtlı Hayvanlar' }}
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
          name="Uyarılar" 
          component={AlertsScreen}
          options={{ title: 'Uyarılar' }}
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
});
