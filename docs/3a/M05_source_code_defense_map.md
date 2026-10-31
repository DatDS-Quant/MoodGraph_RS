# BẢN ĐỒ MÃ NGUỒN VÀ HƯỚNG DẪN BẢO VỆ MODULE M05 (SOURCE CODE DEFENSE MAP)

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Module:** M05 – Full Spark ALS Training  
> **Branch:** `feature/als-3a` | **Commit:** `38c5c4f` | **Môi trường:** Python 3.12, PySpark 4.2.0, Windows 11  
> **Cam kết:** 100% số dòng và đường dẫn đã được kiểm tra thực tế trên workspace `D:\PROJECT BIG DATA\MoodGraph`.

---

## I. BẢN ĐỒ MÃ NGUỒN CHÍNH XÁC (SOURCE CODE DEFENSE MAP)

Bảng đối chiếu vị trí mã nguồn giúp chủ dự án mở chính xác tập tin và dòng code khi hội đồng phản biện yêu cầu:

| Chức năng Kỹ thuật | File | Class/Function | Dòng (Line) | Giải thích & Trách nhiệm Kỹ thuật | Test chứng minh | Lệnh mở VS Code |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Đọc Train Parquet** | `recommender/als/data_loader.py` | `load_train_data` | L98–L122 | Nạp 24.675.013 tương tác từ `data/processed/splits/train` qua Spark Parquet loader. | `test_m01_data_loader.py:test_01` | `code -g recommender/als/data_loader.py:98` |
| **Kiểm tra Schema Train** | `recommender/als/data_loader.py` | `_validate_schema` | L59–L96 | Kiểm tra chặt chẽ sự hiện diện và kiểu dữ liệu của `userId`, `movieId`, `rating`, `timestamp`. | `test_m01_data_loader.py:test_02` | `code -g recommender/als/data_loader.py:59` |
| **Cấu hình SparkSession** | `recommender/als/data_loader.py` | `get_spark_session` | L38–L56 | Khởi tạo Spark local 4 threads, 6GB driver memory, cấu hình shuffle partitions và Windows bind address. | `test_m00_environment.py:test_03` | `code -g recommender/als/data_loader.py:38` |
| **Khai báo Cấu hình ALS** | `recommender/als/trainer.py` | `class ALSConfig` | L43–L98 | Định nghĩa dataclass cấu hình: rank=16, maxIter=10, regParam=0.1, coldStart='nan', seed=42. | `test_als_trainer.py:test_01-05` | `code -g recommender/als/trainer.py:43` |
| **Kiểm soát Tham số ALS** | `recommender/als/trainer.py` | `ALSConfig.validate` | L61–L80 | Kiểm tra biên giá trị: rank > 0, max_iter > 0, reg_param >= 0.0, strategy in ('nan', 'drop'). | `test_als_trainer.py:test_01-04` | `code -g recommender/als/trainer.py:61` |
| **Kiểm tra DataFrame Huấn luyện**| `recommender/als/trainer.py`| `validate_training_dataframe`| L132–L162 | Bảo đảm DataFrame đầu vào có đủ cột và kiểu số nguyên (IntegerType/LongType) cho ID. | `test_als_trainer.py:test_06-07` | `code -g recommender/als/trainer.py:132` |
| **Khởi tạo và Fit ALS** | `recommender/als/trainer.py` | `ALSTrainer.fit` | L164–L192 | Khởi tạo PySpark `ALS(...)` và thực thi phân tích ma trận `als.fit(train_df)`. | `test_als_trainer.py:test_08` | `code -g recommender/als/trainer.py:164` |
| **Kiểm toán Nhân tố Ẩn** | `recommender/als/trainer.py` | `ALSTrainer.audit_factors` | L194–L258 | Đếm số lượng, kiểm tra số chiều (16), quét sạch NaN/Inf và tính phân phối chuẩn vector L2. | `test_als_trainer.py:test_09` | `code -g recommender/als/trainer.py:194` |
| **Kiểm chứng Tích vô hướng** | `recommender/als/trainer.py` | `verify_manual_dot_product` | L260–L348 | Trích xuất vector, tính tích vô hướng bằng NumPy và so khớp với `model.transform()` (dung sai 1e-4).| `test_als_trainer.py:test_10` | `code -g recommender/als/trainer.py:260` |
| **Chẩn đoán Sai số Train** | `recommender/als/trainer.py` | `compute_train_diagnostics` | L350–L392 | Tính RMSE và MAE trên mẫu tương tác Train phục vụ chẩn đoán nội bộ quá trình hội tụ. | `test_als_trainer.py:test_13` | `code -g recommender/als/trainer.py:350` |
| **Lưu trữ Mô hình và Manifest** | `recommender/als/trainer.py` | `ALSTrainer.save_model` | L394–L431 | Lưu Spark model vào đĩa cùng tệp metadata manifest.json (commit, tham số, số lượng factor). | `test_als_trainer.py:test_11` | `code -g recommender/als/trainer.py:394` |
| **Nạp lại Mô hình từ Đĩa** | `recommender/als/trainer.py` | `ALSTrainer.load_model` | L433–L453 | Đọc `ALSModel.load()` và đọc manifest để tái sử dụng mô hình trong các module tiếp theo. | `test_als_trainer.py:test_12` | `code -g recommender/als/trainer.py:433` |
| **Kiểm chứng Tái lập Sau Nạp** | `recommender/als/trainer.py` | `verify_reloaded_model` | L455–L510 | So sánh dự đoán mô hình gốc vs mô hình nạp lại qua composite key (userId, movieId), sai số 0.0. | `test_als_trainer.py:test_12` | `code -g recommender/als/trainer.py:455` |
| **Kịch bản Huấn luyện Full** | `scripts/run_m05_train_als.py` | `run_m05_training_pipeline` | L67–L260 | Pipeline tự động hóa 10 bước huấn luyện trên 24.67M ratings, xuất artifact kết quả. | `scripts/run_m05_train_als.py` | `code -g scripts/run_m05_train_als.py:67` |
| **Bộ 14 Kiểm thử Tự động** | `tests/als/test_als_trainer.py` | `test_01` đến `test_14` | L51–L275 | Toàn bộ 14 bài test kiểm tra config, schema, fit, audit, dot product, persistence, cold start. | `pytest tests/als/test_als_trainer.py` | `code -g tests/als/test_als_trainer.py:51` |

---

## II. BỘ CÂU HỎI VẤN ĐÁP BẢO VỆ CHUYÊN SÂU (ORAL DEFENSE Q&A)

### Câu 1: Apache Spark đọc và nạp 24,6 triệu dòng ratings ở đâu trong mã nguồn?
- **Trả lời:**
  Spark nạp dữ liệu thông qua hàm `load_train_data` tại `recommender/als/data_loader.py:98`. Hàm này gọi `spark.read.parquet()` trỏ vào thư mục phân vùng `data/processed/splits/train` và thực thi kiểm tra hợp đồng schema qua hàm `_validate_schema` (dòng 59). Dữ liệu được nạp dưới dạng DataFrame phân tán (Lazy Evaluation) và chỉ đọc các cột cần thiết (`userId`, `movieId`, `rating`, `timestamp`) mà không bao giờ tải toàn bộ vào RAM Driver dưới dạng pandas.

### Câu 2: Lệnh khởi tạo và huấn luyện mô hình ALS thực sự diễn ra tại dòng nào?
- **Trả lời:**
  Lớp `ALSTrainer.fit()` tại `recommender/als/trainer.py:164` thực thi nhiệm vụ này.
  Tại dòng 176, đối tượng `ALS(...)` của Spark MLlib được khởi tạo với các tham số từ `ALSConfig`.
  Lệnh huấn luyện thực sự bắt đầu tại dòng 191 thông qua lệnh `model = als.fit(train_df)`. Tại thời điểm này, Spark kích hoạt đồ thị tính toán DAG gồm các vòng lặp cập nhật luân phiên ma trận người dùng và ma trận phim.

### Câu 3: Tại sao trong M05 lại chọn cấu hình rank = 16 và regParam = 0.1?
- **Trả lời:**
  Cấu hình `rank = 16` và `regParam = 0.1` là cấu hình kỹ thuật ban đầu (Initial Engineering Baseline) được phê duyệt trong Master Roadmap để thiết lập đường cơ sở huấn luyện ổn định trên 24,6 triệu dòng. Đây **chưa phải là bộ tham số tối ưu**. Việc tinh chỉnh tham số chuyên sâu (Hyperparameter Tuning) để tìm ra bộ rank và regParam đạt NDCG@K cao nhất sẽ được thực hiện bài bản ở Module M07.

### Câu 4: Vì sao bài toán MovieLens 25M bắt buộc phải thiết lập implicitPrefs = False?
- **Trả lời:**
  MovieLens 25M là tập dữ liệu phản hồi tường minh (Explicit Feedback), nơi người dùng chủ động cho điểm số chính xác từ 0.5 đến 5.0 sao. Khi đặt `implicitPrefs = False`, hàm tổn thất chỉ tính sai số bình phương trên tập các ô đã có đánh giá (R). Nếu để `implicitPrefs = True`, thuật toán sẽ hiểu nhầm toàn bộ 99.74% ô trống là điểm không thích (số 0), làm sụp đổ phân phối xác suất và phá hủy khả năng dự đoán điểm của hệ thống.

### Câu 5: Khi nào Spark ALS thực sự bắt đầu tính toán ma trận trên CPU/RAM?
- **Trả lời:**
  Spark hoạt động theo cơ chế Lazy Evaluation. Khi gọi `train_df = load_train_data(...)`, Spark mới chỉ xây dựng kế hoạch thực thi logic (Logical Plan). Quá trình tính toán thực sự chỉ bùng nổ khi gặp một Action, cụ thể là lệnh `als.fit(train_df)` tại dòng 191 của `trainer.py`. Lúc này, Spark chia nhỏ ma trận, phân phối công việc xuống 4 luồng CPU và bắt đầu các vòng lặp shuffle trao đổi dữ liệu.

### Câu 6: Mô hình học ra bao nhiêu vector người dùng và vector phim?
- **Trả lời:**
  Mô hình học ra chính xác **162.541** vector người dùng trong `model.userFactors` (tương ứng 100% số người dùng trong tập Train) và **58.932** vector bộ phim trong `model.itemFactors` (tương ứng số phim có ít nhất 1 rating Train). Con số này khớp hoàn hảo với báo cáo kiểm toán dữ liệu M01. Toàn bộ 3.491 bộ phim trong catalog không có rating Train sẽ được xử lý qua chính sách cold-start.

### Câu 7: Mỗi vector nhân tố ẩn chứa những con số gì? Có thể coi chiều số 0 là Action được không?
- **Trả lời:**
  Mỗi vector chứa đúng 16 con số thực (float) biểu diễn tọa độ trong không gian tiềm ẩn k chiều. Ta **tuyệt đối không được gán nhãn** chiều 0 là Action hay chiều 1 là Romance. Thuật toán tối ưu hóa hoàn toàn dựa trên sai số bình phương mà không có ràng buộc phân tách ngữ nghĩa độc lập. Các chiều này là những đặc trưng tiềm ẩn phi tuyến tính phức tạp do máy tự học từ thói quen cộng đồng.

### Câu 8: Làm sao kiểm chứng được dự đoán của Spark transform là hoàn toàn chính xác về mặt toán học?
- **Trả lời:**
  Hàm `verify_manual_dot_product` tại `recommender/als/trainer.py:260` thực hiện việc này: lấy vector người dùng p_u từ `userFactors`, vector phim q_i từ `itemFactors`, tự tính tích vô hướng `np.dot(p_u, q_i)` bằng NumPy và so sánh với cột `prediction` của Spark. Kết quả thực nghiệm trên 30 mẫu ngẫu nhiên cho thấy sai số tối đa chỉ là `0.00000050`, chứng minh dự đoán của Spark hoàn toàn khớp với công thức giải tích.

### Câu 9: Vì sao không tạo ra một ma trận đầy đủ (Dense Matrix) gồm 162.541 hàng và 62.423 cột?
- **Trả lời:**
  Một ma trận Dense với kích thước 162.541 × 62.423 chứa tới hơn 10.1 tỷ phần tử. Nếu lưu dưới dạng số thực float 32-bit (4 bytes), ma trận này sẽ ngốn hơn **40.5 GB RAM**, vượt quá khả năng của bất kỳ máy tính cá nhân nào và gây sập hệ thống (OOM) ngay lập tức. Thay vào đó, ALS chỉ lưu hai ma trận cấp thấp P (162.541 × 16) và Q (58.932 × 16), chỉ tốn khoảng **14.2 MB RAM**, tiết kiệm bộ nhớ tới 2.800 lần.

### Câu 10: Mô hình được lưu ở đâu và Module M06 sẽ tái sử dụng nó như thế nào?
- **Trả lời:**
  Mô hình được lưu trữ tại `artifacts/models/als/m05_spark_als_rank16` thông qua hàm `save_model` tại dòng 394 của `trainer.py`. Thư mục này chứa mô hình native của Spark và tệp `manifest.json`. Khi Module M06 khởi chạy để sinh ứng viên Top-N cho toàn bộ danh mục, nó chỉ cần gọi `ALSTrainer.load_model()` tại dòng 433 để nạp lại mô hình trong 0.4 giây mà không cần tốn thời gian huấn luyện lại.

### Câu 11: Tại sao Train RMSE đạt 0.7698 nhưng vẫn chưa thể kết luận ALS tốt hơn mô hình Popularity?
- **Trả lời:**
  Train RMSE (0.7698) chỉ là thước đo sai số dự đoán điểm số trên tập dữ liệu mô hình đã được nhìn thấy trong quá trình tối ưu (In-Sample Fit). Trong hệ thống gợi ý, người dùng chỉ quan tâm đến danh sách Top-N bộ phim hay nhất được xếp ở đầu danh sách. Một mô hình có Train RMSE thấp hoàn toàn có thể bị đánh bại bởi Popularity trên các độ đo xếp hạng thực tế như NDCG@K và HitRate@K trên tập Validation chưa từng nhìn thấy (Out-of-Sample). Khẳng định chất lượng bắt buộc phải chờ kết quả đo đạc Top-N ở Module M06 và M08.

---

## III. KỊCH BẢN DEMO THỰC THI TRỰC TIẾP TRONG 5 PHÚT (5-MINUTE LIVE DEMO SCRIPT)

Khi giảng viên hoặc hội đồng yêu cầu chạy demo trực tiếp trên máy chấm, thực hiện theo các bước sau:

### Bước 1: Mở mã nguồn và chỉ các vị trí trọng yếu (60 giây)
- Mở lớp cấu hình ALS: `code -g recommender/als/trainer.py:43` (Chỉ các tham số rank=16, regParam=0.1, coldStart='nan').
- Mở hàm Fit: `code -g recommender/als/trainer.py:164` (Chỉ lệnh `als.fit(train_df)` tại dòng 191).
- Mở hàm Lưu mô hình: `code -g recommender/als/trainer.py:394` (Chỉ cấu trúc thư mục lưu model và manifest).

### Bước 2: Nạp mô hình đã lưu và chứng minh kiểm chứng tích vô hướng (90 giây)
Chạy một lệnh Python ngắn gọn để tải mô hình đã lưu và in kiểm chứng sai số tích vô hướng:
```powershell
python -c "
from recommender.als.trainer import ALSTrainer
from recommender.als.data_loader import get_spark_session, load_train_data
spark = get_spark_session(master='local[2]', driver_memory='2g')
trainer = ALSTrainer()
model, manifest = trainer.load_model('artifacts/models/als/m05_spark_als_rank16')
print('Loaded Model Rank:', model.rank)
print('User Factors Count:', model.userFactors.count())
print('Item Factors Count:', model.itemFactors.count())
sample_df = load_train_data(spark).limit(10)
audit = trainer.verify_manual_dot_product(model, sample_df)
print('Manual Dot vs Spark Transform Match:', audit['all_matched'])
print('Max Absolute Diff:', audit['max_abs_diff'])
"
```
**Kết quả hiển thị trên màn hình:**
- Rank: 16
- User Factors Count: 162.541
- Item Factors Count: 58.932
- All Matched: True
- Max Absolute Diff: < 0.000001

### Bước 3: Chạy toàn bộ 14 bài test tự động của Module M05 (90 giây)
```powershell
python -m pytest tests/als/test_als_trainer.py -v
```
**Kết quả:** 14/14 tests PASSED 100%.

### Bước 4: Mở báo cáo thực nghiệm và tóm tắt kết quả (60 giây)
Mở tệp [M05_training_report.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M05_training_report.md) và chỉ rõ cho hội đồng thấy thời gian huấn luyện 85.96 giây, các chỉ số kiểm toán vector và hợp đồng sẵn sàng cho Module M06.
