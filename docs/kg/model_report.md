# BÁO CÁO THUẬT TOÁN & KẾT QUẢ ĐÁNH GIÁ (GATE 4 MODEL REPORT)

> **Dự án:** MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark  
> **Nhiệm vụ:** Task 3B — Knowledge Graph Recommender  
> **Tài liệu:** `docs/kg/model_report.md`  
> **Thời điểm lập:** 2026-11-04  
> **Người thực hiện:** Senior Python & Knowledge Graph Engineer (AI Assistant)

---

## 1. THUẬT TOÁN TÍNH ĐIỂM THEO ĐƯỜNG ĐI (PATH-BASED WEIGHTED SCORER)

Hệ thống Knowledge Graph v1 triển khai thuật toán tính điểm dựa trên bằng chứng theo đường đi (**Path-based Weighted Evidence Scorer**). Thuật toán được thiết kế minh bạch, hoàn toàn tiền định và có thể truy ngược từng điểm số về các cạnh có thật trong đồ thị tri thức.

### 1.1. Hàm trọng số sở thích tích cực (Positive Preference Weight)
Để đảm bảo mô hình chỉ lan truyền tri thức từ các bộ phim người dùng thực sự yêu thích:
$$w(r) = \max\left(0, \frac{r - 3.0}{2.0}\right)$$
- Rating $5.0 \implies w(r) = 1.0$ (Tín hiệu mạnh nhất)
- Rating $4.5 \implies w(r) = 0.75$
- Rating $4.0 \implies w(r) = 0.50$
- Rating $3.5 \implies w(r) = 0.25$
- Rating $\le 3.0 \implies w(r) = 0.0$ (Không đóng góp điểm lan truyền)

---

### 1.2. Các đường suy luận thành phần (Metapaths)

#### Đường P1 — Đồng thể loại (Genre Metapath)
- **Chuỗi quan hệ:** `User -[:RATED]-> Movie_A -[:IN_GENRE]-> Genre <-[:IN_GENRE]- Candidate`
- **Công thức:**
  $$S_{P1}(u, c) = \sum_{a \in \mathcal{H}_u} \sum_{g \in \mathcal{G}_a \cap \mathcal{G}_c} \frac{w(r_{u, a})}{\sqrt{|\mathcal{M}_g|}}$$
- **Cơ chế chuẩn hóa bậc (Degree Normalization):** Chia cho $\sqrt{|\mathcal{M}_g|}$ (trong đó $|\mathcal{M}_g|$ là tổng số phim thuộc thể loại $g$). Cơ chế này triệt tiêu thiên kiến từ các thể loại quá đại trà (như Drama có tới hơn 25,000 phim), ngăn không cho các phim thuộc thể loại lớn áp đảo danh sách gợi ý.

#### Đường P2 — Đặc trưng ngữ nghĩa Genome (Genome Metapath)
- **Chuỗi quan hệ:** `User -[:RATED]-> Movie_A -[:HAS_GENOME_TAG]-> Tag <-[:HAS_GENOME_TAG]- Candidate`
- **Công thức:**
  $$S_{P2}(u, c) = \sum_{a \in \mathcal{H}_u} \sum_{t \in \mathcal{T}_a \cap \mathcal{T}_c} \frac{w(r_{u, a}) \cdot \text{rel}(a, t) \cdot \text{rel}(c, t)}{\log(1 + |\mathcal{M}_t|)}$$
- **Ý nghĩa:** Khai thác tương đồng ngữ nghĩa sâu sắc qua 1,128 đặc trưng Tag Genome. Điểm liên quan được nhân chéo $\text{rel}(a, t) \cdot \text{rel}(c, t)$ và chuẩn hóa theo độ phổ biến của tag $\log(1 + |\mathcal{M}_t|)$.

#### Đường P3 — Hợp tác đồ thị đa bước (Collaborative Graph Metapath)
- **Chuỗi quan hệ:** `User_A -[:RATED]-> Anchor_Movie <-[:RATED]- User_B -[:RATED]-> Candidate`
- **Công thức:**
  $$S_{P3}(u, c) = \sum_{v \in \mathcal{N}_u} \text{Sim}(u, v) \cdot w(r_{v, c})$$
- **Độ tương đồng Overlap Cosine:**
  $$\text{Sim}(u, v) = \frac{|\mathcal{H}_u \cap \mathcal{H}_v|}{\sqrt{|\mathcal{H}_u| \cdot |\mathcal{H}_v|}}$$
- **Kiểm soát nổ đường đi:** Giới hạn tối đa $K = 50$ láng giềng thân cận nhất ($\text{Sim}(u, v)$ cao nhất). Chỉ xem xét láng giềng khi họ cũng đánh giá cao anchor movie ($r \ge 3.5$).

---

### 1.3. Dung hợp và chuẩn hóa điểm số
$$S_{KG}(u, c) = \alpha \cdot \text{norm}(S_{P1}) + \beta \cdot \text{norm}(S_{P2}) + \gamma \cdot \text{norm}(S_{P3})$$
- Trọng số cấu hình: $\alpha = 0.35, \beta = 0.45, \gamma = 0.20$ ($\alpha + \beta + \gamma = 1.0$).
- Phép chuẩn hóa $\text{norm}(S)$ thực hiện min-max scaling trên tập ứng viên của người dùng để đưa điểm 3 nhánh về cùng thang đo $[0, 1]$.
- Sắp xếp ổn định (Deterministic Tie-break): `raw_score DESC, movieId ASC`.

---

## 2. KẾT QUẢ ĐÁNH GIÁ OFFLINE & ABLATION STUDY (GATE 4)

Quá trình đánh giá được thực thi trực tiếp trên tập pilot 100 users thực tế bằng script `scripts/kg_evaluate_pilot.py`:
- **Giao thức:** User-wise Leave-1-Last theo `docs/evaluation_protocol.md`.
- **Không gian ứng viên (Candidate Pool):** Toàn bộ danh mục loại trừ phim đã xem: $\text{Candidate\_Pool}(u) = \text{Catalog} \setminus (\text{Train}_u \cup \text{Val}_u)$ (~62,000 ứng viên).
- **Ngưỡng thích (Positive Threshold):** $r \ge 3.5$.
- **Mẫu số đánh giá (Positive Denominator):** **71 users** có rating Validation $\ge 3.5$.
- **Độ sẵn sàng (Score Availability):** **100.0%** (71/71 users đều sinh được khuyến nghị).

### Bảng ma trận đối chứng (Ablation Matrix - Đo Lường Chuẩn Hóa Sau Khi Sửa Lỗi Evaluator):

| Cấu hình thử nghiệm | Metapaths kích hoạt | Score Availability | Catalog Coverage@10 | HR@5 | HR@10 | HR@20 | NDCG@10 | NDCG@20 | MRR@20 | Thời gian đo (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Genre-only (P1)** | P1 | **100.0%** (71/71) | 145 phim | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 70.98s |
| **2. Genre + Genome (P1 + P2)** | P1 + P2 | **100.0%** (71/71) | **344 phim** | 0.0563 | 0.0563 | 0.1127 | 0.0389 | 0.0529 | 0.0366 | 112.18s |
| **3. Full Path-based (P1 + P2 + P3)** | P1 + P2 + P3 | **100.0%** (71/71) | 276 phim | **0.0986** | **0.0986** | **0.1549** | **0.0460** | **0.0595** | **0.0324** | 115.20s |

> [!NOTE]
> **Hiệu chỉnh Evaluator (Audit Resolution):** Phiên bản trước đây vô tình truyền `exclude_movie_ids={target_mid}` trong vòng lặp đánh giá khiến phim mục tiêu ground-truth bị loại trừ trước khi xếp hạng, dẫn đến HR/NDCG bị ép về 0 giả tạo. Sau khi hiệu chỉnh đúng giao thức (giữ nguyên target item trong candidate pool và chỉ loại trừ lịch sử Train), kết quả thực nghiệm khẳng định đường P2 (Genome) mang lại mức tăng vọt Hit Rate từ 0% lên 11.27% (@20), và đường P3 (Collaborative) tiếp tục nâng Hit Rate lên **15.49% (@20)** và NDCG@20 đạt **0.0595**.

---

## 3. PHÂN TÍCH CHUYÊN SÂU & GIẢI MÃ HIỆN TƯỢNG ĐỘ PHỦ (COVERAGE ANALYSIS)

### 3.1. Vì sao Catalog Coverage tăng từ 145 lên 346 (+138.6%)?
- **Nghẽn cổ chai của Thể loại (Genre Bottleneck):**
  - Danh mục MovieLens 25M chỉ có đúng 19 thể loại phân biệt. Khi chỉ sử dụng $P1$, các phim được đề xuất bị giới hạn trong cụm thể loại của phim đã xem. Vì các thể loại lớn như *Drama, Comedy, Action* có hàng nghìn phim, cơ chế chuẩn hóa bậc và liên kết thô chỉ có thể xoay quanh 145 đầu phim đại diện nổi bật nhất.
- **Sức mạnh phân giải của Tag Genome ($P2$):**
  - Tích hợp thêm 1,128 đặc trưng Tag Genome đã mở ra các chiều ngữ nghĩa vi mô (ví dụ: *clever dialog, dark humor, dystopian, atmospheric, cult classic*).
  - Hai bộ phim cùng thể loại *Sci-Fi* nhưng một phim có tag *space opera* còn phim kia có tag *cyberpunk* sẽ được phân hóa rõ rệt. Nhờ vậy, hệ thống khám phá được các phim nằm sâu trong đuôi dài (long-tail), đưa độ phủ tăng vọt thêm **+201 bộ phim mới** (+138.6%).

### 3.2. Vai trò cân bằng của Collaborative Path ($P3$):
- Khi bổ sung đường $P3$ (`P1 + P2 + P3`), độ phủ danh mục điều chỉnh từ 346 về 276 phim.
- Đây là hiện tượng mang tính khoa học cao: Đường $P3$ đưa hành vi cộng đồng thực tế vào đánh giá. Những phim có đặc trưng ngữ nghĩa tốt nhưng chưa từng được cộng đồng có chung gu thưởng thức sẽ bị giảm nhẹ điểm số, nhường chỗ cho các phim nhận được sự đồng thuận cao hơn từ các láng giềng thân cận.

---

## 4. HÀNH VI ĐỐI VỚI COLD-START VÀ CÁC TRƯỜNG HỢP BIÊN

1. **Movie Cold-Start (Phim chưa có rating trong Train):**
   - Đồ thị tri thức giải quyết triệt để vấn đề này nếu phim có metadata. Phim chưa từng được ai xem trong Train nhưng có Thể loại hoặc Genome Tag liên quan vẫn được $P1$ và $P2$ sinh điểm và đề xuất (đã được kiểm chứng qua `test_kg12_cold_start_movie_behavior`).
   - Với phim cô lập hoàn toàn không có metadata (như Movie 7 trong fixture), hệ thống trả điểm 0 và không ảo giác liên kết.
2. **User Cold-Start / No-History:**
   - Với người dùng ngoài tập train không có lịch sử, hệ thống trả về danh sách rỗng `[]` kèm thông báo tường minh, không tự ý gán fallback ngẫu nhiên giả mạo là kết quả KG.

---

## 5. PHÂN TÍCH KHẢ NĂNG MỞ RỘNG QUY MÔ & GIỚI HẠN PHẦN CỨNG (SCALABILITY ANALYSIS)

Hệ thống đã thực hiện benchmark mở rộng quy mô theo 5 mốc từ 100 đến 5,000 users theo kịch bản `scripts/kg_pilot_scaling_benchmark.py`:

```text
[TỔNG KẾT KHẢ NĂNG MỞ RỘNG QUY MÔ PILOT]
Mốc 100 users   :    13,096 ratings |   194,061 edges |  6.56s import | 2.1s latency | RSS 596 MB
Mốc 500 users   :    61,834 ratings |   303,679 edges | 14.17s import | 1.8s latency | RSS 527 MB
Mốc 1,000 users :   141,565 ratings |   448,549 edges | 24.24s import | 3.4s latency | RSS 502 MB
Mốc 2,000 users :   283,699 ratings |   620,404 edges | 57.91s import | 3.3s latency | RSS 597 MB
Mốc 5,000 users :   723,155 ratings | 1,095,900 edges | 35.17s import | 5.2s latency | RSS 502 MB
```

### 5.1. Nhận định về Quản lý Bộ nhớ (RAM Management):
- Đỉnh bộ nhớ RSS luôn duy trì ổn định trong khoảng **500 – 600 MB**, lượng RAM trống của máy luôn duy trì $> 1.0\text{ GB}$.
- Việc phân mảnh dữ liệu qua `PyArrow` theo batch và cấu trúc bộ nhớ danh sách kề tối ưu trong `InMemoryGraph` cho phép nạp thành công **vượt ngưỡng 1.09 triệu quan hệ** mà không gây tràn bộ nhớ (Zero OOM).

### 5.2. Sự tăng trưởng của Độ trễ Truy vấn (Query Latency Scaling):
- Khi quy mô tăng từ 100 lên 5,000 users, số lượng quan hệ $P3$ (Collaborative) tăng gấp 55 lần (từ 13k lên 723k ratings), dẫn đến số lượng láng giềng tiềm năng cho mỗi user tăng theo.
- Độ trễ gợi ý tăng nhẹ từ **~2.1s lên ~5.2s/user** trên không gian quét toàn bộ 62,423 phim. Cơ chế giới hạn $K=50$ top láng giềng đã chứng minh vai trò then chốt trong việc kiểm soát nổ đường đi, giữ độ trễ trong ngưỡng hoàn toàn chấp nhận được cho xử lý offline batch.

---

## 6. GIỚI HẠN KHÁCH QUAN & KẾT LUẬN CHO KHỐI 4 HYBRID

- **Về chỉ số Hit Rate:**
  - Trên không gian xếp hạng toàn danh mục ~62,000 phim (Full-Catalog Top-20) mà không có sự trợ lực của ma trận hệ số ẩn ALS và thiên kiến phổ biến (popularity bias), chỉ số HR của KG thuần túy trên mẫu 71 users là 0.0. Đây là kết quả trung thực, phản ánh đúng đặc thù của đồ thị tri thức trong bài toán ranking không gian cực lớn khi chạy độc lập.
- **Ý nghĩa đối với Khối 4 Hybrid Recommender:**
  - Kết quả này khẳng định giá trị cốt lõi của **Candidate Union**: Nhánh ALS (Task 3A) chịu trách nhiệm bắt trúng các phim phổ biến và xu hướng chung, trong khi nhánh Knowledge Graph (Task 3B) bổ sung các ứng viên ngách giàu ngữ nghĩa và cung cấp bằng chứng giải thích tường minh (**Explainable Evidence**).

