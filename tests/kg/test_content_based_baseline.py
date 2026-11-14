"""
Kiểm thử tính đúng đắn và tính độc lập của mô hình Content-Based Baseline.
"""

import pytest
from recommender.kg.content_based_baseline import ContentBasedRecommender
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data


@pytest.fixture
def synthetic_graph():
    graph = InMemoryGraph()
    import_synthetic_data(graph)
    return graph


def test_01_content_based_initialization():
    cbf = ContentBasedRecommender(min_liked_rating=3.5, alpha_genre=0.5, beta_genome=0.5)
    assert cbf.min_liked_rating == 3.5
    assert abs(cbf.alpha_genre - 0.5) < 1e-6
    assert abs(cbf.beta_genome - 0.5) < 1e-6


def test_02_cosine_similarity_edge_cases():
    cbf = ContentBasedRecommender()
    # Vector rỗng
    assert cbf.cosine_similarity({}, {"A": 1.0}) == 0.0
    assert cbf.cosine_similarity({"A": 1.0}, {}) == 0.0

    # Vector không có thuộc tính chung (trực giao)
    assert cbf.cosine_similarity({"A": 1.0}, {"B": 1.0}) == 0.0

    # Vector trùng khít
    assert abs(cbf.cosine_similarity({"A": 2.0, "B": 3.0}, {"A": 2.0, "B": 3.0}) - 1.0) < 1e-6

    # Vector song song khác độ dài
    assert abs(cbf.cosine_similarity({"A": 1.0, "B": 2.0}, {"A": 2.0, "B": 4.0}) - 1.0) < 1e-6


def test_03_recommend_genre_only_synthetic(synthetic_graph):
    cbf = ContentBasedRecommender()
    recs = cbf.recommend(user_id=1, graph=synthetic_graph, top_n=5, mode="genre_only")
    assert isinstance(recs, list)
    assert len(recs) <= 5
    for r in recs:
        assert "movieId" in r
        assert "score" in r
        assert "rank" in r
        assert r["mode"] == "genre_only"


def test_04_recommend_full_mode_seen_filtering(synthetic_graph):
    cbf = ContentBasedRecommender()
    # Lấy lịch sử xem của user 1
    seen = set(synthetic_graph.user_rated_movie.get(1, {}).keys())
    recs = cbf.recommend(user_id=1, graph=synthetic_graph, top_n=10, mode="full")

    # Đảm bảo không có phim nào trong top gợi ý bị trùng với phim đã xem
    for r in recs:
        assert r["movieId"] not in seen


def test_05_cold_user_returns_empty(synthetic_graph):
    cbf = ContentBasedRecommender()
    # User 999999 không có trong đồ thị
    recs = cbf.recommend(user_id=999999, graph=synthetic_graph, top_n=10)
    assert recs == []
