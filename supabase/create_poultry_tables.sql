-- =====================================================
-- Kanatlı Hayvan (Kümes) Modülü - Supabase Tabloları
-- =====================================================
-- Bu dosyayı Supabase SQL Editor'de çalıştırın
-- Tablo oluşturma sırası önemli (foreign key bağımlılıkları)
-- =====================================================

-- =====================================================
-- 1. Kümes (Coop) Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS coops (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255),
    capacity INTEGER DEFAULT 0,
    coop_type VARCHAR(50) DEFAULT 'standard', -- standard, broiler, layer, breeder
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_coops_active ON coops(is_active);
CREATE INDEX IF NOT EXISTS idx_coops_type ON coops(coop_type);

-- RLS
ALTER TABLE coops ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to coops" ON coops FOR ALL USING (true);

-- =====================================================
-- 2. Kümes Bölgeleri Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS coop_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coop_id UUID REFERENCES coops(id) ON DELETE CASCADE,
    zone_type VARCHAR(50) NOT NULL, -- feeder, waterer, roost, nest_box, dust_bath, free_range, brooder, quarantine
    name VARCHAR(100) NOT NULL,
    bbox_x1 INTEGER NOT NULL,
    bbox_y1 INTEGER NOT NULL,
    bbox_x2 INTEGER NOT NULL,
    bbox_y2 INTEGER NOT NULL,
    capacity INTEGER DEFAULT 0,
    current_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_coop_zones_coop ON coop_zones(coop_id);
CREATE INDEX IF NOT EXISTS idx_coop_zones_type ON coop_zones(zone_type);
CREATE INDEX IF NOT EXISTS idx_coop_zones_active ON coop_zones(is_active);

-- RLS
ALTER TABLE coop_zones ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to coop_zones" ON coop_zones FOR ALL USING (true);

-- =====================================================
-- 3. Kanatlı Hayvan Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS poultry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_id VARCHAR(50) UNIQUE, -- Küpe/halka numarası
    name VARCHAR(100),
    poultry_type VARCHAR(50) NOT NULL, -- chicken, rooster, chick, turkey, goose, duck, quail, guinea_fowl
    breed VARCHAR(100),
    color VARCHAR(50),
    gender VARCHAR(10), -- male, female, unknown
    coop_id UUID REFERENCES coops(id) ON DELETE SET NULL,
    birth_date DATE,
    acquisition_date DATE,
    health_status VARCHAR(50) DEFAULT 'healthy', -- healthy, sick, injured, molting, broody, stressed
    weight_grams INTEGER,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_poultry_coop ON poultry(coop_id);
CREATE INDEX IF NOT EXISTS idx_poultry_type ON poultry(poultry_type);
CREATE INDEX IF NOT EXISTS idx_poultry_health ON poultry(health_status);
CREATE INDEX IF NOT EXISTS idx_poultry_active ON poultry(is_active);
CREATE INDEX IF NOT EXISTS idx_poultry_tag ON poultry(tag_id);

-- RLS
ALTER TABLE poultry ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to poultry" ON poultry FOR ALL USING (true);

-- =====================================================
-- 4. Kanatlı Tespit Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS poultry_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poultry_id UUID REFERENCES poultry(id) ON DELETE CASCADE,
    camera_id VARCHAR(50),
    coop_id UUID REFERENCES coops(id) ON DELETE SET NULL,
    zone_id UUID REFERENCES coop_zones(id) ON DELETE SET NULL,
    confidence DECIMAL(5,4) NOT NULL,
    bbox_x1 INTEGER NOT NULL,
    bbox_y1 INTEGER NOT NULL,
    bbox_x2 INTEGER NOT NULL,
    bbox_y2 INTEGER NOT NULL,
    behavior VARCHAR(50), -- feeding, drinking, roosting, nesting, etc.
    health_status VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_poultry_det_poultry ON poultry_detections(poultry_id);
CREATE INDEX IF NOT EXISTS idx_poultry_det_coop ON poultry_detections(coop_id);
CREATE INDEX IF NOT EXISTS idx_poultry_det_zone ON poultry_detections(zone_id);
CREATE INDEX IF NOT EXISTS idx_poultry_det_behavior ON poultry_detections(behavior);
CREATE INDEX IF NOT EXISTS idx_poultry_det_timestamp ON poultry_detections(timestamp);
CREATE INDEX IF NOT EXISTS idx_poultry_det_time_desc ON poultry_detections(timestamp DESC);

-- Partitioning için timestamp
CREATE INDEX IF NOT EXISTS idx_poultry_det_ts_range ON poultry_detections USING BRIN (timestamp);

-- RLS
ALTER TABLE poultry_detections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to poultry_detections" ON poultry_detections FOR ALL USING (true);

-- =====================================================
-- 5. Yumurta Üretimi Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS egg_production (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coop_id UUID REFERENCES coops(id) ON DELETE CASCADE,
    nest_box_id UUID REFERENCES coop_zones(id) ON DELETE SET NULL,
    poultry_id UUID REFERENCES poultry(id) ON DELETE SET NULL,
    egg_count INTEGER DEFAULT 1,
    egg_quality VARCHAR(50) DEFAULT 'normal', -- normal, soft_shell, double_yolk, blood_spot, small, large
    egg_weight_grams INTEGER,
    collection_time TIMESTAMPTZ,
    recorded_by VARCHAR(100),
    notes TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_eggs_coop ON egg_production(coop_id);
CREATE INDEX IF NOT EXISTS idx_eggs_poultry ON egg_production(poultry_id);
CREATE INDEX IF NOT EXISTS idx_eggs_quality ON egg_production(egg_quality);
CREATE INDEX IF NOT EXISTS idx_eggs_recorded ON egg_production(recorded_at);
CREATE INDEX IF NOT EXISTS idx_eggs_date ON egg_production(DATE(recorded_at));

-- RLS
ALTER TABLE egg_production ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to egg_production" ON egg_production FOR ALL USING (true);

-- =====================================================
-- 6. Kanatlı Sağlık Kayıtları Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS poultry_health_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poultry_id UUID REFERENCES poultry(id) ON DELETE CASCADE,
    coop_id UUID REFERENCES coops(id) ON DELETE SET NULL,
    health_status VARCHAR(50) NOT NULL,
    symptoms TEXT[], -- Array of symptoms
    diagnosis TEXT,
    treatment TEXT,
    medication VARCHAR(255),
    veterinarian VARCHAR(100),
    cost DECIMAL(10,2),
    notes TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    is_resolved BOOLEAN DEFAULT false
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_health_poultry ON poultry_health_records(poultry_id);
CREATE INDEX IF NOT EXISTS idx_health_coop ON poultry_health_records(coop_id);
CREATE INDEX IF NOT EXISTS idx_health_status ON poultry_health_records(health_status);
CREATE INDEX IF NOT EXISTS idx_health_resolved ON poultry_health_records(is_resolved);
CREATE INDEX IF NOT EXISTS idx_health_recorded ON poultry_health_records(recorded_at);

-- RLS
ALTER TABLE poultry_health_records ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to poultry_health_records" ON poultry_health_records FOR ALL USING (true);

-- =====================================================
-- 7. Davranış Logları Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS poultry_behavior_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    poultry_id UUID REFERENCES poultry(id) ON DELETE CASCADE,
    coop_id UUID REFERENCES coops(id) ON DELETE SET NULL,
    zone_id UUID REFERENCES coop_zones(id) ON DELETE SET NULL,
    behavior VARCHAR(50) NOT NULL, -- feeding, drinking, roosting, nesting, dust_bathing, preening, walking, running, resting, foraging, flocking, mating, brooding, feather_pecking, panic, lethargy, isolation
    duration_seconds INTEGER,
    intensity VARCHAR(20), -- low, medium, high
    is_abnormal BOOLEAN DEFAULT false,
    notes TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_behavior_poultry ON poultry_behavior_logs(poultry_id);
CREATE INDEX IF NOT EXISTS idx_behavior_coop ON poultry_behavior_logs(coop_id);
CREATE INDEX IF NOT EXISTS idx_behavior_zone ON poultry_behavior_logs(zone_id);
CREATE INDEX IF NOT EXISTS idx_behavior_type ON poultry_behavior_logs(behavior);
CREATE INDEX IF NOT EXISTS idx_behavior_abnormal ON poultry_behavior_logs(is_abnormal);
CREATE INDEX IF NOT EXISTS idx_behavior_timestamp ON poultry_behavior_logs(timestamp);

-- RLS
ALTER TABLE poultry_behavior_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to poultry_behavior_logs" ON poultry_behavior_logs FOR ALL USING (true);

-- =====================================================
-- 8. Kanatlı Uyarıları Tablosu
-- =====================================================
CREATE TABLE IF NOT EXISTS poultry_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    coop_id UUID REFERENCES coops(id) ON DELETE CASCADE,
    poultry_id UUID REFERENCES poultry(id) ON DELETE SET NULL,
    alert_type VARCHAR(50) NOT NULL, -- panic, cannibalism, health_issue, stress, low_production, molting, broody
    severity VARCHAR(20) NOT NULL, -- info, warning, critical
    title VARCHAR(255) NOT NULL,
    message TEXT,
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(100),
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_alerts_coop ON poultry_alerts(coop_id);
CREATE INDEX IF NOT EXISTS idx_alerts_poultry ON poultry_alerts(poultry_id);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON poultry_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON poultry_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON poultry_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON poultry_alerts(created_at);

-- RLS
ALTER TABLE poultry_alerts ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all access to poultry_alerts" ON poultry_alerts FOR ALL USING (true);

-- =====================================================
-- 9. Günlük Üretim Özeti View
-- =====================================================
CREATE OR REPLACE VIEW daily_egg_summary AS
SELECT 
    DATE(recorded_at) as production_date,
    coop_id,
    COUNT(*) as total_records,
    SUM(egg_count) as total_eggs,
    COUNT(CASE WHEN egg_quality = 'normal' THEN 1 END) as normal_eggs,
    COUNT(CASE WHEN egg_quality = 'soft_shell' THEN 1 END) as soft_shell_eggs,
    COUNT(CASE WHEN egg_quality = 'double_yolk' THEN 1 END) as double_yolk_eggs,
    ROUND(AVG(egg_weight_grams)::numeric, 1) as avg_weight_grams
FROM egg_production
GROUP BY DATE(recorded_at), coop_id
ORDER BY production_date DESC;

-- =====================================================
-- 10. Sürü Özeti View
-- =====================================================
CREATE OR REPLACE VIEW flock_summary AS
SELECT 
    c.id as coop_id,
    c.name as coop_name,
    COUNT(p.id) as total_count,
    COUNT(CASE WHEN p.poultry_type = 'chicken' THEN 1 END) as chicken_count,
    COUNT(CASE WHEN p.poultry_type = 'rooster' THEN 1 END) as rooster_count,
    COUNT(CASE WHEN p.poultry_type = 'chick' THEN 1 END) as chick_count,
    COUNT(CASE WHEN p.poultry_type = 'turkey' THEN 1 END) as turkey_count,
    COUNT(CASE WHEN p.poultry_type = 'duck' THEN 1 END) as duck_count,
    COUNT(CASE WHEN p.poultry_type = 'goose' THEN 1 END) as goose_count,
    COUNT(CASE WHEN p.health_status = 'healthy' THEN 1 END) as healthy_count,
    COUNT(CASE WHEN p.health_status = 'sick' THEN 1 END) as sick_count,
    COUNT(CASE WHEN p.health_status = 'molting' THEN 1 END) as molting_count,
    COUNT(CASE WHEN p.health_status = 'broody' THEN 1 END) as broody_count
FROM coops c
LEFT JOIN poultry p ON p.coop_id = c.id AND p.is_active = true
WHERE c.is_active = true
GROUP BY c.id, c.name;

-- =====================================================
-- 11. Updated Trigger Fonksiyonu
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_coops_updated_at ON coops;
CREATE TRIGGER update_coops_updated_at
    BEFORE UPDATE ON coops
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_coop_zones_updated_at ON coop_zones;
CREATE TRIGGER update_coop_zones_updated_at
    BEFORE UPDATE ON coop_zones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_poultry_updated_at ON poultry;
CREATE TRIGGER update_poultry_updated_at
    BEFORE UPDATE ON poultry
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Bilgi Mesajı
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Kanatlı Hayvan (Kümes) tabloları başarıyla oluşturuldu!';
    RAISE NOTICE '';
    RAISE NOTICE 'Oluşturulan tablolar:';
    RAISE NOTICE '  1. coops - Kümes bilgileri';
    RAISE NOTICE '  2. coop_zones - Kümes bölgeleri';
    RAISE NOTICE '  3. poultry - Kanatlı hayvan kayıtları';
    RAISE NOTICE '  4. poultry_detections - Tespit kayıtları';
    RAISE NOTICE '  5. egg_production - Yumurta üretimi';
    RAISE NOTICE '  6. poultry_health_records - Sağlık kayıtları';
    RAISE NOTICE '  7. poultry_behavior_logs - Davranış logları';
    RAISE NOTICE '  8. poultry_alerts - Uyarılar';
    RAISE NOTICE '';
    RAISE NOTICE 'Oluşturulan view''ler:';
    RAISE NOTICE '  - daily_egg_summary';
    RAISE NOTICE '  - flock_summary';
END $$;
