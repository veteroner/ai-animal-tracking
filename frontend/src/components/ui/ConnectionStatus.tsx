'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react';

interface ServiceStatus {
  name: string;
  url: string;
  connected: boolean;
  checking: boolean;
}

export default function ConnectionStatus() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { name: 'Backend API', url: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000', connected: false, checking: true },
    { name: 'Supabase', url: 'Database', connected: false, checking: true },
  ]);
  const [minimized, setMinimized] = useState(false);

  const checkConnections = async () => {
    setServices(prev => prev.map(s => ({ ...s, checking: true })));

    // Check Backend
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      setServices(prev => prev.map(s => 
        s.name === 'Backend API' ? { ...s, connected: response.ok, checking: false } : s
      ));
    } catch {
      setServices(prev => prev.map(s => 
        s.name === 'Backend API' ? { ...s, connected: false, checking: false } : s
      ));
    }

    // Check Supabase
    try {
      const { supabase } = await import('@/lib/supabase');
      const { error } = await supabase.from('zones').select('count').limit(1);
      setServices(prev => prev.map(s => 
        s.name === 'Supabase' ? { ...s, connected: !error, checking: false } : s
      ));
    } catch {
      setServices(prev => prev.map(s => 
        s.name === 'Supabase' ? { ...s, connected: false, checking: false } : s
      ));
    }
  };

  useEffect(() => {
    checkConnections();
    const interval = setInterval(checkConnections, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const allConnected = services.every(s => s.connected);
  const anyChecking = services.some(s => s.checking);

  if (minimized) {
    return (
      <button
        onClick={() => setMinimized(false)}
        className={`fixed bottom-4 right-4 p-3 rounded-full shadow-lg ${
          allConnected ? 'bg-success-500' : 'bg-danger-500'
        }`}
      >
        {anyChecking ? (
          <Loader2 className="w-5 h-5 text-white animate-spin" />
        ) : allConnected ? (
          <CheckCircle className="w-5 h-5 text-white" />
        ) : (
          <XCircle className="w-5 h-5 text-white" />
        )}
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 bg-white rounded-xl shadow-lg border border-gray-200 p-4 min-w-[240px]">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">Bağlantı Durumu</h3>
        <div className="flex items-center gap-2">
          <button
            onClick={checkConnections}
            className="p-1 hover:bg-gray-100 rounded"
            title="Yenile"
          >
            <RefreshCw className={`w-4 h-4 text-gray-500 ${anyChecking ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setMinimized(true)}
            className="p-1 hover:bg-gray-100 rounded text-gray-500"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {services.map((service) => (
          <div key={service.name} className="flex items-center justify-between">
            <span className="text-sm text-gray-600">{service.name}</span>
            {service.checking ? (
              <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
            ) : service.connected ? (
              <div className="flex items-center gap-1 text-success-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-xs">Bağlı</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-danger-600">
                <XCircle className="w-4 h-4" />
                <span className="text-xs">Bağlı Değil</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
