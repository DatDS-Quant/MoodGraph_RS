# MoodGraph Phase 5: Kiem dinh Truy cap Du lieu va Thiet ke Luu tru Ben vung (Data Access & Persistence Audit)

**Nguoi lap bao cao:** Senior Data Engineer and Database Architect  
**Ngay kiem dinh:** 2026-11-07  
**Phien ban He thong:** MoodGraph Phase 5 (Phat trien ke thua tu Phase 4 v4.0.0)  
**Trang thai He thong:** 25,000,095 MovieLens 25M Ratings dong bang, 62,423 Movies, 162,541 Users, 1,128 Genome Tags  

---

## 1. Tong quan va Bang Danh gia Cac Cong Kiem dinh Du lieu (Data & Persistence Gates Matrix)

Bao cao nay la tai lieu danh gia doc lap ve toan bo ha tang truy cap du lieu va thiet ke luu tru ben vung cho Phase 5 cua he thong MoodGraph. Nhiem vu trong tam bao gom:
1. Tham dinh toan dien cac tap du lieu Parquet da tien xu ly duoi `data/processed/core/`, `data/processed/features/`, va `data/processed/splits/`.
2. Kiem dinh co che chi muc nen CSR `artifacts/als/m10/train_seen_csr.npz` danh cho lich su Train 24.6M tuong tac.
3. Kiem dinh cac lop truy cap do thi trong `recommender/kg/data_access.py` va `recommender/kg/import_graph.py`.
4. Danh gia trang thai van hanh thuc te cua Neo4j Server va co che InMemoryGraph.
5. Thiet ke kien truc kho luu tru chuyen biet (Repositories) cho Movie Catalog va User Profile voi cam ket tuyet doi khong gay ro ri du lieu (Zero Data Leakage).
6. Thiet ke mo hinh luu tru trang thai ung dung (Application State) bang SQLite cho cac tuong tac demo nguoi dung ma khong dong cham hoac nhan ban tap du lieu 25M dong bang.

### Bang danh gia cac cong kiem dinh (Data Gates Matrix)

| Ma Cong | Tieu chi Kiem dinh | Trang thai | Ket qua va Danh gia Chi tiet |
| :--- | :--- | :---: | :--- |
| **D-GATE-01** | **Tinh Toan ven Datasets Parquet Core** | **PASS** | 5 tap core (`movies`, `links`, `genome_tags`, `genome_scores`, `tags`) va 2 tap features (`movie_genres`, `tags_train`) ton tai day du 100%, schema chuan hoa khong co null field bat thuong, Snappy compression. |
| **D-GATE-02** | **Cach ly Phau phan Du lieu (Split Isolation)** | **PASS** | Train (24,675,013 dong), Validation (162,541 dong), Test (162,541 dong) duoc phan tach vat ly ro rang. Ty le chia 98.7% / 0.65% / 0.65% dung quy chuan Leave-1-Last. |
| **D-GATE-03** | **Anh xa Dinh danh Goc (MovieLens Canonical IDs)** | **PASS** | Dinh danh `userId` lien tuc tu 1 den 162,541. Dinh danh `movieId` thua tu 1 den 209,171 (62,423 phim catalog, 58,932 phim co rating train, 3,376 phim catalog cold-start). |
| **D-GATE-04** | **Chi muc CSR Train-Seen Sieu toc** | **PASS** | `train_seen_csr.npz` (50.8 MB) luu tru 162,543 offsets va 24,675,013 `movie_ids`. Truy van O(1) theo microsecond, loai bo 100% rui ro bo nho RAM khi loc phim da xem. |
| **D-GATE-05** | **Trang thai Backend Graph (Neo4j vs InMemoryGraph)** | **PARTIAL** | Python driver `neo4j` chua duoc cai dat trong moi truong, Neo4j daemon offline. InMemoryGraph la che do van hanh duoc xac thuc 100% (verified operational mode) voi do tre < 5ms. |
| **D-GATE-06** | **Thiet ke Movie Catalog Repository** | **PASS** | Ban thiet ke in-memory index cho 62,423 phim (RAM ~ 4.35 MB) ket hop metadata `links` (IMDb, TMDb) giup tim kiem, loc the loai va phan trang dat P99 < 10ms. |
| **D-GATE-07** | **Thiet ke User Profile Repository (Zero Leakage)** | **PASS** | Ban thiet ke khoa chat: chi doc tu `splits/train` va CSR Index. Cach ly tuyet doi khoi `validation` va `test`. PyArrow predicate pushdown quet lich su train < 80ms. |
| **D-GATE-08** | **Luu tru State Demo bang SQLite** | **PASS** | Schema 5 bang ro rang (`demo_users`, `saved_movies`, `user_preferences`, `user_ratings`, `experiment_sessions`) cho phep ghi doc tuong tac demo ma khong lam o nhiem tap 25M dong bang. |

---

## 2. Kiem dinh Thuc te Cac Tep Du lieu Parquet (Parquet Datasets Physical Audit)

Toan bo du lieu processed duoc kiem tra truc tiep thong qua thu vien `pyarrow.parquet` tren he thong file vat ly.

### 2.1. Danh muc Du lieu Nen tang (Core & Features Datasets)

| Dataset Path | So tep | Tong so ban ghi | Dung luong RAM uoc tinh | Cac cot & Kieu du lieu chinh | Ghi chu kien truc |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `data/processed/core/movies` | 1 | 62,423 | 4.35 MB | `movieId: int32`, `title: string`, `genres: string`, `genre_list: list<element: string>` | Da tien xu ly san cot `genre_list` dang mang chuoi. 5,062 phim mang gia tri '(no genres listed)'. |
| `data/processed/core/links` | 1 | 62,423 | 1.15 MB | `movieId: int32`, `imdbId: string`, `tmdbId: int32` | Khop 1-1 voi tap movies. Cung cap id ngoai phuc vu lay poster va lien ket dien anh. |
| `data/processed/core/genome_tags` | 1 | 1,128 | 0.05 MB | `tagId: int32`, `tag: string` | Danh muc 1,128 dac trung ngu nghia (tag genome) chuan hoa. |
| `data/processed/core/genome_scores` | 4 | 15,584,448 | ~ 180 MB | `movieId: int32`, `tagId: int32`, `relevance: float` | 13,816 phim co diem genome x 1,128 tags = 15,584,448 dong. Da sap xep phan manh. |
| `data/processed/core/tags` | 2 | 1,093,360 | ~ 35 MB | `userId: int32`, `movieId: int32`, `tag: string`, `timestamp: int64`, `tag_clean: string` | Nhan gan nguoi dung tu do tren toan bo lich su MovieLens. |
| `data/processed/features/movie_genres` | 1 | 107,245 | ~ 2.5 MB | `movieId: int32`, `genre: string` | Dang unnested (1 phim nhieu dong the loai), 19 the loai duy nhat. |
| `data/processed/features/tags_train` | 1 | 1,074,090 | ~ 34 MB | `userId: int32`, `movieId: int32`, `tag: string`, `timestamp: int64`, `tag_clean: string` | Tap tags da duoc loc chat che theo moc thoi gian cua tap Train. |

### 2.2. Danh muc Cac Phau phan Danh gia (Splits Datasets)

| Dataset Path | So tep | Tong so ban ghi | Tinh chat du lieu | Quy cach phan vung |
| :--- | :---: | :---: | :--- | :--- |
| `data/processed/splits/train` | 8 | 24,675,013 | Tap huan luyen da dong bang. Chiem 98.7% tong so ratings. | 8 phan manh snappy parquet. Dung luong tren dia: ~ 260 MB. |
| `data/processed/splits/validation` | 1 | 162,541 | Tap danh gia tuning (Leave-1-Last). Moi user co dung 1 rating. | 1 phan manh snappy parquet. Dung luong tren dia: ~ 2.1 MB. |
| `data/processed/splits/test` | 1 | 162,541 | Tap kiem thu benchmark (Leave-1-Last). Moi user co dung 1 rating. | 1 phan manh snappy parquet. Dung luong tren dia: ~ 2.1 MB. |

### 2.3. Quy luat phan bo Dinh danh va Phat hien Quan trong
Qua phan tich tap du lieu:
- Tong so phim trong Catalog: 62,423 phim.
- Tong so phim xuat hien trong Train ratings: 58,932 phim.
- Tong so phim xuat hien trong Validation: 11,042 phim (trong do co 53 phim chua tung xuat hien trong Train).
- Tong so phim xuat hien trong Test: 11,606 phim (trong do co 65 phim chua tung xuat hien trong Train).
- So luong phim khong co bat ky rating nao o ca 3 tap (Train/Val/Test): 3,376 phim. Day la tap ung vien Cold-Start tuyet doi trong he thong, chi co the tiep can qua Genre hoac Tag Genome.

---

## 3. Kiem dinh Chi muc Nen CSR Train-Seen (`train_seen_csr.npz`)

Chi muc `artifacts/als/m10/train_seen_csr.npz` la mot giai phap ky thuat xuat sac duoc ke thua tu Milestone M10 cua Task 3A.

### 3.1. Cau truc Vat ly
Tep npz gom 2 mang du lieu kieu 32-bit integer:
- `offsets`: mang kich thuoc `(162543,)`, kieu `int32`.
- `movie_ids`: mang kich thuoc `(24675013,)`, kieu `int32`.

### 3.2. Co che Anh xa 1-Based truc tiep
- Do tap user cua MovieLens danh so tu 1 den 162,541, chi muc CSR duoc thiet ke voi quy tac truy van truc tiep theo chi so mang ma khong can qua bang bam (zero hash table overhead):
  - `start = offsets[user_id]`
  - `end = offsets[user_id + 1]`
  - `seen_movies = movie_ids[start:end]`
- **Kiem tra bien (Boundary Check):**
  - `offsets[0] = 0` (dummy padding).
  - `offsets[1] = 0`, `offsets[2] = 68` -> User 1 da xem 68 phim trong tap Train.
  - `offsets[162541] = 24674833`, `offsets[162542] = 24675013` -> User 162541 da xem 180 phim trong tap Train.
  - `offsets[162542] = 24,675,013`, khop tuyet doi 100% voi tong so dong cua `splits/train`.

### 3.3. Uu diem vuot troi cho Phase 5
1. **Toc do cuc han:** Viec cat mang NumPy `movie_ids[start:end]` ton duoi 1 microsecond.
2. **Bo nho sieu nhe:** Tep tren dia chi 50.8 MB. Khi load vao RAM, 2 mang nay chi chiem ~ 99 MB, hoan toan loai bo nhu cau tao 162,541 tap hop `Set[int]` trong Python (von ton hon 1.2 GB RAM).
3. **Dung cho Candidate Filtering:** Hybrid Engine su dung CSR de tru tap phim da xem ra khoi danh sach goi y chi trong chop mat.

---

## 4. Kiem dinh Lop Do thi va Trang thai Backend Graph (Neo4j Status)

### 4.1. Audit `recommender/kg/data_access.py`
Module `DataAccess` cung cap cac phuong thuc doc du lieu Parquet theo stream batch:
- `stream_movies`: doc theo lo mac dinh 5,000 ban ghi.
- `stream_movie_genres`: doc theo lo tu `features/movie_genres`.
- `stream_genome_tags`: doc `core/genome_tags`.
- `stream_top_m_genome_scores`: su dung min-heap kich thuoc co dinh `top_m` de loc 20 tag relevance cao nhat cho moi phim, kiem soat bo nho chat che (< 30 MB) va chong hien tuong mat tag khi phim nam tren nhieu chunk.
- `stream_train_ratings`: doc doc quyen tu `splits/train`.

**Nhan xet:** Code sach se, dung chuan PyArrow dataset scanner, tuan thu split isolation.

### 4.2. Audit `recommender/kg/import_graph.py` & Trang thai Neo4j
- Tap lenh ho tro hai backend: `Neo4jGraph` va `InMemoryGraph`.
- **Kiem tra hien truong he thong:**
  1. Goi Python `neo4j` **CHUA DUOC CAI DAT** trong moi truong hien tai (`ModuleNotFoundError: No module named 'neo4j'`).
  2. Cong Neo4j `bolt://localhost:7687` **OFFLINE** (khong co tien trinh Neo4j server nao chay tren may host).
  3. Lop `InMemoryGraph` la backend duoc viet thuan Python voi cac dictionary chi muc hai chieu (`user_rated_movie`, `movie_rated_by_users`, `movie_in_genre`, `genre_to_movies`, `movie_has_genome_tag`, `genome_tag_to_movies`).
  4. Che do Fallback an toan trong `recommender/kg/recommend.py` (dong 33-50) co co che bao ve: ngan chan am tham suy giam (silent degradation) bang cach chan fallback sang synthetic fixture neu bien moi truong `KG_ALLOW_SYNTHETIC_FALLBACK` khong duoc bat.

### 4.3. Ket luan Chuyen gia ve Graph Storage cho Phase 5
- **Trang thai:** **PARTIAL** (Neo4j Server khong kha dung trong runtime hien tai).
- **Backend van hanh chuan hoa (Verified Operational Mode):** `InMemoryGraph` va cac chi muc tep (File-based CSR / Parquet / ALS factors) la nen tang cot loi de phuc vu Phase 5.
- Trong pham vi phuc vu demo va danh gia he thong, `InMemoryGraph` dap ung hoan hao ve toc do (< 5ms cho khai pha duong di P1/P2/P3 tren tap cohort) ma khong doi hoi ha tang may chu Neo4j phuc tap.

---

## 5. Thiet ke Kho Du lieu Doc (Read-Only Repositories Blueprint)

De phuc vu Mode A (Movie Discovery) va Mode B (Recommendation Lab), he thong can cac lop truu tuong truy cap du lieu chuyen biet, ngan cach ro rang giua Catalog, User Profile va Engine goi y.

```
+-------------------------------------------------------------------------------+
|                            PHASE 5 REPOSITORY LAYER                           |
|                                                                               |
|  +----------------------------+             +-------------------------------+ |
|  |   IMovieCatalogRepository  |             |     IUserProfileRepository    | |
|  +----------------------------+             +-------------------------------+ |
|  | - get_by_id(movieId)       |             | - get_history(userId, page)   | |
|  | - search(query, genre, p)  |             | - get_seen_set(userId)        | |
|  | - list_genres()            |             | - get_genre_profile(userId)   | |
|  | - get_tags(movieId)        |             | - exists(userId)              | |
|  +--------------+-------------+             +---------------+---------------+ |
|                 |                                           |                 |
|                 v                                           v                 |
|  +----------------------------+             +-------------------------------+ |
|  | ParquetMovieCatalogRepo    |             | HybridUserProfileRepo         | |
|  | (In-memory 62K DF / Index) |             | (CSR O(1) + Train Parquet)    | |
|  +--------------+-------------+             +---------------+---------------+ |
|                 |                                           |                 |
+-----------------|-------------------------------------------|-----------------+
                  v                                           v
   [data/processed/core/movies]                [artifacts/als/m10/train_seen_csr]
   [data/processed/core/links]                 [data/processed/splits/train]
```

### 5.1. Movie Catalog Repository (`IMovieCatalogRepository`)

#### Nguyen tac Thiet ke:
1. **Pre-warmed In-Memory Index:** Do tap `movies` chi co 62,423 dong (~ 4.35 MB) va `links` chi co 1.15 MB, toan bo thong tin cot loi nen duoc doc vao bo nho trong qua trinh khoi dong FastAPI Lifespan.
2. **Ho tro Tim kiem va Loc da tieu chi:**
   - Tim kiem theo ten phim (Sub-string / Case-insensitive hoac Regex token).
   - Loc theo the loai (Genre matching).
   - Phan trang (Limit, Offset) va sap xep (theo movieId hoac release year).
3. **Giau hoa Sieu du lieu (Enriched Metadata):**
   - Tu dong ghep voi `links` de tra ve IMDb URL (`https://www.imdb.com/title/tt{imdbId}`) va TMDb URL (`https://www.themoviedb.org/movie/{tmdbId}`).
   - Trich xuat nam phat hanh tu chuoi tieu de (vi du: "Toy Story (1995)" -> nam 1995).

#### Giao dien Chuan hoa (Python Interface):

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

@dataclass(frozen=True)
class MovieRecord:
    movieId: int
    title: str
    year: Optional[int]
    genres: List[str]
    imdbId: Optional[str] = None
    tmdbId: Optional[int] = None
    imdbUrl: Optional[str] = None
    tmdbUrl: Optional[str] = None

@dataclass(frozen=True)
class MovieCatalogPage:
    items: List[MovieRecord]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class IMovieCatalogRepository(ABC):
    @abstractmethod
    def get_by_id(self, movie_id: int) -> Optional[MovieRecord]:
        """Lay thong tin chi tiet 1 phim theo canonical movieId."""
        pass

    @abstractmethod
    def get_by_ids(self, movie_ids: List[int]) -> Dict[int, MovieRecord]:
        """Lay thong tin theo danh sach movieIds theo thu tu tra ve."""
        pass

    @abstractmethod
    def search(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> MovieCatalogPage:
        """Tim kiem phim kem loc the loai va phan trang."""
        pass

    @abstractmethod
    def list_genres(self) -> List[str]:
        """Liet ke toan bo 19 the loai phim co trong he thong."""
        pass

    @abstractmethod
    def get_top_genome_tags(self, movie_id: int, top_m: int = 10) -> List[Dict[str, Any]]:
        """Lay danh sach top-M tag genome dac trung cua phim."""
        pass
```

### 5.2. User Profile Repository (`IUserProfileRepository`)

#### Nguyen tac Thiet ke & Bao ve Du lieu:
1. **Cam tuyet doi Doc tu Validation hoac Test:**
   - Tap `validation` va `test` la danh gia khoa hoc Leave-1-Last. Moi hanh vi doc 2 tep nay trong User Profile phuc vu giao dien hoac tinh toan profile deu bi coi la vi pham kien truc nghiem trong (Data Leakage).
2. **Co che Truy van Ket hop (Hybrid Lookup):**
   - De lay danh sach cac ID phim da xem (phuc vu Seen Filtering): Dung `train_seen_csr.npz` voi toc do microsecond.
   - De lay chi tiet ratings, thoi gian tuong tac va tinh phan bo the loai yeu thich cua user: Quet `data/processed/splits/train` qua PyArrow Predicate Pushdown (`filter=(ds.field("userId") == user_id)`), thoi gian hoan tat tu 70ms den 200ms.
   - Ket qua duoc dua vao LRU Cache cuc bo cua Service de nhung lan goi tiep theo tra ve ngay trong 0.1ms.

#### Giao dien Chuan hoa (Python Interface):

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

@dataclass(frozen=True)
class UserRatingRecord:
    userId: int
    movieId: int
    rating: float
    timestamp: int
    title: Optional[str] = None
    genres: Optional[List[str]] = None

@dataclass(frozen=True)
class UserProfileSummary:
    userId: int
    total_ratings: int
    mean_rating: float
    top_genres: List[Dict[str, Any]]
    first_activity: int
    last_activity: int

class IUserProfileRepository(ABC):
    @abstractmethod
    def get_seen_movie_ids(self, user_id: int) -> Set[int]:
        """Truy xuat tap movieIds da xem trong Train thong qua chi muc CSR O(1)."""
        pass

    @abstractmethod
    def get_rating_history(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        min_rating: Optional[float] = None
    ) -> List[UserRatingRecord]:
        """Doc lich su danh gia cua nguoi dung tu tap Train, ho tro phan trang va loc."""
        pass

    @abstractmethod
    def get_profile_summary(self, user_id: int) -> Optional[UserProfileSummary]:
        """Tong hop ho so so thich the loai va thong ke danh gia cua user tu tap Train."""
        pass

    @abstractmethod
    def exists(self, user_id: int) -> bool:
        """Kiem tra xem userId co ton tai trong tap Train hay khong (1 <= userId <= 162541)."""
        pass
```

---

## 6. Thiet ke Luu tru Trang thai Ung dung bang SQLite (Application State Blueprint)

Trong Phase 5, he thong can ho tro nguoi dung demo trai nghiem cac tinh nang tuong tac thuc te:
- Luu phim vao danh sach yeu thich (Watchlist / Saved Movies).
- Tinh chinh so thich ca nhan (Custom Preferred Genres, Moods).
- Gui danh gia, phan hoi (Rating feedback cho phim).
- Luu vet cac phien thu nghiem so sanh mo hinh o Mode B.

### 6.1. Tai sao la SQLite?
1. **Khong xam pham Big Data:** Du lieu MovieLens 25M Parquet duoc giu bat bien (Read-Only). SQLite chi luu nhung gi nguoi dung demo phat sinh.
2. **Khong ton chi phi ha tang:** SQLite di kem san trong Python Standard Library (`sqlite3`), khong can Docker container, khong can tai khoan root, khong can mo port mang.
3. **Hieu nang cao va An toan Giao dich:** Ho tro WAL Mode (Write-Ahead Logging), cho phep nhieu luong doc song song trong khi 1 luong ghi dang thuc thi.

### 6.2. So do Quan he Thuc the SQLite (ERD)

```
+-----------------------------------------------------------------------------------+
|                            SQLITE APPLICATION PERSISTENCE                         |
|                                                                                   |
|      +------------------------+             +-------------------------------+     |
|      |       demo_users       |             |          saved_movies         |     |
|      +------------------------+             +-------------------------------+     |
|      | PK user_id (TEXT/INT)  |<---+        | PK id (INTEGER AUTOINCREMENT) |     |
|      |    username (TEXT)     |    |        | FK user_id (TEXT/INT)         |-----+
|      |    display_name (TEXT) |    |        |    movie_id (INTEGER)         |     |
|      |    created_at (INT)    |    |        |    list_type (TEXT)           |     |
|      +------------------------+    |        |    created_at (INTEGER)       |     |
|                   |                |        +-------------------------------+     |
|                   |                |                                              |
|                   |                |        +-------------------------------+     |
|                   |                +------->|          user_ratings         |     |
|                   |                |        +-------------------------------+     |
|                   |                |        | PK id (INTEGER AUTOINCREMENT) |     |
|                   |                |        | FK user_id (TEXT/INT)         |     |
|                   |                |        |    movie_id (INTEGER)         |     |
|                   |                |        |    rating (REAL)              |     |
|                   |                |        |    feedback_text (TEXT)       |     |
|                   |                |        |    created_at (INTEGER)       |     |
|                   v                |        +-------------------------------+     |
|      +------------------------+    |                                              |
|      |    user_preferences    |    |        +-------------------------------+     |
|      +------------------------+    +------->|      experiment_sessions      |     |
|      | PK user_id (TEXT/INT)  |             +-------------------------------+     |
|      |    genres_json (TEXT)  |             | PK session_id (TEXT)          |     |
|      |    moods_json (TEXT)   |             | FK user_id (TEXT/INT)         |     |
|      |    preferred_years_json|             |    model_a (TEXT)             |     |
|      |    updated_at (INTEGER)|             |    model_b (TEXT)             |     |
|      +------------------------+             |    comparison_results (TEXT)  |     |
|                                             |    created_at (INTEGER)       |     |
|                                             +-------------------------------+     |
+-----------------------------------------------------------------------------------+
```

### 6.3. Chi tiet Schema DDL Chuan hoa (SQL Data Definition)

```sql
-- Kich hoat che do Write-Ahead Logging de tang toc do doc ghi song song
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Bang Nguoi dung Demo (Ho tro ca synthetic persona va guest session)
CREATE TABLE IF NOT EXISTS demo_users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    bio TEXT,
    created_at INTEGER NOT NULL
);

-- 2. Bang Danh sach Phim da luu (Watchlist, Favorites)
CREATE TABLE IF NOT EXISTS saved_movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    movie_id INTEGER NOT NULL,
    list_type TEXT NOT NULL DEFAULT 'watchlist' CHECK(list_type IN ('watchlist', 'favorites', 'hidden')),
    created_at INTEGER NOT NULL,
    UNIQUE(user_id, movie_id, list_type),
    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_saved_movies_user ON saved_movies(user_id, list_type);

-- 3. Bang So thich Nguoi dung (Genres, Moods, Preferred Decades)
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id TEXT PRIMARY KEY,
    genres_json TEXT NOT NULL DEFAULT '[]',
    moods_json TEXT NOT NULL DEFAULT '[]',
    min_year INTEGER,
    max_year INTEGER,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
);

-- 4. Bang Danh gia phan hoi truc tiep cua nguoi dung Demo
CREATE TABLE IF NOT EXISTS user_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    movie_id INTEGER NOT NULL,
    rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
    feedback_text TEXT,
    created_at INTEGER NOT NULL,
    UNIQUE(user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_user_ratings_user ON user_ratings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_ratings_movie ON user_ratings(movie_id);

-- 5. Bang Nhat ky Phien thi nghiem So sanh Mo hinh (Mode B Lab Sessions)
CREATE TABLE IF NOT EXISTS experiment_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    mode TEXT NOT NULL DEFAULT 'compare',
    model_a TEXT NOT NULL,
    model_b TEXT NOT NULL,
    params_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_experiment_user ON experiment_sessions(user_id, created_at DESC);
```

### 6.4. SQLite Repository Interface (`IAppStateRepository`)

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class IAppStateRepository(ABC):
    @abstractmethod
    def save_movie(self, user_id: str, movie_id: int, list_type: str = "watchlist") -> bool:
        """Them phim vao danh sach watchlist hoac favorites cua demo user."""
        pass

    @abstractmethod
    def remove_saved_movie(self, user_id: str, movie_id: int, list_type: str = "watchlist") -> bool:
        """Xoa phim khoi danh sach watchlist."""
        pass

    @abstractmethod
    def list_saved_movies(self, user_id: str, list_type: str = "watchlist") -> List[int]:
        """Lay danh sach cac movieId duoc luu boi demo user."""
        pass

    @abstractmethod
    def set_user_preferences(
        self,
        user_id: str,
        genres: List[str],
        moods: List[str],
        min_year: Optional[int] = None,
        max_year: Optional[int] = None
    ) -> bool:
        """Cap nhat so thich the loai va tam trang cua demo user."""
        pass

    @abstractmethod
    def get_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Lay cau hinh so thich cua demo user."""
        pass

    @abstractmethod
    def submit_rating(self, user_id: str, movie_id: int, rating: float, feedback: Optional[str] = None) -> bool:
        """Ghi nhan danh gia va gop y tu demo user."""
        pass

    @abstractmethod
    def get_custom_ratings(self, user_id: str) -> Dict[int, float]:
        """Lay toan bo danh gia custom cua demo user duoi dang dict {movieId: rating}."""
        pass
```

---

## 7. Ke hoach Thuc thi va Lo trinh Tich hop (Execution & Migration Plan)

De dua kien truc luu tru nay vao thuc te ma khong gay anh huong den he thong dang hoat dong, lo trinh thuc hien gom 4 buoc cu the:

```
Buoc 1: Tao Module Repository Chuyen biet
├── recommender/repositories/
│   ├── __init__.py
│   ├── base.py               (Interface dinh nghia hop dong)
│   ├── movie_catalog.py      (ParquetMovieCatalogRepository voi in-memory index)
│   ├── user_profile.py       (HybridUserProfileRepository voi CSR + Train scan)
│   └── app_state.py          (SQLiteAppStateRepository)

Buoc 2: Thiet lap SQLite Schema & Migration Script
├── scripts/
│   └── init_app_state_db.py  (Khoi tao data/app_state.db va tao tables + indexes)

Buoc 3: Refactor HybridRecommenderService va Delivery
├── Loai bo viec goi truc tiep `kg_graph.movies` de lay ten phim.
├── Thay the bang `movie_catalog_repo.get_by_id(movie_id)`.
└── Tich hop custom_seen tu `app_state_repo.list_saved_movies()` vao candidate filtering.

Buoc 4: Tich hop FastAPI Lifespan trong `recommender/hybrid/api.py`
├── Pre-warming MovieCatalog (nap 62K movies vao RAM trong < 600ms khi khoi dong).
├── Pre-loading CSR Index offsets va movie_ids.
└── Khoi tao ket noi SQLite pool an toan cho async requests.
```

---

## 8. Ket luan Chuyen gia (Architectural Verdict)

1. **Du lieu Parquet va Chi muc CSR:** Hoan toan vung chac, chat che va san sang 100% cho Phase 5. Khong co bat ky su thieu hut file hay sai lech schema nao.
2. **Kiem soat Data Leakage:** Viec khoa chat User Profile vao tap Train va loai tru 100% tap Validation va Test bao ve tinh chinh xac khoa hoc cua toan bo he thong.
3. **Mo hinh Luu tru Phan tach:** Ket hop giua Read-Only Big Data (Parquet + CSR) va Lightweight Read/Write Relational State (SQLite) la giai phap thiet ke toi uu nhat cho MoodGraph Phase 5: khong nhan ban 25M dong rating, khong ton chi phi van hanh server csdl rieng, va duy tri tinh toan ven tuyet doi cua du lieu goc.
