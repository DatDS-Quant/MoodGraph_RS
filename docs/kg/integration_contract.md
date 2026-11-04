# HỢP ĐỒNG TÍCH HỢP TASK 3B VÀ KHỐI 4 HYBRID (INTEGRATION CONTRACT)

> **Dự án:** MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark  
> **Nhiệm vụ:** Task 3B — Knowledge Graph Recommender  
> **Tài liệu:** `docs/kg/integration_contract.md`  
> **Thời điểm lập:** 2026-11-04  
> **Người thực hiện:** Senior Python & Knowledge Graph Engineer (AI Assistant)

---

## 1. MỤC TIÊU VÀ NGUYÊN TẮC TÍCH HỢP

Task 3B (Knowledge Graph Recommender) và Task 3A (Spark ALS) được phát triển song song, độc lập nhưng cùng hướng đến việc cung cấp đầu vào cho **Khối 4: Hybrid Recommendation Engine**.

Các nguyên tắc bắt buộc:
1. **Độc lập tính toán:** Task 3B không phụ thuộc vào latent factors, điểm số hay danh sách Top-100 của ALS.
2. **Hợp tập ứng viên (Candidate Union):** Khối 4 không ép KG chỉ xếp hạng lại (rerank) danh sách của ALS, mà lấy hợp tập ứng viên từ cả hai nhánh:
   $$\mathcal{C}_{hybrid}(u) = \mathcal{C}_{ALS}(u) \cup \mathcal{C}_{KG}(u)$$
3. **Thang đo điểm độc lập:** Điểm số thô (`raw_score`) của KG không cùng thang đo với ALS. Khối 4 phải thực hiện chuẩn hóa (Min-Max hoặc Percentile Rank) trước khi dung hợp tuyến tính.
4. **Giải thích có thể kiểm chứng (Explainable Evidence):** Mọi đề xuất từ KG đều mang theo siêu dữ liệu chứng minh có thể truy ngược từ đồ thị.

---

## 2. ĐẶC TẢ GIAO DIỆN PYTHON (PYTHON FACADE API)

Module `recommender.kg.recommend` cung cấp hàm chuẩn hóa:

```python
def recommend_kg(
    user_id: int,
    top_n: int = 10,
    exclude_movie_ids: Optional[Set[int]] = None,
    graph: Optional[Any] = None,
    config: Optional[KGConfig] = None,
    enable_p1: bool = True,
    enable_p2: bool = True,
    enable_p3: bool = True
) -> List[Dict[str, Any]]:
    """
    Sinh danh sách Top-N gợi ý độc lập dựa trên Knowledge Graph.

    Args:
        user_id (int): ID người dùng cần gợi ý (phải là số nguyên dương).
        top_n (int): Số lượng phim gợi ý tối đa (mặc định: 10).
        exclude_movie_ids (Optional[Set[int]]): Tập movieId cần loại trừ 
            (bắt buộc loại trừ các phim đã xem trong Train; khi đo Validation/Test 
            loại trừ thêm các phim tương ứng theo protocol).
        graph (Optional[Any]): Thể hiện đồ thị (mặc định: dùng Live Neo4j hoặc InMemory singleton).
        config (Optional[KGConfig]): Cấu hình trọng số và ngưỡng (mặc định: đọc từ .env).
        enable_p1 (bool): Bật/tắt đường đồng thể loại P1 (Genre).
        enable_p2 (bool): Bật/tắt đường đặc trưng ngữ nghĩa P2 (Genome).
        enable_p3 (bool): Bật/tắt đường hợp tác đồ thị P3 (Collaborative).

    Returns:
        List[Dict[str, Any]]: Danh sách ứng viên xếp hạng giảm dần theo raw_score,
            mỗi phần tử tuân thủ nghiêm ngặt JSON Evidence Schema.
    """
```

---

## 3. ĐẶC TẢ ĐẦU RA JSON (EVIDENCE CONTRACT SCHEMA)

Mỗi phần tử trong danh sách trả về bắt buộc có định dạng sau:

```json
{
  "userId": 42,
  "movieId": 318,
  "title": "Shawshank Redemption, The (1994)",
  "raw_score": 0.8452,
  "rank": 1,
  "model_name": "KG_PATH",
  "evidence": [
    {
      "path_type": "GENOME",
      "sourceMovieId": 296,
      "sourceMovieTitle": "Pulp Fiction (1994)",
      "sharedEntity": {
        "type": "GenomeTag",
        "key": 1024,
        "name": "clever dialog"
      },
      "sourceRating": 5.0,
      "contribution": 0.3125
    },
    {
      "path_type": "GENRE",
      "sourceMovieId": 16,
      "sourceMovieTitle": "Casino (1995)",
      "sharedEntity": {
        "type": "Genre",
        "key": "Crime"
      },
      "sourceRating": 4.5,
      "contribution": 0.2500
    },
    {
      "path_type": "COLLABORATIVE",
      "sourceMovieId": 296,
      "sourceMovieTitle": "Pulp Fiction (1994)",
      "neighborUserId": 1337,
      "userRating": 5.0,
      "neighborRating": 5.0,
      "contribution": 0.1875
    }
  ]
}
```

### Chi tiết các trường dữ liệu:

| Tên trường | Kiểu dữ liệu | Bắt buộc | Mô tả |
| :--- | :---: | :---: | :--- |
| `userId` | `int` | Có | ID người dùng được gợi ý |
| `movieId` | `int` | Có | ID phim được gợi ý |
| `title` | `string` | Có | Tên đầy đủ và năm phát hành của phim |
| `raw_score` | `float` | Có | Điểm đồ thị tri thức tổng hợp $[0.0, 1.0]$ |
| `rank` | `int` | Có | Thứ hạng của phim trong danh sách Top-N (bắt đầu từ 1) |
| `model_name` | `string` | Có | Định danh mô hình: luôn là `"KG_PATH"` |
| `evidence` | `list[dict]` | Có | Danh sách tối đa 3–5 bằng chứng đóng góp cao nhất |

### Cấu trúc từng mục `evidence`:
- `path_type`: Định danh loại đường đi: `"GENRE"`, `"GENOME"`, hoặc `"COLLABORATIVE"`.
- `sourceMovieId`: ID bộ phim nguồn mà người dùng đã từng thích ($r \ge 3.5$).
- `sourceMovieTitle`: Tên bộ phim nguồn.
- `sharedEntity`: Thực thể trung gian kết nối: Thể loại (`Genre`) hoặc Thẻ đặc trưng (`GenomeTag`).
- `contribution`: Mức độ đóng góp của đường đi này vào điểm tổng thể.
- `neighborUserId`: ID của người dùng láng giềng (đối với đường `COLLABORATIVE`).

---

## 4. HƯỚNG DẪN DUNG HỢP TẠI KHỐI 4 (HYBRID FUSION PROTOCOL)

Khi Khối 4 kết hợp kết quả từ Task 3A và Task 3B:

1. **Hợp tập ứng viên (Candidate Union):**
   ```python
   # Lấy Top-50 từ ALS và Top-50 từ KG
   als_candidates = get_als_recommendations(user_id, top_n=50) # {movieId: als_score}
   kg_candidates = {r["movieId"]: r for r in recommend_kg(user_id, top_n=50)}
   
   union_movie_ids = set(als_candidates.keys()).union(set(kg_candidates.keys()))
   ```

2. **Chuẩn hóa điểm số (Score Normalization):**
   ```python
   # Chuẩn hóa Min-Max riêng biệt cho từng nhánh trên tập ứng viên hợp nhất
   norm_als = min_max_scale(als_candidates, union_movie_ids)
   norm_kg = min_max_scale({mid: r["raw_score"] for mid, r in kg_candidates.items()}, union_movie_ids)
   ```

3. **Tính điểm kết hợp (Weighted Fusion):**
   $$S_{hybrid}(u, m) = \lambda \cdot \text{norm}(S_{ALS}) + (1 - \lambda) \cdot \text{norm}(S_{KG})$$
   *(Trong đó $\lambda \in [0, 1]$ được tinh chỉnh trên tập Validation).*

4. **Kế thừa Bằng chứng giải thích (Preserve Explanations):**
   - Với các phim nằm trong tập giao $\mathcal{C}_{ALS} \cap \mathcal{C}_{KG}$ hoặc thuần $\mathcal{C}_{KG}$, Khối 4 giữ nguyên trường `evidence` từ KG để chuyển giao sang **Web Backend (FastAPI)** sinh lời giải thích tự nhiên bằng tiếng Việt cho người dùng cuối.

