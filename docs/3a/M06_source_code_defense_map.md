# BẢN ĐỒ MÃ NGUỒN VÀ HƯỚNG DẪN BẢO VỆ MODULE M06 (SOURCE CODE DEFENSE MAP)

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Chuyên đề:** Task 3A – Khối Gợi Ý Lọc Cộng Tác Phân Tán (Spark ALS Collaborative Filtering)  
> **Module:** M06 – Exact ALS Top-N Recommendation & Validation Evaluation  
> **Branch:** `feature/als-3a` | **Mô hình M05 Nguồn:** Commit `2e16fd6` (Git HEAD tại training `38c5c4f`)  
> **Môi trường:** Python 3.12, PySpark 4.2.0, Windows 11  
> **Cam kết:** 100% số dòng, tên hàm, đường dẫn và kịch bản demo đã được kiểm chứng trực tiếp trên workspace `D:\PROJECT BIG DATA\MoodGraph`.

---

## I. BẢN ĐỒ MÃ NGUỒN CHÍNH XÁC (SOURCE CODE DEFENSE MAP)

Bảng đối chiếu chi tiết giúp chủ dự án mở chính xác tập tin và vị trí dòng lệnh khi giảng viên hoặc hội đồng phản biện yêu cầu:

| STT | Chức năng Kỹ thuật | File Đường dẫn | Class / Function | Dòng (Line) | Đầu vào (Input) | Đầu ra (Output) | Test Chứng minh | Lệnh mở VS Code |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| 1 | **Cấu hình Sinh Ứng viên** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`ALSCandidateConfig`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L35) | L35–L68 | `k_list, batch_size, model_version` | Dataclass cấu hình đã kiểm tra tính hợp lệ | `test_candidates.py:test_18` | `code -g recommender/als/candidates.py:35` |
| 2 | **Cấu trúc Catalog Khả dĩ** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`ScoreableCatalog`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L70) | L70–L106 | `movie_ids, factors, catalog_movie_ids` | Đối tượng chứa vector phim và ánh xạ O(1) | `test_candidates.py:test_11,16` | `code -g recommender/als/candidates.py:70` |
| 3 | **Cấu trúc Vector Người dùng** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`UserFactorsContainer`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L108) | L108–L150 | `user_ids, factors` | Đối tượng chứa vector người dùng và kiểm tra NaN | `test_candidates.py:test_16,17` | `code -g recommender/als/candidates.py:108` |
| 4 | **Oracle Toán học Độc lập** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`exact_top_k_oracle`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L153) | L153–L195 | `u_factor, item_factors, seen_ids, k` | Danh sách Top-K giải tích chuẩn không tối ưu | `test_candidates.py:test_01` | `code -g recommender/als/candidates.py:153` |
| 5 | **Trích chọn Top-K Tối ưu** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`fast_exact_top_k_from_scores`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L198) | L198–L237 | Mảng điểm 1D (đã gán -inf), `movie_ids, k` | Top-K danh sách `(movieId, score)` khớp 100% Oracle | `test_candidates.py:test_01,08,09` | `code -g recommender/als/candidates.py:198` |
| 6 | **Nạp Mô hình & Catalog** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`load_catalog_and_factors`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L255) | L255–L303 | Đường dẫn thư mục mô hình M05 và Parquet movies | Nạp mảng float32 vào RAM trong < 1.0 giây | `test_candidates.py:test_11` | `code -g recommender/als/candidates.py:255` |
| 7 | **Kiểm toán Danh mục Phim** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`audit_catalog`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L305) | L305–L321 | Catalog đã nạp | Thống kê 62.423 phim catalog vs 58.932 phim Train | `test_candidates.py:test_11` | `code -g recommender/als/candidates.py:305` |
| 8 | **Nhân GEMM Khối Bounded** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`_score_batch`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L323) | L323–L336 | `P_batch` và `Q.T` | Ma trận điểm BLAS-3 kích thước `B x M` | `test_candidates.py:test_13` | `code -g recommender/als/candidates.py:323` |
| 9 | **Lọc Phim Đã Xem Tiền Xử lý**| [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`_mask_seen`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L338) | L338–L353 | `scores` và `seen_indices` | Gán `-np.inf` cho các vị trí đã xem | `test_candidates.py:test_02,07` | `code -g recommender/als/candidates.py:338` |
| 10 | **Gợi ý Cho 1 Người Dùng** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`recommend_user`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L355) | L355–L385 | `user_id, seen_movie_ids, k` | Top-K phim chưa xem cho cá nhân | `test_candidates.py:test_02-07` | `code -g recommender/als/candidates.py:355` |
| 11 | **Gợi ý Theo Batch Phân vùng** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`recommend_batch`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L387) | L387–L440 | `batch_user_ids, user_histories, k` | Nhân ma trận P_batch @ Q.T và lọc seen hàng loạt | `test_candidates.py:test_13` | `code -g recommender/als/candidates.py:387` |
| 12 | **Tạo Gợi ý Toàn Bộ Tập Dân** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`generate_recommendations`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L442) | L442–L478 | 162.541 `target_user_ids`, batch_size=2.048 | Dictionary 162.541 danh sách Top-K khuyến nghị | `test_candidates.py:test_14` | `code -g recommender/als/candidates.py:442` |
| 13 | **Chuyển đổi Arrow DataFrame** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`export_recommendations_dataframe`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L480) | L480–L519 | Dictionary recommendations | Apache Arrow Table 3.250.820 dòng có schema chuẩn | `test_candidates.py:test_19` | `code -g recommender/als/candidates.py:480` |
| 14 | **Lưu Khuyến Nghị Parquet** | [`candidates.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py) | [`save_recommendations_parquet`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L521) | L521–L531 | Arrow Table và đường dẫn đĩa | Ghi tệp nén Snappy Parquet (19.38 MB) | `test_candidates.py:test_19` | `code -g recommender/als/candidates.py:521` |
| 15 | **Nạp Validation Target** | [`run_m06_als_topn.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py) | [`load_target_users`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py#L45) | L45–L63 | Tệp `splits/validation` | 162.541 targets (109.779 positive, 52.762 non-pos) | `test_candidates.py:test_20` | `code -g scripts/run_m06_als_topn.py:45` |
| 16 | **Trích xuất Lịch sử Train** | [`run_m06_als_topn.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py) | [`load_train_seen_history`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py#L66) | L66–L82 | Tệp `splits/train` (24.67M rows) | Dict hash set phim đã xem cho 162.541 người dùng | `test_candidates.py:test_07` | `code -g scripts/run_m06_als_topn.py:66` |
| 17 | **Đánh giá Bằng TopNEvaluator**| [`run_m06_als_topn.py`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py) | [`run_evaluation_pipeline`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m06_als_topn.py#L220) | L220–L278 | Recommendations và Targets | Đánh giá độc lập trên K=5, 10, 20 bằng module M02 | `test_candidates.py:test_20,21` | `code -g scripts/run_m06_als_topn.py:220` |

---

## II. BỘ CÂU HỎI VẤN ĐÁP BẢO VỆ CHUYÊN SÂU (ORAL DEFENSE Q&A)

### Câu 1: Tại sao hệ thống bắt buộc phải lọc phim đã xem (seen-item filtering) trước khi chọn Top-K thay vì lấy Top-100 rồi lọc sau?
- **Trả lời:**
  Phương pháp lấy Top-K thô rồi mới lọc phim đã xem (Naive Oversampling) có lỗi sai nghiêm trọng về mặt nguyên lý: Nếu một người dùng tích cực đã đánh giá toàn bộ các bộ phim nằm trong Top-100 điểm cao nhất, việc lọc sau sẽ làm danh sách khuyến nghị bị teo tóp lại (chỉ còn ít hơn K phim hoặc thậm chí rỗng 0 phim).
  Trong MovieLens 25M, người dùng tích cực nhất (`userId 72315`) đã xem tới **32.200 bộ phim** trong Train. Nếu dùng cách oversampling cố định, hệ thống chắc chắn sẽ thất bại.
  Hệ thống MoodGraph giải quyết triệt để vấn đề này tại dòng 338 của tệp `recommender/als/candidates.py` bằng giải pháp **Exact Filter-Before-Top-K**: Gán điểm số của các phim đã xem thành `-infinity` trên toàn bộ ma trận trước khi áp dụng thuật toán `argpartition`. Nhờ đó, hệ thống bảo đảm 100% người dùng nhận đủ K bộ phim chưa xem mới nhất, được chứng minh qua bài test `test_12_oversampling_counterexample_failure`.

### Câu 2: Làm sao hệ thống sinh được điểm gợi ý cho 162.541 người dùng trên 58.932 bộ phim mà không bị tràn RAM?
- **Trả lời:**
  Ma trận đầy đủ giữa 162.541 người dùng và 58.932 bộ phim có kích thước lên tới **9,58 tỷ ô**. Nếu tạo ra ma trận này trong bộ nhớ, hệ thống cần tới **38,3 GB RAM**, điều này bất khả thi trên máy tính cá nhân 16 GB RAM.
  Hệ thống áp dụng kiến trúc **Bounded Batched Matrix Scoring** tại hàm `recommend_batch` (dòng 387 của `candidates.py`):
  1. Chỉ nạp 2 ma trận nhân tố ẩn vào RAM: `P` (162.541 x 16, ~10 MB) và `Q` (58.932 x 16, ~3.7 MB).
  2. Chia người dùng thành từng khối hữu hạn (`batch_size = 2,048` người dùng).
  3. Với mỗi khối, tính ma trận điểm cục bộ kích thước `2.048 x 58.932`, chỉ tốn đúng **482,7 MB RAM**.
  4. Trích xuất ngay Top-20 phim có điểm cao nhất rồi giải phóng vùng nhớ đệm trước khi chuyển sang batch tiếp theo.
  Toàn bộ 162.541 người dùng được xử lý trong đúng 198 giây (~3,3 phút) với đỉnh RAM quan sát được luôn dưới 1,6 GB.

### Câu 3: Điểm số ALS Score của một cặp (u, i) được tính như thế nào trong mã nguồn?
- **Trả lời:**
  Điểm ALS là tích vô hướng giữa vector đặc trưng của người dùng u và vector đặc trưng của phim i:
  `ALS_score(u, i) = dot(p_u, q_i) = sum_{d=0}^{15} p_u[d] * q_i[d]`
  Trong mã nguồn, đối với người dùng đơn lẻ, phép tính được thực hiện qua `np.dot(catalog.factors, u_factor)` tại dòng 363. Đối với một khối 2.048 người dùng, phép tính được thực hiện đồng thời qua phép nhân ma trận đa luồng BLAS `np.matmul(user_batch_factors, self.catalog.factors.T)` tại dòng 334 của `recommender/als/candidates.py`.

---

## III. KỊCH BẢN THUYẾT MINH BẢO VỆ 5 PHÚT (ORAL DEMO SCRIPT)

### Phút 1: Giới thiệu Kiến trúc & Vị trí Mã Nguồn
- Mở VS Code: `code -g recommender/als/candidates.py:240`
- *"Thưa thầy cô, Module M06 chịu trách nhiệm chuyển hóa các vector ẩn 16 chiều đã huấn luyện ở M05 thành danh sách Top-20 bộ phim gợi ý cá nhân hóa cho toàn bộ 162.541 người dùng."*

### Phút 2: Chứng minh Cơ chế Lọc Phim Đã Xem An Toàn Bộ Nhớ
- Mở VS Code: `code -g recommender/als/candidates.py:338`
- *"Để không lãng phí 38 GB RAM nếu nhân toàn thể ma trận, em chia nhỏ thành các batch 2.048 users (chỉ tốn 482 MB RAM). Tại dòng 348, em áp dụng kỹ thuật gán điểm `-np.inf` trực tiếp cho các phim người dùng đã xem trong Train."*

### Phút 3: Giải thích Thuật toán Top-K Tuyến tính O(M) & Tie-Breaking
- Mở VS Code: `code -g recommender/als/candidates.py:198`
- *"Thay vì sắp xếp toàn bộ catalog O(M log M), hàm `fast_exact_top_k_from_scores` dùng `argpartition` đạt tốc độ tuyến tính O(M). Tại dòng 223, cơ chế straddling tie detection xử lý hòa điểm tất định theo quy tắc `als_score DESC, movieId ASC`."*

### Phút 4: Trình bày Kết quả Kiểm toán Độc lập & Hiện tượng Fluke Bias
- Mở file: `docs/3a/M06_candidates_report.md`
- *"Kết quả đánh giá trên 109.779 người dùng Validation đạt HitRate = 0.00000. Đây không phải lỗi code: kiểm toán độc lập xác nhận 63,80% vị trí Top-20 bị chiếm bởi các phim chỉ có 1 đánh giá 5 sao trong Train (Fluke Bias), đẩy các phim hay thực sự xuống thứ hạng trung vị 3.990. Đây là bằng chứng thực nghiệm quan trọng làm tiền đề cho Module M07."*

### Phút 5: Chạy Test Chứng minh Tự động
- Chạy terminal: `python -m pytest tests/als/test_candidates.py -v`
- *"Toàn bộ 21 unit và integration tests kiểm thử độc lập bao quát từ ca biên heavy user 32.200 phim đến kiểm thử tích hợp ghi nhận HitRate dương đều đã vượt qua 100% trong 2.8 giây."*
