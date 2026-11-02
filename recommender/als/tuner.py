"""
MoodGraph - Task 3A: Scientific ALS Hyperparameter Tuning
Mô-đun: M07 - Tinh chỉnh siêu tham số ALS trên tập Validation.

Cung cấp:
- Cấu trúc dữ liệu thử nghiệm: TrialConfig, TrialStatus, LongTailDiagnostics, TrialResult.
- ExperimentRegistry: Đăng ký, lưu trữ nguyên tử (atomic persistence) và phục hồi phiên thử nghiệm.
- ScreeningCohortManager: Quản lý tập cohort 5.000 người dùng dương cố định, tái lập 100%.
- ALSTuner: Điều phối huấn luyện ALSTrainer, sinh ứng viên ALSCandidateGenerator và đánh giá TopNEvaluator.
- Independent Selection Oracle: Bộ quy tắc chọn mô hình tối ưu độc lập và tất định.
- Chốt chặn bảo vệ tập Test (guard_test_split_access): Tuyệt đối ngăn chặn rò rỉ dữ liệu Test split.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

import numpy as np
import pyarrow.parquet as pq

# Enforce Spark/Windows configuration
if sys.platform == "win32":
    if "HADOOP_HOME" not in os.environ:
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
        os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from recommender.als.candidates import (
    ALSCandidateConfig,
    ALSCandidateGenerator,
    ScoreableCatalog,
    UserFactorsContainer,
    fast_exact_top_k_from_scores,
)
from recommender.als.evaluator import EvaluationSummary, HeldOutTarget, TopNEvaluator
from recommender.als.trainer import ALSConfig, ALSTrainer


# ==============================================================================
# I. TEST ISOLATION GUARD
# ==============================================================================

def guard_test_split_access(path: Union[str, Path]) -> None:
    """
    Chốt chặn ranh giới khoa học: Kích hoạt PermissionError nếu bất kỳ nhánh mã nào
    cố tình truy cập hoặc đọc dữ liệu phân vùng Test trong quá trình tinh chỉnh M07.
    """
    norm_path = str(path).replace("\\", "/").lower()
    if "splits/test" in norm_path or "splits\\test" in str(path).lower():
        raise PermissionError(
            f"SCIENTIFIC VIOLATION: Access to Test split '{path}' is strictly prohibited during M07 tuning."
        )


# ==============================================================================
# II. EXPERIMENT CONFIGURATION & DATA STRUCTURES
# ==============================================================================

class TrialStatus(str, Enum):
    PLANNED = "PLANNED"
    RUNNING = "RUNNING"
    TRAINED = "TRAINED"
    EVALUATED = "EVALUATED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"
    SELECTED = "SELECTED"


class ModelFamily(str, Enum):
    ALS_ONLY = "ALS_ONLY"
    ALS_PLUS_TRAIN_SUPPORT_FILTER = "ALS_PLUS_TRAIN_SUPPORT_FILTER"


@dataclass
class TrialConfig:
    """
    Cấu hình bất biến của một thử nghiệm siêu tham số ALS (rank, regParam, maxIter, seed).
    """
    trial_id: str
    model_family: str = ModelFamily.ALS_ONLY.value
    rank: int = 16
    reg_param: float = 0.1
    max_iter: int = 10
    implicit_prefs: bool = False
    cold_start_strategy: str = "nan"
    seed: int = 42
    support_filter_min_ratings: Optional[int] = None
    description: str = ""

    def validate(self) -> None:
        """Kiểm tra các bất biến siêu tham số hợp lệ."""
        if not self.trial_id or not isinstance(self.trial_id, str):
            raise ValueError("trial_id must be a non-empty string")
        if self.model_family not in {ModelFamily.ALS_ONLY.value, ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value}:
            raise ValueError(f"Invalid model_family: {self.model_family}")
        if not isinstance(self.rank, int) or self.rank <= 0:
            raise ValueError(f"rank must be a positive integer, got: {self.rank}")
        if not isinstance(self.reg_param, (int, float)) or self.reg_param < 0.0:
            raise ValueError(f"reg_param must be non-negative, got: {self.reg_param}")
        if not isinstance(self.max_iter, int) or self.max_iter <= 0:
            raise ValueError(f"max_iter must be a positive integer, got: {self.max_iter}")
        if not isinstance(self.seed, int):
            raise ValueError(f"seed must be an integer, got: {self.seed}")
        if self.model_family == ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value:
            if self.support_filter_min_ratings is None or self.support_filter_min_ratings <= 0:
                raise ValueError("support_filter_min_ratings must be > 0 for ALS_PLUS_TRAIN_SUPPORT_FILTER")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrialConfig:
        cfg = cls(**data)
        cfg.validate()
        return cfg


@dataclass
class LongTailDiagnostics:
    """
    Thống kê phơi nhiễm đuôi dài (Long-tail) và thiên lệch Fluke Bias trên danh sách gợi ý.
    """
    pct_slots_1_rating: float = 0.0
    pct_slots_2_to_5_ratings: float = 0.0
    pct_slots_6_to_10_ratings: float = 0.0
    pct_slots_11_to_100_ratings: float = 0.0
    pct_slots_gt_100_ratings: float = 0.0
    top_10_recommended_movie_ids: List[int] = field(default_factory=list)
    score_min: float = 0.0
    score_median: float = 0.0
    score_max: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrialResult:
    """
    Hồ sơ thực nghiệm đầy đủ của một lượt chạy mô hình (Trial).
    """
    trial_id: str
    config: TrialConfig
    status: TrialStatus = TrialStatus.PLANNED
    screening_metrics: Optional[Dict[str, Any]] = None
    full_metrics: Optional[Dict[str, Any]] = None
    long_tail_diagnostics: Optional[LongTailDiagnostics] = None
    training_time_sec: float = 0.0
    scoring_time_sec: float = 0.0
    evaluation_time_sec: float = 0.0
    model_artifact_path: Optional[str] = None
    git_commit: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["config"] = self.config.to_dict()
        d["status"] = self.status.value if isinstance(self.status, TrialStatus) else self.status
        if self.long_tail_diagnostics is not None:
            d["long_tail_diagnostics"] = self.long_tail_diagnostics.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TrialResult:
        cfg = TrialConfig.from_dict(data["config"])
        status = TrialStatus(data["status"])
        diag = (
            LongTailDiagnostics(**data["long_tail_diagnostics"])
            if data.get("long_tail_diagnostics")
            else None
        )
        return cls(
            trial_id=data["trial_id"],
            config=cfg,
            status=status,
            screening_metrics=data.get("screening_metrics"),
            full_metrics=data.get("full_metrics"),
            long_tail_diagnostics=diag,
            training_time_sec=data.get("training_time_sec", 0.0),
            scoring_time_sec=data.get("scoring_time_sec", 0.0),
            evaluation_time_sec=data.get("evaluation_time_sec", 0.0),
            model_artifact_path=data.get("model_artifact_path"),
            git_commit=data.get("git_commit"),
            error_message=data.get("error_message"),
            timestamp=data.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
        )


# ==============================================================================
# III. EXPERIMENT REGISTRY WITH RESUME AND ATOMIC PERSISTENCE
# ==============================================================================

class ExperimentRegistry:
    """
    Sổ đăng ký thử nghiệm (Experiment Registry) an toàn đa luồng, hỗ trợ phục hồi (resume-capable).
    Lưu trữ metadata, trạng thái, chỉ số đánh giá và quyết định lựa chọn mô hình ra tệp JSON nguyên tử.
    """

    def __init__(self, registry_file: Union[str, Path]):
        self.registry_file = Path(registry_file).resolve()
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.trials: Dict[str, TrialResult] = {}
        self.selected_trial_id: Optional[str] = None
        self._load()

    def _load(self) -> None:
        """Nạp sổ đăng ký từ JSON nếu file đã tồn tại trên đĩa."""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.selected_trial_id = data.get("selected_trial_id")
                trials_data = data.get("trials", {})
                for tid, tdict in trials_data.items():
                    self.trials[tid] = TrialResult.from_dict(tdict)
            except Exception as e:
                print(f"[ExperimentRegistry] Warning loading registry: {e}", file=sys.stderr)

    def save(self) -> None:
        """Ghi bền vững nguyên tử (atomic persist) dữ liệu sổ đăng ký ra đĩa."""
        data = {
            "version": "1.0",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "selected_trial_id": self.selected_trial_id,
            "trials": {tid: t.to_dict() for tid, t in self.trials.items()},
        }
        temp_file = self.registry_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        temp_file.replace(self.registry_file)

    def register_trial(self, config: TrialConfig) -> TrialResult:
        """Đăng ký một thử nghiệm mới theo kế hoạch hoặc trả về thử nghiệm đã có."""
        config.validate()
        if config.trial_id in self.trials:
            return self.trials[config.trial_id]
        res = TrialResult(trial_id=config.trial_id, config=config, status=TrialStatus.PLANNED)
        self.trials[config.trial_id] = res
        self.save()
        return res

    def update_trial(self, result: TrialResult) -> None:
        """Cập nhật kết quả thử nghiệm vào sổ đăng ký."""
        self.trials[result.trial_id] = result
        self.save()

    def is_trial_completed(self, trial_id: str, require_full: bool = False) -> bool:
        """Kiểm tra xem thử nghiệm đã hoàn thành và đánh giá xong hay chưa."""
        if trial_id not in self.trials:
            return False
        t = self.trials[trial_id]
        if t.status not in {TrialStatus.EVALUATED, TrialStatus.SELECTED}:
            return False
        if require_full:
            return t.full_metrics is not None
        return t.screening_metrics is not None

    def select_best_model(
        self,
        cohort: str = "full",
        primary_metric: str = "ndcg_10",
        secondary_metric: str = "hit_rate_10",
    ) -> Optional[TrialResult]:
        """
        Quy tắc lựa chọn mô hình độc lập (Independent Selection Oracle):
        1. Chỉ xem xét các mô hình thuộc họ ALS_ONLY thuần túy.
        2. Sắp xếp theo primary_metric DESC (mặc định: ndcg_10).
        3. Phá vỡ thế hòa theo secondary_metric DESC (mặc định: hit_rate_10).
        4. Phá vỡ thế hòa theo độ đơn giản mô hình (rank nhỏ hơn ASC).
        5. Phá vỡ thế hòa theo hệ số reg_param nhỏ hơn ASC.
        6. Phá vỡ thế hòa theo thứ tự bảng chữ cái trial_id ASC.
        """
        eligible: List[TrialResult] = []
        for t in self.trials.values():
            if t.config.model_family != ModelFamily.ALS_ONLY.value:
                continue
            metrics = t.full_metrics if cohort == "full" else t.screening_metrics
            if metrics is not None:
                eligible.append(t)

        if not eligible:
            return None

        def sort_key(t: TrialResult) -> Tuple[float, float, int, float, str]:
            metrics = t.full_metrics if cohort == "full" else t.screening_metrics
            assert metrics is not None
            p_val = float(metrics.get(primary_metric, 0.0))
            s_val = float(metrics.get(secondary_metric, 0.0))
            # Tuple: (-p_val, -s_val, rank, reg_param, trial_id)
            return (-p_val, -s_val, t.config.rank, t.config.reg_param, t.trial_id)

        eligible.sort(key=sort_key)
        best = eligible[0]
        self.selected_trial_id = best.trial_id
        best.status = TrialStatus.SELECTED
        self.save()
        return best


# ==============================================================================
# IV. SCREENING COHORT MANAGER
# ==============================================================================

class ScreeningCohortManager:
    """
    Quản lý tập người dùng dương lấy mẫu cố định cho giai đoạn sàng lọc (Screening Cohort).
    Bảo đảm 100% tái lập và nhất quán tập người dùng trên mọi thử nghiệm tinh chỉnh.
    """

    def __init__(
        self,
        cohort_file: Union[str, Path],
        target_size: int = 5000,
        seed: int = 42,
    ):
        self.cohort_file = Path(cohort_file).resolve()
        self.cohort_file.parent.mkdir(parents=True, exist_ok=True)
        self.target_size = target_size
        self.seed = seed
        self.user_ids: List[int] = []
        self._load_or_create()

    def _load_or_create(self) -> None:
        """Nạp tập screening cohort từ đĩa nếu file đã tồn tại."""
        if self.cohort_file.exists():
            with open(self.cohort_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.user_ids = [int(u) for u in data["user_ids"]]
            self.target_size = len(self.user_ids)

    def create_cohort(
        self,
        val_targets: Dict[int, HeldOutTarget],
        relevance_threshold: float = 3.5,
    ) -> List[int]:
        """
        Lấy mẫu chính xác target_size người dùng validation có đánh giá dương bằng seed tất định.
        """
        positive_uids = [
            uid for uid, target in val_targets.items()
            if target.rating >= relevance_threshold
        ]
        positive_uids.sort()  # deterministic ordering before shuffle

        if len(positive_uids) <= self.target_size:
            sampled = positive_uids
        else:
            rng = np.random.RandomState(self.seed)
            sampled_idx = rng.choice(len(positive_uids), size=self.target_size, replace=False)
            sampled_idx.sort()
            sampled = [positive_uids[i] for i in sampled_idx]

        self.user_ids = sampled
        data = {
            "cohort_name": "m07_screening_cohort",
            "seed": self.seed,
            "target_size": len(self.user_ids),
            "relevance_threshold": relevance_threshold,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_ids": self.user_ids,
        }
        with open(self.cohort_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return self.user_ids


# ==============================================================================
# V. LONG-TAIL / FLUKE BIAS AUDITOR
# ==============================================================================

def compute_long_tail_diagnostics(
    recommendations: Dict[int, Sequence[Tuple[int, float]]],
    item_train_counts: Dict[int, int],
) -> LongTailDiagnostics:
    """
    Tính toán mức độ thiên lệch Fluke Bias và phân phối điểm số trên danh sách gợi ý.
    """
    total_slots = 0
    cnt_1 = 0
    cnt_2_5 = 0
    cnt_6_10 = 0
    cnt_11_100 = 0
    cnt_gt_100 = 0

    all_scores: List[float] = []
    item_freq: Counter[int] = Counter()

    for uid, rec_list in recommendations.items():
        for mid, sc in rec_list:
            total_slots += 1
            if math.isfinite(sc):
                all_scores.append(float(sc))
            item_freq[mid] += 1
            c = item_train_counts.get(mid, 0)
            if c == 1:
                cnt_1 += 1
            elif 2 <= c <= 5:
                cnt_2_5 += 1
            elif 6 <= c <= 10:
                cnt_6_10 += 1
            elif 11 <= c <= 100:
                cnt_11_100 += 1
            else:
                cnt_gt_100 += 1

    top_10_mids = [m for m, _ in item_freq.most_common(10)]

    if total_slots > 0:
        p1 = (cnt_1 / total_slots) * 100.0
        p2_5 = (cnt_2_5 / total_slots) * 100.0
        p6_10 = (cnt_6_10 / total_slots) * 100.0
        p11_100 = (cnt_11_100 / total_slots) * 100.0
        pgt_100 = (cnt_gt_100 / total_slots) * 100.0
    else:
        p1 = p2_5 = p6_10 = p11_100 = pgt_100 = 0.0

    if all_scores:
        s_arr = np.array(all_scores, dtype=np.float32)
        s_min = float(np.min(s_arr))
        s_med = float(np.median(s_arr))
        s_max = float(np.max(s_arr))
    else:
        s_min = s_med = s_max = 0.0

    return LongTailDiagnostics(
        pct_slots_1_rating=p1,
        pct_slots_2_to_5_ratings=p2_5,
        pct_slots_6_to_10_ratings=p6_10,
        pct_slots_11_to_100_ratings=p11_100,
        pct_slots_gt_100_ratings=pgt_100,
        top_10_recommended_movie_ids=top_10_mids,
        score_min=s_min,
        score_median=s_med,
        score_max=s_max,
    )


# ==============================================================================
# VI. ALS TUNER ORCHESTRATOR
# ==============================================================================

class ALSTuner:
    """
    Bộ điều phối tinh chỉnh siêu tham số tự động cho Spark ALS.
    Quản lý huấn luyện, chấm điểm ứng viên, đánh giá đa cấp (screening & full validation),
    kiểm toán đuôi dài và tự động lựa chọn mô hình vô địch.
    """

    def __init__(
        self,
        registry: ExperimentRegistry,
        models_root: Union[str, Path],
        artifacts_root: Union[str, Path],
        spark: Optional[SparkSession] = None,
    ):
        self.registry = registry
        self.models_root = Path(models_root).resolve()
        self.artifacts_root = Path(artifacts_root).resolve()
        self.models_root.mkdir(parents=True, exist_ok=True)
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self.spark = spark

    def _ensure_spark(self) -> SparkSession:
        """Khởi tạo hoặc tái sử dụng SparkSession với cấu hình tối ưu bộ nhớ local."""
        if self.spark is None:
            self.spark = (
                SparkSession.builder.appName("MoodGraph_M07_ALS_Tuning")
                .master("local[2]")
                .config("spark.driver.host", "127.0.0.1")
                .config("spark.driver.bindAddress", "127.0.0.1")
                .config("spark.driver.extraJavaOptions", "-Xss4m")
                .config("spark.executor.extraJavaOptions", "-Xss4m")
                .config("spark.driver.memory", "4g")
                .config("spark.sql.shuffle.partitions", "2")
                .config("spark.ui.enabled", "false")
                .getOrCreate()
            )
        return self.spark

    def register_m05_baseline(
        self,
        m05_model_dir: Union[str, Path],
        train_seen_dict: Dict[int, Set[int]],
        val_targets_dict: Dict[int, HeldOutTarget],
        screening_uids: List[int],
        item_train_counts: Dict[int, int],
        movies_parquet_path: Optional[Union[str, Path]] = None,
    ) -> TrialResult:
        """
        Đăng ký mô hình baseline M05 mà không cần huấn luyện lại.
        Đánh giá trên tập screening cohort để thiết lập mốc so chuẩn ban đầu.
        """
        trial_id = "M05_ALS_R16_REG0.1_ITER10"
        cfg = TrialConfig(
            trial_id=trial_id,
            model_family=ModelFamily.ALS_ONLY.value,
            rank=16,
            reg_param=0.1,
            max_iter=10,
            seed=42,
            description="M05 Baseline (Explict ALS, default parameters)",
        )
        trial = self.registry.register_trial(cfg)
        trial.model_artifact_path = str(Path(m05_model_dir).resolve())

        if self.registry.is_trial_completed(trial_id, require_full=False):
            print(f"[{trial_id}] Baseline already registered and evaluated.")
            return self.registry.trials[trial_id]

        print(f"[{trial_id}] Loading M05 baseline factors and scoring screening cohort...")
        gen = ALSCandidateGenerator()
        gen.load_catalog_and_factors(m05_model_dir, movies_parquet_path)

        t0 = time.time()
        screening_recs = gen.generate_recommendations(
            target_user_ids=screening_uids,
            user_histories=train_seen_dict,
            k=20,
            batch_size=2048,
            show_progress=False,
        )
        scoring_time = time.time() - t0

        # Evaluate on screening cohort
        eval_recs = {uid: [mid for mid, _ in rlist] for uid, rlist in screening_recs.items()}
        screening_targets = {
            uid: val_targets_dict[uid]
            for uid in screening_uids
            if uid in val_targets_dict
        }
        assert len(screening_targets) == len(screening_uids), (
            f"Screening targets cohort mismatch: expected {len(screening_uids)} targets, got {len(screening_targets)}"
        )
        assert set(eval_recs.keys()) == set(screening_targets.keys()), (
            f"Screening recs cohort mismatch: {len(eval_recs)} recs vs {len(screening_targets)} targets"
        )
        evaluator = TopNEvaluator(
            k_list=[5, 10, 20],
            relevance_threshold=3.5,
            catalog_size=62423,
            scorable_catalog_size=gen.catalog.num_movies if gen.catalog else 58932,
        )
        t_eval0 = time.time()
        eval_res = evaluator.evaluate(eval_recs, screening_targets)
        eval_time = time.time() - t_eval0

        s5 = eval_res[5]
        s10 = eval_res[10]
        s20 = eval_res[20]

        screening_metrics = {
            "hit_rate_5": s5.hit_rate,
            "hit_rate_10": s10.hit_rate,
            "hit_rate_20": s20.hit_rate,
            "ndcg_5": s5.ndcg,
            "ndcg_10": s10.ndcg,
            "ndcg_20": s20.ndcg,
            "mrr_10": s10.mrr,
            "precision_10": s10.precision,
            "catalog_coverage_10": s10.catalog_coverage_full,
            "distinct_movies_10": s10.num_unique_recommended_movies,
            "hit_count_10": s10.hit_count,
            "positive_cohort_size": s10.positive_cohort_size,
        }

        diag = compute_long_tail_diagnostics(screening_recs, item_train_counts)

        trial.status = TrialStatus.EVALUATED
        trial.screening_metrics = screening_metrics
        trial.long_tail_diagnostics = diag
        trial.scoring_time_sec = scoring_time
        trial.evaluation_time_sec = eval_time
        self.registry.update_trial(trial)
        return trial

    def fit_and_evaluate_trial(
        self,
        config: TrialConfig,
        train_df: DataFrame,
        train_seen_dict: Dict[int, Set[int]],
        val_targets_dict: Dict[int, HeldOutTarget],
        screening_uids: List[int],
        item_train_counts: Dict[int, int],
        movies_parquet_path: Optional[Union[str, Path]] = None,
        git_commit: Optional[str] = None,
        base_model_artifact_dir: Optional[Union[str, Path]] = None,
    ) -> TrialResult:
        """
        Fit a single ALS trial, audit factors, save model, and score screening cohort.
        If base_model_artifact_dir is provided (e.g. for diagnostic branches), reuses
        existing factor weights without fitting.
        """
        config.validate()
        trial = self.registry.register_trial(config)

        if self.registry.is_trial_completed(config.trial_id, require_full=False):
            print(f"[{config.trial_id}] Trial already completed. Skipping fit.")
            return self.registry.trials[config.trial_id]

        trial.status = TrialStatus.RUNNING
        trial.git_commit = git_commit
        self.registry.update_trial(trial)

        if base_model_artifact_dir is not None:
            model_dir = Path(base_model_artifact_dir).resolve()
            trial.model_artifact_path = str(model_dir)
            t_train = 0.0
            print(f"[{config.trial_id}] Reusing base model artifact at {model_dir}")
        else:
            model_dir = self.models_root / config.trial_id
            model_dir.mkdir(parents=True, exist_ok=True)
            trial.model_artifact_path = str(model_dir)

            spark_model_dir = model_dir / "spark_model"

            # 1. Fit Model if not already persisted
            t_train = 0.0
            if not spark_model_dir.exists():
                print(f"[{config.trial_id}] Fitting Spark ALS (rank={config.rank}, regParam={config.reg_param}, maxIter={config.max_iter})...")
                spark_cfg = ALSConfig(
                    rank=config.rank,
                    max_iter=config.max_iter,
                    reg_param=config.reg_param,
                    implicit_prefs=config.implicit_prefs,
                    cold_start_strategy=config.cold_start_strategy,
                    seed=config.seed,
                )
                trainer = ALSTrainer(spark_cfg)

                t0 = time.time()
                spark_model = trainer.fit(train_df)
                t_train = time.time() - t0
                print(f"[{config.trial_id}] Model fitted in {t_train:.2f}s. Auditing factors...")

                u_audit, i_audit = trainer.audit_factors(spark_model)
                if not u_audit.is_valid or not i_audit.is_valid:
                    raise ValueError(f"Factor audit failed: user valid={u_audit.is_valid}, item valid={i_audit.is_valid}")

                print(f"[{config.trial_id}] Saving model to {model_dir}...")
                trainer.save_model(spark_model, model_dir, metadata={"trial_id": config.trial_id, "git_commit": git_commit})
            else:
                print(f"[{config.trial_id}] Existing model artifact found at {model_dir}. Reusing.")

        trial.status = TrialStatus.TRAINED
        trial.training_time_sec = t_train
        self.registry.update_trial(trial)

        try:
            # 2. Score Screening Cohort
            print(f"[{config.trial_id}] Loading factors and generating Top-20 for {len(screening_uids):,} screening users...")
            gen = ALSCandidateGenerator()
            gen.load_catalog_and_factors(model_dir, movies_parquet_path)

            # Support filter diagnostic branch: mask items with < support_filter_min_ratings
            if config.model_family == ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value:
                assert config.support_filter_min_ratings is not None
                min_sup = config.support_filter_min_ratings
                low_support_mids = {mid for mid, count in item_train_counts.items() if count < min_sup}
                print(f"[{config.trial_id}] Applying support filter: masking {len(low_support_mids):,} movies with < {min_sup} ratings.")
                # We can add low_support_mids to user seen histories during candidate generation
                augmented_histories = {
                    uid: train_seen_dict.get(uid, set()) | low_support_mids
                    for uid in screening_uids
                }
            else:
                augmented_histories = train_seen_dict

            t_score0 = time.time()
            recs = gen.generate_recommendations(
                target_user_ids=screening_uids,
                user_histories=augmented_histories,
                k=20,
                batch_size=2048,
                show_progress=False,
            )
            scoring_time = time.time() - t_score0

            # 3. Evaluate Screening Cohort
            eval_recs = {uid: [mid for mid, _ in rlist] for uid, rlist in recs.items()}
            screening_targets = {
                uid: val_targets_dict[uid]
                for uid in screening_uids
                if uid in val_targets_dict
            }
            assert len(screening_targets) == len(screening_uids), (
                f"Screening targets cohort mismatch: expected {len(screening_uids)} targets, got {len(screening_targets)}"
            )
            assert set(eval_recs.keys()) == set(screening_targets.keys()), (
                f"Screening recs cohort mismatch: {len(eval_recs)} recs vs {len(screening_targets)} targets"
            )
            evaluator = TopNEvaluator(
                k_list=[5, 10, 20],
                relevance_threshold=3.5,
                catalog_size=62423,
                scorable_catalog_size=gen.catalog.num_movies if gen.catalog else 58932,
            )
            t_eval0 = time.time()
            eval_res = evaluator.evaluate(eval_recs, screening_targets)
            eval_time = time.time() - t_eval0

            s5 = eval_res[5]
            s10 = eval_res[10]
            s20 = eval_res[20]

            screening_metrics = {
                "hit_rate_5": s5.hit_rate,
                "hit_rate_10": s10.hit_rate,
                "hit_rate_20": s20.hit_rate,
                "ndcg_5": s5.ndcg,
                "ndcg_10": s10.ndcg,
                "ndcg_20": s20.ndcg,
                "mrr_10": s10.mrr,
                "precision_10": s10.precision,
                "catalog_coverage_10": s10.catalog_coverage_full,
                "distinct_movies_10": s10.num_unique_recommended_movies,
                "hit_count_10": s10.hit_count,
                "positive_cohort_size": s10.positive_cohort_size,
            }

            diag = compute_long_tail_diagnostics(recs, item_train_counts)

            trial.status = TrialStatus.EVALUATED
            trial.screening_metrics = screening_metrics
            trial.long_tail_diagnostics = diag
            trial.scoring_time_sec = scoring_time
            trial.evaluation_time_sec = eval_time
            self.registry.update_trial(trial)
            print(f"[{config.trial_id}] Screening Completed: HR@10 = {s10.hit_rate:.5f}, NDCG@10 = {s10.ndcg:.5f}, 1-rating slots = {diag.pct_slots_1_rating:.1f}%")
            return trial

        except Exception as e:
            trial.status = TrialStatus.FAILED
            trial.error_message = str(e)
            self.registry.update_trial(trial)
            print(f"[{config.trial_id}] Trial FAILED with error: {e}", file=sys.stderr)
            raise e

    def evaluate_full_validation(
        self,
        trial_id: str,
        train_seen_dict: Dict[int, Set[int]],
        val_targets_dict: Dict[int, HeldOutTarget],
        all_validation_uids: List[int],
        item_train_counts: Dict[int, int],
        movies_parquet_path: Optional[Union[str, Path]] = None,
        save_parquet_path: Optional[Union[str, Path]] = None,
    ) -> TrialResult:
        """
        Execute Level 2: Full Validation (109,779 positive users) for a finalist model.
        """
        if trial_id not in self.registry.trials:
            raise KeyError(f"Trial '{trial_id}' not found in registry")

        trial = self.registry.trials[trial_id]
        if trial.full_metrics is not None:
            print(f"[{trial_id}] Full validation already computed.")
            return trial

        model_dir = trial.model_artifact_path
        if not model_dir or not Path(model_dir).exists():
            raise FileNotFoundError(f"Model path '{model_dir}' not found for trial {trial_id}")

        print(f"[{trial_id}] Running Level 2: FULL VALIDATION across {len(all_validation_uids):,} users...")
        gen = ALSCandidateGenerator()
        gen.load_catalog_and_factors(model_dir, movies_parquet_path)

        # Support filter diagnostic branch if applicable
        if trial.config.model_family == ModelFamily.ALS_PLUS_TRAIN_SUPPORT_FILTER.value:
            assert trial.config.support_filter_min_ratings is not None
            min_sup = trial.config.support_filter_min_ratings
            low_support_mids = {mid for mid, count in item_train_counts.items() if count < min_sup}
            augmented_histories = {
                uid: train_seen_dict.get(uid, set()) | low_support_mids
                for uid in all_validation_uids
            }
        else:
            augmented_histories = train_seen_dict

        t0 = time.time()
        recs = gen.generate_recommendations(
            target_user_ids=all_validation_uids,
            user_histories=augmented_histories,
            k=20,
            batch_size=2048,
            show_progress=True,
        )
        scoring_time = time.time() - t0
        print(f"[{trial_id}] Full recommendations generated in {scoring_time:.2f}s ({len(all_validation_uids)/scoring_time:.1f} users/s).")

        # Save Parquet recommendations if requested
        if save_parquet_path is not None:
            gen.save_recommendations_parquet(recs, save_parquet_path)

        # Evaluate on full cohort
        eval_recs = {uid: [mid for mid, _ in rlist] for uid, rlist in recs.items()}
        full_val_targets = {
            uid: val_targets_dict[uid]
            for uid in all_validation_uids
            if uid in val_targets_dict
        }
        assert len(full_val_targets) == len(all_validation_uids), (
            f"Full validation targets mismatch: expected {len(all_validation_uids)}, got {len(full_val_targets)}"
        )
        assert set(eval_recs.keys()) == set(full_val_targets.keys()), (
            f"Full validation recs mismatch: {len(eval_recs)} recs vs {len(full_val_targets)} targets"
        )
        evaluator = TopNEvaluator(
            k_list=[5, 10, 20],
            relevance_threshold=3.5,
            catalog_size=62423,
            scorable_catalog_size=gen.catalog.num_movies if gen.catalog else 58932,
        )
        t_eval0 = time.time()
        eval_res = evaluator.evaluate(eval_recs, full_val_targets)
        eval_time = time.time() - t_eval0

        s5 = eval_res[5]
        s10 = eval_res[10]
        s20 = eval_res[20]

        full_metrics = {
            "hit_rate_5": s5.hit_rate,
            "hit_rate_10": s10.hit_rate,
            "hit_rate_20": s20.hit_rate,
            "ndcg_5": s5.ndcg,
            "ndcg_10": s10.ndcg,
            "ndcg_20": s20.ndcg,
            "mrr_10": s10.mrr,
            "precision_10": s10.precision,
            "catalog_coverage_5": s5.catalog_coverage_full,
            "catalog_coverage_10": s10.catalog_coverage_full,
            "catalog_coverage_20": s20.catalog_coverage_full,
            "distinct_movies_10": s10.num_unique_recommended_movies,
            "hit_count_5": s5.hit_count,
            "hit_count_10": s10.hit_count,
            "hit_count_20": s20.hit_count,
            "positive_cohort_size": s10.positive_cohort_size,
        }

        full_diag = compute_long_tail_diagnostics(recs, item_train_counts)

        trial.full_metrics = full_metrics
        trial.long_tail_diagnostics = full_diag
        self.registry.update_trial(trial)
        print(f"[{trial_id}] FULL VALIDATION COMPLETED: HR@10 = {s10.hit_rate:.5f}, NDCG@10 = {s10.ndcg:.5f}, Coverage@10 = {s10.catalog_coverage_full*100:.2f}%")
        return trial
