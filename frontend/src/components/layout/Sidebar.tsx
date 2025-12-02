'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Camera,
  Dog,
  Activity,
  AlertTriangle,
  Settings,
  Bell,
  MapPin,
  Egg,
  Bird,
  Droplets,
  Menu,
  X,
  FileText,
  User,
} from 'lucide-react';
import { useState } from 'react';

type FarmMode = 'cattle' | 'poultry';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  modes?: FarmMode[];
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Canlı Kamera', href: '/camera', icon: Camera },
  { name: 'Hayvanlar', href: '/animals', icon: Dog, modes: ['cattle'] },
  { name: 'Kanatlılar', href: '/poultry', icon: Bird, modes: ['poultry'] },
  { name: 'Yumurta Takibi', href: '/eggs', icon: Egg, modes: ['poultry'] },
  { name: 'Sağlık Kayıtları', href: '/health', icon: Activity },
  { name: 'Bölge Haritası', href: '/zones', icon: MapPin },
  { name: 'Su Kaynakları', href: '/water', icon: Droplets },
  { name: 'Raporlar', href: '/reports', icon: FileText },
  { name: 'Uyarılar', href: '/alerts', icon: AlertTriangle },
  { name: 'Bildirimler', href: '/notifications', icon: Bell },
  { name: 'Profil', href: '/profile', icon: User },
  { name: 'Ayarlar', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [farmMode, setFarmMode] = useState<FarmMode>('cattle');
  const [mobileOpen, setMobileOpen] = useState(false);

  const filteredNav = navigation.filter(
    (item) => !item.modes || item.modes.includes(farmMode)
  );

  const SidebarContent = () => (
    <>
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-gray-200">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
          <Dog className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="font-bold text-gray-900">AI Hayvan</h1>
          <p className="text-xs text-gray-500">Takip Sistemi</p>
        </div>
      </div>

      {/* Farm Mode Selector */}
      <div className="px-4 py-4 border-b border-gray-200">
        <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          Çiftlik Modu
        </label>
        <div className="mt-2 flex rounded-lg bg-gray-100 p-1">
          <button
            onClick={() => setFarmMode('cattle')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-md transition-colors ${
              farmMode === 'cattle'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Dog className="w-4 h-4" />
            Büyükbaş
          </button>
          <button
            onClick={() => setFarmMode('poultry')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-sm font-medium rounded-md transition-colors ${
              farmMode === 'poultry'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <Bird className="w-4 h-4" />
            Kanatlı
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {filteredNav.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
              }`}
            >
              <item.icon
                className={`w-5 h-5 ${
                  isActive ? 'text-primary-600' : 'text-gray-400'
                }`}
              />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* System Status */}
      <div className="px-4 py-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
          <span className="text-xs text-gray-500">Sistem Aktif</span>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white shadow-md"
      >
        <Menu className="w-6 h-6 text-gray-600" />
      </button>

      {/* Mobile Sidebar */}
      <div
        className={`lg:hidden fixed inset-0 z-50 transition-opacity duration-300 ${
          mobileOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
      >
        <div
          className="absolute inset-0 bg-black/50"
          onClick={() => setMobileOpen(false)}
        />
        <aside
          className={`absolute left-0 top-0 bottom-0 w-64 bg-white flex flex-col transition-transform duration-300 ${
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <button
            onClick={() => setMobileOpen(false)}
            className="absolute top-4 right-4 p-1 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
          <SidebarContent />
        </aside>
      </div>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex w-64 bg-white border-r border-gray-200 flex-col">
        <SidebarContent />
      </aside>
    </>
  );
}
