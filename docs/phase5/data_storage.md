# MoodGraph Phase 5: Kien truc Luu tru & Tuan thu Tinh toan ven Du lieu (Data Storage & Integrity)

## 1. Phan dinh Ranh gioi Du lieu (Data Partitioning Boundaries)

MoodGraph phuc vu 25 trieu dong danh gia tu MovieLens 25M. De dam bao do tin cay tuyet doi ve mat khoa hoc va ky thuat phan mem, du lieu duoc phan dinh ranh gioi thanh 2 khoang rieng biet:

```
+---------------------------------------------------------------------------------+
|                                 DATA BOUNDARIES                                 |
|                                                                                 |
|   [READ-ONLY IMMUTABLE DATASETS]               [MUTABLE APPLICATION PERSISTENCE]|
|   - data/processed/core/movies (62,423 rows)   - data/app_state.db (SQLite)     |
|   - data/processed/core/links (62,423 rows)    - WAL Mode (Write-Ahead Logging) |
|   - data/processed/splits/train (24.6M rows)   - demo_users                     |
|   - artifacts/als/m10/train_seen_csr.npz       - saved_movies                   |
|                                                - user_ratings                   |
|   [FORBIDDEN FOR PROFILE & DEMO QUERIES]       - user_preferences               |
|   - data/processed/splits/validation (162K)    - experiment_sessions            |
|   - data/processed/splits/test (162K)                                           |
+---------------------------------------------------------------------------------+
```

---

## 2. Chi tiet Cac Kho Luu tru

### 2.1. MovieCatalogRepository
- **Nguon du lieu:** `data/processed/core/movies` va `data/processed/core/links`.
- **Cơ chế nạp:** Toan bo du lieu (62,423 phim ~ 4.35 MB) duoc nap vao RAM trong qua trinh khoi dong FastAPI Lifespan.
- **Cau truc chi muc:**
  * `_movies_by_id`: Dictionary ánh xạ `movieId -> Dict[str, Any]` voi toc do truy van O(1).
  * `_title_index`: Danh sach tuple `(title_lower, movieId)` phuc vu tim kiem nhanh.
  * `_genre_index`: Dictionary anh xa `genre -> List[movieId]`.
  * `_distinct_genres`: Danh sach 19 the loai phim duy nhat duoc sap xep theo chu cai.

### 2.2. UserHistoryRepository (Zero-Leakage CSR Index)
- **Nguon du lieu:**
  * `artifacts/als/m10/train_seen_csr.npz`: Mang offsets (162,542 phan tu) va movie_ids (24,675,013 phan tu).
  * `data/processed/splits/train`: Phung vung danh gia tap Train.
- **Co che Seen Filtering O(1):**
  * `seen_movies = movie_ids[offsets[user_id]:offsets[user_id + 1]]`
  * Toc do cat mang: Duoi 1 microsecond.
  * Bo nho RAM: Chi ~99 MB, khong can tao 162K Set trong Python.
- **Cam ket Bao ve Tinh toan ven (Zero-Leakage Guarantee):**
  * Tat ca cac phuong thuc trong `UserHistoryRepository` va `UserProfileService` deu chi truy van tren `train_split_path` va `train_seen_csr.npz`.
  * Khong co bat ky dong lenh nao mo hoac doc tu `splits/validation` hay `splits/test`.
  * Duoc kiem chung 100% boi test case `test_user_history_zero_leakage`.

### 2.3. SQLiteStateRepository (WAL Mode)
- **Muc tieu:** Cho phep nguoi dung demo trai nghiem luu watchlist, danh gia phim, tuy chinh the loai ma KHONG xam pham vao tap du lieu lon MovieLens 25M.
- **Tep tin:** `data/app_state.db`
- **Cau hinh Pragma:**
  ```sql
  PRAGMA journal_mode = WAL;
  PRAGMA synchronous = NORMAL;
  PRAGMA foreign_keys = ON;
  ```
- **Ket cau bang:**
  * `demo_users`: Luu thong tin tai khoan demo.
  * `saved_movies`: Luu danh sach phim watchlist/favorites kem timestamp.
  * `user_preferences`: Luu chuoi JSON genres, moods, khoang nam phat hanh.
  * `user_ratings`: Luu danh gia cua user tu 0.5 den 5.0 sao.
  * `experiment_sessions`: Luu nhat ky cac lan so sanh da mo hinh o Mode B.

---

## 3. Danh gia Trang thai Backend Graph (Neo4j Status)
- Thu vien `neo4j` hien tai khong duoc cai dat trong runtime moi truong local va port `bolt://localhost:7687` offline.
- He thong su dung backend van hanh chuan hoa la `InMemoryGraph` duoc khoi tao tu cac tep Parquet Pilot.
- `InMemoryGraph` duy tri day du cac chi muc hai chieu giua Users, Movies, Genres va GenomeTags (Top-20 relevance), cung cap toc do duyet do thi duoi 5ms ma khong lam tang do phuc tap van hanh.

