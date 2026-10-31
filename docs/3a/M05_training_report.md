# BÁO CÁO THỰC THI HUẤN LUYỆN SPARK ALS THẬT TRÊN MOVIELENS 25M (MODULE M05)

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Chuyên đề:** Task 3A – Khối Gợi Ý Lọc Cộng Tác Phân Tán (Spark ALS Collaborative Filtering)  
> **Module:** M05 – Full Spark ALS Training  
> **Branch:** `feature/als-3a` | **Packaging Commit:** `2e16fd6` (Base commit lúc train: `38c5c4f`) | **Môi trường:** Python 3.12, PySpark 4.2.0, Windows 11  
> **Trạng thái:** **`M05_ACCEPTANCE_PASS`** (Đã qua kiểm toán kỹ thuật & nghiệm thu khoa học)

---

## I. TỔNG QUAN PHẠM VI VÀ KẾT QUẢ THỰC NGHIỆM

Module M05 đánh dấu bước chuyển mình quan trọng từ lý thuyết và dữ liệu Toy (M04) sang huấn luyện thực tế trên quy mô dữ liệu phân tán lớn (Big Data). Mô hình Alternating Least Squares (ALS) của Apache Spark MLlib đã được huấn luyện thành công trên toàn bộ 24.675.013 tương tác của tập Train MovieLens 25M mà không gặp bất kỳ lỗi Out-of-Memory (OOM) nào.

### Tóm tắt các chỉ số kỹ thuật chính thức:
- **Tập dữ liệu huấn luyện:** `data/processed/splits/train` (24.675.013 ratings, 162.541 users, 58.932 movies).
- **Cấu hình mô hình:** `rank = 16`, `maxIter = 10`, `regParam = 0.1`, `implicitPrefs = False`, `coldStartStrategy = "nan"`, `seed = 42`.
- **Thời gian nạp Parquet:** `3.44 giây`.
- **Thời gian huấn luyện ALS fit:** `85.96 giây` (~1.43 phút trên CPU AMD Ryzen 5 7530U 6 cores / 12 threads).
- **Số lượng nhân tố ẩn học được:**
  - `userFactors`: **162.541** vector người dùng (mỗi vector đúng 16 chiều, 0 NaN, 0 Inf).
  - `itemFactors`: **58.932** vector bộ phim (mỗi vector đúng 16 chiều, 0 NaN, 0 Inf).
- **Kiểm chứng độc lập tích vô hướng:** Sai số tuyệt đối tối đa so với Spark transform là **0.00000050** (nhỏ hơn ngưỡng dung sai 0.0001 tới 200 lần).
- **Lưu trữ và tái nạp mô hình:** Lưu thành công tại `artifacts/models/als/m05_spark_als_rank16`. Khi nạp lại, dự đoán khớp chính xác 100% với sai số tuyệt đối **0.00000000**.
- **Chẩn đoán nội bộ tập Train:** RMSE = 0.7698, MAE = 0.6013 (trên 50.000 mẫu chẩn đoán).
- **Tổng thời gian pipeline:** `113.74 giây` (< 1.9 phút).

---

## II. CHI TIẾT CẤU HÌNH VÀ THÔNG SỐ HUẤN LUYỆN

Cấu hình huấn luyện được đóng gói chặt chẽ trong lớp `ALSConfig` tại [trainer.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py):

| Tham số | Giá trị | Ý nghĩa kỹ thuật |
| :--- | :--- | :--- |
| `rank` | 16 | Số chiều của không gian nhân tố ẩn. Đây là cấu hình khởi đầu kỹ thuật (initial baseline), việc dò tìm tối ưu sẽ diễn ra ở M07. |
| `maxIter` | 10 | Số chu kỳ luân phiên cập nhật P và Q. Đủ để hàm tổn thất hội tụ mà không gây tràn RDD lineage. |
| `regParam` | 0.1 | Hệ số phạt chuẩn Frobenius (lambda) giúp co ép vector và ngăn ngừa Overfitting. |
| `implicitPrefs` | False | Chế độ Explicit Feedback: ô trống là chưa quan sát (unobserved), tuyệt đối không coi là điểm 0. |
| `coldStartStrategy` | "nan" | Giữ nguyên các hàng không tính được để bộ đo Top-N bảo toàn đúng mẫu số đánh giá. |
| `seed` | 42 | Khóa hạt giống ngẫu nhiên khởi tạo vector nhân tố. Lưu ý khoa học: Trên cụm phân tán hoặc các kiến trúc CPU khác nhau, thứ tự cộng dồn floating-point không giao hoán (BLAS reduction non-associativity) có thể tạo ra chênh lệch bit nhỏ ở bậc thập phân sâu. |
| `userCol` / `itemCol` / `ratingCol` | userId / movieId / rating | Định danh các cột tương tác theo hợp đồng dữ liệu M00/M01. |
| `storageLevels` | MEMORY_AND_DISK | Cơ chế lưu trữ đệm phân tán an toàn trên máy tính cá nhân 16 GB RAM. |

---

## III. KIỂM TOÁN MA TRẬN NHÂN TỐ ẨN (FACTOR MATRICES AUDIT)

Sau khi gọi `model = als.fit(train_df)`, hai ma trận phân tán `model.userFactors` và `model.itemFactors` được kiểm toán toàn diện bằng hàm `audit_factors`:

```text
================================================================================
KẾT QUẢ KIỂM TOÁN NHÂN TỐ ẨN (FACTOR MATRICES AUDIT)
================================================================================
1. Ma trận Vector Người dùng (userFactors):
   - Tổng số thực thể:          162,541 users (Khớp 100% với tập Train)
   - Số chiều vector:            Đúng 16 chiều trên toàn bộ 162,541 vectors
   - Giá trị bất thường:         Hoàn toàn không có NaN, không có Inf
   - Chuẩn vector L2 (Norm):
     * Cực tiểu (Min Norm):     0.2805
     * Cực đại (Max Norm):     3.9494
     * Trung bình (Mean Norm):  2.3609
     * Độ lệch chuẩn (Std):     0.2435

2. Ma trận Vector Bộ phim (itemFactors):
   - Tổng số thực thể:          58,932 movies (Khớp 100% với số phim có Train rating)
   - Số chiều vector:            Đúng 16 chiều trên toàn bộ 58,932 vectors
   - Giá trị bất thường:         Hoàn toàn không có NaN, không có Inf
   - Chuẩn vector L2 (Norm):
     * Cực tiểu (Min Norm):     0.1518
     * Cực đại (Max Norm):     3.5729
     * Trung bình (Mean Norm):  1.6089
     * Độ lệch chuẩn (Std):     0.3462
================================================================================
```

### Nhận xét phân phối:
- Chuẩn vector người dùng tập trung quanh mức 2.36 với độ lệch chuẩn nhỏ (0.24), cho thấy các vector phân bố đồng đều trong không gian 16 chiều, không xảy ra hiện tượng bùng nổ số (exploding factors) hay triệt tiêu vector (vanishing factors).
- Chuẩn vector bộ phim có mức độ phân tán rộng hơn (std = 0.35, min = 0.15 đến max = 3.57). Giả thuyết định tính đặt ra là các bộ phim kinh điển được nhiều tương tác có xu hướng mang độ dài chuẩn lớn hơn, trong khi phim ít tương tác bị hệ số phạt regParam co ép về gần 0; tuy nhiên đây là quan sát hành vi mang tính giả thuyết trực giác chứ không phải định lý chứng minh toán học trong M05. Kiểm định định lượng tương quan giữa chuẩn vector và tần suất xuất hiện sẽ được thực hiện khi phân tích sâu ở các module tiếp theo.

---

## IV. ĐỐI CHIẾU TOÁN HỌC ĐỘC LẬP: SPARK TRANSFORM VS TÍCH VÔ HƯỚNG

Để chứng minh tính đúng đắn toán học của mô hình Spark trên 24,6 triệu dòng, hàm `verify_manual_dot_product` đã trích xuất ngẫu nhiên 30 cặp (userId, movieId) từ tập Train, lấy vector từ `userFactors` và `itemFactors`, tính tích vô hướng bằng NumPy và đối chiếu với kết quả của `model.transform()`:

| User ID | Movie ID | Điểm thực | Spark Prediction | Tích vô hướng thủ công | Sai số tuyệt đối | Trạng thái |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 947 | 648 | 4.5 | 3.4367 | 3.4367 | 0.0000001 | **MATCH** |
| 961 | 1198 | 4.0 | 3.4085 | 3.4085 | 0.0000001 | **MATCH** |
| 973 | 119141 | 3.5 | 2.9148 | 2.9148 | 0.0000002 | **MATCH** |
| 1030 | 3114 | 3.0 | 3.4386 | 3.4386 | 0.0000004 | **MATCH** |
| 1229 | 4508 | 3.5 | 3.5466 | 3.5466 | 0.0000002 | **MATCH** |

- **Số mẫu kiểm thử:** 30 / 30 mẫu.
- **Sai số tuyệt đối cực đại:** `0.00000050` (5.0e-7).
- **Sai số tuyệt đối trung bình:** `0.00000018` (1.8e-7).
- **Kết luận:** Tích vô hướng độc lập hoàn toàn trùng khớp với hàm biến đổi phân tán của Spark trong giới hạn số thực chính xác kép.

---

## V. KIỂM CHỨNG LƯU TRỮ VÀ TÁI NẠP MÔ HÌNH (PERSISTENCE INTEGRITY)

Mô hình huấn luyện đã được lưu trữ an toàn theo cấu trúc chuẩn:
```text
artifacts/models/als/m05_spark_als_rank16/
├── spark_model/
│   ├── metadata/
│   ├── itemFactors/ (Parquet)
│   └── userFactors/ (Parquet)
└── manifest.json
```

Quá trình nạp lại mô hình từ đĩa (`ALSTrainer.load_model`) mất 0.40 giây. Hàm `verify_reloaded_model` thực hiện kiểm chứng dự đoán trên tập mẫu giữa mô hình gốc trong bộ nhớ và mô hình nạp lại:
- **Max Absolute Prediction Difference:** `0.00000000` (Khớp float tuyệt đối).
- **Rank kiểm chứng:** 16 == 16.
- **Bài học kỹ thuật (HERMES-M05-02):** Khác biệt về thứ tự phân vùng khi `collect()` giữa hai phiên Spark riêng biệt đòi hỏi phải ánh xạ theo cặp khóa `(userId, movieId)` trước khi đối chiếu sai số.

---

## VI. CHẨN ĐOÁN NỘI BỘ TẬP TRAIN (DIAGNOSTIC METRICS)

Trên tập mẫu 50.000 tương tác Train:
- **Diagnostic Train RMSE:** `0.7698`
- **Diagnostic Train MAE:** `0.6013`

> [!CAUTION] CẢNH BÁO KHOA HỌC QUAN TRỌNG:
> Điểm số RMSE = 0.7698 và MAE = 0.6013 trên tập Train chỉ là thước đo chẩn đoán kỹ thuật nội bộ (In-Sample Optimization Diagnostic Check) nhằm xác nhận quá trình luân phiên bình phương tối thiểu đang giảm dần hàm tổn thất trên các cặp quan sát được.
> **TUYỆT ĐỐI KHÔNG ĐƯỢC:**
> 1. Dùng Train RMSE thấp để tuyên bố mô hình ALS có khả năng tổng quát hóa tốt hay đã hội tụ toàn cục tối ưu.
> 2. Dùng Train RMSE để kết luận ALS vượt trội hơn mô hình Popularity Baseline.
> 3. Đánh giá chất lượng gợi ý thực tế bằng RMSE. Việc đánh giá khả năng gợi ý bắt buộc phải thông qua độ đo xếp hạng Top-N (NDCG@K, HitRate@K) trên tập Validation được triển khai độc lập ở Module M06.

---

## VII. HỢP ĐỒNG ĐẦU RA BÀN GIAO CHO MODULE M06

Mô hình M05 bàn giao nguyên vẹn artifact cho Module M06 (Full-Catalog Candidate Generation):
- **Đường dẫn artifact:** `artifacts/models/als/m05_spark_als_rank16`
- **Tập nhân tố người dùng:** 162.541 users
- **Tập nhân tố bộ phim:** 58.932 movies
- **Số chiều latent:** 16 dimensions
- **Mã định danh Git Provenance:** Base training execution tại commit `38c5c4f`; đóng gói module tại commit `2e16fd6`.
- **Tình trạng:** Sẵn sàng tái sử dụng trực tiếp qua `ALSTrainer.load_model()` mà không cần huấn luyện lại.

