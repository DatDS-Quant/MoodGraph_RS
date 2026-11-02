# BÁO CÁO NGHIÊN CỨU & KIỂM TOÁN THỰC NGHIỆM: MODULE M06
## SINH ỨNG VIÊN TOP-N CHÍNH XÁC, LỌC PHIM ĐÃ XEM VÀ ĐÁNH GIÁ TRÊN TẬP VALIDATION

> **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị tri thức (Knowledge Graph) và Apache Spark  
> **Module:** M06 – Exact ALS Top-N Recommendation & Validation Evaluation  
> **Trạng thái:** ACCEPTED – VERIFIED (119/119 Tests PASS, HERMES 16/16 Valid)  
> **Branch:** `feature/als-3a` | **Mô hình Nguồn:** `artifacts/models/als/m05_spark_als_rank16/`  

---

## I. MỤC TIÊU VÀ RANH GIỚI KỸ THUẬT

Module M06 hiện thực hóa quá trình suy luận Top-N ngoại tuyến cho toàn bộ 162.541 người dùng trong MovieLens 25M bằng cách sử dụng các vector nhân tử tiềm ẩn từ mô hình ALS đã huấn luyện tại M05.

### Phân cấp Tuyên bố Khoa học (Epistemic Classification)
- **VERIFIED_FACT (Dữ kiện Đã Kiểm Chứng):**
  - Thuật toán sinh ứng viên Top-K khớp 100% với Oracle toán học độc lập trên mọi tập dữ liệu thử nghiệm.
  - 100% phim người dùng đã tương tác trong tập Train bị loại trừ triệt để bằng kỹ thuật gán điểm `-np.inf` trước Top-K.
  - Quy tắc tie-breaking (`als_score DESC, movieId ASC`) đảm bảo tính tất định trên cùng một môi trường runtime.
  - Phân bố thực tế các vị trí gợi ý trong Top-20: 63,80% vị trí thuộc về các phim chỉ có 1 lượt đánh giá trong Train; 95,89% thuộc về các phim có từ 1 đến 5 lượt đánh giá.
  - Điểm số Validation đo được: `HitRate@5 = 0.00000`, `HitRate@10 = 0.00000`, `HitRate@20 = 0.00000` trên 109.779 người dùng positive cohort.
- **EMPIRICALLY_SUPPORTED_EXPLANATION (Giải thích Có Cơ sở Thực nghiệm):**
  - Hiện tượng 0 hits tại M06 do Fluke Bias: Mô hình Explicit ALS với `regParam = 0.1` bị overfitting cục bộ vào 10.324 phim có 1 lượt đánh giá (đặc biệt là 820 phim đạt 5.0 sao), đẩy điểm số dự đoán của chúng lên mức 5.0 đến 9.6. Do đó, các phim này chiếm trọn Top-20 và đẩy các phim Validation tích cực thực tế xuống thứ hạng trung vị 3.990.
- **KNOWN_LIMITATION (Giới hạn Kỹ thuật Đã Biết):**
  - Có 3.491 phim trong catalog 62.423 phim không có lượt tương tác nào trong tập Train nên không có vector ALS. 30 người dùng có mục tiêu Validation rơi vào nhóm phim này không thể có điểm từ ALS thuần túy, giới hạn trần HitRate lý thuyết ở mức 99,9727%.
  - Tính tất định tuyệt đối qua các phần cứng và thư viện BLAS khác nhau (x86 vs ARM, MKL vs OpenBLAS) có thể bị ảnh hưởng nhẹ bởi sai số làm tròn số thực dấu phẩy động (1e-7).

---

## II. BẢNG ĐỐI CHIẾU THỰC NGHIỆM CHÍNH THỨC

Nguồn dữ liệu đối chiếu:
- **Popularity Baseline:** Đọc trực tiếp từ tệp gốc [`artifacts/m03_popularity_results.json`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/m03_popularity_results.json).
- **Spark ALS rank 16:** Đọc trực tiếp từ tệp gốc [`artifacts/als/m06/m06_als_evaluation_results.json`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m06/m06_als_evaluation_results.json).

Tập đánh giá: **109.779 người dùng** có tương tác tích cực trên tập Validation (rating >= 3.5), giao thức Leave-Two-Last-Out (Leave-1-Last cho Validation). Mẫu số đánh giá được bảo toàn tuyệt đối 100%.

| Thước đo (Metric) | K | Popularity Count (M03) | Spark ALS rank 16 (M06) | Tỷ lệ (ALS / Pop) | Ghi chú Phương pháp Luận |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **HitRate@K** | 5 | 0.03298 | 0.00000 | 0.00x | 3.621 hits (Pop) vs 0 hits (ALS) |
| **HitRate@K** | **10** | **0.05519** | **0.00000** | **0.00x** | **6.059 hits (Pop) vs 0 hits (ALS)** |
| **HitRate@K** | 20 | 0.08956 | 0.00000 | 0.00x | 9.832 hits (Pop) vs 0 hits (ALS) |
| **NDCG@K** | 5 | 0.02079 | 0.00000 | 0.00x | Pop: Phim trúng tập trung ở rank đầu |
| **NDCG@K** | **10** | **0.02789** | **0.00000** | **0.00x** | IDCG = 1.0 (chuẩn hóa single-target) |
| **NDCG@K** | 20 | 0.03649 | 0.00000 | 0.00x | Hàm suy giảm logarit vị trí |
| **Precision@K** | 5 | 0.00660 | 0.00000 | 0.00x | Pop: 3.621 / (109.779 * 5) |
| **Precision@K** | **10** | **0.00552** | **0.00000** | **0.00x** | Pop: 6.059 / (109.779 * 10) |
| **Precision@K** | 20 | 0.00448 | 0.00000 | 0.00x | Pop: 9.832 / (109.779 * 20) |
| **Catalog Coverage** | 5 | 0,35% (218 phim) | 1,50% (938 phim) | 4.3x | ALS bao phủ danh mục rộng hơn |
| **Catalog Coverage** | **10** | **0,50% (310 phim)** | **2,48% (1.545 phim)**| **5.0x** | ALS gợi ý đa dạng phim hơn |
| **Catalog Coverage** | 20 | 0,74% (460 phim) | 4,05% (2.528 phim)| 5.5x | Trên toàn bộ 62.423 phim catalog |

---

## III. KIỂM ĐỊNH THỰC CHỨNG GIẢ THUYẾT FLUKE BIAS

Để xác minh độc lập nguyên nhân dẫn đến `HitRate = 0`, nhóm kiểm toán đã quét toàn bộ 3.250.820 vị trí gợi ý Top-20 và 24.675.013 đánh giá tập Train.

### 1. Phân bố Lượt Đánh giá Train của Phim trong Danh sách Gợi ý Top-20

| Nhóm Lượt Đánh giá trong Train | Số Vị trí Gợi ý (Slots) | Tỷ lệ Vị trí (%) | Số Phim Độc nhất | Tỷ lệ Phim (%) | Nhận xét Thực nghiệm |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Đúng 1 Train rating** | **2.074.146** | **63,80%** | 129 | 4,57% | **Chiếm đa số tuyệt đối các slot gợi ý** |
| **Từ 2 đến 5 Train ratings** | **1.043.111** | **32,09%** | 1.376 | 48,74% | Bị kéo theo bởi vector người dùng thưa |
| **Tổng cộng <= 5 ratings** | **3.117.257** | **95,89%** | **1.505** | **53,31%** | **95,89% Top-20 là phim đuôi dài cực đoan** |
| Từ 6 đến 10 Train ratings | 106.907 | 3,29% | 796 | 28,20% | Phim ít phổ biến |
| Từ 11 đến 100 Train ratings | 26.636 | 0,82% | 511 | 18,10% | Phim trung bình |
| **Trên 100 Train ratings** | **20** | **0,00%** | 11 | 0,39% | **Hầu như biến mất khỏi Top-20** |
| **Toàn bộ Top-20** | **3.250.820** | **100,00%** | **2.823** | **100,00%** | Thống kê trên toàn bộ 162.541 users |

### 2. Danh sách Top 10 Phim Được Gợi ý Nhiều Nhất Toàn Hệ thống

| movieId | Tên Phim | Số Lần Xuất Hiện trong Top-20 | Số Lượt Đánh Giá trong Train | Điểm Trung bình Train |
| :---: | :--- | :---: | :---: | :---: |
| 203086 | Truth and Justice (2019) | 148.246 users (91,2%) | 1 | 5.0 |
| 194434 | Adrenaline (1990) | 144.613 users (89,0%) | 1 | 5.0 |
| 203882 | Dead in the Water (2006) | 144.548 users (88,9%) | 1 | 5.0 |
| 151989 | The Thorn (1971) | 144.256 users (88,8%) | 1 | 5.0 |
| 183947 | NOFX Backstage Passport 2 | 139.183 users (85,6%) | 1 | 5.0 |
| 192089 | National Theatre Live: One Man, Two Guvnors | 114.167 users (70,2%) | 1 | 5.0 |
| 202231 | Foster (2018) | 106.078 users (65,3%) | 1 | 5.0 |
| 166812 | Seeing Red: Stories of American Communists | 98.727 users (60,7%) | 2 | 5.0 |
| 194334 | Les Luthiers: El Grosso Concerto (2001) | 92.410 users (56,9%) | 1 | 5.0 |
| 187947 | Finger of God (2007) | 90.152 users (55,5%) | 1 | 5.0 |

*Kết luận kiểm định:* Bằng chứng dữ liệu xác nhận rằng các bộ phim chỉ có 1 lượt đánh giá 5.0 sao được thuật toán ALS gán vector tự do xoay theo vector của người đánh giá duy nhất đó. Điểm tích vô hướng của chúng đạt từ 5.0 đến 9.66, khiến chúng chiếm trọn danh sách Top-20 của gần như mọi người dùng trong hệ thống.

---

## IV. BẢNG TRUY VẾT CHẨN ĐOÁN MẪU NGƯỜI DÙNG VALIDATION CỐ ĐỊNH

Truy vết chi tiết trên mẫu người dùng Validation đại diện để kiểm tra tính toàn vẹn của chuỗi dữ liệu (Data Pipeline Integrity):

| userId | validation_movieId | rating | target_scoreable | target_als_score | target_full_rank | top20_contains_target | evaluator_hit | Phân loại & Giải thích |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **12** | 48516 | 4.0 | True | 3.7581 | 2.241 | False | False | **Phim phổ biến** (*The Departed*): Rank 2.241 do bị 2.240 phim đuôi dài điểm cao hơn chèn ép. |
| **1405** | 5232 | 4.0 | True | 3.2878 | 21.282 | False | False | **Phim trung bình** (*Road to Singapore*): Rank 21.282, điểm 3.29 thấp hơn ngưỡng cạnh tranh. |
| **38287** | 161181 | 4.5 | True | 3.8328 | 17.727 | False | False | **Phim hiếm** (*A Beautiful Planet*): Rank 17.727 dù rating 4.5. |
| **16127** | 197373 | 4.0 | False | N/A | N/A | False | False | **Phim không có Train item factor** (*Liyana*): Phim có 0 lượt xem trong Train; tính là Miss hợp lệ. |
| **67** | 2701 | 2.0 | True | 2.3563 | 47.191 | False | False | **Mục tiêu không tích cực** (*Wild Wild West*): Rating 2.0 < 3.5, loại khỏi positive cohort. |
| **1** | 296 | 5.0 | True | 4.1746 | 338 | False | False | **Phim kinh điển** (*Pulp Fiction*): Điểm 4.17 rất cao nhưng vẫn đứng thứ 338 sau 337 phim fluke. |
| **42** | 2126 | 5.0 | True | 3.4145 | 15.835 | False | False | **Phim cố định user 42** (*Snake Eyes*): Rank 15.835. |
| **100** | 213 | 4.0 | True | 4.0074 | 766 | False | False | **Phim cố định user 100** (*Fall Time*): Điểm 4.01, xếp thứ 766. |

*Nhận định kiểm toán:* 
- Không có lỗi hoán đổi `userId` và `movieId`.
- Không có hiện tượng rò rỉ target vào tập Train seen.
- Điểm số của target tính toán độc lập khớp 100% với phép biến đổi vector.
- Thứ hạng thực tế của các phim Validation yêu thích nằm trong khoảng từ 338 đến 21.282, giải thích hoàn toàn lý do tại sao không có bất kỳ hit nào xuất hiện trong Top-20.

---

## V. KIỂM TOÁN TÍNH TOÀN VẸN CỦA ĐỘNG CƠ ĐÁNH GIÁ (EVALUATION WIRING AUDIT)

1. **Kiểm tra Khóa Nối và Schema:**
   - DataFrame gợi ý gồm 4 cột: `userId` (int32), `movieId` (int32), `rank` (int32 từ 1 đến 20), `als_score` (float32).
   - Bộ đánh giá `TopNEvaluator` thực hiện tra cứu theo khóa `userId`, duyệt danh sách phim theo thứ tự thứ hạng `rank`.
2. **Kiểm thử Tích hợp Đầu-Cuối Độc lập (`test_21_exact_evaluation_wiring_and_positive_hit_rate`):**
   - Đã bổ sung bài kiểm thử tích hợp xác nhận: Khi một mục tiêu xuất hiện tại rank 2 và rank 7 trong danh sách gợi ý, `TopNEvaluator` tính toán chính xác `HitRate@5 = 1/3 (0.33333)`, `HitRate@10 = 2/3 (0.66667)` và điểm số `NDCG` dương tương ứng.
   - Chứng minh rằng bộ đánh giá hoàn toàn có khả năng ghi nhận HitRate dương khi danh sách gợi ý chứa đúng mục tiêu.
3. **Bảo toàn Mẫu số Đánh giá:**
   - Đúng 109.779 người dùng có tương tác Validation >= 3.5 được đưa vào mẫu số.
   - Các trường hợp không trúng hoặc không có gợi ý đều nhận điểm 0.0 và giữ nguyên trong mẫu số.

---

## VI. KẾT LUẬN VÀ PHÊ DUYỆT NGHIỆM THU (VERDICT)

- **Kết luận:** Kết quả `HitRate = 0.00000` của mô hình Spark ALS rank 16 trên tập Validation là một **kết quả thực nghiệm hợp lệ, khách quan và có thể tái lập 100%**. Nó phản ánh chính xác bản chất toán học của thuật toán Explicit Matrix Factorization khi chưa có cơ chế phạt tần suất (frequency damping) hoặc chính quy hóa thích ứng.
- **Quyết định:** **M06_ACCEPTANCE_PASS**.
- **Định hướng M07 (Hyperparameter Tuning):**
  - Giữ nguyên cấu trúc sinh ứng viên và giao thức đánh giá M02/M06.
  - Tinh chỉnh không gian siêu tham số: thử nghiệm các giá trị chính quy hóa lớn hơn (`regParam = 0.5, 1.0, 5.0`) để thu nhỏ mạnh mẽ vector của các phim ít lượt đánh giá.
  - Thử nghiệm Implicit ALS với trọng số độ tin cậy (`alpha`) nhằm triệt tiêu Fluke Bias và đưa các phim chất lượng cao trở lại Top-N.
