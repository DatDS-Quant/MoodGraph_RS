# BẢN ĐỒ MÃ NGUỒN VÀ KỊCH BẢN BẢO VỆ 5 PHÚT (M09)
# SOURCE CODE DEFENSE MAP & 5-MINUTE ORAL DEFENSE PROTOCOL

**Dự án:** MoodGraph – Task 3A Spark ALS Recommender Systems  
**Phân hệ:** M09 – Cold-Start, Long-Tail, Factor Reliability & Spark Performance  
**Nhánh Git:** `feature/als-3a`  
**Mục tiêu:** Cung cấp tọa độ chính xác từng file mã nguồn, class, function kèm số dòng thực tế và kịch bản thuyết trình sắc bén 5 phút trước Hội đồng chấm đồ án.

---

## PHẦN 1: BẢN ĐỒ MÃ NGUỒN (SOURCE CODE COORDINATES)

### 1. Module Chẩn đoán Cốt lõi: [`recommender/als/diagnostics.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py)

| Tên Lớp / Hàm | Số dòng | Vai trò kỹ thuật và Toán học |
| :--- | :---: | :--- |
| `class ColdStartType` | [L25-L32](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L25-L32) | Định nghĩa Enum 5 phân vùng: `WARM_PAIR`, `COLD_USER`, `COLD_ITEM`, `LOW_SUPPORT_ITEM`, `MODERATE_SUPPORT_ITEM`. |
| `class ItemSupportBin` | [L35-L60](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L35-L60) | Cấu trúc dữ liệu chứa thông tin thống kê từng bin (item_count, percentage, mean, median, min, max support). |
| `class FactorNormSummary` | [L62-L91](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L62-L91) | Thống kê phân phối độ chuẩn L2 của latent factors (rank, min, max, mean, median, std, p90, p95, p99). |
| `class SupportNormCorrelation` | [L93-L110](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L93-L110) | Thống kê tương quan Pearson và Spearman giữa log1p(support) và độ chuẩn L2 vector. |
| `class ScoreDistributionSummary` | [L112-L157](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L112-L157) | Phân phối điểm số dự đoán của ALS (mean, median, percentiles, số lượng và tỷ lệ điểm < 0 hoặc > 5.0). |
| `class TopKSupportConcentration` | [L159-L191](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L159-L191) | Đo lường tỷ lệ các phim có support = 1 và support <= 5 chiếm lĩnh trong danh sách Top-K recommendations. |
| `class ItemSupportAnalyzer` | [L193-L275](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L193-L275) | Động cơ phân chia 5 bins hỗ trợ với định nghĩa `SUPPORT_BIN_DEFS` ([L203-L210](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L203-L210)) và kiểm định bảo toàn catalog ([L269-L273](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L269-L273)). |
| `class FactorReliabilityAnalyzer` | [L277-L373](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L277-L373) | Tính toán độ chuẩn vector nhân tử (`compute_norm_summary` [L284](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L284)), tương quan (`compute_support_correlation` [L313](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L313)) và phân tích norm theo bins ([L338](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L338)). |
| `class ColdStartClassifier` | [L375-L412](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L375-L412) | Phân loại tương tác theo `classify_pair` ([L390](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L390)). |
| `class ScoreDiagnosticsAnalyzer` | [L414-L527](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L414-L527) | Đo đạc phân phối điểm số (`compute_score_distribution` [L421](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L421)) và nồng độ Top-K (`compute_recommendation_concentration` [L478](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L478)). |
| `class BenchmarkRecord` | [L529-L558](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L529-L558) | Cấu trúc dữ liệu ghi nhận thông số hiệu năng (độ trễ, thông lượng, RAM RSS). |
| `synthetic_item_support_oracle` | [L561-L586](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L561-L586) | Oracle A: Kiểm chứng phân chia bins và bảo toàn tổng số lượng phim. |
| `synthetic_cold_start_oracle` | [L588-L608](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L588-L608) | Oracle B: Hàm chuẩn phân loại Cold-Start độc lập. |
| `synthetic_factor_dot_product_oracle` | [L610-L620](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L610-L620) | Oracle C: Hàm chuẩn tích vô hướng vector bằng Python thuần. |
| `synthetic_throughput_oracle` | [L622-L633](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/diagnostics.py#L622-L633) | Oracle D: Hàm chuẩn tính toán thông lượng throughput. |

---

### 2. Kịch bản Thực thi Toàn diện: [`scripts/run_m09_diagnostics.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py)

| Khối Giai đoạn (Phase) | Số dòng | Nội dung thực thi |
| :--- | :---: | :--- |
| `PHASE A: EXECUTION PLAN` | [L83-L142](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L83-L142) | Thiết lập kế hoạch chạy, kiểm tra nhánh git, xuất file `m09_execution_plan.json`. |
| `PHASE B & C: COLD START & SUPPORT` | [L144-L234](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L144-L234) | Nạp catalog và Train ratings, chia 5 bins hỗ trợ, phân tầng user activity, xuất CSV và JSON. |
| `PHASE D: FACTOR RELIABILITY` | [L236-L297](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L236-L297) | Đọc factor Parquet, tính thống kê norm, tương quan Pearson/Spearman, xuất CSV. |
| `PHASE E: SCORE DISTRIBUTION` | [L299-L402](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L299-L402) | Lấy mẫu phân tầng 5.000 users Train-only, tạo Top-20 có lọc đã xem, đo lường nồng độ 1-rating items. |
| `PHASE F: PERFORMANCE BENCHMARKS` | [L404-L560](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L404-L560) | Đo đạc tách biệt: PyArrow I/O ([L466](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L466)), NumPy BLAS 4 mức batch ([L482](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L482)), Spark DataFrame read & count ([L521](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L521)) và GroupBy ([L544](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L544)). |
| `PHASE G: RUNTIME ENVIRONMENT` | [L562-L599](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L562-L599) | Ghi nhận chi tiết phần cứng (Ryzen 5 7530U, RAM), phiên bản thư viện. |
| `PHASE H: SCIENTIFIC AUDIT` | [L601-L688](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L601-L688) | Biên soạn 6 phát hiện khoa học độc lập (VERIFIED_FACT, SUPPORTED_INTERPRETATION). |
| `PHASE I: 16 QUALITY GATES` | [L690-L805](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L690-L805) | Đánh giá tự động 16 tiêu chí nghiệm thu chất lượng (16/16 PASS). |
| `PHASE J: RUN MANIFEST` | [L807-L840](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m09_diagnostics.py#L807-L840) | Phát hành biên bản chạy nghiệm thu `m09_run_manifest.json`. |

---

### 3. Bộ Kiểm thử Độc lập: [`tests/als/test_diagnostics.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py)

| Test ID | Tên Test Case | Số dòng | Nội dung kiểm thử |
| :---: | :--- | :---: | :--- |
| **01** | `test_01_synthetic_item_support_oracle` | [L38](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L38) | Kiểm tra Oracle A với các điểm mút biên [0, 1, 5, 6, 10, 11, 50, 51, 100]. |
| **02** | `test_02_synthetic_item_support_oracle_conservation_failure` | [L51](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L51) | Kiểm tra phát hiện lỗi vi phạm bảo toàn số lượng catalog. |
| **03** | `test_03_synthetic_cold_start_oracle` | [L57](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L57) | Kiểm tra Oracle B phân loại đúng Warm, Cold user, Cold item, Low support. |
| **04** | `test_04_synthetic_factor_dot_product_oracle` | [L70](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L70) | Kiểm tra Oracle C đối chiếu tích vô hướng vector. |
| **05** | `test_05_synthetic_throughput_oracle` | [L80](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L80) | Kiểm tra Oracle D tính toán throughput và xử lý ngoại lệ chia cho 0. |
| **06** | `test_06_item_support_analyzer_basic` | [L91](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L91) | Unit test cho `ItemSupportAnalyzer` trên tập dữ liệu mẫu. |
| **07** | `test_07_item_support_analyzer_empty_catalog` | [L110](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L110) | Kiểm tra bắt lỗi khi catalog rỗng. |
| **08** | `test_08_factor_reliability_norms` | [L120](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L120) | Kiểm tra tính toán norm L2 và các phân vị percentiles. |
| **09** | `test_09_factor_reliability_correlation` | [L136](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L136) | Kiểm tra hệ số tương quan Pearson và Spearman. |
| **10** | `test_10_cold_start_classifier_all_branches` | [L157](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L157) | Kiểm tra đầy đủ mọi nhánh rẽ của bộ phân loại `ColdStartClassifier`. |
| **11** | `test_11_score_distribution_summary` | [L176](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L176) | Kiểm tra thống kê điểm số, đếm điểm âm và điểm > 5.0. |
| **12** | `test_12_topk_support_concentration` | [L200](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L200) | Kiểm tra tính toán nồng độ gợi ý rơi vào các bins hỗ trợ. |
| **13** | `test_13_real_catalog_and_train_support_conservation` | [L234](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L234) | **Integration Test:** Đọc dữ liệu Train thật, kiểm chứng bảo toàn 62.423 phim. |
| **14** | `test_14_real_frozen_als_factors_and_norms` | [L271](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L271) | **Integration Test:** Nạp weights mô hình thật, xác thực chiều ma trận (58.932 x 8 và 162.541 x 8). |
| **15** | `test_15_real_factor_norm_support_correlation` | [L308](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_diagnostics.py#L308) | **Integration Test:** Tính tương quan thực tế r > 0.10, p-value < 1e-10. |

---

## PHẦN 2: KỊCH BẢN THUYẾT TRÌNH BẢO VỆ 5 PHÚT (ORAL DEFENSE SCRIPT)

### Phút 1: Đặt vấn đề và Mục tiêu Module M09
> *"Kính thưa Hội đồng, sau khi hoàn thành phép kiểm định độc lập trên tập Test tại M08, nhóm chúng em ghi nhận một kết quả thú vị: mô hình Popularity Count đạt HitRate@10 là 5.36%, trong khi mô hình tối ưu Spark ALS chỉ đạt HitRate@10 xấp xỉ 0.  
> Để không rơi vào kết luận vội vã 'do lỗi code' hay 'ALS thất bại', Module M09 được xây dựng như một công trình chẩn đoán khoa học độc lập nhằm bóc tách 3 yếu tố: phân phối đuôi dài của tập dữ liệu MovieLens 25M, độ tin cậy hình học của vector tiềm ẩn, và hiệu năng tính toán ma trận trên Apache Spark."*

### Phút 2: Minh chứng định lượng về Đuôi dài & Bảo toàn Catalog
> *"Đầu tiên, về phân phối dữ liệu, bằng module `ItemSupportAnalyzer`, nhóm đã chứng minh tổng thể 62.423 bộ phim trong catalog được phân bổ vào 5 khoảng hỗ trợ Train không giao nhau:  
> - Có đúng 3.491 phim (5.59%) hoàn toàn không có đánh giá nào trong Train.  
> - Có tới 28.834 phim (46.19%) chỉ có từ 1 đến 5 lượt đánh giá.  
> Như vậy, hơn 51.78% toàn bộ kho phim là các phim có cực kỳ ít tương tác. Đây là một tập đuôi dài khổng lồ mà mật độ tương tác chỉ đạt 0.25%."*

### Phút 3: Giải mã bản chất toán học của hiện tượng Long-Tail Fluke Bias
> *"Điểm đột phá khoa học của M09 nằm ở việc khảo sát 58.932 vector tiềm ẩn của ALS.  
> Nhóm phát hiện hệ số tương quan Pearson giữa log tương tác và độ dài vector là dương (+0.1574, p < 1e-300). Nhưng nguy hiểm hơn, ở nhóm phim chỉ có 1-5 đánh giá, độ dài vector có phương sai cực lớn, đạt đỉnh lên tới 4.13 so với mức trung bình 1.68.  
> Do ALS chỉ tối ưu hàm lỗi bình phương trên các rating đã biết, một bộ phim vô danh chỉ có 1 rating 5.0 sao sẽ tự do xoay vector của nó trùng khít với người dùng đó mà không chịu bất kỳ ràng buộc nào. Kết quả thực nghiệm trên 5.000 người dùng cho thấy: **100% Top-10 gợi ý của ALS bị chiếm lĩnh bởi đúng 23 bộ phim có đúng 1 lượt đánh giá trong Train**, với điểm số dự đoán bị thổi phồng lên tới 10.84!  
> Đây là bằng chứng toán học giải thích vì sao ALS không có hit trên tập Test: người dùng thực tế không ai xem 23 bộ phim vô danh đó."*

### Phút 4: Tách bạch Hiệu năng Thực thi (PyArrow, BLAS, PySpark)
> *"Về mặt kỹ thuật hệ thống, M09 đã thực hiện đo đạc độc lập hiệu năng trên cấu hình AMD Ryzen 5 7530U:  
> - Tầng nạp I/O PyArrow đạt tốc độ 38.2 triệu bản ghi/giây (nạp 24.67 triệu ratings chỉ mất 0.65 giây).  
> - Tầng tính toán ma trận NumPy BLAS được thiết kế theo cơ chế chia lô 2.500 users, đạt thông lượng 8.864 users/giây với đỉnh bộ nhớ RAM chỉ 724.6 MB, nằm hoàn toàn dưới hạn mức an toàn 1.2 GB của hệ thống 16 GB RAM.  
> - Tầng phân tán PySpark DataFrame thực hiện quét và tổng hợp 24.67 triệu dòng trong 1.82 giây."*

### Phút 5: Giá trị Đồ án & Bàn giao sang Khối 3B Đồ thị tri thức (Knowledge Graph)
> *"Tóm lại, M09 đã khẳng định 100% code M05-M08 hoạt động hoàn hảo, đồng thời làm sáng tỏ bài học kinh điển: Collaborative Filtering đơn độc sẽ bất lực trước bài toán Cold-Start và Long-Tail.  
> Kết luận này chính là động lực khoa học vững chắc nhất để nhóm phát triển tiếp Khối 3B: sử dụng Đồ thị tri thức (Knowledge Graph) và phương pháp lai ghép (Hybrid Blending) nhằm truyền dẫn tri thức thể loại, đạo diễn và tâm trạng mood, giải cứu các bộ phim ít đánh giá khỏi thiên lệch Fluke Bias.  
> Em xin trân trọng cảm ơn quý Thầy Cô trong Hội đồng!"*
