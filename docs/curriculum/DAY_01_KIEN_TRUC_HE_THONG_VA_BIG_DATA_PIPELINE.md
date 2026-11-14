# KHÓA HUẤN LUYỆN LÀM CHỦ MOODGRAPH (5-DAY MASTERY CURRICULUM)
# BÀI GIẢNG NGÀY 01: KIẾN TRÚC HỆ THỐNG TỔNG THỂ & BIG DATA PIPELINE

> **Vai trò Mentor**: Bài giảng này được thiết kế dành riêng cho anh để hiểu sâu từ gốc rễ đến ngọn ngành hệ thống MoodGraph. Mỗi phần đều đính kèm **ĐỊA CHỈ FILE VÀ DÒNG CODE CHÍNH XÁC** trong dự án, giúp anh khi đứng trước Hội đồng Giảng viên có thể tự tin 100%, thầy hỏi câu nào là mở ngay file đó, chỉ đúng dòng code đó giải thích rành rọt!

---

## MỤC LỤC BÀI GIẢNG NGÀY 01

1. **Lộ Trình Tổng Thể 5 Ngày Đạt 90%+ Độ Hiểu Sâu**
2. **Bản Đồ Kiến Trúc Toàn Hệ Thống MoodGraph (Architecture Map)**
3. **Bảng Tra Cứu Nhanh Cho Thầy Xem (Code Show-and-Tell Cheat Sheet)**
4. **Bản Chất Bộ Dữ Liệu Lớn MovieLens 25M & Movie Genome**
5. **Độ Thưa Ma Trận (Matrix Sparsity) & Thách Thức Big Data**
6. **Mổ Xẻ Chi Tiết PySpark Preprocessing Pipeline (`recommender/preprocess.py`)**
   * 6.1. Thiết lập SparkSession tối ưu hóa trên Windows 11
   * 6.2. Định nghĩa Schema cứng (Explicit StructType)
   * 6.3. Làm sạch dữ liệu và tách đa nhãn Thể loại (Genre Explosion)
   * 6.4. Thuật toán Phân chia Thời gian Leave-1-Last bằng Spark Window Function
   * 6.5. Kỹ thuật Anti-Join chống 100% Rò rỉ Dữ liệu (Zero Data Leakage)
   * 6.6. Đóng gói lưu trữ dạng Parquet Columnar với Snappy Compression
7. **Bảo Chứng Chất Lượng & Tính Toàn Vẹn (`manifest.json` & SHA-256)**
8. **5 Câu Hỏi Vấn Đáp "Chí Mạng" Của Giảng Viên & Cách Trả Lời Điểm 10**
9. **Bài Tập Thực Hành Ngày 01 Dành Cho Anh**

---

## 1. LỘ TRÌNH TỔNG THỂ 5 NGÀY ĐẠT 90%+ ĐỘ HIỂU SÂU

```text
[NGÀY 1] (HÔM NAY): Kiến trúc Hệ thống & Big Data Pipeline (MovieLens 25M, Spark, Parquet, Leave-One-Out)
    │
[NGÀY 2]: Trụ Cột Gợi Ý 1 - Collaborative Filtering với Ma Trận Phân Rã Spark ALS (Loss, Latent Factors)
    │
[NGÀY 3]: Trụ Cột Gợi Ý 2 - Đồ Thị Tri Thức Đa Tầng (Embedded Knowledge Graph, Metapaths P1-P2-P3, Inverted Index)
    │
[NGÀY 4]: Trụ Cột Hợp Nhất Đa Mô Hình (Hybrid Cormack RRF, Min-Max, Re-ranking, Closed-Loop Feedback)
    │
[NGÀY 5]: Đánh Giá Học Thuật (HR@K, NDCG@K, MRR), Full-Stack Serving & Kịch Bản Phản Biện Trước Hội Đồng
```

---

## 2. BẢN ĐỒ KIẾN TRÚC TOÀN HỆ THỐNG MOODGRAPH

MoodGraph là một hệ thống gợi ý điện ảnh kết hợp học máy phân tán quy mô lớn và đồ thị tri thức, chia làm 4 tầng độc lập:

```text
+-----------------------------------------------------------------------------------+
|                        TẦNG 1: DỮ LIỆU & PIPELINE (BIG DATA)                      |
|  - MovieLens 25M Raw CSVs (25M ratings, 62K movies, 1.1M tags, 15.58M genome)    |
|  - Apache Spark 3.x / 4.x (PySpark) Data Cleansing & Strict Schema Ingestion       |
|  - User-wise Leave-1-Last Chronological Split (Train: 24.67M, Val: 162K, Test: 162K) |
|  - Parquet Columnar Storage (Snappy compressed, 205.5 MB thay vì >1.2 GB CSV)     |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                   TẦNG 2: MÔ HÌNH HỌC MÁY & ĐỒ THỊ TRI THỨC                       |
|  [Trụ Cột A: Collaborative Filtering]     [Trụ Cột B: Knowledge Graph Engine]     |
|   - Spark MLlib ALS Matrix Factorization   - Đồ thị tri thức nhúng in-memory       |
|   - 25M ratings phân tán                   - 62,423 Movies, 19 Genres, 1,128 Tags  |
|   - Latent User/Item Vectors (k = 32)      - Khai phá 3 Metapaths P1, P2, P3       |
|   - Phục vụ sở thích hành vi lịch sử       - Phục vụ tâm trạng và tính giải thích  |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                    TẦNG 3: BỘ HỢP NHẤT LAI & DỊCH VỤ WEB BACKEND                  |
|  - Thuật toán xếp hạng Reciprocal Rank Fusion (Cormack RRF) k = 60                |
|  - Bộ chuẩn hóa Min-Max Normalized Weighted Combination                           |
|  - Bộ đa dạng hóa danh mục kết quả (Genre Coverage / Intra-List Diversity)        |
|  - Dynamic Closed-Loop Re-ranking (Phản hồi tức thì khi người dùng chấm sao)     |
|  - FastAPI ASGI Backend (Cổng 8000, async endpoints, Swagger UI)                 |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
|                   TẦNG 4: GIAO DIỆN NGƯỜI DÙNG & PHÒNG THÍ NGHIỆM                 |
|  - Mode A: Discovery Feed (Khám phá điện ảnh theo cảm xúc, Poster tự phục hồi)    |
|  - Mode B: Academic Lab (So sánh trực tiếp Head-to-Head ALS vs KG vs RRF)        |
|  - Mạng đồ thị tri thức đa tầng tương tác vis-network (Obsidian Dark Glass)      |
|  - Không gian nhúng 3D Three.js OrbitControls (Trực quan hóa UMAP/PCA cụm phim)   |
+-----------------------------------------------------------------------------------+
```

---

## 3. BẢNG TRA CỨU NHANH CHO THẦY XEM (CODE SHOW-AND-TELL CHEAT SHEET)

Khi thầy cô yêu cầu: *"Em mở code phần này ra cho tôi xem nằm ở file nào, hàm nào?"*, anh lập tức mở đúng các file sau:

| Thầy Cô Hỏi Về Vấn Đề Gì | File Code Cần Mở | Hàm / Class Cụ Thể | Dòng Code |
| :--- | :--- | :--- | :--- |
| **Pipeline tiền xử lý Big Data Spark** | [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) | Hàm `run_pipeline()` | Line 79 - 372 |
| **Cấu hình SparkSession trên Windows** | [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) | Hàm `get_spark_session()` | Line 37 - 50 |
| **Định nghĩa Schema chuẩn hóa** | [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) | `ratings_raw_schema`, `movies_raw_schema` | Line 102 - 137 |
| **Tách nhãn Thể loại (Genre Array)** | [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) | `F.split(F.col("genres"), "\\|")` | Line 149 - 156 |
| **Chiến lược chia Train/Val/Test** | [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) | `Window.partitionBy("userId").orderBy(...)` | Line 213 - 226 |
| **Chống rò rỉ dữ liệu (Anti-Join)** | [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) | `tags_clean.join(... how="left_anti")` | Line 272 - 278 |
| **Đóng gói Parquet & Checksum** | [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) | `compute_dir_sha256_and_size()` | Line 62 - 76, 305 - 318 |
| **File Báo cáo Dữ liệu & Checksums** | [data/processed/manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json) | File JSON thống kê toàn bộ output | Line 1 - 100 |
| **Bộ kiểm tra chất lượng dữ liệu** | [recommender/validate_data.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/validate_data.py) | Great Expectations Data Quality Validator | Toàn bộ file |
| **Phân tích khám phá dữ liệu (EDA)** | [recommender/eda.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/eda.py) | Hàm tính Sparsity, Gini, Power-Law | Toàn bộ file |

---

## 4. BẢN CHẤT BỘ DỮ LIỆU LỚN MOOVIELENS 25M & MOVIE GENOME

Dự án sử dụng bộ dữ liệu chuẩn mực học thuật quốc tế **MovieLens 25M** do phòng thí nghiệm GroupLens (Đại học Minnesota, Hoa Kỳ) phát hành, kết hợp dữ liệu nghiên cứu **Movie Genome**.

### Bảng Thống Kê Quy Mô Dữ Liệu Thực Tế Trong Dự Án:
* **Tổng số lượt đánh giá (Ratings)**: 25,000,095 dòng (thang điểm 0.5 đến 5.0 sao).
* **Tổng số người dùng (Users)**: 162,541 người dùng độc lập.
* **Tổng số tác phẩm điện ảnh (Movies)**: 62,423 bộ phim.
* **Tổng số thẻ gắn từ người dùng (User Tags)**: 1,093,360 thẻ văn bản tự do.
* **Tổng số điểm liên kết tâm trạng Genome (Genome Scores)**: 15,584,448 điểm số liên kết.
* **Tổng số chiều thuộc tính tâm trạng Genome (Genome Tags)**: 1,128 chiều vector cảm xúc điện ảnh (ví dụ: `atmospheric`, `surreal`, `thought-provoking`, `melancholy`, `dark comedy`...).
* **Liên kết dữ liệu ngoài (Links)**: 62,423 mã định danh liên kết trực tiếp IMDb ID và TMDb ID.

> **Ý nghĩa học thuật cho đồ án Big Data**:
> Dữ liệu 25 triệu dòng không thể xử lý bằng thư viện thông thường như Pandas trên RAM một máy tính đơn lẻ nếu không dùng kỹ thuật phân vùng phân tán. Đây là lý do chúng ta bắt buộc sử dụng **Apache Spark (PySpark DataFrame)** để xử lý song song trên nhiều lõi CPU.

---

## 5. ĐỘ THƯA MA TRẬN (MATRIX SPARSITY) & THÁCH THỨC BIG DATA

Khi thầy hỏi: *"Độ thưa ma trận trong bài toán của em là bao nhiêu và nó gây ra khó khăn gì?"*, anh trình bày như sau:

### Công thức tính Độ thưa Ma trận:
```text
Tổng số ô trong ma trận = Số Users × Số Movies
                       = 162,541 × 62,423
                       = 10,146,296,843 ô (hơn 10.1 tỷ ô tiềm năng)

Số ô đã có dữ liệu đánh giá = 25,000,095 ô

Tỷ lệ mật độ (Density) = 25,000,095 / 10,146,296,843 ≈ 0.002464 (tương đương 0.246%)

Độ thưa Ma trận (Sparsity) = 1 - Density = 1 - 0.002464 ≈ 99.754%
```

### Ý nghĩa thực tiễn:
* **Hơn 99.75% các ô trong ma trận người dùng - phim là ô trống** (người dùng chưa từng xem hoặc chưa từng đánh giá phim đó).
* Nếu dùng thuật toán lọc cộng tác truyền thống (k-NN dựa trên tương đồng Cosine giữa các dòng User), độ phức tạp tính toán là O(N^2) trên 162K users và sẽ gặp hiện tượng "véc-tơ trực giao rỗng" vì hai người dùng ngẫu nhiên hiếm khi xem trùng một bộ phim.
* **Giải pháp của MoodGraph**: 
  1. Sử dụng **Phân rã ma trận ALS (Alternating Least Squares)** để ánh xạ không gian 10.1 tỷ ô thưa thớt về không gian ẩn (Latent Factor Space) 32 chiều liên tục.
  2. Bổ sung **Đồ thị Tri thức Đa tầng (Knowledge Graph)** để liên kết các bộ phim thưa thớt thông qua cầu nối Thể loại (Genre) và Nhãn Tâm trạng (Genome Mood Tags).

---

## 6. MỔ XẺ CHI TIẾT PYSPARK PREPROCESSING PIPELINE

File mã nguồn chính: [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py)

### 6.1. Thiết Lập SparkSession Tối Ưu Hóa (Lines 37–50)
```python
def get_spark_session(app_name: str = "MoodGraph_Preprocessing") -> SparkSession:
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
```
* `local[*]`: Sử dụng toàn bộ các lõi CPU của máy để chạy worker song song.
* `spark.sql.shuffle.partitions = 16`: Tránh tạo ra 200 partition mặc định quá nhỏ gây nghẽn I/O khi shuffle dữ liệu.
* `spark.sql.adaptive.enabled = true`: Bật cơ chế Adaptive Query Execution (AQE) của Spark để tự động tối ưu kế hoạch thực thi khi join các bảng lớn.
* `snappy`: Thuật toán nén siêu tốc của Google cân bằng tối hảo giữa tốc độ giải nén và dung lượng lưu trữ.

---

### 6.2. Định Nghĩa Schema Cứng (Explicit Schema) (Lines 102–137)
Tại sao không dùng `inferSchema=True`?
* **Lý do Big Data**: `inferSchema` yêu cầu Spark phải đọc quét toàn bộ file CSV hai lần (1 lần để suy diễn kiểu dữ liệu, 1 lần để tải dữ liệu), làm tăng gấp đôi thời gian I/O trên file 25 triệu dòng.
* Khai báo Schema tường minh giúp Spark ép kiểu ngay từ dòng byte đầu tiên và từ chối mọi dòng dữ liệu sai định dạng:
```python
ratings_raw_schema = StructType([
    StructField("userId", IntegerType(), nullable=False),
    StructField("movieId", IntegerType(), nullable=False),
    StructField("rating", FloatType(), nullable=False),
    StructField("timestamp", LongType(), nullable=False),
])
```

---

### 6.3. Làm Sạch Dữ Liệu Và Tách Đa Nhãn Thể Loại (Lines 149–156)
Trong file CSV gốc, cột thể loại có dạng chuỗi ghép `Action|Adventure|Sci-Fi` hoặc `(no genres listed)`.
Spark thực hiện chuẩn hóa:
```python
movies_clean = movies_df.withColumn(
    "genre_list",
    F.when(
        (F.col("genres").isNull()) | (F.col("genres") == "(no genres listed)"),
        F.array().cast(ArrayType(StringType()))
    ).otherwise(F.split(F.col("genres"), "\\|"))
)
```
Nếu phim không có thể loại, chuyển thành mảng rỗng thay vì để chuỗi lỗi; nếu có, tách thành mảng mảng chuỗi `ArrayType(StringType())`. Sau đó dùng `F.explode("genre_list")` để tạo bảng chuẩn hóa thực thể đồ thị [recommender/preprocess.py#L256-L260](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L256-L260).

---

### 6.4. Thuật Toán Phân Chia Thời Gian Leave-1-Last (Lines 213–244)
Đây là phần **học thuật quan trọng bậc nhất** mà thầy cô sẽ thẩm vấn kỹ:

```text
       Lịch sử xem phim của mỗi người dùng theo dòng thời gian (Timestamp)
[ ... Quá khứ: Đánh giá phim 1, 2, 3, ... ] -> [ Đánh giá Kế chót ] -> [ Đánh giá Cuối cùng ]
                   │                                     │                      │
                   ▼                                     ▼                      ▼
         TẬP HUẤN LUYỆN (TRAIN)                   TẬP VALIDATION            TẬP TEST
          (rn_desc > 2)                            (rn_desc == 2)        (rn_desc == 1)
       24,675,013 lượt đánh giá                    162,541 lượt          162,541 lượt
```

Đoạn mã Spark Window Function thực thi:
```python
# Phân vùng theo từng User, sắp xếp giảm dần theo thời gian đánh giá
split_window = Window.partitionBy("userId").orderBy(
    F.col("timestamp").desc(),
    F.col("movieId").desc()  # Khóa phụ giải quyết xung đột khi cùng timestamp
)

ranked_ratings = ratings_df.withColumn("rn_desc", F.row_number().over(split_window))

# Tách thành 3 tập dữ liệu không giao thoa (Disjoint sets)
test_df  = ranked_ratings.filter(F.col("rn_desc") == 1).drop("rn_desc")
val_df   = ranked_ratings.filter(F.col("rn_desc") == 2).drop("rn_desc")
train_df = ranked_ratings.filter(F.col("rn_desc") > 2).drop("rn_desc")
```

> **Tại sao không chia ngẫu nhiên (Random 80/10/10 Split)?**
> Nếu chia ngẫu nhiên, mô hình sẽ học dữ liệu của "tương lai" để dự đoán hành vi trong "quá khứ". Trong thực tế triển khai, hệ thống gợi ý chỉ biết quá khứ của người dùng để gợi ý phim tiếp theo. Do đó, **User-wise Leave-1-Last Chronological Split** là quy chuẩn vàng học thuật bắt buộc để mô phỏng chính xác bài toán thực tế.

---

### 6.5. Kỹ Thuật Anti-Join Chống Rò Rỉ Dữ Liệu Tuyệt Đối (Lines 263–280)
Khi tạo đặc trưng gắn thẻ của người dùng (`tags_train`), nếu người dùng gắn một thẻ vào một bộ phim ở tập Test nhưng mô hình huấn luyện lại được nhìn thấy thẻ đó thì sẽ xảy ra hiện tượng **Rò rỉ tương tác (Interaction Leakage)**.
Hệ thống sử dụng kỹ thuật lọc thời gian kết hợp phép nối phủ định Spark Left-Anti Join:
```python
tags_train_df = (
    tags_clean.join(user_val_cutoffs, on="userId", how="inner")
    .filter(F.col("timestamp") < F.col("val_cutoff_ts")) # Chỉ lấy thẻ tạo trước mốc validation
    .drop("val_cutoff_ts")
    .join(val_items, on=["userId", "movieId"], how="left_anti") # Loại bỏ item ở tập Val
    .join(test_items, on=["userId", "movieId"], how="left_anti") # Loại bỏ item ở tập Test
)
```
* **Kết quả**: Đảm bảo 100% mô hình hoàn toàn không có bất kỳ thông tin nào về các bộ phim nằm trong tập kiểm định và thử nghiệm.

---

### 6.6. Đóng Gói Lưu Trữ Dạng Parquet Columnar
Sau khi làm sạch và phân chia, toàn bộ dữ liệu được lưu dưới dạng file Parquet phân vùng tại `data/processed/`:
* File CSV thô ban đầu: **~1.2 GB**.
* File Parquet sau tiền xử lý: **205.51 MB** (tiết kiệm hơn 82% dung lượng đĩa nhờ cơ chế nén cột theo kiểu dữ liệu và Snappy compression).
* Hỗ trợ **Predicate Pushdown**: Khi truy vấn đọc một cột cụ thể, Spark không cần quét qua các cột khác, giảm thiểu tối đa tải I/O.

---

## 7. BẢO CHỨNG CHẤT LƯỢNG & TÍNH TOÀN VẸN (`manifest.json` & SHA-256)

Mọi dữ liệu sau khi chạy xong pipeline đều được tính mã băm SHA-256 cho từng file và lưu lại tại [data/processed/manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json):

* **Dataset Name**: MovieLens 25M - MoodGraph Processed Package
* **Version**: 1.0.0
* **Tổng số bản ghi sau xử lý**: 42,985,212 bản ghi.
* **Tổng dung lượng gói xử lý**: 205.51 MB.
* **Thời gian thực thi pipeline Spark**: 69.04 giây.

Mỗi khi hệ thống huấn luyện khởi động, hàm kiểm định sẽ đọc `manifest.json` và kiểm tra checksum, bảo đảm không có bất kỳ file nào bị lỗi phần cứng hay biến đổi dữ liệu ngoài ý muốn.

---

## 8. 5 CÂU HỎI VẤN ĐÁP "CHÍ MẠNG" CỦA GIẢNG VIÊN & CÁCH TRẢ LỜI ĐIỂM 10

Dưới đây là 5 câu hỏi kinh điển nhất của các thầy cô bộ môn Dữ liệu Lớn khi phản biện đồ án:

### Câu Hỏi 1: *"Tại sao em không dùng thư viện Pandas để đọc file CSV cho đơn giản mà phải dùng Apache Spark?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, bộ dữ liệu MovieLens 25M có hơn 25 triệu dòng đánh giá và 15.5 triệu dòng genome scores. Khi nạp toàn bộ vào bộ nhớ, Pandas yêu cầu lượng RAM gấp 3 đến 5 lần dung lượng file và chỉ chạy đơn luồng trên một lõi CPU, rất dễ gây ra lỗi tràn bộ nhớ (Out-Of-Memory).
> Trong khi đó, Apache Spark sử dụng cấu trúc phân vùng dữ liệu phân tán (DataFrame Resilient Distributed Dataset), quản lý bộ nhớ thông qua cơ chế Catalyst Optimizer và Tungsten Execution Engine, đồng thời tận dụng toàn bộ số lõi CPU của máy tính để xử lý song song. Khi mở rộng lên cụm máy chủ nhiều nút (cluster), mã nguồn PySpark này có thể giữ nguyên mà không cần phải viết lại."*

### Câu Hỏi 2: *"Em giải thích kỹ thuật phân chia tập dữ liệu (Data Splitting) của em xem? Tại sao không dùng K-Fold Cross Validation hay Random Train/Test Split?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, hệ thống gợi ý là bài toán dự đoán hành vi tương lai dựa trên dữ liệu quá khứ. Nếu chia ngẫu nhiên (Random Split) hoặc K-Fold thông thường, một lượt xem phim vào năm 2018 có thể lọt vào tập Train để dự đoán một lượt xem phim vào năm 2015 trong tập Test. Đây là lỗi rò rỉ dữ liệu thời gian nghiêm trọng (Temporal Data Leakage).
> Đồ án áp dụng phương pháp User-wise Leave-1-Last Chronological Split: Với mỗi người dùng, hệ thống sử dụng hàm Spark Window sắp xếp các tương tác giảm dần theo mốc thời gian (timestamp). Đánh giá cuối cùng (rn = 1) được đưa vào tập Test, đánh giá kế chót (rn = 2) đưa vào tập Validation, và toàn bộ đánh giá trước đó (rn > 2) dùng để huấn luyện. Phương pháp này phản ánh trung thực 100% trải nghiệm thực tế của người dùng."*

### Câu Hỏi 3: *"Làm sao em chứng minh được tập Train không bị rò rỉ thông tin về nhãn (Tags) của tập Test?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, trong file code `recommender/preprocess.py` tại dòng 263 đến 280, em đã thiết kế bộ lọc 2 lớp:
> Lớp 1: Em lọc theo điều kiện thời gian: chỉ giữ lại các tags được gắn trước thời điểm tương tác của tập Validation (`timestamp < val_cutoff_ts`).
> Lớp 2: Em thực hiện phép nối phủ định Spark Left-Anti Join (`how='left_anti'`) với các cặp `(userId, movieId)` xuất hiện trong tập Validation và Test. Bất kỳ phim nào người dùng tương tác trong tập kiểm định đều bị loại bỏ hoàn toàn khỏi đặc trưng thẻ huấn luyện."*

### Câu Hỏi 4: *"Tại sao hệ thống lại lưu trữ định dạng Parquet thay vì giữ nguyên CSV?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, Parquet là định dạng lưu trữ dạng cột (Columnar Storage) chuẩn mực trong hệ sinh thái Big Data:
> Thứ nhất, Parquet nén dữ liệu theo từng cột cùng kiểu dữ liệu bằng thuật toán Snappy, giúp giảm kích thước từ 1.2 GB CSV xuống còn 205.5 MB (giảm 82% dung lượng).
> Thứ hai, Parquet lưu trữ sẵn lược đồ (Schema) và thống kê Min/Max của từng khối dữ liệu. Khi truy vấn một vài cột nhất định, Spark áp dụng cơ chế Column Pruning và Predicate Pushdown để chỉ đọc đúng các byte cần thiết mà không cần quét toàn bộ file, giúp tốc độ nạp dữ liệu nhanh hơn từ 5 đến 10 lần so với CSV."*

### Câu Hỏi 5: *"Độ thưa ma trận của em là hơn 99.7%, vậy hệ thống làm thế nào để gợi ý được phim cho người dùng khi hầu hết các ô đều rỗng?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, để giải quyết vấn đề độ thưa 99.754%, MoodGraph áp dụng kiến trúc kết hợp 2 hướng tiếp cận (Hybrid Architecture):
> Hướng 1: Mô hình ALS sử dụng kỹ thuật phân rã ma trận xấp xỉ bậc thấp (Low-rank Matrix Factorization) để ánh xạ ma trận thưa về không gian 32 chiều liên tục, tìm ra sở thích tiềm ẩn giữa những người dùng có chung hành vi.
> Hướng 2: Bổ sung Đồ thị Tri thức Đa tầng (Knowledge Graph). Ngay cả khi hai bộ phim chưa từng được cùng một người xem, chúng vẫn được kết nối thông qua các nút trung gian là Thể loại (Genre) và Nhãn Tâm trạng (Genome Mood Tags) với hơn 1,128 chiều cảm xúc, giúp giải quyết triệt để vấn đề thưa dữ liệu và hỗ trợ giải thích lý do gợi ý."*

---

## 9. BÀI TẬP THỰC HÀNH NGÀY 01 DÀNH CHO ANH

Để nhớ lâu và tự tay kiểm chứng các con số trong bài giảng, anh hãy mở Terminal và thực hiện 3 lệnh sau:

### Lệnh 1: Xem trực tiếp file Manifest chứa toàn bộ số liệu thống kê
```powershell
Get-Content -Path "data\processed\manifest.json" | Select-Object -First 50
```
*Mục đích*: Thấy tận mắt số dòng 25,000,095 ratings, 24.67M train, 162K val, 162K test.

### Lệnh 2: Kiểm tra dung lượng và các thư mục Parquet sau xử lý
```powershell
Get-ChildItem -Path "data\processed\splits", "data\processed\core"
```
*Mục đích*: Thấy các thư mục `train`, `validation`, `test`, `movies`, `genome_scores` được lưu dưới dạng file `.parquet`.

### Lệnh 3: Mở file mã nguồn `recommender/preprocess.py` để xem các đoạn code quan sát
Anh mở file [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py) và đọc các dòng:
* Dòng 37–50: Cấu hình Spark.
* Dòng 213–226: Spark Window Function Leave-1-Last.
* Dòng 263–280: Phép Anti-Join chống rò rỉ dữ liệu.

---
*Ngày mai (Ngày 02), chúng ta sẽ bước sang Bài giảng chuyên sâu về Trụ cột Gợi ý 1: **Thuật toán Ma trận Phân rã Spark ALS, Hàm mất mát Loss Function, Regularization, và cách tối ưu siêu tham số trên Big Data**.*
