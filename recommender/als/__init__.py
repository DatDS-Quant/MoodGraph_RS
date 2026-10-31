"""
MoodGraph - Task 3A: Spark ALS Recommendation Module
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
]
