# MoodGraph Task 3A – Module M02: Top-N Evaluation Engine Report

## 1. Mục tiêu & Phạm vi Nghiệm thu (Scope & Objectives)

- **Module**: M02 – Top-N Evaluation Engine & Hand-Calculated Tests
- **Dự án**: MoodGraph – Hybrid Recommendation System (MovieLens 25M)
- **Branch**: `feature/als-3a`
- **Mục tiêu cốt lõi**:
  - Xây dựng bộ công cụ đánh giá ngoại tuyến (Offline Evaluation Engine) độc lập, chính xác tuyệt đối về toán học, không phụ thuộc vào cấu trúc bên trong của mô hình gợi ý (ALS, Popularity, Knowledge Graph hay Hybrid).
  - Khóa chặt thước đo và giao thức đánh giá **trước khi** bước vào huấn luyện các mô hình, ngăn chặn hoàn toàn rủi ro lựa chọn thước đo thiên vị theo kết quả sau huấn luyện.
  - Kiểm thử đầy đủ các trường hợp biên và đối chiếu tính tay 21 bài kiểm tra độc lập.
- **Phạm vi kiểm soát (Scope Boundaries)**:
  - **Không** huấn luyện mô hình ALS ở M02.
  - **Không** xây dựng Popularity Baseline ở M02 (dành riêng cho M03).
  - **Không** đọc nhãn hoặc dữ liệu của tập Test (`data/processed/splits/test`) để chọn mô hình (chỉ dùng dữ liệu giả lập synthetic để kiểm tra logic lọc ứng viên).

---

## 2. Định nghĩa Toán học các Chỉ số Đánh giá (Metrics Mathematical Formulations)

Trong giao thức chính **User-wise Leave-1-Last** của MoodGraph:
- Mỗi người dùng u có chính xác **1 tương tác Validation được giữ lại** với phim mục tiêu m* và điểm đánh giá r*.
- Ngưỡng quan tâm tích cực (Relevance Threshold): `r* >= 3.5`.
- Khi đánh giá Top-K, mô hình đề xuất danh sách K bộ phim có thứ tự: `[m_1, m_2, ..., m_K]`.

### 2.1. Hit Rate@K (HR@K)
- **Ý nghĩa**: Đo lường liệu phim mục tiêu có nằm trong danh sách Top-K đề xuất hay không.
- **Công thức**:
  ```text
  HR@K = 1.0  nếu m* thuộc {m_1, ..., m_K} (với rank j <= K)
  HR@K = 0.0  nếu m* không thuộc {m_1, ..., m_K}
  ```

### 2.2. Recall@K
- **Ý nghĩa**: Tỷ lệ các mục tiêu tích cực quan sát được mà hệ thống tìm lại được.
- **Công thức**:
  Do mỗi người dùng trong nhóm mục tiêu tích cực chỉ có duy nhất 1 tương tác tích cực quan sát được (mẫu số bằng 1):
  ```text
  Recall@K = (Số mục tiêu tích cực trúng trong Top-K) / (Tổng số mục tiêu tích cực quan sát được)
  Recall@K = 1.0 / 1.0 = 1.0  nếu trúng (hit = 1)
  Recall@K = 0.0 / 1.0 = 0.0  nếu trượt (hit = 0)
  ```
  > [!NOTE]
  > Trong giao thức 1-held-out target, giá trị của Recall@K trùng khớp với HitRate@K trên từng cá nhân người dùng.

### 2.3. Precision@K
- **Ý nghĩa**: Tỷ lệ vị trí trong Top-K chứa phim mục tiêu quan sát được.
- **Công thức**:
  ```text
  Precision@K = (Số mục tiêu trúng trong Top-K) / K
  Precision@K = 1.0 / K  nếu trúng (hit = 1)
  Precision@K = 0.0      nếu trượt (hit = 0)
  ```
  > [!IMPORTANT]
  > Mẫu số của Precision@K **LUÔN LUÔN là K**. Tuyệt đối không được rút ngắn mẫu số khi danh sách gợi ý ngắn hơn K (ví dụ nếu danh sách chỉ có 2 phim và trúng 1 phim, Precision@5 vẫn là 1/5 = 0.2, không được tính thành 1/2 = 0.5).

### 2.4. Normalized Discounted Cumulative Gain@K (NDCG@K)
- **Ý nghĩa**: Đánh giá vị trí xếp hạng của đề xuất đúng, phạt nặng các đề xuất đúng nhưng đứng ở vị trí cuối bảng.
- **Công thức**:
  - Với 1 mục tiêu duy nhất, danh sách lý tưởng xếp m* ở vị trí 1:
    ```text
    IDCG@K = 1.0 / log2(1 + 1) = 1.0 / log2(2) = 1.0
    ```
  - Nếu m* xuất hiện tại vị trí thứ tự j (với 1 <= j <= K):
    ```text
    DCG@K = 1.0 / log2(j + 1)
    NDCG@K = DCG@K / IDCG@K = 1.0 / log2(j + 1)
    ```
  - Nếu m* không xuất hiện trong Top-K: `NDCG@K = 0.0`.
  - Giá trị cụ thể theo các thứ hạng đầu:
    - Vị trí 1: `1.0 / log2(2) = 1.000000`
    - Vị trí 2: `1.0 / log2(3) ≈ 0.630930`
    - Vị trí 3: `1.0 / log2(4) = 0.500000`
    - Vị trí 4: `1.0 / log2(5) ≈ 0.430677`
    - Vị trí 5: `1.0 / log2(6) ≈ 0.386853`

### 2.5. Mean Reciprocal Rank@K (MRR@K)
- **Ý nghĩa**: Nghịch đảo thứ hạng đầu tiên tìm thấy mục tiêu.
- **Công thức**:
  - Nếu m* xuất hiện tại vị trí j (1 <= j <= K): `MRR@K = 1.0 / j`.
  - Nếu m* không xuất hiện: `MRR@K = 0.0`.

### 2.6. Catalog Coverage@K
- **Ý nghĩa**: Tỷ lệ danh mục phim được mô hình khai thác và đề xuất tới người dùng, đo lường mức độ đa dạng danh mục và khả năng chống co cụm vào nhóm phim phổ biến.
- **Công thức**:
  ```text
  Catalog Coverage (Full) = |Hợp các phim Top-K của mọi user| / |Toàn bộ danh mục phim|
  Catalog Coverage (Scorable) = |Hợp các phim Top-K của mọi user| / |Số phim có thể chấm điểm|
  ```

---

## 3. Quy tắc Positive-Target Cohort & Cách Tính Mẫu Số

### 3.1. Phân định Nhóm Mục tiêu Tích cực (Positive Cohort)
- Một tương tác kiểm định được xem là mục tiêu tích cực khi và chỉ khi `rating >= 3.5`.
- **Nếu user có `rating < 3.5`**: Điều này phản ánh user không thích hoặc đánh giá thấp bộ phim đó. Trong giao thức 1-held-out target, ta không có bất kỳ bộ phim tích cực nào được quan sát cho user này.
- **Quy tắc toán học**:
  - Khi không có ground-truth positive, Recall@K và NDCG@K không xác định (mẫu số bằng 0).
  - Không được tự gán Recall hay NDCG bằng 0 rồi cộng vào mẫu số của nhóm mục tiêu tích cực.
  - Nhóm user này được tách riêng thành `non_positive_cohort` và ghi nhận trong thống kê phụ chẩn đoán (`diagnostic_all_users`).
  - Mẫu số chính (`positive_cohort_size`) để tính trung bình các chỉ số chất lượng gợi ý chỉ gồm các user có `rating >= 3.5`.

### 3.2. Bảo toàn Mẫu số khi Mô hình Thiếu Dự đoán (No Selective Dropping)
- Nếu user thuộc `positive_cohort` nhưng mô hình không sinh được đề xuất (danh sách rỗng `[]` hoặc user không có trong output dự đoán):
  - User đó nhận điểm số: `HR=0.0, Recall=0.0, Precision=0.0, NDCG=0.0, MRR=0.0`.
  - User đó **BẮT BUỘC ĐƯỢC GIỮ NGUYÊN TRONG MẪU SỐ** `positive_cohort_size`.
  - Tuyệt đối không được loại bỏ user này để làm đẹp chỉ số.

---

## 4. Quy tắc Sắp xếp & Lọc Không gian Ứng viên (Candidate Pool Rules)

### 4.1. Quy tắc Sắp xếp & Giải quyết Điểm Bằng Nhau (Tie-Breaking)
Khi sắp xếp các ứng viên dựa trên điểm số `raw_score`:
1. Sắp xếp giảm dần theo điểm số: `raw_score DESC`.
2. Nếu điểm số bằng nhau, sắp xếp tăng dần theo ID phim: `movieId ASC`.
3. Kiểm tra tính hữu hạn: Nếu `raw_score` chứa giá trị `NaN`, `+Inf` hoặc `-Inf`, hệ thống sẽ kích hoạt ngoại lệ `ValueError`.

### 4.2. Quy tắc Lọc Phim Đã Tương tác (Seen-Items Filtering)
- **Khi đánh giá trên tập Validation**:
  - Không gian ứng viên loại bỏ toàn bộ các phim user đã xem trong tập Train:
    `Candidate_Pool(u) = Catalog \ Train_u`
- **Khi đánh giá trên tập Test**:
  - Không gian ứng viên loại bỏ toàn bộ các phim user đã xem trong cả tập Train và Validation:
    `Candidate_Pool(u) = Catalog \ (Train_u U Val_u)`
- Bộ đánh giá tích hợp hàm [`validate_candidate_pool`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/evaluator.py) nhằm phát hiện ngay lập tức nếu xuất hiện phim đã xem lọt vào danh sách gợi ý.

---

## 5. Kết quả Kiểm thử Tính tay Độc lập (Hand-Calculated Test Suite)

Tất cả **21/21** bài kiểm tra trong [`tests/als/test_evaluator.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_evaluator.py) đã chạy và đạt 100% PASS:

| Test ID | Tình huống Kiểm thử (Test Case Scenario) | Kỳ vọng Tính tay (Hand-Calculated Expected) | Kết quả Thực tế (Observed) | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| `test_01` | Phim tích cực tại vị trí 1 trong Top-5 | HR=1, Recall=1, P=0.2, NDCG=1.0, MRR=1.0 | HR=1.0, Recall=1.0, P=0.2, NDCG=1.0, MRR=1.0 | PASS |
| `test_02` | Phim tích cực tại vị trí 3 trong Top-5 | HR=1, Recall=1, P=0.2, NDCG=0.5, MRR=0.3333 | HR=1.0, Recall=1.0, P=0.2, NDCG=0.5, MRR=0.3333 | PASS |
| `test_03` | Phim tích cực tại vị trí cuối K=5 | HR=1, Recall=1, P=0.2, NDCG=1/log2(6)=0.3869, MRR=0.2 | HR=1.0, Recall=1.0, P=0.2, NDCG=0.3869, MRR=0.2 | PASS |
| `test_04` | Phim tích cực không xuất hiện trong Top-K | HR=0, Recall=0, P=0, NDCG=0, MRR=0 | HR=0.0, Recall=0.0, P=0.0, NDCG=0.0, MRR=0.0 | PASS |
| `test_05` | Phim xuất hiện tại vị trí K+1 (rank 6 cho K=5) | K=5: Miss (0.0); K=10: Hit tại rank 6 (NDCG=0.3562) | Khớp hoàn toàn tính tay | PASS |
| `test_06` | User có rating Validation = 2.0 | Loại khỏi mẫu số positive-cohort, đếm vào non-pos | pos_size=0, non_pos_size=1 | PASS |
| `test_07` | User có rating Validation = 3.5 (ngưỡng) | Tính vào positive-cohort | pos_size=1, non_pos_size=0, HR=1.0 | PASS |
| `test_08` | User có target nhưng danh sách gợi ý rỗng `[]` | Tính là miss (0.0), giữ nguyên trong mẫu số pos | pos_size=1, HR=0.0, missing_recs=1 | PASS |
| `test_09` | User không có mặt trong dict dự đoán | Tính là miss (0.0), giữ nguyên trong mẫu số pos | pos_size=1, HR=0.0, missing_recs=1 | PASS |
| `test_10` | Danh sách gợi ý trùng lặp `movieId` | Phát hiện lỗi và ném ValueError | ValueError: Duplicate movieId | PASS |
| `test_11` | Hai phim bằng điểm số | Tie-break ổn định: `movieId ASC` | Thứ tự ưu tiên chính xác theo ID tăng dần | PASS |
| `test_12` | Điểm số chứa NaN hoặc Inf | Phát hiện lỗi và ném ValueError | ValueError: must be finite | PASS |
| `test_13` | K không hợp lệ (K=0, K=-5, K=float) | Phát hiện lỗi và ném ValueError | ValueError: strictly positive integer | PASS |
| `test_14` | Danh sách gợi ý ngắn hơn K (dài 2, K=5) | Mẫu số Precision luôn là K=5 (1/5=0.2, không phải 1/2) | Precision = 0.2 | PASS |
| `test_15` | Catalog Coverage trên nhiều user | Hợp các phim không đếm trùng, chia đúng catalog_size | Coverage tính đúng 4/10 = 40.0% | PASS |
| `test_16` | Lọc ứng viên Validation loại Train | Loại trừ chính xác phim Train, báo leak nếu vi phạm | Leak detected & filtered | PASS |
| `test_17` | Lọc ứng viên Test synthetic | Loại trừ cả Train và Validation | Seen items removed | PASS |
| `test_18` | Phim mục tiêu cold-start không chấm điểm được | Tính là miss (0.0), không xóa khỏi mẫu số | pos_size=1, hit_count=0, HR=0.0 | PASS |
| `test_19` | Phân biệt mẫu số Positive Cohort vs All Users | Positive HR = 1/2 = 0.5; Diagnostic All HR = 1/4 = 0.25 | pos_HR=0.5, all_HR=0.25 | PASS |
| `test_20` | Tính tất định & khả năng tái lập | Đánh giá lặp lại 3 lần cho kết quả giống hệt 100% | Bit-for-bit identical | PASS |
| `test_21` | Đánh giá đa mốc K (K=5, 10, 20) trong 1 lần chạy | Khớp hoàn toàn chỉ số tại từng mốc K | Multi-K evaluation verified | PASS |

---

## 6. Kết quả Kiểm tra trên Tập Validation Thực tế (Stage V)

Thông qua script kiểm định thực tế [`scripts/verify_m02_evaluator.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/scripts/verify_m02_evaluator.py):

| Thuộc tính Tập Validation Thực tế | Giá trị Quan sát (Observed) | Tỷ lệ (%) | Trạng thái Xác minh |
| :--- | :--- | :--- | :--- |
| Tổng số lượt đánh giá Validation | **162,541** | 100.00% | VERIFIED (Khớp 100% Manifest) |
| Số lượng người dùng độc lập | **162,541** | 100.00% | VERIFIED (Chính xác 1 tương tác/user) |
| Mục tiêu Tích cực (`rating >= 3.5`) | **109,779** | **67.54%** | VERIFIED (`positive_cohort_size`) |
| Mục tiêu Không tích cực (`rating < 3.5`) | **52,762** | **32.46%** | VERIFIED (`non_positive_cohort_size`) |
| Tổng danh mục phim MovieLens 25M | **62,423** | - | VERIFIED (`catalog_size`) |

---

## 7. Giới hạn Khoa học & Các Lưu ý cho M03, M06, M08

1. **Giới hạn của Giao thức 1-Held-Out Target (Leave-1-Last)**:
   - Giao thức chỉ đo lường khả năng mô hình tìm lại đúng 1 bộ phim mà người dùng thực tế đã xem và thích.
   - Nó không thể khẳng định người dùng sẽ ghét toàn bộ hàng nghìn bộ phim khác chưa từng xem.
   - Precision@K trong bài toán này bị chặn trên bởi `1/K` (Precision@10 tối đa chỉ là 0.10). Do đó, chỉ số phản ánh tỷ lệ phát hiện mục tiêu quan sát, không phản ánh chất lượng toàn bộ K vị trí.
2. **Khóa Chỉ số Đánh giá Chính cho ALS Tuning (M07)**:
   - Đề xuất khóa chính thức **`NDCG@10`** làm chỉ số tối ưu hóa chính cho quá trình tuning mô hình ALS ở Module M07.
3. **Hiệu năng Bộ nhớ trong Khâu Đánh giá Quy mô Lớn (M06, M08)**:
   - Với 109,779 users trong positive cohort, việc sinh ma trận dự đoán Top-K cần thực hiện theo batch (ví dụ: batch 5,000–10,000 users) để tránh tiêu tốn RAM vượt ngưỡng 16 GB của máy trạm.

---

## 8. Các Câu hỏi Bản chất dành cho Chủ dự án (Learning Check)

1. **Tại sao RMSE tốt chưa chắc đem lại kết quả Top-N tốt?**
   - *Trả lời*: RMSE tối ưu hóa sai số trung bình trên toàn bộ các mức điểm (kể cả dự đoán 1.5 thành 2.0). Trong khi đó, Top-N chỉ quan tâm đến thứ tự xếp hạng ở các vị trí đầu bảng (top 10 phim cao nhất). Một mô hình có thể dự đoán sai lệch điểm số tuyệt đối nhưng xếp đúng thứ tự phim yêu thích lên đầu vẫn đạt Top-N xuất sắc.
2. **Sự khác nhau giữa NDCG và Hit Rate là gì?**
   - *Trả lời*: Hit Rate chỉ quan tâm mục tiêu có xuất hiện trong Top-K hay không (nhị phân 0 hoặc 1). NDCG quan tâm sâu sắc đến vị trí xuất hiện: trúng ở vị trí 1 (NDCG=1.0) có giá trị cao hơn rất nhiều so với trúng ở vị trí 10 (NDCG≈0.289).
3. **Vì sao Recall và Hit Rate trên 1 held-out positive target lại giống nhau?**
   - *Trả lời*: Bởi vì tổng số phim tích cực cần tìm kiếm chỉ là 1. Nếu tìm thấy (Hit = 1) thì tỷ lệ tìm thấy là 1/1 = 100% (Recall = 1). Nếu không tìm thấy (Hit = 0) thì Recall = 0/1 = 0%.
4. **Có thể coi các phim người dùng chưa xem là phim bị ghét không?**
   - *Trả lời*: Tuyệt đối không. Trong hệ thống gợi ý, đa số phim chưa xem là do người dùng chưa biết đến sự tồn tại của chúng (unobserved interaction), không phải là tín hiệu tiêu cực (negative feedback).

---

## 9. Kết luận Nghiệm thu Kỹ thuật

- Toàn bộ module [`recommender/als/evaluator.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/evaluator.py) và bộ kiểm thử [`tests/als/test_evaluator.py`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_evaluator.py) đã hoàn thành, vượt qua **40/40 tests** của toàn hệ thống mà không có bất kỳ xung đột hay lỗi hồi quy nào.
- Trạng thái nghiệm thu: **`M02_ENGINEERING_PASS`** (Đã kiểm chứng đầy đủ).
- Sẵn sàng bàn giao cho Mentor và chuyển tiếp sang **Module M03: Global Popularity Baseline**.
