"""
Tests for Phase 5 Security, Administrative Authorization, Input Validation, and Health contracts.
Strictly verifies:
1. Missing server-side admin token configuration denies administrative access (fail-closed policy).
2. Missing request header token returns 403 Forbidden.
3. Invalid request token returns 403 Forbidden.
4. Valid X-Admin-Token header authorized.
5. Query-string token is NOT accepted (rejected as missing header).
6. Unauthorized filter_seen=false is strictly denied (403 without header, 400 without allow_unfiltered).
7. Zero secret exposure in error responses or headers.
8. SQL injection resilience and input boundary validations.
"""

import os
import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app

TEST_ADMIN_SECRET = "moodgraph-super-secret-key-2026"


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


def test_cache_clear_missing_server_admin_key_denies_access(client, monkeypatch):
    """When ADMIN_API_KEY is not configured on server, administrative endpoints fail-closed (403)."""
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    resp = client.post("/api/system/cache/clear", headers={"X-Admin-Token": "some_token"})
    assert resp.status_code == 403
    assert "Server administrator token is unconfigured (fail-closed policy)" in resp.json()["detail"]


def test_cache_clear_missing_request_token_returns_403(client, monkeypatch):
    """When ADMIN_API_KEY is set, missing X-Admin-Token header returns 403."""
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_SECRET)
    resp = client.post("/api/system/cache/clear")
    assert resp.status_code == 403
    assert "Missing X-Admin-Token header" in resp.json()["detail"]


def test_cache_clear_invalid_request_token_returns_403(client, monkeypatch):
    """When ADMIN_API_KEY is set, invalid X-Admin-Token header returns 403."""
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_SECRET)
    resp = client.post("/api/system/cache/clear", headers={"X-Admin-Token": "invalid_wrong_token"})
    assert resp.status_code == 403
    assert "Invalid administrator token" in resp.json()["detail"]


def test_cache_clear_query_string_token_not_accepted(client, monkeypatch):
    """Query-string tokens (?token=...) are NOT accepted and must return 403."""
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_SECRET)
    resp = client.post(f"/api/system/cache/clear?token={TEST_ADMIN_SECRET}")
    assert resp.status_code == 403
    assert "Missing X-Admin-Token header" in resp.json()["detail"]


def test_cache_clear_valid_header_token_authorized(client, monkeypatch):
    """Valid X-Admin-Token header successfully clears cache and returns 200."""
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_SECRET)
    resp = client.post("/api/system/cache/clear", headers={"X-Admin-Token": TEST_ADMIN_SECRET})
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_filter_seen_false_security_matrix(client, monkeypatch):
    """Diagnostic filter_seen=false requires valid X-Admin-Token header and allow_unfiltered=true."""
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_SECRET)

    # 1. Without header -> 403 Forbidden
    resp = client.get("/api/recommendations/1?filter_seen=false")
    assert resp.status_code == 403

    # 2. With invalid header -> 403 Forbidden
    resp = client.get("/api/recommendations/1?filter_seen=false", headers={"X-Admin-Token": "wrong"})
    assert resp.status_code == 403

    # 3. With query-string token -> 403 Forbidden (query tokens not accepted)
    resp = client.get(f"/api/recommendations/1?filter_seen=false&admin_token={TEST_ADMIN_SECRET}")
    assert resp.status_code == 403

    # 4. With valid header but missing allow_unfiltered -> 400 Bad Request
    resp = client.get(
        "/api/recommendations/1?filter_seen=false",
        headers={"X-Admin-Token": TEST_ADMIN_SECRET},
    )
    assert resp.status_code == 400
    assert "allow_unfiltered=true" in resp.json()["detail"]

    # 5. With valid header and allow_unfiltered=true -> 200 OK
    resp = client.get(
        "/api/recommendations/1?filter_seen=false&allow_unfiltered=true",
        headers={"X-Admin-Token": TEST_ADMIN_SECRET},
    )
    assert resp.status_code == 200
    assert "recommendations" in resp.json()


def test_filter_seen_fails_closed_when_server_key_missing(client, monkeypatch):
    """When ADMIN_API_KEY is not configured, filter_seen=false fails closed (403)."""
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    resp = client.get(
        "/api/recommendations/1?filter_seen=false&allow_unfiltered=true",
        headers={"X-Admin-Token": "any_token"},
    )
    assert resp.status_code == 403
    assert "Server administrator token is unconfigured (fail-closed policy)" in resp.json()["detail"]


def test_cache_isolation_across_authorization_modes(client, monkeypatch):
    """
    Verifies cache isolation:
    1. Normal seen-filtered request is served.
    2. Authorized diagnostic request (filter_seen=false) bypasses cache and does NOT overwrite or pollute user's filtered cache.
    3. Subsequent normal request still returns filtered recommendations consistently.
    """
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_SECRET)

    # 1. Normal request (filter_seen=True)
    resp_filtered_1 = client.get("/api/recommendations/1?top_n=5")
    assert resp_filtered_1.status_code == 200
    mids_filtered_1 = [r["movieId"] for r in resp_filtered_1.json()["recommendations"]]

    # 2. Diagnostic request (filter_seen=False, allow_unfiltered=True) with admin header
    resp_unfiltered = client.get(
        "/api/recommendations/1?top_n=5&filter_seen=false&allow_unfiltered=true",
        headers={"X-Admin-Token": TEST_ADMIN_SECRET},
    )
    assert resp_unfiltered.status_code == 200
    mids_unfiltered = [r["movieId"] for r in resp_unfiltered.json()["recommendations"]]

    # 3. Subsequent normal request must match original filtered result exactly (not poisoned by unfiltered diagnostic run)
    resp_filtered_2 = client.get("/api/recommendations/1?top_n=5")
    assert resp_filtered_2.status_code == 200
    mids_filtered_2 = [r["movieId"] for r in resp_filtered_2.json()["recommendations"]]
    assert mids_filtered_1 == mids_filtered_2


def test_zero_secret_exposure_in_errors(client, monkeypatch):
    """Secret tokens must NEVER appear in error messages, details, or logs."""
    monkeypatch.setenv("ADMIN_API_KEY", TEST_ADMIN_SECRET)
    resp = client.post("/api/system/cache/clear", headers={"X-Admin-Token": "attempted_guess"})
    content = resp.text
    assert TEST_ADMIN_SECRET not in content
    assert "attempted_guess" not in content


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
