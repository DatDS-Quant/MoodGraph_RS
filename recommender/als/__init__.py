"""
MoodGraph - Task 3A: Spark ALS Recommendation Module (Mô-đun Khuyến nghị ALS PySpark).

Gói thư viện cung cấp toàn bộ quy trình định lượng cho Mô hình Nhân tố Ẩn (Matrix Factorization)
bằng thuật toán Alternating Least Squares (ALS) trên nền tảng Apache Spark:
- data_loader: Nạp dữ liệu Train, Validation, Test, Movies và kiểm tra schema PySpark.
- data_audit: Kiểm toán tính toàn vẹn, phân phối ratings và hiện tượng Cold-Start người dùng/vật phẩm.
- toy_als: Triển khai kiểm chứng toán học độc lập (Golden Vector, NumPy reference, ALS loss).
- trainer: Huấn luyện Spark ALS (explicit feedback), checkpointing và kiểm toán ma trận nhân tố.
- candidates: Khởi tạo catalog dự đoán, sinh Top-K recommendations và tính điểm tích vô hướng (Dot Product).
- evaluator: Đánh giá Top-N đa chỉ số (HR@K, NDCG@K, MRR@K, Coverage@K) trên tập Hold-out dương.
- popularity: Mô hình Baseline Popularity (Count & IMDb Weighted Average) làm chuẩn so sánh.
- tuner: Tinh chỉnh siêu tham số ALS (Screening Grid Search & Full Validation).
- benchmark: Đánh giá độc lập trên Frozen Test Split (M08).
- diagnostics: Phân tích chuẩn đoán phân phối điểm số, suy thoái Cold-Start và Top-K concentration (M09).
- delivery: Giao diện suy diễn chuẩn hóa (Standard Delivery Contract) và lọc lịch sử Train (M10).
"""

from .data_loader import (
    get_spark_session,
    load_train_data,
    load_validation_data,
    load_movies_data,
    load_als_datasets,
)
from .data_audit import (
    validate_train_input_constraints,
    audit_als_input_distribution,
    audit_movie_cold_start,
    run_full_m01_audit,
)
from .evaluator import (
    HeldOutTarget,
    SingleUserMetricResult,
    EvaluationSummary,
    compute_single_user_metrics,
    sort_and_rank_candidates,
    filter_seen_items,
    validate_candidate_pool,
    TopNEvaluator,
)
from .popularity import (
    PopularityMovieRecord,
    PopularityRecommendation,
    compute_weighted_score,
    rank_movies_by_count,
    rank_movies_by_weighted_average,
    generate_user_top_k,
    generate_batch_top_k,
    PopularityRecommender,
)
from .toy_als import (
    TOY_USERS,
    TOY_MOVIES,
    TOY_TRAIN_RATINGS,
    compute_dot_product,
    compute_als_loss,
    als_update_user_factors,
    als_update_item_factors,
    run_toy_als_reference,
    verify_golden_example_step,
    create_toy_spark_dataframe,
    fit_spark_toy_als,
    extract_factors,
    verify_spark_vs_manual_dot,
    demonstrate_cold_start_difference,
    verify_euclidean_vs_dot_product_counterexample,
)
from .trainer import (
    ALSConfig,
    FactorMatrixAuditResult,
    ALSTrainer,
)

__all__ = [
    "get_spark_session",
    "load_train_data",
    "load_validation_data",
    "load_movies_data",
    "load_als_datasets",
    "validate_train_input_constraints",
    "audit_als_input_distribution",
    "audit_movie_cold_start",
    "run_full_m01_audit",
    "HeldOutTarget",
    "SingleUserMetricResult",
    "EvaluationSummary",
    "compute_single_user_metrics",
    "sort_and_rank_candidates",
    "filter_seen_items",
    "validate_candidate_pool",
    "TopNEvaluator",
    "PopularityMovieRecord",
    "PopularityRecommendation",
    "compute_weighted_score",
    "rank_movies_by_count",
    "rank_movies_by_weighted_average",
    "generate_user_top_k",
    "generate_batch_top_k",
    "PopularityRecommender",
    "TOY_USERS",
    "TOY_MOVIES",
    "TOY_TRAIN_RATINGS",
    "compute_dot_product",
    "compute_als_loss",
    "als_update_user_factors",
    "als_update_item_factors",
    "run_toy_als_reference",
    "verify_golden_example_step",
    "create_toy_spark_dataframe",
    "fit_spark_toy_als",
    "extract_factors",
    "verify_spark_vs_manual_dot",
    "demonstrate_cold_start_difference",
    "verify_euclidean_vs_dot_product_counterexample",
    "ALSConfig",
    "FactorMatrixAuditResult",
    "ALSTrainer",
]
