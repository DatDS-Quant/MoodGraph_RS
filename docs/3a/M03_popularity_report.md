# MoodGraph Task 3A – Module M03: Popularity Baseline Recommender Report

## 1. Mục tiêu & Định nghĩa Bài toán (Scope & Objectives)

- **Module**: M03 – Global Popularity Baseline Recommender & Source Code Defense Map
- **Dự án**: MoodGraph – Personalized Movie Recommendation using Knowledge Graphs and Apache Spark
- **Branch**: `feature/als-3a`
- **Mục tiêu kỹ thuật (Engineering Goal)**:
  - Xây dựng mô hình gợi ý phim phổ biến (Popularity Baseline) không cá nhân hóa dựa hoàn toàn trên tập `splits/train`.
  - Triển khai và đối chứng thực nghiệm hai biến thể: **Rating Count Baseline** và **Bayesian / Weighted Average Baseline**.
  - Tích hợp bộ lọc phim đã xem (seen-item filtering) nhằm bảo đảm mọi người dùng đều nhận đủ K phim ứng viên hợp lệ.
  - Tái sử dụng trực tiếp bộ đánh giá **TopNEvaluator** từ Module M02 để đo lường hiệu năng trên toàn bộ tập Validation.
- **Ranh giới an toàn (Safety Boundaries)**:
  - **Không** sử dụng nhãn hoặc tương tác của tập Validation để tính điểm phổ biến.
  - **Tuyệt đối không** đọc hoặc nạp tập Test (`splits/test`).
  - **Không** huấn luyện ALS ở Module M03 (dành riêng cho M04–M07).
  - **Không** can thiệp vào nhánh Knowledge Graph (Task 3B).

---

## 2. Công thức & Cơ chế Xếp hạng của Các Biến Thể Baseline

### 2.1. Biến thể A: Rating Count Baseline (`POPULARITY_COUNT`)
- **Triết lý**: Bộ phim được nhiều người xem và đánh giá nhất trong quá khứ phản ánh độ phổ biến đại chúng cao nhất.
- **Điểm số**:
  ```text
  raw_score = float(v)
  ```
  trong đó `v` là tổng số lượt đánh giá của bộ phim trong tập Train.
- **Quy tắc sắp xếp (Tie-breaking)**:
  1. `rating_count DESC` (Tiêu chí chính)
  2. `avg_rating DESC` (Tiêu chí phụ khi bằng lượt)
  3. `movieId ASC` (Phá hòa tất định theo ID tăng dần)

### 2.2. Biến thể B: Bayesian / Weighted Average Baseline (`POPULARITY_WEIGHTED`)
- **Triết lý**: Kết hợp điểm trung bình của bộ phim với số lượng đánh giá và điểm trung bình toàn cục để ngăn chặn các bộ phim chỉ có 1–2 lượt đánh giá 5 sao vô danh chiếm lĩnh đầu bảng (Fluke bias).
- **Công thức (Dirichlet Prior / IMDB Formula)**:
  ```text
  WeightedScore = (v * R + m * C) / (v + m)
  ```
  trong đó:
  - `v`: Số lượt đánh giá của bộ phim trong tập Train (`rating_count`).
  - `R`: Điểm đánh giá trung bình của bộ phim trong tập Train (`avg_rating`).
  - `C`: Điểm đánh giá trung bình toàn cục của toàn bộ 24,675,013 tương tác Train (`global_mean = 3.531522`).
  - `m`: Trọng số làm mượt / số lượt đánh giá giả định (Prior weight, mặc định `m = 10.0`).
- **Hành vi tiệm cận của công thức**:
  - Khi `v -> ∞`: `WeightedScore -> R` (Số lượng mẫu lớn, điểm trung bình của chính bộ phim chiếm ưu thế tuyệt đối).
  - Khi `v -> 0`: `WeightedScore -> C` (Ít mẫu, điểm số bị kéo mạnh về điểm trung bình toàn dân C).
  - Khi `m = 0`: `WeightedScore = R` (Trở về điểm trung bình thô không điều chỉnh).
- **Quy tắc sắp xếp (Tie-breaking)**:
  1. `weighted_score DESC` (Tiêu chí chính)
  2. `rating_count DESC` (Tiêu chí phụ)
  3. `movieId ASC` (Phá hòa tất định)

### 2.3. Ví dụ Minh Họa Tính Tay Độc Lập
Giả sử điểm trung bình toàn cục `C = 3.5` và hệ số làm mượt `m = 10.0`:
- **Phim A (Phim kinh điển được nhiều người khen)**: `v = 100`, `R = 4.5`:
  ```text
  WeightedScore = (100 * 4.5 + 10 * 3.5) / (100 + 10) = (450 + 35) / 110 = 485 / 110 ≈ 4.409091
  ```
- **Phim B (Phim ngách, chỉ có 1 người chấm điểm tối đa)**: `v = 1`, `R = 5.0`:
  ```text
  WeightedScore = (1 * 5.0 + 10 * 3.5) / (1 + 10) = (5 + 35) / 11 = 40 / 11 ≈ 3.636364
  ```
- **Phim C (Phim ngách, 1 người chê)**: `v = 1`, `R = 1.0`:
  ```text
  WeightedScore = (1 * 1.0 + 10 * 3.5) / (1 + 10) = (1 + 35) / 11 = 36 / 11 ≈ 3.272727
  ```
*Nhận xét:* Nếu chỉ dùng điểm trung bình thô R, Phim B (`R = 5.0`) sẽ đứng trên Phim A (`R = 4.5`). Khi dùng Bayesian Average, Phim B bị kéo tụt xuống `3.636` và xếp sau Phim A (`4.409`), giải quyết triệt để lỗi mẫu nhỏ.

---

## 3. Kiến Trúc Thực Thi & Chiến Lược Kiểm Soát Tài Nguyên

### 3.1. Tổng Hợp Thống Kê Phân Tán Bằng Spark
- Tính toán trực tiếp trên 24,675,013 dòng bằng `train_df.groupBy("movieId").agg(...)` và `train_df.select(F.avg("rating"))`.
- Bảng tổng hợp trả về driver chỉ gồm **58,932 dòng** (tương đương ~2.5 MB bộ nhớ RAM), hoàn thành trong **5.02 giây** với 12 cores CPU.
- Driver không bao giờ phải nạp toàn bộ 24.6 triệu dòng thô vào Python list hay pandas DataFrame.

### 3.2. Chiến Lược Lọc Phim Đã Xem (Seen Items Filtering) & Bù Ứng Viên
- **Bài toán**: Người dùng không được nhận lại phim họ đã đánh giá trong Train. Trong khi đó, người dùng tích cực nhất trong MovieLens 25M đã xem tới **32,200 phim** trong Train.
- **Giải pháp**:
  - Sắp xếp toàn bộ 58,932 phim theo thứ tự phổ biến toàn cục (chỉ làm 1 lần duy nhất).
  - Với mỗi user, lưu lịch sử Train dưới dạng `set` số nguyên (tra cứu O(1)).
  - Duyệt tuần tự danh sách phim phổ biến: nếu phim nằm trong `seen_movies` thì bỏ qua, nếu chưa xem thì lấy vào danh sách đề xuất. Dừng lại khi đủ K phim.
  - Do danh mục có 58,932 phim và người xem nhiều nhất là 32,200 phim, hệ thống luôn luôn tìm đủ K = 5, 10, 20 phim chưa xem cho 100% người dùng.
- **Kiểm soát bộ nhớ**:
  - Không thực hiện phép Cross Join toàn bộ 162,541 users × 62,423 movies (tránh tạo ma trận 10 tỷ phần tử gây tràn 16 GB RAM).
  - Thuật toán sinh Top-K trong Python chỉ mất **8.28 giây** để sinh và lọc cho toàn bộ 162,541 người dùng!

---

## 4. Bảng Kết Quả Thực Nghiệm Toàn Diện Trên Tập Validation

Thực nghiệm được thực thi tự động qua script [`scripts/run_m03_popularity.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m03_popularity.py) trên toàn bộ **162,541 người dùng Validation** với **109,779 người dùng thuộc nhóm mục tiêu tích cực (Positive-Target Cohort)**:

### 4.1. Bảng So Sánh Chi Tiết Giữa Hai Biến Thể

| Phương pháp (Baseline Variant) | Cutoff (K) | HitRate@K (HR) | NDCG@K | MRR@K | Precision@K | Recall@K | Catalog Coverage (Full) | Số Phim Độc Lập Được Gợi Ý |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A. POPULARITY_COUNT** | **K = 5** | 0.0330 (3.30%) | 0.0208 | 0.0168 | 0.0066 | 0.0330 | 0.35% | 218 phim |
| **A. POPULARITY_COUNT** | **K = 10** | **0.0552 (5.52%)** | **0.0279** | **0.0197** | **0.0055** | **0.0552** | **0.50%** | **310 phim** |
| **A. POPULARITY_COUNT** | **K = 20** | 0.0896 (8.96%) | 0.0365 | 0.0220 | 0.0045 | 0.0896 | 0.74% | 460 phim |
| **B. POPULARITY_WEIGHTED** | **K = 5** | 0.0091 (0.91%) | 0.0043 | 0.0028 | 0.0018 | 0.0091 | 0.05% | 30 phim |
| **B. POPULARITY_WEIGHTED** | **K = 10** | **0.0197 (1.97%)** | **0.0077** | **0.0042** | **0.0020** | **0.0197** | **0.07%** | **46 phim** |
| **B. POPULARITY_WEIGHTED** | **K = 20** | 0.0332 (3.32%) | 0.0111 | 0.0051 | 0.0017 | 0.0332 | 0.16% | 102 phim |

*Ghi chú Mẫu số Đánh giá:*
- Mẫu số chính (`positive_cohort_size`): **109,779** người dùng có rating Validation >= 3.5.
- Số người dùng trúng mục tiêu ở K=10:
  - `POPULARITY_COUNT`: **6,059** users trúng.
  - `POPULARITY_WEIGHTED`: **2,161** users trúng.
- Nhóm 52,762 users có rating < 3.5 được ghi nhận riêng trong thống kê chẩn đoán toàn dân (`diagnostic_all_users.all_users_hit_rate = 3.73%` đối với Count và `1.33%` đối với Weighted).

---

## 5. Phân Tích Khoa Học & Quyết Định Chọn Baseline Chính

### 5.1. Tại sao Rating Count Vượt Trội Hơn Weighted Average Gần 3 Lần?
1. **Thiên lệch phổ biến cực đoan trong MovieLens (Popularity Bias)**:
   - Các bộ phim có lượt tương tác lớn nhất trong Train (`movieId 318`: 80,448 lượt; `movieId 356`: 80,375 lượt; `movieId 296`: 78,735 lượt) là các tác phẩm bom tấn kinh điển mà phần lớn người dùng trong cộng đồng đều đã từng xem hoặc muốn xem.
   - Do đó, trong một mô hình **hoàn toàn không có thông tin cá nhân hóa**, xác suất một người dùng ngẫu nhiên tương tác với một phim bom tấn cao hơn rất nhiều so với một bộ phim ít người biết.
2. **Hạn chế của Bayesian Average đối với Top-N Ranking không cá nhân hóa**:
   - Bayesian Average xếp các phim có điểm trung bình cao lên đầu bảng (ví dụ: `movieId 171011` có điểm 4.48 nhưng chỉ có 1,082 người xem). Mặc dù chất lượng nội dung của phim đó được đánh giá cao, nhưng phạm vi người xem của nó rất hẹp. Đề xuất phim này cho 162,541 người dùng dẫn đến xác suất trúng cực kỳ thấp.
3. **Quyết định kỹ thuật**:
   - Chọn chính thức **`POPULARITY_COUNT`** làm **Primary Baseline Recommender** cho toàn bộ dự án MoodGraph.
   - Điểm số chuẩn cần vượt qua tại mốc kiểm định K=10 là: **NDCG@10 = 0.02789** và **HitRate@10 = 5.519%**.
   - Mọi mô hình tiếp theo (Spark ALS ở M05–M08 và Hybrid ở Phase 7) bắt buộc phải vượt qua mốc chuẩn này để chứng minh giá trị của thuật toán cá nhân hóa.

---

## 6. Khảo Sát Catalog Coverage & Giới Hạn Cold-Start

1. **Catalog Coverage Cực Thấp (0.50% ở K=10)**:
   - Trên toàn bộ 109,779 người dùng, `POPULARITY_COUNT` chỉ gợi ý tổng cộng **310 bộ phim độc lập** trong tổng số 62,423 bộ phim của danh mục MovieLens 25M.
   - Hơn **99.5% danh mục phim** (các phim ở vùng đuôi dài - Long Tail) hoàn toàn không bao giờ được xuất hiện trong danh sách đề xuất.
   - Đây là bằng chứng thực nghiệm rõ ràng nhất cho thấy sự nghèo nàn về mặt đa dạng danh mục của các mô hình gợi ý theo độ phổ biến.
2. **Khả Năng Xử Lý Cold-Start**:
   - Đối với **User Cold-Start** (người dùng mới chưa có lịch sử Train): Mô hình Popularity hoạt động hoàn hảo như một cơ chế cứu cánh (fallback), trả về ngay 10 phim phổ biến nhất danh mục.
   - Đối với **Movie Cold-Start** (3,491 phim trong catalog chưa từng có lượt đánh giá nào trong Train): Mô hình Popularity hoàn toàn bất lực và không thể xếp hạng các phim này. Đây là động lực bắt buộc phải có nhánh Đồ thị Tri thức (Task 3B - Knowledge Graph) dựa trên đạo diễn, thể loại và diễn viên để giải cứu phim cold-start.

---

## 7. Kết Quả Kiểm Thử Tự Động & Hồi Quy (62/62 Tests PASS)

Toàn bộ **62/62 tests** của dự án đã vượt qua 100% trong **35.35 giây**:

- **Suite M03: Popularity Baseline (22/22 PASS)**:
  - `test_01_count_aggregation_correctness`: PASS
  - `test_02_average_rating_correctness`: PASS
  - `test_03_hand_calculated_weighted_average`: PASS (Khớp tính tay)
  - `test_04_count_ranking_order`: PASS
  - `test_05_weighted_average_ranking_order`: PASS
  - `test_06_stable_tie_breaking`: PASS (Xử lý hòa tất định theo ID tăng dần)
  - `test_07_single_rating_movie_behavior`: PASS
  - `test_08_movie_with_zero_ratings_behavior`: PASS
  - `test_09_seen_items_filtering`: PASS (Không lọt phim đã xem)
  - `test_10_top_k_replenishment_after_seen_filtering`: PASS (Bù đủ K phim)
  - `test_11_heavy_user_seen_many_movies`: PASS (User xem 1,000 phim)
  - `test_12_no_duplicate_movie_ids_in_top_k`: PASS
  - `test_13_no_out_of_catalog_movies`: PASS
  - `test_14_all_scores_finite_no_nan_or_inf`: PASS
  - `test_15_deterministic_output`: PASS
  - `test_16_integration_with_m02_evaluator`: PASS
  - `test_17_positive_user_without_hit_kept_in_denominator`: PASS
  - `test_18_no_validation_leakage_in_popularity_stats`: PASS
  - `test_19_test_split_isolation`: PASS
  - `test_20_multi_k_support_and_consistency`: PASS
  - `test_21_independent_reference_implementation_comparison`: PASS (Khớp code tham chiếu độc lập)
  - `test_22_parameter_m_limiting_behavior`: PASS (Kiểm chứng tiệm cận m -> 0 và m -> ∞)
- **Regression Suite M00 (5/5 PASS)**: Đạt 100%.
- **Regression Suite M01 (14/14 PASS)**: Đạt 100%.
- **Regression Suite M02 (21/21 PASS)**: Đạt 100%.

---

## 8. Kết Nối Tài Liệu & Kho Tri Thức HERMES

- Bản đồ mã nguồn chi tiết và cẩm nang bảo vệ đồ án trước Hội đồng: [`docs/3a/M03_source_code_defense_map.md`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M03_source_code_defense_map.md).
- Bài học kiểm chứng đã ghi nhận vào kho tri thức: `[HERMES-M03-01]` (Xác minh thực nghiệm tính vượt trội của Rating Count so với Bayesian Weighted Average trong Top-N).
- Lệnh tra cứu nhanh tri thức: `python scripts/hermes_memory.py search "Popularity"`.

---

## 9. Kết Luận Nghiệm Thu Kỹ Thuật

- Module M03 đã hoàn thành xuất sắc toàn bộ các yêu cầu khắt khe của Autonomous Engineering Quality Protocol.
- Trạng thái nghiệm thu: **`M03_ENGINEERING_PASS`** (Có đầy đủ bằng chứng kiểm thử tự động, kết quả thực nghiệm 24.6M ratings và Defense Map chỉ rõ từng dòng code).
- Sẵn sàng bàn giao cho Mentor và chủ dự án trước khi chuyển tiếp sang **Module M04: Toy ALS Implementation & Verification**.
