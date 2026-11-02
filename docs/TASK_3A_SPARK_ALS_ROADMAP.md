# MOODGRAPH | TASK 3A: SPARK ALS RECOMMENDER

> **MASTER ROADMAP & IMPLEMENTATION CONTRACT CHO GOOGLE ANTIGRAVITY**  
> Dự án: **Personalized Movie Recommendation using Knowledge Graphs and Apache Spark**  
> Nhánh thực hiện: **3A – Spark MLlib ALS / Collaborative Filtering**  
> Phát triển song song với **3B – Knowledge Graph**, tích hợp về sau tại **Khối 4 – Hybrid Recommendation**.  
> Trạng thái tài liệu: **SPEC / KẾ HOẠCH – CHƯA PHẢI BẰNG CHỨNG CÁC MODULE ĐÃ CHẠY**  
> Phiên bản hợp đồng: `3A-plan-v1.0` | Ngày soạn: `2026-10-27`  
> **Đối tượng đọc:** teammate, chủ nhánh ALS, Technical Mentor, Google Antigravity coding agent.

---

## 0. MỆNH LỆNH ƯU TIÊN CAO NHẤT CHO ANTIGRAVITY

**ĐỌC HẾT FILE NÀY TRƯỚC KHI VIẾT CODE. CHỈ LÀM MODULE ĐƯỢC NGƯỜI DÙNG GIAO RÕ.** Việc đọc roadmap M00–M10 **KHÔNG** đồng nghĩa được triển khai tất cả. Nếu người dùng chỉ yêu cầu M00, hoàn thành M00, tự kiểm thử, báo cáo, **DỪNG**. Không tự tiến tới M01. Mỗi module cần được chủ dự án/Technical Mentor review trước khi đi tiếp.

Quy tắc tuyệt đối:

1. **Không giả lập kết quả thực nghiệm**: không tự tạo metrics, không cài recommendation hardcode, không dùng kết quả synthetic làm số liệu MovieLens thật. Phân biệt `EXPECTED`, `OBSERVED`, `PASS`, `FAIL`, `BLOCKED`.
2. **Không chạm vào nguồn**: không sửa `data/raw/`, `data/processed/`, `recommender/preprocess.py`, `recommender/validate_data.py`, hoặc dữ liệu split và manifest Phase 4. Nếu phát hiện lỗi data, ghi bug report và dừng tác vụ phụ thuộc.
3. **Không chạm nhánh 3B**: không chỉnh `recommender/kg/`, Neo4j, `docs/kg/`, hay graph scoring. Không tự thêm GNN, embeddings KG, vector DB, frontend/backend vào 3A.
4. **Git an toàn**: chỉ làm trên `feature/als-3a`; không push `main`, không merge, force-push, reset, stash, đổi branch hoặc commit/push khi chưa có hướng dẫn/cho phép. Nếu working tree có thay đổi chưa rõ nguồn gốc, báo trước khi thao tác có nguy cơ ghi đè.
5. **Chống leakage**: chỉ `splits/train` được `fit()` ALS, tính Popularity hoặc xây user-history train. Validation chỉ để chọn tham số. Test chỉ mở ở M08 **sau khi chốt cấu hình**. `core/tags`/Tag Genome **không** là đầu vào của ALS-only.
6. **Bám tài nguyên thật**: máy tham chiếu Windows 11, Ryzen 5 7530U (6C/12T), RAM 16 GB, PySpark theo manifest. Chạy toy/subset trước full data. Không `collect()` toàn bộ ratings, không `toPandas()` bảng lớn, không tạo dense 162,541 × 62,423 score matrix.
7. **Tài liệu và tests là phần sản phẩm**: mỗi module phải có code có thể chạy, tests thật, log/report, hướng dẫn tái chạy, nêu hạn chế. Một file viết xong nhưng chưa chạy **không** là PASS.
8. **Cập nhật tiến độ có kiểm soát**: ghi riêng `docs/3a/` sau mỗi module. Không tự thay `HERMES.md` nếu teammate đang chỉnh; chỉ gửi dòng trạng thái đề xuất để maintainer hợp nhất sau review.
9. **Giữ tính độc lập**: ALS-only phải train, score và trả Top-N độc lập với KG. Tích hợp Hybrid để giai đoạn khác. Không giới hạn ứng viên KG chỉ trong top ALS.
10. **Không tự kết luận ALS thắng**: baseline có thể thắng; phải giữ và giải thích mọi kết quả thực nghiệm thực.

**Thứ tự ưu tiên khi có mâu thuẫn**: (1) an toàn nguồn dữ liệu/Git và ranh giới train-test; (2) `docs/evaluation_protocol.md`, `docs/data_dictionary.md`, manifest/code thực; (3) roadmap này; (4) suy đoán riêng của agent. Nếu protocol thực tế khác roadmap, **báo conflict, không tự sửa hoặc bỏ qua**.

---

## 1. BỨC TRANH TỔNG THỂ VÀ ĐIỂM KẾT THÚC 3A

```text
                 PHASE 4: APPROVED DATA PIPELINE
        data/processed/splits/{train,validation,test}/
                             |
              +--------------v--------------+
              |   TASK 3A – SPARK ALS        |
              | M00-03 contract/eval/baseline|
              | M04-05 toy ALS / full fit    |
              | M06-07 Top-N / tuning        |
              | M08-09 final eval / diagnostic|
              | M10 delivery and PR         |
              +--------------+--------------+
                             |
            userId, movieId, raw_score, rank
                             |
                      KHỐI 4: HYBRID
                             ^
              TASK 3B KG (teammate, independent)
```

### 1.1. Định nghĩa hoàn thành (Definition of Done)

3A chỉ hoàn thành khi có: (a) Spark ALS-only fit thật chỉ từ Train; (b) lưu/nạp lại model; (c) `recommend_als(user_id, top_n, ...)` trả Top-N chưa tương tác, score/rank ổn định; (d) baseline Popularity; (e) metric functions unit-tested; (f) chọn cấu hình trên Validation, Test được dùng một lần khi đã khóa; (g) báo cáo thực nghiệm đủ metadata và giới hạn; (h) model/inference contract tương thích 3B/Hybrid; (i) PR được người duyệt xem xét. **Không bắt buộc ALS phải thắng Popularity.**

### 1.2. Trách nhiệm chia nhánh

| 3A (em) | 3B (teammate) | Khối 4 (sau này) |
|---|---|---|
| `ratings_train` → ALS factors/score | Train+Movie/Genre/Genome → KG paths/score | Union ALS/KG candidates, normalize, fuse |
| Popularity baseline, evaluation infrastructure | KG-only path scoring + real evidence | Validate fusion weights |
| Model artifact, Top-N, cold-start diagnostics | Neo4j graph, importer, graph tests | Hybrid ranking, explainability/UI/API |
| `raw_score` thường gần thang rating nhưng không giới hạn [0.5,5] | `raw_score` KG có thang riêng | Không cộng raw scores trực tiếp |

### 1.3. Không nằm trong phạm vi 3A

- Không huấn luyện KG, build graph, NLP, Mood Ontology, GNN, recommender dựa trên poster/trailer.
- Không tự crawl IMDb/TMDb.
- Không làm full website/UI/API sản phẩm (chỉ module Python đơn giản & output contract).
- Item-Based CF và Content-Based là **mô hình đối chứng mở rộng thuộc workstream riêng**, không chèn vào 3A nếu chưa có yêu cầu mới. M03 Popularity là baseline bắt buộc cho 3A.
- Không bắt buộc xây cluster Spark nhiều node. `local[*]` là Spark local song song, **không được mô tả là cluster nhiều máy**.

---

## 2. NGUỒN DỮ LIỆU & HỢP ĐỒNG ĐẦU VÀO

Các đường dẫn tính từ **root repo**. Các đường dẫn Parquet là **thư mục**, không nhất thiết là file `train.parquet` đơn lẻ.

| Nguồn | Số dòng kỳ vọng từ báo cáo Phase 4 | Quyền sử dụng ở 3A |
|---|---:|---|
| `data/processed/splits/train/` | 24,675,013 | **Fit ALS**, compute Popularity, train user histories |
| `data/processed/splits/validation/` | 162,541 | **Tuning** / chọn mô hình, không fit |
| `data/processed/splits/test/` | 162,541 | **Final reporting** chỉ sau frozen choice |
| `data/processed/core/movies/` | 62,423 | Catalog/candidate metadata và join title, không fit ALS |
| `data/processed/manifest.json` | Metadata | Check version, schema, checksums |
| `data/processed/test_results.json` | Audit | Kiểm tra trạng thái Phase 4 |
| `data/processed/features/tags_train/` | 1,074,090 | **Không dùng** trong ALS-only; dành cho KG |
| `data/processed/core/genome_scores/` | 15,584,448 | **Không dùng** trong ALS-only; dành cho KG/content baseline |

**Các số ở trên là EXPECTED, không phải observed trên máy agent mới.** Đọc lại, xác minh bằng Spark và ghi observed. Nếu dữ liệu thiếu, M00/M01 đánh dấu `BLOCKED`, được tạo toy fixture để học, **không tạo số liệu ảo hoặc tự tải/phát tán data**.

Schema split bắt buộc theo Data Dictionary: `userId:int`, `movieId:int`, `rating:float`, `timestamp:long`. Movie schema tối thiểu `movieId`, `title`, `genres`, `genre_list` (kiểm chứng thực tế).

### 2.1. Giao thức đánh giá phải được áp dụng chính xác

- Giao thức chính: **User-wise Leave-1-Last** với `(timestamp ASC, movieId ASC)`, mỗi user một Validation và một Test.
- **Validation ranking**: khi dự đoán tương tác Val, history/seen items chỉ dùng `Train_u`; mẫu test chưa được dùng.
- **Test ranking**: khi dự đoán tương tác Test, danh sách seen items loại cả `Train_u ∪ Val_u`, **nhưng ALS factors vẫn fit từ Train**, không tự cập nhật factors bằng Val. Validation không được chèn vào train để “hiểu user tốt hơn” nếu chưa có protocol mới.
- **Catalog ứng viên khái niệm chung:** Movie IDs trong `core/movies` trừ các seen items theo giai đoạn. Không được xây tập ứng viên từ labels Test hoặc giới hạn về phim test-positive.
- **ALS scoreability:** ALS chỉ có item factors cho phim xuất hiện trong Train; không có factor → **unscorable**, không tự thêm Popularity vào `ALS-only`. Nếu target Test unscorable, đánh giá ALS-only **miss** và báo coverage (không drop user khỏi benchmark chính).
- **Full-catalog intent:** xếp trên toàn bộ danh mục hợp lệ/scoreable của từng mô hình mà không lấy 99 negative samples trá hình. Báo rõ `catalog_size`, `scorable_count`, `user_batch_size`. Không tạo full dense matrix cho tất cả users.
- **Relevance threshold** ban đầu: `rating >= 3.5`. Một user có test/val item dưới ngưỡng không có positive observed target, không được lén coi đó là negative truth cho toàn catalog. Báo metric **primary trên Positive-Target Cohort**, cohort được chọn định trước bằng quy tắc không nhìn label; group all-users chỉ là diagnostic. Với user không có positive target, Recall là không xác định, không dùng phép chia 0.
- **Giới hạn học thuật:** Leave-1-Last không loại trừ cross-user temporal leakage. Tag Genome có post-hoc leakage, nhưng **ALS-only không dùng Genome**. One-held-out rating chỉ đánh giá khả năng tìm một phim đã được user đánh giá, không chứng minh được user sẽ thích tất cả phim không đánh giá.
- **Tie-break cuối cùng**: sort `raw_score DESC, movieId ASC`, xử lý NULL/NaN/Inf và scores ngoài [0.5,5] minh bạch.
- **Randomness**: cố định seed của cohort, model và các sampling phụ; lưu seed trong report/config.

### 2.2. Giao diện đầu ra chung với 3B

| Field | Kiểu / nội dung | Yêu cầu |
|---|---|---|
| `userId` | int | ID gốc MovieLens |
| `movieId` | int | ID gốc, join được với KG & catalog |
| `raw_score` | float/double | Điểm ALS chưa chuẩn hóa, finite |
| `rank` | int, từ 1 | Duy nhất trong từng user/model, theo score desc + ID asc |
| `model_name` | string | `ALS` (không ghi `HYBRID`) |
| `model_version` | string | Có phiên bản run/model rõ ràng |
| `run_id` | optional string | Liên hệ experiment manifest |

Đối với KG, 3B có `model_name='KG_PATH'`, `evidence_json`. Hai nhánh có thể thống nhất phần giao nhau `(userId, movieId, raw_score, rank, model_name)`. Không ép KG phải có factor; không ép ALS phải sinh evidence paths giả. Tích hợp ở Khối 4 theo **candidate union**, không chỉ KG rerank Top-100 của ALS.

---

## 3. CẤU TRÚC FILE VÀ CÁCH CHẠY ĐỀ XUẤT

```text
MoodGraph/
├── recommender/
│   ├── als/
│   │   ├── __init__.py
│   │   ├── config.py                 # M00/M01, cấu hình + seed
│   │   ├── data_loader.py            # M01
│   │   ├── evaluator.py              # M02
│   │   ├── popularity.py             # M03
│   │   ├── toy_als.py                # M04
│   │   ├── train_als.py              # M05/M07
│   │   ├── recommend.py              # M06
│   │   ├── tuning.py                 # M07
│   │   ├── benchmark.py              # M08
│   │   ├── diagnostics.py            # M09
│   │   └── delivery.py               # M10
├── tests/
│   └── als/                         # Synthetic fixtures + pytest/unittest tests
├── docs/
│   └── 3a/
│       ├── M00_contract.md
│       ├── M01_data_audit.md
│       ├── M02_evaluator_report.md
│       ├── ...
│       └── M10_delivery.md
├── data/processed/                   # READ-ONLY cho 3A
└── HERMES.md                         # Không chỉnh đồng thời với 3B
```

Đây là **đề xuất file layout**, không bắt buộc tạo tất cả file ở M00. Mỗi module chỉ tạo code/dirs cần thiết và không được preempt công việc module sau.

- `tests/als/`: ưu tiên framework đã có trong repo; không tự cài dependency chỉ để đẹp.
- `artifacts/als/` hoặc `models/als/`: nơi lưu model & benchmark thật, mặc định **gitignored**, kiểm tra `.gitignore` trước khi ghi.
- `docs/3a/`: các report Markdown/log cấu hình có thể commit khi duyệt, không nhét datasets/model binary vào repo.
- Paths phải hỗ trợ project root tương đối; cấu hình Windows riêng (Python env/driver bind) không hardcode tên người dùng.

---

## 4. QUY TRÌNH TRIỂN KHAI TỪNG MODULE (STAGE-GATE)

```text
Đọc module + học khái niệm → triển khai tối thiểu → chạy toy/unit test
→ thử real subset → chạy full khi thích hợp → ghi observed metrics/log
→ agent tự audit + câu hỏi phản biện → Mentor kiểm kê
→ em giải thích lại được → PASS → module kế tiếp.
```

**Hai chữ PASS riêng:** `ENGINEERING_PASS` (code/tests có bằng chứng) và `LEARNING_PASS` (chủ nhánh trả lời được câu hỏi). Nếu một trong hai chưa đạt, module ở `PENDING_REVIEW` dù code có chạy.

### Mẫu báo cáo chung bắt buộc sau từng module

```text
MODULE: Mxx – tên
BRANCH / COMMIT: ... (nếu chưa commit, ghi working-tree state)
STATUS: PASS / FAIL / BLOCKED / PENDING_REVIEW
INPUT DATASET VERSION / MANIFEST HASH: ...
FILES CREATED/MODIFIED: ...
COMMANDS ACTUALLY EXECUTED: ...
UNIT TESTS: passed/failed/skipped, lý do skipped
INTEGRATION TESTS / REAL DATA CHECKS: ...
OBSERVED COUNTS / METRICS / DURATIONS: ... (không bịa)
MATERIAL LIMITATIONS / OPEN RISKS: ...
LEARNING QUESTIONS FOR OWNER: ...
CHANGES TO SHARED CONTRACTS: none / request approval
NEXT MODULE: chỉ được gợi ý, không tự thực hiện
```

---

# M00 – PROJECT CONTRACT, GIT SAFETY & ENVIRONMENT

**Mục tiêu:** Khóa đúng phạm vi 3A, xác minh đầu vào, chọn cấu trúc file, đồng bộ contract với teammate 3B. Không train, không baseline.

**Kiến thức em phải nắm:** raw vs processed; Train/Val/Test; data contract vs model contract; vì sao latent factor ALS không đòi genre/tag; 3A độc lập với 3B nhưng có điểm giao `userId/movieId`.

**Inputs:** `README.md`, `HERMES.md`, `.gitignore`, `docs/evaluation_protocol.md`, `docs/data_dictionary.md`, `docs/preprocessing_report.md`, `data/processed/manifest.json` và `TASK_3B_KNOWLEDGE_GRAPH.md` nếu hiện diện (chỉ đọc interface, không sửa).

**Việc Antigravity phải làm:**

1. Hiện Git branch, clean/dirty, remote/tracking; nếu chưa ở `feature/als-3a`, xác minh điều kiện an toàn trước khi đề xuất tạo/chuyển branch.
2. Đọc môi trường Python/Java/PySpark/SparkSession; ghi lại cấu hình thành công, tránh cài mới khi chưa cần.
3. Kiểm tra path Parquet và một phần schema, đối chiếu manifest; nếu thiếu artifact báo `BLOCKED` thay vì viết model giả.
4. Viết output contract 3A, thống nhất cột chung với 3B, quy tắc seen-item filters và cold-start policy.
5. Tạo `docs/3a/M00_contract.md` (không tạo mã các module khác).

**Bài kiểm thử bắt buộc:** kiểm tra file manifest, path, schema, ID types; SparkSession tạo/đóng thành công; `.gitignore` không theo dõi Parquet/artifacts. Ghi kết quả thật.

**Definition of PASS:** chuẩn giao tiếp, môi trường, phạm vi file rõ, không thay đổi data hoặc KG; blockers được nêu; owner đồng ý.

**Câu hỏi bảo vệ:** (1) Tại sao cùng `movieId` giúp ghép ALS & KG? (2) Tại sao không train bằng Test? (3) Nếu teammate đổi tên ID thành `film_id`, chuyện gì xảy ra?

**Dừng tại đây** nếu được giao M00.

---

# M01 – DATA LOADER & ALS INPUT AUDIT

**Mục tiêu:** Xây loader sạch, xác định đúng tập user/item đủ điều kiện để ALS học, thống kê metadata và cold-start trước training.

**Kiến thức:** sparse user–item matrix, observed vs unobserved, distinct users/items, train-only coverage; biết giải thích vì sao 99% sparsity không đồng nghĩa 99% điểm 0.

**Files dự kiến:** `recommender/als/data_loader.py`, `tests/als/test_data_loader.py`, `docs/3a/M01_data_audit.md`.

**Bước thực hiện:**

1. Dùng PySpark đọc `train/validation/test/movies` có explicit checks schema và null. Không pandas trên full data.
2. Validate các ID numeric, rating trong `{0.5,...,5.0}`, duplicate key và full catalog membership. Phân biệt null và zero.
3. Compute user count, train-known movie count, min/median/p95 rating counts (có thể dùng approxPercentile), train cold items, Val/Test target missing factor count.
4. Phân biệt `train_movie_set` và `catalog_movie_set`; đếm phim chỉ có rating Val/Test, phim zero rating toàn bộ.
5. Implement predictable path handling, close SparkSession, no unexpected write.

**Tests:** synthetic fixture 2–4 users xác minh counts, null invalid, missing movie references, empty dataset, schema mismatches, no silent data drop. Real Parquet counts đối chiếu expected nhưng report observed.

**PASS:** loader đọc đúng Parquet, trả DataFrames với schema được xác minh; báo cold-start counts chính xác; không sửa dữ liệu; không dùng val/test để fit.

**Câu hỏi bảo vệ:** (1) Tại sao phim không có rating Train vẫn hiện diện trong `movies`? (2) Cold movie khác phim ít rating? (3) Từ ratings dạng triplet hình dung ma trận thưa như thế nào?

---

# M02 – EVALUATION ENGINE & HAND-CALCULATED TESTS

**Mục tiêu:** Có bộ đo đúng **trước khi** train ALS để tránh chọn thước đo theo kết quả mong muốn.

**Kiến thức:** rating prediction vs Top-N ranking; HR@K, NDCG@K, MRR@K, Precision@K, Recall@K, Catalog Coverage; cohort denominator; một positive/test user; candidate pool và seen filtering.

**Files:** `recommender/als/evaluator.py`, `tests/als/test_evaluator.py`, `docs/3a/M02_evaluator_report.md`.

**Bước thực hiện:**

1. Viết pure metric functions chạy được với fixture synthetic, tách khỏi PySpark (có thể thêm adapter Spark cho batch user).
2. Trường hợp 1 positive duy nhất, đứng ở rank `j <= K`: `HR@K=1`, `Recall@K=1`, `Precision@K=1/K`, `NDCG@K=1/log2(j+1)`, `MRR@K=1/j`. Không xuất hiện => 0; nếu không có positive target thì **không xác định Recall/NDCG theo positive-cohort**, phải report `excluded_nonpositive_count`.
3. Xác minh K=5/10/20; tie break; duplicates; absent predictions, empty list, K>list length, score NaN/Inf, unknown user.
4. Define **Positive-Target Cohort** primary (positive `rating >=3.5`), báo kích thước và phân phối; all-user diagnostic tách rời, không giả Recall là metric hợp lệ khi denominator=0.
5. Catalog Coverage: unique recommended movieIds / fixed eligible catalog size; báo cả coverage của ALS factor catalog để so sánh công bằng.
6. Có function đảm bảo item được đánh giá là thực sự nằm trong candidate pool theo từng stage.

**Hand-check phải có trong tests:**

- User có một positive movie tại vị trí 3 của Top-5: HR=1, Recall=1, P=0.2, NDCG≈0.5, MRR≈0.3333.
- User positive không xuất hiện Top-5: metrics hit = 0.
- User giữ rating=2.0: không có observed positive, loại khỏi positive-cohort denominator; không gọi bất kỳ unobserved item nào là true negative.
- Test candidate excludes Train ∪ Validation; Val candidate excludes Train.

**PASS:** các metric khớp tính tay; chạy test; không rò rỉ Test vào khâu tuning; output phải gồm denominator/user counts.

**Câu hỏi bảo vệ:** (1) RMSE tốt có chắc Top-N tốt không? (2) NDCG khác HR thế nào? (3) Vì sao Recall và HR trên một held-out positive có thể giống nhau? (4) Có thể gọi phim không rating là phim bị ghét không?

---

# M03 – GLOBAL POPULARITY BASELINE

**Mục tiêu:** Một recommender thật không cá nhân hóa để kiểm chứng toàn bộ luồng train → Top-N → evaluator.

**Kiến thức:** global popularity, count-vs-average-rating bias, baseline, long-tail, filtering seen items; sự khác nhau giữa candidate generation và personalization.

**Files:** `recommender/als/popularity.py`, `tests/als/test_popularity.py`, `docs/3a/M03_popularity_report.md`.

**Bước thực hiện:**

1. Đếm `rating_count` theo `movieId` **chỉ** từ Train; baseline chính là **rating count** (không tự trộn với Val/Test). Tie break `count DESC, movieId ASC`.
2. Sinh Top-N cho user sau khi trừ lịch sử phù hợp (Train đối với Val, Train+Val đối với Test).
3. Nếu trên catalog có phim chưa bao giờ rated, ghi rõ chúng không vào popularity rank hoặc có score 0 theo config, đảm bảo không dùng Val/Test để tạo popularity stats.
4. Tích hợp với M02 trên synthetic và một pilot Validation; không mở Test để thử nghiệm trước M08.
5. Save lightweight artifact (sorted popularity list + metadata), không lưu observed hidden ratings.

**Tests:** known popularity counts fixture; tie determinism; no seen items; insufficient candidates; user without history; repeatability.

**PASS:** có recommend function thật, metric Validation thực, không dùng Test; log coverage/timing.

**Câu hỏi bảo vệ:** (1) Popularity có cá nhân hóa không? (2) Vì sao count popularity có bias? (3) Nếu Popularity thắng ALS, phải làm gì?

---

# M04 – ALS THEORY, TOY FIT & LATENT FACTOR INSPECTION

**Mục tiêu:** Em phải hình dung được toán học và cách Spark học factors trên toy data trước khi train 25M ratings.

**Kiến thức cốt lõi:** explicit MF, latent factors, dot product, objective `Σ(r_ui - p_u·q_i)^2 + regularization`, alternating solve users/items, `rank`, `regParam`, `maxIter`, cold-start.

**Files:** `recommender/als/toy_als.py`, `tests/als/test_toy_als.py`, `docs/3a/M04_als_foundations.md`.

**Bước thực hiện:**

1. Tạo fixture synthetic (4–8 users, 5–10 movies, diverse ratings), có một cặp user/movie chưa rating và một unseen item.
2. Fit Spark ALS với `implicitPrefs=False`, cấu hình rank nhỏ (ví dụ 2/3), seed cố định. Đừng coi những factor có nghĩa sẵn “action/romance”; chúng được học tự động và không định danh ngữ nghĩa.
3. In userFactors/itemFactors của fixture nhỏ, chỉ minh họa số chiều và ID; tính dot product thủ công cho một cặp rồi so với Spark `transform()` trong tolerance hợp lý.
4. Minh họa hai loại cold-start: user chưa từng train và movie chưa từng train; kiểm tra NaN/drop behavior rõ ràng.
5. Giải thích vì sao vector gần nhau trong Euclidean space **không thay thế được** điều kiện `p_u·q_i` cao.
6. Lưu toy report có phương trình, dữ liệu/param, bảng minh họa thật, không ngụ ý factors có nhãn genre.

**Tests:** factor vectors đúng rank, finite; dot≈Spark prediction, known→score; unseen→unscorable; repeat same seed within tolerance. Toy output không mang sang bộ kết quả chính.

**PASS:** code toy chạy, đối chiếu dot thành công, chủ nhánh giải thích được ALS mà không nhìn code.

**Câu hỏi bảo vệ:** (1) Vì sao ALS không cần movies.csv? (2) Latent factor là gì, có phải genre không? (3) Tại sao unknown ≠ 0? (4) Tham số regParam lớn quá có hậu quả gì? (5) ALS cập nhật 2 bảng factors luân phiên nghĩa là gì?

---

# M05 – SPARK ALS TRAINING ON REAL TRAIN SPLIT

**Mục tiêu:** Fit ALS-only trên `splits/train`, lưu/nạp model có kiểm thử, không dùng Test.

**Kiến thức:** Spark distributed DataFrames, explicitPrefs, RDD vs DataFrame (đủ để giải thích), partition, shuffle, model persistence, reproducibility, single-machine Spark vs cluster.

**Files:** `recommender/als/train_als.py`, `recommender/als/config.py`, `tests/als/test_training.py`, `docs/3a/M05_training_report.md`.

**Bước thực hiện:**

1. Train pilot trên user cohort/subset **lấy từ Train**; chỉ chuyển full khi pilot không OOM/timeout. Nếu tạo subset, ghi user/item filtering effect; tuyệt đối không gọi pilot là full model.
2. Thiết lập `ALS(userCol='userId', itemCol='movieId', ratingCol='rating', implicitPrefs=False, rank=..., regParam=..., maxIter=..., seed=..., coldStartStrategy='nan'...)`. Tránh dùng `drop` để tự che tỷ lệ unscorable trong scoring/eval.
3. Cấu hình Spark local cẩn trọng, ghi `driver.memory`, `spark.sql.shuffle.partitions`, AQE, số threads, training time, training user/item counts. Không suy ra speedup Big Data từ 1 run.
4. Save model to versioned gitignored path, load lại Spark ALSModel. Kiểm tra một tập (userId, movieId) warm có prediction trước/sau load tương đương.
5. Ghi model metadata gắn với manifest ID và training config, không publish artifacts khi chưa rõ quyền chia sẻ.

**Tests:** model factors không rỗng; factor user/items count phù hợp observed Train; save/load score parity; inputs chỉ Train; negative/unknown user behavior; no raw write; recoverable failure reports.

**PASS:** mô hình thật fit thành công (pilot hoặc full ghi đúng nhãn), artifact nạp lại được; nếu chỉ pilot thì M05 trạng thái **PARTIAL**, chưa hoàn tất full-training gate.

**Câu hỏi bảo vệ:** (1) Spark MLlib chạy trên local[*] có phải multi-node không? (2) ALS lưu gì? (3) Vì sao scores có thể vượt 5.0? (4) ALS có cần normalize genre không?

---

# M06 – ALS TOP-N CANDIDATE GENERATION & SEEN FILTER

**Mục tiêu:** Biến factors thành sản phẩm recommender độc lập, không chỉ `model.transform` vài dòng.

**Kiến thức:** inference, candidate generation, ranking, recall, seen-item filtering, over-fetch, cold-start item factor coverage, batch vs online inference.

**Files:** `recommender/als/recommend.py`, `tests/als/test_recommend.py`, `docs/3a/M06_topn_report.md`.

**Bước thực hiện:**

1. Định nghĩa interface `recommend_als(user_id, top_n, stage='validation'|'test', model_version=...)` và batch equivalent. `stage` quyết định seen-history (Val: Train; Test: Train∪Val).
2. Sinh ALS candidate scores từ userFactors × itemFactors hoặc Spark recommendation APIs; không dùng genre/genome để ghi đè ALS rank.
3. **Quan trọng:** `recommendForUserSubset(top_n)` rồi mới lọc seen items có thể không đủ Top-N. Chọn một cách đúng: full-score per bounded user batch + anti-join seen + top-K, hoặc over-fetch tăng dần **có kiểm chứng**. Ghi rõ exact vs approximate và coverage. Đối với offline full-catalog benchmark, cần ranking chính xác trong vùng item scoreable; không gọi over-fetch nhỏ là full-catalog nếu chưa chứng minh đủ ứng viên.
4. Sort `raw_score DESC, movieId ASC`, loại NaN/Inf, loại item seen, duplicate. Ghi thống kê khả năng score và số user thiếu đủ ứng viên.
5. Cho phép `movie title` join từ `core/movies` **chỉ để display**, không ảnh hưởng điểm.
6. Xuất per-user candidates với hợp đồng đã khóa; không normalizing với KG ở 3A.

**Tests:** exact toy dot/rank; seen filter ở cả Val/Test; tie; top N; no duplicate; unseen item; unseen user; invalid K; load model same output; rank deterministic.

**PASS:** chạy Top-N cho nhiều user thật, cùng input/model ra cùng ordered list; không chứa seen items; report omissions/unscorables.

**Câu hỏi bảo vệ:** (1) `model.fit` khác `recommend` thế nào? (2) Tại sao không lấy Top-10 trước rồi xóa phim đã xem? (3) Tại sao item cold-start không có score ALS? (4) Candidate union 3A+3B khác ALS-only ranking ra sao?

---

# M07 – VALIDATION-ONLY HYPERPARAMETER TUNING

**Mục tiêu:** Chọn cấu hình ALS trên **Validation** theo metric xếp hạng được khóa ở M02, với ngân sách phù hợp RAM 16 GB.

**Kiến thức:** bias-variance, regularization, latent dimensionality rank, generalization, hyperparameter selection, data snooping, multiple comparisons.

**Files:** `recommender/als/tuning.py`, `tests/als/test_tuning.py`, `docs/3a/M07_tuning_report.md`, machine-readable experiments table.

**Bước thực hiện:**

1. Đóng băng cohort validation **trước** khi xem scores: từ Train user stats, phân tầng light/medium/heavy, seed cố định; ghi cách chọn, số user, cohort positive count sau đó. Không chọn user do mô hình dự đoán đúng.
2. Chốt metric chính và K (ví dụ `NDCG@10` trên Positive Validation Cohort), phụ HR@10, Coverage@10 và runtime. Nếu sau này thay phải có documented decision, không tùy tiện đổi để tăng điểm.
3. Thử grid nhỏ, ví dụ pilot config `rank ∈ {16,32}`, `regParam ∈ {0.05,0.1}`, `maxIter=10`. Đây chỉ là **đề xuất**, điều chỉnh sau pilot tài nguyên, không giả đó là tối ưu.
4. Mỗi config fit **Train**; validate trên full item candidate pool cho cohort Val theo M02/M06; ghi training time, scoreability, positive users, metrics, reproducibility seed.
5. Chọn champion bằng deterministic objective/tie-break rule (ví dụ NDCG@10 cao nhất; nếu đồng điểm chọn mô hình nhẹ hơn). Không đọc Test để chọn hoặc chỉnh.
6. Save best model artifact, full config, experiment table, lý do chọn. Không cần cài Optuna/MLflow nếu có thể làm bằng CSV/JSON đơn giản.

**Tests:** hyperparams distinct, no Test dependency, cohort seed stable, champion selection deterministic, report includes all attempted runs incl failures.

**PASS:** có ít nhất >1 config thực sự train/validate, bảng số liệu thật, champion có lý do và **FROZEN** trước M08.

**Câu hỏi bảo vệ:** (1) Tăng rank có luôn tốt không? (2) regParam nhỏ quá có thể gây gì? (3) Vì sao không nhìn Test? (4) Chọn model có NDCG cao hơn 0.001 có chắc ý nghĩa thống kê không?

---

# M08 – FINAL OFFLINE BENCHMARK: ALS VS POPULARITY

**Mục tiêu:** Một phép đo cuối minh bạch, không “chọn metric sau khi nhìn kết quả”.

**Kiến thức:** test leakage, population vs cohort, one-held-out limitations, fair candidate pool, offline recall/NDCG, popularity baseline, coverage, scoreability.

**Files:** `recommender/als/benchmark.py`, `tests/als/test_benchmark.py`, `docs/3a/M08_final_benchmark.md`, result JSON/CSV.

**Bước thực hiện:**

1. Chỉ bắt đầu khi M07 champion/parameters, M02 metric definitions, cohort policy đã **frozen**. Tạo snapshot config hoặc content hash.
2. Test user cohort chọn theo dữ liệu Train và seed đã định, không chọn theo Test label, cùng user set cho ALS và Popularity. Cohort size phải phù hợp RAM, báo sampling method & sampling error/limits; không gọi cohort nhỏ là toàn bộ 162,541 users.
3. Test candidates = full `core/movies` catalog minus `Train_u ∪ Val_u`; ranking/model scoreability được báo tường minh. Dùng user batches, không tạo giant dense score matrix. Đếm phim không có ALS factor; targets unscorable được tính miss, không drop để làm đẹp kết quả.
4. Tính metrics cùng evaluator M02, same cohort/ground truth/candidate definition. Primary metric trên positive-target cohort, all-user diagnostic riêng, count mẫu số.
5. Lưu bảng ALS vs Popularity: HR@5/10/20, NDCG@5/10/20, MRR (nếu dùng), Coverage@K, runtime, eligible users, skipped/unscorable. Không chỉ xuất 1 con số đẹp nhất.
6. Kiểm tra output của một vài user bằng query/test để chắc ranking và seen filter; **không** đổi thuật toán/tune sau khi nhìn Test để giành điểm. Nếu bug nghiêm trọng làm phép đo vô hiệu, ghi INVALIDATED và cần quy trình đánh giá lại có giải trình, không âm thầm sửa và báo mới.
7. Không kết luận thắng/thua khi khác cohort; báo giới hạn Leave-1-Last cross-user future knowledge.

**Tests:** same cohort/candidates; no Test used in `.fit()` or model selection; output deterministic; missing scores not dropped; metric math matches M02.

**PASS:** bảng benchmark thật, đầy đủ protocol, run_id, dataset/model versions, counts, runtime; nhận định cân bằng dù ALS có thua baseline.

**Câu hỏi bảo vệ:** (1) Nếu ALS thua Popularity@10, nguyên nhân khả dĩ? (2) Why not sample 99 negatives? (3) Khác biệt coverage của ALS và KG có ý nghĩa gì? (4) Kết quả Test có cho phép tune rank lại không?

---

# M09 – COLD-START, LONG-TAIL & BIG-DATA DIAGNOSTICS

**Mục tiêu:** Giải thích những trường hợp ALS yếu và chứng minh Spark giúp xử lý dữ liệu theo số liệu thực; **không dùng diagnostics để retroactively chọn model dựa trên Test**.

**Kiến thức:** cold-start vs long-tail, known vs unseen users/items, factor reliability, regularization, partitions/shuffle, throughput vs latency, local benchmarking.

**Files:** `recommender/als/diagnostics.py`, `tests/als/test_diagnostics.py`, `docs/3a/M09_diagnostics.md`.

**Bước thực hiện:**

1. Đếm item train ratings bins `0`, `1–5`, `6–10`, `11–50`, `>50`; report ALS factor availability per bin. Nếu report metrics trên Test theo bin, coi là phân tích mô tả hậu kiểm, không dùng để retune.
2. Phân biệt `unscorable` (không có factor) vs `weakly learned` (ít rating, có factor). Không khẳng định “KG chắc chắn khắc phục” khi chưa đo KG.
3. Benchmark đọc Parquet / fit Spark trên 2–3 kích thước Train có quy tắc (ví dụ cohort subsets), log rows, hardware, partitions, wall time, shuffle warnings và peak memory nếu quan sát được. Không so runtime trên các tập có characteristics khác mà không nói giới hạn.
4. Explain `coldStartStrategy='nan'|'drop'`; chính thức báo ALS-only không fallback. Nếu thử ALS+Popularity fallback, làm variant phụ **có nhãn khác**, không thay bảng ALS-only.
5. Theo dõi model artifact size, inference batch runtime; không tuyên bố multi-node scalability từ local.

**Tests:** bins tổng đúng; unseen item missing score; no implicit fallback; deterministic diagnostics; safe OOM handling.

**PASS:** có bảng tình huống ALS không phục vụ được, benchmark thật với cấu hình máy và nhận định không phóng đại.

**Câu hỏi bảo vệ:** (1) Cold movie khác long-tail item? (2) Vì sao ALS không biết phim chưa ai rating? (3) Local Spark có đo được cluster scaling không? (4) Những ca nào KG có thể hỗ trợ?

---

# M10 – MODEL DELIVERY, INTEGRATION CONTRACT & PR REVIEW

**Mục tiêu:** Đóng gói 3A thành module thực sự tích hợp được vào Khối 4, không ép KG phải chờ ALS internals.

**Kiến thức:** training vs inference, model artifact, reproducibility, versioned outputs, service/data contracts, software release gates, Git PR.

**Files:** `recommender/als/delivery.py` (nếu cần), `docs/3a/M10_delivery.md`, `docs/3a/integration_contract.md`, README module, run artifacts manifest, smoke tests.

**Bước thực hiện:**

1. Expose `recommend_als(user_id, top_n, ...)` và batch recommendations. Xác định explicit model path, dataset version, candidate stage và missing-factor behavior.
2. Output máy đọc được: `userId`, `movieId`, `raw_score`, `rank`, `model_name='ALS'`, `model_version`, optional `run_id`. Scored rows finite, unique key `(userId,movieId,model_name,model_version)`.
3. Save/load smoke test trên model thật; join Title chỉ display; không trả Test rating/label trong production output.
4. Report benchmark summary, params, known limitations, training data lineage, manifest/checksums, commands reproducible. Hướng dẫn teammate 3B/hybrid tiếp nhận candidate union.
5. Bảo vệ `.gitignore`: Parquet/raw data/model binary khối lượng lớn không commit hoặc phát tán khi chưa được phép; chỉ commit code, configs mẫu, docs, synthetic fixtures, test outputs nhỏ không chứa MovieLens thật nếu được duyệt.
6. Review `git diff`, `git status`, lint/tests và file thuộc sở hữu. Chuẩn bị nội dung PR: scope, changes, commands run, observed counts, metric table, risks, TODO. **Chỉ push và mở PR khi maintainer cho phép**; không merge trực tiếp `main`.
7. Tạo checklist integration tests với 3B (shared ID types; shared user cohort; same seen filter rule; score separate and not added raw; candidate union), không triển khai Fusion tại M10.

**Tests:** load/recommend parity; schema & type contract; no seen; finite scores; version references; gitignored artifacts; no KG files modified.

**PASS:** owner có thể dùng model output từ repo branch để chạy integration harness, PR được review; không cần có Hybrid hoàn chỉnh ở 3A.

**Câu hỏi bảo vệ:** (1) Giữa output ALS và KG phần nào có thể join? (2) Tại sao không cộng raw_score? (3) Tại sao phải version model? (4) Muốn đổi weight Hybrid nên tune trên Train, Validation hay Test?

---

## 5. MASTER ACCEPTANCE MATRIX (BẮT BUỘC REVIEW)

| Module | Engineering evidence không thể thiếu | Kiến thức cần bảo vệ | Trạng thái ban đầu |
|---|---|---|---|
| M00 | paths/schema/env/branch checked, contract documented | Data/model contracts | NOT_STARTED |
| M01 | loader + real counts + synthetic validation | Sparsity, train/item coverage | NOT_STARTED |
| M02 | hand-calculated metric tests pass | HR/NDCG/MRR/denominators | NOT_STARTED |
| M03 | Popularity Top-N + Val report | Baseline, bias, seen filter | NOT_STARTED |
| M04 | toy ALS fit + dot-product parity | MF, latent factors, ALS objective | NOT_STARTED |
| M05 | real ALS trained + persisted + load parity | Train, Spark local, factor tables | NOT_STARTED |
| M06 | Top-N real, no-seen, deterministic | Prediction vs ranking | NOT_STARTED |
| M07 | multi-config Val-only tuning, champion frozen | Generalization, regularization | NOT_STARTED |
| M08 | frozen-test benchmark vs Popularity | Fair eval, test leakage | NOT_STARTED |
| M09 | cold-start counts + Spark performance | Cold-start, long-tail, scaling | NOT_STARTED |
| M10 | integration contract + PR review materials | Artifacts, Hybrid interface | NOT_STARTED |

**Một module không PASS khi:** chỉ tạo file, không thực thi test; demo hardcoded; giấu failed cases; dùng Test chọn tham số; thiếu input; code chạy trên synthetic rồi tuyên bố full MovieLens; chỉ báo MAE/RMSE mà không có Top-N khi nhiệm vụ yêu cầu gợi ý; hoặc chủ nhánh không giải thích được logic.

### 5.1. Những lỗi Anti phải chủ động phát hiện

- Tự train từ `ratings.csv` toàn bộ 25M thay vì `splits/train`.
- Tạo ma trận dense/collect tất cả 162K × 62K cặp để rank.
- Tự dùng `coldStartStrategy='drop'` rồi giảm denominator mà không báo.
- Đặt ngưỡng relevance/normalize theo Test, tự kết luận ALS thắng.
- Lấy top-N rồi lọc history khiến không đủ K mà không kiểm tra.
- Tính popularity count từ Train+Val+Test.
- Coi Latent factor 1 là Action, factor 2 là Romance; diễn giải sai dot product bằng Euclidean distance.
- Đưa Tag Genome/genre vào ALS-only mà không đặt tên biến thể khác.
- Đổi seed/cohort/metric sau khi thấy kết quả.
- Kết quả rating thấp của target bị xem là positive, hoặc xem unseen rating là negative truth.
- Để branch 3A ghi đè `HERMES.md`, code 3B, các file Phase 4 hoặc `main`.

### 5.2. Quy tắc dùng tài nguyên & an toàn hệ thống

- Đối với toy unit tests được phép sử dụng local collections nhỏ, **ghi rõ synthetic**.
- Các benchmark cần đặt cấu hình rõ ràng, thử pilot và có giới hạn resources. OOM phải báo và điều chỉnh có ghi log, không tự chuyển sang sampling negatives rồi gọi là full-catalog.
- Một model trained trên một subset Train được gọi `pilot/subset model`, không là `production/full model`.
- Nếu không có model artifact thật từ M05 thì M06/M08/M10 không được giả lập trạng thái PASS.

---

## 6. HƯỚNG DẪN HỢP TÁC GIT – CHỐNG XUNG ĐỘT VỚI 3B

1. Maintainer giữ `main` ổn định; 3A làm `feature/als-3a`; 3B làm `feature/kg-3b`.
2. 3A chủ yếu sửa `recommender/als/`, `tests/als/`, `docs/3a/`; 3B sửa `recommender/kg/`, `tests/kg/`, `docs/kg/`.
3. Không cùng sửa file shared (`HERMES.md`, root `README.md`, `.gitignore`, `requirements`/dependency lock) khi chưa thỏa thuận. Đề xuất thay đổi vào PR.
4. Mỗi module được review rồi commit theo nhóm thay đổi liên quan, không gộp cả M00–M10 trong commit đầu.
5. Trước merge: chạy test độc lập của 3A, verify không sửa Phase 4; so sánh schema output với 3B; owner review PR; **không tự merge**.
6. Nếu muốn kiểm kê PR teammate: pull/fetch nhánh, test trên môi trường phù hợp, kiểm tra data leakage, import/query logs và KG evidence thật. Không merge chỉ vì agent nói “all tests PASS”.

---

## 7. QUY TRÌNH BẮT ĐẦU CHO ANTIGRAVITY (CHỈ ĐỌC ROADMAP, KHÔNG CHẠY HẾT)

**Sao chép file này vào:** `docs/TASK_3A_SPARK_ALS_ROADMAP.md` trong repository. Sau đó gửi agent:

> Đọc **toàn bộ** `docs/TASK_3A_SPARK_ALS_ROADMAP.md`, `HERMES.md`, `docs/evaluation_protocol.md`, `docs/data_dictionary.md`, `docs/preprocessing_report.md` và manifest nếu có. Đây là MASTER ROADMAP của Task 3A. **Hiện chỉ thực hiện MODULE M00**, tuyệt đối không làm M01–M10, không train ALS, không sửa data/3B, không tự commit/push. Tạo `docs/3a/M00_contract.md`, thực thi kiểm tra môi trường/path/schema/Git thật, báo PASS/FAIL/BLOCKED và dừng chờ Technical Mentor review. Khi tiến sang module khác sẽ có lệnh riêng từ chủ nhánh.

### 7.1. Sau khi Anti trả kết quả Mxx

Chủ nhánh gửi Technical Mentor: (1) báo cáo module; (2) file code chính và tests; (3) log command thật; (4) config/manifest relevant; (5) phần nào chưa hiểu. Mentor đối chiếu và hỏi vấn đáp rồi mới duyệt module tiếp theo.

**Nguyên tắc cuối:** **Vibe code không đồng nghĩa vibe evidence.** Agent có thể viết phần lớn code, nhưng từng quyết định khoa học và con số kiểm thử đều phải có khả năng truy xuất và được người học giải thích độc lập.
