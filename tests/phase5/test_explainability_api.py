"""
Tests for Phase 5 Recommendation Explainability API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_recommendation_explanation(client):
    """GET /api/explanations/{user_id}/{movie_id} returns structural explanations."""
    resp = client.get("/api/explanations/1/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == 1
    assert data["movieId"] == 1
    assert "Toy Story" in data["movie_title"]
    assert data["overall_recommendation_source"] in ("BOTH", "ALS", "KG")
    assert len(data["graph_explanations"]) >= 1
    assert "summary_text" in data
    # Check that at least one metapath is present
    metapaths = [e["metapath"] for e in data["graph_explanations"]]
    assert any("P" in m for m in metapaths)
