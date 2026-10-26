# Báo cáo Khám phá Dữ liệu (Exploratory Data Analysis - EDA)
## Dự án MoodGraph - Bộ dữ liệu MovieLens 25M

- **Ngày thực hiện:** 2026-10-23 20:00:49
- **Engine thực thi:** Apache Spark (PySpark DataFrame / Spark SQL)
- **Thời gian tính toán phân tán:** 66.02 giây

---

## 1. Tổng quan Bản số (Cardinality) & Độ thưa Ma trận (Matrix Sparsity)

| Chỉ số | Giá trị thực tế | Ghi chú |
| :--- | :--- | :--- |
| Tổng số tương tác ratings | 25,000,095 | ratings.csv |
| Tổng số người dùng (Users) | 162,541 | Đều có tối thiểu 20 ratings |
| Phim có tương tác rating | 59,047 | Xuất hiện trong ratings.csv |
| Tổng danh mục phim (Catalog) | 62,423 | movies.csv |
| Phim không có rating nào | 3,376 | 5.41% danh mục catalog |
| Không gian User x Movie (Active) | 9,597,558,427 | Ô tiềm năng |
| **Độ thưa ma trận (Sparsity - Active)** | **99.7395%** | Mật độ (Density) = 0.2605% |
| **Độ thưa ma trận (Sparsity - Catalog)** | **99.7536%** | Mật độ (Density) = 0.2464% |
| Bản ghi trùng cặp `(userId, movieId)` | **0** | Hoàn toàn không có duplicate |

### Nhận xét về Độ thưa (Sparsity):
- Độ thưa đạt **99.74%** (chỉ có khoảng 0.26% ô có dữ liệu). Đây là đặc trưng kinh điển của bài toán Collaborative Filtering quy mô lớn.
- Ma trận cực thưa đòi hỏi thuật toán Matrix Factorization như **Spark MLlib ALS** phải được tinh chỉnh tham số `regParam` (chống overfitting) và `rank` thích hợp, đồng thời cần cold-start strategy vững chắc cho 3,376 phim trong catalog chưa từng được đánh giá.

---

## 2. Phân bố Điểm số (Rating Distribution)

- **Điểm trung bình (Mean):** 3.5339
- **Độ lệch chuẩn (Std Dev):** 1.0607
- **Trung vị (Median):** 3.5
- **Thang điểm:** 0.5 đến 5.0 (bước nhảy 0.5)

| Mức điểm (Rating) | Số lượng tương tác | Tỷ lệ (%) | Biểu đồ thanh |
| :--- | :--- | :--- | :--- |
| 0.5 | 393,068 |  1.57% | `` |
| 1.0 | 776,815 |  3.11% | `#` |
| 1.5 | 399,490 |  1.60% | `` |
| 2.0 | 1,640,868 |  6.56% | `###` |
| 2.5 | 1,262,797 |  5.05% | `##` |
| 3.0 | 4,896,928 | 19.59% | `#########` |
| 3.5 | 3,177,318 | 12.71% | `######` |
| 4.0 | 6,639,798 | 26.56% | `#############` |
| 4.5 | 2,200,539 |  8.80% | `####` |
| 5.0 | 3,612,474 | 14.45% | `#######` |

### Nhận xét Phân bố Điểm:
- Phân bố bị lệch phải (positive skewness): Các mức điểm cao (3.0, 4.0, 5.0) chiếm đại đa số.
- Điểm 4.0 là mức điểm phổ biến nhất, chiếm tới 26.73% toàn bộ ratings.
- Xu hướng người dùng chấm điểm số nguyên (1.0, 2.0, 3.0, 4.0, 5.0) vượt trội so với các mức điểm nửa sao (0.5, 1.5, 2.5, 3.5, 4.5).
- Rating trung bình đạt 3.53/5.0, cho thấy người dùng có xu hướng chỉ chủ động đánh giá những bộ phim họ thích hoặc thấy đáng chú ý.

---

## 3. Hoạt động Người dùng & Mức độ Phổ biến của Phim (Long-tail Distribution)

### Phân vị số lượng Ratings:

| Phân vị (Percentile) | Số ratings / User | Số ratings / Movie (Active) |
| :--- | :--- | :--- |
| Min | 20 | 1 |
| p5 | 22 | 1 |
| p25 | 36 | 2 |
| **p50 (Median)** | **71** | **6** |
| p75 | 162 | 36 |
| p90 | 353 | 412 |
| p95 | 554 | 1497 |
| p99 | 1224 | 9872 |
| p99.9 | 2746 | 34188 |
| Max | 32,202 | 81,491 |
| **Mean +- Std** | **153.8 +- 268.0** | **423.4 +- 2477.9** |

### Nhận xét Phân bố Đuôi dài (Long-tail):
- **Về phía User:** Mọi user đều có tối thiểu 20 ratings (do điều kiện lọc ban đầu của GroupLens). Median là 71 ratings, nhưng user tích cực nhất có tới 32,202 ratings.
- **Về phía Movie:** Phân bố cực kỳ bất đối xứng (heavy long-tail). Median chỉ là 6 ratings/phim, trong khi phim được đánh giá nhiều nhất lên tới 81,491 ratings.
- Có tới **28,840 phim** (48.84%) chỉ có từ 1 đến 5 lượt đánh giá; **35,690 phim** (60.44%) có <= 10 lượt đánh giá.

---

## 4. Độ phủ của Thể loại (Genre), Thẻ tự do (Tags) & Tag Genome

### 4.1. Độ phủ Thể loại (Genre):
- Phim có thể loại hợp lệ: **57,361 / 62,423 (91.89%)**.
- Phim không có thể loại `(no genres listed)`: **5,062 (8.11%)**.

| Thể loại (Genre) | Số lượng phim xuất hiện | Tỷ lệ trên tổng phim (%) |
| :--- | :--- | :--- |
| Drama | 25,606 | 41.02% |
| Comedy | 16,870 | 27.03% |
| Thriller | 8,654 | 13.86% |
| Romance | 7,719 | 12.37% |
| Action | 7,348 | 11.77% |
| Horror | 5,989 |  9.59% |
| Documentary | 5,605 |  8.98% |
| Crime | 5,319 |  8.52% |
| (no genres listed) | 5,062 |  8.11% |
| Adventure | 4,145 |  6.64% |
| Sci-Fi | 3,595 |  5.76% |
| Children | 2,935 |  4.70% |
| Animation | 2,929 |  4.69% |
| Mystery | 2,925 |  4.69% |
| Fantasy | 2,731 |  4.37% |
| War | 1,874 |  3.00% |
| Western | 1,399 |  2.24% |
| Musical | 1,054 |  1.69% |
| Film-Noir | 353 |  0.57% |
| IMAX | 195 |  0.31% |

### 4.2. Độ phủ Thẻ người dùng tự do (Free-text Tags):
- Tổng lượt gán tag: **1,093,360**.
- Số tag duy nhất: **73,051**.
- Số người dùng tham gia gắn tag: **14,592** (chỉ chiếm 8.98% tổng số users có rating).
- Số phim có ít nhất 1 tag: **45,251** (72.49% catalog).

### 4.3. Độ phủ Tag Genome & Tỷ lệ Ratings Thần kỳ (The Genome Paradox):
- Số lượng tag genome được chuẩn hóa: **1,128**.
- Số phim sở hữu vector đặc trưng Tag Genome: **13,816 phim**.
  - Tỷ lệ trên danh mục phim (Catalog): **22.13%** (13,816 / 62,423).
  - Tỷ lệ trên phim có rating: **23.40%** (13,816 / 59,047).
- **TỔNG RATINGS THUỘC VỀ PHIM CÓ TAG GENOME:** **24,674,113 / 25,000,095 ratings**.
- **TỶ LỆ RATINGS ĐƯỢC TAG GENOME BAO PHỦ:** **98.70%**.

> [!IMPORTANT]
> **Phát hiện Định lượng Trọng yếu:** Mặc dù Tag Genome chỉ bao phủ **22.13%** số lượng phim trong danh mục, nhưng tập hợp 13,816 bộ phim này lại chiếm tới **98.70% toàn bộ khối lượng tương tác ratings** của người dùng! Điều này khẳng định Tag Genome bao phủ gần như toàn bộ các tác phẩm phổ biến nhất ('head' và 'torso' của phân bố). Đây là cơ sở khoa học hoàn hảo để xây dựng **Mood / Emotional Knowledge Graph** và mô hình gợi ý kết hợp (Hybrid).

---

## 5. Dòng thời gian (Timeline) & Chiến lược Chia Dữ liệu (Train/Val/Test Split)

- **Khoảng thời gian Ratings:** từ `1995-01-09 18:46:49` đến `2019-11-21 16:15:03` (hơn 24 năm).
- **Khoảng thời gian Tags:** từ `2005-12-24 20:00:10` đến `2019-11-21 13:11:36` (hơn 13 năm, từ 2006 đến 2019).

### Phân bố số lượng Ratings theo Năm:

| Năm | Số lượng Ratings | Tỷ lệ (%) |
| :--- | :--- | :--- |
| 1995 | 3 |  0.00% |
| 1996 | 1,429,377 |  5.72% |
| 1997 | 626,752 |  2.51% |
| 1998 | 272,153 |  1.09% |
| 1999 | 1,057,061 |  4.23% |
| 2000 | 1,736,472 |  6.95% |
| 2001 | 1,057,705 |  4.23% |
| 2002 | 777,852 |  3.11% |
| 2003 | 920,749 |  3.68% |
| 2004 | 1,047,253 |  4.19% |
| 2005 | 1,613,101 |  6.45% |
| 2006 | 1,039,384 |  4.16% |
| 2007 | 930,485 |  3.72% |
| 2008 | 1,019,240 |  4.08% |
| 2009 | 809,938 |  3.24% |
| 2010 | 792,795 |  3.17% |
| 2011 | 676,424 |  2.71% |
| 2012 | 634,940 |  2.54% |
| 2013 | 515,965 |  2.06% |
| 2014 | 478,353 |  1.91% |
| 2015 | 1,603,949 |  6.42% |
| 2016 | 1,757,009 |  7.03% |
| 2017 | 1,690,203 |  6.76% |
| 2018 | 1,310,810 |  5.24% |
| 2019 | 1,202,122 |  4.81% |

### Đánh giá Chiến lược Chia Dữ liệu cho Giai đoạn tiếp theo:
1. **Time-based Split (Phân chia theo dòng thời gian):**
   - Phù hợp nhất để kiểm tra khả năng dự đoán trong tương lai, ngăn ngừa rò rỉ dữ liệu (data leakage).
   - Ví dụ: Dùng dữ liệu trước năm 2018 làm Train, năm 2018 làm Validation, và 2019 làm Test.
   - *Thách thức:* Một số user cũ không còn tương tác ở năm 2019, hoặc các user mới xuất hiện năm 2019 sẽ biến thành Cold-start Users ở tập Test.
2. **Leave-One-Last / Leave-k-Last Split (Phân chia theo thời gian trên từng User):**
   - Với mỗi user, lấy k tương tác mới nhất theo timestamp làm Test, k tương tác áp chót làm Validation, toàn bộ tương tác trước đó làm Train.
   - *Ưu điểm:* Đảm bảo 100% users đều có mặt trong tập Train, tránh rủi ro cold-start user trong bài toán Collaborative Filtering ALS, đồng thời vẫn bảo đảm tính tuần tự thời gian.
3. **Stratified Random Split:**
   - Chia 80/10/10 ngẫu nhiên theo user.
   - *Hạn chế:* Bị data leakage về mặt thời gian (dùng tương lai để dự đoán quá khứ).

---

## 6. Đánh giá Rủi ro Đối với ALS và Knowledge Graph (Risks & Mitigations)

### 6.1. Rủi ro đối với Mô hình ALS (Collaborative Filtering)
1. **Rủi ro Ma trận Cực thưa (Sparsity ~ 99.75%):**
   - ALS rất dễ bị overfit nếu tham số `regParam` quá nhỏ. Cần điều chỉnh `regParam` trong khoảng [0.05, 0.15] và `rank` trong khoảng [32, 128].
2. **Rủi ro Phim Đuôi dài (Long-tail / Cold-start Movies):**
   - Có 3,376 phim không có rating nào và 16,804 phim có <= 5 ratings. ALS thuần túy không thể tạo vector tiềm ẩn (latent vector) chất lượng cho các phim này.
   - *Giải pháp:* Thiết lập `coldStartStrategy='drop'` trong Spark MLlib ALS khi đánh giá RMSE/NDCG trên test set để tránh lỗi NaN; đồng thời fallback sang Content-based / Genre / Knowledge Graph cho các phim cold-start.
3. **Rủi ro Mất cân bằng Hoạt động (User Activity Imbalance):**
   - User tích cực nhất có 32,202 ratings trong khi phân vị p50 là 71 ratings. Các siêu người dùng (heavy users) có thể làm chệch hàm mất mát của ALS nếu không chuẩn hóa trọng số.

### 6.2. Rủi ro đối với Kiến trúc Knowledge Graph (MoodGraph)
1. **Rủi ro Phân mảnh Thẻ tự do (Free-text Tags):**
   - Có tới 73,050 tag tự do khác nhau nhưng chỉ có 14,592 users đóng góp. Tags có nhiều từ đồng nghĩa, biến thể chính tả, tiếng lóng, viết tắt ('sci fi', 'scifi', 'sci-fi') và 16 bản ghi chứa nhãn 'NA'.
   - *Giải pháp:* Không đưa trực tiếp toàn bộ 73,050 tags tự do vào làm nút (node) trong KG. Thay vào đó, dùng 1,128 Tag Genome chuẩn hóa làm Semantic Backbone, và áp dụng NLP / Embedding để nhóm các user tag hợp lệ vào các mood / attribute concepts.
2. **Rủi ro Độ phủ của Tag Genome đối với Phim Catalog (Chỉ 22.13% số phim):**
   - Nếu xây dựng KG hoàn toàn phụ thuộc vào Tag Genome, 77.87% số phim trong catalog sẽ bị cô lập thành các nút cô đơn (isolated nodes) không có liên kết cảm xúc.
   - *Giải pháp:* Thiết kế lược đồ KG đa tầng: Tầng 1 sử dụng Thể loại (Genre) và Đạo diễn/Diễn viên (từ IMDb/TMDb) để bảo đảm 100% độ phủ cho mọi phim; Tầng 2 bổ sung Tag Genome và Mood Embeddings làm tầng liên kết sâu cho 98.70% lượng tương tác thực tế.
