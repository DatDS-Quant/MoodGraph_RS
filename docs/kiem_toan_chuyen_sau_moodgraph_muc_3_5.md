# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.5

> **Chuyên đề:** 3.5. Phương pháp đối chứng: Popularity, Spark ALS và Hybrid mở rộng  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Tệp kiểm toán cốt lõi:**  
> - `recommender/als/popularity.py` (M03: Global Popularity Baselines - Count & Bayesian Weighted)  
> - `recommender/als/trainer.py` (M05: Distributed Spark ALS Trainer Engine)  
> - `recommender/als/candidates.py` (M06/M10: Exact Filter-Before-Top-K Candidate Generation)  
> - `recommender/als/tuner.py` (M07: Validation Grid Search & Long-tail Diagnostics)  
> - `recommender/hybrid/engine.py` (Phase 4: Hybrid Recommender Coordination Service)  
> - `recommender/hybrid/fusion.py` (Phase 4: Cormack RRF & Weighted Score Fusion Algorithms)  
> - `recommender/hybrid/config.py` (Phase 4: Hybrid Configuration & Serving Defaults)  
> - `artifacts/als/m07/best_als_model_manifest.json` (Champion ALS Model Metadata)  
> - `artifacts/als/m08/m08_test_benchmark_results.json` (Test Benchmark trên 111.211 users)  
> - `docs/phase4/hybrid_validation_results.json` (Kết quả thực nghiệm lưới trọng số Hybrid)  
> - `docs/audits/HYBRID_FUSION_RESEARCH.md` (Báo cáo nghiên cứu động lực học dung hợp)  
> **Trạng thái:** ĐÃ KIỂM ĐỊNH MÃ NGUỒN VÀ ĐỐI CHIẾU THỰC TẾ 100%

---

## PHẦN A — BẢNG KIỂM TOÁN KỸ THUẬT

| Thành phần kỹ thuật | Thuật toán triển khai thực tế | Cấu hình tham số | Vai trò hệ thống | Bằng chứng file:line |
| :--- | :--- | :--- | :--- | :--- |
| **Popularity Count** | Xếp hạng toàn cục theo tổng lượt đánh giá trong Train. Tie-breaking: `count DESC, avg_rating DESC, movieId ASC`. | Không tham số. Tính thuần túy từ tập `splits/train`. | Baseline không cá nhân hóa sơ cấp; Fallback khẩn cấp khi người dùng hoàn toàn mới. | [popularity.py:108-136](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py#L108-L136) |
| **Popularity Weighted** | Điểm trung bình có trọng số Bayes (Dirichlet / IMDb prior): $WS = \frac{v \cdot R + m \cdot C}{v + m}$. Tie-breaking: `ws DESC, v DESC, movieId ASC`. | $m = 10.0$ (tham số làm mượt tiên nghiệm), $C \approx 3.53$ (trung bình toàn cục Train). | Baseline phân phối điểm số chuẩn; lọc bớt phim ít vote điểm cao ảo. | [popularity.py:76-105](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py#L76-L105)<br>[popularity.py:139-174](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py#L139-L174) |
| **Spark ALS Trainer** | Phân rã ma trận luân phiên phân tán (Distributed Alternating Least Squares) trên đánh giá hiện (Explicit feedback). | Mặc định code: `rank=16, reg_param=0.1, max_iter=10`. Huấn luyện trên toàn bộ 24.6 triệu ratings. | Động cơ biểu diễn nhân tố ẩn (Collaborative Latent Factor Embeddings). | [trainer.py:44-71](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py#L44-L71) |
| **Champion ALS Model** | Mô hình chiến thắng sau quá trình quét lưới siêu tham số (M07 Hyperparameter Tuning). | `rank=8, reg_param=0.3, max_iter=10, seed=42, cold_start='nan'`. Artifact: `ALS_R8_REG0.3_ITER10`. | Mô hình ALS chính thức được đóng gói và nạp phục vụ thực tế trong Hybrid Engine. | [best_als_model_manifest.json:8-15](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m07/best_als_model_manifest.json#L8-L15) |
| **Exact ALS Top-N** | Nhân ma trận BLAS theo lô ($P_{\text{batch}} \cdot Q^T$), lọc trước phim đã xem bằng mặt nạ $-\infty$, trích xuất `argpartition` $O(M)$. | `batch_size=2500`, danh mục chấm điểm: 58.932 phim. Tie-breaking: `score DESC, movieId ASC`. | Bộ sinh ứng viên Top-K độc lập không mắc lỗi thiếu hụt Top-K do oversampling. | [candidates.py:188-237](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L188-L237) |
| **Hybrid Candidate Generation** | Hợp nhất ứng viên độc lập: $\mathcal{C}_{\text{hybrid}}(u) = \mathcal{C}_{\text{ALS}}(u) \cup \mathcal{C}_{\text{KG}}(u)$. | Top-$K_{\text{ALS}} = 50$, Top-$K_{\text{KG}} = 50$, danh mục hợp nhất tối đa 100 ứng viên. | Mở rộng không gian tìm kiếm, kết hợp tương quan hành vi tiềm ẩn và đồ thị ngữ nghĩa. | [engine.py:144-179](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/engine.py#L144-L179)<br>[config.py:20-21](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/config.py#L20-L21) |
| **Defense-in-depth Seen Filtering** | Lọc phim đã xem ở 3 tầng: Tầng sinh ứng viên riêng lẻ, Tầng Hybrid Engine trước khi Fusion, Tầng Database API. | Loại bỏ toàn bộ `seen_movies` khỏi tập hợp ứng viên hợp nhất. | Ngăn chặn 100% rò rỉ phim đã tương tác vào danh sách đề xuất cá nhân hóa. | [engine.py:227-229](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/engine.py#L227-L229) |
| **Reciprocal Rank Fusion (RRF)** | Dung hợp theo thứ hạng bất biến thang đo (Scale-Invariant): $\sum_{S} \frac{1}{k + \text{Rank}_S(m)}$. | $k = 60$ (hằng số làm mịn Cormack). Tie-breaking: `hybrid_score DESC, movieId ASC`. | Chiến lược dung hợp mặc định của hệ thống; loại trừ ưu thế điểm thô bùng nổ của ALS. | [fusion.py:58-159](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L58-L159) |
| **Weighted Score Fusion** | Chuẩn hóa Min-Max tuyến tính độc lập từng nguồn rồi tính tổ hợp tuyến tính: $w_{\text{ALS}} \cdot s_{\text{norm}}^{\text{ALS}} + w_{\text{KG}} \cdot s_{\text{norm}}^{\text{KG}}$. | Mặc định phục vụ: $w_{\text{ALS}}=0.5, w_{\text{KG}}=0.5$. Tối ưu thực nghiệm: $w_{\text{ALS}}=0.1, w_{\text{KG}}=0.9$. | Chiến lược dung hợp định lượng; cho phép điều chỉnh tỷ trọng đóng góp linh hoạt. | [fusion.py:162-291](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L162-L291)<br>[config.py:18-19](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/config.py#L18-L19) |
| **Chiến lược Nội suy (Imputation)** | Xử lý ứng viên chỉ xuất hiện ở một nguồn: `zero` (0.0), `min` (giá trị tối thiểu), `neutral` (0.5), `source_aware` (ALS=0.2, KG=0.0). | Mặc định: `imputation_strategy = "zero"`. | Đảm bảo tính toán công bằng cho các ứng viên không thuộc tập giao của 2 mô hình. | [fusion.py:214-229](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L214-L229) |

---

## PHẦN B — CÔNG THỨC TOÁN HỌC CHUẨN XÁC

### 1. Công thức Điểm Phổ biến Bayes (IMDb / Dirichlet Prior Weighted Score)

Công thức tính điểm trung bình có trọng số Bayes cho bộ phim $i$ dựa trên phân phối tiên nghiệm toàn cục:

$$\text{WS}(i) = \frac{v_i \cdot R_i + m \cdot C}{v_i + m}$$

Trong đó:
- $v_i \ge 0$: Số lượng lượt đánh giá của bộ phim $i$ trong tập huấn luyện (`splits/train`), tương ứng với biến `rating_count`.
- $R_i$: Điểm đánh giá trung bình thực tế của bộ phim $i$ trong tập huấn luyện (`avg_rating`).
- $C$: Điểm đánh giá trung bình toàn cục tính trên toàn bộ các lượt tương tác của tập huấn luyện (`global_mean`, thực nghiệm MovieLens 25M đạt xấp xỉ $3.533$).
- $m \ge 0$: Tham số làm mượt tiên nghiệm (smoothing parameter / prior pseudo-counts), được cố định bằng $10.0$ trong mã nguồn.

*Điều kiện biên:* Nếu $v_i = 0$ và $m = 0$, hàm trả về $\text{WS}(i) = C$.  
*Bằng chứng mã nguồn:* [recommender/als/popularity.py:76-105](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/popularity.py#L76-L105).

---

### 2. Hàm Mục tiêu Tối ưu và Dự đoán Điểm số của Spark ALS

Hàm mất mát bình phương tối thiểu có điều chuẩn $L_2$ giải bằng phương pháp luân phiên (Alternating Least Squares) trên dữ liệu tường minh:

$$\mathcal{L}_{\text{ALS}}(\mathbf{U}, \mathbf{V}) = \sum_{(u, i) \in \mathcal{R}_{\text{train}}} \left( r_{ui} - \mathbf{u}_u^T \mathbf{v}_i \right)^2 + \lambda \left( \sum_{u=1}^U \|\mathbf{u}_u\|_2^2 + \sum_{i=1}^M \|\mathbf{v}_i\|_2^2 \right)$$

Công thức dự đoán mức độ ưa thích của người dùng $u$ cho tác phẩm $i$:

$$\hat{r}_{ui} = \mathbf{u}_u^T \mathbf{v}_i = \sum_{f=1}^k u_{u, f} \cdot v_{i, f}$$

Trong đó:
- $r_{ui} \in [0.5, 5.0]$: Điểm đánh giá số sao thực tế giữa người dùng $u$ và phim $i$ trong tập Train.
- $\mathbf{u}_u \in \mathbb{R}^k$: Vector nhân tố ẩn của người dùng $u$ (User Latent Factor).
- $\mathbf{v}_i \in \mathbb{R}^k$: Vector nhân tố ẩn của bộ phim $i$ (Item Latent Factor).
- $k$: Số chiều nhân tố ẩn (`rank`). Cấu hình mặc định trong code là $k = 16$; cấu hình Champion Model thực tế là $k = 8$.
- $\lambda \ge 0$: Hệ số điều chuẩn (`reg_param`). Cấu hình mặc định trong code là $\lambda = 0.1$; cấu hình Champion Model thực tế là $\lambda = 0.3$.

*Lưu ý triển khai:* Giá trị $\hat{r}_{ui}$ không bị chặn trần hoặc chặn sàn về khoảng $[0.5, 5.0]$, dẫn đến hiện tượng bùng nổ điểm số đối với các vật phẩm đuôi dài.  
*Bằng chứng mã nguồn:* [recommender/als/trainer.py:48-55](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py#L48-L55), [recommender/als/candidates.py:178](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/candidates.py#L178).

---

### 3. Công thức Dung hợp Thứ hạng Nghịch đảo Cormack (Reciprocal Rank Fusion - RRF)

Điểm số dung hợp thứ hạng RRF cho bộ phim $m$ đối với người dùng $u$ từ hai nguồn ứng viên $\mathcal{C}_{\text{ALS}}(u)$ và $\mathcal{C}_{\text{KG}}(u)$:

$$\text{Score}_{\text{RRF}}(u, m) = \sum_{S \in \{\text{ALS}, \text{KG}\}} \frac{\mathbb{I}(m \in \mathcal{C}_S(u))}{k_{\text{RRF}} + \text{Rank}_S(u, m)}$$

Trong đó:
- $S \in \{\text{ALS}, \text{KG}\}$: Nguồn sinh danh sách ứng viên tương ứng (Spark ALS hoặc Knowledge Graph).
- $\mathcal{C}_S(u)$: Tập hợp các bộ phim ứng viên do nguồn $S$ đề xuất cho người dùng $u$ (với $|\mathcal{C}_S(u)| \le 50$).
- $\mathbb{I}(\cdot)$: Hàm chỉ thị (Indicator function), nhận giá trị $1$ nếu ứng viên $m$ xuất hiện trong danh sách của nguồn $S$, và nhận giá trị $0$ nếu ứng viên vắng mặt.
- $\text{Rank}_S(u, m) \in \{1, 2, \dots, |\mathcal{C}_S(u)|\}$: Thứ hạng của bộ phim $m$ trong danh sách sắp xếp nội bộ của nguồn $S$ (hạng 1 là tốt nhất).
- $k_{\text{RRF}} > 0$: Hằng số làm mịn phân vị Cormack, mặc định $k_{\text{RRF}} = 60$.

*Bằng chứng mã nguồn:* [recommender/hybrid/fusion.py:77](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L77), [recommender/hybrid/fusion.py:103-108](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L103-L108).

---

### 4. Công thức Dung hợp Điểm số Tuyến tính Chuẩn hóa (Weighted Score Fusion)

Điểm số dung hợp có trọng số giữa ALS và KG trên tập hợp ứng viên hợp nhất $\mathcal{C}_{\text{hybrid}}(u) = \mathcal{C}_{\text{ALS}}(u) \cup \mathcal{C}_{\text{KG}}(u)$:

$$\text{Score}_{\text{Weighted}}(u, m) = w_{\text{ALS}}' \cdot \tilde{s}_{\text{ALS}}(u, m) + w_{\text{KG}}' \cdot \tilde{s}_{\text{KG}}(u, m)$$

Trong đó trọng số chuẩn hóa đơn vị thỏa mãn:

$$w_{\text{ALS}}' = \frac{w_{\text{ALS}}}{w_{\text{ALS}} + w_{\text{KG}}}, \quad w_{\text{KG}}' = \frac{w_{\text{KG}}}{w_{\text{ALS}} + w_{\text{KG}}}$$

Hàm chuẩn hóa Min-Max cục bộ trên danh sách ứng viên của từng nguồn $S \in \{\text{ALS}, \text{KG}\}$:

$$\tilde{s}_S(u, m) = \begin{cases}
\frac{s_S(u, m) - \min_{x \in \mathcal{C}_S(u)} s_S(u, x)}{\max_{x \in \mathcal{C}_S(u)} s_S(u, x) - \min_{x \in \mathcal{C}_S(u)} s_S(u, x)}, & \text{nếu } m \in \mathcal{C}_S(u) \text{ và } \Delta s_S \ge 10^{-12} \\
1.0, & \text{nếu } m \in \mathcal{C}_S(u) \text{ và } \Delta s_S < 10^{-12} \text{ và } \max s_S > 0 \\
s_{\text{impute}}^S, & \text{nếu } m \notin \mathcal{C}_S(u)
\end{cases}$$

Trong đó $s_{\text{impute}}^S$ là giá trị nội suy cho các ứng viên chỉ xuất hiện ở một bên (chính sách mặc định `zero` gán $s_{\text{impute}}^S = 0.0$).  
*Bằng chứng mã nguồn:* [recommender/hybrid/fusion.py:22-38](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L22-L38), [recommender/hybrid/fusion.py:180-239](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L180-L239).

---

## PHẦN C — SO SÁNH CÁC PHƯƠNG PHÁP ĐỐI CHỨNG

| Tiêu chí phân định | Popularity Baseline (M03) | Spark ALS (M05 / M07) | Knowledge Graph (P1–P3) | Hybrid RRF (Phase 4) | Hybrid Weighted (Phase 4) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Nguồn dữ liệu đầu vào** | Số lượt đánh giá và điểm số trong Train. | Ma trận tương tác người dùng - vật phẩm thô. | Đồ thị đa quan hệ (Thể loại, 1.128 Genome Tags, Co-ratings). | Danh sách thứ hạng ứng viên từ ALS và KG. | Điểm số chuẩn hóa Min-Max từ ALS và KG. |
| **Nguyên lý tính toán** | Thống kê tần suất toàn cục và trung bình Bayes. | Phân rã ma trận tối ưu hàm mất mát bình phương. | Duyệt đường đi suy luận siêu liên kết (Metapaths). | Nghịch đảo thứ hạng có làm mịn Cormack ($k=60$). | Tổ hợp tuyến tính có trọng số độc lập ($w_{\text{ALS}}, w_{\text{KG}}$). |
| **Cơ chế cá nhân hóa** | **Hoàn toàn không** (Danh sách cố định cho mọi user sau lọc). | **Cá nhân hóa gián tiếp** qua không gian vector ẩn. | **Cá nhân hóa trực tiếp** theo lịch sử yêu thích tích cực. | **Cá nhân hóa đa chiều** (đồng thuận thứ hạng). | **Cá nhân hóa đa chiều** (kết hợp biên độ điểm số). |
| **Yêu cầu huấn luyện** | Chỉ cần tính toán gom cụm thống kê một lần ($O(N)$). | Huấn luyện phân tán nặng (Spark MLlib cluster). | Không cần huấn luyện tham số; duyệt đồ thị in-memory. | Không cần huấn luyện; dung hợp trực tiếp tại thời gian phục vụ. | Không cần huấn luyện mô hình; chỉ quét lưới trọng số ($w$). |
| **Khả năng giải thích** | Kém (chỉ giải thích dựa trên xu hướng đám đông). | Hộp đen toán học (không thể giải thích trực tiếp). | **Tuyệt đối minh bạch** (truy vết từng nút và cạnh). | **Giải thích lai ghép** (bảo toàn bằng chứng KG + ALS). | **Giải thích lai ghép** (bảo toàn bằng chứng KG + ALS). |
| **Độ phủ danh mục (Coverage@10)** | Thấp (317 phim trên Test, 45 phim trên Val). | Cực thấp (12–35 phim trên Val, thiên lệch phim 1-rating). | **Rất cao (276 phim trên Val)**. | Trung bình (152 phim trên Val). | **Rất cao (276 phim tại tỷ lệ 0.1/0.9)**. |
| **Khả năng xử lý Cold-Start** | Xuất sắc (là phương án fallback tối hậu). | Thất bại (trả về NaN nếu user chưa có vector ẩn). | Tốt nếu user có vài tương tác thể loại ban đầu. | Chuyển giao tự động sang KG nếu user thiếu vector ALS. | Chuyển giao tự động sang KG nếu user thiếu vector ALS. |

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.5. Phương pháp đối chứng: Popularity, Spark ALS và Hybrid mở rộng

Để thiết lập cơ sở kiểm chứng thực nghiệm chặt chẽ cho phương pháp đề xuất dựa trên đồ thị tri thức, nghiên cứu triển khai ba nhóm mô hình đối chứng đại diện cho các trường phái gợi ý kinh điển: mô hình phổ biến toàn cục không cá nhân hóa, mô hình lọc cộng tác nhân tố tiềm ẩn quy mô lớn và mô hình lai ghép đa nguồn.

Mô hình phổ biến toàn cục đóng vai trò là ngưỡng tham chiếu cơ sở thông qua hai biến thể: xếp hạng theo tổng lượt đánh giá và xếp hạng theo điểm trung bình có trọng số Bayes. Trong đó, biến thể trọng số Bayes kết hợp số lượt tương tác của từng bộ phim với điểm đánh giá trung bình toàn cục thông qua tham số làm mượt tiên nghiệm. Cơ chế này ngăn chặn hiện tượng các tác phẩm có quá ít lượt đánh giá nhưng đạt điểm số tuyệt đối chiếm lĩnh danh sách gợi ý. Mặc dù không chứa đựng yếu tố cá nhân hóa, phương pháp phổ biến thể hiện tính bền vững cao trên không gian xếp hạng toàn thư mục và đóng vai trò là giải pháp dự phòng cuối cùng khi hệ thống đối mặt với người dùng hoàn toàn mới.

Phương pháp lọc cộng tác được hiện thực hóa thông qua thuật toán phân rã ma trận luân phiên phân tán trên nền tảng Apache Spark MLlib, vận hành trực tiếp trên dữ liệu phản hồi tường minh của toàn bộ tập huấn luyện. Quá trình tối ưu hóa ánh xạ người dùng và tác phẩm điện ảnh vào một không gian nhân tố ẩn có cùng số chiều, từ đó dự đoán điểm số thông qua tích vô hướng của hai vector đại diện. Sau quá trình tinh chỉnh siêu tham số trên phân vùng thẩm định độc lập, mô hình tối ưu được lựa chọn với số chiều ẩn bằng 8 và hệ số điều chuẩn bằng 0.3. Nhằm phục vụ kiểm thử xếp hạng chính xác, thuật toán sinh ứng viên áp dụng cơ chế lọc trước các phim đã xem và tính toán ma trận theo lô thông qua phép nhân ma trận tối ưu hóa, bảo đảm tính tất định và triệt tiêu sai số cắt tỉa.

Nhằm kết hợp ưu thế tìm kiếm ngữ nghĩa của đồ thị tri thức và không gian tiềm ẩn của lọc cộng tác, hệ thống mở rộng phân hệ gợi ý lai ghép theo hai chiến lược dung hợp ứng viên. Chiến lược thứ nhất áp dụng thuật toán dung hợp thứ hạng nghịch đảo Cormack với hằng số làm mịn cố định bằng 60, vận hành dựa trên vị trí thứ tự thay vì biên độ điểm số thô nhằm triệt tiêu chênh lệch thang đo giữa hai mô hình thành phần. Chiến lược thứ hai áp dụng cơ chế tổ hợp tuyến tính điểm số có chuẩn hóa cực trị độc lập kèm chính sách nội suy cho các ứng viên không thuộc tập giao. Cả hai giải pháp lai ghép đều duy trì nguyên tắc lọc phim đã xem đa tầng và bảo toàn toàn vẹn các cấu trúc bằng chứng phục vụ giải thích đề xuất.

---

## PHẦN E — BỘ CÂU HỎI PHẢN BIỆN HỌC THUẬT VÀ GIẢI ĐÁP

### Câu hỏi 1: Vì sao cần triển khai Popularity khi hệ thống đã có Knowledge Graph tiên tiến?
**Trả lời dựa trên mã nguồn và thực nghiệm:**
- *Cơ sở khoa học:* Trong nghiên cứu hệ thống gợi ý, Popularity là **ngưỡng cơ sở bắt buộc (sanity-check baseline)**. Nếu một mô hình học máy phức tạp không vượt qua được Popularity thì mô hình đó chưa chứng minh được giá trị thực tế.
- *Thực tế thực nghiệm:* Trên tập kiểm thử MovieLens 25M gồm 111.211 người dùng ([m08_test_benchmark_results.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m08/m08_test_benchmark_results.json#L43-L49)), `M03_POPULARITY_COUNT` đạt $\text{HR@10} = 5.36\%$ và $\text{NDCG@10} = 0.0272$. Đây là một mốc so sánh rất mạnh mà mô hình Spark ALS thuần không thể vượt qua.
- *Vai trò kỹ thuật:* Popularity là tuyến phòng thủ cuối cùng (fallback) khi cả ALS và KG đều rơi vào trạng thái người dùng mới hoàn toàn (cold-start) chưa có bất kỳ mắt xích liên kết nào.

### Câu hỏi 2: Đề tài tập trung vào Knowledge Graph, tại sao lại phải đầu tư xây dựng Spark ALS phân tán phức tạp?
**Trả lời dựa trên mã nguồn và thực nghiệm:**
- *Tính toàn diện của nghiên cứu:* Spark ALS đại diện cho trường phái Lọc cộng tác ma trận ẩn (Matrix Factorization) — chuẩn mực công nghiệp thống trị suốt hơn một thập kỷ qua trên tập dữ liệu MovieLens. Việc đặt KG lên bàn cân đối đầu trực tiếp với Spark ALS trên cùng một tập dữ liệu phân vùng chuẩn là minh chứng khoa học khách quan nhất.
- *Nguồn bổ trợ biểu diễn:* Vector nhân tố ẩn của ALS ($8$ chiều) khai thác các mối quan hệ ngầm (latent patterns) xuyên suốt ma trận thưa mà các đường đi đồ thị tường minh (Metapaths P1–P3) chưa bao phủ hết, đóng vai trò là một nguồn sinh ứng viên độc lập cho Khối 4 Hybrid.

### Câu hỏi 3: Phân biệt sự khác nhau bản chất giữa Spark ALS và Metapath P3 (Collaborative Graph)?
**Trả lời dựa trên mã nguồn:**
- **Spark ALS** ([trainer.py:48-55](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py#L48-L55)): Tối ưu hóa toàn cục phi tuyến tính, nén toàn bộ không gian tương tác vào một không gian vector liên tục chiều thấp ($k=8$). Mối liên hệ giữa hai người dùng được biểu diễn gián tiếp qua góc hình học giữa hai vector, mang tính chất hộp đen và không thể truy vết đường đi cụ thể.
- **Metapath P3 (Collaborative Graph)** ([scorer.py:157-197](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L157-L197)): Khai phá cục bộ dựa trên mạng lưới đồng xuất hiện trực tiếp (Co-occurrence Network) qua độ đo Salton Cosine trên tập các phim cùng thích. Mối quan hệ được biểu diễn bằng đường đi cấu trúc rõ ràng: $\text{User} \to \text{Liked Movie} \leftarrow \text{Neighbor User} \to \text{Candidate Movie}$, có khả năng truy xuất định danh người dùng láng giềng và giải thích tường minh.

### Câu hỏi 4: Tại sao hệ thống phải cung cấp cả hai chiến lược dung hợp RRF và Weighted Score Fusion?
**Trả lời dựa trên mã nguồn:**
- *Khác biệt về giả định toán học:*
  - **RRF ($k=60$)** ([fusion.py:58-82](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L58-L82)): Không phụ thuộc vào phân phối điểm số (Scale-Invariant). Điểm số ALS (thường bùng nổ lên $8.0 - 12.5$) và điểm số KG ($0.2 - 2.5$) không cần phải điều chỉnh hay chuẩn hóa mà chỉ dựa vào thứ hạng tương đối. RRF có ưu thế triệt tiêu hoàn toàn nhiễu đuôi dài điểm cao đột biến của ALS.
  - **Weighted Score Fusion** ([fusion.py:162-179](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/fusion.py#L162-L179)): Giữ lại độ lớn khoảng cách chênh lệch điểm số (Score Margin) sau chuẩn hóa Min-Max, cho phép người vận hành can thiệp trực tiếp vào tỷ trọng mong muốn giữa hai mô hình thông qua tham số $w_{\text{ALS}}$ và $w_{\text{KG}}$.

### Câu hỏi 5: Nếu kết quả thực nghiệm cho thấy Hybrid không vượt qua KG thuần thì nghiên cứu này có bị xem là thất bại không?
**Trả lời dựa trên mã nguồn và thực nghiệm:**
- *Không hề thất bại, đây là một phát hiện học thuật trung thực và có giá trị cao:*
  - Báo cáo kiểm toán [HYBRID_FUSION_RESEARCH.md](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/audits/HYBRID_FUSION_RESEARCH.md) chỉ ra rõ: Trong bài toán xếp hạng trên toàn bộ thư mục (Full-Catalog Ranking với hơn 58.000 phim chưa xem), mô hình ALS phân rã ma trận bị thiên lệch cực nặng về các vật phẩm cực đuôi dài (phim chỉ có $1$ lượt rating trong Train chiếm tới $95.76\%$ số vị trí đề xuất do vector norm bị kéo dãn).
  - Do đó, khi kết hợp với ALS, tín hiệu của ALS đóng vai trò như một nguồn nhiễu số học kéo tụt độ chính xác của KG.
  - Việc công bố trung thực kết quả này khẳng định tính ưu việt của Knowledge Graph trong việc kiểm soát phân phối ngữ nghĩa và hạn chế thiên lệch đuôi dài so với các phương pháp phân rã ma trận cổ điển.

### Câu hỏi 6: Tại sao lại chọn cấu hình trọng số $w_{\text{ALS}}=0.1, w_{\text{KG}}=0.9$ trên tập Thẩm định và có nguy cơ bị overfitting không?
**Trả lời dựa trên mã nguồn và thực nghiệm:**
- *Cơ sở lựa chọn:* Kết quả quét lưới trên tập Validation ([hybrid_validation_results.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/phase4/hybrid_validation_results.json#L97-L121)) cho thấy khi $w_{\text{ALS}} \ge 0.5$, $\text{HR@10}$ sụt giảm nghiêm trọng từ $9.86\%$ xuống $4.23\%$ rồi về $0.0\%$. Điểm $0.1 / 0.9$ là điểm cân bằng thực nghiệm nơi mô hình duy trì được $\text{HR@10} = 9.86\%$, $\text{HR@20} = 15.49\%$ và độ phủ danh mục đạt đỉnh $276$ phim.
- *Nguy cơ Overfitting:* Việc chọn trọng số diễn ra trên phân vùng Thẩm định (Validation split) độc lập, hoàn toàn cách ly với phân vùng Kiểm thử (Test split) thông qua chốt chặn an toàn `guard_test_split_access` ([tuner.py:57-66](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/tuner.py#L57-L66)), do đó tuân thủ chuẩn mực phương pháp luận nghiên cứu và không bị rò rỉ dữ liệu sang tập Test.

---

## PHẦN F — RÀ SOÁT ĐỘ CHÍNH XÁC VÀ TRÁNH NHẦM LẪN

1. **Phân biệt cấu hình ALS mặc định trong mã nguồn và Champion Model thực tế:**
   - Trong file code `ALSConfig` ([trainer.py:59-61](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py#L59-L61)), cấu hình mặc định khởi tạo là `rank = 16, reg_param = 0.1, max_iter = 10`.
   - Nhưng mô hình Champion Model chính thức được lựa chọn qua tuning và lưu trong artifact `best_als_model_manifest.json` là **`rank = 8, reg_param = 0.3, max_iter = 10`** (`ALS_R8_REG0.3_ITER10`). Khi viết báo cáo phải ghi rõ cấu hình Champion Model này.

2. **Khẳng định rõ ràng: ALS sử dụng Explicit Feedback chứ không phải Implicit Feedback:**
   - Trong `ALSConfig`, biến `implicit_prefs = False` ([trainer.py:62](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/trainer.py#L62)).
   - Dữ liệu MovieLens 25M được huấn luyện dựa trên số sao đánh giá thực tế từ $0.5$ đến $5.0$, không phải ma trận nhị phân tương tác xem/click.

3. **Phân biệt cấu hình Hybrid mặc định phục vụ và cấu hình tối ưu thực nghiệm:**
   - Trong tệp cấu hình runtime `HybridConfig` ([config.py:18-19](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/config.py#L18-L19)), hệ thống đặt trọng số mặc định là `weight_als = 0.5, weight_kg = 0.5` và chiến lược mặc định là `default_fusion_strategy = "rrf"`.
   - Tuy nhiên, trong phân tích thực nghiệm thẩm định ([HYBRID_FUSION_RESEARCH.md:60](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/audits/HYBRID_FUSION_RESEARCH.md#L60)), cấu hình trọng số tốt nhất được chứng minh là **`w_ALS = 0.1, w_KG = 0.9`**. Tuyệt đối không đánh đồng hai cấu hình này.

4. **Phân biệt quy mô của tập Validation Pilot và Frozen Test Benchmark:**
   - Kết quả trong `hybrid_validation_results.json` được đo đạc trên tập **Validation pilot cohort gồm 100 người dùng** (trong đó có 71 người dùng có mục tiêu dương $\ge 3.5$).
   - Kết quả trong `m08_test_benchmark_results.json` được đo đạc trên toàn bộ **Frozen Test cohort gồm 111.211 người dùng**. Không được trộn lẫn số liệu phần trăm giữa hai tập này.

---

## PHẦN G — GIỚI HẠN VÀ ĐIỂM CHƯA XÁC MINH

1. **Hiện tượng bùng nổ điểm số tích vô hướng của Spark ALS (Unbounded Prediction Fluke):**
   - Mã nguồn không thực hiện thao tác cắt chặn giá trị dự đoán (clipping). Vector nhân tố của các phim có $1$ lượt rating trong Train bị trôi dạt trong quá trình luân phiên, khiến điểm dự đoán $\hat{r}_{ui}$ đạt tới $12.50$ (vượt xa thang đo $5.0$). Đây là nguyên nhân cốt lõi khiến ALS thuần chỉ đạt $\text{HR@10} = 0.000009$ trên Full-Catalog Ranking.

2. **Chưa thực hiện đánh giá Hybrid quy mô lớn trên toàn bộ 111.211 users của tập Test:**
   - Trong khi ALS và Popularity đã có báo cáo đo lường toàn diện trên 111.211 users ở mốc kiểm thử M08 ([m08_test_benchmark_results.json](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m08/m08_test_benchmark_results.json)), phân hệ Hybrid mới chỉ dừng lại ở kết quả thẩm định trên cohort 100 users của tập Validation. Chưa có tệp kết quả chạy full Test cho Hybrid trong thư mục artifacts.

3. **Tính năng ALS Cross-scoring cho ứng viên KG mặc định bị tắt:**
   - Trong `HybridConfig` ([config.py:25](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/config.py#L25)), cờ `cross_score_als` mặc định là `False`. Điều này có nghĩa là các ứng viên sinh ra từ KG thông thường sẽ không được tính điểm tích vô hướng ALS bổ sung trừ khi biến môi trường được kích hoạt thủ công.
