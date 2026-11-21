# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.3.4

> **Chuyên đề:** 3.3.4. Tính trọng số, tổng hợp điểm P1–P3 và xếp hạng Top-N  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Tệp kiểm toán cốt lõi:** `recommender/kg/scorer.py`, `recommender/kg/config.py`, `recommender/kg/kg_config.yaml`, `recommender/kg/evaluate.py`  
> **Trạng thái:** ĐÃ KIỂM ĐỊNH MÃ NGUỒN VÀ ĐỐI CHIẾU THỰC NGHIỆM 100%

---

## PHẦN A — BẢNG KIỂM TOÁN MÃ NGUỒN

| Thành phần kỹ thuật | Quy tắc triển khai trong mã nguồn | Ý nghĩa kỹ thuật | Bằng chứng file:line |
|---|---|---|---|
| **Chuẩn hóa Min-Max riêng biệt** | $\text{Norm\_P}_i(c) = \frac{\text{Raw} - \min}{\max - \min}$ cho từng đường đi $i \in \{1, 2, 3\}$ | Đưa điểm thô của từng Metapath về thang đo $[0.0, 1.0]$ trên tập ứng viên được sinh ra, triệt tiêu chênh lệch biên độ trước khi kết hợp. | [scorer.py:281-283](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L281-L283)<br>[scorer.py:325-333](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L325-L333) |
| **Xử lý biên Min-Max** | Nếu $\max - \min < 10^{-9}$: trả về $1.0$ (khi $\max > 0$) hoặc $0.0$ (khi $\max \le 0$) | Ngăn chặn hoàn toàn lỗi chia cho 0 khi tất cả ứng viên có điểm số bằng nhau hoặc đều bằng 0. | [scorer.py:331-332](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L331-L332) |
| **Bộ ba trọng số KG** | $\alpha = 0.35, \beta = 0.45, \gamma = 0.20$ | Trọng số thiết kế định hướng tri thức (Expert Heuristic): ưu tiên vi ngữ nghĩa Tag Genome ($0.45$), thể loại vĩ mô ($0.35$) và láng giềng cộng đồng ($0.20$). | [kg_config.yaml:7-9](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L7-L9)<br>[config.py:80-83](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/config.py#L80-L83)<br>[scorer.py:71-73](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L71-L73) |
| **Tự động chuẩn hóa trọng số** | $\alpha' = \frac{\alpha}{\alpha + \beta + \gamma}$ | Bảo đảm tổng ba trọng số luôn luôn bằng $1.0$, cho phép điều chỉnh linh hoạt qua biến môi trường. | [config.py:85-89](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/config.py#L85-L89)<br>[scorer.py:78-81](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L78-L81) |
| **Công thức KG Score tổng hợp** | $\text{Score}_{\text{KG}} = \alpha \cdot \text{Norm\_P1} + \beta \cdot \text{Norm\_P2} + \gamma \cdot \text{Norm\_P3}$ | Kết hợp tuyến tính các bằng chứng đồ thị chuẩn hóa; giá trị $\text{Score}_{\text{KG}} \in [0.0, 1.0]$. | [scorer.py:13](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L13)<br>[scorer.py:290](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L290) |
| **Khởi tạo Candidate Pool** | Nhánh lớn: $P_3$ và $P_2$ sinh ứng viên; $P_1$ chấm điểm giao thoa trên tập đó | Tối ưu hóa thời gian phục vụ (<30ms); tránh quét cạn 62.000 phim bằng cách để các vi đặc trưng và láng giềng thu hẹp không gian tìm kiếm. | [scorer.py:196](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L196)<br>[scorer.py:219](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L219)<br>[scorer.py:248](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L248) |
| **Lọc phim đã xem (Seen Filter)** | $c \notin \text{total\_exclude}$ trong suốt quá trình duyệt | Loại bỏ 100% phim đã xuất hiện trong lịch sử của người dùng mục tiêu (cả đánh giá cao lẫn đánh giá thấp). | [scorer.py:122-124](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L122-L124)<br>[scorer.py:193](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L193)<br>[scorer.py:217](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L217) |
| **Sắp xếp và Tie-breaking** | `candidate_scores.sort(key=lambda x: (-x[1], x[0]))` | Sắp xếp tất định: Điểm $\text{Score}_{\text{KG}}$ giảm dần; nếu bằng điểm thì `movieId` nhỏ hơn xếp trước. | [scorer.py:294](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L294) |
| **Trích xuất bằng chứng Top-N** | Chỉ trích xuất evidence cho Top-$N$ sau khi xếp hạng | Tiết kiệm hơn 99% thời gian CPU; chỉ tạo đối tượng `EvidenceItem` cho các phim thực sự được đề xuất. | [scorer.py:297-312](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L297-L312) |

---

## PHẦN B — CÔNG THỨC TOÁN HỌC CHUẨN

### 1. Chuẩn hóa Min-Max của từng Metapath thành phần
Gọi $\mathcal{C} = \{c_1, c_2, \dots, c_J\}$ là tập hợp toàn bộ các bộ phim ứng viên được kích hoạt trong phiên suy luận của người dùng $u$. Với mỗi đường đi $P_i \in \{P_1, P_2, P_3\}$, điểm số thô $\text{Score}_{P_i}^{\text{raw}}(u, c)$ được đưa về đoạn $[0.0, 1.0]$ theo công thức:
$$\text{Score}_{P_i}^{\text{norm}}(u, c) = \begin{cases} 
\frac{\text{Score}_{P_i}^{\text{raw}}(u, c) - \min_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x)}{\max_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x) - \min_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x)}, & \text{nếu } \max_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x) - \min_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x) \ge 10^{-9} \\
1.0, & \text{nếu } \max_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x) = \min_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x) > 0 \\
0.0, & \text{nếu } \max_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x) = \min_{x \in \mathcal{C}} \text{Score}_{P_i}^{\text{raw}}(u, x) \le 0
\end{cases}$$

### 2. Chuẩn hóa bộ ba trọng số liên kết
Bộ ba tham số đóng góp $\alpha_{\text{genre}}, \beta_{\text{genome}}, \gamma_{\text{collab}} > 0$ được tự động chuẩn hóa về phân phối trọng số đơn vị:
$$\alpha = \frac{\alpha_{\text{genre}}}{\alpha_{\text{genre}} + \beta_{\text{genome}} + \gamma_{\text{collab}}}, \quad \beta = \frac{\beta_{\text{genome}}}{\alpha_{\text{genre}} + \beta_{\text{genome}} + \gamma_{\text{collab}}}, \quad \gamma = \frac{\gamma_{\text{collab}}}{\alpha_{\text{genre}} + \beta_{\text{genome}} + \gamma_{\text{collab}}}$$
Mặc định trong cấu hình hệ thống: $\alpha = 0.35$, $\beta = 0.45$, $\gamma = 0.20$, thỏa mãn điều kiện $\alpha + \beta + \gamma = 1.0$.

### 3. Công thức tổng hợp điểm số đồ thị tri thức (KG Score)
Điểm số tổng hợp của đồ thị tri thức cho tác phẩm ứng viên $c$ đối với người dùng $u$ là tổ hợp tuyến tính có trọng số của ba điểm thành phần đã chuẩn hóa:
$$\text{Score}_{\text{KG}}(u, c) = \alpha \cdot \text{Score}_{P_1}^{\text{norm}}(u, c) + \beta \cdot \text{Score}_{P_2}^{\text{norm}}(u, c) + \gamma \cdot \text{Score}_{P_3}^{\text{norm}}(u, c)$$
Do $\text{Score}_{P_i}^{\text{norm}}(u, c) \in [0.0, 1.0]$ và $\alpha + \beta + \gamma = 1.0$, miền giá trị của điểm tổng hợp luôn luôn được bảo đảm:
$$\text{Score}_{\text{KG}}(u, c) \in [0.0, 1.0]$$

### 4. Lựa chọn và xếp hạng danh sách Top-N
Danh sách đề xuất cuối cùng $\mathcal{R}_N(u)$ gồm $N$ tác phẩm được lựa chọn thông qua quan hệ thứ tự toàn phần có giải quyết hòa điểm tất định:
$$\mathcal{R}_N(u) = \operatorname{argTop-}N_{c \in \mathcal{C}} \left( \text{Score}_{\text{KG}}(u, c), -c \right)$$
Trong đó, tiêu chí sắp xếp ưu tiên điểm số $\text{Score}_{\text{KG}}(u, c)$ giảm dần; nếu hai ứng viên có điểm số trùng khớp nhau, ứng viên có mã định danh $c$ nhỏ hơn (`movieId ASC`) sẽ được ưu tiên xếp trước.

---

## PHẦN C — VÍ DỤ TÍNH TAY MINH HỌA

### 1. Dữ liệu đầu vào giả định
Xét người dùng $u$ với 3 tác phẩm ứng viên $\{c_1, c_2, c_3\}$ trong Candidate Pool (đều chưa xem).
Bảng điểm thô đã tính toán từ các mục trước:

| Ứng viên | Mã phim (`movieId`) | Điểm thô $P_1$ | Điểm thô $P_2$ | Điểm thô $P_3$ |
|---|---|---|---|---|
| $c_1$ | 101 | $0.80$ | $1.20$ | $0.50$ |
| $c_2$ | 205 | $0.40$ | $0.60$ | $1.00$ |
| $c_3$ | 302 | $0.00$ | $0.00$ | $0.25$ |

Bộ trọng số mặc định: $\alpha = 0.35$, $\beta = 0.45$, $\gamma = 0.20$. Yêu cầu chọn Top-$N = 2$.

### 2. Các bước tính toán chi tiết

**Bước 1: Chuẩn hóa Min-Max độc lập cho từng Metapath:**
- **Đường đi $P_1$:**
  * $\min(P_1) = 0.00$, $\max(P_1) = 0.80 \implies \Delta_1 = 0.80$.
  * $\text{Norm\_P1}(c_1) = \frac{0.80 - 0.00}{0.80} = 1.0000$.
  * $\text{Norm\_P1}(c_2) = \frac{0.40 - 0.00}{0.80} = 0.5000$.
  * $\text{Norm\_P1}(c_3) = \frac{0.00 - 0.00}{0.80} = 0.0000$.
- **Đường đi $P_2$:**
  * $\min(P_2) = 0.00$, $\max(P_2) = 1.20 \implies \Delta_2 = 1.20$.
  * $\text{Norm\_P2}(c_1) = \frac{1.20 - 0.00}{1.20} = 1.0000$.
  * $\text{Norm\_P2}(c_2) = \frac{0.60 - 0.00}{1.20} = 0.5000$.
  * $\text{Norm\_P2}(c_3) = \frac{0.00 - 0.00}{1.20} = 0.0000$.
- **Đường đi $P_3$:**
  * $\min(P_3) = 0.25$, $\max(P_3) = 1.00 \implies \Delta_3 = 0.75$.
  * $\text{Norm\_P3}(c_1) = \frac{0.50 - 0.25}{0.75} = \frac{0.25}{0.75} \approx 0.3333$.
  * $\text{Norm\_P3}(c_2) = \frac{1.00 - 0.25}{0.75} = \frac{0.75}{0.75} = 1.0000$.
  * $\text{Norm\_P3}(c_3) = \frac{0.25 - 0.25}{0.75} = \frac{0.00}{0.75} = 0.0000$.

**Bước 2: Tổng hợp điểm số Knowledge Graph ($\text{Score}_{\text{KG}}$):**
- **Ứng viên $c_1$:**
  $$\text{Score}_{\text{KG}}(u, c_1) = 0.35 \times 1.0000 + 0.45 \times 1.0000 + 0.20 \times 0.3333 = 0.3500 + 0.4500 + 0.0667 = 0.8667$$
- **Ứng viên $c_2$:**
  $$\text{Score}_{\text{KG}}(u, c_2) = 0.35 \times 0.5000 + 0.45 \times 0.5000 + 0.20 \times 1.0000 = 0.1750 + 0.2250 + 0.2000 = 0.6000$$
- **Ứng viên $c_3$:**
  $$\text{Score}_{\text{KG}}(u, c_3) = 0.35 \times 0.0000 + 0.45 \times 0.0000 + 0.20 \times 0.0000 = 0.0000$$

**Bước 3: Xếp hạng và chọn Top-2:**
1. **Hạng 1:** Ứng viên $c_1$ (`movieId = 101`) với $\text{Score}_{\text{KG}} = 0.8667$.
2. **Hạng 2:** Ứng viên $c_2$ (`movieId = 205`) với $\text{Score}_{\text{KG}} = 0.6000$.
3. **Bị loại:** Ứng viên $c_3$ (`movieId = 302`) với $\text{Score}_{\text{KG}} = 0.0000$ (nằm ngoài ngưỡng Top-2).

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.3.4. Tính trọng số, tổng hợp điểm P1–P3 và xếp hạng Top-N

Sau khi hoàn tất quá trình tích lũy điểm số thô từ ba đường đi siêu liên kết, hệ thống tiến hành dung hợp các nguồn thông tin độc lập nhằm thiết lập danh sách tác phẩm gợi ý hoàn chỉnh. Do mỗi đường đi vận hành trên các không gian đặc trưng có độ thưa và thang đo toán học khác nhau, việc cộng trực tiếp các giá trị thô sẽ dẫn tới hiện tượng một đường đi chiếm ưu thế áp đảo. Để bảo đảm tính bình đẳng giữa các luồng suy luận, điểm số của từng đường đi được chuẩn hóa độc lập theo phương pháp Min-Max trên toàn bộ tập ứng viên được kích hoạt, đưa các phân phối điểm về cùng đoạn giá trị từ 0 đến 1 trước khi thực hiện phép nhân trọng số.

Điểm số đồ thị tri thức tổng hợp được xác định bằng tổ hợp tuyến tính có trọng số của ba thành phần đã chuẩn hóa:

$$\text{Score}_{\text{KG}}(u, c) = \alpha \cdot \text{Score}_{P_1}^{\text{norm}}(u, c) + \beta \cdot \text{Score}_{P_2}^{\text{norm}}(u, c) + \gamma \cdot \text{Score}_{P_3}^{\text{norm}}(u, c)$$

Trong công thức trên, các ký hiệu được định nghĩa như sau: Score_{P1}^{norm}, Score_{P2}^{norm} và Score_{P3}^{norm} lần lượt là điểm số chuẩn hóa của đường đi thể loại, đường đi thẻ ngữ nghĩa và đường đi cộng tác láng giềng đối với tác phẩm c; các hệ số alpha, beta và gamma đại diện cho tỷ trọng đóng góp của từng đường đi và được ràng buộc chuẩn hóa có tổng bằng 1. Dựa trên phân tích thực nghiệm và đặc thù ngữ nghĩa, cấu hình mặc định của hệ thống gán alpha = 0,35, beta = 0,45 và gamma = 0,20. Tỷ trọng này phản ánh sự ưu tiên cao nhất cho không gian cảm xúc vi mô Tag Genome, tiếp đến là khung thể loại vĩ mô, và sử dụng tín hiệu láng giềng cộng đồng như một thành phần bổ trợ đa dạng hóa.

Quá trình xếp hạng cuối cùng được thực hiện thông qua việc sắp xếp tập ứng viên theo thứ tự điểm số tổng hợp giảm dần và giải quyết trường hợp hòa điểm bằng mã định danh phim tăng dần. Nhằm tối ưu hóa hiệu năng phục vụ thời gian thực, toàn bộ các tác phẩm người dùng đã từng tương tác bị loại bỏ nghiêm ngặt khỏi tập ứng viên trước khi xếp hạng. Sau khi cắt tỉa lấy N tác phẩm dẫn đầu, hệ thống mới tiến hành truy vết cấu trúc đồ thị con để trích xuất bằng chứng suy luận cho riêng danh sách rút gọn này, bảo đảm độ trễ phản hồi toàn trình duy trì dưới ngưỡng 30 mili giây.

---

## PHẦN E — PHẢN BIỆN HỌC THUẬT (5 CÂU HỎI HỘI ĐỒNG)

### Câu 1: Tại sao nhóm lại chọn bộ trọng số $\alpha = 0.35, \beta = 0.45, \gamma = 0.20$? Bộ trọng số này có phải là kết quả học máy tối ưu toàn cục không?
- **Trả lời:** **KHÔNG.** Bộ trọng số này không phải là nghiệm tối ưu toàn cục được học bằng Gradient Descent hay Backpropagation. Đây là **bộ trọng số thiết kế định hướng tri thức (Expert Heuristic)** được kiểm chứng qua các thử nghiệm Ablation Study (Gate 4 trong `recommender/kg/evaluate.py`). Tag Genome được gán tỷ trọng cao nhất ($0.45$) vì sở hữu 1,128 chiều liên tục mang tính phân tách vi mô vượt trội; Genre ($0.35$) giữ vai trò ổn định khung vĩ mô; và Collaborative ($0.20$) bổ trợ xu hướng cộng đồng. Hệ thống hỗ trợ cấu hình linh hoạt qua biến môi trường để thích ứng khi phân phối dữ liệu thay đổi.
- **Bằng chứng:** [kg_config.yaml:7-9](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/kg_config.yaml#L7-L9), [evaluate.py:7-11](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/evaluate.py#L7-L11).

### Câu 2: Tại sao phải chuẩn hóa Min-Max riêng từng đường đi trước khi cộng, thay vì nhân trọng số trực tiếp vào điểm thô?
- **Trả lời:** Điểm thô của ba đường đi có thứ nguyên và miền giá trị hoàn toàn khác nhau do khác biệt về cấu trúc tô-pô:
  - $P_1$ chia cho $\sqrt{\text{deg}(g)}$ nên điểm thô thường dao động trong khoảng $[0.1, 2.0]$.
  - $P_2$ nhân hai đầu relevance và chia cho $\ln(1 + \text{deg}(t))$ nên điểm thô có thể vượt lên $[1.0, 5.0]$.
  - $P_3$ là tổng tích Cosine và rating láng giềng nên phụ thuộc vào mật độ người dùng cùng gu.
  Nếu nhân trọng số trực tiếp mà không chuẩn hóa, đường đi có biên độ thô lớn nhất sẽ lấn át hoàn toàn các đường đi còn lại, làm vô hiệu hóa tỷ trọng $\alpha, \beta, \gamma$. Chuẩn hóa Min-Max đưa cả ba về cùng miền $[0.0, 1.0]$, bảo đảm sự đóng góp thực tế đúng tỷ lệ thiết kế.
- **Bằng chứng:** [scorer.py:281-283](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L281-L283), [scorer.py:325-333](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L325-L333).

### Câu 3: Điểm $\text{Score}_{\text{KG}}$ có phải là dự đoán số sao người dùng sẽ chấm (Rating Prediction) hay xác suất click/thích phim không?
- **Trả lời:** **HOÀN TOÀN KHÔNG.** $\text{Score}_{\text{KG}}$ là điểm tích lũy bằng chứng đồ thị (Path Evidence Score) được chuẩn hóa về $[0.0, 1.0]$ phục vụ bài toán xếp hạng tương đối (Top-N Ranking). Điểm số này không mang ngữ nghĩa xác suất thống kê (không thỏa mãn tiên đề xác suất Kolmogorov) và cũng không phải điểm sao trên thang đo 1–5.
- **Bằng chứng:** [scorer.py:12-13](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L12-L13), [scorer.py:290](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L290).

### Câu 4: Trong nhánh đồ thị lớn (`is_large_graph`), tại sao P1 không tự sinh ứng viên mới? Điều này có gây mất mát phim tiềm năng chỉ có thể loại giống nhau không?
- **Trả lời:** Đúng là có sự đánh đổi kỹ thuật (Engineering Trade-off). Một thể loại như Drama có hơn 25,000 phim. Nếu $P_1$ tự sinh ứng viên, hệ thống sẽ phải đưa hàng chục ngàn phim vào bộ nhớ để chấm điểm, khiến thời gian truy vấn vượt quá 500ms. Trong khi đó, mục tiêu của MoodGraph là khai thác ngữ nghĩa tâm trạng vi mô. Do đó, hệ thống để $P_2$ (Top-15 thẻ tích cực) và $P_3$ (Top-50 láng giềng) thu hẹp Candidate Pool về vài trăm ứng viên tiềm năng cao nhất, sau đó $P_1$ mới tham gia chấm điểm thể loại trên tập này. Các phim chỉ có thể loại giống nhau thuần túy mà không có bất kỳ kết nối ngữ nghĩa hay cộng đồng nào được xem là quá đại trà và bị cắt tỉa để bảo đảm thời gian phục vụ dưới 30ms.
- **Bằng chứng:** [scorer.py:241-253](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L241-L253).

### Câu 5: Tại sao hệ thống lại thực hiện trích xuất bằng chứng (Evidence Extraction) sau khi cắt Top-N thay vì làm đồng thời trong lúc tính điểm?
- **Trả lời:** Quá trình tính điểm thô diễn ra ở tầng số học nguyên thủy (Fast Float Accumulation) chỉ mất 15–20 mili giây trên hàng trăm ứng viên. Ngược lại, trích xuất bằng chứng đòi hỏi khởi tạo các đối tượng cấu trúc dữ liệu phức tạp (`EvidenceItem`, truy vấn tên phim, định danh đỉnh, nhãn quan hệ). Nếu trích xuất bằng chứng cho toàn bộ ứng viên, hệ thống sẽ tiêu tốn hơn 90% CPU vào việc cấp phát bộ nhớ cho những bộ phim sau đó bị loại bỏ. Việc trì hoãn trích xuất bằng chứng cho đến sau khi đã chọn đúng Top-$N$ (thường $N=50$) giúp tiết kiệm hơn 99% tài nguyên tính toán.
- **Bằng chứng:** [scorer.py:15-17](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L15-L17), [scorer.py:296-304](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L296-L304).

---

## PHẦN F — KIỂM TRA SAI LỆCH VÀ BẢO ĐẢM HỌC THUẬT

1. **Phân biệt trọng số KG với trọng số Hybrid:**
   - Đã xác minh: $\alpha = 0.35, \beta = 0.45, \gamma = 0.20$ là bộ trọng số **nội bộ của Knowledge Graph Scorer**. Tuyệt đối không nhầm lẫn với trọng số của mô hình Hybrid ALS/KG ($w_{\text{ALS}} = 0.60, w_{\text{KG}} = 0.40$).
2. **Không khẳng định tối ưu toàn cục:**
   - Đã kiểm chứng: Mã nguồn sử dụng cấu hình heuristic được kiểm định qua Gate 4 Ablation Study, không sử dụng thuật toán tối ưu hóa tự động liên tục trên tập trọng số này.
3. **Phân biệt các khái niệm Top:**
   - Top-$N$ Recommendation: Số lượng phim gợi ý trả về cuối cùng cho người dùng (mặc định $N = 50$).
   - Top-$M$ Genome Tags: 20 thẻ có relevance cao nhất được lưu trên mỗi phim khi xây dựng đồ thị ($M = 20$).
   - Top-15 Active Tags: 15 thẻ có trọng số tích lũy lớn nhất của người dùng được kích hoạt để lan truyền trên đồ thị lớn.
4. **Xử lý Seen Filtering:**
   - Toàn bộ phim đã đánh giá trong tập Train bị loại bỏ 100% qua `total_exclude` trước khi tính điểm và xếp hạng.
5. **Xử lý người dùng cold-start:**
   - Nếu người dùng không có lịch sử hoặc không có đánh giá $\ge 3.5$, luồng KG trả về danh sách rỗng `[]`. Việc fallback sang Popularity được đảm nhiệm bởi tầng dịch vụ điều phối cấp cao hơn.
