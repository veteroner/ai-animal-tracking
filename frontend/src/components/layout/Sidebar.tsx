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
  Heart,
  Calendar,
  Baby,
  Stethoscope,
  Users,
  LayoutGrid,
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
  // Üreme Modülü
  { name: 'Üreme Takibi', href: '/reproduction', icon: Heart, modes: ['cattle'] },
  { name: 'Kızgınlık Tespiti', href: '/reproduction/estrus', icon: Activity, modes: ['cattle'] },
  { name: 'Gebelik Takibi', href: '/reproduction/pregnancies', icon: Baby, modes: ['cattle'] },
  { name: 'Üreme Takvimi', href: '/reproduction/calendar', icon: Calendar, modes: ['cattle'] },
  // Kanatlı Modülü
  { name: 'Kanatlılar', href: '/poultry', icon: Bird, modes: ['poultry'] },
  { name: 'Sürü Yönetimi', href: '/poultry/flock', icon: Users, modes: ['poultry'] },
  { name: 'Yumurta Üretimi', href: '/poultry/eggs', icon: Egg, modes: ['poultry'] },
  { name: 'Kümes Sağlık', href: '/poultry/health', icon: Stethoscope, modes: ['poultry'] },
  { name: 'Davranış Analizi', href: '/poultry/behavior', icon: Activity, modes: ['poultry'] },
  { name: 'Bölge Yönetimi', href: '/poultry/zones', icon: LayoutGrid, modes: ['poultry'] },
  // Ortak Modüller
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
      {/* Teknova Logo */}
      <div className="flex flex-col items-center gap-3 px-6 py-5 border-b border-gray-200">
        <div className="relative">
          {/* Background Circle with Gradient */}
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center shadow-lg shadow-primary-500/40">
            {/* Inner Circle */}
            <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
              {/* AI Eye Symbol */}
              <div className="relative">
                <div className="w-8 h-5 border-2 border-white rounded-full flex items-center justify-center">
                  <div className="w-2.5 h-2.5 bg-white rounded-full"></div>
                </div>
                <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-amber-400 -translate-y-1/2"></div>
              </div>
            </div>
          </div>
          {/* Paw Print Accent */}
          <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-amber-400 rounded-full flex items-center justify-center">
            <Dog className="w-3 h-3 text-white" />
          </div>
        </div>
        <div className="text-center">
          <h1 className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary-500 to-primary-700 tracking-wider text-lg">TEKNOVA</h1>
          <p className="text-xs text-gray-500">AI Animal Tracking</p>
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

      {/* System Status + Copyright */}
      <div className="px-4 py-4 border-t border-gray-200">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
          <span className="text-xs text-gray-500">Sistem Aktif</span>
        </div>
        <div className="text-center">
          <p className="text-[10px] text-gray-400">© 2025 Teknova</p>
          <p className="text-[10px] text-gray-400">Tüm hakları saklıdır.</p>
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
