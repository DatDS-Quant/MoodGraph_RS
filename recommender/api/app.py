"""
MoodGraph Phase 5: Production-Ready FastAPI Application.
Integrates Movie Discovery (Mode A), Recommendation Lab (Mode B),
SQLite state persistence, pre-warmed lifespan loading, and CORS support.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from recommender.api.discovery_router import router as discovery_router
from recommender.api.interaction_router import router as interaction_router
from recommender.api.lab_router import router as lab_router
from recommender.api.system_router import router as system_router
from recommender.services import (
    CatalogService,
    ExplainabilityService,
    LabService,
    UserInteractionService,
    UserProfileService,
)
from recommender.storage import (
    MovieCatalogRepository,
    ResearchMetricsRepository,
    SQLiteStateRepository,
    UserHistoryRepository,
    get_catalog_repository,
    get_research_metrics_repository,
    get_sqlite_state_repository,
    get_user_history_repository,
)

logger = logging.getLogger("recommender.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI Lifespan Manager:
    Pre-warms in-memory movie catalog, train seen CSR index, and hybrid engines
    to eliminate cold-start latency spikes.
    """
    logger.info("Starting MoodGraph Phase 5 API Lifespan Pre-warming...")

    # 1. Pre-warm Movie Catalog (~4.35 MB)
    catalog_repo = get_catalog_repository()
    catalog_repo.ensure_loaded()
    logger.info(f"Movie Catalog pre-warmed: {catalog_repo.get_movie_count()} movies indexed.")

    # 2. Pre-warm User History CSR Index (~50 MB)
    history_repo = get_user_history_repository()
    history_repo.warmup_index()
    logger.info("User History CSR index pre-warmed.")

    # 3. Initialize Metrics and SQLite repositories
    metrics_repo = get_research_metrics_repository()
    sqlite_repo = get_sqlite_state_repository()

    # 4. Initialize Hybrid Engine
    hybrid_engine = None
    try:
        from recommender.hybrid.engine import HybridRecommenderService
        from recommender.hybrid.config import HybridConfig
        config = HybridConfig(cache_enabled=True, cross_score_als=True)
        hybrid_engine = HybridRecommenderService(config=config)
        # Trigger warm-up of internal ALS model if available
        if hasattr(hybrid_engine.als_service, "warmup"):
            hybrid_engine.als_service.warmup()
        logger.info("HybridRecommenderService pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"HybridRecommenderService initialization note: {e}")

    # 4b. Pre-warm Embedded Knowledge Graph snapshot cache (<0.5s)
    embedded_kg = None
    try:
        from recommender.kg.cache_manager import CacheManager
        embedded_kg = CacheManager.get_or_create_graph()
        logger.info(
            f"EmbeddedKnowledgeGraph pre-warmed: {len(embedded_kg.movies)} movies, "
            f"{len(embedded_kg.genres)} genres indexed."
        )
    except Exception as e:
        logger.warning(f"EmbeddedKnowledgeGraph pre-warm note: {e}")

    # 5. Wire Application Services
    catalog_svc = CatalogService(catalog_repo=catalog_repo)
    user_svc = UserProfileService(history_repo=history_repo, catalog_repo=catalog_repo)
    explain_svc = ExplainabilityService(
        catalog_repo=catalog_repo,
        history_repo=history_repo,
        hybrid_engine=hybrid_engine,
    )
    lab_svc = LabService(
        hybrid_engine=hybrid_engine,
        metrics_repo=metrics_repo,
        catalog_repo=catalog_repo,
        sqlite_repo=sqlite_repo,
    )
    interaction_svc = UserInteractionService(
        sqlite_repo=sqlite_repo,
        catalog_repo=catalog_repo,
        hybrid_engine=hybrid_engine,
    )

    # Attach singletons to application state for dependency injection
    app.state.catalog_repo = catalog_repo
    app.state.history_repo = history_repo
    app.state.metrics_repo = metrics_repo
    app.state.sqlite_repo = sqlite_repo
    app.state.hybrid_engine = hybrid_engine
    app.state.embedded_kg = embedded_kg
    app.state.catalog_service = catalog_svc
    app.state.user_profile_service = user_svc
    app.state.explainability_service = explain_svc
    app.state.lab_service = lab_svc
    app.state.interaction_service = interaction_svc

    logger.info("MoodGraph Phase 5 API Lifespan startup completed successfully.")
    yield
    logger.info("MoodGraph Phase 5 API shutting down.")


def create_app() -> FastAPI:
    """Factory function for creating the FastAPI application."""
    application = FastAPI(
        title="MoodGraph Recommender API",
        description=(
            "MoodGraph Big Data Movie Recommendation Platform API. "
            "Supports Mode A (Movie Discovery & Personalization) and "
            "Mode B (Recommendation Lab & Multi-Model Evaluation)."
        ),
        version="0.5.0-phase5",
        lifespan=lifespan,
    )

    # Enable CORS for interactive UI clients
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Vô hiệu hóa cache trình duyệt cho static assets để mọi thay đổi UI phản hồi tức thì
    @application.middleware("http")
    async def add_no_cache_headers(request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/demo") or path.endswith((".js", ".css", ".html")) or path == "/":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # Mount Routers
    application.include_router(system_router)
    application.include_router(discovery_router)
    application.include_router(lab_router)
    application.include_router(interaction_router)

    # Mount Static Web Client (demo/ directory)
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles

    demo_dir = Path(__file__).resolve().parent.parent.parent / "demo"
    if demo_dir.is_dir():
        application.mount("/demo", StaticFiles(directory=str(demo_dir), html=True), name="demo_static")
        application.mount("/", StaticFiles(directory=str(demo_dir), html=True), name="static")

    return application


app = create_app()
