# MoodGraph Phase 5: Preflight Baseline Audit

## 1. Thông tin Môi trường & Điểm mốc Ban đầu (Baseline Provenance)
- **Repository:** `https://github.com/DatDS-Quant/MoodGraph_RS`
- **Nhánh phát triển:** `feature/phase5-backend-platform` (tạo từ nhánh `main` tại commit `03e30fd5a919d6f0fc17b67895b8f3202ff363a0`).
- **Môi trường thực thi:** Python 3.12.3 / Windows x64.
- **Trạng thái Working Tree:** Sạch hoàn toàn (`nothing to commit, working tree clean`).
- **Thời điểm khởi tạo:** 2026-11-07 15:44:00 (UTC+7).

---

## 2. Kết quả Xác minh Kiểm thử Điểm mốc (Baseline Verification)

### 2.1. Kiểm thử Hồi quy Toàn hệ thống (Full Regression Suite)
- **Lệnh thực thi:** `python -m pytest tests/ -q`
- **Kết quả:** **246 passed, 0 failed, 0 skipped** (2 warnings) trong 278.64s.
  * Module Spark ALS (`tests/als/`): 184 tests PASS.
  * Module Knowledge Graph (`tests/kg/`): 24 tests PASS.
  * Module Hybrid Recommender (`tests/hybrid/`): 38 tests PASS.
- **Bộ kiểm thử nhanh:** `python -m pytest tests/als/test_delivery.py tests/kg/ tests/hybrid/ -q` -> **86 passed** trong 16.92s.

### 2.2. Kiểm định Tích hợp Hiện vật Thực tế (Real-Artifact Integration)
- **Lệnh thực thi:** `python scripts/verify_real_integration.py`
- **Kết quả:** **10 / 10 tiêu chí ĐẠT 100% PASS**:
  * Nạp ALS Delivery Service: 58,932 phim, 162,541 users.
  * Nạp KG Pilot Graph: 62,423 phim, 100 users, 73,720 cạnh Genome.
  * Gợi ý ALS-only, KG-only, Hybrid RRF, Hybrid Weighted hoạt động chuẩn xác trên dữ liệu thật.
  * Lọc phim đã xem (Train-seen filtering) loại bỏ 100% phim đã xem.
  * Tăng tốc bộ nhớ đệm: Cache Miss: 653 ms -> Cache Hit: 0.04 ms (Tăng tốc 16,000+ lần).
  * Xử lý Cold-Start: Trả về danh sách rỗng kèm `is_cold_start=True`.
  * Chuẩn hóa hợp đồng Pydantic: 100% hợp lệ.

---

## 3. Kiểm kê Thành phần Hệ thống (Component Inventory)

| Thành phần (Component) | Trạng thái Hiện tại | Định hướng Xử lý trong Phase 5 |
| :--- | :---: | :--- |
| **Spark ALS Model Serving** (`recommender/als/delivery.py`) | **EXISTING (STABLE)** | Tái sử dụng nguyên vẹn model finalist `ALS_R8_REG0.3_ITER10` và CSR train-seen index. |
| **Knowledge Graph Recommender** (`recommender/kg/`) | **EXISTING (STABLE)** | Tái sử dụng thuật toán duyệt đường đi P1, P2, P3 và InMemoryGraph pilot. Neo4j là tùy chọn triển khai. |
| **Hybrid Recommendation Engine** (`recommender/hybrid/engine.py`) | **EXISTING (STABLE)** | Tái sử dụng Candidate Union, RRF, Weighted Fusion, ALS cross-scoring và bounded LRU cache. |
| **MovieLens Datasets** (`data/processed/core/`, `splits/`) | **EXISTING (STABLE)** | Dữ liệu Parquet đã sẵn sàng: `movies`, `genome_tags`, `genome_scores`, `links`, `tags`, `splits/train`. |
| **FastAPI Base Serving** (`recommender/hybrid/api.py`) | **REUSABLE & EXTENDABLE** | Đã có các endpoint cơ sở: `/api/health`, `/api/model_info`, `/api/recommendations`, `/api/cache/clear`. Cần tái cấu trúc theo mô hình Router phân tầng. |
| **Movie Catalog APIs** (`/api/movies`, `/api/movies/{id}`) | **MISSING** | Cần xây dựng mới: Tìm kiếm tên phim, lọc theo thể loại/năm phát hành, phân trang an toàn (pagination). |
| **User Profile APIs** (`/api/users/{id}`, `.../profile`, `.../history`) | **MISSING** | Cần xây dựng mới: Trích xuất lịch sử tương tác và sở thích thể loại thuần túy từ tập Train (tuyệt đối cách ly Validation/Test). |
| **Dedicated Explainability API** (`/api/explanations/{uid}/{mid}`) | **MISSING** | Cần xây dựng mới: Truy xuất bằng chứng đồ thị và nhân tử tiềm ẩn khớp chính xác ngữ cảnh gợi ý. |
| **Recommendation Lab APIs** (`/api/lab/...`) | **MISSING** | Cần xây dựng mới: Registry mô hình, so sánh song song đa mô hình, hiển thị metric nghiên cứu phiên bản hóa thực tế từ `docs/phase4/`. |
| **Application State Persistence** (SQLite Storage) | **MISSING** | Cần xây dựng mới: Lưu trữ trạng thái người dùng tương tác thử nghiệm (phim đã lưu, đánh giá demo) mà không làm ô nhiễm tập Train 25M. |

---

## 4. Quyết định Kiến trúc & Phạm vi Triển khai Phase 5

1. **Bảo toàn Tuyệt đối Phase 4:** Không viết lại hay thay đổi logic toán học của các động cơ gợi ý cốt lõi. Phase 5 tập trung vào tầng Platform, Repository, Services và API Routers.
2. **Kiến trúc Phân tầng (Layered Architecture):**
   - **Tầng API (Routers):** `discovery_router`, `lab_router`, `user_router`, `movie_router`, `recommendation_router`.
   - **Tầng Dịch vụ (Application Services):** `CatalogService`, `UserProfileService`, `ExplainabilityService`, `LabService`, `UserInteractionService`.
   - **Tầng Truy xuất Dữ liệu (Repositories):** `ParquetCatalogRepository`, `TrainHistoryRepository`, `SQLiteStateRepository`.
   - **Tầng Động cơ (Model Serving):** Tái sử dụng `HybridRecommenderService`.
3. **Phân định Rõ ràng Hai Chế độ Trải nghiệm:**
   - **MODE A — Movie Discovery:** Phục vụ người dùng cuối tìm kiếm phim, xem chi tiết, khám phá gợi ý cá nhân hóa và bằng chứng giải thích.
   - **MODE B — Recommendation Lab:** Phục vụ nghiên cứu sinh / chuyên gia định lượng so sánh các mô hình, kiểm tra metric thực nghiệm và phân tích thứ hạng.

