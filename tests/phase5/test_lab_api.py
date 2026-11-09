"""
Tests for Phase 5 Recommendation Lab (Mode B) API endpoints.
Verifies multi-model comparison, overlap analysis, and offline metric provenance.
"""

import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_registered_models(client):
    """GET /api/lab/models returns catalog of models."""
    resp = client.get("/api/lab/models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    model_ids = [m["model_id"] for m in data["models"]]
    assert "als" in model_ids
    assert "kg" in model_ids
    assert "hybrid_rrf" in model_ids
    assert "popularity" in model_ids


def test_lab_compare_models(client):
    """POST /api/lab/compare evaluates models side-by-side."""
    payload = {
        "user_id": 1,
        "models": ["als", "popularity"],
        "top_n": 5,
        "filter_seen": True,
    }
    resp = client.post("/api/lab/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 1
    assert "als" in data["results"]
    assert "popularity" in data["results"]
    assert "pairwise_overlaps" in data
    assert len(data["pairwise_overlaps"]) == 1
    assert "jaccard_similarity" in data["pairwise_overlaps"][0]


def test_get_lab_metrics(client):
    """GET /api/lab/metrics serves verified Phase 4 offline metrics."""
    resp = client.get("/api/lab/metrics?split=validation&metric_group=all")
    assert resp.status_code == 200
    data = resp.json()
    assert data["evaluation_users_count"] == 132
    assert "metrics" in data
    metric_names = [m["metric_name"] for m in data["metrics"]]
    assert "NDCG@10" in metric_names
    assert "HR@10" in metric_names
    assert "Catalog_Coverage@10" in metric_names
    assert "scientific_note" in data


def test_get_lab_metadata(client):
    """GET /api/lab/metadata returns dataset and model dimensions."""
    resp = client.get("/api/lab/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dataset_name"] == "MovieLens 25M (ml-25m)"
    assert data["total_ratings"] == 25000095
    assert data["catalog_size"] == 62423
    assert data["als_model"]["factors_dim"] == 8

