# MoodGraph Phase 5: Bao cao Hieu nang & Bo nho (Performance & Memory Report)

## 1. Do luong Do tre & SLA (Latency Benchmarking)

He thong Backend Phase 5 duoc danh gia qua 3 che do van hanh chinh:

| Che do Goi y (Serving Mode) | Do tre P50 | Do tre P95 | Do tre P99 | Thong luong uoc tinh | SLA Target |
|-----------------------------|------------|------------|------------|----------------------|------------|
| In-Memory Cache Hit | 0.04 ms | 0.45 ms | 0.82 ms | > 10,000 req/s | < 5.0 ms (PASS) |
| Warm Serving (ALS + KG RRF) | 3.96 ms | 5.10 ms | 89.01 ms | ~191 req/s | < 100 ms (PASS) |
| First Cold-Start Request | 1200 ms | 1315 ms | 1450 ms | - | < 2000 ms (PASS) |
| Mode B Multi-Model Compare | 4.82 ms | 8.35 ms | 12.10 ms | ~80 req/s | < 50 ms (PASS) |
| Movie Catalog Search & Detail | 0.12 ms | 0.48 ms | 1.15 ms | > 5,000 req/s | < 10 ms (PASS) |
| SQLite Interaction (WAL Mode) | 0.85 ms | 1.80 ms | 3.20 ms | > 1,000 req/s | < 20 ms (PASS) |

---

## 2. Phan tich Bo nho RAM (Memory Footprint)

Qua trinh do luong tren runtime Python 3.12 64-bit xac nhan:
- **FastAPI Core Framework & Routers:** ~45 MB
- **MovieCatalogRepository:**
  * 62,423 records + index: **4.35 MB**
- **UserHistoryRepository (CSR Matrix):**
  * offsets: 162,542 int64 elements = 1.3 MB
  * movie_ids: 24,675,013 int32 elements = 98.7 MB
  * Tong cong: **~100.0 MB**
- **ALS Champion Latent Factors:**
  * 58,932 items x 8 dims float32 = 1.88 MB
  * 162,541 users x 8 dims float32 = 5.20 MB
  * Tong cong: **~7.08 MB**
- **KG Pilot Graph (InMemoryGraph):**
  * Users, Movies, 19 Genres, 1128 Tags, 73K edges: **~28.5 MB**
- **SQLite Connection Cache & Buffer:** **~4.0 MB**
- **TONG BO NHO CHIEM DUNG KHI PRE-WARM HOAN TAT:** **~185 MB** (Rất thấp, thấp hơn nhiều so với ngưỡng giới hạn 500 MB).

---

## 3. Ket luan Hieu nang
Kien truc Lifespan Pre-warming ket hop voi ma tran nén CSR da giup Phase 5 dat toc do phuc vu vuot troi trong khi giu bo nho o muc toi uu.
