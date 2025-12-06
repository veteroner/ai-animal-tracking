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
