"""
MoodGraph: Production-Grade Data Preprocessing Pipeline (Phase 4)
Dataset: MovieLens 25M
Engine: Apache Spark (PySpark DataFrame API)

This module executes end-to-end data cleansing, schema standardization,
user-wise Leave-1-Last chronological splitting, and Parquet data packaging.
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path

# Configure Hadoop and Python environments for Windows 11
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
    """Initialize an optimized local SparkSession on Windows 11."""
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
    """Compute SHA-256 hash of a file for manifest integrity."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024 * 2), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_dir_sha256_and_size(directory: Path):
    """Compute total size and file-level SHA256 list for a dataset directory."""
    total_size = 0
    file_hashes = {}
    for p in sorted(directory.rglob("*")):
        if p.is_file():
            sz = p.stat().st_size
            total_size += sz
            # Compute hash for non-crc / non-empty files
            if not p.name.endswith(".crc") and not p.name.startswith("."):
                file_hashes[p.name] = {
                    "size_bytes": sz,
                    "sha256": compute_file_sha256(p),
                }
    return total_size, file_hashes


def run_pipeline():
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
    # 1. SCHEMAS FOR RAW INGESTION
    # -------------------------------------------------------------------------
    ratings_raw_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
        StructField("timestamp", LongType(), nullable=False),
    ])

    movies_raw_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("title", StringType(), nullable=False),
        StructField("genres", StringType(), nullable=True),
    ])

    tags_raw_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("tag", StringType(), nullable=True),
        StructField("timestamp", LongType(), nullable=False),
    ])

    genome_scores_raw_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("tagId", IntegerType(), nullable=False),
        StructField("relevance", FloatType(), nullable=False),
    ])

    genome_tags_raw_schema = StructType([
        StructField("tagId", IntegerType(), nullable=False),
        StructField("tag", StringType(), nullable=False),
    ])

    links_raw_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("imdbId", StringType(), nullable=True),
        StructField("tmdbId", IntegerType(), nullable=True),
    ])

    # -------------------------------------------------------------------------
    # 2. PROCESSING CORE DATASETS
    # -------------------------------------------------------------------------
    step_times = {}

    # [2.1] Movies
    t0 = time.time()
    print("[1/5] Processing Movies...")
    movies_df = spark.read.csv(str(raw_dir / "movies.csv"), header=True, schema=movies_raw_schema)
    
    # Transform genre_list: if '(no genres listed)' or null -> empty array, else split by '|'
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

    # [2.2] Links
    t0 = time.time()
    print("[2/5] Processing Links...")
    links_df = spark.read.csv(str(raw_dir / "links.csv"), header=True, schema=links_raw_schema)
    links_out = core_dir / "links"
    links_df.coalesce(1).write.mode("overwrite").parquet(str(links_out))
    step_times["core_links"] = time.time() - t0
    print(f"      -> Links written to {links_out} ({step_times['core_links']:.2f}s)")

    # [2.3] Genome Tags
    t0 = time.time()
    print("[3/5] Processing Genome Tags...")
    genome_tags_df = spark.read.csv(str(raw_dir / "genome-tags.csv"), header=True, schema=genome_tags_raw_schema)
    gtags_out = core_dir / "genome_tags"
    genome_tags_df.coalesce(1).write.mode("overwrite").parquet(str(gtags_out))
    step_times["core_genome_tags"] = time.time() - t0
    print(f"      -> Genome Tags written to {gtags_out} ({step_times['core_genome_tags']:.2f}s)")

    # [2.4] Genome Scores (15.58M rows)
    t0 = time.time()
    print("[4/5] Processing Genome Scores (15.58M records)...")
    genome_scores_df = spark.read.csv(str(raw_dir / "genome-scores.csv"), header=True, schema=genome_scores_raw_schema)
    gscores_out = core_dir / "genome_scores"
    genome_scores_df.coalesce(4).write.mode("overwrite").parquet(str(gscores_out))
    step_times["core_genome_scores"] = time.time() - t0
    print(f"      -> Genome Scores written to {gscores_out} ({step_times['core_genome_scores']:.2f}s)")

    # [2.5] Tags (with tag_clean preserving raw tag)
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
    # 3. LEAVE-1-LAST SPLIT IMPLEMENTATION (Window Partitioning)
    # -------------------------------------------------------------------------
    t0 = time.time()
    print("\n" + "=" * 60)
    print("EXECUTING LEAVE-1-LAST CHRONOLOGICAL SPLIT ON 25M RATINGS")
    print("=" * 60)
    ratings_df = spark.read.csv(str(raw_dir / "ratings.csv"), header=True, schema=ratings_raw_schema)

    # Window partition by user, order by timestamp DESC, movieId DESC (stable tie-breaker)
    split_window = Window.partitionBy("userId").orderBy(
        F.col("timestamp").desc(),
        F.col("movieId").desc()
    )

    ranked_ratings = ratings_df.withColumn("rn_desc", F.row_number().over(split_window))

    # Split into 3 non-overlapping DataFrames
    test_df = ranked_ratings.filter(F.col("rn_desc") == 1).drop("rn_desc")
    val_df = ranked_ratings.filter(F.col("rn_desc") == 2).drop("rn_desc")
    train_df = ranked_ratings.filter(F.col("rn_desc") > 2).drop("rn_desc")

    # Cache validation and test to derive tag cutoffs and item exclusion
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
    # 4. DERIVED FEATURES (movie_genres & tags_train)
    # -------------------------------------------------------------------------
    t0 = time.time()
    print("\n" + "=" * 60)
    print("GENERATING DERIVED FEATURES (STRICT LEAKAGE-GUARDED)")
    print("=" * 60)

    # Feature 1: movie_genres (exploded genres, excluding empty)
    print("Generating movie_genres feature...")
    movie_genres_df = (
        movies_clean.select("movieId", F.explode("genre_list").alias("genre"))
        .filter((F.col("genre") != "") & (F.col("genre").isNotNull()))
    )
    movie_genres_out = features_dir / "movie_genres"
    movie_genres_df.coalesce(1).write.mode("overwrite").parquet(str(movie_genres_out))

    # Feature 2: tags_train (strictly tags prior to validation timestamp AND zero overlap with val/test items)
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
    # 5. GENERATE MANIFEST AND INTEGRITY CHECKSUMS
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
