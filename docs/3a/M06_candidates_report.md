# BÁO CÁO KỸ THUẬT & NGHIÊN CỨU THỰC NGHIỆM MODULE M06
## SINH ỨNG VIÊN TOP-N ALS, LỌC PHIM ĐÃ XEM VÀ ĐÁNH GIÁ TRÊN TẬP VALIDATION

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Chuyên đề:** Task 3A – Khối Gợi Ý Lọc Cộng Tác Phân Tán (Spark ALS Collaborative Filtering)  
> **Module:** M06 – Exact ALS Top-N Recommendation & Validation Evaluation  
> **Branch:** `feature/als-3a` | **Môi trường:** Python 3.12.3, PySpark 4.2.0, CPU AMD Ryzen 5 7530U, RAM 16 GB  
> **Trạng thái Kỹ thuật:** **`M06_ENGINEERING_PASS`**

---

## I. TỔNG QUAN PHẠM VI VÀ KẾT QUẢ THỰC NGHIỆM

Module M06 hiện thực hóa bước chuyển đổi từ mô hình nhân tố ẩn đã huấn luyện (M05) sang **bộ máy sinh danh sách gợi ý Top-N chuẩn xác (Exact Top-N Candidate Generator)**, tích hợp cơ chế loại trừ phim đã xem (seen-item filtering) tuyệt đối trước khi chọn Top-K, và thực thi đánh giá ngoại tuyến trên toàn bộ giao thức Validation đã cam kết tại M02.

### 1. Tóm tắt các chỉ số vận hành và tài nguyên:
- **Tập dữ liệu Validation:** 162.541 người dùng, 162.541 held-out ratings.
- **Positive-Target Cohort:** 109.779 người dùng có điểm đánh giá Validation >= 3.5.
- **Non-positive Cohort:** 52.762 người dùng có điểm đánh giá Validation < 3.5.
- **Mô hình ALS nạp lại:** `artifacts/models/als/m05_spark_als_rank16` (rank=16, regParam=0.1, maxIter=10, commit base `38c5c4f`). Không huấn luyện lại mô hình.
- **Thời gian trích xuất lịch sử Train (Seen Items):** 13.59 giây cho toàn bộ 24.675.013 tương tác của 162.541 users.
- **Thời gian sinh Top-20 cho toàn bộ 162.541 người dùng:** 198.03 giây (~3.3 phút), đạt thông lượng **820.8 users/giây**.
- **Bộ nhớ RAM sử dụng (Working Set Peak):** < 3.5 GB (hoàn toàn an toàn trên máy tính cá nhân 16 GB RAM, không tràn bộ nhớ, không swap đĩa).
- **Artifact đầu ra:** Lưu thành công 3.250.820 dòng Top-20 khuyến nghị dạng Snappy Parquet (19.38 MB) tại `artifacts/als/m06/m06_als_top20_recommendations.parquet`.

---

## II. BẢNG KẾT QUẢ ĐÁNH GIÁ CHÍNH THỨC TRÊN TẬP VALIDATION (M02 EVALUATOR)

Đánh giá được thực hiện tự động bằng bộ đo độc lập [TopNEvaluator](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/evaluator.py#L269) từ Module M02 trên đúng mẫu số 109.779 người dùng mục tiêu tích cực:

| Chỉ số Đánh giá (Metric) | K = 5 | K = 10 | K = 20 | Ghi chú & Ý nghĩa Kỹ thuật |
| :--- | :---: | :---: | :---: | :--- |
| **HitRate@K (HR)** | **0.00000** | **0.00000** | **0.00000** | Tỷ lệ tìm thấy phim mục tiêu trong Top-K (0 hit / 109.779 users). |
| **NDCG@K** | **0.00000** | **0.00000** | **0.00000** | Điểm xếp hạng chiết khấu theo vị trí (Discounted Cumulative Gain). |
| **MRR@K** | **0.00000** | **0.00000** | **0.00000** | Mean Reciprocal Rank (nghịch đảo vị trí xuất hiện đầu tiên). |
| **Precision@K** | **0.00000** | **0.00000** | **0.00000** | Độ chính xác trung bình trên K vị trí đề xuất. |
| **Recall@K** | **0.00000** | **0.00000** | **0.00000** | Bằng HitRate@K dưới giao thức Single Positive Target. |
| **Catalog Coverage (Full)** | **1.50%** | **2.48%** | **4.05%** | Tỷ lệ phim được gợi ý trên toàn bộ 62.423 phim danh mục. |
| **Catalog Coverage (Scorable)**| **1.59%** | **2.62%** | **4.29%** | Tỷ lệ phim được gợi ý trên 58.932 phim có vector Train factor. |
| **Số Phim Độc Lập Được Đề Xuất**| **938 phim** | **1.545 phim** | **2.528 phim** | Phản ánh tính phân tán của không gian vector cá nhân hóa. |
| **Tổng Số Người Dùng Trúng Đích**| 0 users | 0 users | 0 users | Không có người dùng nào có positive target lọt vào Top-20. |
| **Mẫu số Đánh giá (Denominator)**| **109.779** | **109.779** | **109.779** | Bảo toàn nghiêm ngặt 100% người dùng thuộc positive cohort. |

---

## III. ĐỐI CHỨNG THỰC NGHIỆM: SPARK ALS RANK 16 VS POPULARITY COUNT BASELINE (K = 10)

Bảng đối chiếu khoa học giữa mô hình phổ biến toàn dân M03 và mô hình ALS cá nhân hóa M06 trên cùng tập Validation:

| Tiêu chí Đánh giá | Popularity Count (M03) | Spark ALS rank 16 (M06) | So sánh Tỷ lệ (ALS / Pop) | Nhận định Bản chất Khoa học |
| :--- | :---: | :---: | :---: | :--- |
| **HitRate@10** | **0.05519 (5.52%)** | **0.00000 (0.00%)** | **0.00x** | Popularity vượt trội tuyệt đối về khả năng đoán trúng phim. |
| **NDCG@10** | **0.02789** | **0.00000** | **0.00x** | Popularity đưa được phim trúng đích vào các vị trí đầu bảng. |
| **MRR@10** | **0.01970** | **0.00000** | **0.00x** | Popularity có điểm nghịch đảo thứ hạng dương rõ rệt. |
| **Precision@10** | **0.00552** | **0.00000** | **0.00x** | Popularity đạt 0.55% độ chính xác danh mục. |
| **Catalog Coverage (Full)** | **0.50%** | **2.48%** | **+4.96x** | ALS bao phủ danh mục gấp 5 lần so với Popularity. |
| **Số Phim Độc Lập Được Đề Xuất**| **310 phim** | **1.545 phim** | **+4.98x** | ALS gợi ý đa dạng gấp 5 lần, khám phá nhiều vùng phim hơn. |
| **Mẫu số đánh giá** | 109.779 users | 109.779 users | 1.00x | Tuyệt đối đồng nhất về cohort và quy chuẩn đánh giá. |

---

## IV. PHÂN TÍCH KHOA HỌC SÂU: TẠI SAO ALS CHƯA TUNING BỊ HITRATE = 0 TRƯỚC POPULARITY?

Hiện tượng mô hình Collaborative Filtering có Train RMSE rất thấp (0.7698) nhưng lại đạt HitRate@10 = 0.00000 khi xếp hạng Top-N trên toàn bộ danh mục 58.932 phim là một bài học kinh điển trong lý thuyết Hệ thống Gợi ý (Recommender Systems Theory).

Kiểm toán độc lập đã thực hiện phân tích định lượng vi mô để bóc tách căn nguyên toán học:

### 1. Nghịch lý Hiện tượng Điểm số Đột biến ở Vùng Đuôi Dài (The Long-Tail Extreme Rating Fluke)
Trong tập Train MovieLens 25M:
- Có tới **10.324 bộ phim (17.52%)** chỉ có duy nhất **1 lượt đánh giá** trong toàn bộ lịch sử!
- Có tới **17.968 bộ phim (30.49%)** chỉ có từ 1 đến 2 lượt đánh giá!
- Phần lớn các lượt đánh giá đơn lẻ này là điểm số tuyệt đối 5.0 sao (hoặc 4.5 sao) do một người hâm mộ cá biệt chấm.

### 2. Hành vi của Hàm Tổn thất Explicit ALS
Trong chế độ Explicit Feedback (`implicitPrefs = False`), bài toán tối ưu hóa giải phương trình Ridge Regression:
```text
min_{P, Q} sum_{(u, i) in R} (r_ui - p_u^T * q_i)^2 + lambda * (||p_u||^2 + ||q_i||^2)
```
- Đối với một bộ phim vô danh `i` chỉ có 1 tương tác 5 sao từ người dùng `u*`: Thuật toán chỉ cần xoay vector `q_i` hướng theo vector `p_u*` là sai số bình phương trở về gần bằng 0!
- Hệ số phạt `regParam = 0.1` là quá nhỏ để triệt tiêu độ dài vector của các phim đơn lẻ này.
- Kết quả: Có hàng ngàn bộ phim vô danh đạt điểm dự đoán `p_u^T * q_i` từ **4.8 đến 5.3 sao**!

### 3. Sự chèn ép đối với các Phim Kinh điển Thật sự (Crowding-out of True Blockbusters)
- Các bộ phim kiệt tác như *Pulp Fiction* (`movieId 296`, 78.735 ratings) hay *The Shawshank Redemption* (`movieId 318`, 80.448 ratings) có đánh giá từ hàng chục ngàn người với gu thẩm mỹ đa dạng (từ 0.5 đến 5.0 sao). Điểm trung bình thực tế của chúng dao động quanh mức **4.19 đến 4.42 sao**.
- Mô hình ALS học rất chuẩn xác điểm này: Điểm số dự đoán của *Pulp Fiction* cho User 1 đạt **4.1746** (sai số so với thực tế chỉ 0.015 sao!).
- **Hậu quả xếp hạng:** Mặc dù 4.1746 là một điểm số rất cao, nhưng nó bị **338 bộ phim vô danh 1 tương tác** (có điểm giả lập từ 4.18 đến 5.21) vượt mặt và đẩy *Pulp Fiction* văng xuống tận vị trí thứ 339!
- Khi cắt ngưỡng `Top-K` ở mức K = 5, 10, 20: Toàn bộ 20 vị trí đầu bảng của mọi người dùng đều bị chiếm trọn bởi các bộ phim đuôi dài đột biến này (như phim *The Thorn (1971)*, *Sing (1989)*, *Dead in the Water (2006)*).

### 4. Khảo sát Vị trí Xếp hạng Thực tế của Phim Mục tiêu (Validation Target Rank Distribution)
Khảo sát phân phối vị trí thực tế của phim mục tiêu trên mẫu 500 người dùng tích cực:
- **Vị trí tốt nhất (Min Rank):** 188 (không có bất kỳ người dùng nào có mục tiêu lọt vào Top-100!).
- **Vị trí trung vị (Median Rank):** **3.990,0** (nửa số người dùng có mục tiêu nằm từ vị trí 4.000 trở xuống).
- **Vị trí trung bình (Mean Rank):** **7.803,0** trên 58.932 phim.
- **Tỷ lệ mục tiêu nằm trong Top-500:** 3.20%.
- **Tỷ lệ mục tiêu nằm trong Top-1000:** 13.00%.

### 5. Kết luận Khoa học & Giá trị Định hướng cho M07 và Phase 7
- Kết quả này chứng minh bằng thực nghiệm: **Tối ưu hóa RMSE trên tập Train hoàn toàn không đồng nghĩa với tối ưu hóa năng lực xếp hạng Top-N!**
- Mô hình ALS Explicit thuần túy với tham số mặc định (`regParam = 0.1`, `rank = 16`) bị thất bại hoàn toàn trước Popularity Baseline vì thiếu cơ chế phạt độ tin cậy (Confidence / Popularity Shrinkage).
- Đây chính là luận cứ khoa học vững chắc nhất để triển khai:
  1. **Module M07 (Hyperparameter Tuning):** Thử nghiệm các mức phạt `regParam` lớn hơn (ví dụ 0.5, 1.0, 5.0) để co ép mạnh các vector ít tương tác về gốc tọa độ, hoặc chuyển sang cơ chế Implicit/Confidence-weighted ALS.
  2. **Phase 7 (Hybrid Recommender):** Kết hợp Đồ thị Tri thức (Task 3B - Knowledge Graph) để dùng độ tin cậy của thực thể và độ phổ biến thực tế làm bộ lọc định tuyến trước khi lấy điểm ALS.

---

## V. KIỂM TOÁN DANH MỤC & HIỆU ỨNG COLD-START (CATALOG ELIGIBILITY AUDIT)

Kiểm toán toàn diện mối quan hệ giữa danh mục phim gốc và không gian nhân tố M05:
1. **Full Catalog:** **62.423 bộ phim** (`data/processed/core/movies`).
2. **ALS-Scoreable Catalog:** **58.932 bộ phim (94.41%)** có mặt trong `itemFactors` của M05.
3. **Unscoreable Catalog:** **3.491 bộ phim (5.59%)** hoàn toàn không có tương tác nào trong tập Train.
4. **Tác động lên tập Validation:**
   - Trong số 109.779 người dùng positive cohort, có đúng **30 người dùng** có phim mục tiêu rơi vào nhóm 3.491 phim unscoreable này.
   - **Trần lý thuyết tối đa của ALS-only:** `(109.779 - 30) / 109.779 = 99.9727%`.
   - **Nguyên tắc khoa học:** 30 người dùng này được tính là trượt (miss = 0.0) và **tuyệt đối giữ nguyên trong mẫu số 109.779**, không loại bỏ để làm đẹp số liệu.

---

## VI. HIỆU NĂNG TÍNH TOÁN & CƠ CHẾ AN TOÀN BỘ NHỚ (PERFORMANCE BENCHMARK)

Bảng đo đạc hiệu năng thực tế trên laptop cá nhân (CPU AMD Ryzen 5 7530U, RAM 16 GB):

| Cổng Kiểm tra (Benchmark Gate) | Quy mô | Thời gian Thực thi | Thông lượng (Throughput) | Nhận xét An toàn |
| :--- | :---: | :---: | :---: | :--- |
| **Gate A: Single Regular User** | 1 user (68 seen items) | 4.15 ms | 240.9 users/s | Phép nhân vector-matrix cực nhanh qua BLAS. |
| **Gate B: Single Heavy User** | 1 user (32.200 seen items) | 12.55 ms | 79.7 users/s | Lọc 32.200 phim qua hash set O(1), 0 rò rỉ seen item. |
| **Gate C: Small Batch** | 100 users | 206.56 ms | 484.1 users/s | Ma trận (100, 16) @ (16, 58.932). |
| **Gate D: Medium Batch** | 2.500 users | 3.938.81 ms | 634.7 users/s | Khối tính toán chuẩn 589 MB trong RAM, 0 tràn nhớ. |
| **Full Validation Generation**| **162.541 users** | **198.03 s (~3.3 phút)** | **820.8 users/s** | Xử lý tuần tự 66 batch, bộ nhớ ổn định < 3.5 GB. |
| **TopNEvaluator Evaluation** | 109.779 users | 3.66 s | 29.994 users/s | Đánh giá song song K=5, 10, 20. |

---

## VII. ĐỐI CHỨNG VỚI MÔ HÌNH ORACLE TOÁN HỌC & KIỂM THỬ NGHỊCH LÝ

Hệ thống đã vượt qua 100% bộ kiểm thử tự động tại [test_candidates.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_candidates.py):
1. **Mathematical Oracle Equivalence:** So sánh với hàm tính tay chuẩn giải tích `exact_top_k_oracle`, đạt độ trùng khớp 100% trên cả dữ liệu ngẫu nhiên và dữ liệu có hòa điểm (tie).
2. **Oversampling Counterexample (Bài test 12):** Chứng minh phương pháp lấy Top-K trước rồi lọc seen (`recommend(K) -> remove_seen`) bị rỗng danh sách (0 items) khi top phim đã xem hết, trong khi thuật toán Exact Filter-Before-Top-K trả về chính xác 5 phim hợp lệ tiếp theo.
3. **Phá hòa tất định (Deterministic Tie-breaking):** Bảo đảm quy tắc `als_score DESC` và `movieId ASC` hoạt động ổn định trên toàn bộ các biên phân vùng.
4. **Hồi quy toàn diện:** Toàn bộ **118/118 bài test** của Task 3A (từ M00 đến M06) đều PASS 100%.

---

## VIII. DANH MỤC ARTIFACTS VÀ CHUYỂN GIAO CHO MODULE M07

Các tệp kết quả chính thức đã được xuất bản và lưu trữ vĩnh viễn:
1. `artifacts/als/m06/m06_als_top20_recommendations.parquet`: Bảng gợi ý Top-20 cho toàn bộ 162.541 người dùng (3.250.820 dòng, 19.38 MB).
2. `artifacts/als/m06/m06_als_evaluation_results.json`: Báo cáo chi tiết toàn bộ các chỉ số đo đạc, benchmark thời gian và kiểm toán danh mục.
3. `artifacts/als/m06/m06_sample_user_recommendations.json`: Bản ghi minh họa danh sách gợi ý kèm tiêu đề phim thực tế cho các đối tượng người dùng tiêu biểu phục vụ vấn đáp bảo vệ.
4. **Nhiệm vụ chuyển giao cho M07 (Hyperparameter Tuning):**
   - Giữ nguyên cấu trúc `ALSCandidateGenerator` và hợp đồng `TopNEvaluator`.
   - Thực hiện dò quét lưới (Grid Search) trên không gian tham số: `regParam in [0.01, 0.05, 0.1, 0.5, 1.0, 5.0]` và `rank in [8, 16, 32, 64]`.
   - Mục tiêu tối thượng của M07: Tìm ra cấu hình siêu tham số khắc phục hiện tượng Fluke Bias ở vùng đuôi dài và đánh bại mốc chuẩn `HitRate@10 = 0.05519` của Popularity Count.
