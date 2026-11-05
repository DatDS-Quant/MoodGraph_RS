# MOODGRAPH | TASK 3B: KNOWLEDGE GRAPH RECOMMENDER

> **Tài liệu giao việc + hợp đồng triển khai cho Antigravity (AI coding agent)**  
> Dự án: **Personalized Movie Recommendation using Knowledge Graphs and Apache Spark**  
> Phạm vi: **Khối 3B độc lập**, tích hợp ở Khối 4 Hybrid sau này  
> Tình trạng: **SPEC / CHƯA TRIỂN KHAI**. Mọi số đo hiệu năng bên dưới là điều kiện nghiệm thu, **không phải kết quả đã đo**.  
> Người thực hiện: **Teammate phụ trách KG** | Người review/merge: **chủ nhánh 3A / maintainer MoodGraph**

## 0. CHỈ DẪN BẮT BUỘC CHO ANTIGRAVITY

**Đọc trọn file trước khi viết code.** Bạn là kỹ sư triển khai KG trong repository MoodGraph, **không** phải người thiết kế lại toàn bộ hệ thống. Thực hiện theo checklist, chạy kiểm thử thật, tự kiểm chứng bằng truy vấn Neo4j, xuất bằng chứng và dừng ở trạng thái **Pull Request chờ review**. Không tuyên bố `PASS` nếu chưa thực thi. Không push thẳng `main`, không tự merge, không force-push, không sửa mã ALS/ETL của teammate.

**Tệp bắt buộc phải đọc trong repo trước khi làm:** `README.md`, `HERMES.md`, `docs/evaluation_protocol.md`, `docs/data_dictionary.md`, `docs/preprocessing_report.md`, `data/processed/manifest.json` (nếu hiện diện), `.gitignore`. **Ưu tiên code/data thật hơn các đoạn mô tả trong tài liệu.** Nếu schema, đường dẫn hay số dòng khác spec, ghi rõ và xin review bằng PR, tuyệt đối không tự sửa pipeline 3A/Phase 4.

**Đầu ra tối thiểu:** (a) Neo4j graph thực truy vấn được; (b) importer idempotent và có xác minh đếm nodes/edges; (c) KG-only path-based scorer tạo được Top-N cho user trong train mà không dùng ALS; (d) evidence thật, không dựng chuỗi giải thích bằng văn bản ngẫu nhiên; (e) test tự động + báo cáo thật; (f) branch và PR chờ maintainer review.

## 1. BỐI CẢNH VÀ MỤC TIÊU

Sơ đồ MoodGraph: **1. MovieLens 25M → 2. PySpark ETL/EDA → 3A. Spark ALS (do thành viên A) || 3B. KG (nhiệm vụ này) → 4. Hybrid → 5. Backend → 6. Web → 7. Evaluation/Report**.

**3A và 3B phát triển song song**. Cả hai dùng cùng `movieId`, `userId`, dữ liệu split và giao thức đánh giá. Nhánh 3B **không gọi model ALS, không chờ latent factors và không lấy điểm ALS**. Phải cung cấp một hàm gợi ý độc lập để mai sau khối 4 hợp ứng viên và kết hợp điểm.

**Câu hỏi nghiên cứu:** Khi biểu diễn phim, user, thể loại và Tag Genome thành **quan hệ thật** và suy luận bằng đường đi đa bước, KG có thể bổ sung những ứng viên nào, vì sao, và có lợi hơn đối chứng dựa trên thuộc tính đơn thuần không? **Không mặc định KG hay Hybrid tốt hơn ALS**.

**Definition of Done của 3B:** `recommend_kg(user_id, top_n, context, ...)` thực sự trả về các movie chưa tương tác cùng raw KG score và các path hợp lệ truy xuất từ graph; chạy lại kết quả ổn định trên cùng graph/params; có test, benchmark sơ bộ trên validation, báo cáo giới hạn và PR có thể review.

## 2. GIAO DIỆN DỮ LIỆU ĐẦU VÀO (DATA CONTRACT)

Đường dẫn tính từ **root repository**. Tất cả là **Parquet directories**, không phải một file `.parquet` duy nhất. Đọc schema thực tế, không suy diễn.

| Đường dẫn | Dữ liệu dự kiến theo Phase 4 | Dùng cho 3B | Quy tắc |
|---|---:|---|---|
| `data/processed/core/movies/` | 62,423 phim | Node `Movie`, tên phim | Giữ cả phim không genres |
| `data/processed/features/movie_genres/` | 107,245 cạnh | `Movie`–`Genre` | Thuộc tính phim, không tương tác user |
| `data/processed/core/genome_tags/` | 1,128 tag | Node `GenomeTag` | `tagId` riêng, **không** đánh đồng với free-text tag |
| `data/processed/core/genome_scores/` | 15,584,448 cặp | Candidate `Movie`–`GenomeTag` | **Không** nạp toàn bộ mặc định; chọn lọc có cấu hình |
| `data/processed/splits/train/` | 24,675,013 ratings | Node `User`, cạnh `RATED` | **Chỉ Train**; bắt buộc |
| `data/processed/features/tags_train/` | 1,074,090 tags | Cạnh `USER_TAGGED` mở rộng tùy chọn | Đã giới hạn thời gian & loại cặp Val/Test theo báo cáo; vẫn phải xác minh |
| `data/processed/splits/validation/` | 162,541 ratings | Đánh giá / chọn tham số | **Cấm tạo cạnh RATED train từ đây** |
| `data/processed/splits/test/` | 162,541 ratings | Chỉ dùng test cuối sau khi khóa model | **Cấm huấn luyện, chọn tham số, xây graph** |
| `data/processed/core/tags/` | 1,093,360 tags | **Không dùng** xây user graph offline | Có thể dùng audit riêng, không làm user profile |

Các con số là **mốc kỳ vọng từ báo cáo**. `manifest.json` và output kiểm tra thực tế mới quyết định trạng thái `VERIFIED`. Tất cả dữ liệu MovieLens được xử lý theo giấy phép nguồn: **không commit, upload công khai hay chuyển dữ liệu nguyên/bản dẫn xuất khi chưa có quyền phân phối**; teammate nên dùng nguồn tải chính thức và tái tạo qua pipeline của nhóm nếu chưa có phép chia sẻ phù hợp.

### 2.1. Kiểm tra trước khi import (bắt buộc)

1. Thực hiện preflight: tồn tại đường dẫn, đọc thành công schema, row counts và `manifest.json` (nếu có). Nếu dữ liệu không tồn tại, **dừng import full** và dùng fixture synthetic cho đến khi có dataset hợp lệ.
2. Xác nhận không dùng `validation/test` hay `core/tags` ở nhánh tạo cạnh tương tác.
3. Kiểm tra các ID là số nguyên, các `movieId` tham chiếu phim, `tagId` genome tham chiếu từ điển; không silently drop bản ghi lỗi.
4. Không chuyển 25 triệu ratings sang `pandas` hoặc `list` RAM; nếu cần chuyển PySpark → Neo4j thì **stream/chunk/batch**.
5. Kiểm tra dải ratings 0.5–5.0; `relevance` từ 0–1; không coi toàn bộ ratings là lời khen.
6. Log dataset version/split protocol, machine/environment, input row counts và selection policies vào báo cáo import.

### 2.2. Tập dữ liệu synthetic (test fixture)

Tạo fixture **tự nghĩ, không sao chép MovieLens**, ví dụ 4 users, 7 movies, 3 genres, 4 genome tags, rating gồm 5 sao, 2 sao, các shared edges, 1 movie không rating nhưng có genre. Fixture phải có một đường collaborative đa bước `User→Movie←User→Movie`, một đường genre, một đường genome, một movie chưa có metadata và một tag bất thường. Lưu trong `tests/kg/fixtures/`. Các expected paths và expected scores **tính tay, xuất hiện trong tests**.

## 3. GRAPH DATA MODEL (CỐ ĐỊNH V1)

### 3.1. Nút và khóa duy nhất

| Node | Key | Properties cơ bản | Nguồn |
|---|---|---|---|
| `(:User)` | `userId` | `userId:int` | train ratings |
| `(:Movie)` | `movieId` | `movieId:int`, `title:string`, `genresRaw:string` | movies |
| `(:Genre)` | `name` | `name:string` | movie_genres |
| `(:GenomeTag)` | `tagId` | `tagId:int`, `name:string` | genome_tags |

Node `FreeTag` từ tags người dùng là **tùy chọn sau khi core đạt**, không thay thế `GenomeTag`. **Không thêm Actor, Director, Mood Archetype, GNN embedding hoặc nguồn IMDb/TMDb mới** vào v1.

### 3.2. Cạnh

| Cạnh Cypher | Thuộc tính | Điều kiện |
|---|---|---|
| `(u:User)-[:RATED]->(m:Movie)` | `rating:float`, `timestamp:int/long` | **Chỉ từ train**; 1 cạnh/cặp (userId,movieId) |
| `(m:Movie)-[:IN_GENRE]->(g:Genre)` | không bắt buộc | Chỉ từ movie_genres |
| `(m:Movie)-[:HAS_GENOME_TAG]->(t:GenomeTag)` | `relevance:float` | **Giữ Top-M theo relevance**, M cấu hình và xác định trên validation; không full 15.5M mặc định |
| `(u:User)-[:USER_TAGGED]->(m:Movie)` | `tag:string`, `timestamp:long` | **Tùy chọn**, chỉ `features/tags_train`, có thể nhiều tag/cặp; cần chiến lược khóa để không sinh bản sao khi rerun |

Khuyến nghị core ban đầu **không nạp `USER_TAGGED`**: 3 loại cạnh đầu đủ để phát triển và kiểm thử path-based scoring. Chỉ thêm khi kiểm thử cho thấy giá trị, tránh kéo thêm 1M cạnh và xử lý tự do NLP ngoài phạm vi.

**Neo4j Community:** tạo `UNIQUE` constraints cho `User.userId`, `Movie.movieId`, `Genre.name`, `GenomeTag.tagId` bằng `CREATE CONSTRAINT ... IF NOT EXISTS`; không yêu cầu key/property existence constraints chỉ có ở các tier khác. Cypher sử dụng `MERGE`/`MATCH` theo khóa và query parameters, không nối input trực tiếp vào câu truy vấn.

### 3.3. Kiến trúc đường đi (metapaths) có thể giải thích

**P1. Genre path:** `User -RATED-> Movie_A -IN_GENRE-> Genre <-IN_GENRE- Movie_B`.

**P2. Genome path:** `User -RATED-> Movie_A -HAS_GENOME_TAG-> Tag <-HAS_GENOME_TAG- Movie_B`.

**P3. Collaborative graph path (quan trọng để phân biệt với Content-Based):** `User_A -RATED-> Movie_X <-RATED- User_B -RATED-> Movie_Y`.

P3 phải có cơ chế chống nổ số đường đi: chỉ mở rộng từ phim user thực sự thích, giới hạn neighbor user theo số giao nhau/độ tin cậy, cắt hub quá phổ biến, giới hạn depth/breadth, batch và `LIMIT` thích hợp. **Không Cartesian product hàng triệu cạnh**. Nếu P3 trên full graph quá nặng, chứng minh trên pilot thực, công bố giới hạn, đề xuất cải tiến; tuyệt đối không dùng giả lập scoring và tuyên bố đã chạy full.

## 4. KHÁI NIỆM KG SCORING CÓ THỂ TRIỂN KHAI

### 4.1. Quy tắc tính điểm v1

Thiết kế `Path-based Weighted Evidence Scorer`, một công thức **đơn giản, tái lập và giải thích được**. Mỗi ứng viên phải có ít nhất một path thật. Không lấy cosine genre/tag đơn thuần rồi đặt tên "KG recommender".

- **Positive preference weight**: mặc định `w(r) = max(0, (r - 3.0) / 2.0)` cho rating 0.5–5.0; đây là **lựa chọn khởi tạo cần tuning trên Val**, không là sự thật học thuật.
- **P1 contribution**: cộng trọng số `w(r)` qua đường User→Movie→Genre→Candidate, có chuẩn hóa theo genre degree / mức phổ biến để hạn chế hub.
- **P2 contribution**: cộng `w(r) * relevance(source, tag) * relevance(candidate, tag)` qua mỗi GenomeTag được giữ; chuẩn hóa theo số phim nối tag và số path.
- **P3 contribution**: tổng hợp lời chứng từ các users khác nối qua phim đã thích, ưu tiên neighbor có nhiều phim cùng thích và có normalization/capping; không xem một neighbor có hàng ngàn rating là bằng chứng áp đảo.
- **Final KG score**: `score_KG = α * norm(P1) + β * norm(P2) + γ * norm(P3)`, `α, β, γ >= 0`, tổng bằng 1. Chọn trọng số bằng Validation **chỉ sau khi scorer đúng**, có cấu hình và log.
- Nếu một path type thiếu metadata, **điểm loại đó bằng 0**, không invent liên kết. Số path và lý do thiếu phải được log cho diagnostic.
- **Không được sử dụng test** để chọn M, threshold, α/β/γ, K hoặc giới hạn neighbor.

Các phép `norm` phải được định nghĩa cụ thể trong tài liệu (ví dụ chuẩn hóa theo tổng trọng số path hoặc per-user min-max ổn định), xử lý score cùng nhau và test bằng ví dụ tay. Không được điều chỉnh normalizer theo test. Điểm `raw_score` của KG là điểm nội bộ **không cùng thang** với ALS.

### 4.2. Candidate generation và filtering

`recommend_kg(user_id, top_n=10, exclude_movie_ids=None)` tìm candidates theo P1/P2/P3. Loại các phim user đã đánh giá trong **train** trước khi xếp hạng. Trong đánh giá Validation: lịch sử đã biết = train. Trong đánh giá Test: loại train **và** validation ở candidate pool theo `evaluation_protocol.md`, nhưng **không** được tự thêm val vào graph scorer nếu chưa có giao thức cập nhật tương ứng.

Trả Top-N với tie-break `score desc, movieId asc` để lặp lại kết quả. Không để `NaN`, `inf`, negative top scores giả định; nếu không đủ candidates, trả ít hơn N và report coverage. Với user ngoài train không có tín hiệu, KG-only có thể trả `[]` + lý do `no_history`; fallback phải là cấu hình riêng, không tự giấu lỗi.

**Movie cold-start:** phim không có rating trong train nhưng có Genre/Genome liên quan **có thể** được KG đề xuất. Kiểm thử synthetic. Không hứa khắc phục toàn bộ cold-start nếu phim thiếu metadata.

### 4.3. Bằng chứng giải thích (evidence contract)

Mỗi movie recommendation có `evidence` gồm tối đa 3–5 path/quan hệ thật theo thứ tự đóng góp, ví dụ:

```json
{
  "userId": 42,
  "movieId": 318,
  "raw_score": 0.712,
  "rank": 1,
  "model_name": "KG_PATH",
  "evidence": [
    {
      "path_type": "GENRE",
      "sourceMovieId": 1,
      "sharedEntity": {"type": "Genre", "key": "Animation"},
      "sourceRating": 5.0,
      "contribution": 0.12
    }
  ]
}
```

**Ví dụ này chỉ mô tả schema, không phải kết quả chạy thật.** Khi code thực tế, mọi node ID, cạnh, rating, relevance và contribution trong `evidence` phải truy ngược được từ graph/snapshot nguồn. Với `USER_COLLAB` gồm `neighborUserId` và `anchorMovieId` theo đường đi xác thực. Không dựng `explanation` bằng cách gọi LLM hoặc nối tên phim thiếu bằng chứng. Tối thiểu cung cấp machine-readable evidence để FastAPI/Web về sau dựng lời giải thích tiếng Việt.

### 4.4. Hợp đồng tích hợp giữa 3A và 3B

- Python facade dự kiến: `recommend_kg(user_id: int, top_n: int = 10, exclude_movie_ids: set[int] | None = None) -> list[dict]` (kiểu chính xác có thể chuyển sang dataclass nhưng không phá JSON schema).
- Dạng lưu output batch: `userId:int, movieId:int, raw_score:float, rank:int, model_name:string, evidence_json:string`, cộng `run_id`, `algorithm_version` ở metadata. Không gắn `rating` thực của Val/Test vào output.
- Bộ join với ALS ở khối 4 dùng `(userId, movieId)`; **Hybrid giữ candidate union**, không yêu cầu KG chỉ rerank ALS Top-100.
- Nếu 3A đã định nghĩa schema khác, **mở issue/PR thảo luận**, không tự sửa thư mục ALS.

## 5. TRIỂN KHAI THEO TỪNG CỔNG NGHIỆM THU (STAGE GATES)

### Gate 0. Repository & môi trường (không chỉnh ALS)

1. `git fetch`, cập nhật từ `main`, tạo branch `feature/kg-3b` (nếu chưa có branch tương tự).
2. Kiểm tra Neo4j Community chạy được, phiên bản thực tế, Python + official `neo4j` driver, công cụ đọc Parquet (`pyarrow`, PySpark hoặc exporter có sẵn). Chỉ cài dependency thực sự cần và ghi phiên bản vào dependency riêng cho KG.
3. Dùng `.env.example` cho `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `MOODGRAPH_DATA_ROOT`, `KG_IMPORT_MODE`, `KG_TAG_TOP_M`, `KG_BATCH_SIZE`. **Không commit `.env`/password.**
4. Viết `recommender/kg/README.md` và `docs/kg/architecture.md` mô tả đường đi. Chưa đụng frontend/backend.

**PASS Gate 0:** script smoke test `driver.verify_connectivity()` trả PASS, có ghi rõ Neo4j version/port/credential source (không lộ password); read Parquet schema thành công hoặc chuyển sang synthetic mode có log rõ ràng.

### Gate 1. Graph schema + synthetic import

- Tạo constraints theo node key.
- Tạo fixture synthetic có expected exact counts; nạp User/Movie/Genre/GenomeTag và 3 loại edges core.
- Viết import theo **node trước, edge sau**; dùng parameterized `UNWIND` + `MERGE` theo batch, transaction rõ ràng, rollback batch lỗi, checkpoint/resume nếu cần.
- **Rerun cùng fixture 2 lần** không tăng số nodes/relationships; cập nhật thuộc tính deterministically. Log missing endpoints và reject nếu vượt kiểm thử.
- Viết truy vấn `MATCH` xuất một đường P1/P2/P3 có đủ đúng node/edge thực.

**PASS Gate 1:** exact counts, 0 duplicate keys, 0 dangling edges, idempotent 2 runs, query evidence path thật.

### Gate 2. KG scorer chính xác trên fixture

- Xây P1 trước, P2 sau, P3 sau. Với mỗi loại, unit test và expected result tính tay.
- Cài normalization, dedup paths, giới hạn degree, bound depth, exclude seen, score finite và stable tie.
- **Mutation test:** xóa một edge genre/genome hoặc collaborative trên fixture, chỉ số contribution/evidence của path tương ứng phải thay đổi dự đoán được. Nếu thay đổi graph mà score không đổi, nghi ngờ không có graph reasoning.
- Kiểm tra khác biệt so với baseline content-only (P1/P2 không P3) để xác định đóng góp đường P3; không bắt buộc phải có metric tốt hơn, chỉ chứng minh pipeline thực sự dùng quan hệ đa bước.

**PASS Gate 2:** scorer trả Top-N + evidence truy xuất được; qua tất cả tests synthetic; không dùng ALS, không đụng Val/Test.

### Gate 3. Pilot MovieLens thật, tăng dần

- Dùng **sample users/movies xác định** có seed và log các IDs/counts, không dùng `limit` không trật tự rồi gọi là reproducible.
- Thứ tự tăng: synthetic → ví dụ 100–500 users (có train history đủ) → 1,000–5,000 users, rồi mở rộng chỉ nếu tài nguyên cho phép.
- Chỉ nhập `RATED` từ `train`; `movie_genres`/genome tag có thể nạp rộng hơn sau khi đánh giá memory. Các phim ngoài pilot train được coi là item metadata, không giả lập có rating.
- Với `genome_scores` chọn `Top-M` theo `relevance DESC, tagId ASC` **trước khi nạp**; M mặc định để thử 10/20/30 theo validation, không tự nhận 20 là tối ưu. Log số edge trước/sau và độ phủ.
- Đo số nodes/edges, DB size, peak RSS/heap nếu có, import throughput, query latency trên sample thật; báo khác biệt với full 25M.
- Nếu full `RATED` 24.7M làm Neo4j vượt tài nguyên, **không ép** nhập; đề xuất cấu hình đánh giá có coverage/scope rõ, hoặc kiến trúc graph subgraph phục vụ giải thích, trong khi xử lý off-line bằng Spark. Không gọi pilot là full MovieLens.

**PASS Gate 3:** log counts hợp lệ, 0 edge Val/Test, rerun 2 lần counts bất biến, được thông số tài nguyên trên dữ liệu thật, graph query không lỗi.

### Gate 4. Validation và ablation (không test tuning)

- Đánh giá trên **cùng danh sách user được chọn rõ ràng**, dùng ranking protocol đã khóa; mẫu cohort, seed, % coverage phải báo, không gọi sample candidate là full-catalog nếu không thực sự rank catalog.
- Cấu hình ít nhất: `Genre-only graph (P1)`, `Genre+Genome (P1+P2)`, `Full path-based graph (P1+P2+P3)`. Đây là **ablation trong nhánh KG**. Có Popularity/Content-based benchmark nếu bên A cung cấp; không tự sửa code họ.
- Positive Val threshold 3.5; người có val rating < 3.5 không có positive target và phải báo cohort denominator, số cases scoreable/unsupported.
- Tính HR@5/10/20, NDCG@5/10/20, Catalog Coverage@10; có thể Recall/MRR khi định nghĩa chuẩn. Với mỗi user có đúng 1 positive Val, Recall=HR trên positive cohort, không trình bày như hai bằng chứng khác nhau.
- Không nhúng val/test vào graph; chỉ dùng Val cho tham số; test **chưa mở** ở Task 3B nếu chưa được maintainer cho phép final evaluation.
- So sánh chi phí mỗi biến thể, score availability, Cold-start movie coverage, giải thích valid path ratio.

**PASS Gate 4:** metrics có số liệu log và mã tái lập; không fabricated numbers; cấu hình cuối chọn trên Val, không nhìn test.

### Gate 5. Handover và PR

- Freeze cấu hình KG scorer và snapshot dataset/seed; lưu `kg_config.yaml` / JSON; rõ output format.
- Ghi `docs/kg/import_report.md`, `docs/kg/model_report.md`, `docs/kg/testing_report.md`, `docs/kg/integration_contract.md`, README setup chạy end-to-end.
- Tạo `recommender/kg/` module sạch, không đụng `recommender/als/`, `web/` hoặc `data/raw/`, không commit `data/processed/`, Neo4j databases, cache, secrets hay file log lớn.
- Chạy smoke tests, unit tests, integration tests, static format/lint phù hợp, thử fresh clone setup ở mức có thể. **Nếu cần DB Neo4j mới để integration tests thì dùng DB test riêng**, không `MATCH (n) DETACH DELETE n` trên DB không chắc chắn là fixture.
- `git status`, kiểm tra diff rồi **push branch riêng**; tạo Pull Request vào `main`, nêu schema thay đổi, metric Val, giới hạn pilot/full, lệnh test, ảnh/truy vấn evidence và issue còn mở.
- **DỪNG. KHÔNG MERGE, KHÔNG PUSH THẲNG MAIN.**

**PASS Gate 5:** maintainer có thể checkout branch, chạy unit test/Neo4j test, truy xuất recommendation và explanation, đọc PR trước khi merge.

## 6. CẤU TRÚC THƯ MỤC ĐỀ XUẤT (KHÔNG THAY ĐỔI CODE 3A)

```text
MoodGraph/
  recommender/
    kg/
      __init__.py
      README.md
      config.py                 # config và env validation
      schema.cypher             # unique constraints / indexes
      data_access.py            # read Parquet in batches
      import_graph.py           # CLI: synthetic/pilot/full(if approved)
      queries.py                # parameterized Cypher templates
      scorer.py                 # weighted path-based scoring
      recommend.py              # recommend_kg facade
      evaluate.py               # validation-only metrics/cohort
      checks.py                 # graph data-quality checks
  tests/
    kg/
      fixtures/                 # synthetic generated, không chứa MovieLens rows
      test_schema.py
      test_import_idempotency.py
      test_path_scoring.py
      test_no_leakage.py
      test_recommendations.py
      test_evidence.py
      test_metrics.py
  docs/
    kg/
      architecture.md
      import_report.md
      model_report.md
      testing_report.md
      integration_contract.md
  scripts/
    kg_smoke_test.py
```

Có thể thay đổi tên file theo repo thực tế nếu **ghi rõ lý do và giữ chức năng**, tránh tạo quá nhiều framework. Toàn bộ model/data artifact thực tế để trong thư mục gitignored (`data/` hoặc `artifacts/` đã kiểm tra `.gitignore`).

## 7. HƯỚNG DẪN KỸ THUẬT TỐI THIỂU

### 7.1. Ví dụ constraints (điều chỉnh theo Neo4j version)

```cypher
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE;
CREATE CONSTRAINT movie_id_unique IF NOT EXISTS
FOR (m:Movie) REQUIRE m.movieId IS UNIQUE;
CREATE CONSTRAINT genre_name_unique IF NOT EXISTS
FOR (g:Genre) REQUIRE g.name IS UNIQUE;
CREATE CONSTRAINT genome_tag_id_unique IF NOT EXISTS
FOR (t:GenomeTag) REQUIRE t.tagId IS UNIQUE;
```

### 7.2. Ví dụ nguyên tắc import batch

```cypher
UNWIND $rows AS row
MATCH (u:User {userId: row.userId})
MATCH (m:Movie {movieId: row.movieId})
MERGE (u)-[r:RATED]->(m)
SET r.rating = row.rating,
    r.timestamp = row.timestamp;
```

> **Cảnh báo:** `MERGE` relationship giữa hai endpoint đã được `MATCH` bằng khóa. Phải tạo unique constraints và node trước. Nếu source có record lỗi endpoint hoặc duplicates, log & fail chứ không tự im lặng bỏ. Không dùng list toàn bộ 24.7M ratings trong `$rows`.

### 7.3. Truy vấn đường đi ví dụ (không dùng để tính score full-scale chưa profiling)

```cypher
MATCH (u:User {userId: $userId})-[r:RATED]->(liked:Movie)
MATCH (liked)-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(candidate:Movie)
WHERE r.rating >= $minLikedRating
  AND NOT EXISTS {
    MATCH (u)-[:RATED]->(candidate)
  }
RETURN candidate.movieId AS movieId,
       liked.movieId AS sourceMovieId,
       g.name AS sharedGenre,
       r.rating AS sourceRating
LIMIT $pathLimit;
```

Trong triển khai phải lọc, normalize, deterministic sort và lưu provenance; `LIMIT` chỉ là giới hạn an toàn, không mặc định đường đi được chọn như nhau khi không có ORDER BY. Quy tắc `minLikedRating` là hyperparameter chọn bằng Val. Không truy vấn trực tiếp hàng chục triệu path rồi `collect` sang Python.

### 7.4. Neo4j import options

Neo4j có `LOAD CSV` và các phương án `neo4j-admin database import` cho initial load; khả năng nhập Parquet trực tiếp của **admin import phụ thuộc phiên bản Neo4j**, nên kiểm tra bản máy đang dùng. Với scope phát triển và tests của 3B, phương án Python official driver + batch parameterized `UNWIND` là cách dễ kiểm thử và idempotent. Chỉ dùng bulk import nếu có benchmark chứng minh cần và quy trình khởi tạo DB trống an toàn. Tránh `LOAD CSV` trỏ thẳng vào Parquet, vì đó không phải cùng định dạng.

## 8. MA TRẬN KIỂM THỬ VÀ BẰNG CHỨNG BẮT BUỘC

| Test ID | Kiểm tra | PASS khi |
|---|---|---|
| KG-01 | Preflight schema + manifest | Inputs có thật, schema đúng, không dùng nguồn cấm |
| KG-02 | Unique nodes | Key mỗi label không trùng; constraints hiện diện |
| KG-03 | Graph edges | Chỉ nối node tồn tại, đúng edge type, no dangling |
| KG-04 | Import idempotency | Nhập lặp 2 lần: counts & properties không thay đổi bất thường |
| KG-05 | Split isolation | Không có `(userId,movieId)` Val/Test thành `RATED`; không dùng core/tags xây user graph |
| KG-06 | Genome selection | Mỗi Movie ≤ Top-M GenomeTag, tie-break xác định, edges count đúng |
| KG-07 | P1/P2/P3 path validity | Mọi evidence thật sự truy vấn được từ graph |
| KG-08 | Scoring fixture | Điểm khớp phép tính tay trong tolerance; không NaN/Inf |
| KG-09 | Mutation test | Gỡ cạnh có ảnh hưởng ⇒ path contribution/evidence biến đổi |
| KG-10 | Seen-item filtering | Không gợi ý phim user đã train-rated; test pool loại cả val |
| KG-11 | Deterministic ranking | Same graph+config ⇒ same Top-N và thứ tự tie |
| KG-12 | Cold-start behavior | Phim chưa có train rating nhưng có metadata có thể được xét; no-metadata không hallucinate |
| KG-13 | No-history behavior | User không có train history trả kết quả/diagnostic rõ ràng |
| KG-14 | Integration output | Đúng schema `(userId,movieId,raw_score,rank,model_name,evidence)` |
| KG-15 | Validation metrics | Có cohort, denominator, seed, score availability, metric từ data thật |
| KG-16 | Resource sanity | Nhập/query pilot không OOM, báo RAM/DB/time và giới hạn scale |
| KG-17 | Git hygiene | Diff không chạm ALS/ETL, không commit data/passwords, PR chờ review |

**Cấm tạo JSON `PASSED` bằng cách hardcode.** Kiểm thử nào chỉ mới mô tả, mark `NOT_RUN`. Kiểm thử lỗi thì mark `FAILED`, cung cấp log lệnh, exception và cách khắc phục. Thống nhất output test machine-readable JSON với `test_id`, `status`, `actual`, `expected`, `duration_ms`, `evidence_path`.

## 9. QUẢN LÝ HIỆU NĂNG VÀ GIỚI HẠN

- Laptop của chủ pipeline từng dùng RAM 16GB; **không giả định máy teammate mạnh hơn**. Đo thực tế trên máy teammate và cấu hình heap/page-cache phù hợp.
- Nạp full 24,675,013 ratings vào Neo4j **không phải điều kiện tuyệt đối để thông qua Gate 2**. Cần pilot thật và báo scope. Không dán nhãn Full KG nếu chỉ chạy 500 users.
- Không nạp thẳng 15,584,448 Genome edges vì mặc định; dùng top-M, báo phim không Genome (~48,607 trong catalog) và genre fallback.
- Candidate graph paths có thể nhiều hơn số films; phải aggregation theo `candidateMovieId` và giảm bias bởi phim/người dùng cực phổ biến.
- Nếu dùng Top-M graph tags, **ghi rõ đây là view đã lọc**, không sửa/tái ghi `core/genome_scores` nguồn.
- Không tự cam kết latency <100 ms; benchmark thực nghiệm và công bố p50/p95 trên cohort, warm/cold cache nếu đo được.
- Không trộn mô hình graph-only với external ALS candidates trong báo cáo KG-only.

## 10. GIT COLLABORATION VÀ QUYỀN MERGE

**Luồng yêu cầu:** `main` (protected / shared) → teammate tạo `feature/kg-3b` → commit nhỏ, có mô tả → `git push -u origin feature/kg-3b` → mở Pull Request → chủ 3A review diff + test + evidence → chốt review → **mới merge vào main**.

Đề xuất commit theo gates:

1. `feat(kg): define schema and synthetic fixtures`
2. `feat(kg): add idempotent Neo4j importer`
3. `feat(kg): implement path-based scorer and evidence`
4. `test(kg): add leakage and scoring validation`
5. `docs(kg): document data contract benchmarks and limitations`

Không commit data Parquet, nguyên liệu MovieLens, user credentials, `.env`, Neo4j DB, caches, logs cực lớn. **Đừng để Antigravity tự merge chỉ vì tests nó tự báo PASS.** Maintainer xem lại Git diff, chạy test độc lập, đối chiếu score và evidence; nếu chưa đạt thì yêu cầu sửa trên cùng PR. Khi đã merge, hai thành viên cùng pull `main` và giải quyết xung đột theo trách nhiệm file.

### PR acceptance checklist cho chủ nhánh 3A

- [ ] PR chỉ thay đổi phần 3B và docs/tests liên quan; không đụng pipeline 3A/Phase 4.
- [ ] Fixture synthetic chạy xanh và Mutation test chứng minh đường đi thật ảnh hưởng score.
- [ ] Import idempotent, constraints, query evidence đều đạt.
- [ ] Không có leakage rating val/test, tag user ngoài train-only.
- [ ] Recommendations Top-N thực, loại seen items, rank ổn định.
- [ ] Output contract với ALS đã thống nhất, không cộng điểm khác thang trực tiếp.
- [ ] Báo cáo pilot/full scope trung thực, metric Val có cohort/denominator.
- [ ] `git diff` không chứa dữ liệu MovieLens, secrets, model lớn hoặc code ngoài phạm vi.
- [ ] Teammate trình bày được P1/P2/P3 và vì sao KG khác content-only.

## 11. CÁC CÂU HỎI PHẢI TỰ TRẢ LỜI TRƯỚC KHI ĐÁNH DẤU HOÀN THÀNH

1. Khi Neo4j thiếu một quan hệ Genre, Top-N/evidence của user nào thay đổi? Có test chứng minh?
2. P3 (`User→Movie←User→Movie`) có tồn tại và tạo đóng góp không, hay toàn bộ điểm chỉ là content similarity?
3. Genome score có nguồn hậu kỳ; vì sao cần ablation Genre-only? Kết quả Val nói gì?
4. Graph có thể gợi ý một phim `train_rating_count = 0` nhưng có genre như thế nào? Giới hạn?
5. `features/tags_train` khác `core/tags` thế nào? Test ngăn việc dùng sai bảng ở đâu?
6. Nếu importer chạy lặp, những gì bảo đảm không tăng cạnh đúp?
7. Nếu Neo4j thiếu RAM cho full train, báo cáo pilot với các giới hạn ra sao mà không phóng đại?
8. Ai quyết định merge? Trình tự review và nghiệm thu sau PR là gì?

## 12. MẪU BÁO CÁO KẾT THÚC CỦA AGENT (BẮT BUỘC)

Agent phải xuất báo cáo ngắn, **có số thực** theo form:

```text
TASK 3B STATUS: READY_FOR_REVIEW | BLOCKED | PARTIAL
BRANCH / COMMIT / PR: ...
NEO4J VERSION & IMPORT MODE: ...
DATA VERSION / INPUT COUNTS: ...
SCOPE: synthetic / N-user pilot / full train (đánh dấu đúng)
GRAPH: User=..., Movie=..., Genre=..., GenomeTag=...
EDGES: RATED=..., IN_GENRE=..., HAS_GENOME_TAG=..., USER_TAGGED=...
TAG TOP-M POLICY: ...
KG PATH TYPES IMPLEMENTED: P1=..., P2=..., P3=...
KG RECOMMENDATION EXAMPLE: userId=..., top5=[...] (dữ liệu chạy thật)
EXPLANATION EXAMPLE: các node/edge truy vết thật
TESTS: passed=..., failed=..., not_run=..., log_path=...
VALIDATION: cohort=..., HR@10=..., NDCG@10=..., coverage=... (nếu chạy)
PERFORMANCE: import_time=..., db_size=..., query_p50/p95=... (nếu đo)
FILES CHANGED: ...
KNOWN LIMITATIONS / OPEN QUESTIONS: ...
REQUEST TO MERGE: NO. Await maintainer approval.
```

## 13. THAM KHẢO KỸ THUẬT CHÍNH THỨC

- Neo4j Python driver: https://neo4j.com/docs/python-manual/current/
- Neo4j managed transactions: https://neo4j.com/docs/python-manual/current/transactions/
- Neo4j uniqueness constraints: https://neo4j.com/docs/cypher-manual/current/schema/constraints/create-constraints/
- Neo4j `LOAD CSV`: https://neo4j.com/docs/cypher-manual/current/clauses/load-csv/
- Neo4j database import (kiểm tra capability theo version): https://neo4j.com/docs/operations-manual/current/import/
- GroupLens MovieLens 25M: https://grouplens.org/datasets/movielens/25m/
- Tài liệu nội bộ repo: `docs/evaluation_protocol.md`, `docs/data_dictionary.md`, `HERMES.md`

**Lưu ý:** Neo4j docs có nội dung tùy phiên bản. Agent phải kiểm tra phiên bản đang cài thay vì copy vô điều kiện một câu lệnh dành cho phiên bản khác.

---

## 14. PROMPT KHỞI ĐỘNG NGẮN (DÁN VÀO ANTIGRAVITY CỦA TEAMMATE)

> Hãy đọc kỹ `docs/TASK_3B_KNOWLEDGE_GRAPH.md` trước tiên. Bạn phụ trách độc lập **MoodGraph Task 3B (Knowledge Graph Recommendation)** trên branch `feature/kg-3b`, không chỉnh ALS/ETL/Frontend. Thực hiện từ Gate 0 tới Gate 5 theo các yêu cầu, data contracts và acceptance tests trong tài liệu. Bắt đầu với Neo4j + fixture synthetic; sau đó pilot dữ liệu Parquet thật; chỉ mở rộng khi đủ RAM và có báo cáo. Dùng train-only cho user edges, thực thi P1/P2/P3 path-based scoring thật, xuất Top-N + evidence cùng schema tích hợp Hybrid. Viết tests và report bằng kết quả đã chạy; không giả số hay tự tuyên bố full run nếu chỉ là pilot. Push branch riêng, mở PR chờ người phụ trách 3A kiểm kê; **không merge vào main**. Nếu thiếu quyền truy cập nguồn dữ liệu, tạo fixture synthetic và báo BLOCKED cho full import, không tự đưa dữ liệu MovieLens lên public. Đọc HERMES và protocol trước khi tạo file.
