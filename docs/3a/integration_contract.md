# MOODGRAPH | TASK 3A -> TASK 3B HYBRID INTEGRATION CONTRACT
# Specification for Collaborative Filtering (ALS) & Knowledge Graph (KG) Recommendation Fusion

## 1. Executive Summary & Purpose

Tài liệu này xác lập hợp đồng giao diện kỹ thuật (Technical Integration Contract) chuẩn giữa thành phần Collaborative Filtering (Spark ALS, Module Task 3A) và thành phần Knowledge Graph (KG Recommender, Module Task 3B) trong hệ thống gợi ý lai MoodGraph.

Mục tiêu cốt lõi:
- Đảm bảo tính độc lập module (Separation of Concerns): Task 3A chịu trách nhiệm candidate generation dựa trên tương tác hành vi người dùng; Task 3B chịu trách nhiệm candidate generation và giải thích thực thể (semantic explanations) dựa trên tri thức đồ thị.
- Ngăn chặn lỗi thiết kế phổ biến: Không bao giờ ép buộc Knowledge Graph chỉ được xếp hạng lại (rerank) trên Top-20 của ALS.
- Quy định giao thức định danh đồng nhất: Cả hai thành phần cùng giao tiếp qua original MovieLens `userId` (int64) và `movieId` (int64).
- Nghiêm cấm cộng trực tiếp điểm số thô chưa chuẩn hóa (prohibit uncalibrated raw score addition).

---

## 2. Shared Identity Schema & Identifier Mapping

### 2.1 Identifier Definitions
- `userId`: 64-bit integer (`int64`), đại diện cho ID người dùng thực trong bộ dữ liệu MovieLens 25M. Phạm vi giá trị: `[1, 162541]`.
- `movieId`: 64-bit integer (`int64`), đại diện cho ID phim gốc của MovieLens 25M. Phạm vi giá trị: `[1, 209171]`. Phù hợp trực tiếp với trường `id` trong bảng `movies.parquet` và các node entity trong Knowledge Graph (Task 3B).

### 2.2 Spark ALS Internal Index Mapping
Mô hình Spark ALS huấn luyện trên chỉ số nội bộ 32-bit (`user_idx`, `movie_idx`). Thành phần Task 3A chịu trách nhiệm hoàn toàn việc ánh xạ ngược từ `movie_idx` về `movieId` gốc trước khi xuất danh sách gợi ý ra ngoài:

```text
[Internal Matrix Factorization]
user_idx (int32) x movie_idx (int32)
       |
       v (Internal Inverted Index)
original userId (int64) x original movieId (int64)
       |
       v (Delivery Service)
ALSRecommendationItem(userId, movieId, raw_score, rank, model_name, model_version, run_id)
```

Consumer của Task 3B và Hybrid Layer KHÔNG BAO GIỜ phải xử lý `user_idx` hay `movie_idx`.

---

## 3. Candidate Generation & Fusion Architecture

### 3.1 Architectural Principle: Independent Candidate Generation
Mô hình gợi ý lai MoodGraph áp dụng kiến trúc Candidate Union (Hợp tập ứng viên độc lập), KHÔNG áp dụng kiến trúc Sequential Filter (Lọc tuần tự):

```text
[User Request: userId]
       |
       +---------------------------------------+
       |                                       |
       v                                       v
[Task 3A: ALS Service]                [Task 3B: KG Service]
(Behavioral CF Retrieval)             (Semantic Graph Retrieval)
Top-K_ALS Candidates                  Top-K_KG Candidates
       |                                       |
       +-------------------+-------------------+
                           |
                           v
              [Candidate Union Layer]
         Union = Candidates_ALS ∪ Candidates_KG
                           |
                           v
            [Feature Extraction & Normalization]
              - ALS Normalized Score: S_ALS in [0, 1]
              - KG Normalized Score: S_KG in [0, 1]
                           |
                           v
            [Hybrid Reranker / Blender]
        Combined Score = w_ALS * S_ALS + w_KG * S_KG
                           |
                           v
                 [Final Top-K Hybrid]
```

### 3.2 Formal Prohibition: No Forced ALS-Only Filtering
Nghiêm cấm tuyệt đối quy trình:
```text
CẤM: User -> ALS Top-20 -> Filter/Rerank by KG -> Final Top-K
```
Lý do:
1. Độ phủ danh mục (Item Coverage): ALS model `ALS_R8_REG0.3_ITER10` tập trung vào các phim phổ biến vừa và cao, có độ phủ danh mục trên tập Test khoảng 0.05% - 0.50%. Trong khi đó, Knowledge Graph bao phủ các quan hệ ngữ nghĩa (đạo diễn, diễn viên, thể loại, giải thưởng) vươn tới phần đuôi dài (long-tail items).
2. Cold-start Items: Những bộ phim mới có rất ít hoặc chưa có ratings sẽ bị ALS bỏ qua hoàn toàn. Nếu ép KG chỉ rerank trên output của ALS, toàn bộ sức mạnh khám phá thực thể mới của KG sẽ bị triệt tiêu 100%.

### 3.3 Candidate Union Contract
- Hợp tập ứng viên:
```text
Candidates_Hybrid = Set(movieId in Candidates_ALS) ∪ Set(movieId in Candidates_KG)
```
- Số lượng ứng viên hợp nhất:
```text
Max(len(Candidates_ALS), len(Candidates_KG)) <= len(Candidates_Hybrid) <= len(Candidates_ALS) + len(Candidates_KG)
```
- Bất kỳ item nào chỉ xuất hiện ở KG (`movieId in Candidates_KG \ Candidates_ALS`) vẫn phải được giữ lại trong Candidate Set để đưa vào bộ chấm điểm lai.

---

## 4. Score Calibration & Combination Contract

### 4.1 Score Distribution Reality
- **ALS Raw Score (`raw_score`)**:
  - Bản chất: Tích vô hướng của user factor vector và item factor vector: `score = dot(U_u, V_i)`.
  - Phân bố thực tế quan sát được trong M10: Giá trị dao động trong khoảng từ `0.05` đến `11.50` (hoặc âm đối với một số factor không ràng buộc).
  - Không bị chặn trên `1.0` hay `5.0`.
- **KG Raw Score**:
  - Bản chất: Điểm tương đồng đồ thị, Path confidence, hoặc xác suất suy luận quan hệ (TransE, RotatE, GCN, Path-based relevance).
  - Phân bố thường gặp: `[0.0, 1.0]` hoặc `[0.0, 10.0]`.

### 4.2 Prohibited Operation: Direct Raw Score Addition
Nghiêm cấm phép tính trực tiếp:
```python
# CẤM TUYỆT ĐỐI
hybrid_score = als_item.raw_score + kg_item.raw_score
```
Hậu quả nếu vi phạm:
Điểm số ALS với magnitude lớn (ví dụ 7.5 - 10.8) sẽ hoàn toàn áp đảo điểm số KG (ví dụ 0.65 - 0.85), biến hệ thống lai thành mô hình ALS thuần túy và vô hiệu hóa tín hiệu đồ thị.

### 4.3 Standard Normalization Methods for Fusion
Hybrid Module (Task 3B / Hybrid) bắt buộc phải chuẩn hóa điểm số trước khi phối hợp:

1. **Min-Max Normalization per User Candidate List**:
```text
S_norm(i) = (raw_score(i) - min_score) / (max_score - min_score + 1e-9)
```
Đưa điểm số của từng nguồn ứng viên về đoạn chuẩn `[0.0, 1.0]`.

2. **Rank-based Fusion (Reciprocal Rank Fusion - RRF)**:
```text
RRF_score(i) = 1 / (60 + rank_ALS(i)) + 1 / (60 + rank_KG(i))
```
Nếu item không nằm trong danh sách gợi ý của nguồn nào, giá trị reciprocal rank tương ứng bằng 0.

3. **Z-score Standardization**:
```text
Z_score(i) = (raw_score(i) - mu_user) / (sigma_user + 1e-9)
```

---

## 5. Output Data Schema & API Contract

### 5.1 Python Dataclass Schema
```python
@dataclass(frozen=True)
class ALSRecommendationItem:
    userId: int          # Original MovieLens userId (int64)
    movieId: int         # Original MovieLens movieId (int64)
    raw_score: float     # Uncalibrated inner-product dot(U_u, V_i)
    rank: int            # 1-based rank (1 to K)
    model_name: str      # Always "ALS"
    model_version: str   # Version identifier, e.g. "ALS_R8_REG0.3_ITER10"
    run_id: str          # Execution instance ID
```

### 5.2 Service Signatures
```python
def recommend_als(
    user_id: int,
    k: int = 10,
    filter_seen: bool = True
) -> List[ALSRecommendationItem]:
    """Sinh danh sách Top-K cho 1 user."""
    ...

def recommend_als_batch(
    user_ids: List[int],
    k: int = 10,
    filter_seen: bool = True,
    batch_size: int = 500
) -> Dict[int, List[ALSRecommendationItem]]:
    """Sinh danh sách Top-K cho batch user."""
    ...
```

### 5.3 Behavior on Edge Cases
- **Known User**: Trả về danh sách Top-K đúng hợp đồng, sắp xếp giảm dần theo `raw_score`, `rank` từ 1 đến K.
- **Cold User (User chưa từng xuất hiện trong Train set)**:
  - Trả về danh sách rỗng: `[]`.
  - KHÔNG trả về điểm 0.0 giả tạo.
  - KHÔNG tự tiện chèn fallback popularity vào danh sách ALS. Fallback là trách nhiệm của Hybrid Orchestrator.
- **Candidate Filtering**: Nếu `filter_seen=True`, các `movieId` đã nằm trong lịch sử tương tác Train của user sẽ bị lọc bỏ 100% trước khi chọn Top-K.

---

## 6. Verification and Compliance Test Suite

Tính tương thích của hợp đồng này được kiểm định tự động bằng test suite độc lập `tests/als/test_delivery.py`:
- `test_hybrid_consumer_contract_union_and_no_forced_rerank`: Kiểm tra khả năng tạo hợp tập và giữ lại các phim KG-only.
- `test_uncalibrated_raw_score_blending_prohibition`: Kiểm tra sự sai lệch tỷ trọng khi cộng điểm thô và tính đúng đắn của Min-Max Normalization.
- `test_als_recommendation_item_schema`: Kiểm tra tính toàn vẹn kiểu dữ liệu và trường thông tin.
- `test_unknown_user_returns_empty_list`: Kiểm tra hành vi cold-start sạch.

Toàn bộ 20 tests trong module delivery đã PASS, sẵn sàng 100% để tích hợp sang Task 3B.

