"""
Tests for Phase 5 User Profile and Train History API endpoints.
Verifies Zero-Leakage Guarantee and strict split isolation.
"""

import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_list_sample_users(client):
    """GET /api/users returns curated sample users."""
    resp = client.get("/api/users?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10
    user_1 = next((u for u in data["items"] if u["userId"] == 1), None)
    assert user_1 is not None
    assert user_1["train_ratings_count"] > 0


def test_get_user_profile_user_1(client):
    """GET /api/users/1/profile returns aggregated profile from Train split."""
    resp = client.get("/api/users/1/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == 1
    assert data["ratings_count"] == 68  # User 1 has 68 ratings in Train CSR
    assert data["mean_rating"] > 0.0
    assert isinstance(data["top_favorite_genres"], list)
    assert data["activity_level"] in ("highly_active", "moderate", "casual")


def test_get_user_history_pagination(client):
    """GET /api/users/1/history returns paginated ratings with titles."""
    resp = client.get("/api/users/1/history?page=1&page_size=15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == 1
    assert data["total_rated"] == 68
    assert len(data["items"]) == 15
    for item in data["items"]:
        assert "movieId" in item
        assert "title" in item
        assert "rating" in item
        assert 0.5 <= item["rating"] <= 5.0


def test_user_history_zero_leakage(client):
    """
    Verifies that the movies returned in User 1's history are strictly
    from the Train partition.
    """
    resp = client.get("/api/users/1/history?page=1&page_size=100")
    assert resp.status_code == 200
    data = resp.json()
    returned_movie_ids = {item["movieId"] for item in data["items"]}

    # Read CSR index directly to verify exact match
    from recommender.storage import get_user_history_repository
    history_repo = get_user_history_repository()
    expected_train_seen = history_repo.get_user_seen_movie_ids(1)

    assert returned_movie_ids == expected_train_seen
