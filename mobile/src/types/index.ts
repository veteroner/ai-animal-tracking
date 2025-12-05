// Type definitions for the app

export interface DetectedAnimal {
  track_id: number;
  animal_id: string;
  class_name: string;
  bbox: [number, number, number, number]; // [x1, y1, x2, y2]
  confidence: number;
  similarity: number;
  is_new: boolean;
  center: [number, number];
  velocity: [number, number];
  direction: number;
}

export interface ProcessResult {
  frame_id: number;
  timestamp: number;
  fps: number;
  count: number;
  total_registered: number;
  new_this_frame: number;
  animals: DetectedAnimal[];
}

export interface GalleryAnimal {
  animal_id: string;
  class_name: string;
  first_seen: number;
  last_seen: number;
  total_detections: number;
  best_confidence: number;
  metadata: Record<string, any>;
}

export interface GalleryStats {
  total_animals: number;
  by_class: Record<string, number>;
  id_counters: Record<string, number>;
}

export interface GalleryResponse {
  animals: GalleryAnimal[];
  stats: GalleryStats;
}

export interface Alert {
  id: string;
  type: 'sağlık' | 'güvenlik' | 'sistem' | 'aktivite';
  severity: 'düşük' | 'orta' | 'yüksek' | 'kritik';
  title: string;
  message: string;
  animal_id?: string;
  is_read: boolean;
  created_at: string;
}
