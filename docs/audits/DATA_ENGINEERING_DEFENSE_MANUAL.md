# BÁO CÁO PHẢN BIỆN KHOA HỌC: TOÀN BỘ VẤN ĐỀ DỮ LIỆU (DATA PIPELINE & KNOWLEDGE GRAPH DATA ENGINEERING)
## DỰ ÁN: MOODGRAPH — BẢO VỆ TRƯỚC HỘI ĐỒNG TS. BÙI THANH HÙNG

**Môn học:** Giới thiệu về Dữ liệu lớn (Big Data)  
**Tác giả:** Đội ngũ Kỹ sư Dữ liệu & Nghiên cứu Đồ thị Tri thức MoodGraph  
**Vị trí tài liệu:** `docs/audits/DATA_ENGINEERING_DEFENSE_MANUAL.md`  
**Mục đích:** Cung cấp bộ câu hỏi phản biện chuyên sâu, câu trả lời chuẩn học thuật đan thép và liên kết mã nguồn cụ thể (dòng code, tệp dữ liệu) giúp tác giả làm chủ 100% bản chất dữ liệu khi Thầy Bùi Thanh Hùng chất vấn.

---

## MỤC LỤC CHI TIẾT
1. [Tổng quan Kiến trúc Dữ liệu Lớn (Big Data Architecture Overview)](#1-tổng-quan-kiến-trúc-dữ-liệu-lớn)
2. [Bộ 10 Câu hỏi Phản biện Sống còn về Dữ liệu & Lời giải Đan thép](#2-bộ-10-câu-hỏi-phản-biện-sống-còn-về-dữ-liệu)
   - [Câu 1: Nguồn gốc, quy mô và tính xác thực của bộ dữ liệu](#câu-1-nguồn-gốc-quy-mô-và-tính-xác-thực-của-bộ-dữ-liệu)
   - [Câu 2: Công nghệ xử lý Dữ liệu lớn và tối ưu hóa phân mảnh Parquet](#câu-2-công-nghệ-xử-lý-dữ-liệu-lớn-và-tối-ưu-hóa-phân-mảnh-parquet)
   - [Câu 3: Giao thức chia Train/Val/Test và cam kết Zero Leakage](#câu-3-giao-thức-chia-trainvaltest-và-cam-kết-zero-leakage)
   - [Câu 4: Xử lý tệp 15.5 triệu dòng Genome Scores chống tràn RAM](#câu-4-xử-lý-tệp-155-triệu-dòng-genome-scores-chống-tràn-ram)
   - [Câu 5: Chuyển đổi dữ liệu bảng (Tabular) thành Đồ thị Tri thức (KG)](#câu-5-chuyển-đổi-dữ-liệu-bảng-tabular-thành-đồ-thị-tri-thức-kg)
   - [Câu 6: Vấn đề dữ liệu đuôi dài (Long-Tail) và Cold-Start](#câu-6-vấn-đề-dữ-liệu-đuôi-dài-long-tail-và-cold-start)
   - [Câu 7: Tránh rò rỉ nhãn khi tiền xử lý thẻ người dùng (User Tags)](#câu-7-tránh-rò-rỉ-nhãn-khi-tiền-xử-lý-thẻ-người-dùng-user-tags)
   - [Câu 8: Đồng bộ tương tác người dùng thời gian thực (Live Dual-Sync)](#câu-8-đồng-bộ-tương-tác-người-dùng-thời-gian-thực-live-dual-sync)
   - [Câu 9: Tính tiền định và chống trùng lặp dữ liệu (Idempotency)](#câu-9-tính-tiền-định-và-chống-trùng-lặp-dữ-liệu-idempotency)
   - [Câu 10: Ràng buộc tính nhất quán và kiểm tra toàn vẹn mã băm SHA256](#câu-10-ràng-buộc-tính-nhất-quán-và-kiểm-tra-toàn-vẹn-mã-băm-sha256)
3. [Bản đồ Dò vết Mã nguồn (Source Code Traceability Map)](#3-bản-đồ-dò-vết-mã-nguồn-source-code-traceability-map)

---

## 1. TỔNG QUAN KIẾN TRÚC DỮ LIỆU LỚN

Hệ thống MoodGraph xử lý toàn bộ tập dữ liệu chuẩn quốc tế **MovieLens 25M** (hơn 41.8 triệu bản ghi thô, 25 triệu lượt đánh giá) theo mô hình đường ống dữ liệu 3 tầng (3-Tier Big Data Pipeline):

```text
[ TẦNG 1: DỮ LIỆU THÔ (RAW) ]
  movielens/25m: movies.csv, ratings.csv, genome-tags.csv, genome-scores.csv, tags.csv
                           │
                           ▼  (Apache Spark 3.5+ Catalyst Optimizer & Window Partitioning)
[ TẦNG 2: DỮ LIỆU CHẾ BIẾN CHUẨN HÓA (PROCESSED PARQUET) ]
  data/processed/
    ├── core/ (movies, links, genome_tags, genome_scores)
    ├── features/ (movie_genres, tags_train)
    └── splits/ (train: 24.67M, validation: 162.5k, test: 162.5k)
                           │
                           ▼  (PyArrow Streaming Batch Ingestion: batch_size=5000/10000)
[ TẦNG 3: ĐỒ THỊ TRI THỨC NHÚNG (EMBEDDED KNOWLEDGE GRAPH) ]
  In-Memory Inverted Indices (RAM) + Gzip-Pickled Snapshot (embedded_kg_cache.pkl.gz)
    ├── Nodes: User (162k), Movie (62k), Genre (19), GenomeTag (1,128)
    └── Edges: [:RATED], [:IN_GENRE], [:HAS_GENOME_TAG] (Top-M Filtered)
```

---

## 2. BỘ 10 CÂU HỎI PHẢN BIỆN SỐNG CÒN VỀ DỮ LIỆU

### CÂU 1: NGUỒN GỐC, QUY MÔ VÀ TÍNH XÁC THỰC CỦA BỘ DỮ LIỆU
**Hội đồng hỏi:**  
*"Dữ liệu dự án lấy từ đâu? Quy mô thực tế thế nào? Có phải nhóm tự tạo dữ liệu nhỏ lẻ (toy data) để chạy demo không?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, dự án sử dụng bộ dữ liệu chuẩn học thuật **MovieLens 25M** được phát hành bởi phòng nghiên cứu **GroupLens Research (Đại học Minnesota)** vào tháng 12/2019 (trích dẫn công trình: *F. Maxwell Harper & Joseph A. Konstan, ACM TiiS 2015*).
- Dữ liệu thô gồm **25,000,095 đánh giá**, **1,093,360 thẻ người dùng gắn**, **62,423 bộ phim** và ma trận đặc trưng ngữ nghĩa **15,584,448 dòng điểm liên quan genome**.
- Toàn bộ tệp nén gốc được kiểm tra mã băm toàn vẹn: `MD5 = 6b51fb2759a8657d3bfcbfc42b592ada`. Toàn bộ dữ liệu sau khi chế biến được kiểm toán tự động và lưu đặc tả trong tệp cấu hình nghiệm thu `manifest.json`.

**Vị trí mã nguồn và tài liệu đối chứng:**
- Tệp đặc tả dữ liệu: [data/processed/manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json#L5-L40)
- Tệp kiểm tra chất lượng dữ liệu: [docs/data_quality_report.md](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/data_quality_report.md#L1-L50)
- Mã nguồn kiểm tra tính toàn vẹn: [recommender/validate_data.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/validate_data.py#L40-L95)

---

### CÂU 2: CÔNG NGHỆ XỬ LÝ DỮ LIỆU LỚN VÀ TỐI ƯU HÓA PHÂN MẢNH PARQUET
**Hội đồng hỏi:**  
*"Với 25 triệu dòng dữ liệu, nhóm dùng Pandas hay công nghệ gì để tiền xử lý? Tại sao lại chuyển từ CSV sang Parquet?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, với hơn 25 triệu bản ghi, việc sử dụng Pandas trên bộ nhớ RAM đơn luồng sẽ dẫn đến sụp đổ bộ nhớ (Out-Of-Memory). Nhóm đã sử dụng **Apache Spark (PySpark DataFrame API)** kết hợp bộ tối ưu hóa truy vấn **Catalyst Optimizer**.
- Toàn bộ dữ liệu được chuyển đổi từ CSV dạng văn bản thô sang định dạng cột phân tán **Snappy Parquet** vì 3 lý do cốt tử trong Dữ liệu lớn:
  1. **Nén dữ liệu vượt trội:** Giảm dung lượng từ hơn 1.2 GB CSV xuống còn **205.51 MB Parquet** (tỷ lệ nén gần 6 lần).
  2. **Tối ưu hóa đọc theo cột (Columnar Projection & Predicate Pushdown):** Khi nạp đồ thị hay mô hình ALS, hệ thống chỉ cần đọc đúng các cột `userId`, `movieId`, `rating` mà không phải quét toàn bộ dòng dữ liệu.
  3. **Bảo tồn kiểu dữ liệu chuẩn (Strict Typed Schema):** Định dạng Parquet lưu trực tiếp kiểu dữ liệu nguyên thủy (`int32`, `float32`, `int64`), triệt tiêu hoàn toàn lỗi parse chuỗi (Type Casting Overhead) khi đọc lại.

**Vị trí mã nguồn:**
- Đường ống xử lý Spark: [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L45-L120)
- Hàm lưu Parquet phân mảnh: [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L280-L315)
- Thông số phân mảnh: 16 partitions, nén snappy tại [data/processed/manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json#L15-L18).

---

### CÂU 3: GIAO THỨC CHIA TRAIN/VAL/TEST VÀ CAM KẾT ZERO LEAKAGE
**Hội đồng hỏi:**  
*"Dữ liệu được chia Train, Validation, Test theo tỷ lệ ngẫu nhiên 80/10/10 hay thế nào? Làm sao đảm bảo không bị rò rỉ dữ liệu (Data Leakage) trong hệ gợi ý?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, trong hệ thống gợi ý, **tuyệt đối không được chia ngẫu nhiên (Random Split)** vì sẽ gây ra hiện tượng rò rỉ thời gian (Temporal Leakage - lấy tương lai dự đoán quá khứ).
- Nhóm áp dụng chuẩn mực học thuật quốc tế khắt khe: **Giao thức phân chia theo thời gian trên từng người dùng (User-wise Leave-1-Last)**:
  - Sắp xếp tương tác của từng người dùng theo thứ tự thời gian tăng dần: `timestamp ASC, movieId ASC` (giải quyết trường hợp cùng giây bằng `movieId`).
  - **Tập Test:** Tương tác cuối cùng của mỗi người dùng (`rn_desc == 1`, đúng **162,541 ratings**).
  - **Tập Validation:** Tương tác áp chót của mỗi người dùng (`rn_desc == 2`, đúng **162,541 ratings**).
  - **Tập Train:** Toàn bộ các tương tác trước đó trong lịch sử (`rn_desc > 2`, gồm **24,675,013 ratings**).
- **Cam kết Zero Leakage cho Đồ thị Tri thức:** Toàn bộ tập Validation và Test hoàn toàn bị **CẤM NẠP VÀO GRAPH** (được kiểm tra tự động tại `verify_split_isolation`). Đồ thị tri thức chỉ học từ tri thức quá khứ trong Train.

**Vị trí mã nguồn:**
- Logic phân chia Window Function PySpark: [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L195-L245)
- Tách bạch dữ liệu không giao nhau: [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L235-L244)
- Kiểm định cô lập split: [recommender/kg/checks.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/checks.py#L45-L75)

---

### CÂU 4: XỬ LÝ TỆP 15.5 TRIỆU DÒNG GENOME SCORES CHỐNG TRÀN RAM
**Hội đồng hỏi:**  
*"Tệp genome_scores có hơn 15.5 triệu dòng, nếu nạp hết vào RAM hoặc cơ sở dữ liệu đồ thị thì sẽ nổ bộ nhớ. Nhóm xử lý bài toán này như thế nào?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, đây chính là bài toán chắt lọc tín hiệu (Signal Distillation) kinh điển của Dữ liệu lớn.
- Bảng `core/genome_scores` có tới **15,584,448 dòng** (tương ứng ma trận dày đặc 13,816 phim x 1,128 thẻ). Trong thực tế, đa phần các cặp điểm liên quan đều có giá trị rất nhỏ (`relevance < 0.2`), chỉ là nhiễu thống kê.
- Nhóm đã đưa ra **Chính sách lọc Top-M Thẻ cảm xúc cốt lõi (Top-M Genome Policy)**:
  1. Với mỗi bộ phim, chỉ giữ lại tối đa **$M = 20$ thẻ** có điểm số liên quan cao nhất.
  2. Cơ chế chống hòa điểm tiền định (Deterministic Tie-break): Sắp xếp theo `relevance DESC, tagId ASC`.
  3. Sử dụng **PyArrow Streaming Batch Ingestion** nạp theo từng lô 10,000 dòng, không bao giờ load cả 15.5 triệu dòng cùng lúc vào RAM.
- **Kết quả:** Giảm số cạnh từ 15.58 triệu cạnh xuống còn **265,500 cạnh chất lượng cao** (giảm hơn 98% dung lượng cạnh), đỉnh bộ nhớ RAM duy trì ổn định dưới **600 MB**, không bao giờ bị lỗi tràn bộ nhớ (Out-Of-Memory).

**Vị trí mã nguồn:**
- Chính sách Top-M trong cấu hình: [recommender/kg/kg_config.yaml](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L14)
- Đọc stream lọc Top-M bằng PyArrow: [recommender/kg/data_access.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/data_access.py#L85-L125)
- Đo đạc thực nghiệm mở rộng quy mô (Scaling Report): [docs/kg/import_report.md](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/kg/import_report.md#L41-L69)

---

### CÂU 5: CHUYỂN ĐỔI DỮ LIỆU BẢNG (TABULAR) THÀNH ĐỒ THỊ TRI THỨC (KG)
**Hội đồng hỏi:**  
*"Từ các bảng dữ liệu quan hệ (Parquet Tables), làm sao nhóm ánh xạ (mapping) thành Đỉnh (Nodes) và Cạnh (Edges) trong Đồ thị?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, quá trình nạp dữ liệu tuân thủ nghiêm ngặt nguyên lý kỹ thuật đồ thị: **Tạo Đỉnh trước, Nối Cạnh sau (Nodes First, Edges Second)**:
  1. **Bước 1: Nạp 4 loại đỉnh (Nodes):**
     - Đọc `core/movies/` -> Khởi tạo đỉnh `Movie(movieId, title, genresRaw)`.
     - Đọc `features/movie_genres/` -> Khởi tạo 19 đỉnh `Genre(name)`.
     - Đọc `core/genome_tags/` -> Khởi tạo 1,128 đỉnh `GenomeTag(tagId, name)`.
     - Đọc `splits/train/` -> Khởi tạo đỉnh `User(userId)`.
  2. **Bước 2: Nạp 3 loại quan hệ (Edges):**
     - Cạnh `[:IN_GENRE]`: Nối từ `Movie` sang `Genre`.
     - Cạnh `[:HAS_GENOME_TAG]`: Nối từ `Movie` sang `GenomeTag` kèm thuộc tính trọng số `relevance`.
     - Cạnh `[:RATED]`: Nối từ `User` sang `Movie` kèm thuộc tính `rating` và `timestamp`.
  3. **Tổ chức chỉ mục ngược (Inverted Indices) trong Embedded KG:** Mọi cạnh đều được lưu trữ hai chiều (`user_rated_movie` <-> `movie_rated_by_users`) dưới dạng cấu trúc `dict` và `set` trong RAM để phục vụ suy luận đường dẫn P1, P2, P3 với độ phức tạp $O(1)$.

**Vị trí mã nguồn:**
- Hàm nạp đồ thị hoàn chỉnh: [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L252-L318)
- Định nghĩa các thao tác merge đỉnh và cạnh: [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L67-L132)
- Bản cài đặt tương đương trên Neo4j: [recommender/kg/import_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/import_graph.py#L67-L130)

---

### CÂU 6: VẤN ĐỀ DỮ LIỆU ĐUÔI DÀI (LONG-TAIL) VÀ COLD-START
**Hội đồng hỏi:**  
*"Trong tập MovieLens 25M, phân phối dữ liệu phim thế nào? Các phim chưa từng có ai xem (Cold-Start) thì Đồ thị Tri thức xử lý ra sao?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, nhóm đã tiến hành phân tích khoa học toàn bộ 62,423 phim tại Module M09 và phát hiện:
  - **Hơn 51.78% danh mục (32,325 phim) thuộc diện Đuôi Dài Cực Hạn (Extreme Long-Tail):** Gồm 3,491 phim có đúng 0 rating trong Train và 28,834 phim chỉ có từ 1 đến 5 lượt đánh giá.
  - **Mật độ ma trận cực kỳ thưa thớt (Sparsity):** Chỉ đạt **0.2576%**.
- **Cơ chế xử lý Cold-Start vượt trội của Knowledge Graph:**
  - Đối với các mô hình Collaborative Filtering như Spark ALS, phim Cold-Start (0 rating) sẽ hoàn toàn không có vector đặc trưng (Unscoreable).
  - Ngược lại, Đồ thị Tri thức kết nối phim qua các thuộc tính nội dung phong phú (`Movie -[:IN_GENRE]-> Genre` và `Movie -[:HAS_GENOME_TAG]-> Tag`). Dù một bộ phim độc lập (Indie film) chưa từng có ai đánh giá trong Train, chỉ cần nó có thông tin Thể loại hoặc Thẻ ngữ nghĩa tâm trạng, các đường suy luận **P1** và **P2** vẫn tìm thấy đường đi và chấm điểm chính xác cho người dùng phù hợp.

**Vị trí mã nguồn và báo cáo chẩn đoán:**
- Báo cáo khoa học phân tích đuôi dài M09: [docs/3a/M09_diagnostics_report.md](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_report.md#L26-L56)
- Tệp CSV phân phối hỗ trợ phim: [artifacts/als/m09/item_support_distribution.csv](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m09/item_support_distribution.csv)
- Kiểm thử hành vi Cold-Start của KG: [tests/kg/test_edge_cases.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/kg/test_edge_cases.py) (test case `test_kg12_cold_start_movie_behavior`).

---

### CÂU 7: TRÁNH RÒ RỈ NHÃN KHI TIỀN XỬ LÝ THẺ NGƯỜI DÙNG (USER TAGS)
**Hội đồng hỏi:**  
*"Bảng tags.csv do người dùng tự gõ từ khóa. Nhóm làm thế nào để đảm bảo không lấy từ khóa người dùng gõ trong tương lai để đưa vào huấn luyện?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, đây là một điểm rò rỉ dữ liệu rất tinh vi (Look-ahead Leakage) mà nhiều đồ án thường bỏ qua.
- Nhóm đã xây dựng cơ chế lọc nghiêm ngặt 2 lớp cho bảng `core/tags`:
  1. **Lớp 1 (Lọc chặn mốc thời gian Validation):** Chỉ giữ lại các bản ghi tag có `timestamp` xảy ra **trước** thời điểm tương tác Validation của chính người dùng đó.
  2. **Lớp 2 (Phép trừ tập hợp Left-Anti Join):** Thực hiện phép `left_anti join` trên cặp khóa `(userId, movieId)` với cả tập Validation và Test. Bất kỳ bộ phim nào xuất hiện trong tập kiểm thử của người dùng thì toàn bộ thẻ mà người dùng đó từng gán cho bộ phim đó đều bị loại bỏ hoàn toàn khỏi tập huấn luyện.
- Tệp kết quả được lưu độc lập tại `features/tags_train/` gồm đúng **1,074,090 dòng**, bảo đảm 100% tính trong sạch về thời gian.

**Vị trí mã nguồn:**
- Logic Left-Anti Join trong tiền xử lý: [recommender/preprocess.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L250-L278)
- Định nghĩa trong manifest: [data/processed/manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json#L28)

---

### CÂU 8: ĐỒNG BỘ TƯƠNG TÁC NGƯỜI DÙNG THỜI GIAN THỰC (LIVE DUAL-SYNC)
**Hội đồng hỏi:**  
*"Khi chạy Web Demo, nếu người dùng chấm điểm một bộ phim mới thì dữ liệu được ghi vào đâu? Đồ thị tri thức có nhận được không hay phải khởi động lại máy chủ?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, hệ thống triển khai kiến trúc **Đồng bộ Kép Tức Thời (Live Dual-Sync Architecture)**:
  1. Khi người dùng đánh giá phim trên giao diện web, ứng dụng FastAPI ghi nhận tương tác vào cơ sở dữ liệu SQLite tại [data/app_state.db](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/app_state.db) (bảng `user_ratings`).
  2. Phương thức `sync_with_sqlite()` trong `EmbeddedKnowledgeGraph` được gọi định kỳ hoặc kích hoạt trực tiếp theo sự kiện: đọc các dòng mới từ SQLite và gọi hàm `merge_rating(user_id, movie_id, rating)` để chèn ngay một cạnh `[:RATED]` mới vào đồ thị trong RAM.
  3. Quá trình này diễn ra trong **dưới 2 mili-giây**, cho phép hệ thống lập tức tái tính toán 3 đường suy luận P1, P2, P3 và đổi mới danh sách gợi ý theo thời gian thực mà **hoàn toàn không cần khởi động lại máy chủ (Zero Server Downtime)**.

**Vị trí mã nguồn:**
- Hàm đồng bộ SQLite vào Graph: [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L199-L247)
- Dịch vụ người dùng ghi nhận tương tác: [recommender/services/user_interaction_service.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/services/user_interaction_service.py#L30-L75)

---

### CÂU 9: TÍNH TIỀN ĐỊNH VÀ CHỐNG TRÙNG LẶP DỮ LIỆU (IDEMPOTENCY)
**Hội đồng hỏi:**  
*"Nếu quá trình nạp dữ liệu vào Đồ thị bị gián đoạn và chạy lại lần thứ hai, đồ thị có bị tăng gấp đôi số cạnh hoặc số đỉnh không?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, toàn bộ các hàm nạp dữ liệu đồ thị đều được thiết kế tuân thủ nguyên lý **Bất biến / Tiền định (Idempotent Merge Protocol)**:
  - Trên cơ sở dữ liệu **Neo4j**: Sử dụng mệnh đề `MERGE (n:Movie {movieId: $id})` kết hợp hệ thống 4 ràng buộc duy nhất (`UNIQUE CONSTRAINTS`).
  - Trên **Embedded In-Memory Graph**: Sử dụng cấu trúc tập hợp (Python `set`) và bảng băm (`dict` key-value). Nếu `user_id` hay `movie_id` đã tồn tại, hàm chỉ ghi đè cập nhật chứ không cấp phát thêm đỉnh mới. Cạnh giữa hai đỉnh được lưu bằng `dict[src][dst]`, ngăn ngừa 100% việc tạo cạnh trùng lặp (Zero Duplicate Edges).
- Nhóm đã kiểm chứng thực nghiệm bằng kịch bản `verify_idempotency`: Nạp đồ thị liên tiếp 2 lần, chênh lệch số đỉnh $\Delta_{\text{nodes}} = 0$ và chênh lệch số cạnh $\Delta_{\text{edges}} = 0$.

**Vị trí mã nguồn:**
- Kiểm tra tính bất biến: [recommender/kg/checks.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/checks.py#L15-L42)
- Idempotent merge logic: [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L67-L132)

---

### CÂU 10: RÀNG BUỘC TÍNH NHẤT QUÁN VÀ KIỂM TRA TOÀN VẸN MÃ BĂM SHA256
**Hội đồng hỏi:**  
*"Làm sao Hội đồng có thể tin tưởng rằng dữ liệu sau khi tiền xử lý không bị sửa đổi thủ công hoặc thất thoát dữ liệu?"*

**Trả lời chuẩn đan thép:**  
- Dạ thưa Thầy, sau khi PySpark hoàn tất tiền xử lý, hệ thống tự động chạy kịch bản thẩm định khoa học `recommender/validate_data.py`:
  1. Kiểm tra 100% không có giá trị rỗng (`NULL`) trên các cột định danh chính (`userId`, `movieId`, `tagId`).
  2. Tính toán và đóng dấu mã băm mật mã học **SHA256** cho từng tệp phân mảnh Parquet trong `manifest.json`.
  3. Bất kỳ sự thay đổi dù chỉ 1 byte dữ liệu trên đĩa cứng cũng sẽ làm sai lệch mã băm SHA256 và kích hoạt cảnh báo lỗi toàn vẹn dữ liệu ngay khi khởi chạy.

**Vị trí mã nguồn và tài liệu:**
- Bảng mã băm SHA256 cho từng file Parquet: [data/processed/manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json#L53-L250)
- Kịch bản kiểm tra toàn vẹn tự động: [recommender/validate_data.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/validate_data.py#L110-L160)
- Tệp kết quả kiểm thử dữ liệu: [data/processed/test_results.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/test_results.json)

---

## 3. BẢN ĐỒ DÒ VẾT MÃ NGUỒN (SOURCE CODE TRACEABILITY MAP)

Bảng đối chiếu nhanh giúp bạn mở file ngay lập tức trong phòng vấn đáp:

| Chủ đề dữ liệu | Tệp mã nguồn trọng tâm | Đoạn code / Dòng quan trọng | Nhiệm vụ chính |
| :--- | :--- | :--- | :--- |
| **Tiền xử lý Spark & Chia tập** | `recommender/preprocess.py` | Dòng **195 – 245** | Phân chia Leave-1-Last bằng Window Function, chống rò rỉ dữ liệu. |
| **Lọc thời gian thẻ người dùng** | `recommender/preprocess.py` | Dòng **250 – 278** | Left-Anti Join loại bỏ thẻ người dùng trong tập test. |
| **Đọc dữ liệu theo lô (Batch Stream)**| `recommender/kg/data_access.py`| Dòng **85 – 125** | Dùng PyArrow đọc Parquet theo từng lô 10k dòng chống tràn RAM. |
| **Chuyển đổi Bảng thành Đồ thị** | `recommender/kg/embedded_graph.py`| Dòng **252 – 318** | Đọc các bảng Parquet và khởi tạo đỉnh, cạnh trong RAM. |
| **Đồng bộ Live Web SQLite** | `recommender/kg/embedded_graph.py`| Dòng **199 – 247** | Hàm `sync_with_sqlite` cập nhật tức thì đánh giá mới của user vào KG. |
| **Ràng buộc duy nhất Cypher** | `recommender/kg/schema.cypher` | Dòng **1 – 27** | Khởi tạo Unique Constraints trên Neo4j. |
| **Kiểm tra toàn vẹn & Tiền định** | `recommender/kg/checks.py` | Dòng **15 – 75** | Kiểm tra tính bất biến (Idempotency) và cô lập split. |
| **Lý lịch tệp & Mã băm SHA256** | `data/processed/manifest.json`| Toàn bộ file (dòng **1 – 300**) | Thống kê số dòng, dung lượng MB và mã băm SHA256. |

---
*Tài liệu được biên soạn phục vụ bảo vệ xuất sắc đồ án môn Giới thiệu về Dữ liệu lớn — TS. Bùi Thanh Hùng.*
