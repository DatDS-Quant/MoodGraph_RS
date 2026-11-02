# TRUNG TÂM TÀI LIỆU DỰ ÁN MOODGRAPH

Trang này cung cấp mục lục truy cập các tài liệu phân tích dữ liệu, giao thức đánh giá và các báo cáo chuyên đề của hệ thống MoodGraph.

---

## 1. Dữ Liệu & Giao Thức Đánh Giá Tổng Thể
- [Từ Điển Dữ Liệu (Data Dictionary)](data_dictionary.md): Định nghĩa cấu trúc các trường thông tin trong MovieLens 25M đã tiền xử lý.
- [Báo Cáo Phân Tích Dữ Liệu Khám Phá (EDA)](data_eda.md): Phân tích phân phối đánh giá (ratings), người dùng, phim và thể loại.
- [Báo Cáo Chất Lượng Dữ Liệu (Data Quality Report)](data_quality_report.md): Đánh giá độ sạch, tính nhất quán và các giá trị ngoại lai.
- [Quy Trình Tiền Xử Lý Dữ Liệu (Preprocessing Report)](preprocessing_report.md): Pipeline phân chia tập dữ liệu Train/Validation/Test theo dòng thời gian (Temporal Split).
- [Giao Thức Đánh Giá Ngoại Tuyến (Evaluation Protocol)](evaluation_protocol.md): Quy chuẩn đánh giá Top-N Ranking, rào chắn rò rỉ hai lớp (Dual Leakage Guard).

---

## 2. Tài Liệu Phân Hệ Chuyên Đề
- [Phân Hệ 3A: Spark ALS Collaborative Filtering](3a/README.md): Bản đồ chỉ mục toàn bộ 31 tài liệu lý thuyết, cẩm nang học tập, báo cáo thực nghiệm M00 - M10 và bản đồ bảo vệ mã nguồn.
- **Phân Hệ 3B: Knowledge Graph Recommendation**: Đang trong quá trình nghiên cứu & phát triển đồ thị tri thức (Node2Vec / TransE / GNN).
- **Khối 4: Hybrid Recommendation**: Chuẩn bị tích hợp sau khi hoàn thiện Phân hệ 3B.
- **Khối 5: Web Application**: Giao diện và API phục vụ người dùng cuối (FastAPI + Next.js).
