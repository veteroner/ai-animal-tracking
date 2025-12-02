import './globals.css';
import type { Metadata } from 'next';
import Sidebar from '@/components/layout/Sidebar';
import Header from '@/components/layout/Header';

export const metadata: Metadata = {
  title: 'AI Hayvan Takip Sistemi',
  description: 'Yapay zeka destekli hayvan izleme ve sağlık takip sistemi',
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
      </body>
    </html>
  );
}
