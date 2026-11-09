# MoodGraph Phase 5: Kiem dinh Kien truc & Hop dong He thong (Architecture & Contract Audit)

**Nguoi lap bao cao:** Principal Software Architect  
**Ngay kiem dinh:** 2026-11-07  
**Phien ban He thong:** MoodGraph Phase 5 (Phat trien tren nen tang Phase 4 v4.0.0)  
**Trang thai He thong hien tai:** 246/246 Regression Tests PASS, 10/10 Real-Artifact Integration Tests PASS  

---

## 1. Tong quan & Bang Danh gia Cac Cong Kien truc (Architectural Gates Dashboard)

Kiem dinh kien truc nay danh gia toan dien trang thai ma nguon hien tai cua he thong MoodGraph sau Phase 4 va thiet lap ban thiet ke chi tiet cho Phase 5 (Nen tang Backend Service phuc vu 2 che do: **Mode A - Movie Discovery** va **Mode B - Recommendation Lab**).

### Bang danh gia cac cong kien truc (Architectural Gates Matrix)

| Ma Cong | Tieu chi Kiem dinh | Trang thai | Tom tat danh gia |
| :--- | :--- | :---: | :--- |
| **GATE-01** | **Ranh gioi Module & Tinh Dong goi** | **PARTIAL** | Core recommendation engines (ALS, KG, Hybrid) hoat dong chinh xac nhung `recommender/hybrid/engine.py` va `api.py` bi ro ri truu tuong (leaky abstraction): truy cap truc tiep vao thuoc tinh noi bo `user_factors` cua ALS va `movies` cua KG. API flat chua tach routers. |
| **GATE-02** | **Kien truc Phan tang Phase 5** | **PASS** | Mo hinh 5 tang duoc xac lap ro rang: API Routers -> Application Services -> Repositories -> Model Serving -> Infrastructure. Dam bao phu hop voi nguyen ly Dependency Inversion. |
| **GATE-03** | **Hop dong Public API Mode A** | **PASS** | Hop dong day du cho `/api/movies`, `/api/users`, `/api/recommendations`, `/api/explanations` voi day du kieu du lieu, phan trang, loc the loai va cam ket bao ve du lieu Train/Val. |
| **GATE-04** | **Hop dong Public API Mode B** | **PASS** | Hop dong day du cho `/api/lab/models`, `/api/lab/compare`, `/api/lab/metrics`, `/api/lab/metadata` ho tro so sanh da mo hinh song song, do do tuong dong Jaccard va he so tuong quan hang. |
| **GATE-05** | **Khong phu thuoc vong (Zero Circularity)** | **PASS** | Do thi phu thuoc mot chieu duoc chung minh. Lop contracts va config nam o goc (leaf). Khong ton tai bat ky chu trinh import nao giua cac goi. |
| **GATE-06** | **Quan ly Vong doi & Resource Lifespan** | **PARTIAL** | He thong Phase 4 hien tai su dung lazy initialization dan den hien tuong Cold-Start Latency Spike (> 600ms o request dau tien). Phase 5 can chuyen giao sang FastAPI `@asynccontextmanager lifespan` voi pre-warming bat buoc. |
| **GATE-07** | **Tuong thich nguoc 100% Phase 4** | **PASS** | Giu nguyen ven schema va hanh vi cua `/api/recommendations/{user_id}`, `/api/health`, `/api/model_info`, `/api/cache/clear`. |
| **GATE-08** | **Cach ly Du lieu Huan luyen & Kiem thu** | **PASS** | Tuyet doi khong truy van ratings tu validation hoac test partitions cho bat ky API nguoi dung nao; chi phuc vu ratings tu `data/processed/splits/train`. |

---

## 2. Kiem dinh Chi tiet Module Hien huu & Ranh gioi Trach nhiem

Sau khi ra soat sau 6 module nen tang:
- `recommender/hybrid/api.py`
- `recommender/hybrid/engine.py`
- `recommender/hybrid/contracts.py`
- `recommender/hybrid/config.py`
- `recommender/als/delivery.py`
- `recommender/kg/recommend.py`

Kien truc su dua ra cac danh gia chi tiet sau:

### 2.1. Module `recommender/hybrid/api.py`
- **Chuc nang hien tai:** Dinh nghia FastAPI app phuc vu 4 endpoint: `GET /api/health`, `GET /api/model_info`, `GET /api/recommendations/{user_id}`, `POST /api/cache/clear`.
- **Van de kien truc (Architectural Smells):**
  1. *Thiet ke don khoi (Monolithic API script):* Toan bo router, dependency getter, Pydantic schemas, va logic xu ly tham so quan tri token bi gom vao mot tep duy nhat (219 dong).
  2. *Khoi tao trang thai toan cuc thu dong (Ad-hoc Global State):* Bien `_service_instance: Optional[HybridRecommenderService]` duoc khoi tao lanh lung khi co request dau tien. Khong co su kiem soat vong doi server (FastAPI Lifespan).
  3. *Thieu cac router chuyen biet:* Khong co router cho Movie Catalog, User Profile, Lab Experiments, va Explainability.
  4. *Kiem tra Health Check thieu tinh thuc te:* Line 92-93 kiem tra `service._als_service is not None or True` luon luon tra ve `True` (bypassed check).

### 2.2. Module `recommender/hybrid/engine.py`
- **Chuc nang hien tai:** Dieu phoi HybridRecommenderService ket hop ung vien ALS va KG, thuc hien loc phim da xem (Train-seen filtering), ap dung Reciprocal Rank Fusion (RRF) hoac Weighted Score Fusion, chen metadata va cache ket qua qua `HybridRecommendationCache`.
- **Van de kien truc & Ro ri Truu tuong (Leaky Abstraction):**
  1. *Truy cap sau vao noi bo ALS (Line 183-207):* Logic `cross_score_als` tu y thau tom doi tuong `gen = getattr(self.als_service, "generator", None)` va truy cap truc tiep vao ma tran nhan tu `gen.user_factors.factors` de thuc hien `np.dot`. Dieu nay pha vo nguyen ly dong goi cua ALSDeliveryService. ALSDeliveryService can phai cung cap public method `batch_score_items(user_id, movie_ids)` thay vi de Engine tu thao tac con tro mang NumPy.
  2. *Phu thuoc thuoc tinh KG InMemoryGraph (Line 298-305):* Logic doc ten phim su dung `movie_titles = getattr(self.kg_graph, "movies", {})`. Khi he thong chay voi Neo4jGraph that, thuoc tinh `.movies` khong phai la tu dien in-memory, dan den viec ten phim bi bo trong hoac bo qua. Viec lay thong tin metadata cua phim phai thuoc ve `CatalogRepository`, khong duoc ky sinh vao graph database.
  3. *Lazy Imports nam rai rac trong runtime:* Cac lenh import `from recommender.als.delivery import get_delivery_service` va `from recommender.kg.recommend import get_default_graph, recommend_kg` duoc dat ben trong property va method `recommend()`. Mac du giup tranh circular import tam thoi o cap file, no gay kho khan cho static type analysis va lam cham nhip xu ly luc run-time.

### 2.3. Module `recommender/hybrid/contracts.py`
- **Chuc nang hien tai:** Dinh nghia `CandidateSource`, `FusionStrategy`, `HybridRecommendationItem`, `HybridRecommendationResponse`.
- **Danh gia kien truc: XUAT SAC (PASS)**.
  - Module hoan toan doc lap, chi su dung Python Standard Library (`math`, `dataclasses`, `enum`, `typing`).
  - Cac dataclass duoc dong bang (`frozen=True`) dam bao tinh bat bien (immutability) cua ban ghi goi y sau khi sinh.
  - Phuong thuc `to_dict()` duoc dong goi chuan xac, giup serialization JSON khong bi loi Type serialization.
  - Day la mau thiet ke chuan can tiep tuc phat huy cho toan bo he thong contracts cua Phase 5.

### 2.4. Module `recommender/hybrid/config.py`
- **Chuc nang hien tai:** Dinh nghia `HybridConfig` va ham nap bien moi truong `load_hybrid_config()`.
- **Danh gia kien truc: TOT (PASS)**.
  - Co co che kiem tra rang buoc logic o `__post_init__` (vi du: `rrf_k > 0`, `top_k > 0`).
  - Tu dong can bang tong trong so ALS + KG ve 1.0 neu sai lech.
  - Can duoc tich hop vao bo cau hinh tong the `AppConfig` cua ung dung Phase 5.

### 2.5. Module `recommender/als/delivery.py`
- **Chuc nang hien tai:** Cung cap `ALSDeliveryService`, quan ly mo hinh `ALS_R8_REG0.3_ITER10`, su dung nhan ma tran BLAS tren CPU va ma tran CSR de loc phim da xem trong 0.2ms.
- **Danh gia kien truc: RAT TOT (PASS)**.
  - Ranh gioi module sach se, khong he phu thuoc vao KG hay Hybrid.
  - Nhuoc diem duy nhat: chua cung cap API cham diem theo lo cho danh sach phim co san (`score_user_movie_pairs`), buoc hybrid engine phai choc vao `user_factors`.

### 2.6. Module `recommender/kg/recommend.py`
- **Chuc nang hien tai:** Facade goi y dua tren Do thi tri thuc (PathBasedScorer voi 3 metapaths P1, P2, P3).
- **Danh gia kien truc: TOT (PASS)**.
  - Co che Fallback an toan: tu choi fallback sang synthetic fixture neu o moi truong Production de tranh suy giam am tham (silent degradation).
  - Hoan toan doc lap voi ALS va Hybrid.

---

## 3. Ban Thiet ke Kien truc Phan tang MoodGraph Phase 5 (Layered Architecture Blueprint)

De giai quyet dut diem cac nhuoc diem tren va ho tro tron ven ca hai che do Mode A va Mode B, Phase 5 thiet lap kien truc 5 tang khep kin:

```
+---------------------------------------------------------------------------------------+
|                                    TANG 1: API ROUTERS                                |
|  +--------------------+  +--------------------+  +-----------------+  +------------+  |
|  |   DiscoveryRouter  |  |      LabRouter     |  |   SystemRouter  |  | Auth/Admin |  |
|  | (/movies, /users,  |  | (/lab/models,      |  | (/health,       |  | Middleware |  |
|  |  /recs, /explain)  |  |  /compare, metrics)|  |  /cache/clear)  |  | & Guards   |  |
|  +---------+----------+  +---------+----------+  +--------+--------+  +-----+------+  |
+------------|-----------------------|----------------------|-----------------|---------+
             |                       |                      |                 |
             v                       v                      v                 v
+---------------------------------------------------------------------------------------+
|                               TANG 2: APPLICATION SERVICES                            |
|  +------------------+  +-------------------+  +------------------+  +---------------+ |
|  |  CatalogService  |  | UserProfileService|  |ExplainabilityServ|  |  LabService   | |
|  +--------+---------+  +---------+---------+  +--------+---------+  +-------+-------+ |
+-----------|----------------------|---------------------|--------------------|---------+
            |                      |                     |                    |
            +------------+---------+                     |                    |
                         v                               v                    v
+---------------------------------------------------------------------------------------+
|                                TANG 3: MODEL SERVING ENGINES                          |
|  +----------------------------------------------------------------------------------+ |
|  |                          HybridRecommenderService                                | |
|  |            (Candidate Union, RRF, Weighted Fusion, Defense Seen Filter)          | |
|  +---------------------------+-----------------------------------+------------------+ |
|                              |                                   |                    |
|                              v                                   v                    |
|             +--------------------------------+   +--------------------------------+   |
|             |       ALSDeliveryService       |   |      KnowledgeGraphService     |   |
|             |     (BLAS Factors & CSR)       |   |       (Metapaths P1,P2,P3)     |   |
|             +--------------------------------+   +--------------------------------+   |
+---------------------------------------------------------------------------------------+
                               |                                   |
                               v                                   v
+---------------------------------------------------------------------------------------+
|                                  TANG 4: REPOSITORIES                                 |
|  +-----------------------+  +------------------------+  +---------------------------+ |
|  | MovieCatalogRepository|  |  UserHistoryRepository |  | ResearchMetricsRepository | |
|  | (Parquet / Index O(1))|  | (Train CSR & Parquet)  |  | (Phase 4 JSON Benchmarks) | |
|  +-----------------------+  +------------------------+  +---------------------------+ |
+---------------------------------------------------------------------------------------+
                               |                                   |
                               v                                   v
+---------------------------------------------------------------------------------------+
|                           TANG 5: INFRASTRUCTURE & LIFESPAN                           |
|  +-----------------------+  +------------------------+  +---------------------------+ |
|  | FastAPI Lifespan      |  | In-Memory Cache Engine |  | Logging & Latency Tracing | |
|  | (Pre-warming & Cleanup|  | (LRU / TTL Bounded)    |  | (P50, P95, P99 Profiling) | |
|  +-----------------------+  +------------------------+  +---------------------------+ |
+---------------------------------------------------------------------------------------+
```

### Nguyen ly phan tang nghiem ngat (Strict Architectural Rules)
1. **Chieu phu thuoc mot chieu (Downward Dependency Rule):** Tang tren goi xuong tang duoi truc tiep. Tuyet doi khong co chieu nguoc lai (tang duoi khong biet den su ton tai cua tang tren).
2. **Dong goi Schema & Contracts:** API Routers chi phu trach phan tich HTTP params, validate Pydantic request/response, va goi Application Services.
3. **Phan tach nguon du lieu goc (Data Isolation):**
   - `MovieCatalogRepository`: Nguon chan ly metadata phim tu `data/processed/core/movies/` kem theo `links`, `genome_tags`, `tags`.
   - `UserHistoryRepository`: Chi doc tu `data/processed/splits/train` hoac CSR Train Index. Tuyet doi khong doc tu `validation` hoac `test`.
   - `ResearchMetricsRepository`: Doc cac file ket qua danh gia thuc nghiem da dong bang cua Phase 4 (`docs/phase4/expanded_validation_results.json`, `docs/phase4/phase4_gate_report.json`).

---

## 4. Dac ta Hop dong Public API Chi tiet (API Contracts Specification)

### 4.1. MODE A: Movie Discovery (Dung cho Nguoi dung cuoi & Kham pha phim)

#### 1. Endpoint Danh muc Phim: `GET /api/movies`
- **Muc tieu:** Tim kiem, loc the loai, loc nam phat hanh, ho tro phan trang an toan.
- **Tham so Query:**
  - `query` (Optional[str]): Tu khoa tim kiem theo ten phim (khong phan biet hoa thuong).
  - `genre` (Optional[str]): Loc theo the loai (vi du: `Action`, `Sci-Fi`, `Comedy`).
  - `year_min` (Optional[int]): Nam phat hanh tu (vi du: `1990`).
  - `year_max` (Optional[int]): Nam phat hanh den (vi du: `2020`).
  - `page` (int, default=1, ge=1): Trang hien tai.
  - `page_size` (int, default=20, ge=1, le=100): So luong phim tren mot trang.
  - `sort_by` (str, default="popularity", enum=["popularity", "title", "year", "rating"]): Tieu chi sap xep.
- **Pydantic Response Schema (`MovieCatalogResponse`):**
  ```python
  class MovieItemSchema(BaseModel):
      movieId: int
      title: str
      clean_title: str
      release_year: Optional[int] = None
      genres: List[str]
      imdb_id: Optional[str] = None
      tmdb_id: Optional[str] = None
      rating_count: int = 0
      rating_mean: float = 0.0
      top_tags: List[str] = Field(default_factory=list)

  class MovieCatalogResponse(BaseModel):
      total: int
      page: int
      page_size: int
      total_pages: int
      items: List[MovieItemSchema]
  ```

#### 2. Endpoint Chi tiet Phim: `GET /api/movies/{movie_id}`
- **Tham so Path:** `movie_id` (int, ge=1).
- **Pydantic Response Schema (`MovieDetailResponse`):**
  ```python
  class MovieDetailResponse(BaseModel):
      movieId: int
      title: str
      clean_title: str
      release_year: Optional[int]
      genres: List[str]
      links: Dict[str, Optional[str]] # imdb, tmdb
      stats: Dict[str, Any]           # count, mean_rating, variance
      genome_tags: List[Dict[str, Any]] # tag, relevance score
      similar_movies: List[Dict[str, Any]] # fallback similar movies
  ```

#### 3. Endpoint Danh sach Nguoi dung: `GET /api/users`
- **Muc tieu:** Cung cap danh sach cac test users mau cho giao dien lua chon kham pha (Users co du lieu day du trong tap Train va KG Pilot).
- **Tham so Query:**
  - `user_type` (str, default="all", enum=["all", "pilot_kg", "cold_start", "active"]): Phan loai user.
  - `page` (int, default=1, ge=1), `page_size` (int, default=20, ge=1, le=50).
- **Response Schema (`UserListResponse`):**
  ```python
  class UserSummaryItem(BaseModel):
      userId: int
      train_ratings_count: int
      favorite_genres: List[str]
      is_in_kg_pilot: bool
      is_in_als_train: bool

  class UserListResponse(BaseModel):
      total: int
      page: int
      page_size: int
      items: List[UserSummaryItem]
  ```

#### 4. Endpoint Ho so Nguoi dung: `GET /api/users/{user_id}/profile`
- **Tham so Path:** `user_id` (int, ge=1).
- **Response Schema (`UserProfileResponse`):**
  ```python
  class UserProfileResponse(BaseModel):
      userId: int
      ratings_count: int
      mean_rating: float
      genre_distribution: Dict[str, int]
      top_favorite_genres: List[str]
      activity_level: str # "highly_active", "moderate", "casual", "cold"
  ```

#### 5. Endpoint Lich su Danh gia: `GET /api/users/{user_id}/history`
- **Cam ket:** Chi tra ve danh sach danh gia tu tap Train (`data/processed/splits/train`), tuyet doi khong de ro ri tap Validation hoac Test.
- **Tham so Query:** `page` (int, default=1), `page_size` (int, default=20), `min_rating` (Optional[float]).
- **Response Schema (`UserHistoryResponse`):**
  ```python
  class UserRatingItem(BaseModel):
      movieId: int
      title: str
      genres: List[str]
      rating: float
      timestamp: int

  class UserHistoryResponse(BaseModel):
      userId: int
      total_rated: int
      page: int
      page_size: int
      items: List[UserRatingItem]
  ```

#### 6. Endpoint Goi y Phim Thoi gian thuc: `GET /api/recommendations/{user_id}`
- **Cam ket:** Bao toan 100% Signature va Response Schema cua Phase 4 (`RecommendationResponseSchema`).

#### 7. Endpoint Giai thich Chuyen sau: `GET /api/explanations/{user_id}/{movie_id}`
- **Muc tieu:** Cung cap day du ly le logic tai sao mot bo phim cu the duoc de xuat cho nguoi dung.
- **Tham so Path:** `user_id` (int), `movie_id` (int).
- **Response Schema (`ExplanationDetailResponse`):**
  ```python
  class MetapathExplanation(BaseModel):
      metapath: str          # "P1_GENRE", "P2_GENOME", "P3_COLLABORATIVE"
      score_contribution: float
      connecting_entities: List[Dict[str, Any]]
      verbal_explanation: str

  class LatentFactorExplanation(BaseModel):
      dot_product_score: float
      model_version: str
      percentile_alignment: float
      verbal_explanation: str

  class ExplanationDetailResponse(BaseModel):
      userId: int
      movieId: int
      movie_title: str
      overall_recommendation_source: str # "BOTH", "ALS", "KG"
      graph_explanations: List[MetapathExplanation]
      latent_factor_explanation: Optional[LatentFactorExplanation] = None
      summary_text: str
  ```

---

### 4.2. MODE B: Recommendation Lab (Dung cho Nghien cuu sinh & Chuyen gia Dinh luong)

#### 1. Endpoint Danh muc Mo hinh Dang ky: `GET /api/lab/models`
- **Response Schema (`RegisteredModelsResponse`):**
  ```python
  class ModelRegistryEntry(BaseModel):
      model_id: str
      model_family: str      # "ALS", "KNOWLEDGE_GRAPH", "HYBRID"
      version: str
      display_name: str
      status: str            # "CHAMPION", "CANDIDATE", "BASELINE"
      hyperparameters: Dict[str, Any]
      description: str
      capabilities: List[str]

  class RegisteredModelsResponse(BaseModel):
      models: List[ModelRegistryEntry]
      fusion_strategies: List[str]
  ```

#### 2. Endpoint So sanh Song song Da mo hinh: `POST /api/lab/compare`
- **Request Body (`LabCompareRequest`):**
  ```python
  class LabCompareRequest(BaseModel):
      user_id: int = Field(..., ge=1)
      models: List[str] = Field(default=["als", "kg", "hybrid_rrf", "hybrid_weighted"])
      top_n: int = Field(10, ge=1, le=50)
      filter_seen: bool = True
      rrf_k: int = 60
      weight_als: float = 0.5
      weight_kg: float = 0.5
  ```
- **Response Schema (`LabCompareResponse`):**
  ```python
  class ModelRunResult(BaseModel):
      model_id: str
      execution_time_ms: float
      recommendations: List[Dict[str, Any]] # mid, title, score, rank

  class OverlapMetric(BaseModel):
      model_a: str
      model_b: str
      jaccard_similarity: float
      rank_correlation_kendall: Optional[float]
      rank_correlation_spearman: Optional[float]
      common_movies_count: int

  class LabCompareResponse(BaseModel):
      user_id: int
      top_n: int
      results: Dict[str, ModelRunResult]
      pairwise_overlaps: List[OverlapMetric]
      summary: Dict[str, Any]
  ```

#### 3. Endpoint Metric Nghien cuu Phase 4: `GET /api/lab/metrics`
- **Muc tieu:** Cung cap cac bang ket qua danh gia thuc nghiem chuan hoa (Offline Evaluation) duoc doc truc tiep tu cac artifact da duoc xac thuc o Phase 4.
- **Tham so Query:**
  - `split` (str, default="validation", enum=["validation", "test"]): Tap danh gia.
  - `metric_group` (str, default="all", enum=["all", "ranking", "beyond_accuracy", "latency"]).
- **Response Schema (`LabMetricsResponse`):**
  ```python
  class MetricDetail(BaseModel):
      metric_name: str       # "NDCG@10", "MAP@10", "Precision@10", "Recall@10", "Catalog_Coverage", "Novelty"
      display_name: str
      als_champion_score: float
      kg_only_score: float
      hybrid_rrf_score: float
      hybrid_weighted_score: float
      best_model: str

  class LatencyBenchmark(BaseModel):
      strategy: str
      p50_ms: float
      p95_ms: float
      p99_ms: float
      cache_hit_p95_ms: float

  class LabMetricsResponse(BaseModel):
      provenance: str
      evaluation_users_count: int
      metrics: List[MetricDetail]
      latency_benchmarks: List[LatencyBenchmark]
  ```

#### 4. Endpoint Sieu du lieu He thong & Dataset: `GET /api/lab/metadata`
- **Response Schema (`SystemMetadataResponse`):**
  ```python
  class SystemMetadataResponse(BaseModel):
      dataset_name: str      # "MovieLens 25M (ml-25m)"
      total_ratings: int     # 25000095
      split_provenance: Dict[str, int] # train: 24675013, validation: 162541, test: 162541
      catalog_size: int      # 62423 movies
      als_factor_dim: int    # 8
      kg_node_counts: Dict[str, int] # Movie, User, Genre, Tag
      kg_edge_counts: Dict[str, int] # RATED, IN_GENRE, HAS_GENOME_TAG
      system_environment: Dict[str, str]
  ```

---

## 5. Phan tich Rủi ro Phu thuoc Vong & Chien luoc Triet tieu (Circularity Mitigation)

### 5.1. Kiem dinh Do thi Phu thuoc Hien tai (Current Dependency Graph)
Do thi phu thuoc giua cac module dang tuan thu quan he phan cap mot chieu:
- `recommender.hybrid.api` -> `recommender.hybrid.engine` -> `recommender.hybrid.contracts`, `recommender.hybrid.config`, `recommender.hybrid.fusion`, `recommender.hybrid.cache`
- `recommender.hybrid.engine` -> (lazy call) -> `recommender.als.delivery`, `recommender.kg.recommend`
- `recommender.als.delivery` -> `recommender.als.candidates`, `recommender.als.evaluator` (Doc lap 100% voi KG va Hybrid)
- `recommender.kg.recommend` -> `recommender.kg.config`, `recommender.kg.scorer`, `recommender.kg.import_graph` (Doc lap 100% voi ALS va Hybrid)

Ket luan kiem dinh: **Hien tai KHONG co phu thuoc vong (Zero Circular Dependency - PASS)**.

### 5.2. Nguy co tiem an khi mo rong Phase 5 & Bien phap Kiem soat
Khi bo sung cac Routers, Services va Repositories moi trong Phase 5, nguy co chu trinh xuat hien tai 2 diem nut:
1. *Routers import Services -> Services import Routers/Schemas:*
   - **Giai phap:** Triet de ap dung thu muc `schemas/` hoac `contracts.py` lam goc. Routers va Services cung import tu `schemas/`. Services khong bao gio import Routers.
2. *CatalogService va HybridRecommenderService goi nhau:*
   - HybridEngine can ten phim tu Catalog, trong khi CatalogService co the muon nhung goi y hybrid.
   - **Giai phap:** `CatalogRepository` la lop truy xuat du lieu thuan tuy (doc Parquet/dict). `HybridRecommenderService` chi phu thuoc vao `MovieCatalogRepository`. `CatalogService` dong vai tro Application Service tang cao dieu phoi ca Repository va Engine khi can.
3. *Su dung Dependency Injection cua FastAPI (`Depends`):*
   - Thay vi khoi tao singleton truc tiep bang global variable trong tung file router, toan bo instance service duoc khoi tao trong Lifespan va duoc inject vao endpoint thong qua `fastapi.Depends()`.

---

## 6. Kien truc Quan ly Vong doi & Tai nguyen (FastAPI Lifespan & Resource Management)

### 6.1. Han che cua Co che Lazy Initialization hien tai
- Hien tai, khi uvicorn khoi dong, cac mo hinh ALS va Do thi KG khong duoc nap.
- Khi request dau tien den `GET /api/recommendations/1`:
  - `ALSDeliveryService` doc Parquet factors va nén ma tran CSR (ton ~450ms).
  - `KGGraph` khoi tao ket noi Neo4j hoac nạp In-Memory Graph (ton ~150ms).
  - Tong do tre request dau tien len den **~650ms** (vi pham chuan P95 < 200ms).

### 6.2. Thiet ke FastAPI Lifespan Context Manager trong Phase 5
Phase 5 thay the hoan toan khoi tao lanh bang `@asynccontextmanager lifespan`:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. STARTUP PHASE (Pre-warming Resource Singletons)
    logger.info("Initializing MoodGraph Platform resources...")
    
    # Nap truoc Catalog Repository & Build Index
    catalog_repo = MovieCatalogRepository()
    catalog_repo.load_and_index()
    
    # Nap truoc Train History Index
    history_repo = UserHistoryRepository()
    history_repo.warmup_index()
    
    # Khoi dong ALS Model Serving Singleton
    als_service = get_delivery_service()
    _ = als_service.recommend(user_id=1, top_n=1) # Warmup BLAS matrix mul
    
    # Khoi dong KG Engine Singleton
    kg_graph = get_default_graph()
    
    # Khoi dong Hybrid Serving Service voi bo nho dem
    hybrid_service = HybridRecommenderService(
        als_service=als_service,
        kg_graph=kg_graph,
        catalog_provider=catalog_repo
    )
    
    # Dang ky vao app.state phuc vu Dependency Injection
    app.state.catalog_repo = catalog_repo
    app.state.history_repo = history_repo
    app.state.hybrid_service = hybrid_service
    app.state.models_ready = True
    
    logger.info("MoodGraph Platform pre-warming complete. Ready for warm serving.")
    
    yield
    
    # 2. SHUTDOWN PHASE (Graceful Resource Teardown)
    logger.info("Tearing down MoodGraph Platform resources...")
    if hasattr(kg_graph, "close"):
        kg_graph.close()
    if hybrid_service.cache:
        hybrid_service.cache.clear()
    logger.info("Teardown complete.")
```

### 6.3. Loi ich Dat duoc
- **Triet tieu Cold-Start Spike:** Request dau tien tu nguoi dung dat toc do warm ngay lap tuc (Latency < 20ms thay vi 650ms).
- **Thread Safety:** Tranh race conditions khi nhieu requests dong thoi toi server luc mo hinh dang duoc nap do.
- **Fail-Fast Policy:** Neu file artifact bi thieu hoac loi corruption, server se dung ngay lap tuc khi boot (Startup Exit Code != 0), khong bao gio chay o trang thai "nua song nua chet".

---

## 7. Bao dam Tinh Tuong thich Nguoc voi Phase 4 (Backward Compatibility Guarantees)

Moi thay doi trong Phase 5 cam ket bao ve 100% tinh tuong thich nguoc voi cac he thong client va bai kiem thu da viet o Phase 4:

1. **Endpoint `GET /api/recommendations/{user_id}`:**
   - Cac tham so query `top_n`, `model`, `fusion`, `w_als`, `w_kg`, `rrf_k`, `filter_seen`, `allow_unfiltered`, `cross_score_als`, `use_cache`, `x_admin_token`, `admin_token` giu nguyen 100% ten va kieu du lieu.
   - Response tra ve giu nguyen JSON Root Structure:
     ```json
     {
       "userId": 1,
       "recommendations": [ ... ],
       "metadata": { ... }
     }
     ```
   - Cac truong trong `recommendations`: `userId`, `movieId`, `title`, `hybrid_score`, `rank`, `source`, `fusion_method`, `als_raw_score`, `als_normalized_score`, `als_rank`, `kg_raw_score`, `kg_normalized_score`, `kg_rank`, `evidence`.
2. **Endpoint `GET /api/health`:**
   - Tra ve status="ok", version, cache_stats va models_ready.
3. **Endpoint `GET /api/model_info`:**
   - Giu nguyen cac thong so metadata ALS Champion va KG Paths.
4. **Endpoint `POST /api/cache/clear`:**
   - Giu nguyen phuong thuc xac thuc qua Admin Token va ket qua tra ve.

---

## 8. Lo trinh Thuc thi Kien truc Phase 5 (Actionable Implementation Roadmap)

De trien khai thanh cong kien truc tren ma khong gay anh huong den bo test suite 246 tests hien tai:

### Buoc 1: Xay dung Tang Repositories & Schemas Moi
- Tao `recommender/platform/schemas/`: Dinh nghia cac Pydantic models cho Mode A (`movie_schemas.py`, `user_schemas.py`, `explanation_schemas.py`) va Mode B (`lab_schemas.py`).
- Tao `recommender/platform/repositories/`:
  - `MovieCatalogRepository`: Doc Parquet `data/processed/core/movies/` va lap chi muc tim kiem nhanh tren RAM.
  - `UserHistoryRepository`: Doc tap Train Parquet de trich xuat lich su danh gia cua nguoi dung.
  - `ResearchMetricsRepository`: Doc cac file JSON danh gia Phase 4 de phuc vu Lab.

### Buoc 2: Hoan thien Tang Application Services
- Tao `recommender/platform/services/`:
  - `CatalogService`: Xu ly logic tim kiem, loc the loai, phan trang.
  - `UserProfileService`: Tong hop so thich the loai tu lich su danh gia tap Train.
  - `ExplainabilityService`: Dong goi ly le cho tung cap (user_id, movie_id).
  - `LabService`: So sanh cac mo hinh song song, tinh chi so Jaccard va tuong quan rank.

### Buoc 3: Dong goi Routers & FastAPI Lifespan
- Tao `recommender/platform/routers/`:
  - `discovery_router.py`: Gan endpoints Mode A.
  - `lab_router.py`: Gan endpoints Mode B.
  - `system_router.py`: Chuyen cac endpoints tu `api.py` cu sang.
- Tao `recommender/platform/app.py`:
  - Khoi tao FastAPI app voi lifespan pre-warming.
  - Gan cac sub-routers voi prefix tuong ung.
- Trong `recommender/hybrid/api.py`: Chuyen thanh facade goi toi `recommender/platform/app.py` hoac tich hop router de dam bao cac test cu chay `from recommender.hybrid.api import app` van pass 100%.

### Buoc 4: Chay Bo Kiem thu Hoi quy Toan dien (Full Regression Verification)
- Chay lai `python -m pytest tests/` -> Xac nhan 246/246 tests cu pass.
- Bo sung cac bo test moi cho Routers Mode A va Mode B trong `tests/platform/`.

---

## 9. Ket luan Kien truc

He thong MoodGraph sau Phase 4 so huu nen tang thuat toan va hieu nang phan cung rat vung chac (ALS BLAS sub-millisecond, KG Metapaths da dang, Hybrid RRF tieu chuan). Ban kiem dinh kien truc nay da xac lap ranh gioi phan tang ro rang, khac phuc triet de cac diem ro ri truu tuong, loai bo do tre khoi dong lanh thong qua Lifespan Pre-warming, va san sang de doi ngu ky su tien hanh hien thuc hoa Phase 5 theo dung tieu chuan ky thuat cao nhat.
