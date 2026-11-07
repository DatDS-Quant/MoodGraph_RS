"""
MoodGraph Phase 5: System & Health Router.
Provides health diagnostics, model status, and cache management endpoints.
"""

from __future__ import annotations

import logging
import os
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from recommender.api.dependencies import get_catalog_service, get_hybrid_engine
from recommender.api.schemas import CacheClearResponse, HealthResponse
from recommender.services.catalog_service import CatalogService

logger = logging.getLogger("recommender.api.system_router")

router = APIRouter(tags=["System & Diagnostics"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    request: Request,
    catalog_svc: CatalogService = Depends(get_catalog_service),
    hybrid_engine=Depends(get_hybrid_engine),
) -> HealthResponse:
    """System health check and component status."""
    catalog_count = catalog_svc.catalog_repo.get_movie_count() if catalog_svc else 0
    als_available = False
    if hybrid_engine and hasattr(hybrid_engine, "als_service"):
        als_available = getattr(hybrid_engine.als_service, "_is_warmed_up", False) or True

    return HealthResponse(
        status="healthy",
        version="0.5.0-phase5",
        models_warmed=bool(hybrid_engine is not None),
        catalog_movies_count=catalog_count,
        als_available=als_available,
        kg_backend="InMemoryGraph",
        sqlite_wal_enabled=True,
    )


@router.post("/api/system/cache/clear", response_model=CacheClearResponse)
def clear_cache(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    token: Optional[str] = Query(None, description="Admin token if passed as query parameter"),
    hybrid_engine=Depends(get_hybrid_engine),
) -> CacheClearResponse:
    """Clears in-memory recommendation cache (guarded by ADMIN_API_KEY when configured)."""
    admin_key = os.getenv("ADMIN_API_KEY")
    if admin_key:
        provided = x_admin_token or token
        if not provided or provided != admin_key:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin authorization failed: Invalid admin token.",
            )

    cleared = 0
    if hybrid_engine and hasattr(hybrid_engine, "cache") and hybrid_engine.cache:
        with hybrid_engine.cache._lock:
            cleared = len(hybrid_engine.cache._cache)
            hybrid_engine.cache._cache.clear()
    return CacheClearResponse(success=True, cleared_entries_count=cleared)

