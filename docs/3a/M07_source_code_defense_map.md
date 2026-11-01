# BẢN ĐỒ MÃ NGUỒN VÀ KỊCH BẢN BẢO VỆ M07 (ĐÃ KIỂM TOÁN CHÍNH XÁC)

- **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị Tri thức và Apache Spark
- **Mã module:** M07 (Khối 3A – Spark ALS)
- **Tài liệu:** Bản đồ số dòng mã nguồn (Exact Code Map) và Kịch bản bảo vệ 5 phút

---

## PHẦN 1: BẢN ĐỒ MÃ NGUỒN CHI TIẾT (EXACT SOURCE CODE MAP)

### 1. Module lõi điều phối tinh chỉnh: [`recommender/als/tuner.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py)

| Thành phần / Chức năng | Lớp / Hàm | Vị trí dòng | Mục đích kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Bảo vệ dữ liệu Test tuyệt đối** | `guard_test_split_access()` | [Dòng 48-60](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L48-L60) | Kiểm tra chuỗi đường dẫn, ném `PermissionError` nếu phát hiện bất kỳ truy cập nào tới tập `test`. |
| **Định nghĩa cấu hình thử nghiệm** | `TrialConfig` | [Dòng 63-95](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L63-L95) | Dataclass lưu trữ siêu tham số (`rank`, `reg_param`, `max_iter`, `model_family`), kiểm tra tính hợp lệ toán học. |
| **Nhật ký thử nghiệm nguyên tử** | `ExperimentRegistry` | [Dòng 173-290](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L173-L290) | Quản lý vòng đời các trial, lưu trữ JSON an toàn (`experiment_registry.json`), hỗ trợ resume nếu tiến trình bị gián đoạn. |
| **Bộ quy tắc chọn mô hình độc lập** | `ExperimentRegistry.select_best_model()` | [Dòng 271-310](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L271-L310) | Cài đặt Selection Oracle: sắp xếp theo `ndcg_10 DESC`, `hit_rate_10 DESC`, `rank ASC` (Occam's razor), `reg_param ASC`. |
| **Quản lý Screening Cohort 5.000 users** | `ScreeningCohortManager` | [Dòng 313-370](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L313-L370) | Lấy mẫu tiền định 5.000 người dùng Validation tích cực (seed 42), lưu trữ cố định ra JSON đảm bảo tính tái lập. |
| **Chẩn đoán phân bố đuôi dài** | `compute_long_tail_diagnostics()` | [Dòng 373-475](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L373-L475) | Phân tích tỉ lệ xuất hiện của các phim theo các khoảng hỗ trợ (1 rating, 2-5 ratings, 6-10 ratings, >100 ratings) và thống kê điểm min/median/max. |
| **Thực thi huấn luyện và tầm soát** | `ALSTuner.fit_and_evaluate_trial()` | [Dòng 578-720](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L578-L720) | Huấn luyện mô hình ALS qua Spark MLlib, sinh gợi ý Top-20 cho screening cohort, tính toán các chỉ số Top-N. |
| **Kiểm định toàn phần Level 2** | `ALSTuner.run_full_validation_for_finalist()` | [Dòng 723-810](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L723-L810) | Sinh Top-20 cho toàn bộ 109.779 người dùng Validation tích cực, xuất file parquet đầy đủ và lưu trữ manifest. |

---

### 2. Kịch bản chạy toàn diện: [`scripts/run_m07_tuning.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py)

| Khối chức năng | Vị trí dòng | Mục đích thực thi |
| :--- | :--- | :--- |
| **Đọc dữ liệu siêu tốc bằng PyArrow** | [Dòng 45-88](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L45-L88) | Nạp 24.675.013 tương tác Train và 109.779 người dùng Validation mà không gây nghẽn RAM. |
| **Khởi tạo Screening Cohort tiền định** | [Dòng 92-120](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L92-L120) | Cố định 5.000 người dùng kiểm định nhanh với seed 42. |
| **Giai đoạn 0: Đăng ký Baseline M05** | [Dòng 130-155](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L130-L155) | Tái sử dụng model M05 (rank 16, regParam 0.1) làm mốc so sánh chuẩn. |
| **Giai đoạn A: Regularization Sweep** | [Dòng 170-205](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L170-L205) | Quét regParam (0.3, 1.0, 3.0) để kiểm tra hành vi co ép điểm số và phân bố đuôi dài. |
| **Giai đoạn B: Latent Dimension Sweep** | [Dòng 210-245](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L210-L245) | Quét rank (8, 32) tại regParam tối ưu. |
| **Giai đoạn D: Controlled Diagnostic Branch** | [Dòng 250-295](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L250-L295) | Thử nghiệm bộ lọc hỗ trợ (min_ratings = 5, min_ratings = 20) để cô lập nguyên nhân toán học. |
| **Giai đoạn 5-6: Selection Oracle & Full Validation** | [Dòng 300-360](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m07_tuning.py#L300-L360) | Lựa chọn mô hình finalist, chạy Level 2 Full Validation và xuất toàn bộ báo cáo CSV, JSON, Parquet. |

---

### 3. Bộ kiểm thử tự động: [`tests/als/test_tuner.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py)

| Tên kiểm thử | Vị trí dòng | Trọng tâm kiểm thử |
| :--- | :--- | :--- |
| `test_guard_test_split_access` | [Dòng 32-48](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L32-L48) | Đảm bảo hàm ném `PermissionError` khi có chuỗi "test". |
| `test_trial_config_validation` | [Dòng 50-75](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L50-L75) | Kiểm soát biên cho rank <= 0, regParam < 0, maxIter <= 0. |
| `test_experiment_registry_lifecycle_and_persistence` | [Dòng 78-115](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L78-L115) | Kiểm tra ghi và đọc JSON registry nguyên tử, không làm mất trạng thái khi reload. |
| `test_experiment_registry_selection_rule` | [Dòng 118-160](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L118-L160) | Kiểm tra thứ tự ưu tiên: NDCG -> HitRate -> Occam's razor (ưu tiên rank nhỏ hơn). |
| `test_screening_cohort_manager` | [Dòng 163-228](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L163-L228) | Đảm bảo kích thước 5.000 users cố định và tính tiền định giữa các lần gọi. |
| `test_compute_long_tail_diagnostics` | [Dòng 230-262](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L230-L262) | Kiểm tra tính toán chính xác tỉ lệ phần trăm các khoảng phân bố số lượt đánh giá. |
| `test_metric_source_consistency` | [Dòng 265-295](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L265-L295) | Kiểm tra số liệu M03 khớp với `artifacts/m03_popularity_results.json` (HR=0.05519, NDCG=0.02789). |
| `test_cohort_specific_coverage` | [Dòng 298-325](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L298-L325) | Phân biệt rõ catalog coverage trên 5.000 screening users vs 109.779 full users. |
| `test_hit_count_and_denominator_consistency` | [Dòng 328-344](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L328-L344) | Kiểm tra công thức HitRate = hit_count / positive_cohort_size. |
| `test_model_selection_tie_breaking` | [Dòng 347-380](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L347-L380) | Kiểm tra Selection Oracle giải hòa theo Occam's Razor khi toàn bộ trials có HR=0. |
| `test_screening_vs_full_validation_metric_provenance` | [Dòng 383-400](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_tuner.py#L383-L400) | Kiểm tra tính rõ ràng về nguồn gốc của metric screening vs full validation. |

---

## PHẦN 2: KỊCH BẢN BẢO VỆ TRỰC DIỆN 5 PHÚT (5-MINUTE ORAL DEFENSE SCRIPT)

### Phút 1: Bối cảnh và Mục tiêu Khoa học
"Kính thưa Quý Thầy/Cô trong Hội đồng,
Sau khi hoàn tất bộ đánh giá Top-N tại M02, mô hình Popularity Baseline tại M03 với HitRate@10 đạt 5.52%, và huấn luyện mô hình Spark ALS cơ sở tại M05, chúng em nhận thấy tại M06 rằng mô hình ALS ban đầu bị ảnh hưởng bởi hiện tượng Fluke Bias: 65.57% vị trí gợi ý bị chiếm bởi các phim chỉ có đúng 1 lượt đánh giá trong Train, dẫn đến HitRate@10 bằng 0.
Mục tiêu khoa học của Module M07 là: **Tiến hành tinh chỉnh có hệ thống các siêu tham số chính (hệ số điều chuẩn regParam và số chiều ẩn rank) trên tập Validation để xác định xem liệu việc điều chỉnh này có thể cải thiện chất lượng xếp hạng Top-N hay không.**"

### Phút 2: Giao thức Thực nghiệm Hai Tầng và An toàn Dữ liệu
"Để bảo đảm tính chặt chẽ và tối ưu hóa tài nguyên tính toán, chúng em đã thiết kế kiến trúc hai tầng trong file [`recommender/als/tuner.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py):
- **Tầng 1 - Screening Cohort:** Chọn mẫu tiền định 5.000 người dùng Validation tích cực với seed 42 cố định. Mọi cấu hình siêu tham số đều được sàng lọc nhanh trên cohort này trong thời gian 7 đến 9 giây.
- **Tầng 2 - Full Validation:** Chỉ dành cho mô hình finalist được lựa chọn độc lập bởi thuật toán `Selection Oracle`, thực hiện đánh giá toàn phần trên 109.779 người dùng tích cực.
- Về an toàn dữ liệu, hàm `guard_test_split_access` đảm bảo tập Test bị cách ly 100%, ngăn ngừa mọi rủi ro rò rỉ dữ liệu."

### Phút 3: Kết quả Thực nghiệm và Phân tích Toán học
"Chúng em đã thực hiện 5 lần huấn luyện Spark ALS và 2 lượt chẩn đoán:
- **Khảo sát hệ số điều chuẩn:** Khi tăng `regParam` từ 0.1 lên 0.3, 1.0 và 3.0, tỉ lệ phim 1-rating trong Top-10 không giảm mà tăng lên 95.7% và 100.0%.
- Về mặt lý thuyết giải tích, chúng em đã chứng minh rằng trong trường hợp đồng nhất lý tưởng, số lượng đánh giá `n_i` triệt tiêu trong phương trình chuẩn của Spark ALS-WR. Tuy nhiên, trên dữ liệu MovieLens 25M, do các phim 1-rating 5-sao chỉ khớp một người dùng duy nhất nên vector của nó tự do xoay cùng hướng với người dùng đó. Ngược lại, phim phổ biến phải dung hòa hàng chục nghìn người dùng, khiến điểm dự đoán bị kéo về mức trung bình. Khi tăng điều chuẩn, điểm số bị co ngắn lại nhưng các phim 1-rating 5-sao vẫn giữ vị trí đứng đầu danh sách đề xuất.
- **Khảo sát số chiều ẩn:** Khi quét rank từ 8, 16 đến 32, HitRate vẫn bằng 0. Thuật toán Selection Oracle đã áp dụng nguyên lý Occam's Razor để chọn cấu hình **rank = 8, regParam = 0.3** làm mô hình tối giản ưu tiên (Complexity-preferred finalist) vì thời gian huấn luyện nhanh nhất (100.4 giây)."

### Phút 4: Bằng chứng từ Nhánh Chẩn đoán và Đối soát Số liệu
"Để xác minh năng lực biểu diễn của các vector ẩn, chúng em đã thực hiện nhánh chẩn đoán `ALS_PLUS_TRAIN_SUPPORT_FILTER`:
- Khi giữ nguyên các vector tiềm ẩn và che các phim có dưới 20 lượt đánh giá, tỉ lệ phim phổ biến trong Top-10 tăng lên 76.04%, và hệ thống ghi nhận ngay **24 hits tại K=10** trên nhóm Screening (đạt HitRate 0.48%).
- Điều này chứng minh rằng các vector đặc trưng ẩn thực sự có chứa tín hiệu tương quan sở thích, nhưng các tín hiệu này bị che lấp trong không gian Top-N không có bộ lọc hỗ trợ.
- Qua kiểm toán độc lập, chúng em đã đối soát và đồng nhất 100% số liệu: Popularity Count chuẩn mực đạt **HR@10 = 0.05519** và **NDCG@10 = 0.02789**, độ phủ danh mục của ALS M05 trên toàn tập Validation là **2.48% (1.545 phim)**."

### Phút 5: Kết luận và Định hướng Khối 3B, 3C
"Tóm lại, kết luận nghiệm thu của Module M07 là:
1. **Về kỹ thuật:** Đạt chuẩn **M07_ACCEPTANCE_PASS**, toàn bộ pipeline và 130/130 bài kiểm thử tự động đạt 100% PASS.
2. **Về chất lượng mô hình:** **M07_MODEL_QUALITY_NOT_IMPROVED**. Việc tinh chỉnh siêu tham số trong không gian Explicit ALS không cải thiện được chất lượng gợi ý Top-N.
Đây là một kết quả thực nghiệm trung thực, có giá trị học thuật cao, và chính là minh chứng thuyết phục nhất khẳng định sự cần thiết phải phát triển **Khối 3B: Đồ thị Tri thức (Knowledge Graph)** và **Khối 3C: Mô hình Lai (Hybrid Recommender)** nhằm kết hợp thông tin cấu trúc ngữ nghĩa và giải quyết triệt để bài toán gợi ý Top-N.
Em xin chân thành cảm ơn Quý Thầy/Cô và sẵn sàng tiếp thu các câu hỏi phản biện."
