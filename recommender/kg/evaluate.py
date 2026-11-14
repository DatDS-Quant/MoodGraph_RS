"""
Hệ thống đánh giá Offline trên tập Validation (Gate 4 Evaluation & Ablation Study).
Tuyệt đối tuân thủ giao thức User-wise Leave-1-Last trong docs/evaluation_protocol.md:
- Candidate Pool = Catalog \\ (Train_u U Val_u)
- Positive threshold: rating >= 3.5
- Đo lường HR@K, NDCG@K, MRR@K, Catalog Coverage@K tại K in {5, 10, 20}
- Ablation study so sánh 3 cấu hình:
    1. Genre-only (P1)
    2. Genre + Genome (P1 + P2)
    3. Full Path-based (P1 + P2 + P3)
"""

import math
import time
from typing import Dict, Any, List, Set, Tuple, Optional
from pathlib import Path
import pyarrow.dataset as ds

from recommender.kg.config import load_kg_config, KGConfig
from recommender.kg.recommend import recommend_kg


def compute_ndcg_at_k(target_movie_id: int, rec_movie_ids: List[int], k: int) -> float:
    """Tính NDCG@K cho 1 target item."""
    top_k = rec_movie_ids[:k]
    if target_movie_id in top_k:
        rank = top_k.index(target_movie_id) + 1  # Thứ hạng bắt đầu từ 1 (1-based rank)
        dcg = 1.0 / math.log2(rank + 1)
        idcg = 1.0  # Chỉ có 1 ground-truth positive item
        return dcg / idcg
    return 0.0


def compute_hr_at_k(target_movie_id: int, rec_movie_ids: List[int], k: int) -> float:
    """Tính Hit Rate (HR@K)."""
    return 1.0 if target_movie_id in rec_movie_ids[:k] else 0.0


def compute_mrr_at_k(target_movie_id: int, rec_movie_ids: List[int], k: int) -> float:
    """Tính MRR@K."""
    top_k = rec_movie_ids[:k]
    if target_movie_id in top_k:
        rank = top_k.index(target_movie_id) + 1
        return 1.0 / rank
    return 0.0


class ValidationEvaluator:
    """Bộ đánh giá hiệu năng offline trên tập dữ liệu Validation cho hệ gợi ý Knowledge Graph."""
    def __init__(self, data_root: Path, positive_threshold: float = 3.5):
        self.data_root = Path(data_root)
        self.positive_threshold = positive_threshold
        self.val_data: Dict[int, Dict[str, Any]] = {}  # userId -> {movieId, rating}

    def load_validation_cohort(self, user_cohort: Optional[Set[int]] = None):
        """Đọc splits/validation cho tập user_cohort."""
        val_path = self.data_root / "splits/validation"
        dataset = ds.dataset(str(val_path), format="parquet")
        filter_expr = ds.field("userId").isin(list(user_cohort)) if user_cohort else None

        scanner = dataset.scanner(
            columns=["userId", "movieId", "rating"],
            filter=filter_expr
        )
        for batch in scanner.to_batches():
            pydict = batch.to_pydict()
            for i in range(batch.num_rows):
                uid = int(pydict["userId"][i])
                mid = int(pydict["movieId"][i])
                r = float(pydict["rating"][i])
                self.val_data[uid] = {"movieId": mid, "rating": r}

    def evaluate_configuration(
        self,
        graph: Any,
        user_cohort: List[int],
        config_name: str,
        enable_p1: bool = True,
        enable_p2: bool = True,
        enable_p3: bool = True,
        top_k_list: List[int] = [5, 10, 20]
    ) -> Dict[str, Any]:
        """Đánh giá một cấu hình cụ thể trên tập user cohort."""
        positive_cohort = [
            uid for uid in user_cohort
            if uid in self.val_data and self.val_data[uid]["rating"] >= self.positive_threshold
        ]

        total_users = len(user_cohort)
        positive_denom = len(positive_cohort)

        hits = {k: 0.0 for k in top_k_list}
        ndcgs = {k: 0.0 for k in top_k_list}
        mrrs = {k: 0.0 for k in top_k_list}
        recommended_catalog_items: Set[int] = set()
        scoreable_count = 0

        t0 = time.time()
        for uid in positive_cohort:
            target_mid = self.val_data[uid]["movieId"]
            # Phim đã xem trong Train đã được đồ thị tự động loại trừ bên trong recommend_kg().
            # Phim target_mid trong Validation là mục tiêu ground-truth để xếp hạng đánh giá,
            # TUYỆT ĐỐI KHÔNG loại trừ target_mid khỏi candidate pool.
            recs = recommend_kg(
                user_id=uid,
                top_n=max(top_k_list),
                exclude_movie_ids=None,
                graph=graph,
                enable_p1=enable_p1,
                enable_p2=enable_p2,
                enable_p3=enable_p3
            )

            if recs:
                scoreable_count += 1
                rec_ids = [r["movieId"] for r in recs]
                # Cập nhật catalog coverage (tại Top-10)
                recommended_catalog_items.update(rec_ids[:10])

                for k in top_k_list:
                    hits[k] += compute_hr_at_k(target_mid, rec_ids, k)
                    ndcgs[k] += compute_ndcg_at_k(target_mid, rec_ids, k)
                    mrrs[k] += compute_mrr_at_k(target_mid, rec_ids, k)

        eval_duration = time.time() - t0

        results = {
            "config_name": config_name,
            "total_evaluated_users": total_users,
            "positive_cohort_denominator": positive_denom,
            "scoreable_users": scoreable_count,
            "score_availability": scoreable_count / positive_denom if positive_denom > 0 else 0.0,
            "duration_seconds": round(eval_duration, 2),
            "metrics": {}
        }

        for k in top_k_list:
            results["metrics"][f"HR@{k}"] = round(hits[k] / positive_denom if positive_denom > 0 else 0.0, 4)
            results["metrics"][f"NDCG@{k}"] = round(ndcgs[k] / positive_denom if positive_denom > 0 else 0.0, 4)
            results["metrics"][f"MRR@{k}"] = round(mrrs[k] / positive_denom if positive_denom > 0 else 0.0, 4)

        results["metrics"]["Catalog_Coverage@10"] = len(recommended_catalog_items)

        return results

