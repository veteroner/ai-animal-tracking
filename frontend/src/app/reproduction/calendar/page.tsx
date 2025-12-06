'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, EstrusDetection, Pregnancy, Birth, BreedingRecord } from '@/lib/supabase';

interface CalendarEvent {
  id: string;
  date: string;
  type: 'estrus' | 'pregnancy_due' | 'birth' | 'breeding' | 'pregnancy_check';
  title: string;
  animal_id: string;
  color: string;
  details?: string;
}

export default function CalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, [currentMonth]);

  const loadData = async () => {
    try {
      const [estrusData, pregnanciesData, birthsData, breedingsData] = await Promise.all([
        api.estrus.getAll(),
        api.pregnancies.getAll(),
        api.births.getAll(),
        api.breeding.getAll(),
      ]);

      const calendarEvents: CalendarEvent[] = [];

      // Estrus events
      estrusData.forEach((e: EstrusDetection) => {
        calendarEvents.push({
          id: `estrus-${e.id}`,
          date: e.detection_time.split('T')[0],
          type: 'estrus',
          title: 'Kızgınlık Tespiti',
          animal_id: e.animal_id,
          color: 'bg-pink-500',
          details: `Güven: %${(e.confidence * 100).toFixed(0)}`
        });
        if (e.optimal_breeding_start) {
          calendarEvents.push({
            id: `breeding-window-${e.id}`,
            date: e.optimal_breeding_start.split('T')[0],
            type: 'estrus',
            title: 'Optimal Tohumlama Penceresi',
            animal_id: e.animal_id,
            color: 'bg-rose-400',
            details: 'Tohumlama için ideal zaman'
          });
        }
      });

      // Pregnancy due dates
      pregnanciesData.forEach((p: Pregnancy) => {
        if (p.status === 'aktif' && p.expected_birth_date) {
          calendarEvents.push({
            id: `due-${p.id}`,
            date: p.expected_birth_date,
            type: 'pregnancy_due',
            title: 'Tahmini Doğum',
            animal_id: p.animal_id,
            color: 'bg-purple-500',
            details: p.pregnancy_confirmed ? 'Gebelik Doğrulanmış' : 'Gebelik Şüpheli'
          });
        }
      });

      // Birth dates
      birthsData.forEach((b: Birth) => {
        calendarEvents.push({
          id: `birth-${b.id}`,
          date: b.birth_date.split('T')[0],
          type: 'birth',
          title: 'Doğum',
          animal_id: b.mother_id,
          color: 'bg-blue-500',
          details: `${b.offspring_count} yavru - ${b.birth_type}`
        });
      });

      // Breeding dates
      breedingsData.forEach((br: BreedingRecord) => {
        calendarEvents.push({
          id: `breeding-${br.id}`,
          date: br.breeding_date.split('T')[0],
          type: 'breeding',
          title: 'Çiftleştirme',
          animal_id: br.female_id,
          color: 'bg-indigo-500',
          details: br.breeding_method.replace(/_/g, ' ')
        });

        // Add pregnancy check reminder (21 days after breeding for cattle)
        const checkDate = new Date(br.breeding_date);
        checkDate.setDate(checkDate.getDate() + 21);
        calendarEvents.push({
          id: `check-${br.id}`,
          date: checkDate.toISOString().split('T')[0],
          type: 'pregnancy_check',
          title: 'Gebelik Kontrolü',
          animal_id: br.female_id,
          color: 'bg-yellow-500',
          details: 'İlk gebelik kontrolü zamanı'
        });
      });

      setEvents(calendarEvents);
    } catch (error) {
      console.error('Veri yükleme hatası:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    return { daysInMonth, startingDay };
  };

  const { daysInMonth, startingDay } = getDaysInMonth(currentMonth);
  const monthNames = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 
                      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
  const dayNames = ['Paz', 'Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt'];

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  const getEventsForDate = (day: number) => {
    const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return events.filter(e => e.date === dateStr);
  };

  const selectedEvents = selectedDate ? events.filter(e => e.date === selectedDate) : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <div className="flex items-center space-x-2">
            <Link href="/reproduction" className="text-gray-500 hover:text-gray-700">
              ← Üreme
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mt-2">📅 Üreme Takvimi</h1>
          <p className="text-gray-600">Kızgınlık, gebelik ve doğum takip takvimi</p>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 bg-white rounded-xl shadow p-4">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-pink-500"></div>
          <span className="text-sm">Kızgınlık</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-purple-500"></div>
          <span className="text-sm">Doğum Tahmini</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-blue-500"></div>
          <span className="text-sm">Doğum</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-indigo-500"></div>
          <span className="text-sm">Çiftleştirme</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded bg-yellow-500"></div>
          <span className="text-sm">Kontrol</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow p-6">
          {/* Month Navigation */}
          <div className="flex justify-between items-center mb-6">
            <button
              onClick={prevMonth}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              ← Önceki
            </button>
            <h2 className="text-xl font-bold">
              {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
            </h2>
            <button
              onClick={nextMonth}
              className="p-2 hover:bg-gray-100 rounded-lg"
            >
              Sonraki →
            </button>
          </div>

          {/* Day Names */}
          <div className="grid grid-cols-7 gap-1 mb-2">
            {dayNames.map(day => (
              <div key={day} className="text-center text-sm font-medium text-gray-500 py-2">
                {day}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-1">
            {/* Empty cells for days before month starts */}
            {Array.from({ length: startingDay }, (_, i) => (
              <div key={`empty-${i}`} className="h-24 bg-gray-50 rounded-lg"></div>
            ))}
            
            {/* Days of month */}
            {Array.from({ length: daysInMonth }, (_, i) => {
              const day = i + 1;
              const dayEvents = getEventsForDate(day);
              const dateStr = `${currentMonth.getFullYear()}-${String(currentMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
              const isToday = dateStr === new Date().toISOString().split('T')[0];
              const isSelected = selectedDate === dateStr;

              return (
                <div
                  key={day}
                  onClick={() => setSelectedDate(dateStr)}
                  className={`h-24 rounded-lg p-1 cursor-pointer transition-colors ${
                    isSelected ? 'ring-2 ring-green-500 bg-green-50' :
                    isToday ? 'bg-blue-50' : 'bg-gray-50 hover:bg-gray-100'
                  }`}
                >
                  <div className={`text-sm font-medium ${isToday ? 'text-blue-600' : ''}`}>
                    {day}
                  </div>
                  <div className="space-y-1 overflow-hidden">
                    {dayEvents.slice(0, 3).map((event, idx) => (
                      <div
                        key={idx}
                        className={`text-xs px-1 py-0.5 rounded truncate text-white ${event.color}`}
                        title={`${event.title} - ${event.animal_id}`}
                      >
                        {event.animal_id.substring(0, 8)}
                      </div>
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="text-xs text-gray-500 px-1">
                        +{dayEvents.length - 3} daha
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Event Details */}
        <div className="bg-white rounded-xl shadow p-6">
          <h3 className="text-lg font-bold mb-4">
            {selectedDate 
              ? new Date(selectedDate).toLocaleDateString('tr-TR', { 
                  weekday: 'long', 
                  year: 'numeric', 
                  month: 'long', 
                  day: 'numeric' 
                })
              : 'Bir tarih seçin'}
          </h3>

          {selectedDate && selectedEvents.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <span className="text-4xl">📭</span>
              <p className="mt-2">Bu tarihte etkinlik yok</p>
            </div>
          )}

          <div className="space-y-4">
            {selectedEvents.map((event) => (
              <div key={event.id} className="border rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${event.color}`}></div>
                  <span className="font-medium">{event.title}</span>
                </div>
                <div className="mt-2 pl-6 space-y-1 text-sm text-gray-600">
                  <p>Hayvan: <span className="font-medium">{event.animal_id}</span></p>
                  {event.details && <p>{event.details}</p>}
                </div>
              </div>
            ))}
          </div>

          {/* Upcoming Events */}
          <div className="mt-6 pt-6 border-t">
            <h4 className="font-medium mb-3">Yaklaşan Olaylar</h4>
            <div className="space-y-2">
              {events
                .filter(e => new Date(e.date) >= new Date())
                .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
                .slice(0, 5)
                .map((event) => (
                  <div
                    key={event.id}
                    onClick={() => setSelectedDate(event.date)}
                    className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                  >
                    <div className={`w-2 h-2 rounded-full ${event.color}`}></div>
                    <span className="text-sm flex-1 truncate">{event.title}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(event.date).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' })}
                    </span>
                  </div>
                ))
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
