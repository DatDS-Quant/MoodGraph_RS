"""
Unit and Adversarial Test Suite for Module M06: ALS Candidate Generation & Exact Top-N.

Covers:
- Layer A: Mathematical correctness (Oracle matching, dot product, deterministic tie-breaking).
- Layer B: Seen-item filtering (highest-score seen, fewer than K unseen, all seen, zero seen).
- Layer C: Adversarial & stress cases (heavy user with 32,200 items, negative/zero scores, boundary ties).
- Layer D: Scientific invariants & contract guards (cold users, unscoreable items, NaN/Inf guards, rank mismatch).
- Layer E: Oversampling counterexample (proves naive top-K oversampling fails where exact filter-before-top-K succeeds).
- Layer F: Batch processing integrity (batch vs single consistency, batch boundary transitions, no duplicates).
- Layer G: Integration with TopNEvaluator (M02) and Parquet serialization round-trip.
"""

import math
import tempfile
from pathlib import Path
from typing import Dict, List, Set, Tuple

import numpy as np
import pyarrow.parquet as pq
import pytest

from recommender.als.candidates import (
    ALSCandidateConfig,
    ALSCandidateGenerator,
    ScoreableCatalog,
    UserFactorsContainer,
    exact_top_k_oracle,
    fast_exact_top_k_from_scores,
)
from recommender.als.evaluator import HeldOutTarget, TopNEvaluator


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_catalog() -> ScoreableCatalog:
    """Create a controlled synthetic catalog with 20 items in 4 dimensions."""
    np.random.seed(42)
    mids = np.array([101, 102, 103, 104, 105, 106, 107, 108, 109, 110,
                     201, 202, 203, 204, 205, 206, 207, 208, 209, 210], dtype=np.int64)
    factors = np.random.randn(20, 4).astype(np.float32)
    full_catalog_ids = set(mids) | {991, 992, 993}  # 3 unscoreable movies
    return ScoreableCatalog(
        movie_ids=mids,
        factors=factors,
        catalog_movie_ids=full_catalog_ids,
    )


@pytest.fixture
def synthetic_users() -> UserFactorsContainer:
    """Create a controlled synthetic user container with 5 users in 4 dimensions."""
    np.random.seed(42)
    uids = np.array([1, 2, 3, 4, 5], dtype=np.int64)
    factors = np.random.randn(5, 4).astype(np.float32)
    return UserFactorsContainer(user_ids=uids, factors=factors)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_01_exact_top_k_oracle_random_data():
    """Verify that fast_exact_top_k matches exact_top_k_oracle across random floats and IDs."""
    np.random.seed(123)
    rank = 8
    m = 500
    user_factor = np.random.randn(rank).astype(np.float32)
    item_factors = np.random.randn(m, rank).astype(np.float32)
    movie_ids = np.arange(1000, 1000 + m, dtype=np.int64)
    seen_ids = set(np.random.choice(movie_ids, size=100, replace=False))

    k = 15
    oracle_res = exact_top_k_oracle(user_factor, item_factors, movie_ids, seen_ids, k)

    # Compute scores and mask seen items
    scores = np.dot(item_factors, user_factor)
    for idx, mid in enumerate(movie_ids):
        if mid in seen_ids:
            scores[idx] = -np.inf

    fast_res = fast_exact_top_k_from_scores(scores, movie_ids, k)

    assert len(fast_res) == k
    assert len(oracle_res) == k
    for i in range(k):
        assert fast_res[i][0] == oracle_res[i][0], f"ID mismatch at rank {i+1}"
        assert pytest.approx(fast_res[i][1], rel=1e-5) == oracle_res[i][1]


def test_02_seen_item_filtering_highest_score(synthetic_catalog, synthetic_users):
    """If user's seen set includes the #1 highest scoring movie, it MUST NOT appear in Top-K."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    # Get raw unmasked recommendations
    raw_recs = generator.recommend_user(user_id=1, seen_movie_ids=set(), k=5)
    highest_mid = raw_recs[0][0]

    # Filter with highest item in seen
    filtered_recs = generator.recommend_user(user_id=1, seen_movie_ids={highest_mid}, k=5)
    recommended_ids = [mid for mid, _ in filtered_recs]

    assert highest_mid not in recommended_ids
    assert len(filtered_recs) == 5
    assert filtered_recs[0][0] == raw_recs[1][0]  # The second item becomes rank 1


def test_03_all_seen_except_k_items(synthetic_catalog, synthetic_users):
    """User has seen all candidate movies except exactly K; generator returns exactly those K."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    k = 4
    unseen_target_ids = {101, 105, 202, 208}
    all_movie_ids = set(synthetic_catalog.movie_ids)
    seen_ids = all_movie_ids - unseen_target_ids

    recs = generator.recommend_user(user_id=2, seen_movie_ids=seen_ids, k=k)
    recommended_ids = {mid for mid, _ in recs}

    assert len(recs) == k
    assert recommended_ids == unseen_target_ids


def test_04_user_with_fewer_than_k_unseen_items(synthetic_catalog, synthetic_users):
    """User has seen all items except 2; requesting K=5 returns exactly 2 items without error or padding."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    unseen_target_ids = {103, 205}
    all_movie_ids = set(synthetic_catalog.movie_ids)
    seen_ids = all_movie_ids - unseen_target_ids

    recs = generator.recommend_user(user_id=3, seen_movie_ids=seen_ids, k=5)

    assert len(recs) == 2
    assert {mid for mid, _ in recs} == unseen_target_ids
    for mid, sc in recs:
        assert math.isfinite(sc)
        assert sc > -np.inf


def test_05_user_with_all_items_seen(synthetic_catalog, synthetic_users):
    """User has seen every scorable item in catalog; returns empty list []."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    all_seen = set(synthetic_catalog.movie_ids)
    recs = generator.recommend_user(user_id=4, seen_movie_ids=all_seen, k=10)

    assert recs == []


def test_06_user_with_zero_seen_items(synthetic_catalog, synthetic_users):
    """User with no prior seen items receives full Top-K based strictly on dot product."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    recs = generator.recommend_user(user_id=5, seen_movie_ids=set(), k=5)
    assert len(recs) == 5
    # Verify scores are strictly descending
    for i in range(len(recs) - 1):
        assert recs[i][1] >= recs[i+1][1]


def test_07_heavy_user_seen_filtering():
    """Heavy user with 32,200 seen items out of 58,932 items in synthetic setup."""
    np.random.seed(99)
    m = 58932
    movie_ids = np.arange(1, m + 1, dtype=np.int64)
    item_factors = np.random.randn(m, 16).astype(np.float32)

    user_factor = np.random.randn(16).astype(np.float32)
    # 32,200 seen items
    seen_indices = np.random.choice(m, size=32200, replace=False)
    seen_ids = set(movie_ids[seen_indices])

    catalog = ScoreableCatalog(movie_ids=movie_ids, factors=item_factors)
    container = UserFactorsContainer(
        user_ids=np.array([999], dtype=np.int64),
        factors=user_factor[np.newaxis, :],
    )

    generator = ALSCandidateGenerator()
    generator.catalog = catalog
    generator.user_factors = container

    recs = generator.recommend_user(user_id=999, seen_movie_ids=seen_ids, k=20)

    assert len(recs) == 20
    rec_ids = {mid for mid, _ in recs}
    # Invariant: 0 seen items leaked
    assert len(rec_ids.intersection(seen_ids)) == 0
    # Invariant: unique IDs
    assert len(rec_ids) == 20


def test_08_straddling_tie_break_movie_id_asc():
    """Verify deterministic tie-breaking: identical scores resolved by movieId ASC."""
    # 6 items all with identical score 3.0, IDs out of order
    movie_ids = np.array([500, 200, 400, 100, 300, 600], dtype=np.int64)
    scores = np.array([3.0, 3.0, 3.0, 3.0, 3.0, 3.0], dtype=np.float32)

    # Request Top-3
    top_3 = fast_exact_top_k_from_scores(scores, movie_ids, k=3)
    assert len(top_3) == 3
    # Must be 100, 200, 300
    assert [mid for mid, _ in top_3] == [100, 200, 300]


def test_09_negative_and_zero_als_scores():
    """Ensure finite negative and zero scores are preserved and sorted correctly above -inf."""
    movie_ids = np.array([1, 2, 3, 4], dtype=np.int64)
    # item 2 is seen (-inf), items 1, 3, 4 have negative/zero scores
    scores = np.array([-2.5, -np.inf, 0.0, -1.0], dtype=np.float32)

    recs = fast_exact_top_k_from_scores(scores, movie_ids, k=3)
    assert len(recs) == 3
    # Order: 0.0 (mid 3), -1.0 (mid 4), -2.5 (mid 1)
    assert [mid for mid, _ in recs] == [3, 4, 1]
    assert recs[0][1] == 0.0
    assert recs[1][1] == -1.0
    assert recs[2][1] == -2.5


def test_10_cold_user_no_factor(synthetic_catalog, synthetic_users):
    """User not present in user_factors returns empty list [] without raising error."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    cold_uid = 999999
    recs = generator.recommend_user(user_id=cold_uid, seen_movie_ids=set(), k=10)
    assert recs == []


def test_11_unscoreable_item_catalog_audit(synthetic_catalog):
    """Unscoreable items are audited properly and cannot be scored or recommended."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog

    audit = generator.audit_catalog()
    assert audit["full_catalog_size"] == 23
    assert audit["scorable_catalog_size"] == 20
    assert audit["unscoreable_catalog_size"] == 3
    assert pytest.approx(audit["scorable_coverage_percent"], rel=1e-3) == (20 / 23) * 100.0


def test_12_oversampling_counterexample_failure():
    """
    Counterexample proving that naive oversampling 'recommend(K) -> remove seen'
    FAILS where exact filter-before-top-K succeeds.
    """
    # 10 items with scores 10 down to 1
    movie_ids = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=np.int64)
    scores = np.array([10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], dtype=np.float32)

    # User has seen the top 5 movies (items 1, 2, 3, 4, 5)
    seen_ids = {1, 2, 3, 4, 5}
    k = 5

    # Flawed naive oversampling: take raw top-5 without filtering, then filter seen
    naive_top_5 = [mid for mid in movie_ids[:k]]
    naive_filtered = [mid for mid in naive_top_5 if mid not in seen_ids]
    # Naive method returns EMPTY list (0 items)!
    assert len(naive_filtered) == 0

    # Exact method: filter first, then take top-5
    masked_scores = scores.copy()
    for idx, mid in enumerate(movie_ids):
        if mid in seen_ids:
            masked_scores[idx] = -np.inf

    exact_recs = fast_exact_top_k_from_scores(masked_scores, movie_ids, k=k)
    assert len(exact_recs) == 5
    # Exact method correctly returns items 6, 7, 8, 9, 10
    assert [mid for mid, _ in exact_recs] == [6, 7, 8, 9, 10]


def test_13_batch_vs_single_user_consistency(synthetic_catalog, synthetic_users):
    """Verify that a user receives 100% identical recommendations in batch mode vs single user mode."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    user_histories = {
        1: {101, 102},
        2: {103, 104, 205},
        3: set(),
        4: {201, 202, 203, 204},
        5: {105},
    }

    # Batch generation
    batch_res = generator.recommend_batch([1, 2, 3, 4, 5], user_histories, k=5)

    # Single user generation
    for uid in [1, 2, 3, 4, 5]:
        single_res = generator.recommend_user(uid, user_histories[uid], k=5)
        assert len(single_res) == len(batch_res[uid])
        for r_idx in range(len(single_res)):
            assert single_res[r_idx][0] == batch_res[uid][r_idx][0]
            assert pytest.approx(single_res[r_idx][1], rel=1e-5) == batch_res[uid][r_idx][1]


def test_14_batch_boundary_integrity(synthetic_catalog, synthetic_users):
    """Verify that batch size boundaries (e.g. batch_size=2) do not lose or alter users."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    user_histories = {uid: {101} for uid in [1, 2, 3, 4, 5]}

    # Run full generation with batch_size=2 (creates 3 batches: [1,2], [3,4], [5])
    recs_batched = generator.generate_recommendations(
        target_user_ids=[1, 2, 3, 4, 5],
        user_histories=user_histories,
        k=5,
        batch_size=2,
        show_progress=False,
    )

    assert len(recs_batched) == 5
    assert set(recs_batched.keys()) == {1, 2, 3, 4, 5}
    for uid in [1, 2, 3, 4, 5]:
        assert len(recs_batched[uid]) == 5
        # Verify no seen item leaked
        rec_ids = [mid for mid, _ in recs_batched[uid]]
        assert 101 not in rec_ids


def test_15_duplicate_seen_inputs_deduplication(synthetic_catalog, synthetic_users):
    """Seen item set containing duplicate IDs or non-catalog IDs is handled cleanly."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    # Seen includes duplicate 101, and non-catalog ID 99999
    seen_set = {101, 101, 99999}
    recs = generator.recommend_user(user_id=1, seen_movie_ids=seen_set, k=5)
    rec_ids = [mid for mid, _ in recs]

    assert 101 not in rec_ids
    assert len(rec_ids) == 5


def test_16_duplicate_ids_or_nan_guard():
    """ScoreableCatalog and UserFactorsContainer reject NaN/Inf and duplicate IDs."""
    mids_duplicate = np.array([101, 101], dtype=np.int64)
    factors_ok = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    with pytest.raises(ValueError, match="Duplicate movieId"):
        ScoreableCatalog(movie_ids=mids_duplicate, factors=factors_ok)

    mids_ok = np.array([101, 102], dtype=np.int64)
    factors_nan = np.array([[1.0, np.nan], [3.0, 4.0]], dtype=np.float32)

    with pytest.raises(ValueError, match="NaN or Inf"):
        ScoreableCatalog(movie_ids=mids_ok, factors=factors_nan)

    uids_duplicate = np.array([1, 1], dtype=np.int64)
    with pytest.raises(ValueError, match="Duplicate userId"):
        UserFactorsContainer(user_ids=uids_duplicate, factors=factors_ok)


def test_17_rank_mismatch_guard():
    """Rank mismatch between user and item factors raises ValueError."""
    catalog = ScoreableCatalog(
        movie_ids=np.array([101], dtype=np.int64),
        factors=np.array([[1.0, 2.0, 3.0]], dtype=np.float32),  # rank 3
    )
    users = UserFactorsContainer(
        user_ids=np.array([1], dtype=np.int64),
        factors=np.array([[1.0, 2.0]], dtype=np.float32),  # rank 2
    )

    generator = ALSCandidateGenerator()
    generator.catalog = catalog
    generator.user_factors = users

    with pytest.raises(ValueError):
        generator.recommend_user(user_id=1, seen_movie_ids=set(), k=1)


def test_18_k_validation_guards(synthetic_catalog, synthetic_users):
    """k <= 0 or invalid k raises ValueError."""
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    with pytest.raises(ValueError):
        generator.recommend_user(user_id=1, k=0)

    with pytest.raises(ValueError):
        generator.recommend_user(user_id=1, k=-5)


def test_19_arrow_table_export_and_parquet_serialization(synthetic_catalog, synthetic_users):
    """Verify conversion to Arrow Table, schema validity, and Parquet save/load."""
    generator = ALSCandidateGenerator(ALSCandidateConfig(candidate_source="ALS", model_version="m05_test"))
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    recs = generator.generate_recommendations(
        target_user_ids=[1, 2],
        user_histories={1: set(), 2: {101}},
        k=5,
        show_progress=False,
    )

    tbl = generator.export_recommendations_dataframe(recs)
    assert tbl.num_rows == 10
    assert tbl.schema.names == ["userId", "movieId", "rank", "als_score", "candidate_source", "model_version"]

    with tempfile.TemporaryDirectory() as tmp_dir:
        pq_path = Path(tmp_dir) / "test_recs.parquet"
        generator.save_recommendations_parquet(recs, pq_path)
        assert pq_path.exists()

        reloaded_tbl = pq.read_table(pq_path)
        assert reloaded_tbl.num_rows == 10
        df = reloaded_tbl.to_pandas()
        assert list(df["userId"].unique()) == [1, 2]
        assert list(df[df["userId"] == 1]["rank"]) == [1, 2, 3, 4, 5]


def test_20_end_to_end_with_top_n_evaluator(synthetic_catalog, synthetic_users):
    """
    Full integration between ALSCandidateGenerator and TopNEvaluator (M02).
    Verifies metric calculation, NDCG, HitRate, and cohort preservation.
    """
    generator = ALSCandidateGenerator()
    generator.catalog = synthetic_catalog
    generator.user_factors = synthetic_users

    recs = generator.generate_recommendations(
        target_user_ids=[1, 2, 3, 4, 5],
        user_histories={uid: set() for uid in [1, 2, 3, 4, 5]},
        k=10,
        show_progress=False,
    )

    # Pick the rank-1 item for user 1 as their target (guaranteed hit at rank 1)
    target_mid_1 = recs[1][0][0]
    # Pick an item at rank 5 for user 2
    target_mid_2 = recs[2][4][0]
    # Pick a non-existent item for user 3 (guaranteed miss)
    target_mid_3 = 99999
    # Non-positive rating for user 4 (< 3.5)
    target_mid_4 = recs[4][0][0]
    # Cold target for user 5 (unscoreable item 991)
    target_mid_5 = 991

    targets: Dict[int, HeldOutTarget] = {
        1: HeldOutTarget(movie_id=target_mid_1, rating=4.5),  # Hit at rank 1
        2: HeldOutTarget(movie_id=target_mid_2, rating=4.0),  # Hit at rank 5
        3: HeldOutTarget(movie_id=target_mid_3, rating=5.0),  # Miss
        4: HeldOutTarget(movie_id=target_mid_4, rating=2.0),  # Non-positive (excluded from pos cohort)
        5: HeldOutTarget(movie_id=target_mid_5, rating=4.0),  # Positive unscoreable target (Miss)
    }

    evaluator = TopNEvaluator(
        k_list=[5, 10],
        relevance_threshold=3.5,
        catalog_size=23,
        scorable_catalog_size=20,
    )

    # Format recs as Dict[userId, List[movieId]] for evaluator
    eval_recs = {uid: [mid for mid, _ in rec_list] for uid, rec_list in recs.items()}
    summary = evaluator.evaluate(eval_recs, targets)

    s10 = summary[10]
    # Positive cohort size: users 1, 2, 3, 5 = 4 users. (User 4 has rating 2.0 < 3.5)
    assert s10.positive_cohort_size == 4
    assert s10.non_positive_cohort_size == 1
    # Hits: user 1 (rank 1), user 2 (rank 5). Users 3 and 5 missed. Total hits = 2
    assert s10.hit_count == 2
    assert s10.hit_rate == pytest.approx(2.0 / 4.0)  # 0.50

    # NDCG calculation:
    # User 1: 1.0 / log2(1 + 1) = 1.0
    # User 2: 1.0 / log2(5 + 1) = 1.0 / 2.5849625 = 0.3868528
    # User 3: 0.0
    # User 5: 0.0
    expected_ndcg = (1.0 + (1.0 / math.log2(6.0))) / 4.0
    assert s10.ndcg == pytest.approx(expected_ndcg, rel=1e-5)
