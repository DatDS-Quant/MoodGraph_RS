# HỒ SƠ ĐÓNG BĂNG VÀ BÀN GIAO MÔ HÌNH: M07 SANG M08 (M07-TO-M08 FREEZE MANIFEST)

- **Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị Tri thức và Apache Spark
- **Mã hồ sơ:** M07-TO-M08-FREEZE-MANIFEST
- **Module nguồn:** M07 (ALS Hyperparameter Tuning on Validation)
- **Module tiếp nhận:** M08 (Frozen-Test Benchmark vs Popularity)
- **Git Branch:** `feature/als-3a`
- **Trạng thái đóng băng:** **HOÀN TOÀN ĐÓNG BĂNG (STRICTLY FROZEN)**
- **Phán quyết nghiệm thu cuối:** **`M07_FINAL_CLOSURE_PASS`**

---

## 1. THÔNG TIN MÔ HÌNH CHIẾN THẮNG ĐƯỢC ĐÓNG BĂNG (FROZEN FINALIST MODEL)

| Thuộc tính | Giá trị đóng băng | Ghi chú kỹ thuật |
| :--- | :--- | :--- |
| **Trial ID** | `ALS_R8_REG0.3_ITER10` | Cấu hình tinh chỉnh tối ưu tại M07 |
| **Họ mô hình** | `ALS_ONLY` | Ma trận nhân tử hóa thuần túy (không dùng heuristic post-filter) |
| **Đường dẫn Artifact** | [`artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10`](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/models/als/m07_tuning/ALS_R8_REG0.3_ITER10) | Mô hình Spark MLlib ALSModel đã huấn luyện hoàn tất |
| **Số chiều ẩn (rank)** | **8** | Tối giản độ phức tạp bộ nhớ và thời gian tính toán |
| **Hệ số phạt (regParam)** | **0.3** | Mức phạt điều chuẩn tối ưu từ giai đoạn quét siêu tham số |
| **Số vòng lặp (maxIter)** | **10** | Đảm bảo hội tụ tiêu chuẩn |
| **Implicit Prefs** | `False` | Huấn luyện điểm số tường minh (Explicit Feedback) |
| **Cold Start Strategy** | `nan` | Theo hợp đồng kiến trúc (bảo toàn mẫu số người dùng) |
| **Random Seed** | `42` | Đảm bảo tính tái lập 100% |
| **Cơ sở lựa chọn** | **Complexity-preferred finalist** | Áp dụng nguyên lý Dao cạo Occam khi tất cả cấu hình `ALS_ONLY` hòa NDCG@10 = 0 |

---

## 2. BẤT BIẾN DỮ LIỆU ĐẦU VÀO (DATASET INVARIANTS & PROVENANCE)

1. **Tập Train (splits/train):**
   - Số dòng tương tác: **24.675.013** ratings
   - Số người dùng duy nhất: **162.541** users
   - Số bộ phim có rating: **58.932** items
2. **Tập Validation (splits/validation):**
   - Tổng số người dùng kiểm định: **162.541** users
   - Số người dùng có tương tác tích cực (rating >= 3.5): **109.779** users (`positive_cohort_size`)
   - Số người dùng không có tương tác tích cực (rating < 3.5): **52.762** users
3. **Danh mục phim (core/movies):**
   - Tổng số phim trong danh mục: **62.423** movies
   - Số phim đủ điều kiện chấm điểm (scorable): **58.932** movies (có mặt trong Train)
   - Số phim không có factor (unscoreable): **3.491** movies

---

## 3. BẢNG TỔNG HỢP CHỈ SỐ KIỂM ĐỊNH ĐÃ ĐƯỢC KIỂM TOÁN CHUẨN XÁC

### 3.1. Nhóm tầm soát (Screening Cohort - 5.000 positive users, Seed 42)

| Chỉ số | Cutoff K=5 | Cutoff K=10 | Cutoff K=20 |
| :--- | :---: | :---: | :---: |
| **HitRate@K** | 0.00000 | 0.00000 | 0.00000 |
| **NDCG@K** | 0.00000 | 0.00000 | 0.00000 |
| **MRR@K** | 0.00000 | 0.00000 | 0.00000 |
| **Catalog Coverage (Full)** | 0.021% | 0.034% | 0.051% |
| **Số phim độc lập Top-K** | 13 phim | 21 phim | 32 phim |

### 3.2. Toàn bộ tập Validation tích cực (Full Validation - 109.779 positive users)

| Chỉ số | Cutoff K=5 | Cutoff K=10 | Cutoff K=20 |
| :--- | :---: | :---: | :---: |
| **HitRate@K** | 0.00000 | 0.00000 | 0.00000 |
| **NDCG@K** | 0.00000 | 0.00000 | 0.00000 |
| **MRR@K** | 0.00000 | 0.00000 | 0.00000 |
| **Catalog Coverage (Full)** | 0.026% | 0.056% | 0.101% |
| **Số phim độc lập Top-K** | 16 phim | 35 phim | 63 phim |

### 3.3. So sánh chuẩn mực với các Baseline (109.779 positive users tại K=10)

| Mô hình | HR@10 | NDCG@10 | MRR@10 | Coverage@10 | Số phim Top-10 | Nguồn đối soát |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Popularity Count (M03)** | **0.05519** | **0.02789** | 0.01970 | **0.497%** | 310 | `artifacts/m03_popularity_results.json` |
| **Popularity Weighted (M03)** | **0.01969** | **0.00771** | 0.00416 | **0.074%** | 46 | `artifacts/m03_popularity_results.json` |
| **Spark ALS Baseline M05 (R16, Reg0.1)** | **0.00000** | **0.00000** | 0.00000 | **2.475%** | 1.545 | `artifacts/als/m06/m06_als_evaluation_results.json` |
| **Spark ALS Finalist M07 (R8, Reg0.3)** | **0.00000** | **0.00000** | 0.00000 | **0.056%** | 35 | `artifacts/als/m07/best_als_model_manifest.json` |

---

## 4. HỢP ĐỒNG GỢI Ý VÀ LỌC PHIM ĐÃ XEM (SEEN-ITEM FILTERING CONTRACT)

1. **Nguyên tắc bất biến:** Không bao giờ gợi ý cho người dùng những bộ phim họ đã tương tác trong tập Train (`data/processed/splits/train`).
2. **Cơ chế kỹ thuật:** Áp dụng chiến lược **Exact Filter-Before-Top-K**: gán điểm số của toàn bộ phim đã xem trong Train thành `-inf` trước khi thực hiện phân đoạn `argpartition` tìm Top-K.
3. **Quy tắc phá hòa (Tie-Breaking):** `als_score DESC`, sau đó `movieId ASC` để bảo đảm tính tất định 100%.

---

## 5. CÁC QUY TẮC CÁCH LY BẮT BUỘC KHI CHUYỂN SANG MODULE M08

Khi bước vào Module M08 (Frozen-Test Benchmark):
1. **Tuyệt đối cấm tinh chỉnh lại siêu tham số:** Không được thay đổi `rank`, `regParam` hay `maxIter` sau khi quan sát kết quả trên tập Test.
2. **Tuyệt đối cấm huấn luyện lại (No Retraining):** Mô hình `ALS_R8_REG0.3_ITER10` đã đóng băng phải được nạp nguyên trạng từ thư mục artifact.
3. **Đánh giá một lần duy nhất (Single-Shot Evaluation):** Tập Test chỉ được nạp để tính điểm số đối chứng cuối cùng so với Popularity Count và Popularity Weighted.
4. **Bảo toàn tính liêm chính khoa học:** Báo cáo trung thực kết quả thực nghiệm trên tập Test mà không cắt xén mẫu số hay thay đổi định nghĩa đánh giá.

