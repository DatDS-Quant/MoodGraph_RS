"""
MoodGraph - Task 3A: Spark ALS
Module M01: Unit Tests for Data Loader & Input Audit Engine
Using synthetic Parquet fixtures generated via PyArrow.
"""

import os
import sys
from pathlib import Path

# Cấu hình môi trường Windows chuẩn trước khi import pyspark
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if sys.platform.startswith("win"):
    os.environ["HADOOP_HOME"] = r"C:\hadoop"
    os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    ArrayType,
    FloatType,
    IntegerType,
    LongType,
    StringType,
    StructField,
    StructType,
)

from recommender.als.data_loader import (
    _validate_schema,
    load_train_data,
    load_validation_data,
    load_movies_data,
    load_als_datasets,
)
from recommender.als.data_audit import (
    validate_train_input_constraints,
    audit_als_input_distribution,
    audit_movie_cold_start,
)


@pytest.fixture(scope="session")
def spark():
    """Session-scoped Spark fixture."""
    session = (
        SparkSession.builder.appName("MoodGraph_M01_UnitTests")
        .master("local[2]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "2")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture(scope="session")
def synthetic_data_dir(tmp_path_factory):
    """
    Generate synthetic Parquet package in temporary directory:
    - 4 users (1, 2, 3, 4)
    - 6 catalog movies (10, 20, 30, 40, 50, 60)
    - Train: 8 ratings
        User 1: (10, 4.0), (20, 3.5), (30, 5.0) -> 3 ratings
        User 2: (10, 2.5), (20, 4.5)             -> 2 ratings
        User 3: (10, 5.0), (40, 1.0)             -> 2 ratings
        User 4: (10, 3.0)                        -> 1 rating
      Train-known movies: {10, 20, 30, 40} -> 4 movies
      Train-unseen movies: {50, 60}        -> 2 movies
    - Validation: 4 ratings
        User 1: (50, 4.0) [unseen in train, positive >= 3.5]
        User 2: (10, 3.5) [known in train, positive >= 3.5]
        User 3: (20, 2.0) [known in train, non-positive < 3.5]
        User 4: (60, 1.5) [unseen in train, non-positive < 3.5]
    """
    base = tmp_path_factory.mktemp("als_synthetic_data")
    train_dir = base / "splits" / "train"
    val_dir = base / "splits" / "validation"
    movies_dir = base / "core" / "movies"

    train_dir.mkdir(parents=True)
    val_dir.mkdir(parents=True)
    movies_dir.mkdir(parents=True)

    # 1. Train Table
    train_table = pa.table({
        "userId": pa.array([1, 1, 1, 2, 2, 3, 3, 4], type=pa.int32()),
        "movieId": pa.array([10, 20, 30, 10, 20, 10, 40, 10], type=pa.int32()),
        "rating": pa.array([4.0, 3.5, 5.0, 2.5, 4.5, 5.0, 1.0, 3.0], type=pa.float32()),
        "timestamp": pa.array([1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008], type=pa.int64()),
    })
    pq.write_table(train_table, train_dir / "part-0.parquet")

    # 2. Validation Table
    val_table = pa.table({
        "userId": pa.array([1, 2, 3, 4], type=pa.int32()),
        "movieId": pa.array([50, 10, 20, 60], type=pa.int32()),
        "rating": pa.array([4.0, 3.5, 2.0, 1.5], type=pa.float32()),
        "timestamp": pa.array([2001, 2002, 2003, 2004], type=pa.int64()),
    })
    pq.write_table(val_table, val_dir / "part-0.parquet")

    # 3. Movies Catalog Table
    movies_table = pa.table({
        "movieId": pa.array([10, 20, 30, 40, 50, 60], type=pa.int32()),
        "title": pa.array(["M10", "M20", "M30", "M40", "M50", "M60"], type=pa.string()),
        "genres": pa.array(["Action", "Comedy", "Drama", "Horror", "Sci-Fi", "Romance"], type=pa.string()),
        "genre_list": pa.array([["Action"], ["Comedy"], ["Drama"], ["Horror"], ["Sci-Fi"], ["Romance"]], type=pa.list_(pa.string())),
    })
    pq.write_table(movies_table, movies_dir / "part-0.parquet")

    return base


def test_01_loader_reads_valid_schema(spark, synthetic_data_dir):
    """Test 1: Loader successfully loads datasets with expected schema."""
    train_df, val_df, movies_df = load_als_datasets(spark, synthetic_data_dir)
    assert train_df.count() == 8
    assert val_df.count() == 4
    assert movies_df.count() == 6

    # Verify column data types
    assert isinstance(train_df.schema["userId"].dataType, IntegerType)
    assert isinstance(train_df.schema["movieId"].dataType, IntegerType)
    assert isinstance(train_df.schema["rating"].dataType, FloatType)
    assert isinstance(train_df.schema["timestamp"].dataType, LongType)


def test_02_loader_fails_on_corrupt_schema(spark, tmp_path):
    """Test 2: Schema validator raises ValueError on missing columns or wrong types."""
    corrupt_dir = tmp_path / "corrupt"
    corrupt_train = corrupt_dir / "splits" / "train"
    corrupt_train.mkdir(parents=True)

    corrupt_table = pa.table({
        "userId": pa.array([1], type=pa.int32()),
        "movieId": pa.array([10], type=pa.int32()),
        "rating": pa.array(["bad_rating_str"], type=pa.string()),
    })
    pq.write_table(corrupt_table, corrupt_train / "part-0.parquet")

    with pytest.raises(ValueError) as excinfo:
        load_train_data(spark, corrupt_dir)
    assert "missing required columns" in str(excinfo.value) or "type mismatches" in str(excinfo.value)


def test_03_missing_input_path(spark, tmp_path):
    """Test 3: Loader raises FileNotFoundError on missing path."""
    non_existent_dir = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        load_train_data(spark, base_dir=non_existent_dir)


def test_04_detect_nulls_in_required_columns(spark, tmp_path, synthetic_data_dir):
    """Test 4: Input validation detects null in required columns."""
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)

    dirty_path = tmp_path / "dirty_null.parquet"
    dirty_table = pa.table({
        "userId": pa.array([None], type=pa.int32()),
        "movieId": pa.array([10], type=pa.int32()),
        "rating": pa.array([4.0], type=pa.float32()),
        "timestamp": pa.array([1000], type=pa.int64()),
    })
    pq.write_table(dirty_table, dirty_path)
    dirty_df = train_df.union(spark.read.parquet(str(dirty_path)))

    res = validate_train_input_constraints(dirty_df, movies_df)
    assert res["passed"] is False
    assert res["null_userId_count"] == 1


def test_05_detect_rating_out_of_bounds(spark, tmp_path, synthetic_data_dir):
    """Test 5: Detects rating < 0.5 or > 5.0."""
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)

    dirty_path = tmp_path / "dirty_bounds.parquet"
    dirty_table = pa.table({
        "userId": pa.array([1, 2], type=pa.int32()),
        "movieId": pa.array([10, 20], type=pa.int32()),
        "rating": pa.array([0.2, 5.5], type=pa.float32()),
        "timestamp": pa.array([1000, 1001], type=pa.int64()),
    })
    pq.write_table(dirty_table, dirty_path)
    dirty_df = train_df.union(spark.read.parquet(str(dirty_path)))

    res = validate_train_input_constraints(dirty_df, movies_df)
    assert res["passed"] is False
    assert res["range_violation_count"] == 2


def test_06_detect_rating_step_violation(spark, tmp_path, synthetic_data_dir):
    """Test 6: Detects rating not on 0.5 step (e.g. 3.7)."""
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)

    dirty_path = tmp_path / "dirty_step.parquet"
    dirty_table = pa.table({
        "userId": pa.array([1], type=pa.int32()),
        "movieId": pa.array([10], type=pa.int32()),
        "rating": pa.array([3.7], type=pa.float32()),
        "timestamp": pa.array([1000], type=pa.int64()),
    })
    pq.write_table(dirty_table, dirty_path)
    dirty_df = train_df.union(spark.read.parquet(str(dirty_path)))

    res = validate_train_input_constraints(dirty_df, movies_df)
    assert res["passed"] is False
    assert res["step_violation_count"] == 1


def test_07_detect_duplicate_user_movie_pairs(spark, tmp_path, synthetic_data_dir):
    """Test 7: Detects duplicate (userId, movieId) pair."""
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)

    dirty_path = tmp_path / "dirty_dup.parquet"
    dirty_table = pa.table({
        "userId": pa.array([1], type=pa.int32()),
        "movieId": pa.array([10], type=pa.int32()),
        "rating": pa.array([4.5], type=pa.float32()),
        "timestamp": pa.array([1000], type=pa.int64()),
    })
    pq.write_table(dirty_table, dirty_path)
    dirty_df = train_df.union(spark.read.parquet(str(dirty_path)))

    res = validate_train_input_constraints(dirty_df, movies_df)
    assert res["passed"] is False
    assert res["duplicate_pair_count"] == 1


def test_08_detect_unreferenced_movies(spark, tmp_path, synthetic_data_dir):
    """Test 8: Detects movieId in Train that does not exist in catalog."""
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)

    dirty_path = tmp_path / "dirty_dangling.parquet"
    dirty_table = pa.table({
        "userId": pa.array([1], type=pa.int32()),
        "movieId": pa.array([999], type=pa.int32()),
        "rating": pa.array([4.0], type=pa.float32()),
        "timestamp": pa.array([1000], type=pa.int64()),
    })
    pq.write_table(dirty_table, dirty_path)
    dirty_df = train_df.union(spark.read.parquet(str(dirty_path)))

    res = validate_train_input_constraints(dirty_df, movies_df)
    assert res["passed"] is False
    assert res["dangling_movies_count"] == 1


def test_09_distinguish_missing_vs_zero_rating(spark, tmp_path, synthetic_data_dir):
    """Test 9: Distinguishes missing rating from explicit zero rating."""
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)

    dirty_path = tmp_path / "dirty_zero.parquet"
    dirty_table = pa.table({
        "userId": pa.array([1], type=pa.int32()),
        "movieId": pa.array([20], type=pa.int32()),
        "rating": pa.array([0.0], type=pa.float32()),
        "timestamp": pa.array([1000], type=pa.int64()),
    })
    pq.write_table(dirty_table, dirty_path)
    dirty_df = train_df.union(spark.read.parquet(str(dirty_path)))

    res = validate_train_input_constraints(dirty_df, movies_df)
    assert res["passed"] is False
    assert res["zero_rating_count"] == 1


def test_10_count_train_known_and_unseen_movies(spark, synthetic_data_dir):
    """Test 10 & 11: Correctly counts train-known and train-unseen movies."""
    train_df, val_df, movies_df = load_als_datasets(spark, synthetic_data_dir)
    cold_res = audit_movie_cold_start(train_df, val_df, movies_df)

    assert cold_res["catalog_movie_count"] == 6
    assert cold_res["train_known_movie_count"] == 4
    assert cold_res["train_unseen_movie_count"] == 2
    assert cold_res["train_unseen_percentage"] == pytest.approx(33.333, rel=1e-2)


def test_11_movie_popularity_binning(spark, synthetic_data_dir):
    """Test 12: Correctly bins movie popularity: 1-5, 6-10, >10."""
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)
    dist_res = audit_als_input_distribution(train_df, movies_df)

    buckets = dist_res["movie_popularity_buckets"]
    assert buckets["ratings_1_to_5"] == 4
    assert buckets["ratings_6_to_10"] == 0
    assert buckets["ratings_gt_10"] == 0
    assert buckets["zero_train_ratings"] == 2


def test_12_density_and_sparsity_hand_calculation(spark, synthetic_data_dir):
    """
    Test 13: Verify density and sparsity matches exact hand calculations:
    - 4 users, 4 train-known movies -> cells = 16. Ratings = 8.
      density_known = 8 / 16 = 0.5 (50%), sparsity_known = 0.5 (50%)
    - 4 users, 6 catalog movies -> cells = 24. Ratings = 8.
      density_catalog = 8 / 24 = 1/3 ≈ 0.3333 (33.33%), sparsity_catalog = 2/3 ≈ 0.6667 (66.67%)
    """
    train_df, _, movies_df = load_als_datasets(spark, synthetic_data_dir)
    dist_res = audit_als_input_distribution(train_df, movies_df)

    known_u = dist_res["train_known_universe"]
    assert known_u["density"] == pytest.approx(0.5, rel=1e-5)
    assert known_u["sparsity"] == pytest.approx(0.5, rel=1e-5)

    cat_u = dist_res["full_catalog_universe"]
    assert cat_u["density"] == pytest.approx(1.0 / 3.0, rel=1e-5)
    assert cat_u["sparsity"] == pytest.approx(2.0 / 3.0, rel=1e-5)


def test_13_validation_item_coverage_hand_calculation(spark, synthetic_data_dir):
    """
    Test 14: Verify validation item coverage matches exact hand calculations:
    - Total val = 4 (users 1, 2, 3, 4)
    - Movies: 50 (unseen), 10 (known), 20 (known), 60 (unseen)
    - All-target coverage: 2 / 4 = 50.0%
    - Positive-target cohort (rating >= 3.5):
        User 1: (50, 4.0) -> positive, unscorable
        User 2: (10, 3.5) -> positive, scoreable
      Total positive = 2, scoreable = 1 -> coverage = 50.0%
    """
    train_df, val_df, movies_df = load_als_datasets(spark, synthetic_data_dir)
    cold_res = audit_movie_cold_start(train_df, val_df, movies_df)

    all_targets = cold_res["validation_all_targets"]
    assert all_targets["total"] == 4
    assert all_targets["scoreable_by_als"] == 2
    assert all_targets["unscorable_by_als"] == 2
    assert all_targets["coverage_percentage"] == 50.0

    pos_targets = cold_res["validation_positive_targets"]
    assert pos_targets["total"] == 2
    assert pos_targets["scoreable_by_als"] == 1
    assert pos_targets["unscorable_by_als"] == 1
    assert pos_targets["coverage_percentage"] == 50.0


def test_14_empty_dataframe_handling(spark, tmp_path):
    """Test 15: Empty DataFrame handling returns zero counts without crashing."""
    empty_train_path = tmp_path / "empty_train.parquet"
    empty_movies_path = tmp_path / "empty_movies.parquet"

    empty_train_table = pa.table({
        "userId": pa.array([], type=pa.int32()),
        "movieId": pa.array([], type=pa.int32()),
        "rating": pa.array([], type=pa.float32()),
        "timestamp": pa.array([], type=pa.int64()),
    })
    pq.write_table(empty_train_table, empty_train_path)

    empty_movies_table = pa.table({
        "movieId": pa.array([], type=pa.int32()),
        "title": pa.array([], type=pa.string()),
        "genres": pa.array([], type=pa.string()),
        "genre_list": pa.array([], type=pa.list_(pa.string())),
    })
    pq.write_table(empty_movies_table, empty_movies_path)

    empty_df = spark.read.parquet(str(empty_train_path))
    empty_movies_df = spark.read.parquet(str(empty_movies_path))

    constraints = validate_train_input_constraints(empty_df, empty_movies_df)
    assert constraints["passed"] is True
    assert constraints["total_train_rows"] == 0
