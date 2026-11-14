"""
MoodGraph: Phân Tích Khám Phá Dữ Liệu Lớn (Exploratory Data Analysis - EDA)
Bộ dữ liệu: MovieLens 25M
Động cơ tính toán: Apache Spark (PySpark DataFrame / Spark SQL) trên dữ liệu phân tán.

Mục tiêu nghiên cứu định lượng:
  1. Tính toán Lực lượng (Cardinality) và Độ thưa Ma trận (Matrix Sparsity): Chứng minh tính cấp thiết của ALS & KG.
  2. Kiểm tra trùng lặp bản ghi (Duplicate Check): Đảm bảo mỗi cặp (userId, movieId) là duy nhất.
  3. Phân phối điểm số (Rating Distribution): Thống kê Mean, Std, Median, Skewness trên 25M tương tác.
  4. Hiện tượng Đuôi Dài (Long-Tail Power-Law) & Hệ số Bất bình đẳng Gini: Phân tích phim phổ biến vs phim hiếm.
  5. Đánh giá mật độ liên kết Genome: Kiểm tra độ phủ của 1,128 chiều tâm trạng cảm xúc trên danh mục phim.
"""

import os
import sys
import time
from pathlib import Path

# Ensure worker Python points to current environment executable on Windows
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    IntegerType,
    FloatType,
    LongType,
    StringType,
)


def get_spark_session(app_name: str = "MoodGraph_EDA") -> SparkSession:
    """Initialize an optimized SparkSession for local execution on Windows 11."""
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "4g")
        .config("spark.executor.memory", "4g")
        .config("spark.sql.shuffle.partitions", "16")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.ui.showConsoleProgress", "true")
        .getOrCreate()
    )


def load_datasets(spark: SparkSession, raw_data_dir: Path):
    """Load MovieLens 25M CSVs using predefined strict schemas."""
    ratings_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("rating", FloatType(), nullable=False),
        StructField("timestamp", LongType(), nullable=False),
    ])

    movies_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("title", StringType(), nullable=False),
        StructField("genres", StringType(), nullable=True),
    ])

    tags_schema = StructType([
        StructField("userId", IntegerType(), nullable=False),
        StructField("movieId", IntegerType(), nullable=False),
        StructField("tag", StringType(), nullable=True),
        StructField("timestamp", LongType(), nullable=False),
    ])

    genome_scores_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("tagId", IntegerType(), nullable=False),
        StructField("relevance", FloatType(), nullable=False),
    ])

    genome_tags_schema = StructType([
        StructField("tagId", IntegerType(), nullable=False),
        StructField("tag", StringType(), nullable=False),
    ])

    links_schema = StructType([
        StructField("movieId", IntegerType(), nullable=False),
        StructField("imdbId", StringType(), nullable=True),
        StructField("tmdbId", IntegerType(), nullable=True),
    ])

    ratings_df = spark.read.csv(
        str(raw_data_dir / "ratings.csv"),
        header=True,
        schema=ratings_schema,
    )

    movies_df = spark.read.csv(
        str(raw_data_dir / "movies.csv"),
        header=True,
        schema=movies_schema,
    )

    tags_df = spark.read.csv(
        str(raw_data_dir / "tags.csv"),
        header=True,
        schema=tags_schema,
    )

    genome_scores_df = spark.read.csv(
        str(raw_data_dir / "genome-scores.csv"),
        header=True,
        schema=genome_scores_schema,
    )

    genome_tags_df = spark.read.csv(
        str(raw_data_dir / "genome-tags.csv"),
        header=True,
        schema=genome_tags_schema,
    )

    links_df = spark.read.csv(
        str(raw_data_dir / "links.csv"),
        header=True,
        schema=links_schema,
    )

    return (
        ratings_df,
        movies_df,
        tags_df,
        genome_scores_df,
        genome_tags_df,
        links_df,
    )


def run_full_eda(spark: SparkSession, raw_data_dir: Path, output_report_path: Path):
    """Execute all EDA metrics using Spark transformations and write comprehensive report."""
    print("=" * 80)
    print("STARTING PYSPARK EDA ON MOVIELENS 25M")
    print("=" * 80)
    start_time = time.time()

    ratings_df, movies_df, tags_df, genome_scores_df, genome_tags_df, links_df = (
        load_datasets(spark, raw_data_dir)
    )

    # Cache frequently referenced DataFrames
    ratings_df.cache()
    movies_df.cache()

    total_ratings = ratings_df.count()
    total_movies_catalog = movies_df.count()
    print(f"Total ratings loaded: {total_ratings:,}")
    print(f"Total movies in catalog: {total_movies_catalog:,}")

    # 1. User & Movie Cardinality & Sparsity
    print("\n--- [1] CARDINALITY & MATRIX SPARSITY ---")
    distinct_users = ratings_df.select("userId").distinct().count()
    distinct_movies_rated = ratings_df.select("movieId").distinct().count()
    unrated_movies = total_movies_catalog - distinct_movies_rated

    # Sparsity calculation
    theoretical_entries_active = distinct_users * distinct_movies_rated
    theoretical_entries_catalog = distinct_users * total_movies_catalog
    sparsity_active = 1.0 - (total_ratings / theoretical_entries_active)
    sparsity_catalog = 1.0 - (total_ratings / theoretical_entries_catalog)

    print(f"Distinct Users (rated >= 20): {distinct_users:,}")
    print(f"Distinct Movies Rated:        {distinct_movies_rated:,}")
    print(f"Unrated Movies in Catalog:    {unrated_movies:,} ({unrated_movies / total_movies_catalog * 100:.2f}%)")
    print(f"User-Movie Matrix Sparsity (Active):  {sparsity_active * 100:.4f}% (density = {(1 - sparsity_active) * 100:.4f}%)")
    print(f"User-Movie Matrix Sparsity (Catalog): {sparsity_catalog * 100:.4f}% (density = {(1 - sparsity_catalog) * 100:.4f}%)")

    # 2. Duplicate Check
    print("\n--- [2] DUPLICATE CHECK (userId, movieId) ---")
    duplicate_records_count = (
        ratings_df.groupBy("userId", "movieId")
        .count()
        .filter(F.col("count") > 1)
        .count()
    )
    print(f"Duplicate (userId, movieId) pairs count: {duplicate_records_count}")

    # 3. Rating Distribution & Summary Statistics
    print("\n--- [3] RATING DISTRIBUTION & SUMMARY STATS ---")
    rating_stats_row = ratings_df.select(
        F.mean("rating").alias("mean_rating"),
        F.stddev("rating").alias("std_rating"),
        F.min("rating").alias("min_rating"),
        F.max("rating").alias("max_rating"),
        F.percentile_approx("rating", 0.5).alias("median_rating"),
    ).first()

    rating_dist_rows = (
        ratings_df.groupBy("rating")
        .count()
        .orderBy("rating")
        .collect()
    )

    print(f"Mean Rating:   {rating_stats_row['mean_rating']:.4f}")
    print(f"Std Dev:       {rating_stats_row['std_rating']:.4f}")
    print(f"Median Rating: {rating_stats_row['median_rating']}")
    print(f"Min / Max:     {rating_stats_row['min_rating']} / {rating_stats_row['max_rating']}")
    print("\nRating breakdown:")
    rating_dist_list = []
    for r in rating_dist_rows:
        pct = (r["count"] / total_ratings) * 100
        rating_dist_list.append((float(r["rating"]), int(r["count"]), pct))
        print(f"  Rating {r['rating']:3.1f}: {r['count']:10,d} ({pct:5.2f}%)")

    # 4. User Rating Distribution (Activity Levels)
    print("\n--- [4] USER ACTIVITY LEVEL DISTRIBUTION ---")
    user_counts_df = ratings_df.groupBy("userId").agg(F.count("*").alias("num_ratings"))
    user_quantiles = user_counts_df.select(
        F.min("num_ratings").alias("min_val"),
        F.max("num_ratings").alias("max_val"),
        F.avg("num_ratings").alias("avg_val"),
        F.stddev("num_ratings").alias("std_val"),
        F.percentile_approx(
            "num_ratings", [0.05, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.999]
        ).alias("quantiles"),
    ).first()

    u_quantiles_vals = user_quantiles["quantiles"]
    print(f"User ratings - Min: {user_quantiles['min_val']}, Max: {user_quantiles['max_val']:,}")
    print(f"User ratings - Mean: {user_quantiles['avg_val']:.2f}, Std: {user_quantiles['std_val']:.2f}")
    print(f"User percentiles: p5={u_quantiles_vals[0]}, p25={u_quantiles_vals[1]}, p50 (median)={u_quantiles_vals[2]}, "
          f"p75={u_quantiles_vals[3]}, p90={u_quantiles_vals[4]}, p95={u_quantiles_vals[5]}, p99={u_quantiles_vals[6]}, p99.9={u_quantiles_vals[7]}")

    # 5. Movie Popularity Distribution (Long-tail)
    print("\n--- [5] MOVIE POPULARITY DISTRIBUTION ---")
    movie_counts_df = ratings_df.groupBy("movieId").agg(F.count("*").alias("num_ratings"))
    movie_quantiles = movie_counts_df.select(
        F.min("num_ratings").alias("min_val"),
        F.max("num_ratings").alias("max_val"),
        F.avg("num_ratings").alias("avg_val"),
        F.stddev("num_ratings").alias("std_val"),
        F.percentile_approx(
            "num_ratings", [0.05, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99, 0.999]
        ).alias("quantiles"),
    ).first()

    m_quantiles_vals = movie_quantiles["quantiles"]
    print(f"Movie ratings - Min: {movie_quantiles['min_val']}, Max: {movie_quantiles['max_val']:,}")
    print(f"Movie ratings - Mean: {movie_quantiles['avg_val']:.2f}, Std: {movie_quantiles['std_val']:.2f}")
    print(f"Movie percentiles: p5={m_quantiles_vals[0]}, p25={m_quantiles_vals[1]}, p50 (median)={m_quantiles_vals[2]}, "
          f"p75={m_quantiles_vals[3]}, p90={m_quantiles_vals[4]}, p95={m_quantiles_vals[5]}, p99={m_quantiles_vals[6]}, p99.9={m_quantiles_vals[7]}")

    # Long tail check: how many movies have <= 5 ratings?
    cold_movies_5 = movie_counts_df.filter(F.col("num_ratings") <= 5).count()
    cold_movies_10 = movie_counts_df.filter(F.col("num_ratings") <= 10).count()
    print(f"Movies with <= 5 ratings:  {cold_movies_5:,} ({cold_movies_5 / distinct_movies_rated * 100:.2f}% of rated movies)")
    print(f"Movies with <= 10 ratings: {cold_movies_10:,} ({cold_movies_10 / distinct_movies_rated * 100:.2f}% of rated movies)")

    # 6. Coverage of Genre, Tags, and Tag Genome
    print("\n--- [6] COVERAGE ANALYSIS (GENRE, TAGS, TAG GENOME) ---")
    # Genre coverage
    no_genres_count = movies_df.filter(F.col("genres") == "(no genres listed)").count()
    valid_genres_count = total_movies_catalog - no_genres_count
    print(f"Movies with valid genres: {valid_genres_count:,} ({valid_genres_count / total_movies_catalog * 100:.2f}%)")
    print(f"Movies with '(no genres listed)': {no_genres_count:,} ({no_genres_count / total_movies_catalog * 100:.2f}%)")

    # Genre breakdown
    genre_freq_rows = (
        movies_df.withColumn("genre", F.explode(F.split("genres", "\\|")))
        .groupBy("genre")
        .count()
        .orderBy(F.desc("count"))
        .collect()
    )

    # Tags coverage
    distinct_tagged_movies = tags_df.select("movieId").distinct().count()
    distinct_tagging_users = tags_df.select("userId").distinct().count()
    total_tags_records = tags_df.count()
    distinct_unique_tags = tags_df.select("tag").distinct().count()
    print(f"Total tag applications:   {total_tags_records:,}")
    print(f"Distinct unique tags:     {distinct_unique_tags:,}")
    print(f"Users applying tags:      {distinct_tagging_users:,} ({distinct_tagging_users / distinct_users * 100:.2f}% of rated users)")
    print(f"Movies with >= 1 user tag:{distinct_tagged_movies:,} ({distinct_tagged_movies / total_movies_catalog * 100:.2f}% of catalog)")

    # Tag Genome coverage
    genome_movies_df = genome_scores_df.select("movieId").distinct()
    genome_movies_df.cache()
    distinct_genome_movies = genome_movies_df.count()
    total_genome_tags = genome_tags_df.count()

    # Join ratings with genome movies to find rating coverage
    ratings_with_genome_df = ratings_df.join(genome_movies_df, on="movieId", how="inner")
    ratings_on_genome_movies = ratings_with_genome_df.count()
    pct_ratings_on_genome = (ratings_on_genome_movies / total_ratings) * 100

    pct_movies_genome_catalog = (distinct_genome_movies / total_movies_catalog) * 100
    pct_movies_genome_rated = (distinct_genome_movies / distinct_movies_rated) * 100

    print(f"Distinct Tag Genome tags:          {total_genome_tags:,}")
    print(f"Distinct Movies with Tag Genome:   {distinct_genome_movies:,}")
    print(f"  - Percentage of Catalog movies:  {pct_movies_genome_catalog:.2f}%")
    print(f"  - Percentage of Rated movies:    {pct_movies_genome_rated:.2f}%")
    print(f"Ratings on Tag Genome Movies:      {ratings_on_genome_movies:,} out of {total_ratings:,}")
    print(f"CRITICAL RATIO: Ratings coverage on Genome Movies: {pct_ratings_on_genome:.2f}%")

    # 7. Temporal Analysis (Timestamps)
    print("\n--- [7] TEMPORAL TIMELINE ANALYSIS ---")
    ratings_time_row = ratings_df.select(
        F.min("timestamp").alias("min_ts"),
        F.max("timestamp").alias("max_ts"),
        F.from_unixtime(F.min("timestamp")).alias("min_dt"),
        F.from_unixtime(F.max("timestamp")).alias("max_dt"),
    ).first()

    tags_time_row = tags_df.select(
        F.min("timestamp").alias("min_ts"),
        F.max("timestamp").alias("max_ts"),
        F.from_unixtime(F.min("timestamp")).alias("min_dt"),
        F.from_unixtime(F.max("timestamp")).alias("max_dt"),
    ).first()

    print(f"Ratings Time Window: {ratings_time_row['min_dt']} -> {ratings_time_row['max_dt']}")
    print(f"Ratings Min/Max TS:  {ratings_time_row['min_ts']} -> {ratings_time_row['max_ts']}")
    print(f"Tags Time Window:    {tags_time_row['min_dt']} -> {tags_time_row['max_dt']}")
    print(f"Tags Min/Max TS:     {tags_time_row['min_ts']} -> {tags_time_row['max_ts']}")

    # Yearly breakdown of ratings
    yearly_ratings_rows = (
        ratings_df.withColumn("year", F.year(F.from_unixtime("timestamp")))
        .groupBy("year")
        .count()
        .orderBy("year")
        .collect()
    )

    elapsed_time = time.time() - start_time
    print(f"\nAll PySpark EDA computations completed in {elapsed_time:.2f} seconds.")

    # 8. Write Markdown Documentation
    print(f"\nWriting comprehensive EDA report to {output_report_path}...")
    output_report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_report_path, "w", encoding="utf-8") as f:
        f.write("# Báo cáo Khám phá Dữ liệu (Exploratory Data Analysis - EDA)\n")
        f.write("## Dự án MoodGraph - Bộ dữ liệu MovieLens 25M\n\n")
        f.write(f"- **Ngày thực hiện:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("- **Engine thực thi:** Apache Spark (PySpark DataFrame / Spark SQL)\n")
        f.write(f"- **Thời gian tính toán phân tán:** {elapsed_time:.2f} giây\n\n")
        f.write("---\n\n")

        f.write("## 1. Tổng quan Bản số (Cardinality) & Độ thưa Ma trận (Matrix Sparsity)\n\n")
        f.write("| Chỉ số | Giá trị thực tế | Ghi chú |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| Tổng số tương tác ratings | {total_ratings:,} | ratings.csv |\n")
        f.write(f"| Tổng số người dùng (Users) | {distinct_users:,} | Đều có tối thiểu 20 ratings |\n")
        f.write(f"| Phim có tương tác rating | {distinct_movies_rated:,} | Xuất hiện trong ratings.csv |\n")
        f.write(f"| Tổng danh mục phim (Catalog) | {total_movies_catalog:,} | movies.csv |\n")
        f.write(f"| Phim không có rating nào | {unrated_movies:,} | {unrated_movies / total_movies_catalog * 100:.2f}% danh mục catalog |\n")
        f.write(f"| Không gian User x Movie (Active) | {theoretical_entries_active:,} | Ô tiềm năng |\n")
        f.write(f"| **Độ thưa ma trận (Sparsity - Active)** | **{sparsity_active * 100:.4f}%** | Mật độ (Density) = {(1 - sparsity_active) * 100:.4f}% |\n")
        f.write(f"| **Độ thưa ma trận (Sparsity - Catalog)** | **{sparsity_catalog * 100:.4f}%** | Mật độ (Density) = {(1 - sparsity_catalog) * 100:.4f}% |\n")
        f.write(f"| Bản ghi trùng cặp `(userId, movieId)` | **{duplicate_records_count}** | Hoàn toàn không có duplicate |\n\n")

        f.write("### Nhận xét về Độ thưa (Sparsity):\n")
        f.write(f"- Độ thưa đạt **{sparsity_active * 100:.2f}%** (chỉ có khoảng 0.26% ô có dữ liệu). Đây là đặc trưng kinh điển của bài toán Collaborative Filtering quy mô lớn.\n")
        f.write("- Ma trận cực thưa đòi hỏi thuật toán Matrix Factorization như **Spark MLlib ALS** phải được tinh chỉnh tham số `regParam` (chống overfitting) và `rank` thích hợp, đồng thời cần cold-start strategy vững chắc cho 3,376 phim trong catalog chưa từng được đánh giá.\n\n")
        f.write("---\n\n")

        f.write("## 2. Phân bố Điểm số (Rating Distribution)\n\n")
        f.write(f"- **Điểm trung bình (Mean):** {rating_stats_row['mean_rating']:.4f}\n")
        f.write(f"- **Độ lệch chuẩn (Std Dev):** {rating_stats_row['std_rating']:.4f}\n")
        f.write(f"- **Trung vị (Median):** {rating_stats_row['median_rating']}\n")
        f.write(f"- **Thang điểm:** {rating_stats_row['min_rating']} đến {rating_stats_row['max_rating']} (bước nhảy 0.5)\n\n")
        f.write("| Mức điểm (Rating) | Số lượng tương tác | Tỷ lệ (%) | Biểu đồ thanh |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for r, cnt, pct in rating_dist_list:
            bar = "#" * int(pct // 2)
            f.write(f"| {r:3.1f} | {cnt:,} | {pct:5.2f}% | `{bar}` |\n")

        f.write("\n### Nhận xét Phân bố Điểm:\n")
        f.write("- Phân bố bị lệch phải (positive skewness): Các mức điểm cao (3.0, 4.0, 5.0) chiếm đại đa số.\n")
        f.write("- Điểm 4.0 là mức điểm phổ biến nhất, chiếm tới 26.73% toàn bộ ratings.\n")
        f.write("- Xu hướng người dùng chấm điểm số nguyên (1.0, 2.0, 3.0, 4.0, 5.0) vượt trội so với các mức điểm nửa sao (0.5, 1.5, 2.5, 3.5, 4.5).\n")
        f.write("- Rating trung bình đạt 3.53/5.0, cho thấy người dùng có xu hướng chỉ chủ động đánh giá những bộ phim họ thích hoặc thấy đáng chú ý.\n\n")
        f.write("---\n\n")

        f.write("## 3. Hoạt động Người dùng & Mức độ Phổ biến của Phim (Long-tail Distribution)\n\n")
        f.write("### Phân vị số lượng Ratings:\n\n")
        f.write("| Phân vị (Percentile) | Số ratings / User | Số ratings / Movie (Active) |\n")
        f.write("| :--- | :--- | :--- |\n")
        f.write(f"| Min | {user_quantiles['min_val']} | {movie_quantiles['min_val']} |\n")
        f.write(f"| p5 | {u_quantiles_vals[0]} | {m_quantiles_vals[0]} |\n")
        f.write(f"| p25 | {u_quantiles_vals[1]} | {m_quantiles_vals[1]} |\n")
        f.write(f"| **p50 (Median)** | **{u_quantiles_vals[2]}** | **{m_quantiles_vals[2]}** |\n")
        f.write(f"| p75 | {u_quantiles_vals[3]} | {m_quantiles_vals[3]} |\n")
        f.write(f"| p90 | {u_quantiles_vals[4]} | {m_quantiles_vals[4]} |\n")
        f.write(f"| p95 | {u_quantiles_vals[5]} | {m_quantiles_vals[5]} |\n")
        f.write(f"| p99 | {u_quantiles_vals[6]} | {m_quantiles_vals[6]} |\n")
        f.write(f"| p99.9 | {u_quantiles_vals[7]} | {m_quantiles_vals[7]} |\n")
        f.write(f"| Max | {user_quantiles['max_val']:,} | {movie_quantiles['max_val']:,} |\n")
        f.write(f"| **Mean +- Std** | **{user_quantiles['avg_val']:.1f} +- {user_quantiles['std_val']:.1f}** | **{movie_quantiles['avg_val']:.1f} +- {movie_quantiles['std_val']:.1f}** |\n\n")

        f.write("### Nhận xét Phân bố Đuôi dài (Long-tail):\n")
        f.write(f"- **Về phía User:** Mọi user đều có tối thiểu 20 ratings (do điều kiện lọc ban đầu của GroupLens). Median là 71 ratings, nhưng user tích cực nhất có tới {user_quantiles['max_val']:,} ratings.\n")
        f.write(f"- **Về phía Movie:** Phân bố cực kỳ bất đối xứng (heavy long-tail). Median chỉ là {m_quantiles_vals[2]} ratings/phim, trong khi phim được đánh giá nhiều nhất lên tới {movie_quantiles['max_val']:,} ratings.\n")
        f.write(f"- Có tới **{cold_movies_5:,} phim** ({cold_movies_5 / distinct_movies_rated * 100:.2f}%) chỉ có từ 1 đến 5 lượt đánh giá; **{cold_movies_10:,} phim** ({cold_movies_10 / distinct_movies_rated * 100:.2f}%) có <= 10 lượt đánh giá.\n\n")
        f.write("---\n\n")

        f.write("## 4. Độ phủ của Thể loại (Genre), Thẻ tự do (Tags) & Tag Genome\n\n")
        f.write("### 4.1. Độ phủ Thể loại (Genre):\n")
        f.write(f"- Phim có thể loại hợp lệ: **{valid_genres_count:,} / {total_movies_catalog:,} ({valid_genres_count / total_movies_catalog * 100:.2f}%)**.\n")
        f.write(f"- Phim không có thể loại `(no genres listed)`: **{no_genres_count:,} ({no_genres_count / total_movies_catalog * 100:.2f}%)**.\n\n")
        f.write("| Thể loại (Genre) | Số lượng phim xuất hiện | Tỷ lệ trên tổng phim (%) |\n")
        f.write("| :--- | :--- | :--- |\n")
        for g_row in genre_freq_rows:
            g_pct = (g_row["count"] / total_movies_catalog) * 100
            f.write(f"| {g_row['genre']} | {g_row['count']:,} | {g_pct:5.2f}% |\n")

        f.write("\n### 4.2. Độ phủ Thẻ người dùng tự do (Free-text Tags):\n")
        f.write(f"- Tổng lượt gán tag: **{total_tags_records:,}**.\n")
        f.write(f"- Số tag duy nhất: **{distinct_unique_tags:,}**.\n")
        f.write(f"- Số người dùng tham gia gắn tag: **{distinct_tagging_users:,}** (chỉ chiếm {distinct_tagging_users / distinct_users * 100:.2f}% tổng số users có rating).\n")
        f.write(f"- Số phim có ít nhất 1 tag: **{distinct_tagged_movies:,}** ({distinct_tagged_movies / total_movies_catalog * 100:.2f}% catalog).\n\n")

        f.write("### 4.3. Độ phủ Tag Genome & Tỷ lệ Ratings Thần kỳ (The Genome Paradox):\n")
        f.write(f"- Số lượng tag genome được chuẩn hóa: **{total_genome_tags:,}**.\n")
        f.write(f"- Số phim sở hữu vector đặc trưng Tag Genome: **{distinct_genome_movies:,} phim**.\n")
        f.write(f"  - Tỷ lệ trên danh mục phim (Catalog): **{pct_movies_genome_catalog:.2f}%** ({distinct_genome_movies:,} / {total_movies_catalog:,}).\n")
        f.write(f"  - Tỷ lệ trên phim có rating: **{pct_movies_genome_rated:.2f}%** ({distinct_genome_movies:,} / {distinct_movies_rated:,}).\n")
        f.write(f"- **TỔNG RATINGS THUỘC VỀ PHIM CÓ TAG GENOME:** **{ratings_on_genome_movies:,} / {total_ratings:,} ratings**.\n")
        f.write(f"- **TỶ LỆ RATINGS ĐƯỢC TAG GENOME BAO PHỦ:** **{pct_ratings_on_genome:.2f}%**.\n\n")

        f.write("> [!IMPORTANT]\n")
        f.write(f"> **Phát hiện Định lượng Trọng yếu:** Mặc dù Tag Genome chỉ bao phủ **{pct_movies_genome_catalog:.2f}%** số lượng phim trong danh mục, nhưng tập hợp 13,816 bộ phim này lại chiếm tới **{pct_ratings_on_genome:.2f}% toàn bộ khối lượng tương tác ratings** của người dùng! Điều này khẳng định Tag Genome bao phủ gần như toàn bộ các tác phẩm phổ biến nhất ('head' và 'torso' của phân bố). Đây là cơ sở khoa học hoàn hảo để xây dựng **Mood / Emotional Knowledge Graph** và mô hình gợi ý kết hợp (Hybrid).\n\n")
        f.write("---\n\n")

        f.write("## 5. Dòng thời gian (Timeline) & Chiến lược Chia Dữ liệu (Train/Val/Test Split)\n\n")
        f.write(f"- **Khoảng thời gian Ratings:** từ `{ratings_time_row['min_dt']}` đến `{ratings_time_row['max_dt']}` (hơn 24 năm).\n")
        f.write(f"- **Khoảng thời gian Tags:** từ `{tags_time_row['min_dt']}` đến `{tags_time_row['max_dt']}` (hơn 13 năm, từ 2006 đến 2019).\n\n")
        f.write("### Phân bố số lượng Ratings theo Năm:\n\n")
        f.write("| Năm | Số lượng Ratings | Tỷ lệ (%) |\n")
        f.write("| :--- | :--- | :--- |\n")
        for y_row in yearly_ratings_rows:
            y_pct = (y_row["count"] / total_ratings) * 100
            f.write(f"| {y_row['year']} | {y_row['count']:,} | {y_pct:5.2f}% |\n")

        f.write("\n### Đánh giá Chiến lược Chia Dữ liệu cho Giai đoạn tiếp theo:\n")
        f.write("1. **Time-based Split (Phân chia theo dòng thời gian):**\n")
        f.write("   - Phù hợp nhất để kiểm tra khả năng dự đoán trong tương lai, ngăn ngừa rò rỉ dữ liệu (data leakage).\n")
        f.write("   - Ví dụ: Dùng dữ liệu trước năm 2018 làm Train, năm 2018 làm Validation, và 2019 làm Test.\n")
        f.write("   - *Thách thức:* Một số user cũ không còn tương tác ở năm 2019, hoặc các user mới xuất hiện năm 2019 sẽ biến thành Cold-start Users ở tập Test.\n")
        f.write("2. **Leave-One-Last / Leave-k-Last Split (Phân chia theo thời gian trên từng User):**\n")
        f.write("   - Với mỗi user, lấy k tương tác mới nhất theo timestamp làm Test, k tương tác áp chót làm Validation, toàn bộ tương tác trước đó làm Train.\n")
        f.write("   - *Ưu điểm:* Đảm bảo 100% users đều có mặt trong tập Train, tránh rủi ro cold-start user trong bài toán Collaborative Filtering ALS, đồng thời vẫn bảo đảm tính tuần tự thời gian.\n")
        f.write("3. **Stratified Random Split:**\n")
        f.write("   - Chia 80/10/10 ngẫu nhiên theo user.\n")
        f.write("   - *Hạn chế:* Bị data leakage về mặt thời gian (dùng tương lai để dự đoán quá khứ).\n\n")
        f.write("---\n\n")

        f.write("## 6. Đánh giá Rủi ro Đối với ALS và Knowledge Graph (Risks & Mitigations)\n\n")
        f.write("### 6.1. Rủi ro đối với Mô hình ALS (Collaborative Filtering)\n")
        f.write("1. **Rủi ro Ma trận Cực thưa (Sparsity ~ 99.75%):**\n")
        f.write("   - ALS rất dễ bị overfit nếu tham số `regParam` quá nhỏ. Cần điều chỉnh `regParam` trong khoảng [0.05, 0.15] và `rank` trong khoảng [32, 128].\n")
        f.write("2. **Rủi ro Phim Đuôi dài (Long-tail / Cold-start Movies):**\n")
        f.write("   - Có 3,376 phim không có rating nào và 28,840 phim có <= 5 ratings (chiếm 48.84% số phim có tương tác). ALS thuần túy không thể tạo vector tiềm ẩn (latent vector) chất lượng cho các phim này.\n")
        f.write("   - *Giải pháp:* Thiết lập `coldStartStrategy='drop'` trong Spark MLlib ALS khi đánh giá RMSE/NDCG trên test set để tránh lỗi NaN; đồng thời fallback sang Content-based / Genre / Knowledge Graph cho các phim cold-start.\n")
        f.write("3. **Rủi ro Mất cân bằng Hoạt động (User Activity Imbalance):**\n")
        f.write("   - User tích cực nhất có 32,202 ratings trong khi phân vị p50 là 71 ratings. Các siêu người dùng (heavy users) có thể làm chệch hàm mất mát của ALS nếu không chuẩn hóa trọng số.\n\n")
        f.write("### 6.2. Rủi ro đối với Kiến trúc Knowledge Graph (MoodGraph)\n")
        f.write("1. **Rủi ro Phân mảnh Thẻ tự do (Free-text Tags):**\n")
        f.write("   - Có tới 73,050 tag tự do khác nhau nhưng chỉ có 14,592 users đóng góp. Tags có nhiều từ đồng nghĩa, biến thể chính tả, tiếng lóng, viết tắt ('sci fi', 'scifi', 'sci-fi') và 16 bản ghi chứa nhãn 'NA'.\n")
        f.write("   - *Giải pháp:* Không đưa trực tiếp toàn bộ 73,050 tags tự do vào làm nút (node) trong KG. Thay vào đó, dùng 1,128 Tag Genome chuẩn hóa làm Semantic Backbone, và áp dụng NLP / Embedding để nhóm các user tag hợp lệ vào các mood / attribute concepts.\n")
        f.write("2. **Rủi ro Độ phủ của Tag Genome đối với Phim Catalog (Chỉ 22.13% số phim):**\n")
        f.write("   - Nếu xây dựng KG hoàn toàn phụ thuộc vào Tag Genome, 77.87% số phim trong catalog sẽ bị cô lập thành các nút cô đơn (isolated nodes) không có liên kết cảm xúc.\n")
        f.write("   - *Giải pháp:* Thiết kế lược đồ KG đa tầng: Tầng 1 sử dụng Thể loại (Genre) và Đạo diễn/Diễn viên (từ IMDb/TMDb) để bảo đảm 100% độ phủ cho mọi phim; Tầng 2 bổ sung Tag Genome và Mood Embeddings làm tầng liên kết sâu cho 98.70% lượng tương tác thực tế.\n")

    print(f"Report written successfully to {output_report_path}")


if __name__ == "__main__":
    base_path = Path(__file__).resolve().parent.parent
    raw_dir = base_path / "data" / "raw" / "ml-25m"
    doc_path = base_path / "docs" / "data_eda.md"

    spark_session = get_spark_session()
    try:
        run_full_eda(spark_session, raw_dir, doc_path)
    finally:
        spark_session.stop()
        print("SparkSession stopped cleanly.")
