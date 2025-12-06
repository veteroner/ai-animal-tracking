import axios from 'axios';

// Local network - telefondan da erişilebilir
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://172.20.10.3:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Animal {
  id: number;
  tag_id: string;
  name?: string;
  species: string;
  breed?: string;
  birth_date?: string;
  gender: string;
  weight?: number;
  health_status: string;
  zone_id?: number;
  created_at: string;
}

export interface HealthRecord {
  id: number;
  animal_id: number;
  check_date: string;
  health_status: string;
  temperature?: number;
  weight?: number;
  symptoms?: string;
  diagnosis?: string;
  treatment?: string;
  notes?: string;
}

export interface Alert {
  id: number;
  animal_id?: number;
  alert_type: string;
  severity: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface Zone {
  id: number;
  name: string;
  zone_type: string;
  coordinates?: string;
  capacity?: number;
  animal_count?: number;
}

export interface SystemStats {
  total_animals: number;
  healthy_animals: number;
  sick_animals: number;
  warning_animals: number;
  active_cameras: number;
  unread_alerts: number;
  total_zones: number;
}

export interface Detection {
  id: number;
  animal_id?: number;
  detection_time: string;
  confidence: number;
  bbox: string;
  class_name: string;
  camera_id?: number;
}

// Poultry Types
export interface Poultry {
  id: number;
  tag_id: string;
  name?: string;
  poultry_type: string;
  breed?: string;
  hatch_date?: string;
  gender: string;
  weight?: number;
  health_status: string;
  coop_id?: number;
}

export interface EggProduction {
  id: number;
  poultry_id?: number;
  coop_id: number;
  collection_date: string;
  quantity: number;
  quality: string;
  weight_avg?: number;
  notes?: string;
}

// API Functions

// Animals
export const getAnimals = () => api.get<Animal[]>('/api/animals');
export const getAnimal = (id: number) => api.get<Animal>(`/api/animals/${id}`);
export const createAnimal = (data: Partial<Animal>) => api.post<Animal>('/api/animals', data);
export const updateAnimal = (id: number, data: Partial<Animal>) => api.put<Animal>(`/api/animals/${id}`, data);
export const deleteAnimal = (id: number) => api.delete(`/api/animals/${id}`);

// Health Records
export const getHealthRecords = (animalId?: number) => {
  const url = animalId ? `/api/health?animal_id=${animalId}` : '/api/health';
  return api.get<HealthRecord[]>(url);
};
export const createHealthRecord = (data: Partial<HealthRecord>) => api.post<HealthRecord>('/api/health', data);

// Alerts
export const getAlerts = (unreadOnly?: boolean) => {
  const url = unreadOnly ? '/api/alerts?unread=true' : '/api/alerts';
  return api.get<Alert[]>(url);
};
export const markAlertRead = (id: number) => api.put(`/api/alerts/${id}/read`);
export const deleteAlert = (id: number) => api.delete(`/api/alerts/${id}`);

// Zones
export const getZones = () => api.get<Zone[]>('/api/zones');
export const getZone = (id: number) => api.get<Zone>(`/api/zones/${id}`);
export const createZone = (data: Partial<Zone>) => api.post<Zone>('/api/zones', data);

// Stats
export const getSystemStats = () => api.get<SystemStats>('/api/stats');
export const getDailyStats = (days?: number) => {
  const url = days ? `/api/stats/daily?days=${days}` : '/api/stats/daily';
  return api.get(url);
};

// Detections
export const getRecentDetections = (limit?: number) => {
  const url = limit ? `/api/detections?limit=${limit}` : '/api/detections';
  return api.get<Detection[]>(url);
};

// Poultry
export const getPoultry = () => api.get<Poultry[]>('/api/poultry');
export const getPoultryById = (id: number) => api.get<Poultry>(`/api/poultry/${id}`);
export const createPoultry = (data: Partial<Poultry>) => api.post<Poultry>('/api/poultry', data);
export const updatePoultry = (id: number, data: Partial<Poultry>) => api.put<Poultry>(`/api/poultry/${id}`, data);

// Egg Production
export const getEggProduction = (days?: number) => {
  const url = days ? `/api/eggs?days=${days}` : '/api/eggs';
  return api.get<EggProduction[]>(url);
};
export const recordEggProduction = (data: Partial<EggProduction>) => api.post<EggProduction>('/api/eggs', data);
export const getEggStats = () => api.get('/api/eggs/stats');

// Camera Stream
export const getCameraStreamUrl = (cameraId: number = 0) => `${API_URL}/api/camera/stream/${cameraId}`;

// WebSocket for real-time updates
export const createWebSocket = (path: string) => {
  const wsUrl = API_URL.replace('http', 'ws');
  return new WebSocket(`${wsUrl}${path}`);
};

export default api;
