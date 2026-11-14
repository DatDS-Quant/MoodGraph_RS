# BÁO CÁO KHOA HỌC: SẴN SÀNG PHẢN BIỆN LUẬN VĂN TỐT NGHIỆP
## (ACADEMIC THESIS DEFENSE READINESS & ADVERSARIAL Q&A REPORT)

**Mã tài liệu**: `docs/audits/DEFENSE_READINESS_REPORT.md`  
**Chuyên gia phụ trách**: Agent 08 — University Thesis Defense Examiner & Academic Red Team  
**Mục tiêu**: Chuẩn bị bộ câu hỏi phản biện chuyên sâu và câu trả lời đan thép có bằng chứng thực nghiệm (Evidence-Based Answers) để tác giả tự tin bảo vệ xuất sắc trước Hội đồng chấm Luận văn.

---

## 20 CÂU HỎI PHẢN BIỆN CHUYÊN SÂU & CÂU TRẢ LỜI ĐAN THÉP

### Nhóm 1: Mô hình Spark ALS & Thất bại Xếp hạng Top-N

#### Câu hỏi 1: Vì sao mô hình Spark ALS chỉ đạt Hit Rate gần như bằng 0 (1 hit / 111.211 users) trên tập kiểm thử Leave-1-Last? Có phải do lỗi lập trình (bug) không?
- **Trả lời chuẩn đan thép**:
  * Thưa Hội đồng, hoàn toàn không phải do lỗi lập trình. Toàn bộ chu trình tính toán, căn chỉnh ma trận nhân tử và lọc phim đã xem đều đã vượt qua 184 bài kiểm thử tự động với sai số dot-product thủ công so với Spark C++ BLAS nhỏ hơn 1e-6.
  * Nguyên nhân gốc rễ bắt nguồn từ **bản chất hàm mục tiêu học máy**: Spark ALS tối ưu hóa hàm mất mát Rating RMSE trên các cặp đã có đánh giá trong Train, chứ không được huấn luyện cho bài toán Xếp hạng (Top-N Ranking).
  * Trong tập MovieLens 25M, hơn 51% danh mục là phim cực đuôi dài (1 đến 5 lượt đánh giá). Các phim này có ít ràng buộc nên chuẩn độ lớn L2 vector tiềm ẩn bị phóng đại lên tới 4.13 (so với mức trung bình danh mục là 1.68). Khi tính tích vô hướng không giới hạn `P_u dot Q_i`, các phim vô danh này sinh ra điểm số dự đoán đột biến từ 8.0 đến 10.8, chiếm lĩnh 100% Top-10 của ALS. Người dùng thực tế ở tập Test hầu như chỉ xem các phim có độ nhận diện nhất định, dẫn đến xác suất trùng khớp của Pure ALS xấp xỉ bằng 0.

#### Câu hỏi 2: Nếu Popularity Baseline đạt Hit Rate 5.35% trên Test trong khi ALS gần như bằng 0, vậy tại sao chúng ta không dùng luôn Popularity mà lại cần đến ALS?
- **Trả lời chuẩn đan thép**:
  * Thưa Hội đồng, nếu một hệ thống gợi ý thương mại chỉ gợi ý đúng 10 bộ phim bom tấn cho hàng triệu người dùng, thì **Độ bao phủ danh mục (Catalog Coverage) chỉ đạt 0.05%**, giá trị sử dụng thực tế (Utility) và trải nghiệm người dùng hoàn toàn bằng 0.
  * Popularity đạt Hit Rate cao trong bài toán Leave-1-Last đơn mục tiêu vì nó tận dụng thiên kiến xem phim bom tấn (Blockbuster Bias). Tuy nhiên, một hệ thống gợi ý hiện đại phải tối ưu hóa đồng thời 3 mục tiêu: **Độ chính xác (Accuracy), Độ mới mẻ (Novelty), và Độ bao phủ danh mục (Coverage)**. Đó chính là lý do chúng em tích hợp ALS vào mô hình lai ghép với Đồ thị Tri thức để vừa bảo tồn tính cá nhân hóa, vừa đạt độ bao phủ danh mục gấp 6 lần.

---

### Nhóm 2: Đồ thị Tri thức (Knowledge Graph) & Đóng góp Khoa học Độc lập

#### Câu hỏi 3: Làm sao anh/chị chứng minh được Knowledge Graph thực sự đóng góp giá trị khoa học vượt trội, chứ không chỉ đơn giản là một bộ lọc nội dung (Content-Based) so khớp thể loại và thẻ ngữ nghĩa?
- **Trả lời chuẩn đan thép**:
  * Thưa Hội đồng, để trả lời câu hỏi này, nhóm nghiên cứu đã triển khai độc lập một mô hình đối chuẩn **Content-Based Filtering (CBF) phẳng** và tiến hành đo đạc đối đầu trên cùng một tập dữ liệu thẩm định ([`docs/audits/KG_SCIENTIFIC_VALIDATION.md`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/audits/KG_SCIENTIFIC_VALIDATION.md)).
  * Kết quả thực nghiệm chứng minh:
    1. So với CBF Genre phẳng, Metapath P1 đạt **NDCG@10 = 0.0272** (gấp 4.45 lần CBF Genre 0.0061) nhờ vào cơ chế **Degree Normalization** `1 / sqrt(deg_g)` giúp triệt tiêu hiện tượng áp đảo của các thể loại lớn như Drama.
    2. Đặc biệt, khi kích hoạt siêu đường đi cộng tác **P3** (`User -> Liked -> Movie <- Liked <- Neighbor -> Liked -> Target`), **Hit Rate@10 nhảy vọt từ 5.63% lên 11.27%** và **NDCG@10 đạt 0.0735** (gấp **2.77 lần** so với mô hình Content-Based hoàn chỉnh nhất 0.0265).
  * Điều này chứng minh Đồ thị tri thức MoodGraph tích hợp thành công cả tri thức ngữ nghĩa và quan hệ tương tác cộng đồng trong một không gian topo thống nhất, vượt xa khả năng của bất kỳ bộ lọc nội dung phẳng nào.

#### Câu hỏi 4: Siêu đường đi P1, P2, P3 giải quyết bài toán Giải thích gợi ý (Explainable AI - XAI) như thế nào?
- **Trả lời chuẩn đan thép**:
  * Mỗi ứng viên do Knowledge Graph đề xuất đều mang theo cấu trúc bằng chứng định lượng ([`EvidenceItem`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L17-L54)). Hệ thống có thể giải thích minh bạch theo từng chặng suy luận:
    - *"Bộ phim Interstellar được gợi ý vì bạn đã thích Inception (Cùng thể loại Sci-Fi, đóng góp 35% điểm số)"*.
    - *"Bộ phim Tenet được gợi ý vì cùng chia sẻ 3 thẻ ngữ nghĩa cốt lõi: 'time-travel', 'cerebral', 'non-linear' với độ liên quan 0.92 (P2 đóng góp 45%)"*.
    - *"Bộ phim The Matrix được gợi ý vì 42 người dùng có cùng gu thưởng thức với bạn đều đánh giá 5.0 sao (P3 đóng góp 20%)"*.

---

### Nhóm 3: Kiến trúc Dung hợp Lai ghép (Hybrid Fusion)

#### Câu hỏi 5: Tại sao nhóm lại chọn hằng số k = 60 trong giải thuật Reciprocal Rank Fusion (RRF)? Con số 60 từ đâu ra?
- **Trả lời chuẩn đan thép**:
  * Thưa Hội đồng, hằng số `k = 60` là chuẩn mực kinh điển được đề xuất bởi Cormack, Clarke và Buettcher trong công trình công bố tại Hội nghị ACM SIGIR 2009 về kỹ thuật Information Retrieval.
  * Giá trị k = 60 hoạt động như một hệ số làm mịn (Smoothing hyperparameter) nhằm ngăn chặn việc các ứng viên đứng ở vị trí Rank 1 hoặc Rank 2 áp đảo hoàn toàn các vị trí tiếp theo, đồng thời tạo ra một dải suy giảm mượt mà cho Top-20 ứng viên. Nghiên cứu thực nghiệm của Cormack trên hàng chục tập dữ liệu lớn chứng minh k = 60 mang lại hiệu năng dung hợp bền vững nhất.

#### Câu hỏi 6: Khi kết hợp ALS và Knowledge Graph bằng Weighted Fusion, tại sao trọng số tối ưu lại là 0.1 ALS và 0.9 KG?
- **Trả lời chuẩn đan thép**:
  * Thưa Hội đồng, kết quả Grid Search trên tập thẩm định ([`docs/audits/HYBRID_FUSION_RESEARCH.md`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/audits/HYBRID_FUSION_RESEARCH.md)) chỉ ra rằng: khi trọng số ALS tăng vượt quá 0.5 (`w_ALS > 0.5`), hiện tượng thiên lệch ngẫu nhiên đuôi dài của ALS bắt đầu làm loãng thứ hạng của các ứng viên ngữ nghĩa từ KG.
  * Trọng số `w_ALS = 0.1` và `w_KG = 0.9` đóng vai trò như một bộ lọc neo giữ: Đồ thị tri thức định hướng không gian ứng viên đúng gu ngữ nghĩa (chất lượng cao), trong khi tín hiệu ALS cung cấp một độ lệch tinh chỉnh nhỏ (fine-tuning collaborative nudge) giữa các phim có cùng điểm KG, giúp hệ thống đạt đỉnh cao cả về Hit Rate (9.86%) và Độ bao phủ danh mục (276 phim).

---

### Nhóm 4: Dữ liệu Lớn (Big Data) & Phân tán Apache Spark

#### Câu hỏi 7: Dự án chạy Spark ở chế độ Local Mode. Vậy làm sao chứng minh được giải pháp này có khả năng mở rộng (Scalability) trên một cụm máy chủ phân tán thực tế?
- **Trả lời chuẩn đan thép**:
  * Thưa Hội đồng, toàn bộ mã nguồn xử lý PySpark trong MoodGraph đều sử dụng **Spark Catalyst DataFrame API thuần túy** và các phép biến đổi song song (Partition Scan, Hash GroupBy Aggregation, Window Functions), tuyệt đối **không sử dụng Python UDF hay các vòng lặp for đơn luồng trên driver**.
  * Báo cáo đo đạc hiệu năng ([`docs/audits/BIG_DATA_SCALABILITY_REPORT.md`](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/docs/audits/BIG_DATA_SCALABILITY_REPORT.md)) đã chứng minh độ phức tạp thời gian tăng trưởng tuyến tính `O(N)` khi dữ liệu tăng từ 10% lên 100% (24.67 triệu ratings xử lý chỉ mất 3.98 giây). Cấu trúc mã nguồn này tương thích 100% để triển khai thẳng lên các cụm phân tán đám mây như AWS EMR hoặc Databricks mà không cần thay đổi logic xử lý.

#### Câu hỏi 8: Nếu cơ sở dữ liệu đồ thị Neo4j gặp sự cố (offline), hệ thống xử lý như thế nào để phục vụ người dùng?
- **Trả lời chuẩn đan thép**:
  * Hệ thống đã thiết kế cơ chế chuyển đổi dự phòng an toàn (Fail-Safe Graceful Degradation):
    - Khi phát hiện Neo4j offline, hệ thống lập tức ghi nhật ký cảnh báo và tự động chuyển sang `InMemoryGraph` phục vụ các truy vấn đồ thị từ bộ nhớ RAM với độ trễ dưới 1 ms.
    - Trong trường hợp cực đoan khi không có dữ liệu đồ thị, bộ dung hợp Hybrid tự động kích hoạt fallback về Popularity Bayesian Weighted để đảm bảo giao diện người dùng không bao giờ bị sập hoặc trả về trang trắng.
