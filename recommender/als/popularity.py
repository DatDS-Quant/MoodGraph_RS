"""
MoodGraph - Task 3A: Spark ALS & Baselines
Mô-đun: M03 - Mô hình gợi ý Baseline Phổ biến Toàn cục (Global Popularity Baseline).

Triển khai các mô hình gợi ý baseline không cá nhân hóa làm chuẩn so sánh thực nghiệm:
1. Baseline Số lượt đánh giá (POPULARITY_COUNT):
   Xếp hạng phim theo tổng số lượt rating trong tập Train (rating_count DESC).
   Phá vỡ thế hòa: avg_rating DESC, movieId ASC.
2. Baseline Trung bình có trọng số Bayes / IMDb (POPULARITY_WEIGHTED):
   Xếp hạng phim theo công thức Dirichlet / Bayesian prior:
       WeightedScore = (v * R + m * C) / (v + m)
   Trong đó:
       v: Số lượt đánh giá của phim trong Train (rating_count)
       R: Điểm trung bình của phim trong Train (avg_rating)
       C: Điểm trung bình toàn cục trên toàn bộ Train (global_mean)
       m: Tham số làm mượt tiên nghiệm (prior pseudo-counts, mặc định: 10.0)
   Phá vỡ thế hòa: WeightedScore DESC, v DESC, movieId ASC.

Đặc tính kỹ thuật:
- Lõi toán học thuần Python bảo đảm tính tất định 100% trong kiểm thử.
- Tích hợp PySpark phân tán xử lý gom cụm trên dữ liệu lớn (24,6 triệu ratings).
- Lọc lịch sử đã xem (Seen-item filtering) bảo đảm trả về đúng K phim chưa xem cho mỗi người dùng.
- Tương thích hoàn toàn với chuẩn M02 TopNEvaluator và hợp đồng tích hợp Task 3B.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
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

from pyspark.sql import DataFrame
import pyspark.sql.functions as F


@dataclass(frozen=True)
class PopularityMovieRecord:
    """Đại diện cho một bộ phim kèm thống kê độ phổ biến và thứ hạng tương ứng."""
    movie_id: int
    rating_count: int
    avg_rating: float
    weighted_score: float
    rank: int


@dataclass(frozen=True)
class PopularityRecommendation:
    """Đại diện cho một bản ghi gợi ý phim cho người dùng từ mô hình Popularity."""
    user_id: int
    movie_id: int
    rank: int
    raw_score: float
    model_name: str

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi bản ghi gợi ý phổ biến sang dictionary."""
        return {
            "userId": self.user_id,
            "movieId": self.movie_id,
            "rank": self.rank,
            "raw_score": self.raw_score,
            "model_name": self.model_name,
        }


def compute_weighted_score(v: int, r: float, c: float, m: float) -> float:
    """
    Tính điểm trung bình có trọng số Bayes (Công thức IMDb / Dirichlet prior):
        WeightedScore = (v * R + m * C) / (v + m)
    
    Args:
        v: Số lượt đánh giá của phim trong Train (v >= 0).
        r: Điểm trung bình của phim trong Train.
        c: Điểm trung bình toàn cục trên toàn bộ Train.
        m: Trọng số tiên nghiệm / tham số làm mượt (m >= 0).
    
    Returns:
        Điểm số trọng số hữu hạn dạng float.
    """
    if v < 0:
        raise ValueError(f"Rating count v must be non-negative, got {v}")
    if m < 0:
        raise ValueError(f"Smoothing parameter m must be non-negative, got {m}")
    if math.isnan(r) or math.isinf(r):
        raise ValueError(f"Movie average rating r must be finite, got {r}")
    if math.isnan(c) or math.isinf(c):
        raise ValueError(f"Global mean c must be finite, got {c}")

    denominator = float(v + m)
    if denominator == 0.0:
        # Trường hợp biên: Phim có 0 lượt đánh giá và tham số m bằng 0
        return float(c)

    score = (float(v) * float(r) + float(m) * float(c)) / denominator
    return score


def rank_movies_by_count(
    movie_stats: Sequence[Tuple[int, int, float]],
) -> List[PopularityMovieRecord]:
    """
    Sắp xếp tất định danh sách phim theo Số lượng đánh giá (Rating Count).
    
    Quy tắc phá vỡ thế hòa:
    1. rating_count DESC (ưu tiên chính)
    2. avg_rating DESC (ưu tiên phụ)
    3. movieId ASC (tất định)
    """
    # Sắp xếp theo khóa: (-rating_count, -avg_rating, movieId)
    sorted_stats = sorted(
        movie_stats,
        key=lambda x: (-x[1], -x[2], x[0]),
    )

    ranked_records: List[PopularityMovieRecord] = []
    for rank_idx, (mid, count, avg_r) in enumerate(sorted_stats, start=1):
        record = PopularityMovieRecord(
            movie_id=mid,
            rating_count=count,
            avg_rating=avg_r,
            weighted_score=float(count),  # Điểm raw chính là số lượt rating
            rank=rank_idx,
        )
        ranked_records.append(record)

    return ranked_records


def rank_movies_by_weighted_average(
    movie_stats: Sequence[Tuple[int, int, float]],
    global_mean: float,
    m: float = 10.0,
) -> List[PopularityMovieRecord]:
    """
    Sắp xếp tất định danh sách phim theo Trung bình có trọng số Bayes.
    
    Quy tắc phá vỡ thế hòa:
    1. weighted_score DESC (ưu tiên chính)
    2. rating_count DESC (ưu tiên phụ)
    3. movieId ASC (tất định)
    """
    scored_items: List[Tuple[int, int, float, float]] = []
    for mid, count, avg_r in movie_stats:
        ws = compute_weighted_score(v=count, r=avg_r, c=global_mean, m=m)
        scored_items.append((mid, count, avg_r, ws))

    # Sắp xếp theo khóa: (-weighted_score, -rating_count, movieId)
    sorted_stats = sorted(
        scored_items,
        key=lambda x: (-x[3], -x[1], x[0]),
    )

    ranked_records: List[PopularityMovieRecord] = []
    for rank_idx, (mid, count, avg_r, ws) in enumerate(sorted_stats, start=1):
        record = PopularityMovieRecord(
            movie_id=mid,
            rating_count=count,
            avg_rating=avg_r,
            weighted_score=ws,
            rank=rank_idx,
        )
        ranked_records.append(record)

    return ranked_records


def generate_user_top_k(
    user_id: int,
    ranked_movie_ids: Sequence[int],
    scores_map: Dict[int, float],
    seen_movies: Set[int],
    k: int = 10,
    model_name: str = "POPULARITY",
) -> List[PopularityRecommendation]:
    """
    Sinh danh sách Top-K cho một người dùng bằng cách lọc bỏ các phim đã xem.
    Duyệt danh sách xếp hạng toàn cục và bỏ qua seen_movies cho đến khi đủ K phim.
    """
    if k <= 0:
        raise ValueError(f"Cutoff k must be strictly positive, got: {k}")

    recs: List[PopularityRecommendation] = []
    rank_counter = 1

    for mid in ranked_movie_ids:
        if mid not in seen_movies:
            score = scores_map.get(mid, 0.0)
            rec = PopularityRecommendation(
                user_id=user_id,
                movie_id=mid,
                rank=rank_counter,
                raw_score=score,
                model_name=model_name,
            )
            recs.append(rec)
            rank_counter += 1
            if len(recs) == k:
                break

    return recs


def generate_batch_top_k(
    user_histories: Dict[int, Set[int]],
    ranked_movie_ids: Sequence[int],
    scores_map: Dict[int, float],
    k: int = 10,
    model_name: str = "POPULARITY",
    target_user_ids: Optional[Iterable[int]] = None,
) -> Dict[int, List[int]]:
    """
    Sinh danh sách Top-K cho tập hợp người dùng. Trả về mapping userId -> List[movieId].
    """
    eval_uids = target_user_ids if target_user_ids is not None else user_histories.keys()
    results: Dict[int, List[int]] = {}

    for uid in eval_uids:
        seen = user_histories.get(uid, set())
        recs = generate_user_top_k(
            user_id=uid,
            ranked_movie_ids=ranked_movie_ids,
            scores_map=scores_map,
            seen_movies=seen,
            k=k,
            model_name=model_name,
        )
        results[uid] = [r.movie_id for r in recs]

    return results


class PopularityRecommender:
    """
    Bộ gợi ý Popularity đầy đủ hỗ trợ cả 2 biến thể: Count và Weighted Average.
    """

    def __init__(self, m: float = 10.0):
        self.m = float(m)
        self.global_mean: float = 0.0
        self.count_ranked_records: List[PopularityMovieRecord] = []
        self.weighted_ranked_records: List[PopularityMovieRecord] = []
        self._count_ranked_ids: List[int] = []
        self._weighted_ranked_ids: List[int] = []
        self._count_scores_map: Dict[int, float] = {}
        self._weighted_scores_map: Dict[int, float] = {}
        self.is_fitted: bool = False

    def fit_from_stats(
        self,
        movie_stats: Sequence[Tuple[int, int, float]],
        global_mean: float,
        m: Optional[float] = None,
    ) -> PopularityRecommender:
        """
        Khớp mô hình từ thống kê phim đã tổng hợp trước (dùng cho test và deploy nhẹ).
        """
        if m is not None:
            self.m = float(m)
        self.global_mean = float(global_mean)

        self.count_ranked_records = rank_movies_by_count(movie_stats)
        self.weighted_ranked_records = rank_movies_by_weighted_average(
            movie_stats, self.global_mean, self.m
        )

        self._count_ranked_ids = [r.movie_id for r in self.count_ranked_records]
        self._weighted_ranked_ids = [r.movie_id for r in self.weighted_ranked_records]

        self._count_scores_map = {r.movie_id: float(r.rating_count) for r in self.count_ranked_records}
        self._weighted_scores_map = {r.movie_id: r.weighted_score for r in self.weighted_ranked_records}

        self.is_fitted = True
        return self

    def fit_from_spark(
        self,
        train_df: DataFrame,
        m: Optional[float] = None,
    ) -> PopularityRecommender:
        """
        Khớp mô hình trực tiếp từ PySpark Train DataFrame bằng phép gom cụm phân tán.
        """
        if m is not None:
            self.m = float(m)

        # 1. Tính điểm trung bình toàn cục
        global_mean_val = (
            train_df.select(F.avg("rating").alias("mean_r")).first()["mean_r"]
        )
        self.global_mean = float(global_mean_val)

        # 2. Tính số lượng và điểm trung bình theo từng movieId
        movie_agg_df = train_df.groupBy("movieId").agg(
            F.count("userId").alias("rating_count"),
            F.avg("rating").alias("avg_rating"),
        )

        # Thu thập bảng gọn nhẹ (58.932 dòng, ~2-3 MB)
        rows = movie_agg_df.collect()
        movie_stats = [
            (int(row["movieId"]), int(row["rating_count"]), float(row["avg_rating"]))
            for row in rows
        ]

        return self.fit_from_stats(movie_stats, self.global_mean, self.m)

    def recommend(
        self,
        user_id: int,
        seen_movies: Set[int],
        k: int = 10,
        variant: str = "count",
    ) -> List[PopularityRecommendation]:
        """
        Sinh gợi ý Top-K cho một người dùng đơn lẻ (biến thể 'count' hoặc 'weighted').
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted. Call fit_from_stats or fit_from_spark first.")

        var_lower = variant.lower()
        if var_lower == "count":
            ranked_ids = self._count_ranked_ids
            scores_map = self._count_scores_map
            model_name = "POPULARITY_COUNT"
        elif var_lower in ("weighted", "bayesian"):
            ranked_ids = self._weighted_ranked_ids
            scores_map = self._weighted_scores_map
            model_name = "POPULARITY_WEIGHTED"
        else:
            raise ValueError(f"Unknown popularity variant: {variant}. Expected 'count' or 'weighted'.")

        return generate_user_top_k(
            user_id=user_id,
            ranked_movie_ids=ranked_ids,
            scores_map=scores_map,
            seen_movies=seen_movies,
            k=k,
            model_name=model_name,
        )

    def recommend_for_users(
        self,
        user_histories: Dict[int, Set[int]],
        k: int = 10,
        variant: str = "count",
        target_user_ids: Optional[Iterable[int]] = None,
    ) -> Dict[int, List[int]]:
        """
        Sinh từ điển gợi ý Top-K cho nhiều người dùng.
        """
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted.")

        var_lower = variant.lower()
        if var_lower == "count":
            ranked_ids = self._count_ranked_ids
            scores_map = self._count_scores_map
            model_name = "POPULARITY_COUNT"
        elif var_lower in ("weighted", "bayesian"):
            ranked_ids = self._weighted_ranked_ids
            scores_map = self._weighted_scores_map
            model_name = "POPULARITY_WEIGHTED"
        else:
            raise ValueError(f"Unknown popularity variant: {variant}")

        return generate_batch_top_k(
            user_histories=user_histories,
            ranked_movie_ids=ranked_ids,
            scores_map=scores_map,
            k=k,
            model_name=model_name,
            target_user_ids=target_user_ids,
        )

    def export_ranking_table(self, variant: str = "count", top_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """Xuất bảng xếp hạng phim dưới dạng danh sách từ điển."""
        if not self.is_fitted:
            raise RuntimeError("Model has not been fitted.")

        var_lower = variant.lower()
        if var_lower == "count":
            records = self.count_ranked_records
        else:
            records = self.weighted_ranked_records

        if top_n is not None:
            records = records[:top_n]

        return [asdict(r) for r in records]
