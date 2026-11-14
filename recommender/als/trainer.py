"""
MoodGraph - Task 3A: Spark ALS
Mô-đun: M05 - Động cơ huấn luyện Spark ALS và lưu trữ mô hình chuẩn Production.

Cung cấp toàn bộ quy trình huấn luyện Collaborative Filtering thông qua
Apache Spark MLlib ALS trên tập dữ liệu MovieLens 25M:
1. ALSConfig: Cấu hình siêu tham số nghiêm ngặt với các chốt chặn kiểm tra.
2. Huấn luyện phân tán: pyspark.ml.recommendation.ALS trên dữ liệu đánh giá hiện (explicit feedback).
3. Kiểm toán ma trận nhân tố (FactorMatrixAuditResult): Kiểm tra kích thước rank, NaN/Inf và chuẩn L2.
4. Kiểm chứng toán học độc lập: So khớp dự đoán của Spark transform với tích vô hướng thủ công.
5. Lưu trữ và nạp mô hình (save/load) kèm metadata manifest đầy đủ.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

if sys.platform.startswith("win"):
    if os.path.exists(r"C:\hadoop"):
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
        os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import numpy as np
from pyspark.ml.recommendation import ALS, ALSModel
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, FloatType, IntegerType, LongType, StructType


# ==============================================================================
# I. CẤU HÌNH KÈM CÁC CHỐT CHẶN BẢO VỆ (CONFIGURATION WITH GUARDS)
# ==============================================================================

@dataclass
class ALSConfig:
    """
    Cấu hình siêu tham số và thiết lập thực thi cho thuật toán Spark ALS (Matrix Factorization):
    
    Hàm mục tiêu toán học (Loss Function) giải bằng phương pháp luân phiên (Alternating):
      Mất mát = Tổng_(u, i có rating) [ r_ui - (User_u . Item_i) ]^2 + λ * [ Tổng_u ||User_u||^2 + Tổng_i ||Item_i||^2 ]
    
    Ý nghĩa các siêu tham số:
    - rank (k = 16 hoặc 32): Số chiều của không gian nhân tố ẩn (Latent Dimension).
    - max_iter (10 hoặc 15): Số vòng lặp luân phiên tối ưu giữa ma trận User và Item.
    - reg_param (λ = 0.1): Hệ số điều chuẩn L2 (Regularization) chống hiện tượng quá khớp (Overfitting).
    - implicit_prefs (False): Dữ liệu MovieLens 25M là rating tường minh (Explicit Feedback: 0.5 - 5.0 sao).
    - cold_start_strategy ('nan'): Tránh gán nhãn 0 giả định; chuyển giao cho Đồ thị tri thức xử lý khi cold-start.
    - intermediate_storage_level ('MEMORY_AND_DISK'): Cache phân vùng trung gian để chống tràn RAM máy trạm.
    """
    rank: int = 16
    max_iter: int = 10
    reg_param: float = 0.1
    implicit_prefs: bool = False
    cold_start_strategy: str = "nan"
    seed: int = 42
    user_col: str = "userId"
    item_col: str = "movieId"
    rating_col: str = "rating"
    intermediate_storage_level: str = "MEMORY_AND_DISK"
    final_storage_level: str = "MEMORY_AND_DISK"
    checkpoint_interval: int = 10

    def validate(self) -> None:
        """Thực thi ràng buộc hợp đồng cấu hình nghiêm ngặt trước khi chạy huấn luyện."""
        if not isinstance(self.rank, int) or self.rank <= 0:
            raise ValueError(f"rank must be a positive integer, got: {self.rank}")
        if not isinstance(self.max_iter, int) or self.max_iter <= 0:
            raise ValueError(f"max_iter must be a positive integer, got: {self.max_iter}")
        if not isinstance(self.reg_param, (int, float)) or self.reg_param < 0.0:
            raise ValueError(f"reg_param must be a non-negative float, got: {self.reg_param}")
        if self.cold_start_strategy not in {"nan", "drop"}:
            raise ValueError(
                f"cold_start_strategy must be 'nan' or 'drop', got: '{self.cold_start_strategy}'"
            )
        if not isinstance(self.seed, int):
            raise ValueError(f"seed must be an integer, got: {self.seed}")
        if not self.user_col or not isinstance(self.user_col, str):
            raise ValueError("user_col must be a non-empty string")
        if not self.item_col or not isinstance(self.item_col, str):
            raise ValueError("item_col must be a non-empty string")
        if not self.rating_col or not isinstance(self.rating_col, str):
            raise ValueError("rating_col must be a non-empty string")

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi cấu hình sang từ điển phục vụ lưu trữ JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ALSConfig:
        """Tạo đối tượng cấu hình từ từ điển kèm kiểm tra tính hợp lệ."""
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        cfg = cls(**filtered)
        cfg.validate()
        return cfg


# ==============================================================================
# II. KẾT QUẢ KIỂM TOÁN MA TRẬN NHÂN TỐ (FACTOR MATRIX AUDIT RESULT)
# ==============================================================================

@dataclass
class FactorMatrixAuditResult:
    """Kết quả kiểm toán ma trận nhân tố ẩn ALS (userFactors hoặc itemFactors)."""
    factor_type: str
    count: int
    rank: int
    has_nan: bool
    has_inf: bool
    norm_min: float
    norm_max: float
    norm_mean: float
    norm_std: float
    is_valid: bool

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi kết quả kiểm toán sang dictionary."""
        return asdict(self)


# ==============================================================================
# III. ĐỘNG CƠ HUẤN LUYỆN SPARK ALS (SPARK ALS TRAINER ENGINE)
# ==============================================================================

class ALSTrainer:
    """
    Động cơ huấn luyện ALS chuẩn Production trên MovieLens 25M Collaborative Filtering.
    """

    def __init__(self, config: Optional[ALSConfig] = None):
        self.config = config if config is not None else ALSConfig()
        self.config.validate()

    def validate_training_dataframe(self, df: DataFrame) -> None:
        """
        Xác minh DataFrame đầu vào tuân thủ các yêu cầu của Spark ALS:
        - Các cột bắt buộc tồn tại: user_col, item_col, rating_col.
        - Kiểu dữ liệu: user_col và item_col phải là IntegerType (hoặc LongType).
        - Cột rating phải là FloatType hoặc DoubleType.
        """
        fields = {field.name: field.dataType for field in df.schema.fields}
        for col_name in [self.config.user_col, self.config.item_col, self.config.rating_col]:
            if col_name not in fields:
                raise ValueError(
                    f"Training DataFrame is missing required column: '{col_name}'. "
                    f"Available columns: {list(fields.keys())}"
                )

        u_type = fields[self.config.user_col]
        i_type = fields[self.config.item_col]
        r_type = fields[self.config.rating_col]

        if not isinstance(u_type, (IntegerType, LongType)):
            raise TypeError(
                f"user_col '{self.config.user_col}' must be IntegerType or LongType, got {u_type}"
            )
        if not isinstance(i_type, (IntegerType, LongType)):
            raise TypeError(
                f"item_col '{self.config.item_col}' must be IntegerType or LongType, got {i_type}"
            )
        if not isinstance(r_type, (FloatType, DoubleType)):
            raise TypeError(
                f"rating_col '{self.config.rating_col}' must be FloatType or DoubleType, got {r_type}"
            )

    def fit(self, train_df: DataFrame) -> ALSModel:
        """
        Huấn luyện PySpark ALS trên ratings hiện (explicit feedback).
        
        Args:
            train_df: DataFrame phân tán với các cột (userId, movieId, rating).
            
        Returns:
            Mô hình ALSModel đã khớp.
        """
        self.validate_training_dataframe(train_df)

        als = ALS(
            userCol=self.config.user_col,
            itemCol=self.config.item_col,
            ratingCol=self.config.rating_col,
            implicitPrefs=self.config.implicit_prefs,
            rank=self.config.rank,
            maxIter=self.config.max_iter,
            regParam=self.config.reg_param,
            seed=self.config.seed,
            coldStartStrategy=self.config.cold_start_strategy,
            intermediateStorageLevel=self.config.intermediate_storage_level,
            finalStorageLevel=self.config.final_storage_level,
            checkpointInterval=self.config.checkpoint_interval,
        )

        model = als.fit(train_df)
        return model

    def audit_factors(self, model: ALSModel) -> Tuple[FactorMatrixAuditResult, FactorMatrixAuditResult]:
        """
        Kiểm toán cả hai DataFrame userFactors và itemFactors:
        - Đếm số lượng ID nhân tố phân biệt.
        - Xác minh số chiều vector bằng đúng rank cấu hình.
        - Kiểm tra các giá trị NaN hoặc Vô cực (Inf).
        - Tính toán thống kê phân phối chuẩn L2 của các vector.
        """
        def _audit_single_matrix(df: DataFrame, factor_name: str) -> FactorMatrixAuditResult:
            rows = df.select("id", "features").collect()
            count = len(rows)
            if count == 0:
                return FactorMatrixAuditResult(
                    factor_type=factor_name,
                    count=0,
                    rank=self.config.rank,
                    has_nan=False,
                    has_inf=False,
                    norm_min=0.0,
                    norm_max=0.0,
                    norm_mean=0.0,
                    norm_std=0.0,
                    is_valid=False,
                )

            norms: List[float] = []
            has_nan = False
            has_inf = False
            wrong_rank_count = 0

            for r in rows:
                features = r["features"]
                if len(features) != self.config.rank:
                    wrong_rank_count += 1
                arr = np.array(features, dtype=np.float64)
                if np.isnan(arr).any():
                    has_nan = True
                if np.isinf(arr).any():
                    has_inf = True
                norms.append(float(np.linalg.norm(arr)))

            norm_arr = np.array(norms, dtype=np.float64)
            is_valid = (
                count > 0
                and wrong_rank_count == 0
                and not has_nan
                and not has_inf
            )

            return FactorMatrixAuditResult(
                factor_type=factor_name,
                count=count,
                rank=self.config.rank,
                has_nan=has_nan,
                has_inf=has_inf,
                norm_min=float(np.min(norm_arr)),
                norm_max=float(np.max(norm_arr)),
                norm_mean=float(np.mean(norm_arr)),
                norm_std=float(np.std(norm_arr)),
                is_valid=is_valid,
            )

        user_audit = _audit_single_matrix(model.userFactors, "userFactors")
        item_audit = _audit_single_matrix(model.itemFactors, "itemFactors")
        return user_audit, item_audit

    def verify_manual_dot_product(
        self,
        model: ALSModel,
        sample_df: DataFrame,
        tolerance: float = 1e-4,
    ) -> Dict[str, Any]:
        """
        Xác minh dự đoán của phép biến đổi Spark transform khớp với tích vô hướng thủ công độc lập:
        r_hat = p_u^T q_i
        """
        u_col = self.config.user_col
        i_col = self.config.item_col

        # Dự đoán bằng hàm transform của Spark
        predictions_df = model.transform(sample_df).select(
            u_col, i_col, self.config.rating_col, "prediction"
        )
        sample_rows = predictions_df.collect()

        sample_user_ids = {int(r[u_col]) for r in sample_rows}
        sample_movie_ids = {int(r[i_col]) for r in sample_rows}

        # Thu thập vector người dùng cho các mẫu kiểm thử
        user_factors_sample = (
            model.userFactors.filter(F.col("id").isin(list(sample_user_ids)))
            .select("id", "features")
            .collect()
        )
        u_dict = {int(r["id"]): np.array(r["features"], dtype=np.float64) for r in user_factors_sample}

        # Thu thập vector phim cho các mẫu kiểm thử
        item_factors_sample = (
            model.itemFactors.filter(F.col("id").isin(list(sample_movie_ids)))
            .select("id", "features")
            .collect()
        )
        i_dict = {int(r["id"]): np.array(r["features"], dtype=np.float64) for r in item_factors_sample}

        max_abs_diff = 0.0
        sum_abs_diff = 0.0
        comparison_records: List[Dict[str, Any]] = []

        for r in sample_rows:
            uid = int(r[u_col])
            mid = int(r[i_col])
            spark_pred = float(r["prediction"]) if r["prediction"] is not None else float("nan")

            if uid in u_dict and mid in i_dict:
                manual_dot = float(np.dot(u_dict[uid], i_dict[mid]))
                abs_diff = abs(spark_pred - manual_dot)
                max_abs_diff = max(max_abs_diff, abs_diff)
                sum_abs_diff += abs_diff
                matched = abs_diff <= tolerance
                comparison_records.append({
                    "userId": uid,
                    "movieId": mid,
                    "true_rating": float(r[self.config.rating_col]),
                    "spark_prediction": spark_pred,
                    "manual_dot": manual_dot,
                    "abs_diff": abs_diff,
                    "matched": matched,
                })
            else:
                comparison_records.append({
                    "userId": uid,
                    "movieId": mid,
                    "true_rating": float(r[self.config.rating_col]),
                    "spark_prediction": spark_pred,
                    "manual_dot": None,
                    "abs_diff": float("inf"),
                    "matched": False,
                })

        num_samples = len(comparison_records)
        mean_abs_diff = sum_abs_diff / num_samples if num_samples > 0 else 0.0
        all_matched = (
            num_samples > 0
            and all(rec["matched"] for rec in comparison_records)
            and max_abs_diff <= tolerance
        )

        return {
            "num_samples": num_samples,
            "max_abs_diff": max_abs_diff,
            "mean_abs_diff": mean_abs_diff,
            "tolerance": tolerance,
            "all_matched": all_matched,
            "sample_records": comparison_records,
        }

    def compute_train_diagnostics(
        self,
        model: ALSModel,
        sample_df: DataFrame,
    ) -> Dict[str, float]:
        """
        Tính toán các chỉ số chẩn đoán RMSE và MAE trên một mẫu đánh giá của tập huấn luyện.
        
        LƯU Ý: Đây chỉ là chỉ số chẩn đoán kỹ thuật nội bộ, TUYỆT ĐỐI KHÔNG ĐƯỢC coi là
        hiệu năng tổng quát hóa hay chất lượng gợi ý Top-N.
        """
        predictions_df = model.transform(sample_df).filter(
            F.col("prediction").isNotNull() & ~F.isnan(F.col("prediction"))
        )

        diff_df = predictions_df.withColumn(
            "err", F.col(self.config.rating_col) - F.col("prediction")
        ).withColumn(
            "sq_err", F.col("err") * F.col("err")
        ).withColumn(
            "abs_err", F.abs(F.col("err"))
        )

        stats = diff_df.select(
            F.count("err").alias("count"),
            F.sum("sq_err").alias("sum_sq"),
            F.sum("abs_err").alias("sum_abs"),
        ).first()

        count = int(stats["count"]) if stats and stats["count"] is not None else 0
        if count == 0:
            return {"sample_count": 0.0, "diagnostic_rmse": 0.0, "diagnostic_mae": 0.0}

        sum_sq = float(stats["sum_sq"])
        sum_abs = float(stats["sum_abs"])
        rmse = math.sqrt(sum_sq / count)
        mae = sum_abs / count

        return {
            "sample_count": float(count),
            "diagnostic_rmse": rmse,
            "diagnostic_mae": mae,
        }

    def save_model(
        self,
        model: ALSModel,
        output_dir: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
        overwrite: bool = True,
    ) -> Path:
        """
        Lưu mô hình Spark ALSModel đã khớp và ghi tập tin manifest kiểm toán chuẩn mực.
        
        Cấu trúc thư mục đầu ra:
            output_dir/
                spark_model/         <- Lưu trữ mô hình nguyên bản của PySpark
                manifest.json        <- Tập tin manifest siêu dữ liệu
        """
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        model_save_path = out_path / "spark_model"
        writer = model.write()
        if overwrite:
            writer = writer.overwrite()
        writer.save(str(model_save_path))

        manifest_data = {
            "model_version": "m05_spark_als",
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "config": self.config.to_dict(),
            "spark_model_path": str(model_save_path),
            "custom_metadata": metadata or {},
        }

        manifest_file = out_path / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)

        return out_path

    @staticmethod
    def load_model(model_dir: Union[str, Path]) -> Tuple[ALSModel, Dict[str, Any]]:
        """
        Nạp mô hình ALSModel đã lưu trữ cùng tập tin manifest siêu dữ liệu.
        
        Returns:
            Tuple gồm (ALSModel, manifest_dict)
        """
        path = Path(model_dir).resolve()
        spark_model_path = path / "spark_model"
        manifest_file = path / "manifest.json"

        if not spark_model_path.exists():
            raise FileNotFoundError(f"Persisted Spark model not found at: {spark_model_path}")

        manifest: Dict[str, Any] = {}
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        model = ALSModel.load(str(spark_model_path))
        return model, manifest

    def verify_reloaded_model(
        self,
        original_model: ALSModel,
        reloaded_model: ALSModel,
        test_df: DataFrame,
    ) -> Dict[str, Any]:
        """
        Xác minh mô hình nạp lại tạo ra các dự đoán và kích thước nhân tố giống hệt
        như mô hình ban đầu trong bộ nhớ.
        
        Sử dụng cơ chế lập chỉ mục theo khóa (userId, movieId) để loại bỏ sai lệch
        do khác biệt thứ tự phân vùng khi xáo trộn (shuffle) phân tán.
        """
        orig_preds = original_model.transform(test_df).select(
            self.config.user_col, self.config.item_col, "prediction"
        ).collect()
        reload_preds = reloaded_model.transform(test_df).select(
            self.config.user_col, self.config.item_col, "prediction"
        ).collect()

        orig_dict = {
            (int(r[self.config.user_col]), int(r[self.config.item_col])): (
                float(r["prediction"]) if r["prediction"] is not None else None
            )
            for r in orig_preds
        }
        reload_dict = {
            (int(r[self.config.user_col]), int(r[self.config.item_col])): (
                float(r["prediction"]) if r["prediction"] is not None else None
            )
            for r in reload_preds
        }

        if set(orig_dict.keys()) != set(reload_dict.keys()):
            return {
                "matched": False,
                "reason": "Key set mismatch between original and reloaded predictions",
            }

        max_diff = 0.0
        for k in orig_dict:
            p1 = orig_dict[k]
            p2 = reload_dict[k]
            if p1 is None and p2 is None:
                continue
            if (p1 is None) != (p2 is None):
                return {
                    "matched": False,
                    "reason": f"Null prediction discrepancy for key {k}: {p1} vs {p2}",
                }
            diff = abs(p1 - p2)
            max_diff = max(max_diff, diff)

        matched = max_diff <= 1e-5
        return {
            "matched": matched,
            "max_absolute_prediction_diff": max_diff,
            "sample_count": len(orig_dict),
            "rank_original": original_model.rank,
            "rank_reloaded": reloaded_model.rank,
        }
