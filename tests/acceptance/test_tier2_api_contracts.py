"""
Tầng 2: Tuân thủ Hợp đồng API RESTful (API Contract Compliance).
Kiểm định tự động tất cả các endpoints qua FastAPI TestClient:
- GET /health
- GET /api/recommendations/{user_id} (Mode A & Recommender Engine)
- GET /api/movies & GET /api/movies/{id}
- GET /api/genres
- GET /api/users & GET /api/users/{id}/profile
- POST /api/lab/compare (Mode B Model Confrontation)
- GET /api/lab/graph/subgraph (Interactive Graph Visualizer)
- GET /api/lab/metrics & GET /api/lab/metadata
- GET /api/explanations/{user_id}/{movie_id} (Explainability Evidence)
- GET/POST/DELETE /api/interactions/watchlist
- POST /api/system/cache/clear (Security Fail-Closed)
"""

import pytest
from fastapi.testclient import TestClient
from recommender.api.app import app


@pytest.fixture(scope="module")
def api_client():
    with TestClient(app) as client:
        yield client


class TestTier2APIContracts:
    """Bộ kiểm thử kiểm tra hợp đồng API RESTful và schema dữ liệu."""

    def test_01_health_endpoint_contract(self, api_client):
        """Kiểm tra hợp đồng /health."""
        resp = api_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.5.0-phase5"
        assert data["catalog_movies_count"] >= 62000
        assert data["sqlite_wal_enabled"] is True
        assert data["kg_backend"] in ("EmbeddedKnowledgeGraph", "InMemoryGraph")

    def test_02_recommendations_endpoint_modes(self, api_client):
        """Kiểm tra endpoint /api/recommendations/{user_id} với các chế độ dung hợp."""
        # 1. Chế độ rrf mặc định
        resp_rrf = api_client.get("/api/recommendations/1?top_n=5&strategy=rrf")
        assert resp_rrf.status_code == 200
        data = resp_rrf.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) <= 5
        if data["recommendations"]:
            first_item = data["recommendations"][0]
            assert "movieId" in first_item
            assert "title" in first_item
            assert "hybrid_score" in first_item or "score" in first_item
            assert "rank" in first_item

        # 2. Chế độ weighted
        resp_w = api_client.get("/api/recommendations/1?top_n=5&strategy=weighted")
        assert resp_w.status_code == 200

        # 3. Chế độ als_only
        resp_als = api_client.get("/api/recommendations/1?top_n=5&strategy=als_only")
        assert resp_als.status_code == 200

        # 4. Chế độ kg_only
        resp_kg = api_client.get("/api/recommendations/1?top_n=5&strategy=kg_only")
        assert resp_kg.status_code == 200

    def test_03_recommend_validation_boundaries(self, api_client):
        """Kiểm tra xử lý lỗi khi tham số không hợp lệ (422 Unprocessable Entity)."""
        # top_n âm hoặc bằng 0
        resp_neg_top = api_client.get("/api/recommendations/1?top_n=0")
        assert resp_neg_top.status_code == 422

        # user_id âm
        resp_neg_uid = api_client.get("/api/recommendations/-5?top_n=5")
        assert resp_neg_uid.status_code == 422

    def test_04_movies_catalog_endpoints(self, api_client):
        """Kiểm tra danh mục phim: danh sách tìm kiếm và chi tiết phim."""
        # Danh sách phim
        resp_list = api_client.get("/api/movies?page=1&page_size=5")
        assert resp_list.status_code == 200
        data = resp_list.json()
        assert "items" in data
        assert len(data["items"]) == 5
        assert "movieId" in data["items"][0]
        assert "title" in data["items"][0]

        # Chi tiết phim tồn tại (Toy Story mid=1)
        resp_detail = api_client.get("/api/movies/1")
        assert resp_detail.status_code == 200
        detail = resp_detail.json()
        assert detail["movieId"] == 1
        assert "Toy Story" in detail["title"]

        # Chi tiết phim không tồn tại -> 404
        resp_404 = api_client.get("/api/movies/99999999")
        assert resp_404.status_code == 404

    def test_05_genres_endpoint(self, api_client):
        """Kiểm tra danh sách thể loại phim."""
        resp = api_client.get("/api/genres")
        assert resp.status_code == 200
        data = resp.json()
        assert "genres" in data
        genres = data["genres"]
        assert isinstance(genres, list)
        assert len(genres) >= 18
        assert "Animation" in genres or "Action" in genres

    def test_06_users_profile_endpoints(self, api_client):
        """Kiểm tra danh sách người dùng mẫu và hồ sơ người dùng."""
        # Mẫu users
        resp_users = api_client.get("/api/users?page=1&page_size=10")
        assert resp_users.status_code == 200
        users_data = resp_users.json()
        assert "items" in users_data
        assert len(users_data["items"]) > 0
        assert "userId" in users_data["items"][0]

        # Hồ sơ user 1
        resp_u1 = api_client.get("/api/users/1/profile")
        assert resp_u1.status_code == 200
        u1_data = resp_u1.json()
        assert u1_data["userId"] == 1
        assert "ratings_count" in u1_data

    def test_07_lab_compare_endpoint(self, api_client):
        """Kiểm tra Mode B đối đầu mô hình (POST /api/lab/compare)."""
        payload = {
            "user_id": 1,
            "models": ["als", "kg_only", "hybrid_rrf", "hybrid_weighted", "popularity"],
            "top_n": 5,
        }
        resp = api_client.post("/api/lab/compare", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "pairwise_overlaps" in data
        # Kiểm tra ma trận so sánh
        overlaps = data["pairwise_overlaps"]
        for pair in overlaps:
            assert "model_a" in pair
            assert "model_b" in pair
            assert "jaccard_similarity" in pair
            assert 0.0 <= pair["jaccard_similarity"] <= 1.0

    def test_08_lab_subgraph_endpoint(self, api_client):
        """Kiểm tra endpoint trích xuất đồ thị con tương tác (/api/lab/graph/subgraph)."""
        resp = api_client.get("/api/lab/graph/subgraph?user_id=1&movie_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert "nodes" in data
        assert "edges" in data
        assert "academic_explanation" in data
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0
        first_node = data["nodes"][0]
        assert "id" in first_node
        assert "label" in first_node
        assert "type" in first_node
        assert "color" in first_node

    def test_09_lab_metrics_and_metadata(self, api_client):
        """Kiểm tra endpoint trả về bảng metrics nghiên cứu khoa học."""
        resp_m = api_client.get("/api/lab/metrics?split=validation")
        assert resp_m.status_code == 200
        data = resp_m.json()
        assert "metrics" in data

        resp_meta = api_client.get("/api/lab/metadata")
        assert resp_meta.status_code == 200
        assert "dataset_name" in resp_meta.json()

    def test_10_explainability_endpoint(self, api_client):
        """Kiểm tra endpoint giải thích lý do gợi ý (/api/explanations/{user_id}/{movie_id})."""
        resp = api_client.get("/api/explanations/1/1")
        assert resp.status_code == 200
        data = resp.json()
        assert "userId" in data
        assert "movieId" in data
        assert "graph_explanations" in data

    def test_11_watchlist_lifecycle(self, api_client):
        """Kiểm tra quy trình thêm, xem và xóa khỏi watchlist."""
        # 1. Thêm phim 1 vào watchlist
        payload = {"user_id": "test_user_qa", "movie_id": 1, "list_type": "watchlist"}
        post_resp = api_client.post("/api/interactions/watchlist", json=payload)
        assert post_resp.status_code in (200, 201)

        # 2. Đọc watchlist
        get_resp = api_client.get("/api/interactions/watchlist/test_user_qa?list_type=watchlist")
        assert get_resp.status_code == 200
        items = get_resp.json()
        assert any(it.get("movieId") == 1 for it in items)

        # 3. Xóa phim khỏi watchlist
        del_resp = api_client.delete("/api/interactions/watchlist?user_id=test_user_qa&movie_id=1&list_type=watchlist")
        assert del_resp.status_code == 200

    def test_12_security_fail_closed_cache_clear(self, api_client):
        """Kiểm tra rào chắn bảo mật 403 Forbidden khi thiếu Admin Token."""
        resp = api_client.post("/api/system/cache/clear")
        assert resp.status_code == 403
