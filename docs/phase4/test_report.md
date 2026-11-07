# BÁO CÁO KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST REPORT) - PHASE 4

## 1. TỔNG QUAN KẾT QUẢ KIỂM THỬ

- **Thư mục kiểm thử**: `tests/hybrid/`
- **Môi trường kiểm thử**: Python 3.12.3, PyTest 8.4.2
- **Tổng số bài test Phase 4**: 33 bài test
- **Kết quả thực thi**: **33 PASSED, 0 FAILED, 0 SKIPPED (100% Pass Rate)**
- **Thời gian thực thi**: **2.27 giây**

---

## 2. CHI TIẾT KẾT QUẢ THEO NHÓM KIỂM THỬ (TEST GROUPS)

| Nhóm kiểm thử | File test | Số bài test | Trạng thái | Nội dung thẩm định |
| :--- | :--- | :---: | :---: | :--- |
| **Group A: Contracts & Schemas** | `tests/hybrid/test_contracts.py` | 4 | PASS | Dataclass immutability, type assertions, serialization `to_dict()`, bắt lỗi rank < 1 hoặc invalid types |
| **Group B: Candidate Union** | `tests/hybrid/test_candidate_union.py` | 3 | PASS | Lực lượng tập hợp hợp nhất `|C_hybrid|`, deduplication, gán nhãn nguồn gốc (`BOTH`, `ALS`, `KG`), disjoint sets |
| **Group C: Fusion Mathematics** | `tests/hybrid/test_fusion.py` | 5 | PASS | Đối chiếu toán học độc lập với giá trị tính bằng tay RRF và Weighted Score, Min-Max bounds, empty inputs |
| **Group D: Leakage & Seen Filter** | `tests/hybrid/test_leakage_and_seen.py` | 2 | PASS | Lọc phim đã xem trong Train phòng vệ nhiều lớp, hỗ trợ `custom_seen` override |
| **Group E: Explainability** | `tests/hybrid/test_explainability.py` | 3 | PASS | Bảo toàn 100% bằng chứng đường đi KG (P1/P2/P3), giải thích ALS trung thực qua nhân tử tiềm ẩn, không tạo path giả |
| **Group F: Determinism** | `tests/hybrid/test_determinism.py` | 2 | PASS | Phá vỡ thế hòa điểm bằng `movieId ASC`, tính tái lập 100% sau 20 lượt chạy lặp |
| **Group G: Engine Integration** | `tests/hybrid/test_engine.py` | 4 | PASS | Luồng tích hợp dịch vụ, xử lý Cold-Start minh bạch, đo đạc độ trễ tăng tốc khi trúng cache (< 20ms) |
| **Group H: Cache & Performance** | `tests/hybrid/test_cache.py` | 4 | PASS | Thao tác get/put, chính sách đào thải LRU eviction, tự động hết hạn TTL (1s), an toàn đa luồng 8 workers |
| **Group I: Serving API Endpoints** | `tests/hybrid/test_api.py` | 6 | PASS | Endpoints `/api/health`, `/api/model_info`, `/api/recommendations/{user_id}`, `/api/cache/clear`, HTTP 422 validation |

---

## 3. KIỂM THỬ HỒI QUY TÍCH HỢP TOÀN BỘ HỆ THỐNG (COMBINED REGRESSION)

- Lệnh thực thi:
  ```powershell
  python -m pytest tests/als/test_delivery.py tests/kg/ tests/hybrid/ -q
  ```
- Kết quả thu thập: **81 tests collected** (24 ALS delivery + 24 KG + 33 Hybrid)
- Kết quả thực thi: **81 PASSED, 0 FAILED (100% PASS)** trong thời gian **20.5 giây**.
- Xác nhận: Toàn bộ module Khối 3A (Spark ALS) và Khối 3B (Knowledge Graph) không hề bị suy thoái hay phá vỡ khi tích hợp Khối 4.

