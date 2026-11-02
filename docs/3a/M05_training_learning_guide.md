# HƯỚNG DẪN HỌC TẬP VÀ CHUYỂN GIAO KIẾN THỨC SPARK ALS (MODULE M05)

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Chuyên đề:** Task 3A – Khối Gợi Ý Lọc Cộng Tác Phân Tán (Spark ALS Collaborative Filtering)  
> **Tài liệu:** Cẩm nang học tập dành riêng cho chủ dự án  
> **Mục tiêu:** Giúp chủ dự án làm chủ toàn diện từ lý thuyết mô hình lớn, cách thức Spark thực thi phân tán trên 24,6 triệu dòng, giải thích lưu loát các khái niệm và liên hệ trực tiếp với mã nguồn thực tế.

---

## I. 15 CÂU HỎI BẢN CHẤT GIẢI THÍCH DỄ HIỂU

### 1. Module M05 khác biệt căn bản gì so với Module M04?
- **M04 (Toy ALS):** Dùng dữ liệu siêu nhỏ (6 người, 7 phim) nhằm mục đích **chứng minh toán học**: kiểm tra từng bước tính tay của Golden Example, kiểm chứng công thức đạo hàm Ridge Regression và hiểu rõ nguyên lý luân phiên.
- **M05 (Full Training):** Bước vào bài toán **kỹ thuật dữ liệu lớn (Big Data Engineering)**: xử lý toàn bộ 24.675.013 tương tác thật trên Apache Spark, đối mặt với bài toán tối ưu bộ nhớ RAM, phân vùng dữ liệu, chống tràn bộ nhớ (OOM) và kiểm chứng mô hình có thể lưu/nạp an toàn phục vụ sản xuất.

### 2. Tại sao cần phải huấn luyện trên toàn bộ 24,6 triệu ratings thay vì lấy mẫu 1 triệu?
Lọc cộng tác dựa vào hiệu ứng mạng lưới (Network Effects) và các đường liên kết gián tiếp giữa người dùng. Trong không gian 62.423 bộ phim, hơn 80% số phim thuộc về nhóm "đuôi dài" (Long-Tail) với số lượng đánh giá ít. Nếu chỉ lấy mẫu 1 triệu dòng, phần lớn các bộ phim ít phổ biến sẽ bị mất trắng tương tác, khiến mô hình chỉ học được các phim bom tấn và hoàn toàn mất đi khả năng gợi ý cá nhân hóa sâu cho người dùng.

### 3. Apache Spark xử lý 24,6 triệu tương tác như thế nào mà không bị tràn RAM?
Spark sử dụng mô hình tính toán phân tán theo các Partition (phân vùng dữ liệu).
- Dữ liệu 24,6 triệu dòng được lưu dưới dạng Parquet nén Snappy (chỉ tốn khoảng 415 MB trên đĩa).
- Khi nạp vào Spark, dữ liệu được chia nhỏ thành 16 phân vùng xử lý song song trên 4 luồng CPU.
- Thuật toán ALS luân phiên phát thanh (Broadcast) các khối vector và thực hiện phép nhân ma trận cục bộ trên từng phân vùng, giải phóng bộ nhớ ngay sau mỗi chu kỳ mà không bao giờ nạp toàn bộ ma trận khổng lồ vào RAM cùng một lúc.

### 4. Tại sao hệ thống tuyệt đối không cần tạo ma trận đầy đủ (Dense Matrix)?
Ma trận đầy đủ gồm 162.541 người dùng × 62.423 bộ phim có kích thước lên tới **10,14 tỷ ô**.
- Nếu tạo ma trận này trong RAM, hệ thống cần tối thiểu `10.14 * 10^9 * 4 bytes ≈ 40.5 GB RAM`. Máy tính 16 GB RAM sẽ lập tức sập nguồn do lỗi Out-of-Memory.
- Trong thực tế, 99.74% số ô này là ô trống (chưa xem). Thuật toán Phân rã Ma trận chỉ lưu hai ma trận nhân tố cấp thấp: ma trận người dùng P (162.541 × 16) và ma trận phim Q (58.932 × 16). Tổng dung lượng RAM cần thiết chỉ là **14,2 MB**, giảm tải bộ nhớ tới 2.800 lần.

### 5. Lệnh `als.fit()` thực sự làm những công việc gì bên dưới?
Khi gọi `als.fit()`, Spark kích hoạt một chuỗi các công việc (Jobs & Stages):
1. Khởi tạo ngẫu nhiên ma trận vector bộ phim Q kích thước 58.932 × 16.
2. **Vòng lặp 1:** Cố định Q, duyệt qua từng phân vùng người dùng để giải hệ phương trình Ridge Regression tìm ma trận vector người dùng P tối ưu.
3. Cố định P vừa tìm được, duyệt qua từng phân vùng bộ phim để giải hệ phương trình Ridge Regression cập nhật lại ma trận Q.
4. Lặp lại quá trình luân phiên trên đúng 10 lần (`maxIter = 10`). Sau 10 chu kỳ, hai ma trận hội tụ và được đóng gói thành đối tượng `ALSModel`.

### 6. Vector đặc trưng người dùng và bộ phim được hình thành như thế nào?
Ban đầu, các vector là những con số ngẫu nhiên vô nghĩa. Qua mỗi vòng lặp giải bài toán bình phương tối thiểu, tọa độ của các vector được hiệu chỉnh dần để sao cho tích vô hướng `p_u^T * q_i` tiệm cận sát nhất với điểm số đánh giá thực tế của người dùng. Những người dùng có thói quen chấm điểm tương đồng sẽ có vector bị kéo lại gần nhau về mặt hướng, và các bộ phim thường được xem cùng nhau cũng có vector chỉ về cùng một miền không gian.

### 7. Tham số `rank` ảnh hưởng thế nào đến khả năng học của mô hình?
- **Rank nhỏ (ví dụ rank = 4 hoặc 8):** Không gian biểu diễn bị giới hạn. Mô hình chỉ nắm bắt được những xu hướng sở thích rất rộng (như mức độ giải trí, phim cũ vs phim mới) nhưng bỏ sót các gu thẩm mỹ tinh tế (Underfitting).
- **Rank lớn (ví dụ rank = 64 hoặc 128):** Mô hình có khả năng ghi nhớ rất chi tiết từng cá nhân nhưng tốn nhiều RAM, tính toán chậm và dễ ghi nhớ cả những nhiễu ngẫu nhiên trong dữ liệu (Overfitting).
- `rank = 16` là điểm cân bằng kỹ thuật phù hợp cho bước kiểm định M05 trước khi tiến hành dò quét tối ưu ở M07.

### 8. Tham số `regParam` (lambda) giúp hạn chế Overfitting ra sao?
`regParam` đóng vai trò như một sợi dây co giãn trừng phạt độ dài của vector. Trong công thức tối ưu:
```text
Tổn thất = Sai số bình phương + regParam * (Tổng độ dài vector P + Tổng độ dài vector Q)
```
Nếu một người dùng chỉ xem duy nhất 1 bộ phim và chấm 5 sao, thuật toán không có `regParam` sẽ kéo dài vector của người đó vô hạn để khớp đúng 5 sao. `regParam` buộc vector phải co lại sát gốc tọa độ, giữ cho mô hình thận trọng và không suy diễn quá mức từ các tương tác đơn lẻ.

### 9. Tham số `maxIter` có ý nghĩa gì đối với sự hội tụ?
`maxIter` xác định số lần cập nhật luân phiên giữa hai ma trận. Thường từ vòng lặp thứ 5 đến thứ 10, độ giảm sai số bắt đầu chậm dần (bão hòa). Đặt `maxIter = 10` giúp mô hình đạt điểm hội tụ đủ tốt mà không làm kéo dài thời gian huấn luyện hay làm phình to đồ thị RDD lineage của Spark.

### 10. Tại sao bắt buộc phải lưu mô hình ra đĩa cứng?
Quá trình huấn luyện trên 24,6 triệu dòng mất gần 1,5 phút CPU. Ở Module tiếp theo (M06 – Sinh ứng viên Top-N), hệ thống cần trích xuất các vector để tính điểm cho 162.541 người dùng trên toàn bộ 62.423 bộ phim. Nếu không lưu mô hình, mỗi lần chạy test hay phục vụ API ta lại phải huấn luyện lại từ đầu, gây lãng phí tài nguyên và không thể triển khai vào thực tế.

### 11. Làm sao ta biết được các vector học ra là hợp lệ, không bị lỗi toán học?
Hàm kiểm toán `audit_factors` tại dòng 194 của `trainer.py` kiểm tra 4 điều kiện khắt khe:
1. Số lượng vector phải khớp đúng số lượng thực thể (162.541 users, 58.932 movies).
2. Chiều dài mỗi vector phải bằng đúng `rank = 16`.
3. Quét sạch 100% các phần tử, bảo đảm không có giá trị rỗng (`NaN`) hay vô cực (`Infinity`).
4. Chuẩn vector L2 phải có giá trị dương hợp lý (trung bình 2.36 với user, 1.61 với movie), không bị bùng nổ số hay suy biến về 0.

### 12. Sai số Train RMSE và chỉ số gợi ý Top-N NDCG khác nhau ở điểm nào?
- **Train RMSE (0.7698):** Đo mức độ lệch điểm trên các phim **người dùng đã chấm rồi**. Người dùng không cần hệ thống dự đoán lại những phim họ đã xem.
- **Top-N NDCG:** Đo khả năng xếp hạng chính xác bộ phim mà người dùng **sẽ thích trong tương lai** trong số hàng chục ngàn bộ phim chưa xem. Một mô hình có Train RMSE rất thấp có thể xếp hạng sai vị trí của phim hay nhất, dẫn tới NDCG rất kém.

### 13. Vì sao M05 chưa thể tuyên bố ALS tốt hơn mô hình Popularity Baseline?
Vì M05 mới chỉ hoàn thành bước huấn luyện mô hình (Model Fitting). Để so sánh khoa học, ta bắt buộc phải dùng mô hình M05 để sinh danh sách Top-10 phim gợi ý cho toàn bộ 109.779 người dùng trong tập Validation và so sánh chỉ số NDCG@10 với mức chuẩn `0.0279` của Popularity Count. Bước đối đầu thực nghiệm này thuộc phạm vi của Module M06 và M08.

### 14. Module M06 sẽ sử dụng kết quả của M05 như thế nào?
Module M06 sẽ gọi `ALSTrainer.load_model('artifacts/models/als/m05_spark_als_rank16')`, nạp hai ma trận `userFactors` và `itemFactors`, sau đó thực hiện phép nhân ma trận phân tán `P * Q^T` để tìm ra Top-K bộ phim có điểm số cao nhất cho từng người dùng sau khi đã lọc bỏ các phim đã xem trong tập Train.

### 15. Những lỗi thường gặp khi làm việc với Spark ALS trên máy tính cá nhân là gì?
- **Lỗi 1 (Hadoop Winutils):** Quên cấu hình `HADOOP_HOME` dẫn đến lỗi `NativeIO$Windows.access0`. Đã được xử lý triệt để ở đầu tệp `trainer.py`.
- **Lỗi 2 (Driver OOM):** Dùng lệnh `train_df.toPandas()` hoặc `collect()` toàn bộ 24,6 triệu dòng về Python. Phải xử lý phân tán hoàn toàn trên Spark.
- **Lỗi 3 (Thứ tự phân vùng):** So sánh dự đoán mô hình gốc và mô hình nạp lại bằng cách zip danh sách mà không ánh xạ theo `(userId, movieId)`, gây ra sai số thứ tự giả tạo. Đã được khắc phục trong hàm `verify_reloaded_model`.

---

## II. CHUYÊN ĐỀ: “TỪ CODE ĐẾN KIẾN THỨC” (CODE-TO-CONCEPT MAP)

Bảng đối chiếu trực tiếp giữa khái niệm lý thuyết và vị trí triển khai trong mã nguồn dự án:

```text
+-----------------------+----------------------------------+-----------------------------------------------+
| Khái niệm Lý thuyết   | File & Dòng Code                 | Chức năng Triển khai                          |
+-----------------------+----------------------------------+-----------------------------------------------+
| Rank (Số chiều ẩn)    | recommender/als/trainer.py:48    | Khai báo rank=16 trong dataclass ALSConfig     |
| L2 Regularization     | recommender/als/trainer.py:50    | Khai báo reg_param=0.1 chống Overfitting      |
| Explicit Feedback     | recommender/als/trainer.py:51    | implicit_prefs=False, coi ô trống là chưa xem |
| Checkpoint Lineage    | scripts/run_m05_train_als.py:84  | sc.setCheckpointDir(...) chống tràn bộ nhớ DAG|
| ALS Model Fit         | recommender/als/trainer.py:191   | model = als.fit(train_df) thực thi tính toán  |
| Factor Inspection     | recommender/als/trainer.py:194   | audit_factors kiểm toán kích thước & NaN/Inf  |
| Prediction = Dot Prod | recommender/als/trainer.py:260   | verify_manual_dot_product chứng minh p_u^T*q_i|
| Model Persistence     | recommender/als/trainer.py:394   | save_model lưu trữ mô hình và manifest.json   |
| Safe Model Reload     | recommender/als/trainer.py:433   | load_model nạp lại ALSModel từ đĩa cứng       |
+-----------------------+----------------------------------+-----------------------------------------------+
```

---

## III. CÂU HỎI TỰ KIỂM TRA DÀNH CHO BẠN (SELF-CHECK QUIZ)

Hãy thử tự trả lời 3 câu hỏi này trước gương:
1. **Nếu giảng viên hỏi:** *"Em chứng minh bằng cách nào là dự đoán của Spark ALS thực chất chỉ là phép nhân vô hướng của 2 vector?"*
   - *Gợi ý trả lời:* Em mở file `recommender/als/trainer.py:260` hàm `verify_manual_dot_product`. Em lấy vector của user trong `model.userFactors` và phim trong `model.itemFactors`, tự nhân vô hướng bằng thư viện NumPy thì ra kết quả trùng khớp với cột `prediction` của Spark tới 7 chữ số thập phân (sai số cực đại chỉ 0.00000050).
2. **Nếu giảng viên hỏi:** *"Tại sao em không dùng Test set để kiểm tra xem mô hình ALS có bị học vẹt không?"*
   - *Gợi ý trả lời:* Theo nguyên tắc khoa học về chống rò rỉ dữ liệu (Data Leakage) đã quy định trong `docs/evaluation_protocol.md`, tập Test là chiếc chìa khóa niêm phong cuối cùng chỉ được mở duy nhất một lần ở Module M08 để báo cáo kết quả đồ án. Mọi quá trình thử nghiệm, chẩn đoán và tinh chỉnh tham số chỉ được phép thực hiện trên tập Train và tập Validation.
3. **Nếu giảng viên hỏi:** *"Sau khi chạy M05, em đã có danh sách gợi ý cho người dùng chưa?"*
   - *Gợi ý trả lời:* Dạ chưa, M05 là module huấn luyện và trích xuất các không gian vector đặc trưng ẩn. Việc sử dụng các vector này để nhân ma trận, tìm kiếm Top-K bộ phim có điểm số cao nhất cho 162.541 người dùng trên toàn bộ 62.423 phim catalog là trách nhiệm của Module M06 (Full-Catalog Top-N Candidate Generation).
