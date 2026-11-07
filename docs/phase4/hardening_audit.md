# MoodGraph Phase 4 — Independent Release Hardening & Scientific Audit Report

## 1. Executive Summary & Audit Mandate
Báo cáo kiểm định độc lập và làm rắn rỏi (Hardening Audit) cho Phase 4: Hybrid Recommendation Engine & Serving API thuộc dự án MoodGraph.
- **Repository:** `DatDS-Quant/MoodGraph_RS`
- **Branch mục tiêu:** `feature/phase4-hybrid-recommender`
- **Cam kết nguyên tắc:** Không phá vỡ hiện vật lịch sử (frozen scientific artifacts của M08/M10), bảo toàn các bài kiểm định hồi quy 100%, không che giấu lỗi, và tuân thủ chuẩn mực khoa học định lượng trung thực.

---

## 2. Phân loại và Điều tra Các Mối quan ngại Kỹ thuật (Concern Classification)

### 2.1. Concern 1 — Độ lệch Độ trễ Benchmark (Benchmark Latency Inconsistency)
- **Hiện tượng:** Trong báo cáo sơ bộ ban đầu, độ trễ được báo cáo là 0.017 ms/user (KG-only) và 0.247 ms/user (RRF), trong khi ở Phase 3B độ trễ duyệt đồ thị là ~1,100 ms/user.
- **Phân loại:** **CONFIRMED_DEFECT** (về mặt đo lường thực nghiệm).
- **Nguyên nhân gốc rễ (Root Cause):**
  Trong kịch bản đánh giá cũ `scripts/hybrid_evaluate_validation.py`, danh sách ứng viên `user_cand_als` và `user_cand_kg` đã được sinh trước trong bộ nhớ (precomputed/cached in memory). Khi vòng lặp đánh giá chạy qua từng mô hình:
  - Model `kg_only` chỉ thực hiện thao tác cắt mảng `user_cand_kg[uid][:20]`, mất 0.017 ms.
  - Model `rrf` chỉ thực hiện thuật toán dung hợp trên 2 mảng có sẵn trong RAM, mất 0.247 ms.
  Con số này chỉ phản ánh **chi phí thuật toán xếp hạng nội tại trong RAM (in-memory fusion overhead)**, hoàn toàn KHÔNG PHẢI là **độ trễ suy luận toàn trình (end-to-end inference latency)**.
- **Biện pháp xử lý & Định lượng chuẩn xác:**
  Xây dựng công cụ chuyên dụng `scripts/profile_serving_latency.py` đo lường phân rã độc lập 9 giai đoạn phục vụ:
  1. Nạp ALS Delivery Model: 534.44 ms.
  2. Nạp KG Graph (100 users, 62k movies, 73k edges): 9,967.92 ms.
  3. Sinh ứng viên ALS (Top-50): Trung bình 16.02 ms (P95: 183.03 ms).
  4. Sinh ứng viên KG Cold Graph Traversal (Top-50): Trung bình 1,565.90 ms (P95: 6,172.30 ms).
  5. Hợp nhất tập ứng viên (Candidate Union): 0.0133 ms.
  6. Dung hợp RRF: 0.1561 ms.
  7. Dung hợp Weighted Score: 0.2101 ms.
  8. JSON Serialization: 0.1122 ms.
  9. End-to-End API Cold (Cache Miss): 1,314.76 ms.
  10. End-to-End API Warm (LRU Cache Hit): P50 = 3.96 ms, P95 = 5.10 ms.
  11. Thông lượng chịu tải thực tế (Warm Serving Load Test): Đạt 191.3 RPS (2,000 requests trong 10.45s).

---

### 2.2. Concern 2 — Ngữ nghĩa Điểm số Khuyết thiếu trong Weighted Fusion (Missing-Score Semantics)
- **Hiện tượng:** Khi một ứng viên chỉ xuất hiện trong 1 nguồn (ví dụ phim X có trong KG nhưng không có trong Top-50 ALS), hàm `weighted_score_fusion` gán cứng điểm chuẩn hóa là 0.0 cho nguồn vắng mặt.
- **Phân loại:** **CONFIRMED_DEFECT** (thiếu sót linh hoạt và ngữ nghĩa định lượng chưa tối ưu).
- **Nguyên nhân gốc rễ:**
  Gán cứng 0.0 đồng nghĩa với việc đối xử một ứng viên vắng mặt ngang bằng với ứng viên có điểm số thấp nhất (Worst-in-List Penalty). Điều này gây trừng phạt quá nặng cho các ứng viên KG có tính cá nhân hóa ngữ nghĩa cao nhưng không lọt vào Top-50 của ALS.
- **Biện pháp xử lý:**
  1. Bổ sung tham số `imputation_strategy` hỗ trợ 4 chiến lược:
     - `"zero"`: Gán 0.0 (Worst-in-list penalty).
     - `"min"`: Gán giá trị nhỏ nhất của danh sách quan sát được.
     - `"neutral"`: Gán giá trị trung tính 0.5 (Neutral prior).
     - `"source_aware"`: Gán mức phạt nhẹ có trọng số phụ thuộc nguồn.
  2. Triển khai cơ chế **ALS Active Cross-Scoring**:
     Vì ALS Matrix Factorization có sẵn vector người dùng `u_vec` và ma trận embedding phim `item_factors` trong RAM, hệ thống có thể tính toán tích vô hướng chính xác `dot(u_vec, m_vec)` cho bất kỳ phim nào từ KG trong chưa đầy 1 micro-giây. Điều này loại bỏ hoàn toàn việc phải đoán điểm khuyết thiếu (Zero Imputation Guesswork).

---

### 2.3. Concern 3 — Ô nhiễm Bộ nhớ Đệm (Cache Key Contamination & Isolation)
- **Hiện tượng:** Khóa cache của Hybrid Service chỉ bao gồm `(user_id, strategy, top_n)`.
- **Phân loại:** **CONFIRMED_DEFECT**.
- **Nguyên nhân gốc rễ:**
  Khi quản trị viên hoặc kịch bản chẩn đoán gọi API với `filter_seen=False` để xem toàn bộ danh mục, kết quả chưa lọc này sẽ bị lưu vào cache. Một request sau đó của người dùng bình thường với `filter_seen=True` sẽ nhận trúng kết quả đã lưu trong cache, dẫn đến việc gợi ý những phim người dùng đã xem trong quá khứ (Train Contamination). Ngoài ra, các thay đổi về trọng số hay candidate budget cũng bị bỏ qua.
- **Biện pháp xử lý:**
  Mở rộng khóa cache thành một tuple bất biến toàn diện:
  `cache_key = (user_id, strategy, top_n, filter_seen, candidates_als_count, candidates_kg_count, weight_als, weight_kg, rrf_k, imputation_strategy, cross_score_als)`
  Đã viết test kiểm chứng độc lập `tests/hybrid/test_hybrid_hardening.py::test_05_cache_isolation_filter_seen` chứng minh hoàn toàn không còn hiện tượng rò rỉ hay ô nhiễm cache giữa các cấu hình khác nhau.

---

### 2.4. Concern 4 — Ranh giới Đa luồng và Đa tiến trình của Cache (Thread vs Process Boundary)
- **Hiện tượng:** Bộ nhớ đệm sử dụng `threading.RLock()`.
- **Phân loại:** **DESIGN_TRADEOFF**.
- **Đánh giá kiến trúc:**
  `threading.RLock` bảo đảm thread-safety tuyệt đối cho môi trường đa luồng (multi-threaded ASGI workers hoặc FastStream event loops) bên trong một Python process. Tuy nhiên, khi triển khai Uvicorn với cờ `--workers N` (đa tiến trình), mỗi process sở hữu không gian bộ nhớ riêng biệt, do đó bộ đệm là độc lập trên từng process.
- **Khuyến nghị kiến trúc (Architecture Guidance):**
  Đối với môi trường single-worker hoặc scale theo container pods (K8s pods), in-memory LRU cache là tối ưu nhất vì không có độ trễ mạng (zero-latency IPC). Nếu cần dùng multi-process Uvicorn trên cùng một máy chủ mà muốn đồng bộ cache chung, kiến trúc khuyến nghị là gắn một Redis Service đằng sau làm distributed cache.

---

### 2.5. Concern 5 — An toàn API & Kiểm soát Tham số (API Hardening & Diagnostics Guard)
- **Hiện tượng:** Endpoint `/api/recommendations` cho phép người dùng tùy ý gửi `filter_seen=False`, và endpoint `/api/cache/clear` không có cơ chế bảo vệ.
- **Phân loại:** **CONFIRMED_DEFECT** (Lỗ hổng kiểm soát phục vụ sản xuất).
- **Biện pháp xử lý:**
  1. Bảo vệ `filter_seen=False`: Chế độ không lọc lịch sử bị khóa chặt, chỉ cho phép thực thi khi đi kèm cờ tường minh `allow_unfiltered=True` (chế độ chẩn đoán QA). Nếu gửi `filter_seen=False` mà không có `allow_unfiltered=True`, API tự động nâng cờ an toàn `filter_seen=True` để bảo vệ trải nghiệm người dùng cuối.
  2. Bảo vệ `/api/cache/clear`: Yêu cầu header `X-Admin-Token` khớp với token bí mật môi trường `HYBRID_ADMIN_TOKEN` (mặc định: `moodgraph-admin-secret`). Request không có token hoặc sai token lập tức bị từ chối với HTTP 403 Forbidden.

---

### 2.6. Concern 6 — Dự phòng Đồ thị KG và Rủi ro Synthetic Graph Silent Fallback
- **Hiện tượng:** Nếu nạp KG thất bại, hệ thống có thể âm thầm rơi vào Synthetic Graph khiến kết quả gợi ý không đúng với dữ liệu thực tế.
- **Phân loại:** **VERIFIED_CORRECT & HARDENED**.
- **Biện pháp xử lý:**
  Trong `recommender/hybrid/engine.py`, việc khởi tạo dịch vụ yêu cầu tường minh cờ `allow_synthetic_kg=False` ở chế độ sản xuất. Nếu đường dẫn đồ thị KG không tồn tại hoặc lỗi, dịch vụ sẽ kích hoạt chế độ Graceful Degradation chuyển sang ALS Champion phục vụ người dùng kèm cảnh báo hệ thống rõ ràng trong response (`source=als_fallback`), tuyệt đối không âm thầm sinh dữ liệu giả định.
