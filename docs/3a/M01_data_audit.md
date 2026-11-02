# MoodGraph Task 3A – Module M01: Data Loader & ALS Input Audit Report

## 1. Executive Summary & Metadata

- **Module**: M01 – Data Loader & ALS Input Audit
- **Project**: MoodGraph – Hybrid Recommendation System (MovieLens 25M)
- **Branch**: `feature/als-3a`
- **Execution Date**: 2026-10-30
- **Environment**:
  - OS: Windows 11 Pro 64-bit
  - Python: 3.12.3
  - PySpark: 4.2.0 (Local Standalone, master `local[*]`, 12 CPU cores, 16 GB RAM)
  - Hadoop: Winutils Hadoop 3.3.6 (`C:\hadoop\bin`)
  - JVM: Java 17.0.12 (Eclipse Adoptium OpenJDK 64-Bit Server VM)
- **M01 Status**: **`M01_ENGINEERING_PASS`** (All 8 constraints PASSED, 19/19 pytest suites PASSED, 0 data corruptions).

---

## 2. Parquet Schema & Ingestion Contract Verification

Dữ liệu được nạp thông qua module [recommender/als/data_loader.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/data_loader.py) với xác thực kiểu dữ liệu nghiêm ngặt:

| Dataset Path | Expected Schema | Ingested Schema | Nullable Policy | Status |
| :--- | :--- | :--- | :--- | :--- |
| `data/processed/splits/train` | `userId: int, movieId: int, rating: float, timestamp: long` | `userId: int, movieId: int, rating: float, timestamp: long` | Strictly non-null | PASS |
| `data/processed/splits/validation` | `userId: int, movieId: int, rating: float, timestamp: long` | `userId: int, movieId: int, rating: float, timestamp: long` | Strictly non-null | PASS |
| `data/processed/core/movies` | `movieId: int, title: string, genres: string, genre_list: array<string>` | `movieId: int, title: string, genres: string, genre_list: array<string>` | Strictly non-null ID | PASS |

> [!NOTE]
> Phân vùng `data/processed/splits/test` hoàn toàn **KHÔNG** được đọc hoặc nạp trong Module M01 để tuân thủ tuyệt đối quy tắc Data Leakage Isolation.

---

## 3. Train Data Integrity & Constraint Audit (24,675,013 Rows)

Kiểm toán toàn bộ 24,675,013 bản ghi huấn luyện thông qua hàm [validate_train_input_constraints](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/data_audit.py):

| Constraint / Check Description | Expected Value | Observed Value | Status |
| :--- | :--- | :--- | :--- |
| Total Train Ratings Count | 24,675,013 | 24,675,013 | PASS |
| Null `userId` count | 0 | 0 | PASS |
| Null `movieId` count | 0 | 0 | PASS |
| Null `rating` count | 0 | 0 | PASS |
| Null `timestamp` count | 0 | 0 | PASS |
| Rating Out-of-Bounds (`< 0.5` OR `> 5.0`) | 0 | 0 | PASS |
| Zero Ratings (`rating == 0.0`) | 0 (Unobserved != 0) | 0 | PASS |
| Rating Step Violations (Not in `{0.5, 1.0, ..., 5.0}`) | 0 | 0 | PASS |
| Duplicate Pairs `(userId, movieId)` | 0 | 0 | PASS |
| Dangling Movies (Train `movieId` not in Movie Catalog) | 0 | 0 | PASS |

---

## 4. Sparsity & Density Analysis

Ma trận tương tác User-Item được tính toán trên hai không gian:

### 4.1. Không gian Huấn luyện Thực tế (Train-Known Universe)
Chỉ tính trên tập hợp các phim có ít nhất 1 đánh giá trong tập Train:
- **Số người dùng (Users)**: 162,541
- **Số phim xuất hiện (Active Movies)**: 58,932
- **Tổng số ô ma trận (Total Cells)**: 162,541 × 58,932 = 9,578,866,212 ô
- **Số ô quan sát (Observed Ratings)**: 24,675,013
- **Mật độ (Density)**: `0.00257598` (tương đương **0.2576%**)
- **Độ thưa (Sparsity)**: `0.99742402` (tương đương **99.7424%**)

### 4.2. Không gian Danh mục Toàn phần (Full-Catalog Universe)
Tính trên toàn bộ 62,423 phim trong danh mục MovieLens 25M:
- **Số người dùng (Users)**: 162,541
- **Tổng danh mục phim (Catalog Movies)**: 62,423
- **Tổng số ô ma trận (Total Cells)**: 162,541 × 62,423 = 10,146,296,843 ô
- **Số ô quan sát (Observed Ratings)**: 24,675,013
- **Mật độ (Density)**: `0.00243192` (tương đương **0.2432%**)
- **Độ thưa (Sparsity)**: `0.99756808` (tương đương **99.7568%**)

---

## 5. Phân phối Mức độ Hoạt động (Activity Distributions)

### 5.1. Phân phối Đánh giá trên mỗi Người dùng (Ratings per User)
- **Tối thiểu (Min)**: 18 đánh giá
- **Trung vị (Median / p50)**: 69.0 đánh giá
- **Phân vị 95 (p95)**: 548.0 đánh giá
- **Tối đa (Max)**: 32,200 đánh giá

### 5.2. Phân phối Đánh giá trên mỗi Phim (Ratings per Movie)
- **Tối thiểu (Min)**: 1 đánh giá
- **Trung vị (Median / p50)**: 6.0 đánh giá
- **Phân vị 95 (p95)**: 1,442.0 đánh giá
- **Tối đa (Max)**: 80,448 đánh giá (Phim phổ biến nhất)

### 5.3. Phân nhóm Độ phổ biến Phim (Movie Popularity Buckets)
- **Nhóm 1–5 đánh giá (Long-tail cực đoan)**: 28,834 phim (chiếm 46.19% danh mục)
- **Nhóm 6–10 đánh giá (Ít tương tác)**: 6,838 phim (chiếm 10.95% danh mục)
- **Nhóm >10 đánh giá (Tương tác ổn định)**: 23,260 phim (chiếm 37.26% danh mục)
- **Nhóm 0 đánh giá trong Train (Unseen / Phim mới)**: 3,491 phim (chiếm 5.59% danh mục)

---

## 6. Khảo sát Cold-Start & Khả năng Phủ Tập Validation (Target Coverage)

### 6.1. Phim Cold-Start trong Danh mục
- Tổng danh mục: 62,423 phim.
- Phim đã có trong Train: 58,932 phim (94.41%).
- Phim chưa từng xuất hiện trong Train: 3,491 phim (**5.59%**).
- Phim chỉ có duy nhất 1 rating trong Train: 10,324 phim (16.54%).

### 6.2. Mức độ Bao phủ trên Tập Kiểm định (Validation Target Coverage)
Tập Validation gồm 162,541 cặp đánh giá hold-out (1 rating ngẫu nhiên mới nhất của mỗi user):

1. **Toàn bộ tập Validation (162,541 targets)**:
   - Số mục ALS có thể chấm điểm (Item factor tồn tại trong Train): **162,486** targets (**99.9662%**).
   - Số mục Unscorable do Cold-start Item (Phim chưa từng xuất hiện trong Train): **55** targets (**0.0338%**).
2. **Tập Validation Mục tiêu Tích cực (`rating >= 3.5`, 109,779 targets)**:
   - Số mục ALS có thể chấm điểm: **109,749** targets (**99.9727%**).
   - Số mục Unscorable do Cold-start Item: **30** targets (**0.0273%**).

### 6.3. Đề xuất Chiến lược Xử lý Cold-Start cho các Module tiếp theo
1. **Trong Huấn luyện ALS (M03–M06)**: Cấu hình bắt buộc tham số `coldStartStrategy="drop"` trong PySpark ALS Evaluator để loại trừ 55 mục không thể tính toán ma trận nhân tố, tránh NaN làm hỏng chỉ số RMSE / NDCG.
2. **Trong Phục vụ Khuyến nghị (Serving & Ranking)**: Đối với 55 mục cold-start này, hệ thống sẽ tự động kích hoạt fallback recommendation dựa trên Global Top Popularity hoặc thông qua nhánh Hybrid Knowledge Graph (Task 3B) dựa trên Genre/Director similarity.

---

## 7. Kết quả Kiểm thử Tự động (Automated Test Suite)

Tất cả 19 bài kiểm thử độc lập đã chạy và vượt qua 100%:

### 7.1. Suite M00: Môi trường & Hợp đồng Dữ liệu (5/5 PASS)
1. `test_01_git_safety_and_ignore`: PASSED
2. `test_02_manifest_verification`: PASSED
3. `test_03_spark_session_and_schema_contract`: PASSED
4. `test_04_spark_parquet_row_counts`: PASSED
5. `test_05_roadmap_provenance_and_cleanliness`: PASSED

### 7.2. Suite M01: Data Loader & Data Audit (14/14 PASS)
1. `test_01_loader_reads_valid_schema`: PASSED
2. `test_02_loader_fails_on_corrupt_schema`: PASSED
3. `test_03_missing_input_path`: PASSED
4. `test_04_detect_nulls_in_required_columns`: PASSED
5. `test_05_detect_rating_out_of_bounds`: PASSED
6. `test_06_detect_rating_step_violation`: PASSED
7. `test_07_detect_duplicate_user_movie_pairs`: PASSED
8. `test_08_detect_unreferenced_movies`: PASSED
9. `test_09_distinguish_missing_vs_zero_rating`: PASSED
10. `test_10_count_train_known_and_unseen_movies`: PASSED
11. `test_11_movie_popularity_binning`: PASSED
12. `test_12_density_and_sparsity_hand_calculation`: PASSED
13. `test_13_validation_item_coverage_hand_calculation`: PASSED
14. `test_14_empty_dataframe_handling`: PASSED

---

## 8. Kết luận & Quyết định Nghiệm thu

- Dữ liệu MovieLens 25M Parquet đã được chia tách hoàn toàn sạch sẽ, bảo đảm tính toàn vẹn 100%.
- Không phát hiện bất kỳ lỗi null, lỗi miền giá trị, lỗi bước nhảy rating hay trùng lặp user-movie.
- Tỷ lệ bao phủ kiểm định thực tế đạt mức rất cao: 99.9662% cho toàn bộ target và 99.9727% cho target tích cực.
- Module M01 chính thức đạt tiêu chuẩn nghiệm thu kỹ thuật: **`M01_ENGINEERING_PASS`**.
- Sẵn sàng chuyển tiếp sang **Module M02: Baseline & Popularity Recommender**.
