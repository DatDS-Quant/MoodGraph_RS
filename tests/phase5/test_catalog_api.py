"""
Tests for Phase 5 Movie Discovery and Catalog API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_list_genres(client):
    """GET /api/genres returns list of distinct genres."""
    resp = client.get("/api/genres")
    assert resp.status_code == 200
    data = resp.json()
    assert "genres" in data
    assert len(data["genres"]) >= 15
    assert "Action" in data["genres"]
    assert "Drama" in data["genres"]


def test_search_movies_pagination(client):
    """GET /api/movies pagination and defaults."""
    resp = client.get("/api/movies?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10
    assert data["total"] > 60000


def test_search_movies_with_query(client):
    """GET /api/movies with query parameter."""
    resp = client.get("/api/movies?query=Toy Story&page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    titles = [m["title"] for m in data["items"]]
    assert any("Toy Story" in t for t in titles)


def test_search_movies_with_genre(client):
    """GET /api/movies filtered by genre."""
    resp = client.get("/api/movies?genre=Animation&page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert "Animation" in item["genres"]


def test_get_movie_detail_success(client):
    """GET /api/movies/{movie_id} for Toy Story (1)."""
    resp = client.get("/api/movies/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["movieId"] == 1
    assert "Toy Story" in data["title"]
    assert data["clean_title"] == "Toy Story"
    assert data["release_year"] == 1995
    assert "Adventure" in data["genres"]
    assert "links" in data
    assert data["links"]["imdb_url"] is not None
    assert "similar_movies" in data


def test_get_movie_detail_not_found(client):
    """GET /api/movies/{movie_id} for non-existent movie returns 404."""
    resp = client.get("/api/movies/99999999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
