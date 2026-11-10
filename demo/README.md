# HƯỚNG DẪN NGHIỆM THU BẢN MẪU TƯƠNG TÁC ĐỘC LẬP MOODGRAPH
## Standalone Interactive Web Prototype — Phase 6 UI/UX & Benchmark Lab

**Thư mục làm việc**: `MoodGraph/tmp/ui_ux_prototype/`  
**Đối tượng phục vụ**: Khán giả trải nghiệm điện ảnh (Mode A) & Nghiên cứu sinh, kỹ sư hệ thống gợi ý (Recommender Systems / AI Lab) (Mode B)  
**Tập dữ liệu nền tảng**: MovieLens 25M (`ml-25m`) & MoodGraph Knowledge Graph Engine  
**Kiến trúc vận hành**: 100% Client-side Standalone (Không cần bất kỳ backend server hay môi trường cài đặt)  

---

## 1. HƯỚNG DẪN KHỞI CHẠY VÀ MỞ BẢN MẪU

Bản mẫu được thiết kế để hoạt động hoàn toàn độc lập thông qua giao thức tệp cục bộ (`file:///`):

### Cách 1: Mở Trực Tiếp Trên Trình Duyệt (Khuyên Dùng — Không Cần Cài Đặt)
1. Mở trình duyệt web bất kỳ (Google Chrome, Microsoft Edge, Mozilla Firefox, Safari, Brave...).
2. Kéo thả trực tiếp file sau vào trình duyệt hoặc nhấp đúp chuột để mở:
   ```text
   D:\PROJECT BIG DATA\MoodGraph\tmp\ui_ux_prototype\index.html
   ```
3. Hoặc nhấn tổ hợp phím `Ctrl + O` trên trình duyệt và điều hướng chọn file `index.html`.

### Cách 2: Mở Qua Máy Chủ Tĩnh Tùy Chọn (Tùy Chọn Mở Rộng)
Nếu quý thầy cô hoặc kỹ sư muốn kiểm thử qua cổng HTTP nội bộ:
```powershell
# Chạy với Python 3
cd "D:\PROJECT BIG DATA\MoodGraph\tmp\ui_ux_prototype"
python -m http.server 8080

# Truy cập trình duyệt tại: http://localhost:8080/
```

---

## 2. TỔNG QUAN TÍNH NĂNG VÀ HƯỚNG DẪN TRẢI NGHIỆM

Hệ thống sở hữu cơ chế chuyển đổi hai chế độ tức thì (Zero-Reload Tab Switcher) ngay trên Universal Header:

```text
+---------------------------------------------------------------------------------------------------------+
| [MoodGraph PROTOTYPE]   [Mode A: Khám Phá & Gợi Ý]  [Mode B: Phòng Thí Nghiệm Lab]   [Search] [Watchlist] [User 1] |
+---------------------------------------------------------------------------------------------------------+
```

### 2.1. Chế Độ A — Giao Diện Khám Phá & Gợi Ý Phim (Movie Discovery & Streaming UI)
Định vị phong cách Cinematic Dark Theme sang trọng (Obsidian Dark `#070A0F`, `#090D14`), kết hợp kính quang học (Glassmorphism):

1. **Hero Featured Banner**:
   - Nổi bật tác phẩm Top 1 cá nhân hóa cho User 1 (*The Shawshank Redemption* hoặc *Inception*).
   - Áp dụng kỹ thuật Scrim Gradient 3 lớp giúp văn bản tương phản sắc nét trên mọi hình ảnh nền.
   - Nút hành động chính: *"Khám Phá & Xem Bằng Chứng Gợi Ý"* (mở modal giải thích sâu) và *"+ Lưu vào Watchlist"* (phản hồi trạng thái ngay lập tức).

2. **Thanh Lọc 19 Thể Loại Chuẩn MovieLens 25M & Tìm Kiếm Tức Thì**:
   - Băng trượt ngang 19 thể loại điện ảnh (Action, Adventure, Animation, Comedy, Crime, Drama, Sci-Fi, Thriller...).
   - Nhấp chọn bất kỳ thể loại nào: Lưới phim lập tức lọc lại trong thời gian thực mà không tải lại trang.
   - Thanh tìm kiếm thông minh hỗ trợ phím tắt `/` hoặc `Ctrl + K`.
   - Có trạng thái rỗng thân thiện (Empty State) kèm nút *"Đặt Lại Bộ Lọc"* khi không có kết quả khớp.

3. **Bảng Gợi Ý Cá Nhân Hóa Top-N với 4 Loại Thẻ Giải Thích Nguồn Gốc (Audited Provenance Typing)**:
   - Mỗi bộ phim đề xuất đều gắn huy hiệu minh bạch nguồn gốc:
     * **P1 Thạch Anh Tím (`#9333EA`)**: Metapath Thể loại (Duyệt đồ thị trực tiếp từ phim bạn đã chấm điểm cao).
     * **P2 Xanh Ngọc (`#14B8A6`)**: Metapath Tâm trạng & 1,128 Genome Tags điện ảnh.
     * **P3 Cam Mật Ong (`#F97316`)**: Metapath Đồng tương tác (Người dùng đồng gu #1405 trong cộng đồng).
     * **ALS Đỏ Crimson (`#F43F5E`)**: Tích vô hướng vector thẩm mỹ trong không gian tiềm ẩn Spark ALS (Rank=8).

4. **Modal Chi Tiết Phim & Bảng Giải Mã Sâu (Deep Explainability Modal)**:
   - Nhấp vào bất kỳ phim nào để mở cửa sổ chi tiết 2 cột:
     * *Cột trái*: Poster kích thước lớn, thông số đạo diễn, thời lượng, và **2 nút liên kết ngoài chính thức**:
       + `[ IMDb ↗ ]`: Mở trực tiếp trang IMDb chuẩn xác (`https://www.imdb.com/title/tt...`).
       + `[ TMDb ↗ ]`: Mở trực tiếp trang The Movie Database (`https://www.themoviedb.org/movie/...`).
       + Bộ điều khiển chấm điểm cá nhân 0.5 - 5.0 sao.
     * *Cột phải*: Tóm tắt nội dung đầy đủ và 4 khối chi tiết nguồn gốc (P1, P2, P3, ALS) cùng danh sách phim cùng phong cách nghệ thuật.

5. **Ngăn Kéo Danh Sách Xem (Watchlist Slide-Over Drawer)**:
   - Nhấp vào nút *"Watchlist"* trên thanh Header để trượt mở ngăn kéo từ mép phải màn hình.
   - Quản lý danh sách các phim đã lưu, xóa từng phim hoặc xóa sạch toàn bộ, đồng bộ số đếm tức thì.

6. **Bộ Chấm Điểm 0.5 - 5.0 Sao & Thông Báo Toast**:
   - Thiết kế 5 ngôi sao chia đôi (10 mức nửa sao). Rê chuột để xem nhãn cảm xúc trực quan (*"4.5★ — Xuất sắc / Tuyệt vời"*, *"5.0★ — Kiệt tác đỉnh cao"*).
   - Nhấp chọn: Điểm số được lưu vào hồ sơ, kích hoạt hiệu ứng xung nhịp và bắn Toast phản hồi góc phải màn hình.

7. **Hồ Sơ Người Dùng Mẫu: User 1 (User Profile Modal)**:
   - Bấm vào Avatar User 1 ở góc phải Header để mở Modal kiểm chứng:
     * Thống kê 68 phim đã đánh giá trong tập Train, điểm trung bình cá nhân 3.78 sao.
     * Biểu đồ tỷ lệ phân bổ các thể loại: Drama chiếm 75%, Comedy 32.4%, Romance 25%, Adventure 16.2%...
     * Danh sách các phim đã chấm điểm cao trong tập huấn luyện.
     * Minh chứng không rò rỉ dữ liệu (Zero Data Leakage): Mục tiêu Validation (*Pulp Fiction* 5.0★) và Test (*Eternal Sunshine...* 5.0★) được giấu kín hoàn toàn.

---

### 2.2. Chế Độ B — Phòng Thí Nghiệm So Sánh Mô Hình Gợi Ý (Recommendation Model Lab)
Bảng điều khiển chuyên sâu dành cho nghiên cứu sinh và kỹ sư hệ thống gợi ý (Recommender Systems / AI Lab):

1. **Thanh Điều Khiển Thí Nghiệm (Lab Control Bar)**:
   - Chuyển đổi giữa 4 đoàn hệ người dùng kiểm chuẩn: User 1 (Gu Auteur), User 2 (Sci-Fi), User 3 (Film-Noir), User 42 (Cold-Start người dùng mới toanh).
   - Bộ lọc đồng thuận: `[Tất cả Top-10]`, `[Trùng >= 2 mô hình]`, `[Phim độc bản]`.
   - Thẻ đo độ trễ suy luận thực nghiệm: Spark ALS (3.28 ms), KG (3.63 ms), Hybrid RRF (3.08 ms), Weighted (2.88 ms), Popularity (0.025 ms).

2. **Bảng Đối Đầu Top-10 Song Song Giữa 5 Mô Hình**:
   - 5 cột song song: Spark ALS (Cyan), Knowledge Graph (Emerald), Hybrid RRF (Purple), Hybrid Weighted (Amber), Popularity Baseline (Rose).
   - Mỗi cột gồm 10 thẻ vi mô hiển thị: Thứ hạng 1..10, Tên phim, Năm, Thể loại chính, Điểm số số học monospaced, và Huy hiệu đồng thuận (`x2`, `x3`, `x4`).
   - Chân mỗi cột hiển thị điểm Novelty trung bình và Tỷ lệ phim đuôi dài (Long-tail ratio).

3. **Tính Năng Tương Tác Cao Cấp: Hover Interlock (Cross-Model Overlap Highlighting)**:
   - Rê chuột vào một bộ phim ở bất kỳ vị trí nào (ví dụ: *The Godfather* ở cột Hybrid RRF):
     * Tất cả các vị trí của bộ phim đó trên toàn bộ 4 cột còn lại lập tức sáng rực với viền vàng hổ phách `#F59E0B`.
     * Toàn bộ các bộ phim không liên quan khác mờ xuống 35%, giúp mắt bắt trọn ngay sự dịch chuyển thứ hạng.
     * Dải thông báo trên đầu bảng cập nhật chi tiết:  
       `Đồng thuận 4 mô hình cho "The Godfather": ALS (#2) | KG (#10) | RRF (#2) | WEIGHTED (#2)`

4. **Ma Trận Tương Quan Nhiệt Lưỡng Cực 5x5 (Correlation Heatmap Matrix)**:
   - Nút hoán đổi mượt mà giữa hai góc nhìn toán học:
     * **Hệ Số Tương Quan Thứ Hạng Spearman (ρ) [-1.0, 1.0]**: Thang màu phân kỳ (Đỏ âm -> Xám trung tính -> Xanh lam -> Lục bảo rực rỡ).
     * **Độ Tương Đồng Tập Hợp Jaccard [0.0, 1.0]**: Thang màu đơn cực Cyan phát quang.
   - **Xử lý chuẩn xác quy tắc toán học**: Khi số phim chung giữa 2 mô hình `k < 2` (k = 0 hoặc k = 1), hệ số Spearman không xác định và hiển thị chuẩn nhãn `null` màu xám nhạt (cam kết tuyệt đối không bịa đặt số 0.0 hay số giả).
   - **Tương tác nhấp ô ma trận**: Bấm vào bất kỳ ô giao thoa nào để mở Modal đối chiếu danh sách các bộ phim chung kèm thứ hạng so sánh của từng bên.

5. **Khu Vực Phân Tích Định Lượng Chuyên Sâu**:
   - **Khối Chẩn Đoán Cold-Start**:
     * Đối chiếu hành vi khi gặp người dùng mới toanh (Zero-history user): Spark ALS sập lỗi vector null, Knowledge Graph phát huy bước đi ngẫu nhiên 1-hop, Hybrid tự động suy thoái êm ái sang KG và Popularity.
     * Biểu đồ suy thoái Sparsity Curve khi lịch sử rút gọn từ 50 về 0 đánh giá.
   - **Khối Khai Phá Phim Đuôi Dài (Long-Tail Exploration)**:
     * Biểu đồ so sánh Độ phủ toàn danh mục Catalog Coverage@10 trên 200 người dùng: KG đạt **414 phim** (gấp 7.5 lần Popularity 55 phim).
     * Điểm Novelty Shannon: KG đạt **9.14 bits** so với Popularity chỉ **3.42 bits**.
     * Tỷ lệ vàng của Hybrid RRF: **60% Short-Head / 40% Long-Tail** (cân bằng hoàn hảo giữa tính quen thuộc và sự mới lạ khám phá).

6. **Bảng Chỉ Số Kiểm Chuẩn Offline Thực Nghiệm (Offline Benchmarks Leaderboard)**:
   - Đối chiếu các chỉ số HR@5..20, NDCG@5..20, MRR@5..20, Coverage và Latency đo lường trên đoàn hệ 132 người dùng với Temporal Leave-1-Last Split.

---

## 3. BẢNG ĐỐI SOÁT CÁC TIÊU CHÍ NGHIỆM THU (ACCEPTANCE CRITERIA MATRIX)

| Tiêu Chí | Yêu Cầu Gốc | Hiện Trạng Triển Khai Trong Bản Mẫu | Đánh Giá |
|---|---|---|:---:|
| **R1** | Mode A: Movie Discovery & Streaming UI | Đầy đủ Hero Banner Top 1, Lọc 19 thể loại, Tìm kiếm tức thì, 4 loại thẻ Provenance (P1, P2, P3, ALS), Chi tiết phim kèm link IMDb/TMDb, Watchlist Drawer, Rating 0.5-5.0 sao, Hồ sơ User 1 đối soát Zero Leakage. | **ĐẠT 100%** |
| **R2** | Mode B: Recommendation Model Lab | Bảng đối đầu 5 mô hình Top-10 với Hover Interlock mượt mà, Ma trận nhiệt hoán đổi Spearman (null khi k < 2) và Jaccard, Chẩn đoán Cold-start, Phân tích Long-tail catalog coverage 414 vs 55 phim, Bảng offline benchmarks. | **ĐẠT 100%** |
| **R3** | Standalone Web Prototype | Triển khai hoàn chỉnh bằng HTML5, Tailwind CSS, Vanilla JS và `mock_data.js`. Mở trực tiếp bằng trình duyệt qua `file:///`, không phụ thuộc server, không có lỗi console, có fallback gradient cho poster nếu offline. | **ĐẠT 100%** |
| **R4** | Hồ Sơ Đặc Tả Độc Lập trong Thư Mục Tạm | Đặt toàn bộ trong `MoodGraph/tmp/ui_ux_prototype/` gồm `DESIGN_SPEC.md`, `USER_FLOW.md`, `mock_data.js`, `index.html`, `styles.css`, `app.js`, `README.md`. Không chỉnh sửa mã nguồn chính của dự án. Tuân thủ 100% chuẩn thuật ngữ Khoa học Dữ liệu / Hệ Thống Gợi Ý (Recommender Systems / AI Lab). | **ĐẠT 100%** |

---

## 4. TỔ CHỨC CẤU TRÚC TỆP TIN (FILE STRUCTURE)

```text
MoodGraph/tmp/ui_ux_prototype/
├── index.html                  # Giao diện chính Standalone Single-Page (Mode A + Mode B + Navigation + Drawers)
├── css/
│   └── styles.css              # Stylesheet tùy biến: Glassmorphism, Design Tokens, Heatmap Gradients, Interlock
├── js/
│   ├── mock_data.js            # Kho dữ liệu mẫu chân thực chuẩn hóa MovieLens 25M & Thực nghiệm MoodGraph
│   └── app.js                  # Bộ điều khiển tương tác App Controller: Search, Filter, Modal, Toast, Hover Interlock
├── DESIGN_SPEC.md              # Hồ sơ đặc tả thiết kế chi tiết: Design System, Tokens, Palette, Typography
├── USER_FLOW.md                # Hồ sơ luồng trải nghiệm người dùng & Wireframes bằng biểu đồ Mermaid
└── README.md                   # Tài liệu hướng dẫn mở và nghiệm thu prototype này
```

---

*Bản mẫu web tương tác độc lập đã sẵn sàng 100% để người dùng, giảng viên và hội đồng nghiệm thu.*
