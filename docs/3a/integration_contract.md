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

### 2.2 Spark ALS Factor Identifier Mapping
Mô hình Spark ALS `ALS_R8_REG0.3_ITER10` được huấn luyện trực tiếp trên `userId` và `movieId` gốc của MovieLens (không qua bảng remapping dense 0-based gián tiếp):
- Trong bảng `itemFactors`, trường `id` mang trực tiếp giá trị `movieId` gốc (từ 1 đến 209171, bao phủ 58.932 phim có trong Train set).
- Ánh xạ giữa chỉ số hàng ma trận `0..58931` và `movieId` gốc là ánh xạ song ánh (bijective) được lưu trong `catalog.movie_ids`.
- Consumer của Task 3B và Hybrid Layer hoàn toàn nhận và truyền các `userId` và `movieId` gốc của MovieLens 25M.

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
        Combined Score = f(S_ALS, S_KG, Features)
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
1. Độ phủ danh mục (Item Coverage): Trên tập Test M08, mô hình ALS `ALS_R8_REG0.3_ITER10` chỉ tạo ra gợi ý trên 34 bộ phim duy nhất (tương ứng 0.054% catalog). Trong khi đó, Knowledge Graph bao phủ các quan hệ ngữ nghĩa vươn tới phần đuôi dài (long-tail items).
2. Cold-start Items: Những bộ phim có trong catalog nhưng không có trong Train ratings (ví dụ phim thật `movieId = 25817: Break of Hearts (1935)` đã kiểm chứng tại test case `test_22`) hoàn toàn không có vector trong ALS. Nếu ép KG chỉ rerank trên output của ALS, toàn bộ các phim khởi động lạnh này sẽ bị loại bỏ 100%.

### 3.3 Candidate Union Contract
- Hợp tập ứng viên:
```text
Candidates_Hybrid = Set(movieId in Candidates_ALS) ∪ Set(movieId in Candidates_KG)
```
- Số lượng ứng viên hợp nhất:
```text
Max(len(Candidates_ALS), len(Candidates_KG)) <= len(Candidates_Hybrid) <= len(Candidates_ALS) + len(Candidates_KG)
```
- Bất kỳ item nào chỉ xuất hiện ở KG (`movieId in Candidates_KG \ Candidates_ALS`) vẫn phải được giữ lại trong Candidate Set với `als_raw_score = None` (không được tự tiện gán điểm 0.0 giả tạo).

---

## 4. Score Calibration & Candidate Fusion Strategies

### 4.1 Score Distribution Reality
- **ALS Raw Score (`raw_score`)**:
  - Bản chất: Tích vô hướng của user factor vector và item factor vector: `score = dot(U_u, V_i)`.
  - Phân bố thực tế quan sát được trong M10: Giá trị dao động trong khoảng từ `0.05` đến `11.50`.
- **KG Raw Score**:
  - Bản chất: Điểm tương đồng đồ thị, Path confidence, hoặc khoảng cách TransE/RotatE chuẩn hóa trong khoảng `[0.0, 1.0]`.

### 4.2 Prohibited Operation: Direct Raw Score Addition
Nghiêm cấm phép tính trực tiếp:
```python
# CẤM TUYỆT ĐỐI
hybrid_score = als_item.raw_score + kg_item.raw_score
```
Hậu quả nếu vi phạm:
Điểm số ALS với magnitude lớn (~7.5 - 10.8) sẽ hoàn toàn áp đảo điểm số KG (~0.65 - 0.85), chiếm gần 90% tổng điểm và vô hiệu hóa tín hiệu đồ thị.

### 4.3 Candidate Fusion Strategies (Dành cho nhóm Hybrid đánh giá trên Validation)
Các chiến lược phối hợp cần được nhóm Hybrid thử nghiệm và tối ưu hóa trọng số:

1. **Min-Max Normalization per User Candidate List**:
```text
S_norm(i) = (raw_score(i) - min_score) / (max_score - min_score + 1e-9)
```
Đưa điểm số của từng nguồn ứng viên về đoạn chuẩn `[0.0, 1.0]`. Lưu ý: Trọng số danh định `0.5 * S_ALS + 0.5 * S_KG` chỉ là baseline mẫu, không bảo đảm tự động tạo ảnh hưởng thực tế ngang nhau; nhóm Hybrid cần điều chỉnh trọng số dựa trên độ đo Validation.

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
    top_n: int = 20,
    k: Optional[int] = None,
    filter_seen: bool = True,
    stage: str = "production",
) -> List[Dict[str, Any]]:
    """Sinh danh sách Top-N cho 1 user."""
    ...

def recommend_als_batch(
    user_ids: Sequence[int],
    top_n: int = 20,
    k: Optional[int] = None,
    filter_seen: bool = True,
    stage: str = "production",
) -> Dict[int, List[Dict[str, Any]]]:
    """Sinh danh sách Top-N cho batch user."""
    ...
```

### 5.3 Behavior on Edge Cases
- **Known User**: Trả về danh sách Top-K đúng hợp đồng, sắp xếp giảm dần theo `raw_score`, `rank` từ 1 đến K.
- **Cold User (User chưa từng xuất hiện trong Train set)**:
  - Trả về danh sách rỗng: `[]`.
  - KHÔNG trả về điểm 0.0 giả tạo.
  - Fallback là trách nhiệm của Hybrid Orchestrator.
- **Complete Seen Filtering**: Dịch vụ lọc bỏ 100% các phim đã tương tác trong Train set qua cấu trúc nén CSR `train_seen_csr.npz` (24.675.013 tương tác), đảm bảo 0% phim đã xem lọt vào danh sách gợi ý.
