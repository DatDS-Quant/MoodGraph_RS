"""
MoodGraph: Pipeline Tiền Xử Lý Dữ Liệu Lớn Chuẩn Công Nghiệp (Big Data Pipeline)
Bộ dữ liệu: MovieLens 25M (25 triệu lượt đánh giá, 62K phim, 1.1M thẻ nhãn, 15.58M genome scores)
Công nghệ cốt lõi: Apache Spark (PySpark DataFrame API) trên môi trường phân tán.

Quy trình xử lý tuần tự 5 bước:
  Bước 1: Nạp dữ liệu thô với Lược đồ cứng (Strict Schema Ingestion) chống suy diễn sai kiểu.
  Bước 2: Làm sạch, khử trùng lặp và tách đa nhãn thể loại (Genre List Array).
  Bước 3: Phân chia thời gian Leave-1-Last bằng Spark Window Function (Train/Val/Test).
  Bước 4: Trích xuất đặc trưng với cơ chế Anti-Join chống 100% rò rỉ dữ liệu (Zero Data Leakage).
  Bước 5: Đóng gói lưu trữ Parquet dạng cột (Columnar Storage) kèm kiểm định mã băm SHA-256.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path

# Cấu hình môi trường Hadoop và Python cục bộ cho Windows 11
os.environ["HADOOP_HOME"] = r"C:\hadoop"
os.environ["PATH"] = r"C:\hadoop\bin;" + os.environ.get("PATH", "")
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import (
    StructType,
    StructField,
    IntegerType,
    FloatType,
    LongType,
    StringType,
    ArrayType,
)


def get_spark_session(app_name: str = "MoodGraph_Preprocessing") -> SparkSession:
    """
    Khởi tạo và cấu hình SparkSession tối ưu hóa trên máy đơn (Local Cluster):
    - master('local[*]'): Sử dụng toàn bộ số nhân/luồng CPU có sẵn để xử lý song song.
    - driver/executor memory (5g): Cấp phát 5 GB RAM cho Driver và Executor tránh lỗi Out-Of-Memory.
    - shuffle.partitions = 16: Giảm từ 200 mặc định xuống 16 để tránh chia nhỏ file gây nghẽn I/O đĩa.
    - adaptive.enabled = true: Bật Adaptive Query Execution (AQE) tự động tối ưu kế hoạch thực thi khi join.
    - compression.codec = snappy: Thuật toán nén dạng cột của Google, tốc độ giải nén siêu tốc.
    """
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "5g")
        .config("spark.executor.memory", "5g")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.parquet.compression.codec", "snappy")
        .getOrCreate()
    )


def compute_file_sha256(filepath: Path) -> str:
    """Tính toán mã băm mật mã SHA-256 của từng file để bảo đảm tính toàn vẹn dữ liệu (Data Integrity)."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024 * 2), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_dir_sha256_and_size(directory: Path):
    """Tính toán tổng dung lượng và danh sách mã băm SHA-256 mức tệp cho một thư mục tập dữ liệu."""
    total_size = 0
    file_hashes = {}
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            sz = p.stat().st_size
            total_size += sz
            # Tính mã băm cho các tệp không phải .crc và không rỗng
            if not p.name.endswith(".crc") and not p.name.startswith("."):
                file_hashes[p.name] = {
                    "size_bytes": sz,
                    "sha256": compute_file_sha256(p),
                }
    return total_size, file_hashes


def run_pipeline():
    """Thực thi toàn bộ quy trình tiền xử lý dữ liệu MovieLens 25M và phân chia tập dữ liệu chuẩn hóa."""
    start_total_time = time.time()
    base_dir = Path(__file__).resolve().parent.parent
    raw_dir = base_dir / "data" / "raw" / "ml-25m"
    processed_dir = base_dir / "data" / "processed"

    core_dir = processed_dir / "core"
    splits_dir = processed_dir / "splits"
    features_dir = processed_dir / "features"

    for d in [core_dir, splits_dir, features_dir]:
        d.mkdir(parents=True, exist_ok=True)

    spark = get_spark_session()
    print("=" * 80)
    print("STARTING MOODGRAPH PHASE 4: DATA PREPROCESSING PIPELINE")
    print("=" * 80)
    print(f"Source RAW dir:      {raw_dir}")
    print(f"Destination PROCESSED: {processed_dir}\n")

    # -------------------------------------------------------------------------
    # 1. KHAI BÁO SCHEMA CỨNG CHO DỮ LIỆU THÔ (STRICT SCHEMAS)
    # Tuyệt đối không dùng inferSchema=True vì Spark sẽ phải quét 2 lần toàn bộ 25M dòng,
    # làm tăng gấp đôi thời gian I/O và dễ suy diễn sai kiểu dữ liệu.
    # -------------------------------------------------------------------------
    # Schema bảng đánh giá: userId, movieId, rating (0.5 - 5.0), timestamp (giây epoch)
    ratings_raw_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
        StructField("timestamp", LongType(), nullable=False),
    ])

    # Schema bảng danh mục phim: movieId, title (kèm năm phát hành), genres (phân tách bởi '|')
    movies_raw_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("title", StringType(), nullable=False),
        StructField("genres", StringType(), nullable=True),
    ])

    # Schema bảng thẻ người dùng gắn: userId, movieId, tag (từ khóa tự do), timestamp
    tags_raw_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("tag", StringType(), nullable=True),
        StructField("timestamp", LongType(), nullable=False),
    ])

    # Schema bảng điểm số tâm trạng Genome: 15.58M bản ghi ánh xạ mức độ phù hợp (relevance)
    genome_scores_raw_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("tagId", IntegerType(), nullable=False),
        StructField("relevance", FloatType(), nullable=False),
    ])

    # Schema từ điển thẻ tâm trạng Genome: 1,128 tagId mô tả cảm xúc, phong cách điện ảnh
    genome_tags_raw_schema = StructType([
        StructField("tagId", IntegerType(), nullable=False),
        StructField("tag", StringType(), nullable=False),
    ])

    # Schema liên kết mã quốc tế: liên kết mã phim với IMDb ID và TMDb ID
    links_raw_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("imdbId", StringType(), nullable=True),
        StructField("tmdbId", IntegerType(), nullable=True),
    ])

    # -------------------------------------------------------------------------
    # 2. XỬ LÝ VÀ CHUẨN HÓA DỮ LIỆU CỐT LÕI (CORE DATASETS)
    # -------------------------------------------------------------------------
    step_times = {}

    # [2.1] Xử lý Bảng Phim (Movies): Chuẩn hóa chuỗi rỗng thành mảng rỗng, tách '|' thành Array
    t0 = time.time()
    print("[1/5] Processing Movies...")
    movies_df = spark.read.csv(str(raw_dir / "movies.csv"), header=True, schema=movies_raw_schema)
    
    # Chuyển đổi 'Action|Adventure' thành mảng ['Action', 'Adventure'] để nạp vào Đồ thị tri thức
    movies_clean = movies_df.withColumn(
        "genre_list",
        F.when(
            (F.col("genres").isNull()) | (F.col("genres") == "(no genres listed)"),
            F.array().cast(ArrayType(StringType()))
        ).otherwise(F.split(F.col("genres"), "\\|"))
    )
    
    movies_out = core_dir / "movies"
    movies_clean.coalesce(1).write.mode("overwrite").parquet(str(movies_out))
    step_times["core_movies"] = time.time() - t0
    print(f"      -> Movies written to {movies_out} ({step_times['core_movies']:.2f}s)")

    # [2.2] Xử lý Bảng Liên Kết Ngoài (Links: IMDb & TMDb IDs)
    t0 = time.time()
    print("[2/5] Processing Links...")
    links_df = spark.read.csv(str(raw_dir / "links.csv"), header=True, schema=links_raw_schema)
    links_out = core_dir / "links"
    links_df.coalesce(1).write.mode("overwrite").parquet(str(links_out))
    step_times["core_links"] = time.time() - t0
    print(f"      -> Links written to {links_out} ({step_times['core_links']:.2f}s)")

    # [2.3] Xử lý Bảng Danh Mục Thẻ Genome (1,128 Thẻ Tâm Trạng)
    t0 = time.time()
    print("[3/5] Processing Genome Tags...")
    genome_tags_df = spark.read.csv(str(raw_dir / "genome-tags.csv"), header=True, schema=genome_tags_raw_schema)
    gtags_out = core_dir / "genome_tags"
    genome_tags_df.coalesce(1).write.mode("overwrite").parquet(str(gtags_out))
    step_times["core_genome_tags"] = time.time() - t0
    print(f"      -> Genome Tags written to {gtags_out} ({step_times['core_genome_tags']:.2f}s)")

    # [2.4] Xử lý Bảng Điểm Số Genome (15.58 Triệu Bản Ghi Điểm Số Cảm Xúc)
    # coalesce(4): Chia thành 4 file Parquet để đọc ghi song song hiệu năng cao
    t0 = time.time()
    print("[4/5] Processing Genome Scores (15.58M records)...")
    genome_scores_df = spark.read.csv(str(raw_dir / "genome-scores.csv"), header=True, schema=genome_scores_raw_schema)
    gscores_out = core_dir / "genome_scores"
    genome_scores_df.coalesce(4).write.mode("overwrite").parquet(str(gscores_out))
    step_times["core_genome_scores"] = time.time() - t0
    print(f"      -> Genome Scores written to {gscores_out} ({step_times['core_genome_scores']:.2f}s)")

    # [2.5] Xử lý Thẻ Gắn Người Dùng (Tags): Chuẩn hóa chữ thường (lower case) và cắt khoảng trắng thừa
    t0 = time.time()
    print("[5/5] Processing User Tags...")
    tags_df = spark.read.option("quote", "\"").option("escape", "\"").csv(
        str(raw_dir / "tags.csv"), header=True, schema=tags_raw_schema
    )
    tags_clean = tags_df.withColumn(
        "tag_clean",
        F.when(F.col("tag").isNotNull(), F.lower(F.trim(F.col("tag")))).otherwise(F.lit(None))
    )
    tags_out = core_dir / "tags"
    tags_clean.coalesce(2).write.mode("overwrite").parquet(str(tags_out))
    step_times["core_tags"] = time.time() - t0
    print(f"      -> Tags written to {tags_out} ({step_times['core_tags']:.2f}s)")

    # -------------------------------------------------------------------------
    # 3. THUẬT TOÁN PHÂN CHIA THỜI GIAN LEAVE-1-LAST BẰNG SPARK WINDOW FUNCTION
    # Quy tắc phân chia học thuật chuẩn quốc tế:
    # - Tuyệt đối không chia ngẫu nhiên (Random Split) vì sẽ gây rò rỉ dữ liệu tương lai.
    # - Gom nhóm theo từng userId (partitionBy), sắp xếp mốc thời gian giảm dần (timestamp DESC).
    # - Đánh giá cuối cùng của mỗi user (rn_desc == 1) -> Tập TEST (162,541 mẫu).
    # - Đánh giá kế chót của mỗi user (rn_desc == 2) -> Tập VALIDATION (162,541 mẫu).
    # - Toàn bộ các đánh giá trước đó (rn_desc > 2) -> Tập TRAIN (24,675,013 mẫu).
    # -------------------------------------------------------------------------
    t0 = time.time()
    print("\n" + "=" * 60)
    print("EXECUTING LEAVE-1-LAST CHRONOLOGICAL SPLIT ON 25M RATINGS")
    print("=" * 60)
    ratings_df = spark.read.csv(str(raw_dir / "ratings.csv"), header=True, schema=ratings_raw_schema)

    # Cửa sổ phân vùng Spark Window Function
    split_window = Window.partitionBy("userId").orderBy(
        F.col("timestamp").desc(),
        F.col("movieId").desc()  # Khóa phụ đảm bảo tính tất định (Deterministic Tie-Breaker)
    )

    # Đánh số thứ tự nghịch đảo (1 là tương tác mới nhất của user)
    ranked_ratings = ratings_df.withColumn("rn_desc", F.row_number().over(split_window))

    # Tách thành 3 tập dữ liệu hoàn toàn không giao thoa
    test_df = ranked_ratings.filter(F.col("rn_desc") == 1).drop("rn_desc")
    val_df = ranked_ratings.filter(F.col("rn_desc") == 2).drop("rn_desc")
    train_df = ranked_ratings.filter(F.col("rn_desc") > 2).drop("rn_desc")

    # Đưa vào bộ nhớ đệm Cache để tái sử dụng nhanh khi tạo đặc trưng chống rò rỉ
    val_df.cache()
    test_df.cache()

    train_out = splits_dir / "train"
    val_out = splits_dir / "validation"
    test_out = splits_dir / "test"

    print("Writing Test split (1 record per user, 162,541 expected)...")
    test_df.coalesce(1).write.mode("overwrite").parquet(str(test_out))

    print("Writing Validation split (1 record per user, 162,541 expected)...")
    val_df.coalesce(1).write.mode("overwrite").parquet(str(val_out))

    print("Writing Train split (all remaining records, 24,675,013 expected)...")
    train_df.coalesce(8).write.mode("overwrite").parquet(str(train_out))
    step_times["splits"] = time.time() - t0
    print(f"Splits completed in {step_times['splits']:.2f}s.")

    # -------------------------------------------------------------------------
    # 4. TRÍCH XUẤT ĐẶC TRƯNG CHỐNG RÒ RỈ TUYỆT ĐỐI (ZERO LEAKAGE FEATURES)
    # -------------------------------------------------------------------------
    t0 = time.time()
    print("\n" + "=" * 60)
    print("GENERATING DERIVED FEATURES (STRICT LEAKAGE-GUARDED)")
    print("=" * 60)

    # Đặc trưng 1: Bung mảng thể loại (movie_genres) thành từng dòng riêng để nạp quan hệ Đồ thị
    print("Generating movie_genres feature...")
    movie_genres_df = (
        movies_clean.select("movieId", F.explode("genre_list").alias("genre"))
        .filter((F.col("genre") != "") & (F.col("genre").isNotNull()))
    )
    movie_genres_out = features_dir / "movie_genres"
    movie_genres_df.coalesce(1).write.mode("overwrite").parquet(str(movie_genres_out))

    # Đặc trưng 2: tags_train - Thẻ huấn luyện sạch
    # Áp dụng bộ lọc 2 lớp:
    # 1. Thời gian tạo thẻ phải nghiêm ngặt trước mốc thời gian của tập Validation (timestamp < val_cutoff_ts)
    # 2. Phép nối phủ định Spark Left-Anti Join: Loại bỏ 100% các bộ phim xuất hiện trong tập Val và Test
    print("Generating tags_train feature (strictly before validation cutoff AND anti-joined with val/test items)...")
    user_val_cutoffs = val_df.select(
        F.col("userId"),
        F.col("timestamp").alias("val_cutoff_ts")
    )
    val_items = val_df.select("userId", "movieId").distinct()
    test_items = test_df.select("userId", "movieId").distinct()

    tags_train_df = (
        tags_clean.join(user_val_cutoffs, on="userId", how="inner")
        .filter(F.col("timestamp") < F.col("val_cutoff_ts"))
        .drop("val_cutoff_ts")
        .join(val_items, on=["userId", "movieId"], how="left_anti")
        .join(test_items, on=["userId", "movieId"], how="left_anti")
    )
    tags_train_out = features_dir / "tags_train"
    tags_train_df.coalesce(1).write.mode("overwrite").parquet(str(tags_train_out))
    step_times["features"] = time.time() - t0
    print(f"Features completed in {step_times['features']:.2f}s.")

    # -------------------------------------------------------------------------
    # 5. TẠO TẬP TIN MANIFEST VÀ MÃ BĂM TOÀN VẸN DỮ LIỆU SHA-256
    # -------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("COMPUTING MANIFEST & SHA-256 CHECKSUMS")
    print("=" * 60)
    
    manifest_datasets = {}
    dataset_targets = {
        "core_movies": (movies_out, movies_clean),
        "core_links": (links_out, links_df),
        "core_tags": (tags_out, tags_clean),
        "core_genome_tags": (gtags_out, genome_tags_df),
        "core_genome_scores": (gscores_out, genome_scores_df),
        "split_train": (train_out, train_df),
        "split_validation": (val_out, val_df),
        "split_test": (test_out, test_df),
        "feature_movie_genres": (movie_genres_out, movie_genres_df),
        "feature_tags_train": (tags_train_out, tags_train_df),
    }

    total_processed_size = 0
    for key, (path_obj, spark_df) in dataset_targets.items():
        row_count = spark_df.count()
        dir_size, file_hashes = compute_dir_sha256_and_size(path_obj)
        total_processed_size += dir_size
        manifest_datasets[key] = {
            "relative_path": str(path_obj.relative_to(processed_dir)).replace("\\", "/"),
            "row_count": row_count,
            "size_bytes": dir_size,
            "size_mb": round(dir_size / (1024 * 1024), 2),
            "schema": [f"{f.name}: {f.dataType.simpleString()}" for f in spark_df.schema.fields],
            "files": file_hashes,
        }
        print(f"  [{key}] {row_count:,} rows | {dir_size / (1024*1024):.2f} MB")

    total_pipeline_time = time.time() - start_total_time

    manifest_content = {
        "dataset_name": "MovieLens 25M - MoodGraph Processed Package",
        "version": "1.0.0",
        "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "source": {
            "provider": "GroupLens Research (University of Minnesota)",
            "url": "https://grouplens.org/datasets/movielens/25m/",
            "citation": "F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM TiiS 5, 4.",
            "license": "Non-commercial research use only. Redistribution restricted by GroupLens terms.",
            "raw_zip_md5": "6b51fb2759a8657d3bfcbfc42b592ada",
        },
        "environment": {
            "os": sys.platform,
            "python_version": sys.version.split()[0],
            "pyspark_version": spark.version,
            "spark_driver_memory": "5g",
            "spark_shuffle_partitions": 16,
        },
        "splitting_protocol": {
            "strategy": "User-wise Leave-1-Last",
            "sort_keys": ["timestamp ASC", "movieId ASC"],
            "test_definition": "Last interaction (rn_desc == 1) per user",
            "val_definition": "Second-to-last interaction (rn_desc == 2) per user",
            "train_definition": "All prior interactions (rn_desc > 2) per user",
            "tags_train_definition": "tags with timestamp strictly less than user validation timestamp AND left_anti joined with validation and test items on (userId, movieId) to guarantee zero interaction leakage",
        },
        "summary": {
            "total_raw_records": 41803877,
            "total_raw_ratings": 25000095,
            "total_processed_records": sum(d["row_count"] for d in manifest_datasets.values()),
            "train_ratings": manifest_datasets["split_train"]["row_count"],
            "val_ratings": manifest_datasets["split_validation"]["row_count"],
            "test_ratings": manifest_datasets["split_test"]["row_count"],
            "total_processed_size_bytes": total_processed_size,
            "total_processed_size_mb": round(total_processed_size / (1024 * 1024), 2),
            "execution_time_seconds": round(total_pipeline_time, 2),
        },
        "datasets": manifest_datasets,
    }

    manifest_file = processed_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_content, f, indent=2)

    print(f"\nManifest successfully written to {manifest_file}")
    print(f"Total processed data package size: {total_processed_size / (1024*1024):.2f} MB")
    print(f"Pipeline executed in {total_pipeline_time:.2f} seconds.")
    print("=" * 80)

    spark.stop()


if __name__ == "__main__":
    run_pipeline()
