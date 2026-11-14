"""
Kho lưu trữ lịch sử tương tác người dùng (UserHistoryRepository) cho MoodGraph Phase 5.
Chỉ truy xuất từ tập Train (`artifacts/als/m10/train_seen_csr.npz` và `data/processed/splits/train`).
TUYỆT ĐỐI CÁCH LY và không đọc bất kỳ dữ liệu nào từ tập Validation hoặc Test.
"""

from __future__ import annotations

import threading
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pyarrow as pa
import pyarrow.dataset as ds


_DEFAULT_DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
_DEFAULT_CSR_PATH = Path(__file__).resolve().parent.parent.parent / "artifacts" / "als" / "m10" / "train_seen_csr.npz"


class UserHistoryRepository:
    """
    Kho lưu trữ lịch sử tương tác người dùng chỉ đọc từ tập Train.
    Bảo đảm 100% không rò rỉ dữ liệu kiểm chuẩn (Zero-Leakage Guarantee).
    """

    def __init__(
        self,
        data_root: Optional[Path] = None,
        csr_path: Optional[Path] = None,
    ) -> None:
        self.data_root = Path(data_root) if data_root else _DEFAULT_DATA_ROOT
        self.train_split_path = self.data_root / "splits" / "train"
        self.csr_path = Path(csr_path) if csr_path else _DEFAULT_CSR_PATH

        # Khóa đồng bộ đa luồng bảo vệ truy cập chỉ mục CSR
        self._lock = threading.RLock()
        # Mảng vị trí bắt đầu và kết thúc của từng user trong ma trận CSR
        self._csr_offsets: Optional[np.ndarray] = None
        # Mảng movieId tương ứng mà các user đã xem trong tập Train
        self._csr_mids: Optional[np.ndarray] = None
        # Cờ đánh dấu trạng thái nạp dữ liệu CSR vào RAM
        self._is_csr_loaded: bool = False
        # Bộ nhớ đệm danh sách đánh giá chi tiết của người dùng: userId -> List[Rating]
        self._user_ratings_cache: Dict[int, List[Dict[str, Any]]] = {}

    def warmup_index(self) -> None:
        """Nạp trước chỉ mục CSR tập Train vào bộ nhớ để tăng tốc."""
        with self._lock:
            if self._is_csr_loaded:
                return
            if self.csr_path.exists():
                data = np.load(self.csr_path)
                self._csr_offsets = data["offsets"]
                self._csr_mids = data["movie_ids"]
                self._is_csr_loaded = True

    def ensure_csr_loaded(self) -> None:
        if not self._is_csr_loaded:
            self.warmup_index()

    def get_user_seen_movie_ids(self, user_id: int) -> Set[int]:
        """
        Truy xuất tập hợp ID phim người dùng đã tương tác trong tập Train.
        Sử dụng chỉ mục CSR nén để đạt tốc độ microsecond.
        """
        self.ensure_csr_loaded()
        if self._csr_offsets is not None and self._csr_mids is not None:
            num_offsets = len(self._csr_offsets)
            if 1 <= user_id < num_offsets:
                start = self._csr_offsets[user_id]
                end = self._csr_offsets[user_id + 1]
                return set(self._csr_mids[start:end].tolist())
            return set()

        # Fallback đọc từ Parquet nếu CSR không có sẵn
        ratings = self.get_user_train_ratings(user_id)
        return {r["movieId"] for r in ratings}

    def get_user_train_ratings(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Truy xuất toàn bộ danh sách đánh giá của người dùng từ tập Train.
        Cam kết bảo vệ: CHỈ quét phân vùng Train, không quét Validation/Test.
        """
        with self._lock:
            if user_id in self._user_ratings_cache:
                return self._user_ratings_cache[user_id]

        if not self.train_split_path.exists():
            return []

        train_ds = ds.dataset(str(self.train_split_path), format="parquet")
        scanner = train_ds.scanner(
            columns=["userId", "movieId", "rating", "timestamp"],
            filter=ds.field("userId") == int(user_id)
        )
        ratings_list: List[Dict[str, Any]] = []
        for batch in scanner.to_batches():
            pydict = batch.to_pydict()
            for i in range(batch.num_rows):
                ratings_list.append({
                    "movieId": int(pydict["movieId"][i]),
                    "rating": float(pydict["rating"][i]),
                    "timestamp": int(pydict["timestamp"][i]),
                })

        # Sắp xếp theo thời gian tăng dần
        ratings_list.sort(key=lambda r: (r["timestamp"], r["movieId"]))
        del scanner
        del train_ds
        pa.default_memory_pool().release_unused()

        with self._lock:
            self._user_ratings_cache[user_id] = ratings_list

        return ratings_list

    def get_user_profile_summary(
        self,
        user_id: int,
        catalog_lookup: Any,
    ) -> Dict[str, Any]:
        """
        Tổng hợp hồ sơ người dùng thuần túy từ tập Train:
        - Tổng số tương tác Train
        - Điểm đánh giá trung bình
        - Các thể loại yêu thích (từ phim được đánh giá >= 3.5 sao)
        - Trạng thái người dùng mới (is_cold_start)
        """
        ratings = self.get_user_train_ratings(user_id)
        interaction_count = len(ratings)

        if interaction_count == 0:
            return {
                "userId": user_id,
                "is_cold_start": True,
                "interaction_count": 0,
                "rating_mean": 0.0,
                "favorite_genres": [],
                "recent_liked_movies": [],
            }

        scores = [r["rating"] for r in ratings]
        avg_rating = round(float(sum(scores) / len(scores)), 2)

        genre_counter: Counter[str] = Counter()
        recent_liked_mids: List[int] = []

        # Duyệt từ tương tác mới nhất về cũ nhất
        for r in reversed(ratings):
            mid = r["movieId"]
            if r["rating"] >= 3.5:
                if len(recent_liked_mids) < 10:
                    recent_liked_mids.append(mid)
                movie = catalog_lookup.get_movie_by_id(mid) if catalog_lookup else None
                if movie and movie.get("genres"):
                    for g in movie["genres"]:
                        if g and g != "(no genres listed)":
                            genre_counter[g] += 1

        top_genres = [g for g, _ in genre_counter.most_common(5)]

        recent_liked_movies = []
        if catalog_lookup:
            for mid in recent_liked_mids:
                m_info = catalog_lookup.get_movie_by_id(mid)
                if m_info:
                    recent_liked_movies.append({
                        "movieId": mid,
                        "title": m_info["title"],
                        "genres": m_info["genres"],
                    })

        return {
            "userId": user_id,
            "is_cold_start": False,
            "interaction_count": interaction_count,
            "rating_mean": avg_rating,
            "favorite_genres": top_genres,
            "recent_liked_movies": recent_liked_movies,
        }


# Thể hiện Singleton của UserHistoryRepository
_USER_HISTORY_REPO_INSTANCE: Optional[UserHistoryRepository] = None


def get_user_history_repository(
    data_root: Optional[Path] = None,
    csr_path: Optional[Path] = None,
) -> UserHistoryRepository:
    """Lấy hoặc khởi tạo singleton UserHistoryRepository."""
    global _USER_HISTORY_REPO_INSTANCE
    if _USER_HISTORY_REPO_INSTANCE is None:
        _USER_HISTORY_REPO_INSTANCE = UserHistoryRepository(data_root=data_root, csr_path=csr_path)
        _USER_HISTORY_REPO_INSTANCE.warmup_index()
    return _USER_HISTORY_REPO_INSTANCE

