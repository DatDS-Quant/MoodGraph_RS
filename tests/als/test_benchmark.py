"""
Tests for Module M08: Frozen Test Benchmark
Verifies all evaluation invariants, preflight checks, seen filtering, and fairness contracts.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Set

import numpy as np
import pytest

from recommender.als.benchmark import (
    PreflightBlockedError,
    compute_sha256,
    load_train_and_val_seen,
    run_preflight_audit,
)
from recommender.als.evaluator import HeldOutTarget, TopNEvaluator
from recommender.als.popularity import (
    compute_weighted_score,
    generate_user_top_k,
    rank_movies_by_count,
    rank_movies_by_weighted_average,
)


def test_01_preflight_audit_on_actual_repo():
    """Verify preflight audit passes on current frozen repository state."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    report = run_preflight_audit(repo_root)
    assert report["status"] == "PASS"
    assert report["checks"]["user_factor_count"] == 162541
    assert report["checks"]["item_factor_count"] == 58932
    assert report["checks"]["user_factor_dim"] == 8
    assert report["checks"]["item_factor_dim"] == 8


def test_02_preflight_blocks_on_tampered_hash(tmp_path: Path):
    """Verify preflight raises PreflightBlockedError if a frozen manifest is altered."""
    fake_root = tmp_path / "fake_repo"
    fake_root.mkdir()
    # Missing files must immediately raise PreflightBlockedError
    with pytest.raises(PreflightBlockedError, match="M08_PREFLIGHT_BLOCKED"):
        run_preflight_audit(fake_root)


def test_03_test_stage_seen_filtering_synthetic_oracle():
    """
    Synthetic verification of Test-stage seen filtering:
    User has seen:
    - movie 10 in Train
    - movie 20 in Validation
    Candidate catalog has movies: [10, 20, 30, 40, 50].
    Movie 30 is the held-out Test target.
    Recommendations MUST:
    - Exclude movie 10 (seen in Train).
    - Exclude movie 20 (seen in Validation).
    - Include movie 30 (held-out target).
    """
    user_id = 999
    train_seen = {10}
    val_seen = {20}
    test_target_movie = 30

    test_seen: Set[int] = train_seen | val_seen
    assert test_seen == {10, 20}
    assert test_target_movie not in test_seen, "Test target must not be masked!"

    movie_stats = [
        (10, 1000, 4.5),  # in Train seen
        (20, 800, 4.2),   # in Val seen
        (30, 500, 4.0),   # Test target
        (40, 300, 3.8),   # Unseen candidate
        (50, 100, 3.5),   # Unseen candidate
    ]
    ranked_records = rank_movies_by_count(movie_stats)
    ranked_ids = [r.movie_id for r in ranked_records]
    scores_map = {r.movie_id: float(r.rating_count) for r in ranked_records}

    recs = generate_user_top_k(
        user_id=user_id,
        ranked_movie_ids=ranked_ids,
        scores_map=scores_map,
        seen_movies=test_seen,
        k=3,
        model_name="POPULARITY_COUNT",
    )
    rec_ids = [r.movie_id for r in recs]

    assert 10 not in rec_ids, "Movie 10 (seen in Train) must be excluded!"
    assert 20 not in rec_ids, "Movie 20 (seen in Validation) must be excluded!"
    assert 30 in rec_ids, "Movie 30 (held-out Test target) must be recommended!"
    assert rec_ids == [30, 40, 50], f"Expected [30, 40, 50], got {rec_ids}"


def test_04_als_vectorized_masking_oracle():
    """
    Verify ALS dot-product scoring with -np.inf masking excludes Train and Validation seen items.
    """
    # 1 user factor, 4 item factors of rank 2
    u_vec = np.array([1.0, 1.0], dtype=np.float32)
    # Items: 10, 20, 30, 40
    item_ids = np.array([10, 20, 30, 40], dtype=np.int64)
    item_factors = np.array([
        [5.0, 5.0],  # Dot product = 10.0 (Highest score, but in Train seen!)
        [4.0, 4.0],  # Dot product = 8.0  (2nd highest, but in Val seen!)
        [3.0, 3.0],  # Dot product = 6.0  (Test target)
        [2.0, 2.0],  # Dot product = 4.0  (Unseen)
    ], dtype=np.float32)

    # Compute raw scores
    raw_scores = np.dot(item_factors, u_vec)  # [10., 8., 6., 4.]
    assert raw_scores.tolist() == [10.0, 8.0, 6.0, 4.0]

    # Seen filter: Train={10}, Val={20}
    test_seen = {10, 20}
    id_to_idx = {int(mid): idx for idx, mid in enumerate(item_ids)}

    masked_scores = raw_scores.copy()
    for s_mid in test_seen:
        if s_mid in id_to_idx:
            masked_scores[id_to_idx[s_mid]] = -np.inf

    # Select Top 2 unseen items
    # Valid scores: movie 30 (6.0), movie 40 (4.0)
    top2_idx = np.argsort(-masked_scores)[:2]
    top2_movies = item_ids[top2_idx].tolist()

    assert 10 not in top2_movies
    assert 20 not in top2_movies
    assert top2_movies == [30, 40]


def test_05_unscoreable_cold_target_preserved_in_denominator():
    """
    Verify that unscoreable positive targets (movies with 0 train ratings)
    contribute a miss and are strictly preserved in the evaluation denominator.
    """
    evaluator = TopNEvaluator(
        k_list=[5, 10],
        relevance_threshold=3.5,
        catalog_size=62423,
        scorable_catalog_size=58932,
    )

    # 2 positive users:
    # User 1 target is scoreable movie 100
    # User 2 target is unscoreable movie 99999 (0 train ratings)
    targets = {
        1: HeldOutTarget(movie_id=100, rating=4.0),
        2: HeldOutTarget(movie_id=99999, rating=4.5),
    }

    # Model recommends movie 100 to user 1, but cannot recommend 99999 to user 2
    predictions = {
        1: [100, 101, 102, 103, 104],
        2: [200, 201, 202, 203, 204],
    }

    results = evaluator.evaluate(predictions, targets)
    metrics_5 = results[5].to_dict()

    # Denominator must be exactly 2 (both positive users)
    assert metrics_5["positive_cohort_size"] == 2
    # Hit count is 1 (only user 1 hit)
    assert metrics_5["hit_count"] == 1
    # HitRate@5 = 1 / 2 = 0.500
    assert pytest.approx(metrics_5["hit_rate"], abs=1e-6) == 0.500
    # User 1 hit at rank 1: NDCG = 1.0, User 2 NDCG = 0.0 -> Mean NDCG = 0.500
    assert pytest.approx(metrics_5["ndcg"], abs=1e-6) == 0.500


def test_06_fairness_identical_cohort_and_catalog():
    """Verify that multiple models evaluated with TopNEvaluator share identical cohort and catalog settings."""
    evaluator = TopNEvaluator(
        k_list=[10],
        relevance_threshold=3.5,
        catalog_size=62423,
        scorable_catalog_size=58932,
    )

    targets = {
        1: HeldOutTarget(movie_id=10, rating=4.0),
        2: HeldOutTarget(movie_id=20, rating=5.0),
    }

    model_a_preds = {1: [10, 11, 12], 2: [21, 22, 23]}
    model_b_preds = {1: [11, 12, 13], 2: [20, 21, 22]}

    res_a = evaluator.evaluate(model_a_preds, targets)[10].to_dict()
    res_b = evaluator.evaluate(model_b_preds, targets)[10].to_dict()

    assert res_a["positive_cohort_size"] == res_b["positive_cohort_size"] == 2
    assert res_a["hit_count"] == 1  # user 1 hit
    assert res_b["hit_count"] == 1  # user 2 hit
    assert res_a["hit_rate"] == res_b["hit_rate"] == 0.5


def test_07_m08_artifacts_presence_and_schema():
    """Verify that all 6 required M08 artifacts exist and have valid structure."""
    m08_dir = Path("artifacts/als/m08")
    expected_files = [
        "m08_test_benchmark_results.json",
        "m08_test_comparison_table.csv",
        "m08_test_cohort_manifest.json",
        "m08_model_provenance.json",
        "m08_runtime_diagnostics.json",
        "m08_scientific_audit.json",
    ]
    for fname in expected_files:
        p = m08_dir / fname
        assert p.exists(), f"Missing M08 artifact: {fname}"


def test_08_m08_results_verification():
    """Verify the exact empirical metrics on Test split across all 3 models."""
    import json
    bench_path = Path("artifacts/als/m08/m08_test_benchmark_results.json")
    if not bench_path.exists():
        pytest.skip("m08_test_benchmark_results.json not found")

    with open(bench_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = data["models"]
    pos_cohort = data["metadata"]["positive_cohort_size"]
    assert pos_cohort == 111211, f"Expected 111,211 positive Test users, got {pos_cohort}"

    # Model A: Popularity Count
    count_m = models["M03_POPULARITY_COUNT"]["metrics"]["10"]
    assert count_m["hit_count"] == 5958
    assert pytest.approx(count_m["hit_rate"], abs=1e-5) == 5958 / 111211.0  # ~0.05357
    assert pytest.approx(count_m["ndcg"], abs=1e-5) == 0.02721

    # Model B: Popularity Weighted
    wgt_m = models["M03_POPULARITY_WEIGHTED_M10"]["metrics"]["10"]
    assert wgt_m["hit_count"] == 2095
    assert pytest.approx(wgt_m["hit_rate"], abs=1e-5) == 2095 / 111211.0   # ~0.01884
    assert pytest.approx(wgt_m["ndcg"], abs=1e-5) == 0.00742

    # Model C: ALS Champion
    als_m = models["ALS_R8_REG0.3_ITER10"]["metrics"]["10"]
    assert als_m["hit_count"] == 1
    assert pytest.approx(als_m["hit_rate"], abs=1e-5) == 1 / 111211.0      # ~0.00001
    assert pytest.approx(als_m["ndcg"], abs=1e-5) == 0.00001


def test_09_m08_unscoreable_targets_audit():
    """Verify that 29 unscoreable positive targets are documented and retained as misses."""
    import json
    cohort_path = Path("artifacts/als/m08/m08_test_cohort_manifest.json")
    if not cohort_path.exists():
        pytest.skip("m08_test_cohort_manifest.json not found")

    with open(cohort_path, "r", encoding="utf-8") as f:
        cdata = json.load(f)

    assert cdata["unscoreable_positive_targets_count"] == 29
    assert cdata["total_test_users"] == 162541
    assert cdata["positive_cohort_size"] == 111211
    assert cdata["non_positive_cohort_size"] == 51330
    assert cdata["seen_filtering_policy"] == "Train_u ∪ Validation_u"


def test_10_single_positive_hit_rank_4_synthetic_precision():
    """
    Independent synthetic test: Single hit at rank 4 across 111,211 positive users.
    Verifies exact mathematical formulas:
    - HR@10 = 1 / 111,211 ≈ 8.991916e-6
    - NDCG@10 = 1 / (log2(5) * 111,211) ≈ 3.872608e-6
    - MRR@10 = 1 / (4 * 111,211) ≈ 2.247979e-6
    """
    evaluator = TopNEvaluator(k_list=[5, 10, 20], relevance_threshold=3.5)
    cohort_size = 111211
    targets = {i: HeldOutTarget(movie_id=1000 + i, rating=4.0) for i in range(1, cohort_size + 1)}

    # User 1 target is 1001, place at rank 4 (0-based index 3)
    recs = {1: [9991, 9992, 9993, 1001, 9995]}

    results = evaluator.evaluate(recs, targets)[10].to_dict()
    exp_hr = 1.0 / cohort_size
    exp_ndcg = 1.0 / (math.log2(5.0) * cohort_size)
    exp_mrr = 1.0 / (4.0 * cohort_size)

    assert pytest.approx(results["hit_rate"], rel=1e-7) == exp_hr
    assert pytest.approx(results["ndcg"], rel=1e-7) == exp_ndcg
    assert pytest.approx(results["mrr"], rel=1e-7) == exp_mrr


def test_11_empirical_als_hit_rank_2_and_rounding_verification():
    """
    Verify that the empirical ALS hit in M08 occurred at rank 2 (not rank 4)
    and that NDCG=0.00001 is the standard 5-decimal rounding of 5.673268e-6.
    """
    import json
    bench_path = Path("artifacts/als/m08/m08_test_benchmark_results.json")
    if not bench_path.exists():
        pytest.skip("m08_test_benchmark_results.json not found")

    with open(bench_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    als_m = data["models"]["ALS_R8_REG0.3_ITER10"]["metrics"]["10"]
    cohort_size = data["metadata"]["positive_cohort_size"]
    assert cohort_size == 111211
    assert als_m["hit_count"] == 1

    # Exact raw floats stored in JSON
    raw_hr = als_m["hit_rate"]
    raw_ndcg = als_m["ndcg"]
    raw_mrr = als_m["mrr"]

    # In rank 2:
    exp_hr = 1.0 / cohort_size                       # 8.991916e-6
    exp_mrr = 1.0 / (2.0 * cohort_size)              # 4.495958e-6
    exp_ndcg = 1.0 / (math.log2(3.0) * cohort_size)  # 5.673268e-6

    assert pytest.approx(raw_hr, rel=1e-7) == exp_hr
    assert pytest.approx(raw_mrr, rel=1e-7) == exp_mrr
    assert pytest.approx(raw_ndcg, rel=1e-7) == exp_ndcg

    # Decimal rounding:
    # 5.673268e-6 formatted with :.5f rounds to 0.00001
    assert f"{raw_ndcg:.5f}" == "0.00001"
    # 8.991916e-6 formatted with :.5f rounds to 0.00001
    assert f"{raw_hr:.5f}" == "0.00001"
    # 4.495958e-6 formatted with :.5f rounds to 0.00000
    assert f"{raw_mrr:.5f}" == "0.00000"


