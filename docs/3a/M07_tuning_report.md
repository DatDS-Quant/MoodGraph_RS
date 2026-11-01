# BÁO CÁO KHOA HỌC M07 (ĐÃ KIỂM TOÁN TẬP TRUNG): THỰC NGHIỆM TINH CHỈNH SIÊU THAM SỐ SPARK ALS TRÊN TẬP VALIDATION

- **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị Tri thức và Apache Spark
- **Mã module:** M07 (Khối 3A – Spark ALS)
- **Git Branch:** `feature/als-3a`
- **Phiên bản báo cáo:** Audited Acceptance Revision (01/11/2026)
- **Tập dữ liệu huấn luyện:** MovieLens 25M Train split (`data/processed/splits/train` – 24.675.013 ratings, 162.541 users, 58.932 items)
- **Tập đánh giá:** MovieLens 25M Validation split (`data/processed/splits/validation` – 109.779 positive users có rating >= 3.5)
- **Trạng thái Test Split:** Cách ly tuyệt đối 100% (`data/processed/splits/test` không bị truy cập)

---

## 1. ĐỐI SOÁT VÀ ĐỒNG NHẤT HÓA CHỈ SỐ GIỮA CÁC MODULE (M03 / M06 / M07 METRICS RECONCILIATION)

Để đảm bảo tính liêm chính và nhất quán khoa học tuyệt đối, bảng dưới đây đối chiếu chi tiết từng chỉ số giữa các báo cáo, nguồn artifact và cohort đánh giá thực tế:

| Phương pháp / Mô hình | Module | Cohort đánh giá | Mẫu số người dùng | HR@10 | NDCG@10 | MRR@10 | Coverage@10 | Số phim Top-10 | Nguồn Artifact gốc |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Popularity Count** | M03 | Full Positive Validation | 109.779 | **0.05519** | **0.02789** | 0.01970 | **0.497%** | 310 | `artifacts/m03_popularity_results.json` |
| **Popularity Weighted (m=10)** | M03 | Full Positive Validation | 109.779 | **0.01969** | **0.00771** | 0.00416 | **0.074%** | 46 | `artifacts/m03_popularity_results.json` |
| **Spark ALS M05 Baseline** | M06 | Full Positive Validation | 109.779 | **0.00000** | **0.00000** | 0.00000 | **2.475%** | 1.545 | `artifacts/als/m06/m06_als_evaluation_results.json` |
| **Spark ALS M05 Baseline** | M07 | Screening Cohort (Seed 42) | 5.000 | **0.00000** | **0.00000** | 0.00000 | **1.086%** | 678 | `artifacts/als/m07/experiment_registry.json` |
| **ALS Finalist (R8, Reg0.3)** | M07 | Screening Cohort (Seed 42) | 5.000 | **0.00000** | **0.00000** | 0.00000 | **0.034%** | 21 | `artifacts/als/m07/experiment_registry.json` |
| **ALS Finalist (R8, Reg0.3)** | M07 | Full Positive Validation | 109.779 | **0.00000** | **0.00000** | 0.00000 | **0.056%** | 35 | `artifacts/als/m07/best_als_model_manifest.json` |

### Làm rõ nguyên nhân sai lệch đã được kiểm toán (Root Cause Analysis):
1. **Chỉ số Popularity M03:** Bản nháp ban đầu của M07 ghi nhận nhầm giá trị 0.09117 và 0.04603. Kiểm toán xác nhận đây là số liệu xấp xỉ tại cutoff K=20 (HR@20 = 0.08956, NDCG@20 = 0.03649) từ một bản test phụ. Giá trị chuẩn mực tại K=10 theo `artifacts/m03_popularity_results.json` là **HR@10 = 0.05519** và **NDCG@10 = 0.02789**. Mã nguồn và manifest đã được hiệu chỉnh chính xác.
2. **Độ phủ danh mục (Catalog Coverage@10) của M05 Baseline:** 
   - Tại M06, khi sinh gợi ý cho toàn bộ 109.779 người dùng, có tổng cộng **1.545 bộ phim độc lập** xuất hiện trong Top-10, tương ứng độ phủ **2.48%** trên toàn danh mục (62.423 phim).
   - Tại M07, khi tầm soát trên 5.000 người dùng Screening, nhóm người dùng này chỉ nhận **678 bộ phim độc lập**, tương ứng độ phủ **1.09%**.
   - Con số 0.056% (35 phim) thuộc về mô hình finalist `ALS_R8_REG0.3_ITER10` khi đánh giá trên toàn bộ 109.779 người dùng. Không được đánh đồng các tỷ lệ độ phủ này khi quy mô tập người dùng đánh giá khác nhau.

---

## 2. KIỂM TOÁN MẪU SỐ VÀ KẾT QUẢ CỦA NHÁNH CHẨN ĐOÁN (SUPPORT-FILTER AUDIT)

Tại thử nghiệm chẩn đoán `ALS_DIAGNOSTIC_MIN_RATINGS_20` (che các phim có dưới 20 lượt đánh giá Train), báo cáo registry ghi nhận `hit_rate_10 = 0.0002186 ≈ 0.00022`. Kiểm toán chuyên sâu xác định:

1. **Mẫu số đánh giá và số lượng trúng mục tiêu thực tế:**
   - Trong quá trình tầm soát, hàm `TopNEvaluator.evaluate` nhận danh sách gợi ý của 5.000 người dùng Screening nhưng lại nhận `val_targets` của toàn bộ **109.779 positive users**.
   - Do đó, 104.779 người dùng không thuộc Screening được gán danh sách rỗng `[]` (miss) và được bảo toàn trong mẫu số.
   - **Số lượng hits thực tế tại K=10 là 24 hits** (không phải 1 hit):
     `24 hits / 109.779 users = 0.000218621` (chính xác bằng giá trị ghi nhận trong registry).
2. **Nếu chuẩn hóa theo đúng mẫu số nhóm Screening (5.000 positive users):**
   - **HitRate@5:** 20 / 5.000 = **0.00400 (0.40%)**
   - **HitRate@10:** 24 / 5.000 = **0.00480 (0.48%)**
   - **HitRate@20:** 43 / 5.000 = **0.00860 (0.86%)**
   - **NDCG@10:** 9.9244e-5 × (109.779 / 5.000) = **0.002179**
   - **MRR@10:** 6.2875e-5 × (109.779 / 5.000) = **0.001380**
3. **Phát biểu khoa học thận trọng:**
   - Việc ghi nhận 24 hits khi che các phim ít lượt đánh giá chứng minh rằng các vector đặc trưng ẩn của ALS có chứa tín hiệu xếp hạng hữu ích đối với các phim có hỗ trợ thống kê.
   - Tuy nhiên, **không được kết luận một cách thái quá** rằng các vector này đã đạt độ cá nhân hóa cao, bởi vì HitRate 0.48% vẫn thấp hơn đáng kể so với Popularity Count (5.52%).

---

## 3. PHÂN TÍCH TOÁN HỌC CHUẨN XÁC VỀ CƠ CHẾ ĐIỀU CHUẨN SPARK ALS-WR

Báo cáo trước đó có nhận định giản lược rằng "vì có n_i nên ALS-WR luôn phạt phim nhiều rating nặng hơn phim ít rating". Nhận định này cần được hiệu chỉnh về mặt giải tích toán học:

### 3.1. Phương trình nghiệm chuẩn trong ALS-WR
Tại mỗi bước lặp cố định vector người dùng, vector của item `y_i` được giải theo phương trình:
```text
[ sum_{u in R_i} (x_u * x_u^T) + lambda * n_i * I ] * y_i = sum_{u in R_i} (r_{ui} * x_u)
```

### 3.2. Chứng minh giải tích trường hợp đồng nhất (Rank = 1)
Xét bài toán với rank = 1, mọi người dùng có vector đặc trưng `x_u = 1.0` và mọi lượt đánh giá của item `i` đều có cùng giá trị `r`:
- `sum_{u in R_i} (x_u * x_u^T) = sum 1 = n_i`
- `sum_{u in R_i} (r_{ui} * x_u) = sum r = n_i * r`
Phương trình trở thành:
```text
(n_i + lambda * n_i) * y_i = n_i * r
<=> n_i * (1 + lambda) * y_i = n_i * r
<=> y_i = r / (1 + lambda)
```
**Số lượng lượt đánh giá n_i bị triệt tiêu hoàn toàn!**
Điều này chứng minh về mặt toán học: Thư viện Spark MLlib đưa thừa số `n_i` vào số hạng điều chuẩn chính là để **chuẩn hóa quy mô phạt theo số lượng quan sát**, giúp cho nghiệm `y_i` không bị phụ thuộc đơn thuần vào việc item có 1 hay 100.000 đánh giá trong điều kiện lý tưởng.

### 3.3. Phân định ranh giới giữa Cơ chế thuật toán, Số liệu đo được và Giả thuyết khoa học

1. **Cơ chế thuật toán đã được tài liệu Spark xác nhận:**
   Số hạng phạt là `lambda * n_i * I`. Mục tiêu là co ép độ lớn của vector đặc trưng dựa trên mức phạt trung bình cho mỗi tương tác.
2. **Kết quả thực nghiệm M07 đã đo trên MovieLens 25M:**
   - Tại `regParam = 0.1`: 65.57% khe Top-10 là phim 1-rating.
   - Tại `regParam = 0.3`: 95.66% khe Top-10 là phim 1-rating.
   - Tại `regParam = 1.0` và `3.0`: 100.00% khe Top-10 là phim 1-rating.
   - Thang điểm dự đoán trung vị co ép từ 5.75 xuống 4.14 và 0.09.
3. **Giả thuyết khoa học giải thích hiện tượng đo được:**
   - Trong dữ liệu thực tế, các vector người dùng `x_u` không hề đồng nhất mà phân tán theo nhiều hướng trong không gian đa chiều (`rank >= 8`).
   - Phim 1-rating 5-sao chỉ phải khớp duy nhất 1 vector người dùng, vector của nó tự do xoay thẳng hàng tuyệt đối với người dùng đó và bảo toàn tích vô hướng cực đại.
   - Phim phổ biến phải khớp hàng chục nghìn người dùng với các vector phân tán và mức điểm dao động từ 0.5 đến 5.0, khiến ma trận hiệp phương sai trải rộng ra mọi chiều và kéo điểm số trung bình về mức trung bình của tập dữ liệu.
   - Khi tăng `lambda`, cả hai loại vector đều bị co ngắn lại. Tuy nhiên, do Top-N chỉ lấy các điểm số cực trị (argmax), các phim 1-rating 5-sao vốn có độ thẳng hàng cao hơn vẫn giữ được vị trí đứng đầu danh sách đề xuất.
   - **Kết luận:** Đây là hiện tượng quan sát được trong không gian thực nghiệm của MovieLens 25M, không phải là định lý áp dụng cho mọi hệ thống gợi ý ma trận nhân tử hóa.

---

## 4. KIỂM TOÁN QUY TRÌNH CHỌN MÔ HÌNH (MODEL SELECTION AUDIT)

1. **Trạng thái kết quả của họ mô hình ALS_ONLY:**
   - Cả 5 thử nghiệm huấn luyện chính quy (`ALS_R16_REG0.3`, `ALS_R16_REG1.0`, `ALS_R16_REG3.0`, `ALS_R8_REG0.3`, `ALS_R32_REG0.3`) và mô hình M05 cơ sở đều ghi nhận **Screening HR@10 = 0.00000** và **Screening NDCG@10 = 0.00000**.
2. **Quy tắc phá hòa (Tie-Breaking Rule) của Selection Oracle:**
   - Bộ quy tắc lựa chọn độc lập đã thực hiện phá hòa tất định theo đúng trình tự:
     1. `ndcg_10 DESC` (hòa 0.0)
     2. `hit_rate_10 DESC` (hòa 0.0)
     3. `rank ASC` -> Áp dụng nguyên lý Occam's Razor: chọn mô hình có số chiều ẩn nhỏ nhất (`rank = 8` < `rank = 16` < `rank = 32`).
     4. `reg_param ASC` -> `0.3`.
3. **Định danh chính xác của mô hình Finalist:**
   - Cấu hình `ALS_R8_REG0.3_ITER10` được định danh là **"Complexity-preferred finalist among tied screening trials"** (Mô hình tối giản được ưu tiên theo độ phức tạp giữa các thử nghiệm hòa điểm trên tập tầm soát).
   - **Tuyệt đối không tuyên bố** rằng cấu hình này có chất lượng gợi ý vượt trội hơn các cấu hình khác.
4. **Phạm vi kiểm định toàn phần (Level 2 Full Validation):**
   - Chỉ duy nhất mô hình finalist `ALS_R8_REG0.3_ITER10` được thực thi Level 2 trên toàn bộ 109.779 người dùng tích cực.
   - Kết quả Full Validation xác nhận: **Full HR@10 = 0.00000**, **Full NDCG@10 = 0.00000**, **Coverage@10 = 0.056%** (35 phim).
   - Không khẳng định rằng Explicit ALS không thể cải thiện trong mọi không gian tìm kiếm khả dĩ, mà khẳng định trung thực trong phạm vi không gian siêu tham số đã kiểm tra tại M07 (rank từ 8 đến 32, regParam từ 0.1 đến 3.0), việc tinh chỉnh siêu tham số không cải thiện được chất lượng gợi ý.

---

## 5. KIỂM TOÁN PHẠM VI TẬP NGƯỜI DÙNG VÀ NGUỒN GỐC TỶ LỆ FLUKE BIAS (DIAGNOSTICS SCOPE & PROVENANCE AUDIT)

Kiểm toán đã làm rõ ranh giới nguồn gốc (provenance) của các con số tỷ lệ phơi nhiễm phim 1-rating giữa các module:
1. **Kết quả toàn dân tại M06 (All-Users Full Catalog Result):**
   - M06 sinh Top-20 cho toàn bộ **162.541 người dùng Validation** (tổng cộng 3.250.820 slots).
   - Có **2.074.146 slots** thuộc về các phim chỉ có đúng 1 lượt đánh giá Train -> Tỷ lệ chính xác: `2.074.146 / 3.250.820 = 63.80%`.
   - Đây là số liệu đo lường trên toàn bộ 162.541 người dùng, không phải mẫu 10.000 người dùng.
2. **Kết quả nhóm tầm soát tại M07 (Screening Cohort Result):**
   - M07 đo trên đúng **5.000 người dùng Screening tích cực** (tổng cộng 100.000 slots).
   - Mô hình M05 baseline ghi nhận **65.57%** slots thuộc về phim 1-rating.
   - Thử nghiệm `ALS_R16_REG0.3_ITER10` ghi nhận **95.66%** slots thuộc về phim 1-rating.
   - Thử nghiệm `ALS_R8_REG0.3_ITER10` ghi nhận **95.74%** slots thuộc về phim 1-rating.
3. **Kết quả toàn tập tích cực tại M07 (Full Positive Cohort Result):**
   - Mô hình finalist `ALS_R8_REG0.3_ITER10` được đánh giá trên toàn bộ **109.779 người dùng tích cực** (2.195.580 slots).
   - Ghi nhận **95.76%** slots thuộc về phim 1-rating.
- **Quy tắc khoa học:** Tuyệt đối không so sánh trực tiếp các tỷ lệ từ các tập người dùng khác nhau (162.541 all users vs 5.000 screening users vs 109.779 positive users) như thể chúng cùng một mẫu thử nghiệm.

---

## 6. HẠ CẤP VÀ CHUẨN HÓA CÁC TUYÊN BỐ KHOA HỌC (SCIENTIFIC CLAIMS REVIEW)

1. **Về hiện tượng Fluke Bias:**
   - Không tuyên bố Fluke Bias là "giới hạn toán học bất khả kháng của mọi mô hình Matrix Factorization".
   - Tuyên bố chuẩn mực: Fluke Bias là một hiện tượng thiên lệch quan sát thực nghiệm phổ biến khi áp dụng mô hình Explicit ALS tối ưu hàm mục tiêu hồi quy sai số bình phương (RMSE) cho bài toán xếp hạng Top-N trên dữ liệu đánh giá thưa thớt có đuôi dài lớn.
2. **Về vai trò của Khối 3B (Knowledge Graph) và Khối 3C (Hybrid):**
   - Không khẳng định Đồ thị Tri thức hay Mô hình Lai "chắc chắn sẽ khắc phục hoàn toàn thất bại của ALS".
   - Tuyên bố chuẩn mực: Đồ thị tri thức cung cấp cấu trúc ngữ nghĩa bổ trợ (thể loại, đạo diễn, liên kết nội dung) và mô hình Hybrid cung cấp cơ chế kết hợp thông tin đa nguồn, tạo cơ sở khoa học đầy triển vọng để kiểm soát thiên lệch mà mô hình thuần cộng tác gặp phải.

---

## 7. KẾT LUẬN NGHIỆM THU

- **Đánh giá Kỹ thuật (Engineering Verdict):** **M07_ACCEPTANCE_PASS**.
  - Pipeline tinh chỉnh hai tầng vận hành ổn định, bảo vệ dữ liệu Test tuyệt đối, ghi nhận đầy đủ 130 tests kiểm thử tự động đạt 100% PASS.
- **Đánh giá Khoa học (Scientific Verdict):** **M07_MODEL_QUALITY_NOT_IMPROVED**.
  - Kết quả thực nghiệm âm tính (negative result) được báo cáo trung thực, minh bạch, có số liệu đối soát chính xác và giải thích giải tích chặt chẽ.
