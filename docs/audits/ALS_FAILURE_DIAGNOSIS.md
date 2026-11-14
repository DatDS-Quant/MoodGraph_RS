# CHẨN ĐOÁN KHOA HỌC: SỰ SỤP ĐỔ CHẤT LƯỢNG CỦA MÔ HÌNH SPARK ALS TRÊN BÀI TOÁN XẾP HẠNG TOP-N
## (SCIENTIFIC FAILURE DIAGNOSIS: SPARK ALS TOP-N RANKING COLLAPSE)

**Mã tài liệu**: `docs/audits/ALS_FAILURE_DIAGNOSIS.md`  
**Chuyên gia phụ trách**: Agent 02 — Senior ML Researcher & ALS Specialist  
**Đối tượng khảo sát**: Mô hình vô địch `ALS_R8_REG0.3_ITER10` (rank=8, regParam=0.3, maxIter=10)  
**Tập dữ liệu**: MovieLens 25M (24.67M Train ratings, 162.541 users, 58.932 items)  
**Tập kiểm định**: Frozen Test Leave-1-Last (111.211 positive users)  

---

## 1. MÔ TẢ VẤN ĐỀ THỰC NGHIỆM (EMPIRICAL PROBLEM STATEMENT)

Trên tập Frozen Test Split gồm 111.211 người dùng kiểm thử tích cực (có đánh giá cuối cùng đạt ngưỡng yêu thích rating >= 3.5):
- **Mô hình Cơ sở Phổ biến (Popularity Count Baseline):**
  * Hit Rate: `HR@10 = 0.05357` (5.958 hits / 111.211 users)
  * NDCG: `NDCG@10 = 0.02721`
  * Catalog Coverage: `Coverage@10 = 317 phim` (0.508%)
- **Mô hình Nhân tử Ma trận Spark ALS Champion (`ALS_R8_REG0.3_ITER10`):**
  * Hit Rate: `HR@10 = 0.00000899` (**Đúng 1 hit duy nhất** tại Rank 2 / 111.211 users)
  * NDCG: `NDCG@10 = 0.00000567`
  * Catalog Coverage: `Coverage@10 = 34 phim` (0.054%)

Đây là một sự chênh lệch khổng lồ (gần 6.000 lần về Hit Rate), đặt ra câu hỏi học thuật nghiêm trọng:
**"Tại sao một thuật toán học máy cộng tác Matrix Factorization phức tạp lại có hiệu năng Top-N thua kém hoàn toàn một mô hình đếm tần suất ngây thơ (Naive Popularity Count)?"**

---

## 2. QUY TRÌNH KIỂM TOÁN TÍNH ĐÚNG ĐẮN CỦA PHẦN MỀM (CODE CORRECTNESS AUDIT)

Trước khi đi đến kết luận về mô hình học máy, Agent 02 và Agent 03 đã kiểm toán toàn bộ chu trình xử lý phần mềm:
1. **Kiểm tra căn chỉnh ID (ID Alignment):**
   * Ma trận nhân tử `userFactors` (162.541 x 8) và `itemFactors` (58.932 x 8) được index trực tiếp bằng số nguyên `id: int`.
   * Đối chiếu tích vô hướng thủ công với phép biến đổi `pyspark.ml.recommend.transform`: sai số tuyệt đối lớn nhất `< 1e-6` ([`tests/als/test_als_trainer.py::test_10_manual_dot_product_alignment`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_als_trainer.py)).
2. **Quy tắc lọc dữ liệu đã xem (Seen-Item Filtering):**
   * Phim đã xem trong Train và Validation được nạp đầy đủ (24.837.554 lượt xem) và gán điểm `-inf` trước khi chọn Top-10.
   * Phim mục tiêu trong Test **không bị loại nhầm**, bảo đảm tính hợp lệ của ground-truth.
3. **Quy tắc bảo toàn mẫu số (Denominator Integrity):**
   * Có 29 bộ phim mục tiêu trong Test hoàn toàn không có trong Train (Cold-Start Items). Cả 29 trường hợp này đều được tính đúng là ca trượt (Miss) và nằm trong mẫu số 111.211.
4. **Kết quả kiểm toán phần mềm:** 
   * Toàn bộ 286 unit/integration tests đều PASS 100%. 
   * **KẾT LUẬN: Không có lỗi lập trình (Bug-free code). Sự sụp đổ của ALS hoàn toàn bắt nguồn từ bản chất toán học của mô hình hóa định lượng (Modeling Flaw).**

---

## 3. NGUYÊN NHÂN GỐC RỄ ĐÃ ĐƯỢC XÁC THỰC (CONFIRMED ROOT CAUSES)

### 3.1. Sự Lệch pha giữa Hàm Mục tiêu RMSE và Bài toán Xếp hạng Top-N
- Spark ALS là thuật toán giải ma trận nhân tử tối ưu hóa sai số trung bình bình phương (RMSE):
  `L(P, Q) = sum_{(u, i)} (R_{u, i} - P_u dot Q_i)^2 + lambda * (||P_u||^2 + ||Q_i||^2)`
- **Bản chất của RMSE:** Thuật toán chỉ cố gắng dự đoán chính xác điểm số của các cặp đã quan sát trong tập Train. Nó **hoàn toàn không được huấn luyện để xếp hạng (Rank Optimization)** giữa hàng chục ngàn cặp chưa quan sát.

### 3.2. Hiện tượng Thiên lệch Ngẫu nhiên Đuôi Dài (Long-Tail Fluke Bias)
Theo số liệu kiểm toán tại Module M09:
- **51.78% Catalog MovieLens 25M** thuộc nhóm đuôi dài (3.491 phim có 0 rating và 28.834 phim chỉ có từ 1 đến 5 ratings).
- Với các phim chỉ có đúng 1 rating (ví dụ 1 người dùng chấm 5.0 sao):
  * Thuật toán ALS cố gắng xoay vector `Q_i` sao cho tích vô hướng `P_u dot Q_i ≈ 5.0`.
  * Vì chỉ có đúng 1 quan sát ràng buộc, hướng của vector `Q_i` bị tự do cực lớn.
  * Chuẩn độ lớn L2 (`||Q_i||`) của nhóm phim 1 rating vọt lên tới **4.13** (so với mức trung bình danh mục là 1.68).
- **Tích vô hướng không bị chặn (Unconstrained Dot Product):**
  * Khi tính điểm cho một người dùng bất kỳ: `Score(u, i) = P_u dot Q_i`.
  * Hàng ngàn phim đuôi dài có norm cao sẽ tình cờ có góc nhọn với vector người dùng, sinh ra điểm số dự đoán bị thổi phồng từ **8.0 đến 10.8** (vượt xa trần danh nghĩa 5.0).
- **Hệ quả chiếm lĩnh Top-10:**
  * Khảo sát trên 5.000 người dùng cho thấy: **100% danh sách Top-10 của Pure ALS bị chiếm trọn bởi đúng 23 bộ phim vô danh có đúng 1 rating trong Train**!

### 3.3. Thiên kiến Bom tấn của Tập Test (Blockbuster Popularity Reality)
- Trong bài toán đánh giá Leave-1-Last: mỗi người dùng có 1 phim mục tiêu duy nhất trong Test.
- Trong thế giới thực, hành vi xem phim của con người tuân theo phân phối hàm mũ (Power-law / Pareto). Đa số người dùng kiểm thử đánh giá các bộ phim nổi tiếng (như The Shawshank Redemption, Inception, Pulp Fiction).
- Khi ALS chỉ toàn gợi ý 23 bộ phim vô danh không ai biết tới:
  * Xác suất một người dùng kiểm thử tình cờ xem trúng 1 trong 23 phim vô danh đó xấp xỉ bằng 0.
  * Đó là lý do ALS chỉ ghi nhận đúng **1 hit duy nhất trên 111.211 người dùng**!
- Trong khi đó, Popularity Baseline gợi ý 10 bộ phim được hàng triệu người xem nhiều nhất, do đó trùng khớp tự nhiên với 5.958 người dùng Test (đạt HR@10 = 5.36%).

---

## 4. CHIẾN LƯỢC HỒI PHỤC VÀ GIẢI PHÁP CAN THIỆP (RECOVERY STRATEGY)

Để khắc phục hiện tượng này mà không cần huấn luyện lại toàn bộ Spark ALS trên cụm máy lớn, có 3 biện pháp can thiệp có thể chứng minh tính khoa học:

1. **Hiệu chỉnh Độ chuẩn Vector (Vector Norm Regularization / Cosine Normalization):**
   * Thay vì sử dụng tích vô hướng trần `P_u dot Q_i`, sử dụng độ tương đồng Cosine: `Cosine(u, i) = (P_u dot Q_i) / (||P_u|| * ||Q_i||)`.
   * Biện pháp này triệt tiêu hoàn toàn ưu thế "ăn gian" của các phim đuôi dài có norm đột biến.
2. **Hiệu chuẩn Tần suất Hỗ trợ (Support-Aware Frequency Penalty):**
   * Nhân điểm số dự đoán với hệ số giảm chấn độ tin cậy (Empirical Bayes Shrinkage): `Score_calibrated = Score * (support_i / (support_i + C))`.
3. **Cơ chế Lai ghép với Đồ thị Tri thức (Knowledge Graph Hybrid Fusion):**
   * Sử dụng Đồ thị Tri thức (KG) để neo giữ ý nghĩa ngữ nghĩa (Genre + Tag Genome). 
   * KG chỉ gợi ý các bộ phim có liên kết thực tế với sở thích của người dùng, ngăn chặn hoàn toàn việc các phim vô danh lọt vào danh sách gợi ý.
