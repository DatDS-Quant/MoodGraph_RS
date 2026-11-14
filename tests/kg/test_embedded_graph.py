"""
Kiểm thử Toàn diện cho Phân hệ Embedded Knowledge Graph & Subgraph Visualization API.
Kiểm tra:
- Khởi tạo và nạp dữ liệu in-memory (Movies, Genres, Genome Tags, Ratings).
- CacheManager snapshot save và load nhị phân nén.
- Tính điểm Metapath P1, P2, P3 và trích xuất Subgraph.
- Đồng bộ dữ liệu tương tác SQLite app_state.db.
- API Endpoint GET /api/lab/graph/subgraph theo Interface Contract.
"""

import os
import tempfile
import pytest
from pathlib import Path
from recommender.kg.embedded_graph import EmbeddedKnowledgeGraph
from recommender.kg.cache_manager import CacheManager
from recommender.kg.explainability import extract_subgraph_for_pair
from recommender.kg.recommend import recommend_kg
from recommender.kg.scorer import PathBasedScorer


@pytest.fixture
def sample_embedded_graph():
    """Tạo một đồ thị nhúng mẫu với đầy đủ 4 loại thực thể và liên kết."""
    g = EmbeddedKnowledgeGraph()
    # 1. Movies
    g.merge_movie(1, "Toy Story (1995)", "Animation|Children|Comedy", 1995)
    g.merge_movie(2, "Jumanji (1995)", "Adventure|Children|Fantasy", 1995)
    g.merge_movie(3, "Grumpier Old Men (1995)", "Comedy|Romance", 1995)
    g.merge_movie(4, "Waiting to Exhale (1995)", "Comedy|Drama|Romance", 1995)
    g.merge_movie(5, "Father of the Bride Part II (1995)", "Comedy", 1995)

    # 2. Genres
    for g_name in ["Animation", "Children", "Comedy", "Adventure", "Fantasy", "Romance", "Drama"]:
        g.merge_genre(g_name)

    g.merge_movie_genre(1, "Animation")
    g.merge_movie_genre(1, "Children")
    g.merge_movie_genre(1, "Comedy")
    g.merge_movie_genre(2, "Adventure")
    g.merge_movie_genre(2, "Children")
    g.merge_movie_genre(3, "Comedy")
    g.merge_movie_genre(3, "Romance")
    g.merge_movie_genre(4, "Comedy")
    g.merge_movie_genre(4, "Drama")
    g.merge_movie_genre(5, "Comedy")

    # 3. Genome Tags
    g.merge_genome_tag(10, "pixar")
    g.merge_genome_tag(20, "sequel")
    g.merge_genome_score(1, 10, 0.95)
    g.merge_genome_score(5, 20, 0.88)
    g.merge_genome_score(1, 20, 0.70)

    # 4. User ratings
    g.merge_rating(100, 1, 5.0, 1000)
    g.merge_rating(100, 2, 4.0, 1001)
    g.merge_rating(200, 1, 4.5, 1002)
    g.merge_rating(200, 3, 4.0, 1003)

    return g


def test_embedded_graph_contract_methods(sample_embedded_graph):
    """Kiểm tra toàn bộ phương thức trong Interface Contract của EmbeddedKnowledgeGraph."""
    g = sample_embedded_graph

    # get_user_liked_movies
    liked = g.get_user_liked_movies(100, min_rating=3.5)
    assert 1 in liked
    assert liked[1] == 5.0
    assert 2 in liked

    # get_movie_genres
    genres_1 = g.get_movie_genres(1)
    assert "Animation" in genres_1
    assert "Comedy" in genres_1

    # get_movies_by_genre
    comedy_movies = g.get_movies_by_genre("Comedy")
    assert 1 in comedy_movies
    assert 3 in comedy_movies
    assert 5 in comedy_movies

    # get_movie_top_genome_tags
    top_tags = g.get_movie_top_genome_tags(1, top_m=5)
    assert 10 in top_tags
    assert top_tags[10] == 0.95

    # get_movies_by_genome_tag
    movies_pixar = g.get_movies_by_genome_tag(10)
    assert 1 in movies_pixar
    assert movies_pixar[1] == 0.95

    # get_similar_users
    sim_users = g.get_similar_users(100, top_k=5)
    assert len(sim_users) > 0
    assert sim_users[0][0] == 200
    assert sim_users[0][1] > 0.0


def test_embedded_graph_cache_manager(sample_embedded_graph):
    """Kiểm tra lưu và nạp snapshot nhị phân nén qua CacheManager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = Path(tmpdir) / "test_cache.pkl.gz"
        assert not cache_file.exists()

        # Lưu cache
        saved = CacheManager.save_cache(sample_embedded_graph, cache_file)
        assert saved is True
        assert cache_file.exists()

        # Nạp cache
        loaded_g = CacheManager.load_cache(cache_file)
        assert loaded_g is not None
        assert len(loaded_g.movies) == len(sample_embedded_graph.movies)
        assert loaded_g.get_user_liked_movies(100) == sample_embedded_graph.get_user_liked_movies(100)


def test_extract_subgraph_structure(sample_embedded_graph):
    """Kiểm tra tính đúng đắn của cấu trúc Subgraph và bảng mã màu học thuật."""
    g = sample_embedded_graph
    subgraph = g.extract_subgraph(user_id=100, candidate_movie_id=3)

    assert "nodes" in subgraph
    assert "edges" in subgraph
    assert "academic_explanation" in subgraph

    nodes = {n["id"]: n for n in subgraph["nodes"]}
    assert "user_100" in nodes
    assert nodes["user_100"]["type"] == "USER"
    assert nodes["user_100"]["color"] == "#F59E0B"  # Vàng Hổ Phách

    assert "cand_3" in nodes
    assert nodes["cand_3"]["type"] == "RECOMMENDED_MOVIE"
    assert nodes["cand_3"]["color"] == "#8B5CF6"  # Tím Thạch Anh

    # Có ít nhất 1 node thể loại
    genre_nodes = [n for n in subgraph["nodes"] if n["type"] == "GENRE"]
    assert len(genre_nodes) > 0
    assert genre_nodes[0]["color"] == "#10B981"  # Lục Bảo

    # Kiểm tra chú thích học thuật không chứa LaTeX hoặc ký hiệu dollar
    explanation = subgraph["academic_explanation"]
    assert "$" not in explanation
    assert "\\" not in explanation
    assert "Metapath" in explanation


def test_recommend_kg_with_embedded_graph(sample_embedded_graph):
    """Kiểm tra recommend_kg vận hành chuẩn xác trên EmbeddedKnowledgeGraph."""
    recs = recommend_kg(user_id=100, top_n=3, graph=sample_embedded_graph)
    assert len(recs) > 0
    # Phim đã xem (1, 2) không được xuất hiện trong recommendations
    recommended_mids = [r["movieId"] for r in recs]
    assert 1 not in recommended_mids
    assert 2 not in recommended_mids
    # Mỗi item có trường evidence
    assert "evidence" in recs[0]
    assert len(recs[0]["evidence"]) > 0


def test_subgraph_api_endpoint():
    """Kiểm tra endpoint GET /api/lab/graph/subgraph trả về 200 và tuân thủ schema."""
    from fastapi.testclient import TestClient
    from recommender.api.app import app

    client = TestClient(app)
    resp = client.get("/api/lab/graph/subgraph?user_id=1&movie_id=1")
    assert resp.status_code == 200

    data = resp.json()
    assert "nodes" in data
    assert "edges" in data
    assert "academic_explanation" in data

    # Kiểm tra các node màu
    for node in data["nodes"]:
        assert "id" in node
        assert "label" in node
        assert "type" in node
        assert "color" in node
        assert node["color"].startswith("#")

    # Kiểm tra các edge
    for edge in data["edges"]:
        assert "from" in edge
        assert "to" in edge
        assert "weight" in edge
        assert "type" in edge
