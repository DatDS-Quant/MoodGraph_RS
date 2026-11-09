# MoodGraph Phase 5: Bao Cao Kiem Dinh An Ninh Doc Lap & Doi Khang (Independent Adversarial Security & Vulnerability Audit)

**Chuyen vien phu trach:** Principal Security Auditor & Adversarial Red Team Engineer  
**Ngay thuc hien:** 2026-11-07  
**Doi tuong kiem dinh:** MoodGraph Platform Phase 5 (Tien trinh Backend Platform, Repositories, Application Services va REST API)  
**Moi truong kiem thu:** Python 3.12.3 / FastAPI 0.115+ / PyArrow 19.0 / SQLite 3 (WAL Mode) / Windows x64  
**Pham vi ra soat:** Toan bo source code trong `recommender/api/`, `recommender/storage/`, `recommender/services/`, va cac phan vung du lieu `data/processed/splits/`  

---

## 1. Tong Quan & Bang Danh Gia Cac Cong An Ninh (Security Gates Dashboard)

Kiem dinh an ninh nay duoc thuc hien doc lap theo phuong phap doi khang (Adversarial White-Box & Dynamic Probing), doi chieu voi tieu chuan quoc te **OWASP API Security Top 10 (2023 Edition)**, nguyen tac bao ve toan ven du lieu nghien cuu (**Zero Data Leakage**), va cac nguyen tac phong thu chieu sau (Defense-in-Depth).

### Bang Danh Gia Cac Cong An Ninh (Security Gates Matrix)

| Ma Cong | Tieu Chi Kiem Dinh | Ket Qua | Muc Do Rui Ro | Danh Gia Chuyen Gia |
| :--- | :--- | :---: | :---: | :--- |
| **SEC-GATE-01** | **Cach Ly Du Lieu Nghien Cuu (Zero-Leakage)** | **PASS** | LOW (None) | 100% API va Repositories cach ly tuyet doi `splits/validation` va `splits/test`. Lich su danh gia va bo loc train-seen chi doc tu `splits/train` va `train_seen_csr.npz`. |
| **SEC-GATE-02** | **Khang Tiem Nhap SQL (SQLi Resilience)** | **PASS** | LOW (None) | 100% cau lenh SQL trong `sqlite_state_repo.py` su dung Parameterized Queries (bien `?`). Fuzzing voi chuoi injection doc hai bi vo hieu hoa hoan toan. |
| **SEC-GATE-03** | **Kiem Soat Ranh Gioi Tham So (Input Boundaries)** | **PARTIAL** | MEDIUM | Cac tham so danh gia (`rating` [0.5, 5.0]), phan trang (`page >= 1`, `page_size <= 100`), va bo loc nam truyen qua query da duoc kiem soat chat che bang Pydantic v2. Tuy nhien, `min_year` va `max_year` trong `PreferencesRequest` chua co rang buoc khoang va thieu kiem tra thu tu logic (`min_year <= max_year`). |
| **SEC-GATE-04** | **Cau Hinh CORS & Nguon Goc Cheo** | **FAIL** | HIGH | `app.py` cau hinh dong thoi `allow_origins=["*"]` va `allow_credentials=True`. Starlette CORS Middleware tu dong phan chieu bat ky header `Origin` nao cua ke tan cong, tao lo hong CORS Misconfiguration cho phep danh cap du lieu cheo nguon. |
| **SEC-GATE-05** | **Xac Thuc & Phan Quyen Doi Tuong (BOLA/IDOR)** | **PARTIAL** | MEDIUM-HIGH | He thong hien thuc che do Demo Platform mo, chua tich hop JWT / Session Token. Cac endpoint `/api/interactions/*` cho phep truyen bat ky `user_id` nao ma khong kiem tra quyen so huu, tao rui ro BOLA neu dua len internet cong cong. |
| **SEC-GATE-06** | **Chong Can Kiet Tai Nguyen (DoS / Rate Limiting)** | **FAIL** | MEDIUM-HIGH | Endpoint quan tri `POST /api/system/cache/clear` khong co xac thuc. Endpoint `POST /api/lab/compare` khong gioi han so luong mo hinh yeu cau trong mang `models`. Thieu middleware Rate Limiting ngan chan brute-force / DoS. |
| **SEC-GATE-07** | **Ro Ri Thong Tin & Quan Ly Ngoai Le** | **PARTIAL** | LOW-MEDIUM | Endpoint `/api/recommendations/{user_id}` tra ve truc tiep chuoi loi `str(e)` khi gap exception he thong thay vi thong diep an toan, co the tiet lo chi tiet file nguon hoac thu vien noi bo. |
| **SEC-GATE-08** | **An Toan Tep SQLite & Concurrency (WAL Mode)** | **PASS** | LOW | SQLite duoc cau hinh chuan WAL mode (`PRAGMA journal_mode = WAL; foreign_keys = ON;`). Ho tro da tien trinh doc/ghi song song an toan, khong bi deadlock. |

---

## 2. Kiem Dinh Chi Tiet Theo Khung OWASP API Security Top 10 (2023)

He thong MoodGraph Phase 5 duoc doi chieu toan dien voi 10 rui ro an ninh API hang dau theo OWASP 2023:

```
+-----------------------------------------------------------------------------------+
|               OWASP API SECURITY TOP 10 (2023) - AUDIT SCORECARD                  |
+----+----------------------------------------------+----------+--------------------+
| ID | Danh Muc Rui Ro OWASP                        | Trang    | Muc Do Nghiem      |
|    |                                              | Thai     | Trong (Severity)   |
+----+----------------------------------------------+----------+--------------------+
| 01 | Broken Object Level Authorization (BOLA)     | VULNERABLE| HIGH               |
| 02 | Broken Authentication                        | OPEN     | MEDIUM (Demo Mode) |
| 03 | Broken Object Property Level Authorization   | SECURE   | PASS               |
| 04 | Unrestricted Resource Consumption            | VULNERABLE| HIGH               |
| 05 | Broken Function Level Authorization          | VULNERABLE| MEDIUM             |
| 06 | Unrestricted Access to Sensitive Flows       | SECURE   | PASS               |
| 07 | Server-Side Request Forgery (SSRF)           | SECURE   | PASS               |
| 08 | Security Misconfiguration (CORS, Exceptions) | VULNERABLE| HIGH               |
| 09 | Improper Inventory Management                | SECURE   | PASS               |
| 10 | Unsafe Consumption of APIs                   | SECURE   | PASS               |
+----+----------------------------------------------+----------+--------------------+
```

### API1:2023 - Broken Object Level Authorization (BOLA / IDOR)
- **Trang thai:** **CANH BAO (HIGH SEVERITY neu cong khai Internet)**
- **Phan tich ky thuat:**
  Trong module `recommender/api/interaction_router.py`:
  - `POST /api/interactions/watchlist`: Nhan body JSON co chuoi `user_id`. Bat ky client nao cung co the truyen `user_id="cinephile_dat"` hoac ID cua bat ky nguoi dung nao khac de them phim vao watchlist cua ho.
  - `DELETE /api/interactions/watchlist`: Query parameter `user_id: str`. Khong co co che so khop giua nguoi goi yeu cau va chu so huu ban ghi.
  - `GET /api/interactions/watchlist/{user_id}`: Cho phep xem danh sach phim da luu cua bat ky ai.
  - `POST /api/interactions/ratings`: Cho phep ghi de hoac chen danh gia moi cho bat ky `user_id` nao.
  - `POST /api/interactions/preferences`: Cho phep ghi de so thich the loai/nam cua bat ky `user_id` nao.
- **Boi canh danh gia:** Trong giai doan Phase 5 (Local Demo & Research Platform), day la thiet ke chu dich phuc vu trai nghiem nhanh khong can man hinh Login. Tuy nhien, ve mat an ninh phan mem chuan, day la lo hong BOLA co the bi khai thac de pha hoai du lieu nguoi dung demo khac.

### API2:2023 - Broken Authentication
- **Trang thai:** **ACCEPTABLE CHO LOCAL DEMO / INCOMPLETE CHO PRODUCTION (MEDIUM)**
- **Phan tich ky thuat:**
  API hien tai hoan toan khong co lop bao ve xac thuc (Zero Authentication Layer). Khong ton tai co che phat hanh token (JWT, API Keys, Session Cookies) hoac middleware kiem tra Header `Authorization`.
- **Hanh dong:** Can giu nguyen su tien loi cho che do Local Discovery, dong thoi bo sung che do Optional API Key hoac Bearer Token Header khi bien `ENVIRONMENT=production`.

### API3:2023 - Broken Object Property Level Authorization (Mass Assignment & Excessive Data Exposure)
- **Trang thai:** **AN TOAN (PASS)**
- **Phan tich ky thuat:**
  - 100% model du lieu dau ra deu duoc dong goi boi cac Pydantic Response Schema cu the: `MovieSearchResponse`, `MovieDetailResponse`, `UserProfileResponse`, `UserHistoryResponse`, `LabCompareResponse`, `HealthResponse`.
  - Khong co hien tuong tra ve truc tiep con tro database row hoac du lieu nhay cam (nhu mat khau, hashed tokens, duong dan he thong noi bo).
  - Khong cho phep Mass Assignment tren cac bang SQLite vi moi phuong thuc trong `SQLiteStateRepository` chi trich xuat va cap nhat dung cac truong duoc phep (`genres_json`, `moods_json`, `rating`, `feedback_text`).

### API4:2023 - Unrestricted Resource Consumption (DoS / Can Kiet Tai Nguyen)
- **Trang thai:** **CO LO HONG (HIGH SEVERITY)**
- **Phan tich ky thuat & Bang chung doi khang:**
  1. *Khai thac mang mo hinh khong gioi han trong Lab Compare:*
     Tai `recommender/api/schemas.py`, schema `LabCompareRequest` dinh nghia:
     ```python
     models: List[str] = Field(default=["als", "kg", "hybrid_rrf", "hybrid_weighted"])
     ```
     Truong `models` khong co rang buoc do dai (`max_length` hoac `max_items`). Ke tan cong co the gui mang gom 100 phan tu `models=["kg"] * 100`. Dieu nay khien `LabService.compare_models` phai thuc thi thuat toan duyet do thi da chieu (Graph Multi-Hop Traversal) 100 lan lien tiep trong 1 request duy nhat, gay chiem dung 100% CPU va treo Event Loop.
  2. *Tan cong bom chuoi (String Length Bomb) tai feedback_text:*
     Tai `RatingSubmitRequest`, truong `feedback_text: Optional[str] = None` khong co gioi han ky tu (`max_length`). Khi thu nghiem gui chuoi 100,000 ky tu (100KB), he thong van tiep nhan voi HTTP 200 va ghi truc tiep vao file `data/app_state.db`. Neu gui lap lai voi chuoi 10MB, he thong se nhanh chong lam day dung luong dia cung (Disk Space Exhaustion).
  3. *Tan cong can kiet bo nho qua mang the loai:*
     Tai `PreferencesRequest`, `genres: List[str]` khong bi gioi han so luong phan tu.

### API5:2023 - Broken Function Level Authorization
- **Trang thai:** **CO LO HONG (MEDIUM SEVERITY)**
- **Phan tich ky thuat:**
  Endpoint quan tri he thong `POST /api/system/cache/clear` nam cung cap do truy cap cong khai nhu cac endpoint xem phim thong thuong. Bat ky ai tren mang cung co the goi lien tuc de xoa sach bo nho dem LRU (`HybridRecommendationCache`), ep he thong phai tinh toan lai tu dau cho moi request (Cache Thrashing Attack).

### API6:2023 - Unrestricted Access to Sensitive Business Flows
- **Trang thai:** **AN TOAN (PASS)**
- **Phan tich ky thuat:**
  Cac luong nghiep vu danh gia phim demo co co che vo hieu hoa cache cho chinh user do (`_invalidate_user_cache(user_id)`). Viec nay khong gay anh huong den cache toan cuc cua cac nguoi dung khac.

### API7:2023 - Server-Side Request Forgery (SSRF)
- **Trang thai:** **HOAN TOAN AN TOAN (PASS)**
- **Phan tich ky thuat:**
  He thong Backend khong co bat ky endpoint nao tiep nhan URL tu phia nguoi dung de thuc hien HTTP request ra ben ngoai. Cac duong dan IMDb va TMDb (`https://www.imdb.com/title/tt...`, `https://www.themoviedb.org/movie/...`) deu duoc sinh ra tu dong bang string template dua tren ma so hop le tu file Parquet da duoc tien xu ly san.

### API8:2023 - Security Misconfiguration (Cau Hinh Sai CORS & Lo Thong Tin Exception)
- **Trang thai:** **CO LO HONG NGHIEP TRONG (HIGH SEVERITY)**
- **Phan tich ky thuat & Bang chung thuc nghiem:**
  1. *Lo hong CORS Misconfiguration:*
     File `recommender/api/app.py` cau hinh:
     ```python
     application.add_middleware(
         CORSMiddleware,
         allow_origins=["*"],
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
     ```
     Kiem tra bang thu nghiem thuc te voi `TestClient`:
     - Khi gui Header `Origin: http://malicious-attacker.com` toi endpoint, Starlette Middleware tra ve:
       `access-control-allow-origin: http://malicious-attacker.com`
       `access-control-allow-credentials: true`
     - **Co che lo hong:** Khi `allow_origins=["*"]` di kem voi `allow_credentials=True`, Middleware se tu dong lay bat ky gia tri nao trong header `Origin` va gan vao `Access-Control-Allow-Origin`. Dieu nay cho phep mot website doc hai duoc nguoi dung truy cap co the gui yeu cau xuyen mien (Cross-Origin XHR/Fetch) de doc va sua doi Watchlist, Ratings va Preferences cua nguoi dung ma khong bi trinh duyet chan lai.
  2. *Ro ri Stack Trace / Chi tiet Exception:*
     Tai `recommender/api/discovery_router.py` (dong 174):
     ```python
     except Exception as e:
         logger.error(f"Error serving recommendations for user {user_id}: {e}")
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail=f"Recommendation pipeline error: {str(e)}",
         )
     ```
     Viec tra ve truc tiep `str(e)` trong ma loi HTTP 500 tiet lo cau truc thu muc noi bo, ten bien, ten module hoac thong bao loi cua thu vien numpy/scipy cho ke tan cong khi xay ra loi ngoai du tinh.

### API9:2023 - Improper Inventory Management
- **Trang thai:** **AN TOAN (PASS)**
- **Phan tich ky thuat:**
  Tat ca cac API deu duoc dinh tuyen co he thong qua cac Router co prefix ro rang (`/api/movies`, `/api/users`, `/api/recommendations`, `/api/lab`, `/api/interactions`, `/health`). Khong co API ngam (shadow endpoints) hoac API bi bo quen (zombie endpoints).

### API10:2023 - Unsafe Consumption of APIs
- **Trang thai:** **HOAN TOAN AN TOAN (PASS)**
- **Phan tich ky thuat:**
  MoodGraph Phase 5 hoan toan doc lap, khong phu thuoc hoac tiep nhan du lieu synchronous tu bat ky ben thu ba nao trong runtime. Toan bo du lieu nạp vao deu xuat phat tu he thong file noi bo da kiem chung.

---

## 3. Kiem Dinh SQLite Repository: Parameterized Queries, SQL Injection & Quyen Tep

Module kiem dinh: `recommender/storage/sqlite_state_repo.py`.

### 3.1. Danh Gia Parameterized Queries & Kha Nang Khang SQL Injection
Do kiem dinh tien hanh ra soat 100% cac cau lenh truy van SQL trong lop `SQLiteStateRepository`:

```
+---------------------------+----------------------------------------------+---------------+-------------+
| Phuong Thuc               | Thao Tac SQL                                 | Su Dung Bien  | Khang SQLi  |
| (Method)                  | (Statement Type)                             | Placeholder ? | (Resilience)|
+---------------------------+----------------------------------------------+---------------+-------------+
| ensure_user               | INSERT OR IGNORE INTO demo_users             | DUNG (?)      | 100% PASS   |
| save_movie                | INSERT INTO saved_movies ... ON CONFLICT     | DUNG (?)      | 100% PASS   |
| remove_saved_movie        | DELETE FROM saved_movies WHERE ...           | DUNG (?)      | 100% PASS   |
| list_saved_movies         | SELECT ... FROM saved_movies WHERE ...       | DUNG (?)      | 100% PASS   |
| record_rating             | INSERT INTO user_ratings ... ON CONFLICT     | DUNG (?)      | 100% PASS   |
| get_user_demo_ratings     | SELECT ... FROM user_ratings WHERE ...       | DUNG (?)      | 100% PASS   |
| save_preferences          | INSERT INTO user_preferences ... ON CONFLICT | DUNG (?)      | 100% PASS   |
| get_preferences           | SELECT ... FROM user_preferences WHERE ...   | DUNG (?)      | 100% PASS   |
| log_experiment_session    | INSERT INTO experiment_sessions              | DUNG (?)      | 100% PASS   |
+---------------------------+----------------------------------------------+---------------+-------------+
```

**Ket luan ve SQL Injection:**
- **Tuyet doi khong su dung phep noi chuoi (Zero String Concatenation):** Khong co bat ky doan code nao su dung `f"SELECT ... {user_id}"` hoac `"%s"` hay `.format()`.
- **Ket qua kiem thu doi khang (Fuzzing Injection):**
  Thuc hien injection voi payload kinh dien: `user_id = "'; DROP TABLE demo_users; --"`.
  - Ket qua: Chuoi doc hai duoc xu ly thuan tuy nhu mot gia tri literal `TEXT`.
  - Bang `demo_users` va toan bo du lieu van nguyen ven 100%.
  - Truy van sau do tra ve dung ban ghi voi ID do ma khong lam vo cau truc co so du lieu.

### 3.2. Toan Ven Schema & Rang Buoc Database (Database Integrity & Constraints)
Cac bang duoc thiet ke voi cac rang buoc co so du lieu chat che:
1. `CHECK(list_type IN ('watchlist', 'favorites', 'hidden'))`: Ngan chan gia tri list_type bat hop phap o muc engine SQLite.
2. `CHECK(rating >= 0.5 AND rating <= 5.0)`: Bao dam diem rating luon nam trong khoang hop le cua chuan MovieLens.
3. `FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE`: Rang buoc toan ven tham chieu duoc kich hoat chu dong qua `conn.execute("PRAGMA foreign_keys = ON;")`.
4. `PRAGMA journal_mode = WAL; PRAGMA synchronous = NORMAL;`: Kich hoat che do Write-Ahead Logging giup ho tro nhieu tien trinh doc dong thoi ma khong bi block boi tien trinh ghi, ngan ngua nguy co database lock / timeout.

### 3.3. Ranh Gioi Quyen Tep & Luu Tru Co So Du Lieu
- Tep co so du lieu mac dinh: `data/app_state.db`.
- **Rui ro:** Trong moi truong he dieu hanh chia se (shared host), neu file `app_state.db` duoc tao voi quyen mac dinh (umask 0022 cho phep doc toan he thong), cac tien trinh cua nguoi dung khac tren cung he thong co the doc truc tiep noi dung database.
- **Kien nghi:** Bo sung ma lenh dat quyen doc/ghi gioi han (chmod 0600 tren Linux/macOS) cho file database va thu muc chua khi khoi tao.

---

## 4. Kiem Dinh Ranh Gioi Du Lieu Nghien Cuu (Zero-Leakage Data Boundaries Audit)

Nguyen tac toi thuong trong nghien cuu he thong goi y la **tuyet doi khong duoc phep ro ri tap danh gia (Validation) va tap kiem thu (Test)** vao bat ky luong phuc vu truc tiep nao cua nguoi dung (Data Leakage Contamination).

Do kiem dinh da tien hanh truy vet ma nguon cua toan bo cac Router va Repository:

```
+------------------------------------+--------------------------+-----------------------+--------------------+
| Thanh Phan / Endpoint              | Nguon Du Lieu Truy Cap   | Trang Thai Cach Ly    | Ket Qua Kiem Dinh  |
+------------------------------------+--------------------------+-----------------------+--------------------+
| GET /api/movies                    | data/processed/core/     | Hoan toan tach biet   | ZERO-LEAKAGE PASS  |
| GET /api/movies/{id}               | data/processed/core/     | Hoan toan tach biet   | ZERO-LEAKAGE PASS  |
| GET /api/genres                    | data/processed/core/     | Hoan toan tach biet   | ZERO-LEAKAGE PASS  |
| GET /api/users                     | splits/train + CSR index | Khong doc val/test    | ZERO-LEAKAGE PASS  |
| GET /api/users/{id}/profile        | splits/train             | Khong doc val/test    | ZERO-LEAKAGE PASS  |
| GET /api/users/{id}/history        | splits/train             | Khong doc val/test    | ZERO-LEAKAGE PASS  |
| GET /api/recommendations/{id}      | train_seen_csr.npz       | Bo loc chi dung train | ZERO-LEAKAGE PASS  |
| GET /api/explanations/{uid}/{mid}  | splits/train             | Khong doc val/test    | ZERO-LEAKAGE PASS  |
| GET /api/lab/compare               | train_seen_csr.npz       | Bo loc chi dung train | ZERO-LEAKAGE PASS  |
| GET /api/lab/metrics               | JSON metrics (Phase 4)   | Chi doc chi so tong hop| ZERO-LEAKAGE PASS |
| GET /api/lab/metadata              | Counters tong quan       | Chi tra ve so dem     | ZERO-LEAKAGE PASS  |
| API Interactions (/watchlist, ...) | data/app_state.db        | Hoan toan tach biet   | ZERO-LEAKAGE PASS  |
+------------------------------------+--------------------------+-----------------------+--------------------+
```

### Chi Tiet Kiem Chung:
1. **Module `UserHistoryRepository` (`recommender/storage/user_history_repo.py`):**
   - Duong dan tap du lieu duoc hardcode va rang buoc chat che:
     `self.train_split_path = self.data_root / "splits" / "train"`
   - Khong co bat ky phuong thuc hoac logic nao doc hoac mo duong dan `splits/validation` hay `splits/test`.
   - Chi muc CSR (`train_seen_csr.npz`) duoc trich xuat duy nhat tu tap Train 24.67 trieu ban ghi danh gia.
2. **Endpoint `/api/users/{user_id}/history`:**
   - Truyen `user_id` vao `UserProfileService.get_user_history`.
   - Quet Parquet Dataset bang filter `ds.field("userId") == int(user_id)` ap dung tren duy nhat thu muc `splits/train`.
   - Nguoi dung khong the xem cac tuong tac da bi giu lai o tap Validation hoac Test (Leave-One-Last evaluation items duoc bao ve 100%).
3. **Endpoint `/api/lab/metrics`:**
   - Tiep nhan tham so query `split: str = Query("validation", pattern="^(validation|test)")`.
   - Khi kiem tra sau vao `ResearchMetricsRepository.get_metrics_comparison`:
     He thong trich xuat du lieu tu file bao cao tong hop `docs/phase4/expanded_validation_results.json`.
     Khong co ban ghi danh gia ca nhan nao bi trich xuat; chi co cac chi so thong ke vi mo (Hit Rate @ K, NDCG @ K, MRR @ K, thoi gian latency P95) duoc hien thi.
     Ngay ca khi truyen `split="test"`, he thong van giu nguyen su trung thuc khoa hoc, khong bao gio doc du lieu raw ratings tu phan vung Test.

---

## 5. Kiem Dinh Ranh Gioi Tham So Dau Vao & Validation (Input Boundaries)

### 5.1. Kiem Dinh Thang Diem Rating [0.5, 5.0]
- **Tai Router / Pydantic Schema:** `rating: float = Field(..., ge=0.5, le=5.0)` tai `RatingSubmitRequest`.
- **Tai Query Parameter:** `min_rating: Optional[float] = Query(None, ge=0.5, le=5.0)` tai `/api/users/{user_id}/history`.
- **Tai SQLite Schema:** `CHECK(rating >= 0.5 AND rating <= 5.0)`.
- **Tai Storage Code:** `if not (0.5 <= rating <= 5.0): raise ValueError(...)`.
- **Ket qua thuc nghiem:**
  - Gui `rating=5.5`: Bi chan voi HTTP 422 Unprocessable Entity.
  - Gui `rating=0.2`: Bi chan voi HTTP 422 Unprocessable Entity.
  - Gui `rating=-1.0`: Bi chan voi HTTP 422 Unprocessable Entity.
  - Gui `rating=4.5`: Chap nhan voi HTTP 200 OK.
- **Danh gia:** **HOAN HAO (Triple-Layer Boundary Enforcement)**.

### 5.2. Kiem Dinh Phan Trang (Pagination: page >= 1, 1 <= page_size <= 100)
- **Tai cac Endpoint:**
  - `GET /api/movies`: `page: int = Query(1, ge=1)`, `page_size: int = Query(20, ge=1, le=100)`.
  - `GET /api/users`: `page: int = Query(1, ge=1)`, `page_size: int = Query(20, ge=1, le=50)`.
  - `GET /api/users/{user_id}/history`: `page: int = Query(1, ge=1)`, `page_size: int = Query(20, ge=1, le=100)`.
- **Phong thu theo chieu sau tai Repository/Service:**
  - `catalog_repo.py`: `if page < 1: page = 1; page_size = max(1, min(page_size, 100))`
  - `user_profile_service.py`: `page = max(1, page); page_size = max(1, min(page_size, 100))`
- **Ket qua thuc nghiem:**
  - Gui `page=0`: Bi chan boi FastAPI validator voi HTTP 422.
  - Gui `page=-5`: Bi chan boi FastAPI validator voi HTTP 422.
  - Gui `page_size=1000`: Bi chan boi FastAPI validator voi HTTP 422.
- **Danh gia:** **XUAT SAC (PASS)**.

### 5.3. Kiem Dinh Gioi Han Nam Phat Hanh (Release Year Boundaries)
- **Tai `discovery_router.py`:**
  - `year_min: Optional[int] = Query(None, ge=1870, le=2050)`
  - `year_max: Optional[int] = Query(None, ge=1870, le=2050)`
  - Ket qua: Kiem soat chat che qua Pydantic/FastAPI Query validator.
- **Lo hong phat hien tai `PreferencesRequest` (`schemas.py`):**
  - Dinh nghia hien tai:
    ```python
    class PreferencesRequest(BaseModel):
        user_id: str
        genres: List[str]
        moods: Optional[List[str]] = Field(default_factory=list)
        min_year: Optional[int] = None
        max_year: Optional[int] = None
    ```
  - **Ket qua thu nghiem doi khang:**
    Gui request: `{"user_id": "test", "genres": ["Action"], "min_year": 2025, "max_year": 1990}`.
    He thong van tiep nhan voi HTTP 200 va luu vao SQLite gia tri nam nguoc doi (`min_year > max_year`), va khong co chan duoi `ge=1870, le=2050`.
  - **Danh gia:** **GAP IDENTIFIED - Can bo sung validator Pydantic.**

### 5.4. Kiem Dinh Path Parameters (ID am)
- **Tai `discovery_router.py`:**
  - `user_id: int` trong `/api/users/{user_id}/profile` khong co `Path(..., ge=1)`.
  - `movie_id: int` trong `/api/movies/{movie_id}` khong co `Path(..., ge=1)`.
  - `user_id: int` trong `/api/recommendations/{user_id}` khong co `Path(..., ge=1)`.
- **Ket qua thu nghiem:**
  - Gui `GET /api/users/-1/profile`: He thong tra ve HTTP 200 kem profile rong cua user am.
  - **Khuyen nghi:** Bo sung `Path(..., ge=1)` cho tat ca cac tham so path `user_id` va `movie_id`.

---

## 6. Danh Sach Phat Hien & Ma Tran Khac Phuc Lo Hong (Vulnerability Remediation Matrix)

Doi kiem dinh tong hop toan bo cac phat hien an ninh thanh ma tran phan loai muc do nghiem trong va giai phap xu ly:

```
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| Ma Phat| Muc Do   | Ten Lo Hong / Rui Ro An Ninh                      | Vi Tri Tep         | Trang Thai Khac Phuc   |
| Hien   | (Severity| (Vulnerability Description)                       | (Source Location)  | De Xuat                |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| SEC-01 | HIGH     | CORS Misconfiguration: allow_origins=['*'] cung   | recommender/api/   | THAY BANG EXPLICIT     |
|        |          | allow_credentials=True cho phep phan chieu bat ky | app.py             | ALLOWED ORIGINS        |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| SEC-02 | HIGH     | Unrestricted Model Array DoS tai /api/lab/compare | recommender/api/   | THEM max_length=10 CHO |
|        |          | gay nguy co lam dung CPU duyet do thi hang loat   | schemas.py         | TRUONG models          |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| SEC-03 | MEDIUM   | Unrestricted Payload Size tai feedback_text       | recommender/api/   | THEM max_length=1000   |
|        |          | gay nguy co can kiet bo nho luu tru SQLite        | schemas.py         | CHO feedback_text      |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| SEC-04 | MEDIUM   | Thieu Boundary & Logic Check min_year/max_year    | recommender/api/   | THEM ge=1870, le=2050  |
|        |          | trong PreferencesRequest                          | schemas.py         | & model_validator      |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| SEC-05 | MEDIUM   | Unprotected Administrative Cache Clear Endpoint   | recommender/api/   | THEM HEADER / TOKEN    |
|        |          | POST /api/system/cache/clear khong co xac thuc    | system_router.py   | XAC THUC CHO ADMIN     |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| SEC-06 | LOW-MED  | Ro ri chuoi ngoai le truc tiep str(e) tai         | recommender/api/   | CHE GIAU CHI TIET LOI, |
|        |          | /api/recommendations/{user_id} khi gap loi he thong| discovery_router.py| CHI GHI LOG NOI BO     |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
| SEC-07 | LOW      | Thieu Path(..., ge=1) validation cho cac duong    | recommender/api/   | BO SUNG Path(..., ge=1)|
|        |          | dan chua user_id va movie_id                      | discovery_router.py| CHO CAC PATH PARAMS    |
+--------+----------+---------------------------------------------------+--------------------+------------------------+
```

---

## 7. Huong Dan Va Ban Va Gia Co Chi Tiet (Actionable Security Patches)

Doi kiem dinh cung cap chi tiet cac khoi code can ap dung de gia co toan dien he thong len chuan an ninh Production:

### 7.1. Ban Va SEC-01: Khac Phuc CORS Misconfiguration (`recommender/api/app.py`)
Thay the cau hinh CORS wildcard bang danh sach mien ro rang (hoac tat `allow_credentials` neu dung wildcard):

```python
# recommender/api/app.py

import os

# Danh sach cac nguon duoc phep truy cap tu frontend
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

# Neu co bien moi truong FRONTEND_URL, bo sung vao whitelist
extra_origin = os.environ.get("MOODGRAPH_FRONTEND_URL")
if extra_origin:
    ALLOWED_ORIGINS.append(extra_origin)

application.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

### 7.2. Ban Va SEC-02, SEC-03, SEC-04: Gia Co Schemas Pydantic (`recommender/api/schemas.py`)
Bo sung cac rang buoc do dai, gioi han so luong phan tu, va rang buoc logic giua cac nam:

```python
# recommender/api/schemas.py

from pydantic import BaseModel, Field, model_validator

class LabCompareRequest(BaseModel):
    user_id: int = Field(..., ge=1, description="Target user ID")
    models: List[str] = Field(
        default=["als", "kg", "hybrid_rrf", "hybrid_weighted"],
        min_length=1,
        max_length=10, # Ngan chan DoS thuc thi qua nhieu mo hinh
        description="Models to evaluate side-by-side (max 10)",
    )
    top_n: int = Field(10, ge=1, le=50)
    filter_seen: bool = True
    rrf_k: int = Field(60, ge=1, le=200)
    weight_als: float = Field(0.5, ge=0.0, le=1.0)
    weight_kg: float = Field(0.5, ge=0.0, le=1.0)


class RatingSubmitRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64, description="User identifier")
    movie_id: int = Field(..., ge=1)
    rating: float = Field(..., ge=0.5, le=5.0)
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Max 1000 characters")


class PreferencesRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    genres: List[str] = Field(..., min_length=1, max_length=20)
    moods: Optional[List[str]] = Field(default_factory=list, max_length=10)
    min_year: Optional[int] = Field(None, ge=1870, le=2050)
    max_year: Optional[int] = Field(None, ge=1870, le=2050)

    @model_validator(mode="after")
    def validate_year_order(self) -> "PreferencesRequest":
        if self.min_year is not None and self.max_year is not None:
            if self.min_year > self.max_year:
                raise ValueError(f"min_year ({self.min_year}) must be <= max_year ({self.max_year})")
        return self
```

### 7.3. Ban Va SEC-06 & SEC-07: Che Giau Thong Tin Exception & Path Validation (`recommender/api/discovery_router.py`)
Su dung `Path(..., ge=1)` va an chuoi loi he thong:

```python
# recommender/api/discovery_router.py

from fastapi import Path

@router.get("/recommendations/{user_id}")
def get_recommendations(
    user_id: int = Path(..., ge=1, description="Positive user ID"),
    top_n: int = Query(10, ge=1, le=50),
    strategy: Optional[str] = Query(None, pattern="^(rrf|weighted|als_only|kg_only)"),
    filter_seen: bool = Query(True),
    use_cache: bool = Query(True),
    hybrid_engine=Depends(get_hybrid_engine),
):
    if hybrid_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hybrid recommender engine is warming up. Please retry in a few seconds.",
        )

    try:
        resp = hybrid_engine.recommend(
            user_id=user_id,
            top_n=top_n,
            strategy=strategy,
            filter_seen=filter_seen,
            use_cache=use_cache,
        )
        return resp.dict()
    except Exception as e:
        logger.error(f"Error serving recommendations for user {user_id}: {e}", exc_info=True)
        # Khong tra ve str(e) truc tiep cho client nham tranh ro ri thong tin noi bo
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating recommendations. Please check server logs.",
        )
```

---

## 8. Ket Luan & Kien Nghi Cho Giai Doan San Sang Trien Khai (Production Readiness)

1. **Danh Gia Chung:**
   - He thong Backend MoodGraph Phase 5 dat muc do an toan xuat sac o cac khau then chot:
     * **100% Zero-Leakage:** Cach ly tuyet doi va bao ve du lieu kiem dinh (Validation/Test).
     * **100% SQL Injection Resilience:** Parameterized queries toan dien, kien truc WAL transaction nhat quan.
     * **Clean Pydantic Layer:** Cac schema duoc phan dinh ranh mach, khong co Mass Assignment hay ro ri metadata khong mong muon.
2. **Kien Nghi Bat Buoc Truoc Khi Cong Khai Internet:**
   - Ap dung ngay Ban va SEC-01 (CORS Whitelist) de tranh nguy co CSRF/Cross-Origin data theft.
   - Ap dung Ban va SEC-02, SEC-03, SEC-04 (Pydantic Input Bound Hardening) de triet tieu cac vector tan cong can kiet tai nguyen dia va CPU.
   - Bo sung co che Token xac thuc cho endpoint quan tri `/api/system/cache/clear`.
3. **Ket Luan:**
   - He thong dat yeu cau ve mat kien truc bao mat cho moi truong Local Platform & Evaluation Lab.
   - Khi ap dung cac ban va phong thu neu tren, he thong hoan toan du tieu chuan an toan de trien khai len moi truong thu nghiem thuc te (Production/Staging Environment).
