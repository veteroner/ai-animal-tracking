-- =====================================================
-- Kanatlı Hayvan (Kümes) Modülü - Örnek Veriler
-- =====================================================
-- Bu dosyayı create_poultry_tables.sql çalıştırıldıktan sonra çalıştırın
-- =====================================================

-- =====================================================
-- 1. Örnek Kümesler
-- =====================================================
INSERT INTO coops (id, name, location, capacity, coop_type, description) VALUES
('coop-001', 'Ana Kümes', 'Çiftlik Merkezi - Bina 1', 200, 'layer', 'Yumurtacı tavukların ana kümesi'),
('coop-002', 'Broiler Kümesi', 'Çiftlik Merkezi - Bina 2', 500, 'broiler', 'Etlik tavuk yetiştirme kümesi'),
('coop-003', 'Civciv Kümesi', 'Çiftlik Merkezi - Bina 3', 100, 'standard', 'Civciv büyütme kümesi'),
('coop-004', 'Hindi Kümesi', 'Çiftlik Kuzey', 50, 'standard', 'Hindi yetiştirme alanı'),
('coop-005', 'Serbest Gezinti', 'Dış Alan', 150, 'standard', 'Serbest gezinti alanı');

-- =====================================================
-- 2. Kümes Bölgeleri
-- =====================================================
INSERT INTO coop_zones (id, coop_id, zone_type, name, bbox_x1, bbox_y1, bbox_x2, bbox_y2, capacity) VALUES
-- Ana Kümes Bölgeleri
('zone-001', 'coop-001', 'feeder', 'Ana Yemlik', 100, 100, 300, 200, 40),
('zone-002', 'coop-001', 'waterer', 'Suluk 1', 350, 100, 450, 180, 20),
('zone-003', 'coop-001', 'waterer', 'Suluk 2', 500, 100, 600, 180, 20),
('zone-004', 'coop-001', 'roost', 'Tünek Alanı', 100, 300, 600, 450, 60),
('zone-005', 'coop-001', 'nest_box', 'Yumurtlama Kutuları', 650, 100, 800, 300, 20),
('zone-006', 'coop-001', 'dust_bath', 'Toz Banyosu', 100, 500, 250, 600, 15),

-- Broiler Kümesi
('zone-007', 'coop-002', 'feeder', 'Broiler Yemlik 1', 100, 100, 400, 200, 80),
('zone-008', 'coop-002', 'feeder', 'Broiler Yemlik 2', 450, 100, 750, 200, 80),
('zone-009', 'coop-002', 'waterer', 'Broiler Suluk', 200, 250, 600, 350, 50),

-- Civciv Kümesi
('zone-010', 'coop-003', 'brooder', 'Civciv Isıtma Alanı', 100, 100, 400, 300, 50),
('zone-011', 'coop-003', 'feeder', 'Civciv Yemliği', 100, 350, 250, 450, 30),
('zone-012', 'coop-003', 'waterer', 'Civciv Suluğu', 300, 350, 400, 450, 20);

-- =====================================================
-- 3. Kanatlı Hayvanlar
-- =====================================================
INSERT INTO poultry (id, tag_id, name, poultry_type, breed, color, gender, coop_id, birth_date, health_status) VALUES
-- Ana Kümes Tavukları
('ptr-001', 'T-001', 'Pamuk', 'chicken', 'Leghorn', 'white', 'female', 'coop-001', '2024-03-15', 'healthy'),
('ptr-002', 'T-002', 'Sarı', 'chicken', 'Rhode Island Red', 'brown', 'female', 'coop-001', '2024-03-15', 'healthy'),
('ptr-003', 'T-003', 'Benekli', 'chicken', 'Plymouth Rock', 'barred', 'female', 'coop-001', '2024-03-20', 'healthy'),
('ptr-004', 'T-004', 'Kara', 'chicken', 'Australorp', 'black', 'female', 'coop-001', '2024-02-10', 'healthy'),
('ptr-005', 'T-005', 'Tüylü', 'chicken', 'Silkie', 'white', 'female', 'coop-001', '2024-04-01', 'broody'),
('ptr-006', 'T-006', NULL, 'chicken', 'Leghorn', 'white', 'female', 'coop-001', '2024-03-15', 'healthy'),
('ptr-007', 'T-007', NULL, 'chicken', 'Leghorn', 'white', 'female', 'coop-001', '2024-03-18', 'molting'),
('ptr-008', 'T-008', NULL, 'chicken', 'Rhode Island Red', 'brown', 'female', 'coop-001', '2024-03-20', 'healthy'),
('ptr-009', 'T-009', NULL, 'chicken', 'Rhode Island Red', 'brown', 'female', 'coop-001', '2024-03-22', 'healthy'),
('ptr-010', 'T-010', NULL, 'chicken', 'Plymouth Rock', 'barred', 'female', 'coop-001', '2024-03-25', 'healthy'),

-- Horozlar
('ptr-011', 'H-001', 'Kral', 'rooster', 'Rhode Island Red', 'brown', 'male', 'coop-001', '2024-01-10', 'healthy'),
('ptr-012', 'H-002', 'Sultan', 'rooster', 'Leghorn', 'white', 'male', 'coop-001', '2024-01-15', 'healthy'),

-- Civcivler
('ptr-013', 'C-001', NULL, 'chick', 'Mixed', 'yellow', 'unknown', 'coop-003', '2024-11-20', 'healthy'),
('ptr-014', 'C-002', NULL, 'chick', 'Mixed', 'yellow', 'unknown', 'coop-003', '2024-11-20', 'healthy'),
('ptr-015', 'C-003', NULL, 'chick', 'Mixed', 'brown', 'unknown', 'coop-003', '2024-11-22', 'healthy'),
('ptr-016', 'C-004', NULL, 'chick', 'Mixed', 'brown', 'unknown', 'coop-003', '2024-11-22', 'healthy'),
('ptr-017', 'C-005', NULL, 'chick', 'Mixed', 'black', 'unknown', 'coop-003', '2024-11-25', 'healthy'),

-- Hindiler
('ptr-018', 'HN-001', 'Büyük Tom', 'turkey', 'Bronze', 'bronze', 'male', 'coop-004', '2024-05-01', 'healthy'),
('ptr-019', 'HN-002', 'Hindi Ana', 'turkey', 'Bronze', 'bronze', 'female', 'coop-004', '2024-05-05', 'healthy'),
('ptr-020', 'HN-003', NULL, 'turkey', 'White', 'white', 'female', 'coop-004', '2024-06-01', 'healthy'),

-- Ördekler
('ptr-021', 'O-001', 'Vakvak', 'duck', 'Pekin', 'white', 'female', 'coop-005', '2024-07-10', 'healthy'),
('ptr-022', 'O-002', NULL, 'duck', 'Pekin', 'white', 'male', 'coop-005', '2024-07-12', 'healthy'),

-- Kazlar
('ptr-023', 'K-001', 'Gaga', 'goose', 'Toulouse', 'gray', 'female', 'coop-005', '2024-04-20', 'healthy'),
('ptr-024', 'K-002', NULL, 'goose', 'Toulouse', 'gray', 'male', 'coop-005', '2024-04-22', 'healthy');

-- =====================================================
-- 4. Yumurta Üretim Kayıtları (Son 7 gün)
-- =====================================================
INSERT INTO egg_production (coop_id, nest_box_id, poultry_id, egg_count, egg_quality, egg_weight_grams, recorded_at) VALUES
-- Bugün
('coop-001', 'zone-005', 'ptr-001', 1, 'normal', 62, NOW() - INTERVAL '2 hours'),
('coop-001', 'zone-005', 'ptr-002', 1, 'normal', 58, NOW() - INTERVAL '3 hours'),
('coop-001', 'zone-005', 'ptr-003', 1, 'normal', 60, NOW() - INTERVAL '4 hours'),
('coop-001', 'zone-005', 'ptr-004', 1, 'large', 72, NOW() - INTERVAL '5 hours'),
('coop-001', 'zone-005', NULL, 1, 'normal', 55, NOW() - INTERVAL '6 hours'),
('coop-001', 'zone-005', NULL, 1, 'double_yolk', 78, NOW() - INTERVAL '7 hours'),

-- Dün
('coop-001', 'zone-005', 'ptr-001', 1, 'normal', 61, NOW() - INTERVAL '1 day 2 hours'),
('coop-001', 'zone-005', 'ptr-002', 1, 'normal', 59, NOW() - INTERVAL '1 day 3 hours'),
('coop-001', 'zone-005', 'ptr-003', 1, 'soft_shell', 52, NOW() - INTERVAL '1 day 4 hours'),
('coop-001', 'zone-005', 'ptr-004', 1, 'normal', 64, NOW() - INTERVAL '1 day 5 hours'),
('coop-001', 'zone-005', NULL, 1, 'normal', 57, NOW() - INTERVAL '1 day 6 hours'),

-- 2 gün önce
('coop-001', 'zone-005', 'ptr-001', 1, 'normal', 60, NOW() - INTERVAL '2 days 2 hours'),
('coop-001', 'zone-005', 'ptr-002', 1, 'normal', 58, NOW() - INTERVAL '2 days 3 hours'),
('coop-001', 'zone-005', 'ptr-004', 1, 'normal', 63, NOW() - INTERVAL '2 days 4 hours'),
('coop-001', 'zone-005', NULL, 1, 'blood_spot', 56, NOW() - INTERVAL '2 days 5 hours'),
('coop-001', 'zone-005', NULL, 1, 'normal', 59, NOW() - INTERVAL '2 days 6 hours'),

-- 3 gün önce
('coop-001', 'zone-005', 'ptr-001', 1, 'normal', 62, NOW() - INTERVAL '3 days 2 hours'),
('coop-001', 'zone-005', 'ptr-002', 1, 'normal', 57, NOW() - INTERVAL '3 days 3 hours'),
('coop-001', 'zone-005', 'ptr-003', 1, 'normal', 61, NOW() - INTERVAL '3 days 4 hours'),
('coop-001', 'zone-005', 'ptr-004', 1, 'normal', 65, NOW() - INTERVAL '3 days 5 hours'),
('coop-001', 'zone-005', NULL, 1, 'small', 48, NOW() - INTERVAL '3 days 6 hours');

-- =====================================================
-- 5. Sağlık Kayıtları
-- =====================================================
INSERT INTO poultry_health_records (poultry_id, coop_id, health_status, symptoms, diagnosis, treatment, veterinarian, notes, is_resolved, resolved_at) VALUES
('ptr-005', 'coop-001', 'broody', ARRAY['yumurta üzerinde oturma', 'saldırgan davranış'], 'Kuluçka davranışı', 'İzleme', NULL, 'Normal kuluçka davranışı, doğal süreç', false, NULL),
('ptr-007', 'coop-001', 'molting', ARRAY['tüy dökümü', 'yumurta üretimi durması'], 'Mevsimsel tüy değişimi', 'Protein takviyeli yem', NULL, 'Normal tüy dökümü süreci', false, NULL),
('ptr-003', 'coop-001', 'sick', ARRAY['ishal', 'iştahsızlık'], 'Hafif sindirim sorunu', 'Probiyotik takviyesi', 'Dr. Veteriner', 'Tedavi başlandı, 3 gün takip', true, NOW() - INTERVAL '2 days');

-- =====================================================
-- 6. Davranış Logları (Son 24 saat)
-- =====================================================
INSERT INTO poultry_behavior_logs (poultry_id, coop_id, zone_id, behavior, duration_seconds, intensity, is_abnormal) VALUES
-- Yem yeme davranışları
('ptr-001', 'coop-001', 'zone-001', 'feeding', 120, 'medium', false),
('ptr-002', 'coop-001', 'zone-001', 'feeding', 90, 'medium', false),
('ptr-003', 'coop-001', 'zone-001', 'feeding', 150, 'high', false),
('ptr-004', 'coop-001', 'zone-001', 'feeding', 100, 'medium', false),

-- Su içme
('ptr-001', 'coop-001', 'zone-002', 'drinking', 30, 'low', false),
('ptr-002', 'coop-001', 'zone-002', 'drinking', 25, 'low', false),

-- Tünek
('ptr-001', 'coop-001', 'zone-004', 'roosting', 600, 'low', false),
('ptr-002', 'coop-001', 'zone-004', 'roosting', 550, 'low', false),
('ptr-011', 'coop-001', 'zone-004', 'roosting', 480, 'low', false),

-- Yumurtlama
('ptr-001', 'coop-001', 'zone-005', 'nesting', 1800, 'medium', false),
('ptr-002', 'coop-001', 'zone-005', 'nesting', 2100, 'medium', false),
('ptr-005', 'coop-001', 'zone-005', 'brooding', 7200, 'high', false),

-- Toz banyosu
('ptr-003', 'coop-001', 'zone-006', 'dust_bathing', 900, 'high', false),
('ptr-004', 'coop-001', 'zone-006', 'dust_bathing', 720, 'medium', false),

-- Yürüme ve arama
('ptr-001', 'coop-001', NULL, 'walking', 300, 'medium', false),
('ptr-002', 'coop-001', NULL, 'foraging', 450, 'medium', false),

-- Anormal davranış örneği
('ptr-007', 'coop-001', NULL, 'lethargy', 1200, 'low', true);

-- =====================================================
-- 7. Uyarı Kayıtları
-- =====================================================
INSERT INTO poultry_alerts (coop_id, poultry_id, alert_type, severity, title, message, is_resolved) VALUES
('coop-001', 'ptr-005', 'broody', 'info', 'Kuluçka Davranışı Tespit Edildi', 'ptr-005 (Tüylü) kuluçka davranışı gösteriyor. Yumurta üretimi durabilir.', false),
('coop-001', 'ptr-007', 'molting', 'info', 'Tüy Dökümü Başladı', 'ptr-007 tüy dökümü sürecine girdi. Normal mevsimsel değişim.', false),
('coop-001', NULL, 'stress', 'warning', 'Stres Davranışı Gözlemlendi', 'Kümeste bazı tavuklarda tüy gagalama davranışı gözlemlendi. Çevre koşulları kontrol edilmeli.', true);

-- =====================================================
-- Bilgi Mesajı
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Kanatlı Hayvan örnek verileri başarıyla eklendi!';
    RAISE NOTICE '';
    RAISE NOTICE 'Eklenen veriler:';
    RAISE NOTICE '  - 5 kümes';
    RAISE NOTICE '  - 12 kümes bölgesi';
    RAISE NOTICE '  - 24 kanatlı hayvan (tavuk, horoz, civciv, hindi, ördek, kaz)';
    RAISE NOTICE '  - 20+ yumurta üretim kaydı';
    RAISE NOTICE '  - 3 sağlık kaydı';
    RAISE NOTICE '  - 17 davranış logu';
    RAISE NOTICE '  - 3 uyarı';
END $$;
