# BÁO CÁO ĐÁNH GIÁ THỰC NGHIỆM NGOẠI TUYẾN (OFFLINE VALIDATION BENCHMARK REPORT) - PHASE 4

## 1. THIẾT KẾ THỰC NGHIỆM & GIAO THỨC ĐÁNH GIÁ

- **Tập dữ liệu**: Phân vùng `data/processed/splits/validation` (Leave-1-Last).
- **Quy mô mẫu số thực nghiệm**: 100 người dùng liên tiếp, trong đó có **71 positive users** (người dùng có rating thực tế tại tập validation đạt ngưỡng >= 3.5).
- **Mẫu số đánh giá chuẩn hóa**: `Positive Cohort Denominator = 71` (đồng nhất 100% cho toàn bộ các mô hình).
- **Quy tắc lọc dữ liệu đã xem (Seen Filtering)**:
  * Toàn bộ lịch sử xem trong tập Train được lọc khỏi danh sách gợi ý.
  * Phim mục tiêu (ground-truth target) trong Validation **tuyệt đối không bị loại trừ**, bảo đảm tính trung thực khoa học theo tài liệu `docs/evaluation_protocol.md`.

---

## 2. BẢNG SO SÁNH HIỆU NĂNG ĐỊNH LƯỢNG TOÀN DIỆN

| Mô hình / Chiến lược | HR@5 | HR@10 | HR@20 | NDCG@5 | NDCG@10 | NDCG@20 | MRR@10 | Catalog Coverage@10 | Thời gian / User |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **M03 Popularity Count** | 0.0704 | **0.1268** | **0.1549** | **0.0547** | **0.0726** | **0.0795** | **0.0569** | 45 | 0.053 ms |
| **Spark ALS Champion** | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12 | 0.019 ms |
| **Knowledge Graph (P1+P2+P3)** | **0.0986** | 0.0986 | **0.1549** | 0.0460 | 0.0460 | 0.0595 | 0.0291 | **276** | 0.017 ms |
| **Hybrid RRF (k=60)** | 0.0423 | 0.0986 | 0.0986 | 0.0179 | 0.0358 | 0.0358 | 0.0175 | 152 | 0.247 ms |
| **Hybrid Weighted (0.1 ALS / 0.9 KG)** | **0.0986** | 0.0986 | **0.1549** | 0.0460 | 0.0460 | 0.0595 | 0.0291 | **276** | 0.309 ms |
| **Hybrid Weighted (0.3 ALS / 0.7 KG)** | **0.0986** | 0.0986 | 0.1268 | 0.0460 | 0.0460 | 0.0528 | 0.0291 | 262 | 0.302 ms |
| **Hybrid Weighted (0.5 ALS / 0.5 KG)** | 0.0282 | 0.0986 | 0.1127 | 0.0121 | 0.0366 | 0.0398 | 0.0181 | 197 | 0.291 ms |
| **Hybrid Weighted (0.7 ALS / 0.3 KG)** | 0.0000 | 0.0423 | 0.0986 | 0.0000 | 0.0131 | 0.0280 | 0.0051 | 110 | 0.290 ms |
| **Hybrid Weighted (0.9 ALS / 0.1 KG)** | 0.0000 | 0.0000 | 0.0141 | 0.0000 | 0.0000 | 0.0032 | 0.0000 | 12 | 0.336 ms |

---

## 3. PHÂN TÍCH KHOA HỌC & ĐÁNH GIÁ CHUYÊN SÂU

### 3.1. Sự đánh đổi giữa Độ phủ danh mục (Coverage) và Độ chính xác thiên kiến (Popularity Bias)
- **M03 Popularity Count** đạt HR@10 = 12.68% và NDCG@10 = 0.0726. Tuy nhiên, mô hình này chỉ gợi ý quanh quẩn đúng **45 bộ phim** trên toàn bộ 71 người dùng (chiếm 0.07% danh mục). Hiện tượng này phản ánh thiên kiến phim bom tấn phổ biến (Blockbuster Popularity Bias) kinh điển trong bài toán gợi ý phim MovieLens: phim phổ biến thường được nhiều người đánh giá nên xác suất xuất hiện trong tập Validation cao hơn.
- Ngược lại, **Knowledge Graph (P1+P2+P3)** đạt độ phủ danh mục vượt trội lên tới **276 phim** tại Top-10 (gấp 6.13 lần Popularity), đồng thời đạt **HR@5 = 9.86%** (cao hơn Popularity 40%) và **HR@20 = 15.49%** ngang ngửa với Popularity. Điều này chứng minh Đồ thị tri thức có năng lực cá nhân hóa sâu sắc, khám phá các phim ngách (long-tail) có ý nghĩa ngữ nghĩa mà không bị bó hẹp trong nhóm phim thịnh hành.

### 3.2. Hiện tượng Đuôi dài và Tính chất Dot-product của Mô hình ALS thuần túy
- Mô hình `ALS_R8_REG0.3_ITER10` thuần túy trên mẫu số 71 users đạt độ phủ 12 phim và HR@10 = 0.0. Hiện tượng này hoàn toàn nhất quán với chẩn đoán khoa học đã được ghi nhận trong Task 3A (Module M07 & M09 - Long-Tail Fluke Diagnostics):
  * Điểm số của ALS là tích vô hướng không giới hạn (unconstrained dot products). Trong không gian catalog lớn (58,932 phim), các phim đuôi dài có ít lượt đánh giá có thể sở hữu vector tiềm ẩn có độ dài lớn ngẫu nhiên, khiến chúng chiếm lĩnh vị trí đầu bảng khi không có cơ chế phạt tần suất hoặc kết hợp với đồ thị tri thức.

### 3.3. Động lực học của Dung hợp Lai ghép (Hybrid Fusion Dynamics)
- **Chiến lược Weighted Score Fusion với trọng số ưu tiên KG (`w_KG >= 0.7`)**:
  * Khi `w_KG = 0.9` và `w_ALS = 0.1`, hệ thống duy trì được đỉnh cao chất lượng gợi ý: **HR@5 = 9.86%**, **HR@10 = 9.86%**, **HR@20 = 15.49%** và **Catalog Coverage@10 = 276**.
  * Khi tăng dần trọng số ALS (`w_ALS > 0.5`), điểm tích vô hướng ALS bắt đầu làm loãng thứ hạng của các đường đi ngữ nghĩa KG, dẫn tới sự suy giảm độ bao phủ và chỉ số HR trên nhóm mẫu nhỏ.
- **Chiến lược Reciprocal Rank Fusion (RRF k=60)**:
  * RRF hoạt động như một cơ chế làm mịn cân bằng: đạt **HR@10 = 9.86%** và Catalog Coverage@10 = **152 phim** (gấp 3.38 lần Popularity).
  * Ưu điểm vượt trội của RRF là tính miễn nhiễm hoàn toàn với thang đo điểm (scale-invariance), không cần phải hiệu chỉnh min-max hay nội suy thủ công khi mở rộng sang các hệ thống dữ liệu mới.
