"""
MoodGraph Phase 5: Recommendation Lab Mathematical Invariants & Edge Case Tests.
Independently verifies:
1. Jaccard similarity correctness across sets.
2. Spearman rank correlation semantics (identical, reversed, permutation, offsets).
3. Undefined cases: empty recommendations, disjoint candidate sets, single common candidate.
4. Robustness: duplicate movie IDs in candidate lists, different Top-N lengths.
5. Strict boundedness: Spearman correlation rho in [-1.0, 1.0] without rank offset distortion.
"""

import pytest
from unittest.mock import MagicMock
from recommender.services.lab_service import LabService


def test_jaccard_identical_rankings():
    """Identical candidate sets must yield Jaccard similarity = 1.0."""
    service = LabService()
    # Mock models returning identical movies
    mock_engine = MagicMock()
    mock_resp = MagicMock()
    mock_items = [
        MagicMock(movieId=1, title="A", hybrid_score=0.9, rank=1, source="M1"),
        MagicMock(movieId=2, title="B", hybrid_score=0.8, rank=2, source="M1"),
        MagicMock(movieId=3, title="C", hybrid_score=0.7, rank=3, source="M1"),
    ]
    mock_resp.recommendations = mock_items
    mock_engine.recommend.return_value = mock_resp
    service.hybrid_engine = mock_engine

    res = service.compare_models(user_id=1, models=["als", "kg"], top_n=3)
    pairwise = res["pairwise_overlaps"][0]
    assert pairwise["jaccard_similarity"] == 1.0
    assert pairwise["common_movies_count"] == 3
    assert pairwise["rank_correlation_spearman"] == 1.0


def test_spearman_reversed_rankings():
    """Exact reversed relative rankings on common items must yield Spearman rho = -1.0."""
    service = LabService()
    service.hybrid_engine = MagicMock()

    # Model A: [1, 2, 3] at ranks 1, 2, 3
    # Model B: [3, 2, 1] at ranks 1, 2, 3
    def mock_rec(user_id, top_n, fusion_strategy, **kwargs):
        resp = MagicMock()
        if fusion_strategy == "als_only":
            mids = [1, 2, 3]
        else:
            mids = [3, 2, 1]
        resp.recommendations = [
            MagicMock(movieId=m, title=f"M_{m}", hybrid_score=1.0 / (idx + 1), rank=idx + 1, source=fusion_strategy)
            for idx, m in enumerate(mids)
        ]
        return resp

    service.hybrid_engine.recommend.side_effect = mock_rec
    res = service.compare_models(user_id=1, models=["als", "kg"], top_n=3)
    pairwise = res["pairwise_overlaps"][0]
    assert pairwise["jaccard_similarity"] == 1.0
    assert pairwise["common_movies_count"] == 3
    assert pairwise["rank_correlation_spearman"] == -1.0


def test_disjoint_candidate_sets():
    """Disjoint candidate sets must yield Jaccard = 0.0, common_count = 0, and Spearman = None."""
    service = LabService()
    service.hybrid_engine = MagicMock()

    def mock_rec(user_id, top_n, fusion_strategy, **kwargs):
        resp = MagicMock()
        mids = [10, 20, 30] if fusion_strategy == "als_only" else [40, 50, 60]
        resp.recommendations = [
            MagicMock(movieId=m, title=f"M_{m}", hybrid_score=1.0, rank=idx + 1, source=fusion_strategy)
            for idx, m in enumerate(mids)
        ]
        return resp

    service.hybrid_engine.recommend.side_effect = mock_rec
    res = service.compare_models(user_id=1, models=["als", "kg"], top_n=3)
    pairwise = res["pairwise_overlaps"][0]
    assert pairwise["jaccard_similarity"] == 0.0
    assert pairwise["common_movies_count"] == 0
    assert pairwise["rank_correlation_spearman"] is None


def test_single_common_candidate():
    """Single common candidate (k=1) has undefined rank correlation and must return None."""
    service = LabService()
    service.hybrid_engine = MagicMock()

    def mock_rec(user_id, top_n, fusion_strategy, **kwargs):
        resp = MagicMock()
        mids = [10, 20, 30] if fusion_strategy == "als_only" else [30, 40, 50]
        resp.recommendations = [
            MagicMock(movieId=m, title=f"M_{m}", hybrid_score=1.0, rank=idx + 1, source=fusion_strategy)
            for idx, m in enumerate(mids)
        ]
        return resp

    service.hybrid_engine.recommend.side_effect = mock_rec
    res = service.compare_models(user_id=1, models=["als", "kg"], top_n=3)
    pairwise = res["pairwise_overlaps"][0]
    assert pairwise["common_movies_count"] == 1
    # 1 common movie out of 5 distinct: 1 / 5 = 0.2
    assert pairwise["jaccard_similarity"] == 0.2
    assert pairwise["rank_correlation_spearman"] is None


def test_empty_recommendation_lists():
    """Empty recommendation lists must yield Jaccard = 0.0 and Spearman = None without throwing."""
    service = LabService()
    service.hybrid_engine = MagicMock()
    mock_resp = MagicMock()
    mock_resp.recommendations = []
    service.hybrid_engine.recommend.return_value = mock_resp

    res = service.compare_models(user_id=999999, models=["als", "kg"], top_n=5)
    pairwise = res["pairwise_overlaps"][0]
    assert pairwise["jaccard_similarity"] == 0.0
    assert pairwise["common_movies_count"] == 0
    assert pairwise["rank_correlation_spearman"] is None


def test_rank_offsets_do_not_distort_correlation():
    """
    Items with rank offsets in different lists (e.g. ranks 1,2 in List A vs 8,9 in List B)
    must evaluate relative to their shared intersection order, avoiding invalid negative overflow.
    """
    service = LabService()
    service.hybrid_engine = MagicMock()

    def mock_rec(user_id, top_n, fusion_strategy, **kwargs):
        resp = MagicMock()
        # In List A: 100, 200, 300 appear at ranks 1, 2, 3
        # In List B: 999, 888, 777, 666, 100, 200, 300 (appear at ranks 5, 6, 7 in the same relative order)
        if fusion_strategy == "als_only":
            mids = [100, 200, 300]
        else:
            mids = [999, 888, 777, 666, 100, 200, 300]
        resp.recommendations = [
            MagicMock(movieId=m, title=f"M_{m}", hybrid_score=1.0, rank=idx + 1, source=fusion_strategy)
            for idx, m in enumerate(mids)
        ]
        return resp

    service.hybrid_engine.recommend.side_effect = mock_rec
    res = service.compare_models(user_id=1, models=["als", "kg"], top_n=7)
    pairwise = res["pairwise_overlaps"][0]
    assert pairwise["common_movies_count"] == 3
    # Same relative order on intersection items must yield rho = +1.0
    assert pairwise["rank_correlation_spearman"] == 1.0


def test_duplicate_movie_ids_deduplication():
    """Duplicate candidate IDs within a model's output must be gracefully deduplicated."""
    service = LabService()
    service.hybrid_engine = MagicMock()

    def mock_rec(user_id, top_n, fusion_strategy, **kwargs):
        resp = MagicMock()
        # List A has duplicates: [10, 20, 10, 30]
        # List B has duplicates: [10, 30, 20, 20]
        if fusion_strategy == "als_only":
            mids = [10, 20, 10, 30]
        else:
            mids = [10, 30, 20, 20]
        resp.recommendations = [
            MagicMock(movieId=m, title=f"M_{m}", hybrid_score=1.0, rank=idx + 1, source=fusion_strategy)
            for idx, m in enumerate(mids)
        ]
        return resp

    service.hybrid_engine.recommend.side_effect = mock_rec
    res = service.compare_models(user_id=1, models=["als", "kg"], top_n=5)
    pairwise = res["pairwise_overlaps"][0]
    assert pairwise["common_movies_count"] == 3
    assert pairwise["jaccard_similarity"] == 1.0
    # In dedup A: 10 (1), 20 (2), 30 (3)
    # In dedup B: 10 (1), 30 (2), 20 (3)
    # d = [0, -1, 1], sum d^2 = 2. rho = 1 - 6*2 / (3*8) = 1 - 0.5 = 0.5
    assert pairwise["rank_correlation_spearman"] == 0.5
