# MoodGraph Phase 5: He thong Kien truc Backend & Luong Du lieu

## 1. Kien truc Phan tang 5 Tang (5-Tier Layered Architecture)

He thong Backend cua MoodGraph duoc to chuc theo mo hinh phan lop mot chieu nghiem ngat, ngan ngua hoan toan rui ro phu thuoc vong (Zero Circular Dependency):

```
+-------------------------------------------------------------------------------+
|                             FASTAPI APPLICATION                               |
|                         recommender/api/app.py                                |
|  - Lifespan Manager: Pre-warm Catalog (62K) & CSR Index (~50MB)               |
|  - Middleware: CORS, Request Tracing, Error Handling                          |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                            ROUTERS & API SCHEMAS                              |
|                          recommender/api/                                     |
|  - discovery_router.py:  /api/movies, /api/users, /api/recommendations        |
|  - lab_router.py:        /api/lab/models, /api/lab/compare, /api/lab/metrics  |
|  - interaction_router.py:/api/interactions/watchlist, /ratings, /preferences  |
|  - system_router.py:     /health, /api/system/cache/clear                     |
|  - schemas.py:           Pydantic v2 Type-Safe Contracts                      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                          APPLICATION SERVICES LAYER                           |
|                         recommender/services/                                 |
|  - CatalogService:       Tra cuu, tim kiem, loc the loai, phim tuong tu       |
|  - UserProfileService:   Tong hop ho so Train, phan cap hoat dong             |
|  - ExplainabilityService:Giai thich da huong P1/P2/P3 va Latent projection    |
|  - LabService:           Dieu phoi so sanh da mo hinh, tinh Jaccard & Spearman|
|  - UserInteractionService:Ghi nhan tuong tac demo va dong bo cache             |
+-------------------------------------------------------------------------------+
                                      |
                   +------------------+------------------+
                   |                                     |
                   v                                     v
+------------------------------------+ +----------------------------------------+
|      RECOMMENDATION ENGINES        | |            STORAGE REPOSITORIES        |
|      recommender/hybrid/           | |            recommender/storage/        |
|  - HybridRecommenderService        | |  - MovieCatalogRepository              |
|  - ALSDeliveryService              | |  - UserHistoryRepository (Zero Leak)   |
|  - KG KnowledgeGraph (P1/P2/P3)    | |  - ResearchMetricsRepository           |
|  - HybridRecommendationCache       | |  - SQLiteStateRepository (WAL Mode)    |
+------------------------------------+ +----------------------------------------+
                   |                                     |
                   v                                     v
+------------------------------------+ +----------------------------------------+
|      OFFLINE MODELS & INDICES      | |            DATA PERSISTENCE            |
|  - artifacts/models/als/m07/       | |  - data/processed/core/movies          |
|  - artifacts/als/m10/train_seen_csr| |  - data/processed/core/links           |
|  - InMemoryGraph (1128 Tags, 19 G) | |  - data/processed/splits/train        |
|                                    | |  - data/app_state.db (SQLite WAL)      |
+------------------------------------+ +----------------------------------------+
```

---

## 2. Phan tich Luong Du lieu (Data Flow Analysis)

### 2.1. Luong Mode A: Movie Discovery & Recommendations
1. **Nguoi dung tim kiem phim (`GET /api/movies?query=Star`):**
   - Router goi `CatalogService.search_movies()`.
   - `MovieCatalogRepository` thuc hien loc tren chi muc In-Memory title index trong O(K).
   - Tra ve danh sach phim duoc giau hoa kem duong dan IMDb va TMDb.
2. **Nguoi dung yeu cau goi y ca nhan hoa (`GET /api/recommendations/1`):**
   - Router lay singleton `HybridRecommenderService` tu application state.
   - Kiem tra cache: Neu trung khop -> Tra ve trong 0.04 ms.
   - Neu cache miss:
     * Sinh ung vien ALS thong qua phep nhan vector nguoi dung voi danh muc phim.
     * Sinh ung vien KG thong qua cac duong di P1 (Genre), P2 (Genome), P3 (Collaborative).
     * Ap dung defense-in-depth Seen Filtering bang CSR index tu tap Train.
     * Dung hop bang thuat toan RRF (Reciprocal Rank Fusion, k=60).
     * Luu vao cache va tra ve ket qua cho client.

### 2.2. Luong Mode B: Recommendation Lab
1. **So sanh da mo hinh (`POST /api/lab/compare`):**
   - `LabService` nhan danh sach mo hinh: `["als", "kg", "hybrid_rrf", "hybrid_weighted", "popularity"]`.
   - Chay tung mo hinh, do luong thoi gian thuc thi (`execution_time_ms`).
   - Tinh toan he so trung lap Jaccard giua cac cap mo hinh:
     `Jaccard(A, B) = |A ∩ B| / |A ∪ B|`
   - Tinh toan he so tuong quan hang Spearman tren tap phim chung:
     `Spearman = 1 - (6 * sum(d_i^2)) / (k * (k^2 - 1))`
   - Luu thong tin session vao bang `experiment_sessions` trong SQLite.

### 2.3. Luong Tuong tac Nguoi dung Demo
1. **Them phim vao Watchlist / Danh gia phim:**
   - Client goi `POST /api/interactions/watchlist` hoac `POST /api/interactions/ratings`.
   - `UserInteractionService` xac thuc `movieId` trong danh muc.
   - Ghi nhan vao SQLite bang `saved_movies` hoac `user_ratings` duoi che do WAL.
   - Tu dong lam sach (invalidate) cache goi y cua user do trong `HybridRecommendationCache`.

---

## 3. Co che Khoi dong Lifespan Pre-warming
- Trong cac he thong goi y quy mo lon, viec load model va scan file Parquet o request dau tien (cold-start) thuong ton tu 600ms den 1000ms.
- FastAPI `@asynccontextmanager lifespan` trong Phase 5 thuc hien nap toan bo tai nguyen vao bo nho truoc khi san sang lang nghe traffic:
  * Catalog Repository (62,423 phim, ~4.35 MB) nạp chỉ mục trong ~250ms.
  * Train Seen CSR Index (24.6M interactions, ~50 MB) nạp mảng offsets và movie_ids trong ~80ms.
  * Hybrid Engine pre-warmed và sẵn sàng phục vụ.
- Ket qua: Khong con hien tuong spike do tre o request dau tien, 100% cac truy van tra ve on dinh.
