"""
Unit and Integration Tests for Module M04: ALS Theory, Toy Fit & Latent Factor Inspection.
Covers:
- Hand-calculated dot product and loss formulas.
- Verified Golden Example (An, Binh, Movies A, B, C).
- Pure Python reference ALS solver convergence.
- PySpark ALS fitting, factor extraction, and dot product verification.
- Explicit feedback contract (unobserved != 0).
- Cold-start behavior ('nan' vs 'drop').
- Reproducibility and regularization shrinkage.
- Geometric counterexample (Euclidean distance vs dot product).
"""

import math
import numpy as np
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

from recommender.als.toy_als import (
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


@pytest.fixture(scope="session")
def spark_session() -> SparkSession:
    """Session-scoped SparkSession for fast test execution."""
    spark = (
        SparkSession.builder.appName("MoodGraph_M04_ToyALS_Tests")
        .master("local[2]")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.shuffle.partitions", "2")
        .getOrCreate()
    )
    yield spark
    spark.stop()


def test_01_hand_calculated_dot_product():
    """Verify dot product r_hat = p_u^T q_i on 1D, 2D, and 3D vectors."""
    # 1D
    u1 = np.array([2.5])
    i1 = np.array([1.6])
    assert math.isclose(compute_dot_product(u1, i1), 4.0, abs_tol=1e-6)

    # 2D
    u2 = np.array([1.2, 3.4])
    i2 = np.array([0.5, -1.0])
    # 1.2 * 0.5 + 3.4 * (-1.0) = 0.6 - 3.4 = -2.8
    assert math.isclose(compute_dot_product(u2, i2), -2.8, abs_tol=1e-6)

    # 3D
    u3 = np.array([1.0, 2.0, 3.0])
    i3 = np.array([4.0, 5.0, 6.0])
    # 4 + 10 + 18 = 32
    assert math.isclose(compute_dot_product(u3, i3), 32.0, abs_tol=1e-6)

    # Dimension mismatch should raise ValueError
    with pytest.raises(ValueError, match="Dimension mismatch"):
        compute_dot_product(np.array([1.0, 2.0]), np.array([1.0]))


def test_02_hand_calculated_als_loss_without_reg():
    """Verify explicit ALS loss calculation with lambda = 0.0."""
    ratings = [
        (1, 10, 4.0),
        (2, 20, 2.0),
    ]
    user_factors = {
        1: np.array([2.0, 1.0]),
        2: np.array([1.0, 0.0]),
    }
    item_factors = {
        10: np.array([1.5, 0.5]),  # pred = 2.0*1.5 + 1.0*0.5 = 3.0 + 0.5 = 3.5 -> err = 4.0 - 3.5 = 0.5 -> sq = 0.25
        20: np.array([2.0, 3.0]),  # pred = 1.0*2.0 + 0.0*3.0 = 2.0 -> err = 2.0 - 2.0 = 0.0 -> sq = 0.0
    }
    # Total loss = 0.25 + 0.0 = 0.25
    loss = compute_als_loss(ratings, user_factors, item_factors, reg_param=0.0)
    assert math.isclose(loss, 0.25, abs_tol=1e-6)


def test_03_hand_calculated_als_loss_with_reg():
    """Verify explicit ALS loss with Frobenius regularization."""
    ratings = [(1, 10, 5.0)]
    user_factors = {1: np.array([2.0, 0.0])}  # norm_sq = 4.0
    item_factors = {10: np.array([2.0, 1.0])} # norm_sq = 4.0 + 1.0 = 5.0
    # pred = 4.0 -> err = 5.0 - 4.0 = 1.0 -> sq = 1.0
    # reg sum = lambda * (4.0 + 5.0) = 0.1 * 9.0 = 0.9
    # Total loss = 1.0 + 0.9 = 1.9
    loss = compute_als_loss(ratings, user_factors, item_factors, reg_param=0.1)
    assert math.isclose(loss, 1.9, abs_tol=1e-6)


def test_04_golden_example_step_by_step():
    """Verify the exact Golden Example step-by-step hand calculation."""
    res = verify_golden_example_step()
    assert math.isclose(res["p_An"], 2.0, abs_tol=1e-6)
    assert math.isclose(res["p_Binh"], 1.0, abs_tol=1e-6)
    assert math.isclose(res["q_C_updated"], 1.5, abs_tol=1e-6)
    assert math.isclose(res["pred_An_on_C"], 3.0, abs_tol=1e-6)


def test_05_reference_als_solver_monotonic_loss_decrease():
    """Verify that pure Python reference solver converges and monotonically decreases loss."""
    ratings = TOY_TRAIN_RATINGS
    user_factors, item_factors, loss_history = run_toy_als_reference(
        ratings=ratings,
        rank=2,
        max_iter=10,
        reg_param=0.01,
        seed=42,
    )
    assert len(loss_history) == 11
    # Check that final loss is significantly lower than initial loss
    assert loss_history[-1] < loss_history[0]
    # Check that after the first step, loss decreases or stabilizes
    for step in range(1, len(loss_history) - 1):
        assert loss_history[step + 1] <= loss_history[step] + 1e-4


def test_06_spark_toy_als_fit_and_factor_shapes(spark_session: SparkSession):
    """Verify PySpark ALS fits on toy data and yields correct factor dimensions."""
    df = create_toy_spark_dataframe(spark_session)
    rank = 3
    model = fit_spark_toy_als(df, rank=rank, max_iter=10, reg_param=0.05, seed=42)
    user_factors, item_factors = extract_factors(model)

    # 5 warm users in toy train ratings
    assert len(user_factors) == 5
    for u_id, vec in user_factors.items():
        assert vec.shape == (rank,)
        assert not np.isnan(vec).any()
        assert not np.isinf(vec).any()

    # 6 warm movies in toy train ratings
    assert len(item_factors) == 6
    for m_id, vec in item_factors.items():
        assert vec.shape == (rank,)
        assert not np.isnan(vec).any()
        assert not np.isinf(vec).any()


def test_07_spark_prediction_vs_manual_dot_product(spark_session: SparkSession):
    """Verify manual dot product p_u^T q_i perfectly matches Spark transform within 1e-4."""
    df = create_toy_spark_dataframe(spark_session)
    model = fit_spark_toy_als(df, rank=2, max_iter=15, reg_param=0.05, seed=42)
    audit = verify_spark_vs_manual_dot(model, df, tolerance=1e-4)

    assert audit["num_samples"] == len(TOY_TRAIN_RATINGS)
    assert audit["all_matched"] is True
    assert audit["max_abs_diff"] <= 1e-4


def test_08_missing_ratings_not_treated_as_zero():
    """Verify explicit feedback contract: unrated pairs are NOT counted as zero in loss."""
    ratings_dense = [
        (1, 10, 4.0),
        (1, 20, 0.0),  # explicit zero
    ]
    ratings_sparse = [
        (1, 10, 4.0),
        # (1, 20) is unrated / missing
    ]
    user_factors = {1: np.array([2.0])}
    item_factors = {
        10: np.array([2.0]),  # pred = 4.0, err = 0
        20: np.array([1.0]),  # pred = 2.0
    }
    # With explicit 0: error is (0 - 2)^2 = 4.0
    loss_dense = compute_als_loss(ratings_dense, user_factors, item_factors, reg_param=0.0)
    # With missing pair: pair (1, 20) is omitted from loss
    loss_sparse = compute_als_loss(ratings_sparse, user_factors, item_factors, reg_param=0.0)

    assert math.isclose(loss_sparse, 0.0, abs_tol=1e-6)
    assert math.isclose(loss_dense, 4.0, abs_tol=1e-6)
    assert loss_dense > loss_sparse


def test_09_cold_start_strategy_nan_vs_drop(spark_session: SparkSession):
    """Verify coldStartStrategy='nan' vs 'drop' on unseen user/item."""
    train_df = create_toy_spark_dataframe(spark_session)
    model_nan = fit_spark_toy_als(train_df, cold_start_strategy="nan")
    model_drop = fit_spark_toy_als(train_df, cold_start_strategy="drop")

    # Cold test data: user 999 and movie 999 have never been seen in train
    cold_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", DoubleType(), nullable=False),
    ])
    cold_rows = [
        (1, 101, 2.0),   # warm user, warm movie
        (999, 101, 4.0), # cold user, warm movie
        (1, 999, 3.5),   # warm user, cold movie
        (999, 999, 5.0), # cold user, cold movie
    ]
    cold_df = spark_session.createDataFrame(cold_rows, schema=cold_schema)

    audit = demonstrate_cold_start_difference(model_nan, model_drop, cold_df)
    assert audit["input_row_count"] == 4
    assert audit["nan_strategy_output_count"] == 4
    assert audit["nan_strategy_unscorable_count"] == 3  # 3 rows contain unseen entity
    assert audit["drop_strategy_output_count"] == 1      # Only the warm/warm pair remains
    assert audit["dropped_rows_count"] == 3


def test_10_als_determinism_with_fixed_seed(spark_session: SparkSession):
    """Verify fitting with identical seed produces identical factor matrices."""
    df = create_toy_spark_dataframe(spark_session)
    model_1 = fit_spark_toy_als(df, rank=2, max_iter=10, reg_param=0.05, seed=123)
    model_2 = fit_spark_toy_als(df, rank=2, max_iter=10, reg_param=0.05, seed=123)

    u_fac_1, i_fac_1 = extract_factors(model_1)
    u_fac_2, i_fac_2 = extract_factors(model_2)

    for u_id in u_fac_1:
        np.testing.assert_allclose(u_fac_1[u_id], u_fac_2[u_id], atol=1e-5)
    for m_id in i_fac_1:
        np.testing.assert_allclose(i_fac_1[m_id], i_fac_2[m_id], atol=1e-5)


def test_11_regularization_shrinkage_effect():
    """Verify higher regularization lambda shrinks factor norms toward zero."""
    ratings = TOY_TRAIN_RATINGS
    _, _, _ = run_toy_als_reference(ratings, rank=2, max_iter=15, reg_param=0.001, seed=42)
    u_low, i_low, _ = run_toy_als_reference(ratings, rank=2, max_iter=15, reg_param=0.001, seed=42)
    u_high, i_high, _ = run_toy_als_reference(ratings, rank=2, max_iter=15, reg_param=10.0, seed=42)

    norm_u_low = sum(np.linalg.norm(v) for v in u_low.values())
    norm_u_high = sum(np.linalg.norm(v) for v in u_high.values())

    assert norm_u_high < norm_u_low, "Regularization must shrink factor magnitudes"


def test_12_euclidean_vs_dot_product_counterexample():
    """Verify the geometric proof that Euclidean distance != dot product preference."""
    res = verify_euclidean_vs_dot_product_counterexample()
    assert res["is_counterexample_valid"] is True
    assert res["euclidean_dist_item1"] < res["euclidean_dist_item2"]
    assert res["dot_product_item2"] > res["dot_product_item1"]


def test_13_cold_entities_present_in_toy_catalog():
    """Verify cold user and cold movie exist in metadata with 0 train interactions."""
    assert TOY_USERS[6]["type"] == "cold"
    assert TOY_MOVIES[107]["type"] == "cold"

    train_users = {u for u, _, _ in TOY_TRAIN_RATINGS}
    train_movies = {m for _, m, _ in TOY_TRAIN_RATINGS}

    assert 6 not in train_users
    assert 107 not in train_movies

