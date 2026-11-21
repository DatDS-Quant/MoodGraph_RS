# KỊCH BẢN THAO TÁC & LỜI THOẠI DEMO WEB MOODGRAPH
## BẢO VỆ ĐỒ ÁN MÔN GIỚI THIỆU VỀ DỮ LIỆU LỚN — TS. BÙI THANH HÙNG

**Hệ thống thực thi:** MoodGraph (Web App chạy tại `http://localhost:8000`)  
**Mục tiêu kịch bản:** Dẫn dắt Thầy qua 4 màn trình diễn đỉnh cao (Showcase), thao tác tới đâu nói trúng trọng tâm học thuật tới đó, làm nổi bật tính chất Big Data, sức mạnh vượt trội của Đồ thị tri thức (KG) so với Ma trận ẩn (ALS), và tính năng giải thích minh bạch (Explainable AI).

---

## TỔNG QUAN LỘ TRÌNH DEMO (3 - 5 PHÚT)

```text
[ MÀN 1: TỔNG QUAN HỆ THỐNG ] ──> Giới thiệu giao diện điện ảnh, độ trễ < 5ms, 4 thanh trượt gu thẩm mỹ
             │
             ▼
[ MÀN 2: THỬ THÁCH COLD-START ] ──> Chọn tài khoản mới 0 đánh giá: ALS sụp đổ (rỗng), KG cứu vớt thành công
             │
             ▼
[ MÀN 3: TƯƠNG TÁC CLOSED-LOOP ] ──> Chấm 5 sao cho 1 bộ phim: Re-ranking tức thì, đồ thị RAM cập nhật trong 1.5ms
             │
             ▼
[ MÀN 4: GIẢI THÍCH SUBGRAPH ]  ──> Mở mạng lưới đồ thị tri thức, soi từng đường đi P1, P2, P3 minh bạch 100%
```

---

## CHI TIẾT KỊCH BẢN TỪNG BƯỚC: THAO TÁC & LỜI THOẠI ĐAN THÉP

### MÀN 1: MỞ ĐẦU & TRẢI NGHIỆM ĐIỆN ẢNH (MODE A — DISCOVERY FEED)

#### 1. Thao tác trên màn hình:
1. Mở trình duyệt tại địa chỉ `http://localhost:8000`.
2. Màn hình đang ở chế độ mặc định **"Trải Nghiệm Điện Ảnh"** (Mode A).
3. Đưa chuột lướt nhẹ qua biểu ngữ nổi bật (Hero Spotlight Top 1) và lưới phim Top 2 – 10.
4. Bấm vào một chip tâm trạng (ví dụ: **"Trí tuệ"** hoặc **"Hồi hộp"**), sau đó kéo nhẹ thanh trượt **"Chiều sâu cốt truyện"** từ 75% lên 90%.
5. Chỉ tay vào huy hiệu góc phải: **`Độ trễ: 3.2 ms`**.

#### 2. Lời thoại trình bày:
> *"Kính thưa Thầy và Hội đồng, đây là giao diện người dùng của MoodGraph. Ở chế độ phục vụ này, hệ thống sử dụng **Động cơ Gợi ý Lai (Hybrid Recommender Engine)** kết hợp giữa Đồ thị tri thức và Lọc cộng tác Spark ALS.*  
> 
> *Điểm đặc biệt đầu tiên là hệ thống không chỉ gợi ý tĩnh theo thể loại, mà mô hình hóa không gian cảm xúc thông qua **1,128 chiều Tag Genome** và **4 thanh trượt gu thẩm mỹ**: Chiều sâu, Nhịp độ, Bản sắc tác giả và Sắc thái.  
> 
> *Khi em thay đổi tâm trạng hoặc tinh chỉnh thanh trượt, toàn bộ danh sách phim được tái tính toán và re-ranking ngay lập tức trên trình duyệt với **độ trễ chỉ từ 3 đến 5 mili-giây**, mang lại trải nghiệm 60 khung hình/giây siêu tốc mà không cần tải lại trang."*

---

### MÀN 2: "CÚ ĐÒN HỌC THUẬT" — THỬ THÁCH COLD-START VÀ ĐỐI ĐẦU 5 MÔ HÌNH (MODE B)

#### 1. Thao tác trên màn hình:
1. Trên thanh điều hướng trên cùng, bấm vào nút **"Phòng Thí Nghiệm"** (chuyển sang Mode B).
2. Tại thanh chọn đối tượng khán giả (User Selector), chọn **"Khán giả 42 (Cold-Start thuần túy • 0 đánh giá)"** (hoặc "Tài khoản trực tiếp" khi chưa chấm sao).
3. Cuộn màn hình xuống khu vực **"Bảng Đối Đầu 5 Thuật Toán Gợi Ý (Head-to-Head Comparison)"**.
4. Chỉ chuột vào 5 cột mô hình xếp cạnh nhau:
   - Cột 1: *Popularity Baseline*
   - Cột 2: *Spark ALS Champion* ➔ **ĐANG TRỐNG RỖNG / BÁO COLD-START**
   - Cột 3: *Knowledge Graph (P1+P2+P3)* ➔ **XUẤT HIỆN ĐẦY ĐỦ 10 PHIM CHẤT LƯỢNG**
   - Cột 4: *Hybrid RRF (k=60)* ➔ **TỰ ĐỘNG ĐIỀU HÒA BẢO TỒN GỢI Ý**
   - Cột 5: *Hybrid Weighted*

#### 2. Lời thoại trình bày:
> *"Thưa Thầy, để chứng minh giá trị khoa học thực sự của Đồ thị tri thức, em xin chuyển sang **Phòng thí nghiệm Học thuật (Mode B)** và mô phỏng tình huống hóc búa nhất trong hệ gợi ý: **Người dùng mới tinh, chưa từng có đánh giá nào (Cold-Start)**.*  
> 
> *Nhìn vào bảng đối đầu 5 mô hình thực tế đang chạy song song:*
> - *Cột **Spark ALS** hoàn toàn tê liệt và báo rỗng, vì mô hình phân rã ma trận bắt buộc phải có lịch sử tương tác mới chiếu được vector tiềm ẩn.*
> - *Ngược lại, cột **Knowledge Graph** của chúng em vẫn hoạt động xuất sắc. Nhờ vào các mối liên kết thực thể đa tầng giữa Thể loại và Thẻ ngữ nghĩa tâm trạng, đồ thị vẫn dẫn đường và gợi ý được 10 tác phẩm kinh điển phù hợp.*
> - *Và ở cột **Hybrid RRF**, giải thuật dung hợp thứ hạng Cormack k=60 tự động phát hiện nhánh ALS bị khuyết thiếu để lấy tri thức từ KG bù đắp, đảm bảo hệ thống không bao giờ bị trả về trang trắng trước mắt người dùng."*

---

### MÀN 3: TƯƠNG TÁC THỜI GIAN THỰC & TÁI XẾP HẠNG KHÉP KÍN (CLOSED-LOOP RE-RANKING)

#### 1. Thao tác trên màn hình:
1. Bấm quay lại **"Trải Nghiệm Điện Ảnh"** (Mode A).
2. Tại ô tìm kiếm hoặc danh mục Catalog bên dưới, gõ tìm phim **"The Godfather"** (Bố Già) hoặc **"Inception"**.
3. Bấm vào nút đánh giá và chọn **5.0 sao** (Kiệt tác điện ảnh đỉnh cao).
4. Hệ thống hiện thông báo Toast màu vàng hổ phách: *"Đã ghi nhận đánh giá 5.0★... Đồ thị tri thức đã tái tính toán."*
5. Bấm chuyển ngay sang **"Phòng Thí Nghiệm"** (Mode B) và chọn **"Tài Khoản Trực Tiếp (Live Session)"**.
6. Chỉ vào số lượng đánh giá: **`Live Session • 1 đánh giá`**.
7. Cho Thầy thấy: **Cột Spark ALS lập tức sống lại**, và cả 5 cột đều đã được tái xếp hạng đồng loạt theo gu của bộ phim vừa chấm!

#### 2. Lời thoại trình bày:
> *"Bây giờ, em xin trình diễn cơ chế **Tương tác khép kín thời gian thực (Real-time Closed-Loop Feedback)** — một trong những đóng góp kỹ thuật lớn nhất của nhóm:*  
> 
> *Em vừa chấm 5 sao cho bộ phim 'The Godfather'. Trong các hệ thống Big Data thông thường, muốn cập nhật mô hình ALS cho 25 triệu ratings thì phải chờ huấn luyện lại theo lô (batch retrain) mất vài chục phút.*  
> 
> *Nhưng ở MoodGraph, hệ thống triển khai kiến trúc **Embedded Knowledge Graph**:*  
> 1. *Tương tác vừa được lưu tức thì vào SQLite `app_state.db`.*  
> 2. *Bộ nhớ đệm gợi ý cũ bị hủy (Cache Invalidation).*  
> 3. *Đồ thị trong RAM gọi hàm `sync_with_sqlite()`, chèn ngay một cạnh `[:RATED]` mới chỉ trong **1.5 mili-giây**.*  
> 4. *Và như Thầy thấy trên màn hình: Toàn bộ danh sách Top-10 của các mô hình đã tự động xoay trục, tập trung sang các bộ phim cùng đạo diễn Coppola, các kiệt tác hình sự tội phạm như Goodfellas, Scarface chỉ trong tích tắc!"*

---

### MÀN 4: BẰNG CHỨNG MINH BẠCH — MẠNG LƯỚI ĐỒ THỊ CON GIẢI THÍCH (EXPLAINABLE SUBGRAPH)

#### 1. Thao tác trên màn hình:
1. Tại danh sách phim gợi ý (ở Trang 1 hoặc Trang 2), rê chuột vào một bộ phim được gợi ý (ví dụ: *Goodfellas* hoặc *Apocalypse Now*).
2. Bấm vào nút có biểu tượng **Mạng lưới Đồ thị** (hoặc bấm xem chi tiết phim rồi chọn tab "Mạng lưới Tri thức").
3. Một cửa sổ tương tác đồ thị (vis-network) mở ra với các quả cầu màu sắc Obsidian Glassmorphism:
   - Quả cầu Vàng Hổ Phách: **Khán giả của em**
   - Quả cầu Xanh Cyan: **Phim The Godfather em vừa thích (5.0★)**
   - Quả cầu Lục Bảo: **Thể loại Crime / Drama**
   - Quả cầu Xanh Ngọc: **Thẻ tâm trạng 'organized-crime', 'mafia', 'masterpiece'**
   - Quả cầu Tím Thạch Anh: **Phim được đề xuất**
4. Kéo thả các nút đồ thị co giãn trực quan cho Thầy thấy.
5. Chỉ vào dòng chữ giải thích học thuật bên dưới cửa sổ:  
   *`"Được đề xuất bởi tổ hợp Metapath P1 (Đồng thể loại Crime, đóng góp 35%) và Metapath P2 (Cùng mang đặc trưng ngữ nghĩa 'mafia, organized-crime', đóng góp 45%)."`*

#### 2. Lời thoại trình bày:
> *"Thưa Thầy, đây chính là câu trả lời cho bài toán **Explainable AI** trong hệ thống gợi ý:*  
> 
> *Các mô hình hộp đen như Deep Learning hay ALS chỉ có thể trả ra một con số dự đoán vô hồn. Còn MoodGraph có thể trích xuất chính xác **Mạng con đồ thị giải thích (Subgraph)** giải trình minh bạch cho người dùng:*  
> - *Vì sao phim này được gợi ý? Vì người dùng đã thích The Godfather (5 sao).*  
> - *Đi theo con đường nào? Metapath P1 đóng góp 35% qua nút thể loại Crime; Metapath P2 đóng góp 45% qua các nút thẻ tâm trạng 'mafia' và 'organized crime' với độ liên quan trên 0.9.*  
> 
> *Người dùng không chỉ nhận được gợi ý chính xác mà còn hoàn toàn thấu hiểu và tin tưởng vào lý do hệ thống đưa ra quyết định."*

---

### MÀN 5: KẾT THÚC DEMO & MỜI THẦY ĐẶT CÂU HỎI

#### 1. Thao tác trên màn hình:
1. Cuộn nhanh qua **Không gian nhúng 3D Three.js** hoặc **Ma trận tương quan nhiệt Spearman/Jaccard** ở cuối Trang 2 để chứng minh tính hoàn thiện kỹ thuật cao độ.
2. Đưa màn hình về lại bảng đối đầu 5 mô hình.

#### 2. Lời thoại kết thúc:
> *"Dạ thưa Thầy, toàn bộ giao diện tương tác, động cơ đồ thị nhúng và các thuật toán dung hợp lai ghép đều đang vận hành mượt mà, độc lập trên dữ liệu lớn chuẩn MovieLens 25M. Em xin kết thúc phần demo sản phẩm và rất mong nhận được câu hỏi chất vấn từ Thầy và Hội đồng ạ!"*

---

## BẢNG XỬ LÝ NHANH KHI GẶP TÌNH HUỐNG BẤT NGỜ TRONG PHÒNG THI

| Tình huống phát sinh | Cách xử lý thao tác ngay | Câu nói "chữa cháy" chuyên nghiệp |
| :--- | :--- | :--- |
| **Thầy bảo: "Mở code chỗ tính điểm lên cho Thầy xem!"** | Mở ngay file `recommender/kg/scorer.py` và chỉ vào dòng **155 – 294**. | *"Dạ đây ạ, hàm `compute_user_candidates` tính độc lập 3 đường P1, P2, P3 và chuẩn hóa Min-Max kết hợp trọng số 0.35, 0.45, 0.20 tại dòng 290 ạ."* |
| **Thầy bảo: "Tại sao ALS lại có lúc bằng 0 hit?"** | Mở file `docs/3a/M09_diagnostics_report.md` chỉ vào bảng đuôi dài. | *"Dạ thưa Thầy, do hiện tượng Fluke Bias: 51.8% catalog là phim ít hơn 5 rating khiến vector ALS bị phóng đại độ chuẩn, nhóm đã chứng minh bằng thực nghiệm tại Module M09 ạ."* |
| **Trang web bị đơ hoặc tải chậm do máy chiếu** | Nhấn phím `F5` tải lại trang (hệ thống có LocalStorage và Pre-warm cache dưới 0.5s). | *"Hệ thống có bộ đệm Cache Snapshot nén nhị phân nên khởi động lại ngay lập tức trong 0.5 giây ạ."* |

---
*Tài liệu kịch bản chuẩn bị bảo vệ đề tài MoodGraph — Môn Giới thiệu về Dữ liệu lớn (TS. Bùi Thanh Hùng).*
