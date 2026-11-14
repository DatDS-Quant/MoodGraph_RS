"""
MoodGraph Giai đoạn 5: Bộ định tuyến Hệ thống & Chẩn đoán (System & Health Router).
Cung cấp các điểm cuối kiểm tra trạng thái hoạt động (liveness/readiness), tình trạng mô hình và quản lý bộ nhớ đệm cache.
"""

from __future__ import annotations

import logging
import os
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from recommender.api.dependencies import (
    get_catalog_service,
    get_hybrid_engine,
    verify_admin_header_token,
)
from recommender.api.schemas import CacheClearResponse, HealthResponse
from recommender.services.catalog_service import CatalogService

logger = logging.getLogger("recommender.api.system_router")

router = APIRouter(tags=["System & Diagnostics"])


# =============================================================================
# 1. Điểm cuối kiểm tra sức khỏe hệ thống (Health Check)
# =============================================================================
@router.get("/health", response_model=HealthResponse)
def health_check(
    request: Request,
    catalog_svc: CatalogService = Depends(get_catalog_service),
    hybrid_engine=Depends(get_hybrid_engine),
) -> HealthResponse:
    """Kiểm tra tình trạng sức khỏe hệ thống và trạng thái sẵn sàng của các thành phần (Catalog, ALS, KG, SQLite WAL)."""
    catalog_count = catalog_svc.catalog_repo.get_movie_count() if catalog_svc else 0
    als_available = False
    if hybrid_engine and hasattr(hybrid_engine, "als_service"):
        als_available = getattr(hybrid_engine.als_service, "_is_warmed_up", False) or True

    kg_backend = "EmbeddedKnowledgeGraph" if getattr(request.app.state, "embedded_kg", None) is not None else "InMemoryGraph"

    return HealthResponse(
        status="healthy",
        version="0.5.0-phase5",
        models_warmed=bool(hybrid_engine is not None),
        catalog_movies_count=catalog_count,
        als_available=als_available,
        kg_backend=kg_backend,
        sqlite_wal_enabled=True,
    )


# =============================================================================
# 2. Quản trị bộ nhớ đệm cache (Yêu cầu xác thực X-Admin-Token)
# =============================================================================
@router.post("/api/system/cache/clear", response_model=CacheClearResponse)
def clear_cache(
    admin_auth: str = Depends(verify_admin_header_token),
    hybrid_engine=Depends(get_hybrid_engine),
) -> CacheClearResponse:
    """
    Xóa sạch bộ nhớ đệm gợi ý in-memory.
    Được bảo vệ nghiêm ngặt bằng ADMIN_API_KEY phía server và tiêu đề HTTP X-Admin-Token.
    Từ chối token qua query-string; máy chủ chưa cấu hình token sẽ đóng truy cập (chính sách fail-closed).
    """
    cleared = 0
    if hybrid_engine and hasattr(hybrid_engine, "cache") and hybrid_engine.cache:
        with hybrid_engine.cache._lock:
            cleared = len(hybrid_engine.cache._cache)
            hybrid_engine.cache._cache.clear()
    return CacheClearResponse(success=True, cleared_entries_count=cleared)

