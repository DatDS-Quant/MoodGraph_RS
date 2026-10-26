# Giao thức Phân chia Dữ liệu & Quy tắc Đánh giá Offline
## Dự án MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark

- **Tài liệu:** `docs/evaluation_protocol.md`
- **Bộ dữ liệu mục tiêu:** MovieLens 25M (25,000,095 ratings, 162,541 users, 62,423 movies)
- **Bài toán cốt lõi:** Personalized Top-N Recommendation & Rating Prediction
- **Trạng thái:** PROPOSED (Đang chờ Technical Mentor phê duyệt)

---

## 1. Mục tiêu & Nguyên tắc Thiết kế

Giao thức đánh giá offline nhằm đo lường khả năng của mô hình trong việc đề xuất các bộ phim người dùng thực sự quan tâm và đánh giá cao, dựa trên lịch sử tương tác quá khứ. Các nguyên tắc bao gồm:

1. **Tuân thủ Thứ tự Thời gian (Temporal Ordering):**
   - Với từng người dùng, các tương tác dùng để huấn luyện phải xảy ra trước các tương tác dùng để kiểm thử.
2. **Tách biệt Dữ liệu (Data Partitioning):**
   - Mô hình chỉ được học tham số và xây dựng đặc trưng trên tập Train. Tập Validation dùng để chọn siêu tham số, tập Test chỉ dùng để báo cáo kết quả cuối cùng.
3. **Đánh giá Khách quan & Minh bạch:**
   - Đánh giá trên cùng tập kiểm thử chung cho mọi mô hình.
   - Báo cáo rõ ràng các giả định, giới hạn phương pháp và phân biệt tường minh giữa kết quả mô hình thuần túy và mô hình có cơ chế bổ trợ (fallback).

---

## 2. Chiến lược Phân chia Dữ liệu: User-wise Leave-1-Last

### 2.1. Quy cách Phân chia
Dựa trên đặc thù toàn bộ 162,541 users trong MovieLens 25M đều có tối thiểu 20 ratings (trung vị 71 ratings), phương án phân chia offline chính được chọn là **User-wise Leave-1-Last theo Timestamp**:

Với mỗi người dùng, sắp xếp toàn bộ lịch sử tương tác tăng dần theo khóa:
`ORDER BY timestamp ASC, movieId ASC` (sử dụng `movieId` làm khóa phụ ổn định để giải quyết triệt để các trường hợp trùng timestamp).

- **Tập Test (`ratings_test`):** Lấy **1 tương tác cuối cùng** của mỗi user (162,541 bản ghi).
- **Tập Validation (`ratings_val`):** Lấy **1 tương tác áp chót** ngay trước tập Test của mỗi user (162,541 bản ghi).
- **Tập Train (`ratings_train`):** Toàn bộ các tương tác còn lại phía trước (24,675,013 bản ghi, chiếm 98.70%). Mỗi user có ít nhất 18 tương tác và trung vị là 69 tương tác.

```text
Trục tương tác của từng User (sắp xếp theo timestamp ASC, movieId ASC):
[ r_1, r_2, r_3, ..., r_{n-2} ]  ->  [ r_{n-1} ]  ->  [ r_n ]
|_____________________________|      |___________|    |_______|
     TẬP TRAIN (>= 18 ratings)         VALIDATION        TEST
```

### 2.2. So sánh với Global Chronological Split & Giới hạn Cần Công bố

| Tiêu chí | Global Chronological Split (Cắt theo mốc ngày dương lịch) | User-wise Leave-1-Last Split (Đề xuất) |
| :--- | :--- | :--- |
| **Cách thực hiện** | Chọn một mốc thời gian T (ví dụ: trước 2018 làm Train, 2018 làm Val, 2019 làm Test). | Với mỗi user, giữ lại tương tác áp chót làm Val và tương tác cuối cùng làm Test. |
| **Độ phủ Người dùng** | Thấp: Người dùng ngừng hoạt động trước mốc T sẽ không có dữ liệu Test; người dùng mới sau mốc T trở thành pure cold-start user. | Toàn diện: 100% users (162,541) đều hiện diện trong cả Train, Val và Test với lịch sử Train >= 18 tương tác. |
| **Tương thích ALS** | Rất khó khăn khi đánh giá: ALS không thể sinh latent factor cho user không có dữ liệu Train. | Thuận lợi: ALS học được latent vector cho toàn bộ users tham gia đánh giá. |

#### Giới hạn Temporal Leakage giữa các User (Cross-User Temporal Leakage):
- **Bản chất giới hạn:** Cửa sổ thời gian tương tác giữa các user không đồng nhất. User A có thể có test rating vào năm 2005, trong khi User B có các train ratings vào năm 2018. Khi mô hình (như Item-Item CF hay ALS) học mẫu hành vi chung từ toàn bộ `ratings_train`, các mẫu tương tác năm 2018 của User B có thể gián tiếp tác động đến việc dự đoán sự kiện năm 2005 của User A.
- **Công bố khoa học:** Giao thức Leave-1-Last bảo đảm tính tuần tự thời gian *trên từng cá nhân người dùng (intra-user temporal integrity)*, nhưng **không ngăn chặn hoàn toàn rò rỉ thời gian giữa các người dùng (cross-user temporal leakage)**. Đây là một trade-off có chủ đích để giữ trọn vẹn tập user cho bài toán Collaborative Filtering quy mô lớn.

---

## 3. Ranh giới Dữ liệu Huấn luyện & Đánh giá

Để tránh rò rỉ dữ liệu giữa các phân vùng:

| Thành phần Mô hình | Nguồn Dữ liệu Được phép Sử dụng | Ranh giới Bắt buộc |
| :--- | :--- | :--- |
| **Spark MLlib ALS** | `ratings_train` | Không sử dụng `ratings_val` và `ratings_test` trong quá trình fit mô hình. |
| **Item-Based CF** | `ratings_train` | Ma trận tương đồng / đồng xuất hiện chỉ tính từ tập Train. |
| **Content-Based Profile** | `ratings_train` | Vector sở thích user chỉ được tổng hợp từ các phim user đã xem trong tập Train. |
| **Knowledge Graph (Cạnh động)** | `ratings_train` và `tags_train` | Các quan hệ giữa User và Phim/Thể loại/Tag chỉ được tạo từ dữ liệu xảy ra trước thời điểm split. |
| **Knowledge Graph (Cạnh tĩnh)** | `movies.csv`, `genome-scores.csv` | Quan hệ bản thể tĩnh giữa Phim và Thể loại/Tag Genome. |
| **Popularity Baseline** | `ratings_train` | Tần suất đánh giá chỉ được đếm trên tập Train. |
| **Hyperparameter Tuning** | `ratings_val` | Tinh chỉnh tham số trên Validation, không dùng Test. |

---

## 4. Đánh giá Khách quan về Dữ liệu Tag Genome

### 4.1. Bản chất Phụ thuộc Dữ liệu Cộng đồng của Tag Genome
- Tệp `genome-scores.csv` không phải là metadata sản xuất độc lập (như năm phát hành hay danh sách diễn viên). Điểm số này do GroupLens tính toán vào cuối năm 2019 dựa trên thuật toán học máy xử lý toàn bộ dữ liệu cộng đồng (ratings, user tags, reviews) tích lũy suốt 24 năm.
- Do đó, Tag Genome mang tính chất tri thức cộng đồng được tổng hợp hậu kỳ.

### 4.2. Phương án Đối chứng Minh bạch (Ablation Study)
Để đánh giá chính xác giá trị thực tế của Tag Genome mà không ngộ nhận hiệu năng:
- Bắt buộc duy trì hai biến thể đối chứng song song trong quá trình thử nghiệm:
  1. **Genre-only Baseline:** Mô hình chỉ sử dụng Thể loại chuẩn từ `movies.csv`.
  2. **Genre + Tag Genome Model:** Mô hình tích hợp thêm điểm số liên kết Tag Genome.
- Mức độ cải thiện giữa hai biến thể sẽ phản ánh đóng góp thực tế của Tag Genome.

---

## 5. Xử lý User & Movie Cold-Start và Quy tắc Báo cáo ALS

### 5.1. User Cold-Start
- Do giao thức Leave-1-Last được áp dụng trên tập 162,541 users có sẵn >= 20 ratings, không xuất hiện user cold-start trong tập Test đối với bài toán cá nhân hóa.

### 5.2. Movie Cold-Start & Phân định Rõ ràng Kết quả ALS
Theo thống kê EDA, có 1,811 phim chỉ có đúng 1 rating trên toàn hệ thống. Nếu tương tác duy nhất này rơi vào tập Test của một user, bộ phim đó hoàn toàn chưa từng xuất hiện trong `ratings_train`.

#### Quy tắc Báo cáo Bắt buộc:
1. **Phân biệt rạch ròi giữa ALS thuần và ALS có Fallback:**
   - **ALS-only (ALS thuần):** Khi gặp phim cold-start không có latent factor, mô hình ALS thuần túy không thể đưa ra dự đoán điểm (trả về NaN hoặc xếp cuối bảng). Khi báo cáo chỉ số của "ALS", **tuyệt đối không được gán fallback rồi công bố đó là kết quả của ALS thuần**.
   - **ALS + Fallback (Mô hình kết hợp cơ bản):** Áp dụng cơ chế bổ trợ (như dự đoán bằng User Mean hoặc Global Popularity) cho các trường hợp ALS không dự đoán được. Báo cáo phải ghi rõ nhãn "ALS + Fallback (Popularity/Mean)".
2. **Không Loại bỏ Tùy tiện Lượt Test (No Selective Dropping):**
   - Khi so sánh giữa các mô hình khác nhau trên cùng một bảng tổng kết, tập ground-truth kiểm thử phải được giữ nguyên vẹn cho tất cả các mô hình, không tùy tiện drop các mẫu khó để nâng cao điểm số.

---

## 6. Giao thức Đánh giá Top-N Khách quan (Top-N Evaluation Protocol)

### 6.1. Không gian Ứng viên & Loại trừ Lịch sử Đã Tương tác
- **Không gian Ứng viên (Candidate Pool):**
  - Hướng tới mục tiêu đánh giá trên toàn bộ danh mục chưa xem (**Full-Catalog Ranking**).
  - Khi đánh giá tập Test cho người dùng `u`, **toàn bộ các phim mà `u` đã đánh giá trong cả tập Train và tập Validation phải bị loại khỏi danh sách ứng viên**:
    `Candidate_Pool(u) = Catalog \ (Train_u U Val_u)`
  - Điều này bảo đảm mô hình không gợi ý lại những phim người dùng đã từng xem trong quá khứ.

### 6.2. Chiến lược Thực thi: Batch Evaluation trên Tập User Đại diện
- **Kiểm soát Tài nguyên RAM & Tránh Tràn bộ nhớ:**
  - Việc tính toán điểm số cho 162,541 users x ~62,000 phim cùng lúc trong bộ nhớ sẽ tạo ra ma trận kích thước hơn 10 tỷ phần tử (tiêu tốn ~40GB RAM), dẫn tới nguy cơ tràn bộ nhớ.
  - **Quy tắc thực thi:** 
    - Đánh giá theo từng batch (lô) người dùng, giải phóng bộ nhớ sau mỗi batch.
    - Trong giai đoạn thử nghiệm offline ban đầu, lựa chọn một **tập user đại diện có quy tắc** (ví dụ: lấy mẫu hệ thống có phân tầng theo mức độ hoạt động: Heavy, Medium, Light users) và **dùng chung cố định tập user này cho tất cả các mô hình đối chuẩn**.

### 6.3. Ngưỡng Đánh giá Độ thích (Relevance Threshold) & Xử lý Mẫu số Metric
- **Ngưỡng Độ thích (Relevance Threshold):** `rating >= 3.5` (trên thang 5.0) được chọn làm ngưỡng xác định người dùng thực sự quan tâm/thích phim.
- **Xử lý Trường hợp Test Rating < 3.5:**
  - Nếu tương tác trong tập Test của user có `rating < 3.5`, điều này có nghĩa là người dùng không thích bộ phim đó.
  - **Quy tắc tính toán metric:**
    - *Đánh giá trên Positive Test Cohort:* Báo cáo chính trên tập các users có test rating thỏa mãn `rating >= 3.5` (nơi tồn tại Ground-Truth Positive thực sự để đo lường Hit Rate và NDCG).
    - *Đánh giá trên Toàn bộ Users:* Nếu tính trên toàn bộ 162,541 users, các user có test rating < 3.5 có số lượng true positive bằng 0 (mẫu số của Recall bằng 0). Với nhóm này, mọi gợi ý đều không được tính là hit (hit = 0), tránh chia cho 0 và tránh ngộ nhận đề xuất sai thành đúng.

### 6.4. Các Mô hình Tham gia Đối chuẩn
1. **Global Popularity:** Gợi ý các phim có lượt đánh giá nhiều nhất trong `ratings_train`.
2. **Item-Based Collaborative Filtering:** Gợi ý dựa trên ma trận tương đồng cosine giữa các phim trong `ratings_train`.
3. **Spark MLlib ALS (ALS-only & ALS + Fallback):** Nhân tử hóa ma trận phân tán.
4. **Content-Based:** Gợi ý dựa trên độ tương đồng giữa User Profile và Movie Metadata (Genre-only và Genre + Tag Genome).
5. **Knowledge Graph (Path-based Scoring):** Gợi ý dựa trên khai phá đường đi liên kết trên đồ thị tri thức.
6. **Hybrid Recommender:** Kết hợp điểm số từ ALS và Knowledge Graph với cơ chế candidate union.

### 6.5. Hệ Chỉ số Đánh giá
Đo lường tại các mốc `K = 5, 10, 20`:
- **Hit Rate (HR@K):** Tỷ lệ người dùng có phim mục tiêu xuất hiện trong Top-K.
- **Normalized Discounted Cumulative Gain (NDCG@K):** Đánh giá vị trí xếp hạng của phim mục tiêu trong Top-K.
- **Precision@K & Recall@K:** Đo lường độ chính xác và độ phủ của danh sách gợi ý.
- **Mean Reciprocal Rank (MRR@K):** Nghịch đảo thứ hạng của đề xuất đúng.
- **Catalog Coverage@K:** Tỷ lệ phần trăm tổng số phim trong catalog được hệ thống gợi ý ít nhất một lần trên toàn bộ tập user thử nghiệm.

---

## 7. Kết luận

Giao thức **User-wise Leave-1-Last** kết hợp với **Full-Catalog Candidate Pool (loại trừ Train và Val)** và **đánh giá batch trên tập user đại diện dùng chung** tạo ra một quy chuẩn kiểm thử chặt chẽ, khả thi về mặt tài nguyên phần cứng và minh bạch về mặt khoa học cho các giai đoạn tiếp theo của dự án.
