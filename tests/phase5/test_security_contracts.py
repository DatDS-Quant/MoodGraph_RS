"""
Tests for Phase 5 Security, Input Validation, and Health contracts.
"""

import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_endpoint(client):
    """GET /health returns healthy status and metadata."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.5.0-phase5"
    assert data["catalog_movies_count"] > 60000
    assert data["sqlite_wal_enabled"] is True


def test_cache_clear_endpoint(client):
    """POST /api/system/cache/clear executes safely."""
    resp = client.post("/api/system/cache/clear")
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_input_validation_boundaries(client):
    """Verifies that invalid parameters are rejected with 422 Unprocessable Entity."""
    # Invalid page number < 1
    resp = client.get("/api/movies?page=0")
    assert resp.status_code == 422

    # Rating > 5.0
    resp_rating = client.post("/api/interactions/ratings", json={
        "user_id": "test_boundary",
        "movie_id": 1,
        "rating": 6.5,
    })
    assert resp_rating.status_code == 422

    # Rating < 0.5
    resp_rating_low = client.post("/api/interactions/ratings", json={
        "user_id": "test_boundary",
        "movie_id": 1,
        "rating": 0.2,
    })
    assert resp_rating_low.status_code == 422


def test_sql_injection_resilience(client):
    """Verifies parameterized SQL queries prevent SQL injection attacks."""
    malicious_user = "'; DROP TABLE demo_users; --"
    resp = client.post("/api/interactions/watchlist", json={
        "user_id": malicious_user,
        "movie_id": 10,
        "list_type": "watchlist",
    })
    assert resp.status_code == 200

    # Ensure table demo_users still exists and functions normally
    resp_get = client.get(f"/api/interactions/watchlist/{malicious_user}")
    assert resp_get.status_code == 200
    items = resp_get.json()
    assert len(items) == 1
    assert items[0]["movieId"] == 10
