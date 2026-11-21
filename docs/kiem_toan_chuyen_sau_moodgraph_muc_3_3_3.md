# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.3.3

> **Chuyên đề:** 3.3.3. Đường đi P3: Gợi ý theo quan hệ sở thích cộng đồng (Collaborative Metapath)  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Tệp kiểm toán cốt lõi:** `recommender/kg/scorer.py`, `recommender/kg/embedded_graph.py`, `tests/kg/test_path_scoring.py`  
> **Trạng thái:** ĐÃ KIỂM ĐỊNH MÃ NGUỒN VÀ ĐỐI CHIẾU THỰC NGHIỆM 100%

---

## PHẦN A — BẢNG KIỂM TOÁN MÃ NGUỒN

| Thành phần thuật toán | Công thức / Quy tắc thực tế | Ý nghĩa kỹ thuật | Bằng chứng file:line |
|---|---|---|---|
| **Cấu trúc Metapath** | $u \xrightarrow{\text{RATED}} m \xleftarrow{\text{RATED}} v \xrightarrow{\text{RATED}} c$ | Đường đi 3 chặng qua đồ thị: Người dùng mục tiêu $\to$ Phim mỏ neo $\to$ Người dùng láng giềng $\to$ Phim ứng viên. | [scorer.py:9-10](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L9-L10)<br>[scorer.py:155-197](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L155-L197) |
| **Lọc mỏ neo và láng giềng** | $r \ge 3.5$ ở cả 4 bước | Áp dụng ngưỡng 3.5 sao: (1) Phim mỏ neo của $u$, (2) Phim chung của $v$, (3) Đếm số phim thích của $v$, (4) Phim ứng viên $c$. | [scorer.py:127-129](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L127-L129)<br>[scorer.py:164](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L164)<br>[scorer.py:193](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L193) |
| **Độ tương đồng láng giềng** | $\text{sim}(u, v) = \frac{|\mathcal{M}_u \cap \mathcal{M}_v|}{\sqrt{|\mathcal{M}_u| \cdot |\mathcal{M}_v|}}$ | Salton Cosine Similarity (hệ số Ochiai) tính trên tập hợp các phim được đánh giá tích cực giữa hai người dùng. | [scorer.py:184](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L184)<br>[embedded_graph.py:189](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L189) |
| **Chỉ mục bộ đệm bậc thích** | `user_liked_counts[v]` | Truy xuất trong O(1) tổng số phim có rating >= 3.5 của láng giềng, triệt tiêu phép quét lặp tính mẫu số. | [embedded_graph.py:53-61](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L53-L61)<br>[scorer.py:176-177](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L176-L177) |
| **Trọng số sở thích láng giềng** | $w(r_{v, c}) = \max\left(0, \frac{r_{v, c} - 3.0}{2.0}\right)$ | Tuyến tính hóa rating của láng giềng trên phim ứng viên thành trọng số [0.25, 1.0]. | [scorer.py:85-87](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L85-L87)<br>[scorer.py:194](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L194) |
| **Cắt tỉa Top-K láng giềng** | $\text{Top-}50$ láng giềng cao nhất | Chỉ giữ lại tối đa 50 người dùng có độ tương đồng cao nhất (`max_neighbors = 50`) để lan truyền ứng viên. | [kg_config.yaml:15](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L15)<br>[scorer.py:188](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L188) |
| **Cắt tỉa đồ thị lớn** | Giới hạn 80 user/anchor, lọc chung < 2 phim | Nếu $> 30$ ứng viên láng giềng, bỏ qua láng giềng chỉ chung 1 phim; mỗi mỏ neo lấy tối đa 80 user. | [kg_config.yaml:16](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L16)<br>[scorer.py:167-175](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L167-L175) |
| **Điểm P3 thô (Raw Score)** | $\text{Score}_{P_3}^{\text{raw}}(u, c) = \sum_{v} \text{sim}(u, v) \cdot w(r_{v, c})$ | Tổng đóng góp tích lũy từ toàn bộ láng giềng cùng thích phim ứng viên $c$. | [scorer.py:195](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L195)<br>[scorer.py:406](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L406) |
| **Khởi tạo Candidate Pool** | `all_candidate_ids.add(cand_mid)` | P3 trực tiếp tìm kiếm và đưa các phim do láng giềng yêu thích vào tập ứng viên chung của hệ thống. | [scorer.py:196](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L196) |
| **Chuẩn hóa Min-Max** | $\text{Norm\_P3}(c) = \frac{\text{Raw} - \min}{\max - \min}$ | Chuẩn hóa điểm P3 thô về đoạn [0.0, 1.0] trước khi nhân trọng số $\gamma = 0.20$. | [scorer.py:283](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L283)<br>[scorer.py:325-333](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L325-L333) |

---

## PHẦN B — CÔNG THỨC TOÁN HỌC CHUẨN

Đường đi siêu liên kết cộng tác cộng đồng $P_3$ được định nghĩa theo chuỗi quan hệ:
$$\mathcal{P}_3: \text{User} \xrightarrow{\text{RATED}} \text{Movie} \xleftarrow{\text{RATED}} \text{User} \xrightarrow{\text{RATED}} \text{Movie}$$

### 1. Tập hợp mỏ neo tích cực
Gọi $\mathcal{M}_u^{\text{liked}}$ là tập các phim người dùng mục tiêu $u$ đã đánh giá tích cực trong tập huấn luyện:
$$\mathcal{M}_u^{\text{liked}} = \{m \in \mathcal{M}_u^{\text{seen}} \mid r_{u,m} \ge 3.5\}$$
Trên đồ thị quy mô lớn, nếu $|\mathcal{M}_u^{\text{liked}}| > 20$, hệ thống chỉ giữ lại tập con $\mathcal{M}_u^{\text{active}} \subseteq \mathcal{M}_u^{\text{liked}}$ gồm tối đa 20 phim có điểm đánh giá cao nhất và mốc thời gian gần nhất.

### 2. Độ tương đồng láng giềng (Salton Cosine Similarity)
Một người dùng $v \neq u$ được xem là láng giềng tiềm năng nếu cùng đánh giá tích cực ít nhất một bộ phim mỏ neo của $u$. Độ tương đồng sở thích giữa $u$ và $v$ được xác định theo hệ số Cosine Salton trên tập hợp các bộ phim được yêu thích:
$$\text{sim}(u, v) = \frac{|\mathcal{M}_u^{\text{active}} \cap \mathcal{M}_v^{\text{liked}}|}{\sqrt{|\mathcal{M}_u^{\text{active}}| \cdot |\mathcal{M}_v^{\text{liked}}|}}$$
Trong đó:
- $|\mathcal{M}_u^{\text{active}} \cap \mathcal{M}_v^{\text{liked}}|$ là số lượng bộ phim chung mà cả $u$ và $v$ đều đánh giá $\ge 3.5$ sao.
- $|\mathcal{M}_u^{\text{active}}|$ và $|\mathcal{M}_v^{\text{liked}}|$ lần lượt là tổng số phim được đánh giá tích cực của người dùng $u$ và người dùng $v$.
- Giá trị $\text{sim}(u, v) \in [0.0, 1.0]$. Nếu hai người dùng không có phim thích chung hoặc một trong hai người không có phim thích, $\text{sim}(u, v) = 0$.

Tập hợp láng giềng tinh tuyển $\mathcal{N}_u$ được tạo thành bằng cách sắp xếp giảm dần theo $\text{sim}(u, v)$ và lấy tối đa $K = 50$ người dùng có độ tương đồng cao nhất:
$$\mathcal{N}_u = \text{Top-}50_{v} \left( \text{sim}(u, v) \right)$$

### 3. Công thức tính điểm P3 thô (Raw Score)
Với mỗi tác phẩm ứng viên $c \notin \mathcal{M}_u^{\text{seen}}$, điểm số cộng tác thô $\text{Score}_{P_3}^{\text{raw}}(u, c)$ được tổng hợp từ toàn bộ các láng giềng trong $\mathcal{N}_u$ đã từng đánh giá tích cực bộ phim $c$:
$$\text{Score}_{P_3}^{\text{raw}}(u, c) = \sum_{v \in \mathcal{N}_u \cap \mathcal{U}_c^{\text{liked}}} \text{sim}(u, v) \cdot w(r_{v, c})$$
Trong đó:
- $\mathcal{U}_c^{\text{liked}} = \{v \mid r_{v, c} \ge 3.5\}$ là tập các người dùng từng đánh giá tích cực phim ứng viên $c$.
- $w(r_{v, c}) = \max\left(0, \frac{r_{v, c} - 3.0}{2.0}\right)$ là hàm trọng số sở thích của láng giềng $v$ đối với phim $c$.
- Nếu không có láng giềng nào trong $\mathcal{N}_u$ đánh giá tích cực phim $c$, điểm số $\text{Score}_{P_3}^{\text{raw}}(u, c) = 0.0$.

### 4. Chuẩn hóa Min-Max (Normalized Score)
Để phối hợp đồng bộ với $P_1$ và $P_2$, điểm số thô được đưa về đoạn $[0.0, 1.0]$ trên toàn bộ không gian ứng viên $\mathcal{C}$:
$$\text{Score}_{P_3}^{\text{norm}}(u, c) = \begin{cases} 
\frac{\text{Score}_{P_3}^{\text{raw}}(u, c) - \min_{x \in \mathcal{C}} \text{Score}_{P_3}^{\text{raw}}(u, x)}{\max_{x \in \mathcal{C}} \text{Score}_{P_3}^{\text{raw}}(u, x) - \min_{x \in \mathcal{C}} \text{Score}_{P_3}^{\text{raw}}(u, x)}, & \text{nếu } \max - \min \ge 10^{-9} \\
1.0, & \text{nếu } \max = \min > 0 \\
0.0, & \text{ngược lại}
\end{cases}$$
Điểm chuẩn hóa $\text{Score}_{P_3}^{\text{norm}}(u, c)$ đóng góp với hệ số trọng số $\gamma = 0.20$ vào điểm số đồ thị tri thức tổng hợp.

---

## PHẦN C — VÍ DỤ TÍNH TAY MINH HỌA

### 1. Dữ liệu giả định
- **Người dùng:** An ($u_A$), Bình ($u_B$), Chi ($u_C$).
- **Lịch sử đánh giá ban đầu:**
  * **An ($u_A$):**
    - Phim 1: $5.0$ sao $\implies$ Thích ($w = 1.0$)
    - Phim 2: $4.5$ sao $\implies$ Thích ($w = 0.75$)
    - Phim 3: $3.0$ sao $\implies$ Bị loại khỏi mỏ neo vì $r < 3.5$ và $w(3.0) = 0.0$.  
    $\implies$ Tập phim mỏ neo của An: $\mathcal{M}_A^{\text{liked}} = \{\text{Phim 1, Phim 2}\}$, số lượng $|\mathcal{M}_A^{\text{liked}}| = 2$.
  * **Bình ($u_B$):**
    - Phim 1: $4.5$ sao $\implies$ Thích ($w = 0.75$)
    - Phim 2: $4.0$ sao $\implies$ Thích ($w = 0.50$)
    - Phim 4: $5.0$ sao $\implies$ Thích ($w = 1.0$)  
    $\implies$ Tập phim thích của Bình: $\mathcal{M}_B^{\text{liked}} = \{\text{Phim 1, Phim 2, Phim 4}\}$, số lượng $|\mathcal{M}_B^{\text{liked}}| = 3$.
  * **Chi ($u_C$):**
    - Phim 1: $5.0$ sao $\implies$ Thích ($w = 1.0$)
    - Phim 4: $4.0$ sao $\implies$ Thích ($w = 0.50$)
    - Phim 5: $4.5$ sao $\implies$ Thích ($w = 0.75$)  
    $\implies$ Tập phim thích của Chi: $\mathcal{M}_C^{\text{liked}} = \{\text{Phim 1, Phim 4, Phim 5}\}$, số lượng $|\mathcal{M}_C^{\text{liked}}| = 3$.
- **Phim ứng viên cho An (chưa xem):** Phim 4 và Phim 5.

### 2. Các bước tính toán chi tiết

**Bước 1: Xác định giao thoa phim thích chung:**
- Giữa An và Bình: Chung Phim 1 và Phim 2 $\implies |\mathcal{M}_A \cap \mathcal{M}_B| = 2$.
- Giữa An và Chi: Chung Phim 1 $\implies |\mathcal{M}_A \cap \mathcal{M}_C| = 1$.

**Bước 2: Tính độ tương đồng Salton Cosine:**
- Độ tương đồng giữa An và Bình:
  $$\text{sim}(A, B) = \frac{2}{\sqrt{|\mathcal{M}_A| \cdot |\mathcal{M}_B|}} = \frac{2}{\sqrt{2 \times 3}} = \frac{2}{\sqrt{6}} \approx \frac{2}{2.4495} \approx 0.8165$$
- Độ tương đồng giữa An và Chi:
  $$\text{sim}(A, C) = \frac{1}{\sqrt{|\mathcal{M}_A| \cdot |\mathcal{M}_C|}} = \frac{1}{\sqrt{2 \times 3}} = \frac{1}{\sqrt{6}} \approx \frac{1}{2.4495} \approx 0.4082$$

**Bước 3: Tính trọng số đánh giá của ứng viên từ láng giềng:**
- Bình đánh giá Phim 4 ($r = 5.0$): $w(r_{B, 4}) = \frac{5.0 - 3.0}{2.0} = 1.0$.
- Chi đánh giá Phim 4 ($r = 4.0$): $w(r_{C, 4}) = \frac{4.0 - 3.0}{2.0} = 0.50$.
- Chi đánh giá Phim 5 ($r = 4.5$): $w(r_{C, 5}) = \frac{4.5 - 3.0}{2.0} = 0.75$.
- Bình không đánh giá Phim 5.

**Bước 4: Tính điểm P3 thô ($\text{Raw\_P3}$):**
- **Phim 4** (được cả Bình và Chi cùng đề xuất):
  $$\text{contrib}(B \to 4) = \text{sim}(A, B) \cdot w(r_{B, 4}) = 0.8165 \times 1.0 = 0.8165$$
  $$\text{contrib}(C \to 4) = \text{sim}(A, C) \cdot w(r_{C, 4}) = 0.4082 \times 0.50 = 0.2041$$
  $$\text{Raw\_P3}(4) = 0.8165 + 0.2041 = 1.0206$$
- **Phim 5** (chỉ được Chi đề xuất):
  $$\text{contrib}(C \to 5) = \text{sim}(A, C) \cdot w(r_{C, 5}) = 0.4082 \times 0.75 = 0.3062$$
  $$\text{Raw\_P3}(5) = 0.3062$$

**Bước 5: Chuẩn hóa Min-Max:**
- Tập điểm thô: $\{1.0206, 0.3062\}$.
- Khoảng biến thiên: $\max - \min = 1.0206 - 0.3062 = 0.7144$.
- $\text{Norm\_P3}(4) = \frac{1.0206 - 0.3062}{0.7144} = 1.0$.
- $\text{Norm\_P3}(5) = \frac{0.3062 - 0.3062}{0.7144} = 0.0$.

**Bước 6: Xếp hạng ứng viên:**
1. **Hạng 1:** Phim 4 (Điểm chuẩn hóa = 1.0).
2. **Hạng 2:** Phim 5 (Điểm chuẩn hóa = 0.0).

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.3.3. Đường đi P3: Gợi ý theo quan hệ sở thích cộng đồng

Bên cạnh việc khai thác các thuộc tính nội dung của tác phẩm, MoodGraph tích hợp đường đi siêu liên kết cộng tác nhằm nắm bắt mối tương quan sở thích giữa các cá nhân trong cộng đồng người dùng. Khác với mô hình nhân tố ẩn phân tích ma trận vốn đòi hỏi quá trình huấn luyện ngoại tuyến phức tạp, đường đi cộng tác được hình thành trực tiếp từ cấu trúc tô pô của đồ thị theo chuỗi liên kết: người dùng mục tiêu kết nối tới các bộ phim từng yêu thích, đi ngược về những người dùng khác cũng có đánh giá tích cực trên các tác phẩm này, và tiếp tục lan truyền tới các tác phẩm tiềm năng được những người dùng đồng điệu đó đánh giá cao.

Độ tương đồng hành vi giữa người dùng mục tiêu u và người dùng láng giềng v được định lượng thông qua hệ số tương đồng Cosine Salton trên tập hợp các bộ phim được hai bên đánh giá tích cực:

$$\text{sim}(u, v) = \frac{|\mathcal{M}_u \cap \mathcal{M}_v|}{\sqrt{|\mathcal{M}_u| \cdot |\mathcal{M}_v|}}$$

Trong công thức trên, tử số biểu diễn số lượng tác phẩm chung mà cả hai người dùng đều đánh giá từ 3,5 sao trở lên; mẫu số là căn bậc hai tích số lượng phim yêu thích của từng cá nhân. Dựa trên độ tương đồng này, hệ thống lọc ra tối đa năm mươi láng giềng có chỉ số cao nhất để hình thành tập cộng đồng tham chiếu. Điểm số cộng tác thô của một tác phẩm ứng viên c sau đó được tổng hợp bằng cách tích lũy đóng góp từ tất cả các láng giềng từng yêu thích tác phẩm đó:

$$\text{Score}_{P_3}^{\text{raw}}(u, c) = \sum_{v \in \mathcal{N}_u \cap \mathcal{U}_c^{\text{liked}}} \text{sim}(u, v) \cdot w(r_{v, c})$$

Trong đó, w(r_{v,c}) biểu thị trọng số sở thích rút ra từ điểm đánh giá của láng giềng v trên tác phẩm c. Cơ chế cộng dồn này bảo đảm rằng một tác phẩm càng được nhiều người dùng có gu thưởng thức gần gũi với người dùng mục tiêu đánh giá cao thì càng nhận được điểm ưu tiên vượt trội. Điểm số thô cuối cùng được chuẩn hóa theo thang đo cực trị về đoạn từ 0 đến 1 trước khi kết hợp vào điểm số đồ thị tri thức tổng hợp.

---

## PHẦN E — PHẢN BIỆN HỌC THUẬT (5 CÂU HỎI HỘI ĐỒNG)

### Câu 1: Đường đi P3 khác gì so với mô hình lọc cộng tác Collaborative Filtering truyền thống hay mô hình Spark ALS?
- **Trả lời:** Spark ALS là mô hình phân rã ma trận (Matrix Factorization) tối ưu hóa hàm mất mát lỗi bình phương tối thiểu trên không gian vector ẩn (Latent Factors) toàn cục. Ngược lại, P3 là cơ chế duyệt đồ thị cục bộ (Local Graph Traversal) qua đường đi siêu liên kết trên đồ thị tri thức nhúng. P3 hoạt động hoàn toàn dựa trên cấu trúc liên kết và chỉ mục đảo hai chiều, cho phép truy vết và trích xuất bằng chứng suy luận giải thích trực quan (ví dụ: "Được đề xuất vì Người dùng B có gu tương đồng 81.6% cũng thích phim này") — điều mà các mô hình hộp đen như ALS không thể cung cấp.
- **Bằng chứng:** [scorer.py:9-10](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L9-L10), [scorer.py:400-417](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L400-L417).

### Câu 2: Tại sao công thức tương đồng Salton Cosine không trừ điểm trung bình (Mean-centering) như Pearson Correlation Coefficient?
- **Trả lời:** Trên tập dữ liệu tương tác thưa thớt, việc trừ điểm trung bình đòi hỏi phải truy xuất và lưu trữ toàn bộ phân phối điểm số của hàng ngàn người dùng, gây tốn kém bộ nhớ RAM và làm tăng thời gian tính toán lên nhiều lần. Bằng cách áp dụng bộ lọc ngưỡng cứng $r \ge 3.5$, hệ thống đã biến đổi không gian tương tác thành tập hợp các sở thích tích cực (Implicit Positive Feedback). Trên không gian tập hợp này, hệ số Cosine Salton (Ochiai Coefficient) đem lại hiệu năng tính toán tức thời qua phép đếm giao tập và bảo đảm độ ổn định toán học cao hơn so với Pearson khi số lượng phim chung nhỏ ($1 - 2$ phim).
- **Bằng chứng:** [scorer.py:164](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L164), [scorer.py:184](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L184).

### Câu 3: Mẫu số tính độ tương đồng có nguy cơ bị chia cho 0 không?
- **Trả lời:** **KHÔNG.** Điều kiện tiên quyết để xét láng giềng là $u$ và $v$ phải có ít nhất một phim chung $m$ được đánh giá $\ge 3.5$. Điều này bảo đảm $|\mathcal{M}_u| \ge 1$ và $|\mathcal{M}_v| \ge 1$. Hơn nữa, mã nguồn có lệnh kiểm tra phòng thủ tường minh `if n_liked_count == 0: continue` (dòng 182), loại trừ hoàn toàn nguy cơ mẫu số bằng 0.
- **Bằng chứng:** [scorer.py:182-184](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L182-L184).

### Câu 4: Trên đồ thị thực tế hàng chục ngàn người dùng, làm sao P3 tránh được hiện tượng bùng nổ tổ hợp láng giềng?
- **Trả lời:** Hệ thống áp dụng chiến lược cắt tỉa nhánh 3 lớp (3-tier pruning):
  1. Hạt giống mỏ neo: Chỉ lấy tối đa 20 phim thích nhất (`active_liked`) của người dùng.
  2. Giới hạn đỉnh mỏ neo: Với mỗi phim mỏ neo, chỉ quét tối đa 80 người dùng (`count >= 80: break`) để ngăn các phim bom tấn kéo theo hàng ngàn láng giềng.
  3. Lọc láng giềng yếu: Nếu danh sách láng giềng vượt quá 30 người, hệ thống tự động loại bỏ các láng giềng chỉ chung 1 phim (`len(shared_mids) < 2`), chỉ giữ lại các láng giềng chia sẻ từ 2 phim chung trở lên, sau đó lấy Top-50 láng giềng có độ tương đồng cao nhất.
- **Bằng chứng:** [scorer.py:143-152](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L143-L152), [scorer.py:167-175](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L167-L175).

### Câu 5: P3 đóng vai trò gì trong việc tạo Candidate Pool chung cho toàn bộ Knowledge Graph?
- **Trả lời:** Cùng với P2, P3 là nguồn sinh ứng viên sơ khởi chủ đạo (`all_candidate_ids.add(cand_mid)`). Các bộ phim được các láng giềng có gu tương đồng đánh giá cao sẽ được đưa vào tập ứng viên tiềm năng, tạo tiền đề để P1 (Genre) và P2 (Genome) chấm điểm và hợp nhất bằng chứng đa chiều.
- **Bằng chứng:** [scorer.py:196](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L196), [scorer.py:248](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L248).

---

## PHẦN F — KIỂM TRA SAI LỆCH VÀ BẢO ĐẢM HỌC THUẬT

1. **Phân biệt P3 với ALS:**
   - Đã xác minh: P3 là Collaborative Metapath trên đồ thị in-memory, không phải mô hình phân rã ma trận Matrix Factorization hay Spark ALS.
2. **Xử lý rating thấp:**
   - Đã xác minh: Rating $\le 3.0$ bị triệt tiêu trọng số $w(r) = 0$ và bị loại khỏi tập phim mỏ neo cũng như tập đề cử ứng viên.
3. **Mẫu số độ tương đồng:**
   - Đã xác minh: Sử dụng căn bậc hai tích số lượng phim thích của hai người dùng $\sqrt{|\mathcal{M}_u| \cdot |\mathcal{M}_v|}$, khớp chính xác định nghĩa Cosine Salton.
4. **Phân biệt Raw Score và Normalized Score:**
   - Đã xác minh: Điểm thô $\text{Raw\_P3}$ được tính từ tổng tích $\text{sim} \cdot w$, sau đó được chuẩn hóa Min-Max về đoạn $[0.0, 1.0]$ trước khi nhân hệ số trọng số $\gamma = 0.20$.
5. **Không nhầm lẫn với xác suất:**
   - Điểm số P3 là điểm tích lũy bằng chứng đồ thị (Path Evidence Score), tuyệt đối không phải là xác suất thống kê người dùng thích phim.
