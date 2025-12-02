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

function ZoneMapComponent({ zones, center = [39.9334, 32.8597], zoom = 15 }: ZoneMapProps) {
  const [mapReady, setMapReady] = useState(false);
  const [L, setL] = useState<typeof import('leaflet') | null>(null);
  const [MapComponents, setMapComponents] = useState<{
    MapContainer: any;
    TileLayer: any;
    Circle: any;
    Popup: any;
    Marker: any;
  } | null>(null);

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

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height: '400px', width: '100%', borderRadius: '12px' }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
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
