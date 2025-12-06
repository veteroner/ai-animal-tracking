import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Use real URL from env, or a valid placeholder for build time
const getSupabaseUrl = (): string => {
  const envUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (envUrl && envUrl.startsWith('https://') && envUrl.includes('.supabase.co')) {
    return envUrl;
  }
  // Valid placeholder URL for build time - will be replaced at runtime
  return 'https://placeholder.supabase.co';
};

const getSupabaseKey = (): string => {
  return process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBsYWNlaG9sZGVyIiwicm9sZSI6ImFub24iLCJpYXQiOjE2NDI0MDU2MDAsImV4cCI6MTk1Nzk4MTYwMH0.placeholder-key-for-build';
};

const supabaseUrl = getSupabaseUrl();
const supabaseAnonKey = getSupabaseKey();

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseAnonKey);

// Check if we have real credentials (not placeholder)
export const isSupabaseConfigured = (): boolean => {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || '';
  return url !== '' && 
         url.startsWith('https://') && 
         url.includes('.supabase.co') && 
         !url.includes('placeholder') &&
         !url.includes('example');
};

// Types
export interface Animal {
  id: string;
  name: string;
  tag: string;
  type: string;
  breed: string;
  gender: 'erkek' | 'dişi';
  birth_date: string;
  weight: number;
  status: 'sağlıklı' | 'hasta' | 'tedavide' | 'karantina';
  zone_id: string;
  image_url?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Zone {
  id: string;
  name: string;
  type: 'otlak' | 'ahır' | 'karantina' | 'sulak';
  coordinates: { lat: number; lng: number }[];
  capacity: number;
  current_count: number;
  color: string;
  created_at: string;
}

export interface HealthRecord {
  id: string;
  animal_id: string;
  type: 'muayene' | 'aşı' | 'tedavi' | 'kontrol';
  description: string;
  vet_name: string;
  result: string;
  date: string;
  created_at: string;
}

export interface Alert {
  id: string;
  type: 'sağlık' | 'güvenlik' | 'sistem' | 'aktivite';
  severity: 'düşük' | 'orta' | 'yüksek' | 'kritik';
  title: string;
  message: string;
  animal_id?: string;
  zone_id?: string;
  is_read: boolean;
  created_at: string;
}

export interface Poultry {
  id: string;
  coop_id: string;
  coop_name: string;
  bird_type: 'tavuk' | 'hindi' | 'ördek' | 'kaz';
  breed: string;
  count: number;
  age_weeks: number;
  status: 'aktif' | 'karantina' | 'tedavide';
  avg_weight: number;
  feed_consumption: number;
  water_consumption: number;
  mortality_rate: number;
  temperature: number;
  humidity: number;
  light_hours: number;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface EggProduction {
  id: string;
  poultry_id: string;
  date: string;
  total: number;
  cracked: number;
  dirty: number;
  created_at: string;
}

export interface WaterSource {
  id: string;
  name: string;
  type: 'kuyu' | 'çeşme' | 'gölet' | 'depo';
  lat: number;
  lng: number;
  capacity: number;
  current_level: number;
  status: 'aktif' | 'düşük' | 'kritik' | 'bakımda';
  last_cleaned: string;
  created_at: string;
}

// Reproduction Types
export interface EstrusDetection {
  id: string;
  animal_id: string;
  detection_time: string;
  behaviors: Record<string, number>;
  confidence: number;
  optimal_breeding_start: string;
  optimal_breeding_end: string;
  status: 'detected' | 'confirmed' | 'bred' | 'missed' | 'false_positive';
  notified: boolean;
  notes?: string;
  created_at: string;
}

export interface Pregnancy {
  id: string;
  animal_id: string;
  breeding_date: string;
  expected_birth_date: string;
  actual_birth_date?: string;
  sire_id?: string;
  breeding_method: 'doğal' | 'suni_tohumlama' | 'embriyo_transferi';
  pregnancy_confirmed: boolean;
  confirmation_date?: string;
  confirmation_method?: 'manual' | 'ultrasound' | 'blood_test' | 'observation';
  status: 'aktif' | 'doğum_yaptı' | 'düşük' | 'iptal';
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Birth {
  id: string;
  mother_id: string;
  pregnancy_id?: string;
  birth_date: string;
  offspring_count: number;
  offspring_ids: string[];
  birth_type: 'normal' | 'müdahaleli' | 'sezaryen';
  birth_weight?: number;
  complications?: string;
  vet_assisted: boolean;
  vet_name?: string;
  ai_predicted_at?: string;
  ai_detected_at?: string;
  prediction_accuracy_hours?: number;
  notes?: string;
  created_at: string;
}

export interface BreedingRecord {
  id: string;
  female_id: string;
  male_id?: string;
  breeding_date: string;
  breeding_method: 'doğal' | 'suni_tohumlama' | 'embriyo_transferi';
  technician_name?: string;
  semen_batch?: string;
  estrus_detection_id?: string;
  success?: boolean;
  pregnancy_id?: string;
  notes?: string;
  created_at: string;
}

// API Functions
export const api = {
  // Animals
  animals: {
    getAll: async (): Promise<Animal[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('animals')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data as Animal[];
    },
    getById: async (id: string): Promise<Animal | null> => {
      if (!isSupabaseConfigured()) return null;
      const { data, error } = await supabase
        .from('animals')
        .select('*')
        .eq('id', id)
        .single();
      if (error) throw error;
      return data as Animal;
    },
    create: async (animal: Omit<Animal, 'id' | 'created_at' | 'updated_at'>) => {
      const { data, error } = await supabase
        .from('animals')
        .insert(animal)
        .select()
        .single();
      if (error) throw error;
      return data as Animal;
    },
    update: async (id: string, updates: Partial<Animal>) => {
      const { data, error } = await supabase
        .from('animals')
        .update({ ...updates, updated_at: new Date().toISOString() })
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      return data as Animal;
    },
    delete: async (id: string) => {
      const { error } = await supabase.from('animals').delete().eq('id', id);
      if (error) throw error;
    },
  },

  // Zones
  zones: {
    getAll: async (): Promise<Zone[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('zones')
        .select('*')
        .order('name');
      if (error) throw error;
      return data as Zone[];
    },
    getById: async (id: string): Promise<Zone | null> => {
      if (!isSupabaseConfigured()) return null;
      const { data, error } = await supabase
        .from('zones')
        .select('*')
        .eq('id', id)
        .single();
      if (error) throw error;
      return data as Zone;
    },
  },

  // Health Records
  health: {
    getAll: async () => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('health_records')
        .select('*, animals(name, tag)')
        .order('date', { ascending: false });
      if (error) throw error;
      return data;
    },
    getByAnimal: async (animalId: string): Promise<HealthRecord[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('health_records')
        .select('*')
        .eq('animal_id', animalId)
        .order('date', { ascending: false });
      if (error) throw error;
      return data as HealthRecord[];
    },
    create: async (record: Omit<HealthRecord, 'id' | 'created_at'>) => {
      if (!isSupabaseConfigured()) throw new Error('Supabase not configured');
      const { data, error } = await supabase
        .from('health_records')
        .insert(record)
        .select()
        .single();
      if (error) throw error;
      return data as HealthRecord;
    },
  },

  // Alerts
  alerts: {
    getAll: async (): Promise<Alert[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data as Alert[];
    },
    getUnread: async (): Promise<Alert[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('alerts')
        .select('*')
        .eq('is_read', false)
        .order('created_at', { ascending: false });
      if (error) throw error;
      return data as Alert[];
    },
    markAsRead: async (id: string) => {
      if (!isSupabaseConfigured()) return;
      const { error } = await supabase
        .from('alerts')
        .update({ is_read: true })
        .eq('id', id);
      if (error) throw error;
    },
    markAllAsRead: async () => {
      if (!isSupabaseConfigured()) return;
      const { error } = await supabase
        .from('alerts')
        .update({ is_read: true })
        .eq('is_read', false);
      if (error) throw error;
    },
  },

  // Poultry
  poultry: {
    getAll: async (): Promise<Poultry[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('poultry')
        .select('*')
        .order('coop_name');
      if (error) throw error;
      return data as Poultry[];
    },
    getById: async (id: string): Promise<Poultry | null> => {
      if (!isSupabaseConfigured()) return null;
      const { data, error } = await supabase
        .from('poultry')
        .select('*')
        .eq('id', id)
        .single();
      if (error) throw error;
      return data as Poultry;
    },
  },

  // Egg Production
  eggs: {
    getAll: async () => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('egg_production')
        .select('*, poultry(coop_name)')
        .order('date', { ascending: false });
      if (error) throw error;
      return data;
    },
    getByPoultry: async (poultryId: string): Promise<EggProduction[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('egg_production')
        .select('*')
        .eq('poultry_id', poultryId)
        .order('date', { ascending: false });
      if (error) throw error;
      return data as EggProduction[];
    },
    create: async (record: Omit<EggProduction, 'id' | 'created_at'>) => {
      if (!isSupabaseConfigured()) throw new Error('Supabase not configured');
      const { data, error } = await supabase
        .from('egg_production')
        .insert(record)
        .select()
        .single();
      if (error) throw error;
      return data as EggProduction;
    },
  },

  // Water Sources
  water: {
    getAll: async (): Promise<WaterSource[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('water_sources')
        .select('*')
        .order('name');
      if (error) throw error;
      return data as WaterSource[];
    },
  },

  // Reproduction - Estrus
  estrus: {
    getAll: async (): Promise<EstrusDetection[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('estrus_detections')
        .select('*')
        .order('detection_time', { ascending: false });
      if (error) throw error;
      return data as EstrusDetection[];
    },
    getByAnimal: async (animalId: string): Promise<EstrusDetection[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('estrus_detections')
        .select('*')
        .eq('animal_id', animalId)
        .order('detection_time', { ascending: false });
      if (error) throw error;
      return data as EstrusDetection[];
    },
    getActive: async (): Promise<EstrusDetection[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('estrus_detections')
        .select('*')
        .in('status', ['detected', 'confirmed'])
        .order('detection_time', { ascending: false });
      if (error) throw error;
      return data as EstrusDetection[];
    },
    create: async (record: Omit<EstrusDetection, 'id' | 'created_at'>) => {
      if (!isSupabaseConfigured()) throw new Error('Supabase not configured');
      const { data, error } = await supabase
        .from('estrus_detections')
        .insert(record)
        .select()
        .single();
      if (error) throw error;
      return data as EstrusDetection;
    },
    confirm: async (id: string) => {
      if (!isSupabaseConfigured()) return;
      const { error } = await supabase
        .from('estrus_detections')
        .update({ status: 'confirmed' })
        .eq('id', id);
      if (error) throw error;
    },
    markBred: async (id: string) => {
      if (!isSupabaseConfigured()) return;
      const { error } = await supabase
        .from('estrus_detections')
        .update({ status: 'bred' })
        .eq('id', id);
      if (error) throw error;
    },
  },

  // Reproduction - Pregnancies
  pregnancies: {
    getAll: async (): Promise<Pregnancy[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('pregnancies')
        .select('*')
        .order('expected_birth_date', { ascending: true });
      if (error) throw error;
      return data as Pregnancy[];
    },
    getActive: async (): Promise<Pregnancy[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('pregnancies')
        .select('*')
        .eq('status', 'aktif')
        .order('expected_birth_date', { ascending: true });
      if (error) throw error;
      return data as Pregnancy[];
    },
    getByAnimal: async (animalId: string): Promise<Pregnancy[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('pregnancies')
        .select('*')
        .eq('animal_id', animalId)
        .order('breeding_date', { ascending: false });
      if (error) throw error;
      return data as Pregnancy[];
    },
    getDueSoon: async (days: number = 7): Promise<Pregnancy[]> => {
      if (!isSupabaseConfigured()) return [];
      const today = new Date();
      const futureDate = new Date(today);
      futureDate.setDate(today.getDate() + days);
      
      const { data, error } = await supabase
        .from('pregnancies')
        .select('*')
        .eq('status', 'aktif')
        .gte('expected_birth_date', today.toISOString().split('T')[0])
        .lte('expected_birth_date', futureDate.toISOString().split('T')[0])
        .order('expected_birth_date', { ascending: true });
      if (error) throw error;
      return data as Pregnancy[];
    },
    create: async (record: Omit<Pregnancy, 'id' | 'created_at' | 'updated_at'>) => {
      if (!isSupabaseConfigured()) throw new Error('Supabase not configured');
      const { data, error } = await supabase
        .from('pregnancies')
        .insert(record)
        .select()
        .single();
      if (error) throw error;
      return data as Pregnancy;
    },
    confirm: async (id: string, method: string) => {
      if (!isSupabaseConfigured()) return;
      const { error } = await supabase
        .from('pregnancies')
        .update({ 
          pregnancy_confirmed: true, 
          confirmation_method: method,
          confirmation_date: new Date().toISOString().split('T')[0],
          updated_at: new Date().toISOString()
        })
        .eq('id', id);
      if (error) throw error;
    },
    complete: async (id: string, birthDate: string) => {
      if (!isSupabaseConfigured()) return;
      const { error } = await supabase
        .from('pregnancies')
        .update({ 
          status: 'doğum_yaptı', 
          actual_birth_date: birthDate,
          updated_at: new Date().toISOString()
        })
        .eq('id', id);
      if (error) throw error;
    },
  },

  // Reproduction - Births
  births: {
    getAll: async (): Promise<Birth[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('births')
        .select('*')
        .order('birth_date', { ascending: false });
      if (error) throw error;
      return data as Birth[];
    },
    getByMother: async (motherId: string): Promise<Birth[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('births')
        .select('*')
        .eq('mother_id', motherId)
        .order('birth_date', { ascending: false });
      if (error) throw error;
      return data as Birth[];
    },
    create: async (record: Omit<Birth, 'id' | 'created_at'>) => {
      if (!isSupabaseConfigured()) throw new Error('Supabase not configured');
      const { data, error } = await supabase
        .from('births')
        .insert(record)
        .select()
        .single();
      if (error) throw error;
      return data as Birth;
    },
  },

  // Reproduction - Breeding Records
  breeding: {
    getAll: async (): Promise<BreedingRecord[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('breeding_records')
        .select('*')
        .order('breeding_date', { ascending: false });
      if (error) throw error;
      return data as BreedingRecord[];
    },
    getByFemale: async (femaleId: string): Promise<BreedingRecord[]> => {
      if (!isSupabaseConfigured()) return [];
      const { data, error } = await supabase
        .from('breeding_records')
        .select('*')
        .eq('female_id', femaleId)
        .order('breeding_date', { ascending: false });
      if (error) throw error;
      return data as BreedingRecord[];
    },
    create: async (record: Omit<BreedingRecord, 'id' | 'created_at'>) => {
      if (!isSupabaseConfigured()) throw new Error('Supabase not configured');
      const { data, error } = await supabase
        .from('breeding_records')
        .insert(record)
        .select()
        .single();
      if (error) throw error;
      return data as BreedingRecord;
    },
    markSuccess: async (id: string, success: boolean, pregnancyId?: string) => {
      if (!isSupabaseConfigured()) return;
      const updates: Record<string, unknown> = { success };
      if (pregnancyId) updates.pregnancy_id = pregnancyId;
      
      const { error } = await supabase
        .from('breeding_records')
        .update(updates)
        .eq('id', id);
      if (error) throw error;
    },
  },

  // Reproduction Stats
  reproductionStats: {
    getSummary: async () => {
      if (!isSupabaseConfigured()) {
        return {
          activeEstrus: 0,
          activePregnancies: 0,
          dueSoon: 0,
          totalBirths: 0,
          pendingBreedings: 0,
        };
      }
      
      const today = new Date();
      const weekLater = new Date(today);
      weekLater.setDate(today.getDate() + 7);
      
      const [estrus, pregnancies, dueSoon, births, breeding] = await Promise.all([
        supabase.from('estrus_detections').select('id', { count: 'exact' }).in('status', ['detected', 'confirmed']),
        supabase.from('pregnancies').select('id', { count: 'exact' }).eq('status', 'aktif'),
        supabase.from('pregnancies').select('id', { count: 'exact' })
          .eq('status', 'aktif')
          .gte('expected_birth_date', today.toISOString().split('T')[0])
          .lte('expected_birth_date', weekLater.toISOString().split('T')[0]),
        supabase.from('births').select('id', { count: 'exact' }),
        supabase.from('breeding_records').select('id', { count: 'exact' }).is('success', null),
      ]);

      return {
        activeEstrus: estrus.count || 0,
        activePregnancies: pregnancies.count || 0,
        dueSoon: dueSoon.count || 0,
        totalBirths: births.count || 0,
        pendingBreedings: breeding.count || 0,
      };
    },
  },

  // Dashboard Stats
  stats: {
    getDashboard: async () => {
      if (!isSupabaseConfigured()) {
        return {
          totalAnimals: 0,
          healthyAnimals: 0,
          sickAnimals: 0,
          unreadAlerts: 0,
          totalPoultry: 0,
          activeZones: 0,
        };
      }
      
      const [animals, alerts, zones, poultry] = await Promise.all([
        supabase.from('animals').select('id, status', { count: 'exact' }),
        supabase.from('alerts').select('id', { count: 'exact' }).eq('is_read', false),
        supabase.from('zones').select('id, current_count'),
        supabase.from('poultry').select('id, count'),
      ]);

      const totalAnimals = animals.count || 0;
      const healthyAnimals = animals.data?.filter(a => a.status === 'sağlıklı').length || 0;
      const sickAnimals = animals.data?.filter(a => a.status === 'hasta' || a.status === 'tedavide').length || 0;
      const unreadAlerts = alerts.count || 0;
      const totalPoultry = poultry.data?.reduce((sum, p) => sum + (p.count || 0), 0) || 0;

      return {
        totalAnimals,
        healthyAnimals,
        sickAnimals,
        unreadAlerts,
        totalPoultry,
        activeZones: zones.data?.length || 0,
      };
    },
  },
};

// Auth helpers
export const getCurrentUser = async () => {
  const { data: { user } } = await supabase.auth.getUser();
  return user;
};

export const signOut = async () => {
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
};

export default supabase;
