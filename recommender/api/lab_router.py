"""
MoodGraph Phase 5: Recommendation Lab Router (Mode B).
Provides endpoints for quantitative researchers and reviewers:
Model registry, multi-model side-by-side comparison, overlap metrics,
and verified offline benchmark results.
"""

from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query

from recommender.api.dependencies import get_lab_service
from recommender.api.schemas import (
    LabCompareRequest,
    LabCompareResponse,
    LabMetricsResponse,
    RegisteredModelsResponse,
    SystemMetadataResponse,
)
from recommender.services.lab_service import LabService

logger = logging.getLogger("recommender.api.lab_router")

router = APIRouter(prefix="/api/lab", tags=["Mode B - Recommendation Lab"])


@router.get("/models", response_model=RegisteredModelsResponse)
def get_registered_models(
    lab_svc: LabService = Depends(get_lab_service),
) -> RegisteredModelsResponse:
    """Returns the catalog of registered recommendation models and fusion algorithms."""
    res = lab_svc.get_registered_models()
    return RegisteredModelsResponse(**res)


@router.post("/compare", response_model=LabCompareResponse)
def compare_models_side_by_side(
    req: LabCompareRequest,
    lab_svc: LabService = Depends(get_lab_service),
) -> LabCompareResponse:
    """
    Executes multiple recommendation models side-by-side for a given user,
    measures per-model execution latency, and computes pairwise Jaccard and rank correlation.
    """
    res = lab_svc.compare_models(
        user_id=req.user_id,
        models=req.models,
        top_n=req.top_n,
        filter_seen=req.filter_seen,
        rrf_k=req.rrf_k,
        weight_als=req.weight_als,
        weight_kg=req.weight_kg,
    )
    return LabCompareResponse(**res)


@router.get("/metrics", response_model=LabMetricsResponse)
def get_offline_benchmark_metrics(
    split: str = Query("validation", pattern="^(validation|test)$"),
    metric_group: str = Query("all", pattern="^(all|ranking|beyond_accuracy|latency)$"),
    lab_svc: LabService = Depends(get_lab_service),
) -> LabMetricsResponse:
    """
    Serves verified experimental benchmark results from Phase 4 artifacts.
    Preserves scientific honesty regarding KG vs Hybrid performance.
    """
    res = lab_svc.get_benchmark_metrics(split=split, metric_group=metric_group)
    return LabMetricsResponse(**res)


@router.get("/metadata", response_model=SystemMetadataResponse)
def get_system_and_dataset_metadata(
    lab_svc: LabService = Depends(get_lab_service),
) -> SystemMetadataResponse:
    """
    Returns verified system dimensions, MovieLens 25M partition provenance,
    and runtime environment metadata.
    """
    res = lab_svc.get_system_metadata()
    return SystemMetadataResponse(**res)

