# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.2.2

> **Chuyên đề:** 3.2.2. Tạo liên kết từ lịch sử đánh giá, thể loại và Tag Genome  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Trạng thái kiểm định:** ĐÃ XÁC MINH TRỰC TIẾP TRÊN MÃ NGUỒN (CODE & ARTIFACTS VERIFIED)

---

## PHẦN A — BẢNG KIỂM TOÁN KỸ THUẬT

| Thành phần | Dữ liệu nguồn | Quy trình xử lý thực tế | Đầu ra | Bằng chứng file:line |
|---|---|---|---|---|
| **Cạnh RATED** (`User` → `Movie`) | `data/raw/ml-25m/ratings.csv` → chia tập tại `data/processed/splits/train` (Parquet) | 1. Spark áp dụng Window theo từng `userId`, sắp xếp `timestamp DESC`, `movieId DESC` để tách *Leave-1-Last*.<br>2. Cạnh `RATED` nạp **DUY NHẤT** từ `splits/train` (`rn_desc > 2`).<br>3. Nạp **toàn bộ mọi mức rating** (kể cả rating thấp 0.5–3.0).<br>4. Thuộc tính `rating` và `timestamp` lưu trực tiếp trên cạnh.<br>5. Bổ sung tương tác mới thời gian thực từ bảng `user_ratings` của SQLite `app_state.db`. | Khởi tạo cạnh hai chiều trong RAM:<br>• `user_rated_movie[userId][movieId] = {"rating": r, "timestamp": ts}`<br>• `movie_rated_by_users[movieId][userId] = {"rating": r, "timestamp": ts}`<br>• Tăng `user_liked_counts` nếu `r >= 3.5`. | [preprocess.py:239-270](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L239-L270)<br>[data_access.py:120-147](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/data_access.py#L120-L147)<br>[embedded_graph.py:120-132](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L120-L132)<br>[embedded_graph.py:199-245](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L199-L245) |
| **Cạnh IN_GENRE** (`Movie` → `Genre`) | `data/raw/ml-25m/movies.csv` (cột `genres`) | 1. Chuẩn hóa giá trị rỗng/null và `(no genres listed)` thành mảng rỗng `[]`.<br>2. Phân tách đa thể loại bằng ký tự sổ dọc `\|` tạo cột `genre_list`.<br>3. Dùng `F.explode()` bung mảng thành các cặp `(movieId, genre)` và lọc bỏ chuỗi rỗng tại `features/movie_genres`.<br>4. Tạo đỉnh `Genre` duy nhất (Idempotent Merge) và liên kết hai chiều. | • Cạnh thuận: `movie_in_genre[movieId] = {genre_name, ...}`<br>• Chỉ mục đảo: `genre_to_movies[genre_name] = {movieId, ...}`<br>*(5,062 phim không có thể loại thì có bậc cạnh Genre = 0)*. | [preprocess.py:170-176](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L170-L176)<br>[preprocess.py:284-289](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L284-L289)<br>[embedded_graph.py:100-109](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L100-L109)<br>[data_access.py:39-51](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/data_access.py#L39-L51) |
| **Cạnh HAS_GENOME_TAG** (`Movie` → `GenomeTag`) | `data/raw/ml-25m/genome-tags.csv` & `genome-scores.csv` | 1. `genome-tags.csv` nạp 1,128 thẻ từ vựng cố định.<br>2. `genome-scores.csv` (15.58M bản ghi) được tiền xử lý thành Parquet (`core/genome_scores`).<br>3. Quét luồng qua PyArrow Dataset Scanner kết hợp thuật toán **Min-Heap kích thước cố định Top-M = 20** (`heapq`) cho từng phim.<br>4. Phím sắp xếp: `relevance DESC, tagId ASC` (không lọc cứng threshold).<br>5. Gán trọng số `relevance` (float32) trực tiếp lên cạnh liên kết. | • Cạnh thuận: `movie_has_genome_tag[movieId][tagId] = relevance`<br>• Chỉ mục đảo: `genome_tag_to_movies[tagId][movieId] = relevance`<br>*(48,607 phim không có Genome Scores thì có bậc cạnh Tag = 0)*. | [preprocess.py:139-150](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L139-L150)<br>[preprocess.py:204-209](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L204-L209)<br>[data_access.py:67-118](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/data_access.py#L67-L118)<br>[embedded_graph.py:110-119](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L110-L119) |

---

## PHẦN B — LUỒNG TẠO LIÊN KẾT THỰC TẾ

```
[DỮ LIỆU NGUỒN CSV]
  ├── ratings.csv (25.00M)
  ├── movies.csv (62,423)
  ├── genome-tags.csv (1,128)
  └── genome-scores.csv (15.58M)
           │
           ▼ (PySpark Strict Schema ETL - preprocess.py)
[TIỀN XỬ LÝ & PHÂN CHIA CHỐNG RÒ RỈ]
  ├── ratings -> Window(userId, timestamp DESC, movieId DESC) -> splits/train (24,675,013)
  ├── movies -> split("\\|") & explode -> features/movie_genres (107,245 dòng)
  ├── genome-tags -> core/genome_tags (1,128 dòng)
  └── genome-scores -> core/genome_scores (15,584,448 dòng Parquet)
           │
           ▼ (DataAccess Streaming & In-Memory Builder - embedded_graph.py)
[KIỂM TRA ĐIỀU KIỆN & CẮT TỈA THUẬT TOÁN]
  ├── RATED: Chỉ đọc splits/train; không lọc điểm rating; ghi nhận rating >= 3.5 vào user_liked_counts.
  ├── IN_GENRE: Bỏ qua phim có "(no genres listed)"; hợp nhất đỉnh thể loại duy nhất.
  └── HAS_GENOME_TAG: Min-Heap O(M) stream giữ đúng Top-20 relevance cao nhất (ưu tiên tagId nhỏ hơn khi hòa điểm).
           │
           ▼
[LƯU TRỮ VÀO ĐỒ THỊ TRI THỨC TRONG BỘ NHỚ]
  ├── self.user_rated_movie & self.movie_rated_by_users (Bidirectional Edge + Attributes)
  ├── self.movie_in_genre & self.genre_to_movies (Bidirectional Adjacency Sets)
  └── self.movie_has_genome_tag & self.genome_tag_to_movies (Weighted Adjacency Dicts)
```

### Ví dụ minh họa thực tế từ từng bản ghi dữ liệu:

1. **Quan hệ `IN_GENRE`:**
   - Dòng dữ liệu từ `movies.csv`: `100,City Hall (1996),Drama|Thriller`
   - Tiền xử lý: Chuỗi `Drama|Thriller` được tách thành mảng `["Drama", "Thriller"]`, sau đó `explode` thành 2 bản ghi: `(100, "Drama")` và `(100, "Thriller")`.
   - Nạp vào đồ thị:
     * Kiểm tra node `Movie(100)`, `Genre("Drama")`, `Genre("Thriller")` (nếu chưa có thì khởi tạo).
     * Tạo liên kết: `movie_in_genre[100] = {"Drama", "Thriller"}`.
     * Cập nhật chỉ mục đảo: thêm `100` vào `genre_to_movies["Drama"]` và `genre_to_movies["Thriller"]`.

2. **Quan hệ `HAS_GENOME_TAG`:**
   - Dòng dữ liệu từ `genome-scores.csv` cho phim ID `1`: chứa 1,128 dòng với `relevance` dao động từ `0.01` đến `0.98`.
   - Xử lý qua Min-Heap (`top_m = 20`): Quét qua 1,128 điểm số, min-heap giữ lại đúng 20 thẻ có điểm số cao nhất (ví dụ: `tagId=1036` (toys), `rel=0.982`; `tagId=589` (animation), `rel=0.954`...).
   - Nạp vào đồ thị:
     * Cạnh thuận: `movie_has_genome_tag[1][1036] = 0.982`.
     * Chỉ mục đảo: `genome_tag_to_movies[1036][1] = 0.982`.

3. **Quan hệ `RATED`:**
   - Dòng dữ liệu từ `splits/train`: `userId=1, movieId=110, rating=5.0, timestamp=1425941529`.
   - Nạp vào đồ thị:
     * `user_rated_movie[1][110] = {"rating": 5.0, "timestamp": 1425941529}`.
     * `movie_rated_by_users[110][1] = {"rating": 5.0, "timestamp": 1425941529}`.
     * Do `5.0 >= 3.5`, `user_liked_counts[1]` được cộng thêm 1.

---

## PHẦN C — ĐẶC TẢ KỸ THUẬT QUAN TRỌNG

1. **Ngưỡng rating tích cực (`min_liked_rating = 3.5`):**
   - **Giai đoạn áp dụng:** Không áp dụng khi tạo cạnh `RATED`. Mọi đánh giá từ 0.5 đến 5.0 trong tập Train đều được lưu thành cạnh trong đồ thị.
   - Ngưỡng 3.5 được áp dụng ở pha **Truy vấn / Tính điểm Metapath** (`get_user_liked_movies` và `scorer.py`): chỉ các phim có `rating >= 3.5` mới được chọn làm các đỉnh mỏ neo (Anchor Liked Movies) để khai phá đường dẫn P1, P2, P3 và tính trọng số sở thích tích cực:
     ```text
     w(r) = max(0, (r - 3.0) / 2.0)
     ```
   - *Bằng chứng:* [kg_config.yaml:12-13](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L12-L13); [embedded_graph.py:137-145](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L137-L145); [scorer.py:85-87](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L85-L87).

2. **Chính sách chọn lọc Tag Genome (Top-M Selection Policy):**
   - **Giá trị thực tế:** `top_m = 20`.
   - **Không áp dụng ngưỡng relevance cố định:** Mã nguồn **không lọc** theo kiểu `relevance >= 0.5` trước khi lấy Top-M.
   - **Thứ tự ưu tiên:** `relevance DESC, tagId ASC`. Bộ chọn sử dụng Min-Heap trên cặp khóa `(relevance, -tagId)` để xử lý trường hợp bằng điểm số (tie-breaker: ưu tiên mã thẻ nhỏ hơn).
   - *Bằng chứng:* [data_access.py:67-118](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/data_access.py#L67-L118); [kg_config.yaml:14](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L14).

3. **Phương pháp phân chia Train/Validation/Test:**
   - Chiến lược: **User-wise Leave-1-Last** theo thời gian.
   - Window partition: `Window.partitionBy("userId").orderBy(F.col("timestamp").desc(), F.col("movieId").desc())`.
   - Quy tắc gán nhãn:
     * `rn_desc == 1`: Tập **Test** (đúng 1 tương tác mới nhất của mỗi người dùng = 162,541 bản ghi).
     * `rn_desc == 2`: Tập **Validation** (đúng 1 tương tác kế chót của mỗi người dùng = 162,541 bản ghi).
     * `rn_desc > 2`: Tập **Train** (toàn bộ các tương tác trước đó = 24,675,013 bản ghi).
   - *Bằng chứng:* [preprocess.py:241-254](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L241-L254); [manifest.json:19-27](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/manifest.json#L19-L27).

4. **Quy tắc lọc dữ liệu và xử lý giá trị khuyết:**
   - **Phim thiếu thể loại:** 5,062 phim mang giá trị `(no genres listed)` hoặc null được gán mảng rỗng `[]`, không tạo cạnh `IN_GENRE` nào, đỉnh `Movie` vẫn được lưu với bậc quan hệ thể loại bằng 0.
   - **Phim không có Genome Scores:** 48,607 phim không xuất hiện trong `genome-scores.csv` (chỉ 13,816 phim có điểm genome) được giữ nguyên node nhưng không có cạnh `HAS_GENOME_TAG` (bậc bằng 0). Khi chấm điểm, đóng góp đường dẫn P2 của các phim này bằng 0.
   - **Phân biệt User Tags (`tags.csv`) và Tag Genome (`genome-tags.csv`):**
     * `tags.csv` (1.09M lượt gắn thẻ cá nhân) được lọc chống rò rỉ thời gian và Left-Anti Join với Validation/Test để tạo tập `features/tags_train`. **Tập này không được dùng để tạo cạnh trong đồ thị tri thức**.
     * Đồ thị tri thức chỉ tạo cạnh `HAS_GENOME_TAG` từ 1,128 thẻ chuẩn hóa khách quan của Tag Genome (`genome-scores.csv`).
   - *Bằng chứng:* [preprocess.py:170-176](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L170-L176); [preprocess.py:303-311](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L303-L311); [test_results.json:41-43](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/test_results.json#L41-L43).

5. **Danh mục artifacts đầu ra phục vụ xây dựng đồ thị:**
   - Dữ liệu cột Parquet: `data/processed/core/movies`, `data/processed/core/genome_tags`, `data/processed/core/genome_scores`, `data/processed/features/movie_genres`, `data/processed/splits/train`.
   - Metadata kiểm chứng: `data/processed/manifest.json` (SHA-256 từng file), `data/processed/test_results.json` (8 bài kiểm tra chất lượng dữ liệu).
   - Bộ nhớ đệm đồ thị: `data/embedded_kg_cache.pkl.gz` (lưu trạng thái nạp đồ thị nhúng).

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.2.2. Tạo liên kết từ lịch sử đánh giá, thể loại và Tag Genome

Quá trình kiến tạo liên kết trên đồ thị tri thức MoodGraph được thực hiện tuần tự thông qua ba loại quan hệ ngữ nghĩa, bảo đảm tính nhất quán cấu trúc và tuân thủ nghiêm ngặt ranh giới dữ liệu huấn luyện. Đối với quan hệ đánh giá (`RATED`), đồ thị liên kết trực tiếp đỉnh người dùng (`User`) tới đỉnh phim (`Movie`) kèm hai thuộc tính cạnh là điểm số đánh giá (`rating`) và mốc thời gian phát sinh (`timestamp`). Nhằm triệt tiêu nguy cơ rò rỉ dữ liệu tương lai (data leakage), cạnh `RATED` chỉ được trích xuất duy nhất từ tập huấn luyện (`splits/train`), vốn được phân chia theo giao thức thời gian *User-wise Leave-1-Last* thông qua Spark Window Function. Toàn bộ các tương tác thuộc tập kiểm định (`rn_desc = 2`) và kiểm thử (`rn_desc = 1`) bị loại trừ tuyệt đối khỏi quá trình xây dựng đồ thị; đồng thời, đồ thị lưu trữ toàn bộ các mức đánh giá trong tập huấn luyện, trong khi ngưỡng đánh giá tích cực (rating >= 3.5) chỉ được áp dụng ở giai đoạn trích xuất mỏ neo suy diễn tại bước tính điểm đường dẫn.

Đối với quan hệ phân loại (`IN_GENRE`), hệ thống thực hiện chuẩn hóa trường dữ liệu thể loại từ danh mục phim, phân tách chuỗi đa thể loại thông qua ký tự ngăn cách và loại bỏ các định danh khuyết thiếu hoặc không xác định; từ đó ánh xạ có hướng từ đỉnh phim tới đỉnh thể loại tương ứng (`Genre`). Đồ thị duy trì tính duy nhất cho mỗi thực thể thể loại, cho phép các tác phẩm cùng thể loại cùng quy chiếu về một nút chung nhằm hình thành các đường nối siêu liên kết. 

Cuối cùng, quan hệ thẻ đặc trưng (`HAS_GENOME_TAG`) được thiết lập từ tập dữ liệu Tag Genome độc lập với hành vi gắn thẻ tự do của người dùng. Để kiểm soát độ thưa và hạn chế bùng nổ bậc đỉnh, hệ thống áp dụng thuật toán hàng đợi ưu tiên (Min-Heap) kích thước cố định để chọn lọc đúng M = 20 thẻ có điểm tương quan (`relevance`) cao nhất cho từng tác phẩm theo thứ tự giảm dần của độ liên quan và giải quyết hòa điểm dựa trên định danh thẻ. Điểm số tương quan này được gán trực tiếp làm trọng số liên tục của cạnh, cung cấp cơ sở định lượng vi mô cho quá trình lan truyền bằng chứng sở thích trên không gian đồ thị.

---

## PHẦN E — KIỂM TRA CHÉO TRƯỚC KHI KẾT LUẬN

1. **Có nhầm User Tags với Genome Tags không?**
   - **Xác nhận:** ĐÃ PHÂN BIỆT RÕ RÀNG. User Tags (`tags.csv`) là thẻ tự do của người dùng cá nhân (chỉ dùng trong feature engineering `tags_train` với anti-join). Genome Tags (`genome-tags.csv` và `genome-scores.csv`) là 1,128 thẻ từ vựng khách quan, chỉ có Genome Tags mới được dùng để tạo quan hệ `HAS_GENOME_TAG`.
2. **Có nhầm mọi cạnh RATED với quan hệ đánh giá tích cực không?**
   - **Xác nhận:** ĐÃ PHÂN BIỆT RÕ RÀNG. Cạnh `RATED` lưu **mọi đánh giá** trong tập Train (0.5 đến 5.0 sao). Ngưỡng rating tích cực (>= 3.5) chỉ dùng ở pha truy vấn đường dẫn mỏ neo (`get_user_liked_movies`) và chấm điểm `preference_weight`.
3. **Có đưa dữ liệu Validation/Test vào graph huấn luyện không?**
   - **Xác nhận:** KHÔNG. Cạnh `RATED` chỉ nạp từ `splits/train`. `test_results.json` xác nhận `test_in_train_count = 0`, `val_in_train_count = 0`.
4. **Có nhầm Top-M Genome Tags với Top-K Recommendation không?**
   - **Xác nhận:** KHÔNG. Top-M (M = 20) là chính sách cắt tỉa cạnh `HAS_GENOME_TAG` trên mỗi phim trong đồ thị. Top-K (K thuộc {5, 10, 20}) là số lượng phim gợi ý trả về cho người dùng.
5. **Có khẳng định ngưỡng lọc không đúng code không?**
   - **Xác nhận:** ĐÃ ĐỐI CHIẾU CHÍNH XÁC. Mã nguồn không có bộ lọc tĩnh `relevance >= 0.5`. Hệ thống sử dụng Min-Heap để lấy Top-20 thẻ có relevance cao nhất cho mỗi phim.
6. **Có mô tả sai vai trò của Spark hoặc PyArrow không?**
   - **Xác nhận:** ĐÃ ĐỐI CHIẾU CHÍNH XÁC. PySpark đảm nhiệm tiền xử lý phân tán từ CSV thô ra Parquet và chia split Leave-1-Last. PyArrow đảm nhiệm đọc streaming Parquet vào RAM để dựng đồ thị in-memory.
7. **Có nhầm cấu trúc lưu trữ hai chiều với hai loại quan hệ ngữ nghĩa riêng biệt không?**
   - **Xác nhận:** KHÔNG. Đồ thị chỉ có 3 quan hệ ngữ nghĩa (`RATED`, `IN_GENRE`, `HAS_GENOME_TAG`). Các biến như `genre_to_movies`, `genome_tag_to_movies`, `movie_rated_by_users` là các chỉ mục đảo (Inverted Indices) phục vụ duyệt đồ thị hai chiều trong RAM với độ phức tạp O(1).
8. **Có lặp lại nội dung mục 3.2.1 hoặc đi trước mục 3.2.3 không?**
   - **Xác nhận:** Bản thảo mục 3.2.2 hoàn toàn tập trung vào cơ chế trích xuất và tạo liên kết từ dữ liệu nguồn, không lặp lại định nghĩa hình học đỉnh/cạnh của 3.2.1 và không đi sâu vào cấu trúc nén/tối ưu RAM của 3.2.3.
9. **Có sử dụng số liệu thuộc phiên bản dataset khác không?**
   - **Xác nhận:** ĐÃ KIỂM ĐỊNH TUYỆT ĐỐI. Dữ liệu thực tế 100% là **MovieLens 25M** (25,000,095 ratings, 162,541 users, 62,423 movies, 15,584,448 genome scores). Sự xuất hiện của chuỗi "20M" tại một dòng trong tài liệu tài liệu hóa (`MOODGRAPH_COMPLETE_SYSTEM_KNOWLEDGE_TRANSFER.md:1311`) đã được xác minh là lỗi đánh máy làm tròn số của người viết tài liệu cũ, không ảnh hưởng đến tính toàn vẹn của mã nguồn và dữ liệu thực tế.
10. **Có khẳng định một kỹ thuật loại bỏ hoàn toàn Data Leakage khi chưa đủ bằng chứng không?**
    - **Xác nhận:** ĐÃ PHÂN ĐỊNH CHẶT CHẼ. Hệ thống chứng minh triệt tiêu hoàn toàn rò rỉ chuỗi tương tác người dùng qua kiểm định thời gian Leave-1-Last và phép nối phủ định Left-Anti Join; đồng thời chỉ rõ Genome Scores là metadata tĩnh cấp danh mục (content-based features) không phụ thuộc tương tác cá nhân.
