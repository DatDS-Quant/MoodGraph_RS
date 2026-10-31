"""
Unit and Integration Tests for Module M05: Full Spark ALS Training Engine & Persistence.
Covers:
- Layer 1: ALSConfig validation guards and round-trip serialization.
- Layer 2: Training DataFrame schema and type validation.
- Layer 3: End-to-end ALS fitting, factor matrix extraction, and dimensionality audit.
- Layer 4: Independent mathematical verification (Spark transform vs manual dot product).
- Layer 5: Model persistence (save/load) and exact prediction reproducibility.
- Layer 6: Training diagnostic metrics (RMSE/MAE) and cold-start NaN handling.
"""

import json
import math
import tempfile
from pathlib import Path
import numpy as np
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DoubleType,
    FloatType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

from recommender.als.toy_als import TOY_TRAIN_RATINGS, create_toy_spark_dataframe
from recommender.als.trainer import (
    ALSConfig,
    ALSTrainer,
    FactorMatrixAuditResult,
)


@pytest.fixture(scope="session")
def spark_session() -> SparkSession:
    """Session-scoped SparkSession for fast test execution."""
    spark = (
        SparkSession.builder.appName("MoodGraph_M05_Trainer_Tests")
        .master("local[2]")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    yield spark
    spark.stop()


def test_01_config_validation_positive_rank():
    """Verify rank must be a positive integer."""
    cfg = ALSConfig(rank=16)
    cfg.validate()

    with pytest.raises(ValueError, match="rank must be a positive integer"):
        ALSConfig(rank=0).validate()

    with pytest.raises(ValueError, match="rank must be a positive integer"):
        ALSConfig(rank=-5).validate()


def test_02_config_validation_positive_max_iter():
    """Verify max_iter must be a positive integer."""
    cfg = ALSConfig(max_iter=10)
    cfg.validate()

    with pytest.raises(ValueError, match="max_iter must be a positive integer"):
        ALSConfig(max_iter=0).validate()

    with pytest.raises(ValueError, match="max_iter must be a positive integer"):
        ALSConfig(max_iter=-2).validate()


def test_03_config_validation_non_negative_reg_param():
    """Verify reg_param must be >= 0.0."""
    cfg_zero = ALSConfig(reg_param=0.0)
    cfg_zero.validate()

    cfg_pos = ALSConfig(reg_param=0.1)
    cfg_pos.validate()

    with pytest.raises(ValueError, match="reg_param must be a non-negative float"):
        ALSConfig(reg_param=-0.05).validate()


def test_04_config_validation_cold_start_strategy():
    """Verify cold_start_strategy must be 'nan' or 'drop'."""
    ALSConfig(cold_start_strategy="nan").validate()
    ALSConfig(cold_start_strategy="drop").validate()

    with pytest.raises(ValueError, match="cold_start_strategy must be 'nan' or 'drop'"):
        ALSConfig(cold_start_strategy="ignore").validate()


def test_05_config_serialization_round_trip():
    """Verify ALSConfig serializes to dict and reconstructs identically."""
    original = ALSConfig(
        rank=32,
        max_iter=15,
        reg_param=0.05,
        implicit_prefs=False,
        cold_start_strategy="nan",
        seed=100,
    )
    d = original.to_dict()
    reconstructed = ALSConfig.from_dict(d)
    assert original == reconstructed


def test_06_dataframe_validation_missing_columns(spark_session: SparkSession):
    """Trainer must reject DataFrame missing required user, item, or rating columns."""
    schema = StructType([
        StructField("user_id", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
    ])
    invalid_df = spark_session.createDataFrame([(1, 4.0)], schema=schema)
    trainer = ALSTrainer(ALSConfig(user_col="userId", item_col="movieId", rating_col="rating"))

    with pytest.raises(ValueError, match="missing required column"):
        trainer.validate_training_dataframe(invalid_df)


def test_07_dataframe_validation_incompatible_types(spark_session: SparkSession):
    """Trainer must reject non-integer user/item columns."""
    schema = StructType([
        StructField("userId", StringType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
    ])
    invalid_df = spark_session.createDataFrame([("user_1", 101, 4.0)], schema=schema)
    trainer = ALSTrainer()

    with pytest.raises(TypeError, match="must be IntegerType or LongType"):
        trainer.validate_training_dataframe(invalid_df)


def test_08_trainer_fit_on_toy_data(spark_session: SparkSession):
    """Trainer fits ALS on sample data and produces a valid ALSModel."""
    train_df = create_toy_spark_dataframe(spark_session, TOY_TRAIN_RATINGS)
    config = ALSConfig(rank=4, max_iter=5, reg_param=0.1, seed=42)
    trainer = ALSTrainer(config)

    model = trainer.fit(train_df)
    assert model.rank == 4
    assert model.userFactors.count() == 5  # 5 warm users in toy data
    assert model.itemFactors.count() == 6  # 6 warm movies in toy data


def test_09_factor_matrices_audit_correctness(spark_session: SparkSession):
    """Factor matrices audit checks counts, dimensions, norms, and absence of NaNs."""
    train_df = create_toy_spark_dataframe(spark_session, TOY_TRAIN_RATINGS)
    config = ALSConfig(rank=4, max_iter=5, reg_param=0.1, seed=42)
    trainer = ALSTrainer(config)
    model = trainer.fit(train_df)

    user_audit, item_audit = trainer.audit_factors(model)

    assert isinstance(user_audit, FactorMatrixAuditResult)
    assert user_audit.count == 5
    assert user_audit.rank == 4
    assert user_audit.has_nan is False
    assert user_audit.has_inf is False
    assert user_audit.norm_mean > 0.0
    assert user_audit.is_valid is True

    assert isinstance(item_audit, FactorMatrixAuditResult)
    assert item_audit.count == 6
    assert item_audit.rank == 4
    assert item_audit.has_nan is False
    assert item_audit.has_inf is False
    assert item_audit.norm_mean > 0.0
    assert item_audit.is_valid is True


def test_10_manual_dot_product_alignment(spark_session: SparkSession):
    """Spark model predictions match independent NumPy dot product within 1e-4 tolerance."""
    train_df = create_toy_spark_dataframe(spark_session, TOY_TRAIN_RATINGS)
    config = ALSConfig(rank=4, max_iter=10, reg_param=0.1, seed=42)
    trainer = ALSTrainer(config)
    model = trainer.fit(train_df)

    verification = trainer.verify_manual_dot_product(model, train_df, tolerance=1e-4)

    assert verification["all_matched"] is True
    assert verification["num_samples"] == len(TOY_TRAIN_RATINGS)
    assert verification["max_abs_diff"] <= 1e-4


def test_11_model_save_and_manifest_creation(spark_session: SparkSession):
    """Persisting model writes spark_model directory and manifest.json."""
    train_df = create_toy_spark_dataframe(spark_session, TOY_TRAIN_RATINGS)
    config = ALSConfig(rank=4, max_iter=5, reg_param=0.1, seed=42)
    trainer = ALSTrainer(config)
    model = trainer.fit(train_df)

    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = Path(tmp_dir) / "test_model"
        saved_dir = trainer.save_model(
            model=model,
            output_dir=save_path,
            metadata={"test_run": True, "git_commit": "test"},
        )

        assert (saved_dir / "spark_model").exists()
        assert (saved_dir / "manifest.json").exists()

        with open(saved_dir / "manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)

        assert manifest["config"]["rank"] == 4
        assert manifest["custom_metadata"]["test_run"] is True


def test_12_model_load_and_prediction_equivalence(spark_session: SparkSession):
    """Reloaded model reproduces predictions and rank identically to original model."""
    train_df = create_toy_spark_dataframe(spark_session, TOY_TRAIN_RATINGS)
    config = ALSConfig(rank=4, max_iter=5, reg_param=0.1, seed=42)
    trainer = ALSTrainer(config)
    original_model = trainer.fit(train_df)

    with tempfile.TemporaryDirectory() as tmp_dir:
        save_path = Path(tmp_dir) / "test_model"
        trainer.save_model(model=original_model, output_dir=save_path)

        reloaded_model, manifest = ALSTrainer.load_model(save_path)
        assert reloaded_model.rank == original_model.rank
        assert manifest["config"]["rank"] == 4

        verification = trainer.verify_reloaded_model(
            original_model=original_model,
            reloaded_model=reloaded_model,
            test_df=train_df,
        )
        assert verification["matched"] is True
        assert verification["max_absolute_prediction_diff"] <= 1e-6


def test_13_train_diagnostic_rmse_mae(spark_session: SparkSession):
    """Trainer calculates diagnostic RMSE and MAE on training interactions."""
    train_df = create_toy_spark_dataframe(spark_session, TOY_TRAIN_RATINGS)
    config = ALSConfig(rank=4, max_iter=10, reg_param=0.1, seed=42)
    trainer = ALSTrainer(config)
    model = trainer.fit(train_df)

    diag = trainer.compute_train_diagnostics(model, train_df)

    assert diag["sample_count"] == len(TOY_TRAIN_RATINGS)
    assert 0.0 < diag["diagnostic_rmse"] < 5.0
    assert 0.0 < diag["diagnostic_mae"] < 5.0


def test_14_cold_start_unseen_entities_in_test(spark_session: SparkSession):
    """When coldStartStrategy is 'nan', predictions for unseen entities are NaN."""
    train_df = create_toy_spark_dataframe(spark_session, TOY_TRAIN_RATINGS)
    config = ALSConfig(rank=4, max_iter=5, reg_param=0.1, cold_start_strategy="nan", seed=42)
    trainer = ALSTrainer(config)
    model = trainer.fit(train_df)

    cold_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
    ])
    cold_df = spark_session.createDataFrame([(99999, 88888, 3.5)], schema=cold_schema)

    preds = model.transform(cold_df).collect()
    assert len(preds) == 1
    val = preds[0]["prediction"]
    assert val is None or math.isnan(float(val))
