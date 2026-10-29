# Báo cáo Kiểm định Chất lượng Dữ liệu (Data Quality Audit Report)
## Dự án MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark

- **Tài liệu:** `docs/data_quality_report.md`
- **Bộ dữ liệu mục tiêu:** MovieLens 25M (GroupLens Research, University of Minnesota)
- **Giai đoạn:** Phase 4 – Production-Grade Preprocessing & Validation
- **Thời điểm kiểm định:** 2026-10-26 10:13:00 UTC (17:13:00 UTC+7)
- **Công cụ kiểm tra:** Apache Spark (PySpark DataFrame API) & SHA-256 Checksums
- **Trạng thái:** Hoàn tất kiểm định toàn diện (Trạng thái: **READY FOR MENTOR REVIEW**)

---

## 1. Tổng quan Kiểm định Tính Toàn vẹn Tệp Nguồn

Toàn bộ 6 tệp CSV thô được giải nén từ `ml-25m.zip` đã được đối soát mã băm MD5 chuẩn từ GroupLens:
`MD5: 6b51fb2759a8657d3bfcbfc42b592ada` (Khớp 100%).

| Tên tệp CSV | Dung lượng (Bytes) | Dung lượng (MB MiB) | Số bản ghi (Rows) | Khóa chính / Khóa nghiệp vụ | Trạng thái Toàn vẹn |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `movies.csv` | 3,038,099 | 2.90 MiB | 62,423 | `movieId` | Đạt |
| `ratings.csv` | 678,260,987 | 646.84 MiB | 25,000,095 | `(userId, movieId)` | Đạt |
| `tags.csv` | 38,810,332 | 37.01 MiB | 1,093,360 | `(userId, movieId, tag, timestamp)` | Đạt |
| `genome-tags.csv` | 18,103 | 0.02 MiB | 1,128 | `tagId` | Đạt |
| `genome-scores.csv` | 435,164,157 | 415.00 MiB | 15,584,448 | `(movieId, tagId)` | Đạt |
| `links.csv` | 1,368,578 | 1.31 MiB | 62,423 | `movieId` | Đạt |
| **Tổng cộng** | **1,156,660,256** | **1,103.08 MiB (1,156.66 MB)** | **41,803,877** | | **Toàn vẹn 100%** |

---

## 2. Kiểm định Chi tiết Từng Tệp Dữ liệu

### 2.1. `ratings.csv` (25,000,095 records)
- **Schema khai báo:** `userId: int`, `movieId: int`, `rating: float`, `timestamp: long`.
- **Kiểm tra Null / Khuyết:** `0` bản ghi null ở mọi cột.
- **Kiểm tra Trùng lặp Khóa Nghiệp vụ `(userId, movieId)`:**
  - Kết quả: **`0` bản ghi trùng lặp**. Mỗi người dùng đánh giá một bộ phim tối đa 1 lần.
- **Kiểm tra Miền Giá trị Điểm số (Rating Range & Step):**
  - Giá trị nhỏ nhất: `0.5`
  - Giá trị lớn nhất: `5.0`
  - Bước nhảy hợp lệ: Toàn bộ 25,000,095 ratings thuộc tập `{0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0}`.
- **Kiểm tra Thời gian (Timestamp):**
  - Min timestamp: `789652009` (09/01/1995 18:46:49 UTC).
  - Max timestamp: `1574327703` (21/11/2019 16:15:03 UTC).
  - Không có timestamp âm hoặc timestamp tương lai ngoài phạm vi phát hành dataset.
- **Bảo toàn Dữ liệu:**
  - Đối chiếu 2 chiều Spark trên toàn bộ 4 trường (`userId, movieId, rating, timestamp`): 0 missing, 0 extra, 0 attribute diffs giữa raw CSV và hợp Train+Val+Test.

### 2.2. `movies.csv` (62,423 records)
- **Schema khai báo:** `movieId: int`, `title: string`, `genres: string`.
- **Kiểm tra Trùng lặp `movieId`:** `0` bản ghi trùng khóa chính.
- **Kiểm tra Thể loại:**
  - Có **5,062 phim** (chiếm `8.11%`) mang giá trị `(no genres listed)`.
  - Không xóa bỏ 5,062 phim này. Trong pipeline, trường `genre_list` được gán mảng rỗng `[]` để bảo toàn danh mục phim thực tế.
  - Không suy diễn thể loại từ tiêu đề phim để tránh suy đoán sai lệch.

### 2.3. `tags.csv` (1,093,360 records)
- **Schema khai báo:** `userId: int`, `movieId: int`, `tag: string`, `timestamp: long`.
- **Kiểm tra Chuỗi Văn bản `"NA"`:**
  - Có chính xác **16 bản ghi** mang giá trị chuỗi là `"NA"`.
  - *Bản chất:* Người dùng nhập chuỗi văn bản thuần túy `"NA"`. Pipeline tôn trọng nguyên bản chuỗi ký tự, không tự gán nghĩa ngữ nghĩa chủ quan và không để parser chuyển đổi thành giá trị null/NaN.
  - Cột `tag` gốc được bảo tồn nguyên vẹn 100%. Bổ sung thêm cột `tag_clean` (lowercase, trim khoảng trắng) phục vụ phân tích mà không ghi đè giá trị gốc.
- **Xử lý Ký tự Ngoại lệ (Triple Quotes):**
  - Phát hiện 2 dòng (dòng 835367 và 938378) chứa dấu ngoặc kép ba (`"""..."""`) lồng dấu phẩy. Nếu đọc CSV mặc định sẽ làm lệch cột và sinh ra timestamp bị null.
  - Pipeline đã bổ sung cấu hình `.option("quote", "\"").option("escape", "\"")`, bảo đảm đọc chuẩn xác 100% (0 bản ghi bị null timestamp).

### 2.4. `genome-tags.csv` (1,128 records)
- **Schema khai báo:** `tagId: int`, `tag: string`.
- **Kiểm tra Khóa Chính:** `tagId` chạy liên tục từ `1` đến `1,128`, không trùng lặp, không có giá trị null.

### 2.5. `genome-scores.csv` (15,584,448 records)
- **Schema khai báo:** `movieId: int`, `tagId: int`, `relevance: float`.
- **Kiểm tra Trùng lặp `(movieId, tagId)`:** `0` bản ghi trùng lặp.
- **Cấu trúc Ma trận Dày đặc:** Đúng `13,816 phim` x `1,128 tags` = `15,584,448 dòng`.
- **Kiểm tra Miền Giá trị & Sai số Float32 (Drift Tolerance):**
  - Min relevance: `0.0003`, Max relevance: `1.0000`.
  - Không có giá trị âm hoặc giá trị > 1.0.
  - Kiểm tra độ lệch dấu phẩy động khi lưu kiểu `FloatType` (float32): Sai số cực đại so với double thô là `2.9563903770e-08`, hoàn toàn nằm trong ngưỡng dung sai đơn chính xác IEEE 754 (< 1e-7).
  - Toàn bộ 15.58M bản ghi được giữ nguyên vẹn trong bản chuẩn hóa Parquet, không tự ý lọc ngưỡng 0.8 để dành quyền quyết định cho Phase 6 (Knowledge Graph Construction).

### 2.6. `links.csv` (62,423 records)
- **Schema khai báo:** `movieId: int`, `imdbId: string`, `tmdbId: int`.
- **Bảo toàn Số 0 ở Đầu (Leading Zeros) của `imdbId`:**
  - Giữ kiểu `StringType`. Ví dụ `movieId = 1` có `imdbId = "0114709"` (đủ 7 ký tự). Không bị ép kiểu số nguyên làm mất số 0 đầu.
- **Giá trị Thiếu `tmdbId`:**
  - Có đúng **107 phim** khuyết giá trị `tmdbId` (`null`). Đây là giá trị thiếu hợp lệ từ nguồn GroupLens do chưa ánh xạ được sang TMDb, được giữ nguyên `null`.

---

## 3. Kiểm định Tính Toàn vẹn Tham chiếu (Referential Integrity)

Thực hiện kiểm tra khóa ngoại (Foreign Key Left Anti-Join) giữa tất cả các bảng dữ liệu:

| Quan hệ Tham chiếu Khóa Ngoại | Bảng Con | Bảng Cha | Số Bản ghi Mồ côi (Dangling Records) | Đánh giá |
| :--- | :--- | :--- | :--- | :--- |
| `ratings.movieId -> movies.movieId` | `ratings.csv` | `movies.csv` | **0** | Toàn vẹn 100% |
| `tags.movieId -> movies.movieId` | `tags.csv` | `movies.csv` | **0** | Toàn vẹn 100% |
| `links.movieId -> movies.movieId` | `links.csv` | `movies.csv` | **0** | Toàn vẹn 100% |
| `genome_scores.movieId -> movies.movieId` | `genome-scores.csv` | `movies.csv` | **0** | Toàn vẹn 100% |
| `genome_scores.tagId -> genome_tags.tagId` | `genome-scores.csv` | `genome-tags.csv` | **0** | Toàn vẹn 100% |

> **Kết luận:** Hệ thống dữ liệu nguồn MovieLens 25M đạt tính nhất quán tham chiếu hoàn hảo. Không tồn tại bất kỳ bản ghi mồ côi nào giữa các bảng.

---

## 4. Độ phủ Dữ liệu (Coverage Analysis)

- **Độ phủ Phim có Rating:** `59,047 / 62,423` phim (`94.59%`). Có `3,376` phim catalog chưa từng nhận rating.
- **Độ phủ Phim có Thể loại hợp lệ:** `57,361 / 62,423` phim (`91.89%`).
- **Độ phủ Phim có Tag Người dùng:** `45,251 / 62,423` phim (`72.49%`).
- **Độ phủ Phim có Tag Genome:** `13,816 / 62,423` phim (`22.13%`).
- **Độ phủ Lượng Tương tác Ratings của Phim có Tag Genome:** `24,674,113 / 25,000,095` ratings (**`98.70%`**).

---

## 5. Kết luận Nghiệm thu Data Quality

Bộ dữ liệu đã vượt qua 100% các tiêu chí kiểm định nghiêm ngặt:
1. Không mất mát bản ghi.
2. Không suy diễn dữ liệu giả định.
3. Bảo toàn kiểu dữ liệu nhạy cảm (chuỗi IMDb, float relevance, tag `"NA"`).
4. Phân vùng triệt tiêu rò rỉ thông tin tương tác giữa `tags_train` và các tập Validation/Test.
5. Sẵn sàng chuyển giao sang Technical Mentor thẩm định chính thức.
