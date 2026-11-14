"""
MoodGraph - Task 3A: Spark ALS
Mô-đun: M01 - Bộ nạp và xác thực lược đồ dữ liệu PySpark (Data Loader).

Cung cấp các hàm nạp dữ liệu tái lập, an toàn bộ nhớ và kiểm soát hợp đồng schema
cho tập dữ liệu MovieLens 25M Parquet phục vụ huấn luyện Spark ALS:
- load_train_data: Nạp tập Train (userId, movieId, rating, timestamp).
- load_validation_data: Nạp tập Validation phục vụ tinh chỉnh siêu tham số.
- load_movies_data: Nạp siêu dữ liệu danh mục phim (movieId, title, genres, genre_list).
- load_als_datasets: Tiện ích nạp đồng thời bộ ba dữ liệu Train, Validation, Movies.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Cấu hình môi trường Windows ở mức module trước khi nạp PySpark
if sys.platform.startswith("win"):
    if os.path.exists(r"C:\hadoop"):
        os.environ["HADOOP_HOME"] = r"C:\hadoop"
        os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    ArrayType,
    FloatType,
    DoubleType,
    IntegerType,
    LongType,
    StringType,
)


def get_repo_root() -> Path:
    """Trả về đường dẫn tuyệt đối đến thư mục gốc của repository."""
    return Path(__file__).resolve().parent.parent.parent


def get_spark_session(
    app_name: str = "MoodGraph_ALS_Loader",
    master: str = "local[*]",
    driver_memory: str = "4g",
    shuffle_partitions: int = 16,
) -> SparkSession:
    """Khởi tạo hoặc tái sử dụng SparkSession tối ưu hóa cấu hình thực thi."""
    builder = (
        SparkSession.builder.appName(app_name)
        .master(master)
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", driver_memory)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .config("spark.ui.enabled", "false")
    )
    return builder.getOrCreate()


def _validate_schema(df: DataFrame, dataset_name: str, expected_fields: dict) -> None:
    """
    Xác thực DataFrame chứa đầy đủ các cột bắt buộc với đúng kiểu dữ liệu kỳ vọng.
    Ném ngoại lệ ValueError kèm chẩn đoán chi tiết nếu phát hiện sai lệch.
    """
    actual_fields = {field.name: field.dataType for field in df.schema.fields}

    # Kiểm tra các cột bị thiếu
    missing_cols = [col for col in expected_fields if col not in actual_fields]
    if missing_cols:
        raise ValueError(
            f"Dataset '{dataset_name}' is missing required columns: {missing_cols}. "
            f"Actual columns found: {list(actual_fields.keys())}"
        )

    # Kiểm tra các kiểu dữ liệu không tương thích
    type_mismatches = []
    for col, expected_type in expected_fields.items():
        actual_type = actual_fields[col]
        # Chấp nhận FloatType và DoubleType thay thế cho nhau đối với ratings
        if isinstance(expected_type, (FloatType, DoubleType)) and isinstance(
            actual_type, (FloatType, DoubleType)
        ):
            continue
        # Chấp nhận LongType và IntegerType cho timestamps hoặc IDs nếu tương thích
        if isinstance(expected_type, LongType) and isinstance(actual_type, (LongType, IntegerType)):
            continue
        if actual_type != expected_type:
            type_mismatches.append(
                f"Column '{col}' expected {expected_type}, but got {actual_type}"
            )

    if type_mismatches:
        raise ValueError(
            f"Dataset '{dataset_name}' has schema type mismatches:\n"
            + "\n".join(type_mismatches)
        )


def load_train_data(
    spark: SparkSession,
    base_dir: Optional[Path] = None,
) -> DataFrame:
    """
    Nạp tập dữ liệu huấn luyện Train từ Parquet.
    Hợp đồng schema: userId: int, movieId: int, rating: float, timestamp: long.
    """
    if base_dir is None:
        base_dir = get_repo_root() / "data" / "processed"

    train_path = Path(base_dir) / "splits" / "train"
    if not train_path.exists():
        raise FileNotFoundError(f"Train split directory not found at: {train_path}")

    df = spark.read.parquet(str(train_path))
    expected = {
        "userId": IntegerType(),
        "movieId": IntegerType(),
        "rating": FloatType(),
        "timestamp": LongType(),
    }
    _validate_schema(df, "splits/train", expected)
    return df


def load_validation_data(
    spark: SparkSession,
    base_dir: Optional[Path] = None,
) -> DataFrame:
    """
    Nạp tập dữ liệu kiểm định Validation từ Parquet.
    Hợp đồng schema: userId: int, movieId: int, rating: float, timestamp: long.
    """
    if base_dir is None:
        base_dir = get_repo_root() / "data" / "processed"

    val_path = Path(base_dir) / "splits" / "validation"
    if not val_path.exists():
        raise FileNotFoundError(f"Validation split directory not found at: {val_path}")

    df = spark.read.parquet(str(val_path))
    expected = {
        "userId": IntegerType(),
        "movieId": IntegerType(),
        "rating": FloatType(),
        "timestamp": LongType(),
    }
    _validate_schema(df, "splits/validation", expected)
    return df


def load_movies_data(
    spark: SparkSession,
    base_dir: Optional[Path] = None,
) -> DataFrame:
    """
    Nạp metadata danh mục phim Movie Catalog từ Parquet.
    Hợp đồng schema: movieId: int, title: string, genres: string, genre_list: array<string>.
    """
    if base_dir is None:
        base_dir = get_repo_root() / "data" / "processed"

    movies_path = Path(base_dir) / "core" / "movies"
    if not movies_path.exists():
        raise FileNotFoundError(f"Movie catalog directory not found at: {movies_path}")

    df = spark.read.parquet(str(movies_path))
    expected = {
        "movieId": IntegerType(),
        "title": StringType(),
        "genres": StringType(),
        "genre_list": ArrayType(StringType()),
    }
    _validate_schema(df, "core/movies", expected)
    return df


def load_als_datasets(
    spark: SparkSession,
    base_dir: Optional[Path] = None,
) -> Tuple[DataFrame, DataFrame, DataFrame]:
    """
    Hàm tiện ích nạp đồng thời bộ ba dữ liệu cần thiết cho Task 3A:
    (train_df, val_df, movies_df).
    Tuyệt đối KHÔNG nạp tập Test để bảo vệ tính cô lập thực nghiệm.
    """
    train_df = load_train_data(spark, base_dir)
    val_df = load_validation_data(spark, base_dir)
    movies_df = load_movies_data(spark, base_dir)
    return train_df, val_df, movies_df
