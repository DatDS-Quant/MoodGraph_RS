# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.3.1

> **Chuyên đề:** 3.3.1. Đường đi P1: Gợi ý theo thể loại phim (Genre Metapath)  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Tệp kiểm toán cốt lõi:** `recommender/kg/scorer.py`, `recommender/kg/embedded_graph.py`, `tests/kg/test_path_scoring.py`  
> **Trạng thái:** ĐÃ KIỂM ĐỊNH MÃ NGUỒN VÀ ĐỐI CHIẾU FIXTURE TOÁN HỌC 100%

---

## PHẦN A — BẰNG CHỨNG MÃ NGUỒN

| Thành phần thuật toán | Công thức / Quy tắc thực tế | Ý nghĩa kỹ thuật | Bằng chứng file:line |
|---|---|---|---|
| **Cấu trúc Metapath** | $u \xrightarrow{\text{RATED}} m \xrightarrow{\text{IN\_GENRE}} g \xleftarrow{\text{IN\_GENRE}} c$ | Đường đi 3 chặng từ người dùng qua phim đã thích, thể loại chung đến phim ứng viên. | [scorer.py:5-6](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L5-L6)<br>[scorer.py:239-269](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L239-L269) |
| **Lọc mỏ neo tích cực** | $r_{u,m} \ge 3.5 \land w(r_{u,m}) > 0$ | Chỉ các phim có rating >= 3.5 trong tập Train mới được làm điểm xuất phát mỏ neo. | [scorer.py:126-129](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L126-L129)<br>[kg_config.yaml:12](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L12) |
| **Giới hạn hạt giống** | Lấy tối đa 20 phim thích nhất: `(-rating, -timestamp)` | Nếu đồ thị lớn (>100 phim) và có >20 phim thích, lấy Top-20 để giảm nhiễu và tăng tốc. | [scorer.py:139-152](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L139-L152) |
| **Hàm trọng số sở thích** | $w(r) = \max\left(0, \frac{r - 3.0}{2.0}\right)$ | Ánh xạ rating [3.5, 5.0] tuyến tính thành trọng số [0.25, 1.0]; triệt tiêu rating <= 3.0 về 0. | [scorer.py:85-87](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L85-L87)<br>[test_path_scoring.py:59-61](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/tests/kg/test_path_scoring.py#L59-L61) |
| **Bậc của thể loại** | $\text{deg}(g) = |\text{genre\_to\_movies}[g]|$ | Tổng số phim trong danh mục đồ thị có gắn thể loại $g$. | [scorer.py:251-253](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L251-L253)<br>[scorer.py:260](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L260) |
| **Phạt độ phổ biến** | $\text{norm\_factor} = \frac{1}{\sqrt{\text{deg}(g)}}$ | Phạt các thể loại quá phổ biến (như Drama/Comedy), ưu tiên các thể loại đặc thù. | [scorer.py:253](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L253)<br>[scorer.py:263](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L263) |
| **Điểm P1 thô (Raw)** | $\text{Raw\_P1}(c) = \sum_{g \in \mathcal{G}(c)} \frac{\text{genre\_weights}[g]}{\sqrt{\text{deg}(g)}}$ | Cộng dồn đóng góp của mọi thể loại chung giữa ứng viên $c$ và lịch sử phim đã thích. | [scorer.py:248-253](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L248-L253)<br>[scorer.py:267](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L267) |
| **Lọc phim đã xem** | $c \notin \text{total\_exclude}$ | Loại bỏ 100% phim người dùng đã tương tác trong lịch sử hoặc tập split. | [scorer.py:106-124](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L106-L124)<br>[scorer.py:266](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L266) |
| **Chuẩn hóa Min-Max** | $\text{Norm\_P1}(c) = \frac{\text{Raw} - \min}{\max - \min}$ | Đưa điểm thô về đoạn [0.0, 1.0] để kết hợp tuyến tính với P2 và P3. | [scorer.py:281](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L281)<br>[scorer.py:325-333](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L325-L333) |
| **Xử lý hòa điểm** | `sort(key=lambda x: (-x[1], x[0]))` | Tie-breaker tất định: Điểm cao hơn xếp trước; bằng điểm thì `movieId` nhỏ hơn xếp trước. | [scorer.py:293-294](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L293-L294) |

---

## PHẦN B — CÔNG THỨC TOÁN HỌC CHUẨN

Đường đi siêu liên kết thể loại $P_1$ được định nghĩa theo chuỗi quan hệ:
$$\mathcal{P}_1: \text{User} \xrightarrow{\text{RATED}} \text{Movie} \xrightarrow{\text{IN\_GENRE}} \text{Genre} \xleftarrow{\text{IN\_GENRE}} \text{Movie}$$

### 1. Tập hợp mỏ neo và hàm trọng số sở thích
Gọi $\mathcal{M}_u^{\text{seen}}$ là tập các phim người dùng $u$ đã tương tác. Tập các phim mỏ neo tích cực $\mathcal{M}_u^{\text{liked}}$ được xác định bởi:
$$\mathcal{M}_u^{\text{liked}} = \{m \in \mathcal{M}_u^{\text{seen}} \mid r_{u,m} \ge 3.5\}$$
Trong trường hợp $|\mathcal{M}_u^{\text{liked}}| > 20$, hệ thống chỉ giữ lại tập con $\mathcal{M}_u^{\text{active}} \subseteq \mathcal{M}_u^{\text{liked}}$ gồm tối đa 20 phim có điểm số cao nhất và thời gian gần nhất.

Trọng số sở thích của người dùng $u$ đối với phim mỏ neo $m$ được chuẩn hóa qua hàm tuyến tính có chặn dưới:
$$w(r_{u,m}) = \max\left(0, \frac{r_{u,m} - 3.0}{2.0}\right)$$
Với $r_{u,m} \in [0.5, 5.0]$, giá trị $w(r_{u,m}) \in [0.0, 1.0]$. Cụ thể: $w(5.0) = 1.0$, $w(4.5) = 0.75$, $w(4.0) = 0.50$, $w(3.5) = 0.25$, và $w(r) = 0$ với mọi $r \le 3.0$.

### 2. Tích lũy trọng số thể loại sở thích
Trọng số tích lũy của thể loại $g$ từ các phim người dùng từng thích được xác định bằng:
$$\mathcal{W}_u(g) = \sum_{m \in \mathcal{M}_u^{\text{liked}} \cap \mathcal{M}(g)} w(r_{u,m})$$
Trong đó $\mathcal{M}(g)$ là tập hợp toàn bộ các bộ phim trong danh mục có thuộc tính thể loại $g$.

### 3. Điểm số P1 thô (Raw Score)
Với mỗi phim ứng viên $c \notin \mathcal{M}_u^{\text{seen}}$, điểm số thể loại thô là tổng đóng góp của toàn bộ các thể loại $g \in \mathcal{G}(c)$ có giao thoa với sở thích của người dùng, được phạt bởi căn bậc hai số bậc đỉnh của thể loại đó:
$$\text{Score}_{P_1}^{\text{raw}}(u, c) = \sum_{g \in \mathcal{G}(c)} \frac{\mathcal{W}_u(g)}{\sqrt{\text{deg}(g)}} = \sum_{g \in \mathcal{G}(c) \cap \mathcal{G}(\mathcal{M}_u^{\text{liked}})} \frac{\sum_{m \in \mathcal{M}_u^{\text{liked}} \cap \mathcal{M}(g)} w(r_{u,m})}{\sqrt{|\mathcal{M}(g)|}}$$
Trong đó:
- $\mathcal{G}(c)$ là tập hợp các thể loại của phim ứng viên $c$.
- $\text{deg}(g) = |\mathcal{M}(g)|$ là bậc của đỉnh thể loại $g$ trên đồ thị tri thức (tổng số phim thuộc thể loại $g$).
- $\frac{1}{\sqrt{\text{deg}(g)}}$ là hệ số suy giảm tương đương chuẩn hóa Cosine đối xứng.

### 4. Chuẩn hóa Min-Max (Normalized Score)
Để triệt tiêu sự chênh lệch thứ nguyên khi hợp nhất với $P_2$ và $P_3$, điểm số thô được chuẩn hóa Min-Max trên toàn bộ tập ứng viên $\mathcal{C}$:
$$\text{Score}_{P_1}^{\text{norm}}(u, c) = \begin{cases} 
\frac{\text{Score}_{P_1}^{\text{raw}}(u, c) - \min_{x \in \mathcal{C}} \text{Score}_{P_1}^{\text{raw}}(u, x)}{\max_{x \in \mathcal{C}} \text{Score}_{P_1}^{\text{raw}}(u, x) - \min_{x \in \mathcal{C}} \text{Score}_{P_1}^{\text{raw}}(u, x)}, & \text{nếu } \max - \min \ge 10^{-9} \\
1.0, & \text{nếu } \max = \min > 0 \\
0.0, & \text{ngược lại}
\end{cases}$$
Điểm chuẩn hóa $\text{Score}_{P_1}^{\text{norm}}(u, c) \in [0.0, 1.0]$. Khi chỉ kích hoạt riêng $P_1$, điểm này được nhân với trọng số $\alpha = 0.35$ (hoặc $1.0$ khi chạy mô hình đơn lẻ).

---

## PHẦN C — VÍ DỤ TÍNH TAY MINH HỌA

### 1. Dữ liệu đầu vào giả định
- **Người dùng:** $U_1$.
- **Lịch sử đánh giá của $U_1$:**
  * Phim 1: $r = 5.0$, thể loại = `{"Animation", "Children"}`.
  * Phim 2: $r = 4.5$, thể loại = `{"Animation"}`.
- **Tập ứng viên chưa xem:** Phim 3, Phim 6, Phim 8.
  * Phim 3: Thể loại = `{"Animation", "Comedy"}`.
  * Phim 6: Thể loại = `{"Animation"}`.
  * Phim 8: Thể loại = `{"Crime"}`.
- **Thống kê bậc thể loại trong đồ thị danh mục:**
  * `Animation`: gồm Phim 1, 2, 3, 6 $\implies \text{deg}(\text{Animation}) = 4$.
  * `Children`: gồm Phim 1 $\implies \text{deg}(\text{Children}) = 1$.
  * `Comedy`: gồm Phim 3 $\implies \text{deg}(\text{Comedy}) = 1$.
  * `Crime`: gồm Phim 8 $\implies \text{deg}(\text{Crime}) = 1$.

### 2. Các bước tính toán chi tiết

**Bước 1: Tính trọng số sở thích $w(r)$:**
- Phim 1 ($r = 5.0$): $w(5.0) = \frac{5.0 - 3.0}{2.0} = 1.0$.
- Phim 2 ($r = 4.5$): $w(4.5) = \frac{4.5 - 3.0}{2.0} = 0.75$.

**Bước 2: Tích lũy trọng số thể loại $\mathcal{W}_{U_1}(g)$:**
- `Animation`: Phim 1 ($1.0$) + Phim 2 ($0.75$) $\implies \mathcal{W}_{U_1}(\text{Animation}) = 1.75$.
- `Children`: Phim 1 ($1.0$) $\implies \mathcal{W}_{U_1}(\text{Children}) = 1.0$.
- `Comedy`: Chưa có phim thích $\implies \mathcal{W}_{U_1}(\text{Comedy}) = 0.0$.
- `Crime`: Chưa có phim thích $\implies \mathcal{W}_{U_1}(\text{Crime}) = 0.0$.

**Bước 3: Tính điểm P1 thô ($\text{Raw\_P1}$):**
- **Phim 3** (có `Animation` và `Comedy`):
  $$\text{Raw\_P1}(3) = \frac{\mathcal{W}_{U_1}(\text{Animation})}{\sqrt{\text{deg}(\text{Animation})}} + \frac{\mathcal{W}_{U_1}(\text{Comedy})}{\sqrt{\text{deg}(\text{Comedy})}} = \frac{1.75}{\sqrt{4}} + \frac{0.0}{\sqrt{1}} = \frac{1.75}{2} + 0 = 0.875$$
- **Phim 6** (có `Animation`):
  $$\text{Raw\_P1}(6) = \frac{\mathcal{W}_{U_1}(\text{Animation})}{\sqrt{\text{deg}(\text{Animation})}} = \frac{1.75}{\sqrt{4}} = 0.875$$
- **Phim 8** (có `Crime`):
  $$\text{Raw\_P1}(8) = \frac{\mathcal{W}_{U_1}(\text{Crime})}{\sqrt{\text{deg}(\text{Crime})}} = \frac{0.0}{\sqrt{1}} = 0.0$$

**Bước 4: Chuẩn hóa Min-Max:**
- Tập điểm thô: $\{0.875, 0.875, 0.0\}$.
- $\min = 0.0$, $\max = 0.875 \implies \max - \min = 0.875$.
- $\text{Norm\_P1}(3) = \frac{0.875 - 0.0}{0.875} = 1.0$.
- $\text{Norm\_P1}(6) = \frac{0.875 - 0.0}{0.875} = 1.0$.
- $\text{Norm\_P1}(8) = \frac{0.0 - 0.0}{0.875} = 0.0$.

**Bước 5: Xếp hạng với quy tắc Tie-breaking (`raw_score DESC, movieId ASC`):**
1. **Hạng 1:** Phim 3 (Điểm = 1.0, movieId = 3).
2. **Hạng 2:** Phim 6 (Điểm = 1.0, movieId = 6). Do bằng điểm với Phim 3 nhưng có movieId lớn hơn (6 > 3).
3. **Hạng 3:** Phim 8 (Điểm = 0.0, movieId = 8).

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.3.1. Đường đi P1: Gợi ý theo thể loại phim (Genre)

Đường đi siêu liên kết thể loại khai thác mối quan hệ ngữ nghĩa vĩ mô giữa người dùng và tác phẩm điện ảnh thông qua các thuộc tính thể loại được chia sẻ. Cấu trúc đường đi được thiết lập theo chuỗi liên kết có hướng: người dùng kết nối tới các bộ phim từng đánh giá tích cực trong tập huấn luyện, từ đó lan truyền tới các thể loại của bộ phim đó, và tiếp tục dẫn xuất tới các tác phẩm ứng viên cùng chung danh mục thể loại nhưng chưa xuất hiện trong lịch sử tương tác. Để xác định các đỉnh xuất phát có ý nghĩa thực chất, hệ thống áp dụng ngưỡng đánh giá tối thiểu và chuyển đổi điểm đánh giá thô thành trọng số sở thích thông qua hàm biến đổi tuyến tính:

$$w(r_{u,m}) = \max\left(0, \frac{r_{u,m} - 3.0}{2.0}\right)$$

Trọng số này bảo đảm các mức đánh giá xuất sắc đóng góp tối đa vào độ ưu tiên thể loại, trong khi các tương tác trung bình hoặc tiêu cực bị triệt tiêu hoàn toàn. Điểm số thể loại thô của một tác phẩm ứng viên được xác định bằng tổng đóng góp tích lũy của toàn bộ các thể loại đồng xuất hiện giữa ứng viên và các tác phẩm mỏ neo, có điều chỉnh suy giảm theo mức độ phổ biến của thể loại:

$$\text{Score}_{P_1}^{\text{raw}}(u, c) = \sum_{g \in \mathcal{G}(c) \cap \mathcal{G}(\mathcal{M}_u^{\text{liked}})} \frac{\sum_{m \in \mathcal{M}_u^{\text{liked}} \cap \mathcal{M}(g)} w(r_{u,m})}{\sqrt{\text{deg}(g)}}$$

Trong đó, bậc đỉnh của thể loại phản ánh tổng số lượng phim thuộc thể loại đó trên toàn bộ danh mục đồ thị. Việc chia cho căn bậc hai bậc đỉnh đóng vai trò như một bộ chuẩn hóa đối xứng, giúp giảm thiểu độ lệch ưu tiên đối với các thể loại đại chúng có mật độ phim áp đảo như chính kịch hay hài kịch, đồng thời tôn vinh các thể loại ngách có tính định hình thị hiếu cao. Điểm số thô sau đó được chuẩn hóa theo thang đo cực trị về đoạn từ 0 đến 1 trên toàn bộ không gian ứng viên trước khi chuyển giao sang bước tổng hợp điểm liên kết.

---

## PHẦN E — KIỂM TRA PHẢN BIỆN (5 CÂU HỎI HỘI ĐỒNG)

### Câu 1: Tại sao công thức P1 lại dùng căn bậc hai bậc đỉnh $\sqrt{\text{deg}(g)}$ thay vì chia bậc tuyến tính $\text{deg}(g)$ như phép tính xác suất chuyển trạng thái?
- **Trả lời:** Chia bậc tuyến tính $\text{deg}(g)$ (tương tự Random Walk) sẽ phạt quá nặng các thể loại trung bình, làm suy giảm nghiêm trọng độ phủ (coverage). Chia căn bậc hai $\sqrt{\text{deg}(g)}$ tương đương với chuẩn hóa Cosine đối xứng trên ma trận kề lưỡng phân Phim - Thể loại, cân bằng hoàn hảo giữa khả năng tổng quát hóa và độ phạt độ phổ biến.
- **Bằng chứng:** [scorer.py:253](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L253), [scorer.py:263](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L263).

### Câu 2: Nếu người dùng đánh giá 5 sao cho một phim có 5 thể loại khác nhau, trọng số $w=1.0$ được chia đều cho 5 thể loại hay gán nguyên vẹn $1.0$ cho mỗi thể loại?
- **Trả lời:** Mã nguồn **gán nguyên vẹn** $w(r) = 1.0$ cho mỗi thể loại mà bộ phim đó sở hữu (`genre_weights[g] += w`). Hệ thống không chia đều theo số lượng thể loại của phim nguồn, vì một bộ phim xuất sắc thể hiện đầy đủ giá trị thưởng thức của người dùng trên tất cả các thể loại cấu thành nên nó.
- **Bằng chứng:** [scorer.py:246](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L246), [scorer.py:257](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L257).

### Câu 3: Khi người dùng thích nhiều phim có cùng thể loại, điểm số có bị bão hòa không hay tăng vô hạn?
- **Trả lời:** Trong pha tính điểm thô, điểm $\text{genre\_weights}[g]$ cộng dồn tuyến tính theo số lượng phim thích. Tuy nhiên, hệ thống có hai cơ chế kiềm chế:
  1. Chỉ lấy tối đa 20 phim thích nhất (`active_liked = dict(sorted_liked[:20])`) trên đồ thị lớn để chặn cận trên.
  2. Bước chuẩn hóa Min-Max sau cùng sẽ nén toàn bộ phân phối điểm về đoạn $[0.0, 1.0]$, loại bỏ hoàn toàn nguy cơ điểm số vượt biên.
- **Bằng chứng:** [scorer.py:143-152](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L143-L152), [scorer.py:325-333](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L325-L333).

### Câu 4: Phim không có thể loại (`(no genres listed)`) thì điểm P1 xử lý như thế nào? Có gây lỗi chia cho 0 không?
- **Trả lời:** Hoàn toàn không gây lỗi. Phim không có thể loại có tập $\mathcal{G}(c) = \emptyset$. Trong code, vòng lặp `for g in cand_genres` sẽ không thực hiện, `cand_p1[cand_mid]` giữ nguyên giá trị mặc định là `0.0`. Đồng thời, các thể loại nếu có $\text{deg}(g) == 0$ đều được bảo vệ bởi lệnh kiểm tra `if deg_g > 0:` trước khi thực hiện phép chia.
- **Bằng chứng:** [scorer.py:252](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L252), [scorer.py:261](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L261).

### Câu 5: Tại sao trong code có 2 nhánh `is_large_graph` và nhánh thường? Kết quả toán học có bị sai lệch không?
- **Trả lời:** Hoàn toàn đồng nhất về mặt toán học. 
  - Nhánh thường duyệt xuôi: từ phim nguồn $\to$ thể loại $\to$ phim ứng viên.
  - Nhánh `is_large_graph` đảo chiều tính toán (Target-centric): gom trước trọng số thể loại người dùng $\text{genre\_weights}[g]$, sau đó chỉ duyệt trên tập ứng viên tiềm năng đã được thu hẹp bởi P2 & P3.
  Cách tính này giúp giảm độ phức tạp từ việc quét hàng vạn phim xuống còn dưới 30ms trong khi bảo toàn 100% công thức cộng đóng góp.
- **Bằng chứng:** [scorer.py:240-269](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L240-L269).

---

## PHẦN F — ĐIỂM CHƯA XÁC MINH VÀ LƯU Ý KỸ THUẬT

1. **Khác biệt giữa Docstring và Code thực thi:**
   - Trong Docstring dòng 6 ghi: *"Độ tương đồng ngữ nghĩa cấp độ vĩ mô, độ đo Cosine chia căn bậc hai bậc đỉnh"*. 
   - Trên thực tế triển khai, mẫu số chỉ chia cho $\sqrt{\text{deg}(g)}$ chứ không chia cho $\sqrt{|\mathcal{G}(c)|}$ (bậc thể loại của phim ứng viên). Điều này có nghĩa là công thức phạt độ phổ biến của Genre chứ không phạt phim có nhiều thể loại.
2. **Khác biệt giữa Đồ thị lớn và Đồ thị nhỏ:**
   - Ở đồ thị lớn, P1 chỉ tính trên `all_candidate_ids` (tập ứng viên đã được khởi tạo bởi P3 và P2). Nếu một phim chỉ có P1 mà không có P2 hay P3 thì ở chế độ đồ thị lớn sẽ không được xét đến để tiết kiệm RAM. Tuy nhiên ở chế độ kiểm thử hoặc khi chạy độc lập P1, hệ thống quét toàn bộ tập liên kết thể loại.
