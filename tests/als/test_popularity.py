"""
Unit & Integration Tests for Module M03 - Popularity Baseline Recommender
Covers multi-layer quality assurance:
- Layer 1: Mathematical correctness & hand calculations
- Layer 2: Independent Python reference comparison
- Layer 3: Adversarial edge cases (seen filtering, heavy users, zero counts, tie breaking)
- Layer 4: Integration with M02 TopNEvaluator
"""

import math
import pytest
from typing import Dict, List, Set, Tuple

from recommender.als.evaluator import HeldOutTarget, TopNEvaluator
from recommender.als.popularity import (
    PopularityMovieRecord,
    PopularityRecommendation,
    PopularityRecommender,
    compute_weighted_score,
    generate_batch_top_k,
    generate_user_top_k,
    rank_movies_by_count,
    rank_movies_by_weighted_average,
)


def test_01_count_aggregation_correctness():
    """Case 1: Count aggregation on synthetic ratings."""
    stats = [
        (101, 50, 4.2),
        (102, 120, 3.8),
        (103, 10, 4.9),
    ]
    ranked = rank_movies_by_count(stats)
    # Movie 102 has highest count (120), then 101 (50), then 103 (10)
    assert [r.movie_id for r in ranked] == [102, 101, 103]
    assert [r.rank for r in ranked] == [1, 2, 3]
    assert [r.rating_count for r in ranked] == [120, 50, 10]


def test_02_average_rating_correctness():
    """Case 2: Average rating preserved correctly in movie records."""
    stats = [(101, 10, 4.25), (102, 5, 3.60)]
    ranked = rank_movies_by_count(stats)
    assert ranked[0].avg_rating == 4.25
    assert ranked[1].avg_rating == 3.60


def test_03_hand_calculated_weighted_average():
    """Case 3: Exact hand calculation for Bayesian Weighted Average."""
    # Global mean C = 3.5, smoothing m = 10.0
    c = 3.5
    m = 10.0

    # Movie A: v=100, R=4.5 -> (100 * 4.5 + 10 * 3.5) / (100 + 10) = 485 / 110 = 4.409090909...
    score_a = compute_weighted_score(v=100, r=4.5, c=c, m=m)
    assert score_a == pytest.approx(485.0 / 110.0)
    assert score_a == pytest.approx(4.409090909090909)

    # Movie B: v=1, R=5.0 -> (1 * 5.0 + 10 * 3.5) / (1 + 10) = 40 / 11 = 3.636363636...
    score_b = compute_weighted_score(v=1, r=5.0, c=c, m=m)
    assert score_b == pytest.approx(40.0 / 11.0)
    assert score_b == pytest.approx(3.6363636363636362)

    # Movie C: v=1, R=1.0 -> (1 * 1.0 + 10 * 3.5) / (1 + 10) = 36 / 11 = 3.272727272...
    score_c = compute_weighted_score(v=1, r=1.0, c=c, m=m)
    assert score_c == pytest.approx(36.0 / 11.0)
    assert score_c == pytest.approx(3.272727272727273)


def test_04_count_ranking_order():
    """Case 4: Movie ranking order by Count."""
    stats = [
        (1, 100, 3.0),
        (2, 500, 2.5),
        (3, 300, 4.0),
    ]
    ranked = rank_movies_by_count(stats)
    assert [r.movie_id for r in ranked] == [2, 3, 1]


def test_05_weighted_average_ranking_order():
    """Case 5: Movie ranking order by Weighted Average."""
    # Movie 1 has 100 ratings of 4.5; Movie 2 has 1 rating of 5.0
    stats = [
        (1, 100, 4.5),  # weighted score: 4.409
        (2, 1, 5.0),    # weighted score: 3.636
        (3, 50, 4.2),   # weighted score: (50*4.2 + 35) / 60 = 245 / 60 = 4.083
    ]
    ranked = rank_movies_by_weighted_average(stats, global_mean=3.5, m=10.0)
    # Expected order: Movie 1 (4.409) > Movie 3 (4.083) > Movie 2 (3.636)
    assert [r.movie_id for r in ranked] == [1, 3, 2]
    assert ranked[0].weighted_score > ranked[1].weighted_score > ranked[2].weighted_score


def test_06_stable_tie_breaking():
    """Case 6: Tie-breaking is deterministic (movieId ASC)."""
    stats = [
        (205, 100, 4.0),
        (101, 100, 4.0),
        (150, 100, 4.0),
    ]
    # For count: counts and avgs are identical -> tie break by movieId ASC
    ranked_cnt = rank_movies_by_count(stats)
    assert [r.movie_id for r in ranked_cnt] == [101, 150, 205]

    # For weighted: scores are identical -> tie break by movieId ASC
    ranked_w = rank_movies_by_weighted_average(stats, global_mean=3.5, m=10.0)
    assert [r.movie_id for r in ranked_w] == [101, 150, 205]


def test_07_single_rating_movie_behavior():
    """Case 7: Single-rating 5.0 movie is penalized by Bayesian prior."""
    stats = [
        (10, 1000, 4.3),  # highly rated popular movie
        (20, 1, 5.0),     # fluke 1-rating 5.0 movie
    ]
    ranked = rank_movies_by_weighted_average(stats, global_mean=3.5, m=10.0)
    # Movie 10 must rank above movie 20
    assert ranked[0].movie_id == 10
    assert ranked[1].movie_id == 20


def test_08_movie_with_zero_ratings_behavior():
    """Case 8: Movie with 0 ratings gets score equal to global mean C."""
    score = compute_weighted_score(v=0, r=0.0, c=3.5, m=10.0)
    assert score == pytest.approx(3.5)


def test_09_seen_items_filtering():
    """Case 9: Movies in seen_movies are never recommended."""
    ranked_ids = [101, 102, 103, 104, 105, 106, 107]
    scores_map = {mid: float(mid) for mid in ranked_ids}
    seen = {101, 103, 105}

    recs = generate_user_top_k(
        user_id=1,
        ranked_movie_ids=ranked_ids,
        scores_map=scores_map,
        seen_movies=seen,
        k=3,
        model_name="POPULARITY",
    )

    rec_ids = [r.movie_id for r in recs]
    # Must skip 101, 103, 105 -> [102, 104, 106]
    assert rec_ids == [102, 104, 106]
    assert len(rec_ids) == 3
    assert set(rec_ids).isdisjoint(seen)


def test_10_top_k_replenishment_after_seen_filtering():
    """Case 10: Ensures full K recommendations even when user has seen top movies."""
    # Top 5 movies are seen by user
    ranked_ids = list(range(1, 30))  # 1 to 29
    scores_map = {mid: float(30 - mid) for mid in ranked_ids}
    seen = {1, 2, 3, 4, 5}

    recs = generate_user_top_k(
        user_id=1,
        ranked_movie_ids=ranked_ids,
        scores_map=scores_map,
        seen_movies=seen,
        k=5,
    )

    rec_ids = [r.movie_id for r in recs]
    # Should get [6, 7, 8, 9, 10]
    assert rec_ids == [6, 7, 8, 9, 10]
    assert len(rec_ids) == 5
    assert [r.rank for r in recs] == [1, 2, 3, 4, 5]


def test_11_heavy_user_seen_many_movies():
    """Case 11: Heavy user with 1,000 seen movies still receives full Top-10."""
    ranked_ids = list(range(1, 2000))
    scores_map = {mid: float(2000 - mid) for mid in ranked_ids}
    seen = set(range(1, 1001))  # user has seen first 1,000 movies

    recs = generate_user_top_k(
        user_id=99,
        ranked_movie_ids=ranked_ids,
        scores_map=scores_map,
        seen_movies=seen,
        k=10,
    )

    rec_ids = [r.movie_id for r in recs]
    assert len(rec_ids) == 10
    assert rec_ids == list(range(1001, 1011))
    assert set(rec_ids).isdisjoint(seen)


def test_12_no_duplicate_movie_ids_in_top_k():
    """Case 12: Output contains no duplicate movie IDs."""
    ranked_ids = [10, 20, 30, 40, 50]
    scores_map = {mid: 1.0 for mid in ranked_ids}
    recs = generate_user_top_k(1, ranked_ids, scores_map, seen_movies=set(), k=5)
    rec_ids = [r.movie_id for r in recs]
    assert len(rec_ids) == len(set(rec_ids))


def test_13_no_out_of_catalog_movies():
    """Case 13: Only movies from candidate catalog are returned."""
    catalog = {10, 20, 30}
    ranked_ids = [10, 20, 30]
    scores_map = {10: 3.0, 20: 2.0, 30: 1.0}
    recs = generate_user_top_k(1, ranked_ids, scores_map, seen_movies=set(), k=3)
    rec_ids = [r.movie_id for r in recs]
    for mid in rec_ids:
        assert mid in catalog


def test_14_all_scores_finite_no_nan_or_inf():
    """Case 14: All recommended scores are finite."""
    stats = [(1, 10, 4.0), (2, 20, 3.5)]
    recommender = PopularityRecommender(m=10.0)
    recommender.fit_from_stats(stats, global_mean=3.5)

    recs_count = recommender.recommend(1, seen_movies=set(), k=2, variant="count")
    for r in recs_count:
        assert not math.isnan(r.raw_score)
        assert not math.isinf(r.raw_score)

    recs_weighted = recommender.recommend(1, seen_movies=set(), k=2, variant="weighted")
    for r in recs_weighted:
        assert not math.isnan(r.raw_score)
        assert not math.isinf(r.raw_score)


def test_15_deterministic_output():
    """Case 15: Repeated runs produce bit-for-bit identical results."""
    stats = [(1, 50, 4.2), (2, 50, 4.2), (3, 80, 3.9)]
    rec1 = PopularityRecommender(m=10.0).fit_from_stats(stats, global_mean=3.5)
    rec2 = PopularityRecommender(m=10.0).fit_from_stats(stats, global_mean=3.5)

    out1 = rec1.recommend(1, seen_movies=set(), k=3, variant="count")
    out2 = rec2.recommend(1, seen_movies=set(), k=3, variant="count")

    assert [r.to_dict() for r in out1] == [r.to_dict() for r in out2]


def test_16_integration_with_m02_evaluator():
    """Case 16: Full pipeline integration with M02 TopNEvaluator."""
    # Create synthetic catalog and stats
    stats = [
        (101, 100, 4.5),
        (102, 90, 4.0),
        (103, 80, 3.8),
        (104, 70, 3.5),
        (105, 60, 3.2),
    ]
    recommender = PopularityRecommender(m=10.0).fit_from_stats(stats, global_mean=3.5)

    # 2 users:
    # User 1 has target 101 (rank 1), seen nothing -> Hit at rank 1
    # User 2 has target 105 (rank 5), seen {101, 102} -> Gets [103, 104, 105] -> Hit at rank 3
    user_histories = {
        1: set(),
        2: {101, 102},
    }
    targets = {
        1: HeldOutTarget(movie_id=101, rating=4.0),
        2: HeldOutTarget(movie_id=105, rating=4.5),
    }

    batch_recs = recommender.recommend_for_users(user_histories, k=5, variant="count")
    evaluator = TopNEvaluator(k_list=[5], relevance_threshold=3.5, catalog_size=5)
    results = evaluator.evaluate(batch_recs, targets)
    summary = results[5]

    # User 1: hit rank 1 -> NDCG=1.0, MRR=1.0, HR=1.0
    # User 2: hit rank 3 -> NDCG=1/log2(4)=0.5, MRR=1/3, HR=1.0
    # Average: HR = 1.0, NDCG = (1.0 + 0.5) / 2 = 0.75, MRR = (1.0 + 1/3) / 2 = 2/3 ≈ 0.666667
    assert summary.hit_rate == 1.0
    assert summary.ndcg == pytest.approx(0.75)
    assert summary.mrr == pytest.approx((1.0 + 1.0 / 3.0) / 2.0)
    assert summary.positive_cohort_size == 2


def test_17_positive_user_without_hit_kept_in_denominator():
    """Case 17: User with positive target but target not in Top-5 remains in denominator."""
    stats = [(101, 100, 4.0), (102, 90, 4.0)]
    recommender = PopularityRecommender(m=10.0).fit_from_stats(stats, global_mean=3.5)

    user_histories = {1: set()}
    targets = {1: HeldOutTarget(movie_id=999, rating=4.0)}  # target 999 not in Top-2

    batch_recs = recommender.recommend_for_users(user_histories, k=2, variant="count")
    evaluator = TopNEvaluator(k_list=[2], relevance_threshold=3.5)
    results = evaluator.evaluate(batch_recs, targets)
    summary = results[2]

    assert summary.positive_cohort_size == 1
    assert summary.hit_count == 0
    assert summary.hit_rate == 0.0
    assert summary.ndcg == 0.0


def test_18_no_validation_leakage_in_popularity_stats():
    """Case 18: Popularity statistics only computed from Train."""
    # Ensure stats are independent of any validation labels
    train_stats = [(1, 100, 4.0), (2, 50, 4.0)]
    rec = PopularityRecommender().fit_from_stats(train_stats, global_mean=3.5)
    # Ranks depend purely on train_stats
    assert rec._count_ranked_ids == [1, 2]


def test_19_test_split_isolation():
    """Case 19: Synthetic check that seen items filtering supports Train U Val without reading Test."""
    # For Test evaluation in future: seen = Train | Val
    train_seen = {1, 2}
    val_seen = {3}
    combined_seen = train_seen | val_seen

    ranked_ids = [1, 2, 3, 4, 5, 6]
    scores_map = {mid: 1.0 for mid in ranked_ids}
    recs = generate_user_top_k(1, ranked_ids, scores_map, seen_movies=combined_seen, k=2)
    assert [r.movie_id for r in recs] == [4, 5]


def test_20_multi_k_support_and_consistency():
    """Case 20: Recommender supports K=5, 10, 20 and recommendations are hierarchical prefixes."""
    ranked_ids = list(range(1, 50))
    scores_map = {mid: 1.0 for mid in ranked_ids}
    seen = {1, 5}

    recs_5 = generate_user_top_k(1, ranked_ids, scores_map, seen, k=5)
    recs_10 = generate_user_top_k(1, ranked_ids, scores_map, seen, k=10)
    recs_20 = generate_user_top_k(1, ranked_ids, scores_map, seen, k=20)

    ids_5 = [r.movie_id for r in recs_5]
    ids_10 = [r.movie_id for r in recs_10]
    ids_20 = [r.movie_id for r in recs_20]

    assert ids_10[:5] == ids_5
    assert ids_20[:10] == ids_10
    assert len(ids_5) == 5
    assert len(ids_10) == 10
    assert len(ids_20) == 20


def test_21_independent_reference_implementation_comparison():
    """Case 21: Compares production ranking against a separate naive Python reference implementation."""
    raw_triplets = [
        (1, 101, 5.0),
        (2, 101, 4.0),
        (3, 101, 4.5),
        (1, 102, 3.0),
        (2, 102, 3.5),
        (1, 103, 5.0),
    ]

    # Naive reference implementation
    counts: Dict[int, int] = {}
    rating_sums: Dict[int, float] = {}
    for _, mid, r in raw_triplets:
        counts[mid] = counts.get(mid, 0) + 1
        rating_sums[mid] = rating_sums.get(mid, 0.0) + r

    movie_stats_ref = [
        (mid, counts[mid], rating_sums[mid] / counts[mid])
        for mid in counts
    ]
    global_mean_ref = sum(r for _, _, r in raw_triplets) / len(raw_triplets)

    # Reference weighted score
    m = 5.0
    ref_weighted_ranked = sorted(
        movie_stats_ref,
        key=lambda x: (
            -(x[1] * x[2] + m * global_mean_ref) / (x[1] + m),
            -x[1],
            x[0],
        ),
    )

    # Production implementation
    recommender = PopularityRecommender(m=m).fit_from_stats(movie_stats_ref, global_mean_ref)

    assert [r.movie_id for r in recommender.weighted_ranked_records] == [x[0] for x in ref_weighted_ranked]


def test_22_parameter_m_limiting_behavior():
    """Case 22: Tests m -> 0 (raw average) vs m -> infinity (collapses to global mean)."""
    # Movie 1: v=1, R=5.0
    # Movie 2: v=100, R=4.0
    stats = [(1, 1, 5.0), (2, 100, 4.0)]
    global_mean = 3.0

    # If m = 0: Movie 1 has score 5.0, Movie 2 has score 4.0 -> Movie 1 wins
    rec_m0 = PopularityRecommender(m=0.0).fit_from_stats(stats, global_mean)
    assert rec_m0.weighted_ranked_records[0].movie_id == 1

    # If m = 1000: Movie 2 (100 ratings) has score pulled much less than Movie 1 (1 rating)
    # Movie 1 score: (1*5 + 3000) / 1001 = 3005 / 1001 = 3.00199
    # Movie 2 score: (100*4 + 3000) / 1100 = 3400 / 1100 = 3.09090 -> Movie 2 wins
    rec_m1000 = PopularityRecommender(m=1000.0).fit_from_stats(stats, global_mean)
    assert rec_m1000.weighted_ranked_records[0].movie_id == 2
