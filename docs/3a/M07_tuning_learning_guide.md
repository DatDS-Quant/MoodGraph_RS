# SỔ TAY HỌC TẬP VÀ ÔN LUYỆN BẢO VỆ M07: TINH CHỈNH SIÊU THAM SỐ SPARK ALS

- **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị Tri thức và Apache Spark
- **Mã module:** M07 (Khối 3A – Spark ALS)
- **Tài liệu:** Sổ tay hướng dẫn học tập, tính tay và trả lời phản biện chuyên sâu trước hội đồng bảo vệ

---

## PHẦN 1: BẢN CHẤT TOÁN HỌC VÀ TÍNH TAY (TOY CALCULATIONS)

### 1. Phương trình nghiệm chính xác của Spark ALS-WR
Trong thư viện Spark MLlib, thuật toán ALS được cài đặt theo phương pháp ALS-WR (Weighted Regularization). Tại mỗi vòng lặp, khi cố định vector người dùng x_u, vector của item y_i được cập nhật thông qua phương trình chuẩn (Normal Equation):

```text
[ sum_{u in R_i} (x_u * x_u^T) + lambda * n_i * I ] * y_i = sum_{u in R_i} (r_{ui} * x_u)
```

Trong đó:
- `R_i` là tập hợp những người dùng đã đánh giá item `i`.
- `n_i = |R_i|` là số lượt đánh giá thực tế của item `i`.
- `lambda` chính là siêu tham số `regParam`.
- `I` là ma trận đơn vị kích thước `k x k` (với `k` là `rank`).

### 2. Ví dụ tính tay: Phim 1 lượt đánh giá vs Phim phổ biến
Giả sử không gian ẩn có `rank = 1`.
- Xét phim `A` (phim hiếm / fluke): chỉ có đúng 1 người dùng `u_1` đánh giá 5.0 sao (`n_A = 1`, `r_{1A} = 5.0`). Giả sử vector của người dùng này là `x_1 = 1.0`.
- Xét phim `B` (phim phổ biến): có 100 người dùng đánh giá (`n_B = 100`), điểm trung bình là 4.0 sao, trung bình `x_u^2 = 1.0`, do đó `sum x_u^2 = 100.0` và `sum (r_{uB} * x_u) = 400.0`.

**Trường hợp 1: lambda = 0.1**
- Với phim `A`:
  `y_A = (1.0 * 5.0) / (1.0^2 + 0.1 * 1) = 5.0 / 1.1 ≈ 4.545`
  Dự đoán điểm cho user `u_1`: `r_hat_{1A} = x_1 * y_A = 1.0 * 4.545 = 4.545`.
- Với phim `B`:
  `y_B = 400.0 / (100.0 + 0.1 * 100) = 400.0 / 110.0 ≈ 3.636`
  Dự đoán điểm cho user `u_1`: `r_hat_{1B} = 1.0 * 3.636 = 3.636`.
  -> Phim A (4.545) xếp trên Phim B (3.636).

**Trường hợp 2: Tăng lambda lên 1.0 (nhằm dập tắt overfitting)**
- Với phim `A`:
  `y_A = 5.0 / (1.0 + 1.0 * 1) = 5.0 / 2.0 = 2.500`
  Dự đoán điểm cho user `u_1`: `r_hat_{1A} = 2.500`.
- Với phim `B`:
  `y_B = 400.0 / (100.0 + 1.0 * 100) = 400.0 / 200.0 = 2.000`
  Dự đoán điểm cho user `u_1`: `r_hat_{1B} = 2.000`.
  -> Phim A (2.500) VẪN XẾP TRÊN Phim B (2.000)!

**Kết luận từ tính tay:** Vì số hạng điều chuẩn của Spark ALS là `lambda * n_i`, tỉ lệ phạt luôn được chuẩn hóa theo số quan sát `n_i`. Phim 1 lượt đánh giá 5.0 sao luôn giữ được điểm dự đoán cao hơn phim có nhiều quan sát trung bình, bất kể bạn tăng `lambda` lớn đến mức nào!

---

## PHẦN 2: 19 CÂU HỎI THẤU ĐÁO VỀ BẢN CHẤT HỆ THỐNG M07

1. **Tại sao không được phép tối ưu siêu tham số trực tiếp trên tập Test?**
   - Trả lời: Tối ưu trên Test gây rò rỉ dữ liệu (data leakage) và overfit lên tập kiểm thử. Tập Test chỉ được sử dụng một lần duy nhất tại M08 để báo cáo năng lực tổng quát hóa không thiên vị.
2. **Sự khác nhau cơ bản giữa Explicit ALS và Implicit ALS là gì?**
   - Trả lời: Explicit ALS giải bài toán hồi quy (regression) trên các ô ma trận đã quan sát điểm (1..5 sao), coi các ô trống là "chưa biết". Implicit ALS coi mọi ô là tín hiệu nhị phân (có tương tác / không tương tác) đi kèm độ tin cậy (confidence), phạt mọi tương tác âm.
3. **Tại sao Explicit ALS gặp Fluke Bias nghiêm trọng trong bài toán gợi ý Top-N?**
   - Trả lời: Do mục tiêu huấn luyện là giảm thiểu sai số bình phương RMSE trên các tương tác đã biết. Các phim chỉ có 1 lượt đánh giá 5.0 sao rất dễ được mô hình khớp điểm xấp xỉ 5.0, trong khi các phim đại chúng có phân bố điểm rộng hơn nên điểm dự đoán hiếm khi chạm mức tối đa.
4. **Tại sao tăng regParam trong Spark ALS lại không giảm được tỉ lệ phim 1-rating?**
   - Trả lời: Do cơ chế Weighted Regularization (ALS-WR) nhân thêm `n_i` vào ma trận phạt. Phim 1-rating bị phạt theo `lambda * 1`, trong khi phim phổ biến bị phạt theo `lambda * n_i`, khiến điểm dự đoán của phim phổ biến bị co (shrink) mạnh hơn hoặc ngang bằng với phim hiếm.
5. **Giao thức đánh giá hai tầng (Screening Cohort và Full Validation) mang lại lợi ích gì?**
   - Trả lời: Tiết kiệm tài nguyên tính toán (thời gian sinh gợi ý giảm từ ~3 phút xuống ~8 giây mỗi trial), cho phép rà soát nhiều tổ hợp siêu tham số trước khi chạy nghiệm thu toàn phần trên 109.779 người dùng.
6. **Cách lấy mẫu 5.000 người dùng trong Screening Cohort có bị thiên vị không?**
   - Trả lời: Không. Mẫu được chọn ngẫu nhiên tiền định (pseudo-random với seed 42 cố định) từ đúng danh sách người dùng tích cực của Validation, được lưu cố định ra file json để đảm bảo tính tái lập 100%.
7. **Tại sao Selection Oracle lại ưu tiên rank nhỏ hơn khi các chỉ số đánh giá bằng nhau?**
   - Trả lời: Áp dụng nguyên lý Dao cạo Occam (Occam's Razor). Khi các mô hình cho chất lượng tương đương, mô hình có số chiều ẩn nhỏ hơn (rank = 8) sẽ có kích thước bộ nhớ nhỏ hơn, tốc độ tính tích vô hướng nhanh hơn và chi phí lưu trữ thấp hơn.
8. **Mô hình finalist được chọn ở M07 là cấu hình nào?**
   - Trả lời: Cấu hình `ALS_R8_REG0.3_ITER10` (rank = 8, regParam = 0.3, maxIter = 10).
9. **Tại sao nhánh chẩn đoán ALS_PLUS_TRAIN_SUPPORT_FILTER lại được phân chia thành họ riêng?**
   - Trả lời: Để giữ tính liêm chính khoa học. Bộ lọc loại bỏ phim ít lượt đánh giá là một quy tắc can thiệp hậu xử lý (heuristic post-filtering), không phải năng lực tự thân của mô hình ma trận nhân tử hóa `ALS_ONLY`.
10. **Kết quả của nhánh chẩn đoán min_ratings = 20 chứng minh điều gì?**
    - Trả lời: Chứng minh các nhân tử tiềm ẩn của ALS thực chất có học được sở thích của người dùng (bằng chứng là đạt HitRate@10 = 0.00022 và kéo tỉ lệ phim phổ biến lên 76.04%), nhưng các tín hiệu này bị chôn vùi trong không gian Top-N bởi các mẫu nhiễu đuôi dài.
11. **Tại sao không tăng maxIter lên 20 hay 50?**
    - Trả lời: ALS thường hội tụ rất nhanh sau 10 vòng lặp. Tăng số vòng lặp chỉ làm các nhân tử khớp sát hơn nữa vào các điểm số ngoại lai của các phim ít lượt đánh giá, làm trầm trọng thêm hiện tượng overfitting.
12. **Tại sao số lượng phim duy nhất trong Top-10 của ALS (Catalog Coverage) lại rất thấp (21 đến 35 phim)?**
    - Trả lời: Vì một nhóm nhỏ các phim 1-rating 5-sao có vector đặc trưng tình cờ có góc nhọn với hầu hết các vector người dùng, khiến chúng xuất hiện lặp đi lặp lại trong danh sách gợi ý của hàng chục nghìn người dùng.
13. **Điều gì sẽ xảy ra nếu ta đánh giá trên tập người dùng không lọc rating >= 3.5?**
    - Trả lời: Giao thức đánh giá chuẩn quốc tế (RecSys) định nghĩa "Hit" là gợi ý được phim mà người dùng thực sự yêu thích (positive engagement). Nếu tính cả các phim bị đánh giá 1.0 - 2.0 sao là hit thì hệ thống đang gợi ý phim mà người dùng ghét.
14. **So với baseline Popularity M03, kết quả ALS ở M07 như thế nào?**
    - Trả lời: Thua kém hoàn toàn. Popularity Count đạt HR@10 = 0.09117, trong khi Explicit ALS đạt HR@10 = 0.00000. Đây là hiện tượng phổ biến đã được kiểm chứng khoa học khi đánh giá Top-N trên tập dữ liệu thưa thớt có đuôi dài lớn.
15. **Tại sao không sử dụng Implicit ALS ngay từ đầu ở Task 3A?**
    - Trả lời: Khối 3A được thiết kế theo đúng lộ trình sư phạm: nghiên cứu bản chất Explicit ALS cổ điển trên điểm số tường minh trước, ghi nhận giới hạn toán học của nó, từ đó tạo tiền đề vững chắc và động lực khoa học cho Task 3B (Knowledge Graph) và Task 3C (Hybrid).
16. **Phương thức tính toán của ALSCandidateGenerator có gây thắt nút cổ chai bộ nhớ không?**
    - Trả lời: Không. Generator xử lý theo từng khối (chunking/batching) 2.048 người dùng, sử dụng phép nhân ma trận NumPy BLAS tối ưu và giải thuật `argpartition` phân đoạn Top-K trên CPU đa luồng.
17. **Tại sao điểm số dự đoán của một số cặp user-item lại vượt quá 5.0 (ví dụ max score lên tới 10.5 - 12.5)?**
    - Trả lời: Do hàm mất mát của ALS là hồi quy tuyến tính không bị chặn trên. Tích vô hướng `x_u^T * y_i` có thể nhận bất kỳ giá trị thực nào từ -vô cùng đến +vô cùng nếu không có hàm kích hoạt phi tuyến tính (như sigmoid) ghim lại.
18. **Các tập tin artifact của M07 được tổ chức như thế nào?**
    - Trả lời: Được lưu trữ tập trung tại thư mục `artifacts/als/m07/` bao gồm: file gợi ý parquet đầy đủ 2.195.580 dòng, bảng so sánh csv, báo cáo phân tích đuôi dài csv, manifest json và cohort json.
19. **Thất bại về chỉ số của Explicit ALS có làm giảm giá trị của đồ án tốt nghiệp không?**
    - Trả lời: Hoàn toàn ngược lại, nó nâng tầm giá trị học thuật của đồ án. Một đồ án xuất sắc không phải là "ngụy tạo số liệu đẹp", mà là thực nghiệm bài bản, tìm ra bản chất vấn đề và chứng minh được lý do tại sao phương pháp đề xuất tiếp theo (Đồ thị tri thức) là bắt buộc.

---

## PHẦN 3: 10 TÌNH HUỐNG HỎI ĐÁP PHẢN BIỆN TRƯỚC HỘI ĐỒNG (DEFENSE Q&A)

### Tình huống 1: "Tại sao mô hình ALS phức tạp của em lại có HitRate bằng 0, thua cả một phép đếm Popularity đơn giản?"
- **Cách trả lời tự tin:**
  "Kính thưa Thầy/Cô, đây là một hiện tượng kinh điển trong hệ thống gợi ý đã được nghiên cứu của Cremonesi et al. (RecSys 2010). Explicit ALS được tối ưu hóa cho hàm mục tiêu RMSE trên các ô đã quan sát, chứ không tối ưu cho thứ hạng Top-N. Trong tập MovieLens 25M, có hàng chục nghìn phim chỉ có đúng 1 lượt đánh giá 5 sao. Mô hình Explicit ALS bị overfit vào các phim này và dự đoán điểm của chúng xấp xỉ 5 sao, đẩy chúng chiếm trọn danh sách Top-10 (Fluke Bias). Trong khi đó, người dùng trong tập kiểm định chủ yếu xem và đánh giá các phim có độ nhận diện cao. Do đó, Popularity có hit cao hơn, còn ALS thuần túy bị rơi vào bẫy đuôi dài."

### Tình huống 2: "Tại sao em tăng hệ số phạt regParam từ 0.1 lên 1.0 và 3.0 mà không chặn được hiện tượng overfit này?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, nguyên nhân nằm ở công thức ALS-WR của Spark MLlib. Số hạng điều chuẩn trong phương trình cập nhật của item là `lambda * n_i * I`. Nghĩa là hệ số phạt được nhân thêm với số lượng đánh giá `n_i` của chính item đó. Với phim 1 lượt đánh giá, hệ số phạt chỉ là `lambda * 1`. Còn với phim phổ biến có 50.000 lượt đánh giá, hệ số phạt là `lambda * 50.000`. Khi ta tăng lambda, điểm dự đoán của phim phổ biến bị co ép về 0 nhanh hơn rất nhiều so với phim 1 lượt đánh giá. Thực nghiệm tại M07 của em đã chứng minh: khi tăng regParam lên 1.0 và 3.0, tỉ lệ phim 1-rating trong Top-10 không những không giảm mà còn tăng từ 65.57% lên đúng 100%!"

### Tình huống 3: "Em có bằng chứng nào chứng minh các vector latent của ALS có học được sở thích của người dùng chứ không phải là một mô hình vô dụng?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, em đã thiết kế riêng một nhánh chẩn đoán đối chứng `ALS_PLUS_TRAIN_SUPPORT_FILTER`. Khi em giữ nguyên toàn bộ các vector latent của mô hình và chỉ áp dụng một bộ lọc mặt nạ loại bỏ các phim có dưới 20 lượt đánh giá, tỉ lệ phim đại chúng trong Top-10 lập tức tăng lên 76.04% và hệ thống ghi nhận ngay HitRate@10 dương (0.00022) trên tập Screening. Điều này chứng minh các vector tiềm ẩn vẫn nắm bắt được mối quan hệ sở thích, nhưng tín hiệu này đã bị các phim rác đuôi dài đè bẹp khi không có bộ lọc hỗ trợ."

### Tình huống 4: "Tại sao em không dùng luôn bộ lọc min_ratings = 20 làm kết quả chính thức của ALS để báo cáo số liệu đẹp hơn?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, đó là vấn đề về đạo đức và liêm chính nghiên cứu. Khối 3A có nhiệm vụ đánh giá chính xác năng lực tự thân của giải thuật Explicit ALS (`ALS_ONLY`). Bộ lọc số lượt đánh giá là một can thiệp ngoại vi (heuristic rule). Nếu em gộp chung vào, người nghe sẽ hiểu nhầm đó là sức mạnh của giải thuật ALS. Việc tách bạch rõ ràng giữa họ mô hình thuần túy và họ mô hình chẩn đoán giúp phân định chính xác đâu là năng lực của thuật toán và đâu là đóng góp của kỹ thuật xử lý dữ liệu."

### Tình huống 5: "Tại sao em chọn mô hình rank = 8 làm mô hình tốt nhất khi mà cả rank 8, 16, 32 đều có HitRate bằng 0?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, em đã xây dựng một bộ quy tắc lựa chọn tự động (Selection Oracle) dựa trên nguyên lý Occam's Razor. Khi các mô hình có độ đo đánh giá chính (NDCG@10 và HitRate@10) hòa nhau ở mức 0.0, bộ quy tắc sẽ tự động ưu tiên mô hình có độ phức tạp thấp nhất (rank nhỏ nhất). Cấu hình rank = 8 có thời gian huấn luyện chỉ mất 100.4 giây (so với 396.5 giây của rank 32), kích thước ma trận nhân tử giảm một nửa và tốc độ sinh gợi ý nhanh hơn đáng kể."

### Tình huống 6: "Em bảo vệ dữ liệu tập Test như thế nào trong quá trình tinh chỉnh siêu tham số?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, trong module `recommender/als/tuner.py`, em đã cài đặt hàm kiểm tra bảo vệ `guard_test_split_access`. Nếu bất kỳ tiến trình nào cố tình hoặc vô tình truyền đường dẫn chứa từ khóa `test` vào bộ tinh chỉnh, hệ thống sẽ chủ động ném ra ngoại lệ `PermissionError` và dừng thực thi ngay lập tức. Toàn bộ 5 lần thử nghiệm và 2 lần chẩn đoán tại M07 chỉ được phép tương tác với tập Train và Validation."

### Tình huống 7: "Tại sao em chỉ dừng lại ở 5 lần chạy thử nghiệm ALS mà không thử hàng trăm tổ hợp như Grid Search thông thường?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, mỗi lần huấn luyện ALS trên 24.675.013 dòng đánh giá của MovieLens 25M đòi hỏi tài nguyên phân tán đáng kể. Chúng em đã thiết kế không gian tìm kiếm có định hướng dựa trên giả thuyết khoa học: quét regParam để kiểm chứng khả năng dập tắt Fluke Bias, và quét rank để kiểm tra năng lực biểu diễn không gian ẩn. Khi kết quả toán học chỉ ra rõ ràng rằng cơ chế ALS-WR không thể khắc phục được nghịch lý này, việc tiếp tục đốt tài nguyên cho hàng chục lần chạy vô bổ là không có ý nghĩa khoa học."

### Tình huống 8: "Em có kiểm tra lại tính đúng đắn của code sinh gợi ý và bộ đánh giá không? Lỡ như HitRate bằng 0 là do code bị lỗi bug?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, toàn bộ bộ kiểm thử gồm 125 test cases đã được thực thi và đều vượt qua (100% PASS). Trong đó, module đánh giá M02 đã được chứng minh tính tay với 21 tests, module sinh ứng viên M06 đã vượt qua 21 tests kiểm tra từng biên tính toán, và tuner M07 có 6 tests kiểm tra sự độc lập của Selection Oracle. Đặc biệt, trên cùng một bộ đánh giá này, mô hình Popularity ở M03 đạt HitRate 9.11% và nhánh chẩn đoán M07 đạt HitRate dương. Do đó, kết quả bằng 0 hoàn toàn là bản chất toán học của mô hình, không phải do lỗi phần mềm."

### Tình huống 9: "Vậy bài học rút ra từ M07 để định hướng cho các giai đoạn tiếp theo (Task 3B và 3C) là gì?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, bài học lớn nhất là: một mô hình chỉ dựa trên điểm số đánh giá tường minh đơn thuần không thể giải quyết được bài toán gợi ý Top-N trên đồ thị người dùng - vật phẩm thực tế. Điều này mở ra sự cần thiết tất yếu của Khối 3B: sử dụng Đồ thị Tri thức (Knowledge Graph) để khai thác các mối quan hệ ngữ nghĩa phong phú như diễn viên, đạo diễn, thể loại; và Khối 3C: mô hình Lai (Hybrid) kết hợp Popularity, ALS và Graph Embeddings để vừa cá nhân hóa chính xác, vừa đảm bảo tính tin cậy thống kê."

### Tình huống 10: "Nếu được làm lại từ đầu với ALS, em sẽ thay đổi điều gì để mô hình đạt kết quả tốt hơn?"
- **Cách trả lời:**
  "Dạ thưa Thầy/Cô, nếu tiếp tục phát triển theo hướng Matrix Factorization, em sẽ chuyển đổi từ bài toán Explicit sang Implicit Feedback ALS (Hu, Koren, Volinsky, 2008) bằng cách coi rating >= 3.5 là tương tác dương với độ tin cậy `c_{ui} = 1 + alpha * r_{ui}`, đồng thời coi toàn bộ các phim chưa xem là tương tác âm với độ tin cậy thấp. Cơ chế này sẽ triệt tiêu hoàn toàn Fluke Bias vì các phim 1 lượt đánh giá sẽ bị kéo điểm xuống do thiếu quan sát trên toàn bộ không gian dữ liệu."
