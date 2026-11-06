# BÁO CÁO KIẾN TRÚC & HỢP ĐỒNG DỮ LIỆU HYBRID RECOMMENDER (PHASE 4)

## 1. TỔNG QUAN KIẾN TRÚC TÍCH HỢP HỢP NHẤT

Hệ thống gợi ý phim MoodGraph Phase 4 hiện thực hóa mô hình lai ghép (Hybrid Recommender) kết hợp hai trường phái bổ trợ chặt chẽ:
1. **Collaborative Filtering dựa trên Ma trận Tiềm ẩn (Spark ALS - Task 3A)**: Mô hình finalist đã đóng băng `ALS_R8_REG0.3_ITER10` (Latent Factor Rank=8, Regularization=0.3, Max Iterations=10). Mô hình có khả năng khai thác hành vi ẩn, bao quát không gian người dùng - vật phẩm lớn với tốc độ suy luận microsecond thông qua phép nhân ma trận BLAS trên CPU.
2. **Knowledge Graph dựa trên Đường đi Ngữ nghĩa (Task 3B)**: Đồ thị tri thức hợp nhất 3 đường đi (Metapaths P1 Genre, P2 Genome Tag, P3 Collaborative Graph). Mô hình cung cấp khả năng khám phá quan hệ đa chiều và bằng chứng giải thích nguồn gốc (Explainability) trực tiếp từ các thực thể ngữ nghĩa.

```
                      +-----------------------------+
                      |       Request (userId)      |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   In-Memory LRU / TTL Cache |
                      +--------------+--------------+
                                     | (Cache Miss)
                    +----------------+----------------+
                    |                                 |
                    v                                 v
     +------------------------------+  +------------------------------+
     |      Spark ALS Service       |  |    Knowledge Graph Engine    |
     |   (ALS_R8_REG0.3_ITER10)     |  |       (P1 + P2 + P3)         |
     +--------------+---------------+  +--------------+---------------+
                    | C_ALS(u)                        | C_KG(u)
                    +----------------+----------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Candidate Union & Defense  |
                      |   C_hybrid = C_ALS U C_KG   |
                      |   Seen Filter: Train_u      |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |       Fusion Strategy       |
                      | - Reciprocal Rank (RRF)     |
                      | - Weighted Score Fusion     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Deterministic Tie-Breaking  |
                      | Score DESC, MovieId ASC     |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Evidence & Title Enrichment |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |    Serving Response / API   |
                      +-----------------------------+
```

---

## 2. HỢP ĐỒNG DỮ LIỆU & SCHEMA CHUẨN HÓA

### 2.1. Cấu trúc bản ghi gợi ý (HybridRecommendationItem)
Mỗi bộ phim được gợi ý tuân thủ dataclass chuẩn hóa `recommender.hybrid.contracts.HybridRecommendationItem`:

- `userId` (int, 64-bit MovieLens ID): Định danh người dùng.
- `movieId` (int, 64-bit MovieLens ID): Định danh bộ phim.
- `title` (Optional[str]): Tên phim và năm phát hành chuẩn hóa.
- `hybrid_score` (float, finite): Điểm số dung hợp cuối cùng dùng để xếp hạng.
- `rank` (int, >= 1): Thứ hạng của phim trong danh sách Top-N.
- `source` (str): Nguồn gốc sinh ứng viên (`ALS`, `KG`, `BOTH`).
- `fusion_method` (str): Phương pháp dung hợp được áp dụng (`rrf`, `weighted`, `als_only`, `kg_only`).
- `als_raw_score` (Optional[float]): Điểm tích vô hướng dot-product từ ALS (nếu có).
- `als_normalized_score` (Optional[float]): Điểm ALS sau chuẩn hóa Min-Max hoặc đóng góp hạng RRF.
- `als_rank` (Optional[int]): Thứ hạng gốc của phim trong danh sách ứng viên ALS.
- `kg_raw_score` (Optional[float]): Điểm tích lũy theo đường đi từ KG (nếu có).
- `kg_normalized_score` (Optional[float]): Điểm KG sau chuẩn hóa Min-Max hoặc đóng góp hạng RRF.
- `kg_rank` (Optional[int]): Thứ hạng gốc của phim trong danh sách ứng viên KG.
- `evidence` (List[Dict[str, Any]]): Danh sách bằng chứng giải thích chi tiết.

### 2.2. Cấu trúc phản hồi tổng thể (HybridRecommendationResponse)
- `userId` (int): ID người dùng được phục vụ.
- `recommendations` (List[HybridRecommendationItem]): Danh sách Top-N gợi ý.
- `metadata` (Dict[str, Any]): Các chỉ số đo lường hiệu năng và vận hành:
  * `latency_ms`: Thời gian xử lý yêu cầu tính bằng mili-giây.
  * `cache_hit`: Trạng thái trúng bộ nhớ đệm (`True` / `False`).
  * `fusion_strategy`: Chiến lược dung hợp đang kích hoạt.
  * `is_cold_start`: Cờ báo hiệu người dùng mới (Cold-Start).
  * `candidate_count_als`: Số lượng ứng viên do ALS sinh ra.
  * `candidate_count_kg`: Số lượng ứng viên do KG sinh ra.
  * `candidate_count_union`: Kích thước tập hợp hợp nhất trước khi cắt tỉa.

---

## 3. CƠ CHẾ SINH ỨNG VIÊN & HỢP NHẤT TẬP HỢP

### 3.1. Hợp nhất ứng viên (Candidate Union)
Hệ thống truy xuất độc lập:
- Tập ứng viên ALS: `C_ALS(u)` với kích thước `top_k_candidates_als` (mặc định 50).
- Tập ứng viên KG: `C_KG(u)` với kích thước `top_k_candidates_kg` (mặc định 50).

Tập hợp hợp nhất được định nghĩa:
`C_hybrid(u) = C_ALS(u) ∪ C_KG(u)`

Lực lượng tập hợp thỏa mãn: `max(|C_ALS|, |C_KG|) <= |C_hybrid| <= |C_ALS| + |C_KG|`.

### 3.2. Lọc lịch sử đã xem nhiều lớp (Defense-in-depth Seen Filtering)
- Tầng 1: Bên trong `ALSDeliveryService`, lịch sử Train được lọc ở mức microsecond thông qua cấu trúc CSR nén `train_seen_csr.npz`.
- Tầng 2: Bên trong `recommend_kg`, đồ thị bỏ qua các phim đã nằm trong lịch sử `user_rated_movie`.
- Tầng 3: Bên trong `HybridRecommenderService`, sau khi hợp nhất `C_hybrid`, hệ thống đối chiếu lại tập `seen_movies` để triệt tiêu hoàn toàn khả năng rò rỉ dữ liệu đã xem vào danh sách phục vụ.

---

## 4. CHIẾN LƯỢC DUNG HỢP (FUSION STRATEGIES)

### 4.1. Reciprocal Rank Fusion (RRF)
RRF là giải thuật dung hợp thứ hạng độc lập với thang đo điểm số gốc (scale-invariant), loại bỏ rủi ro lệch phân phối điểm giữa hai hệ thống:

`RRF_score(m) = sum_{s in {ALS, KG}} (1.0 / (k + rank_s(m)))` nếu `m in C_s(u)` ngược lại bằng 0.

Hằng số làm mịn mặc định: `k = 60`.

### 4.2. Weighted Score Fusion
Kết hợp tuyến tính điểm số thành phần sau khi chuẩn hóa về cùng không gian [0.0, 1.0]:

`Weighted_score(m) = w_ALS * norm_ALS(m) + w_KG * norm_KG(m)`

- Chuẩn hóa Min-Max:
  `norm_s(m) = (score_s(m) - min_s) / (max_s - min_s)` nếu `max_s > min_s` ngược lại gán 1.0.
- Cơ chế nội suy (Imputation):
  Đối với các ứng viên chỉ xuất hiện ở một nguồn, giá trị điểm nguồn còn lại được nội suy trung tính `0.0`.

### 4.3. Quy tắc phá vỡ hòa điểm tất định (Deterministic Tie-Breaking)
Mọi danh sách gợi ý bắt buộc được sắp xếp theo tiêu chí:
1. `hybrid_score DESC` (Điểm dung hợp giảm dần).
2. `movieId ASC` (ID phim tăng dần khi điểm số bằng nhau).

Quy tắc này bảo đảm 100% tính tái lập (reproducibility) trong kiểm thử hồi quy và vận hành thực tế.

---

## 5. BẢO TOÀN TÍNH KHẢ GIẢI (EXPLAINABILITY PRESERVATION)

- **Ứng viên từ KG**: Bảo toàn toàn bộ chuỗi bằng chứng ngữ nghĩa (`GENRE`, `GENOME`, `COLLABORATIVE`) từ đồ thị tri thức, ghi nhận rõ phim nguồn, thực thể chia sẻ và mức độ đóng góp (contribution).
- **Ứng viên chỉ từ ALS**: Hệ thống giải thích trung thực bằng cơ chế nhân tử tiềm ẩn:
  `{"path_type": "ALS_LATENT_FACTOR", "model_version": "ALS_R8_REG0.3_ITER10", "description": "High collaborative affinity in latent matrix factorization space"}`.
  Tuyệt đối không tự ngụy tạo đường đi đồ thị giả mạo cho các ứng viên ALS.
- **Ứng viên thuộc cả hai bên (BOTH)**: Kết hợp bằng chứng đồ thị của KG và chú thích điểm tương hỗ của ALS.

