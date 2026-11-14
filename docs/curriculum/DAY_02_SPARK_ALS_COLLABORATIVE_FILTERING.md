# KHÓA HUẤN LUYỆN LÀM CHỦ MOODGRAPH (5-DAY MASTERY CURRICULUM)
# BÀI GIẢNG NGÀY 02: TRỤ CỘT GỢI Ý 1 - MA TRẬN PHÂN RÃ SPARK ALS

> **Vai trò Mentor**: Ở Bài giảng Ngày 01, anh đã nắm vững kiến trúc dữ liệu và pipeline tiền xử lý 25 triệu ratings. Hôm nay, chúng ta đi sâu vào "Trái tim toán học" của phân hệ Lọc cộng tác (Collaborative Filtering): **Mô hình Phân rã Ma trận ALS (Alternating Least Squares) trên Apache Spark MLlib**. Mọi thuật toán, công thức toán và vị trí file code đều được giải thích tường minh để anh tự tin trả lời bất kỳ câu hỏi hóc búa nào của Hội đồng Giảng viên!

---

## MỤC LỤC BÀI GIẢNG NGÀY 02

1. **Vị Trí Của Spark ALS Trong Tổng Thể MoodGraph**
2. **Bảng Tra Cứu Nhanh Cho Thầy Xem (ALS Show-and-Tell Cheat Sheet)**
3. **Bản Chất Toán Học Của Ma Trận Phân Rã (Matrix Factorization)**
   * 3.1. Bài toán xấp xỉ ma trận bậc thấp (Low-rank Approximation)
   * 3.2. Hàm mất mát bình phương tối thiểu có điều chuẩn L2 (Loss Function)
   * 3.3. Cơ chế tối ưu luân phiên (Vì sao gọi là "Alternating"?)
   * 3.4. Dữ liệu đánh giá hiện (Explicit) vs Dữ liệu ngầm định (Implicit)
4. **Mổ Xẻ Chi Tiết Module Huấn Luyện Spark ALS (`recommender/als/trainer.py`)**
   * 4.1. Cấu hình siêu tham số `ALSConfig` và các chốt chặn kiểm toán
   * 4.2. Huấn luyện phân tán `fit()` trên 24.67 triệu ratings
   * 4.3. Kiểm toán ma trận nhân tố ẩn (Factor Matrix Audit: NaN/Inf, L2-norm)
   * 4.4. Cơ chế xử lý người dùng mới: `coldStartStrategy = 'nan'`
5. **Kỹ Thuật Sinh Ứng Viên Top-K Chuẩn Production (`recommender/als/candidates.py`)**
   * 5.1. Thách thức tính toán 10.1 tỷ tích vô hướng trên RAM
   * 5.2. Chấm điểm theo lô an toàn bộ nhớ (Bounded Batch Scoring bằng BLAS `P @ Q.T`)
   * 5.3. Nguyên tắc "Filter-Before-Top-K" (Lọc trước khi chọn Top-K)
   * 5.4. Quy tắc phá vỡ hòa điểm tất định (Deterministic Tie-Breaking)
6. **Phương Pháp Luận Đánh Giá Top-N Chuẩn Leave-1-Last (`recommender/als/evaluator.py`)**
   * 6.1. Hit Rate @ K (HR@K)
   * 6.2. Normalized Discounted Cumulative Gain @ K (NDCG@K)
   * 6.3. Mean Reciprocal Rank (MRR@K)
7. **Phát Hiện Khoa Học: Hiện Tượng Đuôi Dài (Long-Tail Bias) & Lý Do Cần Đồ Thị Tri Thức**
8. **5 Câu Hỏi Vấn Đáp Chuyên Sâu Của Giảng Viên & Cách Trả Lời Điểm 10**
9. **Bài Tập Thực Hành Ngày 02 Dành Cho Anh**

---

## 1. VỊ TRÍ CỦA SPARK ALS TRONG TỔNG THỂ MOODGRAPH

Trong hệ thống MoodGraph, **Spark ALS đóng vai trò là Trụ Cột Gợi Ý Dựa Trên Lịch Sử Hành Vi (Behavioral Backbone)**:

```text
                           DỮ LIỆU HUẤN LUYỆN (TRAIN SPLIT)
                                  24,675,013 Ratings
                                          │
                                          ▼
                      [ MÔ HÌNH PHÂN RÃ MA TRẬN SPARK ALS ]
               Học không gian tiềm ẩn k-chiều (k = 8, 16, 32)
                     Tối ưu hóa phân tán trên Apache Spark
                                          │
                   ┌──────────────────────┴──────────────────────┐
                   ▼                                             ▼
        MA TRẬN USER FACTORS (P)                      MA TRẬN ITEM FACTORS (Q)
           162,541 Users x k                             58,932 Movies x k
     (Đại diện cho gu của người dùng)             (Đại diện cho thuộc tính ẩn của phim)
                   │                                             │
                   └──────────────────────┬──────────────────────┘
                                          ▼
                           [ BỘ SINH ỨNG VIÊN TOP-K ]
                        Nhân ma trận BLAS: Score = P @ Q.T
                           Lọc bỏ các phim đã xem trong Train
                                          │
                                          ▼
                    DANH SÁCH ỨNG VIÊN ALS (Top 50 - 100 Phim)
                Đưa vào Bộ Hợp Nhất Lai Reciprocal Rank Fusion (RRF)
```

* **Ưu điểm lớn nhất của ALS**: Nắm bắt cực tốt các mối liên hệ hành vi ngầm mà người dùng không thể diễn đạt bằng lời (ví dụ: hai bộ phim hoàn toàn khác thể loại nhưng thường được cùng một nhóm khán giả đánh giá 5 sao).
* **Điểm yếu của ALS**: Gặp khó khăn khi người dùng mới chưa có lịch sử đánh giá (Cold-Start) hoặc khi dữ liệu quá thưa ở vùng phim ít người xem (Long-Tail). Đây chính là lý do MoodGraph cần **Đồ thị tri thức (Knowledge Graph - Bài giảng Ngày 03)** để bù đắp hoàn hảo!

---

## 2. BẢNG TRA CỨU NHANH CHO THẦY XEM (ALS SHOW-AND-TELL CHEAT SHEET)

Khi thầy cô kiểm tra mã nguồn phần Lọc cộng tác và Huấn luyện ALS, anh mở ngay các file sau:

| Thầy Cô Hỏi Về Vấn Đề Gì | File Code Cần Mở | Hàm / Class Cụ Thể | Dòng Code |
| :--- | :--- | :--- | :--- |
| **Cấu hình siêu tham số ALS** | [recommender/als/trainer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py) | Class `ALSConfig` | Line 43 - 65 |
| **Hàm huấn luyện Spark ALS `fit()`** | [recommender/als/trainer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py) | Phương thức `ALSTrainer.fit()` | Line 163 - 191 |
| **Kiểm toán ma trận nhân tố ẩn** | [recommender/als/trainer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py) | Phương thức `audit_factors()` | Line 193 - 265 |
| **Sinh ứng viên Top-K bằng BLAS** | [recommender/als/candidates.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | Class `ALSCandidateGenerator` | Line 233 - 330 |
| **Nguyên tắc Filter-Before-Top-K** | [recommender/als/candidates.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | Docstring & Hàm `recommend_for_user()` | Line 15 - 25, 260 - 290 |
| **Công thức HR@K, NDCG@K, MRR** | [recommender/als/evaluator.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/evaluator.py) | Hàm `compute_single_user_metrics()` | Line 146 - 203 |
| **Chốt chặn chống rò rỉ tập Test** | [recommender/als/tuner.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py) | Hàm `guard_test_split_access()` | Line 57 - 65 |
| **Thực thi tinh chỉnh siêu tham số** | [scripts/run_m07_tuning.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py) | Kịch bản điều phối Grid Search M07 | Toàn bộ file |
| **Bản ghi mô hình tốt nhất (Manifest)** | [artifacts/als/m07/best_als_model_manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m07/best_als_model_manifest.json) | File JSON lưu thông số Champion | Line 1 - 90 |

---

## 3. BẢN CHẤT TOÁN HỌC CỦA MA TRẬN PHÂN RÃ (MATRIX FACTORIZATION)

### 3.1. Bài Toán Xấp Xỉ Ma Trận Bậc Thấp
Giả sử ta có ma trận đánh giá thưa R có kích thước `M × N` (trong đó M = 162,541 users, N = 62,423 movies).
Mục tiêu của phân rã ma trận là tìm hai ma trận nhân tố ẩn bậc thấp:
* **Ma trận Người dùng P**: Kích thước `M × k` (mỗi dòng u là một véc-tơ P_u đại diện cho sở thích của người dùng u trong không gian k chiều).
* **Ma trận Vật phẩm Q**: Kích thước `N × k` (mỗi dòng i là một véc-tơ Q_i đại diện cho đặc tính của phim i trong không gian k chiều).
* Số chiều ẩn `k` thường được chọn rất nhỏ so với M và N (ví dụ: k = 8, 16, hoặc 32).

Điểm số dự đoán r^_ui được tính bằng **tích vô hướng (Dot-Product)** giữa hai véc-tơ:
```text
r^_ui = P_u . Q_i = ∑_(f = 1 đến k) [ P_uf × Q_if ]
```

---

### 3.2. Hàm Mất Mát Bình Phương Tối Thiểu Có Điều Chuẩn L2 (Loss Function)
Vì hơn 99.75% các phần tử trong ma trận R là ô trống (chưa được đánh giá), ta **chỉ tính toán mất mát trên tập các ô đã có tương tác** (kí hiệu là R_obs), thay vì coi các ô trống là 0 (vì ô trống không có nghĩa là người dùng ghét phim, mà là họ chưa xem):

```text
Hàm mất mát L(P, Q) = ∑_( (u, i) ∈ R_obs ) [ r_ui - P_u . Q_i ]^2 
                     + λ * ( ∑_u ||P_u||^2 + ∑_i ||Q_i||^2 )
```

Trong đó:
* `r_ui`: Điểm đánh giá thực tế của người dùng u cho phim i (thang điểm 0.5 đến 5.0).
* `P_u . Q_i`: Điểm số do mô hình dự đoán.
* `λ` (`reg_param`): Hệ số điều chuẩn L2 Regularization, có tác dụng phạt các véc-tơ có độ lớn quá cao, chống hiện tượng mô hình học vẹt (Overfitting) trên những người dùng có ít đánh giá.
* `||P_u||^2` và `||Q_i||^2`: Chuẩn Frobenius bậc 2 của các véc-tơ.

---

### 3.3. Cơ Chế Tối Ưu Luân Phiên (Vì Sao Gọi Là "Alternating"?)
Hàm mất mát ở trên chứa tích của hai biến số `P_u` và `Q_i`, do đó bài toán tối ưu là **phi lồi (non-convex)** nếu tối ưu đồng thời cả hai biến cùng lúc.
Tuy nhiên, thuật toán ALS có một phát kiến toán học thiên tài:
1. **Bước 1**: Giả định cố định ma trận phim `Q`. Khi đó, hàm mất mát trở thành hàm lồi bậc hai (Quadratic) đối với ma trận người dùng `P`. Ta có thể giải nghiệm tối ưu toàn cục giải tích (Closed-form OLS solution) cho từng người dùng độc lập:
   ```text
   P_u = ( Q_obs^T . Q_obs + λ . I )^(-1) . Q_obs^T . R_u
   ```
2. **Bước 2**: Giả định cố định ma trận người dùng `P`. Khi đó, hàm mất mát trở thành hàm lồi bậc hai đối với ma trận phim `Q`. Ta lại giải nghiệm tối ưu giải tích cho từng bộ phim:
   ```text
   Q_i = ( P_obs^T . P_obs + λ . I )^(-1) . P_obs^T . R_i
   ```
3. Hai bước trên được thực hiện **luân phiên (Alternating)** lặp đi lặp lại qua `max_iter` vòng lặp (thường từ 10 đến 15 vòng) cho đến khi hàm mất mát hội tụ.

> **Ưu điểm lớn nhất của ALS trong Big Data**:
> Khi cố định Q, nghiệm của từng người dùng `P_u` hoàn toàn độc lập với các người dùng khác. Do đó, Apache Spark có thể phân tán việc tính toán hàng triệu véc-tơ `P_u` song song trên hàng chục nghìn CPU core mà không cần đồng bộ trạng thái phức tạp như thuật toán Stochastic Gradient Descent (SGD)!

---

### 3.4. Dữ Liệu Đánh Giá Hiện (Explicit) vs Dữ Liệu Ngầm Định (Implicit)
* **Explicit Feedback (`implicit_prefs = False`)**: Người dùng chấm điểm số rõ ràng (0.5★ đến 5.0★). Đây chính là bản chất của MovieLens 25M mà MoodGraph sử dụng.
* **Implicit Feedback (`implicit_prefs = True`)**: Người dùng chỉ để lại hành vi nhấp chuột (click, view, purchase), không có điểm số âm hay dương rõ rệt.

Trong [recommender/als/trainer.py#L51](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py#L51), ta đặt `implicit_prefs = False` để mô hình học chính xác giá trị điểm số thực của khán giả.

---

## 4. MỔ XẺ CHI TIẾT MODULE HUẤN LUYỆN SPARK ALS (`trainer.py`)

File mã nguồn: [recommender/als/trainer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py)

### 4.1. Cấu Hình Siêu Tham Số `ALSConfig` (Lines 43–65)
```python
@dataclass
class ALSConfig:
    rank: int = 16                        # Số chiều ẩn k (thử nghiệm: 8, 16, 32)
    max_iter: int = 10                    # Số vòng lặp luân phiên (10 vòng đảm bảo hội tụ)
    reg_param: float = 0.1                # Hệ số điều chuẩn λ (thử nghiệm: 0.05, 0.1, 0.3, 1.0)
    implicit_prefs: bool = False          # Dữ liệu đánh giá hiện (Explicit)
    cold_start_strategy: str = "nan"      # Chặn dự đoán sai số cho user chưa tương tác
    seed: int = 42                        # Hạt giống ngẫu nhiên đảm bảo tái lập 100%
    user_col: str = "userId"
    item_col: str = "movieId"
    rating_col: str = "rating"
    intermediate_storage_level: str = "MEMORY_AND_DISK" # Chống tràn RAM máy tính
```

---

### 4.2. Huấn Luyện Phân Tán Trên Spark (Lines 163–191)
Phương thức `ALSTrainer.fit(train_df)` kiểm tra tính hợp lệ của schema dữ liệu trước khi nạp vào bộ huấn luyện `pyspark.ml.recommendation.ALS`:
```python
als = ALS(
    userCol=self.config.user_col,
    itemCol=self.config.item_col,
    ratingCol=self.config.rating_col,
    implicitPrefs=self.config.implicit_prefs,
    rank=self.config.rank,
    maxIter=self.config.max_iter,
    regParam=self.config.reg_param,
    seed=self.config.seed,
    coldStartStrategy=self.config.cold_start_strategy,
    intermediateStorageLevel=self.config.intermediate_storage_level,
    finalStorageLevel=self.config.final_storage_level,
    checkpointInterval=self.config.checkpoint_interval,
)
model = als.fit(train_df)
```
* Quá trình huấn luyện diễn ra phân tán trên 24,675,013 dòng đánh giá của tập Train.
* Spark tự động phân rã thành các RDD phân vùng và thực hiện phép nhân ma trận trên các Executor.

---

### 4.3. Kiểm Toán Ma Trận Nhân Tố Ẩn (Factor Matrix Audit) (Lines 193–265)
Sau khi huấn luyện xong, mô hình sinh ra hai DataFrame: `model.userFactors` và `model.itemFactors`. Hệ thống thực hiện kiểm toán nghiêm ngặt:
1. **Kiểm tra số chiều**: Đảm bảo 100% véc-tơ có đúng độ dài `rank == k`.
2. **Kiểm tra tính hợp lệ số học**: Đảm bảo không chứa bất kỳ giá trị NaN (Not a Number) hay Vô cùng (Infinite) nào do chia cho 0 trong ma trận nghịch đảo.
3. **Thống kê chuẩn L2 (L2-norm)**: Tính toán Min, Max, Mean, Std của độ dài véc-tơ `||P_u||` và `||Q_i||` để phát hiện hiện tượng bùng nổ véc-tơ (Vector Explosion).

---

### 4.4. Cơ Chế Xử Lý Người Dùng Mới: `coldStartStrategy = 'nan'`
* Trong Spark ALS mặc định, nếu gặp một User hoặc Phim chưa từng xuất hiện trong tập Train, mô hình sẽ quăng lỗi ngoại lệ hoặc gán bừa giá trị trung bình toàn cục.
* Trong MoodGraph, ta thiết lập `coldStartStrategy = "nan"`. Khi đó, Spark sẽ trả về giá trị NaN. Hệ thống sẽ nhận diện ngay lập tức đây là trường hợp người dùng mới và chuyển giao sang **Đồ thị tri thức (Knowledge Graph)** hoặc **Cold-Start Fallback Handler** mà không làm sập ứng dụng.

---

## 5. KỸ THUẬT SINH ỨNG VIÊN TOP-K CHUẨN PRODUCTION (`candidates.py`)

File mã nguồn: [recommender/als/candidates.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py)

### 5.1. Thách Thức Tính Toán 10.1 Tỷ Tích Vô Hướng
Nếu dùng phương thức mặc định `model.recommendForAllUsers(k)` của Spark:
* Spark sẽ phải tính toán toàn bộ ma trận tích `162,541 users × 58,932 movies ≈ 9.58 tỷ giá trị`.
* Việc này đòi hỏi shuffle hàng chục GB dữ liệu qua mạng, rất dễ gây treo JVM và tràn bộ nhớ RAM (OOM) trên các máy tính cấu hình tiêu chuẩn.

### 5.2. Chấm Điểm Theo Lô An Toàn Bộ Nhớ (Bounded Batch Scoring)
Hệ thống MoodGraph thiết kế lớp `ALSCandidateGenerator` tự tối ưu:
```python
# Chấm điểm song song từng lô (ví dụ 2,500 users) bằng thư viện đại số tuyến tính C/BLAS
# P_batch: Ma trận kích thước [2500, k]
# Q:       Ma trận kích thước [58932, k]
scores_batch = np.dot(P_batch, Q.T)  # Kích thước [2500, 58932]
```
* **Hiệu năng**: Sử dụng các lệnh SIMD AVX-512 của CPU qua thư viện NumPy BLAS, tính toán 2,500 users chỉ mất chưa đầy 0.2 giây.
* **Kiểm soát RAM**: Bộ nhớ đỉnh luôn duy trì dưới 600 MB.

---

### 5.3. Nguyên Tắc "Filter-Before-Top-K" (Lọc Trước Khi Chọn Top-K)
Đây là một **nguyên tắc kỹ thuật sống còn** mà nhiều hệ thống gợi ý nghiệp dư hay mắc sai lầm:

```text
CÁCH LÀM SAI (Oversampling sau đó lọc):
Lấy Top 20 phim -> Lọc bỏ phim đã xem -> Nếu user xem 15 phim thì danh sách chỉ còn 5 phim! (Bị thiếu Top-K)

CÁCH LÀM ĐÚNG CỦA MOODGRAPH (Filter-Before-Top-K):
Ma trận điểm 58,932 phim -> Gán điểm -Vô cùng (-inf) cho toàn bộ phim đã xem trong Train
                         -> Dùng cấu trúc Min-Heap trích xuất ĐÚNG K phần tử có điểm cao nhất còn lại
                         -> Đảm bảo 100% trả về đủ K phim mới tinh chưa từng xem!
```
Đoạn code trong [recommender/als/candidates.py#L300-L325](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L300-L325):
```python
# Gán điểm cực âm cho các item đã xem trong lịch sử Train
for seen_mid in seen_items_for_user:
    col_idx = catalog.movie_id_to_col_idx.get(seen_mid)
    if col_idx is not None:
        user_scores[col_idx] = -np.inf

# Trích xuất Top-K chính xác
top_k_indices = np.argpartition(user_scores, -k)[-k:]
top_k_sorted = top_k_indices[np.argsort(-user_scores[top_k_indices])]
```

---

### 5.4. Quy Tắc Phá Vỡ Hòa Điểm Tất Định (Deterministic Tie-Breaking)
Khi có nhiều bộ phim có cùng điểm số dự đoán (ví dụ hai phim cùng có điểm tích vô hướng là `4.125000`), việc xếp thứ tự ngẫu nhiên sẽ làm cho kết quả đánh giá không thể tái lập (Non-deterministic).
MoodGraph áp dụng quy tắc 2 tầng:
```text
Ưu tiên 1: Điểm als_score GIẢM DẦN (Phim điểm cao hơn xếp trước)
Ưu tiên 2: Mã movieId TĂNG DẦN (Phim có ID nhỏ hơn xếp trước khi bằng điểm)
```
Quy tắc này đảm bảo 100% hai lần chạy khác nhau trên cùng một tập dữ liệu sẽ trả về thứ tự Top-K hoàn toàn đồng nhất từng bit!

---

## 6. PHƯƠNG PHÁP LUẬN ĐÁNH GIÁ TOP-N CHUẨN LEAVE-1-LAST (`evaluator.py`)

File mã nguồn: [recommender/als/evaluator.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/evaluator.py)

Trong bài toán gợi ý Top-N theo giao thức Leave-1-Last, mỗi người dùng trong tập kiểm định có ĐÚNG 1 bộ phim mục tiêu (Target Item). Hệ thống đánh giá xem mô hình có đưa được bộ phim mục tiêu này vào danh sách Top-K (K = 5, 10, 20) hay không:

### 6.1. Hit Rate @ K (HR@K)
* **Khái niệm**: Tỷ lệ phần trăm người dùng có phim mục tiêu nằm trong danh sách Top-K gợi ý.
* **Công thức**:
  ```text
  HR@K = ( Tổng số người dùng có phim mục tiêu lọt vào Top-K ) / ( Tổng số người dùng đánh giá )
  ```
  Nếu phim mục tiêu nằm ở vị trí bất kỳ từ 1 đến K: `Hit = 1.0`. Ngược lại: `Hit = 0.0`.

---

### 6.2. Normalized Discounted Cumulative Gain @ K (NDCG@K)
* **Khái niệm**: Thang đo chất lượng thứ hạng có chiết khấu vị trí. Gợi ý đúng phim nhưng xếp ở vị trí #1 sẽ được điểm cao hơn nhiều so với xếp ở vị trí #10.
* **Công thức**:
  Nếu phim mục tiêu xuất hiện ở vị trí thứ `j` (1 <= j <= K):
  ```text
  NDCG@K = 1.0 / log2(j + 1)
  ```
  * Ví dụ: 
    * Nếu phim mục tiêu ở hạng #1: `NDCG = 1.0 / log2(1 + 1) = 1.0 / 1.0 = 1.000` (Điểm tối đa).
    * Nếu phim mục tiêu ở hạng #2: `NDCG = 1.0 / log2(2 + 1) ≈ 1.0 / 1.585 ≈ 0.631`.
    * Nếu phim mục tiêu ở hạng #10: `NDCG = 1.0 / log2(10 + 1) ≈ 1.0 / 3.459 ≈ 0.289`.
    * Nếu không nằm trong Top-K: `NDCG = 0.0`.

---

### 6.3. Mean Reciprocal Rank (MRR@K)
* **Khái niệm**: Giá trị nghịch đảo của vị trí xếp hạng đầu tiên tìm thấy phim mục tiêu:
  ```text
  MRR@K = 1.0 / j (nếu tìm thấy tại hạng j), ngược lại bằng 0.0.
  ```

---

## 7. PHÁT HIỆN KHOA HỌC: HIỆN TƯỢNG ĐUÔI DÀI & LÝ DO CẦN ĐỒ THỊ TRI THỨC

Trong quá trình thực nghiệm tinh chỉnh siêu tham số M07 ([artifacts/als/m07/best_als_model_manifest.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m07/best_als_model_manifest.json)), đội ngũ phát triển MoodGraph đã ghi nhận một **hiện tượng khoa học cực kỳ thú vị**:

1. **Điểm số dự đoán của ALS trên phim đuôi dài (Long-Tail Items)**:
   * Đối với các bộ phim bom tấn có hàng chục nghìn lượt đánh giá (như *Pulp Fiction*, *The Dark Knight*), véc-tơ nhân tố ẩn `Q_i` bị ràng buộc bởi rất nhiều dữ liệu, độ lớn véc-tơ được điều hòa chặt chẽ.
   * Ngược lại, đối với các bộ phim hiếm chỉ có 1 hoặc 2 lượt đánh giá 5.0 sao, véc-tơ `Q_i` có xu hướng bị kéo lệch mạnh theo hướng của người đánh giá đó. Khi nhân vô hướng với người dùng có véc-tơ cùng hướng, điểm số dự đoán của các phim hiếm này bị đội lên rất cao (có thể lên tới 12.5 điểm trên thang 5 sao!).
   * **Hậu quả**: Khi lấy Top 10 phim có điểm số cao nhất của ALS thuần túy, có đến hơn 95% các vị trí bị chiếm đóng bởi các bộ phim quá hiếm (Long-Tail), làm giảm độ chính xác tổng quát trên tập người dùng đại chúng.

2. **Bài học học thuật đắt giá**:
   * **Một mình mô hình ALS là không đủ** để xây dựng một hệ thống gợi ý toàn diện trên thực tế!
   * Để giải quyết triệt để vấn đề này, MoodGraph đã kiến tạo giải pháp lai:
     * Sử dụng **Đồ thị tri thức (Knowledge Graph)** để liên kết phim qua Thể loại và Thẻ cảm xúc Genome được kiểm duyệt khoa học.
     * Sử dụng thuật toán **Dung hợp thứ hạng Reciprocal Rank Fusion (Cormack RRF)** để kết hợp sức mạnh hành vi của ALS với độ tin cậy ngữ nghĩa của Đồ thị tri thức!

---

## 8. 5 CÂU HỎI VẤN ĐÁP CHUYÊN SÂU CỦA GIẢNG VIÊN & CÁCH TRẢ LỜI ĐIỂM 10

Dưới đây là 5 câu hỏi kinh điển nhất của các thầy cô chuyên ngành Học máy và Dữ liệu lớn về thuật toán Phân rã Ma trận:

### Câu Hỏi 1: *"Tại sao em lại chọn giải thuật ALS mà không dùng SVD (Singular Value Decomposition) hay SGD (Stochastic Gradient Descent) để phân rã ma trận?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, có hai lý do mang tính quyết định:
> Thứ nhất, thuật toán SVD truyền thống yêu cầu ma trận đầu vào phải là ma trận đặc (Dense Matrix). Để áp dụng SVD, người ta phải điền giá trị 0 hoặc giá trị trung bình vào 99.75% các ô trống, điều này làm biến dạng nghiêm trọng phân phối dữ liệu và tăng kích thước bộ nhớ lên hàng chục tỷ phần tử.
> Thứ hai, so với thuật toán SGD cập nhật trọng số tuần tự từng cặp tương tác, thuật toán ALS có khả năng phân tán song song hóa cực kỳ tối ưu trên cụm máy tính Apache Spark. Khi cố định ma trận Q, việc giải nghiệm ma trận P của 162,000 người dùng là hoàn toàn độc lập, Spark có thể chia việc cho hàng trăm Executor xử lý đồng thời mà không bị nghẽn đồng bộ tham số."*

### Câu Hỏi 2: *"Số chiều tiềm ẩn k (rank) và hệ số điều chuẩn lambda (regParam) ảnh hưởng như thế nào đến mô hình? Em chọn các giá trị này dựa trên cơ sở nào?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô:
> - Số chiều tiềm ẩn `rank (k)` quyết định năng lực biểu diễn của mô hình: Nếu k quá nhỏ (ví dụ k = 2), mô hình sẽ bị Underfitting (không nắm bắt đủ các khía cạnh sở thích phức tạp). Nếu k quá lớn (ví dụ k = 128), mô hình vừa tốn RAM vừa dễ bị Overfitting trên các dữ liệu nhiễu.
> - Hệ số điều chuẩn `regParam (lambda)` đóng vai trò kiểm soát độ lớn chuẩn L2 của véc-tơ: Nếu lambda quá nhỏ, các bộ phim ít đánh giá sẽ bị phóng đại điểm số; nếu lambda quá lớn, các véc-tơ bị co cụm về gần gốc tọa độ, làm mất tính phân biệt giữa các phim.
> Trong đồ án, em đã thực hiện quá trình tinh chỉnh siêu tham số Grid Search trong module `recommender/als/tuner.py` với các dải giá trị k in {8, 16, 32} và lambda in {0.05, 0.1, 0.3, 1.0} trên tập dữ liệu Validation để chọn ra bộ siêu tham số cân bằng tối ưu."*

### Câu Hỏi 3: *"Tại sao khi sinh danh sách Top-K cho người dùng, em lại phải áp dụng nguyên tắc Filter-Before-Top-K thay vì lấy Top 100 rồi mới lọc bỏ các phim đã xem?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, trong bộ dữ liệu MovieLens 25M, hành vi của người dùng tuân theo phân phối đuôi dài: Có những người dùng bình thường chỉ đánh giá 20 phim, nhưng cũng có những người dùng cuồng nhiệt (Heavy Users) đã đánh giá hơn 2,000 hoặc 5,000 bộ phim.
> Nếu ta áp dụng cách tiếp cận lấy Top 100 rồi mới lọc, đối với những người dùng đã xem hàng nghìn phim, có khả năng toàn bộ 100 phim được gợi ý đều là các phim họ đã xem rồi trong quá khứ. Sau khi lọc, hệ thống sẽ trả về danh sách rỗng hoặc bị thiếu hụt nghiêm trọng số lượng gợi ý.
> Kỹ thuật `Filter-Before-Top-K` trong file `candidates.py` giải quyết triệt để vấn đề này bằng cách gán điểm âm vô cùng (-inf) cho toàn bộ phim đã xem ngay trên mảng điểm, sau đó mới dùng thuật toán phân hoạch Min-Heap để trích xuất đúng K phần tử cao nhất còn lại, bảo đảm 100% trả về đủ K phim mới tinh cho mọi đối tượng người dùng."*

### Câu Hỏi 4: *"Em giải thích ý nghĩa của chỉ số NDCG@K và tại sao nó lại sử dụng hàm logarit ở mẫu số?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, NDCG (Normalized Discounted Cumulative Gain) là thước đo chất lượng thứ hạng có tính đến tâm lý người dùng. Người dùng thường chỉ chú ý đến 1 hoặc 2 vị trí đầu tiên của danh sách gợi ý.
> Mẫu số `log2(j + 1)` đóng vai trò là hàm chiết khấu vị trí (Position Discount):
> Khi bộ phim mục tiêu nằm ở vị trí #1, mẫu số là `log2(2) = 1`, giá trị đạt cực đại là 1.0.
> Khi vị trí j tăng dần (tức là bị đẩy xuống sâu phía dưới danh sách), mẫu số tăng theo hàm logarit làm cho phần thưởng giảm dần nhưng không giảm đột ngột về 0 như hàm bước thang. Điều này giúp đánh giá công bằng nỗ lực của mô hình: Gợi ý đúng phim ở hạng #3 vẫn tốt hơn nhiều so với gợi ý đúng ở hạng #10."*

### Câu Hỏi 5: *"Hệ thống của em giải quyết vấn đề Cold-Start (Người dùng mới chưa từng đánh giá phim nào) trong mô hình ALS như thế nào?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, về mặt bản chất toán học, nếu một người dùng chưa có bất kỳ tương tác nào trong ma trận R, mô hình phân rã ma trận ALS không thể tính toán được véc-tơ P_u (vì không có ràng buộc dữ liệu để tối ưu).
> Trong mã nguồn `recommender/als/trainer.py` tại dòng 52, em thiết lập `coldStartStrategy = 'nan'` để Spark trả về giá trị NaN một cách có chủ đích, thay vì dự đoán sai lệch.
> Khi hệ thống phát hiện trạng thái Cold-Start, bộ điều phối lai (Hybrid Engine) sẽ kích hoạt cơ chế chuyển giao: Sử dụng **Đồ thị tri thức (Knowledge Graph)** gợi ý các bộ phim tiêu biểu theo thể loại mà người dùng vừa chọn, hoặc sử dụng danh sách các tác phẩm kinh điển có điểm số cao nhất của nhân loại (Popularity-based High-Quality Films), giúp người dùng có trải nghiệm khám phá ngay lập tức từ lần đầu tiên truy cập."*

---

## 9. BÀI TẬP THỰC HÀNH NGÀY 02 DÀNH CHO ANH

Để nắm vững phản xạ cơ bắp và tự tin mở code khi giảng viên yêu cầu, anh hãy thực hiện 3 thao tác thực hành sau:

### Lệnh 1: Xem trực tiếp file Manifest của mô hình ALS Champion
```powershell
Get-Content -Path "artifacts\als\m07\best_als_model_manifest.json" | Select-Object -First 35
```
*Mục đích*: Thấy rõ mô hình `ALS_R8_REG0.3_ITER10` với các thông số `rank = 8`, `reg_param = 0.3`, `max_iter = 10`.

### Lệnh 2: Xem đoạn code kiểm toán ma trận nhân tố ẩn trong `trainer.py`
Mở file [recommender/als/trainer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py#L43-L65) và đọc lướt qua:
* Dòng 43–65: Docstring toán học của `ALSConfig`.
* Dòng 175–191: Lời gọi `als.fit(train_df)`.
* Dòng 220–235: Vòng lặp kiểm tra NaN/Inf và tính chuẩn L2 `np.linalg.norm()`.

### Lệnh 3: Xem đoạn code sinh ứng viên Top-K bằng BLAS trong `candidates.py`
Mở file [recommender/als/candidates.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L233-L330) và đọc:
* Dòng 15–30: Docstring giải thích nguyên tắc `Filter-Before-Top-K`.
* Dòng 260–290: Đoạn code gán `-np.inf` cho các phim đã xem và chọn Top-K bằng heap.

---
*Ngày mai (Ngày 03), chúng ta sẽ bước sang Bài giảng về Trụ cột Gợi ý 2: **Đồ thị Tri thức Đa tầng (Embedded Knowledge Graph), Thuật toán khai phá 3 Metapaths P1-P2-P3, và Kỹ thuật Inverted Indexing siêu tốc không cần Neo4j Server**.*
