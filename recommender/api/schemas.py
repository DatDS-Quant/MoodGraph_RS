"""
MoodGraph Giai đoạn 5: Các Mô hình Dữ liệu Pydantic API (API Schemas).
Định nghĩa hợp đồng dữ liệu chuẩn kiểu cho Chế độ Khám phá (Mode A),
Phòng thí nghiệm Gợi ý (Mode B), và các điểm cuối tương tác người dùng.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ===========================================================================
# Chế độ A: Các Schema Khám phá & Danh mục Phim (Movie Discovery & Catalog Schemas)
# ===========================================================================

class MovieLinkSchema(BaseModel):
    """Liên kết định danh ngoài tới IMDb và TMDb."""
    imdb_id: Optional[str] = None
    tmdb_id: Optional[str] = None
    imdb_url: Optional[str] = None
    tmdb_url: Optional[str] = None


class MovieItemSchema(BaseModel):
    """Thông tin tóm tắt của một bộ phim trong danh sách tìm kiếm."""
    movieId: int
    title: str
    clean_title: str
    release_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    links: Optional[MovieLinkSchema] = None


class MovieSearchResponse(BaseModel):
    """Kết quả tìm kiếm phim có phân trang."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[MovieItemSchema]


class MovieDetailResponse(BaseModel):
    """Chi tiết đầy đủ của một bộ phim kèm liên kết và danh sách phim tương đồng."""
    movieId: int
    title: str
    clean_title: str
    release_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    links: Optional[MovieLinkSchema] = None
    stats: Dict[str, Any] = Field(default_factory=dict)
    similar_movies: List[Dict[str, Any]] = Field(default_factory=list)


class GenreListResponse(BaseModel):
    """Danh sách các thể loại phim phân biệt."""
    genres: List[str]


# ===========================================================================
# Các Schema Thăm dò Hồ sơ & Lịch sử Người dùng (User Exploration & History Schemas)
# ===========================================================================

class UserSummaryItem(BaseModel):
    """Thông tin tóm tắt người dùng trong danh sách mẫu."""
    userId: int
    train_ratings_count: int
    favorite_genres: List[str]
    is_in_kg_pilot: bool
    is_in_als_train: bool


class UserListResponse(BaseModel):
    """Danh sách người dùng mẫu có phân trang."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[UserSummaryItem]


class UserProfileResponse(BaseModel):
    """Hồ sơ hoạt động và phân bố thể loại của người dùng từ tập Train."""
    userId: int
    ratings_count: int
    mean_rating: float
    genre_distribution: Dict[str, int]
    top_favorite_genres: List[str]
    activity_level: str
    is_in_als_train: bool


class UserRatingItem(BaseModel):
    """Một bản ghi đánh giá phim của người dùng trong tập Train."""
    movieId: int
    title: str
    genres: List[str]
    rating: float
    timestamp: int


class UserHistoryResponse(BaseModel):
    """Lịch sử đánh giá phim của người dùng có phân trang từ tập Train."""
    userId: int
    total_rated: int
    page: int
    page_size: int
    total_pages: int
    items: List[UserRatingItem]


# ===========================================================================
# Các Schema Minh bạch & Giải thích Khuyến nghị (Explainability Schemas)
# ===========================================================================

class MetapathExplanation(BaseModel):
    """Bằng chứng giải thích dựa trên siêu đường dẫn Đồ thị Tri thức (KG Metapath)."""
    metapath: str
    evidence_type: str = Field(
        ...,
        description="Type of evidence: DIRECT_GRAPH_TRAVERSAL or STRUCTURAL_HEURISTIC",
    )
    verification_status: str = Field(
        ...,
        description="Trạng thái kiểm định: VERIFIED_GROUND_TRUTH hoặc HEURISTIC_ESTIMATE",
    )
    source_model: str = Field(
        ...,
        description="Mô hình hoặc thành phần nguồn tạo ra lời giải thích này",
    )
    score_contribution: Optional[float] = Field(
        None,
        description="Đóng góp điểm số đã xác thực, hoặc null nếu là ước lượng heuristic",
    )
    connecting_entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Danh sách các nút đồ thị kết nối đã xác thực, hoặc rỗng nếu là heuristic",
    )
    verbal_explanation: str
    is_heuristic: bool = Field(
        default=False,
        description="Cờ đánh dấu liệu lời giải thích này có phải là xấp xỉ heuristic hay không",
    )
    provenance: str = Field(
        default="verified_graph_traversal",
        description="Nguồn gốc xuất xứ chi tiết của bằng chứng",
    )


class LatentFactorExplanation(BaseModel):
    """Bằng chứng giải thích dựa trên không gian nhân tố tiềm ẩn ALS."""
    evidence_type: str = Field(
        default="LATENT_FACTOR_AFFINITY",
        description="Loại bằng chứng: LATENT_FACTOR_AFFINITY",
    )
    verification_status: str = Field(
        default="VERIFIED_NUMERICAL_PROJECTION",
        description="Trạng thái kiểm định: VERIFIED_NUMERICAL_PROJECTION",
    )
    source_model: str = Field(
        default="SPARK_ALS_FACTOR_PROJECTION",
        description="Mô hình nhân tố nguồn: SPARK_ALS_FACTOR_PROJECTION",
    )
    dot_product_score: float
    model_version: str
    percentile_alignment: float
    verbal_explanation: str
    is_heuristic: bool = Field(
        default=False,
        description="Cờ đánh dấu liệu lời giải thích có phải là heuristic",
    )
    provenance: str = Field(
        default="verified_spark_als_latent_factor",
        description="Nguồn gốc xuất xứ chi tiết của phép gióng hàng nhân tố",
    )


class ExplanationDetailResponse(BaseModel):
    """Phản hồi giải thích đa tầng hoàn chỉnh cho một cặp người dùng - bộ phim."""
    userId: int
    movieId: int
    movie_title: str
    overall_recommendation_source: str
    graph_explanations: List[MetapathExplanation]
    latent_factor_explanation: Optional[LatentFactorExplanation] = None
    summary_text: str


# ===========================================================================
# Chế độ B: Các Schema Phòng Thí nghiệm Gợi ý (Recommendation Lab Schemas)
# ===========================================================================

class ModelRegistryEntry(BaseModel):
    """Thông tin đăng ký của một mô hình gợi ý trong Lab."""
    model_id: str
    model_family: str
    version: str
    display_name: str
    status: str
    hyperparameters: Dict[str, Any]
    description: str
    capabilities: List[str]


class RegisteredModelsResponse(BaseModel):
    """Danh mục các mô hình và chiến lược kết hợp đã đăng ký."""
    models: List[ModelRegistryEntry]
    fusion_strategies: List[str]


class LabCompareRequest(BaseModel):
    """Yêu cầu so sánh đối đầu đa mô hình song song cho một người dùng."""
    user_id: int = Field(..., ge=1, le=10_000_000, description="ID người dùng mục tiêu")
    models: List[str] = Field(
        default=["als", "kg", "hybrid_rrf", "hybrid_weighted"],
        description="Danh sách mô hình cần đánh giá so sánh đối đầu",
        max_length=10,
    )
    top_n: int = Field(10, ge=1, le=50)
    filter_seen: bool = True
    rrf_k: int = Field(60, ge=1, le=1000, description="Hằng số làm mịn k của thuật toán RRF")
    weight_als: float = Field(0.5, ge=0.0, le=1.0, description="Trọng số chấm điểm ứng viên của ALS")
    weight_kg: float = Field(0.5, ge=0.0, le=1.0, description="Trọng số chấm điểm ứng viên của KG")


class ModelRunResult(BaseModel):
    """Kết quả thực thi và danh sách đề xuất của một mô hình cụ thể."""
    model_id: str
    execution_time_ms: float
    recommendations_count: int
    recommendations: List[Dict[str, Any]]


class OverlapMetric(BaseModel):
    """Chỉ số đo lường độ trùng lặp và tương quan thứ hạng giữa hai mô hình."""
    model_a: str
    model_b: str
    jaccard_similarity: float
    rank_correlation_spearman: Optional[float] = None
    common_movies_count: int


class LabCompareResponse(BaseModel):
    """Kết quả hoàn chỉnh của phiên thực nghiệm so sánh đa mô hình trong Lab."""
    session_id: str
    user_id: int
    top_n: int
    results: Dict[str, ModelRunResult]
    pairwise_overlaps: List[OverlapMetric]
    summary: Dict[str, Any]


class MetricDetail(BaseModel):
    """Chi tiết một chỉ số đo kiểm offline (HR, NDCG, MRR, Coverage)."""
    metric_name: str
    display_name: str
    group: str
    als_champion_score: float
    kg_only_score: float
    hybrid_rrf_score: float
    hybrid_weighted_score: float
    best_model: str


class LatencyBenchmark(BaseModel):
    """Số liệu đo kiểm chuẩn độ trễ truy vấn (P50, P95, P99)."""
    strategy: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    cache_hit_p95_ms: float


class LabMetricsResponse(BaseModel):
    """Bảng so sánh chỉ số đo kiểm thực nghiệm offline từ Giai đoạn 4."""
    provenance: str
    evaluation_users_count: int
    total_cohort_users: int
    metrics: List[MetricDetail]
    latency_benchmarks: List[LatencyBenchmark]
    scientific_note: Optional[str] = None


class SystemMetadataResponse(BaseModel):
    """Siêu dữ liệu về kích thước tập dữ liệu, mô hình và môi trường thực thi."""
    dataset_name: str
    total_ratings: int
    split_provenance: Dict[str, Any]
    catalog_size: int
    als_model: Dict[str, Any]
    kg_graph: Dict[str, Any]
    system_environment: Dict[str, Any]


# ===========================================================================
# Chế độ B: Các Schema Trực quan hóa Đồ thị Con (Subgraph Visualization)
# ===========================================================================

class SubgraphNode(BaseModel):
    """Nút mạng trên đồ thị con giải thích trực quan."""
    id: str
    label: str
    type: str
    color: str
    movieId: Optional[int] = None
    rating: Optional[float] = None
    relevance: Optional[float] = None
    score: Optional[float] = None


class SubgraphEdge(BaseModel):
    """Cạnh nối có hướng mang trọng số trên đồ thị con giải thích."""
    model_config = {"populate_by_name": True}
    from_: str = Field(..., alias="from")
    to: str
    label: str
    weight: float
    type: str


class SubgraphResponse(BaseModel):
    """Phản hồi mạng đồ thị con hoàn chỉnh phục vụ thư viện trực quan vis-network."""
    nodes: List[SubgraphNode]
    edges: List[SubgraphEdge]
    academic_explanation: str


# ===========================================================================
# Các Schema Tương tác & Trạng thái Ứng dụng (Interaction & Application State)
# ===========================================================================

class WatchlistRequest(BaseModel):
    """Yêu cầu thêm phim vào danh sách xem sau/yêu thích."""
    user_id: str = Field(..., min_length=1, max_length=64)
    movie_id: int = Field(..., ge=1)
    list_type: str = Field("watchlist", pattern="^(watchlist|favorites|hidden)$")


class WatchlistResponse(BaseModel):
    """Phản hồi trạng thái lưu phim."""
    success: bool
    user_id: str
    movie_id: int
    list_type: str
    movie_title: Optional[str] = None


class RatingSubmitRequest(BaseModel):
    """Yêu cầu gửi đánh giá và nhận xét của người dùng."""
    user_id: str = Field(..., min_length=1, max_length=64)
    movie_id: int = Field(..., ge=1)
    rating: float = Field(..., ge=0.5, le=5.0)
    feedback_text: Optional[str] = Field(None, max_length=1000)


class RatingSubmitResponse(BaseModel):
    """Phản hồi kết quả ghi nhận đánh giá."""
    success: bool
    user_id: str
    movie_id: int
    rating: float
    movie_title: Optional[str] = None


class PreferencesRequest(BaseModel):
    """Yêu cầu cập nhật sở thích người dùng."""
    user_id: str = Field(..., min_length=1, max_length=64)
    genres: List[str] = Field(..., max_length=30)
    moods: Optional[List[str]] = Field(default_factory=list, max_length=30)
    min_year: Optional[int] = Field(None, ge=1870, le=2050)
    max_year: Optional[int] = Field(None, ge=1870, le=2050)


class PreferencesResponse(BaseModel):
    """Phản hồi lưu cấu hình sở thích người dùng."""
    success: bool
    user_id: str
    genres: List[str]


# ===========================================================================
# Các Schema Hệ thống & Chẩn đoán Sức khỏe (System & Health Schemas)
# ===========================================================================

class HealthResponse(BaseModel):
    """Phản hồi trạng thái hoạt động và sẵn sàng của hệ thống."""
    status: str
    version: str
    models_warmed: bool
    catalog_movies_count: int
    als_available: bool
    kg_backend: str
    sqlite_wal_enabled: bool


class CacheClearResponse(BaseModel):
    """Phản hồi sau khi xóa sạch bộ nhớ đệm cache."""
    success: bool
    cleared_entries_count: int
