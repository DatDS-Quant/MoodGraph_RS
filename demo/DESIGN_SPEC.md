# ĐẶC TẢ HỆ THỐNG THIẾT KẾ GIAO DIỆN MOODGRAPH (DESIGN SPECIFICATION)
## Dự Án: MoodGraph Phase 6 — Standalone Interactive Web Prototype
**Tác giả**: Worker 1 - Spec & Mock Data Engineer (Teamwork Subagent)  
**Tập dữ liệu chuẩn**: MovieLens 25M (`ml-25m`) & MoodGraph Knowledge Graph Engine  
**Môi trường đích**: Web Prototype Độc Lập (`MoodGraph/tmp/ui_ux_prototype/`)  
**Quy chuẩn tài liệu**: 100% Tiếng Việt chuẩn ngữ pháp, UTF-8. Không sử dụng ký tự LaTeX hay dấu Dollar ($).  
**Quy chuẩn thuật ngữ**: Thuật ngữ Khoa học Dữ liệu & Hệ Thống Gợi Ý (Recommender Systems / AI Lab). Mode A là "Giao diện Khám Phá & Gợi Ý Phim (Movie Discovery & Streaming UI)", Mode B là "Phòng Thí Nghiệm So Sánh Mô Hình Gợi Ý (Recommendation Model Lab / Benchmark Dashboard)" dành cho nghiên cứu sinh và kỹ sư hệ gợi ý.

---

## 1. TỔNG QUAN HỆ THỐNG VÀ ĐỊNH VỊ THẨM MỸ (AESTHETIC PHILOSOPHY)

MoodGraph Phase 6 là giao diện người dùng và bảng điều khiển trực quan hóa cho hệ thống gợi ý phim Big Data tiên tiến trên tập dữ liệu chuẩn MovieLens 25M (25,000,095 tương tác, 162,541 người dùng, 62,423 bộ phim).

Hệ thống sở hữu kiến trúc hai chế độ độc lập (Dual-Mode Architecture) vận hành trên cùng một phiên làm việc:
1. **Mode A — Movie Discovery & Streaming UI**: Trải nghiệm giao diện phong cách Cinematic Dark Theme & Modern Streaming (tương tự trải nghiệm cao cấp của Apple TV+, Netflix, HBO Max nhưng mang đậm bản sắc minh bạch dữ liệu của MoodGraph). Hạt nhân cốt lõi là khả năng giải thích nguồn gốc có kiểm toán (Audited Provenance Typing) qua 4 loại thẻ bằng chứng minh bạch (P1, P2, P3, ALS).
2. **Mode B — Recommendation Model Lab / Benchmark Dashboard**: Phòng thí nghiệm so sánh đối đầu dành cho các nghiên cứu sinh và kỹ sư hệ thống gợi ý (Recommender Systems / AI Lab). Giao diện tối giản, mật độ thông tin cao, phong cách Research Lab kỹ thuật số (tương tự Linear, Grafana, Weights & Biases), phục vụ so sánh song song Top-10 giữa 5 mô hình, phân tích ma trận nhiệt tương quan thứ hạng Spearman [-1.0, 1.0] và tương đồng Jaccard [0.0, 1.0], cùng hai khu vực chẩn đoán suy thoái dữ liệu (Cold-start) và phân phối phim đuôi dài (Long-tail).

### Triết lý Thiết kế Cốt lõi
- **Chân thực và Minh bạch (Radical Transparency & Provenance)**: Không coi gợi ý là một "hộp đen". Mỗi đề xuất đến tay người dùng đều có thể truy vết về đồ thị tri thức hoặc phép chiếu không gian tiềm ẩn.
- **Tương phản Công năng (Functional High Contrast)**: Áp dụng bảng màu nền tối sâu thẳm Obsidian Dark `#090D14` hấp thụ ánh sáng chói, giúp tôn vinh màu sắc poster điện ảnh và các đường dẫn đồ thị phát quang. Đạt chuẩn trợ năng WCAG AAA/AA (tỷ lệ tương phản văn bản tối thiểu 4.5:1, đa phần đạt 7:1).
- **Chất liệu Kính Quang Học (Optical Glassmorphism)**: Bề mặt điều khiển và thẻ nổi sử dụng nền bán trong suốt (`rgba(15, 23, 42, 0.75)` đến `rgba(30, 41, 59, 0.85)`) kết hợp mờ phông nền sâu (`backdrop-blur-xl`) và viền kính siêu mảnh (`border-white/10`), tạo cảm giác sang trọng, có chiều sâu không gian đa tầng.
- **Chính xác Số học (Tabular Monospaced Numbers)**: Toàn bộ số liệu, điểm số, hệ số tương quan, thứ hạng đều sử dụng phông chữ đơn khoảng cách `JetBrains Mono` kết hợp `tabular-nums` để không bị xê dịch bố cục khi số liệu cập nhật.

---

## 2. HỆ THỐNG MÃ MÀU VÀ DESIGN TOKENS

Toàn bộ hệ thống giao diện được định nghĩa thông qua các biến màu và lớp CSS Tailwind nhất quán:

### 2.1. Bảng màu Nền và Bề mặt Không Gian (Cosmic Dark Surfaces)
| Token Name | Mã Hex | Lớp Tailwind CSS | Vai trò Giao diện |
|---|---|---|---|
| `space-dark` | `#070A0F` | `bg-[#070A0F]` | Nền vũ trụ sâu thẳm của toàn bộ trang |
| `obsidian-card` | `#090D14` | `bg-[#090D14]` | Nền bảng điều khiển phòng thí nghiệm Mode B |
| `surface-slate-1` | `#0F172A` | `bg-slate-900` | Bề mặt thẻ phim, bảng điều khiển tầng 1 |
| `surface-slate-2` | `#1E293B` | `bg-slate-800` | Bề mặt nổi (Elevated card), popover, dropdown |
| `surface-glass` | `rgba(15, 23, 42, 0.75)` | `bg-slate-900/75 backdrop-blur-xl` | Bề mặt kính quang học trong suốt |
| `hairline-border` | `rgba(255, 255, 255, 0.08)` | `border-white/10` | Đường kẻ lưới kỹ thuật siêu mảnh 1px |
| `hairline-active` | `rgba(99, 102, 241, 0.40)` | `border-indigo-500/40` | Đường viền khi hover hoặc kích hoạt |

### 2.2. Bảng màu Điểm Nhấn và Tương Tác Điện Ảnh (Cinematic Accents)
| Token Name | Mã Hex | Lớp Tailwind CSS | Ứng dụng |
|---|---|---|---|
| `cinema-indigo` | `#6366F1` | `text-indigo-400 bg-indigo-600` | Nút hành động chính (Primary CTA), tiêu điểm sáng |
| `projector-cyan`| `#38BDF8` | `text-cyan-400 bg-cyan-500` | Chùm sáng máy chiếu, liên kết dữ liệu |
| `star-gold` | `#F59E0B` | `text-amber-400 fill-amber-400` | Đánh giá 0.5 - 5.0 sao, điểm IMDb/TMDb |
| `emerald-watchlist`| `#10B981` | `text-emerald-400 bg-emerald-500` | Trạng thái đã lưu vào danh sách xem (Watchlist) |
| `frost-text` | `#F8FAFC` | `text-slate-50` | Tiêu đề lớn, số liệu quan trọng, độ tương phản cực đại |
| `silver-muted` | `#94A3B8` | `text-slate-400` | Văn bản phụ, tóm tắt phim, nhãn thông số |

---

## 3. ĐẶC TẢ CHI TIẾT 4 LOẠI THẺ GIẢI THÍCH NGUỒN GỐC (AUDITED PROVENANCE TYPING)

Mỗi bộ phim được đề xuất trong Mode A bắt buộc gắn kèm ít nhất một trong 4 loại thẻ giải thích nguồn gốc đã được kiểm toán nghiêm ngặt:

```text
+---------------------------------------------------------------------------------------------------------+
|                                4 LOẠI THẺ PROVENANCE TYPING CÓ KIỂM TOÁN                                |
+-----------------------+-----------------------+-----------------------+---------------------------------+
| P1: GENRE METAPATH    | P2: MOOD & GENOME     | P3: CO-INTERACTION    | ALS: LATENT AFFINITY            |
| Tím Thạch Anh #9333EA | Xanh Ngọc #14B8A6     | Cam Mật Ong #F97316   | Đỏ Neon Crimson #F43F5E         |
| Direct Graph Walk     | Relevance Semantic    | Peer-User Consensus   | Dot Product Projection (Rank=8) |
+-----------------------+-----------------------+-----------------------+---------------------------------+
```

### 3.1. Thẻ P1 — Metapath Thể Loại (Genre Metapath)
- **Mã nhận diện**: `P1_GENRE`
- **Màu sắc chủ đạo**: Tím Thạch Anh (Amethyst Purple)
  * Nền: `#581C87` (`bg-purple-950/80`)
  * Viền: `#9333EA` (`border-purple-600/50`)
  * Chữ: `#C084FC` (`text-purple-300`)
- **Biểu tượng**: Cuộn phim điện ảnh (`Film Reel`) hoặc Thẻ nhãn thể loại
- **Bản chất toán học**: Duyệt đồ thị trực tiếp trên tập Train (`DIRECT_GRAPH_TRAVERSAL`):  
  `User 1 -> [RATED >= 3.5] -> Phim Nguồn -> [IN_GENRE] -> Thể Loại <- [IN_GENRE] <- Phim Đề Xuất`
- **Thông số đi kèm**: Điểm đóng góp thể loại `score_contribution = (Số thể loại chung / Tổng thể loại) * (Rating / 5.0)`
- **Trạng thái kiểm toán**: `VERIFIED_GROUND_TRUTH`, cờ `is_heuristic = false`
- **Ví dụ chuỗi bằng chứng thực tế**:  
  *"Gợi ý vì bạn đã chấm 5.0 sao cho phim 'Lost in Translation', có chung các thể loại: Comedy, Drama, Romance."*

### 3.2. Thẻ P2 — Metapath Tâm Trạng & Genome (Mood / Genome Metapath)
- **Mã nhận diện**: `P2_GENOME`
- **Màu sắc chủ đạo**: Xanh Ngọc Mòng Két (Teal / Emerald Lake)
  * Nền: `#134E4A` (`bg-teal-950/80`)
  * Viền: `#14B8A6` (`border-teal-500/50`)
  * Chữ: `#5EEAD4` (`text-teal-300`)
- **Biểu tượng**: Chuỗi xoắn cảm xúc (`DNA Helix`) hoặc Não bộ trí tuệ (`Brain`)
- **Bản chất toán học**: Khai phá từ 1,128 thẻ gen điện ảnh MovieLens (Genome Tags) với điểm liên quan `target_relevance >= 0.85`:  
  `User 1 -> [RATED >= 3.5] -> Phim Nguồn -> [HAS_GENOME_TAG] -> Tag Cảm Xúc <- [HAS_GENOME_TAG] <- Phim Đề Xuất`
- **Trường hợp xác thực trực tiếp**: `VERIFIED_GROUND_TRUTH`, cờ `is_heuristic = false`
- **Trường hợp xấp xỉ cấu trúc (Honest Heuristic Fallback)**: Khi phim chưa có đường dẫn genome trực tiếp trong đồ thị, hệ thống cam kết **không bịa đặt dữ liệu (Zero Fabrication Guarantee)**, hiển thị nhãn `Ước lượng cấu trúc`, `is_heuristic = true`.
- **Ví dụ chuỗi bằng chứng thực tế**:  
  *"Đường dẫn thẻ genome đã xác thực: Có chung thẻ tâm trạng 'philosophical' (độ liên quan 0.89) và 'existential' với kiệt tác 'The Seventh Seal' mà bạn yêu thích."*

### 3.3. Thẻ P3 — Metapath Đồng Tương Tác (Collaborative Co-interaction Metapath)
- **Màu sắc chủ đạo**: Cam Mật Ong / Hổ Phách (Amber Honey / Warm Bronze)
  * Nền: `#7C2D12` (`bg-orange-950/80`)
  * Viền: `#F97316` (`border-orange-500/50`)
  * Chữ: `#FDBA74` (`text-orange-300`)
- **Biểu tượng**: Mạng lưới người dùng đồng thuận (`Network Nodes / Users`)
- **Bản chất toán học**: Khai phá từ mạng cộng tác hai phía (Bipartite Collaborative Graph):  
  `User 1 -> [RATED >= 3.5] -> Phim Nguồn <- [RATED >= 3.5] <- Người Dùng Đồng Gu #1405 -> [RATED >= 3.5] -> Phim Đề Xuất`
- **Trạng thái kiểm toán**: `VERIFIED_GROUND_TRUTH`, `is_heuristic = false`
- **Ví dụ chuỗi bằng chứng thực tế**:  
  *"Đường dẫn đồng tương tác: Người dùng #1405 trong cộng đồng có cùng thị hiếu đặc biệt (đã cho 5.0 sao 'City of God') cũng đánh giá 5.0 sao cho 'The Godfather'."*

### 3.4. Thẻ ALS — Tích Vô Hướng Vector Tiềm Ẩn (Spark ALS Latent Factor Dot Product)
- **Mã nhận diện**: `LATENT_FACTOR_AFFINITY`
- **Màu sắc chủ đạo**: Đỏ Neon Crimson (Cinema Crimson / Quantum Core)
  * Nền: `#881337` (`bg-rose-950/80`)
  * Viền: `#F43F5E` (`border-rose-500/50`)
  * Chữ: `#FDA4AF` (`text-rose-300`)
- **Biểu tượng**: Tọa độ ma trận lượng tử (`Matrix Cpu / Dot Grid`)
- **Bản chất toán học**: Phân rã ma trận nhân tử tiềm ẩn trên Apache Spark MLlib (Rank=8, Reg=0.3, MaxIter=10):  
  `Điểm ALS(u, i) = Vector_Nguoi_Dung(u) · Vector_Phim(i)`
- **Thông số đi kèm**: Điểm số tích vô hướng (ví dụ `4.312`), Phân vị tương đồng (ví dụ `Top 5%` toàn danh mục), Phiên bản mô hình `ALS_R8_REG0.3_ITER10`.
- **Trạng thái kiểm toán**: `VERIFIED_NUMERICAL_PROJECTION`, `is_heuristic = false`
- **Ví dụ chuỗi bằng chứng thực tế**:  
  *"Điểm tích vô hướng vector thẩm mỹ đạt 4.312 (thuộc nhóm 5% tương đồng cao nhất). Vector gu của bạn có sự trùng khớp đặc trưng trong không gian 8 chiều của bộ phim."*

---

## 4. ĐẶC TẢ 5 MÀU SẮC NHẬN DIỆN MÔ HÌNH TRONG RECOMMENDATION LAB (MODE B)

Trong Mode B, mỗi thuật toán được định danh bằng một màu sắc kỹ thuật riêng biệt, duy trì sự nhất quán xuyên suốt từ tiêu đề cột, biểu đồ, cho đến các ô ma trận nhiệt:

| Tên Thuật Toán | Mã Model | Màu Nhận Diện | Mã Hex | Lớp Tailwind CSS | Vai Trò Kiến Trúc |
|---|---|---|---|---|---|
| **Spark ALS** | `als` | **Cyan Điện Tử** | `#06B6D4` | `text-cyan-400 bg-cyan-950/80 border-cyan-500/50` | Champion Lọc Cộng Tác Ma Trận Tiềm Ẩn (Rank=8) |
| **Knowledge Graph** | `kg` | **Emerald Lục Bảo** | `#10B981` | `text-emerald-400 bg-emerald-950/80 border-emerald-500/50` | Candidate Đồ Thị Tri Thức Đa Bước (P1+P2+P3) |
| **Hybrid RRF (k=60)** | `hybrid_rrf` | **Purple Thạch Anh** | `#8B5CF6` | `text-purple-400 bg-purple-950/80 border-purple-500/50` | Champion Dung Hợp Thứ Hạng Tương Hỗ (Phục vụ Mode A) |
| **Hybrid Weighted** | `hybrid_weighted` | **Amber Hổ Phách** | `#F59E0B` | `text-amber-400 bg-amber-950/80 border-amber-500/50` | Candidate Dung Hợp Tuyến Tính Chuẩn Hóa (50/50) |
| **Popularity Baseline** | `popularity` | **Rose Đỏ Thẫm** | `#F43F5E` | `text-rose-400 bg-rose-950/80 border-rose-500/50` | Baseline Tần Suất Toàn Cục & Cứu Cánh Cold-start |

---

## 5. HỆ THỐNG PHÔNG CHỮ VÀ TYPOGRAPHY (TYPOGRAPHIC HIERARCHY)

Hệ thống kết hợp hai họ phông chữ chuyên biệt:
1. **Phông chữ Giao diện Người dùng (UI & Display Sans)**:  
   `font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;`  
   - Thiết lập tỉ mỉ cho tiêu đề phim, văn bản mô tả, nhãn điều hướng. Cấu trúc ký tự trung tính, độ mở cao, không gây mỏi mắt trong môi trường nền tối.
2. **Phông chữ Dữ liệu & Số học (Monospace Tabular Data)**:  
   `font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, SFMono-Regular, monospace;`  
   `font-variant-numeric: tabular-nums;`  
   - Dùng cho toàn bộ: Điểm số mô hình (0.0328, 4.412), Hệ số tương quan Spearman (-0.8421, null), Phần trăm Jaccard (81.8%), Năm phát hành (1994, 2004), Mã phim (#318, #296), và Độ trễ suy luận (3.28 ms).

### Thang Cỡ Chữ và Kiểu Dáng Chuẩn:
- **Hero Title**: `text-4xl md:text-5xl font-extrabold tracking-tight leading-none text-white drop-shadow-lg`
- **Section Heading**: `text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-3`
- **Movie Card Title**: `text-sm font-semibold text-slate-100 line-clamp-1 group-hover:text-indigo-300 transition-colors`
- **Monospace Metric Value**: `font-mono text-xs md:text-sm font-semibold tabular-nums`
- **Provenance Micro Badge**: `text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full`
- **Body & Synopsis**: `text-xs md:text-sm text-slate-300 leading-relaxed line-clamp-2 md:line-clamp-3`

---

## 6. ĐẶC TẢ CHI TIẾT CÁC THÀNH PHẦN GIAO DIỆN MODE A (DISCOVERY UI)

### 6.1. Universal Header & Navigation Bar
- **Bố cục**: Cố định đỉnh trang (`sticky top-0 z-50`), nền kính `bg-slate-950/80 backdrop-blur-xl border-b border-white/10`.
- **Thành phần**:
  1. **Brand Identity**: Logo MoodGraph kết hợp biểu tượng đồ thị quang học đa giác phát quang và dòng chữ "MoodGraph" in đậm điện ảnh.
  2. **Mode Switcher (Tab Chuyển Đổi Không Tải Lại Trang)**:
     - Nút `Mode A: Khám Phá & Gợi Ý` (Active: nền gradient Indigo-Cyan, text trắng).
     - Nút `Mode B: Phòng Thí Nghiệm So Sánh Mô Hình` (Inactive: text xám bạc `text-slate-400`, hover sáng).
  3. **Universal Search Box**: Ô tìm kiếm nhanh với gợi ý phím tắt `/` hoặc `Ctrl + K`.
  4. **Watchlist Drawer Trigger**: Nút Bookmark kèm badge số lượng phát sáng màu ngọc lục bảo (ví dụ `Watchlist (3)`), bấm vào trượt mở Drawer từ bên phải.
  5. **User Profile Selector**: Avatar bo tròn đại diện cho User 1 (68 phim đã đánh giá), bấm vào mở Modal Hồ Sơ Chi Tiết.

### 6.2. Hero Featured Recommendation Banner
- **Vị trí**: Chiếm 60vh đến 70vh ở đầu trang Mode A.
- **Nội dung**: Hiển thị tác phẩm Top 1 Recommendation của User 1 (*The Shawshank Redemption* hoặc *Inception*).
- **Kỹ thuật Gradient Scrim 3 lớp**:
  - Lớp 1 (Dưới chân): Gradient từ đen tuyền `bg-gradient-to-t from-[#070A0F] via-[#070A0F]/60 to-transparent`.
  - Lớp 2 (Bên trái): Gradient ngang `bg-gradient-to-r from-[#070A0F] via-[#070A0F]/80 to-transparent w-full md:w-3/5` để tôn vinh văn bản.
  - Lớp 3 (Góc trên): Ánh sáng tím dịu (Ambient Radial Indigo Glow).
- **Thành phần trên Banner**:
  - Huy hiệu: `TOP PICK CHO BẠN #1` (vàng kim) • `ĐỘ PHÙ HỢP 98.6%` • `HYBRID: SPARK ALS + ĐỒ THỊ TRI THỨC`.
  - Tiêu đề phim lớn in hoa, năm phát hành, thời lượng, 19 thể loại chính, điểm IMDb/TMDb.
  - Tóm tắt cốt truyện cuốn hút.
  - Hai nút hành động:
    * *Nút Chính*: "Khám Phá & Xem Bằng Chứng Gợi Ý" (Nền gradient Indigo sang Cyan, mở Modal Giải Mã Sâu).
    * *Nút Phụ*: "+ Lưu vào Watchlist" (Nền kính, phản hồi đổi thành "Đã Lưu ✓" ngay lập tức).

### 6.3. Băng Lọc 19 Thể Loại Chuẩn MovieLens 25M
- Thanh trượt ngang hỗ trợ cuộn mượt mà (`overflow-x-auto no-scrollbar scroll-smooth snap-x flex gap-2 py-3`).
- Đầy đủ 19 thể loại chuẩn: *Tất cả, Action, Adventure, Animation, Children, Comedy, Crime, Documentary, Drama, Fantasy, Film-Noir, Horror, Musical, Mystery, Romance, Sci-Fi, Thriller, War, Western, (no genres listed)*.
- Nút thể loại đang chọn nổi bật với nền Indigo sáng (`bg-indigo-600 text-white font-semibold shadow-md shadow-indigo-500/30`), các nút khác mang phong cách kính mờ.
- Lọc tức thì trên lưới phim mà không tải lại trang.

### 6.4. Movie Card Component (Thẻ Phim Chuẩn 2:3)
- **Tỷ lệ**: Chuẩn poster rạp 2:3 (`aspect-[2/3]`).
- **Hiệu ứng Micro-interaction khi Hover**:
  - Thẻ nâng nhẹ lên trên: `transform -translate-y-2 scale-[1.02]`.
  - Đường viền phát quang ánh tím/cyan: `border-indigo-500/50 shadow-xl shadow-indigo-500/20`.
  - Nút "Xem Bằng Chứng" xuất hiện ở giữa thẻ với hiệu ứng kính mờ.
- **Thành phần trên thẻ**:
  - Poster chất lượng cao, có cơ chế tự phục hồi nếu link ảnh lỗi.
  - Góc trên trái: Badge Provenance thu nhỏ (`P1`, `P2`, `P3`, `ALS`) kèm chấm phát quang.
  - Góc trên phải: Nút Bookmark nhanh một chạm (thêm/xóa khỏi Watchlist kèm hiệu ứng nảy).
  - Chân thẻ: Tiêu đề phim (cắt gọn thông minh `truncate`), năm phát hành, điểm số cộng đồng, và điểm đánh giá cá nhân (nếu đã chấm).

### 6.5. Modal Chi Tiết Phim & Bảng Giải Mã Sâu (Deep Explainability Modal)
- **Bố cục**: Cửa sổ phóng to 2 cột đối xứng với phông nền mờ sâu:
  - **Cột Trái**: Poster phim kích thước lớn, thông số chi tiết (Đạo diễn, Thời lượng, Ngôn ngữ), **Hai nút liên kết ngoài chính thức**:
    * `[ IMDb ↗ ]`: Màu vàng IMDb thương hiệu (`#E2B616`), mở trực tiếp đường dẫn IMDb chuẩn xác.
    * `[ TMDb ↗ ]`: Màu xanh ngọc TMDb thương hiệu (`#01B4E4`), mở trực tiếp đường dẫn TMDb chuẩn xác.
    * Khung chấm điểm cá nhân 0.5 - 5.0 sao.
  - **Cột Phải**: Cốt truyện đầy đủ và **Bảng Kiểm Tra Bằng Chứng (Provenance Inspector)** với 4 tab độc lập:
    * *Tab P1*: Danh sách phim nguồn trong lịch sử bạn đã chấm điểm cao có chung thể loại.
    * *Tab P2*: Các thẻ gen tâm trạng chung kèm thanh phần trăm độ liên quan (Relevance Bar).
    * *Tab P3*: Thông tin ẩn danh của người dùng đồng gu (Peer User #1405) và các đánh giá chung.
    * *Tab ALS*: Trực quan hóa điểm tích vô hướng (Dot Product Bar) và phân vị trong toàn danh mục.
    * *Phim Tương Tự (Similar Movies)*: 4 poster nhỏ để tiếp tục khám phá.

### 6.6. Bộ Điều Khiển Chấm Điểm 0.5 - 5.0 Sao (Interactive Star Rating)
- Đúng 10 mức đánh giá tương ứng 5 ngôi sao chia đôi: `0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0`.
- Khi di chuột qua từng nửa sao, ngôi sao sáng rực màu vàng kim `#F59E0B` và hiển thị nhãn cảm xúc trực quan (ví dụ: *4.5★ - Xuất sắc / Tuyệt vời*, *5.0★ - Kiệt tác đỉnh cao*).
- Khi nhấp chọn: Ghi nhận điểm số ngay lập tức, phát hiệu ứng xung nhịp (pulse), bắn thông báo Toast màu xanh ngọc và cập nhật hồ sơ người dùng.

### 6.7. Watchlist Drawer & Toast Notification
- **Watchlist Drawer**:
  - Trượt mượt mà từ mép phải màn hình (`translate-x-0 transition-transform duration-300`).
  - Hiển thị danh sách tất cả các bộ phim đã lưu, poster thu nhỏ, năm phát hành, nút xóa nhanh từng phim và nút xóa sạch toàn bộ danh sách.
  - Trạng thái rỗng hiển thị thông điệp gợi ý thân thiện.
- **Toast Notification**:
  - Nổi ở góc dưới cùng bên phải (`fixed bottom-6 right-6 z-50`).
  - Tự động mờ dần và biến mất sau 3.5 giây.
  - Phản hồi sinh động: *"Đã lưu đánh giá 4.5★ cho Inception (2010)! Vector sở thích đã được cập nhật."* hoặc *"Đã thêm The Godfather vào Danh sách xem."*

### 6.8. Hồ Sơ Người Dùng Mẫu: User 1 (User Profile Modal)
- Minh chứng tính trung thực và không rò rỉ dữ liệu (Zero Data Leakage):
  - Mã người dùng: `User ID #1` (Đại diện tiêu chuẩn từ MovieLens 25M).
  - Tổng số phim đã đánh giá trong tập huấn luyện (Train Split): `68 bộ phim`.
  - Điểm đánh giá trung bình cá nhân: `3.78 sao` (Khán giả có gu nghệ thuật khó tính, tinh tế).
  - Mức độ hoạt động: `Người xem tích cực (Moderate Explorer)`.
  - Biểu đồ phân bổ 18 thể loại: Drama chiếm 75.0% (51 phim), Comedy 32.4% (22 phim), Romance 25.0% (17 phim), Adventure 16.2% (11 phim), Crime 10.3% (7 phim)...
  - Danh sách 10 phim đánh giá gần nhất trong Train (*Lost in Translation* 5.0★, *Requiem for a Dream* 5.0★, *The Seventh Seal* 5.0★, *In the Mood for Love* 5.0★, *City of God* 5.0★...).
  - Mục tiêu kiểm chuẩn độc lập (Held-out Targets): Phim Validation là *Pulp Fiction (1994)* 5.0★, Phim Test là *Eternal Sunshine of the Spotless Mind (2004)* 5.0★.

---

## 7. ĐẶC TẢ CHI TIẾT CÁC THÀNH PHẦN GIAO DIỆN MODE B (RECOMMENDATION LAB)

Mode B là Bảng điều khiển Nghiên cứu chuẩn mực (Research Benchmark Dashboard) dành riêng cho nghiên cứu sinh và kỹ sư hệ thống gợi ý (Recommender Systems / AI Lab).

### 7.1. Lab Control Bar (Thanh Điều Khiển Thí Nghiệm)
- **Vị trí**: Ngay dưới Universal Header.
- **Thành phần**:
  - **Bộ chọn Người dùng Kiểm chuẩn (Cohort User Selector)**: Chuyển đổi giữa 4 kịch bản:
    * `User 1`: Khán giả phim tác giả châu Âu (68 ratings Train, 3.78★ avg)
    * `User 2`: Tín đồ Sci-Fi & Cyberpunk (142 ratings Train, 4.25★ avg)
    * `User 3`: Tín đồ Phim đen & Tội phạm cổ điển (89 ratings Train, 4.10★ avg)
    * `User 42 (Cold-Start)`: Người dùng mới toanh (0 ratings, chỉ chọn tag Onboarding)
  - **Bộ Lọc Đồng Thuận (Consensus Filter)**:
    * `[Tất cả Top-10]` • `[Chỉ hiện Phim Trùng Lặp >= 2 mô hình]` • `[Chỉ hiện Phim Độc Bản (Unique Novelty)]`
  - **Thẻ Đo Độ Trễ Suy Luận (Inference Latency Profile)**:
    * Hiển thị thời gian thực nghiệm: `Spark ALS: 3.28 ms` • `KG: 3.63 ms` • `Hybrid RRF: 3.08 ms` • `Weighted: 2.88 ms` • `Popularity: 0.025 ms`.

### 7.2. Bảng Đối Đầu 5 Mô Hình Song Song (Head-to-Head Top-10 Comparison View)
- **Bố cục Grid**: 5 cột song song (`grid grid-cols-1 md:grid-cols-5 gap-3.5`).
- **Mỗi Cột Mô Hình bao gồm**:
  1. **Header Cột**:
     - Tên mô hình viết hoa đậm nét (`SPARK ALS`, `KNOWLEDGE GRAPH`, `HYBRID RRF`, `HYBRID WEIGHTED`, `POPULARITY BASELINE`).
     - Huy hiệu thuật toán cốt lõi với mã màu đặc trưng (Cyan, Emerald, Purple, Amber, Rose).
     - Thời gian thực thi (ms).
  2. **Thân Cột (Danh sách 10 Micro-Cards)**:
     - Chiều cao mỗi thẻ: 54px, bo góc 8px, viền kính siêu mảnh.
     - Thứ hạng 1..10 in đậm với màu nhận diện của mô hình.
     - Tên phim & Năm phát hành (`text-xs font-semibold text-white truncate`).
     - Thể loại chính của phim (nhãn micro-pill).
     - Điểm số mô hình (hiển thị số thực monospaced 4 chữ số thập phân).
     - Huy hiệu Đồng thuận (Consensus Badge): Hiển thị số lượng mô hình khác cùng đề xuất bộ phim này (ví dụ `x2`, `x3`, `x4`).
  3. **Chân Cột (Column Diagnostic Summary)**:
     - Điểm Novelty trung bình của cột (ví dụ: KG đạt 9.14 bits, Popularity chỉ đạt 3.42 bits).
     - Tỷ lệ phim đuôi dài (Long-tail Ratio: ví dụ KG đạt 60%, Popularity 0%).

### 7.3. Tính Năng Tương Tác Cao Cấp: Hover Interlock (Cross-Model Overlap Highlighting)
Đây là tính năng độc đáo giúp nhà nghiên cứu theo dõi sự dịch chuyển thứ hạng của một bộ phim giữa 5 mô hình:
- **Trạng thái Mặc định**: 5 cột hiển thị Top-10 độc lập.
- **Khi Di Chuột (Hover Interlock)**: Khi người dùng rê chuột vào một bộ phim (ví dụ: *The Godfather (1972)* tại cột Hybrid RRF):
  1. Thẻ *The Godfather* tại cột Hybrid RRF lập tức nhận viền phát sáng màu vàng ấm `#F59E0B` (`ring-2 ring-amber-400 bg-slate-800`).
  2. Hệ thống tức thì tìm kiếm và kích hoạt viền phát sáng đồng bộ trên toàn bộ các thẻ *The Godfather* xuất hiện ở các cột khác:
     * Cột Spark ALS: Vị trí #2 (Score 4.385)
     * Cột Knowledge Graph: Vị trí #10 (Score 0.650)
     * Cột Hybrid Weighted: Vị trí #2 (Score 0.912)
  3. Một dải thông báo liên kết nổi bật hiện ra:  
     `Đồng thuận 4 mô hình: ALS (#2) | KG (#10) | RRF (#2) | Weighted (#2)`
  4. Toàn bộ các bộ phim không liên quan ở cả 5 cột tự động giảm độ đậm (`opacity-35 transition-opacity duration-200`), giúp mắt người nghiên cứu bắt trọn ngay bức tranh phân bổ thứ hạng.
- **Khi Rời Chuột**: Tất cả các thẻ trở lại trạng thái bình thường trong 150ms.

### 7.4. Ma Trận Nhiệt Tương Quan Thứ Hạng Spearman & Tương Đồng Jaccard (Correlation Heatmap)
Ma trận vuông đối xứng 5x5 giúp đánh giá định lượng mức độ tương thích và trực giao giữa các thuật toán:
- **Nút Chuyển Đổi (Segmented Metric Toggle)**:
  - `Hệ Số Tương Quan Spearman (rho)`: Miền giá trị `[-1.0, 1.0]` (Đo mức độ đồng điệu về trật tự ưu tiên).
  - `Độ Tương Đồng Jaccard`: Miền giá trị `[0.0, 1.0]` (Đo mức độ trùng lặp tập hợp ứng viên).
- **Quy Tắc Biên Bắt Buộc Khi Tính Spearman (Mathematical Invariant Rules)**:
  - **Khi số phim chung k < 2 (k = 0 hoặc k = 1)**: Hệ số Spearman không xác định về mặt toán học. Giao diện bắt buộc hiển thị nhãn chữ `null` (màu xám nhạt), **tuyệt đối không hiển thị 0.0 hay số giả tạo**.
  - **Khi k >= 2**: Tính toán trên thứ hạng tương đối 1..k của các phim chung, bảo đảm giá trị luôn nằm nghiêm ngặt trong đoạn `[-1.0, 1.0]`.
- **Thang Màu Phân Kỳ Chuẩn Khoa Học (Diverging Color Scale)**:
  - *Đối với Spearman*:
    * Nghịch biến âm `[-1.0, -0.2]`: Đỏ san hô đến cam đậm (`#EF4444` -> `#F97316`).
    * Trực giao trung tính `(-0.2, 0.2)`: Xám đá Slate (`#1E293B`).
    * Tương quan thuận vừa `[0.2, 0.6]`: Xanh lam dịu (`#3B82F6`).
    * Tương quan thuận mạnh `[0.6, 1.0]`: Lục bảo rực sáng (`#10B981`).
  - *Đối với Jaccard*:
    * Từ đen tím `[0.0, 0.2]` -> Xanh Cyan `[0.2, 0.6]` -> Cyan phát quang `[0.6, 1.0]`.
- **Hiển Thị Trong Từng Ô Ma Trận**:
  - Dòng 1: Con số định lượng (ví dụ: `+0.9250` hoặc `null`).
  - Dòng 2: Tỷ lệ và số lượng phim chung (ví dụ: `9/11 phim` hoặc `k=0`).
  - Tương tác nhấp chuột (Click to Inspect): Nhấp vào ô ma trận mở popover liệt kê đích danh danh sách các bộ phim chung giữa hai mô hình kèm thứ hạng so sánh của từng bên.

### 7.5. Thẻ Phân Tích Chuyên Sâu 1: Kịch Bản Cold-Start (Cold-Start Resilience Suite)
Chẩn đoán phản ứng của 5 mô hình trong các điều kiện dữ liệu khắc nghiệt:
1. **Kịch bản Người dùng Mới Toanh (Zero-History User)**:
   - *Spark ALS*: Thất bại hoàn toàn (Vector người dùng không tồn tại -> Báo lỗi hoặc trả về rỗng). Cần cơ chế ngắt mạch fallback sang Popularity.
   - *Knowledge Graph*: Vẫn hoạt động hiệu quả nhờ bước đi ngẫu nhiên 1-hop từ các thẻ thể loại/tâm trạng người dùng chọn khi onboarding.
   - *Hybrid RRF & Weighted*: Tự động suy thoái êm ái (Graceful Degradation), dồn toàn bộ tỷ trọng sang KG và Popularity.
2. **Biểu Đồ Suy Giảm Hiệu Năng Theo Độ Thưa Thớt (Sparsity Degradation Curve)**:
   - Đường cong biểu diễn NDCG@10 khi rút gọn lịch sử tương tác từ 50 xuống 20, 5, 3, 1 và 0 rating.
   - Minh chứng định lượng: KG giữ vững hiệu năng ổn định (chỉ suy giảm 24% khi N=1) nhờ tri thức tiên nghiệm từ đồ thị, trong khi ALS suy giảm dốc đứng (100% khi N=0).
3. **Phim Mới Chưa Có Lượt Đánh Giá (Unrated New Items)**:
   - ALS không thể gợi ý cho đến chu kỳ huấn luyện lại theo lô.
   - KG gợi ý được ngay lập tức thông qua các cạnh tĩnh `IN_GENRE`, `HAS_GENOME_TAG`.

### 7.6. Thẻ Phân Tích Chuyên Sâu 2: Phân Phối Phim Đuôi Dài (Long-Tail Catalog Exploration)
Khai phá kho tàng 62,423 bộ phim và đo lường khả năng chống lại thiên lệch bom tấn (Popularity Bias):
1. **Độ Phủ Toàn Danh Mục (Catalog Coverage @ 10 & @ 20)**:
   - Trên tập kiểm chuẩn 200 người dùng, tổng số lượng phim độc nhất được giới thiệu:
     * *Knowledge Graph (KG)*: Coverage@10 = **414 phim**, Coverage@20 = **693 phim** (Vô địch về độ phủ, phá vỡ bẫy bong bóng thông tin).
     * *Hybrid Weighted*: Coverage@10 = **295 phim**, Coverage@20 = **539 phim**.
     * *Hybrid RRF*: Coverage@10 = **239 phim**, Coverage@20 = **428 phim**.
     * *Popularity Baseline*: Coverage@10 = **55 phim**, Coverage@20 = **90 phim** (Co cụm ở nhóm bom tấn).
     * *Spark ALS*: Coverage@10 = **14 phim**, Coverage@20 = **32 phim** (Dồn cục do ma trận tiềm ẩn).
2. **Điểm Tính Mới Lạ (Novelty Score theo Lý thuyết Thông tin Shannon)**:
   - `Novelty(i) = -log2(P(i)) = -log2(Ratings_Count(i) / Total_Ratings)`
   - KG đạt trung bình cao nhất: **9.14 bits** (đưa các phim nghệ thuật ngách đến đúng đối tượng).
   - Hybrid RRF đạt: **8.36 bits** (cân bằng hoàn hảo).
   - Popularity chỉ đạt: **3.42 bits** (toàn phim ai cũng biết).
3. **Hệ Số Bất Bình Đẳng Gini (Gini Index)**:
   - Popularity đạt `0.912` (bất bình đẳng cực đoan, chỉ có vài chục phim được gợi ý lặp đi lặp lại).
   - KG và Hybrid RRF hạ Gini xuống mức lành mạnh (`0.412` và `0.528`).
4. **Tỷ Lệ Vàng Đầu Ngắn / Đuôi Dài (Short-Head vs Long-Tail Ratio)**:
   - Hybrid RRF đạt tỷ lệ vàng **60% Short-Head / 40% Long-Tail**: Vừa tạo dựng niềm tin ban đầu bằng các tác phẩm kinh điển quen thuộc, vừa mang lại trải nghiệm khám phá đầy bất ngờ với 40% phim ngách chất lượng cao.

---

## 8. QUY CHUẨN TRỢ NĂNG & HIỆU NĂNG (ACCESSIBILITY & PERFORMANCE)

- **Mở Trực Tiếp Không Cần Máy Chủ (Standalone File Protocol)**: Chạy mượt mà trực tiếp qua giao thức `file:///.../index.html` trên mọi trình duyệt hiện đại (Chrome, Edge, Firefox, Safari).
- **Zero Console Errors**: Đảm bảo không có bất kỳ lỗi JavaScript runtime nào khi thao tác chuyển tab, tìm kiếm, lọc thể loại, hover interlock hay chấm điểm.
- **Tốc Độ Phản Hồi Dưới 16ms (60 FPS Micro-interactions)**:
  - Tìm kiếm và lọc thể loại có phản hồi tức thì với cơ chế debounce 200ms.
  - Hover Interlock đồng bộ cột trong thời gian thực tính bằng microsecond.
- **Tiêu Chuẩn WCAG 2.1 AA/AAA**:
  - Độ tương phản chữ trên nền đạt tối thiểu 4.5:1 đối với văn bản thường và 7:1 đối với số liệu quan trọng.
  - Vùng chạm (Touch Target) trên thiết bị di động đạt tối thiểu 44px x 44px.
  - Hỗ trợ đầy đủ phím tắt bàn phím: `/` để tìm kiếm, `Esc` để đóng modal, `Tab` để di chuyển tiêu điểm.
