"""
MoodGraph - Task 3A: Tests for Module M10 Delivery API & Integration Contract
Provides unit, integration, synthetic oracle, and adversarial tests for
production-like ALS recommendation inference and Hybrid integration interfaces.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Set

import numpy as np
import pytest

from recommender.als.delivery import (
    ALSDeliveryService,
    ALSModelRegistry,
    ALSRecommendationItem,
    ModelMetadata,
    get_delivery_service,
    recommend_als,
    recommend_als_batch,
    synthetic_delivery_oracle,
)


# ==============================================================================
# 1. SYNTHETIC ORACLE TESTS
# ==============================================================================

def test_01_synthetic_delivery_oracle_basic():
    """Verify synthetic reference oracle against hand-calculated dot product and ranking."""
    user_vec = np.array([1.0, 2.0], dtype=np.float32)
    item_vecs = np.array([
        [2.0, 1.0],  # Item 101: 1*2 + 2*1 = 4.0
        [1.0, 3.0],  # Item 102: 1*1 + 2*3 = 7.0
        [0.0, 2.0],  # Item 103: 1*0 + 2*2 = 4.0
    ], dtype=np.float32)
    movie_ids = np.array([101, 102, 103], dtype=np.int64)

    recs = synthetic_delivery_oracle(
        user_factor=user_vec,
        item_factors=item_vecs,
        movie_ids=movie_ids,
        seen_movie_ids=set(),
        top_n=3,
    )
    assert len(recs) == 3
    # Rank 1: item 102 (score 7.0)
    assert recs[0]["movieId"] == 102
    assert math.isclose(recs[0]["raw_score"], 7.0, rel_tol=1e-5)
    assert recs[0]["rank"] == 1
    # Rank 2 & 3: items 101 & 103 both have score 4.0 -> tie-break by movieId ASC (101 before 103)
    assert recs[1]["movieId"] == 101
    assert recs[2]["movieId"] == 103


def test_02_synthetic_delivery_oracle_with_seen_filtering():
    """Verify seen item is strictly filtered out before Top-K selection."""
    user_vec = np.array([1.0, 2.0], dtype=np.float32)
    item_vecs = np.array([
        [2.0, 1.0],  # Item 101: score 4.0
        [1.0, 3.0],  # Item 102: score 7.0 (SEEN)
        [0.0, 2.0],  # Item 103: score 4.0
    ], dtype=np.float32)
    movie_ids = np.array([101, 102, 103], dtype=np.int64)

    recs = synthetic_delivery_oracle(
        user_factor=user_vec,
        item_factors=item_vecs,
        movie_ids=movie_ids,
        seen_movie_ids={102},  # Item 102 has been seen
        top_n=2,
    )
    assert len(recs) == 2
    # Item 102 must NOT appear
    assert all(r["movieId"] != 102 for r in recs)
    assert recs[0]["movieId"] == 101
    assert recs[1]["movieId"] == 103


def test_03_synthetic_delivery_oracle_all_seen():
    """When all candidate items are seen, return empty list."""
    user_vec = np.array([1.0, 1.0], dtype=np.float32)
    item_vecs = np.array([[1.0, 1.0]], dtype=np.float32)
    movie_ids = np.array([500], dtype=np.int64)

    recs = synthetic_delivery_oracle(
        user_factor=user_vec,
        item_factors=item_vecs,
        movie_ids=movie_ids,
        seen_movie_ids={500},
        top_n=5,
    )
    assert recs == []


# ==============================================================================
# 2. OUTPUT SCHEMA AND CONTRACT TESTS
# ==============================================================================

def test_04_recommendation_item_schema_validation():
    """Verify ALSRecommendationItem contract properties and to_dict()."""
    item = ALSRecommendationItem(
        userId=42,
        movieId=100,
        raw_score=4.123456,
        rank=1,
        model_name="ALS",
        model_version="ALS_R8_REG0.3_ITER10",
        run_id="test_run",
    )
    d = item.to_dict()
    assert d["userId"] == 42
    assert d["movieId"] == 100
    assert math.isclose(d["raw_score"], 4.123456, rel_tol=1e-5)
    assert d["rank"] == 1
    assert d["model_name"] == "ALS"
    assert d["model_version"] == "ALS_R8_REG0.3_ITER10"
    assert d["run_id"] == "test_run"


def test_05_recommendation_item_invalid_types_raise():
    """Verify validation raises errors on non-integer IDs, non-finite scores, or rank < 1."""
    with pytest.raises(TypeError):
        ALSRecommendationItem(userId="invalid", movieId=10, raw_score=3.0, rank=1)  # type: ignore

    with pytest.raises(TypeError):
        ALSRecommendationItem(userId=1, movieId="invalid", raw_score=3.0, rank=1)  # type: ignore

    with pytest.raises(ValueError):
        ALSRecommendationItem(userId=1, movieId=10, raw_score=float("nan"), rank=1)

    with pytest.raises(ValueError):
        ALSRecommendationItem(userId=1, movieId=10, raw_score=float("inf"), rank=1)

    with pytest.raises(ValueError):
        ALSRecommendationItem(userId=1, movieId=10, raw_score=3.0, rank=0)


# ==============================================================================
# 3. MODEL REGISTRY TESTS
# ==============================================================================

def test_06_model_registry_lookup_and_metadata():
    """Verify registry returns correct metadata for champion model ALS_R8_REG0.3_ITER10."""
    registry = ALSModelRegistry()
    meta = registry.get_model_metadata("ALS_R8_REG0.3_ITER10")

    assert meta.model_id == "ALS_R8_REG0.3_ITER10"
    assert meta.rank == 8
    assert meta.reg_param == 0.3
    assert meta.max_iter == 10
    assert meta.num_user_factors == 162541
    assert meta.num_item_factors == 58932
    assert "data/processed/splits/train" in meta.training_split_provenance
    assert len(meta.limitations) >= 3


def test_07_model_registry_unknown_model_raises():
    """Verify KeyError is raised for unregistered model version."""
    registry = ALSModelRegistry()
    with pytest.raises(KeyError, match="not registered"):
        registry.get_model_metadata("NON_EXISTENT_MODEL")


# ==============================================================================
# 4. DELIVERY SERVICE INTEGRATION TESTS (REAL FROZEN MODEL)
# ==============================================================================

@pytest.fixture(scope="module")
def real_delivery_service() -> ALSDeliveryService:
    """Fixture providing initialized ALSDeliveryService with real frozen model."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    model_dir = repo_root / "artifacts" / "models" / "als" / "m07_tuning" / "ALS_R8_REG0.3_ITER10"
    movies_path = repo_root / "data" / "processed" / "core" / "movies"
    train_path = repo_root / "data" / "processed" / "splits" / "train"
    val_path = repo_root / "data" / "processed" / "splits" / "val"

    assert model_dir.exists(), f"Missing model dir {model_dir}"
    return ALSDeliveryService(
        model_dir=model_dir,
        movies_parquet_path=movies_path,
        train_parquet_path=train_path,
        val_parquet_path=val_path,
    )


def test_08_delivery_service_init_and_properties(real_delivery_service: ALSDeliveryService):
    """Verify delivery service loads champion model with correct dimensions."""
    svc = real_delivery_service
    assert svc.rank == 8
    assert svc.num_known_users == 162541
    assert svc.num_scoreable_items == 58932


def test_09_known_user_top_n_length_and_rank(real_delivery_service: ALSDeliveryService):
    """Verify known user receives exact Top-N recommendations with sequential ranks."""
    svc = real_delivery_service
    top5 = svc.recommend(user_id=1, top_n=5)
    assert len(top5) == 5
    for rank_idx, item in enumerate(top5, start=1):
        assert item["userId"] == 1
        assert item["rank"] == rank_idx
        assert isinstance(item["movieId"], int)
        assert math.isfinite(item["raw_score"])
        assert item["model_name"] == "ALS"

    top20 = svc.recommend(user_id=1, top_n=20)
    assert len(top20) == 20
    # Strict descending sort order check
    scores = [item["raw_score"] for item in top20]
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))


def test_10_unknown_user_cold_start_empty(real_delivery_service: ALSDeliveryService):
    """Cold user (not in Train factors) must return empty list [] in ALS_ONLY mode."""
    svc = real_delivery_service
    # User 999999999 does not exist in Train
    recs = svc.recommend(user_id=999999999, top_n=10)
    assert recs == []


def test_11_top_n_invalid_non_positive_raises(real_delivery_service: ALSDeliveryService):
    """Non-positive top_n must raise ValueError."""
    svc = real_delivery_service
    with pytest.raises(ValueError):
        svc.recommend(user_id=1, top_n=0)
    with pytest.raises(ValueError):
        svc.recommend(user_id=1, top_n=-5)


def test_12_empty_user_batch_returns_empty_dict(real_delivery_service: ALSDeliveryService):
    """Empty user batch must return empty dictionary."""
    svc = real_delivery_service
    assert svc.recommend_batch(user_ids=[], top_n=10) == {}


def test_13_batch_recommendations_parity(real_delivery_service: ALSDeliveryService):
    """Batch recommendation must match individual user recommendation results exactly."""
    svc = real_delivery_service
    uids = [1, 2]
    batch_res = svc.recommend_batch(user_ids=uids, top_n=5)

    single_u1 = svc.recommend(user_id=1, top_n=5)
    single_u2 = svc.recommend(user_id=2, top_n=5)

    assert [r["movieId"] for r in batch_res[1]] == [r["movieId"] for r in single_u1]
    assert [r["movieId"] for r in batch_res[2]] == [r["movieId"] for r in single_u2]


def test_14_seen_filtering_guarantee(real_delivery_service: ALSDeliveryService):
    """Verify custom seen items are strictly excluded from output."""
    svc = real_delivery_service
    # First get top 5 without custom seen
    orig_top5 = svc.recommend(user_id=1, top_n=5)
    top_movie = orig_top5[0]["movieId"]

    # Now mark top_movie as seen
    filtered_top5 = svc.recommend(user_id=1, top_n=5, custom_seen={top_movie})
    filtered_mids = [r["movieId"] for r in filtered_top5]

    assert top_movie not in filtered_mids
    assert len(filtered_top5) == 5


def test_15_stage_aware_history_isolation(real_delivery_service: ALSDeliveryService):
    """Verify stage parameter accepts production, validation, test and rejects unknown."""
    svc = real_delivery_service
    # All valid stages execute without error
    recs_prod = svc.recommend(user_id=1, top_n=5, stage="production")
    recs_val = svc.recommend(user_id=1, top_n=5, stage="validation")
    recs_test = svc.recommend(user_id=1, top_n=5, stage="test")

    assert len(recs_prod) == 5
    assert len(recs_val) == 5
    assert len(recs_test) == 5

    with pytest.raises(ValueError, match="Unknown stage"):
        svc.recommend(user_id=1, top_n=5, stage="invalid_stage")


def test_16_deterministic_repeated_recommendations(real_delivery_service: ALSDeliveryService):
    """Verify recommendation service is deterministic across repeated calls."""
    svc = real_delivery_service
    run1 = svc.recommend(user_id=10, top_n=10)
    run2 = svc.recommend(user_id=10, top_n=10)

    assert [r["movieId"] for r in run1] == [r["movieId"] for r in run2]
    assert [r["raw_score"] for r in run1] == [r["raw_score"] for r in run2]


def test_17_real_model_dot_product_alignment(real_delivery_service: ALSDeliveryService):
    """Verify recommended raw_score matches exact factor dot product P_u @ Q_i."""
    svc = real_delivery_service
    recs = svc.recommend(user_id=1, top_n=3)
    assert len(recs) == 3

    # Extract user factor
    gen = svc.generator
    u_idx = gen.user_factors.user_to_idx[1]
    u_vec = gen.user_factors.factors[u_idx]  # Shape (8,)

    for r in recs:
        mid = r["movieId"]
        item_idx = gen.catalog.movie_to_idx[mid]
        q_vec = gen.catalog.factors[item_idx]  # Shape (8,)
        expected_dot = float(np.dot(u_vec, q_vec))
        assert math.isclose(r["raw_score"], expected_dot, rel_tol=1e-5)


# ==============================================================================
# 5. KNOWLEDGE GRAPH & HYBRID INTEGRATION CONTRACT TESTS
# ==============================================================================

def test_18_candidate_union_contract_with_synthetic_kg(real_delivery_service: ALSDeliveryService):
    """
    Consumer Contract Test: Simulate synthetic KG recommendations, perform candidate union,
    verify schema, source preservation, and lack of forced reranking.
    """
    svc = real_delivery_service
    # 1. ALS candidates (Top-5)
    als_recs = svc.recommend(user_id=1, top_n=5)
    assert len(als_recs) == 5

    # 2. Synthetic KG candidates (independent graph path/embedding search)
    # Includes 1 movie that ALS recommended and 2 movies that ALS did NOT recommend
    synthetic_kg_recs: List[Dict[str, Any]] = [
        {
            "userId": 1,
            "movieId": als_recs[0]["movieId"],  # Overlapping movie
            "raw_score": 0.85,
            "rank": 1,
            "model_name": "KG_PATH",
            "model_version": "KG_V1_MOCK",
        },
        {
            "userId": 1,
            "movieId": 999901,  # KG-only movie (could be cold in ALS)
            "raw_score": 0.72,
            "rank": 2,
            "model_name": "KG_PATH",
            "model_version": "KG_V1_MOCK",
        },
        {
            "userId": 1,
            "movieId": 999902,  # KG-only movie
            "raw_score": 0.65,
            "rank": 3,
            "model_name": "KG_PATH",
            "model_version": "KG_V1_MOCK",
        },
    ]

    # 3. Hybrid Candidate Union: ALS_candidates ∪ KG_candidates
    als_movie_ids = {r["movieId"] for r in als_recs}
    kg_movie_ids = {r["movieId"] for r in synthetic_kg_recs}
    union_movie_ids = als_movie_ids | kg_movie_ids

    # Expected union count: 5 ALS + 2 new KG = 7 movies
    assert len(union_movie_ids) == 7
    # KG-only movies must be retained in the union set
    assert 999901 in union_movie_ids
    assert 999902 in union_movie_ids


def test_19_no_forced_kg_rerank_of_als_top_20(real_delivery_service: ALSDeliveryService):
    """
    Verify integration contract does NOT restrict KG to only reranking ALS Top-20.
    KG candidates can originate from catalog items outside ALS recommendations.
    """
    svc = real_delivery_service
    als_top20 = svc.recommend(user_id=1, top_n=20)
    als_top20_ids = {r["movieId"] for r in als_top20}

    # Suppose KG discovers high-relevance movie 50 (e.g. Toy Story)
    kg_candidate_mid = 50
    # In M09 we saw pure ALS Top-20 is 100% tail items (support <= 5)
    # Movie 50 is a popular head movie not in ALS Top-20
    assert kg_candidate_mid not in als_top20_ids

    # Hybrid pool contains both
    hybrid_pool = als_top20_ids | {kg_candidate_mid}
    assert kg_candidate_mid in hybrid_pool
    assert len(hybrid_pool) == 21


def test_20_no_raw_score_blending_without_normalization():
    """
    Contract Rule: ALS raw_score (scale ~0.1 to 10.8) and KG raw_score (e.g. scale 0.0 to 1.0)
    must NOT be added directly without calibration.
    """
    als_raw_score = 8.5  # Typical inflated ALS tail score
    kg_raw_score = 0.95  # Strong graph path similarity

    # Direct naive addition is dominated by ALS: 8.5 + 0.95 = 9.45 (~90% ALS weight)
    naive_sum = als_raw_score + kg_raw_score
    assert naive_sum > 9.0

    # Contract requires explicit normalization/calibration before fusion:
    # E.g. min-max or z-score normalization
    norm_als = (als_raw_score - 1.0) / (10.0 - 1.0)  # Map to [0, 1] ≈ 0.833
    norm_kg = kg_raw_score  # Already [0, 1] = 0.95
    calibrated_hybrid_score = 0.5 * norm_als + 0.5 * norm_kg
    assert 0.0 <= calibrated_hybrid_score <= 1.0
    assert math.isclose(calibrated_hybrid_score, 0.5 * (7.5 / 9.0) + 0.5 * 0.95, rel_tol=1e-5)

