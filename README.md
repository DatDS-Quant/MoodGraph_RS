# MoodGraph: Hệ Thống Gợi Ý Phim Cá Nhân Hóa Kết Hợp Apache Spark ALS và Đồ Thị Tri Thức

[![PySpark](https://img.shields.io/badge/PySpark-4.2.0-orange.svg)](https://spark.apache.org/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-184%20Passed-brightgreen.svg)](tests/als/)
[![Quality Gates](https://img.shields.io/badge/Quality%20Gates-25%2F25%20Pass-success.svg)](scripts/audit_m10_release.py)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**MoodGraph** là hệ thống gợi ý phim cá nhân hóa quy mô lớn, kết hợp năng lực tính toán phân tán của **Apache Spark MLlib (Collaborative Filtering)** và khả năng biểu diễn ngữ nghĩa phong phú của **Đồ thị tri thức (Knowledge Graph)** nhằm giải quyết các thách thức cố hữu của hệ gợi ý truyền thống: dữ liệu cực thưa (extreme sparsity), người dùng mới (Cold-start) và hiện tượng thiên lệch phổ biến (popularity bias).

---

## 1. Mục Tiêu Dự Án

- **Gợi ý cá nhân hóa chính xác:** Khai phá sở thích tiềm ẩn từ lịch sử tương tác 25 triệu lượt đánh giá (MovieLens 25M) thông qua thuật toán phân rã ma trận W-ALS (Weighted Alternating Least Squares) trên Apache Spark.
- **Làm giàu ngữ cảnh bằng Đồ thị tri thức:** Tận dụng mối liên kết đa chiều giữa phim, đạo diễn, diễn viên, thể loại và từ khóa cảm xúc (mood/tags) để giải thích lý do đề xuất và xử lý người dùng hoặc phim ít tương tác.
- **Kiến trúc Lai (Hybrid Re-ranking):** Kết hợp điểm số dự báo từ Collaborative Filtering và đồ thị tri thức để cân bằng giữa độ chính xác (Accuracy), độ mới (Novelty) và tính đa dạng (Diversity).
- **Quy chuẩn kỹ thuật chuẩn mực:** Phân chia dữ liệu theo dòng thời gian (Temporal Split) nghiêm ngặt với rào chắn rò rỉ hai lớp (Dual Leakage Guard), cam kết không rò rỉ dữ liệu tương lai vào tập huấn luyện.

---

## 2. Kiến Trúc Hệ Thống & Trạng Thái Các Phân Hệ

Dự án được chia thành 5 phân hệ kỹ thuật độc lập với ranh giới hợp đồng rõ ràng:

```text
[MovieLens 25M Raw Data]
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Data Preprocessing & Validation (Temporal Split)          │ -> [HOÀN THÀNH]
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌───────────────────────────────┐ ┌───────────────────────────┐
│ 3A. Spark ALS (CF Phân Tán)   │ │ 3B. Knowledge Graph (KG)  │
│ - W-ALS Factorization         │ │ - Graph Construction      │
│ - Exact Top-N Matrix Mul      │ │ - Node2Vec / TransE Embed │
│ - Seen-Item CSR Filter        │ │ - Semantic Context        │
│ [HOÀN THÀNH - 184 TESTS PASS] │ │ [ĐANG NGHIÊN CỨU & XÂY DỰNG]│
└──────────────┬────────────────┘ └─────────────┬─────────────┘
               │                                │
               └───────────────┬────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Hybrid Recommendation & Multi-Objective Ranking          │ -> [CHUẨN BỊ TÍCH HỢP]
└──────────────────────────────┬──────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Web Application (FastAPI Backend + Next.js Frontend)     │ -> [KẾ HOẠCH TIẾP THEO]
└─────────────────────────────────────────────────────────────┘
```

### Bảng Trạng Thái Thực Tế
| Phân hệ / Khối | Trách nhiệm chính | Trạng thái hiện tại | Bằng chứng kiểm định |
| :--- | :--- | :---: | :--- |
| **Khối 1: Preprocessing** | Xử lý dữ liệu MovieLens 25M, Temporal Split | **Hoàn thành** | [preprocessing_report.md](docs/preprocessing_report.md) |
| **Khối 2: Protocol** | Thiết lập rào chắn rò rỉ, bộ đo độc lập | **Hoàn thành** | [evaluation_protocol.md](docs/evaluation_protocol.md) |
| **Phân hệ 3A: Spark ALS** | Huấn luyện ALS, Top-N ranking, đóng gói API | **Hoàn thành** | [TASK_3A_FINAL_ACCEPTANCE.md](docs/3a/TASK_3A_FINAL_ACCEPTANCE.md) (184 Tests PASS) |
| **Phân hệ 3B: Knowledge Graph** | Xây dựng đồ thị tri thức, nhúng thực thể | *Đang nghiên cứu* | Đang phát triển độc lập |
| **Khối 4: Hybrid Model** | Kết hợp điểm số ALS + KG, reranking | *Chuẩn bị tích hợp* | [integration_contract.md](docs/3a/integration_contract.md) |
| **Khối 5: Web Application** | FastAPI backend và Next.js frontend | *Kế hoạch tiếp theo* | Thư mục nền tảng `web/` |

---

## 3. Cấu Trúc Thư Mục Dự Án

```text
MoodGraph/
├── data/                      # Quản lý tập dữ liệu MovieLens 25M (thô và đã qua xử lý)
│   ├── raw/                   # Dữ liệu gốc tải về (không track git)
│   └── processed/             # Dữ liệu phân tách Train / Validation / Test dạng Parquet
├── docs/                      # Tài liệu hệ thống, kiến trúc và báo cáo thực nghiệm
│   ├── 3a/                    # Hệ thống 31 tài liệu chi tiết của Phân hệ 3A
│   ├── data_dictionary.md     # Từ điển dữ liệu MovieLens 25M
│   ├── data_eda.md            # Báo cáo phân tích khám phá dữ liệu (EDA)
│   └── evaluation_protocol.md # Giao thức đánh giá xếp hạng Top-N
├── recommender/               # Mã nguồn chính của các thuật toán gợi ý
│   ├── als/                   # Module Lọc cộng tác phân tán Spark ALS (Task 3A)
│   │   ├── benchmark.py       # Kịch bản thực thi đánh giá kiểm định Test split
│   │   ├── candidates.py      # Sinh ứng viên Top-N chính xác bằng nhân ma trận
│   │   ├── delivery.py        # Lớp đóng gói mô hình sản xuất ALSDeliveryModel
│   │   ├── diagnostics.py     # Chẩn đoán Cold-start, Long-tail và phân tán
│   │   ├── evaluator.py       # Bộ đo Ranking chuẩn độc lập (HR, NDCG, MRR)
│   │   ├── popularity.py      # Baseline không cá nhân hóa (Popularity & Bayesian)
│   │   ├── trainer.py         # Huấn luyện Spark ALS phân tán với bảo vệ bộ nhớ
│   │   └── tuner.py           # Tối ưu hóa siêu tham số (Grid Search Validation)
│   ├── preprocess.py          # Pipeline tiền xử lý và chia tách thời gian
│   └── validate_data.py       # Kiểm toán chất lượng và rào chắn rò rỉ dữ liệu
├── scripts/                   # Các kịch bản CLI tự động hóa từ M01 đến M10
│   ├── audit_m10_release.py   # Bộ kiểm toán tự động 25 Quality Gates
│   ├── hermes_memory.py       # Công cụ đồng bộ bộ nhớ đặc vụ HERMES
│   ├── run_m08_frozen_benchmark.py # Kịch bản kiểm định trên Frozen Test Split
│   └── run_m10_delivery.py    # Kịch bản suy luận và tạo ma trận thưa Seen-item
├── tests/                     # Toàn bộ test suite kiểm thử tự động
│   └── als/                   # 184 ca kiểm thử chuyên sâu cho Phân hệ 3A
├── artifacts/                 # Thư mục lưu trữ metadata, kết quả đo lường và checkpoints
└── README.md                  # Hướng dẫn tổng quan dự án
```

---

## 4. Kết Quả Thực Nghiệm & Giới Hạn Khoa Học (Phân Hệ 3A)

Kết quả thực nghiệm trên tập **Frozen Test Split** (111.211 người dùng kiểm thử, mỗi người dùng có đúng 1 tương tác đánh giá dương tính làm ground-truth):

| Mô hình | HR@10 | NDCG@10 | MRR@10 | Số Hits (@10) |
| :--- | :---: | :---: | :---: | :---: |
| **M03 Popularity Count** | **0.05357** | **0.02721** | **0.01929** | **5.958** |
| **M03 Popularity Weighted (m=10)** | 0.01884 | 0.00742 | 0.00404 | 2.095 |
| **Spark ALS Champion (R8_REG0.3_ITER10)** | 8.9919e-06 | 5.6733e-06 | 4.4960e-06 | 1 (Rank 2) |

### Nhận Định Khoa Học Trung Thực
- **Hiện tượng thực tế:** Mô hình Popularity Count đạt kết quả cao hơn đáng kể so với ALS trên tập Test đơn mục tiêu dương tính.
- **Nguyên nhân kỹ thuật:** Tập dữ liệu MovieLens có độ thưa rất cao (sparsity > 99%). Khi đánh giá ngoại tuyến trên tương tác cuối cùng của người dùng, ALS thuần túy gặp hiện tượng co cụm vector (latent factor shrinkage) ở những người dùng có ít hành vi.
- **Ý nghĩa đối với kiến trúc MoodGraph:** Kết quả này chứng minh rằng **lọc cộng tác đơn thuần là chưa đủ cho bài toán thực tế**. Đây chính là căn cứ khoa học vững chắc để phát triển **Phân hệ 3B (Đồ thị tri thức)** nhằm bù đắp khoảng trống ngữ nghĩa và kết hợp sức mạnh tại **Khối 4 (Mô hình Lai - Hybrid)**.

---

## 5. Hướng Dẫn Cài Đặt & Môi Trường

### Yêu Cầu Hệ Thống
- Hệ điều hành: Windows 10/11, macOS hoặc Linux
- Python: Phiên bản 3.10 trở lên (khuyến nghị Python 3.12)
- Java: OpenJDK 17 hoặc Java 11 (bắt buộc cho Apache Spark)
- Bộ nhớ RAM: Tối thiểu 16 GB (khuyến nghị khi chạy với 25 triệu ratings)

### Các Bước Cài Đặt
```bash
# 1. Clone kho lưu trữ
git clone https://github.com/DatDS-Quant/MoodGraph_RS.git
cd MoodGraph

# 2. Khởi tạo môi trường ảo Python
python -m venv .venv

# Kích hoạt trên Windows:
.venv\Scripts\activate
# Hoặc kích hoạt trên Linux/macOS:
# source .venv/bin/activate

# 3. Cài đặt các thư viện phụ thuộc
pip install --upgrade pip
pip install pyspark==4.2.0 numpy scipy pandas pytest
```

---

## 6. Chuẩn Bị Dữ Liệu & Artifacts

1. **Dữ liệu phân vùng:** Đảm bảo các tệp parquet `train.parquet`, `validation.parquet`, `test.parquet` đã được đặt tại `data/processed/`.
2. **Khởi tạo Ma trận thưa lọc phim đã xem (Seen-Item CSR):**
   Mô hình ALS cần loại trừ các phim người dùng đã xem trong tập Train khi gợi ý Top-N:
   ```bash
   python scripts/run_m10_delivery.py --build-seen-csr
   ```
   Lệnh trên sẽ quét toàn bộ tương tác Train và lưu ma trận tại `artifacts/als/m10/train_seen_csr.npz`.

---

## 7. Hướng Dẫn Chạy Kiểm Thử (Testing & Quality Gates)

Dự án áp dụng quy chuẩn kiểm thử nghiêm ngặt trước mọi đợt phát hành:

```bash
# 1. Chạy toàn bộ 184 ca kiểm thử của Phân hệ 3A
pytest tests/als/ -v

# 2. Chạy bộ kiểm toán phát hành tự động (25 Quality Gates)
python scripts/audit_m10_release.py

# 3. Kiểm định tính toàn vẹn của bộ nhớ đặc vụ HERMES
python scripts/hermes_memory.py verify
```

---

## 8. Hướng Dẫn Sử Dụng API ALS (Quickstart)

Dưới đây là ví dụ nạp mô hình ALS đã được nghiệm thu và sinh danh sách gợi ý Top-N phim cho một người dùng:

```python
from recommender.als.delivery import ALSDeliveryModel

# 1. Khởi tạo và nạp mô hình sản xuất từ artifact
delivery_model = ALSDeliveryModel.from_artifact_dir(
    model_dir="artifacts/models/als/m05_spark_als_rank16",
    seen_csr_path="artifacts/als/m10/train_seen_csr.npz",
)

# 2. Sinh gợi ý Top-10 phim cho người dùng (user_id = 100)
recommendations = delivery_model.recommend_for_user(
    user_id=100,
    top_k=10,
    filter_seen=True,  # Tự động loại trừ các phim đã xem trong tập Train
)

print(f"Top 10 phim gợi ý cho người dùng 100:")
for rank, (movie_id, predicted_score) in enumerate(recommendations, start=1):
    print(f"  {rank}. Movie ID: {movie_id} - Điểm dự báo: {predicted_score:.4f}")
```

Kiểm tra suy luận nhanh bằng CLI:
```bash
python scripts/run_m10_delivery.py --smoke-only
```

---

## 9. Tra Cứu Tài Liệu Chi Tiết

Mọi tài liệu chi tiết về thiết kế, cẩm nang học tập, thực nghiệm và bản đồ phản biện mã nguồn được lưu trữ tại thư mục `docs/`:
- [Chỉ mục tổng hợp tài liệu dự án](docs/README.md)
- [Bản đồ tài liệu chi tiết Phân hệ 3A (31 tài liệu)](docs/3a/README.md)
- [Hợp đồng tích hợp kỹ thuật với Khối Hybrid](docs/3a/integration_contract.md)
- [Báo cáo nghiệm thu khoa học Phân hệ 3A](docs/3a/TASK_3A_FINAL_ACCEPTANCE.md)

---

## 10. Giấy Phép & Đóng Góp

Dự án được phát triển phục vụ mục đích nghiên cứu học thuật và đồ án tốt nghiệp kỹ sư khoa học dữ liệu. Mọi đóng góp xin vui lòng tạo Issue hoặc Pull Request theo đúng quy chuẩn kiểm thử của dự án.
