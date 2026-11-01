# BẢN ĐỒ MÃ NGUỒN VÀ KỊCH BẢN BẢO VỆ M07: TINH CHỈNH SIÊU THAM SỐ SPARK ALS

- **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị Tri thức và Apache Spark
- **Mã module:** M07 (Khối 3A – Spark ALS)
- **Tài liệu:** Bản đồ chỉ dẫn số dòng mã nguồn (Code Defense Map) và Kịch bản bảo vệ 5 phút

---

## PHẦN 1: BẢN ĐỒ MÃ NGUỒN CHI TIẾT (EXACT SOURCE CODE MAP)

### 1. Module lõi điều phối tinh chỉnh: [`recommender/als/tuner.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py)

| Thành phần / Chức năng | Lớp / Hàm | Vị trí dòng | Mục đích kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Bảo vệ dữ liệu Test tuyệt đối** | `guard_test_split_access()` | [Dòng 48-60](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L48-L60) | Kiểm tra chuỗi đường dẫn, ném `PermissionError` nếu phát hiện bất kỳ truy cập nào tới tập `test`. |
| **Định nghĩa cấu hình thử nghiệm** | `TrialConfig` | [Dòng 63-95](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L63-L95) | Dataclass lưu trữ siêu tham số (`rank`, `reg_param`, `max_iter`, `model_family`), kiểm tra tính hợp lệ toán học. |
| **Nhật ký thử nghiệm nguyên tử** | `ExperimentRegistry` | [Dòng 173-290](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L173-L290) | Quản lý vòng đời các trial, lưu trữ JSON an toàn (`experiment_registry.json`), hỗ trợ resume nếu tiến trình bị gián đoạn. |
| **Bộ quy tắc chọn mô hình độc lập** | `ExperimentRegistry.select_best_trial()` | [Dòng 248-289](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L248-L289) | Cài đặt Selection Oracle: sắp xếp theo `ndcg_10 DESC`, `hit_rate_10 DESC`, `rank ASC` (Occam's razor), `reg_param ASC`. |
| **Quản lý Screening Cohort 5.000 users** | `ScreeningCohortManager` | [Dòng 293-352](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L293-L352) | Lấy mẫu tiền định 5.000 người dùng Validation tích cực (seed 42), lưu trữ cố định ra JSON đảm bảo tính tái lập. |
| **Chẩn đoán phân bố đuôi dài** | `compute_long_tail_diagnostics()` | [Dòng 355-460](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L355-L460) | Phân tích tỉ lệ xuất hiện của các phim theo các khoảng hỗ trợ (1 rating, 2-5 ratings, 6-10 ratings, >100 ratings) và thống kê điểm min/median/max. |
| **Thực thi huấn luyện và tầm soát** | `ALSTuner.fit_and_evaluate_trial()` | [Dòng 578-720](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L578-L720) | Huấn luyện mô hình ALS qua Spark MLlib, sinh gợi ý Top-20 cho screening cohort, tính toán các chỉ số Top-N. |
| **Kiểm định toàn phần Level 2** | `ALSTuner.run_full_validation_for_finalist()` | [Dòng 723-810](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L723-L810) | Sinh Top-20 cho toàn bộ 109.779 người dùng Validation tích cực, xuất file parquet đầy đủ và lưu trữ manifest. |

---

### 2. Kịch bản chạy toàn diện: [`scripts/run_m07_tuning.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py)

| Khối chức năng | Vị trí dòng | Mục đích thực thi |
| :--- | :--- | :--- |
| **Đọc dữ liệu siêu tốc bằng PyArrow** | [Dòng 45-88](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L45-L88) | Nạp 24.675.013 tương tác Train và 109.779 người dùng Validation mà không gây nghẽn RAM. |
| **Khởi tạo và kiểm tra Screening Cohort** | [Dòng 92-120](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L92-L120) | Cố định 5.000 người dùng kiểm định nhanh với seed 42. |
| **Giai đoạn 0: Đăng ký Baseline M05** | [Dòng 130-155](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L130-L155) | Tái sử dụng model M05 (rank 16, regParam 0.1) làm mốc so sánh chuẩn. |
| **Giai đoạn A: Regularization Sweep** | [Dòng 170-205](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L170-L205) | Quét regParam (0.3, 1.0, 3.0) để kiểm tra giả thuyết dập tắt Fluke Bias. |
| **Giai đoạn B: Latent Dimension Sweep** | [Dòng 210-245](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L210-L245) | Quét rank (8, 32) tại regParam tối ưu. |
| **Giai đoạn D: Controlled Diagnostic Branch** | [Dòng 250-295](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L250-L295) | Thử nghiệm bộ lọc hỗ trợ (min_ratings = 5, min_ratings = 20) để cô lập nguyên nhân toán học. |
| **Giai đoạn 5-6: Selection Oracle & Full Validation** | [Dòng 300-360](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L300-L360) | Lựa chọn mô hình tối ưu, chạy Level 2 Full Validation và xuất toàn bộ báo cáo CSV, JSON, Parquet. |

---

### 3. Bộ kiểm thử tự động: [`tests/als/test_tuner.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py)

| Tên kiểm thử | Vị trí dòng | Trọng tâm kiểm thử |
| :--- | :--- | :--- |
| `test_guard_test_split_access` | [Dòng 18-35](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L18-L35) | Đảm bảo hàm ném `PermissionError` khi có chuỗi "test". |
| `test_trial_config_validation` | [Dòng 38-60](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L38-L60) | Kiểm tra kiểm soát biên cho rank <= 0, regParam < 0, maxIter <= 0. |
| `test_experiment_registry_lifecycle_and_persistence` | [Dòng 63-95](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L63-L95) | Kiểm tra ghi và đọc JSON registry nguyên tử, không làm mất trạng thái khi reload. |
| `test_experiment_registry_selection_rule` | [Dòng 98-140](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L98-L140) | Kiểm tra thứ tự ưu tiên: NDCG -> HitRate -> Occam's razor (ưu tiên rank nhỏ hơn). |
| `test_screening_cohort_manager` | [Dòng 143-175](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L143-L175) | Đảm bảo kích thước 5.000 users cố định và tính tiền định giữa các lần gọi. |
| `test_compute_long_tail_diagnostics` | [Dòng 178-225](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L178-L225) | Kiểm tra tính toán chính xác tỉ lệ phần trăm các khoảng phân bố số lượt đánh giá. |

---

## PHẦN 2: KỊCH BẢN BẢO VỆ TRỰC DIỆN 5 PHÚT (5-MINUTE ORAL DEFENSE SCRIPT)

### Phút 1: Đặt vấn đề và Mục tiêu Module M07
"Kính thưa Hội đồng, tại các module trước, chúng em đã xây dựng thành công bộ đánh giá Top-N chuẩn mực M02, mô hình Popularity Baseline M03 và huấn luyện mô hình Spark ALS cơ sở M05 trên toàn bộ 24.675.013 tương tác Train của MovieLens 25M.
Tại M06, khi đánh giá mô hình ALS ban đầu trên 109.779 người dùng Validation tích cực, chúng em phát hiện hiện tượng Fluke Bias nghiêm trọng: 65.57% số gợi ý bị chiếm bởi các phim chỉ có đúng 1 lượt đánh giá, dẫn đến HitRate@10 bằng 0.
Bước sang M07, nhiệm vụ khoa học của chúng em là: **Tiến hành tinh chỉnh siêu tham số có hệ thống trên tập Validation để xác định liệu việc điều chỉnh hệ số điều chuẩn và số chiều ẩn có thể khắc phục được Fluke Bias hay không.**"

### Phút 2: Thiết kế kỹ thuật và Giao thức thực nghiệm hai tầng
"Để thực hiện việc này một cách khoa học và tối ưu tài nguyên tính toán, chúng em đã thiết kế kiến trúc hai tầng trong file [`recommender/als/tuner.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py):
- **Tầng 1 - Screening Cohort:** Chọn mẫu tiền định 5.000 người dùng Validation với seed 42 cố định. Mọi cấu hình siêu tham số đều được sàng lọc nhanh trên cohort này.
- **Tầng 2 - Full Validation:** Chỉ dành cho mô hình chiến thắng được chọn bởi thuật toán `Selection Oracle`, thực hiện đánh giá toàn phần trên 109.779 người dùng.
- Về mặt an toàn dữ liệu, hàm `guard_test_split_access` đảm bảo tập Test bị cách ly 100%, ngăn ngừa mọi rủi ro rò rỉ dữ liệu."

### Phút 3: Kết quả thực nghiệm và Nghịch lý điều chuẩn ALS-WR
"Chúng em đã triển khai 5 lần thử nghiệm chính quy và 2 cấu hình chẩn đoán có đối chứng:
- Trong giai đoạn quét hệ số điều chuẩn `regParam` từ 0.1 lên 0.3, 1.0 và 3.0: Thay vì giảm bớt hiện tượng overfit, tỉ lệ phim 1 lượt đánh giá lại tăng vọt từ 65.57% lên **100.00%**!
- Lý do toán học: Spark ALS sử dụng cơ chế Weighted Regularization (ALS-WR), trong đó hệ số phạt tỷ lệ thuận với số lượt quan sát `n_i` của từng item (`lambda * n_i * I`). Khi tăng lambda, điểm dự đoán của các phim phổ biến bị co về 0 nhanh hơn nhiều so với phim 1 lượt đánh giá.
- Trong giai đoạn quét số chiều ẩn `rank` từ 8, 16 đến 32: Tỉ lệ phim 1-rating duy trì ở mức 95.7% và HitRate vẫn bằng 0. Thuật toán Selection Oracle đã kích hoạt nguyên lý Occam's Razor để chọn cấu hình **rank = 8, regParam = 0.3** làm mô hình finalist vì tính gọn nhẹ và tốc độ huấn luyện nhanh nhất (100.4 giây)."

### Phút 4: Bằng chứng từ Nhánh chẩn đoán (Diagnostic Support Filter)
"Để chứng minh các vector tiềm ẩn của ALS thực sự có giá trị chứ không phải mô hình bị hỏng, chúng em đã tạo nhánh chẩn đoán độc lập `ALS_PLUS_TRAIN_SUPPORT_FILTER`:
- Khi giữ nguyên vector của mô hình ALS và áp bộ lọc mặt nạ loại bỏ các phim có dưới 20 lượt đánh giá, tỉ lệ phim phổ biến trong Top-10 lập tức tăng lên **76.04%**, và hệ thống ghi nhận ngay HitRate@10 dương (**0.00022**) trên tập Screening.
- Điều này chứng minh một cách thực nghiệm rằng: Các nhân tử ẩn của ALS vẫn học được quy luật tương đồng sở thích, nhưng toàn bộ tín hiệu hữu ích này đã bị các phim rác đuôi dài che lấp hoàn toàn trong bài toán xếp hạng Top-N tường minh."

### Phút 5: Kết luận và Định hướng Khối 3B, 3C
"Tóm lại, kết luận khoa học của M07 là:
1. Về mặt kỹ thuật: Toàn bộ pipeline, registry và 125/125 unit tests đạt chuẩn 100% PASS.
2. Về mặt chất lượng mô hình: Việc tinh chỉnh siêu tham số trong không gian Explicit ALS không thể vượt qua giới hạn toán học của Fluke Bias.
Đây là một kết quả hoàn toàn trung thực, có giá trị học thuật cao, và chính là minh chứng thuyết phục nhất khẳng định sự cần thiết của **Khối 3B: Đồ thị Tri thức (Knowledge Graph)** nhằm bổ sung cấu trúc ngữ nghĩa, và **Khối 3C: Mô hình Lai (Hybrid Recommender)** để kết hợp sức mạnh của Popularity và Graph Embeddings.
Em xin chân thành cảm ơn Quý Thầy/Cô và sẵn sàng trả lời các câu hỏi phản biện."
