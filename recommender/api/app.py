"""
MoodGraph Giai đoạn 5: Ứng dụng FastAPI Sẵn sàng Vận hành Thực tế (Production-Ready FastAPI Application).
Tích hợp Chế độ Khám phá Phim (Mode A), Chế độ Phòng thí nghiệm Gợi ý (Mode B),
lưu trữ trạng thái ứng dụng bằng SQLite WAL, cơ chế nạp trước lifespan tăng tốc, và hỗ trợ CORS.
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
    Bộ quản lý Vòng đời Ứng dụng FastAPI (Lifespan Manager):
    Nạp trước toàn bộ danh mục phim vào RAM, lập chỉ mục ma trận thưa CSR tập Train, và khởi động Hybrid Engine
    nhằm triệt tiêu hoàn toàn hiện tượng trễ khởi động nguội (cold-start latency spikes).
    """
    logger.info("Starting MoodGraph Phase 5 API Lifespan Pre-warming...")

    # 1. Nạp trước Danh mục Phim in-memory (~4.35 MB)
    catalog_repo = get_catalog_repository()
    catalog_repo.ensure_loaded()
    logger.info(f"Movie Catalog pre-warmed: {catalog_repo.get_movie_count()} movies indexed.")

    # 2. Nạp trước Chỉ mục CSR Lịch sử Người dùng (~50 MB)
    history_repo = get_user_history_repository()
    history_repo.warmup_index()
    logger.info("User History CSR index pre-warmed.")

    # 3. Khởi tạo kho lưu trữ Metrics thực nghiệm và SQLite trạng thái
    metrics_repo = get_research_metrics_repository()
    sqlite_repo = get_sqlite_state_repository()

    # 4. Khởi tạo Động cơ Gợi ý Lai (Hybrid Engine)
    hybrid_engine = None
    try:
        from recommender.hybrid.engine import HybridRecommenderService
        from recommender.hybrid.config import HybridConfig
        config = HybridConfig(cache_enabled=True, cross_score_als=True)
        hybrid_engine = HybridRecommenderService(config=config)
        # Kích hoạt nạp trước mô hình Spark ALS nội bộ nếu khả dụng
        if hasattr(hybrid_engine.als_service, "warmup"):
            hybrid_engine.als_service.warmup()
        logger.info("HybridRecommenderService pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"HybridRecommenderService initialization note: {e}")

    # 4b. Nạp trước bộ đệm snapshot Đồ thị Tri thức nhúng (<0.5s)
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

    # 5. Kết nối các Dịch vụ Nghiệp vụ Ứng dụng (Application Services)
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

    # Gắn các thể hiện Singleton vào app.state phục vụ Tiêm Phụ thuộc (Dependency Injection)
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
    """Hàm khởi tạo (Factory Function) để cấu hình và tạo đối tượng ứng dụng FastAPI."""
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

    # Kích hoạt cấu hình CORS cho các ứng dụng web tương tác phía client
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

    # Đăng ký các Bộ định tuyến (Mount Routers)
    application.include_router(system_router)
    application.include_router(discovery_router)
    application.include_router(lab_router)
    application.include_router(interaction_router)

    # Phục vụ Giao diện Web tĩnh (Mount Static Web Client demo/)
    from pathlib import Path
    from fastapi.staticfiles import StaticFiles

    demo_dir = Path(__file__).resolve().parent.parent.parent / "demo"
    if demo_dir.is_dir():
        application.mount("/demo", StaticFiles(directory=str(demo_dir), html=True), name="demo_static")
        application.mount("/", StaticFiles(directory=str(demo_dir), html=True), name="static")

    return application


app = create_app()
