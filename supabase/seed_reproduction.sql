-- AI Animal Tracking - Reproduction Module Seed Data
-- =====================================================
-- Bu dosyayı Supabase SQL Editor'de çalıştırın

-- =====================================================
-- ÖRNEK KIZGINLIK TESPİTLERİ (ESTRUS)
-- =====================================================

-- Aktif kızgınlık - inek-001
INSERT INTO estrus_detections (id, animal_id, detection_time, behaviors, confidence, optimal_breeding_start, optimal_breeding_end, status, notified, notes)
VALUES (
  'estrus-001',
  'inek-001',
  NOW() - INTERVAL '2 hours',
  '{"mounting": 0.85, "standing_heat": 0.92, "restlessness": 0.78, "tail_raising": 0.65}',
  0.88,
  NOW() + INTERVAL '4 hours',
  NOW() + INTERVAL '18 hours',
  'detected',
  true,
  'Yüksek güvenle kızgınlık tespit edildi. Optimal tohumlama zamanı yaklaşıyor.'
);

-- Onaylanmış kızgınlık - inek-002
INSERT INTO estrus_detections (id, animal_id, detection_time, behaviors, confidence, optimal_breeding_start, optimal_breeding_end, status, notified, notes)
VALUES (
  'estrus-002',
  'inek-002',
  NOW() - INTERVAL '6 hours',
  '{"mounting": 0.72, "standing_heat": 0.88, "activity_increase": 0.81}',
  0.80,
  NOW() - INTERVAL '2 hours',
  NOW() + INTERVAL '12 hours',
  'confirmed',
  true,
  'Veteriner tarafından kızgınlık onaylandı.'
);

-- Tohumlanmış kızgınlık - koyun-001
INSERT INTO estrus_detections (id, animal_id, detection_time, behaviors, confidence, optimal_breeding_start, optimal_breeding_end, status, notified, notes)
VALUES (
  'estrus-003',
  'koyun-001',
  NOW() - INTERVAL '1 day',
  '{"restlessness": 0.75, "tail_raising": 0.82, "social_interaction": 0.68}',
  0.75,
  NOW() - INTERVAL '20 hours',
  NOW() - INTERVAL '8 hours',
  'bred',
  true,
  'Doğal aşım yapıldı.'
);

-- =====================================================
-- ÖRNEK GEBELİKLER
-- =====================================================

-- Aktif gebelik - inek-003 (7 ay gebe)
INSERT INTO pregnancies (id, animal_id, breeding_date, expected_birth_date, sire_id, breeding_method, pregnancy_confirmed, confirmation_date, confirmation_method, status, notes)
VALUES (
  'preg-001',
  'inek-003',
  NOW() - INTERVAL '210 days',
  NOW() + INTERVAL '73 days',
  'boga-001',
  'suni_tohumlama',
  true,
  NOW() - INTERVAL '180 days',
  'ultrasound',
  'aktif',
  '7 aylık gebe. Ultrason ile doğrulandı. Sağlıklı gelişim.'
);

-- Aktif gebelik - inek-004 (3 ay gebe)
INSERT INTO pregnancies (id, animal_id, breeding_date, expected_birth_date, sire_id, breeding_method, pregnancy_confirmed, confirmation_date, confirmation_method, status, notes)
VALUES (
  'preg-002',
  'inek-004',
  NOW() - INTERVAL '90 days',
  NOW() + INTERVAL '193 days',
  'boga-002',
  'doğal',
  true,
  NOW() - INTERVAL '60 days',
  'blood_test',
  'aktif',
  '3 aylık gebe. Kan testi ile doğrulandı.'
);

-- Aktif gebelik - koyun-002 (yakın doğum - 5 gün kaldı)
INSERT INTO pregnancies (id, animal_id, breeding_date, expected_birth_date, sire_id, breeding_method, pregnancy_confirmed, confirmation_date, confirmation_method, status, notes)
VALUES (
  'preg-003',
  'koyun-002',
  NOW() - INTERVAL '145 days',
  NOW() + INTERVAL '5 days',
  'koc-001',
  'doğal',
  true,
  NOW() - INTERVAL '120 days',
  'observation',
  'aktif',
  'Doğum çok yakın! İzlemeye alındı. Karın belirgin şekilde büyümüş.'
);

-- Doğum yapmış gebelik - inek-005
INSERT INTO pregnancies (id, animal_id, breeding_date, expected_birth_date, actual_birth_date, sire_id, breeding_method, pregnancy_confirmed, confirmation_date, confirmation_method, status, notes)
VALUES (
  'preg-004',
  'inek-005',
  NOW() - INTERVAL '290 days',
  NOW() - INTERVAL '10 days',
  NOW() - INTERVAL '7 days',
  'boga-001',
  'suni_tohumlama',
  true,
  NOW() - INTERVAL '260 days',
  'ultrasound',
  'doğum_yaptı',
  'Sağlıklı bir buzağı dünyaya geldi.'
);

-- =====================================================
-- ÖRNEK DOĞUMLAR
-- =====================================================

-- Normal doğum - inek-005
INSERT INTO births (id, mother_id, pregnancy_id, birth_date, offspring_count, offspring_ids, birth_type, birth_weight, vet_assisted, vet_name, ai_predicted_at, ai_detected_at, prediction_accuracy_hours, notes)
VALUES (
  'birth-001',
  'inek-005',
  'preg-004',
  NOW() - INTERVAL '7 days',
  1,
  '["buzagi-001"]',
  'normal',
  38.5,
  false,
  NULL,
  NOW() - INTERVAL '8 days',
  NOW() - INTERVAL '7 days' + INTERVAL '30 minutes',
  18,
  'Normal doğum gerçekleşti. Anne ve buzağı sağlıklı. Emzirme başladı.'
);

-- Müdahaleli doğum - koyun-003
INSERT INTO births (id, mother_id, pregnancy_id, birth_date, offspring_count, offspring_ids, birth_type, birth_weight, complications, vet_assisted, vet_name, notes)
VALUES (
  'birth-002',
  'koyun-003',
  NULL,
  NOW() - INTERVAL '14 days',
  2,
  '["kuzu-001", "kuzu-002"]',
  'müdahaleli',
  3.2,
  'İkiz doğumda ikinci yavru ters geldi',
  true,
  'Dr. Ahmet Yılmaz',
  'İkiz doğum. İkinci kuzu ters gelmesi nedeniyle veteriner müdahalesi gerekti. Her iki kuzu da sağlıklı.'
);

-- =====================================================
-- ÖRNEK ÇİFTLEŞTİRME KAYITLARI
-- =====================================================

-- Başarılı suni tohumlama
INSERT INTO breeding_records (id, female_id, male_id, breeding_date, breeding_method, technician_name, semen_batch, estrus_detection_id, success, pregnancy_id, notes)
VALUES (
  'breed-001',
  'inek-003',
  'boga-001',
  NOW() - INTERVAL '210 days',
  'suni_tohumlama',
  'Vet. Hekim Mehmet Öz',
  'SB-2024-1234',
  NULL,
  true,
  'preg-001',
  'İlk tohumlamada başarılı gebe kaldı.'
);

-- Beklemede - sonucu bilinmiyor
INSERT INTO breeding_records (id, female_id, male_id, breeding_date, breeding_method, technician_name, semen_batch, estrus_detection_id, success, notes)
VALUES (
  'breed-002',
  'inek-002',
  'boga-002',
  NOW() - INTERVAL '14 days',
  'suni_tohumlama',
  'Vet. Hekim Mehmet Öz',
  'SB-2024-5678',
  'estrus-002',
  NULL,
  '21 gün sonra gebelik kontrolü yapılacak.'
);

-- Doğal aşım - başarılı
INSERT INTO breeding_records (id, female_id, male_id, breeding_date, breeding_method, success, pregnancy_id, notes)
VALUES (
  'breed-003',
  'koyun-002',
  'koc-001',
  NOW() - INTERVAL '145 days',
  'doğal',
  true,
  'preg-003',
  'Doğal aşım ile gebe kaldı. Doğum çok yakın.'
);

-- Başarısız tohumlama
INSERT INTO breeding_records (id, female_id, male_id, breeding_date, breeding_method, technician_name, semen_batch, success, notes)
VALUES (
  'breed-004',
  'inek-006',
  'boga-001',
  NOW() - INTERVAL '45 days',
  'suni_tohumlama',
  'Vet. Hekim Ayşe Kaya',
  'SB-2024-9999',
  false,
  'Gebelik oluşmadı. Tekrar tohumlama planlandı.'
);

-- =====================================================
-- VERİFİKASYON
-- =====================================================

SELECT 'Estrus Detections' as table_name, COUNT(*) as count FROM estrus_detections
UNION ALL
SELECT 'Pregnancies', COUNT(*) FROM pregnancies
UNION ALL
SELECT 'Births', COUNT(*) FROM births
UNION ALL
SELECT 'Breeding Records', COUNT(*) FROM breeding_records;
