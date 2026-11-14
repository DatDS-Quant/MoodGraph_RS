"""
MoodGraph - Task 3A: ALS Candidate Generation & Exact Top-N Recommendation
Mô-đun: M06/M10 - Bộ sinh gợi ý ứng viên Top-N chính xác bằng ALS Spark.

Cung cấp cơ chế sinh danh sách Top-K an toàn bộ nhớ, kiểm chứng toán học chuẩn xác
sử dụng ma trận nhân tố ẩn đã huấn luyện từ Spark ALS (rank=16).

Các nguyên tắc kỹ thuật cốt lõi:
1. Exact Filter-Before-Top-K (Lọc trước khi Top-K):
   Loại bỏ toàn bộ tương tác người dùng đã xem trong Train TRƯỚC KHI trích xuất Top-K.
   Đảm bảo 100% không mắc sai số thiếu Top-K do oversampling cố định (kể cả heavy users).
2. Phép tính theo lô giới hạn an toàn bộ nhớ (Bounded Batch Scoring):
   Chấm điểm theo lô (ví dụ 2.500 users) trên toàn bộ 58.932 phim bằng BLAS matrix multiplication
   (P_batch @ Q.T), kiểm soát RAM đỉnh dưới 600 MB.
3. Phá vỡ thế hòa điểm số tất định (Deterministic Tie-Breaking):
   Ưu tiên 1: als_score DESC; Ưu tiên 2: movieId ASC.
   Xử lý triệt để ranh giới phân vị k khi có nhiều phim đồng hạng điểm số.
4. Tính toàn vẹn khoa học:
   - Toàn bộ danh mục: 62.423 phim.
   - Danh mục có thể chấm điểm: 58.932 phim có nhân tố M05.
   - Danh mục không thể chấm điểm: 3.491 phim không có nhân tố (không gán 0.0 giả tạo).
"""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from recommender.als.evaluator import validate_k


@dataclass(frozen=True)
class ALSCandidateConfig:
    """Cấu hình cho bộ sinh ứng viên ALS (K list, batch size, model version)."""
    k_list: Tuple[int, ...] = (5, 10, 20)
    batch_size: int = 2500
    model_version: str = "m05_spark_als_rank16"
    candidate_source: str = "ALS"

    def validate(self) -> None:
        """Kiểm tra tính hợp lệ của danh sách K và kích thước batch."""
        for k in self.k_list:
            validate_k(k)
        if self.batch_size <= 0:
            raise ValueError(f"batch_size must be positive integer, got: {self.batch_size}")


@dataclass
class ScoreableCatalog:
    """
    Lưu trữ ma trận nhân tố ẩn vật phẩm (Item Factors) và metadata danh mục phục vụ chấm điểm.
    """
    movie_ids: np.ndarray  # Mảng 1D int64 kích thước (M,)
    factors: np.ndarray    # Mảng 2D float32 kích thước (M, rank)
    movie_to_idx: Dict[int, int] = field(default_factory=dict)
    catalog_movie_ids: Optional[Set[int]] = None

    def __post_init__(self) -> None:
        if self.movie_ids.ndim != 1:
            raise ValueError(f"movie_ids must be 1D array, got shape {self.movie_ids.shape}")
        if self.factors.ndim != 2:
            raise ValueError(f"factors must be 2D array, got shape {self.factors.shape}")
        if len(self.movie_ids) != self.factors.shape[0]:
            raise ValueError(
                f"Length mismatch: {len(self.movie_ids)} movie_ids vs {self.factors.shape[0]} factor rows"
            )
        if np.any(np.isnan(self.factors)) or np.any(np.isinf(self.factors)):
            raise ValueError("item factors matrix contains NaN or Inf values")

        # Xây dựng bản đồ movie_to_idx nếu chưa được truyền
        if not self.movie_to_idx:
            self.movie_to_idx = {int(mid): idx for idx, mid in enumerate(self.movie_ids)}
        if len(self.movie_to_idx) != len(self.movie_ids):
            raise ValueError("Duplicate movieId detected in scoreable movie_ids array")

    @property
    def num_movies(self) -> int:
        """Tổng số lượng phim có thể chấm điểm trong danh mục."""
        return len(self.movie_ids)

    @property
    def rank(self) -> int:
        """Số chiều của không gian nhân tố ẩn."""
        return self.factors.shape[1]

    @property
    def scorable_movie_ids(self) -> Set[int]:
        """Tập hợp các mã movieId có thể cho điểm."""
        return set(self.movie_to_idx.keys())

    @property
    def unscoreable_movie_ids(self) -> Set[int]:
        """Tập hợp các mã movieId không thể cho điểm (thiếu vector nhân tố)."""
        if self.catalog_movie_ids is None:
            return set()
        return self.catalog_movie_ids - self.scorable_movie_ids


@dataclass
class UserFactorsContainer:
    """
    Lưu trữ ma trận nhân tố ẩn người dùng (User Factors) và bản đồ tra cứu chỉ mục userId.
    """
    user_ids: np.ndarray  # Mảng 1D int64 kích thước (U,)
    factors: np.ndarray   # Mảng 2D float32 kích thước (U, rank)
    user_to_idx: Dict[int, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.user_ids.ndim != 1:
            raise ValueError(f"user_ids must be 1D array, got shape {self.user_ids.shape}")
        if self.factors.ndim != 2:
            raise ValueError(f"factors must be 2D array, got shape {self.factors.shape}")
        if len(self.user_ids) != self.factors.shape[0]:
            raise ValueError(
                f"Length mismatch: {len(self.user_ids)} user_ids vs {self.factors.shape[0]} factor rows"
            )
        if np.any(np.isnan(self.factors)) or np.any(np.isinf(self.factors)):
            raise ValueError("user factors matrix contains NaN or Inf values")

        if not self.user_to_idx:
            self.user_to_idx = {int(uid): idx for idx, uid in enumerate(self.user_ids)}
        if len(self.user_to_idx) != len(self.user_ids):
            raise ValueError("Duplicate userId detected in user_ids array")

    @property
    def num_users(self) -> int:
        """Tổng số lượng người dùng có vector nhân tố ẩn."""
        return len(self.user_ids)

    @property
    def rank(self) -> int:
        """Số chiều của không gian nhân tố ẩn người dùng."""
        return self.factors.shape[1]


def exact_top_k_oracle(
    user_factor: np.ndarray,
    item_factors: np.ndarray,
    movie_ids: np.ndarray,
    seen_movie_ids: Set[int],
    k: int,
) -> List[Tuple[int, float]]:
    """
    Hàm đối chứng tham chiếu độc lập cho giải thuật Exact Filter-Before-Top-K:
    1. Tính tích vô hướng từng vật phẩm.
    2. Loại bỏ các vật phẩm nằm trong seen_movie_ids.
    3. Sắp xếp tất định các ứng viên chưa xem theo (-score, movieId).
    4. Trả về Top-K [(movieId, score), ...].
    """
    validate_k(k)
    seen_set = set(seen_movie_ids)
    scored_unseen: List[Tuple[int, float]] = []

    for idx, mid in enumerate(movie_ids):
        mid_int = int(mid)
        if mid_int in seen_set:
            continue
        # Tích vô hướng đơn lẻ
        score = float(np.dot(user_factor, item_factors[idx]))
        if math.isnan(score) or math.isinf(score):
            raise ValueError(f"Non-finite score encountered for movie {mid_int}: {score}")
        scored_unseen.append((mid_int, score))

    # Sắp xếp tất định: score DESC, movieId ASC
    scored_unseen.sort(key=lambda x: (-x[1], x[0]))
    return scored_unseen[:k]


def fast_exact_top_k_from_scores(
    scores: np.ndarray,
    movie_ids: np.ndarray,
    k: int,
) -> List[Tuple[int, float]]:
    """
    Trích xuất Top-K nhanh, an toàn bộ nhớ từ mảng điểm số 1D đã được che (mask) vật phẩm đã xem bằng -inf.
    
    Bảo đảm 100% tương đương toán học với exact_top_k_oracle:
    - Bỏ qua các giá trị -inf.
    - Dùng argpartition đạt độ phức tạp trung bình O(M).
    - Phá vỡ thế hòa điểm số tất định (deterministic tie-breaking) tại ranh giới phân vị k.
    """
    validate_k(k)
    valid_mask = np.isfinite(scores)
    valid_count = int(np.sum(valid_mask))
    if valid_count == 0:
        return []

    if valid_count <= k:
        valid_scores = scores[valid_mask]
        valid_ids = movie_ids[valid_mask]
        pairs = [(int(mid), float(sc)) for mid, sc in zip(valid_ids, valid_scores)]
        pairs.sort(key=lambda x: (-x[1], x[0]))
        return pairs

    # Sử dụng argpartition để tìm top K ứng viên
    part_idx = np.argpartition(-scores, k)[:k]
    top_scores = scores[part_idx]
    min_top_score = float(np.min(top_scores))

    # Phát hiện trường hợp hòa điểm số tại ranh giới K
    total_ties = int(np.sum(scores == min_top_score))
    top_ties = int(np.sum(top_scores == min_top_score))

    if total_ties > top_ties:
        # Hòa điểm số qua ngưỡng: Lấy toàn bộ phần tử >= min_top_score và sắp xếp tất định
        cand_mask = scores >= min_top_score
        cand_scores = scores[cand_mask]
        cand_ids = movie_ids[cand_mask]
        pairs = [(int(mid), float(sc)) for mid, sc in zip(cand_ids, cand_scores)]
        pairs.sort(key=lambda x: (-x[1], x[0]))
        return pairs[:k]
    else:
        # Không có hòa điểm số qua ngưỡng: Sắp xếp đúng K phần tử trong partition
        top_ids = movie_ids[part_idx]
        pairs = [(int(mid), float(sc)) for mid, sc in zip(top_ids, top_scores)]
        pairs.sort(key=lambda x: (-x[1], x[0]))
        return pairs[:k]


class ALSCandidateGenerator:
    """
    Bộ sinh ứng viên ALS chuẩn Production.
    
    Vận hành trên ma trận nhân tố ẩn để sinh gợi ý Top-N chính xác
    với cơ chế loại bỏ lịch sử đã xem từ trước và phá vỡ thế hòa tất định.
    """

    def __init__(self, config: Optional[ALSCandidateConfig] = None):
        self.config = config or ALSCandidateConfig()
        self.config.validate()
        self.catalog: Optional[ScoreableCatalog] = None
        self.user_factors: Optional[UserFactorsContainer] = None

    def load_catalog_and_factors(
        self,
        model_dir: Union[str, Path],
        movies_parquet_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Nạp itemFactors, userFactors và danh mục đầy đủ từ các file Parquet trên đĩa.
        """
        model_path = Path(model_dir)
        item_path = model_path / "spark_model" / "itemFactors"
        user_path = model_path / "spark_model" / "userFactors"

        if not item_path.exists():
            raise FileNotFoundError(f"itemFactors parquet directory not found at: {item_path}")
        if not user_path.exists():
            raise FileNotFoundError(f"userFactors parquet directory not found at: {user_path}")

        # 1. Nạp ma trận nhân tố vật phẩm
        tbl_items = pq.read_table(item_path)
        item_df = tbl_items.to_pandas()
        item_ids = item_df["id"].values.astype(np.int64)
        item_vecs = np.vstack(item_df["features"].values).astype(np.float32)

        # 2. Nạp toàn bộ danh mục phim (nếu được cung cấp)
        catalog_ids: Optional[Set[int]] = None
        if movies_parquet_path is not None:
            mov_path = Path(movies_parquet_path)
            if mov_path.exists():
                tbl_movies = pq.read_table(mov_path)
                catalog_ids = set(tbl_movies.column("movieId").to_pylist())

        self.catalog = ScoreableCatalog(
            movie_ids=item_ids,
            factors=item_vecs,
            catalog_movie_ids=catalog_ids,
        )

        # 3. Nạp ma trận nhân tố người dùng
        tbl_users = pq.read_table(user_path)
        user_df = tbl_users.to_pandas()
        user_ids = user_df["id"].values.astype(np.int64)
        user_vecs = np.vstack(user_df["features"].values).astype(np.float32)

        if user_vecs.shape[1] != self.catalog.rank:
            raise ValueError(
                f"Rank mismatch: user factors rank {user_vecs.shape[1]} != item factors rank {self.catalog.rank}"
            )

        self.user_factors = UserFactorsContainer(
            user_ids=user_ids,
            factors=user_vecs,
        )

    def audit_catalog(self) -> Dict[str, Any]:
        """
        Kiểm toán quy mô danh mục phim: Toàn bộ catalog vs Catalog có thể chấm điểm vs Không thể chấm điểm.
        """
        if self.catalog is None:
            raise ValueError("Catalog not loaded. Call load_catalog_and_factors() first.")

        scorable_count = self.catalog.num_movies
        full_count = len(self.catalog.catalog_movie_ids) if self.catalog.catalog_movie_ids else scorable_count
        unscoreable_count = len(self.catalog.unscoreable_movie_ids)
        coverage_pct = (scorable_count / float(full_count)) * 100.0 if full_count > 0 else 100.0

        return {
            "full_catalog_size": full_count,
            "scorable_catalog_size": scorable_count,
            "unscoreable_catalog_size": unscoreable_count,
            "scorable_coverage_percent": coverage_pct,
            "factor_rank": self.catalog.rank,
        }

    def recommend_user(
        self,
        user_id: int,
        seen_movie_ids: Optional[Set[int]] = None,
        k: int = 10,
    ) -> List[Tuple[int, float]]:
        """
        Sinh danh sách gợi ý Top-K chính xác cho một người dùng đơn lẻ.
        Lọc bỏ trước các phim trong seen_movie_ids và giải quyết hòa điểm tất định.
        """
        validate_k(k)
        if self.catalog is None or self.user_factors is None:
            raise ValueError("Model factors not loaded. Call load_catalog_and_factors() first.")

        user_idx = self.user_factors.user_to_idx.get(user_id)
        if user_idx is None:
            # Người dùng cold-start: không có vector nhân tố ẩn
            return []

        u_factor = self.user_factors.factors[user_idx]
        scores = np.dot(self.catalog.factors, u_factor)  # kích thước: (M,)

        seen_set = seen_movie_ids or set()
        for mid in seen_set:
            idx = self.catalog.movie_to_idx.get(mid)
            if idx is not None:
                scores[idx] = -np.inf

        return fast_exact_top_k_from_scores(scores, self.catalog.movie_ids, k)

    def recommend_batch(
        self,
        batch_user_ids: Sequence[int],
        user_histories: Dict[int, Set[int]],
        k: int = 20,
    ) -> Dict[int, List[Tuple[int, float]]]:
        """
        Sinh danh sách gợi ý Top-K chính xác cho một lô người dùng bị chặn giới hạn bộ nhớ.
        Sử dụng BLAS matrix multiplication (P_batch @ Q.T) đạt hiệu năng cao, che mặt nạ lịch sử
        và trích xuất Top-K tất định.
        """
        validate_k(k)
        if self.catalog is None or self.user_factors is None:
            raise ValueError("Model factors not loaded. Call load_catalog_and_factors() first.")

        results: Dict[int, List[Tuple[int, float]]] = {}
        valid_uids: List[int] = []
        valid_row_indices: List[int] = []

        for uid in batch_user_ids:
            uid_int = int(uid)
            idx = self.user_factors.user_to_idx.get(uid_int)
            if idx is not None:
                valid_uids.append(uid_int)
                valid_row_indices.append(idx)
            else:
                # Người dùng cold-start: không có vector nhân tố
                results[uid_int] = []

        if not valid_uids:
            return results

        # Trích xuất P_batch kích thước (B, rank)
        P_batch = self.user_factors.factors[valid_row_indices]  # kích thước: (B, rank)
        # Phép nhân ma trận: (B, rank) @ (rank, M) -> (B, M)
        scores_matrix = np.matmul(P_batch, self.catalog.factors.T)  # kích thước: (B, M)

        # Che mặt nạ các vật phẩm đã xem của từng người dùng bằng -inf
        for row_idx, uid in enumerate(valid_uids):
            seen_set = user_histories.get(uid, set())
            for mid in seen_set:
                item_idx = self.catalog.movie_to_idx.get(mid)
                if item_idx is not None:
                    scores_matrix[row_idx, item_idx] = -np.inf

        # Trích xuất Top-K cho từng người dùng với 2D argpartition vectơ hóa khi có thể
        B = len(valid_uids)
        M = self.catalog.num_movies
        if M > k:
            part_idx_2d = np.argpartition(-scores_matrix, kth=k, axis=1)[:, :k]
            for row_idx, uid in enumerate(valid_uids):
                row_scores = scores_matrix[row_idx]
                top_part = part_idx_2d[row_idx]
                top_scores = row_scores[top_part]
                min_top = float(np.min(top_scores))
                if not np.isfinite(min_top):
                    # Một số vật phẩm trong Top K là -inf (người dùng có ít hơn K phim chưa xem)
                    results[uid] = fast_exact_top_k_from_scores(row_scores, self.catalog.movie_ids, k)
                else:
                    total_ties = int(np.sum(row_scores == min_top))
                    top_ties = int(np.sum(top_scores == min_top))
                    if total_ties > top_ties:
                        results[uid] = fast_exact_top_k_from_scores(row_scores, self.catalog.movie_ids, k)
                    else:
                        top_mids = self.catalog.movie_ids[top_part]
                        pairs = [(int(mid), float(sc)) for mid, sc in zip(top_mids, top_scores)]
                        pairs.sort(key=lambda x: (-x[1], x[0]))
                        results[uid] = pairs
        else:
            for row_idx, uid in enumerate(valid_uids):
                results[uid] = fast_exact_top_k_from_scores(scores_matrix[row_idx], self.catalog.movie_ids, k)

        return results

    def generate_recommendations(
        self,
        target_user_ids: Iterable[int],
        user_histories: Dict[int, Set[int]],
        k: int = 20,
        batch_size: Optional[int] = None,
        show_progress: bool = True,
    ) -> Dict[int, List[Tuple[int, float]]]:
        """
        Sinh gợi ý Top-K cho toàn bộ tập người dùng mục tiêu thông qua các batch giới hạn an toàn RAM.
        """
        validate_k(k)
        effective_batch_size = batch_size or self.config.batch_size
        target_list = list(target_user_ids)
        total_users = len(target_list)
        all_recs: Dict[int, List[Tuple[int, float]]] = {}

        t0_total = time.time()
        num_batches = math.ceil(total_users / effective_batch_size) if total_users > 0 else 0

        for b_idx in range(num_batches):
            start = b_idx * effective_batch_size
            end = min(start + effective_batch_size, total_users)
            batch_uids = target_list[start:end]

            batch_res = self.recommend_batch(
                batch_user_ids=batch_uids,
                user_histories=user_histories,
                k=k,
            )
            all_recs.update(batch_res)

            if show_progress and ((b_idx + 1) % 10 == 0 or (b_idx + 1) == num_batches):
                elapsed = time.time() - t0_total
                processed = len(all_recs)
                speed = processed / elapsed if elapsed > 0 else 0.0
                print(
                    f"  [Progress] Processed {processed:,}/{total_users:,} users "
                    f"({b_idx + 1}/{num_batches} batches) in {elapsed:.1f}s ({speed:.1f} users/s)",
                    flush=True,
                )

        return all_recs

    def export_recommendations_dataframe(
        self,
        recommendations: Dict[int, List[Tuple[int, float]]],
        model_version: Optional[str] = None,
    ) -> pa.Table:
        """
        Chuyển đổi mapping gợi ý sang Apache Arrow Table phục vụ tuần tự hóa tốc độ cao.
        Schema: userId (int64), movieId (int64), rank (int32), als_score (float32),
                candidate_source (string), model_version (string).
        """
        version_str = model_version or self.config.model_version
        uids: List[int] = []
        mids: List[int] = []
        ranks: List[int] = []
        scores: List[float] = []

        for uid, rec_list in recommendations.items():
            for r_idx, (mid, sc) in enumerate(rec_list, start=1):
                uids.append(uid)
                mids.append(mid)
                ranks.append(r_idx)
                scores.append(sc)

        table = pa.Table.from_arrays(
            [
                pa.array(uids, type=pa.int64()),
                pa.array(mids, type=pa.int64()),
                pa.array(ranks, type=pa.int32()),
                pa.array(scores, type=pa.float32()),
                pa.array([self.config.candidate_source] * len(uids), type=pa.string()),
                pa.array([version_str] * len(uids), type=pa.string()),
            ],
            names=["userId", "movieId", "rank", "als_score", "candidate_source", "model_version"],
        )
        return table

    def save_recommendations_parquet(
        self,
        recommendations: Dict[int, List[Tuple[int, float]]],
        output_path: Union[str, Path],
        model_version: Optional[str] = None,
    ) -> None:
        """
        Lưu danh sách gợi ý ra tệp định dạng Parquet với chuẩn nén Snappy.
        """
        table = self.export_recommendations_dataframe(recommendations, model_version)
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, out_p, compression="snappy")
