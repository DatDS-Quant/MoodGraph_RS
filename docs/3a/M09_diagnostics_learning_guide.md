# TÀI LIỆU HƯỚNG DẪN HỌC TẬP VÀ ÔN LUYỆN BẢO VỆ ĐỒ ÁN (M09)
# CHẨN ĐOÁN HỆ GỢI Ý: COLD-START, ĐUÔI DÀI, ĐỘ TIN CẬY NHÂN TỬ VÀ HIỆU NĂNG SPARK

**Chuyên đề:** Khối 3A – Mô hình đề xuất Spark ALS (Collaborative Filtering)  
**Tài liệu tham chiếu:** [M09_diagnostics_report.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_report.md)  
**Mục tiêu:** Cung cấp lý thuyết trực quan, phép tính đồ chơi (toy calculations) và 10 câu hỏi – đáp chuyên sâu giúp sinh viên bảo vệ xuất sắc đồ án trước hội đồng phản biện.

---

## PHẦN 1: BẢN CHẤT TOÁN HỌC & CÁC KHÁI NIỆM CỐT LÕI

### 1.1. Vấn đề "Fluke Bias" (Thiên lệch ngẫu nhiên đuôi dài) là gì?
Trong hệ gợi ý lọc cộng tác (Collaborative Filtering), hàm mất mát của ALS tối ưu hóa sai số bình phương trung bình (RMSE) trên các tương tác đã biết:

```text
Hàm mục tiêu:
L = Tổng_{(u, i) in R} (r_{ui} - P_u . Q_i)^2 + lambda * (Tong_u ||P_u||^2 + Tong_i ||Q_i||^2)
```

- Một bộ phim phổ biến (ví dụ The Matrix) có hàng chục ngàn đánh giá từ rất nhiều người dùng với sở thích khác nhau. Vector `Q_i` của bộ phim này bị "kéo" bởi hàng chục ngàn ràng buộc, khiến nó chỉ hội tụ tại vị trí phản ánh đúng thị hiếu trung bình.
- Ngược lại, một bộ phim vô danh ở đuôi dài (Long-Tail) chỉ có đúng 1 đánh giá 5.0 sao từ 1 người dùng duy nhất. Do chỉ có duy nhất 1 ràng buộc, thuật toán ALS tự do xoay vector `Q_i` sao cho nó gần như song song hoàn hảo với vector `P_u` của người dùng đó để triệt tiêu sai số `(5.0 - P_u . Q_i)^2 = 0`.
- Khi vector `Q_i` có hướng gần trùng với các vector người dùng tích cực, tích vô hướng `P_v . Q_i` của các người dùng khác cũng sẽ vọt lên rất cao (thậm chí đạt 8.0 đến 10.8 sao). Hệ thống tưởng rằng đây là phim "siêu phẩm" và đem nó đi gợi ý cho hàng loạt người dùng khác, dù thực tế không ai biết phim đó là gì. Đây chính là **Long-Tail Fluke Bias**.

### 1.2. Phép tính đồ chơi (Toy Calculation) minh họa Fluke Bias
Giả sử không gian tiềm ẩn 2 chiều (rank = 2), tham số điều chuẩn lambda = 0.1:

```text
User 1 (thích phim hành động): P_1 = [2.0, 0.0]
User 2 (thích phim hành động): P_2 = [1.8, 0.2]

Phim A (Head - Phổ biến, có 10.000 ratings): Q_A = [1.5, 0.1]
-> Điểm dự đoán User 2 xem Phim A: 
   Score = 1.8 * 1.5 + 0.2 * 0.1 = 2.70 + 0.02 = 2.72 (Mức điểm vừa phải)

Phim B (Tail - Vô danh, chỉ có 1 rating quan sát = 5.0 sao từ User 1):
Do chỉ có 1 ràng buộc, Q_B chủ yếu xoay theo vector P_1.
Dưới điều chuẩn L2 (lambda = 0.1), vector Q_B bị co nhẹ về gốc tọa độ:
   Q_B = [2.4, 0.0]
-> Điểm dự đoán cho User 1: P_1 . Q_B = 2.0 * 2.4 = 4.80 (sai số residual = 0.20, không phải nội suy chính xác 5.0)
-> Nhưng điểm dự đoán cho User 2 xem Phim B:
   Score = 1.8 * 2.4 + 0.2 * 0.0 = 4.32!
```

Mặc dù regularized ALS không nội suy tuyệt đối 5.0 sao (vẫn có sai số 0.20 do phạt L2 norm), điểm dự đoán của Phim B cho User 2 (4.32) vẫn vượt trội so với Phim A (2.72). Kết quả là Phim B đẩy văng Phim A ra khỏi danh sách Top-K!

---

## PHẦN 2: BỘ 10 CÂU HỎI – ĐÁP PHẢN BIỆN CHUYÊN SÂU TRƯỚC HỘI ĐỒNG

### Câu 1: Tại sao trong Module M08, mô hình Popularity Count lại có HitRate@10 cao hơn mô hình ALS tới gần 6.000 lần?
**Trả lời:**
- Hiện tượng này hoàn toàn bình thường và là một hiện tượng kinh điển trong hệ gợi ý thực tế.
- Tập kiểm định Test gồm các tương tác thực tế của người dùng. Người dùng thực tế chịu ảnh hưởng mạnh mẽ từ hiệu ứng xã hội và xu hướng truyền thông, do đó họ có xu hướng xem và đánh giá các bộ phim nổi tiếng (Head items chiếm đa số lượt xem).
- Mô hình Popularity gợi ý các phim có hàng chục ngàn lượt xem, do đó xác suất người dùng Test xem các phim này là rất cao (đạt HR@10 = 5.36%).
- Trong khi đó, pure ALS bị mắc kẹt bởi Long-Tail Fluke Bias: 100% Top-10 gợi ý của ALS cho 5.000 users cohort bị chiếm trọn bởi đúng 23 bộ phim có đúng 1 lượt đánh giá trong Train. Xác suất người dùng Test tình cờ xem các phim vô danh này gần như bằng 0 (chỉ đúng 1 hit trên 111.211 users).

### Câu 2: Có phải kết quả ALS HitRate thấp ở M08 là do lỗi lập trình (Bug) trong code M06/M08 không?
**Trả lời:**
- Tuyệt đối không. Module M09 đã thực hiện chẩn đoán độc lập và chứng minh code hoạt động chính xác 100%:
  1. Bảo toàn chính xác danh mục 62.423 phim qua 5 bins hỗ trợ.
  2. Phép tính tích vô hướng ma trận và bộ lọc tương tác đã xem đều được kiểm chứng độc lập bằng 4 synthetic oracles trong bộ unit test (15/15 tests PASS).
  3. Đây là hạn chế bản chất toán học của thuật toán Collaborative Filtering thuần túy khi huấn luyện trên ma trận thưa thớt (độ thưa 99.74%) mà không có hiệu chỉnh tần suất hoặc kết hợp tri thức ngoài.

### Câu 3: Tỷ lệ phim Cold-Start và ít tương tác trong MovieLens 25M là bao nhiêu?
**Trả lời:**
- Tổng danh mục có 62.423 phim.
- 3.491 phim (5.59%) hoàn toàn không có tương tác nào trong Train (0 ratings - Unscoreable).
- 28.834 phim (46.19%) chỉ có từ 1 đến 5 lượt đánh giá (Extreme Tail).
- Như vậy, tổng cộng 32.325 phim (51.78% toàn bộ catalog) thuộc nhóm có <= 5 ratings trong Train. Đây là một tập đuôi dài khổng lồ đặt ra thách thức cực lớn cho hệ thống.

### Câu 4: Phân phối độ chuẩn L2 (Norm) của latent factors nói lên điều gì về độ tin cậy của mô hình?
**Trả lời:**
- Độ chuẩn trung bình của item factor là 1.68 và user factor là 1.81.
- Tuy nhiên, ở các phim thuộc nhóm 1-5 ratings, độ chuẩn có biên độ dao động cực đại: từ 0.2058 (bị co mạnh về gốc tọa độ do regularization) đến tận 4.1289 (bị phóng đại quá mức để khớp điểm số duy nhất).
- Ngược lại, nhóm phim phổ biến (>50 ratings) có độ chuẩn ổn định từ 0.58 đến 2.33. Điều này cho thấy vector của các phim phổ biến có độ tin cậy biểu diễn hình học cao hơn hẳn các phim ở đuôi dài.

### Câu 5: Hệ số tương quan Pearson giữa log1p(support) và factor norm có ý nghĩa gì?
**Trả lời:**
- Hệ số Pearson đạt r = +0.157360 với p-value = 3.0e-323.
- Hệ số tương quan dương có ý nghĩa thống kê cực kỳ mạnh, chỉ ra rằng nhìn chung phim càng có nhiều đánh giá thì vector nhân tử càng có độ chuẩn lớn hơn (do tích lũy nhiều gradient từ nhiều tương tác), nhưng ở cục bộ các phim đuôi dài, phương sai độ chuẩn lại phân tán bất thường.

### Câu 6: Vì sao điểm dự đoán của ALS lại có giá trị lên tới 10.84, trong khi thang điểm MovieLens chỉ từ 0.5 đến 5.0?
**Trả lời:**
- Thuật toán ALS tiêu chuẩn của Spark thực hiện phép nhân ma trận tự do `P_u . Q_i^T` mà không có hàm kích hoạt phi tuyến (như Sigmoid) hay phép kẹp trần (Clipping).
- Khi một user factor có norm ≈ 2.5 và một item factor bị thổi phồng có norm ≈ 4.1 có hướng gần trùng nhau, tích vô hướng có thể đạt:
  `Score ≈ 2.5 * 4.1 * cos(theta) ≈ 10.25`.
- Trong thực nghiệm M09, có khoảng 0.2808% điểm số (165.481 cặp) vượt qua ngưỡng trần 5.0.

### Câu 7: Tại sao PyArrow và Spark DataFrame lại có sự khác biệt về thời gian nạp dữ liệu?
**Trả lời:**
- Phép đo PyArrow (0.65 giây cho 24.67M dòng) và Spark DataFrame (3.98 giây) phản ánh hai khối lượng công việc (workloads) và mục đích kiến trúc khác nhau:
  - PyArrow đọc 2 cột (`movieId`, `userId`) trực tiếp từ file snappy parquet cục bộ bằng thư viện C++ zero-copy vào RAM tiến trình Python, phù hợp cho tầng suy luận nhanh (candidate generation).
  - Spark DataFrame đọc phân tán trên 12 partitions của JVM, khởi tạo Catalyst logical/physical plan và chuẩn bị dữ liệu cho các phép biến đổi phân tán lớn (distributed ETL/training).
- Đây là hai thành phần bổ trợ nhau trong kiến trúc Big Data, không phải phép so sánh để tuyên bố một framework vượt trội hơn framework kia ở mọi tác vụ.

### Câu 8: Cơ chế chia lô (Batch Scoring) bằng NumPy BLAS tối ưu hóa bộ nhớ RAM như thế nào?
**Trả lời:**
- Thay vì tính toán toàn bộ ma trận 162.541 users x 58.932 items một lúc (sẽ tốn tới 38 GB RAM và gây lỗi Out-Of-Memory), nhóm chia người dùng thành các lô nhỏ (batch_size = 2.500).
- Kích thước bộ nhớ lý thuyết cho 1 lô:
  `2.500 users * 58.932 items * 4 bytes (float32) ≈ 589.32 MB`.
- Thực nghiệm M09 cho thấy tại batch_size = 2.500, bộ nhớ RAM đỉnh cô lập chỉ đạt 724.6 MB, nằm hoàn toàn dưới hạn mức an toàn 1.2 GB, đồng thời đạt thông lượng xử lý cực cao: 8.864 users/giây.

### Câu 9: Tại sao nhóm không tăng tham số điều chuẩn (regParam) lên thật cao để triệt tiêu Fluke Bias?
**Trả lời:**
- Nhóm đã thực hiện khảo sát tham số tại Module M07: thử nghiệm các mức `regParam` 0.1 (baseline), 0.3, 1.0, 3.0 trên tập Validation.
- Khi tăng `regParam` lên quá cao (1.0 hay 3.0), thuật toán co mạnh toàn bộ các vector về gốc tọa độ, làm suy giảm khả năng phân biệt sở thích giữa các người dùng và làm tăng đáng kể sai số RMSE.
- Điều chuẩn L2 chỉ co độ dài vector đồng đều chứ không thể bổ sung thông tin ngữ cảnh cho các item chỉ có 1 tương tác. Giải pháp thực tế là kết hợp với đồ thị tri thức (Knowledge Graph) và độ phổ biến tại khối Hybrid tiếp theo.

### Câu 10: Từ kết quả chẩn đoán M09, hướng phát triển cho Khối 3B (Knowledge Graph) và Hệ Hybrid sẽ là gì?
**Trả lời:**
- **Chiến lược Hybrid Blending:** Kết hợp điểm ALS với điểm tri thức (Graph Embedding/Path Score) và điểm phổ biến (Popularity Score):
  `Final_Score = w1 * ALS_Score + w2 * KG_Score + w3 * Popularity_Prior`.
- **Lọc hỗ trợ (Support Filtering):** Đối với các phim thuộc Bin 0 (chưa từng có tương tác) hoặc Bin 1-5 (ít tương tác), hệ thống sẽ dựa chủ yếu vào thông tin Đồ thị tri thức (đạo diễn, diễn viên, thể loại, tâm trạng mood) để đề xuất, thay vì tin cậy vào vector ALS bất ổn định.
- Đây chính là giá trị học thuật cốt lõi của đề tài: chứng minh vì sao cần Đồ thị tri thức để giải quyết bài toán Cold-Start mà các mô hình Collaborative Filtering truyền thống bất lực.

