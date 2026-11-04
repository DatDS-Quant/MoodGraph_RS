# BÁO CÁO KHẢO SÁT REPOSITORY (GIAI ĐOẠN 0 - REPOSITORY AUDIT)
> **Dự án:** MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark  
> **Nhiệm vụ:** Task 3B — Knowledge Graph Recommender  
> **Thời điểm khảo sát:** 2026-11-04  
> **Người thực hiện:** Senior Python & Knowledge Graph Engineer (AI Assistant)

---

## 1. TỔNG QUAN KIẾN TRÚC & MỤC TIÊU TASK 3B

MoodGraph là hệ thống gợi ý phim cá nhân hóa đa tầng gồm các khối:
1. **Dữ liệu nguồn:** MovieLens 25M (25,000,095 ratings, 162,541 users, 62,423 movies, 1,128 genome tags).
2. **PySpark ETL/EDA (Phase 1-4):** Xử lý tiền kỳ, kiểm tra chất lượng, phân chia dữ liệu theo giao thức User-wise Leave-1-Last.
3. **Mô hình song song (Phát triển độc lập):**
   - **Task 3A:** Spark MLlib ALS Collaborative Filtering.
   - **Task 3B (Nhiệm vụ này):** Knowledge Graph Recommender xây dựng trên Neo4j Community, sử dụng thuật toán tính điểm dựa trên đường đi đa bước (**Path-based KG Scoring: P1 Genre, P2 Genome, P3 Collaborative Graph Path**) cùng cơ chế trích xuất bằng chứng suy luận (**Explainable Evidence**).
4. **Khối 4 (Tương lai):** Hybrid Recommender kết hợp điểm số và hợp tập ứng viên (**Candidate Union**) giữa 3A và 3B.
5. **Khối 5-6:** Serving API (FastAPI) và Web UI (Next.js).

> [!IMPORTANT]
> **Ranh giới công việc Task 3B:**
> - Hoạt động độc lập hoàn toàn với Task 3A: Không import module ALS, không chờ latent factors, không phụ thuộc điểm ALS.
> - Không triển khai Hybrid Recommender trong phạm vi Task 3B.
> - Không tự ý thêm Actor/Director, GNN, Joint Embedding, hay Mood Ontology ngoài đặc tả.

---

## 2. CẤU TRÚC REPOSITORY HIỆN TẠI

Khảo sát cấu trúc tệp tại gốc repository:
```text
mood-graph/
├── .agents/
│   └── skills/
│       └── github-task-workflow/    # Untracked (Bảo toàn nguyên vẹn, không commit vào 3B)
├── .git/                            # Git metadata
├── data/
│   ├── moodgraph_processed_v1.0/    # Bộ dữ liệu Parquet đã xử lý và phân tách sạch
│   │   ├── core/                    # movies, links, tags, genome_tags, genome_scores
│   │   ├── features/                # movie_genres, tags_train
│   │   ├── splits/                  # train, validation, test
│   │   ├── manifest.json            # Manifest chi tiết kèm SHA-256 và row counts
│   │   └── test_results.json        # Báo cáo 8 bài kiểm tra chất lượng dữ liệu
│   ├── moodgraph_processed_v1.0.zip # File nén lưu trữ dữ liệu
│   └── .gitkeep
├── docs/
│   ├── data_eda.md                  # Báo cáo phân tích thăm dò dữ liệu PySpark (EDA)
│   ├── evaluation_protocol.md       # Giao thức User-wise Leave-1-Last và metric offline
│   └── TASK_3B_KNOWLEDGE_GRAPH.md   # Đặc tả kỹ thuật và hợp đồng nghiệm thu Task 3B
├── recommender/
│   ├── eda.py                       # Mã nguồn thực thi EDA bằng PySpark
│   └── .gitkeep
├── web/
│   ├── backend/                     # Khung FastAPI (.gitkeep)
│   └── frontend/                    # Khung Next.js (.gitkeep)
├── .gitignore                       # Cấu hình loại trừ data, secrets, venv, parquet...
├── HERMES.md                        # Sổ theo dõi tiến độ, quyết định kỹ thuật và rủi ro
└── README.md                        # Giới thiệu tổng quan dự án
```

### Các tài liệu tham khảo bổ sung ngoài repo:
- `../MoodGraph_KienThuc_KienTruc_HaiCheDo_CO_POSTER.docx`: Tài liệu kiến trúc hai chế độ và nền tảng đồ thị tri thức.
- `../MoodGraph_Task3B_KeHoach_BanGiao.docx`: Bản kế hoạch bàn giao chi tiết Task 3B giữa hai nhánh.

---

## 3. KHẢO SÁT DỮ LIỆU THỰC TẾ & DATA CONTRACT

Dữ liệu tiền xử lý nằm tại thư mục thực tế: `data/moodgraph_processed_v1.0/` (thay vì đường dẫn quy ước `data/processed/` trong một số văn bản dự thảo). Toàn bộ dữ liệu được lưu dưới dạng thư mục Parquet phân mảnh (Snappy compression).

### Bảng đối chiếu số liệu Manifest vs Thực tế:

| Dataset | Đường dẫn thực tế | Số dòng | Schema thực tế | Vai trò trong Task 3B |
| :--- | :--- | :---: | :--- | :--- |
| **Movies** | `core/movies` | 62,423 | `movieId: int, title: string, genres: string, genre_list: array<string>` | Node `(:Movie)` |
| **Movie Genres** | `features/movie_genres` | 107,245 | `movieId: int, genre: string` | Node `(:Genre)`, Cạnh `(:Movie)-[:IN_GENRE]->(:Genre)` |
| **Genome Tags** | `core/genome_tags` | 1,128 | `tagId: int, tag: string` | Node `(:GenomeTag)` |
| **Genome Scores** | `core/genome_scores` | 15,584,448 | `movieId: int, tagId: int, relevance: float` | Cạnh `(:Movie)-[:HAS_GENOME_TAG]->(:GenomeTag)` (Lọc Top-M) |
| **Train Split** | `splits/train` | 24,675,013 | `userId: int, movieId: int, rating: float, timestamp: bigint` | Node `(:User)`, Cạnh `(:User)-[:RATED]->(:Movie)` |
| **Val Split** | `splits/validation` | 162,541 | `userId: int, movieId: int, rating: float, timestamp: bigint` | **Chỉ dùng Validation/Tuning**. Cấm nạp vào Graph |
| **Test Split** | `splits/test` | 162,541 | `userId: int, movieId: int, rating: float, timestamp: bigint` | **Chỉ dùng Final Benchmark**. Cấm nạp vào Graph |
| **Tags Train** | `features/tags_train` | 1,074,090 | `userId: int, movieId: int, tag: string, timestamp: bigint, tag_clean: string` | Cạnh tùy chọn `(:User)-[:USER_TAGGED]->(:Movie)` |
| **Core Tags** | `core/tags` | 1,093,360 | `userId: int, movieId: int, tag: string, timestamp: bigint, tag_clean: string` | **Cấm dùng** xây graph để chống rò rỉ dữ liệu |

### Đánh giá chất lượng dữ liệu:
Tệp `test_results.json` xác nhận:
- 0 bản ghi trùng lặp `(userId, movieId)` trên toàn bộ 25M ratings.
- 0 tương tác rò rỉ giữa Train, Validation và Test.
- Toàn bộ 162,541 users đều có lịch sử Train $\ge 18$ ratings.
- Ranh giới thời gian tuân thủ nghiêm ngặt theo User-wise Leave-1-Last.

---

## 4. KHẢO SÁT MÔI TRƯỜNG KỸ THUẬT & HẠ TẦNG

- **Hệ điều hành:** Windows 11 (win32).
- **Python:** 3.11.9 (Microsoft Store distribution).
- **Bộ nhớ RAM hệ thống:**
  - Tổng RAM vật lý: 8,072,816 KB (~7.70 GB).
  - RAM khả dụng thực tế: ~674 MB – 1.0 GB (Mức tài nguyên rất eo hẹp).
- **Dung lượng ổ cứng:** Ổ C: còn trống 21.76 GB trên tổng số 250.84 GB.
- **Java Runtime:** OpenJDK 1.8.0_504 (Temurin 64-bit Server VM).
- **Docker:** Docker Desktop phiên bản 29.4.0 đã cài đặt; Docker Desktop Service hiện đang ở trạng thái `Stopped`.
- **Neo4j Status:** Chưa có dịch vụ Neo4j cục bộ chạy trên cổng mặc định 7687 / 7474.
- **Thư viện Python hiện có:** `pandas (2.3.1)`, `numpy (2.1.2)`, `networkx (3.6.1)`, `scipy (1.16.1)`, `fastapi (0.136.1)`, `scikit-learn (1.7.2)`.
- **Thư viện còn thiếu:** `pyarrow` (đọc Parquet tối ưu độc lập), `neo4j` (Official Python Driver), `pytest` (hệ thống kiểm thử tự động).

---

## 5. KHẢO SÁT GIT & QUẢN LÝ NHÁNH

- **Branch hiện tại:** `dev/duyndang`.
- **Commit gần nhất:** `8307de3 feat(eda): add PySpark EDA report, offline evaluation protocol, and HERMES memory tracker`.
- **Trạng thái Git:**
  - Tracked files: Sạch sẽ, không có thay đổi dở dang (`git diff --stat` rỗng).
  - Untracked files:
    - `.agents/`: Chứa skill `github-task-workflow` nội bộ. **Phải bảo toàn, không xóa, không đưa vào commit Task 3B theo chỉ thị của người dùng**.
    - `docs/TASK_3B_KNOWLEDGE_GRAPH.md`: File đặc tả Task 3B.
- **Quy tắc làm việc:**
  - Tạo branch `feature/kg-3b` từ điểm hiện tại.
  - Tuyệt đối không can thiệp vào mã nguồn nhánh 3A (`recommender/als/`), pipeline tiền xử lý, hay frontend/backend.
  - Không tự ý merge vào `main` hoặc push trực tiếp `main`.

---

## 6. CÁC TÀI LIỆU CÒN THIẾU & ĐỐI CHIẾU

Theo danh mục bắt buộc tại Mục 2 của Master Prompt:
1. `docs/TASK_3B_KNOWLEDGE_GRAPH.md` $\rightarrow$ **Đã có và đã đọc đầy đủ**.
2. `MoodGraph_KienThuc_KienTruc_HaiCheDo_CO_POSTER.docx` $\rightarrow$ **Đã tìm thấy tại thư mục cha `../` và đã trích xuất nội dung**.
3. `MoodGraph_Task3B_KeHoach_BanGiao.docx` $\rightarrow$ **Đã tìm thấy tại thư mục cha `../` và đã trích xuất nội dung**.
4. `README.md` $\rightarrow$ **Đã có và đã đọc**.
5. `HERMES.md` $\rightarrow$ **Đã có và đã đối chiếu**.
6. `docs/evaluation_protocol.md` $\rightarrow$ **Đã có và đã đối chiếu**.
7. `docs/data_dictionary.md` $\rightarrow$ **THIẾU TRONG REPO**. Tuy nhiên toàn bộ schema, kiểu dữ liệu và mô tả trường đã được ghi nhận đầy đủ, chuẩn xác trong `manifest.json`.
8. `docs/preprocessing_report.md` $\rightarrow$ **THIẾU TRONG REPO**. Toàn bộ số liệu kiểm định thực tế đã được lưu chi tiết trong `test_results.json` và `docs/data_eda.md`.
9. `data/processed/manifest.json` $\rightarrow$ Tồn tại tại vị trí thực tế `data/moodgraph_processed_v1.0/manifest.json`.
10. `.gitignore` $\rightarrow$ Đã đối chiếu (bảo vệ nghiêm ngặt các file Parquet, CSV, Zip, và `.env`).
11. `.agents/skills/github-task-workflow/SKILL.md` $\rightarrow$ Đã đọc và nắm rõ quy trình Git/PR chuẩn.

---

## 7. CÁC THÁCH THỨC KỸ THUẬT & PHƯƠNG ÁN XỬ LÝ (RISK MITIGATION)

1. **Rủi ro cạn kiệt tài nguyên RAM (8 GB RAM vật lý, ~700 MB rảnh):**
   - *Thách thức:* Không thể nạp toàn bộ 24.67 triệu tương tác train và 15.58 triệu quan hệ genome vào RAM hoặc instance Neo4j cục bộ mà không bị OOM.
   - *Giải pháp:*
     - Tuyệt đối tuân thủ chiến lược chia tầng kiểm thử của Gate 0 - Gate 5.
     - Xây dựng **Synthetic Graph Fixture** hoàn chỉnh (tính tay) để kiểm thử toàn diện tính đúng đắn của schema, importer idempotency, metapaths P1/P2/P3, và mutation testing.
     - Trên dữ liệu thật: Triển khai chế độ **Pilot Subgraph** trên một cohort người dùng xác định (100–500 users) kèm chính sách lọc Top-M Genome Tags ($M=10, 20$). Báo cáo minh bạch phạm vi pilot, không tuyên bố nạp toàn bộ 25M nếu tài nguyên không cho phép.
2. **Khả năng chạy Neo4j trên môi trường máy:**
   - Cần thiết lập driver Neo4j, khởi động Neo4j qua Docker hoặc kết nối tới instance Neo4j Community/Desktop nếu có sẵn; đồng thời xây dựng kiến trúc mã nguồn module hóa với driver adapter có cơ chế kiểm tra kết nối (`verify_connectivity`) và chế độ test fixture độc lập.
3. **Phân định rõ ràng Path-based Evidence:**
   - Mỗi recommendation phải kèm danh sách `evidence` có thể truy xuất ngược từ graph, không dùng văn bản suy diễn ngẫu nhiên.

---

## 8. KẾ HOẠCH TRIỂN KHAI THEO STAGE GATES

- **Gate 0:** Thiết lập môi trường Python (`neo4j`, `pyarrow`, `pytest`), cấu hình `.env.example`, `recommender/kg/README.md`, `docs/kg/architecture.md`, và script `scripts/kg_smoke_test.py`.
- **Gate 1:** Định nghĩa constraints, viết bộ sinh synthetic fixtures (`tests/kg/fixtures/`), triển khai `recommender/kg/import_graph.py` theo cơ chế `UNWIND` + `MERGE` có batching và transaction, kiểm thử idempotency 2 lần chạy.
- **Gate 2:** Hiện thực thuật toán `Path-based Weighted Evidence Scorer` (P1, P2, P3), trích xuất bằng chứng (evidence), lọc phim đã xem, kiểm thử mutation test.
- **Gate 3:** Pilot MovieLens thật tăng dần (cohort 100–500 users), lọc Top-M genome, ghi nhận thông số tài nguyên và hiệu năng.
- **Gate 4:** Đánh giá Validation-only theo giao thức User-wise Leave-1-Last, tiến hành ablation study (Genre-only vs Genre+Genome vs Full P1+P2+P3), đo HR@K, NDCG@K, Coverage@K.
- **Gate 5:** Hoàn thiện bộ báo cáo (`import_report.md`, `model_report.md`, `testing_report.md`, `integration_contract.md`), chuẩn bị Git branch và Pull Request draft chờ maintainer phê duyệt.

