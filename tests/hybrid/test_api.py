"""
Unit tests cho FastAPI Serving Endpoints (Phase 4 Group I).
Sử dụng starlette.testclient.TestClient để kiểm thử đồng bộ toàn bộ REST API.
"""

import pytest
from starlette.testclient import TestClient
from recommender.hybrid.api import app, set_api_service
from recommender.hybrid.engine import HybridRecommenderService
from recommender.hybrid.config import HybridConfig
from recommender.kg.import_graph import InMemoryGraph, import_synthetic_data


class FastMockALSService:
    def recommend(self, user_id, top_n, stage="production", custom_seen=None):
        return [
            {"userId": user_id, "movieId": 101, "raw_score": 4.5, "rank": 1, "title": "Inception"},
            {"userId": user_id, "movieId": 102, "raw_score": 4.0, "rank": 2, "title": "Interstellar"},
        ][:top_n]

    def get_seen_history(self, user_ids, stage="production"):
        return {u: set() for u in user_ids}


@pytest.fixture
def api_client():
    g = InMemoryGraph()
    import_synthetic_data(g)
    mock_service = HybridRecommenderService(
        als_service=FastMockALSService(),
        kg_graph=g,
        config=HybridConfig(cache_enabled=True),
    )
    set_api_service(mock_service)
    client = TestClient(app)
    yield client


def test_01_api_health(api_client):
    """Kiểm tra GET /api/health trả về 200 và trạng thái ok."""
    resp = api_client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "cache_stats" in data
    assert "models_ready" in data


def test_02_api_model_info(api_client):
    """Kiểm tra GET /api/model_info cung cấp metadata mô hình."""
    resp = api_client.get("/api/model_info")
    assert resp.status_code == 200
    data = resp.json()
    assert "hybrid_version" in data
    assert "ALS_R8_REG0.3_ITER10" in data["als_champion"]
    assert "rrf" in data["supported_fusion_strategies"]


def test_03_api_recommendations_hybrid_rrf(api_client):
    """Kiểm tra GET /api/recommendations/{user_id} với RRF."""
    resp = api_client.get("/api/recommendations/1?top_n=5&model=hybrid&fusion=rrf")
    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == 1
    assert "recommendations" in data
    assert "metadata" in data
    assert data["metadata"]["fusion_strategy"] == "rrf"


def test_04_api_recommendations_weighted(api_client):
    """Kiểm tra GET /api/recommendations/{user_id} với Weighted fusion."""
    resp = api_client.get("/api/recommendations/1?top_n=5&model=hybrid&fusion=weighted&w_als=0.7&w_kg=0.3")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["fusion_strategy"] == "weighted"


def test_05_api_recommendations_validation_errors(api_client):
    """Kiểm tra validation bounds của tham số query (top_n <= 0 hoặc > 100)."""
    # top_n = 0
    resp_zero = api_client.get("/api/recommendations/1?top_n=0")
    assert resp_zero.status_code == 422  # Pydantic validation error

    # user_id = 0
    resp_neg_user = api_client.get("/api/recommendations/0")
    assert resp_neg_user.status_code == 422


def test_06_api_cache_clear(api_client):
    """Kiểm tra POST /api/cache/clear làm sạch cache thành công."""
    resp = api_client.post("/api/cache/clear")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_07_api_filter_seen_false_restricted(api_client, monkeypatch):
    """
    Kiểm tra bảo vệ an ninh chẩn đoán:
    1. Yêu cầu filter_seen=False từ client thông thường (không token) phải bị từ chối 403 Forbidden.
    2. Yêu cầu có allow_unfiltered=true nhưng không có token cũng bị từ chối 403 Forbidden.
    3. Yêu cầu có token nhưng quên allow_unfiltered=true bị từ chối 400 Bad Request.
    4. Yêu cầu có token hợp lệ VÀ allow_unfiltered=true được chấp nhận 200 OK.
    """
    monkeypatch.setenv("ADMIN_API_KEY", "diag_admin_key_999")

    # 1. Không có token -> 403
    resp_no_token = api_client.get("/api/recommendations/1?filter_seen=false")
    assert resp_no_token.status_code == 403
    assert "Admin Token" in resp_no_token.json()["detail"]

    # 2. allow_unfiltered=true nhưng không có token -> vẫn 403
    resp_unauth = api_client.get("/api/recommendations/1?filter_seen=false&allow_unfiltered=true")
    assert resp_unauth.status_code == 403

    # 3. Có token nhưng không có allow_unfiltered=true -> 400
    resp_need_flag = api_client.get(
        "/api/recommendations/1?filter_seen=false",
        headers={"X-Admin-Token": "diag_admin_key_999"}
    )
    assert resp_need_flag.status_code == 400
    assert "allow_unfiltered=true" in resp_need_flag.json()["detail"]

    # 4. Có token VÀ có allow_unfiltered=true -> 200 OK
    resp_ok = api_client.get(
        "/api/recommendations/1?filter_seen=false&allow_unfiltered=true",
        headers={"X-Admin-Token": "diag_admin_key_999"}
    )
    assert resp_ok.status_code == 200


def test_08_api_cache_clear_admin_protection(api_client, monkeypatch):
    """Kiểm tra bảo vệ endpoint clear cache khi cấu hình ADMIN_API_KEY."""
    monkeypatch.setenv("ADMIN_API_KEY", "secret_admin_token_123")

    # Không truyền token -> 403 Forbidden
    resp_no_token = api_client.post("/api/cache/clear")
    assert resp_no_token.status_code == 403

    # Sai token -> 403 Forbidden
    resp_wrong = api_client.post("/api/cache/clear", headers={"X-Admin-Token": "wrong_token"})
    assert resp_wrong.status_code == 403

    # Đúng token qua header -> 200 OK
    resp_ok = api_client.post("/api/cache/clear", headers={"X-Admin-Token": "secret_admin_token_123"})
    assert resp_ok.status_code == 200
    assert resp_ok.json()["status"] == "success"


