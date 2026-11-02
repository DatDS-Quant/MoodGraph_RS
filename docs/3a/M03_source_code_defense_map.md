# MoodGraph Task 3A – Module M03: Source Code Defense Map
## Bản Đồ Định Vị Mã Nguồn & Cẩm Nang Bảo Vệ Đồ Án Trước Hội Đồng

---

## 1. Bảng Định Vị Mã Nguồn Chi Tiết (Source Code Locator Map)

Bảng dưới đây xác định chính xác 100% vị trí từng chức năng cốt lõi của Module M03 (Popularity Baseline) và sự kế thừa từ Module M01/M02. Tất cả số dòng đã được đối chiếu thực tế từ tệp mã nguồn cuối cùng:

| STT | Chức năng Kỹ thuật | Relative File Path | Class / Function | Line Start–End | Vai trò Kiến trúc | Lệnh Mở Trực Tiếp trong VS Code |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Đọc dữ liệu Train Parquet | `recommender/als/data_loader.py` | `load_train_data` | L100–L122 | Nạp 24,675,013 ratings Train, kiểm định schema 4 trường | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\data_loader.py:100"` |
| 2 | Khởi tạo SparkSession tối ưu | `recommender/als/data_loader.py` | `get_spark_session` | L38–L56 | Cấu hình RAM 6GB, shuffle partitions 16, chống timeout worker | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\data_loader.py:38"` |
| 3 | Tính tổng lượt đánh giá & trung bình phim bằng Spark | `recommender/als/popularity.py` | `PopularityRecommender.fit_from_spark` | L287–L319 | Tính toán phân tán Spark: đếm lượt và điểm trung bình cho 58,932 phim | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:287"` |
| 4 | Tính điểm trung bình toàn cục Train (Global Mean C) | `recommender/als/popularity.py` | `PopularityRecommender.fit_from_spark` | L299–L303 | Tính C = 3.531522 từ 24.6M ratings làm prior cho Bayesian Average | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:299"` |
| 5 | Công thức Bayesian Weighted Average | `recommender/als/popularity.py` | `compute_weighted_score` | L74–L104 | Tính WeightedScore = (v*R + m*C)/(v + m), xử lý điều kiện biên | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:74"` |
| 6 | Xếp hạng theo Rating Count Baseline | `recommender/als/popularity.py` | `rank_movies_by_count` | L106–L135 | Sắp xếp: rating_count DESC, avg_rating DESC, movieId ASC | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:106"` |
| 7 | Xếp hạng theo Bayesian Weighted Average | `recommender/als/popularity.py` | `rank_movies_by_weighted_average` | L137–L173 | Sắp xếp: weighted_score DESC, rating_count DESC, movieId ASC | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:137"` |
| 8 | Giải quyết đồng điểm (Tie-breaking ổn định) | `recommender/als/popularity.py` | `rank_movies_by_count` & `weighted` | L118–L121 & L156–L159 | Phá hòa tất định bằng ID phim tăng dần (movieId ASC) | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:118"` |
| 9 | Lọc phim đã xem & bù ứng viên đủ Top-K | `recommender/als/popularity.py` | `generate_user_top_k` | L175–L211 | Quét danh sách phổ biến, bỏ qua seen items, lấy đủ K phim | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:175"` |
| 10 | Sinh gợi ý theo lô (Batch Top-K Generation) | `recommender/als/popularity.py` | `generate_batch_top_k` | L213–L241 | Sinh Top-K cho 162,541 users trong 8–9 giây không tốn RAM | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:213"` |
| 11 | Lớp điều phối PopularityRecommender | `recommender/als/popularity.py` | `PopularityRecommender` | L243–L403 | Quản lý cả hai biến thể Count & Weighted, export ranking tables | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:243"` |
| 12 | Đánh giá Top-N đa mốc K (M02 Evaluator) | `recommender/als/evaluator.py` | `TopNEvaluator.evaluate` | L322–L429 | Tính HitRate@K, NDCG@K, MRR@K, Precision@K, Recall@K, Coverage | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\evaluator.py:322"` |
| 13 | Phân định Positive-Target Cohort | `recommender/als/evaluator.py` | `TopNEvaluator.evaluate` | L347–L355 | Lọc ra 109,779 users có rating >= 3.5 làm mẫu số chính | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\evaluator.py:347"` |
| 14 | Bảo toàn mẫu số người dùng trượt (Miss) | `recommender/als/evaluator.py` | `TopNEvaluator.evaluate` | L367–L377 | User không nhận được gợi ý trúng nhận điểm 0, giữ trong mẫu số | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\evaluator.py:367"` |
| 15 | Tính Catalog Coverage@K | `recommender/als/evaluator.py` | `TopNEvaluator.evaluate` | L398–L410 | Đếm số phim độc lập trong Top-K chia cho 62,423 phim catalog | `code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\evaluator.py:398"` |
| 16 | Điều phối Thực nghiệm Toàn diện 25M | `scripts/run_m03_popularity.py` | `main` | L37–L167 | Nạp Parquet, huấn luyện, sinh Top-K, đánh giá và lưu JSON | `code -g "D:\PROJECT BIG DATA\MoodGraph\scripts\run_m03_popularity.py:37"` |

---

## 2. Bảng Kiểm Chứng Độc Lập (How This Code Was Verified)

Mọi chức năng cốt lõi đều được kiểm chứng độc lập ở nhiều tầng (tính tay, code độc lập tham chiếu, edge-case và thực nghiệm lớn):

| Chức năng Kỹ thuật | File Triển khai | File Kiểm thử Tương ứng | Tên Bài Kiểm thử Cụ thể | Phương pháp Xác minh Độc lập | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Tính số lượt và trung bình | `popularity.py:106` | `test_popularity.py` | `test_01_count_aggregation_correctness` | Đối chiếu với bảng thống kê độc lập | PASS |
| Công thức Bayesian Average | `popularity.py:74` | `test_popularity.py` | `test_03_hand_calculated_weighted_average` | Tính tay: 485/110 = 4.40909; 40/11 = 3.63636 | PASS |
| Phá hòa tất định (Tie-breaking) | `popularity.py:118` | `test_popularity.py` | `test_06_stable_tie_breaking` | Kiểm tra thứ tự movieId tăng dần khi bằng điểm | PASS |
| Phạt phim ít đánh giá (Fluke movie) | `popularity.py:74` | `test_popularity.py` | `test_07_single_rating_movie_behavior` | Phim 1 đánh giá 5.0 bị xếp sau phim 1,000 đánh giá 4.3 | PASS |
| Lọc phim đã xem (Seen items) | `popularity.py:175` | `test_popularity.py` | `test_09_seen_items_filtering` | Xác nhận tập gợi ý giao với tập seen bằng rỗng | PASS |
| Bù ứng viên cho user xem nhiều | `popularity.py:175` | `test_popularity.py` | `test_10_top_k_replenishment_after_seen_filtering` | User xem top 5 vẫn nhận đủ phim từ hạng 6 đến 10 | PASS |
| User cực hạn (Heavy User 1,000 phim) | `popularity.py:175` | `test_popularity.py` | `test_11_heavy_user_seen_many_movies` | Quét xuống 1,000 phim tiếp theo, nhận đủ Top-10 | PASS |
| Không trùng ID và không ngoài catalog | `popularity.py:175` | `test_popularity.py` | `test_12_no_duplicate` & `test_13_no_out_of_catalog` | Kiểm tra tính duy nhất và tập con catalog | PASS |
| So sánh với Code Độc lập Tham chiếu | `popularity.py:243` | `test_popularity.py` | `test_21_independent_reference_implementation` | So sánh bit-for-bit với code Python độc lập | PASS |
| Tích hợp Evaluator M02 | `popularity.py:355` | `test_popularity.py` | `test_16_integration_with_m02_evaluator` | Tính tay: User 1 rank 1 (NDCG=1), User 2 rank 3 (NDCG=0.5) -> Mean=0.75 | PASS |
| Đánh giá Thực tế 162,541 Users | `scripts/run_m03_popularity.py` | `artifacts/m03_popularity_results.json` | Toàn bộ 109,779 positive targets | Đo đạc trực tiếp trên Spark 24.6M ratings | VERIFIED |

---

## 3. Giảng Viên Hỏi – Em Mở Code Ở Đâu? (Oral Defense Q&A Guide)

Dưới đây là 8 tình huống hỏi thi điển hình nhất của giảng viên và cách em trả lời tự tin, mở đúng dòng code để chứng minh:

---

### Câu hỏi 1: "Em tính mức độ phổ biến của phim trong Train như thế nào mà không bị tràn RAM?"
- **Mở code ngay:** Tệp [`recommender/als/popularity.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py), hàm `fit_from_spark`, **dòng 287–319**.
- **Chỉ tay vào màn hình:** Dòng 306–309:
  ```python
  movie_agg_df = train_df.groupBy("movieId").agg(
      F.count("userId").alias("rating_count"),
      F.avg("rating").alias("avg_rating"),
  )
  ```
- **Giải thích 3–5 câu:**
  "Thưa Thầy/Cô, toàn bộ 24.6 triệu dòng dữ liệu Train được gom nhóm phân tán trên Apache Spark thông qua phép biến đổi `groupBy('movieId').agg(...)`. Kết quả trả về là một bảng tổng hợp chỉ gồm 58,932 dòng (mỗi phim một dòng gồm số lượt và điểm trung bình), dung lượng bộ nhớ chưa tới 3 MB. Nhờ đó, driver chỉ nhận về bảng thống kê nhỏ gọn này mà không bao giờ phải nạp 24.6 triệu dòng vào RAM."
- **Bằng chứng:** Test [`tests/als/test_popularity.py:test_01_count_aggregation_correctness`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_popularity.py) kiểm chứng tính chính xác của phép gom nhóm.

---

### Câu hỏi 2: "Tại sao không xếp hạng thuần túy theo điểm trung bình mà phải dùng Bayesian Weighted Average?"
- **Mở code ngay:** Tệp [`recommender/als/popularity.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py), hàm `compute_weighted_score`, **dòng 74–104**.
- **Chỉ tay vào màn hình:** Dòng 102:
  ```python
  score = (float(v) * float(r) + float(m) * float(c)) / float(v + m)
  ```
- **Giải thích 3–5 câu:**
  "Nếu xếp hạng thuần túy theo điểm trung bình, những bộ phim vô danh chỉ có đúng 1 lượt đánh giá 5 sao sẽ chiếm trọn các vị trí đầu bảng, gây ra lỗi thiên vị mẫu nhỏ (fluke bias). Công thức Bayesian Average khắc phục điều này bằng cách bổ sung m lượt đánh giá ảo với điểm số bằng trung bình toàn cục C (C = 3.5315). Những phim ít lượt đánh giá sẽ bị kéo điểm về mức trung bình chung, còn những phim có hàng chục nghìn lượt đánh giá thì điểm số của chính nó mới được giữ nguyên."
- **Ví dụ tính tay:**
  "Ví dụ với m = 10, C = 3.5: Phim A có 100 lượt đánh giá 4.5 sao đạt điểm 4.409. Trong khi phim B có 1 lượt đánh giá 5.0 sao bị kéo tụt xuống 3.636 và xếp sau phim A."
- **Bằng chứng:** Test [`tests/als/test_popularity.py:test_03_hand_calculated_weighted_average`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_popularity.py).

---

### Câu hỏi 3: "Người dùng đã xem nhiều phim phổ biến rồi, em lọc phim đã xem thế nào để vẫn đủ 10 phim?"
- **Mở code ngay:** Tệp [`recommender/als/popularity.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py), hàm `generate_user_top_k`, **dòng 175–211**.
- **Chỉ tay vào màn hình:** Dòng 195–209:
  ```python
  for mid in ranked_movie_ids:
      if mid not in seen_movies:
          recs.append(...)
          if len(recs) == k:
              break
  ```
- **Giải thích 3–5 câu:**
  "Hệ thống không lấy cứng Top-10 toàn cục rồi mới lọc (vì lọc xong có thể chỉ còn 2–3 phim). Thay vào đó, thuật toán duyệt tuần tự trên danh sách 58,932 phim đã xếp hạng toàn cục. Nếu phim nằm trong tập `seen_movies` của người dùng thì bỏ qua và tiếp tục xét các phim tiếp theo cho đến khi thu thập đủ đúng K phim chưa xem. Nhờ danh mục Train có tới 58,932 phim, kể cả người dùng xem nhiều nhất hệ thống (32,200 phim) vẫn còn hơn 26,000 phim ứng viên để chọn đủ K phim."
- **Bằng chứng:** Test [`test_10_top_k_replenishment_after_seen_filtering`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_popularity.py) và [`test_11_heavy_user_seen_many_movies`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_popularity.py).

---

### Câu hỏi 4: "Giữa Rating Count và Bayesian Weighted Average, phương pháp nào tốt hơn trên thực tế và tại sao?"
- **Mở báo cáo kết quả:** Tệp [`artifacts/m03_popularity_results.json`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/m03_popularity_results.json), dòng 13–83.
- **Dẫn chứng số liệu thực nghiệm:**
  - `POPULARITY_COUNT`: **NDCG@10 = 0.02789**, **HitRate@10 = 5.519%** (trúng 6,059 users).
  - `POPULARITY_WEIGHTED`: **NDCG@10 = 0.00771**, **HitRate@10 = 1.969%** (trúng 2,161 users).
- **Giải thích 3–5 câu:**
  "Thưa Thầy/Cô, thực nghiệm thực tế trên toàn bộ 109,779 người dùng Validation chứng minh Rating Count vượt trội gấp gần 3 lần so với Weighted Average. Nguyên nhân là tập MovieLens 25M có độ thiên lệch phổ biến (popularity bias) rất cao. Các bộ phim bom tấn như Shawshank Redemption, Forrest Gump, Pulp Fiction có từ 70,000 đến 80,000 người xem, xác suất một người dùng bất kỳ thích và đánh giá những phim này là rất lớn. Ngược lại, Bayesian Average đưa lên đầu các phim ngách có điểm trung bình cao nhưng chỉ có khoảng 1,000 người xem, dẫn tới tỷ lệ trúng chung trên toàn bộ dân số rất thấp."

---

### Câu hỏi 5: "Khi hai phim có cùng số lượt đánh giá hoặc cùng điểm số, em xử lý hòa như thế nào?"
- **Mở code ngay:** Tệp [`recommender/als/popularity.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py), dòng **118–121** và dòng **156–159**.
- **Chỉ tay vào màn hình:**
  ```python
  # Sort key: (-rating_count, -avg_rating, movieId)
  sorted_stats = sorted(movie_stats, key=lambda x: (-x[1], -x[2], x[0]))
  ```
- **Giải thích 3–5 câu:**
  "Thuật toán sử dụng khóa sắp xếp đa cấp xác định: tiêu chí 1 là số lượt giảm dần (`-count`), tiêu chí 2 là điểm trung bình giảm dần (`-avg_rating`), và tiêu chí tie-breaking cuối cùng là ID phim tăng dần (`movieId`). Do ID phim là duy nhất trong danh mục, thứ tự xếp hạng được bảo đảm tính tất định 100%, kết quả hoàn toàn có thể tái lập ở mọi lần chạy mà không bị xáo trộn ngẫu nhiên."
- **Bằng chứng:** Test [`tests/als/test_popularity.py:test_06_stable_tie_breaking`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_popularity.py).

---

### Câu hỏi 6: "Em đo NDCG@10 như thế nào? Người dùng không nhận được gợi ý trúng thì tính sao?"
- **Mở code ngay:** Tệp [`recommender/als/evaluator.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/evaluator.py), dòng **207–228** và **367–377**.
- **Chỉ tay vào màn hình:**
  ```python
  # Nếu trúng tại vị trí rank_found (từ 1 đến 10):
  ndcg = 1.0 / math.log2(float(rank_found) + 1.0)
  # Nếu trượt (không trúng):
  ndcg = 0.0
  ```
- **Giải thích 3–5 câu:**
  "Trong giao thức 1-held-out target, danh sách lý tưởng xếp phim mục tiêu ở vị trí 1 với IDCG = 1.0. Nếu phim trúng ở thứ hạng j (từ 1 đến 10), NDCG bằng `1.0 / log2(j + 1)`. Đối với những người dùng có mục tiêu tích cực nhưng mô hình gợi ý trượt, họ nhận điểm số NDCG = 0 và bắt buộc được giữ nguyên trong mẫu số 109,779 users. Hệ thống tuyệt đối không loại bỏ những người dùng này để tránh việc thổi phồng chỉ số sai lệch."

---

### Câu hỏi 7: "Catalog Coverage@10 của Popularity Baseline là bao nhiêu? Tại sao nó lại thấp?"
- **Mở báo cáo kết quả:** Tệp [`artifacts/m03_popularity_results.json`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/m03_popularity_results.json), dòng 45–47.
- **Số liệu:** Catalog Coverage@10 trên toàn bộ danh mục 62,423 phim là **0.50%** (chỉ có **310** bộ phim khác nhau được gợi ý trên toàn bộ 109,779 người dùng).
- **Giải thích 3–5 câu:**
  "Thưa Thầy/Cô, Catalog Coverage của mô hình Popularity rất thấp (0.50%) là hoàn toàn hợp lý về mặt lý thuyết. Vì Popularity là mô hình không cá nhân hóa, mọi người dùng đều nhận chung một danh sách phim phổ biến nhất (chỉ khác nhau đôi chút khi một số người đã xem phim đó trước đây nên hệ thống đẩy phim tiếp theo lên). Mô hình hầu như bỏ rơi 99.5% danh mục phim ở phần đuôi dài (long-tail). Đây chính là điểm yếu cố hữu của Popularity và là lý do cốt lõi chúng ta phải phát triển mô hình cá nhân hóa Spark ALS ở Module M04–M07 và Knowledge Graph ở Task 3B để mở rộng độ phủ danh mục."

---

### Câu hỏi 8: "Em chứng minh mô hình này hoàn toàn không nhìn thấy tập Test xem nào?"
- **Mở code ngay:** Tệp [`scripts/run_m03_popularity.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m03_popularity.py), dòng **47–50**.
- **Chỉ tay vào màn hình:**
  ```python
  train_df = load_train_data(spark)
  val_df = load_validation_data(spark)
  movies_df = load_movies_data(spark)
  # Tuyệt đối không import hoặc gọi load_test_data!
  ```
- **Giải thích 3–5 câu:**
  "Script thực nghiệm chỉ nạp đúng 3 nguồn dữ liệu: `splits/train` để học bảng xếp hạng, `splits/validation` để làm ground-truth đánh giá, và `core/movies` để kiểm tra danh mục. Tập `splits/test` hoàn toàn không được import hay nạp vào bộ nhớ. Bảng thống kê tần suất phim chỉ được tổng hợp từ Train. Điều này bảo đảm tính toàn vẹn của tập Test cho khâu báo cáo nghiệm thu cuối cùng ở M08."

---

## 4. Kịch Bản Demo Trực Tiếp 5 Phút (Live Defense Demonstration Script)

Thực hiện lần lượt 6 lệnh copy-paste dưới đây trong terminal PowerShell để trình diễn trực tiếp trước Hội đồng:

### Bước 1: Mở file mã nguồn Popularity Baseline
```powershell
code -g "D:\PROJECT BIG DATA\MoodGraph\recommender\als\popularity.py:106"
```
*Hành động:* Giới thiệu hai hàm xếp hạng `rank_movies_by_count` (dòng 106) và `rank_movies_by_weighted_average` (dòng 137).

### Bước 2: Chạy toàn bộ 22 bài unit test của M03
```powershell
python -m pytest tests/als/test_popularity.py -v
```
*Kết quả kỳ vọng:* 22 bài kiểm thử PASS trong ~0.5 giây.

### Bước 3: Chạy toàn bộ regression test suite của toàn hệ thống (M00–M03)
```powershell
python -m pytest tests/als/ -v
```
*Kết quả kỳ vọng:* 62/62 tests PASS trong ~35 giây.

### Bước 4: Demo Synthetic – Chạy thử nghiệm trên dữ liệu nhỏ (6 phim) kiểm tra lọc phim đã xem
```powershell
python -c "
import sys; sys.path.insert(0, '.')
from recommender.als.popularity import PopularityRecommender
stats = [(318, 80448, 4.41), (356, 80375, 4.05), (296, 78735, 4.19), (593, 73109, 4.15), (2571, 71787, 4.15), (260, 60000, 4.12)]
rec = PopularityRecommender().fit_from_stats(stats, global_mean=3.53)
user_seen = {318, 296} # User đã xem Shawshank và Pulp Fiction
top3 = rec.recommend(user_id=1, seen_movies=user_seen, k=3, variant='count')
print('=== TOP 3 GỢI Ý CHO USER 1 (ĐÃ LỌC PHIM ĐÃ XEM) ===')
for r in top3:
    print(f'Rank {r.rank}: MovieId {r.movie_id} (Score: {r.raw_score:,.0f})')
"
```
*Kết quả kỳ vọng:* Hệ thống tự động bỏ qua phim 318 và 296, gợi ý chính xác [356, 593, 2571].

### Bước 5: Demo Thực tế – Đọc kết quả thực nghiệm đo đạc trên toàn bộ 109,779 users Validation
```powershell
python -c "
import json
with open('artifacts/m03_popularity_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
c10 = data['variants']['POPULARITY_COUNT']['metrics']['10']
w10 = data['variants']['POPULARITY_WEIGHTED']['metrics']['10']
print('=== ĐỐI CHỨNG VALIDATION (109,779 USERS) ===')
print(f'Count Baseline    : NDCG@10 = {c10[\"ndcg\"]:.4f} | HitRate@10 = {c10[\"hit_rate\"]*100:.2f}% | Hits = {c10[\"hit_count\"]:,}')
print(f'Weighted Baseline : NDCG@10 = {w10[\"ndcg\"]:.4f} | HitRate@10 = {w10[\"hit_rate\"]*100:.2f}% | Hits = {w10[\"hit_count\"]:,}')
"
```
*Kết quả kỳ vọng:*
- Count Baseline: NDCG@10 = 0.0279 | HitRate@10 = 5.52% | Hits = 6,059
- Weighted Baseline: NDCG@10 = 0.0077 | HitRate@10 = 1.97% | Hits = 2,161

### Bước 6: Tra cứu kho tri thức HERMES Memory Engine
```powershell
python scripts/hermes_memory.py search "Popularity"
```
*Kết quả kỳ vọng:* Hiển thị bài học kiểm chứng `[HERMES-M03-01]` chứng minh Count vượt trội hơn Bayesian Weighted Average.

