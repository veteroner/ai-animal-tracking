"""
AI Animal Tracking System - Frame Buffer
========================================

Thread-safe frame buffer implementasyonu.
"""

import threading
import time
from typing import Optional, List
from dataclasses import dataclass
from collections import deque

import numpy as np


@dataclass
class BufferedFrame:
    """Buffer'daki frame"""
    frame: np.ndarray
    timestamp: float
    frame_id: int


class FrameBuffer:
    """
    Thread-safe frame buffer.
    
    Son N frame'i bellekte tutar ve hızlı erişim sağlar.
    Gerçek zamanlı video işleme için optimize edilmiştir.
    
    Kullanım:
        buffer = FrameBuffer(max_size=30)
        buffer.put(frame, timestamp, frame_id)
        latest = buffer.get_latest()
        all_frames = buffer.get_all()
    """
    
    def __init__(self, max_size: int = 30):
        """
        Args:
            max_size: Maksimum buffer boyutu
        """
        self._max_size = max_size
        self._buffer: deque = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._frame_count = 0
        self._dropped_count = 0
    
    @property
    def size(self) -> int:
        """Buffer'daki frame sayısı"""
        with self._lock:
            return len(self._buffer)
    
    @property
    def max_size(self) -> int:
        """Maksimum buffer boyutu"""
        return self._max_size
    
    @property
    def is_empty(self) -> bool:
        """Buffer boş mu"""
        return self.size == 0
    
    @property
    def is_full(self) -> bool:
        """Buffer dolu mu"""
        return self.size >= self._max_size
    
    @property
    def statistics(self) -> dict:
        """Buffer istatistikleri"""
        return {
            "size": self.size,
            "max_size": self._max_size,
            "frame_count": self._frame_count,
            "dropped_count": self._dropped_count,
        }
    
    def put(
        self,
        frame: np.ndarray,
        timestamp: Optional[float] = None,
        frame_id: Optional[int] = None
    ) -> bool:
        """
        Frame ekle.
        
        Args:
            frame: Frame verisi
            timestamp: Zaman damgası
            frame_id: Frame ID
            
        Returns:
            Başarılı ise True
        """
        if frame is None:
            return False
        
        if timestamp is None:
            timestamp = time.time()
        
        with self._lock:
            if frame_id is None:
                frame_id = self._frame_count
            
            # Eğer buffer doluysa en eski düşürülecek
            if self.is_full:
                self._dropped_count += 1
            
            buffered_frame = BufferedFrame(
                frame=frame.copy(),
                timestamp=timestamp,
                frame_id=frame_id,
            )
            
            self._buffer.append(buffered_frame)
            self._frame_count += 1
        
        return True
    
    def get_latest(self) -> Optional[BufferedFrame]:
        """
        En son frame'i al.
        
        Returns:
            BufferedFrame veya None
        """
        with self._lock:
            if self.is_empty:
                return None
            return self._buffer[-1]
    
    def get_oldest(self) -> Optional[BufferedFrame]:
        """
        En eski frame'i al.
        
        Returns:
            BufferedFrame veya None
        """
        with self._lock:
            if self.is_empty:
                return None
            return self._buffer[0]
    
    def get_by_index(self, index: int) -> Optional[BufferedFrame]:
        """
        Index'e göre frame al.
        
        Args:
            index: Buffer index'i (0 = en eski, -1 = en yeni)
            
        Returns:
            BufferedFrame veya None
        """
        with self._lock:
            if self.is_empty or abs(index) > len(self._buffer):
                return None
            return self._buffer[index]
    
    def get_all(self) -> List[BufferedFrame]:
        """
        Tüm frame'leri al.
        
        Returns:
            BufferedFrame listesi
        """
        with self._lock:
            return list(self._buffer)
    
    def get_frames_since(self, timestamp: float) -> List[BufferedFrame]:
        """
        Belirli zamandan sonraki frame'leri al.
        
        Args:
            timestamp: Başlangıç zamanı
            
        Returns:
            BufferedFrame listesi
        """
        with self._lock:
            return [f for f in self._buffer if f.timestamp >= timestamp]
    
    def get_last_n(self, n: int) -> List[BufferedFrame]:
        """
        Son N frame'i al.
        
        Args:
            n: Frame sayısı
            
        Returns:
            BufferedFrame listesi
        """
        with self._lock:
            if n >= len(self._buffer):
                return list(self._buffer)
            return list(self._buffer)[-n:]
    
    def pop_latest(self) -> Optional[BufferedFrame]:
        """
        En son frame'i al ve buffer'dan çıkar.
        
        Returns:
            BufferedFrame veya None
        """
        with self._lock:
            if self.is_empty:
                return None
            return self._buffer.pop()
    
    def pop_oldest(self) -> Optional[BufferedFrame]:
        """
        En eski frame'i al ve buffer'dan çıkar.
        
        Returns:
            BufferedFrame veya None
        """
        with self._lock:
            if self.is_empty:
                return None
            return self._buffer.popleft()
    
    def clear(self):
        """Buffer'ı temizle"""
        with self._lock:
            self._buffer.clear()
    
    def resize(self, new_size: int):
        """
        Buffer boyutunu değiştir.
        
        Args:
            new_size: Yeni maksimum boyut
        """
        with self._lock:
            # Yeni deque oluştur
            new_buffer = deque(maxlen=new_size)
            
            # Mevcut frame'leri kopyala (son new_size kadarını)
            for frame in list(self._buffer)[-new_size:]:
                new_buffer.append(frame)
            
            self._buffer = new_buffer
            self._max_size = new_size
    
    def __len__(self) -> int:
        return self.size
    
    def __iter__(self):
        with self._lock:
            return iter(list(self._buffer))
    
    def __getitem__(self, index: int) -> Optional[BufferedFrame]:
        return self.get_by_index(index)
