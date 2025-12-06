import './globals.css';
import type { Metadata } from 'next';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';
import ConnectionStatus from '@/components/ui/ConnectionStatus';

export const metadata: Metadata = {
  title: 'Teknova AI Animal Tracking',
  description: 'Teknova - Yapay zeka destekli hayvan izleme ve sağlık takip sistemi',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="bg-gray-50">
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar */}
          <Sidebar />
          
          {/* Main Content */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Header */}
            <Header />
            
            {/* Page Content */}
            <main className="flex-1 overflow-y-auto p-6">
              {children}
            </main>
          </div>
        </div>
        
        {/* Connection Status Indicator */}
        <ConnectionStatus />
      </body>
    </html>
  );
}
