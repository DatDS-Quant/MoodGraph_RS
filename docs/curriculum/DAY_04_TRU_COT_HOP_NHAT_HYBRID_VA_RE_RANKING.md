# KHÓA HUẤN LUYỆN LÀM CHỦ MOODGRAPH (5-DAY MASTERY CURRICULUM)

# BÀI GIẢNG NGÀY 04: TRỤ CỘT HỢP NHẤT LAI GHÉP ĐA MÔ HÌNH (HYBRID RECOMMENDER ENGINE & CLOSED-LOOP RE-RANKING)

> **Mục tiêu học tập Ngày 04:**  
> Sau khi đã nắm vững hai trụ cột độc lập: **Lọc cộng tác ma trận ẩn Spark ALS (Ngày 02)** và **Đồ thị tri thức suy luận ngữ nghĩa Knowledge Graph (Ngày 03)**, bài giảng Ngày 04 sẽ giúp bạn hiểu sâu sắc tầng kiến trúc hợp nhất (Fusion Layer):
>
> 1. Làm thế nào để kết hợp hai nguồn điểm có thang đo hoàn toàn khác nhau mà không làm mất tính công bằng?
> 2. Bản chất toán học của thuật toán Cormack Reciprocal Rank Fusion (RRF, k=60).
> 3. Cơ chế Weighted Score Fusion kết hợp Min-Max và các chiến lược nội suy điểm thiếu (Imputation).
> 4. Quy trình phản hồi vòng lặp khép kín (Closed-Loop Feedback) và tái xếp hạng thời gian thực (Real-time Re-ranking) khi người dùng tương tác trên Web.
> 5. Toàn bộ vị trí file mã nguồn, hàm số và dòng code chính xác trong thư mục `recommender/hybrid/` và `recommender/services/`.

---

## MỤC LỤC BÀI GIẢNG NGÀY 04

1. [Bản Chất Triết Lý Của Mô Hình Lai Ghép (Hybrid Architecture)](#1-bản-chất-triết-lý-của-mô-hình-lai-ghép)
2. [Kiến Trúc Hợp Nhất Tập Ứng Viên (Candidate Union Architecture)](#2-kiến-trúc-hợp-nhất-tập-ứng-viên)
3. [Mổ Xẻ Thuật Toán Dung Hợp 1: Cormack Reciprocal Rank Fusion (RRF)](#3-mổ-xẻ-thuật-toán-dung-hợp-1-cormack-reciprocal-rank-fusion-rrf)
4. [Mổ Xẻ Thuật Toán Dung Hợp 2: Weighted Score Fusion & Vấn Đề Nội Suy (Imputation)](#4-mổ-xẻ-thuật-toán-dung-hợp-2-weighted-score-fusion--vấn-đề-nội-suy)
5. [Giải Thích Bản Chất Thực Nghiệm: Vì Sao Hybrid w_ALS=0.1 / w_KG=0.9 Lại Tối Ưu?](#5-giải-thích-bản-chất-thực-nghiệm-vì-sao-hybrid-w_als01--w_kg09-lại-tối-ưu)
6. [Cơ Chế Phản Hồi Vòng Lặp Khép Kín & Tái Xếp Hạng Tức Thời (Closed-Loop Re-ranking)](#6-cơ-chế-phản-hồi-vòng-lặp-khép-kín--tái-xếp-hạng-tức-thời)
7. [Bộ Nhớ Đệm LRU Chống Nhiễm Chéo (Multi-Dimensional Cache)](#7-bộ-nhớ-đệm-lru-chống-nhiễm-chéo)
8. [Bảng Tra Cứu Nhanh Cho Thầy Xem (Code Show-and-Tell Map)](#8-bảng-tra-cứu-nhanh-cho-thầy-xem)
9. [5 Câu Hỏi Vấn Đáp "Chí Mạng" Của TS. Bùi Thanh Hùng & Lời Giải Điểm 10](#9-5-câu-hỏi-vấn-đáp-chí-mạng-của-ts-bùi-thanh-hùng)

---

## 1. BẢN CHẤT TRIẾT LÝ CỦA MÔ HÌNH LAI GHÉP

Trong hệ thống gợi ý, không có một mô hình đơn lẻ nào là hoàn hảo:


| Mô hình đơn lẻ                           | Ưu điểm cốt lõi                                                                                                                                                                    | Nhược điểm chí mạng                                                                                                                                                                |
| :---------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Spark ALS (Matrix Factorization)**     | Bắt trúng hành vi cộng tác ngầm (Latent Collaborative signals); tính toán ma trận phân tán cực nhanh trên tập dữ liệu lớn.                                                         | **Hộp đen (Black-box)**, hoàn toàn không giải thích được; tê liệt trước phim mới (Cold-Start); bị **Fluke Bias** trên danh mục đuôi dài (phóng đại điểm số của phim ít người xem). |
| **Knowledge Graph (Metapaths P1-P2-P3)** | **Minh bạch 100% (Explainable AI)**; phân giải sâu sắc cảm xúc vi mô (1,128 chiều Tag Genome); giải quyết triệt để Cold-Start nhờ các liên kết thực thể (Thể loại, Thẻ ngữ nghĩa). | Độ phức tạp duyệt đồ thị cao hơn tính tích vô hướng ma trận; phụ thuộc vào chất lượng của siêu dữ liệu (metadata).                                                                 |


**Triết lý của Tầng Lai ghép (Hybrid Layer) trong MoodGraph:**
Không để hai mô hình triệt tiêu lẫn nhau, mà đóng vai trò là một **Bộ điều phối cấp cao (Meta-Orchestrator)**:

1. Thu nhận danh sách ứng viên độc lập từ cả hai thế giới (Ma trận ẩn ALS và Đồ thị tri thức KG).
2. Bảo toàn đầy đủ bằng chứng giải thích từ KG và ghi nhận thêm độ tương đồng cộng tác từ ALS.
3. Dung hợp thứ hạng để đưa ra danh sách Top-N vừa chuẩn gu, vừa đa dạng, vừa có lời giải thích tường minh cho người dùng.

---

## 2. KIẾN TRÚC HỢP NHẤT TẬP ỨNG VIÊN (CANDIDATE UNION ARCHITECTURE)

### 2.1. Phép Hợp Tập Hợp (Candidate Union)

Mã nguồn cài đặt: [recommender/hybrid/engine.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/engine.py#L143-L208)

Hệ thống **tuyệt đối không sử dụng đường ống tuần tự (Sequential Pipeline)** theo kiểu: *"Lấy Top-50 của ALS rồi bắt KG xếp hạng lại 50 phim đó"*.  
Lý do: Nếu ALS bị lỗi Fluke Bias (Top-50 toàn phim rác đuôi dài), việc ép KG chỉ chấm điểm trong 50 phim đó sẽ bóp chết hoàn toàn khả năng gợi ý đúng của KG.

Thay vào đó, hệ thống triển khai kiến trúc **Hợp Nhất Ứng Viên Độc Lập (Independent Candidate Generation & Union)**:

```text
[ Người dùng u ]
       ├── Gọi song song ──> ALS Service  ──> Sinh Top 50 ứng viên: C_ALS(u)
       └── Gọi song song ──> KG Engine    ──> Sinh Top 50 ứng viên: C_KG(u)
                                                      │
                                                      ▼
                       HỢP NHẤT: C_Hybrid(u) = C_ALS(u) ∪ C_KG(u)
                           (Quy mô tập ứng viên: 50 đến 100 phim)
                                                      │
                                                      ▼
                                       LỌC PHIM ĐÃ XEM (Seen Filter)
                                                      │
                                                      ▼
                                     THUẬT TOÁN DUNG HỢP (Fusion Engine)
                                          (RRF k=60 hoặc Weighted)
                                                      │
                                                      ▼
                                         DANH SÁCH TOP-N CUỐI CÙNG
```

### 2.2. Cơ Chế Lọc Đã Xem Đa Lớp (Defense-in-depth Seen Filtering)

Mã nguồn: [recommender/hybrid/engine.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/engine.py#L130-L141) và dòng [227 – 230](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/engine.py#L227-L230):

- **Lớp 1 (Tại nguồn):** Truyền tập `seen_movies` vào hàm `recommend()` của từng mô hình con để không sinh ứng viên trùng.
- **Lớp 2 (Tại bộ dung hợp):** Quét lại lần thứ hai trước khi đưa vào hàm fusion:
  ```python
  if filter_seen and seen_movies:
      cand_als = [c for c in cand_als if int(c["movieId"]) not in seen_movies]
      cand_kg = [c for c in cand_kg if int(c["movieId"]) not in seen_movies]
  ```

Điều này đảm bảo 100% không bao giờ có một bộ phim người dùng đã xem trong quá khứ lọt vào danh sách gợi ý.

---

## 3. MỔ XẺ THUẬT TOÁN DUNG HỢP 1: CORMACK RECIPROCAL RANK FUSION (RRF)

Mã nguồn cài đặt: [recommender/hybrid/fusion.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L58-L160)

### 3.1. Vấn Đề Cốt Tử: Xung Đột Thang Đo Điểm Số (Score Incompatibility)

- Mô hình Spark ALS trả về điểm **Tích vô hướng ma trận (Dot-Product)**: Thang đo không chặn, có thể nhận giá trị từ `0.07` đến `10.84`.
- Mô hình Knowledge Graph trả về **Trọng số đường đi chuẩn hóa Min-Max**: Thang đo nằm chặt trong đoạn `[0.0, 1.0]`.

Nếu cộng trực tiếp hai điểm số này lại với nhau (`Score_ALS + Score_KG`), điểm số ALS (lên tới 10.0) sẽ đè bẹp hoàn toàn điểm số KG (chỉ từ 0 đến 1). Việc này biến hệ thống trở thành 100% ALS, phá hủy toàn bộ công sức của Đồ thị tri thức!

### 3.2. Giải Pháp: Bất Biến Với Thang Đo (Scale-Invariant)

Thuật toán **Reciprocal Rank Fusion (RRF)** giải quyết triệt để vấn đề này bằng cách: **Bỏ qua điểm số thô, chỉ quan tâm đến THỨ HẠNG (Rank) của ứng viên trong từng danh sách!**

### 3.3. Công Thức Toán Học Cormack RRF

Công thức tính điểm RRF cho một bộ phim $m$:

```text
RRF_Score(m) = Tổng [ 1 / (k + Rank_s(m)) ]
với s thuộc tập các mô hình {ALS, KG}
```

Trong đó:

- `Rank_s(m)`: Thứ hạng của phim $m$ trong danh sách ứng viên của mô hình $s$ (bắt đầu từ 1, 2, 3...). Nếu phim không nằm trong danh sách của mô hình $s$, số hạng này bằng 0.
- `k`: Hằng số làm mịn (Smoothing constant). Dự án chọn **`k = 60`**.

### 3.4. Vì Sao Lại Chọn Hằng Số `k = 60`?

Đây là câu hỏi Thầy rất hay hỏi để kiểm tra xem bạn có hiểu nguồn gốc thuật toán không:

- **Nguồn gốc học thuật:** Giá trị `k = 60` được đề xuất bởi **Gordon V. Cormack, Charles L. A. Clarke và Stefan Buettcher** trong công trình kinh điển tại Hội nghị **ACM SIGIR 2009** (*"Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods"*).
- **Ý nghĩa toán học của số 60:**
  - Nếu chọn `k` quá nhỏ (ví dụ `k = 1`): Phim xếp hạng 1 sẽ nhận điểm `1 / (1 + 1) = 0.5`, phim xếp hạng 2 nhận `1 / (1 + 2) = 0.333`. Khoảng cách giữa hạng 1 và hạng 2 là quá lớn (chênh lệch 0.167), khiến cho phim đứng đầu của một mô hình áp đảo hoàn toàn các phim khác.
  - Khi chọn `k = 60`:
    - Hạng 1 nhận điểm: `1 / (60 + 1) = 1 / 61 ≈ 0.01639`
    - Hạng 2 nhận điểm: `1 / (60 + 2) = 1 / 62 ≈ 0.01613`
    - Hạng 10 nhận điểm: `1 / (60 + 10) = 1 / 70 ≈ 0.01428`
  - **Sức mạnh kỳ diệu:** Nếu một bộ phim $A$ đứng hạng 5 ở cả hai nguồn ALS và KG (được cả 2 mô hình đồng thuận), điểm của nó là:
  `1 / (60 + 5) + 1 / (60 + 5) = 2 / 65 ≈ 0.03077`
  Điểm này **vượt xa** một bộ phim $B$ chỉ đứng hạng 1 ở ALS nhưng hoàn toàn vắng mặt ở KG (`1 / 61 ≈ 0.01639`)!
  - **Kết luận:** Hằng số `k = 60` đóng vai trò làm mịn đường cong suy giảm thứ hạng, tạo cơ hội cho các ứng viên xuất hiện đồng thời ở cả hai nguồn (**Source = BOTH**) vươn lên dẫn đầu.

### 3.5. Cơ Chế Giải Quyết Hòa Điểm (Deterministic Tie-Breaking)

Mã nguồn dòng 151 trong [recommender/hybrid/fusion.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L151):

```python
fused_items.sort(key=lambda x: (-x["hybrid_score"], x["movieId"]))
```

- Ưu tiên 1: Điểm `hybrid_score` cao hơn xếp trước (dấu trừ `-`).
- Ưu tiên 2: Nếu hai phim bằng điểm RRF nhau chằn chặn, phim nào có `movieId` nhỏ hơn sẽ xếp trước.  
Điều này đảm bảo tính **Tất định 100% (Deterministic)**: Chạy 1 triệu lần thì thứ tự kết quả vẫn đồng nhất tuyệt đối, không có hiện tượng ngẫu nhiên làm sai lệch kết quả thực nghiệm.

---

## 4. MỔ XẺ THUẬT TOÁN DUNG HỢP 2: WEIGHTED SCORE FUSION & VẤN ĐỀ NỘI SUY (IMPUTATION)

Mã nguồn cài đặt: [recommender/hybrid/fusion.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L162-L291)

Nếu không muốn dùng thứ hạng RRF mà muốn kết hợp trực tiếp điểm số thực tế, hệ thống cung cấp thuật toán **Dung Hợp Tuyến Tính Có Trọng Số (Weighted Score Fusion)**.

### 4.1. Chuẩn Hóa Điểm Số (Score Normalization)

Để khắc phục sự xung đột thang đo giữa ALS và KG, hệ thống chuẩn hóa điểm số của từng nguồn độc lập về đoạn `[0.0, 1.0]` bằng hàm `normalize_min_max` (dòng [22 – 39](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L22-L39)):

```text
Norm_Score(m) = (Score(m) - Min_Score) / (Max_Score - Min_Score)
```

*(Nếu toàn bộ điểm bằng nhau hoặc Max == Min, hàm trả về 1.0 để tránh lỗi chia cho 0).*

### 4.2. Bài Toán Nan Giải: Ứng Viên Khuyết Thiếu (Missing Candidate Imputation)

Giả sử phim $X$ nằm trong Top-50 của KG nhưng hoàn toàn **không xuất hiện** trong Top-50 của ALS. Vậy khi tính điểm:

```text
Hybrid_Score(X) = (w_ALS × Norm_ALS(X)) + (w_KG × Norm_KG(X))
```

Thì `Norm_ALS(X)` lấy giá trị bằng bao nhiêu?  
Đây là điểm thể hiện chiều sâu nghiên cứu của nhóm với 4 chiến lược nội suy tại dòng [213 – 229](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L213-L229):

1. **Chiến lược `zero` (Mặc định):** Gán điểm khuyết bằng `0.0`. Ý nghĩa: Nếu mô hình không đề xuất phim này vào Top-50, coi như mô hình đó cho điểm tối thiểu.
2. **Chiến lược `min`:** Gán bằng giá trị chuẩn hóa nhỏ nhất của danh sách hiện tại.
3. **Chiến lược `neutral`:** Gán bằng `0.5` (mức trung lập).
4. **Chiến lược `source_aware` (Nhận thức nguồn gốc):**
   - Với ALS: Gán sàn `0.2` (vì đây là Top-50 cắt cụt từ 62,000 phim; các phim ngoài Top-50 vẫn có một độ tương đồng ẩn nhất định trong không gian vector).
   - Với KG: Gán `0.0` (vì trong đồ thị, nếu không có đường đi kết nối thì độ tương quan thực chất bằng 0).

---

## 5. GIẢI THÍCH BẢN CHẤT THỰC NGHIỆM: VÌ SAO HYBRID W_ALS=0.1 / W_KG=0.9 LẠI TỐI ƯU?

Dữ liệu thực nghiệm đo đạc độc lập tại [docs/phase4/hybrid_validation_results.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/phase4/hybrid_validation_results.json) chỉ ra một kết quả thực nghiệm vô cùng giá trị:


| Trọng số kết hợp                     | HR@5       | HR@10      | HR@20      | NDCG@10    | Catalog Coverage@10 | Nhận xét bản chất                     |
| :------------------------------------ | :----------: | :----------: | :----------: | :----------: | :-------------------: | :------------------------------------- |
| **Pure KG (w\_ALS=0.0, w\_KG=1.0)**  | **0.0986** | **0.0986** | **0.1549** | **0.0460** | **276 phim**        | **Đỉnh cao chất lượng và độ phủ**     |
| **Hybrid (w\_ALS=0.1, w\_KG=0.9)**   | **0.0986** | **0.0986** | **0.1549** | **0.0460** | **276 phim**        | **Tối ưu nhất cho mô hình lai**       |
| Hybrid (w\_ALS=0.3, w\_KG=0.7)       | 0.0986     | 0.0986     | 0.1268     | 0.0460     | 262 phim            | Bắt đầu suy giảm nhẹ HR@20            |
| Hybrid (w\_ALS=0.5, w\_KG=0.5)       | 0.0282     | 0.0986     | 0.1127     | 0.0366     | 197 phim            | Suy giảm rõ rệt cả HR, NDCG, Coverage |
| Hybrid (w\_ALS=0.7, w\_KG=0.3)       | 0.0000     | 0.0423     | 0.0986     | 0.0131     | 110 phim            | Bị ALS kéo tụt chất lượng             |
| **Hybrid (w\_ALS=0.9, w\_KG=0.1)**   | 0.0000     | 0.0000     | 0.0141     | 0.0000     | 12 phim             | Bị hủy hoại bởi Fluke Bias            |
| **Pure ALS (w\_ALS=1.0, w\_KG=0.0)** | 0.0000     | 0.0000     | 0.0000     | 0.0000     | 12 phim             | Thất bại hoàn toàn trên Full-Catalog  |


### Phân Tích Hiện Tượng Dành Cho Bạn Nghiên Cứu Sâu:

1. **Tại sao không phải 50/50 mà phải là 0.1 ALS / 0.9 KG?**
   - Như đã chứng minh tại Module M09, trên không gian toàn bộ 62,423 phim, hơn 51% danh mục là phim cực ít tương tác (1-5 ratings). Mô hình ALS thuần bị hiện tượng **Norm Inflation**: các vector phim ít người xem bị xoay tự do và phóng đại độ chuẩn, tạo ra điểm tích vô hướng cao bất thường (Fluke Bias).
   - Nếu bạn đặt trọng số ALS cao (`w_ALS >= 0.5`), các bộ phim "rác" đuôi dài này của ALS sẽ tràn vào Top-10 và đẩy văng các bộ phim chuẩn gu, giàu ngữ nghĩa của Knowledge Graph ra ngoài!
2. **Vai trò thực sự của ALS trong mô hình lai:**
   - Với tỷ lệ `w_ALS = 0.1` và `w_KG = 0.9`: Knowledge Graph đóng vai trò là **Bộ khung định hướng ngữ nghĩa (Semantic Anchor)** để giữ toàn bộ các phim đề xuất phải đúng gu người dùng.
   - Trọng số nhỏ 0.1 của ALS đóng vai trò là một **Cú huých cộng tác (Collaborative Fine-tuning Nudge)**: Giữa 2 bộ phim có cùng điểm số đồ thị KG tương đương nhau, bộ phim nào có thêm tín hiệu ma trận ẩn ALS ủng hộ sẽ được ưu tiên xếp nhỉnh hơn một bậc.

---

## 6. CƠ CHẾ PHẢN HỒI VÒNG LẶP KHÉP KÍN & TÁI XẾP HẠNG TỨC THỜI (CLOSED-LOOP RE-RANKING)

Đây là tính năng độc đáo giúp hệ thống MoodGraph chuyển từ một thuật toán gợi ý tĩnh (Offline Batch) thành một hệ thống thông minh tương tác thời gian thực (Online Interactive System).

Mã nguồn điều phối:

- Dịch vụ người dùng: [recommender/services/user_interaction_service.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/services/user_interaction_service.py#L76-L105)
- Cơ chế đồng bộ đồ thị: [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L199-L247)

### Quy Trình 5 Bước Vòng Lặp Khép Kín (Closed-Loop Workflow):

```text
[ BƯỚC 1: HÀNH ĐỘNG ] Người dùng bấm chấm 5.0 sao cho phim "Inception" trên Giao diện Web.
                                │
                                ▼
[ BƯỚC 2: LƯU TRỮ ]   UserInteractionService ghi nhận đánh giá vào SQLite (data/app_state.db).
                                │
                                ▼
[ BƯỚC 3: HỦY CACHE ] Gọi self._invalidate_user_cache(user_id):
                      Toàn bộ kết quả gợi ý cũ của user này trong HybridRecommendationCache
                      bị xóa ngay lập tức (Cache Eviction).
                                │
                                ▼
[ BƯỚC 4: ĐỒNG BỘ ĐỒ THỊ ] Khi có yêu cầu gợi ý mới, EmbeddedKnowledgeGraph tự động gọi:
                          sync_with_sqlite() -> Đọc tương tác mới và tạo ngay cạnh:
                          (User) --[:RATED {rating: 5.0}]--> (Inception) vào RAM trong 1.5ms!
                                │
                                ▼
[ BƯỚC 5: TÁI XẾP HẠNG ]   Động cơ tính điểm lan truyền dọc theo 3 đường Metapaths từ "Inception":
                          - P1 lan truyền sang các phim Sci-Fi khác (Interstellar, Tenet).
                          - P2 lan truyền theo các thẻ 'dream', 'mindfuck', 'subconscious'.
                          - P3 lan truyền theo cộng đồng khán giả cũng thích Inception.
                          => Danh sách Top-10 được TÁI XẾP HẠNG MỚI TOÀN BỘ (< 30ms)!
```

---

## 7. BỘ NHỚ ĐỆM LRU CHỐNG NHIỄM CHÉO (MULTI-DIMENSIONAL CACHE)

Mã nguồn cài đặt: [recommender/hybrid/cache.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/cache.py) kết hợp dòng [98 – 129](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/engine.py#L98-L129) trong `engine.py`.

### 7.1. Bài Toán Ô Nhiễm Bộ Nhớ Đệm (Cache Contamination)

Nếu chỉ lưu cache theo `key = user_id`, khi người dùng đổi từ chiến lược RRF sang chiến lược Weighted, hệ thống sẽ trả về nhầm kết quả cũ của RRF!

### 7.2. Giải Pháp: Khóa Bộ Đệm Đa Chiều (13-Dimensional Cache Key)

Hệ thống MoodGraph thiết kế khóa cache tuple gồm đủ 13 tham số biến thiên:

```python
cache_key = (
    user_id,
    effective_top_n,
    effective_strategy,     # 'rrf' hay 'weighted' hay 'als_only'
    effective_w_als,        # 0.1, 0.5, ...
    effective_w_kg,         # 0.9, 0.5, ...
    effective_rrf_k,        # 60
    stage,                  # 'production'
    filter_seen,            # True/False
    top_k_candidates_als,
    top_k_candidates_kg,
    normalize_method,
    imputation_strategy,
    bool(effective_cross_score),
)
```

- **Thời gian sống (TTL):** 3,600 giây (1 giờ).
- **Cơ chế dọn dẹp (Eviction):** Kế thừa cấu trúc `OrderedDict` theo thuật toán LRU (Least Recently Used) với giới hạn `max_size = 10,000` phần tử.
- **Hiệu năng phục vụ (Serving Latency):** Khi Cache Hit, thời gian phản hồi API chỉ mất **0.05 – 0.2 mili-giây** (siêu tốc).

---

## 8. BẢNG TRA CỨU NHANH CHO THẦY XEM (CODE SHOW-AND-TELL MAP)


| Thầy hỏi về vấn đề gì                                          | File cần mở ngay lập tức                           | Dòng code trọng tâm                                                        |
| :-------------------------------------------------------------- | :-------------------------------------------------- | :-------------------------------------------------------------------------- |
| **"Thuật toán Cormack RRF k=60 cài đặt ở đâu?"**               | `recommender/hybrid/fusion.py`                     | Dòng **58 – 160** (Công thức `1.0 / (rrf_k + rank)` và tie-break)          |
| **"Chuẩn hóa Min-Max và dung hợp trọng số Weighted ở đâu?"**   | `recommender/hybrid/fusion.py`                     | Dòng **22 – 39** (Min-Max) và dòng **162 – 291** (Weighted)                |
| **"Xử lý ứng viên khuyết thiếu (Imputation) thế nào?"**        | `recommender/hybrid/fusion.py`                     | Dòng **213 – 229** (4 chiến lược `zero`, `min`, `neutral`, `source_aware`) |
| **"Điều phối hợp nhất ứng viên Candidate Union ở đâu?"**       | `recommender/hybrid/engine.py`                     | Dòng **143 – 230** (Sinh ứng viên độc lập từ ALS và KG rồi hợp tập)        |
| **"Phản hồi khép kín (Closed-Loop) khi user chấm sao ở đâu?"** | `recommender/services/user_interaction_service.py` | Dòng **76 – 105** (Lưu SQLite và hủy cache gợi ý cũ)                       |
| **"Đồng bộ tức thì tương tác mới vào Đồ thị tri thức ở đâu?"** | `recommender/kg/embedded_graph.py`                 | Dòng **199 – 247** (Hàm `sync_with_sqlite`)                                |
| **"Cấu trúc Cache Key 13 chiều chống ô nhiễm đệm ở đâu?"**     | `recommender/hybrid/engine.py`                     | Dòng **100 – 114** (Định nghĩa `cache_key`)                                |
|                                                                |                                                    |                                                                            |


---

## 9. 5 CÂU HỎI VẤN ĐÁP "CHÍ MẠNG" CỦA TS. BÙI THANH HÙNG & LỜI GIẢI ĐIỂM 10

### CÂU 1: Vì sao nhóm không cộng trực tiếp điểm số của ALS và KG mà phải dùng RRF hoặc chuẩn hóa Min-Max?

- **Trả lời điểm 10:**  
*"Dạ thưa Thầy, vì hai mô hình này có thang đo điểm số hoàn toàn xung đột (Scale Incompatible). Điểm ALS là tích vô hướng ma trận không chặn, thực nghiệm cho thấy dao động từ 0.07 đến tận 10.84. Trong khi đó, điểm Knowledge Graph là trọng số đường đi chuẩn hóa chỉ nằm từ 0.0 đến 1.0. Nếu cộng trực tiếp, điểm ALS lớn gấp 10 lần sẽ đè bẹp hoàn toàn điểm KG, biến hệ thống thành mô hình ALS thuần túy. Thuật toán Cormack RRF giải quyết triệt để vấn đề này vì nó hoạt động dựa trên Thứ Hạng (Rank) chứ không phụ thuộc vào thang đo điểm số (Scale-Invariant)."*

### CÂU 2: Con số `k = 60` trong công thức RRF từ đâu ra? Có phải nhóm tự bịa ra không?

- **Trả lời điểm 10:**  
*"Dạ thưa Thầy, số `k = 60` là chuẩn mực kinh điển được đề xuất bởi Cormack, Clarke và Buettcher trong công trình công bố tại Hội nghị ACM SIGIR 2009 về Information Retrieval. Về mặt toán học, hằng số `k = 60` hoạt động như một hệ số làm mịn (Smoothing Factor) để triệt tiêu ưu thế độc tôn của các vị trí đầu bảng (Rank 1, Rank 2), đồng thời tạo ra xác suất toán học để những bộ phim xuất hiện đồng thời ở cả hai nguồn (Source = BOTH) có thể vượt lên dẫn đầu bảng xếp hạng."*

### CÂU 3: Trong thuật toán Weighted Fusion, nếu một bộ phim chỉ nằm trong Top-50 của KG mà không có trong Top-50 của ALS thì nhóm gán điểm ALS bằng bao nhiêu?

- **Trả lời điểm 10:**  
*"Dạ thưa Thầy, trong mã nguồn `recommender/hybrid/fusion.py` tại dòng 213, nhóm đã thiết kế 4 chiến lược nội suy (Imputation Strategy). Mặc định là chiến lược `zero` (gán điểm bằng 0.0). Ngoài ra, nhóm có chiến lược nâng cao là `source_aware`: với các phim ngoài Top-50 của ALS sẽ được gán sàn 0.2 (vì thực tế phim vẫn có độ tương đồng tiềm ẩn nhất định trong không gian vector nhưng bị cắt cụt do Top-K), còn với KG thì gán 0.0 vì không có đường đi kết nối trong đồ thị thì mức độ liên quan thực sự bằng 0."*

### CÂU 4: Kết quả thực nghiệm cho thấy cấu hình Hybrid tối ưu nhất là `0.1 ALS + 0.9 KG`. Tại sao tỷ trọng ALS lại thấp như vậy? Vậy vai trò của ALS là gì?

- **Trả lời điểm 10:**  
*"Dạ thưa Thầy, đây là phát hiện thực nghiệm mang tính khoa học sâu sắc của nhóm: Do danh mục MovieLens 25M có hơn 51% là phim cực ít tương tác (đuôi dài), thuật toán ALS bị hiện tượng Fluke Bias (phóng đại độ chuẩn vector khiến phim ít người xem có điểm dự đoán cao giả tạo). Nếu đặt trọng số ALS cao (từ 0.5 trở lên), các phim rác này sẽ tràn vào Top-10 và phá hủy độ chính xác của KG.*  
*Vì vậy, tỷ lệ `0.1 ALS + 0.9 KG` là tỷ lệ tối ưu nhất: Knowledge Graph (0.9) giữ vai trò là mỏ neo định hướng đúng gu ngữ nghĩa và cảm xúc, còn tín hiệu ALS (0.1) đóng vai trò là một 'cú huých cộng tác' (Collaborative Nudge) giúp phân định thứ hạng giữa các bộ phim có cùng điểm số đồ thị tương đương nhau."*

### CÂU 5: Khi người dùng bấm thích một bộ phim trên web, hệ thống làm thế nào để gợi ý thay đổi ngay lập tức mà không cần train lại ALS?

- **Trả lời điểm 10:**  
*"Dạ thưa Thầy, việc huấn luyện lại mô hình Spark ALS cho 25 triệu ratings mất hơn 2 phút, không thể chạy trong thời gian thực. Nhóm giải quyết bài toán này bằng cơ chế Vòng lặp khép kín (Closed-Loop Feedback) thông qua Đồ thị tri thức nhúng:  
  1. Khi người dùng đánh giá phim, tương tác được lưu vào SQLite `app_state.db`.
  2. Hệ thống lập tức hủy bộ nhớ đệm (Cache Invalidation) của người dùng đó.
  3. Phương thức `sync_with_sqlite()` nạp ngay lập tức cạnh đánh giá mới vào đồ thị trong RAM chỉ mất 1.5ms.
  4. Động cơ đồ thị lan truyền suy luận từ bộ phim mới thích theo 3 đường Metapaths và tính toán lại danh sách gợi ý mới chỉ trong chưa đầy 30ms, mang lại trải nghiệm tương tác thời gian thực mượt mà cho người dùng."*

---

*Tài liệu thuộc bộ giáo trình 5-Day Mastery Curriculum môn Giới thiệu về Dữ liệu lớn — Dự án MoodGraph.*