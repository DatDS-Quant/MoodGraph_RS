# HERMES: TÀI LIỆU THEO DÕI TIẾN ĐỘ & QUYẾT ĐỊNH DỰ ÁN
> **Dự án:** Personalized Movie Recommendation using Knowledge Graphs and Apache Spark  
> **Mục tiêu tài liệu:** Ghi chép trung tâm về hiện trạng kỹ thuật, kết quả kiểm nghiệm thực tế, các quyết định được duyệt và rủi ro mở nhằm duy trì tính nhất quán xuyên suốt các phiên làm việc.  
> *Cập nhật lần cuối:* 2026-10-25  

---

## 1. PHẠM VI DỰ ÁN ĐƯỢC DUYỆT (PROJECT SCOPE)

- **Tên chính thức:** **Personalized Movie Recommendation using Knowledge Graphs and Apache Spark** (Tên mã: MoodGraph).
- **Bộ dữ liệu chính:** MovieLens 25M (25,000,095 ratings, 162,541 users, 62,423 movies, 1,128 genome tags).
- **Phạm vi kỹ thuật cốt lõi:**
  1. Xây dựng pipeline xử lý dữ liệu và huấn luyện mô hình Collaborative Filtering phân tán bằng **Apache Spark MLlib ALS**.
  2. Xây dựng đồ thị tri thức phim dựa trên metadata sẵn có của MovieLens 25M (`movies.csv`, `tags.csv`, `genome-scores.csv`, `genome-tags.csv`) sử dụng **Neo4j Community Edition**.
  3. Áp dụng phương pháp tính điểm dựa trên đường đi (**Path-based KG Scoring**) trên đồ thị tri thức để sinh điểm gợi ý và hỗ trợ giải thích.
  4. Xây dựng mô hình **Hybrid Recommender** kết hợp điểm số từ nhánh ALS và nhánh Knowledge Graph thông qua cơ chế **Candidate Union** (hợp tập ứng viên).
- **Ranh giới phạm vi (Scope Boundaries):**
  - Không mở rộng sang dữ liệu đa phương thức (Multimodal: hình ảnh poster, video trailer, audio).
  - Không tự ý thêm metadata ngoài (Actor/Director từ IMDb/TMDb) vào phạm vi bắt buộc khi chưa có chỉ thị.
  - Không bắt buộc áp dụng Graph Neural Network (GNN) phức tạp hay Joint Embedding đa tầng nếu không cần thiết.
  - Không áp đặt mục tiêu độ trễ cố định (< 100ms) ở giai đoạn nghiên cứu offline.

---

## 2. BẢNG TRẠNG THÁI CÁC GIAI ĐOẠN (PROJECT STATUS TRACKER)

Phân loại trạng thái:
- `[VERIFIED]`: Đã thực thi thực tế trên mã nguồn và kiểm chứng qua dữ liệu/kết quả.
- `[PROPOSED]`: Đề xuất kỹ thuật đã soạn thảo, đang trong quá trình thẩm định.
- `[PENDING]`: Đang chờ duyệt hoặc chưa triển khai.

| Giai đoạn (Phase) | Nội dung Công việc | Trạng thái | Bằng chứng & Ghi chú Kỹ thuật |
| :--- | :--- | :--- | :--- |
| **Phase 1: Data Acquisition & Initial Audit** | Tải MovieLens 25M, kiểm tra MD5, giải nén và rà soát schema, encoding UTF-8, cấu hình `.gitignore`. | **[VERIFIED]** | - MD5 tải về trùng khớp 100% với GroupLens: `6b51fb2759a8657d3bfcbfc42b592ada`.<br>- 6 tệp CSV đặt tại `data/raw/ml-25m/`.<br>- Đã cung cấp script tự động 1 lệnh `scripts/setup_data.py` cho đồng đội.<br>- `git status` xác nhận sạch, dataset được `.gitignore` bảo vệ hoàn toàn. |
| **Phase 2: Spark Setup & EDA** | Kiểm tra môi trường PySpark trên Windows 11; thực hiện EDA toàn diện trên 25M ratings; đo đạc độ thưa ma trận, phân bố điểm, đuôi dài, độ phủ Genome. | **[VERIFIED]** | - Script `recommender/eda.py` chạy thành công bằng Spark trong 66 giây.<br>- Báo cáo đầy đủ tại `docs/data_eda.md`.<br>- Độ thưa: 99.74%. Phim có Genome (13,816 phim) chiếm tới 98.70% tổng lượng ratings. |
| **Phase 3: Evaluation Protocol** | Thiết kế giao thức phân chia Train/Val/Test, ranh giới chống rò rỉ dữ liệu, quy tắc đánh giá Full-Catalog Top-N và cơ chế xử lý cold-start. | **[PROPOSED / PENDING]** | - Tài liệu `docs/evaluation_protocol.md` đã cập nhật đầy đủ theo góp ý của Technical Mentor, đang chờ phê duyệt chính thức. |
| **Phase 4: Data Splitting Pipeline** | Thực thi phân chia dữ liệu bằng PySpark thành các tập Train, Validation, Test lưu định dạng tối ưu. | **[PENDING]** | Chưa triển khai (Chờ Phase 3 được duyệt). |
| **Phase 5: Baselines & ALS Training** | Huấn luyện Popularity, Item-Based CF, và Spark MLlib ALS; chọn siêu tham số trên Validation. | **[PENDING]** | Chưa triển khai. |
| **Phase 6: Knowledge Graph Construction** | Cài đặt Neo4j Community, nạp đồ thị tri thức từ dữ liệu MovieLens 25M, triển khai thuật toán Path-based Scoring. | **[PENDING]** | Chưa triển khai. |
| **Phase 7: Hybrid Fusion & Top-N Evaluation** | Kết hợp điểm ALS và KG theo cơ chế Candidate Union; đánh giá Top-N theo giao thức quy định. | **[PENDING]** | Chưa triển khai. |
| **Phase 8: Serving & Interface** | Xây dựng API và giao diện demo trực quan hóa gợi ý. | **[PENDING]** | Chưa triển khai. |

---

## 3. CÁC QUYẾT ĐỊNH KỸ THUẬT ĐƯỢC DUYỆT (APPROVED DECISIONS)

1. **Giao thức Đánh giá Offline (Evaluation Protocol):**
   - Áp dụng phương pháp **User-wise Leave-1-Last theo Timestamp** (`k_val = 1`, `k_test = 1`) có khóa phụ ổn định `(timestamp ASC, movieId ASC)`.
   - Công bố minh bạch: Giao thức bảo toàn thứ tự thời gian trên từng user cá nhân nhưng chấp nhận giới hạn cross-user temporal leakage để giữ trọn vẹn 100% users cho bài toán Collaborative Filtering.
   - Khi đánh giá Test, tập ứng viên loại trừ toàn bộ các phim user đã xem trong cả Train và Validation: `Candidate_Pool(u) = Catalog \ (Train_u U Val_u)`.
   - Ngưỡng độ thích ban đầu: `rating >= 3.5`. Phân định rõ mẫu số metric khi đánh giá trên nhóm Positive Test Cohort vs Toàn bộ Users.
   - Đánh giá Top-N offline theo batch trên một **tập user đại diện có quy tắc** dùng chung cho mọi mô hình, tránh việc khởi tạo ma trận dự đoán kích thước lớn trong bộ nhớ RAM gây tràn bộ nhớ.
2. **Nguyên tắc Đối chứng Tag Genome:**
   - Tag Genome không được xem là metadata hoàn toàn độc lập với tương tác cộng đồng. Bắt buộc duy trì đối chứng song song: **Genre-only** vs **Genre + Tag Genome** để bóc tách chính xác giá trị thực tế của Genome.
3. **Quy tắc Báo cáo Kết quả ALS:**
   - Phân biệt độc lập giữa **ALS-only (thuần)** và **ALS + Fallback**. Không dùng fallback rồi báo cáo là kết quả của ALS thuần.
4. **Định hướng Công nghệ Đồ thị & Mô hình Lai (Graph & Hybrid Architecture):**
   - Cơ sở dữ liệu đồ thị: Dự kiến sử dụng **Neo4j Community Edition** để lưu trữ các nút `(:Movie)`, `(:Genre)`, `(:Tag)` và các quan hệ.
   - Cơ chế tính điểm đồ thị: Sử dụng thuật toán duyệt đường đi (**Path-based KG Scoring**).
   - Mô hình Hybrid: Kết hợp điểm từ ALS và KG với cơ chế **Candidate Union** (lấy hợp tập các ứng viên hàng đầu từ cả hai nhánh rồi tính điểm kết hợp).

---

## 4. KHO TRI THỨC VÀ BÀI HỌC KINH NGHIỆM ĐÃ KIỂM CHỨNG (VERIFIED KNOWLEDGE)

1. **Môi trường PySpark trên Windows 11:**
   - Phải thiết lập biến môi trường tường minh trước khi khởi tạo SparkSession để trỏ đúng Python worker:
     ```python
     os.environ["PYSPARK_PYTHON"] = sys.executable
     os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
     ```
   - Phải chỉ định `spark.driver.host = "127.0.0.1"` và `spark.driver.bindAddress = "127.0.0.1"` để ngăn lỗi `SocketTimeoutException` trong giao tiếp worker trên Windows.
   - Khi đọc dữ liệu lớn (như 25M ratings), luôn khai báo trước `StructType` schema để tránh chi phí quét `inferSchema`.
2. **Đặc thù Dữ liệu MovieLens 25M:**
   - Có chính xác 16 bản ghi trong `tags.csv` chứa chuỗi ký tự `"NA"` (không phải giá trị rỗng). Cần lưu ý khi đọc dữ liệu để tránh bị parser tự động đổi thành `NaN`.
   - Có 107 phim trong `links.csv` thiếu `tmdbId`.
   - Có 5,062 phim mang nhãn `(no genres listed)`.
   - Toàn bộ 25,000,095 ratings không có bản ghi nào bị trùng lặp cặp `(userId, movieId)`.

---

## 5. RỦI RO KỸ THUẬT & VẤN ĐỀ MỞ (UNRESOLVED RISKS)

1. **Chi phí Tính toán Top-N Full-Catalog Ranking:**
   - Số lượng phim trong danh mục lên tới hơn 62,000 đầu phim. Cần thiết kế mã nguồn đánh giá theo batch có khả năng giải phóng bộ nhớ định kỳ để tránh Out-of-Memory khi tính điểm toàn bộ ứng viên.
2. **Quy mô Cạnh của Đồ thị Tri thức:**
   - Tệp `genome-scores.csv` có 15,584,448 dòng (ma trận dày đặc giữa 13,816 phim và 1,128 tags). Nếu nạp toàn bộ 15.5 triệu quan hệ vào Neo4j sẽ gây nặng nề không cần thiết cho việc truy vấn.
   - *Hướng giải quyết cần xác định ở Phase 6:* Cần xác định ngưỡng cắt lọc `relevance` (ví dụ: chỉ giữ các cạnh có `relevance >= 0.8` hoặc Top-K tag tiêu biểu nhất cho mỗi phim) để đồ thị tập trung vào các liên kết ngữ nghĩa mạnh nhất.
