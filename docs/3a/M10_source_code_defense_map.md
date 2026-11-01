# BẢN ĐỒ BẢO VỆ MÃ NGUỒN (SOURCE CODE DEFENSE MAP) – MODULE M10
# Hướng Dẫn Trả Lời Trực Tiếp Trên Từng Dòng Code – Task 3A Spark ALS

- **Dự án:** MoodGraph – Recommender System (Spark ALS & Knowledge Graph)
- **Module:** M10 – Final ALS Delivery & Hybrid Integration Contract
- **Branch:** `feature/als-3a`
- **Mục tiêu:** Bản đồ tra cứu nhanh vị trí mã nguồn, cấu trúc thuật toán và kịch bản thuyết trình bảo vệ 5 phút trước hội đồng phản biện.

---

## 1. Bản Đồ Tọa Độ File Mã Nguồn Cốt Lõi

| Thành phần | Đường dẫn File | Số dòng | Chức năng chính |
| :--- | :--- | :--- | :--- |
| **Delivery API** | [delivery.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py) | 443 | Inference Service, Top-K Vector BLAS, Seen Masking, Cold-Start Contract |
| **Execution Runner** | [run_m10_delivery.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_m10_delivery.py) | 366 | Real-model Smoke Tests, 8 Machine Artifacts, Checklist 25 Gates |
| **Test Suite M10** | [test_delivery.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/tests/als/test_delivery.py) | 407 | 20 Unit, Integration, Adversarial & Consumer Contract Tests |
| **Integration Contract** | [integration_contract.md](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/docs/3a/integration_contract.md) | 160 | Hợp đồng tích hợp Candidate Union & cấm cộng điểm thô |
| **Audit Script** | [audit_m10_release.py](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/scripts/audit_m10_release.py) | ~200 | Script tự động thẩm tra 25 Gates, Artifacts và Regex Typography |

---

## 2. Chi Tiết Tọa Độ Dòng Code Trong `recommender/als/delivery.py`

### 2.1 Cấu trúc Dữ liệu Đầu ra (`ALSRecommendationItem`)
- **Tọa độ:** [delivery.py#L49-L80](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py#L49-L80)
- **Điểm mấu chốt khi bảo vệ:**
  - `@dataclass(frozen=True)` (Dòng 50): Bất biến 100%, bảo đảm Thread-Safety khi truyền qua các pipeline song song.
  - `userId: int`, `movieId: int` (Dòng 52-53): Định danh nguyên thủy chuẩn 64-bit của MovieLens 25M, hoàn toàn độc lập với chỉ số nội bộ 32-bit `user_idx`, `movie_idx`.
  - `raw_score: float` (Dòng 54): Điểm số thô tích vô hướng, không giả lập xác suất hay bị bóp méo.
  - `model_version: str` (Dòng 57): Truy xuất nguồn gốc mô hình (Provenance Tracking).

### 2.2 Quản trị Đăng ký Mô hình (`ALSModelRegistry`)
- **Tọa độ:** [delivery.py#L101-L153](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py#L101-L153)
- **Điểm mấu chốt khi bảo vệ:**
  - Danh mục mô hình đóng băng `_REGISTRY` (Dòng 104-124) ghi nhận chính xác `ALS_R8_REG0.3_ITER10` tại `artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10` với đầy đủ siêu tham số rank=8, regParam=0.3, maxIter=10.
  - Phương thức `get_default_model_id()` (Dòng 137-140) luôn trả về đúng `ALS_R8_REG0.3_ITER10`.

### 2.3 Quản lý Bộ nhớ & Tải Lười Lịch sử Đã xem (`ALSDeliveryService`)
- **Tọa độ:** [delivery.py#L155-L256](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py#L155-L256)
- **Điểm mấu chốt khi bảo vệ:**
  - `_get_train_seen()` (Dòng 202-218): Tải lười (lazy-load) từ `seen_movies_sample.json` hoặc ánh xạ tương tác Train, chuyển thành `Dict[int, Set[int]]` trong RAM để tra cứu `O(1)`.
  - Hỗ trợ cô lập giai đoạn đánh giá (`stage="train"` vs `stage="test"`) tại [delivery.py#L239-L256](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py#L239-L256) ngăn ngừa Data Leakage.

### 2.4 Thuật toán Tính điểm & Chọn Top-K Hiệu năng Cao
- **Tọa độ:** [delivery.py#L258-L280](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py#L258-L280) (Hàm `recommend`)
- **Điểm mấu chốt khi bảo vệ:**
  - **Cold-Start Handling** (Dòng 267-269):
    ```python
    if user_id not in self.user_id_to_idx:
        return []
    ```
    Khẳng định hợp đồng trả về rỗng minh bạch cho người dùng chưa từng tương tác.
  - **Batch Dot-Product via BLAS** (Dòng 275):
    Gọi `scores = user_vector @ self.item_factors.T` thực hiện nhân vector ma trận trên BLAS đa luồng, tính điểm 58.932 phim trong dưới 0.3 mili-giây.
  - **Seen Masking & Top-K Partition** (Dòng 278-280):
    Gán `scores[seen_indices] = -np.inf`, sau đó dùng `np.argpartition` để tách K phần tử lớn nhất với độ phức tạp `O(N)` thay vì `O(N log N)`.

### 2.5 Hàm Công Khai (Public API)
- **Tọa độ:** [delivery.py#L366-L399](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/recommender/als/delivery.py#L366-L399) (`recommend_als`, `recommend_als_batch`)
  - Interface đơn giản, trực quan, phục vụ trực tiếp cho Hybrid Orchestrator và API Web.

---

## 3. Chi Tiết Tọa Độ Dòng Code Trong `tests/als/test_delivery.py`

| Test Case | Vị trí dòng | Ý nghĩa bảo vệ khoa học & kỹ thuật |
| :--- | :--- | :--- |
| `test_01_synthetic_delivery_oracle_basic` | L32-L57 | Xác minh thuật toán oracle trên ma trận tổng hợp |
| `test_04_recommendation_item_schema_validation` | L103-L122 | Kiểm định tính toàn vẹn kiểu dữ liệu và thuộc tính bất biến |
| `test_09_known_user_top_n_length_and_rank` | L198-L215 | Kiểm tra user thật (User 1): đủ số lượng K, rank từ 1 đến K, điểm giảm dần |
| `test_10_unknown_user_cold_start_empty` | L217-L223 | Kiểm tra cold user (User 999999999) trả về danh sách rỗng `[]` |
| `test_14_seen_filtering_guarantee` | L253-L266 | Đảm bảo 0% phim đã xem lọt vào danh sách gợi ý |
| `test_17_real_model_dot_product_alignment` | L294-L315 | Đối chiếu giá trị `raw_score` của API với phép tính toán học `dot(u, v)` trực tiếp |
| `test_18_candidate_union_contract_with_synthetic_kg` | L317-L366 | Kiểm thử tích hợp: Candidate Union giữ nguyên các phim KG-only |
| `test_19_no_forced_kg_rerank_of_als_top_20` | L368-L387 | Chứng minh nếu ép KG chỉ lọc trên Top-20 ALS sẽ làm mất hoàn toàn ứng viên KG-only |
| `test_20_no_raw_score_blending_without_normalization` | L389-L407 | Chứng minh sự thiên lệch khi cộng điểm thô và tính đúng đắn của Min-Max Normalization |

---

## 4. Kịch Bản Thuyết Trình Bảo Vệ 5 Phút Trước Hội Đồng (5-Minute Defense Script)

### Phút 1: Bối Cảnh & Đóng Băng Mô Hình
"Kính thưa Hội đồng, trong Task 3A của dự án MoodGraph, nhóm chúng em chịu trách nhiệm xây dựng nền tảng Collaborative Filtering sử dụng Spark ALS trên 24.6 triệu tương tác của MovieLens 25M. Sau khi hoàn thành việc điều chỉnh tham số tại M07 và đánh giá mù trên tập Test tại M08, mô hình champion của chúng em là `ALS_R8_REG0.3_ITER10` đã được đóng băng nguyên vẹn. Tại Sprint M10 này, mục tiêu của chúng em không phải là huấn luyện thêm mô hình, mà là đóng gói mô hình thành một Dịch vụ Suy luận cấp sản xuất và ký kết Hợp đồng Tích hợp hoàn chỉnh với nhóm Đồ thị Tri thức Task 3B."

### Phút 2: Kiến Trúc API & Tối Ưu Hiệu Năng
"Tại file `recommender/als/delivery.py`, chúng em đã xây dựng lớp dịch vụ `ALSDeliveryService`. Để đạt được độ trễ thời gian thực cho người dùng, thay vì gọi lại Spark vốn có chi phí khởi tạo JVM lớn, dịch vụ trích xuất trực tiếp ma trận trọng số sang định dạng NumPy và tận dụng thư viện BLAS đa luồng. Phép nhân ma trận vector tính điểm đồng thời cho 58.932 bộ phim chỉ mất dưới 0.3 mili-giây. Đồng thời, bằng việc kết hợp Vector Masking các phim đã xem với thuật toán `np.argpartition`, chúng em giảm độ phức tạp tìm kiếm Top-K từ O(N log N) xuống O(N), đảm bảo 0% phim đã xem xuất hiện lại trong kết quả gợi ý."

### Phút 3: Hợp Đồng Khởi Động Lạnh (Cold-Start Contract)
"Một điểm nổi bật trong thiết kế của chúng em là tính trung thực của mô hình. Khi gặp một người dùng mới (chưa có lịch sử trong tập Train), tại dòng 267 của file `delivery.py`, hàm suy luận lập tức trả về danh sách rỗng `[]`. Chúng em chủ động không chèn các phim phổ biến hay gán điểm số 0.0 giả tạo tại tầng này. Đây là thiết kế chuẩn mực theo nguyên lý Đơn trách nhiệm: ALS thừa nhận nó không có tín hiệu cá nhân hóa, và việc kích hoạt fallback sẽ do Orchestrator ở tầng trên điều phối sang Knowledge Graph hoặc Popularity."

### Phút 4: Hợp Đồng Tích Hợp Mô Hình Lai (Hybrid Integration Contract)
"Để kết nối với Task 3B, chúng em đã ban hành tài liệu `integration_contract.md`. Trong đó, chúng em quy định hai nguyên tắc sống còn:
Thứ nhất, kiến trúc phải là Hợp tập ứng viên (Candidate Union: `ALS ∪ KG`). Chúng em nghiêm cấm việc dùng KG để lọc tuần tự trên Top-20 của ALS, vì điều đó sẽ triệt tiêu toàn bộ các bộ phim ngách và phim khởi động lạnh mà đồ thị tìm ra.
Thứ hai, nghiêm cấm cộng trực tiếp điểm số thô. Do điểm thô ALS là tích vô hướng có giá trị từ 0 đến 11, trong khi điểm KG thường nằm trong khoảng [0, 1], nếu cộng trực tiếp thì ALS sẽ áp đảo 90% kết quả. Hợp đồng quy định bắt buộc phải chuẩn hóa Min-Max hoặc dùng Reciprocal Rank Fusion."

### Phút 5: Kiểm Thẩm Toàn Diện & Kết Luận
"Toàn bộ các quy tắc và hợp đồng trên không chỉ nằm trên tài liệu, mà đã được kiểm chứng tự động qua 20 tests mới trong `test_delivery.py`, nâng tổng số test suite của Task 3A lên 180 tests PASS 100%. Tất cả 25 cổng chất lượng phát hành (Quality Gates) đã được xác nhận đạt chuẩn. Chúng em khẳng định Task 3A đã hoàn thành xuất sắc và sẵn sàng 100% để chuyển giao sang giai đoạn tích hợp mô hình lai. Xin trân trọng cảm ơn Hội đồng!"

