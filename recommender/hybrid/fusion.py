"""
Mô-đun các thuật toán dung hợp (Fusion Algorithms) cho Hybrid Recommender (Phase 4).

Hiện thực:
1. Reciprocal Rank Fusion (RRF):
   - Không phụ thuộc vào thang đo điểm số gốc (scale-invariant).
   - RRF_score(m) = sum_{source} 1 / (k + rank_source(m)).
   - Chuẩn tie-breaking: sắp xếp theo điểm dung hợp giảm dần, ID phim tăng dần.

2. Weighted Score Fusion:
   - Chuẩn hóa điểm số (Min-Max scaling hoặc Percentile Rank).
   - Weighted_score(m) = w_ALS * norm_ALS(m) + w_KG * norm_KG(m).
   - Cơ chế nội suy (imputation) cho ứng viên chỉ xuất hiện ở một bên.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple


def normalize_min_max(
    scores: Sequence[float],
    constant_value: float = 1.0,
) -> List[float]:
    """
    Chuẩn hóa Min-Max tuyến tính về khoảng [0.0, 1.0].
    Xử lý trường hợp biên: danh sách rỗng, đơn phần tử hoặc max == min.
    """
    if not scores:
        return []
    clean = [0.0 if not math.isfinite(s) else float(s) for s in scores]
    min_v = min(clean)
    max_v = max(clean)
    diff = max_v - min_v
    if diff < 1e-12:
        return [constant_value if max_v > 0 else 0.0 for _ in clean]
    return [(s - min_v) / diff for s in clean]


def normalize_percentile(
    scores: Sequence[float],
) -> List[float]:
    """
    Chuẩn hóa thứ hạng theo phân vị (Percentile Rank) về khoảng (0.0, 1.0].
    """
    if not scores:
        return []
    n = len(scores)
    # Sắp xếp các chỉ số theo điểm số tăng dần
    indexed = sorted(enumerate(scores), key=lambda x: (x[1], -x[0]))
    ranks = [0.0] * n
    for rank_idx, (orig_idx, _) in enumerate(indexed, start=1):
        ranks[orig_idx] = rank_idx / float(n)
    return ranks


def reciprocal_rank_fusion(
    candidates_als: Sequence[Dict[str, Any]],
    candidates_kg: Sequence[Dict[str, Any]],
    rrf_k: int = 60,
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Dung hợp danh sách ứng viên từ ALS và KG theo giải thuật Reciprocal Rank Fusion (RRF).

    Công thức:
        RRF_score(m) = sum_{s in {ALS, KG}} (1.0 / (k + rank_s(m))) nếu m in candidates_s else 0.0

    Tie-breaking:
        1. RRF score giảm dần
        2. movieId tăng dần
    """
    if rrf_k <= 0:
        raise ValueError(f"rrf_k must be > 0, got {rrf_k}")

    # Ánh xạ theo movieId
    als_map: Dict[int, Dict[str, Any]] = {int(c["movieId"]): c for c in candidates_als}
    kg_map: Dict[int, Dict[str, Any]] = {int(c["movieId"]): c for c in candidates_kg}

    all_mids = set(als_map.keys()) | set(kg_map.keys())
    if not all_mids:
        return []

    fused_items: List[Dict[str, Any]] = []

    for mid in all_mids:
        als_item = als_map.get(mid)
        kg_item = kg_map.get(mid)

        als_rank: Optional[int] = int(als_item["rank"]) if als_item and "rank" in als_item else None
        kg_rank: Optional[int] = int(kg_item["rank"]) if kg_item and "rank" in kg_item else None

        score = 0.0
        if als_rank is not None:
            score += 1.0 / (rrf_k + als_rank)
        if kg_rank is not None:
            score += 1.0 / (rrf_k + kg_rank)

        if als_item is not None and kg_item is not None:
            source = "BOTH"
        elif als_item is not None:
            source = "ALS"
        else:
            source = "KG"

        title = None
        if kg_item and kg_item.get("title"):
            title = kg_item["title"]
        elif als_item and als_item.get("title"):
            title = als_item["title"]

        evidence = []
        if kg_item and kg_item.get("evidence"):
            evidence.extend(kg_item["evidence"])
        if als_item is not None:
            # Ghi nhận bằng chứng ALS tương hỗ
            evidence.append({
                "path_type": "ALS_LATENT_FACTOR",
                "model_version": als_item.get("model_version", "ALS_R8_REG0.3_ITER10"),
                "raw_score": float(als_item["raw_score"]) if "raw_score" in als_item else None,
                "als_rank": als_rank,
                "description": "High collaborative affinity in latent matrix factorization space",
            })

        fused_items.append({
            "movieId": mid,
            "title": title,
            "hybrid_score": score,
            "source": source,
            "fusion_method": "rrf",
            "als_raw_score": float(als_item["raw_score"]) if als_item and "raw_score" in als_item else None,
            "als_normalized_score": (1.0 / (rrf_k + als_rank)) if als_rank is not None else 0.0,
            "als_rank": als_rank,
            "kg_raw_score": float(kg_item["raw_score"]) if kg_item and "raw_score" in kg_item else None,
            "kg_normalized_score": (1.0 / (rrf_k + kg_rank)) if kg_rank is not None else 0.0,
            "kg_rank": kg_rank,
            "evidence": evidence,
        })

    # Tie-breaking nghiêm ngặt: hybrid_score giảm dần, movieId tăng dần
    fused_items.sort(key=lambda x: (-x["hybrid_score"], x["movieId"]))

    # Gán thứ hạng cuối cùng
    for rank_idx, item in enumerate(fused_items, start=1):
        item["rank"] = rank_idx

    if top_n is not None and top_n > 0:
        return fused_items[:top_n]
    return fused_items


def weighted_score_fusion(
    candidates_als: Sequence[Dict[str, Any]],
    candidates_kg: Sequence[Dict[str, Any]],
    weight_als: float = 0.5,
    weight_kg: float = 0.5,
    normalize_method: str = "min_max",
    imputation_strategy: str = "zero",
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Dung hợp danh sách ứng viên từ ALS và KG theo giải thuật kết hợp điểm số có trọng số.

    Các bước:
    1. Chuẩn hóa thang đo điểm của từng nguồn độc lập (Min-Max hoặc Percentile).
    2. Nội suy điểm số cho các ứng viên không thuộc tập giao (imputation: zero hoặc min).
    3. Weighted_score(m) = weight_als * norm_als(m) + weight_kg * norm_kg(m).
    4. Deterministic sort (-score, mid) và gán hạng.
    """
    if weight_als < 0 or weight_kg < 0:
        raise ValueError(f"Trọng số không được âm: weight_als={weight_als}, weight_kg={weight_kg}")
    total_w = weight_als + weight_kg
    if total_w <= 0:
        raise ValueError("Tổng trọng số phải lớn hơn 0")
    w_als = weight_als / total_w
    w_kg = weight_kg / total_w

    als_map: Dict[int, Dict[str, Any]] = {int(c["movieId"]): c for c in candidates_als}
    kg_map: Dict[int, Dict[str, Any]] = {int(c["movieId"]): c for c in candidates_kg}

    all_mids = set(als_map.keys()) | set(kg_map.keys())
    if not all_mids:
        return []

    # 1. Chuẩn hóa điểm ALS
    als_mids_ordered = list(als_map.keys())
    als_raw_scores = [float(als_map[mid].get("raw_score", 0.0)) for mid in als_mids_ordered]
    if normalize_method == "percentile":
        als_norm_list = normalize_percentile(als_raw_scores)
    else:
        als_norm_list = normalize_min_max(als_raw_scores)
    als_norm_map: Dict[int, float] = {mid: s for mid, s in zip(als_mids_ordered, als_norm_list)}

    # 2. Chuẩn hóa điểm KG
    kg_mids_ordered = list(kg_map.keys())
    kg_raw_scores = [float(kg_map[mid].get("raw_score", 0.0)) for mid in kg_mids_ordered]
    if normalize_method == "percentile":
        kg_norm_list = normalize_percentile(kg_raw_scores)
    else:
        kg_norm_list = normalize_min_max(kg_raw_scores)
    kg_norm_map: Dict[int, float] = {mid: s for mid, s in zip(kg_mids_ordered, kg_norm_list)}

    # Xác định giá trị nội suy theo chiến lược
    strat = (imputation_strategy or "zero").lower()
    if strat == "neutral":
        impute_als = 0.5
        impute_kg = 0.5
    elif strat == "min":
        impute_als = min(als_norm_list) if als_norm_list else 0.0
        impute_kg = min(kg_norm_list) if kg_norm_list else 0.0
    elif strat == "source_aware":
        # Với ALS: Top-K truncation -> giá trị tiệm cận đáy danh sách
        impute_als = max(0.0, min(als_norm_list) * 0.5) if als_norm_list else 0.0
        # Với KG: không có đường đi liên kết -> điểm thực chất bằng 0.0
        impute_kg = 0.0
    else:  # "zero" (mặc định)
        impute_als = 0.0
        impute_kg = 0.0

    fused_items: List[Dict[str, Any]] = []

    for mid in all_mids:
        als_item = als_map.get(mid)
        kg_item = kg_map.get(mid)

        norm_als = als_norm_map.get(mid, impute_als)
        norm_kg = kg_norm_map.get(mid, impute_kg)

        score = w_als * norm_als + w_kg * norm_kg

        if als_item is not None and kg_item is not None:
            source = "BOTH"
        elif als_item is not None:
            source = "ALS"
        else:
            source = "KG"

        title = None
        if kg_item and kg_item.get("title"):
            title = kg_item["title"]
        elif als_item and als_item.get("title"):
            title = als_item["title"]

        evidence = []
        if kg_item and kg_item.get("evidence"):
            evidence.extend(kg_item["evidence"])
        als_rank_val = int(als_item["rank"]) if (als_item and als_item.get("rank") is not None) else None
        kg_rank_val = int(kg_item["rank"]) if (kg_item and kg_item.get("rank") is not None) else None

        if als_item is not None:
            evidence.append({
                "path_type": "ALS_LATENT_FACTOR",
                "model_version": als_item.get("model_version", "ALS_R8_REG0.3_ITER10"),
                "raw_score": float(als_item["raw_score"]) if "raw_score" in als_item else None,
                "als_rank": als_rank_val,
                "description": "High collaborative affinity in latent matrix factorization space",
            })

        fused_items.append({
            "movieId": mid,
            "title": title,
            "hybrid_score": score,
            "source": source,
            "fusion_method": "weighted",
            "als_raw_score": float(als_item["raw_score"]) if als_item and "raw_score" in als_item else None,
            "als_normalized_score": norm_als if als_item is not None else None,
            "als_rank": als_rank_val,
            "kg_raw_score": float(kg_item["raw_score"]) if kg_item and "raw_score" in kg_item else None,
            "kg_normalized_score": norm_kg if kg_item is not None else None,
            "kg_rank": kg_rank_val,
            "evidence": evidence,
        })

    fused_items.sort(key=lambda x: (-x["hybrid_score"], x["movieId"]))

    for rank_idx, item in enumerate(fused_items, start=1):
        item["rank"] = rank_idx

    if top_n is not None and top_n > 0:
        return fused_items[:top_n]
    return fused_items

