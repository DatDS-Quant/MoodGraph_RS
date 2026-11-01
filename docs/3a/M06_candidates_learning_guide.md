# TÀI LIỆU HỌC TẬP VÀ BẢO VỆ ĐỒ ÁN: MODULE M06
## SINH ỨNG VIÊN TOP-N CHÍNH XÁC, LỌC PHIM ĐÃ XEM VÀ ĐÁNH GIÁ TRÊN TẬP VALIDATION

**Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị tri thức (Knowledge Graph) và Apache Spark  
**Module:** M06 – ALS Candidate Generation, Seen-Item Filtering, Top-N Ranking & Validation Evaluation  
**Branch:** `feature/als-3a`  
**Tác giả:** MoodGraph Engineering Team  

---

## MỤC LỤC
1. [Tổng quan Tri thức Module M06](#1-tổng-quan-tri-thức-module-m06)
2. [End-to-End Toy Example: Tính toán Tay từng bước](#2-end-to-end-toy-example-tính-toán-tay-từng-bước)
3. [18 Câu hỏi Cốt lõi & Trả lời Chi tiết](#3-18-câu-hỏi-cốt-lõi--trả-lời-chi-tiết)
4. [Từ Kiến thức đến Source Code (Defense Mapping)](#4-từ-kiến-thức-đến-source-code-defense-mapping)
5. [10 Câu hỏi Vấn đáp Bảo vệ Đồ án (Oral Defense Q&A)](#5-10-câu-hỏi-vấn-đáp-bảo-vệ-đồ-án-oral-defense-qa)

---

## 1. TỔNG QUAN TRI THỨC MODULE M06

Trong hệ thống gợi ý ma trận nhân tử (Matrix Factorization), việc huấn luyện mô hình ở M05 chỉ là một nửa chặng đường. Mô hình ALS sau khi hội tụ sẽ cung cấp hai ma trận vector tiềm ẩn:
- Ma trận người dùng `P` kích thước `N x d` (trong đó `N = 162,541`, số chiều ẩn `d = 16`).
- Ma trận vật phẩm `Q` kích thước `M x d` (trong đó `M = 58,932`, số chiều ẩn `d = 16`).

Mục tiêu của Module M06 là thực thi quá trình **suy luận (inference)**: biến các vector tiềm ẩn này thành danh sách Top-K bộ phim tốt nhất cho từng người dùng, tuân thủ nghiêm ngặt 3 nguyên lý kỹ thuật:
1. **Lọc triệt để phim đã xem trong Train (Seen-Item Filtering):** Người dùng không muốn được gợi ý lại những phim họ đã đánh giá trong lịch sử huấn luyện.
2. **Thuật toán Top-K chính xác (Exact Top-K):** Không dùng xấp xỉ lấy mẫu (sampling) gây thiếu hụt hay sai lệch ứng viên; áp dụng thuật toán phân vùng `argpartition` kết hợp sắp xếp cục bộ với độ phức tạp tuyến tính O(M).
3. **Phá vỡ thế hòa điểm tất định (Deterministic Tie-breaking):** Khi hai bộ phim có điểm số dự đoán bằng nhau, quy tắc `als_score DESC, sau đó movieId ASC` đảm bảo kết quả luôn tái lập 100% qua mọi lần chạy.

---

## 2. END-TO-END TOY EXAMPLE: TÍNH TOÁN TAY TỪNG BƯỚC

Để hiểu thấu đáo luồng dữ liệu, chúng ta cùng xem xét một kịch bản nhỏ gồm 1 người dùng (User 1) và catalog 6 bộ phim với số chiều ẩn d = 2.

### Bước 1: Trạng thái Vector ban đầu
- Vector người dùng: `p_u = [1.2, 0.8]`
- Catalog 6 phim và vector vật phẩm `q_i`:
  - Phim 101: `q_101 = [1.0, 1.0]`
  - Phim 102: `q_102 = [0.5, 2.0]`
  - Phim 103: `q_103 = [2.0, 0.5]`
  - Phim 104: `q_104 = [1.5, 0.5]`
  - Phim 105: `q_105 = [1.0, 1.0]` (chú ý: vector giống hệt Phim 101 để kiểm tra tie-breaking)
  - Phim 106: `q_106 = [0.2, 0.1]`

### Bước 2: Lịch sử tương tác trong Train (Seen Items)
Người dùng 1 đã xem và đánh giá 2 phim trong tập Train:
- `Seen(User 1) = {101, 103}`

Tập ứng viên chưa xem thực tế (Unseen candidate set):
- `Unseen(User 1) = {102, 104, 105, 106}` (tổng cộng 4 phim)

### Bước 3: Tính tích vô hướng thô (Raw Dot Product Scores)
Công thức: `r_hat_ui = dot(p_u, q_i)`
- `r_hat_u,101 = (1.2 * 1.0) + (0.8 * 1.0) = 1.2 + 0.8 = 2.00`
- `r_hat_u,102 = (1.2 * 0.5) + (0.8 * 2.0) = 0.6 + 1.6 = 2.20`
- `r_hat_u,103 = (1.2 * 2.0) + (0.8 * 0.5) = 2.4 + 0.4 = 2.80`
- `r_hat_u,104 = (1.2 * 1.5) + (0.8 * 0.5) = 1.8 + 0.4 = 2.20`
- `r_hat_u,105 = (1.2 * 1.0) + (0.8 * 1.0) = 1.2 + 0.8 = 2.00`
- `r_hat_u,106 = (1.2 * 0.2) + (0.8 * 0.1) = 0.24 + 0.08 = 0.32`

Bảng điểm thô ban đầu:
- Phim 103: 2.80 (Seen)
- Phim 102: 2.20 (Unseen)
- Phim 104: 2.20 (Unseen)
- Phim 101: 2.00 (Seen)
- Phim 105: 2.00 (Unseen)
- Phim 106: 0.32 (Unseen)

### Bước 4: Lọc phim đã xem bằng mặt nạ âm vô cực (-infinity Masking)
Ta gán điểm của các phim trong `Seen(User 1)` thành `-infinity`:
- `r_hat_u,101 = -infinity`
- `r_hat_u,103 = -infinity`

Mảng điểm sau khi lọc:
- Phim 101: `-inf`
- Phim 102: `2.20`
- Phim 103: `-inf`
- Phim 104: `2.20`
- Phim 105: `2.00`
- Phim 106: `0.32`

### Bước 5: Phân hạng Top-K (Chọn K = 3) và Xử lý Tie-Breaking
Cần chọn Top-3 phim chưa xem có điểm cao nhất:
- Xét hai ứng viên dẫn đầu có cùng điểm 2.20: Phim 102 và Phim 104.
  - Quy tắc tie-breaking: `als_score DESC, movieId ASC`.
  - Do `102 < 104`, Phim 102 xếp hạng 1, Phim 104 xếp hạng 2.
- Ứng viên tiếp theo: Phim 105 có điểm 2.00 > Phim 106 (0.32).
  - Phim 105 xếp hạng 3.
- Kết quả Top-3 gợi ý cho User 1:
  - Rank 1: `movieId = 102`, `score = 2.20`
  - Rank 2: `movieId = 104`, `score = 2.20`
  - Rank 3: `movieId = 105`, `score = 2.00`
  *(Phim 101 và 103 có điểm thô cao nhưng đã xem nên bị loại triệt để).*

### Bước 6: Đánh giá trên tập Validation
Giả sử trên tập Validation, User 1 có tương tác tích cực (rating >= 3.5) với danh sách:
- `Validation_Positives(User 1) = {104, 107}`

Đánh giá danh sách gợi ý `[102, 104, 105]`:
- Phim 102: Không có trong Validation Positives -> Miss.
- Phim 104: Nằm trong Validation Positives tại Rank 2 -> **HIT**!
- Phim 105: Không có trong Validation Positives -> Miss.

Tính toán chỉ số tại K = 3:
- `HitRate@3 = 1` (vì có ít nhất 1 hit trong Top-3).
- `DCG@3 = 1 / log2(rank + 1) = 1 / log2(2 + 1) = 1 / log2(3) = 1 / 1.58496 = 0.63093`
- `IDCG@3`: Vị trí lý tưởng nhất nếu Phim 104 ở Rank 1:
  - `IDCG@3 = 1 / log2(1 + 1) = 1 / log2(2) = 1.00000`
- `NDCG@3 = DCG@3 / IDCG@3 = 0.63093 / 1.00000 = 0.63093`

---

## 3. 18 CÂU HỎI CỐT LÕI & TRẢ LỜI CHI TIẾT

### Câu 1: Bản chất toán học của quá trình suy luận Top-N trong Matrix Factorization là gì?
Suy luận Top-N là quá trình tìm kiếm tập hợp con `S_u` gồm K phần tử từ tập vật phẩm chưa xem `U_u = I \ Seen_u` sao cho với mọi item `i` thuộc `S_u` và item `j` thuộc `U_u \ S_u`, ta luôn có:
`r_hat_ui >= r_hat_uj`, trong đó `r_hat_ui = p_u^T * q_i`.
Đây là bài toán cực đại hóa điểm số tiềm ẩn trên không gian vật phẩm còn lại của từng cá nhân.

### Câu 2: Tại sao r_hat_ui = p_u^T * q_i lại đại diện cho điểm dự đoán?
Mỗi chiều `k` trong không gian nhân tử biểu diễn một thuộc tính tiềm ẩn (ví dụ: yếu tố hành động, kỹ xảo, triết lý nghệ thuật, đạo diễn). Giá trị `p_uk` thể hiện mức độ ưa chuộng của người dùng với yếu tố `k`, còn `q_ik` thể hiện mức độ sở hữu yếu tố `k` của bộ phim `i`. Phép nhân vô hướng tổng hợp mức độ tương thích trên tất cả `d` chiều thành một đại lượng vô hướng dự báo mức độ yêu thích.

### Câu 3: Tại sao trong gợi ý thực tế phải lọc bỏ những phim user đã tương tác trong Train?
Gợi ý những bộ phim người dùng đã xem và đánh giá không mang lại giá trị khám phá mới (novelty/discovery) và không giúp người dùng đưa ra quyết định tiêu dùng mới. Trong giao thức đánh giá khoa học, nếu không lọc phim đã xem, mô hình sẽ có xu hướng gợi ý lại đúng những phim Train đạt 5 sao, gây hiện tượng rò rỉ và làm sai lệch chỉ số đánh giá khả năng tổng quát hóa trên tập Validation.

### Câu 4: Tại sao gán r_hat = -infinity trước khi Top-K lại ưu việt hơn lọc sau Top-K?
- Nếu lọc sau Top-K: Khi lấy Top-K từ toàn bộ catalog, nếu người dùng đã xem 8 phim trong Top-10 thì sau khi lọc chỉ còn lại 2 phim. Danh sách gợi ý bị thiếu hụt nghiêm trọng (không đủ K phần tử). Nếu lấy K' lớn hơn (oversampling) thì vẫn có nguy cơ thiếu với những người dùng có hàng nghìn lượt xem (như heavy user có 32,200 đánh giá).
- Khi gán `-infinity` trước Top-K: Các phim đã xem bị đẩy xuống đáy của thang đo. Bất kỳ thuật toán tìm Top-K nào cũng đảm bảo chọn ra đúng K ứng viên chưa xem có điểm cao nhất trong một lượt duy nhất mà không tốn thêm bộ nhớ.

### Câu 5: Khi nào xảy ra hiện tượng tie-breaking và tại sao tie-breaking ngẫu nhiên là tối kỵ?
Hiện tượng hòa điểm (tie) xảy ra khi nhiều vật phẩm có cùng điểm số dự đoán chính xác đến từng bit hoặc khi nhiều vật phẩm chưa từng xuất hiện có vector mặc định giống nhau. Nếu tie-breaking ngẫu nhiên:
- Kết quả gợi ý sẽ thay đổi sau mỗi lần chạy code, vi phạm tính tái lập khoa học.
- Đánh giá benchmark trên Validation sẽ trồi sụt ngẫu nhiên, không thể so sánh công bằng giữa các thuật toán.
Quy tắc chuẩn mực là sắp xếp theo điểm giảm dần, sau đó sắp xếp theo `movieId` tăng dần.

### Câu 6: Thuật toán Top-K exact nào tối ưu khi catalog M = 58,932?
- **Full Sort:** Sắp xếp toàn bộ mảng `M` phần tử tốn độ phức tạp `O(M log M)`. Với M = 58,932, phép tính tốn khoảng 930,000 phép so sánh cho mỗi user.
- **Min-Heap:** Duy trì heap kích thước K tốn `O(M log K)`. Với K = 20, tốn khoảng 260,000 phép toán nhưng chi phí overhead con trỏ trong Python rất lớn.
- **Quickselect / Argpartition:** Hàm `np.argpartition` đưa K phần tử lớn nhất về đầu mảng chỉ tốn thời gian tuyến tính trung bình `O(M)` (khoảng 60,000 phép toán), sau đó chỉ sắp xếp đúng K phần tử đó tốn `O(K log K)`. Đây là giải pháp nhanh nhất và tối ưu bộ nhớ nhất trong NumPy.

### Câu 7: Tại sao batching theo user (P_batch @ Q.T) nhanh hơn tính từng user hàng chục lần?
Khi tính từng user, CPU phải thực hiện phép nhân ma trận - vector (GEMV - BLAS Level 2) với tỷ lệ tái sử dụng cache rất thấp. Ma trận Q kích thước `58,932 x 16` liên tục bị nạp và đẩy ra khỏi CPU cache.
Khi gom nhóm thành batch `B = 2,048` người dùng, phép tính trở thành nhân ma trận - ma trận (GEMM - BLAS Level 3). CPU tận dụng triệt để bộ nhớ đệm L1/L2/L3 và các chỉ thị SIMD (AVX2/AVX-512), đạt thông lượng tính toán hàng chục GFLOPS và tăng tốc độ xử lý hơn 10 - 30 lần.

### Câu 8: BLAS level-3 matrix multiplication (GEMM) hoạt động như thế nào?
GEMM (General Matrix Multiply) chia nhỏ hai ma trận `P_batch` (B x d) và `Q^T` (d x M) thành các khối nhỏ (blocks/tiles) vừa khít với dung lượng cache L1/L2 của từng lõi CPU. Mỗi phần tử được nạp vào thanh ghi một lần và tái sử dụng nhiều lần cho các phép nhân cộng tích lũy, giúp tối đa hóa băng thông bộ nhớ và loại bỏ hiện tượng nghẽn cổ chai truyền dữ liệu từ RAM.

### Câu 9: Tại sao oversampling có thể sinh ra kết quả sai hoặc thiếu K ứng viên?
Nếu dùng chiến lược oversampling với hệ số `alpha` cố định (ví dụ lấy `K' = alpha * K = 100` ứng viên rồi lọc phim đã xem):
- Đối với người dùng thông thường có 20 phim đã xem, 100 ứng viên đủ để lọc ra 20 phim.
- Nhưng đối với người dùng cuồng nhiệt (heavy user có 32,200 phim đã xem), toàn bộ 100 ứng viên ban đầu có thể đều nằm trong danh sách đã xem! Sau khi lọc, danh sách gợi ý sẽ trả về 0 phần tử. Điều này chứng minh về mặt toán học rằng oversampling không thể đảm bảo tính đầy đủ của Top-K.

### Câu 10: Tại sao catalog chỉ có 58,932 phim trong khi MovieLens 25M có 62,423 phim? 3,491 phim đi đâu?
Tập MovieLens 25M gốc chứa 62,423 phim trong file `movies.csv`. Tuy nhiên, 3,491 phim này chưa từng nhận được bất kỳ lượt đánh giá nào trong toàn bộ lịch sử phân vùng hoặc chỉ xuất hiện ở các tập khác mà không có trong tập Train 24.67M ratings. Do ALS chỉ tạo nhân tử tiềm ẩn cho các vật phẩm có ít nhất một quan sát trong tập Train, ma trận `itemFactors` chỉ có đúng 58,932 hàng.

### Câu 11: 3,491 phim ngoài catalog ảnh hưởng thế nào đến tính công bằng khi đánh giá Validation?
Trong tập Validation, có 30 người dùng có tương tác tích cực rơi vào nhóm 3,491 phim không có vector ALS này.
Do mô hình ALS thuần túy không thể cho điểm những phim này, trần lý thuyết (theoretical ceiling) của HitRate đối với ALS trên tập Validation không thể đạt 100% mà bị giới hạn ở mức `(109,779 - 30) / 109,779 = 99.9727%`. Việc giữ nguyên mẫu số 109,779 người dùng là bắt buộc để đảm bảo tính trung thực khoa học, không gọt tỉa mẫu số để làm đẹp số liệu.

### Câu 12: HitRate@K và NDCG@K đo lường hai khía cạnh chất lượng gợi ý khác nhau như thế nào?
- **HitRate@K:** Đo lường tỷ lệ người dùng nhận được ít nhất một gợi ý chính xác trong danh sách Top-K (thước đo dạng nhị phân 0 hoặc 1). Nó phản ánh khả năng "bao phủ nhu cầu" của hệ thống.
- **NDCG@K (Normalized Discounted Cumulative Gain):** Không chỉ quan tâm có trúng hay không mà còn thưởng điểm rất cao nếu bộ phim trúng nằm ở các vị trí đầu tiên (Rank 1, 2) và phạt nặng nếu phim trúng nằm ở cuối danh sách (Rank K) nhờ hàm suy giảm logarit `1 / log2(rank + 1)`.

### Câu 13: Tại sao NDCG@K cần chuẩn hóa bằng IDCG@K và trường hợp IDCG = 0 được xử lý ra sao?
Mỗi người dùng có số lượng phim yêu thích trong tập Validation khác nhau (người có 1 phim, người có 10 phim). Nếu chỉ dùng DCG thô, người có nhiều phim trúng sẽ có điểm cao hơn bất kể thuật toán xếp hạng tốt hay xấu. IDCG@K (Ideal DCG) là điểm DCG tối đa có thể đạt được nếu tất cả các phim đúng được đưa lên đầu.
Khi người dùng không có bất kỳ tương tác tích cực nào trong tập Validation, `IDCG = 0`, theo quy ước chuẩn của RecSys, `NDCG` được gán bằng `0.0`.

### Câu 14: Phân tích hiện tượng Fluke Bias: tại sao mô hình ALS explicit mặc định lại đẩy các phim 1-rating 5-sao lên top?
Trong bài toán ALS Explicit với hàm mục tiêu bình phương tối thiểu có chính quy hóa L2:
- Những bộ phim kinh điển (như *Pulp Fiction*, *The Shawshank Redemption*) có hàng chục nghìn lượt đánh giá với điểm trung bình từ 4.2 đến 4.4. Vector tiềm ẩn của chúng bị ràng buộc bởi hàng vạn người dùng khác nhau, khiến điểm tích vô hướng hiếm khi vượt quá 4.5.
- Ngược lại, có 10,324 bộ phim trong tập Train chỉ có duy nhất 1 lượt đánh giá và lượt đánh giá đó tình cờ là 5.0 sao. Khi giải hệ phương trình ALS với tham số chính quy hóa mặc định `regParam = 0.1`, vector của những bộ phim này tự do xoay theo vector của người đánh giá duy nhất đó, khiến điểm dự đoán của chúng đạt từ 5.0 đến 5.3!
Hậu quả là danh sách Top-20 của hầu hết người dùng bị chiếm trọn bởi các bộ phim vô danh này (Fluke Bias), đẩy các bộ phim hay thực sự xuống thứ hạng hàng nghìn.

### Câu 15: Tại sao ALS explicit có thể cho kết quả Top-N kém hơn Popularity Count baseline trên tập dữ liệu thưa?
Do hiện tượng Fluke Bias nói trên, mô hình ALS explicit chưa được tinh chỉnh siêu tham số sẽ tối ưu điểm RMSE trên tập Train nhưng lại phá hỏng thứ tự xếp hạng tương đối (ranking order) trên tập Validation. Trong khi đó, Popularity Count baseline gợi ý các bộ phim có số lượt xem nhiều nhất toàn hệ thống - vốn là những phim có xác suất được xem lại ở tập Validation rất cao. Đây là minh chứng kinh điển cho thấy RMSE thấp không đồng nghĩa với Top-N Ranking tốt.

### Câu 16: Sự khác biệt căn bản giữa In-Sample Fit (RMSE trên Train) và Out-of-Sample Top-N Ranking (HitRate trên Validation)?
- **In-Sample Fit (RMSE):** Tối ưu hóa sai số khoảng cách giữa điểm dự đoán `r_hat_ui` và điểm thật `r_ui` trên các cặp đã quan sát trong quá khứ.
- **Out-of-Sample Top-N Ranking:** Đòi hỏi mô hình phải phân loại chính xác giữa hàng chục nghìn vật phẩm chưa xem để chọn ra K vật phẩm mà người dùng sẽ tiêu dùng trong tương lai. Tối ưu hóa RMSE có thể dẫn tới overfitting trên các điểm ngoại lai cục bộ mà không bảo tồn được cấu trúc xếp hạng toàn cục.

### Câu 17: Làm thế nào để mở rộng thuật toán từ exact full-scan sang Approximate Nearest Neighbors (ANN)?
Khi catalog tăng từ hàng vạn lên hàng chục triệu phim (như YouTube, Spotify), việc quét toàn bộ `O(M)` cho mỗi user trở nên quá chậm. Ta sử dụng các cấu trúc chỉ mục ANN như HNSW (Hierarchical Navigable Small World) hoặc ScaNN / FAISS:
- Thay vì tính tích vô hướng với mọi phim, thuật toán duyệt trên đồ thị không gian vector để tìm kiếm các láng giềng gần nhất.
- Đánh đổi: Tốc độ truy vấn tăng 100 - 1000 lần (độ trễ dưới 5ms), nhưng chấp nhận mất mát từ 1% đến 5% độ chính xác (Recall@K giảm nhẹ) so với thuật toán Exact Full-Scan.

### Câu 18: Trong hệ thống hybrid tiếp theo (Knowledge Graph + ALS), Top-N của ALS sẽ đóng vai trò gì?
Trong kiến trúc gợi ý đa tầng (Multi-Stage Recommender System):
1. **Tầng sinh ứng viên (Candidate Generation / Retrieval):** ALS đóng vai trò tạo ra một danh sách ứng viên phong phú (ví dụ Top-100 hoặc Top-200) dựa trên hành vi cộng tác tiềm ẩn (collaborative signals).
2. **Tầng xếp hạng lại (Re-ranking / Hybridization):** Đồ thị tri thức (Knowledge Graph) sẽ trích xuất các thuộc tính ngữ nghĩa (đạo diễn, diễn viên, thể loại, tâm trạng mood) và kết hợp với điểm số của ALS để loại bỏ Fluke Bias, đẩy các bộ phim thực sự phù hợp với ngữ cảnh của người dùng lên vị trí cao nhất.

---

## 4. TỪ KIẾN THỨC ĐẾN SOURCE CODE (DEFENSE MAPPING)

| Khái niệm / Nhiệm vụ Kỹ thuật | Cơ sở Toán học / Thuật toán | File Mã Nguồn | Lớp / Hàm Xử lý | Dòng Tham Chiếu |
| :--- | :--- | :--- | :--- | :--- |
| **Cấu hình & Giới hạn Bộ nhớ** | Bounded batch memory `B * M * 4 bytes` | [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`ALSCandidateConfig`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L35) | L35-L67 |
| **Catalog Điểm số Đủ điều kiện** | Ánh xạ ID phim sang index mảng `[0, M-1]` | [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`ScoreableCatalog`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L70) | L70-L105 |
| **Bộ chứa Vector Tiềm ẩn** | Nạp Parquet Spark sang contiguous NumPy | [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`UserFactorsContainer`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L108) | L108-L150 |
| **Oracle Tham chiếu Độc lập** | Python pure unoptimized ground-truth | [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`exact_top_k_oracle`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L153) | L153-L195 |
| **Top-K Tuyến tính Nhanh & Tie-break** | `argpartition` O(M) + lexsort tất định | [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`fast_exact_top_k_from_scores`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L198) | L198-L248 |
| **Nhân Ma trận Khối Bounded GEMM** | `P_batch @ Q.T` BLAS Level-3 | [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`ALSCandidateGenerator._score_batch`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L320) | L320-L335 |
| **Lọc Phim Đã Xem Tiền Xử lý** | Gán `-np.inf` cho `seen_indices` | [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`ALSCandidateGenerator._mask_seen`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L338) | L338-L352 |
| **Kiểm toán Catalog & Trần Lý thuyết** | Audit 62,423 vs 58,932 & Ceiling 99.97% | [`scripts/run_m06_als_topn.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py) | [`audit_catalog_eligibility`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py#L85) | L85-L135 |
| **Đánh giá Đa mức K (5, 10, 20)** | Gọi `TopNEvaluator` bảo toàn mẫu số 109,779 | [`scripts/run_m06_als_topn.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py) | [`run_evaluation_pipeline`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py#L220) | L220-L280 |

---

## 5. 10 CÂU HỎI VẤN ĐÁP BẢO VỆ ĐỒ ÁN (ORAL DEFENSE Q&A)

### Q1: Tại sao em không dùng hàm `recommendForAllUsers(20)` có sẵn của Spark MLlib mà lại tự viết `ALSCandidateGenerator`?
**Trả lời:** Hàm `recommendForAllUsers` của Spark MLlib tính toán trên toàn bộ catalog và **không hỗ trợ lọc bỏ các phim người dùng đã xem trong tập Train**. Hơn nữa, việc chuyển đổi kết quả từ DataFrame phân tán của Spark để đánh giá trên tập Validation ngoại tuyến tốn rất nhiều thời gian shuffle và dễ gây lỗi tràn bộ nhớ (OOM). Module tự viết tận dụng phép nhân ma trận GEMM trong NumPy, hỗ trợ lọc `-infinity` tại chỗ, đảm bảo quy tắc tie-breaking tất định và hoàn thành cho toàn bộ 162,541 người dùng chỉ trong hơn 3 phút trên một máy trạm đơn lẻ.

### Q2: Tại sao kết quả HitRate@10 của ALS rank 16 trên tập Validation lại là 0.00000 trong khi Popularity Count đạt 0.05519? Mô hình của em có bị lỗi code không?
**Trả lời:** Code hoàn toàn không có lỗi, đã được chứng minh qua 20/20 unit test và đối chiếu khớp 100% với Oracle toán học độc lập. Đây là hiện tượng khoa học có tên gọi **Fluke Bias** (thiên kiến vật phẩm hiếm):
- Trong tập Train có hơn 10,000 bộ phim chỉ có đúng 1 lượt đánh giá và đạt 5 sao. Mô hình ALS explicit với siêu tham số mặc định (`regParam = 0.1`) bị overfitting cục bộ vào các phim này, đẩy điểm số dự đoán của chúng lên mức 5.0 - 5.3.
- Kết quả là danh sách Top-20 bị chiếm trọn bởi các phim hiếm này. Trên thực tế tập Validation, người dùng hầu như không xem các phim này mà xem các phim phổ biến.
- Kết quả trung thực này phản ánh đúng bản chất của explicit ALS chưa tinh chỉnh và là cơ sở khoa học để chúng em bước vào Module M07 (Hyperparameter Tuning) và Module Knowledge Graph tiếp theo.

### Q3: Nếu giảng viên nghi ngờ hàm `fast_exact_top_k_from_scores` dùng `argpartition` có thể chọn nhầm phần tử khi có hòa điểm, em giải thích thế nào?
**Trả lời:** Em đã thiết kế hàm phát hiện ranh giới hòa điểm (straddling tie detection) tại dòng 230-245 trong [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L230). Nếu giá trị phần tử thứ `K-1` bằng với phần tử thứ `K` (tức là có các phần tử bằng điểm nhau nằm vắt ngang ranh giới chọn), thuật toán sẽ tự động mở rộng vùng phân vùng để lấy toàn bộ các ứng viên bằng điểm đó, sau đó áp dụng quy tắc sắp xếp từ điển `(-score, movieId)` để chọn ra đúng phần tử có `movieId` nhỏ nhất. Trường hợp này đã được kiểm thử nghiêm ngặt trong test case `test_04_tie_breaking_identical_scores`.

### Q4: Bộ nhớ của thuật toán có bị tràn khi nhân ma trận 162,541 users với 58,932 items không?
**Trả lời:** Hoàn toàn không. Thay vì tạo ra ma trận toàn cục kích thước `162,541 x 58,932` kiểu `float32` tốn tới **38.3 Gigabytes RAM**, em áp dụng chiến lược phân khối (chunking/batching) với kích thước `batch_size = 2,048`. Mỗi batch chỉ tiêu tốn:
`2,048 * 58,932 * 4 bytes = 482.7 Megabytes RAM`.
Bộ nhớ này được giải phóng ngay sau khi chọn Top-20 của batch đó, giúp chương trình chạy ổn định trên các máy tính cá nhân thông thường có từ 8GB đến 16GB RAM.

### Q5: Em xử lý trường hợp người dùng đã xem rất nhiều phim trong tập Train như thế nào?
**Trả lời:** Trong mã nguồn tại [`recommender/als/candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L338), các phim đã xem được chuyển đổi thành chỉ số mảng cột và gán giá trị `-np.inf`. Em đã viết riêng một adversarial test case `test_07_heavy_user_with_many_seen_items` mô phỏng người dùng đã xem 32,200 phim (tương đương người dùng tích cực nhất trong MovieLens 25M). Thuật toán vẫn chọn ra chính xác 20 phim chưa xem hàng đầu mà không bị sót hay giảm số lượng ứng viên.

### Q6: Tại sao em không gạt bỏ 30 người dùng có phim Validation nằm ngoài catalog 58,932 phim để tăng chỉ số HitRate?
**Trả lời:** Trong nghiên cứu khoa học hệ thống gợi ý, việc loại bỏ người dùng khó hoặc người dùng không trúng để làm đẹp số liệu là hành vi vi phạm đạo đức nghiên cứu (data tampering). Giao thức đánh giá chuẩn tại `docs/evaluation_protocol.md` quy định mẫu số đánh giá phải được cố định tuyệt đối ở 109,779 người dùng có tương tác tích cực trong tập Validation. Trần lý thuyết đạt được là 99.9727%, và việc giữ nguyên mẫu số phản ánh sự minh bạch và khách quan của đồ án.

### Q7: Tại sao hàm đánh giá lại sử dụng thang đo nhị phân (Binary Relevance) với ngưỡng rating >= 3.5?
**Trả lời:** Theo quy ước chuẩn của MovieLens và thang điểm 5 sao, mức đánh giá từ 3.5 trở lên đại diện cho việc người dùng thực sự thích và tán thành nội dung bộ phim. Các mức đánh giá từ 3.0 trở xuống (đặc biệt là 0.5 - 2.5) thể hiện sự thất vọng hoặc không thích; nếu hệ thống gợi ý một bộ phim mà người dùng xem xong đánh giá 1 sao thì đó là một gợi ý thất bại chứ không thể tính là một "Hit".

### Q8: So sánh chi phí tính toán giữa việc sinh Top-20 cho toàn bộ 162,541 users so với việc chỉ tính cho 109,779 users trong tập Validation?
**Trả lời:** Trong đồ án, em đã tạo đầy đủ Top-20 cho toàn bộ 162,541 người dùng xuất hiện trong tập Train (tổng cộng 3,250,820 dòng gợi ý) mất 198 giây. Điều này chứng minh hệ thống có năng lực phục vụ thực tế (serving capacity) ở quy mô sản phẩm hoàn chỉnh. Khi đánh giá, bộ đánh giá `TopNEvaluator` thực hiện phép nối nội (inner join) với danh sách người dùng Validation để tính toán chỉ số một cách khách quan.

### Q9: File Parquet lưu kết quả Top-20 có cấu trúc như thế nào và kích thước bao nhiêu?
**Trả lời:** File lưu tại `artifacts/als/m06/m06_als_top20_recommendations.parquet` có kích thước **19.38 MB** (được nén bằng chuẩn Snappy). Cấu trúc bảng gồm 4 cột tuân thủ đúng hợp đồng M00:
- `userId` (int32): Mã định danh người dùng.
- `movieId` (int32): Mã định danh bộ phim được gợi ý.
- `rank` (int32): Thứ hạng gợi ý từ 1 đến 20.
- `als_score` (float32): Điểm số tích vô hướng dự đoán.

### Q10: Nếu có thêm thời gian, em sẽ cải tiến điều gì ở Module M06?
**Trả lời:** Em sẽ thực hiện 2 cải tiến:
1. **Tích hợp chỉ mục vector bán cầu (Hemisphere/MIPS Indexing) bằng FAISS hoặc ScaNN:** Thay thế phép quét toàn bộ bằng tìm kiếm láng giềng gần nhất để giảm thời gian suy luận từ 198 giây xuống dưới 10 giây cho toàn bộ 162,541 người dùng.
2. **Áp dụng bộ lọc ngưỡng tần suất (Frequency Damping / Item Popularity Regularization):** Kết hợp một trọng số phạt nhẹ dựa trên số lượng đánh giá của vật phẩm để ngăn chặn triệt để hiện tượng Fluke Bias ngay tại tầng trích xuất ứng viên.
