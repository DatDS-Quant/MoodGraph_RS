# BẢN ĐỒ MÃ NGUỒN VÀ HƯỚNG DẪN BẢO VỆ MODULE M06 (SOURCE CODE DEFENSE MAP)

> **Dự án:** MoodGraph - Personalized Movie Recommendation with Knowledge Graphs and Apache Spark  
> **Chuyên đề:** Task 3A – Khối Gợi Ý Lọc Cộng Tác Phân Tán (Spark ALS Collaborative Filtering)  
> **Module:** M06 – Exact ALS Top-N Recommendation & Validation Evaluation  
> **Branch:** `feature/als-3a` | **Commit M05 Base:** `38c5c4f` | **Môi trường:** Python 3.12, PySpark 4.2.0, Windows 11  
> **Cam kết:** 100% số dòng, tên hàm, đường dẫn và kịch bản demo đã được kiểm chứng trực tiếp trên workspace `D:\PROJECT BIG DATA\MoodGraph`.

---

## I. BẢN ĐỒ MÃ NGUỒN CHÍNH XÁC (SOURCE CODE DEFENSE MAP)

Bảng đối chiếu chi tiết giúp chủ dự án mở chính xác tập tin và vị trí dòng lệnh khi giảng viên hoặc hội đồng phản biện yêu cầu:

| STT | Chức năng Kỹ thuật | File Đường dẫn | Class / Function | Dòng (Line) | Đầu vào (Input) | Đầu ra (Output) | Test Chứng minh | Lệnh mở VS Code |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :--- | :--- |
| 1 | **Cấu hình Sinh Ứng viên** | `recommender/als/candidates.py` | `ALSCandidateConfig` | L55–L68 | `k_list, batch_size, model_version` | Dataclass cấu hình đã kiểm tra tính hợp lệ | `test_candidates.py:test_18` | `code -g recommender/als/candidates.py:55` |
| 2 | **Cấu trúc Catalog Khả dĩ** | `recommender/als/candidates.py` | `ScoreableCatalog` | L71–L115 | `movie_ids, factors, catalog_movie_ids` | Đối tượng chứa vector phim và ánh xạ O(1) | `test_candidates.py:test_11,16` | `code -g recommender/als/candidates.py:71` |
| 3 | **Cấu trúc Vector Người dùng** | `recommender/als/candidates.py` | `UserFactorsContainer` | L118–L149 | `user_ids, factors` | Đối tượng chứa vector người dùng và kiểm tra NaN | `test_candidates.py:test_16,17` | `code -g recommender/als/candidates.py:118` |
| 4 | **Oracle Toán học Độc lập** | `recommender/als/candidates.py` | `exact_top_k_oracle` | L152–L183 | `u_factor, item_factors, seen_ids, k` | Danh sách Top-K giải tích chuẩn không tối ưu | `test_candidates.py:test_01` | `code -g recommender/als/candidates.py:152` |
| 5 | **Trích chọn Top-K Tối ưu** | `recommender/als/candidates.py` | `fast_exact_top_k_from_scores` | L186–L236 | Mảng điểm 1D (đã gán -inf), `movie_ids, k` | Top-K danh sách `(movieId, score)` khớp 100% Oracle | `test_candidates.py:test_01,08,09` | `code -g recommender/als/candidates.py:186` |
| 6 | **Nạp Mô hình & Catalog** | `recommender/als/candidates.py` | `load_catalog_and_factors` | L253–L304 | Đường dẫn thư mục mô hình M05 và Parquet movies | Nạp mảng float32 vào RAM trong < 1.0 giây | `test_candidates.py:test_11` | `code -g recommender/als/candidates.py:253` |
| 7 | **Kiểm toán Danh mục Phim** | `recommender/als/candidates.py` | `audit_catalog` | L306–L324 | Catalog đã nạp | Thống kê 62.423 phim catalog vs 58.932 phim Train | `test_candidates.py:test_11` | `code -g recommender/als/candidates.py:306` |
| 8 | **Gợi ý Cho 1 Người Dùng** | `recommender/als/candidates.py` | `recommend_user` | L326–L356 | `user_id, seen_movie_ids, k` | Top-K phim chưa xem cho cá nhân | `test_candidates.py:test_02-07` | `code -g recommender/als/candidates.py:326` |
| 9 | **Gợi ý Theo Batch Phân vùng** | `recommender/als/candidates.py` | `recommend_batch` | L358–L431 | `batch_user_ids, user_histories, k` | Nhân ma trận P_batch @ Q.T và lọc seen hàng loạt | `test_candidates.py:test_13` | `code -g recommender/als/candidates.py:358` |
| 10 | **Tạo Gợi ý Toàn Bộ Tập Dân** | `recommender/als/candidates.py` | `generate_recommendations` | L433–L475 | 162.541 `target_user_ids`, batch_size=2.500 | Dictionary 162.541 danh sách Top-K khuyến nghị | `test_candidates.py:test_14` | `code -g recommender/als/candidates.py:433` |
| 11 | **Chuyển đổi Arrow DataFrame** | `recommender/als/candidates.py` | `export_recommendations_dataframe` | L477–L517 | Dictionary recommendations | Apache Arrow Table 3.250.820 dòng có schema chuẩn | `test_candidates.py:test_19` | `code -g recommender/als/candidates.py:477` |
| 12 | **Lưu Khuyến Nghị Parquet** | `recommender/als/candidates.py` | `save_recommendations_parquet` | L519–L529 | Arrow Table và đường dẫn đĩa | Ghi tệp nén Snappy Parquet (19.38 MB) | `test_candidates.py:test_19` | `code -g recommender/als/candidates.py:519` |
| 13 | **Nạp Validation Target** | `scripts/run_m06_als_topn.py` | `run_m06_als_experiment:Step 1` | L54–L73 | Tệp `splits/validation` | 162.541 targets (109.779 positive, 52.762 non-pos) | `test_candidates.py:test_20` | `code -g scripts/run_m06_als_topn.py:54` |
| 14 | **Trích xuất Lịch sử Train** | `scripts/run_m06_als_topn.py` | `run_m06_als_experiment:Step 2` | L75–L93 | Tệp `splits/train` (24.67M rows) | Dict hash set phim đã xem cho 162.541 người dùng | `test_candidates.py:test_07` | `code -g scripts/run_m06_als_topn.py:75` |
| 15 | **Chạy 4 Cổng Benchmark** | `scripts/run_m06_als_topn.py` | `run_m06_als_experiment:Step 4` | L124–L160 | Mẫu user 1, heavy user 72315, batch 100, batch 2500 | Đo thời gian mili-giây và thông lượng users/giây | `test_candidates.py:test_07,13` | `code -g scripts/run_m06_als_topn.py:124` |
| 16 | **Đánh giá Bằng TopNEvaluator**| `scripts/run_m06_als_topn.py` | `run_m06_als_experiment:Step 6` | L177–L200 | Recommendations và Targets | Đánh giá độc lập trên K=5, 10, 20 bằng module M02 | `test_candidates.py:test_20` | `code -g scripts/run_m06_als_topn.py:177` |
| 17 | **So sánh với Popularity** | `scripts/run_m06_als_topn.py` | `run_m06_als_experiment:Step 7` | L223–L253 | Metrics ALS rank16 vs Metrics Popularity Count | Bảng đối chứng thực nghiệm chính thức | `test_candidates.py:test_20` | `code -g scripts/run_m06_als_topn.py:223` |
| 18 | **Xuất Báo Cáo JSON** | `scripts/run_m06_als_topn.py` | `run_m06_als_experiment:Output` | L266–L328 | Toàn bộ kết quả thực nghiệm | Tệp `m06_als_evaluation_results.json` | `run_m06_als_topn.py` | `code -g scripts/run_m06_als_topn.py:266` |

---

## II. BỘ CÂU HỎI VẤN ĐÁP BẢO VỆ CHUYÊN SÂU (ORAL DEFENSE Q&A)

### Câu 1: Tại sao hệ thống bắt buộc phải lọc phim đã xem (seen-item filtering) trước khi chọn Top-K thay vì lấy Top-100 rồi lọc sau?
- **Trả lời:**
  Phương pháp lấy Top-K thô rồi mới lọc phim đã xem (Naive Oversampling) có lỗi sai nghiêm trọng về mặt nguyên lý: Nếu một người dùng tích cực đã đánh giá toàn bộ các bộ phim nằm trong Top-100 điểm cao nhất, việc lọc sau sẽ làm danh sách khuyến nghị bị teo tóp lại (chỉ còn ít hơn K phim hoặc thậm chí rỗng 0 phim).
  Trong MovieLens 25M, người dùng tích cực nhất (`userId 72315`) đã xem tới **32.200 bộ phim** trong Train. Nếu dùng cách oversampling cố định, hệ thống chắc chắn sẽ thất bại.
  Hệ thống MoodGraph giải quyết triệt để vấn đề này tại dòng 397 của tệp `recommender/als/candidates.py` bằng giải pháp **Exact Filter-Before-Top-K**: Gán điểm số của các phim đã xem thành `-infinity` trên toàn bộ ma trận trước khi áp dụng thuật toán `argpartition`. Nhờ đó, hệ thống bảo đảm 100% người dùng nhận đủ K bộ phim chưa xem mới nhất, được chứng minh qua bài test `test_12_oversampling_counterexample_failure`.

### Câu 2: Làm sao hệ thống sinh được điểm gợi ý cho 162.541 người dùng trên 58.932 bộ phim mà không bị sập nguồn vì tràn RAM?
- **Trả lời:**
  Ma trận đầy đủ giữa 162.541 người dùng và 58.932 bộ phim có kích thước lên tới **9,58 tỷ ô**. Nếu tạo ra ma trận này trong bộ nhớ, hệ thống cần tối thiểu gần **40 GB RAM**, điều này bất khả thi trên máy tính cá nhân 16 GB RAM.
  Hệ thống áp dụng kiến trúc **Bounded Batched Matrix Scoring** tại hàm `recommend_batch` (dòng 358 của `candidates.py`):
  1. Chỉ nạp 2 ma trận nhân tố ẩn vào RAM: `P` (162.541 × 16, ~10 MB) và `Q` (58.932 × 16, ~3.7 MB).
  2. Chia người dùng thành từng khối hữu hạn (batch_size = 2.500 người dùng).
  3. Với mỗi khối, tính ma trận điểm cục bộ kích thước (2.500 × 58.932), chỉ tốn đúng **589 MB RAM**.
  4. Trích xuất ngay Top-20 phim có điểm cao nhất rồi giải phóng vùng nhớ đệm trước khi chuyển sang batch tiếp theo.
  Toàn bộ 162.541 người dùng được xử lý trong đúng 198 giây (~3.3 phút) với đỉnh RAM quan sát được luôn dưới 3.5 GB.

### Câu 3: Điểm số ALS Score của một cặp (u, i) được tính như thế nào trong mã nguồn?
- **Trả lời:**
  Điểm ALS là tích vô hướng giữa vector đặc trưng của người dùng u và vector đặc trưng của phim i:
  `ALS_score(u, i) = dot(p_u, q_i) = sum_{d=0}^{15} p_u[d] * q_i[d]`
  Trong mã nguồn, đối với người dùng đơn lẻ, phép tính được thực hiện qua `np.dot(catalog.factors, u_factor)` tại dòng 348. Đối với một khối 2.500 người dùng, phép tính được thực hiện đồng thời qua phép nhân ma trận đa luồng BLAS `np.matmul(P_batch, catalog.factors.T)` tại dòng 394 của `recommender/als/candidates.py`.

### Câu 4: Vì sao kết quả thực nghiệm M06 cho thấy HitRate@10 của ALS rank 16 lại đạt 0.00000 trong khi Popularity Count đạt 0.05519? Mô hình có bị lỗi code không?
- **Trả lời:**
  Code hoàn toàn không bị lỗi và đã được chứng minh khớp 100% với hàm giải tích toán học độc lập (`exact_top_k_oracle`).
  Đây là một phát hiện khoa học sâu sắc về bản chất của mô hình Lọc cộng tác ma trận tường minh (Explicit ALS) khi chưa được tinh chỉnh siêu tham số:
  1. Trong tập Train, có tới **10.324 bộ phim chỉ có đúng 1 lượt đánh giá** (thường là 5.0 sao).
  2. Với hệ số phạt nhỏ `regParam = 0.1`, mô hình Explicit ALS dự đoán điểm số của các bộ phim đơn lẻ này lên tới **5.0 đến 5.3 sao**.
  3. Ngược lại, các phim bom tấn kinh điển (*Pulp Fiction, The Shawshank Redemption*) có hàng vạn lượt đánh giá nên điểm dự đoán hội tụ đúng về điểm trung bình thật là **4.19 đến 4.42 sao**.
  4. Khi xếp hạng trên toàn bộ 58.932 phim, 300 đến 1.000 bộ phim vô danh 1 tương tác đã chiếm trọn các vị trí đầu bảng, đẩy các phim kinh điển trôi xuống vị trí từ 200 đến 4.000.
  5. Vì người dùng thực tế trong tập Validation không bao giờ xem các phim vô danh này, số lượng trúng đích (hit count) bị triệt tiêu về 0.
  Hiện tượng này được ghi nhận chính thức trong tài liệu `HERMES-M06-03` và là động lực kỹ thuật bắt buộc để triển khai **Module M07 (Hyperparameter Tuning)** với hệ số phạt lớn hơn nhằm co ép các phim ít tương tác về gốc tọa độ.

### Câu 5: Hệ thống xử lý các bộ phim không có vector nhân tố ẩn (Unscoreable Catalog Movies) như thế nào? Có gán điểm 0 không?
- **Trả lời:**
  Theo quy định nghiêm ngặt tại Mục IV của bản đặc tả M06, hệ thống **tuyệt đối không được gán điểm 0 giả mạo** cho các phim thiếu vector factor rồi coi đó là dự đoán của ALS.
  Trong toàn bộ danh mục 62.423 phim, có đúng 3.491 phim hoàn toàn không có tương tác nào trong tập Train. Các phim này được phân loại chính thức là `UNSCOREABLE_BY_ALS` và không tham gia vào không gian cạnh tranh của ALS.
  Đối với 30 người dùng trong tập Validation có phim mục tiêu rơi vào nhóm phim này, hệ thống ghi nhận là không trúng (miss) và **giữ nguyên 30 người dùng này trong mẫu số 109.779 người dùng** (không được tự ý loại bỏ để thổi phồng chỉ số).

### Câu 6: Quy tắc phá hòa (Tie-breaking) giữa hai bộ phim có cùng điểm số ALS được cài đặt như thế nào?
- **Trả lời:**
  Quy tắc phá hòa được cài đặt tất định theo hai tiêu chí:
  1. `als_score DESC` (ưu tiên điểm cao hơn).
  2. `movieId ASC` (khi bằng điểm số, chọn phim có mã định danh ID nhỏ hơn).
  Trong mã nguồn, hàm `fast_exact_top_k_from_scores` (dòng 186) tự động phát hiện các trường hợp hòa điểm vắt ngang ranh giới K (straddling ties) và sắp xếp ổn định qua tiêu chuẩn `key=lambda x: (-x[1], x[0])`.

---

## III. KỊCH BẢN DEMO THỰC THI TRỰC TIẾP TRONG 5 PHÚT (5-MINUTE LIVE DEFENSE SCRIPT)

Khi giảng viên hoặc hội đồng yêu cầu chạy minh chứng trực tiếp trên máy chấm, thực hiện theo 4 bước sau:

### Bước 1: Mở mã nguồn và giải thích cơ chế an toàn bộ nhớ (60 giây)
- Mở lớp sinh ứng viên: `code -g recommender/als/candidates.py:358`
- Chỉ vào dòng 394 (lệnh nhân ma trận khối `P_batch @ Q.T`) và dòng 397 (lệnh gán `-np.inf` để loại bỏ phim đã xem).
- Giải thích: *"Thưa thầy, hệ thống chia 162.541 người dùng thành từng batch 2.500 người để ma trận trung gian chỉ chiếm 589 MB RAM, không bao giờ tạo ma trận 10 tỷ ô gây tràn bộ nhớ."*

### Bước 2: Nạp artifact đã lưu và kiểm chứng không có phim đã xem (90 giây)
Chạy một lệnh Python ngắn gọn để tải bảng gợi ý Parquet và kiểm tra tính hợp lệ của người dùng tích cực nhất (`userId 72315`):
```powershell
python -c "
import pyarrow.parquet as pq
tbl = pq.read_table('artifacts/als/m06/m06_als_top20_recommendations.parquet')
df = tbl.to_pandas()
u_recs = df[df['userId'] == 72315]
print('User 72315 Recommendations Count:', len(u_recs))
print('Top-5 Recommended Movie IDs:', list(u_recs['movieId'][:5]))
print('Top-5 ALS Scores:', list(u_recs['als_score'][:5]))

# Kiểm tra xem có phim nào trong lịch sử Train bị lọt vào không
tbl_train = pq.read_table('data/processed/splits/train', columns=['userId', 'movieId'])
df_train = tbl_train.to_pandas()
seen_72315 = set(df_train[df_train['userId'] == 72315]['movieId'])
leaks = set(u_recs['movieId']).intersection(seen_72315)
print('Total Seen Items in Train:', len(seen_72315))
print('Seen Items Leaked into Top-20:', len(leaks))
"
```
**Kết quả hiển thị trên màn hình:**
- User 72315 Recommendations Count: 20
- Total Seen Items in Train: 32,200
- Seen Items Leaked into Top-20: **0** (Tuyệt đối không rò rỉ!).

### Bước 3: Chạy toàn bộ 20 bài kiểm thử tự động của Module M06 (60 giây)
```powershell
python -m pytest tests/als/test_candidates.py -v
```
**Kết quả:** 20/20 bài tests PASSED 100% trong ~2.0 giây.

### Bước 4: Mở báo cáo thực nghiệm và phân tích nguyên nhân khoa học (90 giây)
- Mở tệp [M06_candidates_report.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M06_candidates_report.md).
- Trình bày bảng đối chứng tại Mục III và phân tích hiện tượng Fluke Bias ở Mục IV:
- *"Thưa thầy, M06 chứng minh rằng mô hình Explicit ALS ban đầu chưa thể vượt Popularity vì bị các phim 1 tương tác 5 sao chiếm chỗ. Kết quả này tuân thủ nguyên tắc trung thực khoa học, không sửa mẫu số và định hướng chính xác cho việc tinh chỉnh siêu tham số ở Module M07."*
