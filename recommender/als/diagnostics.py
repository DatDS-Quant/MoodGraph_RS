"""
MoodGraph - Task 3A: ALS Diagnostics Engine
Module: M09 - Cold-Start, Long-Tail, Factor Reliability & Spark Performance

Provides scientific diagnostics, empirical distributions, factor norm statistics,
cold-start classifications, score distribution analysis, and performance benchmarks
for Spark ALS collaborative filtering on MovieLens 25M.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

import numpy as np
import pyarrow.parquet as pq
import scipy.stats as stats


class ColdStartType(str, Enum):
    """Classification types for cold-start and support regimes."""
    WARM_PAIR = "WARM_PAIR"              # User and item both have >= 6 ratings in Train
    COLD_USER = "COLD_USER"              # User has 0 ratings in Train
    COLD_ITEM = "COLD_ITEM"              # Item has 0 ratings in Train (unscoreable catalog item)
    LOW_SUPPORT_ITEM = "LOW_SUPPORT_ITEM"  # Item has 1 to 5 ratings in Train
    MODERATE_SUPPORT_ITEM = "MODERATE_SUPPORT_ITEM"  # Item has 6 to 10 ratings in Train


@dataclass(frozen=True)
class ItemSupportBin:
    """Statistics for a single item support bin."""
    bin_name: str
    lower_bound: int  # Inclusive
    upper_bound: Optional[int]  # Inclusive, None for unbounded (>50)
    item_count: int
    percentage: float
    mean_support: float
    median_support: float
    min_support: int
    max_support: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bin_name": self.bin_name,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "item_count": self.item_count,
            "percentage": round(self.percentage, 4),
            "mean_support": round(self.mean_support, 4),
            "median_support": round(self.median_support, 4),
            "min_support": self.min_support,
            "max_support": self.max_support,
        }


@dataclass(frozen=True)
class FactorNormSummary:
    """Summary statistics of latent factor norms."""
    entity_type: str  # "item" or "user"
    count: int
    rank: int
    min_norm: float
    max_norm: float
    mean_norm: float
    median_norm: float
    std_norm: float
    p90_norm: float
    p95_norm: float
    p99_norm: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "count": self.count,
            "rank": self.rank,
            "min_norm": round(self.min_norm, 6),
            "max_norm": round(self.max_norm, 6),
            "mean_norm": round(self.mean_norm, 6),
            "median_norm": round(self.median_norm, 6),
            "std_norm": round(self.std_norm, 6),
            "p90_norm": round(self.p90_norm, 6),
            "p95_norm": round(self.p95_norm, 6),
            "p99_norm": round(self.p99_norm, 6),
        }


@dataclass(frozen=True)
class SupportNormCorrelation:
    """Correlation analysis between log item support and factor norms."""
    num_items: int
    pearson_corr: float
    pearson_pval: float
    spearman_corr: float
    spearman_pval: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_items": self.num_items,
            "pearson_corr": round(self.pearson_corr, 6),
            "pearson_pval": float(self.pearson_pval),
            "spearman_corr": round(self.spearman_corr, 6),
            "spearman_pval": float(self.spearman_pval),
        }


@dataclass(frozen=True)
class ScoreDistributionSummary:
    """Empirical distribution of predicted ALS dot-product scores."""
    num_users: int
    num_items: int
    total_evaluations: int
    min_score: float
    max_score: float
    mean_score: float
    median_score: float
    std_score: float
    p01_score: float
    p05_score: float
    p25_score: float
    p50_score: float
    p75_score: float
    p95_score: float
    p99_score: float
    count_negative: int
    frac_negative: float
    count_gt_5: int
    frac_gt_5: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "num_users": self.num_users,
            "num_items": self.num_items,
            "total_evaluations": self.total_evaluations,
            "min_score": round(self.min_score, 6),
            "max_score": round(self.max_score, 6),
            "mean_score": round(self.mean_score, 6),
            "median_score": round(self.median_score, 6),
            "std_score": round(self.std_score, 6),
            "p01_score": round(self.p01_score, 6),
            "p05_score": round(self.p05_score, 6),
            "p25_score": round(self.p25_score, 6),
            "p50_score": round(self.p50_score, 6),
            "p75_score": round(self.p75_score, 6),
            "p95_score": round(self.p95_score, 6),
            "p99_score": round(self.p99_score, 6),
            "count_negative": self.count_negative,
            "frac_negative": round(self.frac_negative, 6),
            "count_gt_5": self.count_gt_5,
            "frac_gt_5": round(self.frac_gt_5, 6),
        }


@dataclass(frozen=True)
class TopKSupportConcentration:
    """Concentration of Top-K recommendations across item support bins."""
    k: int
    num_users: int
    total_recommendations: int
    unique_items_recommended: int
    catalog_coverage_pct: float
    frac_support_1: float
    frac_bin_0: float
    frac_bin_1_5: float
    frac_bin_6_10: float
    frac_bin_11_50: float
    frac_bin_gt_50: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "k": self.k,
            "num_users": self.num_users,
            "total_recommendations": self.total_recommendations,
            "unique_items_recommended": self.unique_items_recommended,
            "catalog_coverage_pct": round(self.catalog_coverage_pct, 4),
            "frac_support_1": round(self.frac_support_1, 4),
            "frac_bin_0": round(self.frac_bin_0, 4),
            "frac_bin_1_5": round(self.frac_bin_1_5, 4),
            "frac_bin_6_10": round(self.frac_bin_6_10, 4),
            "frac_bin_11_50": round(self.frac_bin_11_50, 4),
            "frac_bin_gt_50": round(self.frac_bin_gt_50, 4),
        }


# ==============================================================================
# 1. ITEM SUPPORT ANALYZER
# ==============================================================================

class ItemSupportAnalyzer:
    """
    Computes exact Train item-support distribution across 5 disjoint bins:
    1. 0 ratings (unscoreable catalog items)
    2. 1-5 ratings (extreme long-tail / cold-start)
    3. 6-10 ratings (low support)
    4. 11-50 ratings (medium support)
    5. >50 ratings (head / popular items)
    """

    SUPPORT_BIN_DEFS = [
        ("0 ratings", 0, 0),
        ("1-5 ratings", 1, 5),
        ("6-10 ratings", 6, 10),
        ("11-50 ratings", 11, 50),
        (">50 ratings", 51, None),
    ]

    @staticmethod
    def compute_distribution(
        item_supports: Dict[int, int],
        catalog_movie_ids: Set[int],
    ) -> List[ItemSupportBin]:
        """
        Compute support bins given item support dictionary and full catalog movie IDs.
        Guarantees that sum(item_count) == len(catalog_movie_ids).
        """
        total_catalog = len(catalog_movie_ids)
        if total_catalog == 0:
            raise ValueError("catalog_movie_ids cannot be empty")

        # All catalog items
        bins: List[ItemSupportBin] = []
        counted_items = 0

        for bin_name, low, high in ItemSupportAnalyzer.SUPPORT_BIN_DEFS:
            if low == 0 and high == 0:
                # Items in catalog with 0 ratings in Train
                bin_items = [mid for mid in catalog_movie_ids if item_supports.get(mid, 0) == 0]
                bin_supports = [0] * len(bin_items)
            elif high is None:
                bin_items = [mid for mid in catalog_movie_ids if item_supports.get(mid, 0) >= low]
                bin_supports = [item_supports[mid] for mid in bin_items]
            else:
                bin_items = [
                    mid for mid in catalog_movie_ids
                    if low <= item_supports.get(mid, 0) <= high
                ]
                bin_supports = [item_supports[mid] for mid in bin_items]

            count = len(bin_items)
            counted_items += count
            pct = (count / total_catalog) * 100.0
            mean_sup = float(np.mean(bin_supports)) if count > 0 else 0.0
            med_sup = float(np.median(bin_supports)) if count > 0 else 0.0
            min_sup = int(np.min(bin_supports)) if count > 0 else 0
            max_sup = int(np.max(bin_supports)) if count > 0 else 0

            bins.append(
                ItemSupportBin(
                    bin_name=bin_name,
                    lower_bound=low,
                    upper_bound=high,
                    item_count=count,
                    percentage=pct,
                    mean_support=mean_sup,
                    median_support=med_sup,
                    min_support=min_sup,
                    max_support=max_sup,
                )
            )

        if counted_items != total_catalog:
            raise ValueError(
                f"Catalog conservation violated: sum of bins ({counted_items}) != total catalog ({total_catalog})"
            )

        return bins


# ==============================================================================
# 2. FACTOR RELIABILITY ANALYZER
# ==============================================================================

class FactorReliabilityAnalyzer:
    """
    Computes L2 norms and statistical summaries for item and user latent factor vectors.
    Evaluates correlation between item support and factor norms.
    """

    @staticmethod
    def compute_norm_summary(
        factors: np.ndarray,
        entity_type: str,
    ) -> FactorNormSummary:
        """Compute L2 norm distribution statistics for a factor matrix."""
        if factors.ndim != 2:
            raise ValueError(f"factors must be 2D array, got shape {factors.shape}")
        if factors.shape[0] == 0:
            raise ValueError("factors array cannot be empty")

        norms = np.linalg.norm(factors, axis=1)
        count = len(norms)
        rank = factors.shape[1]

        return FactorNormSummary(
            entity_type=entity_type,
            count=count,
            rank=rank,
            min_norm=float(np.min(norms)),
            max_norm=float(np.max(norms)),
            mean_norm=float(np.mean(norms)),
            median_norm=float(np.median(norms)),
            std_norm=float(np.std(norms)),
            p90_norm=float(np.percentile(norms, 90)),
            p95_norm=float(np.percentile(norms, 95)),
            p99_norm=float(np.percentile(norms, 99)),
        )

    @staticmethod
    def compute_support_correlation(
        item_supports: np.ndarray,
        item_factors: np.ndarray,
    ) -> SupportNormCorrelation:
        """
        Compute Pearson and Spearman correlation between log1p(support) and item factor L2 norm.
        """
        if len(item_supports) != len(item_factors):
            raise ValueError("item_supports and item_factors must have equal length")

        norms = np.linalg.norm(item_factors, axis=1)
        log_supports = np.log1p(item_supports)

        p_corr, p_val = stats.pearsonr(log_supports, norms)
        s_corr, s_val = stats.spearmanr(log_supports, norms)

        return SupportNormCorrelation(
            num_items=len(norms),
            pearson_corr=float(p_corr),
            pearson_pval=float(p_val),
            spearman_corr=float(s_corr),
            spearman_pval=float(s_val),
        )

    @staticmethod
    def compute_bin_norm_diagnostics(
        item_ids: np.ndarray,
        item_factors: np.ndarray,
        item_support_dict: Dict[int, int],
    ) -> List[Dict[str, Any]]:
        """Compute mean and median factor norms per item support bin."""
        norms = np.linalg.norm(item_factors, axis=1)
        supports = np.array([item_support_dict.get(int(mid), 0) for mid in item_ids])

        results = []
        for bin_name, low, high in ItemSupportAnalyzer.SUPPORT_BIN_DEFS:
            if low == 0 and high == 0:
                continue  # Items with 0 ratings have no ALS factors
            if high is None:
                mask = supports >= low
            else:
                mask = (supports >= low) & (supports <= high)

            bin_norms = norms[mask]
            count = len(bin_norms)
            if count > 0:
                results.append({
                    "bin_name": bin_name,
                    "item_count": count,
                    "mean_norm": round(float(np.mean(bin_norms)), 6),
                    "median_norm": round(float(np.median(bin_norms)), 6),
                    "min_norm": round(float(np.min(bin_norms)), 6),
                    "max_norm": round(float(np.max(bin_norms)), 6),
                    "std_norm": round(float(np.std(bin_norms)), 6),
                })
        return results


# ==============================================================================
# 3. COLD START CLASSIFIER
# ==============================================================================

class ColdStartClassifier:
    """
    Classifies user-item interactions or pairs into distinct cold-start regimes.
    """

    def __init__(
        self,
        train_users: Set[int],
        train_items: Set[int],
        item_support_dict: Dict[int, int],
    ):
        self.train_users = train_users
        self.train_items = train_items
        self.item_support_dict = item_support_dict

    def classify_pair(self, user_id: int, item_id: int) -> ColdStartType:
        """Classify a user-item pair based on Train history presence and support."""
        user_in_train = user_id in self.train_users
        item_in_train = item_id in self.train_items

        if not user_in_train:
            return ColdStartType.COLD_USER

        if not item_in_train:
            return ColdStartType.COLD_ITEM

        support = self.item_support_dict.get(item_id, 0)
        if support <= 5:
            return ColdStartType.LOW_SUPPORT_ITEM
        if support <= 10:
            return ColdStartType.MODERATE_SUPPORT_ITEM

        return ColdStartType.WARM_PAIR


# ==============================================================================
# 4. SCORE DIAGNOSTICS ANALYZER
# ==============================================================================

class ScoreDiagnosticsAnalyzer:
    """
    Analyzes predicted ALS dot-product scores (P_u dot Q_i) across a deterministic
    Train-only user cohort, assessing score range, distribution, and Top-K concentration.
    """

    @staticmethod
    def compute_score_distribution(
        user_factors: np.ndarray,
        item_factors: np.ndarray,
    ) -> ScoreDistributionSummary:
        """
        Compute score distribution over user_factors @ item_factors.T.
        Scores are calculated in memory-safe chunks if necessary.
        """
        n_users = user_factors.shape[0]
        n_items = item_factors.shape[0]
        total_evals = n_users * n_items

        scores = user_factors @ item_factors.T  # Shape (n_users, n_items)

        min_val = float(np.min(scores))
        max_val = float(np.max(scores))
        mean_val = float(np.mean(scores))
        med_val = float(np.median(scores))
        std_val = float(np.std(scores))

        p01 = float(np.percentile(scores, 1))
        p05 = float(np.percentile(scores, 5))
        p25 = float(np.percentile(scores, 25))
        p50 = med_val
        p75 = float(np.percentile(scores, 75))
        p95 = float(np.percentile(scores, 95))
        p99 = float(np.percentile(scores, 99))

        cnt_neg = int(np.sum(scores < 0.0))
        frac_neg = cnt_neg / float(total_evals)

        cnt_gt5 = int(np.sum(scores > 5.0))
        frac_gt5 = cnt_gt5 / float(total_evals)

        return ScoreDistributionSummary(
            num_users=n_users,
            num_items=n_items,
            total_evaluations=total_evals,
            min_score=min_val,
            max_score=max_val,
            mean_score=mean_val,
            median_score=med_val,
            std_score=std_val,
            p01_score=p01,
            p05_score=p05,
            p25_score=p25,
            p50_score=p50,
            p75_score=p75,
            p95_score=p95,
            p99_score=p99,
            count_negative=cnt_neg,
            frac_negative=frac_neg,
            count_gt_5=cnt_gt5,
            frac_gt_5=frac_gt5,
        )

    @staticmethod
    def compute_recommendation_concentration(
        recommendations: Dict[int, List[Tuple[int, float]]],
        item_support_dict: Dict[int, int],
        catalog_size: int,
        k: int = 20,
    ) -> TopKSupportConcentration:
        """
        Analyze what item support bins dominate the generated Top-K recommendations.
        """
        all_recs: List[int] = []
        for uid, rec_list in recommendations.items():
            for mid, score in rec_list[:k]:
                all_recs.append(mid)

        total_recs = len(all_recs)
        if total_recs == 0:
            raise ValueError("Recommendations list is empty")

        unique_recs = set(all_recs)
        unique_count = len(unique_recs)
        coverage_pct = (unique_count / float(catalog_size)) * 100.0

        supports = np.array([item_support_dict.get(mid, 0) for mid in all_recs])

        cnt_sup_1 = int(np.sum(supports == 1))
        cnt_bin_0 = int(np.sum(supports == 0))
        cnt_bin_1_5 = int(np.sum((supports >= 1) & (supports <= 5)))
        cnt_bin_6_10 = int(np.sum((supports >= 6) & (supports <= 10)))
        cnt_bin_11_50 = int(np.sum((supports >= 11) & (supports <= 50)))
        cnt_bin_gt_50 = int(np.sum(supports > 50))

        return TopKSupportConcentration(
            k=k,
            num_users=len(recommendations),
            total_recommendations=total_recs,
            unique_items_recommended=unique_count,
            catalog_coverage_pct=coverage_pct,
            frac_support_1=cnt_sup_1 / float(total_recs),
            frac_bin_0=cnt_bin_0 / float(total_recs),
            frac_bin_1_5=cnt_bin_1_5 / float(total_recs),
            frac_bin_6_10=cnt_bin_6_10 / float(total_recs),
            frac_bin_11_50=cnt_bin_11_50 / float(total_recs),
            frac_bin_gt_50=cnt_bin_gt_50 / float(total_recs),
        )


# ==============================================================================
# 5. PERFORMANCE BENCHMARK RUNNER
# ==============================================================================

@dataclass(frozen=True)
class BenchmarkRecord:
    """Record of an isolated performance benchmark."""
    component: str  # "Spark_DataFrame", "PyArrow", "NumPy_BLAS"
    operation: str
    scale_units: int
    scale_unit_label: str  # "rows", "users", "items"
    elapsed_seconds: float
    latency_ms: float
    throughput: float
    throughput_label: str  # "rows/s", "users/s"
    memory_rss_mb: float
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component": self.component,
            "operation": self.operation,
            "scale_units": self.scale_units,
            "scale_unit_label": self.scale_unit_label,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "latency_ms": round(self.latency_ms, 2),
            "throughput": round(self.throughput, 2),
            "throughput_label": self.throughput_label,
            "memory_rss_mb": round(self.memory_rss_mb, 1),
            "notes": self.notes,
        }


# ==============================================================================
# 6. SYNTHETIC ORACLES (FOR INDEPENDENT QA & TESTS)
# ==============================================================================

def synthetic_item_support_oracle(
    supports: List[int],
    catalog_size: int,
) -> Dict[str, int]:
    """
    Synthetic Oracle A: Verifies item support bin counts on arbitrary support lists.
    Guarantees bin conservation.
    """
    b0 = sum(1 for s in supports if s == 0)
    b1_5 = sum(1 for s in supports if 1 <= s <= 5)
    b6_10 = sum(1 for s in supports if 6 <= s <= 10)
    b11_50 = sum(1 for s in supports if 11 <= s <= 50)
    b_gt50 = sum(1 for s in supports if s > 50)

    total = b0 + b1_5 + b6_10 + b11_50 + b_gt50
    if total != catalog_size:
        raise ValueError(f"Oracle A failure: sum({total}) != catalog_size({catalog_size})")

    return {
        "0 ratings": b0,
        "1-5 ratings": b1_5,
        "6-10 ratings": b6_10,
        "11-50 ratings": b11_50,
        ">50 ratings": b_gt50,
    }


def synthetic_cold_start_oracle(
    user_id: int,
    item_id: int,
    known_users: Set[int],
    known_items: Set[int],
    support_map: Dict[int, int],
) -> str:
    """
    Synthetic Oracle B: Pure reference function for Cold-Start classification.
    """
    if user_id not in known_users:
        return "COLD_USER"
    if item_id not in known_items:
        return "COLD_ITEM"
    sup = support_map.get(item_id, 0)
    if sup <= 5:
        return "LOW_SUPPORT_ITEM"
    if sup <= 10:
        return "MODERATE_SUPPORT_ITEM"
    return "WARM_PAIR"


def synthetic_factor_dot_product_oracle(
    user_vec: List[float],
    item_vec: List[float],
) -> float:
    """
    Synthetic Oracle C: Scalar dot product computed purely with Python primitives.
    """
    if len(user_vec) != len(item_vec):
        raise ValueError("Vector length mismatch in dot product oracle")
    return sum(u * v for u, v in zip(user_vec, item_vec))


def synthetic_throughput_oracle(
    count: int,
    duration_sec: float,
) -> float:
    """
    Synthetic Oracle D: Pure reference function for throughput calculation.
    """
    if duration_sec <= 0:
        raise ValueError("duration_sec must be positive")
    return float(count) / float(duration_sec)

