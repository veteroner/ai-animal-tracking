'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { supabase, getCurrentUser } from './supabase';
import type { User } from '@supabase/supabase-js';

// Auth Hook
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    // Check demo auth first
    const demoAuth = localStorage.getItem('demo_auth');
    if (demoAuth === 'true') {
      setUser({ id: 'demo', email: 'demo@example.com' } as User);
      setLoading(false);
      return;
    }

    // Check Supabase auth
    getCurrentUser().then((currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signOut = useCallback(async () => {
    localStorage.removeItem('demo_auth');
    await supabase.auth.signOut();
    setUser(null);
    router.push('/login');
  }, [router]);

  return { user, loading, signOut };
}

// Generic Data Fetch Hook
export function useData<T>(
  fetchFn: () => Promise<T>,
  deps: any[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn();
      setData(result);
    } catch (err: any) {
      setError(err.message || 'Veri yüklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    refetch();
  }, deps);

  return { data, loading, error, refetch };
}

// Backend Connection Hook
export function useBackendStatus() {
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/health`, { 
          method: 'GET',
          signal: AbortSignal.timeout(5000)
        });
        setConnected(response.ok);
      } catch {
        setConnected(false);
      } finally {
        setChecking(false);
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return { connected, checking };
}

// Supabase Connection Hook
export function useSupabaseStatus() {
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkSupabase = async () => {
      try {
        const { error } = await supabase.from('zones').select('count').limit(1);
        setConnected(!error);
      } catch {
        setConnected(false);
      } finally {
        setChecking(false);
      }
    };

    checkSupabase();
  }, []);

  return { connected, checking };
}

// Real-time Alerts Hook
export function useRealTimeAlerts(onNewAlert?: (alert: any) => void) {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const channel = supabase
      .channel('realtime-alerts')
      .on('postgres_changes', 
        { event: 'INSERT', schema: 'public', table: 'alerts' }, 
        (payload) => {
          const newAlert = payload.new;
          setAlerts(prev => [newAlert, ...prev]);
          onNewAlert?.(newAlert);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [onNewAlert]);

  return alerts;
}

// Local Storage Hook
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initialValue;
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  };

  return [storedValue, setValue] as const;
}
