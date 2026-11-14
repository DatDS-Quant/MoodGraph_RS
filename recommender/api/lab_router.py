"""
MoodGraph Giai đoạn 5: Bộ định tuyến Phòng thí nghiệm Gợi ý (Recommendation Lab Router - Chế độ Nghiên cứu Mode B).
Cung cấp các điểm cuối phục vụ nghiên cứu định lượng và đánh giá khoa học:
Sổ đăng ký mô hình, so sánh đối đầu đa mô hình song song, chỉ số trùng lặp (Jaccard, Spearman),
và kết quả đo kiểm thực nghiệm benchmark offline đã được xác thực từ Giai đoạn 4.
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
    SubgraphResponse,
)
from recommender.services.lab_service import LabService

logger = logging.getLogger("recommender.api.lab_router")

router = APIRouter(prefix="/api/lab", tags=["Mode B - Recommendation Lab"])


# =============================================================================
# 1. Sổ đăng ký mô hình gợi ý (Model Registry)
# =============================================================================

@router.get("/models", response_model=RegisteredModelsResponse)
def get_registered_models(
    lab_svc: LabService = Depends(get_lab_service),
) -> RegisteredModelsResponse:
    """Trả về danh mục các mô hình gợi ý và các thuật toán kết hợp (fusion strategies) đã đăng ký trong Lab."""
    res = lab_svc.get_registered_models()
    return RegisteredModelsResponse(**res)


# =============================================================================
# 2. So sánh đối đầu đa mô hình (Side-by-Side Model Comparison)
# =============================================================================

@router.post("/compare", response_model=LabCompareResponse)
def compare_models_side_by_side(
    req: LabCompareRequest,
    lab_svc: LabService = Depends(get_lab_service),
) -> LabCompareResponse:
    """
    Thực thi đồng thời nhiều mô hình gợi ý cho cùng một người dùng,
    đo lường độ trễ thực thi của từng mô hình, và tính toán độ tương đồng cặp (Jaccard và tương quan Spearman).
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


# =============================================================================
# 3. Báo cáo đo kiểm thực nghiệm Benchmark Offline từ Giai đoạn 4
# =============================================================================

@router.get("/metrics", response_model=LabMetricsResponse)
def get_offline_benchmark_metrics(
    split: str = Query("validation", pattern="^(validation|test)$"),
    metric_group: str = Query("all", pattern="^(all|ranking|beyond_accuracy|latency)$"),
    lab_svc: LabService = Depends(get_lab_service),
) -> LabMetricsResponse:
    """
    Cung cấp kết quả đo kiểm benchmark thực nghiệm đã được kiểm chứng từ các tệp artifact của Giai đoạn 4.
    Bảo đảm tính trung thực khoa học về hiệu năng tương đối giữa KG, ALS và Hybrid.
    """
    res = lab_svc.get_benchmark_metrics(split=split, metric_group=metric_group)
    return LabMetricsResponse(**res)


# =============================================================================
# 4. Siêu dữ liệu toàn diện về hệ thống và dữ liệu (System & Data Metadata)
# =============================================================================

@router.get("/metadata", response_model=SystemMetadataResponse)
def get_system_and_dataset_metadata(
    lab_svc: LabService = Depends(get_lab_service),
) -> SystemMetadataResponse:
    """
    Trả về các chiều không gian đã xác thực của hệ thống, nguồn gốc phân vùng dữ liệu MovieLens 25M,
    và siêu dữ liệu môi trường runtime.
    """
    res = lab_svc.get_system_metadata()
    return SystemMetadataResponse(**res)


# =============================================================================
# 5. Trích xuất đồ thị con tương tác (Interactive Explainability Subgraph)
# =============================================================================

@router.get("/graph/subgraph", response_model=SubgraphResponse)
def get_graph_subgraph(
    user_id: int = Query(..., ge=1, description="ID người dùng"),
    movie_id: int = Query(..., ge=1, description="ID phim đề xuất"),
    lab_svc: LabService = Depends(get_lab_service),
) -> SubgraphResponse:
    """
    Trích xuất cấu trúc mạng đồ thị con (Interactive Subgraph) giải thích liên kết giữa user và movie,
    phục vụ trực quan hóa tương tác vis-network theo đúng Interface Contract trong PROJECT.md.
    """
    res = lab_svc.get_subgraph(user_id=user_id, movie_id=movie_id)
    return SubgraphResponse(**res)

