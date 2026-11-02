"""
Unit Tests for Module M02 - Top-N Evaluation Engine
Covers all 20 required hand-calculated cases, edge cases, tie-breaking,
candidate pool filtering, and cohort denominator assertions.
"""

import math
import pytest
from typing import Dict, List, Set, Tuple

from recommender.als.evaluator import (
    HeldOutTarget,
    SingleUserMetricResult,
    EvaluationSummary,
    compute_single_user_metrics,
    sort_and_rank_candidates,
    filter_seen_items,
    validate_candidate_pool,
    validate_k,
    validate_raw_score,
    TopNEvaluator,
)


def test_01_single_positive_at_rank_1():
    """Case 1: One positive movie at rank 1 in Top-5."""
    target_mid = 101
    recs = [101, 102, 103, 104, 105]
    m = compute_single_user_metrics(recs, target_mid, k=5)

    assert m["hit"] == 1.0
    assert m["recall"] == 1.0
    assert m["precision"] == pytest.approx(1.0 / 5.0)  # 0.2
    assert m["ndcg"] == pytest.approx(1.0 / math.log2(1 + 1))  # 1.0
    assert m["mrr"] == 1.0
    assert m["rank"] == 1


def test_02_single_positive_at_rank_3_in_top_5():
    """Case 2: One positive movie at rank 3 in Top-5: HR=1, Recall=1, P=0.2, NDCG=0.5, MRR=1/3."""
    target_mid = 103
    recs = [101, 102, 103, 104, 105]
    m = compute_single_user_metrics(recs, target_mid, k=5)

    assert m["hit"] == 1.0
    assert m["recall"] == 1.0
    assert m["precision"] == pytest.approx(0.2)
    # NDCG@5: 1 / log2(3 + 1) = 1 / log2(4) = 1 / 2 = 0.5
    assert m["ndcg"] == pytest.approx(0.5)
    # MRR@5: 1 / 3 = 0.3333333333333333
    assert m["mrr"] == pytest.approx(1.0 / 3.0)
    assert m["rank"] == 3


def test_03_single_positive_at_rank_k_last_position():
    """Case 3: One positive movie at the last position (rank K)."""
    target_mid = 105
    recs = [101, 102, 103, 104, 105]
    m = compute_single_user_metrics(recs, target_mid, k=5)

    assert m["hit"] == 1.0
    assert m["recall"] == 1.0
    assert m["precision"] == pytest.approx(1.0 / 5.0)
    assert m["ndcg"] == pytest.approx(1.0 / math.log2(5 + 1))  # 1 / log2(6) ≈ 0.3868528
    assert m["mrr"] == pytest.approx(1.0 / 5.0)  # 0.2
    assert m["rank"] == 5


def test_04_positive_movie_not_in_top_k():
    """Case 4: Positive movie not in recommendation list."""
    target_mid = 999
    recs = [101, 102, 103, 104, 105]
    m = compute_single_user_metrics(recs, target_mid, k=5)

    assert m["hit"] == 0.0
    assert m["recall"] == 0.0
    assert m["precision"] == 0.0
    assert m["ndcg"] == 0.0
    assert m["mrr"] == 0.0
    assert m["rank"] is None


def test_05_positive_movie_at_rank_k_plus_1():
    """Case 5: Positive movie at rank K+1 (e.g. rank 6 for K=5, but in Top-10)."""
    target_mid = 106
    recs = [101, 102, 103, 104, 105, 106, 107]

    # For K=5: miss
    m5 = compute_single_user_metrics(recs, target_mid, k=5)
    assert m5["hit"] == 0.0
    assert m5["recall"] == 0.0
    assert m5["precision"] == 0.0
    assert m5["ndcg"] == 0.0
    assert m5["mrr"] == 0.0
    assert m5["rank"] is None

    # For K=10: hit at rank 6
    m10 = compute_single_user_metrics(recs, target_mid, k=10)
    assert m10["hit"] == 1.0
    assert m10["recall"] == 1.0
    assert m10["precision"] == pytest.approx(1.0 / 10.0)
    assert m10["ndcg"] == pytest.approx(1.0 / math.log2(6 + 1))  # 1 / log2(7) ≈ 0.356207
    assert m10["mrr"] == pytest.approx(1.0 / 6.0)
    assert m10["rank"] == 6


def test_06_user_validation_rating_below_threshold():
    """Case 6: User with rating = 2.0 (below 3.5), excluded from positive cohort denominator."""
    evaluator = TopNEvaluator(k_list=[5], relevance_threshold=3.5)
    recs = {1: [101, 102, 103, 104, 105]}
    targets = {1: HeldOutTarget(movie_id=101, rating=2.0)}

    res = evaluator.evaluate(recs, targets)
    summary = res[5]

    assert summary.positive_cohort_size == 0
    assert summary.non_positive_cohort_size == 1
    assert summary.total_target_users == 1
    assert summary.hit_rate == 0.0
    assert summary.recall == 0.0
    assert summary.precision == 0.0


def test_07_user_validation_rating_exactly_threshold():
    """Case 7: User with rating = 3.5, counted in positive cohort."""
    evaluator = TopNEvaluator(k_list=[5], relevance_threshold=3.5)
    recs = {1: [101, 102, 103, 104, 105]}
    targets = {1: HeldOutTarget(movie_id=101, rating=3.5)}

    res = evaluator.evaluate(recs, targets)
    summary = res[5]

    assert summary.positive_cohort_size == 1
    assert summary.non_positive_cohort_size == 0
    assert summary.hit_rate == 1.0
    assert summary.recall == 1.0
    assert summary.precision == 0.2


def test_08_user_with_empty_recommendations():
    """Case 8: User in positive cohort has empty recommendation list []. Scored 0, kept in denominator."""
    evaluator = TopNEvaluator(k_list=[5], relevance_threshold=3.5)
    recs = {1: []}
    targets = {1: HeldOutTarget(movie_id=101, rating=4.0)}

    res = evaluator.evaluate(recs, targets)
    summary = res[5]

    assert summary.positive_cohort_size == 1
    assert summary.users_missing_recommendations == 1
    assert summary.users_with_recommendations == 0
    assert summary.hit_rate == 0.0
    assert summary.recall == 0.0
    assert summary.precision == 0.0
    assert summary.ndcg == 0.0
    assert summary.mrr == 0.0


def test_09_user_missing_from_prediction_dict():
    """Case 9: User has positive target but is completely absent from recommendations mapping."""
    evaluator = TopNEvaluator(k_list=[5], relevance_threshold=3.5)
    recs = {}  # No recommendations generated for user 1
    targets = {1: HeldOutTarget(movie_id=101, rating=5.0)}

    res = evaluator.evaluate(recs, targets)
    summary = res[5]

    assert summary.positive_cohort_size == 1
    assert summary.users_missing_recommendations == 1
    assert summary.hit_rate == 0.0
    assert summary.recall == 0.0


def test_10_detect_duplicate_movie_id_in_recommendations():
    """Case 10: Duplicate movieId in recommendations raises ValueError."""
    recs = [101, 102, 101, 104, 105]
    with pytest.raises(ValueError, match="Duplicate movieId"):
        compute_single_user_metrics(recs, target_movie_id=101, k=5)


def test_11_stable_tie_break_score_desc_movie_id_asc():
    """Case 11: Equal scores must tie-break deterministically by movieId ASC."""
    scored = [
        (105, 4.0),
        (102, 4.0),
        (101, 4.0),
        (200, 5.0),  # highest score
    ]
    ranked = sort_and_rank_candidates(scored)
    # Expected: 200 first (score 5.0), then [101, 102, 105] sorted ascending by ID
    assert ranked == [200, 101, 102, 105]


def test_12_detect_nan_and_inf_scores():
    """Case 12: Scores containing NaN or Inf raise ValueError."""
    with pytest.raises(ValueError, match="must be finite"):
        sort_and_rank_candidates([(101, float("nan"))])

    with pytest.raises(ValueError, match="must be finite"):
        sort_and_rank_candidates([(102, float("inf"))])

    with pytest.raises(ValueError, match="must be finite"):
        sort_and_rank_candidates([(103, float("-inf"))])


def test_13_invalid_k_values():
    """Case 13: K <= 0 or non-integer K raises ValueError."""
    with pytest.raises(ValueError, match="strictly positive integer"):
        validate_k(0)

    with pytest.raises(ValueError, match="strictly positive integer"):
        validate_k(-5)

    with pytest.raises(ValueError, match="strictly positive integer"):
        validate_k(5.5)  # type: ignore


def test_14_precision_denominator_always_k_when_list_shorter_than_k():
    """Case 14: Precision denominator is ALWAYS K, never shortened when list length < K."""
    recs = [101, 102]  # length 2, but K = 5
    m = compute_single_user_metrics(recs, target_movie_id=101, k=5)

    # Even though list length is 2, Precision@5 must be 1/5 = 0.2, NOT 1/2 = 0.5
    assert m["precision"] == pytest.approx(0.2)


def test_15_catalog_coverage_calculation():
    """Case 15: Catalog Coverage aggregates distinct movies across multiple users without double-counting."""
    evaluator = TopNEvaluator(k_list=[2], catalog_size=10, scorable_catalog_size=8)
    recs = {
        1: [10, 20],
        2: [20, 30],  # 20 overlaps with user 1
        3: [30, 40],  # 30 overlaps with user 2
    }
    targets = {
        1: HeldOutTarget(movie_id=10, rating=4.0),
        2: HeldOutTarget(movie_id=20, rating=4.0),
        3: HeldOutTarget(movie_id=30, rating=4.0),
    }

    res = evaluator.evaluate(recs, targets)
    summary = res[2]

    # Unique recommended movies: {10, 20, 30, 40} = 4 movies
    assert summary.num_unique_recommended_movies == 4
    assert summary.catalog_coverage_full == pytest.approx(4 / 10.0)  # 0.4
    assert summary.catalog_coverage_scorable == pytest.approx(4 / 8.0)  # 0.5


def test_16_validation_candidate_excludes_train_and_detects_leak():
    """Case 16: Validation candidate filtering removes Train_u seen items and detects leaks."""
    train_seen = {101, 102}
    catalog = {101, 102, 103, 104, 105}
    raw_candidates = [101, 103, 104, 102, 105]

    filtered = filter_seen_items(raw_candidates, train_seen)
    assert filtered == [103, 104, 105]

    # If raw_candidates (containing seen items) are passed to validate_candidate_pool, it raises
    with pytest.raises(ValueError, match="seen_leaks=2"):
        validate_candidate_pool(raw_candidates, seen_movie_ids=train_seen, catalog_movie_ids=catalog, strict=True)


def test_17_test_candidate_excludes_train_and_val():
    """Case 17: Synthetic test candidate filtering removes both Train_u and Val_u."""
    train_u = {10, 20}
    val_u = {30}
    combined_seen = train_u | val_u  # {10, 20, 30}
    raw_recs = [10, 30, 40, 50]

    filtered = filter_seen_items(raw_recs, combined_seen)
    assert filtered == [40, 50]


def test_18_cold_start_target_movie_scored_as_miss_in_denominator():
    """Case 18: Cold-start target movie (cannot be scored) is evaluated as miss, kept in denominator."""
    evaluator = TopNEvaluator(k_list=[5], relevance_threshold=3.5)
    # Target 999 is cold-start (unscorable, not in recommendations)
    targets = {1: HeldOutTarget(movie_id=999, rating=4.0)}
    recs = {1: [101, 102, 103, 104, 105]}

    res = evaluator.evaluate(recs, targets)
    summary = res[5]

    assert summary.positive_cohort_size == 1
    assert summary.hit_rate == 0.0
    assert summary.hit_count == 0


def test_19_denominator_distinction_positive_vs_all():
    """Case 19: Positive-target cohort denominator is strictly N_pos, separated from all-users."""
    evaluator = TopNEvaluator(k_list=[5], relevance_threshold=3.5)
    targets = {
        1: HeldOutTarget(movie_id=101, rating=4.5),  # Positive (hit)
        2: HeldOutTarget(movie_id=999, rating=4.0),  # Positive (miss)
        3: HeldOutTarget(movie_id=101, rating=2.0),  # Non-positive
        4: HeldOutTarget(movie_id=102, rating=1.5),  # Non-positive
    }
    recs = {
        1: [101, 102, 103],
        2: [101, 102, 103],
        3: [101, 102, 103],
        4: [101, 102, 103],
    }

    res = evaluator.evaluate(recs, targets)
    summary = res[5]

    # Positive cohort: exactly 2 users (users 1 and 2)
    assert summary.positive_cohort_size == 2
    assert summary.non_positive_cohort_size == 2
    assert summary.total_target_users == 4

    # Primary hit rate is 1 hit / 2 positive users = 0.5
    assert summary.hit_rate == pytest.approx(0.5)

    # Diagnostic for all users: 1 hit / 4 total users = 0.25
    assert summary.diagnostic_all_users is not None
    assert summary.diagnostic_all_users["all_users_hit_rate"] == pytest.approx(0.25)


def test_20_evaluator_determinism_and_reproducibility():
    """Case 20: Repeated evaluations on identical inputs produce bit-for-bit identical results."""
    evaluator = TopNEvaluator(k_list=[5, 10], relevance_threshold=3.5, catalog_size=100)
    targets = {
        1: HeldOutTarget(movie_id=10, rating=4.0),
        2: HeldOutTarget(movie_id=20, rating=5.0),
    }
    recs = {
        1: [10, 11, 12, 13, 14],
        2: [25, 20, 21, 22, 23],
    }

    res_1 = evaluator.evaluate(recs, targets)
    res_2 = evaluator.evaluate(recs, targets)

    for k in [5, 10]:
        assert res_1[k].hit_rate == res_2[k].hit_rate
        assert res_1[k].ndcg == res_2[k].ndcg
        assert res_1[k].mrr == res_2[k].mrr
        assert res_1[k].precision == res_2[k].precision
        assert res_1[k].recall == res_2[k].recall
        assert res_1[k].num_unique_recommended_movies == res_2[k].num_unique_recommended_movies


def test_21_multi_k_evaluation():
    """Case 21: Evaluates across multiple K cutoffs simultaneously."""
    evaluator = TopNEvaluator(k_list=[5, 10, 20])
    target = 107  # Rank 7 in recommendations
    recs = {1: list(range(101, 125))}  # [101, 102, ..., 124]
    targets = {1: HeldOutTarget(movie_id=target, rating=4.0)}

    res = evaluator.evaluate(recs, targets)

    # K=5: target is at rank 7 > 5 -> miss
    assert res[5].hit_rate == 0.0
    assert res[5].ndcg == 0.0

    # K=10: target is at rank 7 <= 10 -> hit
    assert res[10].hit_rate == 1.0
    assert res[10].ndcg == pytest.approx(1.0 / math.log2(7 + 1))  # 1 / log2(8) = 1 / 3 ≈ 0.333333
    assert res[10].mrr == pytest.approx(1.0 / 7.0)
    assert res[10].precision == pytest.approx(1.0 / 10.0)

    # K=20: target is at rank 7 <= 20 -> hit
    assert res[20].hit_rate == 1.0
    assert res[20].ndcg == pytest.approx(1.0 / math.log2(7 + 1))  # identical DCG
    assert res[20].mrr == pytest.approx(1.0 / 7.0)
    assert res[20].precision == pytest.approx(1.0 / 20.0)
