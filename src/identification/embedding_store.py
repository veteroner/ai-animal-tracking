"""
Embedding Store
Hayvan embedding vektörleri veritabanı
"""

import numpy as np
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
import pickle
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingEntry:
    """Tek bir embedding kaydı"""
    id: int
    embedding: np.ndarray
    animal_id: Optional[str] = None
    source: str = "detection"  # detection, manual, imported
    quality_score: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


class EmbeddingStore:
    """
    Embedding vektörleri depolama ve arama sınıfı
    """
    
    def __init__(
        self,
        storage_path: str = "data/embeddings",
        embedding_dim: int = 512,
        max_entries: int = 100000
    ):
        """
        Args:
            storage_path: Depolama dizini
            embedding_dim: Embedding boyutu
            max_entries: Maksimum kayıt sayısı
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_dim = embedding_dim
        self.max_entries = max_entries
        
        self._entries: Dict[int, EmbeddingEntry] = {}
        self._embeddings_matrix: Optional[np.ndarray] = None
        self._id_to_index: Dict[int, int] = {}
        self._next_id = 1
        self._lock = threading.Lock()
        
        # Index yapısı
        self._animal_index: Dict[str, List[int]] = {}  # animal_id -> entry_ids
        
        # Veritabanını yükle
        self._load()
    
    def _load(self) -> None:
        """Veritabanını yükle"""
        index_path = self.storage_path / "index.json"
        embeddings_path = self.storage_path / "embeddings.npy"
        
        if index_path.exists() and embeddings_path.exists():
            try:
                with open(index_path, 'r') as f:
                    data = json.load(f)
                
                self._next_id = data.get("next_id", 1)
                
                # Embedding matrix'i yükle
                self._embeddings_matrix = np.load(embeddings_path)
                
                # Entry'leri oluştur
                for entry_data in data.get("entries", []):
                    idx = entry_data["index"]
                    entry = EmbeddingEntry(
                        id=entry_data["id"],
                        embedding=self._embeddings_matrix[idx],
                        animal_id=entry_data.get("animal_id"),
                        source=entry_data.get("source", "detection"),
                        quality_score=entry_data.get("quality_score", 1.0),
                        timestamp=datetime.fromisoformat(entry_data["timestamp"]) if entry_data.get("timestamp") else datetime.now(),
                        metadata=entry_data.get("metadata", {})
                    )
                    
                    self._entries[entry.id] = entry
                    self._id_to_index[entry.id] = idx
                    
                    if entry.animal_id:
                        if entry.animal_id not in self._animal_index:
                            self._animal_index[entry.animal_id] = []
                        self._animal_index[entry.animal_id].append(entry.id)
                
                logger.info(f"Embedding store yüklendi: {len(self._entries)} kayıt")
                
            except Exception as e:
                logger.error(f"Embedding store yükleme hatası: {e}")
                self._embeddings_matrix = None
    
    def _save(self) -> None:
        """Veritabanını kaydet"""
        try:
            # Index verisi
            index_data = {
                "next_id": self._next_id,
                "entries": []
            }
            
            for entry_id, entry in self._entries.items():
                index_data["entries"].append({
                    "id": entry.id,
                    "index": self._id_to_index[entry_id],
                    "animal_id": entry.animal_id,
                    "source": entry.source,
                    "quality_score": entry.quality_score,
                    "timestamp": entry.timestamp.isoformat(),
                    "metadata": entry.metadata
                })
            
            # Kaydet
            index_path = self.storage_path / "index.json"
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
            
            if self._embeddings_matrix is not None:
                embeddings_path = self.storage_path / "embeddings.npy"
                np.save(embeddings_path, self._embeddings_matrix)
            
            logger.debug("Embedding store kaydedildi")
            
        except Exception as e:
            logger.error(f"Embedding store kaydetme hatası: {e}")
    
    def add(
        self,
        embedding: np.ndarray,
        animal_id: Optional[str] = None,
        source: str = "detection",
        quality_score: float = 1.0,
        metadata: dict = None
    ) -> int:
        """
        Yeni embedding ekle
        
        Args:
            embedding: Feature vektörü
            animal_id: İlişkili hayvan ID'si
            source: Kaynak (detection, manual, imported)
            quality_score: Kalite skoru (0-1)
            metadata: Ek bilgiler
            
        Returns:
            Embedding ID'si
        """
        with self._lock:
            # Boyut kontrolü
            if len(embedding) != self.embedding_dim:
                # Boyutu ayarla
                if len(embedding) < self.embedding_dim:
                    embedding = np.pad(embedding, (0, self.embedding_dim - len(embedding)))
                else:
                    embedding = embedding[:self.embedding_dim]
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            # Entry oluştur
            entry_id = self._next_id
            self._next_id += 1
            
            entry = EmbeddingEntry(
                id=entry_id,
                embedding=embedding,
                animal_id=animal_id,
                source=source,
                quality_score=quality_score,
                metadata=metadata or {}
            )
            
            # Matrix'e ekle
            if self._embeddings_matrix is None:
                self._embeddings_matrix = embedding.reshape(1, -1)
                idx = 0
            else:
                idx = len(self._embeddings_matrix)
                self._embeddings_matrix = np.vstack([self._embeddings_matrix, embedding])
            
            self._entries[entry_id] = entry
            self._id_to_index[entry_id] = idx
            
            # Animal index güncelle
            if animal_id:
                if animal_id not in self._animal_index:
                    self._animal_index[animal_id] = []
                self._animal_index[animal_id].append(entry_id)
            
            # Periyodik kaydetme
            if len(self._entries) % 100 == 0:
                self._save()
            
            return entry_id
    
    def get(self, entry_id: int) -> Optional[EmbeddingEntry]:
        """ID ile embedding al"""
        return self._entries.get(entry_id)
    
    def get_by_animal(self, animal_id: str) -> List[EmbeddingEntry]:
        """Hayvana ait tüm embedding'leri al"""
        entry_ids = self._animal_index.get(animal_id, [])
        return [self._entries[eid] for eid in entry_ids if eid in self._entries]
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.0,
        animal_id: Optional[str] = None
    ) -> List[Tuple[int, float]]:
        """
        Benzer embedding'leri ara
        
        Args:
            query_embedding: Sorgu vektörü
            top_k: Döndürülecek sonuç sayısı
            threshold: Minimum benzerlik eşiği
            animal_id: Sadece belirli hayvanın embedding'lerini ara
            
        Returns:
            [(entry_id, similarity_score), ...]
        """
        if self._embeddings_matrix is None or len(self._embeddings_matrix) == 0:
            return []
        
        # Normalize
        query = query_embedding.flatten()
        if len(query) != self.embedding_dim:
            if len(query) < self.embedding_dim:
                query = np.pad(query, (0, self.embedding_dim - len(query)))
            else:
                query = query[:self.embedding_dim]
        
        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm
        
        # Animal filtresi
        if animal_id:
            entry_ids = self._animal_index.get(animal_id, [])
            if not entry_ids:
                return []
            
            indices = [self._id_to_index[eid] for eid in entry_ids]
            matrix = self._embeddings_matrix[indices]
            
            # Cosine similarity
            similarities = np.dot(matrix, query)
            
            # Sonuçları sırala
            sorted_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in sorted_indices:
                sim = float(similarities[idx])
                if sim >= threshold:
                    results.append((entry_ids[idx], sim))
            
            return results
        
        else:
            # Tüm embedding'lerde ara
            similarities = np.dot(self._embeddings_matrix, query)
            
            # En iyi sonuçları al
            sorted_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in sorted_indices:
                sim = float(similarities[idx])
                if sim >= threshold:
                    # Index'ten ID'ye çevir
                    entry_id = None
                    for eid, eidx in self._id_to_index.items():
                        if eidx == idx:
                            entry_id = eid
                            break
                    
                    if entry_id:
                        results.append((entry_id, sim))
            
            return results
    
    def search_knn(
        self,
        query_embedding: np.ndarray,
        k: int = 5
    ) -> List[Tuple[int, float]]:
        """K-Nearest Neighbors araması"""
        return self.search(query_embedding, top_k=k, threshold=0.0)
    
    def update_animal_id(self, entry_id: int, animal_id: str) -> bool:
        """Entry'nin hayvan ID'sini güncelle"""
        entry = self._entries.get(entry_id)
        if not entry:
            return False
        
        # Eski index'ten kaldır
        if entry.animal_id and entry.animal_id in self._animal_index:
            if entry_id in self._animal_index[entry.animal_id]:
                self._animal_index[entry.animal_id].remove(entry_id)
        
        # Yeni index'e ekle
        entry.animal_id = animal_id
        if animal_id not in self._animal_index:
            self._animal_index[animal_id] = []
        self._animal_index[animal_id].append(entry_id)
        
        return True
    
    def delete(self, entry_id: int) -> bool:
        """Embedding'i sil"""
        if entry_id not in self._entries:
            return False
        
        entry = self._entries[entry_id]
        
        # Index'lerden kaldır
        if entry.animal_id and entry.animal_id in self._animal_index:
            if entry_id in self._animal_index[entry.animal_id]:
                self._animal_index[entry.animal_id].remove(entry_id)
        
        # Entry'yi sil (matrix'ten silmiyoruz - performans için)
        del self._entries[entry_id]
        
        return True
    
    def get_animal_embedding(self, animal_id: str, method: str = "mean") -> Optional[np.ndarray]:
        """
        Hayvan için temsili embedding al
        
        Args:
            animal_id: Hayvan ID'si
            method: Birleştirme yöntemi (mean, best)
            
        Returns:
            Temsili embedding vektörü
        """
        entries = self.get_by_animal(animal_id)
        if not entries:
            return None
        
        if method == "mean":
            embeddings = np.array([e.embedding for e in entries])
            mean_embedding = np.mean(embeddings, axis=0)
            return mean_embedding / (np.linalg.norm(mean_embedding) + 1e-8)
        
        elif method == "best":
            best_entry = max(entries, key=lambda e: e.quality_score)
            return best_entry.embedding
        
        return None
    
    def compute_animal_similarity(
        self,
        animal_id1: str,
        animal_id2: str
    ) -> float:
        """İki hayvan arasındaki benzerliği hesapla"""
        emb1 = self.get_animal_embedding(animal_id1)
        emb2 = self.get_animal_embedding(animal_id2)
        
        if emb1 is None or emb2 is None:
            return 0.0
        
        return float(np.dot(emb1, emb2))
    
    def get_statistics(self) -> dict:
        """İstatistikleri al"""
        animal_counts = {}
        for animal_id, entry_ids in self._animal_index.items():
            animal_counts[animal_id] = len(entry_ids)
        
        return {
            "total_entries": len(self._entries),
            "total_animals": len(self._animal_index),
            "embedding_dim": self.embedding_dim,
            "entries_per_animal": animal_counts,
            "matrix_shape": self._embeddings_matrix.shape if self._embeddings_matrix is not None else None
        }
    
    def compact(self) -> None:
        """Veritabanını kompakt hale getir (silinmiş entry'leri kaldır)"""
        logger.info("Embedding store compact başlatılıyor...")
        
        # Aktif embedding'leri topla
        active_embeddings = []
        new_id_to_index = {}
        
        for entry_id, entry in self._entries.items():
            idx = len(active_embeddings)
            active_embeddings.append(entry.embedding)
            new_id_to_index[entry_id] = idx
        
        # Matrix'i yeniden oluştur
        if active_embeddings:
            self._embeddings_matrix = np.array(active_embeddings)
        else:
            self._embeddings_matrix = None
        
        self._id_to_index = new_id_to_index
        
        self._save()
        logger.info(f"Compact tamamlandı: {len(self._entries)} kayıt")
    
    def save(self) -> None:
        """Manuel kaydet"""
        self._save()
    
    def clear(self) -> None:
        """Tüm verileri temizle"""
        self._entries.clear()
        self._embeddings_matrix = None
        self._id_to_index.clear()
        self._animal_index.clear()
        self._next_id = 1
        self._save()
        logger.info("Embedding store temizlendi")
