# SỔ TAY HỌC TẬP VÀ ÔN LUYỆN BẢO VỆ M07 (ĐÃ KIỂM TOÁN KHOA HỌC)

- **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị Tri thức và Apache Spark
- **Mã module:** M07 (Khối 3A – Spark ALS)
- **Tài liệu:** Sổ tay hướng dẫn học tập, tính tay giải tích và kịch bản vấn đáp bảo vệ đồ án

---

## PHẦN 1: BẢN CHẤT TOÁN HỌC VÀ CHỨNG MINH GIẢI TÍCH

### 1. Phương trình nghiệm chuẩn trong Spark ALS-WR
Trong thư viện Spark MLlib, thuật toán ALS được cài đặt theo phương pháp ALS-WR (Alternating Least Squares with Weighted-λ Regularization, Zhou et al., 2008). Tại mỗi vòng lặp, khi cố định vector người dùng x_u, vector của item y_i được cập nhật thông qua phương trình chuẩn (Normal Equation):

```text
[ sum_{u in R_i} (x_u * x_u^T) + lambda * n_i * I ] * y_i = sum_{u in R_i} (r_{ui} * x_u)
```

Trong đó:
- `R_i` là tập hợp những người dùng đã đánh giá item `i`.
- `n_i = |R_i|` là số lượt đánh giá thực tế của item `i`.
- `lambda` chính là siêu tham số `regParam`.
- `I` là ma trận đơn vị kích thước `k x k` (với `k` là `rank`).

### 2. Chứng minh giải tích: Sự triệt tiêu của n_i trong điều kiện đồng nhất
Xét bài toán với rank = 1, mọi người dùng có vector đặc trưng `x_u = 1.0` và mọi lượt đánh giá của item `i` đều có cùng giá trị `r`:
- `sum_{u in R_i} (x_u * x_u^T) = sum 1 = n_i`
- `sum_{u in R_i} (r_{ui} * x_u) = sum r = n_i * r`

Thay vào phương trình chuẩn:
```text
(n_i + lambda * n_i) * y_i = n_i * r
<=> n_i * (1 + lambda) * y_i = n_i * r
<=> y_i = r / (1 + lambda)
```
**Nhận xét giải tích then chốt:**
- Số lượng lượt đánh giá `n_i` hoàn toàn triệt tiêu ở cả hai vế!
- Nghiệm `y_i = r / (1 + lambda)` hoàn toàn độc lập với việc item có 1 hay 100.000 lượt đánh giá.
- Điều này chứng minh: Thừa số `n_i` được thiết kế có chủ đích nhằm **chuẩn hóa quy mô phạt điều chuẩn theo số lượng mẫu quan sát**, tránh việc các item có nhiều lượt đánh giá bị thống trị hoặc bị phạt sai lệch so với item ít lượt đánh giá trong điều kiện phân bố đồng nhất.

### 3. Tại sao trong thực nghiệm MovieLens 25M, phim 1-rating lại chiếm 100% Top-N khi tăng lambda?
Sự phân hóa này xuất phát từ sự tương tác giữa phân bố dữ liệu thực tế và không gian vector đa chiều (`rank >= 8`):
1. **Phim 1 lượt đánh giá 5.0 sao (Fluke):**
   - Chỉ có duy nhất 1 vector người dùng `x_u`.
   - Vector của item `y_i` tự do xoay cùng hướng (collinear) với người dùng đó mà không gặp xung đột từ bất kỳ quan sát nào khác.
   - Khi tăng `lambda`, độ dài vector bị co lại nhưng hướng vector vẫn giữ góc cực tiểu với người dùng, bảo toàn tích vô hướng cực đại.
2. **Phim phổ biến có hàng chục nghìn lượt đánh giá:**
   - Phải khớp đồng thời hàng chục nghìn người dùng với các hướng sở thích khác nhau và các mức điểm đánh giá trải rộng từ 0.5 đến 5.0 sao.
   - Ma trận hiệp phương sai `sum (x_u * x_u^T)` trải rộng ra mọi chiều không gian, khiến nghiệm tối ưu bị kéo về tâm phân bố của toàn tập dữ liệu (khoảng 3.5 - 4.0 sao).
3. **Hiệu ứng chọn lọc của bài toán Top-N (Argmax effect):**
   - Xếp hạng Top-N chỉ quan tâm đến thứ tự tương đối của các điểm số cao nhất.
   - Khi tăng `lambda`, điểm số tuyệt đối của toàn bộ danh mục đều giảm (tại `regParam = 3.0`, điểm trung vị rơi xuống 0.09).
   - Tuy nhiên, do các phim 1-rating 5-sao duy trì được độ thẳng hàng cao nhất với các người dùng tương ứng, chúng vẫn chiếm trọn các vị trí đứng đầu danh sách đề xuất.

---

## PHẦN 2: BẢN ĐỒ ĐỐI CHIẾU CHỈ SỐ M03 / M06 / M07 CHUẨN XÁC

| Chỉ số | Popularity Count (M03) | Popularity Weighted (M03) | M05 ALS Baseline (M06) | M07 Finalist (R8, Reg0.3) |
| :--- | :---: | :---: | :---: | :---: |
| **Full Positive HR@10** | **0.05519 (5.52%)** | **0.01969 (1.97%)** | **0.00000 (0.00%)** | **0.00000 (0.00%)** |
| **Full Positive NDCG@10** | **0.02789** | **0.00771** | **0.00000** | **0.00000** |
| **Catalog Coverage@10** | **0.497% (310 phim)** | **0.074% (46 phim)** | **2.475% (1.545 phim)** | **0.056% (35 phim)** |
| **Mẫu số đánh giá** | 109.779 users | 109.779 users | 109.779 users | 109.779 users |
| **Nguồn Artifact** | `m03_popularity_results.json` | `m03_popularity_results.json` | `m06_als_evaluation_results.json` | `best_als_model_manifest.json` |

---

## PHẦN 3: 10 KỊCH BẢN VẤN ĐÁP BẢO VỆ CHUẨN MỰC TRƯỚC HỘI ĐỒNG

### Tình huống 1: "Tại sao mô hình ALS của em lại có HitRate bằng 0 trên tập Validation?"
- **Cách trả lời chuẩn xác:**
  "Kính thưa Thầy/Cô, kết quả HitRate@10 = 0.00000 phản ánh đúng hiện tượng Fluke Bias đã được ghi nhận trong nghiên cứu của Cremonesi et al. (RecSys 2010). Explicit ALS tối ưu hóa hàm mục tiêu sai số bình phương RMSE trên các ô đã quan sát điểm, chứ không tối ưu trực tiếp cho bài toán xếp hạng Top-N. Trong tập MovieLens 25M Train, có hàng chục nghìn phim chỉ có đúng 1 lượt đánh giá 5.0 sao. Mô hình khớp điểm của các phim này xấp xỉ 5.0 sao và đẩy chúng chiếm trọn danh sách Top-10. Do người dùng trong tập Validation chủ yếu xem và thích các phim đại chúng, danh sách gợi ý bị lệch sang phim hiếm đã không tạo ra bất kỳ lượt trúng (hit) nào."

### Tình huống 2: "Tại sao em tăng regParam mà không dập tắt được Fluke Bias?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, về mặt lý thuyết giải tích, phương trình chuẩn của Spark ALS-WR có số hạng phạt `lambda * n_i * I`. Trong trường hợp lý tưởng khi các vector người dùng đồng nhất, `n_i` triệt tiêu và nghiệm không phụ thuộc vào số lượng đánh giá. Tuy nhiên, trên dữ liệu thực tế, các phim 1-rating 5-sao chỉ phải khớp một người dùng duy nhất nên vector của nó tự do xoay cùng hướng với người dùng đó. Ngược lại, phim phổ biến phải dung hòa hàng chục nghìn người dùng có gu khác nhau, khiến điểm dự đoán bị kéo về mức trung bình. Khi tăng `lambda`, điểm số của toàn bộ hệ thống bị co ngắn lại, nhưng các phim 1-rating 5-sao vẫn giữ được thứ tự tương đối cao hơn và chiếm lĩnh Top-N."

### Tình huống 3: "Bằng chứng nào cho thấy các vector ẩn của ALS có học được thông tin chứ không phải mô hình hỏng?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, chúng em đã thực hiện nhánh chẩn đoán độc lập `ALS_PLUS_TRAIN_SUPPORT_FILTER`. Khi giữ nguyên các vector tiềm ẩn của mô hình ALS và áp bộ lọc mặt nạ loại bỏ các phim có dưới 20 lượt đánh giá, hệ thống ghi nhận ngay **24 hits tại K=10** trên nhóm 5.000 người dùng Screening (đạt HitRate 0.48%). Điều này chứng minh rằng các vector đặc trưng ẩn thực sự có chứa tín hiệu tương quan sở thích, nhưng các tín hiệu này bị che lấp trong không gian Top-N không có bộ lọc hỗ trợ."

### Tình huống 4: "Tại sao em chọn cấu hình rank = 8 làm finalist khi tất cả các mô hình đều có HitRate bằng 0?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, đây là quyết định áp dụng nguyên lý Dao cạo Occam (Occam's Razor) thông qua bộ quy tắc Selection Oracle độc lập. Khi tất cả các thử nghiệm trong không gian tìm kiếm đều hòa nhau ở mức NDCG = 0 và HitRate = 0, bộ quy tắc ưu tiên mô hình có độ phức tạp thấp nhất (`rank = 8`). Cấu hình này có thời gian huấn luyện nhanh nhất (100.4 giây so với 396.5 giây của rank 32) và tiết kiệm 50% dung lượng bộ nhớ lưu trữ factor."

### Tình huống 5: "Em có khẳng định Explicit ALS không bao giờ có thể dùng được cho bài toán gợi ý phim không?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, chúng em không đưa ra tuyên bố tuyệt đối hóa. Chúng em kết luận trung thực rằng: trong phạm vi không gian siêu tham số đã khảo sát tại M07 (rank từ 8 đến 32, regParam từ 0.1 đến 3.0), việc tinh chỉnh siêu tham số đơn thuần không thể khắc phục được Fluke Bias trên bài toán xếp hạng Top-N. Để cải thiện, hệ thống cần bổ sung các nguồn tri thức ngoại sinh như Đồ thị Tri thức hoặc chuyển đổi sang mô hình phản hồi ngầm (Implicit Feedback)."

### Tình huống 6: "Tại sao số liệu Popularity của em có lúc ghi 5.52% có lúc lại là 9.12%?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, qua quá trình kiểm toán đối soát độc lập, giá trị chuẩn mực của Popularity Count tại mốc K=10 trên toàn bộ 109.779 người dùng Validation tích cực là **HR@10 = 0.05519 (5.52%)** và **NDCG@10 = 0.02789**, được lưu trữ trong `artifacts/m03_popularity_results.json`. Con số 0.0896 (~9.1%) là kết quả đo tại cutoff K=20. Chúng em đã rà soát và hiệu chỉnh đồng nhất 100% trong toàn bộ tài liệu và manifest."

### Tình huống 7: "Tại sao độ phủ danh mục của ALS lại thay đổi từ 2.48% ở M06 xuống 0.056% ở M07?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, độ phủ danh mục (Catalog Coverage) phụ thuộc chặt chẽ vào quy mô tập người dùng được đánh giá:
  - Ở M06, mô hình cơ sở M05 được đánh giá trên toàn bộ **109.779 người dùng**, sinh ra **1.545 bộ phim độc lập** trong Top-10 (đạt độ phủ 2.48%).
  - Ở M07, khi tầm soát trên **5.000 người dùng Screening**, mô hình M05 chỉ sinh ra **678 phim độc lập** (đạt độ phủ 1.09%).
  - Đối với mô hình finalist `ALS_R8_REG0.3_ITER10`, do chịu hệ số điều chuẩn lớn hơn (`regParam = 0.3`), số lượng phim độc lập trong Top-10 trên 109.779 người dùng bị co hẹp lại còn **35 bộ phim** (đạt độ phủ 0.056%)."

### Tình huống 8: "Em bảo vệ dữ liệu tập Test như thế nào trong quá trình tinh chỉnh?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, hàm `guard_test_split_access` trong file [`recommender/als/tuner.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py) sẽ chủ động ném ra ngoại lệ `PermissionError` nếu phát hiện bất kỳ truy cập nào tới tập `test`. Toàn bộ quá trình tầm soát và kiểm định chỉ diễn ra trên tập Train và tập Validation."

### Tình huống 9: "Đồ án có bị giảm giá trị khi mô hình chính ALS có kết quả thấp hơn baseline đơn giản không?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, trong khoa học dữ liệu, một kết quả thực nghiệm âm tính (negative result) được chứng minh chặt chẽ có giá trị học thuật tương đương với kết quả dương tính. Việc chứng minh ranh giới toán học của Explicit ALS đã cung cấp lý do khoa học đầy sức thuyết phục khẳng định sự cần thiết phải kết hợp Đồ thị Tri thức (Task 3B) và Mô hình Lai (Task 3C) ở các giai đoạn tiếp theo."

### Tình huống 10: "Bước tiếp theo của dự án sau M07 nên làm gì?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, sau khi đóng băng mô hình finalist M07, hướng phát triển tối ưu là:
  1. Tiến hành đánh giá kiểm chứng độc lập một lần duy nhất trên tập Test đã đóng băng tại M08 để có số liệu đối chiếu chuẩn hóa.
  2. Bàn giao contract candidate generation sang Khối 3B để phối hợp xây dựng đồ thị tri thức và phát triển mô hình Hybrid tại Khối 3C."
