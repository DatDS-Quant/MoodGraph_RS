"""
MoodGraph - Task 3A: Evaluation Engine for Top-N Recommender Systems
Mô-đun: M02 - Động cơ đánh giá Top-N đa chỉ số chuẩn khoa học.

Cung cấp công cụ đánh giá ngoại tuyến (offline evaluation) chính xác theo giao thức
User-wise Leave-1-Last (MovieLens 25M).

Các chỉ số hỗ trợ:
- HitRate@K (HR@K)
- NDCG@K
- MRR@K
- Precision@K
- Recall@K
- Catalog Coverage@K (Full-Catalog và Scorable-Catalog)

Quy tắc giao thức cốt lõi:
- Mục tiêu đánh giá dương: rating >= relevance_threshold (mặc định: 3.5 sao).
- Mẫu số đánh giá chuẩn: Đo lường nghiêm ngặt trên Positive-Target Cohort.
- Người dùng thiếu khuyến nghị: Đánh giá bằng 0.0 (miss), bảo lưu 100% trong mẫu số (denominator).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class HeldOutTarget:
    """Đại diện cho một tương tác mục tiêu bị giữ lại (held-out target) của người dùng."""
    movie_id: int
    rating: float
    timestamp: Optional[int] = None


@dataclass(frozen=True)
class SingleUserMetricResult:
    """Kết quả đo lường riêng lẻ cho một người dùng tại một ngưỡng K cụ thể."""
    user_id: int
    k: int
    hit: float
    recall: float
    precision: float
    ndcg: float
    mrr: float
    rank: Optional[int]
    is_positive_target: bool


@dataclass
class EvaluationSummary:
    """Tóm tắt tổng hợp các chỉ số đánh giá Top-K cho toàn bộ tập người dùng."""
    k: int
    hit_rate: float
    recall: float
    precision: float
    ndcg: float
    mrr: float
    catalog_coverage_full: Optional[float]
    catalog_coverage_scorable: Optional[float]
    num_unique_recommended_movies: int
    positive_cohort_size: int
    non_positive_cohort_size: int
    total_target_users: int
    users_with_recommendations: int
    users_missing_recommendations: int
    hit_count: int
    diagnostic_all_users: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi tóm tắt kết quả sang từ điển phục vụ báo cáo và lưu trữ JSON."""
        return {
            "k": self.k,
            "hit_rate": self.hit_rate,
            "recall": self.recall,
            "precision": self.precision,
            "ndcg": self.ndcg,
            "mrr": self.mrr,
            "catalog_coverage_full": self.catalog_coverage_full,
            "catalog_coverage_scorable": self.catalog_coverage_scorable,
            "num_unique_recommended_movies": self.num_unique_recommended_movies,
            "positive_cohort_size": self.positive_cohort_size,
            "non_positive_cohort_size": self.non_positive_cohort_size,
            "total_target_users": self.total_target_users,
            "users_with_recommendations": self.users_with_recommendations,
            "users_missing_recommendations": self.users_missing_recommendations,
            "hit_count": self.hit_count,
            "diagnostic_all_users": self.diagnostic_all_users,
        }


def validate_k(k: int) -> None:
    """Xác thực ngưỡng K phải là số nguyên dương nghiêm ngặt."""
    if not isinstance(k, int) or k <= 0:
        raise ValueError(f"Cutoff K must be a strictly positive integer, got: {k}")


def validate_raw_score(score: float, movie_id: int) -> None:
    """Xác thực raw_score là số hữu hạn hợp lệ (không NaN, không Inf)."""
    if not isinstance(score, (int, float)):
        raise ValueError(f"Score for movie {movie_id} must be numeric, got: {type(score).__name__}")
    if math.isnan(score) or math.isinf(score):
        raise ValueError(f"Score for movie {movie_id} must be finite (got {score})")


def sort_and_rank_candidates(
    scored_items: Iterable[Tuple[int, float]],
    k: Optional[int] = None,
) -> List[int]:
    """
    Sắp xếp tất định các ứng viên đã chấm điểm và trả về danh sách movieIds đã xếp hạng.
    
    Quy tắc phá vỡ thế hòa:
    1. raw_score DESC
    2. movieId ASC (tất định, ổn định)
    """
    items_list = list(scored_items)
    seen_ids: Set[int] = set()
    for mid, score in items_list:
        validate_raw_score(score, mid)
        if mid in seen_ids:
            raise ValueError(f"Duplicate movieId detected in scored candidates: {mid}")
        seen_ids.add(mid)

    # Sort: raw_score descending (-score), movieId ascending (+mid)
    sorted_items = sorted(items_list, key=lambda x: (-x[1], x[0]))

    if k is not None:
        validate_k(k)
        sorted_items = sorted_items[:k]

    return [mid for mid, _ in sorted_items]


def compute_single_user_metrics(
    recommended_movie_ids: Sequence[int],
    target_movie_id: int,
    k: int,
) -> Dict[str, Union[float, Optional[int]]]:
    """
    Tính toán các chỉ số Top-N cho một người dùng đơn lẻ có ĐÚNG 1 phim mục tiêu.
    
    Theo giao thức Leave-1-Last:
    Nếu tìm thấy target tại rank j (1 <= j <= k):
        - HitRate@K = 1.0
        - Recall@K = 1.0
        - Precision@K = 1.0 / k
        - NDCG@K = 1.0 / log2(j + 1)
        - MRR@K = 1.0 / j
        - rank = j
    Nếu không tìm thấy target trong Top-K:
        - HitRate@K = 0.0, Recall@K = 0.0, NDCG@K = 0.0, MRR@K = 0.0, rank = None
    """
    validate_k(k)

    # Validate no duplicate IDs in recommendations
    top_k = list(recommended_movie_ids[:k])
    seen: Set[int] = set()
    for mid in top_k:
        if mid in seen:
            raise ValueError(f"Duplicate movieId {mid} detected in recommendation list")
        seen.add(mid)

    # Search for target in top_k
    rank_found: Optional[int] = None
    for idx, mid in enumerate(top_k, start=1):
        if mid == target_movie_id:
            rank_found = idx
            break

    if rank_found is not None:
        hit = 1.0
        recall = 1.0
        precision = 1.0 / float(k)
        ndcg = 1.0 / math.log2(float(rank_found) + 1.0)
        mrr = 1.0 / float(rank_found)
    else:
        hit = 0.0
        recall = 0.0
        precision = 0.0
        ndcg = 0.0
        mrr = 0.0

    return {
        "hit": hit,
        "recall": recall,
        "precision": precision,
        "ndcg": ndcg,
        "mrr": mrr,
        "rank": rank_found,
    }


def filter_seen_items(
    recommendations: Sequence[int],
    seen_movie_ids: Set[int],
) -> List[int]:
    """
    Lọc bỏ các phim người dùng đã xem trong quá khứ khỏi danh sách ứng viên.
    Bảo toàn nguyên vẹn thứ tự xếp hạng ban đầu.
    """
    return [mid for mid in recommendations if mid not in seen_movie_ids]


def validate_candidate_pool(
    recommendations: Sequence[int],
    seen_movie_ids: Set[int],
    catalog_movie_ids: Optional[Set[int]] = None,
    strict: bool = True,
) -> Dict[str, Any]:
    """
    Kiểm toán tính toàn vẹn của tập ứng viên:
    - Kiểm tra rò rỉ phim đã xem (seen leaks).
    - Kiểm tra phim ngoài danh mục (out of catalog).
    - Kiểm tra phần tử trùng lặp (duplicates).
    """
    seen_leaks = [mid for mid in recommendations if mid in seen_movie_ids]
    out_of_catalog: List[int] = []
    if catalog_movie_ids is not None:
        out_of_catalog = [mid for mid in recommendations if mid not in catalog_movie_ids]

    seen_ids: Set[int] = set()
    duplicates: List[int] = []
    for mid in recommendations:
        if mid in seen_ids:
            duplicates.append(mid)
        seen_ids.add(mid)

    has_violation = bool(seen_leaks or out_of_catalog or duplicates)
    report = {
        "is_valid": not has_violation,
        "seen_leaks": seen_leaks,
        "seen_leaks_count": len(seen_leaks),
        "out_of_catalog": out_of_catalog,
        "out_of_catalog_count": len(out_of_catalog),
        "duplicates": duplicates,
        "duplicates_count": len(duplicates),
    }

    if strict and has_violation:
        msg = f"Candidate pool validation failed: seen_leaks={len(seen_leaks)}, out_of_catalog={len(out_of_catalog)}, duplicates={len(duplicates)}"
        raise ValueError(msg)

    return report


class TopNEvaluator:
    """
    Động cơ đánh giá hệ thống gợi ý Top-N cho MoodGraph.
    
    Các nguyên tắc thiết kế:
    1. Tuân thủ giao thức: Chỉ số chính được đo trên Positive-Target Cohort (rating >= 3.5).
    2. Bảo toàn mẫu số: Người dùng dương không có khuyến nghị được chấm 0.0 và giữ nguyên trong mẫu số.
    3. Chuẩn đoán non-positive: Người dùng có target < 3.5 được theo dõi riêng biệt.
    4. Hỗ trợ đa ngưỡng K: Đánh giá đồng thời nhiều ngưỡng (K = 5, 10, 20).
    5. Độ bao phủ danh mục: Báo cáo tỷ lệ phim được gợi ý trên toàn bộ danh mục và catalog chấm điểm được.
    """

    def __init__(
        self,
        k_list: Sequence[int] = (5, 10, 20),
        relevance_threshold: float = 3.5,
        catalog_size: Optional[int] = None,
        scorable_catalog_size: Optional[int] = None,
    ):
        for k in k_list:
            validate_k(k)
        self.k_list = sorted(list(k_list))
        self.relevance_threshold = float(relevance_threshold)
        self.catalog_size = catalog_size
        self.scorable_catalog_size = scorable_catalog_size

    def evaluate(
        self,
        recommendations: Dict[int, Sequence[int]],
        targets: Dict[int, Union[HeldOutTarget, Tuple[int, float], Dict[str, Any]]],
    ) -> Dict[int, EvaluationSummary]:
        """
        Đánh giá danh sách gợi ý so với tập mục tiêu bị giữ lại (held-out targets).
        
        Args:
            recommendations: Bản đồ userId -> danh sách có thứ tự các movieId được gợi ý.
            targets: Bản đồ userId -> thông tin mục tiêu (HeldOutTarget, tuple hoặc dict).
            
        Returns:
            Bản đồ k -> EvaluationSummary (tổng hợp đầy đủ chỉ số HR, Recall, Precision, NDCG, MRR, Coverage).
        """
        # Normalize targets to HeldOutTarget
        norm_targets: Dict[int, HeldOutTarget] = {}
        for uid, t in targets.items():
            if isinstance(t, HeldOutTarget):
                norm_targets[uid] = t
            elif isinstance(t, (tuple, list)) and len(t) >= 2:
                norm_targets[uid] = HeldOutTarget(movie_id=int(t[0]), rating=float(t[1]))
            elif isinstance(t, dict):
                norm_targets[uid] = HeldOutTarget(
                    movie_id=int(t["movieId"] if "movieId" in t else t["movie_id"]),
                    rating=float(t["rating"]),
                    timestamp=int(t["timestamp"]) if "timestamp" in t else None,
                )
            else:
                raise ValueError(f"Unsupported target format for user {uid}: {t}")

        total_target_users = len(norm_targets)
        positive_users: Dict[int, HeldOutTarget] = {}
        non_positive_users: Dict[int, HeldOutTarget] = {}

        for uid, target in norm_targets.items():
            if target.rating >= self.relevance_threshold:
                positive_users[uid] = target
            else:
                non_positive_users[uid] = target

        pos_cohort_size = len(positive_users)
        non_pos_cohort_size = len(non_positive_users)

        results: Dict[int, EvaluationSummary] = {}

        for k in self.k_list:
            sum_hit = 0.0
            sum_recall = 0.0
            sum_precision = 0.0
            sum_ndcg = 0.0
            sum_mrr = 0.0
            hit_count = 0

            users_with_rec = 0
            users_missing_rec = 0
            unique_recommended_movies: Set[int] = set()

            # Evaluate positive cohort (Primary Evaluation)
            for uid, target in positive_users.items():
                user_rec = recommendations.get(uid, [])
                if len(user_rec) > 0:
                    users_with_rec += 1
                    top_k_items = list(user_rec[:k])
                    unique_recommended_movies.update(top_k_items)
                    m = compute_single_user_metrics(top_k_items, target.movie_id, k)
                else:
                    users_missing_rec += 1
                    m = compute_single_user_metrics([], target.movie_id, k)

                hit = float(m["hit"])
                sum_hit += hit
                sum_recall += float(m["recall"])
                sum_precision += float(m["precision"])
                sum_ndcg += float(m["ndcg"])
                sum_mrr += float(m["mrr"])
                if hit > 0:
                    hit_count += 1

            if pos_cohort_size > 0:
                avg_hit_rate = sum_hit / float(pos_cohort_size)
                avg_recall = sum_recall / float(pos_cohort_size)
                avg_precision = sum_precision / float(pos_cohort_size)
                avg_ndcg = sum_ndcg / float(pos_cohort_size)
                avg_mrr = sum_mrr / float(pos_cohort_size)
            else:
                avg_hit_rate = 0.0
                avg_recall = 0.0
                avg_precision = 0.0
                avg_ndcg = 0.0
                avg_mrr = 0.0

            # Catalog coverage
            num_unique_rec = len(unique_recommended_movies)
            cov_full = (
                num_unique_rec / float(self.catalog_size)
                if self.catalog_size is not None and self.catalog_size > 0
                else None
            )
            cov_scorable = (
                num_unique_rec / float(self.scorable_catalog_size)
                if self.scorable_catalog_size is not None and self.scorable_catalog_size > 0
                else None
            )

            # Diagnostic for all users (if requested)
            diagnostic_all: Optional[Dict[str, float]] = None
            if total_target_users > 0:
                # Under all-users diagnostic, non-positive users get hit=0.0
                diag_hr = sum_hit / float(total_target_users)
                diagnostic_all = {
                    "all_users_hit_rate": diag_hr,
                    "all_users_total_count": total_target_users,
                    "note": "Recall and NDCG are mathematically undefined for users without positive observed targets.",
                }

            results[k] = EvaluationSummary(
                k=k,
                hit_rate=avg_hit_rate,
                recall=avg_recall,
                precision=avg_precision,
                ndcg=avg_ndcg,
                mrr=avg_mrr,
                catalog_coverage_full=cov_full,
                catalog_coverage_scorable=cov_scorable,
                num_unique_recommended_movies=num_unique_rec,
                positive_cohort_size=pos_cohort_size,
                non_positive_cohort_size=non_pos_cohort_size,
                total_target_users=total_target_users,
                users_with_recommendations=users_with_rec,
                users_missing_recommendations=users_missing_rec,
                hit_count=hit_count,
                diagnostic_all_users=diagnostic_all,
            )

        return results
