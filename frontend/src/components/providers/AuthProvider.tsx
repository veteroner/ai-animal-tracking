'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { supabase, getCurrentUser } from '@/lib/supabase';
import type { User } from '@supabase/supabase-js';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  signOut: async () => {},
});

export const useAuthContext = () => useContext(AuthContext);

const publicRoutes = ['/login'];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const checkAuth = async () => {
      // Check demo auth
      const demoAuth = localStorage.getItem('demo_auth');
      if (demoAuth === 'true') {
        setUser({ id: 'demo', email: 'demo@example.com' } as User);
        setLoading(false);
        return;
      }

      // Check Supabase auth
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setLoading(false);

      // Redirect to login if not authenticated and not on public route
      if (!currentUser && !publicRoutes.includes(pathname)) {
        // For demo purposes, allow access without auth
        // Uncomment below to enforce auth:
        // router.push('/login');
      }
    };

    checkAuth();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setUser(session?.user ?? null);
        
        if (event === 'SIGNED_OUT') {
          localStorage.removeItem('demo_auth');
          router.push('/login');
        }
      }
    );

    return () => subscription.unsubscribe();
  }, [pathname, router]);

  const signOut = async () => {
    localStorage.removeItem('demo_auth');
    await supabase.auth.signOut();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
