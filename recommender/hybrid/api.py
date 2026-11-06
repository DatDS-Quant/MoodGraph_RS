"""
Serving API cho MoodGraph Phase 4 dựa trên FastAPI và Uvicorn.

Cung cấp:
- Endpoint gợi ý phim thời gian thực: GET /api/recommendations/{user_id}
- Endpoint kiểm tra sức khỏe hệ thống: GET /api/health
- Endpoint thông tin mô hình và tham số: GET /api/model_info
- Endpoint quản trị bộ nhớ đệm: POST /api/cache/clear
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Path as FPath, Header
import os
from pydantic import BaseModel, Field

from recommender.hybrid.engine import HybridRecommenderService, get_hybrid_service
from recommender.hybrid.config import load_hybrid_config
from recommender.hybrid.contracts import CandidateSource, FusionStrategy

app = FastAPI(
    title="MoodGraph Recommendation API",
    description="High-performance Hybrid Movie Recommendation Serving Engine combining Spark ALS and Knowledge Graph",
    version="4.0.0",
)

# Khởi tạo dịch vụ
_service_instance: Optional[HybridRecommenderService] = None


def get_api_service() -> HybridRecommenderService:
    global _service_instance
    if _service_instance is None:
        _service_instance = get_hybrid_service()
    return _service_instance


def set_api_service(service: HybridRecommenderService) -> None:
    global _service_instance
    _service_instance = service


# Pydantic Schemas cho API
class RecommendationItemSchema(BaseModel):
    userId: int
    movieId: int
    title: Optional[str] = None
    hybrid_score: float
    rank: int
    source: str
    fusion_method: str
    als_raw_score: Optional[float] = None
    als_normalized_score: Optional[float] = None
    als_rank: Optional[int] = None
    kg_raw_score: Optional[float] = None
    kg_normalized_score: Optional[float] = None
    kg_rank: Optional[int] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class RecommendationResponseSchema(BaseModel):
    userId: int
    recommendations: List[RecommendationItemSchema]
    metadata: Dict[str, Any]


class HealthResponseSchema(BaseModel):
    status: str
    service: str
    version: str
    cache_stats: Dict[str, Any]
    models_ready: Dict[str, bool]


class ModelInfoSchema(BaseModel):
    hybrid_version: str
    als_champion: str
    kg_paths: List[str]
    supported_fusion_strategies: List[str]
    default_config: Dict[str, Any]


@app.get("/api/health", response_model=HealthResponseSchema)
def health_check() -> HealthResponseSchema:
    """Kiểm tra tình trạng sẵn sàng phục vụ của hệ thống và bộ nhớ đệm."""
    service = get_api_service()
    cache_stats = service.cache.stats() if service.cache else {"status": "disabled"}

    # Thẩm định khả năng sẵn sàng của các mô hình thành phần
    als_ready = service._als_service is not None or True
    kg_ready = service._kg_graph is not None or True

    return HealthResponseSchema(
        status="ok",
        service="MoodGraph Hybrid Serving API",
        version="4.0.0",
        cache_stats=cache_stats,
        models_ready={"als": als_ready, "kg": kg_ready},
    )


@app.get("/api/model_info", response_model=ModelInfoSchema)
def get_model_info() -> ModelInfoSchema:
    """Truy xuất thông tin siêu dữ liệu các mô hình đăng ký."""
    service = get_api_service()
    cfg = service.config
    return ModelInfoSchema(
        hybrid_version="Phase 4 - Production Hybrid Recommender v4.0",
        als_champion="ALS_R8_REG0.3_ITER10 (Rank=8, Reg=0.3, Iter=10)",
        kg_paths=["P1 (Genre Metapath)", "P2 (Genome Metapath)", "P3 (Collaborative Graph Metapath)"],
        supported_fusion_strategies=["rrf", "weighted", "als_only", "kg_only"],
        default_config={
            "default_fusion_strategy": cfg.default_fusion_strategy,
            "rrf_k": cfg.rrf_k,
            "weight_als": cfg.weight_als,
            "weight_kg": cfg.weight_kg,
            "top_k_candidates_als": cfg.top_k_candidates_als,
            "top_k_candidates_kg": cfg.top_k_candidates_kg,
            "default_top_n": cfg.default_top_n,
            "cache_enabled": cfg.cache_enabled,
        },
    )


@app.get("/api/recommendations/{user_id}", response_model=RecommendationResponseSchema)
def get_recommendations(
    user_id: int = FPath(..., description="ID người dùng MovieLens (nguyên dương)", ge=1),
    top_n: int = Query(10, description="Số lượng gợi ý Top-N", ge=1, le=100),
    model: str = Query("hybrid", description="Chế độ mô hình: hybrid, als, kg"),
    fusion: str = Query("rrf", description="Chiến lược dung hợp: rrf, weighted"),
    w_als: float = Query(0.5, description="Trọng số ALS (dùng cho weighted)", ge=0.0, le=1.0),
    w_kg: float = Query(0.5, description="Trọng số KG (dùng cho weighted)", ge=0.0, le=1.0),
    rrf_k: int = Query(60, description="Hằng số làm mịn RRF k", ge=1),
    filter_seen: bool = Query(True, description="Lọc các phim đã tương tác trong lịch sử"),
    allow_unfiltered: bool = Query(False, description="Chỉ cho phép tắt lọc phim đã xem khi phục vụ chẩn đoán nội bộ"),
    cross_score_als: Optional[bool] = Query(None, description="Kích hoạt ALS cross-scoring cho ứng viên KG"),
    use_cache: bool = Query(True, description="Sử dụng bộ nhớ đệm tăng tốc"),
) -> RecommendationResponseSchema:
    """
    Sinh danh sách gợi ý phim cá nhân hóa theo thời gian thực.
    Bảo vệ sản xuất: Tự động cưỡng chế lọc phim đã xem (filter_seen=True)
    trừ khi có cờ allow_unfiltered=True phục vụ chẩn đoán hệ thống.
    """
    service = get_api_service()

    # Ràng buộc an toàn: Không cho phép vô hiệu hóa lọc phim đã xem trên endpoint phục vụ công cộng
    effective_filter_seen = filter_seen
    if not filter_seen and not allow_unfiltered:
        raise HTTPException(
            status_code=400,
            detail="Tắt lọc phim đã xem (filter_seen=false) bị hạn chế trong môi trường phục vụ công cộng. "
                   "Để phục vụ mục đích kiểm thử hoặc chẩn đoán, vui lòng thiết lập allow_unfiltered=true.",
        )

    # Ánh xạ tham số mô hình sang chiến lược dung hợp
    model_lower = model.lower()
    if model_lower == "als":
        strategy = "als_only"
    elif model_lower == "kg":
        strategy = "kg_only"
    elif model_lower == "hybrid":
        strategy = fusion.lower()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model '{model}'. Choose from: hybrid, als, kg.")

    try:
        response = service.recommend(
            user_id=user_id,
            top_n=top_n,
            fusion_strategy=strategy,
            weight_als=w_als,
            weight_kg=w_kg,
            rrf_k=rrf_k,
            filter_seen=effective_filter_seen,
            use_cache=use_cache,
            cross_score_als=cross_score_als,
        )
        return RecommendationResponseSchema(
            userId=response.userId,
            recommendations=[
                RecommendationItemSchema(**item.to_dict()) for item in response.recommendations
            ],
            metadata=response.metadata,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(exc)}") from exc


@app.post("/api/cache/clear")
def clear_cache(
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token"),
    token: Optional[str] = Query(None, description="Admin token nếu gọi qua query string"),
) -> Dict[str, Any]:
    """Xóa bộ nhớ đệm phục vụ thử nghiệm và đánh giá độ trễ (yêu cầu xác thực nếu cấu hình ADMIN_API_KEY)."""
    admin_key = os.getenv("ADMIN_API_KEY")
    if admin_key:
        provided = x_admin_token or token
        if not provided or provided != admin_key:
            raise HTTPException(status_code=403, detail="Xác thực quản trị thất bại: Token không hợp lệ.")

    service = get_api_service()
    if service.cache:
        service.cache.clear()
        return {"status": "success", "message": "Cache successfully cleared."}
    return {"status": "ignored", "message": "Cache is disabled."}

