# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.3.2

> **Chuyên đề:** 3.3.2. Đường đi P2: Gợi ý theo ngữ nghĩa Tag Genome (Genome Tag Metapath)  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Tệp kiểm toán cốt lõi:** `recommender/kg/scorer.py`, `recommender/kg/embedded_graph.py`, `recommender/kg/data_access.py`  
> **Trạng thái:** ĐÃ KIỂM ĐỊNH MÃ NGUỒN VÀ ĐỐI CHIẾU THỰC NGHIỆM 100%

---

## PHẦN A — BẢNG KIỂM TOÁN KỸ THUẬT

| Thành phần thuật toán | Công thức / Quy tắc thực tế | Ý nghĩa kỹ thuật | Bằng chứng file:line |
|---|---|---|---|
| **Cấu trúc Metapath** | $u \xrightarrow{\text{RATED}} m \xrightarrow{\text{HAS\_TAG}} t \xleftarrow{\text{HAS\_TAG}} c$ | Đường đi 3 chặng nối từ người dùng qua phim đã thích, thẻ tâm trạng Genome chung đến phim ứng viên. | [scorer.py:7-8](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L7-L8)<br>[scorer.py:201-235](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L201-L235) |
| **Lọc mỏ neo tích cực** | $r_{u,m} \ge 3.5 \land w(r_{u,m}) > 0$ | Chỉ các bộ phim có rating >= 3.5 trong tập Train mới được chọn làm đỉnh mỏ neo phát tán sở thích. | [scorer.py:126-129](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L126-L129)<br>[kg_config.yaml:12](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L12) |
| **Hàm trọng số sở thích** | $w(r) = \max\left(0, \frac{r - 3.0}{2.0}\right)$ | Tuyến tính hóa rating [3.5, 5.0] thành trọng số [0.25, 1.0]; gán trọng số 0 cho rating <= 3.0. | [scorer.py:85-87](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L85-L87) |
| **Tích số Relevance hai đầu** | $\text{rel}(m, t) \cdot \text{rel}(c, t)$ | Phản ánh mức độ cộng hưởng ngữ nghĩa vi mô: Hai phim càng cùng biểu đạt mạnh mẽ một thẻ thì liên kết càng mạnh. | [scorer.py:218](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L218)<br>[scorer.py:233](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L233)<br>[scorer.py:385](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L385) |
| **Bậc đỉnh của thẻ** | $\text{deg}(t) = |\text{genome\_tag\_to\_movies}[t]|$ | Tổng số phim trong đồ thị chứa thẻ $t$ trong **Top-M = 20** thẻ tiêu biểu nhất của phim đó. | [scorer.py:212](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L212)<br>[scorer.py:226](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L226)<br>[data_access.py:67-118](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/data_access.py#L67-L118) |
| **Phạt độ bão hòa Logarit** | $\text{norm\_factor} = \frac{1}{\ln(1 + \text{deg}(t))}$ | Sử dụng `math.log1p(deg_t)` (cơ số $e$) để phạt các thẻ xuất hiện quá phổ biến; bảo đảm mẫu số luôn $> 0$. | [scorer.py:215](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L215)<br>[scorer.py:229](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L229)<br>[scorer.py:385](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L385) |
| **Chọn lọc Top-15 thẻ tích cực** | `active_tags = sorted(tag_weights)[:15]` | Trên đồ thị lớn, chỉ lan truyền qua 15 thẻ có trọng số tích lũy cao nhất của người dùng nhằm tối ưu latency < 15ms. | [scorer.py:209](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L209) |
| **Khởi tạo Candidate Pool** | `all_candidate_ids.add(cand_mid)` | P2 trực tiếp kích hoạt và đưa các bộ phim liên quan ngữ nghĩa vào tập ứng viên chung cho toàn hệ thống. | [scorer.py:219](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L219)<br>[scorer.py:234](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L234) |
| **Lọc phim đã tương tác** | $c \notin \text{total\_exclude}$ | Loại bỏ 100% các bộ phim người dùng đã xem trong lịch sử Train hoặc tập split. | [scorer.py:217](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L217)<br>[scorer.py:232](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L232) |
| **Chuẩn hóa Min-Max** | $\text{Norm\_P2}(c) = \frac{\text{Raw} - \min}{\max - \min}$ | Chuẩn hóa điểm P2 thô về thang đo [0.0, 1.0] trước khi nhân trọng số $\beta = 0.45$. | [scorer.py:282](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L282)<br>[scorer.py:325-333](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L325-L333) |

---

## PHẦN B — CÔNG THỨC TOÁN HỌC CHUẨN

Đường đi siêu liên kết ngữ nghĩa Tag Genome $P_2$ được định nghĩa theo chuỗi quan hệ:
$$\mathcal{P}_2: \text{User} \xrightarrow{\text{RATED}} \text{Movie} \xrightarrow{\text{HAS\_GENOME\_TAG}} \text{GenomeTag} \xleftarrow{\text{HAS\_GENOME\_TAG}} \text{Movie}$$

### 1. Trọng số sở thích và tích lũy thẻ người dùng
Gọi $\mathcal{M}_u^{\text{liked}} = \{m \in \mathcal{M}_u^{\text{seen}} \mid r_{u,m} \ge 3.5\}$ là tập các phim mỏ neo tích cực của người dùng $u$. Trọng số đánh giá tích cực là:
$$w(r_{u,m}) = \max\left(0, \frac{r_{u,m} - 3.0}{2.0}\right)$$

Trọng số tích lũy của thẻ Genome $t$ đối với người dùng $u$ được tính bằng tổng tích số giữa độ ưa thích của người dùng và mức độ liên quan của thẻ trên các phim mỏ neo:
$$\mathcal{W}_u(t) = \sum_{m \in \mathcal{M}_u^{\text{liked}} \cap \mathcal{M}(t)} w(r_{u,m}) \cdot \text{rel}(m, t)$$
Trong đó $\text{rel}(m, t) \in [0.0, 1.0]$ là điểm liên quan (relevance) của thẻ $t$ đối với phim $m$, và $\mathcal{M}(t)$ là tập hợp các bộ phim chứa thẻ $t$ trong Top-$M$ ($M = 20$).

Trên đồ thị quy mô lớn phục vụ trực tuyến, hệ thống chỉ kích hoạt tập con $\mathcal{T}_u^{\text{active}} \subseteq \mathcal{T}_u$ gồm 15 thẻ có $\mathcal{W}_u(t)$ lớn nhất để kiểm soát độ phức tạp tính toán.

### 2. Công thức điểm P2 thô (Raw Score)
Với mỗi tác phẩm ứng viên $c \notin \mathcal{M}_u^{\text{seen}}$, điểm số ngữ nghĩa thô $\text{Score}_{P_2}^{\text{raw}}(u, c)$ được tính bằng tổng đóng góp của tất cả các thẻ $t$ đồng xuất hiện giữa ứng viên $c$ và lịch sử mỏ neo của người dùng:
$$\text{Score}_{P_2}^{\text{raw}}(u, c) = \sum_{t \in \mathcal{T}(c) \cap \mathcal{T}(\mathcal{M}_u^{\text{liked}})} \frac{\sum_{m \in \mathcal{M}_u^{\text{liked}} \cap \mathcal{M}(t)} w(r_{u,m}) \cdot \text{rel}(m, t) \cdot \text{rel}(c, t)}{\ln(1 + \text{deg}(t))}$$
Hoặc biểu diễn tương đương qua trọng số tích lũy:
$$\text{Score}_{P_2}^{\text{raw}}(u, c) = \sum_{t \in \mathcal{T}(c) \cap \mathcal{T}_u} \frac{\mathcal{W}_u(t) \cdot \text{rel}(c, t)}{\ln(1 + \text{deg}(t))}$$

**Giải nghĩa các ký hiệu:**
- $\mathcal{T}(c)$: Tập hợp các thẻ Genome thuộc Top-20 của phim ứng viên $c$.
- $\text{rel}(m, t), \text{rel}(c, t) \in (0, 1]$: Điểm mức độ phù hợp liên tục của thẻ $t$ trên phim mỏ neo $m$ và phim ứng viên $c$.
- $\text{deg}(t) = |\mathcal{M}(t)|$: Bậc đỉnh của thẻ $t$ trên đồ thị tri thức nhúng (tổng số phim nhận thẻ $t$ trong Top-20 thẻ tiêu biểu).
- $\ln(1 + \text{deg}(t))$: Hàm phạt độ bão hòa dựa trên logarit tự nhiên (`math.log1p`), làm suy giảm sức nặng của các thẻ quá phổ biến mang ít giá trị phân biệt.
- Miền giá trị: $\text{Score}_{P_2}^{\text{raw}}(u, c) \ge 0.0$ (chưa bị chặn trên).

### 3. Chuẩn hóa Min-Max (Normalized Score)
Để phối hợp đồng bộ với $P_1$ và $P_3$, điểm số thô được đưa về đoạn $[0.0, 1.0]$ trên tập ứng viên $\mathcal{C}$:
$$\text{Score}_{P_2}^{\text{norm}}(u, c) = \begin{cases} 
\frac{\text{Score}_{P_2}^{\text{raw}}(u, c) - \min_{x \in \mathcal{C}} \text{Score}_{P_2}^{\text{raw}}(u, x)}{\max_{x \in \mathcal{C}} \text{Score}_{P_2}^{\text{raw}}(u, x) - \min_{x \in \mathcal{C}} \text{Score}_{P_2}^{\text{raw}}(u, x)}, & \text{nếu } \max - \min \ge 10^{-9} \\
1.0, & \text{nếu } \max = \min > 0 \\
0.0, & \text{ngược lại}
\end{cases}$$
Điểm chuẩn hóa $\text{Score}_{P_2}^{\text{norm}}(u, c)$ đóng góp với hệ số trọng số $\beta = 0.45$ vào điểm số đồ thị tri thức tổng hợp.

---

## PHẦN C — VÍ DỤ TÍNH TAY MINH HỌA

### 1. Dữ liệu giả định
- **Người dùng:** $U_1$.
- **2 phim đã đánh giá trong tập Train:**
  * Phim 1: $r = 5.0 \implies w(5.0) = \frac{5.0 - 3.0}{2.0} = 1.0$.  
    Top Genome Tags: Tag 10 (`pixar`, $\text{rel} = 0.90$), Tag 20 (`family`, $\text{rel} = 0.80$).
  * Phim 2: $r = 4.0 \implies w(4.0) = \frac{4.0 - 3.0}{2.0} = 0.50$.  
    Top Genome Tags: Tag 10 (`pixar`, $\text{rel} = 0.80$), Tag 30 (`space`, $\text{rel} = 0.60$).
- **3 phim ứng viên (chưa xem):**
  * Phim 3: Tag 10 ($\text{rel} = 0.85$), Tag 20 ($\text{rel} = 0.70$).
  * Phim 4: Tag 10 ($\text{rel} = 0.90$).
  * Phim 5: Tag 40 (`action`, $\text{rel} = 0.95$, không trùng thẻ nào trong lịch sử).
- **Thống kê bậc đỉnh $\text{deg}(t)$ trên đồ thị (số phim có thẻ trong Top-20):**
  * Tag 10 (`pixar`): xuất hiện ở Phim 1, 2, 3, 4 $\implies \text{deg}(10) = 4$.
  * Tag 20 (`family`): xuất hiện ở Phim 1, 3 $\implies \text{deg}(20) = 2$.
  * Tag 30 (`space`): xuất hiện ở Phim 2 $\implies \text{deg}(30) = 1$.
  * Tag 40 (`action`): xuất hiện ở Phim 5 $\implies \text{deg}(40) = 1$.

### 2. Các bước tính toán chi tiết

**Bước 1: Tính mẫu số suy giảm logarit $\ln(1 + \text{deg}(t))$:**
- Tag 10: $\ln(1 + 4) = \ln(5) \approx 1.6094$.
- Tag 20: $\ln(1 + 2) = \ln(3) \approx 1.0986$.
- Tag 30: $\ln(1 + 1) = \ln(2) \approx 0.6931$.

**Bước 2: Tích lũy trọng số thẻ người dùng $\mathcal{W}_{U_1}(t)$:**
- Tag 10: $w(r_1) \cdot \text{rel}(1, 10) + w(r_2) \cdot \text{rel}(2, 10) = 1.0 \times 0.90 + 0.50 \times 0.80 = 0.90 + 0.40 = 1.30$.
- Tag 20: $w(r_1) \cdot \text{rel}(1, 20) = 1.0 \times 0.80 = 0.80$.
- Tag 30: $w(r_2) \cdot \text{rel}(2, 30) = 0.50 \times 0.60 = 0.30$.

**Bước 3: Tính điểm P2 thô ($\text{Raw\_P2}$):**
- **Phim 3:**
  * Đóng góp từ Tag 10: $\frac{1.30}{\ln(5)} \times \text{rel}(3, 10) = \frac{1.30}{1.6094} \times 0.85 \approx 0.80775 \times 0.85 \approx 0.6866$.
  * Đóng góp từ Tag 20: $\frac{0.80}{\ln(3)} \times \text{rel}(3, 20) = \frac{0.80}{1.0986} \times 0.70 \approx 0.72820 \times 0.70 \approx 0.5097$.
  * Tổng điểm: $\text{Raw\_P2}(3) = 0.6866 + 0.5097 = 1.1963$.
- **Phim 4:**
  * Đóng góp từ Tag 10: $\frac{1.30}{\ln(5)} \times \text{rel}(4, 10) = \frac{1.30}{1.6094} \times 0.90 \approx 0.80775 \times 0.90 \approx 0.7270$.
  * Tổng điểm: $\text{Raw\_P2}(4) = 0.7270$.
- **Phim 5:**
  * Không giao thoa thẻ nào với lịch sử $\implies \text{Raw\_P2}(5) = 0.0$.

**Bước 4: Chuẩn hóa Min-Max:**
- Tập điểm thô: $\{1.1963, 0.7270, 0.0\}$.
- Khoảng biến thiên: $\max - \min = 1.1963 - 0.0 = 1.1963$.
- $\text{Norm\_P2}(3) = \frac{1.1963 - 0.0}{1.1963} = 1.0$.
- $\text{Norm\_P2}(4) = \frac{0.7270 - 0.0}{1.1963} \approx 0.6077$.
- $\text{Norm\_P2}(5) = \frac{0.0 - 0.0}{1.1963} = 0.0$.

**Bước 5: Xếp hạng ứng viên:**
1. **Hạng 1:** Phim 3 (Điểm chuẩn hóa = 1.0).
2. **Hạng 2:** Phim 4 (Điểm chuẩn hóa = 0.6077).
3. **Hạng 3:** Phim 5 (Điểm chuẩn hóa = 0.0).

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.3.2. Đường đi P2: Gợi ý theo ngữ nghĩa Tag Genome

Khác với đường đi thể loại vốn chỉ nắm bắt các phân lớp điện ảnh ở cấp độ vĩ mô, đường đi siêu liên kết Tag Genome được thiết kế nhằm khai thác các đặc trưng ngữ nghĩa và trạng thái cảm xúc ở cấp độ vi mô thông qua không gian 1.128 chiều thuộc tính được lượng hóa liên tục. Chuỗi liên kết được hình thành từ người dùng qua các bộ phim đã đánh giá tích cực trong quá khứ, tiếp cận các thẻ tâm trạng đặc trưng chung, và lan truyền tới các tác phẩm ứng viên tiềm năng chưa được người dùng trải nghiệm. Thay vì sử dụng quan hệ nhị phân đơn thuần, mỗi liên kết giữa phim và thẻ mang một trọng số thực phản ánh mức độ biểu đạt của thuộc tính đó trên tác phẩm.

Điểm số ngữ nghĩa thô của một tác phẩm ứng viên được xác định bằng tổng tích lũy của các đường đi giao thoa, trong đó mức độ đóng góp phụ thuộc đồng thời vào trọng số sở thích của người dùng, tích số mức độ liên quan ở hai đầu liên kết và hệ số suy giảm độ bão hòa của thẻ trung gian:

$$\text{Score}_{P_2}^{\text{raw}}(u, c) = \sum_{t \in \mathcal{T}(c) \cap \mathcal{T}(\mathcal{M}_u^{\text{liked}})} \frac{\sum_{m \in \mathcal{M}_u^{\text{liked}} \cap \mathcal{M}(t)} w(r_{u,m}) \cdot \text{rel}(m, t) \cdot \text{rel}(c, t)}{\ln(1 + \text{deg}(t))}$$

Trong công thức trên, các đại lượng được định nghĩa cụ thể như sau: $w(r_{u,m})$ là trọng số sở thích rút ra từ điểm đánh giá tích cực của người dùng trên phim mỏ neo; $\text{rel}(m, t)$ và $\text{rel}(c, t)$ lần lượt là điểm tương quan của thẻ ngữ nghĩa $t$ đối với phim mỏ neo $m$ và phim ứng viên $c$; $\mathcal{T}(\cdot)$ biểu diễn tập hợp hai mươi thẻ có độ liên quan cao nhất của từng bộ phim; và $\text{deg}(t)$ là bậc đỉnh của thẻ trên đồ thị, tương ứng với số lượng tác phẩm tiếp nhận thẻ này trong nhóm đặc trưng tiêu biểu.

Việc tích hợp đại lượng tích số tương quan bảo đảm rằng chỉ những tác phẩm cùng chia sẻ mạnh mẽ một sắc thái tâm trạng cụ thể mới nhận được điểm ưu tiên cao. Đồng thời, mẫu số suy giảm logarit tự nhiên đóng vai trò tương tự như hệ số nghịch đảo tần suất tài liệu trong xử lý ngôn ngữ tự nhiên, giúp kiềm chế ảnh hưởng của các thuộc tính phổ quát và khuếch đại sức nặng của các vi đặc trưng giàu tính phân tách. Toàn bộ điểm số thô sau đó được chuẩn hóa theo thang đo cực trị về đoạn từ 0 đến 1 trước khi đưa vào bước tổng hợp điểm suy luận của hệ thống.

---

## PHẦN E — PHẢN BIỆN HỌC THUẬT (5 CÂU HỎI HỘI ĐỒNG)

### Câu 1: Tại sao công thức P2 lại sử dụng logarithm tự nhiên $\ln(1 + \text{deg}(t))$ mà P1 lại dùng căn bậc hai $\sqrt{\text{deg}(g)}$?
- **Trả lời:** Thể loại (Genre) chỉ có 19 lớp, phân phối bậc tương đối đồng đều (thấp nhất vài trăm phim, cao nhất khoảng 25,000 phim), do đó căn bậc hai $\sqrt{\text{deg}(g)}$ là đủ để điều tiết độ phạt tuyến tính. Ngược lại, Tag Genome có tới 1,128 chiều với phân phối đuôi dài cực kỳ dốc (power-law distribution): một số thẻ xuất hiện ở hàng ngàn phim trong khi các thẻ ngách chỉ có ở vài chục phim. Việc áp dụng logarit tự nhiên $\ln(1 + \text{deg}(t))$ (tương tự độ đo IDF) giúp nén thang đo phân kỳ mạnh này, tránh việc phạt quá mức khiến các thẻ phổ biến bị triệt tiêu hoàn toàn.
- **Bằng chứng:** [scorer.py:8](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L8), [scorer.py:215](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L215).

### Câu 2: Relevance có phải là xác suất người dùng sẽ thích bộ phim đó không?
- **Trả lời:** **KHÔNG.** Relevance là điểm số ước lượng mức độ phù hợp về mặt nội dung giữa một từ khóa tâm trạng và một bộ phim do mô hình học máy của Tag Genome (GroupLens) trích xuất từ dữ liệu gắn thẻ cộng đồng. Nó là thuộc tính nội dung khách quan (content property) chứ không phải xác suất hành vi (probability of liking) của người dùng cá nhân. Điểm P2 là điểm tích lũy bằng chứng đồ thị (path evidence accumulation), không phải xác suất.
- **Bằng chứng:** [preprocess.py:139-144](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/preprocess.py#L139-L144), [data_dictionary.md](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/data_dictionary.md).

### Câu 3: Bậc $\text{deg}(t)$ được đếm trên 15.58 triệu bản ghi thô ban đầu hay đếm sau khi lọc Top-M = 20?
- **Trả lời:** Bậc $\text{deg}(t)$ được đếm **sau khi đã lọc Top-M = 20** cho từng phim. Cụ thể, trong `data_access.py`, chỉ các cặp $(m, t)$ nằm trong Top-20 relevance của phim mới được lưu vào `self.genome_tag_to_movies[t]`. Vì vậy $\text{deg}(t) = \text{len}(\text{genome\_tag\_to\_movies}[t])$ phản ánh số lượng phim mà thẻ $t$ thực sự là đặc trưng tiêu biểu nhất.
- **Bằng chứng:** [data_access.py:67-118](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/data_access.py#L67-L118), [embedded_graph.py:118](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L118).

### Câu 4: Trong MovieLens 25M có 48,607 phim không có Genome Scores, P2 xử lý các phim này như thế nào?
- **Trả lời:** Các bộ phim không có Genome Scores sẽ có $\mathcal{T}(c) = \emptyset$. Do đó, vòng lặp tính điểm P2 sẽ bỏ qua các phim này, điểm $\text{Raw\_P2}(c) = 0.0$. Các phim này sẽ được bù đắp điểm số thông qua đường đi thể loại P1 và đường đi cộng tác láng giềng P3.
- **Bằng chứng:** [test_results.json:43](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/data/processed/test_results.json#L43), [scorer.py:201-220](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L201-L220).

### Câu 5: Trên đồ thị thực tế, tại sao hệ thống chỉ lấy Top 15 thẻ (`active_tags[:15]`) trong nhánh `is_large_graph`?
- **Trả lời:** Một người dùng có thể thích 20 phim mỏ neo, mỗi phim có 20 thẻ, tạo ra tối đa $20 \times 20 = 400$ thẻ. Nếu lan truyền qua cả 400 thẻ này tới hàng ngàn phim ứng viên, thời gian truy vấn đồ thị sẽ vượt quá 100ms. Việc chọn 15 thẻ có trọng số tích lũy $\mathcal{W}_u(t)$ cao nhất nắm giữ hơn 85% năng lượng ngữ nghĩa của người dùng, giúp thời gian suy luận hoàn thành dưới 15ms mà không làm suy giảm độ chính xác Top-K.
- **Bằng chứng:** [scorer.py:209-210](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L209-L210).

---

## PHẦN F — KIỂM TRA SAI LỆCH VÀ BẢO ĐẢM HỌC THUẬT

1. **Phân biệt User Tags và Genome Tags:**
   - Đồ thị tri thức MoodGraph **hoàn toàn không dùng** các thẻ tự do trong `tags.csv` (User Tags) để tính P2. P2 được tính độc quyền từ 1,128 thẻ chuẩn hóa trong `genome-tags.csv` và điểm số `genome-scores.csv`.
2. **Phân biệt Relevance và Rating:**
   - Rating là điểm đánh giá của người dùng ($r \in [0.5, 5.0]$) trên quan hệ `RATED`. Relevance là thuộc tính liên tục ($\text{rel} \in [0.0, 1.0]$) trên quan hệ `HAS_GENOME_TAG`. Công thức P2 kết hợp cả hai yếu tố này qua phép nhân $w(r) \cdot \text{rel}(m, t) \cdot \text{rel}(c, t)$.
3. **Mẫu số suy giảm:**
   - Đã xác nhận chính xác mã nguồn sử dụng logarit tự nhiên `math.log1p(deg_t)` tức $\ln(1 + \text{deg}(t))$, tuyệt đối không phải $\sqrt{\text{deg}(t)}$ như P1.
4. **Phân biệt Raw Score và Normalized Score:**
   - Điểm thô $\text{Raw\_P2}$ được tính từ tổng đường đi. Sau đó hàm `_normalize_scores` áp dụng Min-Max đưa về $[0.0, 1.0]$. Trọng số $\beta = 0.45$ chỉ được nhân vào điểm sau khi đã chuẩn hóa Min-Max.
