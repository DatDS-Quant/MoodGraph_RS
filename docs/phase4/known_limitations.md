# CÁC HẠN CHẾ ĐÃ BIẾT & HƯỚNG PHÁT TRIỂN (KNOWN LIMITATIONS & FUTURE WORK) - PHASE 4

## 1. CÁC HẠN CHẾ ĐÃ BIẾT (KNOWN LIMITATIONS)

### 1.1. Xử lý người dùng mới (Cold-Start Users)
- **Bản chất**: Mô hình ma trận phân tích nhân tử Spark ALS (`ALS_R8_REG0.3_ITER10`) không thể sinh vector tiềm ẩn cho người dùng chưa từng xuất hiện trong tập Train.
- **Hành vi hiện tại**:
  * Nếu người dùng chỉ mới có tương tác trên Đồ thị tri thức (KG): Hybrid Engine chuyển sang phục vụ bằng đường đi KG với bằng chứng giải thích đầy đủ.
  * Nếu người dùng hoàn toàn mới (không có dữ liệu trong cả ALS lẫn KG): Hệ thống trả về danh sách rỗng kèm cờ `is_cold_start: True` theo đúng hợp đồng thiết kế, hoặc chuyển tiếp sang baseline Phổ biến Toàn cục (Global Popularity).

### 1.2. Độ trễ duyệt đồ thị thời gian thực (Cold Graph Traversal Latency)
- **Bản chất**: Thuật toán duyệt đường đi P1 (Genre), P2 (Top-20 Genome Tags với 73,720 cạnh quan hệ), P3 (k-NN Collaborative Graph) trên danh mục lớn (62,423 phim) tốn từ 1.0 đến 1.4 giây CPU cho một lượt tính toán lạnh (Cold Traversal).
- **Hành vi hiện tại**: Hệ thống bắt buộc phụ thuộc vào tầng `HybridRecommendationCache` (In-Memory LRU Cache, TTL=1h). Khi Cache Hit, độ trễ đạt mức lý tưởng 0.4 - 1.2 ms (vượt xa chỉ tiêu 200 ms). Tuy nhiên, yêu cầu đầu tiên khi Cache Miss vẫn sẽ chịu độ trễ xấp xỉ 1.2 giây.

### 1.3. Trọng số dung hợp tĩnh (Static Fusion Hyperparameters)
- **Bản chất**: Các tham số dung hợp (`w_ALS = 0.5`, `w_KG = 0.5`, hoặc `RRF k = 60`) hiện được cố định tĩnh ở cấp cấu hình toàn cục cho toàn bộ người dùng.
- **Hệ quả**: Chưa phản ánh được sự khác biệt giữa người dùng tương tác dày đặc (heavy users - vốn phù hợp hơn với Collaborative Filtering) và người dùng tương tác thưa thớt (sparse/niche users - vốn hưởng lợi nhiều hơn từ liên kết ngữ nghĩa đồ thị).

---

## 2. HƯỚNG PHÁT TRIỂN TIẾP THEO (FUTURE ENHANCEMENTS)

1. **Pre-computed Graph Embeddings**: Sử dụng thuật toán Node2Vec, TransE hoặc Graph Convolutional Networks (GCN) để nhúng toàn bộ đồ thị tri thức thành các vector dense cố định. Khi đó, việc tính điểm KG sẽ chuyển thành phép nhân vô hướng dot-product tốc độ cao tương tự như ALS (< 1ms).
2. **Adaptive Context-aware Weighting**: Huấn luyện một mạng nơ-ron định tuyến trọng số (Gating Network) dựa trên số lượng đánh giá của người dùng để tự động phân bổ `w_ALS(u)` và `w_KG(u)`.
3. **Neo4j Enterprise Cluster & Distributed Graph Traversal**: Kết nối cụm Neo4j chuyên dụng với Neo4j Graph Data Science (GDS) library để tăng tốc độ truy vấn đồ thị phân tán.

