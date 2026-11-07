# MoodGraph Phase 5: Cac Gioi han Da biet & Huong Phat trien (Known Limitations & Future Work)

## 1. Cac Gioi han Hien tai (Known Limitations)

1. **Neo4j Offline & In-Memory Graph Pilot:**
   - Moi truong cuc bo hien tai chua cai dat package `neo4j` va khong co container Neo4j Server chay o cong 7687.
   - Do do, he thong dang van hanh che do `InMemoryGraph` dua tren tap Parquet pilot (100 users, 62,423 movies, 1,128 tags).
   - *Giai phap tuong lai:* Trien khai Neo4j Cluster tren Docker Compose hoac Kubernetes va cai dat `neo4j>=5.0` khi scale out sang toan bo 162K users.

2. **Nang luc Mo rong Nguoi dung Demo (Demo State Scale):**
   - SQLite duoc cau hinh WAL mode rat nhanh cho hang ngan truy van dong thoi, nhung van phu thuoc vao disk I/O cuc bo cua 1 may chu (Single Node).
   - *Giai phap tuong lai:* Chuyen sang PostgreSQL hoac Redis Cluster neu he thong can phuc vu hang trieu nguoi dung tuong tac dong thoi truc tuyen.

3. **Chua ho tro Online Learning Thoi gian thuc:**
   - Cac tuong tac moi trong SQLite chua lap tuc cap nhat lai vector ma tran ALS (can quy trinh retraining batch hang ngay tren Spark).
   - Tuy nhien, he thong da ho tro cache invalidation lap tuc de cac de xuat tiep theo phan anh thay doi.

---

## 2. Huong Phat trien Tiep theo (Phase 6 / Production Roadmap)
1. **Frontend Web UI & Interactive Dashboard:**
   - Xay dung giao dien React / Next.js ho tro ca 2 che do Mode A (Kham pha phim, keo tha, xem trailer) va Mode B (Phong thi nghiem truc quan, bieu do Jaccard, heatmap correlation).
2. **Graph Neural Networks (GNN / LightGCN):**
   - Tich hop mo hinh LightGCN hoac PinSage de hoc bieu dien ket hop giua cau truc do thi va ma tran tuong tac.
3. **Containerization & CI/CD:**
   - Dong goi toan bo he thong thanh Docker container da tang (FastAPI, SQLite, Nginx reverse proxy).

