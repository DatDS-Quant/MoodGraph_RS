# BẢN ĐỒ MÃ NGUỒN VÀ HƯỚNG DẪN BẢO VỆ MODULE M04 (SOURCE CODE DEFENSE MAP)

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Module:** M04 – ALS Theory, Toy Fit & Latent Factor Inspection  
> **Branch:** `feature/als-3a` | **Môi trường:** Python 3.12, PySpark 4.2.0, Windows 11  
> **Cam kết:** 100% số dòng và đường dẫn đã được kiểm tra thực tế trên workspace `D:\PROJECT BIG DATA\MoodGraph`.

---

## I. BẢN ĐỒ MÃ NGUỒN (SOURCE CODE LOCATIONS)

Bảng đối chiếu vị trí mã nguồn giúp chủ dự án mở chính xác tập tin và dòng code khi hội đồng phản biện yêu cầu:

| Chức năng Kỹ thuật | File | Dòng | Lệnh mở VS Code | Mô tả & Trách nhiệm Kỹ thuật |
| :--- | :--- | :--- | :--- | :--- |
| **Toy Dataset & Golden Setup** | `recommender/als/toy_als.py` | L37–L85 | `code -g recommender/als/toy_als.py:37` | Định nghĩa 6 người dùng, 7 bộ phim, 20 tương tác và cặp cold-start không có tương tác train. |
| **Dot Product Preference** | `recommender/als/toy_als.py` | L88–L105 | `code -g recommender/als/toy_als.py:88` | Hàm tính điểm dự đoán r_hat = p_u^T * q_i. Kiểm tra chiều vector nghiêm ngặt. |
| **Explicit ALS Loss** | `recommender/als/toy_als.py` | L108–L135 | `code -g recommender/als/toy_als.py:108` | Hàm tổn thất chính quy hóa L2. Tuyệt đối chỉ tính trên các cặp tương tác quan sát được (R). |
| **Closed-Form User Update** | `recommender/als/toy_als.py` | L138–L170 | `code -g recommender/als/toy_als.py:138` | Giải hệ phương trình Ridge Regression cập nhật vector p_u khi cố định item factors. |
| **Closed-Form Item Update** | `recommender/als/toy_als.py` | L173–L205 | `code -g recommender/als/toy_als.py:173` | Giải hệ phương trình Ridge Regression cập nhật vector q_i khi cố định user factors. |
| **Reference ALS Solver** | `recommender/als/toy_als.py` | L208–L260 | `code -g recommender/als/toy_als.py:208` | Bộ giải tham chiếu thuần Python/NumPy, theo dõi độ giảm đơn điệu của hàm tổn thất. |
| **Golden Example Step** | `recommender/als/toy_als.py` | L263–L308 | `code -g recommender/als/toy_als.py:263` | Tính toán từng bước bằng tay theo Golden Example: p_An = 2.0, p_Binh = 1.0, r_hat_An_C = 3.0. |
| **PySpark DataFrame Builder** | `recommender/als/toy_als.py` | L311–L325 | `code -g recommender/als/toy_als.py:311` | Chuyển đổi dữ liệu rating sang DataFrame kiểu dữ liệu chuẩn (userId INT, movieId INT, rating DOUBLE). |
| **PySpark ALS Fit** | `recommender/als/toy_als.py` | L328–L350 | `code -g recommender/als/toy_als.py:328` | Khởi tạo và huấn luyện ALS với implicitPrefs=False, cố định seed=42 và tham số rank, regParam. |
| **Extract Factors Matrices** | `recommender/als/toy_als.py` | L353–L373 | `code -g recommender/als/toy_als.py:353` | Trích xuất hai ma trận `userFactors` và `itemFactors` từ Spark ALSModel sang Python dict. |
| **Spark vs Dot Product Audit** | `recommender/als/toy_als.py` | L376–L438 | `code -g recommender/als/toy_als.py:376` | So khớp từng dự đoán của `model.transform()` với tích vô hướng p_u^T * q_i trong sai số 1e-4. |
| **Cold-Start Strategy Audit** | `recommender/als/toy_als.py` | L441–L479 | `code -g recommender/als/toy_als.py:441` | Đối chiếu coldStartStrategy 'nan' vs 'drop', chứng minh nguy cơ sai lệch mẫu số đánh giá. |
| **Euclidean vs Dot Proof** | `recommender/als/toy_als.py` | L482–L519 | `code -g recommender/als/toy_als.py:482` | Phản ví dụ hình học: khoảng cách Euclidean gần hơn nhưng điểm tích vô hướng lại thấp hơn. |
| **Pipeline Runner Script** | `scripts/run_m04_toy_als.py` | L51–L205 | `code -g scripts/run_m04_toy_als.py:51` | Kịch bản tự động hóa thực nghiệm 5 bước, xuất báo cáo JSON ra `artifacts/m04_toy_als_results.json`. |
| **Test Suite 13 Ca Kiểm Thử**| `tests/als/test_toy_als.py` | L40–L265 | `code -g tests/als/test_toy_als.py:40` | 13 ca kiểm thử tự động bao phủ tính tay, hội tụ, sai số Spark, cold-start và tính tất định. |

---

## II. BỘ CÂU HỎI VẤN ĐÁP BẢO VỆ CHUYÊN SÂU (ORAL DEFENSE Q&A)

Dưới đây là 5 câu hỏi trọng tâm thường gặp trong hội đồng thẩm định cùng câu trả lời mẫu 3–5 câu cô đọng, sắc bén:

### Câu 1: Vì sao thuật toán ALS không cần sử dụng tệp metadata `movies.csv` mà vẫn gợi ý được phim?
- **Trả lời:**
  ALS là phương pháp Lọc cộng tác (Collaborative Filtering) thuần túy dựa trên hành vi tương tác lịch sử giữa người dùng và sản phẩm. Thuật toán tự động phân rã ma trận tương tác R (user-item) thành tích của hai ma trận nhân tố ẩn P (User Factors) và Q (Item Factors) có số chiều k nhỏ hơn rất nhiều. Mọi đặc trưng của phim (như thể loại ngầm, phong cách đạo diễn, cảm xúc người xem) đều được tự động trừu xuất vào không gian vector ẩn thông qua thói quen chấm điểm chung của cộng đồng mà không cần gán nhãn thủ công từ `movies.csv`. Tệp `movies.csv` chỉ đóng vai trò từ điển tra cứu tên phim hiển thị cho người dùng ở tầng Serving.

### Câu 2: Nhân tố ẩn (Latent Factor) là gì? Có thể coi factor 0 là Action và factor 1 là Romance được không?
- **Trả lời:**
  Nhân tố ẩn (Latent Factor) là các chiều trừu tượng trong không gian toán học biểu diễn sở thích của người dùng và tính chất của bộ phim.
  Tuyệt đối **không được** tự ý gán nhãn cố định rằng factor 0 là Action hay factor 1 là Romance.
  Quá trình phân tích ma trận chỉ tối ưu hóa sai số bình phương nhỏ nhất chứ không có ràng buộc phân tách ngữ nghĩa độc lập. Do đó, mỗi chiều nhân tố là một tổ hợp phi tuyến tính phức tạp của nhiều yếu tố tiềm ẩn mà con người không thể định danh một cách đơn lẻ.

### Câu 3: Trong bài toán Explicit Feedback, vì sao các ô trống (missing ratings) không được gán bằng 0?
- **Trả lời:**
  Trong Explicit Feedback, thang điểm thực tế dao động từ 0.5 đến 5.0 sao, thể hiện mức độ ưa thích của người dùng đối với các phim đã xem. Một ô trống đại diện cho sự kiện "chưa xem" (unobserved) chứ không đồng nghĩa với "người dùng ghét phim và chấm 0 sao". Nếu tự ý điền 0 vào toàn bộ ô trống, thuật toán sẽ hiểu nhầm người dùng ghét 99.74% catalog, làm sụp đổ hoàn toàn phân phối xác suất và triệt tiêu khả năng dự đoán các bộ phim mà người dùng thực sự yêu thích nhưng chưa có cơ hội tiếp cận.

### Câu 4: Việc tăng tham số chính quy hóa regParam (lambda) lên quá lớn sẽ dẫn tới hậu quả gì?
- **Trả lời:**
  Tham số regParam (lambda) có nhiệm vụ phạt độ lớn chuẩn Frobenius của các vector nhân tố p_u và q_i nhằm chống hiện tượng Overfitting. Nếu tăng lambda lên quá lớn, đại lượng phạt regParam * I sẽ áp đảo hoàn toàn ma trận hiệp phương sai tương tác Q^T * Q. Kết quả là toàn bộ các vector nhân tố p_u và q_i sẽ bị kéo co cụm (shrinkage) về sát vector 0, khiến mọi tích vô hướng dự đoán r_hat = p_u^T * q_i đều suy giảm về 0 và mô hình rơi vào trạng thái Underfitting nghiêm trọng.

### Câu 5: Thuật toán ALS luân phiên cập nhật (Alternating) hai ma trận nhân tố nghĩa là gì?
- **Trả lời:**
  Hàm mục tiêu của phân tích ma trận chứa tích p_u^T * q_i nên không lồi (non-convex) khi tối ưu đồng thời cả P và Q. Thuật toán ALS giải quyết bài toán này bằng cách biến nó thành chuỗi các bài toán hồi quy lồi (convex Ridge Regression): khi cố định ma trận Q, hàm mục tiêu trở thành lồi bậc hai đối với từng p_u độc lập và có nghiệm đóng dạng giải tích. Ngay sau đó, cố định P và giải nghiệm đóng cho từng q_i. Quá trình luân phiên qua lại này đảm bảo giá trị hàm tổn thất giảm đơn điệu sau mỗi vòng lặp và nhanh chóng hội tụ về điểm cực tiểu cục bộ.

---

## III. KỊCH BẢN DEMO THỰC THI TRỰC TIẾP TRONG 5 PHÚT (5-MINUTE LIVE DEMO SCRIPT)

Khi được yêu cầu trình diễn trực tiếp trên máy chấm, thực hiện theo 3 bước sau:

### Bước 1: Khởi động và chạy toàn bộ kịch bản kiểm định thực nghiệm M04 (60 giây)
Mở terminal tại thư mục gốc của dự án và chạy:
```powershell
python scripts/run_m04_toy_als.py
```
**Điểm cần chỉ trên màn hình:**
- **Bước 1 (Golden Example):** Chỉ ra kết quả tính toán `p_An = 2.0000`, `p_Binh = 1.0000`, dự đoán An trên phim C = `3.0000`.
- **Bước 2 (Convergence):** Chỉ ra hàm tổn thất giảm từ `213.779` xuống `2.052` (giảm 99.04%).
- **Bước 3 (Spark Match):** Chỉ ra bảng so sánh 21 điểm rating: sai số giữa Spark transform và tích vô hướng thủ công là `0.00000024` (nhỏ hơn 1e-4 rất nhiều).
- **Bước 4 (Cold-Start):** Chỉ ra sự khác biệt giữa `'nan'` (giữ đủ 4 hàng) và `'drop'` (vứt bỏ mất 3 hàng).
- **Bước 5 (Euclidean Proof):** Chỉ ra ví dụ phim 1 khoảng cách gần (0.14) nhưng điểm thấp (4.20), phim 2 khoảng cách xa (3.00) nhưng điểm cao (10.00).

### Bước 2: Chạy kiểm thử tự động 13 bài test của Module M04 (30 giây)
```powershell
python -m pytest tests/als/test_toy_als.py -v
```
**Kết quả:** 13/13 tests PASSED 100%.

### Bước 3: Mở file mã nguồn và giải thích trực tiếp (120 giây)
- Mở file: `code -g recommender/als/toy_als.py:263`
- Giải thích đoạn code `verify_golden_example_step`: Cho hội đồng thấy công thức chia tích vô hướng với bình phương vector chuẩn, chứng minh sinh viên tự tay cài đặt thuật toán chứ không chỉ gọi thư viện đen.
