'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

// Leaflet CSS'i client-side'da import et
import 'leaflet/dist/leaflet.css';

interface Zone {
  id: number;
  name: string;
  zone_type: string;
  animal_count: number;
  capacity: number;
  status: 'normal' | 'warning' | 'danger';
  coordinates: [number, number];
  radius?: number;
}

interface ZoneMapProps {
  zones: Zone[];
  center?: [number, number];
  zoom?: number;
  showUserLocation?: boolean;
  onUserLocationFound?: (lat: number, lng: number) => void;
}

const zoneColors = {
  normal: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
};

const zoneTypeColors = {
  grazing: '#22c55e',
  shelter: '#3b82f6',
  water: '#06b6d4',
  feeding: '#f59e0b',
  restricted: '#ef4444',
};

function ZoneMapComponent({ zones, center = [39.9334, 32.8597], zoom = 15, showUserLocation = true, onUserLocationFound }: ZoneMapProps) {
  const [mapReady, setMapReady] = useState(false);
  const [L, setL] = useState<typeof import('leaflet') | null>(null);
  const [MapComponents, setMapComponents] = useState<{
    MapContainer: any;
    TileLayer: any;
    Circle: any;
    Popup: any;
    Marker: any;
    useMap: any;
  } | null>(null);
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>(center);

  // Kullanıcı konumunu al
  useEffect(() => {
    if (showUserLocation && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation([latitude, longitude]);
          setMapCenter([latitude, longitude]);
          if (onUserLocationFound) {
            onUserLocationFound(latitude, longitude);
          }
        },
        (error) => {
          console.error('Konum alınamadı:', error);
          setLocationError('Konum alınamadı. Lütfen konum iznini kontrol edin.');
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 0
        }
      );
    }
  }, [showUserLocation, onUserLocationFound]);

  useEffect(() => {
    // Leaflet'i client-side'da dinamik olarak yükle
    const loadLeaflet = async () => {
      const leaflet = await import('leaflet');
      const reactLeaflet = await import('react-leaflet');
      
      // Fix for default marker icons
      delete (leaflet.Icon.Default.prototype as any)._getIconUrl;
      leaflet.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
      });
      
      setL(leaflet);
      setMapComponents({
        MapContainer: reactLeaflet.MapContainer,
        TileLayer: reactLeaflet.TileLayer,
        Circle: reactLeaflet.Circle,
        Popup: reactLeaflet.Popup,
        Marker: reactLeaflet.Marker,
        useMap: reactLeaflet.useMap,
      });
      setMapReady(true);
    };

    loadLeaflet();
  }, []);

  if (!mapReady || !MapComponents || !L) {
    return (
      <div className="aspect-video bg-gray-100 rounded-xl flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-gray-500">Harita yükleniyor...</p>
        </div>
      </div>
    );
  }

  const { MapContainer, TileLayer, Circle, Popup, Marker } = MapComponents;

  // Kullanıcı konumu için özel ikon
  const userIcon = L.divIcon({
    className: 'user-location-marker',
    html: `
      <div style="
        width: 24px;
        height: 24px;
        background: #3b82f6;
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.5);
        position: relative;
      ">
        <div style="
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 8px;
          height: 8px;
          background: white;
          border-radius: 50%;
        "></div>
      </div>
      <div style="
        position: absolute;
        top: -4px;
        left: -4px;
        width: 32px;
        height: 32px;
        background: rgba(59, 130, 246, 0.2);
        border-radius: 50%;
        animation: pulse 2s infinite;
      "></div>
      <style>
        @keyframes pulse {
          0% { transform: scale(1); opacity: 1; }
          100% { transform: scale(2); opacity: 0; }
        }
      </style>
    `,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
  });

  return (
    <div className="relative">
      {locationError && (
        <div className="absolute top-2 left-2 right-2 z-[1000] bg-yellow-50 text-yellow-800 px-3 py-2 rounded-lg text-sm">
          ⚠️ {locationError}
        </div>
      )}
      {userLocation && (
        <div className="absolute top-2 right-2 z-[1000] bg-blue-50 text-blue-800 px-3 py-2 rounded-lg text-sm">
          📍 Konumunuz: {userLocation[0].toFixed(4)}, {userLocation[1].toFixed(4)}
        </div>
      )}
      <MapContainer
        center={mapCenter}
        zoom={userLocation ? 17 : zoom}
        style={{ height: '400px', width: '100%', borderRadius: '12px' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Kullanıcı Konumu */}
        {userLocation && (
          <>
            <Marker position={userLocation} icon={userIcon}>
              <Popup>
                <div className="p-2 text-center">
                  <h3 className="font-semibold text-blue-600">📍 Konumunuz</h3>
                  <p className="text-sm text-gray-600">
                    {userLocation[0].toFixed(6)}, {userLocation[1].toFixed(6)}
                  </p>
                </div>
              </Popup>
            </Marker>
            {/* Kullanıcı konumu doğruluk çemberi */}
            <Circle
              center={userLocation}
              radius={30}
              pathOptions={{
                color: '#3b82f6',
                fillColor: '#3b82f6',
                fillOpacity: 0.1,
                weight: 1,
                dashArray: '5, 5',
              }}
            />
          </>
        )}
        
        {/* Bölgeler */}
        {zones.map((zone) => {
          const color = zoneTypeColors[zone.zone_type as keyof typeof zoneTypeColors] || zoneColors[zone.status];
          
          return (
            <Circle
              key={zone.id}
              center={zone.coordinates}
              radius={zone.radius || 50}
              pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.3,
                weight: 2,
              }}
            >
              <Popup>
                <div className="p-2">
                  <h3 className="font-semibold text-gray-900">{zone.name}</h3>
                  <p className="text-sm text-gray-600">Hayvan: {zone.animal_count} / {zone.capacity}</p>
                  <p className="text-sm text-gray-600">Durum: {zone.status === 'normal' ? 'Normal' : zone.status === 'warning' ? 'Dikkat' : 'Tehlike'}</p>
                </div>
              </Popup>
            </Circle>
          );
        })}
      </MapContainer>
    </div>
  );
}

// SSR'ı devre dışı bırak
export default dynamic(() => Promise.resolve(ZoneMapComponent), {
  ssr: false,
  loading: () => (
    <div className="aspect-video bg-gray-100 rounded-xl flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
        <p className="text-gray-500">Harita yükleniyor...</p>
      </div>
    </div>
  ),
});
