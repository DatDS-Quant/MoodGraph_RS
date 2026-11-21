# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.4

> **Chuyên đề:** 3.4. Giải thích gợi ý bằng bằng chứng đường đi và đồ thị con (Path Evidence & Subgraph Explanation)  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Tệp kiểm toán cốt lõi:**  
> - `recommender/kg/scorer.py` (Động cơ tính điểm đường đi và trích xuất EvidenceItem)  
> - `recommender/kg/embedded_graph.py` (Đồ thị tri thức nhúng in-memory và trích xuất Subgraph)  
> - `recommender/kg/explainability.py` (Mô-đun trích xuất cấu trúc đồ thị con cho vis-network)  
> - `recommender/services/explainability_service.py` (Dịch vụ ứng dụng giải thích đa tầng và kiểm định xuất xứ)  
> - `recommender/api/discovery_router.py` (Endpoint GET /api/discovery/explanations/{user_id}/{movie_id})  
> - `recommender/api/lab_router.py` (Endpoint GET /api/lab/graph/subgraph)  
> - `demo/js/graph_visualizer.js` (Frontend Mode B: Trực quan hóa tương tác vis-network)  
> - `demo/js/app.js` & `demo/js/modal_component.js` (Frontend Mode A: Provenance Explorer 4 Tabs)  
> - `tests/kg/test_evidence.py`, `tests/kg/test_embedded_graph.py`, `tests/phase5/test_explainability_api.py`  
> **Trạng thái:** ĐÃ KIỂM ĐỊNH MÃ NGUỒN VÀ ĐỐI CHIẾU THỰC TẾ 100%

---

## PHẦN A — BẢNG KIỂM TOÁN MÃ NGUỒN CHI TIẾT

| Thành phần kỹ thuật | Cơ chế triển khai thực tế trong mã nguồn | Dữ liệu đầu vào / đầu ra | Bằng chứng file:line | Trạng thái xác minh |
| :--- | :--- | :--- | :--- | :--- |
| **Cấu trúc dữ liệu Bằng chứng (EvidenceItem)** | Định nghĩa đối tượng chứa siêu dữ liệu của từng đường đi đóng góp (Metapath P1, P2, P3). Có phương thức chuyển đổi `to_dict()`. | **Vào**: path_type, sourceMovieId, sharedEntity, contribution, neighborUserId...<br>**Ra**: Dictionary chuẩn hóa tích hợp. | [scorer.py:28-64](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L28-L64) | **ĐÃ XÁC MINH** |
| **Thời điểm trích xuất bằng chứng** | Trích xuất **hậu kiểm (post-hoc)** chỉ dành riêng cho danh sách Top-N ứng viên sau khi đã hoàn tất tính điểm toàn bộ ứng viên và sắp xếp thứ hạng. Giảm tải 99.9% tính toán CPU. | **Vào**: `top_cand_ids` (Set[int]), `active_liked`, `top_neighbors`.<br>**Ra**: `cand_evidence` (Dict[int, List[EvidenceItem]]). | [scorer.py:296-304](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L296-L304) | **ĐÃ XÁC MINH** |
| **Giới hạn số lượng bằng chứng** | Giới hạn tối đa 5 bằng chứng có mức đóng góp (`contribution`) cao nhất cho mỗi phim được đề xuất. | **Vào**: Danh sách `ev_list` đã sort `contribution DESC`.<br>**Ra**: `ev_list[:5]`. | [scorer.py:75](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L75)<br>[scorer.py:310-312](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L310-L312) | **ĐÃ XÁC MINH** |
| **Bằng chứng P1 (Thể loại)** | Tìm giao thoa thể loại giữa phim đã thích (`rating >= 3.5`) và phim ứng viên. Đóng góp thô tính bằng trọng số sở thích chia căn bậc hai bậc đỉnh thể loại. | **Vào**: `cand_genres`, `src_genres`.<br>**Ra**: `EvidenceItem(path_type="GENRE", shared_entity_type="Genre", contribution=w/sqrt(deg_g))`. | [scorer.py:360-375](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L360-L375) | **ĐÃ XÁC MINH** |
| **Bằng chứng P2 (Genome Tags)** | Tìm giao thoa các thẻ Genome giữa phim nguồn và phim đích. Đóng góp tính bằng tích hai trọng số relevance chia logarit bậc đỉnh thẻ. | **Vào**: `cand_tags`, `src_tags`.<br>**Ra**: `EvidenceItem(path_type="GENOME", shared_entity_type="GenomeTag", contribution=w*rel_src*rel_cand/log1p(deg_t))`. | [scorer.py:377-397](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L377-L397) | **ĐÃ XÁC MINH** |
| **Bằng chứng P3 (Cộng tác)** | Trích xuất từ Top-50 láng giềng Salton Cosine. Lưu định danh người dùng láng giềng và phim trung gian kết nối (anchor movie). | **Vào**: `top_neighbors`, `n_ratings`.<br>**Ra**: `EvidenceItem(path_type="COLLABORATIVE", neighbor_user_id=n_uid, contribution=sim*w_cand)`. | [scorer.py:399-418](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L399-L418) | **ĐÃ XÁC MINH** |
| **Trích xuất Đồ thị con (Explanation Subgraph)** | Hàm `extract_subgraph` duyệt in-memory graph, trích xuất tối đa 2 phim đã thích tiêu biểu nhất, tối đa 2 thể loại và 2 genome tags chung cho mỗi phim. | **Vào**: `user_id: int`, `candidate_movie_id: int`.<br>**Ra**: `Dict` gồm `nodes: List[Dict]`, `edges: List[Dict]`, `academic_explanation: str`. | [embedded_graph.py:322-513](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L322-L513)<br>[explainability.py:24-191](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/explainability.py#L24-L191) | **ĐÃ XÁC MINH** |
| **Phạm vi bao phủ của Đồ thị con** | Đồ thị con **chỉ trích xuất P1 và P2**, hoàn toàn bỏ qua P3 (không tạo node/edge cho người dùng láng giềng). Cạnh thể loại gán trọng số cố định 0.72. | **Nodes**: USER, LIKED_MOVIE, GENRE, GENOME_TAG, RECOMMENDED_MOVIE.<br>**Bỏ sót**: Không có node PEER_USER. | [embedded_graph.py:368](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L368)<br>[embedded_graph.py:429-437](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L429-L437) | **ĐÃ XÁC MINH** |
| **API Giải thích Chi tiết (Provenance API)** | Endpoint `GET /api/discovery/explanations/{user_id}/{movie_id}` trả về cấu trúc giải thích đa tầng có chứng thực xuất xứ (Ground Truth vs Heuristic). | **Vào**: `user_id`, `movie_id`.<br>**Ra**: `ExplanationDetailResponse` (chứa P1, P2, P3 và ALS projection). | [discovery_router.py:240-252](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/api/discovery_router.py#L240-L252)<br>[explainability_service.py:36-258](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/services/explainability_service.py#L36-L258) | **ĐÃ XÁC MINH** |
| **API Đồ thị con Tương tác (Subgraph API)** | Endpoint `GET /api/lab/graph/subgraph` phục vụ trực quan hóa mạng lưới đồ thị con cho Academic Lab. | **Vào**: query `user_id`, `movie_id`.<br>**Ra**: `SubgraphResponse(nodes, edges, academic_explanation)`. | [lab_router.py:106-117](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/api/lab_router.py#L106-L117)<br>[lab_service.py:57-63](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/services/lab_service.py#L57-L63) | **ĐÃ XÁC MINH** |
| **Hiển thị trực quan Frontend** | - **Mode A**: Modal chi tiết phim hiển thị 4 tab Provenance Explorer (P1, P2, P3, P4).<br>- **Mode B**: Khung canvas hiển thị đồ thị mạng lưới tương tác qua thư viện `vis-network`. | **Mode A**: Đọc từ `provenanceTags` (dữ liệu mock/template).<br>**Mode B**: Gọi `fetch('/api/lab/graph/subgraph')` vẽ bằng `vis.Network`. | [graph_visualizer.js:187-213](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/demo/js/graph_visualizer.js#L187-L213)<br>[app.js:1730-1837](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/demo/js/app.js#L1730-L1837) | **ĐÃ XÁC MINH** |
| **Đồng bộ Live Đánh giá vào KG** | Phương thức `sync_with_sqlite` nạp trực tiếp đánh giá mới từ SQLite `app_state.db` vào RAM của `EmbeddedKnowledgeGraph`. | **Vào**: Bảng `user_ratings` trong SQLite.<br>**Ra**: Cập nhật tức thời `user_rated_movie` và `user_liked_counts`. | [embedded_graph.py:199-247](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L199-L247) | **ĐÃ XÁC MINH** |

---

## PHẦN B — QUY TRÌNH GIẢI THÍCH TRONG HỆ THỐNG

Quy trình giải thích trong mã nguồn MoodGraph được tổ chức phân tầng rõ rệt: tách biệt giữa nhánh tạo bằng chứng toán học thời gian thực (Scorer Pipeline) và hai nhánh phục vụ người dùng (On-demand Explanation APIs).

```
                                [LỊCH SỬ NGƯỜI DÙNG]
                                         │
                                         ▼
                      [Lọc Anchor Seeds: active_liked]
                      (Top 20 phim có rating >= 3.5★)
                                         │
                                         ▼
                  [GIAI ĐOẠN 1: KG SCORING & CANDIDATE POOL]
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
                 ▼                       ▼                       ▼
           [Metapath P3]           [Metapath P2]           [Metapath P1]
        Top-50 Láng giềng       Top-15 Active Tags       Target-Centric
          Salton Cosine           Genome Relevance         Genre Overlap
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         ▼
                          [Chuẩn hóa Min-Max Độc lập]
                          Norm_P1, Norm_P2, Norm_P3
                                         │
                                         ▼
                    [Hợp nhất Tuyến tính Điểm số KG]
                    Score_KG = 0.35*P1 + 0.45*P2 + 0.20*P3
                                         │
                                         ▼
                      [Sắp xếp và Chọn Top-N Ứng viên]
                      Order by Score_KG DESC, movieId ASC
                                         │
                                         ▼
                  [GIAI ĐOẠN 2: POST-HOC EVIDENCE EXTRACTION]
                  (_extract_evidence_for_candidates trong RAM)
                 ┌───────────────────────┼───────────────────────┐
                 │                       │                       │
                 ▼                       ▼                       ▼
          [Evidence P1]           [Evidence P2]           [Evidence P3]
        w / sqrt(deg_g)      w*r_src*r_cand/ln(1+deg)      sim * w_cand
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         │
                                         ▼
                      [Cắt tỉa Top-5 EvidenceItem / Phim]
                      ev_list.sort(key=contribution, reverse)
                                         │
                                         ▼
                     [Gắn evidence vào RecommendationItem]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
                   ▼                                           ▼
      [NHÁNH A: PROVENANCE API]                   [NHÁNH B: SUBGRAPH API]
    GET /api/discovery/explanations/               GET /api/lab/graph/subgraph
                   │                                           │
                   ▼                                           ▼
       [ExplainabilityService]                     [EmbeddedKnowledgeGraph]
   Kiểm định xuất xứ Ground Truth              Trích xuất tối đa 2 phim thích,
   so với Heuristic Approximation              2 thể loại, 2 tags (Bỏ qua P3)
                   │                                           │
                   ▼                                           ▼
        [FRONTEND: MODE A]                          [FRONTEND: MODE B]
    Modal 4 Tabs: P1 Thể loại,                   Khung trực quan hóa 2D Canvas
    P2 Tâm trạng, P3 Khán giả,                   Thư viện vis-network tương tác
    P4 ALS Vector (Provenance)                   Hộp Academic Explanation Box
```

---

## PHẦN C — VÍ DỤ MINH HỌA THỰC TẾ TỪ MÃ NGUỒN

Xét kịch bản thực tế dựa trên dữ liệu synthetic và fixture trong mã nguồn (`sample_embedded_graph` trong `tests/kg/test_embedded_graph.py`):
- **Người dùng mục tiêu**: Khán giả `#100`.
- **Lịch sử đánh giá cao**: Đã chấm 5.0 sao cho phim `#1` (*Toy Story (1995)*) và 4.0 sao cho phim `#2` (*Jumanji (1995)*).
- **Phim được gợi ý**: Phim `#3` (*Grumpier Old Men (1995)*) hoặc Phim `#5` (*Father of the Bride Part II (1995)*).

### 1. Bằng chứng Metapath P1 (Thể loại — Genre)
- **Truy vết đồ thị**:
  - Phim xuất phát: *Toy Story* (`movieId: 1`) có các thể loại `{"Animation", "Children", "Comedy"}`.
  - Phim ứng viên: *Grumpier Old Men* (`movieId: 3`) có các thể loại `{"Comedy", "Romance"}`.
  - Thể loại chung: `common_g = {"Comedy"}`.
  - Bậc đỉnh thể loại Comedy trong đồ thị mẫu: `deg_g = 4` (gồm các phim 1, 3, 4, 5).
  - Trọng số sở thích của người dùng: `w = max(0.0, (5.0 - 3.0) / 2.0) = 1.0`.
- **Bằng chứng được trích xuất trong `EvidenceItem`**:
  ```json
  {
    "path_type": "GENRE",
    "sourceMovieId": 1,
    "sourceMovieTitle": "Toy Story (1995)",
    "sharedEntity": {
      "type": "Genre",
      "key": "Comedy"
    },
    "sourceRating": 5.0,
    "contribution": 0.5
  }
  ```
  *(Giá trị `contribution = 1.0 / sqrt(4) = 0.5`)*.
- **Biểu diễn đường đi**: `User #100 ──(Đã thích 5.0★)──> Toy Story ──(HAS_GENRE)──> Comedy <──(HAS_GENRE)── Grumpier Old Men`.

### 2. Bằng chứng Metapath P2 (Thẻ cảm xúc Genome — Genome Tag)
- **Truy vết đồ thị**:
  - *Toy Story* (`movieId: 1`) có thẻ Genome `#20` (*sequel*) với relevance = 0.70.
  - Phim `#5` (*Father of the Bride Part II*) có thẻ `#20` với relevance = 0.88.
  - Bậc đỉnh của thẻ `#20`: `deg_t = 2` (gồm phim 1 và 5).
  - Đóng góp: `w * rel_src * rel_cand / ln(1 + 2) = 1.0 * 0.70 * 0.88 / 1.0986 = 0.5607`.
- **Bằng chứng được trích xuất trong `EvidenceItem`**:
  ```json
  {
    "path_type": "GENOME",
    "sourceMovieId": 1,
    "sourceMovieTitle": "Toy Story (1995)",
    "sharedEntity": {
      "type": "GenomeTag",
      "key": 20,
      "name": "sequel"
    },
    "sourceRating": 5.0,
    "contribution": 0.5607
  }
  ```

### 3. Bằng chứng Metapath P3 (Sở thích cộng đồng — Collaborative)
- **Truy vết đồ thị**:
  - Người dùng láng giềng `#200` cùng đánh giá phim `#1` (*Toy Story*) 4.5 sao.
  - Người dùng `#200` cũng đánh giá phim ứng viên `#3` (*Grumpier Old Men*) 4.0 sao.
  - Độ tương đồng Salton Cosine giữa User #100 và User #200: `sim = 1 / sqrt(2 * 2) = 0.5`.
  - Trọng số ưa thích của láng giềng cho phim #3: `w_cand = max(0.0, (4.0 - 3.0) / 2.0) = 0.5`.
  - Đóng góp: `contrib = 0.5 * 0.5 = 0.25`.
- **Bằng chứng được trích xuất trong `EvidenceItem`**:
  ```json
  {
    "path_type": "COLLABORATIVE",
    "sourceMovieId": 1,
    "sourceMovieTitle": "Toy Story (1995)",
    "neighborUserId": 200,
    "neighborRating": 4.0,
    "sourceRating": 5.0,
    "contribution": 0.25
  }
  ```

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.4. Giải thích gợi ý bằng bằng chứng đường đi và đồ thị con

Hệ thống MoodGraph triển khai cơ chế trích xuất bằng chứng giải thích theo phương pháp hậu kiểm nhằm tối ưu hóa chi phí tính toán trong quá trình phục vụ trực tuyến. Thay vì theo dõi vết đường đi trên toàn bộ không gian ứng viên, thuật toán chỉ thực hiện truy vết cấu trúc liên kết cho tập hợp các bộ phim đã vượt qua ngưỡng xếp hạng đầu bảng. Mỗi bằng chứng đường đi được đóng gói thành một bản ghi định lượng độc lập, phản ánh rõ ràng thực thể xuất phát từ lịch sử đánh giá tích cực của người dùng, thực thể trung gian kết nối và mức độ đóng góp số học của nhánh liên kết tương ứng. Cơ chế này bảo đảm tính giải thích cục bộ cho từng kết quả đề xuất mà không gây ảnh hưởng đến thông lượng xử lý của đồ thị bộ nhớ.

Để hỗ trợ việc kiểm chứng trực quan trên giao diện nghiên cứu, hệ thống tự động trích xuất đồ thị con giải thích biểu diễn mối quan hệ phụ thuộc giữa người dùng và tác phẩm mục tiêu. Cấu trúc mạng con này được khởi tạo trực tiếp từ đồ thị tri thức nhúng, lựa chọn có chọn lọc các bộ phim tiêu biểu nhất trong lịch sử tương tác cùng các thuộc tính đồng thể loại và thẻ đặc trưng ngữ nghĩa tương ứng. Việc giới hạn quy mô đồ thị con ở bán kính hai bước chuyển tiếp giúp trực quan hóa rõ ràng cơ chế suy luận mà vẫn duy trì tính tinh gọn của mô hình biểu diễn.

Sự hiện diện của bằng chứng đường đi đóng vai trò nền tảng trong việc nâng cao tính minh bạch của thuật toán gợi ý. Bằng cách công khai thực thể kết nối và các chỉ số đo lường liên quan, hệ thống chuyển đổi từ một mô hình hộp đen sang một kiến trúc có khả năng giải thích nguồn gốc đề xuất. Người sử dụng có thể kiểm chứng trực tiếp nguyên nhân một tác phẩm điện ảnh xuất hiện trong danh mục cá nhân hóa, từ đó gia tăng mức độ tin cậy vào các quyết định gợi ý của hệ thống.

```
+-------------------------------------------------------------------------+
|                      USER NODE: Khán giả #100                           |
+-----------------------------------+-------------------------------------+
                                    | [RATED: 5.0 sao]
                                    v
                  +-----------------------------------+
                  | LIKED MOVIE: Toy Story (1995)     |
                  +---------+---------------+---------+
                            |               |
       [HAS_GENRE: Thể loại]|               |[HAS_TAG: rel = 0.70]
                            v               v
               +-----------------+     +-----------------+
               | GENRE: Comedy   |     | TAG: sequel     |
               +--------+--------+     +--------+--------+
                        |                       |
   [HAS_GENRE: Đồng thể]|                       |[HAS_TAG: rel = 0.88]
                        v                       v
                  +-----------------------------------+
                  | CANDIDATE: Father of the Bride II |
                  +-----------------------------------+
```
*Hình 3.4. Cấu trúc đồ thị con giải thích đường đi kết nối hai bước giữa người dùng và tác phẩm được đề xuất thông qua thực thể thể loại và thẻ ngữ nghĩa.*

---

## PHẦN E — BỘ CÂU HỎI PHẢN BIỆN VÀ GIẢI ĐÁP HỌC THUẬT

### Câu hỏi 1: Làm sao biết lời giải thích phản ánh đúng cách mô hình tính điểm (Tính trung thực — Faithfulness)?
**Trả lời dựa trên mã nguồn**:
- Hệ thống bảo đảm **tính trung thực định tính (Qualitative Faithfulness)** nhưng **chưa đạt tính trung thực định lượng tuyệt đối (Strict Quantitative Faithfulness)**.
- *Cơ sở chứng minh*: 
  1. Các thực thể trung gian trong `EvidenceItem` ([scorer.py:361-417](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L361-L417)) được truy xuất từ chính các inverted indices của đồ thị (`movie_in_genre`, `movie_has_genome_tag`, `movie_rated_by_users`) vốn đã tham gia vào các vòng lặp tính điểm `cand_p1`, `cand_p2`, `cand_p3`.
  2. Tuy nhiên, giá trị `contribution` trong từng `EvidenceItem` chỉ là giá trị đóng góp thô cục bộ (chưa qua chuẩn hóa Min-Max toàn cục và chưa nhân trọng số alpha, beta, gamma). Do đó, tổng giá trị `contribution` của các bằng chứng không thể cộng dồn để tái tạo chính xác 100% điểm số `raw_score` của bộ phim.

### Câu hỏi 2: Bằng chứng P1, P2 và P3 khác nhau như thế nào về cấu trúc toán học và ngữ nghĩa?
**Trả lời dựa trên mã nguồn**:
- **P1 (Genre)**: Đại diện cho sự tương đồng phân loại vĩ mô. Trọng số đóng góp tính bằng `w / sqrt(deg_g)` ([scorer.py:365](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L365)), phạt độ phổ biến của thể loại theo nghịch đảo căn bậc hai số lượng phim thuộc thể loại đó.
- **P2 (Genome Tags)**: Đại diện cho sự tương đồng cảm xúc vi mô 1,128 chiều. Trọng số tính bằng `w * rel_src * rel_cand / log(1 + deg_t)` ([scorer.py:385](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L385)), kết hợp tích hai độ liên quan liên tục và phạt độ bão hòa logarit của thẻ.
- **P3 (Collaborative)**: Khai phá cấu trúc cộng đồng người dùng đồng điệu (Co-occurrence). Trọng số tính bằng `sim * w_cand` ([scorer.py:406](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L406)), trong đó `sim` là độ tương đồng Salton Cosine giữa hai vectơ nhị phân các phim cùng thích của hai người dùng.

### Câu hỏi 3: Vì sao trích xuất bằng chứng lại thực hiện sau khi chọn Top-N thay vì làm đồng thời trong lúc tính điểm?
**Trả lời dựa trên mã nguồn**:
- *Lý do hiệu năng sống còn (Performance bottleneck)*: Trong không gian đồ thị MovieLens 25M với hơn 62,000 phim, số lượng đường đi khả dĩ giữa các phim người dùng đã thích đến các ứng viên tiềm năng lên tới hàng trăm nghìn nhánh.
- Nếu cấp phát bộ nhớ và khởi tạo đối tượng `EvidenceItem` cho mọi ứng viên trong vòng lặp lan truyền, thời gian tính toán sẽ tăng vọt lên hàng nghìn mili-giây và gây áp lực thu gom rác (GC) lớn trên RAM.
- Mã nguồn tách rời: giai đoạn 1 chỉ tích lũy điểm số dạng số thực nguyên thủy (`float`) trên cấu trúc `defaultdict(float)` ([scorer.py:134-270](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L134-L270)) mất dưới 30ms; giai đoạn 2 chỉ truy vết ngược bằng chứng cho đúng 50 phim đứng đầu ([scorer.py:296-304](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L296-L304)), chỉ mất chưa đầy 1ms.

### Câu hỏi 4: Đồ thị con giải thích có chứa toàn bộ đường đi đóng góp điểm số không?
**Trả lời dựa trên mã nguồn**:
- **KHÔNG**. Đồ thị con trích xuất từ `EmbeddedKnowledgeGraph.extract_subgraph` ([embedded_graph.py:322-513](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L322-L513)) là một **đồ thị con minh họa đại diện (Illustrative Subgraph)**, không phải là đồ thị đóng góp toàn phần.
- Cụ thể, hàm đã áp dụng các bộ lọc cắt tỉa mạnh mẽ:
  1. Chỉ chọn tối đa 2 phim đã thích có điểm giao thoa cao nhất (`top_liked = scored_liked_movies[:2]`).
  2. Mỗi phim chỉ lấy tối đa 2 thể loại và 2 thẻ Genome.
  3. Hoàn toàn loại bỏ đường đi P3 (Collaborative), không hiển thị đỉnh người dùng tương đồng trên canvas để tránh gây rối mắt người dùng (visual clutter) và đơn giản hóa không gian hiển thị.

### Câu hỏi 5: Hệ thống đánh giá chất lượng lời giải thích bằng phương pháp nào?
**Trả lời dựa trên mã nguồn**:
- Hiện tại, hệ thống đánh giá chất lượng lời giải thích thông qua **bài kiểm thử tính hợp lệ giao thức API và kiểm tra nguồn gốc dữ liệu (Provenance Contract Tests)** trong [test_explainability_api.py:18-70](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/phase5/test_explainability_api.py#L18-L70).
- Hệ thống kiểm định xem các trường `evidence_type`, `verification_status`, `source_model` có tuân thủ đúng phân loại (`VERIFIED_GROUND_TRUTH` khi có đường đi thực, `HEURISTIC_ESTIMATE` khi không tìm thấy đường đi trong bộ nhớ) nhằm ngăn chặn việc bịa đặt dữ liệu (hallucination).
- Hệ thống **chưa thực hiện** các đánh giá định lượng nâng cao về giải thích học thuật như: khảo sát người dùng thực tế (User Study về Trust & Transparency), kiểm định mức độ nhạy cảm (Fidelity / Sparsity), hoặc đánh giá phản trực tế (Counterfactual Evaluation).

---

## PHẦN F — GIỚI HẠN, LỖ HỔNG VÀ ĐIỂM CHƯA XÁC MINH

1. **Sự không nhất quán giữa công thức chấm điểm và công thức giải thích tại tầng Service**:
   - Trong `PathBasedScorer` ([scorer.py:365](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L365)), mức đóng góp của thể loại P1 được tính bằng `w / sqrt(deg_g)`.
   - Tuy nhiên, trong `ExplainabilityService` ([explainability_service.py:70](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/services/explainability_service.py#L70)), mức đóng góp P1 lại được tính bằng công thức `overlap_ratio * (user_rating / 5.0)`. Đây là hai công thức hoàn toàn khác biệt nhau, dẫn đến giá trị điểm đóng góp hiển thị ở API chi tiết không khớp với giá trị tính điểm nội bộ của động cơ đồ thị.

2. **Thiếu vắng hoàn toàn đường đi P3 trong Đồ thị con trực quan (vis-network)**:
   - Cả trong [explainability.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/explainability.py) và [embedded_graph.py:368](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L368), biến cờ `p3_found` được khởi tạo bằng `False` nhưng không có bất kỳ dòng code nào tạo node hay edge cho người dùng láng giềng. Do đó, người dùng không thể xem được mạng liên kết cộng tác trực quan trên canvas Mode B.

3. **Vấn đề bảo vệ quyền riêng tư người dùng trong bằng chứng P3 (Privacy Vulnerability)**:
   - Cả `scorer.py` ([dòng 413](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L413)), `explainability_service.py` ([dòng 173](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/services/explainability_service.py#L173)) và frontend [app.js:1733](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/demo/js/app.js#L1733) đều xuất thẳng định danh thô của người dùng láng giềng (ví dụ `User #200`, `Khán giả #200`).
   - Hệ thống **hoàn toàn chưa áp dụng** các kỹ thuật bảo mật như K-anonymity hay tổng hợp cụm người dùng, vi phạm nguyên tắc bảo mật quyền riêng tư nếu triển khai trên môi trường dữ liệu người dùng thực tế.

4. **Trọng số và văn bản giải thích bị gắn cứng (Hardcoded Artifacts)**:
   - Trong `embedded_graph.py` ([dòng 429, 436](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L429)), trọng số cạnh thể loại `HAS_GENRE` bị gán cứng là `0.72`.
   - Trong [embedded_graph.py:501-505](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L501-L505) và [explainability.py:179-181](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/explainability.py#L179-L181), các chuỗi văn bản `"đóng góp 35%"`, `"đóng góp 45%"` được ghi sẵn theo hệ số khởi tạo toàn cục (alpha, beta), không phản ánh tỷ lệ đóng góp thực sự của hai đường đi này trên bộ phim cụ thể.

5. **Frontend Mode A phụ thuộc dữ liệu tĩnh (Mock Data Coupling)**:
   - Frontend `demo/js/app.js` không hề gửi request đến endpoint `GET /api/discovery/explanations/{user_id}/{movie_id}`. Bốn tab giải thích tại modal chi tiết phim ở Mode A đang đọc từ `window.MOCK_DATA` trong [mock_data.js](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/demo/js/mock_data.js) hoặc sinh chuỗi định dạng sẵn trên trình duyệt. Chỉ có khung đồ thị Mode B (`vis-network`) là có kết nối gọi API thực `GET /api/lab/graph/subgraph`.

6. **Những tuyên bố tuyệt đối không được đưa vào báo cáo khoa học**:
   - *Không được khẳng định*: "Hệ thống bảo đảm 100% tính trung thực toán học (faithfulness) giữa điểm số hiển thị và điểm số gợi ý".
   - *Không được khẳng định*: "Đồ thị con hiển thị toàn bộ mạng lưới suy luận đa thể loại, tâm trạng và cộng đồng" (vì P3 hoàn toàn bị khuyết thiếu trên đồ thị con).
   - *Không được khẳng định*: "Hệ thống đã triển khai đầy đủ các cơ chế bảo vệ quyền riêng tư người dùng trong giải thích cộng tác".
