// API Configuration
// Backend IP adresini buradan değiştirin

// Geliştirme için localhost
// export const API_BASE_URL = 'http://localhost:8000';

// Aynı ağdaki bilgisayar için IP adresi
export const API_BASE_URL = 'http://172.20.10.3:8000';
export const API_PREFIX = '/api/v1';

// Endpoints
export const ENDPOINTS = {
  // Detection
  processFrame: `${API_BASE_URL}${API_PREFIX}/detection/process-frame`,
  gallery: `${API_BASE_URL}${API_PREFIX}/detection/gallery`,
  reset: `${API_BASE_URL}${API_PREFIX}/detection/reset`,
  
  // Health
  health: `${API_BASE_URL}/health`,
  
  // Animals (Supabase API)
  animals: `${API_BASE_URL}${API_PREFIX}/animals`,
  
  // Alerts
  alerts: `${API_BASE_URL}${API_PREFIX}/alerts`,
};

export default API_BASE_URL;
