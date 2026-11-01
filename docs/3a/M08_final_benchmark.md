# BÁO CÁO KHOA HỌC M08: ĐỐI CHUẨN OFFLINE TRÊN TẬP TEST ĐÓNG BĂNG (FROZEN TEST BENCHMARK)

- **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị Tri thức và Apache Spark
- **Mã module:** M08 (Final Offline Benchmark on Frozen Test Split)
- **Git Branch:** `feature/als-3a`
- **Mô hình vô địch đã đóng băng:** `ALS_R8_REG0.3_ITER10` ([`best_als_model_manifest.json`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m07/best_als_model_manifest.json))
- **Giao thức:** Đánh giá kiểm định một lượt duy nhất (Single-Shot Evaluation), tuyệt đối không tinh chỉnh lại siêu tham số, không nạp lại tập Test để chọn mô hình.

---

## 1. TỔNG QUAN VÀ BẢO ĐẢM LIÊM CHÍNH TRƯỚC THỰC NGHIỆM (PRE-FLIGHT INTEGRITY)

Trước khi truy cập tập dữ liệu Test (`data/processed/splits/test`), hệ thống đã vượt qua kiểm toán tiền kiểm định tự động ([`run_preflight_audit`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L90-L170)):
1. **Kiểm tra Git Branch:** Đang ở đúng branch `feature/als-3a` tại commit `4449892`.
2. **Khóa mã băm SHA-256 các tài liệu đóng băng:**
   - `artifacts/als/m07/m07_to_m08_freeze_manifest.json`: `5a2a1644c0defed2d6bd9a26d56bec52177af35426bb73d4a501dfd74888dd3f`
   - `artifacts/als/m07/best_als_model_manifest.json`: `4014f5bb25c7a9cce7f1a71f21ceefd2ebd02541c9de808275dc68373abf65e2`
   - `artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10/manifest.json`: `6b62a3fb3116469ddfb900baded9b7387e9524b20196d454b1220561ac6e6322`
   - `artifacts/models/als/m05_spark_als_rank16/manifest.json`: `bf2ac068495cf90f700ca4b5800def53ce006228d0819848f31f00813b611cfa`
   - `docs/TASK_3A_SPARK_ALS_ROADMAP.md`: `90568faa3571490bb67561b9be34d1d5b882349d40242c146294b93cf122ee25`
3. **Mô hình ALS vô địch:**
   - Đường dẫn Canonical: [`artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10)
   - Cấu hình siêu tham số: `rank = 8`, `regParam = 0.3`, `maxIter = 10`, `implicitPrefs = False`, `seed = 42`.
   - Kích thước ma trận nhân tử: `userFactors` có đúng 162.541 dòng (chiều 8), `itemFactors` có đúng 58.932 dòng (chiều 8).

---

## 2. QUY TRÌNH LỌC PHIM ĐÃ XEM VÀ MẪU SỐ KIỂM ĐỊNH TẬP TEST

### 2.1. Quy tắc Lọc Đã xem Cốt lõi (Critical Test-Stage Seen Filtering)
Điểm khác biệt cốt lõi mang tính giao thức khoa học giữa Validation và Test:
- **Giai đoạn Validation (M03, M06, M07):**
  `seen_u = Train_u`
- **Giai đoạn Test (M08):**
  `seen_u = Train_u ∪ Validation_u`

Toàn bộ các phim mà người dùng đã tương tác trong cả tập Train và tập Validation đều bị loại bỏ khỏi không gian ứng viên Top-K của người dùng đó (gán điểm `-inf` trước khi chọn Top-K).
- Số lượng tương tác Train được nạp: **24.675.013** ratings.
- Số lượng tương tác Validation được nạp bổ sung vào bộ lọc: **162.541** ratings.
- Tổng số tương tác đã lọc: **24.837.554** tương tác.
- **Tính độc lập dữ liệu:** Tập Validation **CHỈ** được sử dụng làm danh sách loại trừ (seen filter). Tập Validation tuyệt đối không được gộp vào Train để huấn luyện lại mô hình ALS hoặc tính lại tần suất Popularity.

### 2.2. Xác định Mẫu số Kiểm định Tích cực của Tập Test (Test Positive Cohort)
- Tổng số tương tác trong tập Test: **162.541** ratings (mỗi người dùng có đúng 1 tương tác kiểm thử cuối cùng theo Leave-1-Last).
- Theo giao thức đánh giá đã khóa ([`docs/evaluation_protocol.md`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/evaluation_protocol.md)), ngưỡng yêu thích là `rating >= 3.5`.
- **Thực tế quan sát trên tập Test:**
  - Số người dùng có tương tác tích cực (`rating >= 3.5`): **111.211 users** (`positive_cohort_size`).
  - Số người dùng có tương tác không tích cực (`rating < 3.5`): **51.330 users**.
- **Lưu ý khoa học quan trọng:** Mẫu số của tập Test là **111.211 người dùng**, khác với mẫu số **109.779 người dùng** của tập Validation. Điều này phản ánh tính ngẫu nhiên tự nhiên trong hành vi đánh giá của người dùng tại thời điểm cuối cùng, minh chứng rằng hệ thống không sao chép số liệu Validation sang Test.

### 2.3. Kiểm toán Phim Cold-Start không thể chấm điểm (Unscoreable Targets Audit)
- Trong số 111.211 mục tiêu tích cực của tập Test, có đúng **29 bộ phim** hoàn toàn chưa từng xuất hiện trong tập Train (0 lượt đánh giá Train).
- Mô hình ALS thuần túy không thể tạo vector biểu diễn cho 29 bộ phim này.
- **Quy tắc công bằng:** 29 mục tiêu này **bắt buộc đóng góp vào số ca trượt (miss) và được bảo toàn nguyên vẹn trong mẫu số (111.211)** của mô hình ALS, tuyệt đối không được loại bỏ để làm đẹp chỉ số.

---

## 3. KẾT QUẢ ĐỐI CHUẨN THỰC NGHIỆM TRÊN TẬP TEST (M08 TEST BENCHMARK RESULTS)

Toàn bộ 3 mô hình được đánh giá trên cùng một tập 111.211 người dùng tích cực, cùng danh mục 62.423 phim, áp dụng quy tắc phá hòa nhất quán: `raw_score DESC, movieId ASC`.

### 3.1. Bảng Tổng hợp Kết quả Thực nghiệm trên Tập Test

| Tên Mô hình | Họ Mô hình | K | Test HitRate@K | Test NDCG@K | Test MRR@K | Test Precision@K | Test Recall@K | Coverage (Full) | Số phim Top-K | Số ca trúng (Hits) |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **M03_POPULARITY_COUNT** | Baseline | 5 | **0.03262** | 0.02053 | 0.01659 | 0.00652 | 0.03262 | 0.365% | 228 | 3.628 / 111.211 |
| **M03_POPULARITY_COUNT** | Baseline | 10 | **0.05357** | **0.02721** | **0.01929** | 0.00536 | 0.05357 | **0.508%** | **317** | **5.958 / 111.211** |
| **M03_POPULARITY_COUNT** | Baseline | 20 | **0.08605** | 0.03533 | 0.02146 | 0.00430 | 0.08605 | 0.729% | 455 | 9.570 / 111.211 |
| **M03_POPULARITY_WEIGHTED_M10** | Baseline | 5 | 0.00890 | 0.00424 | 0.00275 | 0.00178 | 0.00890 | 0.050% | 31 | 990 / 111.211 |
| **M03_POPULARITY_WEIGHTED_M10** | Baseline | 10 | **0.01884** | **0.00742** | **0.00404** | 0.00188 | 0.01884 | **0.078%** | **49** | **2.095 / 111.211** |
| **M03_POPULARITY_WEIGHTED_M10** | Baseline | 20 | 0.03193 | 0.01072 | 0.00494 | 0.00160 | 0.03193 | 0.162% | 101 | 3.551 / 111.211 |
| **ALS_R8_REG0.3_ITER10** | ALS_ONLY | 5 | 0.00001 | 0.00001 | 0.00000 | 0.00000 | 0.00001 | 0.027% | 17 | 1 / 111.211 |
| **ALS_R8_REG0.3_ITER10** | ALS_ONLY | 10 | **0.00001** | **0.00001** | **0.00000** | 0.00000 | 0.00001 | **0.054%** | **34** | **1 / 111.211** |
| **ALS_R8_REG0.3_ITER10** | ALS_ONLY | 20 | 0.00001 | 0.00001 | 0.00000 | 0.00000 | 0.00001 | 0.112% | 70 | 1 / 111.211 |

*Nguồn trích xuất tự động:* [`artifacts/als/m08/m08_test_comparison_table.csv`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m08/m08_test_comparison_table.csv).

---

## 4. ĐỐI CHIẾU GIỮA TẬP VALIDATION VÀ TẬP TEST (VALIDATION VS TEST COMPARISON)

Bảng so sánh tính nhất quán giữa giai đoạn Validation và Test tại ngưỡng tiêu chuẩn K=10:

| Chỉ số tại K=10 | Popularity Count (Val) | Popularity Count (Test) | Popularity Weighted (Val) | Popularity Weighted (Test) | Spark ALS Finalist (Val) | Spark ALS Finalist (Test) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Mẫu số (Positive Users)** | 109.779 | **111.211** | 109.779 | **111.211** | 109.779 | **111.211** |
| **Số ca trúng (Hits@10)** | 6.059 | **5.958** | 2.162 | **2.095** | 0 | **1** |
| **HitRate@10** | 0.05519 | **0.05357** | 0.01969 | **0.01884** | 0.00000 | **0.00001** |
| **NDCG@10** | 0.02789 | **0.02721** | 0.00771 | **0.00742** | 0.00000 | **0.00001** |
| **MRR@10** | 0.01970 | **0.01929** | 0.00416 | **0.00404** | 0.00000 | **0.00000** |
| **Coverage@10 (Full)** | 0.497% | **0.508%** | 0.074% | **0.078%** | 0.056% | **0.054%** |
| **Số phim độc lập Top-10** | 310 | **317** | 46 | **49** | 35 | **34** |

### Nhận xét Khoa học về Khác biệt Validation vs Test:
1. **Tính Ổn định Tuyệt vời của Popularity Count:**
   - HitRate@10 giảm rất nhẹ từ `0.05519` (Val) xuống `0.05357` (Test), mức độ chênh lệch chỉ khoảng 2.9%.
   - NDCG@10 giảm từ `0.02789` xuống `0.02721` (giảm 2.4%).
   - Sự sụt giảm nhẹ này là hoàn toàn tự nhiên vì ở bước Test, mỗi người dùng đã có thêm 1 bộ phim bị loại khỏi danh sách (phim xem ở Validation), làm dịch chuyển nhẹ vị trí các ứng viên.
2. **Tính Tương đồng của Popularity Weighted:**
   - HitRate@10 đạt `0.01884` (so với `0.01969` ở Val).
   - Tỷ lệ chênh lệch giữa Count và Weighted tiếp tục được duy trì ở mức **2.84 lần** trên Test (so với 2.80 lần trên Validation).
3. **Hiện tượng của Explicit ALS:**
   - Tại Validation, ALS đạt 0 hits / 109.779 users.
   - Tại Test, ALS đạt **1 hit / 111.211 users** (User ID: 151515, đề xuất trúng phim mục tiêu tại vị trí rank 4).
   - Độ phủ danh mục Top-10 giữ nguyên ở mức cực thấp: 34 bộ phim độc lập (0.054%), khẳng định hiện tượng hội tụ Top-N vào các bộ phim đuôi dài hiếm (Fluke Bias) vẫn hoàn toàn chi phối mô hình Explicit ALS thuần túy.

---

## 5. PHÂN TÍCH NGUYÊN NHÂN VÀ GIỚI HẠN KHOA HỌC (SCIENTIFIC ROOT-CAUSE & LIMITATIONS)

### 5.1. Vì sao Popularity Count áp đảo hoàn toàn Explicit ALS trên dữ liệu thực?
1. **Hàm mục tiêu không đồng nhất (Objective Mismatch):**
   - Spark MLlib ALS được tối ưu để giảm thiểu sai số hồi quy bình phương tối thiểu (RMSE) trên các cặp (user, movie) đã có rating.
   - Một bộ phim chỉ có 1 rating 5.0 trong Train có thể dễ dàng đạt điểm dự đoán 5.0 hoặc cao hơn (thậm chí 8.0 - 10.0 do tích vô hướng factor chưa co đủ mạnh), từ đó chiếm trọn vị trí Top-20 của hàng chục nghìn người dùng.
   - Ngược lại, Popularity Count trực tiếp đo lường xác suất tương tác biên `P(Item)` trên toàn hệ thống. Trong bài toán Leave-1-Last, người dùng thực tế có xu hướng tương tác với các bộ phim quen thuộc, nổi tiếng cao hơn rất nhiều so với các bộ phim ngẫu nhiên chỉ có 1 người xem trên toàn thế giới.
2. **Hiện tượng Thiên lệch Đuôi dài (Fluke Bias):**
   - Như đã kiểm toán tại M07, có tới hơn 95% vị trí Top-20 của mô hình ALS bị chiếm giữ bởi các bộ phim có dưới 5 ratings trong Train. Các bộ phim này hoàn toàn không nằm trong tầm quan tâm của người dùng phổ thông.

### 5.2. Giới hạn của Giao thức Đánh giá One-Held-Out Test
1. **Một mục tiêu duy nhất trên mỗi người dùng (Sparse Positive Feedback):**
   - Trong tập MovieLens 25M, Leave-1-Last chỉ giữ lại đúng 1 tương tác cuối cùng làm Test target.
   - Nếu người dùng xem và thích 100 bộ phim khác nhau trong thực tế nhưng chỉ có 1 phim được chọn làm ground-truth, ngay cả khi mô hình gợi ý 19 bộ phim tuyệt vời khác mà người dùng chưa kịp xem, metric HitRate@20 vẫn bị tính là 0 (miss).
2. **Không kết luận vội vàng về Matrix Factorization:**
   - Kết quả này chứng minh rằng **Explicit ALS với hàm mục tiêu RMSE thô sơ (unconstrained raw dot-product without shrinkage)** không phù hợp cho bài toán xếp hạng Top-N trên dữ liệu cực thưa (sparsity 99.75%).
   - Nó không có nghĩa là các biến thể Implicit Feedback (như iALS với confidence weighting, BPR, hoặc mô hình Hybrid kết hợp KG) không thể đạt hiệu năng cao.

---

## 6. THỜI GIAN THỰC THI VÀ TÀI NGUYÊN BỘ NHỚ (RUNTIME & PERFORMANCE)

Trích xuất từ [`artifacts/als/m08/m08_runtime_diagnostics.json`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m08/m08_runtime_diagnostics.json):
- **Thời gian quét dữ liệu (Train + Val + Test):** ~31.0 giây bằng PyArrow (tổng cộng hơn 25 triệu dòng).
- **Thời gian sinh gợi ý Popularity Count:** 6.29 giây cho 111.211 users (~17.680 users/giây).
- **Thời gian sinh gợi ý Popularity Weighted:** 4.90 giây cho 111.211 users (~22.690 users/giây).
- **Thời gian sinh gợi ý Frozen ALS (Matrix Multiplication theo lô 2.500 users):** 130.64 giây cho 111.211 users (~851.3 users/giây).
- **Thời gian đánh giá TopNEvaluator:** ~1.2 giây/mô hình.
- **Tổng thời gian chạy toàn bộ M08 Pipeline:** **184.23 giây (khoảng 3.0 phút)**.
- **Mức tiêu thụ RAM đỉnh:** Dưới 1.2 GB nhờ cơ chế xử lý theo batch giới hạn và giải phóng bộ nhớ chủ động sau mỗi mẻ tính toán.

---

## 7. KẾT LUẬN VÀ BÀN GIAO CHO M09

```text
================================================================================
                    M08 FINAL OFFLINE BENCHMARK VERDICT
================================================================================
VERDICT: M08_ACCEPTANCE_PASS
TEST SPLIT EVALUATION: COMPLETED IN SINGLE SHOT (111,211 POSITIVE TEST USERS)
FAIRNESS & ZERO-LEAKAGE: FULLY VERIFIED (SEEN FILTER = TRAIN ∪ VALIDATION)
WINNING BENCHMARK MODEL: M03_POPULARITY_COUNT (HR@10 = 0.05357, NDCG@10 = 0.02721)
FROZEN ALS CHAMPION RESULT: HR@10 = 0.00001 (1 HIT / 111,211 USERS)
READINESS: READY FOR M09 (COLD-START & SCALING PROFILING)
================================================================================
```

