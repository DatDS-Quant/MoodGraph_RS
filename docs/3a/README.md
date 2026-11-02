# HỆ THỐNG TÀI LIỆU PHÂN HỆ 3A: SPARK ALS COLLABORATIVE FILTERING

> **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị tri thức và Apache Spark  
> **Chuyên đề:** Phân hệ 3A – Lọc cộng tác phân tán với Apache Spark MLlib ALS  
> **Trạng thái:** ĐÃ HOÀN THÀNH & NGHIỆM THU (184/184 PyTest PASS, 25/25 Quality Gates PASS)

Trang này là bản đồ chỉ mục tra cứu toàn bộ 31 tài liệu kỹ thuật, cẩm nang học tập, báo cáo thực nghiệm và bản đồ bảo vệ mã nguồn của Phân hệ 3A.

---

## 1. Tra Cứu Theo Mục Đích Sử Dụng

### 1.1. Dành Cho Việc Học Tập & Nắm Vững Lý Thuyết
Nếu bạn cần ôn tập kiến thức nền tảng, cơ sở toán học và cơ chế vận hành của hệ gợi ý lọc cộng tác:
- [Cơ sở Lý thuyết ALS & Phân tích Vector Ẩn (M04)](M04_als_foundations.md): Trình bày chi tiết toán học giải thuật Alternating Least Squares, hàm mất mát W-ALS có trọng số, cơ chế hội tụ và ý nghĩa không gian tiềm ẩn (Latent Factor Space).
- [Cẩm nang Huấn luyện Spark ALS Phân tán (M05)](M05_training_learning_guide.md): Hướng dẫn kiến trúc bộ nhớ Spark, kiểm soát checkpoint tránh đứt gãy RDD lineage khi train 25M ratings.
- [Cẩm nang Sinh Ứng viên & Xếp hạng Top-N (M06)](M06_candidates_learning_guide.md): Lý thuyết nhân ma trận vector ẩn Top-N và giải thuật lọc phim đã xem (Seen-Item Filtering) qua ma trận thưa CSR.
- [Cẩm nang Tối ưu hóa Siêu tham số (M07)](M07_tuning_learning_guide.md): Phương pháp Grid Search trên Validation split, kỹ thuật Screening 5.000 users để tiết kiệm chi phí tính toán.
- [Cẩm nang Đánh giá trên Frozen Test Split (M08)](M08_benchmark_learning_guide.md): Nguyên lý rào chắn rò rỉ thông tin (Data Leakage) và phương pháp đánh giá một lần duy nhất trên tập Test đông băng.
- [Cẩm nang Chẩn đoán Cold-Start & Long-Tail (M09)](M09_diagnostics_learning_guide.md): Phân tích động thái suy giảm chất lượng biểu diễn của ALS ở vùng người dùng ít tương tác và đuôi dài sản phẩm.
- [Cẩm nang Đóng gói Mô hình & Phục vụ Sản xuất (M10)](M10_delivery_learning_guide.md): Hướng dẫn thiết kế dịch vụ phục vụ `ALSDeliveryService`, cơ chế tải mô hình và quản lý bộ nhớ.

---

### 1.2. Dành Cho Việc Xem Báo Cáo Thực Nghiệm & Kết Quả Đo Lường
Nếu bạn cần số liệu thực nghiệm định lượng, đối chiếu kết quả giữa các mô hình:
- [Báo cáo Kiểm toán Dữ liệu MovieLens 25M (M01)](M01_data_audit.md): Kiểm tra 25 triệu ratings, xác lập ranh giới thời gian Train/Validation/Test và rào chắn rò rỉ hai lớp.
- [Báo cáo Kiểm định Toán học Bộ đo Ranking (M02)](M02_evaluator_report.md): Kiểm thử độc lập các độ đo Hit Rate (HR@K), NDCG@K, MRR@K độc lập với Spark.
- [Báo cáo Thực nghiệm Mô hình Popularity Baseline (M03)](M03_popularity_report.md): Đo lường hiệu năng của Popularity Count và IMDB Bayesian Weighted Rating (m=10).
- [Báo cáo Huấn luyện Spark ALS Toàn phần (M05)](M05_training_report.md): Ghi nhận tài nguyên, thời gian huấn luyện và log hội tụ trên 25M ratings.
- [Báo cáo Sinh Ứng viên & Xếp hạng Validation (M06)](M06_candidates_report.md): Kết quả sinh Top-N ứng viên và đánh giá trên tập Validation.
- [Báo cáo Tối ưu hóa Siêu tham số & Lựa chọn Champion (M07)](M07_tuning_report.md): Bảng so sánh toàn bộ các cấu hình siêu tham số và căn cứ chọn mô hình Champion `ALS_R8_REG0.3_ITER10`.
- [Biên bản Đóng băng Siêu tham số M07 sang M08](M07_to_M08_handover_freeze_manifest.md): Cam kết khóa tuyệt đối tham số mô hình trước khi mở tập Test.
- [Báo cáo Thực nghiệm Đối đầu trên Frozen Test (M08)](M08_final_benchmark.md): Kết quả đối đầu trung thực giữa Popularity Count, Popularity Weighted và Spark ALS Champion.
- [Báo cáo Chẩn đoán Chuyên sâu & Hiệu năng Phân tán (M09)](M09_diagnostics_report.md): Phân tích chi tiết hành vi Cold-start, độ ổn định phân tán và giới hạn của ALS.
- [Báo cáo Nghiệm thu Bàn giao Mô hình Cuối cùng (M10)](M10_delivery_report.md): Kết quả kiểm định tích hợp và bàn giao mô hình sản xuất.
- [Biên bản Nghiệm thu Khoa học Tổng thể Task 3A](TASK_3A_FINAL_ACCEPTANCE.md): Tổng hợp bằng chứng chấp thuận nghiệm thu chính thức của toàn bộ Task 3A.

---

### 1.3. Dành Cho Việc Bảo Vệ Đồ Án Trước Hội Đồng (Source Code Defense Maps)
Tài liệu định vị chính xác từng hàm, từng dòng code và lập luận kỹ thuật trả lời câu hỏi phản biện:
- [Bản đồ Bảo vệ Mã nguồn M03 – Popularity Baseline](M03_source_code_defense_map.md)
- [Bản đồ Bảo vệ Mã nguồn M04 – Toy ALS & Phân tích Vector](M04_source_code_defense_map.md)
- [Bản đồ Bảo vệ Mã nguồn M05 – Huấn luyện Spark ALS Phân tán](M05_source_code_defense_map.md)
- [Bản đồ Bảo vệ Mã nguồn M06 – Sinh Top-N & Lọc Phim Đã Xem](M06_source_code_defense_map.md)
- [Bản đồ Bảo vệ Mã nguồn M07 – Tối ưu hóa Siêu tham số](M07_source_code_defense_map.md)
- [Bản đồ Bảo vệ Mã nguồn M08 – Đánh giá Độc lập Frozen Test](M08_source_code_defense_map.md)
- [Bản đồ Bảo vệ Mã nguồn M09 – Chẩn đoán Cold-Start & Hiệu năng](M09_source_code_defense_map.md)
- [Bản đồ Bảo vệ Mã nguồn M10 – Đóng gói API & Hợp đồng Tích hợp](M10_source_code_defense_map.md)
- [Báo cáo Kiểm toán Tính Đọc hiểu & Dọn dẹp Mã nguồn](TASK_3A_SOURCE_READABILITY_AND_CLEANUP.md)

---

### 1.4. Dành Cho Việc Kiểm Tra Kết Quả M08 (Nguồn Sự Thật Khoa Học)
Để kiểm tra tính xác thực của số liệu thực nghiệm M08, đối chiếu các tệp:
- Báo cáo văn bản: [M08_final_benchmark.md](M08_final_benchmark.md)
- Tệp JSON gốc đã đóng băng: `artifacts/als/m08/m08_test_benchmark_results.json`
- Số liệu chuẩn M08:
  - Popularity Count: HR@10 = 0.05357, NDCG@10 = 0.02721, MRR@10 = 0.01929 (5.958 hits)
  - Popularity Weighted (m=10): HR@10 = 0.01884, NDCG@10 = 0.00742, MRR@10 = 0.00404 (2.095 hits)
  - Spark ALS Champion: HR@10 = 8.9919e-06, NDCG@10 = 5.6733e-06, MRR@10 = 4.4960e-06 (1 hit tại Rank 2)

---

### 1.5. Dành Cho Việc Chạy Suy Luận (Inference M10)
Để chạy mô hình đã huấn luyện sinh gợi ý cho người dùng:
- Module thực thi: `recommender/als/delivery.py` (lớp `ALSDeliveryService`, hàm `recommend_als`, `recommend_als_batch`)
- Kịch bản CLI phục vụ và kiểm định: `scripts/run_m10_delivery.py`
  - Thực thi toàn bộ quy trình: chuẩn bị registry, sinh ma trận thưa `train_seen_csr.npz`, chạy smoke test và đánh giá 25 Quality Gates: `python scripts/run_m10_delivery.py`
- Báo cáo chi tiết: [M10_delivery_report.md](M10_delivery_report.md)

---

### 1.6. Dành Cho Việc Tích Hợp Mô Hình Lai (Hybrid Integration)
Khi đội ngũ phát triển Task 3B (Đồ thị tri thức) và Khối 4 (Hybrid) cần lấy đầu ra từ ALS:
- [Hợp đồng Tích hợp Kỹ thuật (Integration Contract)](integration_contract.md): Định nghĩa cấu trúc dữ liệu đầu vào/đầu ra, chuẩn điểm số, schema bảng ứng viên và cơ chế fallback.
- [Biên bản Bàn giao Cho Khối Hybrid](TASK_3A_HANDOVER_TO_HYBRID.md): Tóm tắt trách nhiệm bàn giao của Task 3A và các khuyến nghị vận hành cho khối Hybrid.

