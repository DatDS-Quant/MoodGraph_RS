"""
MoodGraph: Automated Data Quality & Integrity Test Suite (Phase 4)
Dataset: Processed MovieLens 25M Parquet Package

This module implements the 8 mandatory Automated Data Quality Tests
mandated by the MoodGraph Technical Specification.
"""

import os
import sys
import time
import json
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
    DoubleType,
    LongType,
    StringType,
)


def get_spark_session(app_name: str = "MoodGraph_DataValidation") -> SparkSession:
    """Initialize SparkSession for test execution."""
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "5g")
        .config("spark.executor.memory", "5g")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )


def run_all_tests():
    start_time = time.time()
    base_dir = Path(__file__).resolve().parent.parent
    processed_dir = base_dir / "data" / "processed"
    raw_dir = base_dir / "data" / "raw" / "ml-25m"
    manifest_path = processed_dir / "manifest.json"

    assert manifest_path.exists(), f"Manifest not found at {manifest_path}!"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    spark = get_spark_session()
    print("=" * 80)
    print("STARTING MOODGRAPH AUTOMATED DATA QUALITY TESTS (8 MANDATORY SUITES)")
    print("=" * 80)

    test_results = {}

    # Load datasets from processed Parquet
    print("Loading processed Parquet datasets into Spark DataFrames...")
    movies_df = spark.read.parquet(str(processed_dir / "core" / "movies"))
    links_df = spark.read.parquet(str(processed_dir / "core" / "links"))
    tags_df = spark.read.parquet(str(processed_dir / "core" / "tags"))
    gtags_df = spark.read.parquet(str(processed_dir / "core" / "genome_tags"))
    gscores_df = spark.read.parquet(str(processed_dir / "core" / "genome_scores"))

    train_df = spark.read.parquet(str(processed_dir / "splits" / "train"))
    val_df = spark.read.parquet(str(processed_dir / "splits" / "validation"))
    test_df = spark.read.parquet(str(processed_dir / "splits" / "test"))

    movie_genres_df = spark.read.parquet(str(processed_dir / "features" / "movie_genres"))
    tags_train_df = spark.read.parquet(str(processed_dir / "features" / "tags_train"))

    train_df.cache()
    val_df.cache()
    test_df.cache()
    movies_df.cache()

    # =========================================================================
    # TEST 1: RECORD PRESERVATION
    # =========================================================================
    print("\n[TEST 1] Record Preservation Test...")
    n_train = train_df.count()
    n_val = val_df.count()
    n_test = test_df.count()
    total_split_ratings = n_train + n_val + n_test
    raw_ratings_count = 25000095

    # Scalable two-way set comparison across all 4 attributes (userId, movieId, rating, timestamp)
    raw_ratings_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
        StructField("timestamp", LongType(), nullable=False),
    ])
    raw_ratings_df = spark.read.csv(str(raw_dir / "ratings.csv"), header=True, schema=raw_ratings_schema)
    union_splits = train_df.unionByName(val_df).unionByName(test_df)
    missing_in_splits = raw_ratings_df.join(union_splits, on=["userId", "movieId"], how="left_anti").count()
    extra_in_splits = union_splits.join(raw_ratings_df, on=["userId", "movieId"], how="left_anti").count()
    attr_mismatches = raw_ratings_df.alias("r").join(
        union_splits.alias("s"), on=["userId", "movieId"]
    ).filter(
        (F.col("r.rating") != F.col("s.rating")) | (F.col("r.timestamp") != F.col("s.timestamp"))
    ).count()

    t1_pass = (
        (n_train == 24675013)
        and (n_val == 162541)
        and (n_test == 162541)
        and (total_split_ratings == raw_ratings_count)
        and (missing_in_splits == 0)
        and (extra_in_splits == 0)
        and (attr_mismatches == 0)
    )
    test_results["test_1_record_preservation"] = {
        "status": "PASSED" if t1_pass else "FAILED",
        "train_records": n_train,
        "val_records": n_val,
        "test_records": n_test,
        "total_split_records": total_split_ratings,
        "raw_records": raw_ratings_count,
        "difference": total_split_ratings - raw_ratings_count,
        "missing_in_splits": missing_in_splits,
        "extra_in_splits": extra_in_splits,
        "attribute_mismatches": attr_mismatches,
    }
    print(f"         Status: {test_results['test_1_record_preservation']['status']}")
    print(f"         Train={n_train:,}, Val={n_val:,}, Test={n_test:,} -> Sum={total_split_ratings:,} (Raw={raw_ratings_count:,})")
    print(f"         Two-way Check: Missing={missing_in_splits}, Extra={extra_in_splits}, Attribute Mismatches={attr_mismatches}")
    assert t1_pass, "Test 1 FAILED: Record count or data mismatch!"

    # =========================================================================
    # TEST 2: SPLIT INTEGRITY
    # =========================================================================
    print("\n[TEST 2] Split Integrity Test...")
    # Check no overlap of (userId, movieId)
    train_keys = train_df.select("userId", "movieId")
    val_keys = val_df.select("userId", "movieId")
    test_keys = test_df.select("userId", "movieId")

    overlap_train_val = train_keys.intersect(val_keys).count()
    overlap_train_test = train_keys.intersect(test_keys).count()
    overlap_val_test = val_keys.intersect(test_keys).count()
    total_overlap = overlap_train_val + overlap_train_test + overlap_val_test

    # User count checks
    val_users_count = val_df.select("userId").distinct().count()
    test_users_count = test_df.select("userId").distinct().count()
    train_users_count = train_df.select("userId").distinct().count()

    # Minimum ratings in train per user
    min_train_per_user = train_df.groupBy("userId").count().select(F.min("count")).first()[0]

    # Full boundary ordering check across all 25M rows:
    # 1. val vs test: val must precede test: (val.ts < test.ts) OR (val.ts == test.ts AND val.movieId < test.movieId)
    val_test_viol = val_df.alias("v").join(test_df.alias("t"), on="userId").filter(
        (F.col("v.timestamp") > F.col("t.timestamp")) |
        ((F.col("v.timestamp") == F.col("t.timestamp")) & (F.col("v.movieId") >= F.col("t.movieId")))
    ).count()

    # 2. train vs val: all train records must precede val:
    # (train.ts < val.ts) OR (train.ts == val.ts AND train.movieId < val.movieId)
    train_val_viol = train_df.alias("tr").join(val_df.alias("v"), on="userId").filter(
        (F.col("tr.timestamp") > F.col("v.timestamp")) |
        ((F.col("tr.timestamp") == F.col("v.timestamp")) & (F.col("tr.movieId") >= F.col("v.movieId")))
    ).count()
    chrono_violations = val_test_viol + train_val_viol

    t2_pass = (
        (total_overlap == 0)
        and (val_users_count == 162541)
        and (test_users_count == 162541)
        and (train_users_count == 162541)
        and (min_train_per_user >= 18)
        and (chrono_violations == 0)
    )

    test_results["test_2_split_integrity"] = {
        "status": "PASSED" if t2_pass else "FAILED",
        "overlap_train_val": overlap_train_val,
        "overlap_train_test": overlap_train_test,
        "overlap_val_test": overlap_val_test,
        "val_distinct_users": val_users_count,
        "test_distinct_users": test_users_count,
        "train_distinct_users": train_users_count,
        "min_train_ratings_per_user": min_train_per_user,
        "chronological_violations": chrono_violations,
        "val_test_violations": val_test_viol,
        "train_val_violations": train_val_viol,
    }
    print(f"         Status: {test_results['test_2_split_integrity']['status']}")
    print(f"         Overlap={total_overlap}, Distinct Users Val/Test/Train={val_users_count}/{test_users_count}/{train_users_count}, Min Train/User={min_train_per_user}, Chrono Violations={chrono_violations} (Train-Val={train_val_viol}, Val-Test={val_test_viol})")
    assert t2_pass, "Test 2 FAILED: Split integrity violated!"

    # =========================================================================
    # TEST 3: REFERENTIAL INTEGRITY
    # =========================================================================
    print("\n[TEST 3] Referential Integrity Test...")
    # Check all movieIds in ratings, tags, links, genome_scores exist in movies
    all_ratings_movies = train_df.select("movieId").union(val_df.select("movieId")).union(test_df.select("movieId")).distinct()
    dangling_ratings_mids = all_ratings_movies.join(movies_df, on="movieId", how="left_anti").count()
    dangling_tags_mids = tags_df.select("movieId").distinct().join(movies_df, on="movieId", how="left_anti").count()
    dangling_links_mids = links_df.select("movieId").distinct().join(movies_df, on="movieId", how="left_anti").count()
    dangling_gscores_mids = gscores_df.select("movieId").distinct().join(movies_df, on="movieId", how="left_anti").count()
    dangling_gscores_tags = gscores_df.select("tagId").distinct().join(gtags_df, on="tagId", how="left_anti").count()

    total_dangling = (
        dangling_ratings_mids
        + dangling_tags_mids
        + dangling_links_mids
        + dangling_gscores_mids
        + dangling_gscores_tags
    )
    t3_pass = (total_dangling == 0)
    test_results["test_3_referential_integrity"] = {
        "status": "PASSED" if t3_pass else "FAILED",
        "dangling_ratings_movieId": dangling_ratings_mids,
        "dangling_tags_movieId": dangling_tags_mids,
        "dangling_links_movieId": dangling_links_mids,
        "dangling_genome_scores_movieId": dangling_gscores_mids,
        "dangling_genome_scores_tagId": dangling_gscores_tags,
    }
    print(f"         Status: {test_results['test_3_referential_integrity']['status']}")
    print(f"         Total dangling foreign keys = {total_dangling}")
    assert t3_pass, "Test 3 FAILED: Dangling foreign keys detected!"

    # =========================================================================
    # TEST 4: SCHEMA VALIDATION
    # =========================================================================
    print("\n[TEST 4] Schema Validation Test...")
    expected_schemas = {
        "train": {"userId": "int", "movieId": "int", "rating": "float", "timestamp": "bigint"},
        "validation": {"userId": "int", "movieId": "int", "rating": "float", "timestamp": "bigint"},
        "test": {"userId": "int", "movieId": "int", "rating": "float", "timestamp": "bigint"},
        "movies": {"movieId": "int", "title": "string", "genres": "string", "genre_list": "array<string>"},
        "links": {"movieId": "int", "imdbId": "string", "tmdbId": "int"},
        "genome_scores": {"movieId": "int", "tagId": "int", "relevance": "float"},
        "genome_tags": {"tagId": "int", "tag": "string"},
        "tags": {"userId": "int", "movieId": "int", "tag": "string", "tag_clean": "string", "timestamp": "bigint"},
    }

    schema_mismatches = []
    datasets_to_check = {
        "train": train_df,
        "validation": val_df,
        "test": test_df,
        "movies": movies_df,
        "links": links_df,
        "genome_scores": gscores_df,
        "genome_tags": gtags_df,
        "tags": tags_df,
    }

    for dname, df in datasets_to_check.items():
        actual_types = {f.name: f.dataType.simpleString() for f in df.schema.fields}
        exp_types = expected_schemas[dname]
        for col_name, exp_type in exp_types.items():
            act_type = actual_types.get(col_name)
            if act_type != exp_type:
                schema_mismatches.append(f"{dname}.{col_name}: expected {exp_type}, got {act_type}")

    t4_pass = (len(schema_mismatches) == 0)
    test_results["test_4_schema_validation"] = {
        "status": "PASSED" if t4_pass else "FAILED",
        "mismatches": schema_mismatches,
    }
    print(f"         Status: {test_results['test_4_schema_validation']['status']}")
    if schema_mismatches:
        print(f"         Mismatches: {schema_mismatches}")
    assert t4_pass, f"Test 4 FAILED: Schema mismatches: {schema_mismatches}"

    # =========================================================================
    # TEST 5: INFORMATION PRESERVATION & METADATA INTEGRITY
    # =========================================================================
    print("\n[TEST 5] Information Preservation & Metadata Integrity Test...")
    # Check no movies deleted
    total_movies = movies_df.count()
    no_genre_movies = movies_df.filter(F.size("genre_list") == 0).count()
    
    # Check movies without genome
    movies_with_genome = gscores_df.select("movieId").distinct().count()
    movies_without_genome = total_movies - movies_with_genome

    # Check rating range
    min_rating = train_df.select(F.min("rating")).first()[0]
    max_rating = train_df.select(F.max("rating")).first()[0]

    # Check "NA" string preserved in tags
    na_tags_count = tags_df.filter(F.col("tag") == "NA").count()
    null_tag_ts = tags_df.filter(F.col("timestamp").isNull()).count()

    # Check IMDb leading zeros preserved
    sample_imdb = links_df.filter(F.col("movieId") == 1).select("imdbId").first()[0]
    has_leading_zeros = sample_imdb.startswith("0") and len(sample_imdb) == 7

    # Check Float32 precision drift on genome_scores
    raw_gscores_schema = StructType([
        StructField("movieId", IntegerType()),
        StructField("tagId", IntegerType()),
        StructField("raw_relevance_double", DoubleType()),
    ])
    raw_gscores_df = spark.read.csv(str(raw_dir / "genome-scores.csv"), header=True, schema=raw_gscores_schema)
    max_drift = float(raw_gscores_df.alias("r").join(gscores_df.alias("p"), on=["movieId", "tagId"]).select(
        F.max(F.abs(F.col("r.raw_relevance_double") - F.col("p.relevance"))).alias("max_drift")
    ).first()["max_drift"])

    # Check derived feature movie_genres matches movies
    derived_mgenres_count = movie_genres_df.count()

    t5_pass = (
        (total_movies == 62423)
        and (no_genre_movies == 5062)
        and (movies_without_genome == 48607)
        and (min_rating == 0.5)
        and (max_rating == 5.0)
        and (na_tags_count == 16)
        and (null_tag_ts == 0)
        and (max_drift < 1e-7)
        and (derived_mgenres_count == 107245)
        and has_leading_zeros
    )
    test_results["test_5_information_preservation"] = {
        "status": "PASSED" if t5_pass else "FAILED",
        "total_movies": total_movies,
        "empty_genre_movies": no_genre_movies,
        "movies_without_genome": movies_without_genome,
        "min_rating": min_rating,
        "max_rating": max_rating,
        "na_string_tags_count": na_tags_count,
        "null_tag_timestamps": null_tag_ts,
        "imdb_sample_leading_zeros": sample_imdb,
        "genome_scores_max_float32_drift": max_drift,
        "derived_movie_genres_count": derived_mgenres_count,
    }
    print(f"         Status: {test_results['test_5_information_preservation']['status']}")
    print(f"         Total Movies={total_movies}, No Genre={no_genre_movies}, No Genome={movies_without_genome}, 'NA' tags={na_tags_count}, Null Tag TS={null_tag_ts}, Float32 Drift={max_drift:.3e}, imdbId='{sample_imdb}', movie_genres={derived_mgenres_count}")
    assert t5_pass, "Test 5 FAILED: Information preservation or metadata fidelity violated!"

    # =========================================================================
    # TEST 6: LEAKAGE GUARD
    # =========================================================================
    print("\n[TEST 6] Leakage Guard Test...")
    # Verify no test ratings exist in train
    leak_test_in_train = test_df.join(train_df, on=["userId", "movieId"], how="inner").count()
    leak_val_in_train = val_df.join(train_df, on=["userId", "movieId"], how="inner").count()

    # Verify tags_train has zero tags occurring at or after user validation timestamp
    u_val_ts_only = val_df.select("userId", F.col("timestamp").alias("val_ts"))
    tags_leak_check = (
        tags_train_df.join(u_val_ts_only, on="userId", how="inner")
        .filter(F.col("timestamp") >= F.col("val_ts"))
        .count()
    )

    # Verify tags_train has ZERO overlap on (userId, movieId) with validation and test ratings
    val_items = val_df.select("userId", "movieId")
    test_items = test_df.select("userId", "movieId")
    overlap_tags_val = tags_train_df.join(val_items, on=["userId", "movieId"], how="inner").count()
    overlap_tags_test = tags_train_df.join(test_items, on=["userId", "movieId"], how="inner").count()

    t6_pass = (
        leak_test_in_train == 0
        and leak_val_in_train == 0
        and tags_leak_check == 0
        and overlap_tags_val == 0
        and overlap_tags_test == 0
    )
    test_results["test_6_leakage_guard"] = {
        "status": "PASSED" if t6_pass else "FAILED",
        "test_in_train_count": leak_test_in_train,
        "val_in_train_count": leak_val_in_train,
        "future_tags_in_train_count": tags_leak_check,
        "tags_train_overlap_validation_items": overlap_tags_val,
        "tags_train_overlap_test_items": overlap_tags_test,
    }
    print(f"         Status: {test_results['test_6_leakage_guard']['status']}")
    print(f"         Test in Train={leak_test_in_train}, Val in Train={leak_val_in_train}, Future Tags in tags_train={tags_leak_check}, Tags-Val Overlap={overlap_tags_val}, Tags-Test Overlap={overlap_tags_test}")
    assert t6_pass, "Test 6 FAILED: Data leakage detected!"

    # =========================================================================
    # TEST 7: REPRODUCIBILITY (DETERMINISTIC SPLIT CHECK)
    # =========================================================================
    print("\n[TEST 7] Reproducibility Test...")
    # Re-run split on a cohort of 500 users from raw CSV and verify exact row-level equality
    raw_ratings_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
        StructField("timestamp", LongType(), nullable=False),
    ])
    raw_ratings_sub = spark.read.csv(str(raw_dir / "ratings.csv"), header=True, schema=raw_ratings_schema).filter(F.col("userId") <= 500)
    
    test_win = Window.partitionBy("userId").orderBy(F.col("timestamp").desc(), F.col("movieId").desc())
    re_ranked = raw_ratings_sub.withColumn("rn_desc", F.row_number().over(test_win))
    re_test = re_ranked.filter(F.col("rn_desc") == 1).select("userId", "movieId", "rating", "timestamp")
    
    # Compare with test_df on the same cohort
    actual_test_sub = test_df.filter(F.col("userId") <= 500).select("userId", "movieId", "rating", "timestamp")
    diff_count = re_test.exceptAll(actual_test_sub).count() + actual_test_sub.exceptAll(re_test).count()

    t7_pass = (diff_count == 0)
    test_results["test_7_reproducibility"] = {
        "status": "PASSED" if t7_pass else "FAILED",
        "sample_cohort_size": 500,
        "differences_detected": diff_count,
    }
    print(f"         Status: {test_results['test_7_reproducibility']['status']}")
    print(f"         Re-computed split comparison on 500-user cohort: differences={diff_count}")
    assert t7_pass, "Test 7 FAILED: Split is non-deterministic!"

    # =========================================================================
    # TEST 8: OUTPUT READABILITY & MANIFEST PARITY
    # =========================================================================
    print("\n[TEST 8] Output Readability & Manifest Parity Test...")
    manifest_datasets = manifest["datasets"]
    parity_errors = []

    for dkey, dinfo in manifest_datasets.items():
        rel_path = dinfo["relative_path"]
        exp_count = dinfo["row_count"]
        target_path = processed_dir / rel_path
        
        # Read back via Spark
        try:
            read_df = spark.read.parquet(str(target_path))
            act_count = read_df.count()
            if act_count != exp_count:
                parity_errors.append(f"{dkey}: read count {act_count} != manifest count {exp_count}")
        except Exception as e:
            parity_errors.append(f"{dkey} read failed: {str(e)}")

    t8_pass = (len(parity_errors) == 0)
    test_results["test_8_output_readability"] = {
        "status": "PASSED" if t8_pass else "FAILED",
        "parity_errors": parity_errors,
        "datasets_verified": len(manifest_datasets),
    }
    print(f"         Status: {test_results['test_8_output_readability']['status']}")
    print(f"         Verified {len(manifest_datasets)} Parquet datasets. Parity errors={len(parity_errors)}")
    assert t8_pass, f"Test 8 FAILED: Parity errors: {parity_errors}"

    total_test_time = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"ALL 8 MANDATORY DATA QUALITY TESTS PASSED IN {total_test_time:.2f}s!")
    print("=" * 80)

    # Save test results report
    test_summary_file = processed_dir / "test_results.json"
    with open(test_summary_file, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2)
    print(f"Test summary saved to {test_summary_file}")

    spark.stop()
    return test_results


if __name__ == "__main__":
    run_all_tests()
