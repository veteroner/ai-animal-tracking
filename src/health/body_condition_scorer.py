"""
Vücut Kondisyon Skoru (BCS) Modülü

Görüntü analizi ile hayvan vücut kondisyon skoru tahmini.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict


class BCSScale(Enum):
    """BCS ölçek türleri"""
    SCALE_5 = 5    # 1-5 ölçeği (çoğu hayvan)
    SCALE_9 = 9    # 1-9 ölçeği (sığır için detaylı)


class BCSCategory(Enum):
    """BCS kategorileri"""
    EMACIATED = "emaciated"       # Aşırı zayıf (BCS 1-2)
    THIN = "thin"                 # Zayıf (BCS 2-3)
    IDEAL = "ideal"               # İdeal (BCS 3-4)
    OVERWEIGHT = "overweight"     # Kilolu (BCS 4-4.5)
    OBESE = "obese"               # Obez (BCS 4.5-5)


@dataclass
class BCSAssessment:
    """BCS değerlendirmesi"""
    assessment_id: str
    animal_id: str
    timestamp: datetime
    score: float                    # 1.0-5.0 arası
    confidence: float               # 0-1 arası güven
    scale: BCSScale
    category: BCSCategory
    visual_features: Dict[str, float] = field(default_factory=dict)
    image_path: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def score_normalized(self) -> float:
        """0-1 arasında normalize skor"""
        max_score = self.scale.value
        return (self.score - 1) / (max_score - 1)
    
    def to_dict(self) -> Dict:
        return {
            "assessment_id": self.assessment_id,
            "animal_id": self.animal_id,
            "timestamp": self.timestamp.isoformat(),
            "score": round(self.score, 2),
            "confidence": round(self.confidence, 3),
            "scale": f"1-{self.scale.value}",
            "category": self.category.value,
            "score_normalized": round(self.score_normalized, 3),
            "visual_features": self.visual_features
        }


@dataclass
class BCSHistory:
    """BCS geçmişi"""
    animal_id: str
    assessments: List[BCSAssessment] = field(default_factory=list)
    
    @property
    def current_score(self) -> Optional[float]:
        if self.assessments:
            return self.assessments[-1].score
        return None
    
    @property
    def trend(self) -> str:
        """Son 30 günlük trend"""
        if len(self.assessments) < 2:
            return "stable"
        
        recent = self.assessments[-5:]
        scores = [a.score for a in recent]
        
        diff = scores[-1] - scores[0]
        if diff > 0.3:
            return "increasing"
        elif diff < -0.3:
            return "decreasing"
        return "stable"
    
    @property
    def average_score(self) -> Optional[float]:
        if self.assessments:
            return np.mean([a.score for a in self.assessments[-10:]])
        return None


@dataclass
class VisualFeatures:
    """Görsel özellikler"""
    spine_visibility: float = 0.0      # Omurga görünürlüğü (0-1)
    rib_visibility: float = 0.0        # Kaburga görünürlüğü (0-1)
    hip_bone_prominence: float = 0.0   # Kalça kemiği belirginliği (0-1)
    tailhead_depression: float = 0.0   # Kuyruk dibi çukurluğu (0-1)
    loin_fullness: float = 0.0         # Bel dolgunluğu (0-1)
    brisket_fullness: float = 0.0      # Döş dolgunluğu (0-1)
    overall_roundness: float = 0.0     # Genel yuvarlaklık (0-1)


class BodyConditionScorer:
    """Vücut kondisyon skoru değerlendirici"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Geçmiş kayıtları
        self.histories: Dict[str, BCSHistory] = {}
        
        # Varsayılan ölçek
        self.default_scale = BCSScale.SCALE_5
        
        # Özellik ağırlıkları
        self.feature_weights = {
            "spine_visibility": 0.20,
            "rib_visibility": 0.20,
            "hip_bone_prominence": 0.15,
            "tailhead_depression": 0.15,
            "loin_fullness": 0.15,
            "overall_roundness": 0.15
        }
        
        # Sayaç
        self._assessment_counter = 0
    
    def _generate_assessment_id(self) -> str:
        """Benzersiz değerlendirme ID'si"""
        self._assessment_counter += 1
        return f"BCS_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._assessment_counter}"
    
    def _get_or_create_history(self, animal_id: str) -> BCSHistory:
        """Geçmişi al veya oluştur"""
        if animal_id not in self.histories:
            self.histories[animal_id] = BCSHistory(animal_id=animal_id)
        return self.histories[animal_id]
    
    def assess_from_features(self, animal_id: str,
                            features: VisualFeatures,
                            scale: Optional[BCSScale] = None,
                            image_path: Optional[str] = None) -> BCSAssessment:
        """Görsel özelliklerden BCS değerlendir"""
        scale = scale or self.default_scale
        
        # Özellik dict'e çevir
        feature_dict = {
            "spine_visibility": features.spine_visibility,
            "rib_visibility": features.rib_visibility,
            "hip_bone_prominence": features.hip_bone_prominence,
            "tailhead_depression": features.tailhead_depression,
            "loin_fullness": features.loin_fullness,
            "overall_roundness": features.overall_roundness
        }
        
        # BCS hesapla
        score = self._calculate_bcs(feature_dict, scale)
        
        # Kategori belirle
        category = self._determine_category(score, scale)
        
        # Güven skoru
        confidence = self._calculate_confidence(feature_dict)
        
        assessment = BCSAssessment(
            assessment_id=self._generate_assessment_id(),
            animal_id=animal_id,
            timestamp=datetime.now(),
            score=score,
            confidence=confidence,
            scale=scale,
            category=category,
            visual_features=feature_dict,
            image_path=image_path
        )
        
        # Geçmişe ekle
        history = self._get_or_create_history(animal_id)
        history.assessments.append(assessment)
        
        return assessment
    
    def assess_from_image(self, animal_id: str,
                         image: np.ndarray,
                         bbox: Optional[Tuple[int, int, int, int]] = None,
                         scale: Optional[BCSScale] = None) -> BCSAssessment:
        """Görüntüden BCS değerlendir"""
        # Görsel özellikleri çıkar (basitleştirilmiş)
        features = self._extract_visual_features(image, bbox)
        
        return self.assess_from_features(animal_id, features, scale)
    
    def _extract_visual_features(self, image: np.ndarray,
                                bbox: Optional[Tuple[int, int, int, int]] = None) -> VisualFeatures:
        """Görüntüden görsel özellikleri çıkar"""
        # Bu basitleştirilmiş bir implementasyon
        # Gerçekte CNN tabanlı özellik çıkarma kullanılır
        
        if bbox:
            x, y, w, h = bbox
            roi = image[y:y+h, x:x+w]
        else:
            roi = image
        
        # Görüntü analizinden özellikler (basitleştirilmiş)
        # Gerçekte derin öğrenme modeli kullanılır
        
        # Gri tonlama
        if len(roi.shape) == 3:
            gray = np.mean(roi, axis=2)
        else:
            gray = roi
        
        # Kenar tespiti (kemik belirginliği için proxy)
        edges = np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()
        edge_score = min(1.0, edges / 50)  # Normalize
        
        # Parlaklık varyansı (doku için proxy)
        variance = np.var(gray) / 1000
        variance_score = min(1.0, variance)
        
        # Basitleştirilmiş özellikler
        return VisualFeatures(
            spine_visibility=edge_score * 0.8,
            rib_visibility=edge_score * 0.7,
            hip_bone_prominence=edge_score * 0.6,
            tailhead_depression=variance_score * 0.5,
            loin_fullness=1 - edge_score * 0.6,
            overall_roundness=1 - variance_score * 0.4
        )
    
    def _calculate_bcs(self, features: Dict[str, float], scale: BCSScale) -> float:
        """BCS hesapla"""
        # Kemik görünürlüğü skoru (yüksek = zayıf)
        bone_score = (
            features.get("spine_visibility", 0) * 0.3 +
            features.get("rib_visibility", 0) * 0.4 +
            features.get("hip_bone_prominence", 0) * 0.3
        )
        
        # Dolgunluk skoru (yüksek = şişman)
        fullness_score = (
            features.get("loin_fullness", 0) * 0.4 +
            features.get("overall_roundness", 0) * 0.4 +
            (1 - features.get("tailhead_depression", 0)) * 0.2
        )
        
        # BCS = dolgunluk - kemik görünürlüğü dengesine göre
        # 0 (çok zayıf) - 1 (çok şişman) arası normalize değer
        normalized_score = (fullness_score - bone_score + 1) / 2
        normalized_score = max(0, min(1, normalized_score))
        
        # Ölçeğe çevir
        max_score = scale.value
        bcs = 1 + normalized_score * (max_score - 1)
        
        return round(bcs, 2)
    
    def _determine_category(self, score: float, scale: BCSScale) -> BCSCategory:
        """BCS kategorisini belirle"""
        # 1-5 ölçeği için
        if scale == BCSScale.SCALE_5:
            if score < 1.5:
                return BCSCategory.EMACIATED
            elif score < 2.5:
                return BCSCategory.THIN
            elif score < 3.5:
                return BCSCategory.IDEAL
            elif score < 4.25:
                return BCSCategory.OVERWEIGHT
            else:
                return BCSCategory.OBESE
        
        # 1-9 ölçeği için
        else:
            if score < 3:
                return BCSCategory.EMACIATED
            elif score < 4.5:
                return BCSCategory.THIN
            elif score < 6:
                return BCSCategory.IDEAL
            elif score < 7.5:
                return BCSCategory.OVERWEIGHT
            else:
                return BCSCategory.OBESE
    
    def _calculate_confidence(self, features: Dict[str, float]) -> float:
        """Güven skoru hesapla"""
        # Özelliklerin tutarlılığına dayalı
        values = list(features.values())
        
        if not values:
            return 0.5
        
        # Varyans düşükse tutarlı = yüksek güven
        variance = np.var(values)
        consistency = 1 - min(1, variance * 4)
        
        # Ekstrem değerler azaltır
        extreme_count = sum(1 for v in values if v < 0.1 or v > 0.9)
        extreme_penalty = extreme_count * 0.05
        
        confidence = max(0.3, min(0.95, 0.7 + consistency * 0.2 - extreme_penalty))
        
        return round(confidence, 3)
    
    def get_current_bcs(self, animal_id: str) -> Optional[BCSAssessment]:
        """Güncel BCS al"""
        history = self.histories.get(animal_id)
        if history and history.assessments:
            return history.assessments[-1]
        return None
    
    def get_bcs_history(self, animal_id: str,
                       days: int = 90) -> List[BCSAssessment]:
        """BCS geçmişini al"""
        history = self.histories.get(animal_id)
        if not history:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        return [a for a in history.assessments if a.timestamp >= cutoff]
    
    def get_bcs_summary(self, animal_id: str) -> Dict:
        """BCS özeti"""
        history = self.histories.get(animal_id)
        if not history or not history.assessments:
            return {"error": "Veri bulunamadı"}
        
        recent = history.assessments[-10:]
        scores = [a.score for a in recent]
        
        return {
            "animal_id": animal_id,
            "current_score": history.current_score,
            "current_category": recent[-1].category.value if recent else None,
            "average_score": round(history.average_score, 2) if history.average_score else None,
            "trend": history.trend,
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "total_assessments": len(history.assessments),
            "last_assessment": recent[-1].timestamp.isoformat() if recent else None
        }
    
    def get_animals_by_category(self, category: BCSCategory) -> List[Dict]:
        """Kategoriye göre hayvanları listele"""
        results = []
        
        for animal_id, history in self.histories.items():
            if not history.assessments:
                continue
            
            current = history.assessments[-1]
            if current.category == category:
                results.append({
                    "animal_id": animal_id,
                    "score": current.score,
                    "category": category.value,
                    "trend": history.trend,
                    "last_assessment": current.timestamp.isoformat()
                })
        
        return sorted(results, key=lambda x: x["score"])
    
    def get_herd_bcs_summary(self) -> Dict:
        """Sürü BCS özeti"""
        if not self.histories:
            return {"error": "Veri bulunamadı"}
        
        all_scores = []
        category_counts = defaultdict(int)
        trend_counts = defaultdict(int)
        
        for history in self.histories.values():
            if not history.assessments:
                continue
            
            current = history.assessments[-1]
            all_scores.append(current.score)
            category_counts[current.category.value] += 1
            trend_counts[history.trend] += 1
        
        total = len(all_scores)
        
        return {
            "total_animals": len(self.histories),
            "assessed_animals": total,
            "average_bcs": round(np.mean(all_scores), 2) if all_scores else 0,
            "median_bcs": round(np.median(all_scores), 2) if all_scores else 0,
            "min_bcs": round(min(all_scores), 2) if all_scores else 0,
            "max_bcs": round(max(all_scores), 2) if all_scores else 0,
            "category_distribution": dict(category_counts),
            "trend_distribution": dict(trend_counts),
            "ideal_percentage": round(category_counts.get("ideal", 0) / total * 100, 1) if total > 0 else 0
        }
    
    def get_recommendations(self, animal_id: str) -> List[str]:
        """BCS için öneriler"""
        assessment = self.get_current_bcs(animal_id)
        if not assessment:
            return ["BCS değerlendirmesi yapılmalı"]
        
        history = self.histories.get(animal_id)
        recommendations = []
        
        if assessment.category == BCSCategory.EMACIATED:
            recommendations.extend([
                "ACİL: Veteriner muayenesi gerekli",
                "Yem miktarını artır",
                "Parazit kontrolü yap",
                "Hastalık taraması yap"
            ])
        
        elif assessment.category == BCSCategory.THIN:
            recommendations.extend([
                "Yem miktarını %10-15 artır",
                "Yem kalitesini kontrol et",
                "Rekabet ortamını değerlendir",
                "2 hafta sonra yeniden değerlendir"
            ])
        
        elif assessment.category == BCSCategory.IDEAL:
            recommendations.append("İdeal kondisyon - mevcut beslemeyi sürdür")
        
        elif assessment.category == BCSCategory.OVERWEIGHT:
            recommendations.extend([
                "Yem miktarını %10 azalt",
                "Egzersiz fırsatlarını artır",
                "Enerji yoğunluğunu düşür"
            ])
        
        elif assessment.category == BCSCategory.OBESE:
            recommendations.extend([
                "Yem miktarını %15-20 azalt",
                "Yüksek lifli yeme geç",
                "Metabolik hastalık riski yüksek",
                "Veteriner danışmanlığı önerilir"
            ])
        
        # Trend bazlı öneriler
        if history and history.trend == "decreasing":
            recommendations.append("UYARI: BCS düşüş eğiliminde - nedeni araştırılmalı")
        elif history and history.trend == "increasing" and assessment.category in [BCSCategory.OVERWEIGHT, BCSCategory.OBESE]:
            recommendations.append("UYARI: BCS artış eğiliminde - obezite riski")
        
        return recommendations
