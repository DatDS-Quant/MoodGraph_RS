# TÀI LIỆU NỀN TẢNG LÝ THUYẾT VÀ BẢO VỆ THUẬT TOÁN SPARK ALS (MODULE M04)

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Chuyên đề:** Task 3A – Khối Gợi Ý Lọc Cộng Tác Phân Tán (Spark ALS Collaborative Filtering)  
> **Mục tiêu:** Cung cấp tài liệu giáo khoa 20 luận điểm chuẩn mực bằng Tiếng Việt giúp chủ dự án tự tin nắm vững bản chất toán học, trả lời lưu loát mọi câu hỏi vấn đáp và chỉ đúng từng dòng mã nguồn khi bảo vệ đồ án trước hội đồng.

---

## MỤC LỤC 20 LUẬN ĐIỂM CỐT LÕI

1. [Bản chất của Lọc cộng tác (Collaborative Filtering)](#1-bản-chất-của-lọc-cộng-tác-collaborative-filtering)
2. [Tại sao phân rã ma trận (Matrix Factorization) giải quyết bài toán gợi ý](#2-tại-sao-phân-rã-ma-trận-matrix-factorization-giải-quyết-bài-toán-gợi-ý)
3. [Định nghĩa ma trận tương tác R, tập quan sát và độ thưa ma trận](#3-định-nghĩa-ma-trận-tương-tác-r-tập-quan-sát-và-độ-thưa-ma-trận)
4. [Vector đặc trưng ẩn của người dùng (User Latent Factor p_u)](#4-vector-đặc-trưng-ẩn-của-người-dùng-user-latent-factor-p_u)
5. [Vector đặc trưng ẩn của bộ phim (Item Latent Factor q_i)](#5-vector-đặc-trưng-ẩn-của-bộ-phim-item-latent-factor-q_i)
6. [Điểm số dự đoán thông qua tích vô hướng](#6-điểm-số-dự-đoán-thông-qua-tích-vô-hướng)
7. [Sự khác biệt cốt lõi giữa Explicit Feedback và Implicit Feedback](#7-sự-khác-biệt-cốt-lõi-giữa-explicit-feedback-và-implicit-feedback)
8. [Tại sao ô trống (missing rating) trong Explicit Feedback KHÔNG được xem là 0](#8-tại-sao-ô-trống-missing-rating-trong-explicit-feedback-không-được-xem-là-0)
9. [Hàm mục tiêu tối ưu hóa bình phương nhỏ nhất (Least Squares Objective)](#9-hàm-mục-tiêu-tối-ưu-hóa-bình-phương-nhỏ-nhất-least-squares-objective)
10. [Vai trò toán học của tham số chính quy hóa lambda và chuẩn Frobenius](#10-vai-trò-toán-học-của-tham-số-chính-quy-hóa-lambda-và-chuẩn-frobenius)
11. [Tại sao Matrix Factorization không lồi khi tối ưu đồng thời P và Q](#11-tại-sao-matrix-factorization-không-lồi-khi-tối-ưu-đồng-thời-p-và-q)
12. [Nguyên lý Alternating Least Squares: Cố định một bên để giải bài toán lồi](#12-nguyên-lý-alternating-least-squares-cố-định-một-bên-để-giải-bài-toán-lồi)
13. [Nghiệm đóng giải tích cập nhật User Factor p_u](#13-nghiệm-đóng-giải-tích-cập-nhật-user-factor-p_u)
14. [Nghiệm đóng giải tích cập nhật Item Factor q_i](#14-nghiệm-đóng-giải-tích-cập-nhật-item-factor-q_i)
15. [Minh họa tính tay từng bước qua Golden Example](#15-minh-họa-tính-tay-từng-bước-qua-golden-example)
16. [Cách Spark MLlib phân tán ma trận và cấu hình tham số](#16-cách-spark-mllib-phân-tán-ma-trận-và-cấu-hình-tham-số)
17. [Cách trích xuất userFactors và itemFactors trong Spark DataFrame](#17-cách-trích-xuất-userfactors-và-itemfactors-trong-spark-dataframe)
18. [Đối chiếu kết quả dự đoán của Spark với tích vô hướng thủ công](#18-đối-chiếu-kết-quả-dự-đoán-của-spark-với-tích-vô-hướng-thủ-công)
19. [Vấn đề Cold-Start và sự khác biệt giữa 'nan' và 'drop'](#19-vấn-đề-cold-start-và-sự-khác-biệt-giữa-nan-và-drop)
20. [Phản ví dụ hình học: Khoảng cách Euclidean không thay thế được tích vô hướng](#20-phản-ví-dụ-hình-học-khoảng-cách-euclidean-không-thay-thế-được-tích-vô-hướng)

---

### 1. Bản chất của Lọc cộng tác (Collaborative Filtering)
Lọc cộng tác (Collaborative Filtering - CF) dựa trên triết lý cốt lõi: *"Những người dùng có cùng sở thích trong quá khứ sẽ tiếp tục có chung sở thích trong tương lai"*.
Thay vì phân tích thuộc tính bề mặt của phim (như thể loại, diễn viên, đạo diễn) vốn đòi hỏi nhiều công sức dán nhãn thủ công và dễ bị phiến diện, CF chỉ cần ghi nhận hành vi chấm điểm của tập thể cộng đồng. Mối liên hệ tương đồng giữa hai bộ phim được phát hiện gián tiếp khi có nhiều người dùng cùng đánh giá cao cả hai phim đó.

### 2. Tại sao phân rã ma trận (Matrix Factorization) giải quyết bài toán gợi ý
Bài toán gợi ý thực chất là bài toán **hoàn thiện ma trận (Matrix Completion)**. Ta có một ma trận kích thước khổng lồ gồm hàng trăm ngàn người dùng và hàng chục ngàn bộ phim, nhưng phần lớn các ô đều bị bỏ trống.
Phân rã ma trận (Matrix Factorization - MF) giả định rằng hành vi chấm điểm phức tạp của con người được chi phối bởi một số lượng nhỏ k chiều đặc trưng tiềm ẩn (ví dụ: mức độ kịch tính, tính triết lý, nhịp độ phim). Bằng cách xấp xỉ ma trận lớn R thông qua tích của hai ma trận cấp thấp (low-rank matrices) P và Q, MF cho phép dự đoán điểm số tại mọi ô trống chưa từng được quan sát.

### 3. Định nghĩa ma trận tương tác R, tập quan sát và độ thưa ma trận
- Giả sử hệ thống có |U| người dùng và |I| bộ phim.
- Ma trận đánh giá R có kích thước |U| × |I|, trong đó phần tử r_{u,i} là điểm số người dùng u chấm cho phim i.
- Tập các cặp tương tác đã quan sát được ký hiệu là R = {(u, i) | r_{u,i} được xác định}.
- **Độ thưa (Sparsity):**
```text
Độ thưa = 1 - (|R| / (|U| × |I|))
```
Trong bộ dữ liệu MovieLens 25M, với 162,541 người dùng và 58,932 phim trong tập Train, tích |U| × |I| lên tới 9.58 tỷ ô, nhưng chỉ có 24,675,013 lượt đánh giá. Độ thưa thực tế đạt **99.7424%**. Điều này đồng nghĩa với việc hơn 99.7% ô trong ma trận là dữ liệu chưa quan sát được.

### 4. Vector đặc trưng ẩn của người dùng (User Latent Factor p_u)
Mỗi người dùng u được đại diện bởi một vector cột p_u trong không gian k chiều (p_u thuộc R^k). Vector này mô tả mức độ nhạy cảm hoặc độ yêu thích của người dùng đối với k khía cạnh tiềm ẩn trong điện ảnh.
Ví dụ: nếu chiều số 1 tình cờ liên quan đến "tính bạo lực, hành động dồn dập", một người đam mê phim Marvel sẽ có giá trị p_u[0] lớn, trong khi một người thích phim tình cảm nhẹ nhàng sẽ có giá trị p_u[0] thấp hoặc âm.

### 5. Vector đặc trưng ẩn của bộ phim (Item Latent Factor q_i)
Mỗi bộ phim i được biểu diễn bởi một vector cột q_i trong cùng không gian k chiều (q_i thuộc R^k). Vector này đo lường mức độ chứa đựng của bộ phim đối với từng khía cạnh tiềm ẩn nói trên.
Lưu ý quan trọng: Thuật toán không bao giờ tự đặt tên cho các chiều này là "Hành động" hay "Lãng mạn". Các chiều hoàn toàn là những con số trừu tượng (uninterpretable latent dimensions) do mô hình tự học nhằm cực tiểu hóa sai số dự đoán.

### 6. Điểm số dự đoán thông qua tích vô hướng
Điểm số dự đoán r_hat_{u,i} mà người dùng u dành cho phim i được tính bằng tích vô hướng (dot product) giữa hai vector:
```text
r_hat_{u,i} = p_u^T * q_i = ∑_{f=1}^k (p_u[f] * q_i[f])
```
Ý nghĩa toán học: Tích vô hướng đạt giá trị cực đại khi hướng sở thích của người dùng p_u trùng khít với đặc tính của bộ phim q_i. Nếu người dùng rất thích một khía cạnh và phim đó thể hiện mạnh mẽ khía cạnh đó, tích số sẽ rất cao.

### 7. Sự khác biệt cốt lõi giữa Explicit Feedback và Implicit Feedback
- **Explicit Feedback (Phản hồi tường minh):** Người dùng chủ động cho điểm số cụ thể (từ 0.5 đến 5.0 sao). Ta biết chính xác người dùng thích mức nào. Ô trống đại diện cho việc chưa xem (Missing Not At Random).
- **Implicit Feedback (Phản hồi ngầm định):** Hệ thống chỉ ghi nhận hành vi nhị phân (Click, Xem, Mua, Thời lượng nghe nhạc). Không có điểm chấm chê; tương tác chỉ thể hiện mức độ tự tin (Confidence) thay vì mức độ ưa thích thuần túy.
- Trong Task 3A MoodGraph, ta làm việc với MovieLens rating nên bắt buộc thiết lập cấu hình **`implicitPrefs=False`**.

### 8. Tại sao ô trống (missing rating) trong Explicit Feedback KHÔNG được xem là 0
Đây là một trong những lỗi căn bản nhất khi làm hệ thống gợi ý. Nếu coi các ô trống là điểm 0, thuật toán sẽ bị ép phải khớp 99.74% ma trận về giá trị 0.
Hậu quả: Mô hình hiểu nhầm rằng người dùng ghét cay ghét đắng gần như toàn bộ kho phim thế giới. Dự đoán cho các phim hay mà người dùng chưa kịp xem sẽ bị kéo sụt xuống 0, phá hủy hoàn toàn khả năng khám phá và gợi ý phim mới. Do đó, trong Explicit ALS, hàm tổn thất chỉ được phép tính tổng trên tập R các ô đã quan sát.

### 9. Hàm mục tiêu tối ưu hóa bình phương nhỏ nhất (Least Squares Objective)
Hàm tổn thất cần cực tiểu hóa trong Explicit Matrix Factorization được định nghĩa chuẩn xác như sau:
```text
L(P, Q) = ∑_{(u,i) ∈ R} (r_{u,i} - p_u^T * q_i)^2 + λ * (∑_u ||p_u||_2^2 + ∑_i ||q_i||_2^2)
```
- Số hạng đầu tiên: Tổng bình phương sai số giữa điểm số thực tế r_{u,i} và điểm dự đoán p_u^T * q_i trên tập quan sát R.
- Số hạng thứ hai: Thành phần phạt chính quy hóa L2 (Ridge Regularization) ngăn chặn vector bị phóng đại kích thước.

### 10. Vai trò toán học của tham số chính quy hóa lambda và chuẩn Frobenius
Tham số lambda (trong PySpark gọi là `regParam`) kiểm soát mức độ trừng phạt kích thước các vector nhân tố ẩn:
```text
||p_u||_2^2 = ∑_{f=1}^k (p_u[f])^2
```
Nếu không có lambda (lambda = 0), mô hình sẽ nhanh chóng rơi vào Overfitting: các vector của những người dùng chấm ít phim sẽ bị kéo dài tùy tiện để khớp hoàn hảo một vài điểm số cá biệt, dẫn tới sai số dự đoán rất tệ trên tập kiểm thử. Tuy nhiên, nếu đặt lambda quá lớn (ví dụ lambda = 10), vector nhân tố sẽ bị co ép (shrinkage) sát về 0, gây ra hiện tượng Underfitting.

### 11. Tại sao Matrix Factorization không lồi khi tối ưu đồng thời P và Q
Hàm mục tiêu L(P, Q) chứa thành phần tích chéo p_u^T * q_i. Khi coi cả hai ma trận P và Q đồng thời là biến số, đạo hàm bậc hai (ma trận Hessian) không xác định dương trên toàn miền không gian. Hàm mục tiêu không lồi (non-convex) và có vô số điểm yên ngựa (saddle points) cũng như cực tiểu cục bộ, khiến cho việc tối ưu hóa đồng thời bằng các phương pháp giải tích thông thường là bất khả thi.

### 12. Nguyên lý Alternating Least Squares: Cố định một bên để giải bài toán lồi
Thuật toán Luân phiên Bình phương Tối thiểu (ALS) đưa ra giải pháp giải bài toán non-convex này:
- **Bước 1:** Khởi tạo ma trận Q ngẫu nhiên. Cố định hoàn toàn Q, xem Q là hằng số. Lúc này, hàm tổn thất trở thành một hàm lồi bậc hai độc lập đối với từng vector người dùng p_u.
- **Bước 2:** Giải nghiệm đóng giải tích tối ưu cho từng p_u thông qua bài toán hồi quy Ridge Regression.
- **Bước 3:** Cố định ma trận P vừa tìm được. Lúc này hàm tổn thất lại trở thành hàm lồi bậc hai đối với từng vector phim q_i.
- **Bước 4:** Giải nghiệm đóng giải tích tối ưu cho từng q_i.
- **Bước 5:** Lặp lại luân phiên hai bước trên cho đến khi hàm tổn thất hội tụ hoặc đạt số vòng lặp tối đa `maxIter`.

### 13. Nghiệm đóng giải tích cập nhật User Factor p_u
Khi cố định toàn bộ item factors Q, lấy đạo hàm riêng của L theo p_u và cho bằng 0:
```text
∂L / ∂p_u = -2 * ∑_{i ∈ I_u} (r_{u,i} - p_u^T * q_i) * q_i + 2 * λ * p_u = 0
<=> (∑_{i ∈ I_u} q_i * q_i^T + λ * I_k) * p_u = ∑_{i ∈ I_u} r_{u,i} * q_i
```
Nghiệm đóng có dạng:
```text
p_u = (Q_{I_u}^T * Q_{I_u} + λ * I_k)^(-1) * Q_{I_u}^T * r_u
```
Trong đó:
- I_u là tập hợp các phim mà người dùng u đã đánh giá.
- Q_{I_u} là ma trận con chứa các vector q_i của các phim thuộc I_u.
- r_u là vector chứa các điểm số thực tế của người dùng u.
- I_k là ma trận đơn vị kích thước k × k. Ma trận (Q_{I_u}^T * Q_{I_u} + λ * I_k) luôn khả nghịch nếu lambda > 0.

### 14. Nghiệm đóng giải tích cập nhật Item Factor q_i
Tương tự, khi cố định toàn bộ user factors P, nghiệm đóng giải tích cho vector q_i của bộ phim i là:
```text
q_i = (P_{U_i}^T * P_{U_i} + λ * I_k)^(-1) * P_{U_i}^T * r_i
```
Trong đó U_i là tập hợp tất cả người dùng đã từng chấm điểm cho bộ phim i, và P_{U_i} là ma trận con gồm các vector p_u tương ứng.

### 15. Minh họa tính tay từng bước qua Golden Example
Xét bài toán nhỏ chuẩn mực:
- **Người dùng:** An (u1), Bình (u2)
- **Bộ phim:** Phim A (m1), Phim B (m2), Phim C (m3)
- **Tương tác thực tế:**
  - An chấm: Phim A = 2.0, Phim B = 4.0, Phim C = Chưa xem (Missing)
  - Bình chấm: Phim A = 1.0, Phim B = 2.0, Phim C = 1.5
- **Thiết lập:** rank k = 1, chính quy hóa lambda = 0.
- **Giả sử Item Factors hiện tại:**
  - q_A = [1.0], q_B = [2.0], q_C = [1.5]

**Bước A: Cập nhật User Factor cho An (p_An)**
- An xem phim A và B:
```text
Mẫu số: q_A^2 + q_B^2 = (1.0)^2 + (2.0)^2 = 1.0 + 4.0 = 5.0
Tử số: r_{An,A} * q_A + r_{An,B} * q_B = (2.0 * 1.0) + (4.0 * 2.0) = 2.0 + 8.0 = 10.0
=> p_An = 10.0 / 5.0 = 2.0
```

**Bước B: Cập nhật User Factor cho Bình (p_Binh)**
- Bình xem cả 3 phim A, B và C:
```text
Mẫu số: q_A^2 + q_B^2 + q_C^2 = (1.0)^2 + (2.0)^2 + (1.5)^2 = 1.0 + 4.0 + 2.25 = 7.25
Tử số: r_{Binh,A}*q_A + r_{Binh,B}*q_B + r_{Binh,C}*q_C = (1*1) + (2*2) + (1.5*1.5) = 1 + 4 + 2.25 = 7.25
=> p_Binh = 7.25 / 7.25 = 1.0
```

**Bước C: Cập nhật Item Factor cho Phim C (q_C)**
- Chỉ có duy nhất Bình chấm điểm phim C (r = 1.5):
```text
Mẫu số: p_Binh^2 = (1.0)^2 = 1.0
Tử số: r_{Binh,C} * p_Binh = 1.5 * 1.0 = 1.5
=> q_C_mới = 1.5 / 1.0 = 1.5
```

**Bước D: Dự đoán điểm số của An cho Phim C chưa từng xem**
```text
r_hat_{An, C} = p_An * q_C_mới = 2.0 * 1.5 = 3.0
```
Kết quả dự đoán bằng tay đạt chính xác **3.0 sao**. Đoạn code tại `recommender/als/toy_als.py:263` (`verify_golden_example_step`) thực hiện đúng quy trình này và đã vượt qua bài test tự động.

### 16. Cách Spark MLlib phân tán ma trận và cấu hình tham số
Trong cụm tính toán Apache Spark, việc nhân ma trận kích thước 162,541 × 58,932 được phân tán theo các Partition:
- Spark phân vùng các tương tác rating và thực hiện cơ chế Broadcast/Shuffle các khối vector nhân tố P và Q giữa Driver và các Executor.
- Các tham số cấu hình cốt lõi của `pyspark.ml.recommendation.ALS`:
  - `userCol='userId'`, `itemCol='movieId'`, `ratingCol='rating'`
  - `implicitPrefs=False`: Bắt buộc cho bài toán chấm điểm explicit.
  - `rank`: Số chiều của không gian nhân tố ẩn (thường chọn 8, 16, 32).
  - `maxIter`: Số chu kỳ luân phiên cập nhật (thường từ 10 đến 20).
  - `regParam`: Hệ số phạt L2 lambda (thường từ 0.01 đến 0.1).
  - `seed`: Giá trị hạt ngẫu nhiên giúp tái lập 100% kết quả huấn luyện.
  - `coldStartStrategy='nan'`: Giữ nguyên giá trị NaN khi gặp người dùng/phim lạ.

### 17. Cách trích xuất userFactors và itemFactors trong Spark DataFrame
Sau khi gọi `model = als.fit(train_df)`, mô hình `ALSModel` lưu trữ kết quả trong hai thuộc tính DataFrame phân tán:
- `model.userFactors`: Chứa hai cột `id: INT` (tương ứng userId) và `features: ARRAY<FLOAT>` (vector p_u có kích thước bằng rank).
- `model.itemFactors`: Chứa hai cột `id: INT` (tương ứng movieId) và `features: ARRAY<FLOAT>` (vector q_i có kích thước bằng rank).
Mã nguồn tại `recommender/als/toy_als.py:353` chuyển đổi các DataFrame này thành Python Dictionary gồm các mảng 1 chiều NumPy để phục vụ tính toán thủ công và kiểm toán độc lập.

### 18. Đối chiếu kết quả dự đoán của Spark với tích vô hướng thủ công
Để chứng minh bản chất toán học của Spark ALS chính là phép nhân vô hướng, đoạn code kiểm toán `verify_spark_vs_manual_dot` đã so khớp từng hàng dự đoán của Spark:
```python
spark_pred = model.transform(df)
manual_pred = np.dot(user_factors[u], item_factors[m])
```
Kết quả thực nghiệm trên toàn bộ 21 mẫu của tập Toy:
- Sai số tuyệt đối tối đa (Max Absolute Difference): **0.00000024** (2.4e-7).
- Sai số tuyệt đối trung bình (Mean Absolute Difference): **0.00000007** (7e-8).
- 100% các mẫu trùng khớp với ngưỡng dung sai nghiêm ngặt 1e-4.

### 19. Vấn đề Cold-Start và sự khác biệt giữa 'nan' và 'drop'
Hiện tượng Khởi động lạnh (Cold-Start) xảy ra khi hệ thống cần đưa ra dự đoán cho một người dùng mới (chưa có điểm train nào) hoặc một bộ phim mới phát hành:
- Khi gặp thực thể này, ALS không có dữ liệu để giải hệ phương trình Ridge Regression và vector nhân tố tương ứng không tồn tại.
- Spark cung cấp hai chiến lược thông qua `coldStartStrategy`:
  1. `coldStartStrategy='nan'`: Giữ nguyên hàng trong DataFrame dự đoán và điền giá trị `NaN` vào cột `prediction`.
  2. `coldStartStrategy='drop'`: Tự động loại bỏ hoàn toàn (xóa sổ) các hàng không dự đoán được khỏi DataFrame kết quả.
- **Tác động nguy hiểm đến đánh giá khoa học:**
  Nếu đặt `coldStartStrategy='drop'` trong quá trình đo đạc Top-N, các mục tiêu kiểm thử khó (unseen items) sẽ bị xóa bỏ một cách âm thầm. Khi đó, mẫu số đánh giá bị thu nhỏ lại, dẫn tới việc chỉ số Recall@K và NDCG@K bị thổi phồng giả tạo (metric inflation). Do đó, trong MoodGraph, ta luôn chọn `'nan'` và bộ đo `TopNEvaluator` bảo toàn 100% mẫu số thật của tập kiểm thử.

### 20. Phản ví dụ hình học: Khoảng cách Euclidean không thay thế được tích vô hướng
Nhiều người lầm tưởng rằng có thể dùng khoảng cách hình học Euclidean `||p_u - q_i||` hoặc cây tìm kiếm láng giềng k-d tree trong không gian nhân tố ẩn để tìm phim gợi ý cho người dùng. Đây là quan niệm sai lầm về mặt toán học.
Ta chứng minh bằng phản ví dụ xây dựng tại `recommender/als/toy_als.py:482`:
- Vector sở thích của người dùng hoạt động tích cực: p_u = [2.0, 0.0] (độ dài vector = 2.0).
- Bộ phim số 1: q_1 = [2.1, 0.1].
  - Khoảng cách Euclidean: `||p_u - q_1|| = sqrt((2.0 - 2.1)^2 + (0.0 - 0.1)^2) ≈ 0.1414` (Rất gần người dùng!).
  - Tích vô hướng điểm số: `p_u^T * q_1 = (2.0 * 2.1) + 0 = 4.20`.
- Bộ phim số 2: q_2 = [5.0, 0.0].
  - Khoảng cách Euclidean: `||p_u - q_2|| = sqrt((2.0 - 5.0)^2 + 0) = 3.0000` (Rất xa người dùng!).
  - Tích vô hướng điểm số: `p_u^T * q_2 = (2.0 * 5.0) + 0 = 10.00` (Điểm ưa thích cao gấp hơn 2.3 lần!).
- **Kết luận:**
  Xếp hạng gợi ý trong ALS phụ thuộc vào độ lớn của tích vô hướng `p_u^T * q_i`, vốn bị chi phối mạnh mẽ bởi độ dài chuẩn (norm) của vector phim. Một bộ phim kinh điển chất lượng cao thường có chuẩn vector lớn. Để tìm kiếm nhanh các ứng viên có tích vô hướng cao nhất, phải sử dụng thuật toán Tìm kiếm Tích vô hướng Cực đại (**Maximum Inner Product Search - MIPS**) chứ không thể dùng thuật toán tìm láng giềng khoảng cách Euclidean thông thường.
