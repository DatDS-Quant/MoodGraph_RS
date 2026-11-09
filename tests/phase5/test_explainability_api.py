"""
Tests for Phase 5 Recommendation Explainability API endpoints.
Verifies provenance fields, evidence types, verification statuses, and adversarial edge cases.
"""

import pytest
from fastapi.testclient import TestClient

from recommender.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_recommendation_explanation_provenance(client):
    """GET /api/explanations/{user_id}/{movie_id} returns strictly audited provenance fields."""
    resp = client.get("/api/explanations/1/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == 1
    assert data["movieId"] == 1
    assert "Toy Story" in data["movie_title"]
    assert data["overall_recommendation_source"] in ("BOTH", "ALS", "KG")
    assert len(data["graph_explanations"]) >= 1
    assert "summary_text" in data

    # Verify explicit provenance metadata for every graph explanation
    for expl in data["graph_explanations"]:
        assert "evidence_type" in expl
        assert "verification_status" in expl
        assert "source_model" in expl
        assert expl["evidence_type"] in ("DIRECT_GRAPH_TRAVERSAL", "STRUCTURAL_HEURISTIC")
        assert expl["verification_status"] in ("VERIFIED_GROUND_TRUTH", "HEURISTIC_ESTIMATE")

        assert "is_heuristic" in expl
        assert "provenance" in expl

        if expl["metapath"] == "P1_GENRE":
            assert expl["evidence_type"] == "DIRECT_GRAPH_TRAVERSAL"
            assert expl["verification_status"] == "VERIFIED_GROUND_TRUTH"
            assert expl["source_model"] == "KNOWLEDGE_GRAPH_TRAIN_SUBGRAPH"
            assert expl["is_heuristic"] is False
            assert expl["provenance"] == "verified_train_history_traversal"
            assert expl["score_contribution"] is not None
            assert len(expl["connecting_entities"]) > 0
        elif expl["metapath"] in ("P2_GENOME", "P3_COLLABORATIVE"):
            # If no graph path exists for this catalog item, must be marked heuristic without fabrication
            if expl["is_heuristic"]:
                assert expl["evidence_type"] == "STRUCTURAL_HEURISTIC"
                assert expl["verification_status"] == "HEURISTIC_ESTIMATE"
                assert expl["score_contribution"] is None
                assert expl["connecting_entities"] == []
            else:
                assert expl["evidence_type"] == "DIRECT_GRAPH_TRAVERSAL"
                assert expl["verification_status"] == "VERIFIED_GROUND_TRUTH"
                assert expl["score_contribution"] is not None
                assert len(expl["connecting_entities"]) > 0

    # Verify explicit provenance on latent factor explanation if present
    if data.get("latent_factor_explanation"):
        lf = data["latent_factor_explanation"]
        assert lf["evidence_type"] == "LATENT_FACTOR_AFFINITY"
        assert lf["verification_status"] == "VERIFIED_NUMERICAL_PROJECTION"
        assert lf["source_model"] == "SPARK_ALS_FACTOR_PROJECTION"
        assert isinstance(lf["dot_product_score"], float)


def test_explainability_adversarial_negative_ids(client):
    """Negative user_id or movie_id must be rejected at API boundary with 422 Unprocessable Entity."""
    # Negative user_id
    resp = client.get("/api/explanations/-1/1")
    assert resp.status_code == 422

    # Negative movie_id
    resp = client.get("/api/explanations/1/-5")
    assert resp.status_code == 422

    # Zero user_id
    resp = client.get("/api/explanations/0/1")
    assert resp.status_code == 422


def test_explainability_adversarial_oversized_ids(client):
    """Oversized user_id or movie_id beyond max integer boundary must be rejected with 422."""
    resp = client.get("/api/explanations/99999999/1")
    assert resp.status_code == 422


def test_explainability_adversarial_cold_user(client):
    """Cold user with no interactions in train must not crash with 500 error."""
    resp = client.get("/api/explanations/999999/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["userId"] == 999999
    assert isinstance(data["graph_explanations"], list)
