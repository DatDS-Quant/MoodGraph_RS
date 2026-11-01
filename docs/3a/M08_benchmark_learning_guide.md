# TÀI LIỆU HƯỚNG DẪN KIẾN THỨC BẢO VỆ M08 (M08 BENCHMARK LEARNING GUIDE)

Tài liệu này được biên soạn để hỗ trợ chủ dự án MoodGraph nắm vững bản chất khoa học, nguyên lý phân tách dữ liệu và trả lời trọn vẹn mọi câu hỏi phản biện của giảng viên và hội đồng kỹ thuật.

---

### Câu hỏi 1: Tập Test khác tập Validation thế nào trong Machine Learning và Recommender Systems?
- **Tập Validation (Tập Kiểm định):** Được dùng để tối ưu hóa, tinh chỉnh siêu tham số (hyperparameter tuning), so sánh giữa các biến thể kiến trúc và đưa ra quyết định chọn ra mô hình tốt nhất (model selection). Nhà nghiên cứu được phép nhìn vào kết quả Validation nhiều lần trong quá trình thử nghiệm.
- **Tập Test (Tập Kiểm thử Độc lập):** Là tập dữ liệu bị khóa kín ("Vault"), đại diện cho tương lai hoàn toàn chưa biết. Tập Test chỉ được mở ra **đúng một lần duy nhất (Single-Shot)** sau khi toàn bộ mô hình và quyết định chọn lựa đã được đóng băng hoàn toàn. Kết quả trên tập Test dùng để báo cáo năng lực khái quát hóa khách quan và tuyệt đối không được dùng để quay ngược lại sửa đổi mô hình.

---

### Câu hỏi 2: Vì sao bắt buộc phải đóng băng (Freeze) mô hình trước khi mở tập Test?
- Nếu mở tập Test khi chưa đóng băng mô hình, kỹ sư sẽ có xu hướng "nhìn trộm" (data snooping / test leakage) và điều chỉnh siêu tham số sao cho điểm Test cao nhất. Hiện tượng này gọi là **Overfitting trên tập Test (Test Set Overfitting)**. Khi đó, tập Test mất hoàn toàn giá trị đo lường khả năng tổng quát hóa thực tế của hệ thống.

---

### Câu hỏi 3: Vì sao bộ lọc phim đã xem tại Test bắt buộc dùng Train ∪ Validation?
- Trong thực tế đời sống, thời gian trôi qua theo chuỗi: `Train -> Validation -> Test`.
- Khi hệ thống gợi ý phim cho người dùng tại thời điểm kiểm thử Test, người dùng **đã từng xem** các bộ phim trong quá khứ xa (tập Train) VÀ **đã xem** cả bộ phim ở quá khứ gần (tập Validation).
- Nếu chỉ lọc bỏ tập Train mà không lọc tập Validation, hệ thống sẽ có nguy cơ gợi ý lại chính bộ phim người dùng vừa mới xem tại bước Validation. Việc loại trừ cả hai (`seen_u = Train_u ∪ Validation_u`) bảo đảm bài toán gợi ý phim mới hoàn toàn khách quan.

---

### Câu hỏi 4: Vì sao mô hình ALS và Popularity vẫn CHỈ được huấn luyện trên tập Train?
- Để bảo đảm tính công bằng tuyệt đối với quy trình offline và tính độc lập của việc chọn mô hình:
  1. Nếu ta gộp Validation vào Train để huấn luyện lại mô hình, các vector latent factor của ALS và các số đếm rating count sẽ bị thay đổi. Khi đó, mô hình đánh giá trên Test không còn là mô hình `ALS_R8_REG0.3_ITER10` đã được chọn lựa tại M07 nữa.
  2. Bằng cách giữ nguyên mô hình đã học từ Train, ta kiểm tra chính xác khả năng của mô hình đó khi đối mặt với dữ liệu tương lai mà nó chưa từng được học.

---

### Câu hỏi 5: Vì sao mẫu số tích cực của Test (111.211) không được copy từ Validation (109.779)?
- Trong giao thức User-wise Leave-1-Last:
  - Tương tác tại tập Validation là tương tác áp chót của người dùng.
  - Tương tác tại tập Test là tương tác cuối cùng của người dùng.
- Một người dùng có thể đánh giá phim áp chót là 3.0 sao (không thỏa mãn `rating >= 3.5`, thuộc nhóm non-positive ở Validation), nhưng ở tương tác cuối cùng họ lại đánh giá 4.5 sao (thỏa mãn `rating >= 3.5`, trở thành positive ở Test).
- Ngược lại, có người dùng đánh giá phim áp chót 5.0 sao nhưng phim cuối cùng chỉ 2.0 sao.
- Do đó, số lượng người dùng tích cực ở hai tập là độc lập ngẫu nhiên: Validation có 109.779 users, trong khi Test có 111.211 users. Việc đo lường chính xác trên đúng 111.211 users minh chứng tính trung thực khoa học, không sao chép giả mạo.

---

### Câu hỏi 6: Thế nào là một phép đối chuẩn công bằng (Fair Comparison)?
Một phép thử đối chuẩn giữa các thuật toán gợi ý chỉ được coi là công bằng khi thỏa mãn 5 nguyên tắc vàng:
1. **Cùng mẫu số đánh giá:** Cả 3 mô hình (Popularity Count, Popularity Weighted, ALS) đều được tính điểm trên đúng 111.211 người dùng.
2. **Cùng không gian danh mục:** Đều đối diện với toàn bộ 62.423 bộ phim của hệ thống MovieLens 25M.
3. **Cùng chính sách lọc đã xem:** Đều bị loại bỏ các phim thuộc `Train_u ∪ Validation_u`.
4. **Cùng quy tắc phá hòa thứ hạng:** `raw_score DESC, movieId ASC` để tránh thiên vị ngẫu nhiên.
5. **Cùng bộ thư viện và công thức đánh giá:** Đều dùng chung Module M02 TopNEvaluator.

---

### Câu hỏi 7: Vì sao Popularity Baseline lại đánh bại Spark Explicit ALS trên dữ liệu thực?
Có hai nguyên nhân cốt lõi về bản chất toán học:
1. **Lệch pha hàm mục tiêu (Objective Function Mismatch):**
   - Explicit ALS tối ưu hóa hàm sai số bình phương hồi quy (RMSE) trên các ô ma trận đã có rating:
     `min ∑ (r_ui - u_u · v_i)^2 + λ(||u_u||^2 + ||v_i||^2)`
   - Mô hình không được thiết kế trực tiếp để xếp hạng Top-N. Một bộ phim lạ lẫm chỉ có đúng 1 rating 5.0 sao sẽ có vector `v_i` tối ưu khớp hoàn hảo với điểm 5.0. Khi tính tích vô hướng cho toàn bộ người dùng, bộ phim này đạt điểm từ 5.0 đến 10.0, đẩy bay toàn bộ các phim kinh điển xuống dưới.
2. **Phân phối Đuôi dài (Long-Tail Fluke Bias):**
   - Hơn 95% danh sách Top-20 của Explicit ALS thuần túy bị ngập tràn bởi các phim có dưới 5 lượt đánh giá (phim cực hiếm). Trong khi đó, người dùng ngoài đời thực luôn có xu hướng xem và đánh giá các bộ phim phổ biến (Blockbusters, phim kinh điển). Popularity Count nắm bắt chính xác xác suất tiên nghiệm biên `P(Item)` này, nên đạt HitRate@10 vượt trội (5.36% so với 0.001%).

---

### Câu hỏi 8: Vì sao Catalog Coverage cao không đồng nghĩa với Độ chính xác (Accuracy)?
- Catalog Coverage đo lường tỷ lệ phần trăm số phim trong danh mục được hệ thống gợi ý cho ít nhất một người dùng.
- Một mô hình gợi ý ngẫu nhiên hoặc bị thiên lệch đuôi dài (Fluke Bias) có thể gợi ý hàng nghìn bộ phim lạ lẫm khác nhau cho các người dùng khác nhau, khiến Coverage tăng rất cao (vài phần trăm đến vài chục phần trăm). Tuy nhiên, vì người dùng không hề muốn xem các bộ phim lạ đó, HitRate và NDCG sẽ bằng 0.
- Do đó, trong hệ thống gợi ý, Coverage phản ánh độ đa dạng/khai phá, nhưng bắt buộc phải đi kèm với HitRate và NDCG để bảo đảm giá trị thực tế.

---

### Câu hỏi 9: Mục tiêu không thể chấm điểm (Unscoreable Targets) ảnh hưởng thế nào đến chỉ số?
- Có 29 bộ phim trong tập Test hoàn toàn không có lượt đánh giá nào trong tập Train (0 train ratings). Mô hình ALS không thể học được vector cho 29 bộ phim này.
- Nếu một hệ thống thiếu liêm chính loại bỏ 29 người dùng này khỏi mẫu số, HitRate sẽ tăng giả tạo.
- Theo quy chuẩn MoodGraph, 29 trường hợp này bắt buộc được giữ lại trong mẫu số (mẫu số vẫn là 111.211) và được tính là các ca trượt tự nhiên của mô hình.

---

### Câu hỏi 10: Giới hạn của giao thức kiểm định One-Held-Out Test là gì?
- Trong tập MovieLens 25M, Leave-1-Last chỉ giữ lại đúng 1 bộ phim cuối cùng làm Ground-Truth cho mỗi người dùng.
- Nếu người dùng có sở thích rộng và sẵn sàng thích 500 bộ phim khác nhau, hệ thống gợi ý đúng 20 bộ phim xuất sắc nhưng không trùng với bộ phim duy nhất rơi vào tập Test, kết quả vẫn bị đánh dấu là trượt (Hit = 0).
- Đây là giới hạn cố hữu của phương pháp kiểm thử offline với dữ liệu phản hồi ngầm định thưa thớt, cần được bổ sung bằng nghiên cứu người dùng (User Studies) hoặc A/B Testing trong môi trường sản xuất thực tế.

---

### Câu hỏi 11: Module M08 khác Module M09 thế nào?
- **M08 (Module hiện tại):** Tập trung vào **Hiệu năng Gợi ý Offline (Recommendation Accuracy & Ranking Quality)** trên tập Test đóng băng, so sánh công bằng giữa Popularity và ALS thuần túy.
- **M09 (Module tiếp theo):** Tập trung vào **Khảo sát Năng lực Tính toán Phân tán và Hành vi Cold-Start (Profiling & Scalability)**: đo lường thông lượng (throughput), thời gian mở rộng quy mô dữ liệu theo số lõi CPU, chi tiết hóa các tầng đuôi dài và đo lường độ trễ suy luận thực tế.
