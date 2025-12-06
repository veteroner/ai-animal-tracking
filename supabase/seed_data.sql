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
  (gen_random_uuid(), 'Ana Otlak', 'otlak', '[{"lat": 39.935, "lng": 32.861}, {"lat": 39.936, "lng": 32.862}, {"lat": 39.934, "lng": 32.863}]'::jsonb, 60, 45, '#22c55e'),
  (gen_random_uuid(), 'Ahır 1', 'ahır', '[{"lat": 39.932, "lng": 32.858}, {"lat": 39.933, "lng": 32.859}, {"lat": 39.931, "lng": 32.860}]'::jsonb, 40, 32, '#3b82f6'),
  (gen_random_uuid(), 'Ahır 2 - Yavru', 'ahır', '[{"lat": 39.933, "lng": 32.856}, {"lat": 39.934, "lng": 32.857}, {"lat": 39.932, "lng": 32.858}]'::jsonb, 30, 28, '#8b5cf6'),
  (gen_random_uuid(), 'Su Deposu Alanı', 'sulak', '[{"lat": 39.934, "lng": 32.862}, {"lat": 39.935, "lng": 32.863}, {"lat": 39.933, "lng": 32.864}]'::jsonb, 20, 12, '#06b6d4'),
  (gen_random_uuid(), 'Karantina Bölgesi', 'karantina', '[{"lat": 39.936, "lng": 32.855}, {"lat": 39.937, "lng": 32.856}, {"lat": 39.935, "lng": 32.857}]'::jsonb, 10, 3, '#ef4444')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 2. HAYVANLAR (ANIMALS)
-- =====================================================
INSERT INTO animals (id, name, tag, type, breed, gender, birth_date, weight, status, zone_id, notes) VALUES
  (gen_random_uuid(), 'Sarıkız', 'TR-001', 'sığır', 'Simental', 'dişi', '2022-03-15', 452, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ana Otlak' LIMIT 1), 'Süt verimi yüksek, günlük 25L'),
  (gen_random_uuid(), 'Karabaş', 'TR-002', 'sığır', 'Holstein', 'erkek', '2021-06-20', 580, 'tedavide', (SELECT id FROM zones WHERE name = 'Ahır 1' LIMIT 1), 'Antibiyotik tedavisi devam ediyor'),
  (gen_random_uuid(), 'Benekli', 'TR-003', 'sığır', 'Jersey', 'dişi', '2023-01-10', 385, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ana Otlak' LIMIT 1), 'Gebe, 5. ay'),
  (gen_random_uuid(), 'Pamuk', 'TR-004', 'koyun', 'Merinos', 'dişi', '2023-05-01', 68, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ana Otlak' LIMIT 1), 'Yün kalitesi A sınıfı'),
  (gen_random_uuid(), 'Kıvırcık', 'TR-005', 'koyun', 'Kıvırcık', 'erkek', '2022-08-15', 75, 'hasta', (SELECT id FROM zones WHERE name = 'Karantina Bölgesi' LIMIT 1), 'Parazit tedavisi'),
  (gen_random_uuid(), 'Beyaz', 'TR-006', 'keçi', 'Saanen', 'dişi', '2023-02-28', 48, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ana Otlak' LIMIT 1), 'Süt keçisi, günlük 3L'),
  (gen_random_uuid(), 'Boynuzlu', 'TR-007', 'sığır', 'Angus', 'erkek', '2020-11-05', 720, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ahır 1' LIMIT 1), 'Damızlık boğa'),
  (gen_random_uuid(), 'Minik', 'TR-008', 'sığır', 'Simental', 'dişi', '2024-06-01', 180, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ahır 2 - Yavru' LIMIT 1), 'Buzağı, gelişimi normal'),
  (gen_random_uuid(), 'Tüylü', 'TR-009', 'koyun', 'Merinos', 'dişi', '2022-04-10', 62, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ana Otlak' LIMIT 1), NULL),
  (gen_random_uuid(), 'Çizgili', 'TR-010', 'keçi', 'Kıl Keçisi', 'erkek', '2023-07-20', 55, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ana Otlak' LIMIT 1), NULL)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 3. SAĞLIK KAYITLARI (HEALTH RECORDS)
-- =====================================================
INSERT INTO health_records (id, animal_id, type, description, vet_name, result, date) VALUES
  (gen_random_uuid(), (SELECT id FROM animals WHERE tag = 'TR-001' LIMIT 1), 'kontrol', 'Rutin sağlık kontrolü yapıldı', 'Dr. Ahmet Yılmaz', 'Sağlık durumu iyi, aşılar güncel', '2024-12-01'),
  (gen_random_uuid(), (SELECT id FROM animals WHERE tag = 'TR-002' LIMIT 1), 'tedavi', 'Üst solunum yolu enfeksiyonu tedavisi', 'Dr. Ahmet Yılmaz', 'Antibiyotik başlandı, 7 gün devam edilecek', '2024-12-02'),
  (gen_random_uuid(), (SELECT id FROM animals WHERE tag = 'TR-003' LIMIT 1), 'muayene', 'Gebelik kontrolü', 'Dr. Fatma Demir', 'Gebelik 5. ayda, sağlıklı', '2024-11-28'),
  (gen_random_uuid(), (SELECT id FROM animals WHERE tag = 'TR-005' LIMIT 1), 'tedavi', 'Parazit tedavisi başlatıldı', 'Dr. Fatma Demir', 'Antiparaziter ilaç verildi', '2024-11-30'),
  (gen_random_uuid(), (SELECT id FROM animals WHERE tag = 'TR-004' LIMIT 1), 'aşı', 'Şap aşısı yapıldı', 'Dr. Ahmet Yılmaz', 'Aşı başarılı', '2024-11-25'),
  (gen_random_uuid(), (SELECT id FROM animals WHERE tag = 'TR-007' LIMIT 1), 'kontrol', 'Damızlık değerlendirmesi', 'Dr. Mehmet Kaya', 'Sperm kalitesi çok iyi', '2024-11-20'),
  (gen_random_uuid(), (SELECT id FROM animals WHERE tag = 'TR-008' LIMIT 1), 'kontrol', 'Buzağı gelişim kontrolü', 'Dr. Fatma Demir', 'Gelişim normal, kilo artışı iyi', '2024-12-03')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 4. UYARILAR (ALERTS)
-- =====================================================
INSERT INTO alerts (id, type, severity, title, message, animal_id, zone_id, is_read) VALUES
  (gen_random_uuid(), 'sağlık', 'yüksek', 'Yüksek Ateş Tespit Edildi', 'TR-002 numaralı hayvanda 40.5°C ateş tespit edildi', (SELECT id FROM animals WHERE tag = 'TR-002' LIMIT 1), NULL, false),
  (gen_random_uuid(), 'güvenlik', 'kritik', 'Bölge İhlali', '3 hayvan karantina bölgesine girdi', NULL, (SELECT id FROM zones WHERE name = 'Karantina Bölgesi' LIMIT 1), false),
  (gen_random_uuid(), 'aktivite', 'orta', 'Anormal Hareket', 'TR-005 numaralı hayvanda anormal hareket paterni tespit edildi', (SELECT id FROM animals WHERE tag = 'TR-005' LIMIT 1), NULL, false),
  (gen_random_uuid(), 'sağlık', 'yüksek', 'Yem Tüketimi Düşük', 'TR-005 24 saattir yem yemedi', (SELECT id FROM animals WHERE tag = 'TR-005' LIMIT 1), NULL, true),
  (gen_random_uuid(), 'sistem', 'düşük', 'Kamera Bağlantısı', 'Kamera 3 bağlantısı zayıf', NULL, NULL, true),
  (gen_random_uuid(), 'aktivite', 'orta', 'Sürüden Ayrılma', 'TR-004 sürüden ayrıldı', (SELECT id FROM animals WHERE tag = 'TR-004' LIMIT 1), NULL, true),
  (gen_random_uuid(), 'sistem', 'düşük', 'Bakım Hatırlatması', 'Su deposu bakım zamanı geldi', NULL, (SELECT id FROM zones WHERE name = 'Su Deposu Alanı' LIMIT 1), false)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 5. KANATLILAR (POULTRY)
-- =====================================================
INSERT INTO poultry (id, coop_id, coop_name, bird_type, breed, count, age_weeks, status, avg_weight, feed_consumption, water_consumption, mortality_rate, temperature, humidity, light_hours, notes) VALUES
  (gen_random_uuid(), 'COOP-001', 'Kümes 1 - Yumurta', 'tavuk', 'Rhode Island Red', 150, 32, 'aktif', 2.5, 18.5, 35.0, 0.5, 22.0, 65.0, 16, 'Yumurta üretimi yüksek'),
  (gen_random_uuid(), 'COOP-002', 'Kümes 2 - Yumurta', 'tavuk', 'Leghorn', 120, 28, 'aktif', 2.2, 15.0, 30.0, 0.3, 21.5, 62.0, 16, 'Beyaz yumurta üretimi'),
  (gen_random_uuid(), 'COOP-003', 'Kümes 3 - Hindi', 'hindi', 'Bronze', 45, 20, 'aktif', 8.5, 45.0, 60.0, 1.0, 20.0, 58.0, 14, 'Kesim için besleniyor'),
  (gen_random_uuid(), 'COOP-004', 'Kümes 4 - Ördek', 'ördek', 'Pekin', 60, 16, 'aktif', 3.2, 12.0, 40.0, 0.8, 19.0, 70.0, 14, 'Su havuzu mevcut'),
  (gen_random_uuid(), 'COOP-005', 'Kümes 5 - Kaz', 'kaz', 'Toulouse', 25, 24, 'karantina', 5.5, 20.0, 45.0, 2.0, 18.0, 55.0, 12, 'Sağlık kontrolü yapılıyor')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 6. YUMURTA ÜRETİMİ (EGG PRODUCTION)
-- =====================================================
INSERT INTO egg_production (id, poultry_id, date, total, cracked, dirty) VALUES
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 1 - Yumurta' LIMIT 1), '2024-12-06', 142, 3, 5),
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 1 - Yumurta' LIMIT 1), '2024-12-05', 138, 2, 4),
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 1 - Yumurta' LIMIT 1), '2024-12-04', 145, 4, 3),
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 2 - Yumurta' LIMIT 1), '2024-12-06', 115, 2, 3),
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 2 - Yumurta' LIMIT 1), '2024-12-05', 112, 1, 2),
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 2 - Yumurta' LIMIT 1), '2024-12-04', 118, 3, 4),
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 4 - Ördek' LIMIT 1), '2024-12-06', 28, 1, 2),
  (gen_random_uuid(), (SELECT id FROM poultry WHERE coop_name = 'Kümes 4 - Ördek' LIMIT 1), '2024-12-05', 25, 0, 1)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- 7. SU KAYNAKLARI (WATER SOURCES)
-- =====================================================
INSERT INTO water_sources (id, name, type, lat, lng, capacity, current_level, status, last_cleaned) VALUES
  (gen_random_uuid(), 'Ana Su Deposu', 'depo', 39.934, 32.862, 10000, 7500, 'aktif', '2024-11-15'),
  (gen_random_uuid(), 'Otlak Sulağı 1', 'çeşme', 39.935, 32.861, 2000, 1800, 'aktif', '2024-12-01'),
  (gen_random_uuid(), 'Otlak Sulağı 2', 'çeşme', 39.933, 32.863, 2000, 500, 'düşük', '2024-11-28'),
  (gen_random_uuid(), 'Ahır Suluğu', 'çeşme', 39.932, 32.858, 500, 450, 'aktif', '2024-12-03'),
  (gen_random_uuid(), 'Kümes Su Deposu', 'depo', 39.931, 32.857, 1000, 200, 'kritik', '2024-11-20'),
  (gen_random_uuid(), 'Yedek Depo', 'depo', 39.930, 32.860, 5000, 5000, 'bakımda', '2024-10-15')
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
