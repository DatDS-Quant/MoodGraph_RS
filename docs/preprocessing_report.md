# Báo cáo Tiền xử lý & Kiểm thử Dữ liệu Tự động (Preprocessing & Automated Validation Report)
## Dự án MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark

- **Tài liệu:** `docs/preprocessing_report.md`
- **Bộ dữ liệu mục tiêu:** MovieLens 25M
- **Mã nguồn pipeline:** `recommender/preprocess.py`
- **Mã nguồn test suite:** `recommender/validate_data.py`
- **Thời gian thực thi:** 69.04 giây (Preprocessing) + 85.34 giây (Validation Suite mở rộng)
- **Kích thước gói dữ liệu Parquet:** 205.51 MB (giảm từ 1,156.66 MB CSV gốc, tỷ lệ giảm 82.2%)
- **Trạng thái:** 8/8 Automated Tests PASSED (Trạng thái: **READY FOR MENTOR REVIEW**)
- **Mốc thời gian:** 2026-10-26 10:13:00 UTC (17:13:00 UTC+7)

---

## 1. Môi trường Thực thi & Quản lý Tài nguyên

| Thông số | Giá trị Cấu hình Thực tế | Ghi chú |
| :--- | :--- | :--- |
| **Hệ điều hành** | Windows 11 Pro 64-bit | Local environment |
| **CPU** | AMD Ryzen 5 7530U (6 Cores / 12 Threads) | `local[*]` khai thác 12 threads |
| **Bộ nhớ RAM** | 16 GB vật lý (Free Physical ~6.5 GB) | Cấu hình Driver/Executor: `5g` |
| **Java Environment** | OpenJDK 17.0.20 (Temurin-17) | `JAVA_HOME` hợp lệ |
| **Hadoop Windows Utility** | `C:\hadoop\bin\winutils.exe` (Hadoop 3.3.0) | `HADOOP_HOME` cấu hình tường minh |
| **Apache Spark** | PySpark 4.2.0 | Shuffle Partitions = 16, Adaptive Execution = True |
| **Chuẩn nén Output** | Snappy Parquet (Columnar Storage) | Tối ưu I/O và tính toán phân tán |

---

## 2. Cấu trúc Gói Dữ liệu Đầu ra (`data/processed/`)

Toàn bộ gói dữ liệu được tổ chức theo cấu trúc module rõ ràng, phân định độc lập giữa dữ liệu cốt lõi, dữ liệu phân chia kiểm thử và dữ liệu đặc trưng:

```text
data/
  processed/
    core/
      movies/             # 62,423 rows | 1.62 MB | schema: movieId, title, genres, genre_list
      links/              # 62,423 rows | 0.86 MB | schema: movieId, imdbId, tmdbId
      tags/               # 1,093,360 rows | 11.90 MB | schema: userId, movieId, tag, tag_clean, timestamp
      genome_tags/        # 1,128 rows | 0.02 MB | schema: tagId, tag
      genome_scores/      # 15,584,448 rows | 25.51 MB | schema: movieId, tagId, relevance
    splits/
      train/              # 24,675,013 rows | 147.14 MB | schema: userId, movieId, rating, timestamp
      validation/         # 162,541 rows | 1.95 MB | schema: userId, movieId, rating, timestamp
      test/               # 162,541 rows | 1.95 MB | schema: userId, movieId, rating, timestamp
    features/
      movie_genres/       # 107,245 rows | 0.48 MB | schema: movieId, genre
      tags_train/         # 1,074,090 rows | 14.08 MB | schema: userId, movieId, tag, tag_clean, timestamp
    manifest.json         # Siêu dữ liệu, phiên bản, hash SHA-256 từng file
    test_results.json     # Báo cáo kết quả 8 bài test tự động
```

---

## 3. Thống kê Trước và Sau Tiền xử lý (Before vs After Audit)

Tổng hợp đối soát chính xác số lượng bản ghi:
- **Tổng số dòng 6 file CSV nguồn:** **41,803,877** bản ghi.
- **Tổng số dòng 10 bảng Parquet đầu ra:** **42,985,212** bản ghi.

| Tên Bảng / Phân vùng | Số Dòng Nguồn | Số Dòng Parquet | Dung lượng CSV | Dung lượng Parquet | Tỷ lệ Nén |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `core/movies` | 62,423 | 62,423 | 2.90 MB | 1.62 MB | Giảm 44.1% |
| `core/links` | 62,423 | 62,423 | 1.31 MB | 0.86 MB | Giảm 34.3% |
| `core/tags` | 1,093,360 | 1,093,360 | 37.01 MB | 11.90 MB | Giảm 67.8% |
| `core/genome_tags` | 1,128 | 1,128 | 0.02 MB | 0.02 MB | Giữ nguyên |
| `core/genome_scores` | 15,584,448 | 15,584,448 | 415.00 MB | 25.51 MB | **Giảm 93.8%** |
| `splits/train` | - | 24,675,013 | - | 147.14 MB | Nén tối ưu |
| `splits/validation` | - | 162,541 | - | 1.95 MB | 1 record/user |
| `splits/test` | - | 162,541 | - | 1.95 MB | 1 record/user |
| **Tổng ratings (Train+Val+Test)** | **25,000,095** | **25,000,095** | **646.84 MB** | **151.04 MB** | **Giảm 76.6%** |
| `features/movie_genres` | - | 107,245 | - | 0.48 MB | Tách thể loại phẳng |
| `features/tags_train` | - | 1,074,090 | - | 14.08 MB | Chống rò rỉ triệt để |
| **TỔNG TOÀN BỘ GÓI** | **41,803,877** | **42,985,212** | **1,156.66 MB** | **205.51 MB** | **Giảm 82.2%** |

### Chi tiết phân loại và loại trừ trong `tags_train`:
- Tổng số tag nguồn: 1,093,360
- Số tag có người dùng không có mốc validation: **0** (100% người dùng gắn tag đều có rating).
- Số tag bị loại do vi phạm mốc thời gian (`timestamp >= val_cutoff_ts`): **18,021**
- Số tag vượt qua điều kiện thời gian: 1,075,339
- Số tag trong nhóm này trùng cặp `(userId, movieId)` với tập Validation: **768** (đã loại bỏ bằng `left_anti`).
- Số tag trong nhóm này trùng cặp `(userId, movieId)` với tập Test: **481** (đã loại bỏ bằng `left_anti`).
- Số bản ghi `tags_train` chuẩn hóa cuối cùng: **1,074,090** bản ghi (đảm bảo overlap với cả Validation và Test đều bằng **0**).

---

## 4. Kết quả Bộ Kiểm thử Tự động 8 Bài (Automated Test Suite)

Tất cả 8 bài kiểm thử nghiêm ngặt tại `recommender/validate_data.py` đã thực thi trực tiếp trên các tệp Parquet và đều đạt trạng thái **PASSED 100%**:

| Mã Test | Tên Bài Kiểm thử | Tiêu chuẩn Nghiệm thu | Kết quả Thực tế | Đánh giá |
| :--- | :--- | :--- | :--- | :--- |
| **TEST 1** | **Record Preservation** | - Tổng Train (24,675,013) + Val (162,541) + Test (162,541) = 25,000,095.<br>- Đối chiếu 2 chiều Spark trên 4 trường (`userId, movieId, rating, timestamp`). | - Tổng: 25,000,095 ratings.<br>- Missing in splits: 0.<br>- Extra in splits: 0.<br>- Attribute mismatches: 0. | **PASSED** |
| **TEST 2** | **Split Integrity** | - Không có cặp `(userId, movieId)` trùng lặp giữa các tập.<br>- Mỗi user có đúng 1 Val, 1 Test, và >= 18 Train.<br>- Trật tự ranh giới nghiêm ngặt: `Train < Val` và `Val < Test` xét cả mốc bằng timestamp và tie-breaker `movieId`. | - Overlap giữa các tập = 0.<br>- Distinct users = 162,541 ở cả 3 tập.<br>- Min train/user = 18.<br>- Vi phạm thứ tự Train-Val: 0.<br>- Vi phạm thứ tự Val-Test: 0. | **PASSED** |
| **TEST 3** | **Referential Integrity** | Mọi khóa ngoại `movieId`, `tagId` đều phải tồn tại trong bảng danh mục cha (`movies`, `genome_tags`). | 0 bản ghi mồ côi (Dangling foreign keys = 0 trên toàn bộ 5 mối quan hệ). | **PASSED** |
| **TEST 4** | **Schema Validation** | Kiểu dữ liệu thực tế của toàn bộ 10 dataset Parquet phải khớp 100% đặc tả schema kỹ thuật. | 0 mismatch. Mọi trường float, int, long, array, string chuẩn xác. | **PASSED** |
| **TEST 5** | **Information Preservation & Metadata Integrity** | - Không xóa phim thiếu genre (5,062 phim) hoặc thiếu genome (48,607 phim).<br>- Giữ nguyên chuỗi văn bản `"NA"` (16 tags).<br>- Giữ leading zeros IMDb (`0114709`).<br>- Khắc phục parser CSV với escape quote (0 null timestamp).<br>- Sai số float32 trên genome relevance < 1e-7. | - Đủ 62,423 phim.<br>- 5,062 phim rỗng thể loại.<br>- 48,607 phim không có genome.<br>- 16 tag mang chuỗi văn bản `"NA"`.<br>- 0 tag có timestamp bị null.<br>- Sai số cực đại float32 drift: 2.956e-08 (< 1e-7 tolerance).<br>- IMDb `"0114709"` nguyên vẹn.<br>- Bảng dẫn xuất `movie_genres` đủ 107,245 dòng. | **PASSED** |
| **TEST 6** | **Leakage Guard** | - Không có rating Test/Val trong Train.<br>- `tags_train` có 0 tag xảy ra tại hoặc sau mốc Validation.<br>- `tags_train` có 0 cặp `(userId, movieId)` xuất hiện trong tập Validation hoặc Test. | - Test in Train = 0.<br>- Val in Train = 0.<br>- Future tags in `tags_train` = 0.<br>- **Tags-Val item overlap = 0**.<br>- **Tags-Test item overlap = 0**. | **PASSED** |
| **TEST 7** | **Reproducibility** | Thuật toán split có tính xác định tuyệt đối (Deterministic). Chạy lại phân tách trên tập mẫu 500 users và đối chiếu từng bản ghi. | Chênh lệch giữa 2 lần chạy = 0 bản ghi. Khóa phụ `movieId` đảm bảo tính ổn định tuyệt đối. | **PASSED** |
| **TEST 8** | **Output Readability & Manifest Parity** | Spark đọc lại thành công toàn bộ 10 tệp Parquet từ đĩa, đối soát row count khớp 100% với `manifest.json`. | Đọc thành công 10/10 dataset. Parity errors = 0. Checksum SHA-256 đối soát toàn vẹn. | **PASSED** |

---

## 5. Ranh giới Rò rỉ Dữ liệu & Công bố Minh bạch (Transparency & Boundaries)

Nhằm đảm bảo tính trung thực học thuật và kỹ thuật:
1. **Intra-user Temporal Isolation:** Pipeline đảm bảo cô lập tuyệt đối dòng thời gian trên từng người dùng đơn lẻ (`Train < Val < Test`). Bảng `tags_train` không chứa bất kỳ thẻ tag nào xuất hiện sau mốc validation, và không chứa bất kỳ tương tác nào của người dùng với chính các phim thuộc tập validation/test.
2. **Giới hạn Cross-user Temporal Leakage:** Trong bài toán Collaborative Filtering offline, để bảo toàn 100% tập người dùng (162,541 users) mà không loại bỏ user hoạt động trong các thời kỳ khác nhau, giao thức Leave-1-Last chấp nhận việc tương tác train của user A có thể xảy ra sau mốc test của user B theo thời gian lịch thiên văn. Đây là trade-off đã được phê chuẩn trong `docs/evaluation_protocol.md`.
3. **Đặc thù Tag Genome:** Dữ liệu `genome-scores.csv` là ma trận điểm phù hợp sinh từ mô hình học máy của MovieLens dựa trên toàn bộ lịch sử gắn thẻ và phản hồi của cộng đồng. Do đó, Tag Genome chứa tri thức cộng đồng tổng hợp hậu kỳ (post-hoc collective metadata), không thể coi là đặc trưng hoàn toàn tách biệt theo từng lát cắt thời gian lịch sử. MoodGraph duy trì nhóm đối chứng song song Genre-only để bóc tách chính xác giá trị gia tăng của Tag Genome.
4. **Bảo tồn chuỗi `"NA"`:** Giá trị `"NA"` trong `tags.csv` là chuỗi ký tự thô do người dùng nhập. Pipeline tôn trọng nguyên bản chuỗi văn bản, không tự ý gán nghĩa ngữ nghĩa chủ quan hay chuyển đổi thành giá trị null/NaN.

---

## 6. Hướng dẫn Tái tạo và Kiểm tra (Reproducibility Guide)

Bất kỳ thành viên nào trong nhóm hoặc Technical Mentor đều có thể tái tạo lại toàn bộ quy trình này từ dữ liệu thô ban đầu:

```bash
# Bước 1: Bảo đảm dữ liệu thô đã có sẵn tại data/raw/ml-25m/
python scripts/setup_data.py

# Bước 2: Chạy toàn bộ pipeline tiền xử lý và sinh gói Parquet
python recommender/preprocess.py

# Bước 3: Chạy bộ kiểm thử tự động 8 bài để xác thực chất lượng dữ liệu
python recommender/validate_data.py
```

Toàn bộ thông tin phiên bản, môi trường thực thi và mã băm SHA-256 của từng file thành phần đã được lưu trữ vĩnh viễn tại [data/processed/manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json).
