"""
Unit and regression tests for Module M07: ALS Hyperparameter Tuning and Diagnostics.
Tests cover:
- Test split access guards (PermissionError on test paths)
- TrialConfig validation and invariants
- ExperimentRegistry persistence, atomic file write, resume capability
- Independent selection oracle (metric sorting, tie-breaking, family exclusion)
- ScreeningCohortManager determinism, reproducibility, and caching
- compute_long_tail_diagnostics fluke bias accounting and score statistics
- Diagnostic support-filter configuration integrity
"""

import json
from pathlib import Path
import pytest
import numpy as np

from recommender.als.tuner import (
    guard_test_split_access,
    TrialStatus,
    ModelFamily,
    TrialConfig,
    LongTailDiagnostics,
    TrialResult,
    ExperimentRegistry,
    ScreeningCohortManager,
    compute_long_tail_diagnostics,
)
from recommender.als.evaluator import HeldOutTarget


def test_guard_test_split_access():
    """Verify test split access is strictly blocked with PermissionError."""
    # Allowed paths
    guard_test_split_access("data/processed/splits/train")
    guard_test_split_access("data/processed/splits/validation")
    guard_test_split_access(Path("d:/PROJECT BIG DATA/MoodGraph/data/processed/splits/train/ratings.parquet"))

    # Blocked paths (both forward and backward slashes)
    with pytest.raises(PermissionError, match="SCIENTIFIC VIOLATION"):
        guard_test_split_access("data/processed/splits/test")

    with pytest.raises(PermissionError, match="SCIENTIFIC VIOLATION"):
        guard_test_split_access(r"data\processed\splits\test\ratings.parquet")

    with pytest.raises(PermissionError, match="SCIENTIFIC VIOLATION"):
        guard_test_split_access(Path("d:/PROJECT BIG DATA/MoodGraph/data/processed/splits/test/ratings.parquet"))


def test_trial_config_validation():
    """Verify TrialConfig parameter validation and invariants."""
    # Valid default config
    cfg = TrialConfig(trial_id="T01", rank=16, reg_param=0.1, max_iter=10)
    cfg.validate()
    assert cfg.model_family == ModelFamily.ALS_ONLY.value

    # Invalid empty trial_id
    with pytest.raises(ValueError, match="trial_id must be a non-empty string"):
        TrialConfig(trial_id="").validate()

    # Invalid rank <= 0
    with pytest.raises(ValueError, match="rank must be a positive integer"):
        TrialConfig(trial_id="T02", rank=0).validate()

    with pytest.raises(ValueError, match="rank must be a positive integer"):
        TrialConfig(trial_id="T03", rank=-5).validate()

    # Invalid reg_param < 0
    with pytest.raises(ValueError, match="reg_param must be non-negative"):
        TrialConfig(trial_id="T04", reg_param=-0.1).validate()

    # Invalid max_iter <= 0
    with pytest.raises(ValueError, match="max_iter must be a positive integer"):
        TrialConfig(trial_id="T05", max_iter=0).validate()

    # Invalid model family
    with pytest.raises(ValueError, match="Invalid model_family"):
        TrialConfig(trial_id="T06", model_family="UNKNOWN").validate()

    # Support filter requires support_filter_min_ratings > 0
    with pytest.raises(ValueError, match="support_filter_min_ratings must be > 0"):
        TrialConfig(
            trial_id="T07",
            model_family=ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value,
            support_filter_min_ratings=None,
        ).validate()

    with pytest.raises(ValueError, match="support_filter_min_ratings must be > 0"):
        TrialConfig(
            trial_id="T08",
            model_family=ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value,
            support_filter_min_ratings=0,
        ).validate()

    # Valid support filter config
    cfg_filter = TrialConfig(
        trial_id="T09",
        model_family=ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value,
        support_filter_min_ratings=5,
    )
    cfg_filter.validate()
    assert cfg_filter.support_filter_min_ratings == 5


def test_experiment_registry_lifecycle_and_persistence(tmp_path: Path):
    """Test registry registration, update, atomic save, and resume from disk."""
    reg_file = tmp_path / "registry.json"
    registry = ExperimentRegistry(reg_file)

    cfg1 = TrialConfig(trial_id="TRIAL_1", rank=16, reg_param=0.1)
    res1 = registry.register_trial(cfg1)
    assert res1.status == TrialStatus.PLANNED
    assert res1.trial_id == "TRIAL_1"

    # Re-registering returns existing record
    res1_dup = registry.register_trial(cfg1)
    assert res1_dup is res1

    # Update trial
    res1.status = TrialStatus.EVALUATED
    res1.screening_metrics = {"ndcg_10": 0.045, "hit_rate_10": 0.082}
    registry.update_trial(res1)

    # Resume from brand new registry instance reading same file
    registry2 = ExperimentRegistry(reg_file)
    assert "TRIAL_1" in registry2.trials
    loaded_trial = registry2.trials["TRIAL_1"]
    assert loaded_trial.status == TrialStatus.EVALUATED
    assert loaded_trial.screening_metrics["ndcg_10"] == 0.045
    assert loaded_trial.screening_metrics["hit_rate_10"] == 0.082


def test_experiment_registry_selection_rule(tmp_path: Path):
    """
    Test independent selection oracle:
    1. Only ALS_ONLY considered (diagnostics excluded).
    2. Primary: NDCG@10 DESC.
    3. Secondary: HitRate@10 DESC.
    4. Simplicity: Rank ASC.
    5. Regularization: regParam ASC.
    6. Lexicographical: trial_id ASC.
    """
    reg_file = tmp_path / "registry.json"
    registry = ExperimentRegistry(reg_file)

    # Model A: NDCG=0.04, HR=0.08, rank=16
    cfg_a = TrialConfig(trial_id="TRIAL_A", rank=16, reg_param=0.1)
    res_a = registry.register_trial(cfg_a)
    res_a.status = TrialStatus.EVALUATED
    res_a.full_metrics = {"ndcg_10": 0.04, "hit_rate_10": 0.08}
    registry.update_trial(res_a)

    # Model B: NDCG=0.05, HR=0.09, rank=32 (Higher NDCG - should win)
    cfg_b = TrialConfig(trial_id="TRIAL_B", rank=32, reg_param=0.1)
    res_b = registry.register_trial(cfg_b)
    res_b.status = TrialStatus.EVALUATED
    res_b.full_metrics = {"ndcg_10": 0.05, "hit_rate_10": 0.09}
    registry.update_trial(res_b)

    # Model C: Support filter diagnostic branch with huge NDCG (0.09) - MUST BE EXCLUDED!
    cfg_c = TrialConfig(
        trial_id="TRIAL_C_FILTER",
        model_family=ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value,
        support_filter_min_ratings=10,
        rank=16,
    )
    res_c = registry.register_trial(cfg_c)
    res_c.status = TrialStatus.EVALUATED
    res_c.full_metrics = {"ndcg_10": 0.09, "hit_rate_10": 0.15}
    registry.update_trial(res_c)

    best = registry.select_best_model(cohort="full", primary_metric="ndcg_10", secondary_metric="hit_rate_10")
    assert best is not None
    assert best.trial_id == "TRIAL_B"
    assert registry.selected_trial_id == "TRIAL_B"

    # Test tie-breaking on simpler rank
    cfg_d = TrialConfig(trial_id="TRIAL_D", rank=8, reg_param=0.1)
    res_d = registry.register_trial(cfg_d)
    res_d.status = TrialStatus.EVALUATED
    # Exactly same NDCG & HR as TRIAL_B, but rank=8 < rank=32
    res_d.full_metrics = {"ndcg_10": 0.05, "hit_rate_10": 0.09}
    registry.update_trial(res_d)

    best2 = registry.select_best_model(cohort="full", primary_metric="ndcg_10", secondary_metric="hit_rate_10")
    assert best2 is not None
    assert best2.trial_id == "TRIAL_D"  # rank 8 beats rank 32 on tie


def test_screening_cohort_manager(tmp_path: Path):
    """Test deterministic screening cohort sampling and reproducibility."""
    cohort_file = tmp_path / "screening_cohort.json"
    manager = ScreeningCohortManager(cohort_file, target_size=10, seed=42)

    # 15 users, 12 positive (>= 3.5), 3 negative (< 3.5)
    val_targets = {
        101: HeldOutTarget(movie_id=1, rating=4.0, timestamp=1000),
        102: HeldOutTarget(movie_id=2, rating=2.0, timestamp=1000),  # neg
        103: HeldOutTarget(movie_id=3, rating=3.5, timestamp=1000),  # pos
        104: HeldOutTarget(movie_id=4, rating=5.0, timestamp=1000),
        105: HeldOutTarget(movie_id=5, rating=1.5, timestamp=1000),  # neg
        106: HeldOutTarget(movie_id=6, rating=4.5, timestamp=1000),
        107: HeldOutTarget(movie_id=7, rating=4.0, timestamp=1000),
        108: HeldOutTarget(movie_id=8, rating=3.5, timestamp=1000),
        109: HeldOutTarget(movie_id=9, rating=3.0, timestamp=1000),  # neg
        110: HeldOutTarget(movie_id=10, rating=4.5, timestamp=1000),
        111: HeldOutTarget(movie_id=11, rating=4.0, timestamp=1000),
        112: HeldOutTarget(movie_id=12, rating=5.0, timestamp=1000),
        113: HeldOutTarget(movie_id=13, rating=4.0, timestamp=1000),
        114: HeldOutTarget(movie_id=14, rating=4.5, timestamp=1000),
        115: HeldOutTarget(movie_id=15, rating=5.0, timestamp=1000),
    }

    uids = manager.create_cohort(val_targets, relevance_threshold=3.5)
    assert len(uids) == 10
    # Assert all sampled uids are positive users
    for u in uids:
        assert val_targets[u].rating >= 3.5

    # Reloading from disk produces identical cohort
    manager2 = ScreeningCohortManager(cohort_file, target_size=10, seed=42)
    assert manager2.user_ids == uids

    # Sampling again with same seed produces identical results
    manager3 = ScreeningCohortManager(tmp_path / "cohort3.json", target_size=10, seed=42)
    uids3 = manager3.create_cohort(val_targets, relevance_threshold=3.5)
    assert uids3 == uids


def test_compute_long_tail_diagnostics():
    """Test calculation of item rating frequency bins and score distributions."""
    item_counts = {
        10: 1,      # 1 rating
        20: 3,      # 2-5 ratings
        30: 8,      # 6-10 ratings
        40: 50,     # 11-100 ratings
        50: 500,    # >100 ratings
    }

    recs = {
        1: [(10, 4.5), (20, 4.0), (30, 3.8), (40, 3.5), (50, 3.2)],
        2: [(10, 5.0), (50, 4.2), (50, 4.0), (50, 3.9), (50, 3.8)],
    }
    # Total slots = 10
    # movie 10 (count 1): 2 slots -> 20%
    # movie 20 (count 3): 1 slot  -> 10%
    # movie 30 (count 8): 1 slot  -> 10%
    # movie 40 (count 50): 1 slot -> 10%
    # movie 50 (count 500): 5 slots -> 50%

    diag = compute_long_tail_diagnostics(recs, item_counts)
    assert pytest.approx(diag.pct_slots_1_rating, abs=1e-5) == 20.0
    assert pytest.approx(diag.pct_slots_2_to_5_ratings, abs=1e-5) == 10.0
    assert pytest.approx(diag.pct_slots_6_to_10_ratings, abs=1e-5) == 10.0
    assert pytest.approx(diag.pct_slots_11_to_100_ratings, abs=1e-5) == 10.0
    assert pytest.approx(diag.pct_slots_gt_100_ratings, abs=1e-5) == 50.0

    # Scores: min=3.2, max=5.0
    assert pytest.approx(diag.score_min, abs=1e-4) == 3.2
    assert pytest.approx(diag.score_max, abs=1e-4) == 5.0
    assert diag.top_10_recommended_movie_ids[0] == 50


def test_metric_source_consistency():
    """Verify reconciled metric consistency between M03 artifacts and M07 manifest."""
    m03_path = Path("artifacts/m03_popularity_results.json")
    m07_manifest_path = Path("artifacts/als/m07/best_als_model_manifest.json")

    if not m03_path.exists() or not m07_manifest_path.exists():
        pytest.skip("Required artifacts not found for source consistency test")

    with open(m03_path, "r", encoding="utf-8") as f:
        m03_data = json.load(f)

    with open(m07_manifest_path, "r", encoding="utf-8") as f:
        m07_manifest = json.load(f)

    # Reconciled Popularity Count at K=10
    m03_count_10 = m03_data["variants"]["POPULARITY_COUNT"]["metrics"]["10"]
    expected_hr = round(m03_count_10["hit_rate"], 5)  # 0.05519
    expected_ndcg = round(m03_count_10["ndcg"], 5)   # 0.02789

    m07_comp = m07_manifest["comparison_with_m03_popularity"]
    assert m07_comp["m03_pop_count_hr_10"] == expected_hr
    assert m07_comp["m03_pop_count_ndcg_10"] == expected_ndcg

    # Reconciled Popularity Weighted at K=10
    m03_weighted_10 = m03_data["variants"]["POPULARITY_WEIGHTED"]["metrics"]["10"]
    expected_weighted_hr = round(m03_weighted_10["hit_rate"], 5)  # 0.01969
    expected_weighted_ndcg = round(m03_weighted_10["ndcg"], 5)   # 0.00771

    assert m07_comp["m03_pop_weighted_hr_10"] == expected_weighted_hr
    assert m07_comp["m03_pop_weighted_ndcg_10"] == expected_weighted_ndcg


def test_cohort_specific_coverage():
    """Verify that catalog coverage is correctly bound to cohort size and not conflated."""
    m06_path = Path("artifacts/als/m06/m06_als_evaluation_results.json")
    m07_manifest_path = Path("artifacts/als/m07/best_als_model_manifest.json")

    if not m06_path.exists() or not m07_manifest_path.exists():
        pytest.skip("Required artifacts not found for cohort coverage test")

    with open(m06_path, "r", encoding="utf-8") as f:
        m06_data = json.load(f)

    with open(m07_manifest_path, "r", encoding="utf-8") as f:
        m07_manifest = json.load(f)

    # M06 evaluated on ALL 109,779 positive validation users:
    m06_cov = m06_data["metrics"]["10"]["catalog_coverage_full"]
    m06_unique = m06_data["metrics"]["10"]["num_unique_recommended_movies"]
    assert m06_unique == 1545
    assert pytest.approx(m06_cov, abs=1e-4) == 0.0248  # ~2.48%

    # M07 screening evaluated on 5,000 users, finalist full validation evaluated on 109,779 users:
    m07_full_cov = m07_manifest["full_metrics"]["catalog_coverage_10"]
    m07_full_unique = m07_manifest["full_metrics"]["distinct_movies_10"]
    assert m07_full_unique == 35
    assert pytest.approx(m07_full_cov, abs=1e-4) == 0.00056  # 0.056%


def test_hit_count_and_denominator_consistency():
    """Verify that HitRate is mathematically consistent with hit_count / positive_cohort_size."""
    registry_path = Path("artifacts/als/m07/experiment_registry.json")
    if not registry_path.exists():
        pytest.skip("experiment_registry.json not found")

    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)

    for trial_id, trial in reg["trials"].items():
        sm = trial.get("screening_metrics")
        if sm and "hit_count_10" in sm and "positive_cohort_size" in sm:
            hit_count = sm["hit_count_10"]
            pos_cohort = sm["positive_cohort_size"]
            calculated_hr = hit_count / float(pos_cohort)
            assert pytest.approx(sm["hit_rate_10"], abs=1e-7) == calculated_hr


def test_model_selection_tie_breaking():
    """Verify Selection Oracle breaks ties deterministically using Occam's Razor."""
    tmp_file = Path("artifacts/als/m07/test_dummy_registry.json")
    reg = ExperimentRegistry(tmp_file)

    # Create 3 tied trials with HR=0 and NDCG=0, but different ranks
    t1 = TrialResult(
        trial_id="ALS_R32",
        config=TrialConfig(trial_id="ALS_R32", rank=32, reg_param=0.3, max_iter=10),
        status=TrialStatus.EVALUATED,
        screening_metrics={"ndcg_10": 0.0, "hit_rate_10": 0.0},
    )
    t2 = TrialResult(
        trial_id="ALS_R8",
        config=TrialConfig(trial_id="ALS_R8", rank=8, reg_param=0.3, max_iter=10),
        status=TrialStatus.EVALUATED,
        screening_metrics={"ndcg_10": 0.0, "hit_rate_10": 0.0},
    )
    t3 = TrialResult(
        trial_id="ALS_R16",
        config=TrialConfig(trial_id="ALS_R16", rank=16, reg_param=0.3, max_iter=10),
        status=TrialStatus.EVALUATED,
        screening_metrics={"ndcg_10": 0.0, "hit_rate_10": 0.0},
    )

    reg.update_trial(t1)
    reg.update_trial(t2)
    reg.update_trial(t3)

    best = reg.select_best_model(cohort="screening")
    assert best.config.trial_id == "ALS_R8"
    assert best.config.rank == 8

    if tmp_file.exists():
        tmp_file.unlink()


def test_screening_vs_full_validation_metric_provenance():
    """Verify clear provenance separation between screening metrics and full validation metrics."""
    manifest_path = Path("artifacts/als/m07/best_als_model_manifest.json")
    if not manifest_path.exists():
        pytest.skip("best_als_model_manifest.json not found")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "screening_metrics" in manifest
    assert "full_metrics" in manifest
    assert manifest["selected_trial_id"] == "ALS_R8_REG0.3_ITER10"
    assert manifest["model_family"] == "ALS_ONLY"
    assert manifest["full_metrics"]["positive_cohort_size"] == 109779


