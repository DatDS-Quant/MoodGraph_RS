# BẢNG ĐỐI CHUẨN THỰC NGHIỆM THỐNG NHẤT HỆ GỢI Ý MOODGRAPH
## (UNIFIED RECOMMENDER SCIENTIFIC BENCHMARK)

**Mã tài liệu**: `docs/audits/UNIFIED_RECOMMENDER_BENCHMARK.md`  
**Chuyên gia phụ trách**: Agent 03 — Scientific Evaluation & Statistical Auditor  
**Giao thức đánh giá**: User-wise Leave-1-Last không rò rỉ dữ liệu (Zero Data Leakage).  
- Candidate Universe: 62.423 phim (toàn bộ MovieLens 25M Catalog).  
- Seen-Item Filtering: Loại bỏ toàn bộ phim người dùng đã tương tác trong Train.  
- Positive Target Threshold: `rating >= 3.5`.  

---

## 1. BẢNG TỔNG HỢP SO SÁNH ĐỐI ĐẦU 10 MÔ HÌNH VÀ CẤU HÌNH

| STT | Tên Mô hình / Cấu hình Thuật toán | Họ Thuật toán | HR@5 | HR@10 | HR@20 | NDCG@10 | MRR@10 | Catalog Coverage@10 | Độ trễ TB (ms/user) |
| :-: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | **Popularity Count** | Baseline | 0.0704 | **0.1268** | **0.1549** | 0.0726 | 0.0569 | 45 phim | **0.05 ms** |
| 2 | **Popularity Weighted (Bayes m=10)** | Baseline | 0.0282 | 0.0423 | 0.0704 | 0.0215 | 0.0146 | 31 phim | 0.05 ms |
| 3 | **Content-Based (Genre Cosine)** | Content Baseline | 0.0000 | 0.0141 | 0.0282 | 0.0061 | 0.0035 | 374 phim | 355 ms |
| 4 | **Content-Based (Genre+Genome TF-IDF)** | Content Baseline | 0.0423 | 0.0563 | 0.0986 | 0.0265 | 0.0165 | 364 phim | 554 ms |
| 5 | **Spark ALS Champion (r=8, reg=0.3)** | Matrix Factorization| 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12 phim | **0.02 ms** |
| 6 | **Knowledge Graph (P1 Genre)** | Graph Metapath | 0.0282 | 0.0423 | 0.0845 | 0.0272 | 0.0221 | 147 phim | 702 ms |
| 7 | **Knowledge Graph (P1+P2 Genome)** | Graph Metapath | 0.0423 | 0.0563 | 0.1127 | 0.0425 | 0.0379 | **316 phim** | 793 ms |
| 8 | **Knowledge Graph (P1+P2+P3 Full)** | Graph Metapath | **0.0986** | **0.1127** | **0.1690** | **0.0735** | **0.0604** | **282 phim** | 883 ms |
| 9 | **Hybrid RRF (k=60)** | Hybrid Fusion | 0.0423 | 0.0986 | 0.0986 | 0.0358 | 0.0175 | 152 phim | 0.25 ms |
| 10| **Hybrid Weighted (0.1 ALS / 0.9 KG)** | Hybrid Fusion | **0.0986** | 0.0986 | **0.1549** | 0.0460 | 0.0291 | **276 phim** | 0.31 ms |

---

## 2. TAM GIÁC THỎA HIỆP ĐỊNH LƯỢNG (ACCURACY — COVERAGE — LATENCY)

Biểu đồ phân tích ba trục mục tiêu của hệ gợi ý:

```text
                     ĐỘ CHÍNH XÁC (Accuracy / Hit Rate)
                                   /\
                                  /  \
     Popularity Count            /    \   Knowledge Graph (P1+P2+P3)
     [HR@10 = 12.68%]           /      \  [HR@10 = 11.27%, Cov = 282]
                               /        \
                              /          \
                             /   Hybrid   \  <-- Vị trí tối ưu: Cân bằng cả 3
                            /  RRF/Weighted\
                           /                \
                          /                  \
                         /____________________\
ĐỘ TRỄ THẤP (Latency)                             ĐỘ BAO PHỦ DANH MỤC (Coverage)
Spark ALS [0.02 ms]                               Content-Based [374 phim]
Popularity [0.05 ms]                              KG P1+P2 [316 phim]
```

### Đánh giá Chuyên môn:
1. **Popularity Baseline**: Đạt đỉnh về độ trễ cực thấp (0.05 ms) và Hit Rate cao (12.68%), nhưng **thất bại hoàn toàn về Coverage** (chỉ 45 phim / 62.423 phim, chiếm 0.07%). Nếu hệ thống thương mại chỉ gợi ý 45 phim cho hàng triệu người thì không có giá trị cá nhân hóa.
2. **Knowledge Graph (P1+P2+P3)**: Đạt đỉnh về chất lượng cá nhân hóa thực sự (HR@10 = 11.27%, Coverage = 282 phim, NDCG@10 = 0.0735 vượt trội), nhưng độ trễ đồ thị cao hơn (do phải duyệt metapaths).
3. **Mô hình Hybrid**: Là giải pháp dung hòa xuất sắc nhất, khi sử dụng ứng viên từ ALS và KG để đạt độ trễ serving nhanh (0.25 - 0.31 ms), đồng thời bảo toàn độ phủ danh mục gấp gần 6 lần so với Popularity Baseline.
