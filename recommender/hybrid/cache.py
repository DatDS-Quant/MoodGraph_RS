"""
Bộ nhớ đệm phục vụ suy luận hiệu năng cao cho Hybrid Recommender (Phase 4).

Tính năng:
- Thread-safe (sử dụng RLock).
- Bounded LRU (Least Recently Used) tự động giới hạn dung lượng bộ nhớ.
- TTL (Time-To-Live) tự động hết hạn các gợi ý cũ.
- Theo dõi thống kê vận hành: hits, misses, evictions, size.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class CacheEntry:
    """Mục lưu trữ trong bộ nhớ đệm kèm nhãn thời gian tạo (timestamp)."""
    value: Any
    created_at: float


class HybridRecommendationCache:
    """
    LRU Memory Cache an toàn đa luồng cho gợi ý người dùng.
    """

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600) -> None:
        if max_size <= 0:
            raise ValueError(f"max_size must be > 0, got {max_size}")
        if ttl_seconds <= 0:
            raise ValueError(f"ttl_seconds must be > 0, got {ttl_seconds}")

        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[Tuple[Any, ...], CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: Tuple[Any, ...]) -> Optional[Any]:
        """Truy xuất giá trị từ cache nếu còn hạn sử dụng."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]
            now = time.monotonic()
            if now - entry.created_at > self.ttl_seconds:
                # Đã hết hạn TTL
                del self._cache[key]
                self._misses += 1
                return None

            # Đánh dấu vừa được sử dụng (chuyển về cuối OrderedDict)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def put(self, key: Tuple[Any, ...], value: Any) -> None:
        """Lưu trữ giá trị vào cache với chính sách LRU eviction."""
        with self._lock:
            now = time.monotonic()
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = CacheEntry(value=value, created_at=now)
                return

            if len(self._cache) >= self.max_size:
                # Đào thải phần tử cũ nhất (đầu OrderedDict)
                self._cache.popitem(last=False)
                self._evictions += 1

            self._cache[key] = CacheEntry(value=value, created_at=now)

    def invalidate(self, key: Tuple[Any, ...]) -> bool:
        """Xóa một key xác định khỏi cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Xóa toàn bộ cache và làm mới chỉ số thống kê."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    def stats(self) -> Dict[str, Any]:
        """Trả về báo cáo thống kê hoạt động của cache."""
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._hits,
                "misses": self._misses,
                "total_lookups": total,
                "hit_ratio": round(hit_ratio, 4),
                "evictions": self._evictions,
            }

