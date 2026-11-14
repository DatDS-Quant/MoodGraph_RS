"""
MoodGraph Phase 5: Pydantic API Schemas.
Defines strict type contracts for Mode A (Discovery), Mode B (Lab), and Interaction endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Mode A: Movie Discovery & Catalog Schemas
# ---------------------------------------------------------------------------

class MovieLinkSchema(BaseModel):
    imdb_id: Optional[str] = None
    tmdb_id: Optional[str] = None
    imdb_url: Optional[str] = None
    tmdb_url: Optional[str] = None


class MovieItemSchema(BaseModel):
    movieId: int
    title: str
    clean_title: str
    release_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    links: Optional[MovieLinkSchema] = None


class MovieSearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[MovieItemSchema]


class MovieDetailResponse(BaseModel):
    movieId: int
    title: str
    clean_title: str
    release_year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    links: Optional[MovieLinkSchema] = None
    stats: Dict[str, Any] = Field(default_factory=dict)
    similar_movies: List[Dict[str, Any]] = Field(default_factory=list)


class GenreListResponse(BaseModel):
    genres: List[str]


# ---------------------------------------------------------------------------
# User Exploration & History Schemas
# ---------------------------------------------------------------------------

class UserSummaryItem(BaseModel):
    userId: int
    train_ratings_count: int
    favorite_genres: List[str]
    is_in_kg_pilot: bool
    is_in_als_train: bool


class UserListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[UserSummaryItem]


class UserProfileResponse(BaseModel):
    userId: int
    ratings_count: int
    mean_rating: float
    genre_distribution: Dict[str, int]
    top_favorite_genres: List[str]
    activity_level: str
    is_in_als_train: bool


class UserRatingItem(BaseModel):
    movieId: int
    title: str
    genres: List[str]
    rating: float
    timestamp: int


class UserHistoryResponse(BaseModel):
    userId: int
    total_rated: int
    page: int
    page_size: int
    total_pages: int
    items: List[UserRatingItem]


# ---------------------------------------------------------------------------
# Explainability Schemas
# ---------------------------------------------------------------------------

class MetapathExplanation(BaseModel):
    metapath: str
    evidence_type: str = Field(
        ...,
        description="Type of evidence: DIRECT_GRAPH_TRAVERSAL or STRUCTURAL_HEURISTIC",
    )
    verification_status: str = Field(
        ...,
        description="Audit verification status: VERIFIED_GROUND_TRUTH or HEURISTIC_ESTIMATE",
    )
    source_model: str = Field(
        ...,
        description="Originating model or component generating this explanation",
    )
    score_contribution: Optional[float] = Field(
        None,
        description="Verified score contribution, or null if explanation is heuristic",
    )
    connecting_entities: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Verified connecting graph nodes, or empty if heuristic",
    )
    verbal_explanation: str
    is_heuristic: bool = Field(
        default=False,
        description="Flag indicating whether this explanation is a heuristic approximation",
    )
    provenance: str = Field(
        default="verified_graph_traversal",
        description="Detailed provenance of the evidence",
    )


class LatentFactorExplanation(BaseModel):
    evidence_type: str = Field(
        default="LATENT_FACTOR_AFFINITY",
        description="Type of evidence: LATENT_FACTOR_AFFINITY",
    )
    verification_status: str = Field(
        default="VERIFIED_NUMERICAL_PROJECTION",
        description="Audit status: VERIFIED_NUMERICAL_PROJECTION",
    )
    source_model: str = Field(
        default="SPARK_ALS_FACTOR_PROJECTION",
        description="Originating factor model: SPARK_ALS_FACTOR_PROJECTION",
    )
    dot_product_score: float
    model_version: str
    percentile_alignment: float
    verbal_explanation: str
    is_heuristic: bool = Field(
        default=False,
        description="Flag indicating whether this explanation is heuristic",
    )
    provenance: str = Field(
        default="verified_spark_als_latent_factor",
        description="Detailed provenance of the factor alignment",
    )


class ExplanationDetailResponse(BaseModel):
    userId: int
    movieId: int
    movie_title: str
    overall_recommendation_source: str
    graph_explanations: List[MetapathExplanation]
    latent_factor_explanation: Optional[LatentFactorExplanation] = None
    summary_text: str


# ---------------------------------------------------------------------------
# Mode B: Recommendation Lab Schemas
# ---------------------------------------------------------------------------

class ModelRegistryEntry(BaseModel):
    model_id: str
    model_family: str
    version: str
    display_name: str
    status: str
    hyperparameters: Dict[str, Any]
    description: str
    capabilities: List[str]


class RegisteredModelsResponse(BaseModel):
    models: List[ModelRegistryEntry]
    fusion_strategies: List[str]


class LabCompareRequest(BaseModel):
    user_id: int = Field(..., ge=1, le=10_000_000, description="Target user ID")
    models: List[str] = Field(
        default=["als", "kg", "hybrid_rrf", "hybrid_weighted"],
        description="Models to evaluate side-by-side",
        max_length=10,
    )
    top_n: int = Field(10, ge=1, le=50)
    filter_seen: bool = True
    rrf_k: int = Field(60, ge=1, le=1000, description="RRF smoothing constant k")
    weight_als: float = Field(0.5, ge=0.0, le=1.0, description="Weight for ALS candidate scoring")
    weight_kg: float = Field(0.5, ge=0.0, le=1.0, description="Weight for KG candidate scoring")


class ModelRunResult(BaseModel):
    model_id: str
    execution_time_ms: float
    recommendations_count: int
    recommendations: List[Dict[str, Any]]


class OverlapMetric(BaseModel):
    model_a: str
    model_b: str
    jaccard_similarity: float
    rank_correlation_spearman: Optional[float] = None
    common_movies_count: int


class LabCompareResponse(BaseModel):
    session_id: str
    user_id: int
    top_n: int
    results: Dict[str, ModelRunResult]
    pairwise_overlaps: List[OverlapMetric]
    summary: Dict[str, Any]


class MetricDetail(BaseModel):
    metric_name: str
    display_name: str
    group: str
    als_champion_score: float
    kg_only_score: float
    hybrid_rrf_score: float
    hybrid_weighted_score: float
    best_model: str


class LatencyBenchmark(BaseModel):
    strategy: str
    p50_ms: float
    p95_ms: float
    p99_ms: float
    cache_hit_p95_ms: float


class LabMetricsResponse(BaseModel):
    provenance: str
    evaluation_users_count: int
    total_cohort_users: int
    metrics: List[MetricDetail]
    latency_benchmarks: List[LatencyBenchmark]
    scientific_note: Optional[str] = None


class SystemMetadataResponse(BaseModel):
    dataset_name: str
    total_ratings: int
    split_provenance: Dict[str, Any]
    catalog_size: int
    als_model: Dict[str, Any]
    kg_graph: Dict[str, Any]
    system_environment: Dict[str, Any]


# ---------------------------------------------------------------------------
# Mode B: Subgraph Visualization Schemas
# ---------------------------------------------------------------------------

class SubgraphNode(BaseModel):
    id: str
    label: str
    type: str
    color: str
    movieId: Optional[int] = None
    rating: Optional[float] = None
    relevance: Optional[float] = None
    score: Optional[float] = None


class SubgraphEdge(BaseModel):
    model_config = {"populate_by_name": True}
    from_: str = Field(..., alias="from")
    to: str
    label: str
    weight: float
    type: str


class SubgraphResponse(BaseModel):
    nodes: List[SubgraphNode]
    edges: List[SubgraphEdge]
    academic_explanation: str


# ---------------------------------------------------------------------------
# Interaction & Mutable Application State Schemas
# ---------------------------------------------------------------------------

class WatchlistRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    movie_id: int = Field(..., ge=1)
    list_type: str = Field("watchlist", pattern="^(watchlist|favorites|hidden)$")


class WatchlistResponse(BaseModel):
    success: bool
    user_id: str
    movie_id: int
    list_type: str
    movie_title: Optional[str] = None


class RatingSubmitRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    movie_id: int = Field(..., ge=1)
    rating: float = Field(..., ge=0.5, le=5.0)
    feedback_text: Optional[str] = Field(None, max_length=1000)


class RatingSubmitResponse(BaseModel):
    success: bool
    user_id: str
    movie_id: int
    rating: float
    movie_title: Optional[str] = None


class PreferencesRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    genres: List[str] = Field(..., max_length=30)
    moods: Optional[List[str]] = Field(default_factory=list, max_length=30)
    min_year: Optional[int] = Field(None, ge=1870, le=2050)
    max_year: Optional[int] = Field(None, ge=1870, le=2050)


class PreferencesResponse(BaseModel):
    success: bool
    user_id: str
    genres: List[str]


# ---------------------------------------------------------------------------
# System & Health Schemas
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str
    version: str
    models_warmed: bool
    catalog_movies_count: int
    als_available: bool
    kg_backend: str
    sqlite_wal_enabled: bool


class CacheClearResponse(BaseModel):
    success: bool
    cleared_entries_count: int
