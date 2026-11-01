# MOODGRAPH | BẢN CHUYỂN GIAO KỸ THUẬT TASK 3A CHO NHÓM PHÁT TRIỂN HYBRID & TASK 3B
# Handover Guide: Collaborative Filtering (ALS) Service Integration for Knowledge Graph Teammates

- **Dự án:** MoodGraph – Recommender System
- **Nguồn chuyển giao:** Nhóm Kỹ thuật Task 3A (Collaborative Filtering / Spark ALS)
- **Đối tượng tiếp nhận:** Nhóm Kỹ thuật Task 3B (Knowledge Graph) & Kiến trúc sư Mô hình Lai (Hybrid Orchestrator)
- **Tài liệu tham chiếu chính:** [integration_contract.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/integration_contract.md)
- **Dịch vụ suy luận:** [delivery.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py)

---

## 1. Lời Chào & Tóm Tắt Chuyển Giao

Thân gửi các đồng đội phụ trách Task 3B (Knowledge Graph) và Hybrid Recommender,

Nhóm Task 3A đã hoàn thành 100% việc huấn luyện, tối ưu tham số, kiểm định độc lập và đóng gói mô hình Collaborative Filtering dựa trên Spark ALS (`ALS_R8_REG0.3_ITER10`). Toàn bộ mã nguồn, mô hình và dữ liệu đã được tinh giản thành một gói dịch vụ suy luận thời gian thực duy nhất tại `recommender/als/delivery.py`.

Tài liệu này cung cấp hướng dẫn thực chiến ngắn gọn để các bạn tích hợp module ALS vào hệ thống gợi ý lai mà không gặp phải bất kỳ trở ngại nào về định dạng dữ liệu hay hiệu năng.

---

## 2. Hướng Dẫn Sử Dụng Nhanh (Quick Start)

### 2.1 Cài đặt & Import Dịch vụ
Module cung cấp hai hàm công khai tiện lợi, không yêu cầu khởi tạo JVM hay Spark Session khi chạy suy luận:

```python
from recommender.als.delivery import recommend_als, recommend_als_batch

# Gợi ý Top-10 cho một người dùng (userId chuẩn của MovieLens)
recommendations = recommend_als(user_id=1, k=10, filter_seen=True)

for item in recommendations:
    print(f"Rank {item.rank}: Movie {item.movieId} | Raw Score: {item.raw_score:.4f}")
```

### 2.2 Định dạng Dữ liệu Đầu ra (`ALSRecommendationItem`)
Mỗi phần tử trong danh sách trả về là một đối tượng `ALSRecommendationItem` bất biến:
- `item.userId` (`int`): ID người dùng gốc (int64).
- `item.movieId` (`int`): ID phim gốc của MovieLens (int64) - dùng trực tiếp để tra cứu Entity trong Knowledge Graph!
- `item.raw_score` (`float`): Điểm số thô (tích vô hướng `U_u @ V_i`).
- `item.rank` (`int`): Thứ hạng từ 1 đến K.
- `item.model_name` (`str`): Luôn là `"ALS"`.
- `item.model_version` (`str`): Định danh phiên bản mô hình, ví dụ `"ALS_R8_REG0.3_ITER10"`.

---

## 3. 4 Nguyên Tắc Sống Còn Khi Tích Hợp (Critical Rules)

Để tránh các sai lầm kinh điển làm giảm độ chính xác của hệ thống lai, các bạn vui lòng tuân thủ nghiêm ngặt 4 nguyên tắc sau:

### Nguyên tắc 1: Luôn dùng Candidate Union (`ALS ∪ KG`), KHÔNG lọc tuần tự trên ALS Top-20
- **SAI (CẤM)**:
  `user -> recommend_als(user, k=20) -> KG_filter(als_movies) -> final_recommendations`
  *Hậu quả*: Toàn bộ các phim ngách, phim mới khởi động lạnh (Cold-Start) mà Knowledge Graph tìm ra sẽ bị biến mất vì ALS đã lọc bỏ chúng ngay từ đầu.
- **ĐÚNG (BẮT BUỘC)**:
  `candidates = set([item.movieId for item in als_recs]) | set(kg_candidate_ids)`
  Sau đó tính điểm lai và rerank trên toàn bộ tập hợp nhất này.

### Nguyên tắc 2: TUYỆT ĐỐI KHÔNG cộng trực tiếp điểm số thô
- **SAI (CẤM)**:
  `hybrid_score = als_item.raw_score + kg_item.score`
  *Hậu quả*: Điểm ALS có độ lớn trung bình từ 4.0 đến 10.0+, trong khi điểm KG thường nằm trong khoảng 0.0 đến 1.0. Điểm ALS sẽ chiếm tới 90% trọng số, làm tê liệt hoàn toàn tác dụng của Knowledge Graph.
- **ĐÚNG (BẮT BUỘC)**:
  Chuẩn hóa Min-Max danh sách ứng viên ALS về đoạn `[0, 1]` trước khi nhân trọng số:
  ```python
  # Min-Max Normalization mẫu cho ALS
  scores = [item.raw_score for item in als_items]
  min_s, max_s = min(scores), max(scores)
  range_s = max_s - min_s if max_s != min_s else 1.0
  norm_als_scores = {item.movieId: (item.raw_score - min_s) / range_s for item in als_items}

  # Tính điểm lai cân bằng
  final_score = 0.5 * norm_als_scores.get(m_id, 0.0) + 0.5 * norm_kg_scores.get(m_id, 0.0)
  ```
  Hoặc sử dụng Reciprocal Rank Fusion (RRF):
  ```python
  rrf_score = 1.0 / (60 + als_rank) + 1.0 / (60 + kg_rank)
  ```

### Nguyên tắc 3: Xử lý Cold-Start User sạch sẽ
Khi gặp người dùng mới chưa từng có tương tác trong tập Train:
- Hàm `recommend_als(cold_user_id)` sẽ trả về danh sách rỗng: `[]`.
- Khi nhận được `[]`, phía Hybrid Orchestrator hãy kích hoạt cơ chế fallback dựa trên Knowledge Graph (ví dụ gợi ý theo thể loại/diễn viên mà người dùng chọn khi đăng ký) hoặc Popularity Baseline.

### Nguyên tắc 4: ID phim là ID gốc MovieLens
Không cần bất kỳ bước chuyển đổi chỉ số (index mapping) nào. Dịch vụ ALS đã tự động chuyển đổi từ ma trận nội bộ sang `movieId` gốc MovieLens 25M (khớp 100% với file `movies.parquet` và đồ thị thực thể Neo4j/NetworkX của Task 3B).

---

## 4. Kiểm Thử Mẫu (Example Consumer Code)

Đoạn code mẫu dưới đây minh họa cách một consumer phía Task 3B gọi ALS và thực hiện gộp ứng viên hợp lệ:

```python
from recommender.als.delivery import recommend_als

def hybrid_candidate_generation(user_id: int, top_k: int = 10):
    # 1. Lấy ứng viên hành vi từ ALS
    als_items = recommend_als(user_id=user_id, k=top_k, filter_seen=True)
    als_candidate_ids = {item.movieId for item in als_items}

    # 2. Lấy ứng viên ngữ nghĩa từ Knowledge Graph (giả lập)
    # kg_candidate_ids = get_kg_candidates(user_id=user_id, k=top_k)
    kg_candidate_ids = {202231, 999101, 999102}

    # 3. Tạo hợp tập ứng viên (Candidate Union)
    union_candidates = als_candidate_ids.union(kg_candidate_ids)

    # 4. Đảm bảo các phim KG-only vẫn tồn tại
    assert 999101 in union_candidates
    return union_candidates
```

---

## 5. Hỗ Trợ & Liên Hệ
Mọi thắc mắc kỹ thuật hoặc nhu cầu mở rộng API, xin vui lòng tra cứu thêm tại:
- Báo cáo chi tiết: [M10_delivery_report.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M10_delivery_report.md)
- Bản đồ bảo vệ mã nguồn: [M10_source_code_defense_map.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/M10_source_code_defense_map.md)
- Test suite kiểm định: [test_delivery.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_delivery.py)

Chúc nhóm Task 3B hoàn thành xuất sắc đồ thị tri thức và tích hợp thành công mô hình lai MoodGraph!

