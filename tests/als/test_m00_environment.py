"""
MoodGraph - Task 3A: Spark ALS
Module M00 - Environment, Git Safety & Data Contract Verification
Enhanced Test Suite (Final Review Fixes)
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

# Cấu hình môi trường Windows chuẩn trước khi import pyspark
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    ArrayType,
    FloatType,
    IntegerType,
    LongType,
    StringType,
)


def test_01_git_safety_and_ignore():
    """Kiểm tra quy tắc an toàn Git, .gitignore và đảm bảo không có dữ liệu/model bị tracking."""
    paths_to_check = [
        "data/raw/ml-25m/ratings.csv",
        "data/processed/splits/train/part-00000.parquet",
        "models/als/model_v1",
        "artifacts/als/test_artifact.bin",
    ]
    for rel_path in paths_to_check:
        res = subprocess.run(
            ["git", "check-ignore", rel_path],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0, f"Đường dẫn {rel_path} chưa được bảo vệ bởi .gitignore!"

    # Kiểm tra git ls-files: Không có bất kỳ tệp dữ liệu, parquet, models, artifacts nào bị tracking ngoài ý muốn
    ls_res = subprocess.run(
        ["git", "ls-files", "data/", "models/", "artifacts/"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    tracked_files = [line.strip() for line in ls_res.stdout.splitlines() if line.strip()]
    # Chỉ cho phép duy nhất data/.gitkeep
    for f in tracked_files:
        assert f.endswith(".gitkeep"), f"Phát hiện file bị git theo dõi trái quy định: {f}"


def test_02_manifest_verification():
    """Kiểm tra cấu trúc manifest.json, phân biệt checksum ZIP nguồn vs checksum manifest, và kiểm tra tồn tại 10 datasets."""
    manifest_path = REPO_ROOT / "data" / "processed" / "manifest.json"
    assert manifest_path.exists(), "Không tìm thấy data/processed/manifest.json!"

    # Tính SHA256 của chính file manifest.json
    hasher = hashlib.sha256()
    with open(manifest_path, "rb") as f:
        hasher.update(f.read())
    manifest_sha256 = hasher.hexdigest().lower()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Phân biệt rõ: Checksum ZIP nguồn (GroupLens MD5) vs Checksum manifest
    raw_zip_md5 = manifest.get("source", {}).get("raw_zip_md5", "").lower()
    assert raw_zip_md5 == "6b51fb2759a8657d3bfcbfc42b592ada", "MD5 ZIP nguồn không khớp với GroupLens!"
    assert manifest_sha256 == "a0e5b8b00ec0c5a1164795b8de16822c8d247395955a9cff1e0abb3842e2d1a2", "SHA256 của manifest.json đã bị thay đổi ngoài ý muốn!"

    # 2. Kiểm tra summary counts
    assert manifest.get("version") == "1.0.0"
    summary = manifest.get("summary", {})
    assert summary.get("total_raw_ratings") == 25000095
    assert summary.get("train_ratings") == 24675013
    assert summary.get("val_ratings") == 162541
    assert summary.get("test_ratings") == 162541

    # 3. Kiểm tra sự tồn tại của toàn bộ 10 dataset trên đĩa
    datasets = manifest.get("datasets", {})
    expected_10_datasets = [
        "core_movies",
        "core_links",
        "core_tags",
        "core_genome_tags",
        "core_genome_scores",
        "split_train",
        "split_validation",
        "split_test",
        "feature_movie_genres",
        "feature_tags_train",
    ]
    for key in expected_10_datasets:
        assert key in datasets, f"Thiếu dataset {key} trong manifest.json!"
        rel_path = datasets[key]["relative_path"]
        full_path = REPO_ROOT / "data" / "processed" / rel_path
        assert full_path.exists(), f"Thư mục Parquet {rel_path} không tồn tại trên đĩa!"


def test_03_spark_session_and_schema_contract():
    """Kiểm tra tạo/đóng SparkSession và xác thực schema Parquet của các tập split."""
    spark = (
        SparkSession.builder.appName("MoodGraph-M00-ContractVerification")
        .master("local[2]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

    if True:
        base_dir = REPO_ROOT / "data" / "processed"

        # 1. Kiểm tra split train schema
        train_df = spark.read.parquet(str(base_dir / "splits" / "train"))
        assert train_df.schema["userId"].dataType == IntegerType()
        assert train_df.schema["movieId"].dataType == IntegerType()
        assert train_df.schema["rating"].dataType == FloatType()
        assert train_df.schema["timestamp"].dataType == LongType()

        # 2. Kiểm tra split validation schema
        val_df = spark.read.parquet(str(base_dir / "splits" / "validation"))
        assert val_df.schema["userId"].dataType == IntegerType()
        assert val_df.schema["movieId"].dataType == IntegerType()
        assert val_df.schema["rating"].dataType == FloatType()
        assert val_df.schema["timestamp"].dataType == LongType()

        # 3. Kiểm tra split test schema
        test_df = spark.read.parquet(str(base_dir / "splits" / "test"))
        assert test_df.schema["userId"].dataType == IntegerType()
        assert test_df.schema["movieId"].dataType == IntegerType()
        assert test_df.schema["rating"].dataType == FloatType()
        assert test_df.schema["timestamp"].dataType == LongType()

        # 4. Kiểm tra catalog movies schema
        movies_df = spark.read.parquet(str(base_dir / "core" / "movies"))
        assert movies_df.schema["movieId"].dataType == IntegerType()
        assert movies_df.schema["title"].dataType == StringType()
        assert movies_df.schema["genres"].dataType == StringType()
        assert movies_df.schema["genre_list"].dataType == ArrayType(StringType())

        # 5. Kiểm tra đọc mẫu (non-empty & valid data ranges)
        sample_train = train_df.limit(5).collect()
        assert len(sample_train) == 5
        for row in sample_train:
            assert isinstance(row["userId"], int)
            assert isinstance(row["movieId"], int)
            assert 0.5 <= row["rating"] <= 5.0
            assert row["timestamp"] > 0



def test_04_spark_parquet_row_counts():
    """Đối chiếu row counts thực tế đọc bằng Spark với manifest cho 4 bảng trọng tâm."""
    spark = (
        SparkSession.builder.appName("MoodGraph-M00-RowCountVerification")
        .master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "4g")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )

    if True:
        base_dir = REPO_ROOT / "data" / "processed"

        # Đọc thực tế và đếm dòng bằng Spark
        train_count = spark.read.parquet(str(base_dir / "splits" / "train")).count()
        val_count = spark.read.parquet(str(base_dir / "splits" / "validation")).count()
        test_count = spark.read.parquet(str(base_dir / "splits" / "test")).count()
        movies_count = spark.read.parquet(str(base_dir / "core" / "movies")).count()

        # Đối chiếu chính xác 100% với expected counts
        assert train_count == 24675013, f"Train count {train_count} không khớp 24,675,013!"
        assert val_count == 162541, f"Validation count {val_count} không khớp 162,541!"
        assert test_count == 162541, f"Test count {test_count} không khớp 162,541!"
        assert movies_count == 62423, f"Movies count {movies_count} không khớp 62,423!"



def test_05_roadmap_provenance_and_cleanliness():
    """Kiểm tra nguồn gốc, tính toàn vẹn và sạch sẽ của Master Roadmap TASK_3A_SPARK_ALS_ROADMAP.md."""
    roadmap_path = REPO_ROOT / "docs" / "TASK_3A_SPARK_ALS_ROADMAP.md"
    assert roadmap_path.exists(), "Không tìm thấy docs/TASK_3A_SPARK_ALS_ROADMAP.md!"

    # Kiểm tra hash SHA256 khớp với bản roadmap chính thức đã được soạn thảo
    hasher = hashlib.sha256()
    with open(roadmap_path, "rb") as f:
        hasher.update(f.read())
    file_hash = hasher.hexdigest().lower()
    assert file_hash == "90568faa3571490bb67561b9be34d1d5b882349d40242c146294b93cf122ee25", "Hash của file roadmap không khớp bản gốc!"

    # Kiểm tra nội dung: Đảm bảo không chứa từ khóa của bất kỳ dự án nào khác ngoài MoodGraph
    with open(roadmap_path, "r", encoding="utf-8") as f:
        content = f.read().lower()

    forbidden_keywords = ["vn30", "xno", "phái sinh", "quant_engine", "stock"]
    for kw in forbidden_keywords:
        assert kw not in content, f"Phát hiện từ khóa ngoài dự án ({kw}) trong roadmap!"
