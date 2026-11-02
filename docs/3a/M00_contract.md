# MOODGRAPH | TASK 3A: SPARK ALS RECOMMENDER
## BÁO CÁO NGHIỆM THU MODULE M00: PROJECT CONTRACT, GIT SAFETY & ENVIRONMENT (BẢN ĐIỀU CHỈNH HẬU REVIEW)

- **Dự án:** Personalized Movie Recommendation using Knowledge Graphs and Apache Spark
- **Mã Task:** Task 3A – Spark MLlib ALS / Collaborative Filtering
- **Module:** M00 – Project Contract, Git Safety & Environment
- **Phiên bản Hợp đồng:** `3A-M00-v1.1` (Cập nhật theo chỉ đạo Technical Mentor)
- **Thời điểm kiểm định:** 2026-10-28
- **Trạng thái Module:** `PENDING_REVIEW (ENGINEERING_PASS - GIT BASELINE BLOCKER)`

---

## 1. KIỂM ĐỊNH NGUỒN GỐC ROADMAP (ROADMAP PROVENANCE AUDIT)

### 1.1. Báo cáo Thao tác Sao chép Tệp Kế hoạch
- **Nguồn gốc tệp:** Tệp Master Roadmap ban đầu được hệ thống soạn thảo và lưu tạm tại thư mục ngoài:  
  `D:\XNO - INTERNSHIP\VN30F_QUANT_ENGINE\docs\plans\TASK_3A_SPARK_ALS_ROADMAP.md`  
  do sự nhầm lẫn đường dẫn trong phiên làm việc trước đó.
- **Thao tác đồng bộ:** Agent đã thực hiện sao chép nguyên trạng tệp này về đúng vị trí chuẩn mực của dự án MoodGraph tại:  
  `docs/TASK_3A_SPARK_ALS_ROADMAP.md`.
- **Kiểm định mã băm (Hash Parity):**
  - SHA256 file nguồn: `90568faa3571490bb67561b9be34d1d5b882349d40242c146294b93cf122ee25`
  - SHA256 file đích: `90568faa3571490bb67561b9be34d1d5b882349d40242c146294b93cf122ee25`
  - Kết quả: **Khớp mã băm tuyệt đối 100%**.

### 1.2. Xác thực Tính Toàn vẹn Nội dung (Content Cleanliness)
- Đã quét tự động toàn bộ nội dung tệp bằng bộ từ khóa ngoài dự án (`VN30`, `XNO`, `phái sinh`, `quant_engine`, `stock`).
- **Kết quả:** 0 từ khóa ngoài lề xuất hiện.
- **Xác nhận:** Văn bản là 100% Master Roadmap chính thức của **Task 3A – Spark ALS**, bao quát toàn bộ 11 module M00–M10, kiến trúc ranh giới với Task 3B (Knowledge Graph), và quy chuẩn đánh giá User-wise Leave-1-Last trên MovieLens 25M.

---

## 2. HIỆN TRẠNG GIT, DỮ LIỆU TRACKING VÀ GIT BASELINE BLOCKER

### 2.1. Trạng thái Git Thực tế (Working Tree State)
- **Branch hiện tại:** `main` (tracking `origin/main`).
- **Thay đổi Phase 4 chưa commit (Uncommitted Phase 4 Changes):**
  - `HERMES.md` (modified – cập nhật tiến độ Phase 4 sang PROPOSED).
  - `recommender/preprocess.py` (untracked – mã nguồn pipeline chia tập Phase 4).
  - `recommender/validate_data.py` (untracked – mã nguồn kiểm định 8 test data quality Phase 4).
  - `docs/data_dictionary.md` (untracked – từ điển dữ liệu chuẩn hóa).
  - `docs/data_quality_report.md` (untracked – biên bản kiểm định 8/8 tests Phase 4).
  - `docs/preprocessing_report.md` (untracked – báo cáo kỹ thuật nén Parquet Phase 4).
- **Trạng thái trên `origin/main`:**
  - Commit mới nhất trên remote: `f12ee07 docs: update HERMES tracker with setup_data script reference`.
  - **Nhận định quan trọng:** Mã nguồn và tài liệu của Phase 4 **chưa xuất hiện trên `origin/main`**.

### 2.2. Kiểm định Dữ liệu Theo dõi qua `git ls-files`
Đã thực thi kiểm tra toàn bộ cây thư mục nhạy cảm bằng `git ls-files data/ models/ artifacts/`:
- Kết quả trả về: Duy nhất tệp rỗng `data/.gitkeep`.
- **Xác nhận an toàn:** Không có bất kỳ tệp dữ liệu thô (raw CSV/ZIP), tệp dữ liệu đã xử lý (Parquet splits), tệp mô hình (model binaries) hay artifact nào bị Git theo dõi ngoài ý muốn. Quy tắc `.gitignore` hoạt động chuẩn xác 100%.

### 2.3. Git Blocker & Đề Xuất Quy Trình Đưa Phase 4 vào Baseline Chung
- **Git Blocker:** Hiện tại working tree trên branch `main` đang chứa toàn bộ sản phẩm của Phase 4 ở trạng thái uncommitted. Nếu tự ý tạo branch `feature/als-3a` ngay bây giờ, các tệp uncommitted này sẽ bị mang theo hoặc gây xung đột với nhánh `feature/kg-3b` của đồng đội.
- **Quy trình đề xuất giải quyết an toàn (Dành cho Maintainer / Technical Mentor duyệt trước khi thực hiện):**
  1. *Bước 1 (Commit Phase 4 trên `main`):* Người quản trị hoặc Technical Mentor phê duyệt và commit toàn bộ gói Phase 4 lên `main`:
     ```bash
     git add HERMES.md recommender/preprocess.py recommender/validate_data.py docs/data_dictionary.md docs/data_quality_report.md docs/preprocessing_report.md
     git commit -m "feat(phase4): finalize data splitting pipeline, quality report and data dictionary"
     git push origin main
     ```
  2. *Bước 2 (Tạo nhánh cô lập cho Task 3A):* Từ điểm baseline sạch của `main`, tạo và chuyển sang nhánh riêng:
     ```bash
     git checkout -b feature/als-3a
     ```
  3. *Bước 3 (Thực hiện commit M00 trên `feature/als-3a`):* Commit các tệp hợp đồng và kiểm thử của Module M00:
     ```bash
     git add docs/TASK_3A_SPARK_ALS_ROADMAP.md docs/3a/M00_contract.md tests/als/test_m00_environment.py
     git commit -m "chore(3a): complete module M00 project contract and environment verification"
     ```

---

## 3. XÁC MINH MANIFEST VÀ ĐỐI CHIẾU NGUỒN DỮ LIỆU

### 3.1. Phân biệt Rạch ròi Checksum Nguồn và Checksum Manifest
- **Checksum ZIP nguồn:** `raw_zip_md5 = 6b51fb2759a8657d3bfcbfc42b592ada`. Đây là mã băm MD5 chính thức do GroupLens (University of Minnesota) công bố cho tệp `ml-25m.zip`, lưu độc lập tại `data/raw/ml-25m.zip.md5`.
- **Checksum của tệp `manifest.json`:** Tệp `data/processed/manifest.json` có mã băm SHA256 là `a0e5b8b00ec0c5a1164795b8de16822c8d247395955a9cff1e0abb3842e2d1a2`.

### 3.2. Mức độ Xác minh 10 Dataset Đã Xử lý
Để đảm bảo tính trung thực khoa học, báo cáo phân định minh bạch phạm vi kiểm định cho từng dataset:

| Tên Dataset | Đường dẫn Parquet | Mức độ kiểm định tại M00 | Ghi chú & Trạng thái |
| :--- | :--- | :--- | :--- |
| **`split_train`** | `data/processed/splits/train` | **Đọc đầy đủ nội dung bằng Spark** (Schema + Row count + Sample rows) | 24,675,013 dòng; 4 cột chuẩn; Khớp 100% |
| **`split_validation`** | `data/processed/splits/validation` | **Đọc đầy đủ nội dung bằng Spark** (Schema + Row count) | 162,541 dòng; 4 cột chuẩn; Khớp 100% |
| **`split_test`** | `data/processed/splits/test` | **Đọc đầy đủ nội dung bằng Spark** (Schema + Row count) | 162,541 dòng; 4 cột chuẩn; Khớp 100% |
| **`core_movies`** | `data/processed/core/movies` | **Đọc đầy đủ nội dung bằng Spark** (Schema + Row count) | 62,423 dòng; 4 cột chuẩn; Khớp 100% |
| **`core_links`** | `data/processed/core/links` | **Kiểm tra đường dẫn & đăng ký manifest** | Đã xác nhận thư mục tồn tại trên đĩa |
| **`core_tags`** | `data/processed/core/tags` | **Kiểm tra đường dẫn & đăng ký manifest** | Đã xác nhận thư mục tồn tại trên đĩa |
| **`core_genome_tags`** | `data/processed/core/genome_tags` | **Kiểm tra đường dẫn & đăng ký manifest** | Đã xác nhận thư mục tồn tại trên đĩa |
| **`core_genome_scores`**| `data/processed/core/genome_scores`| **Kiểm tra đường dẫn & đăng ký manifest** | Đã xác nhận thư mục tồn tại trên đĩa |
| **`feature_movie_genres`**| `data/processed/features/movie_genres`| **Kiểm tra đường dẫn & đăng ký manifest** | Đã xác nhận thư mục tồn tại trên đĩa |
| **`feature_tags_train`**| `data/processed/features/tags_train`| **Kiểm tra đường dẫn & đăng ký manifest** | Đã xác nhận thư mục tồn tại trên đĩa |

---

## 4. XÁC MINH SỐ DÒNG VÀ SCHEMA THỰC TẾ BẰNG PYSPARK

Bộ kiểm định tự động đã nạp trực tiếp Apache Spark và đếm số dòng thực tế trên toàn bộ 4 bảng trọng tâm (không dùng kết quả mô phỏng, không chạy lại preprocessing):

```text
- Train Count:       24,675,013 dòng  (Kỳ vọng: 24,675,013 | Sai lệch: 0 dòng)
- Validation Count:     162,541 dòng  (Kỳ vọng:    162,541 | Sai lệch: 0 dòng)
- Test Count:           162,541 dòng  (Kỳ vọng:    162,541 | Sai lệch: 0 dòng)
- Movies Count:          62,423 dòng  (Kỳ vọng:     62,423 | Sai lệch: 0 dòng)
- Thời gian đếm Spark:  4.22 giây trên 12 luồng CPU Ryzen 5 7530U
```

### Schema Chi Tiết Khớp 100% Data Dictionary:
- `splits/train`: `userId: int, movieId: int, rating: float, timestamp: bigint`.
- `splits/validation`: `userId: int, movieId: int, rating: float, timestamp: bigint`.
- `splits/test`: `userId: int, movieId: int, rating: float, timestamp: bigint`.
- `core/movies`: `movieId: int, title: string, genres: string, genre_list: array<string>`.

---

## 5. BẰNG CHỨNG THỰC THI BỘ KIỂM THỬ MỞ RỘNG (5/5 PASSED)

Bộ kiểm thử `tests/als/test_m00_environment.py` bao gồm toàn bộ 5 bài test theo yêu cầu review của Technical Mentor:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0 -- C:\Users\DAT\anaconda3\python.exe
cachedir: .pytest_cache
rootdir: D:\PROJECT BIG DATA\MoodGraph
plugins: anyio-4.8.0, Faker-37.1.0, langsmith-0.3.45, cov-7.1.0
collecting ... collected 5 items

tests/als/test_m00_environment.py::test_01_git_safety_and_ignore PASSED
tests/als/test_m00_environment.py::test_02_manifest_verification PASSED
tests/als/test_m00_environment.py::test_03_spark_session_and_schema_contract PASSED
tests/als/test_m00_environment.py::test_04_spark_parquet_row_counts PASSED
tests/als/test_m00_environment.py::test_05_roadmap_provenance_and_cleanliness PASSED

============================== 5 passed in 17.38s ==============================
```

---

## 6. DANH SÁCH FILE THAY ĐỔI VÀ KẾT LUẬN

### 6.1. Danh sách Tệp Thay đổi Trong Phiên Làm việc
- **Tạo mới:** `docs/TASK_3A_SPARK_ALS_ROADMAP.md` (Master Roadmap Task 3A).
- **Tạo mới:** `tests/als/test_m00_environment.py` (Bộ 5 bài test tự động cho M00).
- **Cập nhật:** `docs/3a/M00_contract.md` (Báo cáo hợp đồng & nghiệm thu M00 điều chỉnh).

### 6.2. Kết luận Nghiệm thu
- **Về mặt Kỹ thuật (Engineering):** `PASS` (5/5 automated tests đạt, số dòng Spark đếm thực tế khớp 100%, data contract rõ ràng).
- **Về mặt Quản trị Git (Baseline):** `PENDING_REVIEW`. M00 **chưa được đánh dấu hoàn thành tuyệt đối** cho đến khi Maintainer/Technical Mentor thực hiện đưa Phase 4 vào baseline commit trên `main` và phân nhánh an toàn sang `feature/als-3a`.
- **Cam kết kỷ luật:** Tuyệt đối không tự ý triển khai Module M01, không train ALS, không chỉnh sửa dữ liệu, không commit/push. Dừng chờ lệnh từ Technical Mentor.
