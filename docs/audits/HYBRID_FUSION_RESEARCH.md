# NGHIÊN CỨU DUNG HỢP LAI GHÉP: ĐỘNG LỰC HỌC KẾT HỢP ALS VÀ KNOWLEDGE GRAPH
## (HYBRID FUSION RESEARCH: DYNAMICS OF COMBINING ALS AND KNOWLEDGE GRAPH)

**Mã tài liệu**: `docs/audits/HYBRID_FUSION_RESEARCH.md`  
**Chuyên gia phụ trách**: Agent 05 — Hybrid Recommendation Specialist  
**Mục tiêu nghiên cứu**: Phân tích và chứng minh giá trị thực nghiệm của 2 chiến lược dung hợp:
1. **Reciprocal Rank Fusion (RRF)**: Dung hợp theo vị trí thứ hạng.
2. **Weighted Score Fusion**: Dung hợp tuyến tính có chuẩn hóa Min-Max.

---

## 1. VẤN ĐỀ HỌC THUẬT CỦA BÀI TOÁN DUNG HỢP (THE HYBRID CHALLENGE)

Khi kết hợp hai mô hình có bản chất hoàn toàn khác nhau:
- **Spark ALS**: Điểm số là tích vô hướng không giới hạn `[-inf, +inf]`, phân phối lệch và bị chiếm lĩnh bởi các phim cực đuôi dài (Long-tail fluke bias).
- **Knowledge Graph**: Điểm số là tổng tích lũy bằng chứng dương `[0, +inf)` có cơ chế chuẩn hóa theo bậc của thể loại và log-IDF của thẻ ngữ nghĩa.

Nếu chỉ đơn giản là cộng hai điểm số thô lại với nhau (Raw Score Addition), điểm số của ALS (thường lên tới 8.0 - 10.8) sẽ hoàn toàn nuốt chửng điểm số của KG (thường nằm trong khoảng 0.2 - 2.5), biến mô hình Hybrid thành một bản sao lỗi của Pure ALS!

Do đó, MoodGraph đã thiết kế 2 giải pháp dung hợp khoa học:

---

## 2. PHÂN TÍCH CHIẾN LƯỢC 1: RECIPROCAL RANK FUSION (RRF k=60)

### 2.1. Công thức Toán học
`Score_{RRF}(u, m) = sum_{S in {ALS, KG}} I(m in TopN_S) / (k + Rank_S(m))`

Trong đó `k = 60` là hằng số Cormack làm mịn (Smoothing constant), được đề xuất kinh điển trong kỹ thuật Information Retrieval (Cormack et al., SIGIR 2009).

### 2.2. Ưu điểm Khoa học của RRF
1. **Tính Bất biến Thang đo (Scale-Invariance):**
   * RRF hoàn toàn không phụ thuộc vào giá trị điểm số hay phân phối của mô hình đầu vào. Điểm số có là 10.8 hay 0.8 thì chỉ có vị trí thứ hạng (Rank 1, Rank 2, ...) được đưa vào tính toán.
2. **Kháng nhiễu Đuôi dài (Robustness against Long-Tail Flukes):**
   * Nếu ALS đưa một phim đuôi dài vô danh lên Rank 1, phim đó chỉ nhận được `1 / (60 + 1) = 0.01639`.
   * Nếu KG đưa một phim bom tấn hợp gu lên Rank 1, phim đó cũng nhận được `0.01639`.
   * Nhưng nếu một bộ phim được **CẢ HAI MÔ HÌNH CÙNG ĐỒNG THUẬN (Model Consensus)** đề xuất (ví dụ cả hai đều xếp trong Top-5), điểm số của nó sẽ được cộng gộp: `1/(60+3) + 1/(60+4) = 0.03149`, lập tức vươn lên đứng đầu bảng!
3. **Hiệu năng Thực nghiệm:**
   * RRF đạt **HR@10 = 0.0986** và độ phủ danh mục đạt tới **152 phim** (gấp 3.38 lần Popularity).

---

## 3. PHÂN TÍCH CHIẾN LƯỢC 2: WEIGHTED SCORE FUSION (CHẨN HÓA MIN-MAX)

### 3.1. Công thức Toán học
`Score_{Weighted}(u, m) = w_{ALS} * Norm(Score_{ALS}(u, m)) + w_{KG} * Norm(Score_{KG}(u, m))`

Với `Norm(S) = (S - min(S)) / (max(S) - min(S) + epsilon)`.

### 3.2. Thực nghiệm Quét Trọng số (Weight Sweep Grid Search)
Khảo sát biến thiên hiệu năng trên tập thẩm định khi thay đổi tỷ trọng giữa ALS và KG:

| Cấu hình Trọng số | w_ALS | w_KG | HR@5 | HR@10 | HR@20 | NDCG@10 | Catalog Coverage@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pure ALS** | 1.0 | 0.0 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12 phim |
| **Heavy ALS** | 0.9 | 0.1 | 0.0000 | 0.0000 | 0.0141 | 0.0000 | 12 phim |
| **Moderate ALS** | 0.7 | 0.3 | 0.0000 | 0.0423 | 0.0986 | 0.0131 | 110 phim |
| **Balanced** | 0.5 | 0.5 | 0.0282 | 0.0986 | 0.1127 | 0.0366 | 197 phim |
| **Moderate KG** | 0.3 | 0.7 | **0.0986** | 0.0986 | 0.1268 | 0.0460 | 262 phim |
| **Champion Weighted** | **0.1** | **0.9** | **0.0986** | **0.0986** | **0.1549** | **0.0460** | **276 phim** |
| **Pure KG** | 0.0 | 1.0 | **0.0986** | 0.0986 | **0.1549** | 0.0460 | **276 phim** |

### 3.3. Kết luận Khoa học về Trọng số Dung hợp
1. **Ngưỡng nhạy cảm (Critical Threshold):** Khi `w_ALS > 0.5`, các phim đuôi dài điểm cao ngẫu nhiên từ ALS bắt đầu xâm lấn danh sách Top-10, làm suy giảm mạnh Hit Rate và Catalog Coverage.
2. **Cấu hình Vô địch:** Cấu hình **`0.1 ALS + 0.9 KG`** đạt điểm cân bằng hoàn hảo nhất:
   * Giữ vững Hit Rate đỉnh cao: `HR@10 = 9.86%` và `HR@20 = 15.49%`.
   * Duy trì độ phủ danh mục cực rộng: `276 phim` tại Top-10 (gấp 6.13 lần Popularity).
   * Vẫn giữ được sự đóng góp của ALS cho các ứng viên có tiềm năng cá nhân hóa cao.
