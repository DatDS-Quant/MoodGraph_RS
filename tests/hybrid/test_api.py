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
