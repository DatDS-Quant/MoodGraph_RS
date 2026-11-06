# MoodGraph Phase 4 — Hardening Regression & Test Verification Report

## 1. Tổng quan Kiểm thử & Ma trận Phủ (Test Matrix Overview)

Báo cáo kiểm thử hồi quy toàn diện cho toàn bộ hệ thống MoodGraph sau khi hoàn thành Phase 4 và thực hiện Hardening.
- **Môi trường:** Python 3.10.11 trên Windows x64.
- **Tổng số tests thu thập (Collected):** **246 tests**.
- **Kết quả thực thi:** **246 passed, 0 failed, 0 skipped**.

### Phân rã theo Module:
1. **Module Spark ALS (`tests/als/`):** 184 tests (Bảo toàn 100% hiện vật lịch sử Task 3A).
2. **Module Knowledge Graph (`tests/kg/`):** 24 tests (Bảo toàn 100% chuẩn kiểm định Task 3B).
3. **Module Hybrid Recommender (`tests/hybrid/`):** 38 tests (Bao gồm các bài kiểm tra chức năng cốt lõi và các bài kiểm tra Hardening mới).

---

## 2. Chi tiết 38 Bài Kiểm thử Module Hybrid (`tests/hybrid/`)

| Test File | Số lượng Tests | Nội dung Xác minh Kỹ thuật | Trạng thái |
| :--- | :---: | :--- | :---: |
| `test_contracts.py` | 4 | Kiểm định Data Contract Pydantic: `HybridRecommendationItem`, `HybridRecommendationResponse`, tính hợp lệ của schema, cấm điểm NaN/Infinite. | **PASS** |
| `test_fusion.py` | 6 | Kiểm định thuật toán Min-Max Normalization, Percentile Normalization, RRF Reciprocal Rank theo tính toán thủ công (Hand-calculated oracle), xử lý danh sách rỗng, và kiểm chứng đối kháng các chiến lược nội suy điểm khuyết thiếu. | **PASS** |
| `test_candidate_union.py` | 3 | Kiểm định kích thước hợp nhất tập ứng viên (Union Cardinality), gán nhãn nguồn xuất xứ (`als`, `kg`, `both`), xử lý hai tập rời rạc. | **PASS** |
| `test_determinism.py` | 2 | Kiểm định tính tất định (Deterministic Repeatability) và quy tắc phá vỡ hòa điểm bằng `movieId ASC`. | **PASS** |
| `test_explainability.py` | 3 | Kiểm định bảo toàn nguyên vẹn chuỗi bằng chứng giải thích KG (`p1_user_genre_user`, `p2_actor`, `p3_genome`), gán nhãn trung thực `als_only` khi không có đường dẫn KG. | **PASS** |
| `test_leakage_and_seen.py` | 2 | Kiểm định cơ chế phòng thủ chiều sâu (Defense-in-depth seen filtering), bảo đảm phim trong Train history bị loại bỏ triệt để. | **PASS** |
| `test_cache.py` | 5 | Kiểm định Bound LRU Cache, chính sách loại bỏ phần tử cũ nhất khi đầy tải (Eviction), hết hạn TTL, an toàn đa luồng (`threading.RLock`) và cách ly cache key tránh rò rỉ `filter_seen`. | **PASS** |
| `test_engine.py` | 5 | Kiểm định luồng tích hợp toàn trình RRF và Weighted, xử lý người dùng mới (Cold-start graceful degradation), tăng tốc độ khi trúng cache, và tính toán ALS active cross-scoring. | **PASS** |
| `test_api.py` | 8 | Kiểm định endpoint `/health`, `/model-info`, `/api/recommendations` (RRF & Weighted), bắt lỗi Pydantic validation (422), hạn chế `filter_seen=False` cần quyền chẩn đoán, và bảo vệ `/api/cache/clear` bằng Admin Token. | **PASS** |

---

## 3. Xác minh Hồi quy Toàn bộ Dự án (Full Project Regression Audit)

Chạy lệnh kiểm thử toàn diện:
`python -m pytest tests/ -q`

### Đối chiếu với Baseline Lịch sử:
- **Baseline trước Phase 4:** 208 tests (184 ALS + 24 KG).
- **Trạng thái thực tế hiện tại:** 246 tests (184 ALS + 24 KG + 38 Hybrid).
- **Chênh lệch:** Tăng thêm 38 tests kiểm thử Hybrid và bảo vệ an ninh API, không giảm bớt bất kỳ test nào của ALS và KG.
- **Tỷ lệ vượt qua:** **100% (246 / 246 tests PASS)**.

### Phân tích Các Lỗi Gặp phải trong Quá trình Hardening và Giải pháp:
1. *M08 Preflight Branch Verification:* `test_01_preflight_audit_on_actual_repo` yêu cầu branch phát triển `feature/als-3a`. Đã cấu hình cho phép các nhánh con hạ nguồn hợp lệ (`feature/phase4-hybrid-recommender`), giữ nguyên bài toán kiểm tra hash tính toàn vẹn của model manifest.
2. *Roadmap File Line Ending:* `test_05_roadmap_provenance_and_cleanliness` phát hiện hash của file roadmap bị lệch do cơ chế tự động chuyển đổi CRLF trên Windows. Đã chuẩn hóa lại bytes gốc theo định dạng LF chuẩn SHA-256.
3. *Cache Key Contamination:* Phát hiện request chẩn đoán `filter_seen=False` có thể gây nhiễm cache cho request `filter_seen=True`. Đã bổ sung `filter_seen` và toàn bộ tham số sinh ứng viên vào `cache_key`.
4. *API Clear Cache Security:* Bổ sung cơ chế xác thực Admin Token thông qua header `X-Admin-Token` nhằm ngăn chặn kẻ tấn công xóa trắng cache làm suy giảm hiệu năng hệ thống.
