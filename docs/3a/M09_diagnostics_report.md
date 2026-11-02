# MOODGRAPH | KHỐI 3A | MODULE M09: BÁO CÁO KHOA HỌC CHẨN ĐOÁN VÀ HIỆU NĂNG
# COLD-START, LONG-TAIL, FACTOR RELIABILITY & SPARK PERFORMANCE BENCHMARK

**Dự án:** MoodGraph – Hệ thống gợi ý phim cá nhân hóa kết hợp Đồ thị tri thức (Knowledge Graphs) và Apache Spark  
**Nhánh Git:** `feature/als-3a`  
**Mô hình khảo sát:** `ALS_R8_REG0.3_ITER10` (Frozen Spark ALS Champion từ M07, giữ nguyên trọng số)  
**Tập dữ liệu:** MovieLens 25M (Core Movies: 62.423 phim, Train Split: 24.675.013 ratings, 162.541 users, 58.932 items)  
**Môi trường thử nghiệm:** Windows 11, AMD Ryzen 5 7530U (6 cores / 12 threads), 16 GB RAM, Python 3.12.3, PySpark 3.5.x local[*]  
**Cam kết phân giới:** Tuyệt đối không huấn luyện lại ALS, không tuning tham số, không đọc nhãn tập Test (100% Train-only diagnostics).

---

## 1. TỔNG QUAN VÀ MỤC TIÊU NGHIÊN CỨU

Tại Module M08, phép kiểm định Offline Frozen Test Benchmark đã phát hiện một hiện tượng định lượng sâu sắc:
Mô hình đường cơ sở phổ biến (Popularity Count) đạt HR@10 = 0.05357 (5.958 hits trên 111.211 users), trong khi mô hình nhân tử ma trận Spark ALS tối ưu (`ALS_R8_REG0.3_ITER10`) chỉ ghi nhận duy nhất 1 hit (HR@10 = 0.00000899).

Module M09 được triển khai độc lập nhằm trả lời 4 câu hỏi khoa học cốt lõi:
1. **Phân phối độ hỗ trợ phim (Item Support Distribution):** Catalog MovieLens 25M có đặc điểm đuôi dài (Long-Tail) như thế nào? Tỷ lệ phim Cold-Start và phim có rất ít đánh giá trong Train là bao nhiêu?
2. **Độ tin cậy của Vector tiềm ẩn (Factor Reliability):** Vector tiềm ẩn (latent factors) của các item đuôi dài có hành vi toán học ra sao dưới hàm mục tiêu ALS có điều chuẩn L2? Độ chuẩn L2 (norm) tương quan thế nào với log(support)?
3. **Phân phối điểm dự đoán và thiên lệch đuôi dài (Fluke Bias):** Điểm tích vô hướng của ALS có phân phối như thế nào? Vì sao danh sách Top-20 của pure ALS lại bị chiếm lĩnh bởi các phim ít người xem?
4. **Hiệu năng thực thi Apache Spark & NumPy BLAS:** Tách bạch thời gian thực thi và bộ nhớ RAM giữa tầng phân tán Spark DataFrame, tầng nạp cột PyArrow và tầng tính ma trận NumPy/BLAS.

---

## 2. PHÂN PHỐI ĐỘ HỖ TRỢ PHIM VÀ PHÂN TẦNG COLD-START

### 2.1. Bảo toàn Catalog trên 5 Bins Độc Lập
Toàn bộ 62.423 phim trong catalog MovieLens 25M được phân hoạch vào đúng 5 khoảng hỗ trợ không giao nhau dựa trên số lượng đánh giá thực tế trong tập Train (24.675.013 ratings):

```text
Tổng Catalog = Bin(0) + Bin(1-5) + Bin(6-10) + Bin(11-50) + Bin(>50)
62.423 = 3.491 + 28.834 + 6.838 + 10.234 + 13.026
```

Bảng phân phối chi tiết (trích xuất từ [item_support_distribution.csv](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m09/item_support_distribution.csv)):

| Tên phân vùng (Bin) | Ngưỡng hỗ trợ (Train) | Số lượng phim | Tỷ lệ Catalog (%) | Support trung bình | Support trung vị | Min Support | Max Support |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0 ratings (Unscoreable)** | [0, 0] | 3.491 | 5.5925% | 0.00 | 0.0 | 0 | 0 |
| **1-5 ratings (Extreme Tail)** | [1, 5] | 28.834 | 46.1913% | 2.31 | 2.0 | 1 | 5 |
| **6-10 ratings (Low Support)** | [6, 10] | 6.838 | 10.9543% | 7.66 | 7.0 | 6 | 10 |
| **11-50 ratings (Medium)** | [11, 50] | 10.234 | 16.3946% | 23.42 | 20.0 | 11 | 50 |
| **>50 ratings (Head / Popular)**| [51, inf) | 13.026 | 20.8673% | 1.866.75 | 324.0 | 51 | 80.448 |
| **TỔNG TOÀN BỘ CATALOG** | [0, inf) | **62.423** | **100.0000%** | **395.29** | **5.0** | **0** | **80.448** |

### 2.2. Phát hiện Định lượng về Đuôi Dài (VERIFIED_FACT)
- **51.78% Catalog thuộc diện Cold-Start nặng / Cực ít tương tác:** Tổng cộng 32.325 phim (3.491 phim có 0 rating + 28.834 phim có từ 1 đến 5 ratings) chiếm hơn một nửa kho phim.
- **Tính thưa thớt khốc liệt:** 58.932 phim có mặt trong Train trên tổng số 162.541 người dùng tương đương mật độ ma trận chỉ đạt:
  `24.675.013 / (162.541 * 58.932) ≈ 0.2576%`.
- **Phân tầng hoạt động người dùng trong Train:**
  - Nhóm Light (<= 20 ratings): 11.129 users (6.85%).
  - Nhóm Medium (21-100 ratings): 89.592 users (55.12%).
  - Nhóm Heavy (> 100 ratings): 61.820 users (38.03%).

---

## 3. PHÂN TÍCH ĐỘ TIN CẬY CỦA VECTOR TIỀM ẨN (FACTOR RELIABILITY)

### 3.1. Phân phối Độ chuẩn L2 (Norms) của Factors
Khảo sát toàn bộ 58.932 item factors (rank=8) và 162.541 user factors (rank=8) của mô hình `ALS_R8_REG0.3_ITER10`:

| Thực thể (Entity) | Số lượng | Chiều (Rank) | Min Norm | Max Norm | Mean Norm | Median Norm | Std Norm | P90 Norm | P95 Norm | P99 Norm |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Item Factors (Q_i)** | 58.932 | 8 | 0.205798 | 4.128926 | 1.681944 | 1.730172 | 0.358374 | 2.052672 | 2.140130 | 2.389765 |
| **User Factors (P_u)** | 162.541 | 8 | 0.230200 | 3.037728 | 1.812377 | 1.822677 | 0.215210 | 2.063722 | 2.137824 | 2.292200 |

### 3.2. Mối tương quan giữa Độ hỗ trợ (Support) và Độ chuẩn Vector
- Hệ số tương quan Pearson giữa `log1p(support)` và `norm(Q_i)`: **r = +0.157360** (p-value = 3.0e-323, có ý nghĩa thống kê do cỡ mẫu lớn N = 58.932; tuy nhiên kích thước hiệu ứng ở mức khiêm tốn / modest effect size, phản ánh xu hướng tổng thể nhưng không phải mối quan hệ tuyến tính tuyệt đối).
- Hệ số tương quan hạng Spearman: **ρ = +0.144029** (p-value = 1.29e-270).

### 3.3. So sánh Norm giữa các tầng hỗ trợ
```text
Bin 1-5 ratings  (count=28.834): mean_norm = 1.6292, median_norm = 1.6828, min = 0.2058, max = 4.1289
Bin 6-10 ratings (count= 6.838): mean_norm = 1.6940, median_norm = 1.7283, min = 0.2795, max = 2.4901
Bin 11-50 ratings(count=10.234): mean_norm = 1.7245, median_norm = 1.7554, min = 0.3782, max = 2.3894
Bin >50 ratings  (count=13.026): mean_norm = 1.7589, median_norm = 1.7955, min = 0.5820, max = 2.3361
```

**Bình luận khoa học:**
1. Các phim trong nhóm Head (`>50 ratings`) có norm rất ổn định: min norm là 0.5820 và max norm là 2.3361.
2. Ngược lại, nhóm Extreme Tail (`1-5 ratings`) có phương sai độ chuẩn cực lớn: min norm sụt giảm xuống 0.2058 (bị co mạnh về gốc tọa độ do regularization `regParam=0.3`), nhưng max norm lại vọt lên tận 4.1289!
3. Những phim chỉ có đúng 1 lượt đánh giá 5.0 sao rất dễ bị "thổi phồng" độ chuẩn khi thuật toán ALS xoay vector để khớp điểm số duy nhất đó mà không bị ràng buộc bởi các rating khác.

---

## 4. PHÂN PHỐI ĐIỂM SỐ DỰ ĐOÁN VÀ THIÊN LỆCH ĐUÔI DÀI (LONG-TAIL FLUKE BIAS)

### 4.1. Phân phối điểm số trên Cohort chuẩn 1.000 users x 58.932 items
Đo đạc thực nghiệm trên 58.932.000 cặp `(u, i)` tích vô hướng:
- Min score: **0.078379**
- Max score: **10.837794** (Vượt xa thang điểm chuẩn [0.5, 5.0] của MovieLens)
- Mean score: **2.986515**
- Median score: **3.051305**
- Độ lệch chuẩn (Std): **0.744461**
- Tỷ lệ điểm < 0.0: **0.0000%** (Do regularization và implicit bias tự nhiên)
- Tỷ lệ điểm > 5.0: **0.2808%** (Khoảng 165.481 cặp điểm vượt ngưỡng trần 5.0)

### 4.2. Khảo sát Top-K Recommendations trên 5.000 Users Cohort
Tạo Top-20 gợi ý sau khi đã lọc bỏ toàn bộ tương tác đã xem trong Train:

| Chỉ số khảo sát | Top-10 Recommendations | Top-20 Recommendations |
| :--- | :---: | :---: |
| Tổng số lượt gợi ý phát sinh | 50.000 | 100.000 |
| Số lượng phim độc nhất được gợi ý | **23 phim** | **45 phim** |
| Độ phủ danh mục Catalog Coverage (%) | **0.0368%** | **0.0721%** |
| **Tỷ lệ phim có đúng 1 rating trong Train** | **100.00%** | **95.81%** |
| **Tỷ lệ phim có từ 1 đến 5 ratings trong Train** | **100.00%** | **100.00%** |
| **Tỷ lệ phim có > 50 ratings trong Train** | **0.00%** | **0.00%** |

### 4.3. NGUYÊN NHÂN GỐC RỄ KHOA HỌC (SCIENTIFIC ROOT CAUSE)
Kết quả trên chứng minh một cách không thể chối cãi nguyên nhân vì sao ALS đạt HR@10 gần như bằng 0 trên Test tại M08:
1. **Thiên lệch ngẫu nhiên đuôi dài (Long-Tail Fluke Bias):** Mô hình Pure ALS không có cơ chế phạt tần suất (frequency penalty) hay hiệu chỉnh độ phổ biến (popularity prior). Một bộ phim vô danh chỉ có 1 rating 5.0 trong Train sẽ sinh ra một vector `Q_i` có norm lớn (lên tới 4.13) và góc định hướng hẹp. Khi nhân vô hướng với hàng ngàn user vectors có chiều tương tự, điểm số dự đoán bị thổi phồng lên 8.0 đến 10.8!
2. **Chiếm lĩnh hoàn toàn Top-K:** 100% Top-10 gợi ý của ALS cho 5.000 users chỉ xoay quanh đúng 23 bộ phim vô danh này.
3. **Thực tế tập Test:** Tập Test chứa các đánh giá của người dùng thực tế. Người dùng thực tế hầu như chỉ xem các phim có độ nhận diện nhất định (Head và Mid-tier). Khi ALS chỉ gợi ý 23 bộ phim vô danh có 1 rating, xác suất người dùng Test tình cờ xem trúng phim đó gần như bằng 0 (chỉ đúng 1 hit trên 111.211 users).
4. **Vì sao Popularity chiến thắng:** Popularity gợi ý các phim được hàng chục ngàn người xem (ví dụ The Shawshank Redemption, Forrest Gump), do đó trùng khớp với hành vi thực tế của 5.958 người dùng Test (HR@10 = 5.36%).

---

## 5. THỰC NGHIỆM ĐO ĐẠC HIỆU NĂNG TÁCH BẠCH (PERFORMANCE BENCHMARKS)

Toàn bộ các phép đo hiệu năng được thực hiện trong môi trường độc lập, đo đạc thời gian tính toán và bộ nhớ RAM chiếm dụng thực tế (trích xuất từ [performance_benchmarks.csv](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m09/performance_benchmarks.csv)):

| Thành phần (Component) | Thao tác (Operation) | Quy mô | Thời gian (s) | Độ trễ (Latency) | Thông lượng (Throughput) | Peak RAM RSS | Ghi chú kỹ thuật |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **PyArrow** | Columnar Parquet Read | 24.67M ratings | 0.65s | 645.1 ms | **38.248.481 rows/s** | 382.0 MB | Zero-copy batch deserialization từ 8 snappy parquet |
| **NumPy BLAS** | Batch Scoring (batch=1) | 1 user | 0.0001s | 0.11 ms | **9.499 users/s** | 162.2 MB | Tích ma trận: (1, 8) @ (8, 58932) |
| **NumPy BLAS** | Batch Scoring (batch=100) | 100 users | 0.0091s | 9.06 ms | **11.042 users/s** | 184.9 MB | Tích ma trận: (100, 8) @ (8, 58932) |
| **NumPy BLAS** | Batch Scoring (batch=500) | 500 users | 0.0495s | 49.49 ms | **10.103 users/s** | 274.9 MB | Tích ma trận: (500, 8) @ (8, 58932) |
| **NumPy BLAS** | Batch Scoring (batch=2500)| 2.500 users | 0.2820s | 282.04 ms | **8.864 users/s** | **724.6 MB** | Đỉnh RAM 724.6 MB, nằm an toàn dưới trần 1.200 MB |
| **PySpark DataFrame** | Read & Count Partition Scan | 24.67M ratings | 3.98s | 3.979.5 ms | **6.200.519 rows/s** | 1.045.7 MB | Phân tán 12 partitions trên JVM local[*] |
| **PySpark DataFrame** | GroupBy movieId Count Agg | 24.67M ratings | 1.82s | 1.818.2 ms | **13.571.396 rows/s**| 1.045.7 MB | Hash aggregation phân tán trên 58.932 items |

### Nhận định Hiệu năng Kỹ thuật
1. **PyArrow vượt trội ở tầng I/O:** Nạp 24.675.013 bản ghi chỉ mất 0.65 giây (đạt trên 38 triệu bản ghi/giây) với RAM chỉ 382 MB nhờ kiến trúc bộ nhớ cột zero-copy.
2. **NumPy BLAS đạt đỉnh thông lượng ở batch 100 - 500:** Đạt trên 11.000 users/giây. Ở batch 2.500 users, tốc độ đạt 8.864 users/giây, bộ nhớ đỉnh 724.6 MB hoàn toàn tuân thủ giới hạn an toàn 1.2 GB của hệ thống 16 GB RAM.
3. **PySpark tối ưu cho biến đổi phân tán:** Khả năng GroupBy và đếm 24.67 triệu dòng trong 1.82 giây thể hiện sức mạnh phân tán của Catalyst Optimizer trên AMD Ryzen 5 7530U.

---

## 6. DANH MỤC 16 TIÊU CHÍ NGHIỆM THU CHẤT LƯỢNG (16 QUALITY GATES)

Toàn bộ 16 tiêu chí tại [m09_release_checklist.json](file:///d:/PROJECT%20BIG%20DATA/MoodGraph/artifacts/als/m09/m09_release_checklist.json) đều đạt trạng thái **PASS**:

- `GATE_01_NO_RETRAIN`: PASS – Mô hình ALS giữ nguyên trọng số, không huấn luyện lại.
- `GATE_02_NO_TEST_LEAKAGE`: PASS – 100% chẩn đoán chỉ sử dụng dữ liệu Train và Catalog core.
- `GATE_03_CATALOG_CONSERVATION`: PASS – Tổng số item qua 5 bins bảo toàn chính xác 62.423 phim.
- `GATE_04_UNSCOREABLE_ITEMS_AUDITED`: PASS – Xác định đúng 3.491 phim (5.5925%) có 0 rating trong Train.
- `GATE_05_FACTOR_NORMS_VERIFIED`: PASS – Tính toán đầy đủ thống kê độ chuẩn L2 cho item và user factors.
- `GATE_06_SUPPORT_CORRELATION_VERIFIED`: PASS – Tương quan Pearson dương (r = +0.1574) có ý nghĩa thống kê.
- `GATE_07_SCORE_DISTRIBUTION_COMPUTED`: PASS – Phân phối điểm số được tính toán trên 58.932.000 cặp.
- `GATE_08_EXTREME_SCORES_QUANTIFIED`: PASS – Lượng hóa chính xác điểm số > 5.0 (0.2808%).
- `GATE_09_TOPK_SUPPORT_CONCENTRATION`: PASS – Khảo sát nồng độ Top-20 chỉ ra 95.81% phim có support == 1.
- `GATE_10_PYARROW_BENCHMARK`: PASS – Đo đạc độc lập PyArrow nạp 24.67M dòng trong 0.65s.
- `GATE_11_SPARK_DATAFRAME_BENCHMARK`: PASS – Đo đạc Spark DataFrame count (3.98s) và groupBy (1.82s).
- `GATE_12_BLAS_SCORING_BENCHMARK`: PASS – Đo đạc NumPy BLAS qua 4 mức batch size, thông lượng > 8.800 users/s.
- `GATE_13_PEAK_MEMORY_BOUNDED`: PASS – Đỉnh RAM ma trận 724.6 MB, thấp hơn trần quy định 1.200 MB.
- `GATE_14_INDEPENDENT_SYNTHETIC_ORACLES`: PASS – 4 hàm chuẩn độc lập đạt 100% trong bộ test.
- `GATE_15_MACHINE_READABLE_ARTIFACTS`: PASS – Đầy đủ 10/10 artifacts trong thư mục `artifacts/als/m09/`.
- `GATE_16_NO_DOWNSTREAM_OR_CROSS_TASK_CONTAMINATION`: PASS – Không chỉnh sửa Task 3B, KG, hay M10.

---

## 7. KẾT LUẬN VÀ KHUYẾN NGHỊ CHO KHỐI HYBRID RECOMMENDATION

1. **Kết luận khoa học:** Module M09 đã hoàn thành xuất sắc sứ mệnh giải mã bản chất toán học và thực nghiệm của mô hình Collaborative Filtering trên dữ liệu quy mô lớn MovieLens 25M. Mâu thuẫn giữa hàm mục tiêu RMSE của ALS và độ đo xếp hạng Top-N trên tập Test đã được làm sáng tỏ bằng bằng chứng định lượng không thể phản bác.
2. **Khuyến nghị kỹ thuật cho Module tiếp theo (Task 3B & Hybrid):**
   - **Không dùng Pure ALS đơn độc:** Tuyệt đối không đưa Pure ALS vào môi trường thực tế mà không có cơ chế lọc hoặc ghép tầng.
   - **Cơ chế Hybrid Blending:** Khối tiếp theo được khuyến nghị nghiên cứu kết hợp điểm ALS với độ phổ biến (Popularity Prior) hoặc đồ thị tri thức (Knowledge Graph Path Score) nhằm giảm thiểu thiên lệch Fluke Bias ở các item ít tương tác.
   - **Ngưỡng lọc hỗ trợ tối thiểu (Support Thresholding):** Nên thiết lập ngưỡng tối thiểu (ví dụ chỉ chấm điểm ALS cho phim có support >= 10, các phim dưới 10 ratings dùng fallback tri thức hoặc thể loại).

