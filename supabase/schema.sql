-- AI Animal Tracking System - Supabase Database Schema
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- ZONES (Bölgeler)
-- =====================================================
CREATE TABLE zones (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  type VARCHAR(20) NOT NULL CHECK (type IN ('otlak', 'ahır', 'karantina', 'sulak')),
  coordinates JSONB NOT NULL DEFAULT '[]',
  capacity INTEGER NOT NULL DEFAULT 100,
  current_count INTEGER NOT NULL DEFAULT 0,
  color VARCHAR(7) NOT NULL DEFAULT '#3b82f6',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ANIMALS (Hayvanlar)
-- =====================================================
CREATE TABLE animals (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  tag VARCHAR(50) UNIQUE NOT NULL,
  type VARCHAR(50) NOT NULL,
  breed VARCHAR(100),
  gender VARCHAR(10) NOT NULL CHECK (gender IN ('erkek', 'dişi')),
  birth_date DATE,
  weight DECIMAL(10, 2),
  status VARCHAR(20) NOT NULL DEFAULT 'sağlıklı' CHECK (status IN ('sağlıklı', 'hasta', 'tedavide', 'karantina')),
  zone_id UUID REFERENCES zones(id) ON DELETE SET NULL,
  image_url TEXT,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- HEALTH RECORDS (Sağlık Kayıtları)
-- =====================================================
CREATE TABLE health_records (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL CHECK (type IN ('muayene', 'aşı', 'tedavi', 'kontrol')),
  description TEXT NOT NULL,
  vet_name VARCHAR(100),
  result VARCHAR(100),
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ALERTS (Uyarılar)
-- =====================================================
CREATE TABLE alerts (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  type VARCHAR(20) NOT NULL CHECK (type IN ('sağlık', 'güvenlik', 'sistem', 'aktivite')),
  severity VARCHAR(20) NOT NULL DEFAULT 'orta' CHECK (severity IN ('düşük', 'orta', 'yüksek', 'kritik')),
  title VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  animal_id UUID REFERENCES animals(id) ON DELETE SET NULL,
  zone_id UUID REFERENCES zones(id) ON DELETE SET NULL,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- POULTRY (Kanatlılar / Kümesler)
-- =====================================================
CREATE TABLE poultry (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  coop_id VARCHAR(50) UNIQUE NOT NULL,
  coop_name VARCHAR(100) NOT NULL,
  bird_type VARCHAR(20) NOT NULL CHECK (bird_type IN ('tavuk', 'hindi', 'ördek', 'kaz')),
  breed VARCHAR(100),
  count INTEGER NOT NULL DEFAULT 0,
  age_weeks INTEGER NOT NULL DEFAULT 0,
  status VARCHAR(20) NOT NULL DEFAULT 'aktif' CHECK (status IN ('aktif', 'karantina', 'tedavide')),
  avg_weight DECIMAL(10, 2) DEFAULT 0,
  feed_consumption DECIMAL(10, 2) DEFAULT 0,
  water_consumption DECIMAL(10, 2) DEFAULT 0,
  mortality_rate DECIMAL(5, 2) DEFAULT 0,
  temperature DECIMAL(5, 2) DEFAULT 22,
  humidity DECIMAL(5, 2) DEFAULT 65,
  light_hours INTEGER DEFAULT 16,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- EGG PRODUCTION (Yumurta Üretimi)
-- =====================================================
CREATE TABLE egg_production (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  poultry_id UUID NOT NULL REFERENCES poultry(id) ON DELETE CASCADE,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  total INTEGER NOT NULL DEFAULT 0,
  cracked INTEGER NOT NULL DEFAULT 0,
  dirty INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(poultry_id, date)
);

-- =====================================================
-- WATER SOURCES (Su Kaynakları)
-- =====================================================
CREATE TABLE water_sources (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  type VARCHAR(20) NOT NULL CHECK (type IN ('kuyu', 'çeşme', 'gölet', 'depo')),
  lat DECIMAL(10, 8) NOT NULL,
  lng DECIMAL(11, 8) NOT NULL,
  capacity DECIMAL(10, 2) NOT NULL DEFAULT 1000,
  current_level DECIMAL(10, 2) NOT NULL DEFAULT 500,
  status VARCHAR(20) NOT NULL DEFAULT 'aktif' CHECK (status IN ('aktif', 'düşük', 'kritik', 'bakımda')),
  last_cleaned DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- WEIGHT HISTORY (Ağırlık Geçmişi)
-- =====================================================
CREATE TABLE weight_history (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  animal_id UUID NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
  weight DECIMAL(10, 2) NOT NULL,
  date DATE NOT NULL DEFAULT CURRENT_DATE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- ACTIVITY LOGS (Aktivite Kayıtları)
-- =====================================================
CREATE TABLE activity_logs (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  animal_id UUID REFERENCES animals(id) ON DELETE CASCADE,
  zone_id UUID REFERENCES zones(id) ON DELETE SET NULL,
  activity_type VARCHAR(50) NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX idx_animals_status ON animals(status);
CREATE INDEX idx_animals_zone ON animals(zone_id);
CREATE INDEX idx_health_records_animal ON health_records(animal_id);
CREATE INDEX idx_health_records_date ON health_records(date);
CREATE INDEX idx_alerts_is_read ON alerts(is_read);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_egg_production_date ON egg_production(date);
CREATE INDEX idx_activity_logs_animal ON activity_logs(animal_id);
CREATE INDEX idx_activity_logs_created ON activity_logs(created_at);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================
ALTER TABLE animals ENABLE ROW LEVEL SECURITY;
ALTER TABLE zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE poultry ENABLE ROW LEVEL SECURITY;
ALTER TABLE egg_production ENABLE ROW LEVEL SECURITY;
ALTER TABLE water_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE weight_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;

-- Public read access (adjust as needed)
CREATE POLICY "Allow public read" ON animals FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON zones FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON health_records FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON alerts FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON poultry FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON egg_production FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON water_sources FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON weight_history FOR SELECT USING (true);
CREATE POLICY "Allow public read" ON activity_logs FOR SELECT USING (true);

-- Allow all operations for authenticated users (adjust as needed)
CREATE POLICY "Allow all for authenticated" ON animals FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON zones FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON health_records FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON alerts FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON poultry FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON egg_production FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON water_sources FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON weight_history FOR ALL USING (true);
CREATE POLICY "Allow all for authenticated" ON activity_logs FOR ALL USING (true);

-- =====================================================
-- SAMPLE DATA (Örnek Veriler)
-- =====================================================

-- Zones
INSERT INTO zones (name, type, capacity, current_count, color, coordinates) VALUES
('Otlak A', 'otlak', 50, 35, '#22c55e', '[{"lat": 39.925, "lng": 32.835}, {"lat": 39.930, "lng": 32.835}, {"lat": 39.930, "lng": 32.845}, {"lat": 39.925, "lng": 32.845}]'),
('Otlak B', 'otlak', 40, 28, '#3b82f6', '[{"lat": 39.920, "lng": 32.835}, {"lat": 39.925, "lng": 32.835}, {"lat": 39.925, "lng": 32.845}, {"lat": 39.920, "lng": 32.845}]'),
('Ana Ahır', 'ahır', 100, 45, '#8b5cf6', '[{"lat": 39.922, "lng": 32.850}, {"lat": 39.924, "lng": 32.850}, {"lat": 39.924, "lng": 32.855}, {"lat": 39.922, "lng": 32.855}]'),
('Karantina', 'karantina', 20, 3, '#ef4444', '[{"lat": 39.918, "lng": 32.850}, {"lat": 39.920, "lng": 32.850}, {"lat": 39.920, "lng": 32.853}, {"lat": 39.918, "lng": 32.853}]');

-- Animals
INSERT INTO animals (name, tag, type, breed, gender, birth_date, weight, status, zone_id, notes) VALUES
('Sarıkız', 'TR-001-2023', 'İnek', 'Holstein', 'dişi', '2021-03-15', 485, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Otlak A'), 'Süt verimi yüksek'),
('Karabaş', 'TR-002-2023', 'Boğa', 'Angus', 'erkek', '2020-06-20', 720, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Otlak B'), 'Damızlık'),
('Benekli', 'TR-003-2023', 'İnek', 'Simental', 'dişi', '2022-01-10', 420, 'tedavide', (SELECT id FROM zones WHERE name = 'Ana Ahır'), 'Ayak tedavisi devam ediyor'),
('Pamuk', 'TR-004-2023', 'Buzağı', 'Holstein', 'dişi', '2024-08-05', 85, 'sağlıklı', (SELECT id FROM zones WHERE name = 'Ana Ahır'), 'Anne: Sarıkız'),
('Tosun', 'TR-005-2023', 'Tosun', 'Angus', 'erkek', '2023-02-28', 380, 'karantina', (SELECT id FROM zones WHERE name = 'Karantina'), 'Gözlem altında');

-- Health Records
INSERT INTO health_records (animal_id, type, description, vet_name, result, date) VALUES
((SELECT id FROM animals WHERE tag = 'TR-001-2023'), 'muayene', 'Rutin sağlık kontrolü', 'Dr. Ahmet Yılmaz', 'Sağlıklı', '2024-01-10'),
((SELECT id FROM animals WHERE tag = 'TR-001-2023'), 'aşı', 'Şap aşısı', 'Dr. Ahmet Yılmaz', 'Tamamlandı', '2023-12-15'),
((SELECT id FROM animals WHERE tag = 'TR-003-2023'), 'tedavi', 'Ayak enfeksiyonu tedavisi', 'Dr. Fatma Demir', 'Devam ediyor', '2024-01-08'),
((SELECT id FROM animals WHERE tag = 'TR-005-2023'), 'kontrol', 'Karantina giriş kontrolü', 'Dr. Ahmet Yılmaz', 'Gözlem gerekli', '2024-01-12');

-- Alerts
INSERT INTO alerts (type, severity, title, message, animal_id, is_read) VALUES
('sağlık', 'yüksek', 'Tedavi Hatırlatması', 'Benekli (TR-003-2023) için antibiyotik zamanı', (SELECT id FROM animals WHERE tag = 'TR-003-2023'), false),
('güvenlik', 'kritik', 'Bölge İhlali', 'Tosun karantina bölgesinden çıkmaya çalıştı', (SELECT id FROM animals WHERE tag = 'TR-005-2023'), false),
('aktivite', 'orta', 'Düşük Aktivite', 'Sarıkız son 2 saattir hareketsiz', (SELECT id FROM animals WHERE tag = 'TR-001-2023'), false),
('sistem', 'düşük', 'Kamera Bağlantısı', 'Kamera 3 bağlantısı yeniden kuruldu', NULL, true);

-- Poultry
INSERT INTO poultry (coop_id, coop_name, bird_type, breed, count, age_weeks, status, avg_weight, feed_consumption, water_consumption, mortality_rate, temperature, humidity, light_hours, notes) VALUES
('COOP-001', 'Kümes A - Yumurtacı', 'tavuk', 'Lohmann Brown', 2500, 28, 'aktif', 1850, 275, 450, 0.8, 22, 65, 16, 'Verimlilik yüksek'),
('COOP-002', 'Kümes B - Etlik', 'tavuk', 'Ross 308', 3000, 6, 'aktif', 2100, 420, 580, 1.2, 24, 60, 18, 'Kesim yaklaşıyor'),
('COOP-003', 'Kümes C - Hindi', 'hindi', 'Bronz', 500, 16, 'aktif', 8500, 180, 220, 0.5, 20, 55, 14, 'İyi kondisyonda');

-- Egg Production
INSERT INTO egg_production (poultry_id, date, total, cracked, dirty) VALUES
((SELECT id FROM poultry WHERE coop_id = 'COOP-001'), CURRENT_DATE - 6, 2280, 45, 23),
((SELECT id FROM poultry WHERE coop_id = 'COOP-001'), CURRENT_DATE - 5, 2310, 38, 28),
((SELECT id FROM poultry WHERE coop_id = 'COOP-001'), CURRENT_DATE - 4, 2295, 42, 19),
((SELECT id FROM poultry WHERE coop_id = 'COOP-001'), CURRENT_DATE - 3, 2320, 35, 22),
((SELECT id FROM poultry WHERE coop_id = 'COOP-001'), CURRENT_DATE - 2, 2275, 48, 31),
((SELECT id FROM poultry WHERE coop_id = 'COOP-001'), CURRENT_DATE - 1, 2305, 40, 25),
((SELECT id FROM poultry WHERE coop_id = 'COOP-001'), CURRENT_DATE, 2290, 37, 20);

-- Water Sources
INSERT INTO water_sources (name, type, lat, lng, capacity, current_level, status, last_cleaned) VALUES
('Ana Kuyu', 'kuyu', 39.923, 32.840, 5000, 3500, 'aktif', '2024-01-01'),
('Otlak Çeşmesi', 'çeşme', 39.927, 32.838, 500, 480, 'aktif', '2024-01-10'),
('Gölet', 'gölet', 39.920, 32.842, 10000, 7500, 'aktif', '2023-12-15'),
('Yedek Depo', 'depo', 39.922, 32.852, 2000, 400, 'düşük', '2024-01-05');
