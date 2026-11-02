# MoodGraph: Data Dictionary (Từ điển Dữ liệu Chuẩn hóa)

> **Dataset:** MovieLens 25M Processed Package (MoodGraph v1.0.0)  
> **Định dạng lưu trữ:** Apache Parquet (Snappy compression)  
> **Thư mục gốc:** `data/processed/`  
> **Engine xử lý:** Apache Spark (PySpark 4.2.0)  

---

## 1. Tổng quan Kiến trúc Dữ liệu (Architecture Overview)

Dữ liệu tiền xử lý được tổ chức thành 3 phân vùng độc lập nhằm đảm bảo tính toàn vẹn dữ liệu, chống rò rỉ thông tin (leakage guard) và phục vụ thống nhất cho các mô hình Collaborative Filtering (ALS), Content-Based, Knowledge Graph và Hybrid:

```text
data/processed/
├── core/                   # Các bảng thực thể và tương tác chuẩn hóa gốc
│   ├── movies/             # Danh mục phim và danh sách thể loại
│   ├── links/              # Định danh liên kết ngoài (IMDb, TMDb)
│   ├── tags/               # Toàn bộ tương tác gắn tag tự do từ người dùng
│   ├── genome_tags/        # Danh mục 1,128 tag chuẩn hóa trong Tag Genome
│   └── genome_scores/      # Ma trận điểm phù hợp (relevance) phim - tag genome
├── splits/                 # Tập phân chia đánh giá theo giao thức User-wise Leave-1-Last
│   ├── train/              # Tập huấn luyện (>= 18 tương tác đầu mỗi user)
│   ├── validation/         # Tập thẩm định (tương tác áp chót của mỗi user)
│   └── test/               # Tập kiểm thử (tương tác cuối cùng của mỗi user)
├── features/               # Đặc trưng trích xuất phục vụ trực tiếp cho mô hình & KG
│   ├── movie_genres/       # Cặp phẳng (movieId, genre) cho Content-Based & KG
│   └── tags_train/         # User tags đã lọc bỏ rò rỉ thời gian (train-only)
├── manifest.json           # Siêu dữ liệu, schema, checksum SHA-256 từng tệp
└── test_results.json       # Kết quả kiểm định tự động 8 bộ test chất lượng dữ liệu
```

---

## 2. Chi tiết Từ điển Dữ liệu (Data Dictionary by Dataset)

### 2.1. Phân vùng Core (`data/processed/core/`)

#### A. `core/movies/`
- **Mục đích:** Danh mục thực thể phim chuẩn hóa.
- **Số bản ghi:** 62,423
- **Dung lượng:** 1.62 MB
- **Khóa chính (PK):** `movieId`
- **Quy tắc đặc thù:** Chuỗi `(no genres listed)` được chuyển thành danh sách rỗng `[]`. Không xóa bất kỳ phim nào thiếu thể loại.

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `movieId` | `IntegerType` | False | Khóa chính của bộ phim. Tăng dần, không âm. | `1`, `260` |
| `title` | `StringType` | False | Tên đầy đủ của phim, thường kèm năm phát hành trong ngoặc đơn. | `"Toy Story (1995)"` |
| `genres` | `StringType` | False | Chuỗi thể loại gốc phân tách bởi ký tự gạch đứng `\|`. | `"Adventure\|Animation\|Children"` |
| `genre_list` | `ArrayType(StringType)` | False | Mảng danh sách các thể loại. Rỗng `[]` nếu phim mang nhãn `(no genres listed)`. | `["Adventure", "Animation", "Children"]` |

---

#### B. `core/links/`
- **Mục đích:** Bảng ánh xạ khóa ngoài sang các cơ sở dữ liệu phim quốc tế (IMDb, The Movie Database).
- **Số bản ghi:** 62,423
- **Dung lượng:** 0.86 MB
- **Khóa chính (PK):** `movieId`
- **Khóa ngoại (FK):** `movieId -> core/movies.movieId` (1:1 toàn vẹn)

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `movieId` | `IntegerType` | False | Khóa ngoại tham chiếu tới `movies.movieId`. | `1` |
| `imdbId` | `StringType` | False | Mã định danh IMDb 7 chữ số. **Bắt buộc giữ kiểu String** để bảo tồn số 0 ở đầu (leading zeros). | `"0114709"` |
| `tmdbId` | `IntegerType` | True | Mã định danh The Movie Database. Cho phép Null (có 107 phim thiếu TMDb ID trong dataset gốc). | `862` (hoặc `null`) |

---

#### C. `core/tags/`
- **Mục đích:** Lưu trữ toàn bộ tương tác người dùng gắn nhãn (free-text tags) cho phim.
- **Số bản ghi:** 1,093,360
- **Dung lượng:** 11.90 MB
- **Khóa tham chiếu:** `movieId -> core/movies.movieId`, `userId`
- **Quy tắc đặc thù:** Bảo toàn tuyệt đối 16 bản ghi chứa chuỗi ký tự `"NA"` (Namibia / North America / Not Applicable), không để parser chuyển nhầm thành `null` hay `NaN`.

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `userId` | `IntegerType` | False | Mã định danh người dùng gắn tag. | `3` |
| `movieId` | `IntegerType` | False | Khóa ngoại tham chiếu `movies.movieId`. | `260` |
| `tag` | `StringType` | False | Chuỗi tag văn bản nguyên bản người dùng nhập. | `"classic"`, `"NA"`, `"sci-fi"` |
| `timestamp` | `LongType` | False | Mốc thời gian Unix timestamp (tính bằng giây). | `1439472353` |
| `tag_clean` | `StringType` | False | Chuỗi tag đã chuẩn hóa chữ thường (lowercase) và cắt bỏ khoảng trắng thừa đầu/cuối. | `"classic"`, `"na"`, `"sci-fi"` |

---

#### D. `core/genome_tags/`
- **Mục đích:** Bảng từ điển 1,128 thuộc tính ngữ nghĩa chuẩn hóa trong nghiên cứu Tag Genome của GroupLens.
- **Số bản ghi:** 1,128
- **Dung lượng:** 0.02 MB
- **Khóa chính (PK):** `tagId`

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `tagId` | `IntegerType` | False | Khóa chính của tag genome (`1 <= tagId <= 1128`). | `1`, `1128` |
| `tag` | `StringType` | False | Tên ngữ nghĩa của tag. | `"007"`, `"atmospheric"`, `"zombies"` |

---

#### E. `core/genome_scores/`
- **Mục đích:** Điểm phù hợp (relevance score) giữa 13,816 phim và 1,128 tag genome, sinh bởi mô hình học máy của MovieLens.
- **Số bản ghi:** 15,584,448 (Dày đặc 100%: 13,816 x 1,128)
- **Dung lượng:** 25.51 MB
- **Khóa chính tổ hợp:** `(movieId, tagId)`
- **Khóa ngoại:** `movieId -> core/movies.movieId`, `tagId -> core/genome_tags.tagId`
- **Quy tắc:** Giữ toàn vẹn dải điểm liên tục `[0.0, 1.0]`. Không áp đặt ngưỡng lọc thô trong preprocessing để giữ tính linh hoạt cho Phase 6 (Knowledge Graph Construction).

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `movieId` | `IntegerType` | False | Khóa ngoại tham chiếu `movies.movieId`. | `1` |
| `tagId` | `IntegerType` | False | Khóa ngoại tham chiếu `genome_tags.tagId`. | `1` |
| `relevance` | `FloatType` | False | Điểm phù hợp liên tục trong đoạn `[0.0, 1.0]`. | `0.02875` |

---

### 2.2. Phân vùng Splits (`data/processed/splits/`)

Toàn bộ 3 tập dữ liệu phân chia đều tuân thủ chặt chẽ cùng một lược đồ (schema) và phân bổ khóa rời rạc (mutual exclusion):

#### A. `splits/train/`
- **Mục đích:** Huấn luyện mô hình Collaborative Filtering (ALS) và học đồ thị tri thức.
- **Số bản ghi:** 24,675,013 (98.70% tổng ratings)
- **Dung lượng:** 147.14 MB
- **Số user bao phủ:** Đúng 162,541 users (mỗi user có từ 18 đến 32,200 tương tác).
- **Quy tắc phân chia:** Gồm toàn bộ các tương tác của user có thứ hạng thời gian ngược `rn_desc > 2`.

#### B. `splits/validation/`
- **Mục đích:** Tinh chỉnh siêu tham số (hyperparameter tuning) và dừng sớm (early stopping).
- **Số bản ghi:** 162,541 (Đúng 1 tương tác áp chót cho mỗi user, `rn_desc == 2`).
- **Dung lượng:** 1.95 MB
- **Số user bao phủ:** Đúng 162,541 users.

#### C. `splits/test/`
- **Mục đích:** Đánh giá năng lực tổng quát hóa offline (Final Offline Evaluation).
- **Số bản ghi:** 162,541 (Đúng 1 tương tác cuối cùng theo thời gian cho mỗi user, `rn_desc == 1`).
- **Dung lượng:** 1.95 MB
- **Số user bao phủ:** Đúng 162,541 users.

#### Lược đồ chi tiết các tập Splits:

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `userId` | `IntegerType` | False | Mã định danh người dùng (`1 <= userId <= 162541`). | `1` |
| `movieId` | `IntegerType` | False | Khóa ngoại tham chiếu `movies.movieId`. | `296` |
| `rating` | `FloatType` | False | Điểm đánh giá: `0.5 <= rating <= 5.0`, bước nhảy chính xác 0.5. | `4.0`, `5.0` |
| `timestamp` | `LongType` | False | Mốc thời gian Unix timestamp (giây). Dùng làm khóa phân tách theo thứ tự tăng dần. | `1147880044` |

---

### 2.3. Phân vùng Features (`data/processed/features/`)

#### A. `features/movie_genres/`
- **Mục đích:** Quan hệ phẳng (movieId, genre) phục vụ nạp quan hệ `(:Movie)-[:IN_GENRE]->(:Genre)` trong Neo4j và Content-Based Baselines.
- **Số bản ghi:** 107,245
- **Dung lượng:** 0.48 MB
- **Khóa ngoại:** `movieId -> core/movies.movieId`

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `movieId` | `IntegerType` | False | Khóa ngoại tham chiếu `movies.movieId`. | `1` |
| `genre` | `StringType` | False | Tên một thể loại đơn lẻ (1 trong 19 thể loại chuẩn của MovieLens). Các phim không có thể loại đã được lọc sạch khỏi bảng quan hệ này. | `"Action"`, `"Comedy"` |

---

#### B. `features/tags_train/`
- **Mục đích:** Cung cấp thông tin user tag an toàn không rò rỉ (Strict Leakage Guard) để xây dựng hồ sơ người dùng hoặc quan hệ tri thức phía Train.
- **Số bản ghi:** 1,074,090
- **Dung lượng:** 14.08 MB
- **Rào chắn rò rỉ hai lớp (Dual Leakage Guard):**  
  1. `tags_train.timestamp < user_val_rating_timestamp` (loại 18,021 tag diễn ra đồng thời hoặc sau mốc Validation).
  2. `left_anti join` với `ratings_validation` và `ratings_test` trên cặp `(userId, movieId)` (loại tiếp 768 tag trùng phim Validation và 481 tag trùng phim Test, triệt tiêu hoàn toàn tương tác rò rỉ).

| Tên trường | Kiểu dữ liệu PySpark | Nullable | Mô tả & Ràng buộc giá trị | Ví dụ |
| :--- | :--- | :--- | :--- | :--- |
| `userId` | `IntegerType` | False | Mã định danh người dùng. | `3` |
| `movieId` | `IntegerType` | False | Khóa ngoại tham chiếu `movies.movieId` (đảm bảo không thuộc tập Validation hoặc Test của chính user này). | `260` |
| `tag` | `StringType` | False | Thẻ tag nguyên bản người dùng nhập. | `"classic"` |
| `timestamp` | `LongType` | False | Thời điểm gắn tag (nhỏ hơn nghiêm ngặt mốc Validation của user). | `1439472353` |
| `tag_clean` | `StringType` | False | Thẻ tag đã chuẩn hóa chữ thường và khoảng trắng. | `"classic"` |

---

## 3. Ma trận Toàn vẹn Khóa Ngoại (Foreign Key Integrity Matrix)

Tất cả các mối quan hệ liên bảng đã được kiểm chứng tự động bằng Test 3 (`validate_data.py`), cam kết 0 bản ghi mồ côi (dangling records):

| Bảng nguồn (Source Table) | Cột nguồn | Bảng đích (Target Table) | Cột đích | Trạng thái toàn vẹn | Số vi phạm |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `splits/train`, `val`, `test` | `movieId` | `core/movies` | `movieId` | Hoàn hảo (100%) | 0 |
| `core/tags` | `movieId` | `core/movies` | `movieId` | Hoàn hảo (100%) | 0 |
| `core/links` | `movieId` | `core/movies` | `movieId` | Hoàn hảo (100%) | 0 |
| `core/genome_scores` | `movieId` | `core/movies` | `movieId` | Hoàn hảo (100%) | 0 |
| `core/genome_scores` | `tagId` | `core/genome_tags` | `tagId` | Hoàn hảo (100%) | 0 |
| `features/tags_train` | `movieId` | `core/movies` | `movieId` | Hoàn hảo (100%) | 0 |

---

## 4. Hướng dẫn Đọc Dữ liệu Chuẩn với PySpark

Ví dụ nạp dữ liệu chuẩn xác trong các giai đoạn tiếp theo (Phase 5: ALS, Phase 6: Neo4j):

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("MoodGraph-DataLoader") \
    .config("spark.driver.memory", "4g") \
    .getOrCreate()

# Nạp tập Train cho mô hình Collaborative Filtering
train_df = spark.read.parquet("data/processed/splits/train")
print(f"Train row count: {train_df.count():,}")

# Nạp bảng phim và đặc trưng thể loại
movies_df = spark.read.parquet("data/processed/core/movies")
genres_df = spark.read.parquet("data/processed/features/movie_genres")

# Nạp tập tag đã kiểm duyệt chống rò rỉ thời gian
safe_tags_df = spark.read.parquet("data/processed/features/tags_train")
```
