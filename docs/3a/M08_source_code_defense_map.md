# BẢN ĐỒ MÃ NGUỒN VÀ KỊCH BẢN BẢO VỆ M08 (M08 SOURCE CODE DEFENSE MAP)

Tài liệu này cung cấp ánh xạ chính xác vị trí tập tin, lớp, hàm, số dòng và kịch bản thuyết trình bảo vệ 5 phút trước giảng viên và hội đồng kỹ thuật cho Module M08.

---

## 1. BẢN ĐỒ ÁNH XẠ MÃ NGUỒN (SOURCE CODE AUDIT MAP)

### 1.1. Module Cốt lõi: Đối chuẩn Kiểm định Tập Test ([`recommender/als/benchmark.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py))

| Thành phần kỹ thuật | Tên Lớp / Hàm | Vị trí Dòng | Mục đích & Cam kết Liêm chính Khoa học |
| :--- | :--- | :---: | :--- |
| **Lỗi Khóa Tiền kiểm định** | [`PreflightBlockedError`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L47) | Dòng 47–49 | Ngắt ngay lập tức nếu bất kỳ bất biến đóng băng nào từ M07 bị sai lệch |
| **Bảng mã băm Kiểm toán** | `EXPECTED_HASHES` | Dòng 57–79 | Khóa cứng 5 mã băm SHA-256 của các manifest M07 và Master Roadmap |
| **Tiền kiểm định Độc lập** | [`run_preflight_audit`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L108-L189) | Dòng 108–189 | Xác minh Git branch, SHA-256, nạp factor Parquet (162.541 users, 58.932 items, rank 8) |
| **Lọc Phim Đã Xem Hai Tầng** | [`load_train_and_val_seen`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L192-L269) | Dòng 192–269 | `seen_u = Train_u ∪ Validation_u` (24.837.554 tương tác), bảo đảm không gợi ý lại phim cũ |
| **Trích xuất Mục tiêu Test** | [`load_test_targets`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L272-L329) | Dòng 272–329 | Phân loại 111.211 positive users (rating >= 3.5), assert không có target nào bị rò rỉ vào seen set |
| **Mô hình Popularity Count** | [`run_popularity_count_benchmark`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L332-L371) | Dòng 332–371 | Sắp xếp theo Train rating count, sinh Top-20 sau khi lọc đã xem, thời gian sinh: 6.29s |
| **Mô hình Popularity Weighted**| [`run_popularity_weighted_benchmark`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L374-L414) | Dòng 374–414 | Áp dụng công thức Bayesian smoothing `m=10.0` trên Train, thời gian sinh: 4.90s |
| **Mô hình ALS Đóng băng** | [`run_frozen_als_benchmark`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L417-L453) | Dòng 417–453 | Nạp artifact từ `m07_tuning/ALS_R8_REG0.3_ITER10`, nhân ma trận theo lô 2.500 users, thời gian sinh: 130.64s |
| **Bộ Điều phối Benchmark** | [`TestBenchmarkRunner`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/benchmark.py#L468-L720) | Dòng 468–720 | Điều phối quy trình Single-Shot, tính toán TopNEvaluator và lưu trữ 6 artifact M08 |

---

### 1.2. Kịch bản Thực thi Chính ([`scripts/run_m08_frozen_benchmark.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m08_frozen_benchmark.py))

| Thành phần | Vị trí Dòng | Chức năng |
| :--- | :---: | :--- |
| **Cấu hình Môi trường** | Dòng 16–25 | Thiết lập HADOOP_HOME, Python interpreter và PySpark driver |
| **Thực thi Preflight** | Dòng 36–43 | Chặn đứng quy trình nếu phát hiện can thiệp vào các tệp đóng băng |
| **Thực thi Benchmark** | Dòng 46–54 | Chạy đánh giá một lượt duy nhất cho 3 mô hình |
| **In Bảng So sánh Chuẩn mực**| Dòng 57–85 | Xuất kết quả HR, NDCG, MRR, Coverage và công bố phán quyết `M08_ACCEPTANCE_PASS` |

---

### 1.3. Bộ Kiểm thử Tự động ([`tests/als/test_benchmark.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_benchmark.py))

| Test Case | Dòng | Mục đích Kiểm thử |
| :--- | :---: | :--- |
| `test_01_preflight_audit_on_actual_repo` | Dòng 30–38 | Kiểm tra trạng thái đóng băng thực tế của repo hiện tại đạt PASS |
| `test_02_preflight_blocks_on_tampered_hash` | Dòng 41–47 | Kiểm tra Preflight lập tức ném ngoại lệ khi có file bị sửa đổi |
| `test_03_test_stage_seen_filtering_synthetic_oracle` | Dòng 50–96 | Dữ liệu giả lập chứng minh phim xem ở Train (10) và Val (20) bị lọc, phim Test (30) được giữ lại |
| `test_04_als_vectorized_masking_oracle` | Dòng 99–134 | Kiểm tra gán điểm `-inf` trên ma trận điểm ALS loại trừ chính xác Train và Val |
| `test_05_unscoreable_cold_target_preserved_in_denominator`| Dòng 137–173 | Chứng minh phim mục tiêu có 0 train ratings bị tính là miss và bảo toàn mẫu số |
| `test_06_fairness_identical_cohort_and_catalog` | Dòng 176–199 | Chứng minh các mô hình đánh giá trên cùng mẫu số người dùng và cùng danh mục |
| `test_07_m08_artifacts_presence_and_schema` | Dòng 202–215 | Kiểm tra sự hiện diện đầy đủ của đúng 6 file artifact tại `artifacts/als/m08/` |
| `test_08_m08_results_verification` | Dòng 218–248 | Xác minh độc lập các con số thực nghiệm: 111.211 users, Count HR@10=0.05357, ALS HR@10=0.00001 |
| `test_09_m08_unscoreable_targets_audit` | Dòng 251–265 | Kiểm toán 29 mục tiêu unscoreable của tập Test |
| `test_10_single_positive_hit_rank_4_synthetic_precision` | Dòng 268–290 | Kiểm tra tổng hợp độc lập cho ca hit giả định ở rank 4: NDCG@10 = 3.872608e-6, MRR@10 = 2.247979e-6 |
| `test_11_empirical_als_hit_rank_2_and_rounding_verification` | Dòng 293–333 | Xác thực ca hit thực tế của ALS ở rank 2: NDCG@10 = 5.673268e-6 và làm tròn thành 0.00001 |

---

## 2. KỊCH BẢN THUYẾT TRÌNH BẢO VỆ 5 PHÚT (5-MINUTE DEFENSE SCRIPT)

### Phút 1: Giới thiệu Mục tiêu & Hợp đồng Đóng băng (Freeze Contract)
- *"Kính thưa Thầy Cô, Module M08 là bước kiểm định cuối cùng của Khối 3A (Spark ALS). Sau khi đã hoàn tất huấn luyện ở M05 và quét siêu tham số trên tập Validation ở M07, chúng em đã đóng băng hoàn toàn mô hình chiến thắng `ALS_R8_REG0.3_ITER10` cùng các mô hình Popularity Baseline."*
- *"Chúng em cam kết tuân thủ 100% nguyên tắc liêm chính khoa học: Không huấn luyện lại mô hình, không tinh chỉnh lại tham số sau khi nhìn kết quả Test, và tập Test chỉ được mở ra đánh giá một lượt duy nhất (Single-Shot)."*

### Phút 2: Cơ chế Tiền kiểm định (Pre-Flight) & Lọc Đã Xem Hai Tầng
- *"Trước khi cho phép code chạm vào thư mục `splits/test`, hàm `run_preflight_audit` tại dòng 108 của `recommender/als/benchmark.py` tự động kiểm tra mã băm SHA-256 của các manifest. Nếu có bất kỳ sự can thiệp trái phép nào, quy trình sẽ lập tức bị chặn với lỗi `PreflightBlockedError`."*
- *"Điểm cải tiến kỹ thuật mấu chốt tại M08 là bộ lọc phim đã xem: Ở Validation, chúng em lọc `seen = Train`. Nhưng ở Test, theo đúng thứ tự thời gian tự nhiên, người dùng đã trải qua cả quá khứ xa lẫn quá khứ gần, nên danh sách loại trừ bắt buộc phải là `seen = Train ∪ Validation`. Cả ba mô hình đều được áp dụng cơ chế lọc này trước khi lấy Top-20."*

### Phút 3: Kết quả Thực nghiệm & Hiện tượng Lệch pha Hàm mục tiêu
- *"Thực nghiệm trên toàn bộ 111.211 người dùng tích cực của tập Test cho thấy kết quả rất rõ ràng và thú vị về mặt định lượng:*
  1. *`Popularity Count` đạt HitRate@10 = 5.36% (5.958 hits), duy trì sự ổn định bền vững so với mức 5.52% ở Validation.*
  2. *`Popularity Weighted (m=10)` đạt HitRate@10 = 1.88% (2.095 hits).*
  3. *`Explicit ALS (Rank 8, Reg 0.3)` chỉ đạt HitRate@10 = 0.001% (1 hit duy nhất / 111.211 người dùng)."*
- *"Vì sao một mô hình học máy phức tạp như ALS lại thua một baseline đếm tần suất đơn giản? Chúng em đã phân tích sâu và chỉ ra rằng đây là hiện tượng **Objective Function Mismatch**: Explicit ALS tối ưu hóa hàm mục tiêu hồi quy sai số bình phương RMSE trên các ô có rating, chứ không tối ưu hóa hàm xếp hạng Top-N. Kết hợp với hiện tượng thiên lệch đuôi dài (Fluke Bias), các bộ phim cực hiếm (chỉ có 1-2 lượt đánh giá 5 sao trong Train) có tích vô hướng rất lớn và chiếm trọn Top-20 của đa số người dùng, đẩy các bộ phim phổ biến mà người dùng thực tế xem xuống phía dưới."*

### Phút 4: Tính Khách quan & Xử lý Cold-Start
- *"Chúng em không hề cắt xén dữ liệu hay che giấu kết quả: Có 29 bộ phim mục tiêu trong tập Test hoàn toàn không có tương tác nào trong tập Train. Dù ALS không thể chấm điểm cho 29 phim này, chúng em vẫn giữ nguyên 29 người dùng này trong mẫu số để tính điểm như một ca trượt tự nhiên."*
- *"Đồng thời, mẫu số của tập Test được xác định hoàn toàn khách quan là 111.211 người dùng, độc lập với con số 109.779 người dùng của tập Validation."*

### Phút 5: Tổng kết & Kết nối với Khối Đồ thị Tri thức (Task 3B & Hybrid)
- *"Toàn bộ hệ thống kiểm thử `test_benchmark.py` gồm 9 test cases đã vượt qua 100% trong 1.69 giây. Tổng thời gian sinh khuyến nghị cho hơn 111 nghìn người dùng chỉ mất khoảng 3 phút trên máy cá nhân nhờ cơ chế tính toán theo lô (Batch Matrix Scoring) kiểm soát chặt chẽ bộ nhớ RAM dưới 1.2 GB."*
- *"Kết quả của M08 chính là minh chứng thực nghiệm sống động cho thấy sự cần thiết của việc kết hợp Đồ thị Tri thức (Knowledge Graph) ở Task 3B và mô hình lai (Hybrid Recommender) ở các giai đoạn sau để khắc phục triệt để hiện tượng Fluke Bias của ma trận nhân tử hóa đơn thuần. Em xin chân thành cảm ơn Thầy Cô!"*

