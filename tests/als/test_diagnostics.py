"""
MoodGraph - Task 3A: Tests for Module M09 Diagnostics Engine
Provides independent unit, synthetic oracle, and integration tests
for Cold-Start, Long-Tail, Factor Reliability, and Performance Benchmarks.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Set

import numpy as np
import pytest

from recommender.als.diagnostics import (
    ColdStartClassifier,
    ColdStartType,
    FactorNormSummary,
    FactorReliabilityAnalyzer,
    ItemSupportAnalyzer,
    ItemSupportBin,
    ScoreDiagnosticsAnalyzer,
    ScoreDistributionSummary,
    SupportNormCorrelation,
    TopKSupportConcentration,
    synthetic_cold_start_oracle,
    synthetic_factor_dot_product_oracle,
    synthetic_item_support_oracle,
    synthetic_throughput_oracle,
)


# ==============================================================================
# 1. SYNTHETIC ORACLES TESTS
# ==============================================================================

def test_01_synthetic_item_support_oracle():
    """Test Oracle A with exact boundary items [0, 1, 5, 6, 10, 11, 50, 51, 100]."""
    test_supports = [0, 1, 5, 6, 10, 11, 50, 51, 100]
    result = synthetic_item_support_oracle(test_supports, catalog_size=len(test_supports))

    assert result["0 ratings"] == 1
    assert result["1-5 ratings"] == 2  # 1, 5
    assert result["6-10 ratings"] == 2  # 6, 10
    assert result["11-50 ratings"] == 2  # 11, 50
    assert result[">50 ratings"] == 2  # 51, 100
    assert sum(result.values()) == 9


def test_02_synthetic_item_support_oracle_conservation_failure():
    """Oracle A must raise ValueError if sum of items != catalog_size."""
    with pytest.raises(ValueError, match="Oracle A failure"):
        synthetic_item_support_oracle([0, 1, 2], catalog_size=10)


def test_03_synthetic_cold_start_oracle():
    """Test Oracle B with warm user/item, cold user, cold item, and low support."""
    known_users = {10, 20}
    known_items = {100, 200, 300}
    support_map = {100: 2, 200: 8, 300: 100}

    assert synthetic_cold_start_oracle(999, 100, known_users, known_items, support_map) == "COLD_USER"
    assert synthetic_cold_start_oracle(10, 999, known_users, known_items, support_map) == "COLD_ITEM"
    assert synthetic_cold_start_oracle(10, 100, known_users, known_items, support_map) == "LOW_SUPPORT_ITEM"
    assert synthetic_cold_start_oracle(10, 200, known_users, known_items, support_map) == "MODERATE_SUPPORT_ITEM"
    assert synthetic_cold_start_oracle(10, 300, known_users, known_items, support_map) == "WARM_PAIR"


def test_04_synthetic_factor_dot_product_oracle():
    """Test Oracle C against pure Python dot product."""
    u = [1.0, 2.0, -0.5]
    v = [0.5, -1.0, 4.0]
    # 1.0*0.5 + 2.0*(-1.0) + (-0.5)*4.0 = 0.5 - 2.0 - 2.0 = -3.5
    expected = -3.5
    actual = synthetic_factor_dot_product_oracle(u, v)
    assert math.isclose(actual, expected, rel_tol=1e-7)


def test_05_synthetic_throughput_oracle():
    """Test Oracle D for throughput math."""
    assert synthetic_throughput_oracle(1000, 0.5) == 2000.0
    with pytest.raises(ValueError):
        synthetic_throughput_oracle(1000, 0.0)


# ==============================================================================
# 2. ITEM SUPPORT ANALYZER UNIT TESTS
# ==============================================================================

def test_06_item_support_analyzer_basic():
    """Verify ItemSupportAnalyzer correctly groups items and verifies conservation."""
    catalog = {1, 2, 3, 4, 5, 6}
    supports = {1: 0, 2: 3, 3: 5, 4: 8, 5: 25, 6: 120}

    bins = ItemSupportAnalyzer.compute_distribution(supports, catalog)
    assert len(bins) == 5

    bin_map = {b.bin_name: b for b in bins}
    assert bin_map["0 ratings"].item_count == 1
    assert bin_map["1-5 ratings"].item_count == 2
    assert bin_map["6-10 ratings"].item_count == 1
    assert bin_map["11-50 ratings"].item_count == 1
    assert bin_map[">50 ratings"].item_count == 1

    total_count = sum(b.item_count for b in bins)
    assert total_count == 6


def test_07_item_support_analyzer_empty_catalog():
    """ItemSupportAnalyzer must raise ValueError on empty catalog."""
    with pytest.raises(ValueError):
        ItemSupportAnalyzer.compute_distribution({}, set())


# ==============================================================================
# 3. FACTOR RELIABILITY ANALYZER UNIT TESTS
# ==============================================================================

def test_08_factor_reliability_norms():
    """Verify L2 norm computation and percentile summaries."""
    factors = np.array([
        [3.0, 4.0],  # norm = 5.0
        [1.0, 0.0],  # norm = 1.0
        [0.0, 2.0],  # norm = 2.0
    ], dtype=np.float32)

    summary = FactorReliabilityAnalyzer.compute_norm_summary(factors, entity_type="test")
    assert summary.count == 3
    assert summary.rank == 2
    assert math.isclose(summary.min_norm, 1.0, rel_tol=1e-5)
    assert math.isclose(summary.max_norm, 5.0, rel_tol=1e-5)
    assert math.isclose(summary.median_norm, 2.0, rel_tol=1e-5)


def test_09_factor_reliability_correlation():
    """Verify correlation calculation between support and factor norms."""
    supports = np.array([1, 10, 100, 1000], dtype=np.int64)
    # Strictly increasing norms
    factors = np.array([
        [1.0, 0.0],
        [2.0, 0.0],
        [3.0, 0.0],
        [4.0, 0.0],
    ], dtype=np.float32)

    corr = FactorReliabilityAnalyzer.compute_support_correlation(supports, factors)
    assert corr.num_items == 4
    assert corr.pearson_corr > 0.95
    assert corr.spearman_corr == 1.0


# ==============================================================================
# 4. COLD START CLASSIFIER UNIT TESTS
# ==============================================================================

def test_10_cold_start_classifier_all_branches():
    """Verify ColdStartClassifier routes each interaction to correct category."""
    clf = ColdStartClassifier(
        train_users={1, 2},
        train_items={10, 20, 30, 40},
        item_support_dict={10: 2, 20: 8, 30: 55, 40: 0},
    )

    assert clf.classify_pair(99, 10) == ColdStartType.COLD_USER
    assert clf.classify_pair(1, 999) == ColdStartType.COLD_ITEM
    assert clf.classify_pair(1, 10) == ColdStartType.LOW_SUPPORT_ITEM
    assert clf.classify_pair(1, 20) == ColdStartType.MODERATE_SUPPORT_ITEM
    assert clf.classify_pair(1, 30) == ColdStartType.WARM_PAIR


# ==============================================================================
# 5. SCORE DIAGNOSTICS ANALYZER UNIT TESTS
# ==============================================================================

def test_11_score_distribution_summary():
    """Verify score distribution percentiles, negative and extreme score counting."""
    user_f = np.array([
        [1.0, 2.0],
        [-1.0, 0.0],
    ], dtype=np.float32)

    item_f = np.array([
        [3.0, 2.0],  # u0: 1*3 + 2*2 = 7.0 (exceeds 5.0) | u1: -1*3 + 0 = -3.0 (negative)
        [1.0, 1.0],  # u0: 1*1 + 2*1 = 3.0              | u1: -1*1 + 0 = -1.0 (negative)
    ], dtype=np.float32)

    stats = ScoreDiagnosticsAnalyzer.compute_score_distribution(user_f, item_f)
    assert stats.num_users == 2
    assert stats.num_items == 2
    assert stats.total_evaluations == 4
    assert stats.min_score == -3.0
    assert stats.max_score == 7.0
    assert stats.count_negative == 2
    assert stats.frac_negative == 0.5
    assert stats.count_gt_5 == 1
    assert stats.frac_gt_5 == 0.25


def test_12_topk_support_concentration():
    """Verify recommendation concentration across item support bins."""
    recs = {
        1: [(101, 4.5), (102, 4.0)],
        2: [(101, 4.2), (103, 3.8)],
    }
    support_dict = {
        101: 1,    # Support = 1 (Bin 1-5)
        102: 3,    # Support = 3 (Bin 1-5)
        103: 15,   # Support = 15 (Bin 11-50)
    }

    conc = ScoreDiagnosticsAnalyzer.compute_recommendation_concentration(
        recommendations=recs,
        item_support_dict=support_dict,
        catalog_size=100,
        k=2,
    )
    assert conc.k == 2
    assert conc.total_recommendations == 4
    assert conc.unique_items_recommended == 3
    assert math.isclose(conc.catalog_coverage_pct, 3.0, rel_tol=1e-5)
    # 101 appears twice with support 1 -> 2 / 4 = 0.5
    assert math.isclose(conc.frac_support_1, 0.5, rel_tol=1e-5)
    # 101, 102 are in 1-5: 3 / 4 = 0.75
    assert math.isclose(conc.frac_bin_1_5, 0.75, rel_tol=1e-5)
    # 103 is in 11-50: 1 / 4 = 0.25
    assert math.isclose(conc.frac_bin_11_50, 0.25, rel_tol=1e-5)


# ==============================================================================
# 6. INTEGRATION TESTS (REAL TRAIN & FROZEN MODEL ARTIFACTS)
# ==============================================================================

def test_13_real_catalog_and_train_support_conservation():
    """
    Integration Test: Check real catalog (62,423) and Train items (58,932).
    Verifies that the sum across the 5 support bins equals exactly 62,423.
    """
    import pyarrow.parquet as pq

    repo_root = Path(__file__).resolve().parent.parent.parent
    core_movies_path = repo_root / "data" / "processed" / "core" / "movies"
    train_path = repo_root / "data" / "processed" / "splits" / "train"

    assert core_movies_path.exists(), f"Missing {core_movies_path}"
    assert train_path.exists(), f"Missing {train_path}"

    cat_tbl = pq.read_table(core_movies_path, columns=["movieId"])
    catalog_ids = set(cat_tbl["movieId"].to_pylist())
    assert len(catalog_ids) == 62423

    train_tbl = pq.read_table(train_path, columns=["movieId"])
    train_mids = train_tbl["movieId"].to_numpy()
    unique_mids, counts = np.unique(train_mids, return_counts=True)
    assert len(unique_mids) == 58932

    support_dict = dict(zip(unique_mids, counts))
    bins = ItemSupportAnalyzer.compute_distribution(support_dict, catalog_ids)

    bin_map = {b.bin_name: b for b in bins}
    assert bin_map["0 ratings"].item_count == 3491
    assert bin_map["1-5 ratings"].item_count == 28834
    assert bin_map["6-10 ratings"].item_count == 6838
    assert bin_map["11-50 ratings"].item_count == 10234
    assert bin_map[">50 ratings"].item_count == 13026

    total_sum = sum(b.item_count for b in bins)
    assert total_sum == 62423


def test_14_real_frozen_als_factors_and_norms():
    """
    Integration Test: Load frozen champion factors (ALS_R8_REG0.3_ITER10).
    Verify dimensions: 58,932 items x 8, 162,541 users x 8.
    Verify L2 norms are strictly positive and finite.
    """
    import pyarrow.parquet as pq

    repo_root = Path(__file__).resolve().parent.parent.parent
    model_path = repo_root / "artifacts" / "models" / "als" / "m07_tuning" / "ALS_R8_REG0.3_ITER10"
    item_path = model_path / "spark_model" / "itemFactors"
    user_path = model_path / "spark_model" / "userFactors"

    assert item_path.exists()
    assert user_path.exists()

    df_items = pq.read_table(item_path).to_pandas()
    item_vecs = np.vstack(df_items["features"].values).astype(np.float32)
    assert item_vecs.shape == (58932, 8)

    df_users = pq.read_table(user_path).to_pandas()
    user_vecs = np.vstack(df_users["features"].values).astype(np.float32)
    assert user_vecs.shape == (162541, 8)

    item_summary = FactorReliabilityAnalyzer.compute_norm_summary(item_vecs, "item")
    assert item_summary.rank == 8
    assert item_summary.count == 58932
    assert item_summary.min_norm > 0.1
    assert item_summary.max_norm < 10.0

    user_summary = FactorReliabilityAnalyzer.compute_norm_summary(user_vecs, "user")
    assert user_summary.rank == 8
    assert user_summary.count == 162541
    assert user_summary.min_norm > 0.1
    assert user_summary.max_norm < 10.0


def test_15_real_factor_norm_support_correlation():
    """
    Integration Test: Verify positive correlation between log1p(support) and item factor norm.
    Pearson correlation must be positive with p-value < 1e-10.
    """
    import pyarrow.parquet as pq

    repo_root = Path(__file__).resolve().parent.parent.parent
    model_path = repo_root / "artifacts" / "models" / "als" / "m07_tuning" / "ALS_R8_REG0.3_ITER10"
    train_path = repo_root / "data" / "processed" / "splits" / "train"

    df_items = pq.read_table(model_path / "spark_model" / "itemFactors").to_pandas()
    item_ids = df_items["id"].values
    item_vecs = np.vstack(df_items["features"].values).astype(np.float32)

    train_tbl = pq.read_table(train_path, columns=["movieId"])
    train_mids = train_tbl["movieId"].to_numpy()
    unique_mids, counts = np.unique(train_mids, return_counts=True)
    count_dict = dict(zip(unique_mids, counts))

    supports = np.array([count_dict[mid] for mid in item_ids])
    corr = FactorReliabilityAnalyzer.compute_support_correlation(supports, item_vecs)

    assert corr.num_items == 58932
    assert corr.pearson_corr > 0.10
    assert corr.pearson_pval < 1e-10
    assert corr.spearman_corr > 0.10
