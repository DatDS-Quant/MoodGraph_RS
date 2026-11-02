# MOODGRAPH | KHỐI 3A | MODULE M10: BÁO CÁO KIỂM TOÁN VÀ ĐÓNG HỒ SƠ M09
# M09 SCIENTIFIC DOCUMENT CLOSURE AUDIT

**Dự án:** MoodGraph – Task 3A Spark ALS Recommender Systems  
**Phân hệ:** M10 – Final ALS Delivery & Release Engineering  
**Tài liệu được kiểm toán:** [M09_diagnostics_report.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_report.md) và [M09_diagnostics_learning_guide.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_learning_guide.md)  
**Trạng thái:** COMPLETED_AND_CLOSED  

---

## 1. MỤC ĐÍCH KIỂM TOÁN

Module M09 đã đạt nghiệm thu kỹ thuật (16/16 Quality Gates PASS, 160/160 tests PASS). Tuy nhiên, để đảm bảo tính chuẩn xác và trung thực tuyệt đối trong toàn bộ hồ sơ Task 3A trước khi bàn giao sang Khối 3B, đợt kiểm toán này rà soát và đóng dứt điểm các điểm diễn đạt lý thuyết, lịch sử thực nghiệm và ngữ cảnh đo đạc hiệu năng.

---

## 2. NỘI DUNG HIỆU CHỈNH VÀ ĐÓNG HỒ SƠ

### 2.1. Hiệu chỉnh Phép tính Toán học Đồ chơi (A1 - Toy Mathematics)
- **Vị trí:** Mục 1.2 trong [M09_diagnostics_learning_guide.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_learning_guide.md).
- **Vấn đề ban đầu:** Ví dụ ghi `P_1 = [2.0, 0.0]`, `Q_B = [2.4, 0.0]`, observed rating = 5.0, nhưng tích vô hướng `2.0 * 2.4 = 4.80`, không bằng 5.0; đồng thời dùng từ "khớp hoàn hảo".
- **Hiệu chỉnh:** Phân biệt rõ ràng giữa rating quan sát (5.0) và điểm dự đoán của ALS có điều chuẩn L2 (`lambda = 0.1`). Vì có thành phần phạt `lambda * ||Q_B||^2`, vector `Q_B` bị co nhẹ về gốc tọa độ (từ 2.5 xuống 2.4), cho điểm dự đoán `4.80` (residual = 0.20).
- **Kết luận khoa học:** Thuật toán ALS có điều chuẩn L2 không nội suy hoàn hảo (zero residual) mọi điểm đánh giá. Tuy nhiên, do item đuôi dài chỉ có 1 ràng buộc, vector của nó vẫn xoay mạnh theo hướng của user duy nhất đó, dẫn đến điểm dự đoán cho User 2 (`1.8 * 2.4 = 4.32`) vượt trội so với item phổ biến Phim A (`2.72`).

### 2.2. Hiệu chỉnh Lịch sử Siêu tham số M07 (A2 - M07 Hyperparameter History)
- **Vị trí:** Câu hỏi 9 trong [M09_diagnostics_learning_guide.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_learning_guide.md).
- **Vấn đề ban đầu:** Đoạn văn bản liệt kê dãy tham số `regParam 0.05, 0.1, 0.2, 0.3`.
- **Hiệu chỉnh:** Đối chiếu trực tiếp với `artifacts/als/m07/experiment_registry.json`. Các mức `regParam` thực sự được huấn luyện và đánh giá tại M07 gồm: `0.1` (M05 baseline), `0.3` (M07 finalist), `1.0`, và `3.0`.
- **Kết luận:** Khẳng định đúng lịch sử thực nghiệm đã diễn ra, không đưa các tham số chưa chạy vào tài liệu.

### 2.3. Hiệu chỉnh Diễn giải Khoa học (A3 - Scientific Interpretation)
- **Vị trí:** Mục 3.2 và Kết luận trong [M09_diagnostics_report.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_report.md).
- **Vấn đề ban đầu:** Diễn giải p-value cực nhỏ (`3.0e-323`) như một bằng chứng về mối quan hệ cực mạnh, và dùng các từ khẳng định tuyệt đối ("100% hoàn hảo", "triệt tiêu hoàn toàn").
- **Hiệu chỉnh:** Làm rõ rằng Pearson `r = +0.157360` có ý nghĩa thống kê cao là do kích thước mẫu rất lớn (N = 58.932 items), nhưng kích thước hiệu ứng (effect size) ở mức khiêm tốn / vừa phải (`r ≈ 0.157`). Nó phản ánh một xu hướng tích cực nhưng không phải là mối quan hệ tuyến tính chặt chẽ.
- Thay thế các khẳng định tuyệt đối bằng từ ngữ học thuật chuẩn mực: việc kết hợp Knowledge Graph và Popularity Prior là hướng nghiên cứu khuyến nghị nhằm giảm thiểu thiên lệch Fluke Bias, không phải là lời cam đoan triệt tiêu 100% mà chưa có kiểm nghiệm thực nghiệm ở Task 3B.

### 2.4. Ngữ cảnh Phương pháp đo Hiệu năng (A4 - Performance Methodology)
- **Vị trí:** Bảng hiệu năng và bình luận kỹ thuật trong [M09_diagnostics_report.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M09_diagnostics_report.md).
- **Làm rõ:**
  1. Phép đo PyArrow (0.65s) thực hiện đọc 2 cột (`movieId`, `userId`) trực tiếp từ file Parquet cục bộ bằng C++ native zero-copy.
  2. Phép đo Spark DataFrame (3.98s) thực hiện quét phân tán 12 partitions trên JVM và lập kế hoạch Catalyst.
  3. Hai phép đo này phục vụ hai vai trò kiến trúc khác nhau (PyArrow cho candidate generation / inference, Spark cho distributed data processing / training).
  4. Mức bộ nhớ 724.6 MB là RAM RSS cô lập của tiến trình tính ma trận NumPy BLAS ở batch size 2.500, trong khi quy trình end-to-end bao gồm thêm bộ nhớ lọc tương tác đã xem và sắp xếp Top-K.

### 2.5. Ghi nhận Thăm dò Ban đầu (A5 - Exploratory Diagnostics Notice)
- Ghi nhận minh bạch: Trong quá trình thiết kế M09, các khảo sát dữ liệu ban đầu (exploratory checks) đã được thực hiện để xác định ngưỡng phân chia 5 bins hỗ trợ [0, 1-5, 6-10, 11-50, >50], sau đó pipeline tự động chính thức mới được đóng băng và thực thi end-to-end.

### 2.6. Đối chiếu Danh mục Kiểm thử (A6 - Test Inventory Reconciliation)
- Chạy `pytest --collect-only -q` xác nhận đúng 160 tests phân bổ trên 11 test files:
  - `test_als_trainer.py`: 14 tests
  - `test_benchmark.py`: 11 tests
  - `test_candidates.py`: 21 tests
  - `test_diagnostics.py`: 15 tests
  - `test_evaluator.py`: 21 tests
  - `test_hermes_memory.py`: 9 tests
  - `test_m00_environment.py`: 5 tests
  - `test_m01_data_loader.py`: 14 tests
  - `test_popularity.py`: 22 tests
  - `test_toy_als.py`: 13 tests
  - `test_tuner.py`: 15 tests
  - **Tổng cộng: 160 tests collected và 160 tests passed.**

### 2.7. Cam kết Bất biến M08 (A7 - Immutable M08 Preservation)
- Toàn bộ số liệu kiểm định Offline Test Benchmark tại M08 được giữ nguyên 100%:
  - Popularity Count HR@10 = 0.05357 (5.958 hits / 111.211 users)
  - Popularity Weighted HR@10 = 0.01884 (2.095 hits)
  - ALS `ALS_R8_REG0.3_ITER10` HR@10 = 1 / 111.211 ≈ 8.991916e-6 (1 hit duy nhất tại rank 2, NDCG@10 ≈ 5.673268e-6).

---

## 3. KẾT LUẬN KIỂM TOÁN

Hồ sơ Module M09 chính thức được đóng với tính nhất quán khoa học tuyệt đối, tạo nền tảng vững chắc để triển khai Phase C (Delivery API) và Phase E (Integration Contract) tại M10.

