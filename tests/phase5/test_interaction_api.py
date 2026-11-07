"""
Tests for Phase 5 User Interaction and SQLite persistence endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_watchlist_workflow(client):
    """Save to watchlist, list, and delete."""
    user_id = "test_user_phase5"
    movie_id = 1

    # 1. Save movie
    resp = client.post("/api/interactions/watchlist", json={
        "user_id": user_id,
        "movie_id": movie_id,
        "list_type": "watchlist",
    })
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # 2. List saved movies
    resp_list = client.get(f"/api/interactions/watchlist/{user_id}?list_type=watchlist")
    assert resp_list.status_code == 200
    items = resp_list.json()
    assert any(it["movieId"] == movie_id for it in items)

    # 3. Remove movie
    resp_del = client.delete(f"/api/interactions/watchlist?user_id={user_id}&movie_id={movie_id}&list_type=watchlist")
    assert resp_del.status_code == 200
    assert resp_del.json()["success"] is True

    # 4. Verify removed
    resp_list2 = client.get(f"/api/interactions/watchlist/{user_id}?list_type=watchlist")
    assert not any(it["movieId"] == movie_id for it in resp_list2.json())


def test_user_ratings_workflow(client):
    """Submit rating and retrieve."""
    user_id = "test_user_ratings"
    movie_id = 260  # Star Wars: Episode IV

    resp = client.post("/api/interactions/ratings", json={
        "user_id": user_id,
        "movie_id": movie_id,
        "rating": 4.5,
        "feedback_text": "Classic space opera masterpiece!",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["rating"] == 4.5

    # Retrieve ratings
    resp_get = client.get(f"/api/interactions/ratings/{user_id}")
    assert resp_get.status_code == 200
    ratings = resp_get.json()
    assert len(ratings) >= 1
    assert ratings[0]["movieId"] == movie_id
    assert ratings[0]["rating"] == 4.5


def test_user_preferences_workflow(client):
    """Save preferences and retrieve."""
    user_id = "test_user_pref"
    payload = {
        "user_id": user_id,
        "genres": ["Sci-Fi", "Action", "Thriller"],
        "moods": ["mind-bending", "exciting"],
        "min_year": 1980,
        "max_year": 2024,
    }
    resp = client.post("/api/interactions/preferences", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    # Retrieve preferences
    resp_get = client.get(f"/api/interactions/preferences/{user_id}")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert "Sci-Fi" in data["genres"]
    assert data["min_year"] == 1980
