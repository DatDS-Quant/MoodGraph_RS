# MoodGraph Phase 5: Production-Oriented Backend Platform & Storage Layer

## 1. Tong quan Pham vi (Executive Overview)
Phase 5 la giai doan kien truc va hoan thien nen tang Backend phuc vu cho he thong goi y phim MoodGraph. He thong tich hop toan dien cac mo hinh hoc may va do thi tri thuc duoc nghien cuu tu cac pha truoc vao mot kien truc phuc vu san sang cho san pham (Production-Oriented Architecture), bao gom:
- **Mode A: Movie Discovery & Personalization**: Tra cuu danh muc 62,423 phim, ho so tuong tac nguoi dung tu tap Train, goi y ca nhan hoa thoi gian thuc va he thong giai thich da chieu (Metapaths P1/P2/P3 va Latent Factor projection).
- **Mode B: Recommendation Lab**: Khong gian danh rieng cho chuyen gia dinh luong va nghien cuu sinh, ho tro so sanh da mo hinh song song (ALS Champion, Knowledge Graph, Hybrid RRF k=60, Hybrid Weighted, Popularity), tinh toan he so trung lap Jaccard va he so tuong quan thu hang Spearman, dong thoi cong khai day du bang ket qua kiem dinh offline Phase 4.
- **Data Persistence Layer**: Duy tri tinh bat bien (Read-Only) cua tap du lieu MovieLens 25M va luu tru trang thai tuong tac nguoi dung demo (Watchlist, Feedback Rating, So thich ca nhan, Session thi nghiem) thong qua SQLite che do WAL (Write-Ahead Logging).

---

## 2. Cau truc Thu muc Phase 5

```
MoodGraph/
├── recommender/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI Application voi Lifespan pre-warming
│   │   ├── dependencies.py         # Dependency Injection providers
│   │   ├── discovery_router.py     # Endpoints Mode A (Discovery & Serving)
│   │   ├── lab_router.py           # Endpoints Mode B (Lab & Comparison)
│   │   ├── interaction_router.py   # Endpoints SQLite Interactions
│   │   ├── system_router.py        # Health, Cache management
│   │   └── schemas.py              # Pydantic Schemas chuan hoa
│   ├── services/
│   │   ├── __init__.py
│   │   ├── catalog_service.py      # Nghiep vu danh muc & tim kiem phim
│   │   ├── user_profile_service.py # Nghiep vu ho so & lich su tuong tac
│   │   ├── explainability_service.py # Nghiep vu giai thich da chieu
│   │   ├── lab_service.py          # Nghiep vu so sanh da mo hinh
│   │   └── user_interaction_service.py # Nghiep vu tuong tac & dong bo cache
│   └── storage/
│       ├── __init__.py
│       ├── catalog_repo.py         # In-memory O(1) Catalog 62K movies
│       ├── user_history_repo.py    # Zero-leakage CSR index tap Train
│       ├── research_metrics_repo.py # Phuc vu ket qua danh gia offline
│       └── sqlite_state_repo.py    # SQLite WAL mode app_state.db
├── tests/
│   └── phase5/
│       ├── test_catalog_api.py
│       ├── test_user_profile_api.py
│       ├── test_lab_api.py
│       ├── test_interaction_api.py
│       ├── test_explainability_api.py
│       └── test_security_contracts.py
└── docs/
    └── phase5/
        ├── README.md
        ├── architecture.md
        ├── api_contracts.md
        ├── data_storage.md
        ├── security_review.md
        ├── test_report.md
        ├── integration_report.md
        ├── performance_report.md
        ├── scientific_integrity.md
        ├── known_limitations.md
        ├── phase5_gate_report.json
        └── FULL_HANDOVER_REPORT_FOR_CHATGPT.md
```

---

## 3. Cac Nguyen tac Co ban & Cam ket Chat luong
1. **Zero Data Leakage**: Tuyet doi khong doc hoac de lo du lieu tu tap Validation hoac Test vao ho so nguoi dung hoac bo loc lich su da xem.
2. **Zero Model Retraining**: Giu nguyen ven cac mo hinh da dong bang o Phase 3 va Phase 4 (Spark ALS Champion `ALS_R8_REG0.3_ITER10` va KG Graph).
3. **Scientific Honesty**: Bao toan ket luan khoa hoc thuc te rang tren tap cohort 200 users o tap Validation, KG-only dat do chinh xac xep hang cao hon ALS va Hybrid RRF.
4. **Pre-warmed Lifespan**: Nap truoc danh muc phim va chi muc CSR khi server khoi dong, triet tieu do tre khoi dong lanh xuong duoi 5ms o cache hit.
5. **No LaTeX / Dollar Signs**: Tuan thu chat che quy chuan Typography, de doc va hien thi hoan hao tren moi giao dien Markdown.
