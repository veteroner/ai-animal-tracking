-- =====================================================
-- TEKNOVA AI ANIMAL TRACKING - ÖRNEK VERİ EKLEME
-- Supabase SQL Editor'da çalıştırın
-- =====================================================

-- Önce mevcut verileri temizle (opsiyonel)
-- TRUNCATE zones, animals, health_records, alerts, poultry, egg_production, water_sources CASCADE;

-- =====================================================
-- 1. BÖLGELER (ZONES)
-- =====================================================
INSERT INTO zones (id, name, type, coordinates, capacity, current_count, color) VALUES
  ('otlak-001', 'Ana Otlak', 'otlak', '[{"lat": 39.935, "lng": 32.861}, {"lat": 39.936, "lng": 32.862}, {"lat": 39.934, "lng": 32.863}]'::jsonb, 60, 45, '#22c55e'),
  ('ahir-001', 'Ahır 1', 'ahır', '[{"lat": 39.932, "lng": 32.858}, {"lat": 39.933, "lng": 32.859}, {"lat": 39.931, "lng": 32.860}]'::jsonb, 40, 32, '#3b82f6'),
  ('ahir-002', 'Ahır 2 - Yavru', 'ahır', '[{"lat": 39.933, "lng": 32.856}, {"lat": 39.934, "lng": 32.857}, {"lat": 39.932, "lng": 32.858}]'::jsonb, 30, 28, '#8b5cf6'),
  ('sulak-001', 'Su Deposu Alanı', 'sulak', '[{"lat": 39.934, "lng": 32.862}, {"lat": 39.935, "lng": 32.863}, {"lat": 39.933, "lng": 32.864}]'::jsonb, 20, 12, '#06b6d4'),
  ('karantina-001', 'Karantina Bölgesi', 'karantina', '[{"lat": 39.936, "lng": 32.855}, {"lat": 39.937, "lng": 32.856}, {"lat": 39.935, "lng": 32.857}]'::jsonb, 10, 3, '#ef4444')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 2. HAYVANLAR (ANIMALS)
-- =====================================================
INSERT INTO animals (id, name, tag, type, breed, gender, birth_date, weight, status, zone_id, notes) VALUES
  ('inek-001', 'Sarıkız', 'TR-001', 'sığır', 'Simental', 'dişi', '2022-03-15', 452, 'sağlıklı', 'otlak-001', 'Süt verimi yüksek, günlük 25L'),
  ('inek-002', 'Karabaş', 'TR-002', 'sığır', 'Holstein', 'erkek', '2021-06-20', 580, 'tedavide', 'ahir-001', 'Antibiyotik tedavisi devam ediyor'),
  ('inek-003', 'Benekli', 'TR-003', 'sığır', 'Jersey', 'dişi', '2023-01-10', 385, 'sağlıklı', 'otlak-001', 'Gebe, 5. ay'),
  ('koyun-001', 'Pamuk', 'TR-004', 'koyun', 'Merinos', 'dişi', '2023-05-01', 68, 'sağlıklı', 'otlak-001', 'Yün kalitesi A sınıfı'),
  ('koyun-002', 'Kıvırcık', 'TR-005', 'koyun', 'Kıvırcık', 'erkek', '2022-08-15', 75, 'hasta', 'karantina-001', 'Parazit tedavisi'),
  ('keci-001', 'Beyaz', 'TR-006', 'keçi', 'Saanen', 'dişi', '2023-02-28', 48, 'sağlıklı', 'otlak-001', 'Süt keçisi, günlük 3L'),
  ('boga-001', 'Boynuzlu', 'TR-007', 'sığır', 'Angus', 'erkek', '2020-11-05', 720, 'sağlıklı', 'ahir-001', 'Damızlık boğa'),
  ('buzagi-001', 'Minik', 'TR-008', 'sığır', 'Simental', 'dişi', '2024-06-01', 180, 'sağlıklı', 'ahir-002', 'Buzağı, gelişimi normal'),
  ('koyun-003', 'Tüylü', 'TR-009', 'koyun', 'Merinos', 'dişi', '2022-04-10', 62, 'sağlıklı', 'otlak-001', NULL),
  ('keci-002', 'Çizgili', 'TR-010', 'keçi', 'Kıl Keçisi', 'erkek', '2023-07-20', 55, 'sağlıklı', 'otlak-001', NULL)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 3. SAĞLIK KAYITLARI (HEALTH RECORDS)
-- =====================================================
INSERT INTO health_records (id, animal_id, type, description, vet_name, result, date) VALUES
  ('muayene-inek-001', 'inek-001', 'kontrol', 'Rutin sağlık kontrolü yapıldı', 'Dr. Ahmet Yılmaz', 'Sağlık durumu iyi, aşılar güncel', '2024-12-01'),
  ('tedavi-inek-002', 'inek-002', 'tedavi', 'Üst solunum yolu enfeksiyonu tedavisi', 'Dr. Ahmet Yılmaz', 'Antibiyotik başlandı, 7 gün devam edilecek', '2024-12-02'),
  ('gebelik-inek-003', 'inek-003', 'muayene', 'Gebelik kontrolü', 'Dr. Fatma Demir', 'Gebelik 5. ayda, sağlıklı', '2024-11-28'),
  ('tedavi-koyun-002', 'koyun-002', 'tedavi', 'Parazit tedavisi başlatıldı', 'Dr. Fatma Demir', 'Antiparaziter ilaç verildi', '2024-11-30'),
  ('asi-koyun-001', 'koyun-001', 'aşı', 'Şap aşısı yapıldı', 'Dr. Ahmet Yılmaz', 'Aşı başarılı', '2024-11-25'),
  ('damizlik-boga-001', 'boga-001', 'kontrol', 'Damızlık değerlendirmesi', 'Dr. Mehmet Kaya', 'Sperm kalitesi çok iyi', '2024-11-20'),
  ('gelisim-buzagi-001', 'buzagi-001', 'kontrol', 'Buzağı gelişim kontrolü', 'Dr. Fatma Demir', 'Gelişim normal, kilo artışı iyi', '2024-12-03')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 4. UYARILAR (ALERTS)
-- =====================================================
INSERT INTO alerts (id, type, severity, title, message, animal_id, zone_id, is_read) VALUES
  ('ates-inek-002', 'sağlık', 'yüksek', 'Yüksek Ateş Tespit Edildi', 'TR-002 numaralı inek de 40.5°C ateş tespit edildi', 'inek-002', NULL, false),
  ('ihlal-karantina-001', 'güvenlik', 'kritik', 'Bölge İhlali', '3 hayvan karantina bölgesine girdi', NULL, 'karantina-001', false),
  ('hareket-koyun-002', 'aktivite', 'orta', 'Anormal Hareket', 'TR-005 numaralı koyunda anormal hareket paterni tespit edildi', 'koyun-002', NULL, false),
  ('yem-koyun-002', 'sağlık', 'yüksek', 'Yem Tüketimi Düşük', 'TR-005 numaralı koyun 24 saattir yem yemedi', 'koyun-002', NULL, true),
  ('kamera-sistem-001', 'sistem', 'düşük', 'Kamera Bağlantısı', 'Kamera 3 bağlantısı zayıf', NULL, NULL, true),
  ('ayrilma-koyun-001', 'aktivite', 'orta', 'Sürüden Ayrılma', 'TR-004 numaralı koyun sürüden ayrıldı', 'koyun-001', NULL, true),
  ('bakim-sulak-001', 'sistem', 'düşük', 'Bakım Hatırlatması', 'Su deposu bakım zamanı geldi', NULL, 'sulak-001', false)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 5. KANATLILAR (POULTRY)
-- =====================================================
INSERT INTO poultry (id, coop_id, coop_name, bird_type, breed, count, age_weeks, status, avg_weight, feed_consumption, water_consumption, mortality_rate, temperature, humidity, light_hours, notes) VALUES
  ('tavuk-kumes-001', 'COOP-001', 'Kümes 1 - Yumurta', 'tavuk', 'Rhode Island Red', 150, 32, 'aktif', 2.5, 18.5, 35.0, 0.5, 22.0, 65.0, 16, 'Yumurta üretimi yüksek'),
  ('tavuk-kumes-002', 'COOP-002', 'Kümes 2 - Yumurta', 'tavuk', 'Leghorn', 120, 28, 'aktif', 2.2, 15.0, 30.0, 0.3, 21.5, 62.0, 16, 'Beyaz yumurta üretimi'),
  ('hindi-kumes-003', 'COOP-003', 'Kümes 3 - Hindi', 'hindi', 'Bronze', 45, 20, 'aktif', 8.5, 45.0, 60.0, 1.0, 20.0, 58.0, 14, 'Kesim için besleniyor'),
  ('ordek-kumes-004', 'COOP-004', 'Kümes 4 - Ördek', 'ördek', 'Pekin', 60, 16, 'aktif', 3.2, 12.0, 40.0, 0.8, 19.0, 70.0, 14, 'Su havuzu mevcut'),
  ('kaz-kumes-005', 'COOP-005', 'Kümes 5 - Kaz', 'kaz', 'Toulouse', 25, 24, 'karantina', 5.5, 20.0, 45.0, 2.0, 18.0, 55.0, 12, 'Sağlık kontrolü yapılıyor')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 6. YUMURTA ÜRETİMİ (EGG PRODUCTION)
-- =====================================================
INSERT INTO egg_production (id, poultry_id, date, total, cracked, dirty) VALUES
  ('yumurta-tavuk001-1206', 'tavuk-kumes-001', '2024-12-06', 142, 3, 5),
  ('yumurta-tavuk001-1205', 'tavuk-kumes-001', '2024-12-05', 138, 2, 4),
  ('yumurta-tavuk001-1204', 'tavuk-kumes-001', '2024-12-04', 145, 4, 3),
  ('yumurta-tavuk002-1206', 'tavuk-kumes-002', '2024-12-06', 115, 2, 3),
  ('yumurta-tavuk002-1205', 'tavuk-kumes-002', '2024-12-05', 112, 1, 2),
  ('yumurta-tavuk002-1204', 'tavuk-kumes-002', '2024-12-04', 118, 3, 4),
  ('yumurta-ordek004-1206', 'ordek-kumes-004', '2024-12-06', 28, 1, 2),
  ('yumurta-ordek004-1205', 'ordek-kumes-004', '2024-12-05', 25, 0, 1)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 7. SU KAYNAKLARI (WATER SOURCES)
-- =====================================================
INSERT INTO water_sources (id, name, type, lat, lng, capacity, current_level, status, last_cleaned) VALUES
  ('depo-ana-001', 'Ana Su Deposu', 'depo', 39.934, 32.862, 10000, 7500, 'aktif', '2024-11-15'),
  ('cesme-otlak-001', 'Otlak Sulağı 1', 'çeşme', 39.935, 32.861, 2000, 1800, 'aktif', '2024-12-01'),
  ('cesme-otlak-002', 'Otlak Sulağı 2', 'çeşme', 39.933, 32.863, 2000, 500, 'düşük', '2024-11-28'),
  ('cesme-ahir-001', 'Ahır Suluğu', 'çeşme', 39.932, 32.858, 500, 450, 'aktif', '2024-12-03'),
  ('depo-kumes-001', 'Kümes Su Deposu', 'depo', 39.931, 32.857, 1000, 200, 'kritik', '2024-11-20'),
  ('depo-yedek-001', 'Yedek Depo', 'depo', 39.930, 32.860, 5000, 5000, 'bakımda', '2024-10-15')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- VERİ KONTROLÜ
-- =====================================================
SELECT 'zones' as tablo, COUNT(*) as kayit_sayisi FROM zones
UNION ALL
SELECT 'animals', COUNT(*) FROM animals
UNION ALL
SELECT 'health_records', COUNT(*) FROM health_records
UNION ALL
SELECT 'alerts', COUNT(*) FROM alerts
UNION ALL
SELECT 'poultry', COUNT(*) FROM poultry
UNION ALL
SELECT 'egg_production', COUNT(*) FROM egg_production
UNION ALL
SELECT 'water_sources', COUNT(*) FROM water_sources;
