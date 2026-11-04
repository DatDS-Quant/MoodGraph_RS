# Module Recommender Knowledge Graph (Task 3B)

Module gợi ý phim cá nhân hóa dựa trên **Đồ thị tri thức (Knowledge Graph Recommender)** trong hệ thống **MoodGraph**.

---

## 1. GIỚI THIỆU TỔNG QUAN

Khối 3B hoạt động độc lập và song song với Khối 3A (Spark ALS). Module khai thác các liên kết thực giữa Người dùng (`User`), Phim (`Movie`), Thể loại (`Genre`) và Thẻ đặc trưng ngữ nghĩa (`GenomeTag`) để đưa ra:
1. **Danh sách ứng viên Top-N phim gợi ý** cho từng người dùng dựa trên các đường suy luận đa bước.
2. **Điểm số thô (raw_score)** độc lập của đồ thị tri thức.
3. **Bằng chứng giải thích (Explainable Evidence)** có thể truy vết ngược từ đồ thị tri thức, trả lời câu hỏi *"Tại sao phim này được đề xuất?"*.

---

## 2. CÁC ĐƯỜNG SUY LUẬN (METAPATHS)

- **P1 (Genre Path):** `User -[:RATED]-> Movie_A -[:IN_GENRE]-> Genre <-[:IN_GENRE]- Movie_B`
  - Đề xuất phim chia sẻ thể loại với các phim người dùng đánh giá cao ($r \ge 3.5$).
  - Chuẩn hóa theo bậc của thể loại $\frac{1}{\sqrt{|\mathcal{M}_g|}}$ để hạn chế thiên kiến phim thuộc thể loại đại trà (Drama, Comedy).
- **P2 (Genome Path):** `User -[:RATED]-> Movie_A -[:HAS_GENOME_TAG]-> GenomeTag <-[:HAS_GENOME_TAG]- Movie_B`
  - Khai thác tương đồng ngữ nghĩa sâu sắc qua 1,128 Tag Genome.
  - Tích hợp trọng số liên quan $\text{rel}(a, t) \cdot \text{rel}(c, t)$ và chính sách lọc Top-M tags ($M=20$).
- **P3 (Collaborative Graph Path):** `User_A -[:RATED]-> Anchor_Movie <-[:RATED]- User_B -[:RATED]-> Candidate`
  - Khai thác hành vi cộng đồng đa bước vượt ra ngoài thuộc tính nội dung thuần túy.
  - Kiểm soát nổ đường đi bằng cơ chế Overlap Cosine và giới hạn tối đa $K=50$ láng giềng thân cận nhất.

---

## 3. CẤU TRÚC THƯ MỤC

```text
recommender/kg/
├── __init__.py           # Package interface
├── config.py             # Cấu hình từ file .env / biến môi trường
├── schema.cypher         # DDL ràng buộc tính duy nhất (Unique Constraints) & Index
├── data_access.py        # Đọc dữ liệu Parquet phân mảnh theo batch (dùng PyArrow)
├── queries.py            # Cypher templates tham số hóa & an toàn chống injection
├── import_graph.py       # CLI import dữ liệu vào Neo4j (hỗ trợ synthetic, pilot, full)
├── scorer.py             # Bộ tính điểm theo đường đi (Path-based Weighted Scorer)
├── recommend.py          # Facade recommend_kg cung cấp ứng viên Top-N kèm Evidence
├── evaluate.py           # Đánh giá offline trên Validation (HR@K, NDCG@K, Coverage@K)
├── checks.py             # Kiểm tra chất lượng dữ liệu đồ thị và chống rò rỉ
└── requirements.txt      # Thư viện phụ thuộc của riêng module KG
```

---

## 4. HƯỚNG DẪN THIẾT LẬP & SỬ DỤNG

### 4.1. Cài đặt phụ thuộc
```powershell
pip install -r recommender/kg/requirements.txt
```

### 4.2. Cấu hình biến môi trường
Sao chép `.env.example` thành `.env` (nếu cần điều chỉnh thông số kết nối):
```powershell
cp .env.example .env
```

### 4.3. Kiểm tra kết nối nhanh (Smoke Test - Gate 0)
```powershell
python scripts/kg_smoke_test.py
```

### 4.4. Chạy bộ kiểm thử tự động (17/17 Tests PASS)
```powershell
python -m pytest tests/kg/ -v
```

### 4.5. Nạp đồ thị (Import)
- **Chế độ synthetic** (dùng để kiểm thử chức năng và idempotency):
```powershell
python recommender/kg/import_graph.py --mode synthetic
```
- **Chế độ pilot** (dùng mẫu 100 người dùng thực tế từ tập Train):
```powershell
python recommender/kg/import_graph.py --mode pilot --users 100 --top-m 20
```

### 4.6. Chạy đánh giá offline & Ablation Study (Gate 4)
```powershell
python scripts/kg_evaluate_pilot.py 100
```

### 4.7. Sử dụng trong mã nguồn Python (Python Facade)
```python
from recommender.kg.recommend import recommend_kg

# Sinh Top-10 gợi ý cho userId 1
recs = recommend_kg(user_id=1, top_n=10)
for r in recs:
    print(f"Rank {r['rank']}: Movie {r['movieId']} - {r['title']} | Score: {r['raw_score']}")
    print(f"  -> Evidence: {r['evidence'][:2]}")
```
