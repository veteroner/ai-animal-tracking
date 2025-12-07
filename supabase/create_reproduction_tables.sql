-- AI Animal Tracking - Reproduction Tables
-- =====================================================
-- Bu dosyayı Supabase SQL Editor'de ÖNCE çalıştırın
-- Ardından seed_reproduction.sql dosyasını çalıştırın

-- =====================================================
-- ESTRUS DETECTIONS (Kızgınlık Tespitleri)
-- =====================================================
CREATE TABLE IF NOT EXISTS estrus_detections (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  animal_id TEXT NOT NULL,
  detection_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  behaviors JSONB DEFAULT '{}',
  confidence DECIMAL(3, 2) DEFAULT 0.0,
  optimal_breeding_start TIMESTAMP WITH TIME ZONE,
  optimal_breeding_end TIMESTAMP WITH TIME ZONE,
  status TEXT DEFAULT 'detected' CHECK (status IN ('detected', 'confirmed', 'bred', 'missed', 'false_positive')),
  notified BOOLEAN DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PREGNANCIES (Gebelik Kayıtları)
-- =====================================================
CREATE TABLE IF NOT EXISTS pregnancies (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  animal_id TEXT NOT NULL,
  breeding_date DATE NOT NULL,
  expected_birth_date DATE NOT NULL,
  actual_birth_date DATE,
  sire_id TEXT,
  breeding_method TEXT DEFAULT 'doğal' CHECK (breeding_method IN ('doğal', 'suni_tohumlama', 'embriyo_transferi')),
  pregnancy_confirmed BOOLEAN DEFAULT FALSE,
  confirmation_date DATE,
  confirmation_method TEXT CHECK (confirmation_method IN ('manual', 'ultrasound', 'blood_test', 'observation')),
  status TEXT DEFAULT 'aktif' CHECK (status IN ('aktif', 'doğum_yaptı', 'düşük', 'iptal')),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- BIRTHS (Doğum Kayıtları)
-- =====================================================
CREATE TABLE IF NOT EXISTS births (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  mother_id TEXT NOT NULL,
  pregnancy_id TEXT REFERENCES pregnancies(id) ON DELETE SET NULL,
  birth_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  offspring_count INTEGER DEFAULT 1,
  offspring_ids JSONB DEFAULT '[]',
  birth_type TEXT DEFAULT 'normal' CHECK (birth_type IN ('normal', 'müdahaleli', 'sezaryen')),
  birth_weight DECIMAL(10, 2),
  complications TEXT,
  vet_assisted BOOLEAN DEFAULT FALSE,
  vet_name TEXT,
  ai_predicted_at TIMESTAMP WITH TIME ZONE,
  ai_detected_at TIMESTAMP WITH TIME ZONE,
  prediction_accuracy_hours DECIMAL(10, 2),
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- BREEDING RECORDS (Çiftleştirme Kayıtları)
-- =====================================================
CREATE TABLE IF NOT EXISTS breeding_records (
  id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  female_id TEXT NOT NULL,
  male_id TEXT,
  breeding_date DATE NOT NULL,
  breeding_method TEXT DEFAULT 'doğal' CHECK (breeding_method IN ('doğal', 'suni_tohumlama', 'embriyo_transferi')),
  technician_name TEXT,
  semen_batch TEXT,
  estrus_detection_id TEXT REFERENCES estrus_detections(id) ON DELETE SET NULL,
  success BOOLEAN,
  pregnancy_id TEXT REFERENCES pregnancies(id) ON DELETE SET NULL,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES (Performans için)
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_estrus_animal ON estrus_detections(animal_id);
CREATE INDEX IF NOT EXISTS idx_estrus_status ON estrus_detections(status);
CREATE INDEX IF NOT EXISTS idx_estrus_detection_time ON estrus_detections(detection_time);

CREATE INDEX IF NOT EXISTS idx_pregnancies_animal ON pregnancies(animal_id);
CREATE INDEX IF NOT EXISTS idx_pregnancies_status ON pregnancies(status);
CREATE INDEX IF NOT EXISTS idx_pregnancies_due_date ON pregnancies(expected_birth_date);

CREATE INDEX IF NOT EXISTS idx_births_mother ON births(mother_id);
CREATE INDEX IF NOT EXISTS idx_births_date ON births(birth_date);

CREATE INDEX IF NOT EXISTS idx_breeding_female ON breeding_records(female_id);
CREATE INDEX IF NOT EXISTS idx_breeding_date ON breeding_records(breeding_date);

-- =====================================================
-- ROW LEVEL SECURITY (RLS)
-- =====================================================
ALTER TABLE estrus_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE pregnancies ENABLE ROW LEVEL SECURITY;
ALTER TABLE births ENABLE ROW LEVEL SECURITY;
ALTER TABLE breeding_records ENABLE ROW LEVEL SECURITY;

-- Public read policies
CREATE POLICY "Allow public read estrus" ON estrus_detections FOR SELECT USING (true);
CREATE POLICY "Allow public read pregnancies" ON pregnancies FOR SELECT USING (true);
CREATE POLICY "Allow public read births" ON births FOR SELECT USING (true);
CREATE POLICY "Allow public read breeding" ON breeding_records FOR SELECT USING (true);

-- Public write policies (development only - production'da kısıtlayın)
CREATE POLICY "Allow public insert estrus" ON estrus_detections FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public insert pregnancies" ON pregnancies FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public insert births" ON births FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public insert breeding" ON breeding_records FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public update estrus" ON estrus_detections FOR UPDATE USING (true);
CREATE POLICY "Allow public update pregnancies" ON pregnancies FOR UPDATE USING (true);
CREATE POLICY "Allow public update births" ON births FOR UPDATE USING (true);
CREATE POLICY "Allow public update breeding" ON breeding_records FOR UPDATE USING (true);

CREATE POLICY "Allow public delete estrus" ON estrus_detections FOR DELETE USING (true);
CREATE POLICY "Allow public delete pregnancies" ON pregnancies FOR DELETE USING (true);
CREATE POLICY "Allow public delete births" ON births FOR DELETE USING (true);
CREATE POLICY "Allow public delete breeding" ON breeding_records FOR DELETE USING (true);

-- =====================================================
-- VERİFİKASYON
-- =====================================================
SELECT 'Tablolar başarıyla oluşturuldu!' as message;

SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('estrus_detections', 'pregnancies', 'births', 'breeding_records');
