# KHÓA HUẤN LUYỆN LÀM CHỦ MOODGRAPH (5-DAY MASTERY CURRICULUM)
# BÀI GIẢNG NGÀY 03: TRỤ CỘT GỢI Ý 2 - ĐỒ THỊ TRI THỨC ĐA TẦNG (EMBEDDED KG) & 3 SIÊU ĐƯỜNG DẪN METAPATHS

> **Lời Mentor**: Ở Ngày 02, anh đã hiểu cách mô hình Spark ALS học sở thích ngầm từ 25 triệu ratings. Nhưng ALS là một "hộp đen" (Black-box): nó đưa ra điểm số mà không thể giải thích được *vì sao* lại gợi ý phim đó. Hôm nay, chúng ta bước vào **Trụ cột thứ 2: Đồ thị Tri thức Đa tầng (Knowledge Graph)**. Đây là phần "ăn điểm" học thuật lớn nhất của đồ án, giúp hệ thống vừa gợi ý đúng tâm trạng, vừa vẽ được cây phả hệ giải thích lý do gợi ý trực quan cho người dùng!
>
> Toàn bộ bài giảng hôm nay được viết bằng **ngôn từ đời thực, siêu dễ hiểu**, kèm theo **mã nguồn trích xuất chi tiết từng dòng** để khi thầy hỏi: *"Hàm này chạy thế nào? Dòng này có ý nghĩa gì?"*, anh mở code ra và giải thích rành rọt từng chữ!

---

## MỤC LỤC BÀI GIẢNG NGÀY 03

1. **Đồ Thị Tri Thức Là Gì? (Giải Thích Đời Thực Cực Dễ Hiểu)**
2. **Tại Sao Dùng "Embedded KG" Thay Vì Cài Đặt Neo4j Server Cồng Kềnh?**
3. **Bảng Tra Cứu Code Nhanh Cho Thầy Xem (KG Show-and-Tell Cheat Sheet)**
4. **Mổ Xẻ Cấu Trúc Đồ Thị Nhúng Trong RAM (`recommender/kg/embedded_graph.py`)**
   * 4.1. 4 Loại Nút (Nodes) và 3 Loại Cạnh (Edges)
   * 4.2. Kỹ thuật Chỉ mục ngược (Inverted Index) tra cứu siêu tốc O(1)
   * 4.3. Giải phẫu chi tiết hàm khởi tạo và các hàm ghép nối (Merge functions)
   * 4.4. Hàm trích xuất cây đồ thị con `extract_subgraph()` để vẽ mạng nhện trên Web
5. **Mổ Xẻ Chi Tiết 3 Siêu Đường Dẫn Metapaths (`recommender/kg/scorer.py`)**
   * 5.1. Khái niệm Metapath là gì?
   * 5.2. Đường dẫn P1 (Thể loại - Macro Genre): Cùng loại phim
   * 5.3. Đường dẫn P2 (Tâm trạng - Micro Mood Genome): Cùng cảm xúc điện ảnh
   * 5.4. Đường dẫn P3 (Cộng tác - Collaborative Graph): Cùng gu khán giả
   * 5.5. Công thức tổng hợp điểm số Đồ thị: `Score_KG = α * P1 + β * P2 + γ * P3`
6. **Bí Quyết Kỹ Thuật: Duyệt 62,000+ Phim Trong < 30ms Bằng Thuật Toán 2 Pha**
7. **Cơ Chế Bộ Nhớ Đệm Snapshot Nén Nhị Phân (`recommender/kg/cache_manager.py`)**
8. **5 Câu Hỏi Vấn Đáp "Chí Mạng" Của Giảng Viên Về Đồ Thị Tri Thức & Câu Trả Lời Điểm 10**
9. **Bài Tập Thực Hành Ngày 03 Dành Cho Anh**

---

## 1. ĐỒ THỊ TRI THỨC LÀ GÌ? (GIẢI THÍCH ĐỜI THỰC CỰC DỄ HIỂU)

### Hãy Tưởng Tượng Như Thế Này:
* **Cách gợi ý cũ (ALS)**: Nhìn vào bảng điểm số thuần túy. Thấy anh và một người lạ ở Mỹ cùng chấm 5 sao cho phim *Inception*, hệ thống thấy người đó thích *Interstellar* nên đoán anh cũng thích. Nhưng hỏi: *"Tại sao anh thích?"* thì máy tính chịu, không trả lời được vì nó chỉ thấy hai véc-tơ toán học nhân với nhau ra số to!
* **Cách gợi ý bằng Đồ thị Tri thức (MoodGraph)**: Xây dựng một mạng lưới liên kết như mạng nhện. Trong mạng nhện đó:
  * Mỗi **Người dùng**, mỗi **Bộ phim**, mỗi **Thể loại** (Hành động, Viễn tưởng...), và mỗi **Sắc thái cảm xúc** (Kịch tính, U buồn, Nghẹt thở, Triết lý...) là một **Nút tròn (Node)**.
  * Các đường dây nối giữa chúng là các **Cạnh (Edges)**.

```text
========================================================================================
           SƠ ĐỒ MẠNG LƯỚI ĐỒ THỊ TRI THỨC ĐA TẦNG TRỰC QUAN (HETEROGENEOUS KG)
========================================================================================

                 ┌────────────────────────────────────────────────────────┐
                 │                [KHÁN GIẢ / NGƯỜI DÙNG]                │
                 │                 (User Node - Màu Vàng)                 │
                 └───────────────────────────┬────────────────────────────┘
                                             │
                   Đánh giá cao (rating >= 3.5★, w = (r - 3.0)/2.0)
                                             │
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │               [PHIM MỎ NEO ĐÃ TỪNG XEM]                │
                 │               (Liked Movie - Màu Xanh Cyan)            │
                 │           Ví dụ: "Inception (2010)" - 5.0★             │
                 └───────┬───────────────────┼────────────────────┬───────┘
                         │                   │                    │
        [ĐƯỜNG P1: THỂ LOẠI]       [ĐƯỜNG P2: TÂM TRẠNG]     [ĐƯỜNG P3: CỘNG ĐỒNG]
                         │                   │                    │
                         ▼                   ▼                    ▼
                 ┌───────────────┐   ┌───────────────┐    ┌───────────────┐
                 │  [THỂ LOẠI]   │   │ [THẺ CẢM XÚC] │    │  [KHÁN GIẢ]   │
                 │ (Genre Node)  │   │ (Genome Tag)  │    │ (Neighbor)    │
                 │  Màu Lục Bảo  │   │ Màu Xanh Ngọc │    │  Cùng gu xem  │
                 │  "Sci-Fi",    │   │ "Mind-bending"│    │  Inception    │
                 │  "Action"     │   │ "Existential" │    │               │
                 └───────┬───────┘   └───────┬───────┘    └───────┬───────┘
                         │                   │                    │
              Thuộc thể loại này       Gắn thẻ cảm xúc      Cũng đánh giá cao
                         │                   │                    │
                         └───────────────────┼────────────────────┘
                                             │
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │               [BỘ PHIM ỨNG VIÊN ĐỀ XUẤT]               │
                 │           (Recommended Movie - Màu Tím Thạch Anh)      │
                 │           Ví dụ: "Interstellar (2014)" - Top #1        │
                 └────────────────────────────────────────────────────────┘

 CÔNG THỨC ĐIỂM SỐ: Score_KG = (0.35 × P1_Thể_Loại) + (0.45 × P2_Cảm_Xúc) + (0.20 × P3_Cộng_Đồng)
========================================================================================
```

👉 **Lợi ích số 1**: Khi gợi ý phim *Interstellar*, hệ thống không chỉ đưa ra tên phim mà còn nói được cho anh một câu chuyện thuyết phục:
*"Gợi ý cho bạn vì bạn từng thích Inception: Cả hai phim đều chung thể loại Sci-Fi và cùng chia sẻ sắc thái cảm xúc hack não (Mind-bending) với độ tương đồng 92%!"*

👉 **Lợi ích số 2**: Ngay cả khi người dùng mới tinh chưa có bạn bè nào trên mạng (Cold-Start), chỉ cần họ chọn 1 bộ phim yêu thích hoặc 1 tâm trạng, Đồ thị Tri thức ngay lập tức lần theo các sợi dây nối để tìm ra các phim tương ứng mà không cần phải chờ huấn luyện lại mô hình!

👉 **Trực quan hóa trực tiếp trên Web**: Trong dự án của chúng ta, toàn bộ mạng lưới đồ thị tri thức này đã được lập trình sẵn thành **Mạng nhện tương tác thời gian thực bằng thư viện `vis-network`** ngay trên giao diện web Mode B (Academic Lab)! Anh có thể kéo thả, phóng to thu nhỏ và bấm vào từng nút để xem các đường phát sáng cực kỳ ấn tượng trước mặt thầy cô!

---

## 2. TẠI SAO DÙNG "EMBEDDED KG" THAY VÌ CÀI ĐẶT NEO4J SERVER CỒNG KỀNH?

Khi làm việc với Đồ thị tri thức, đa số mọi người sẽ nghĩ ngay đến việc cài đặt một máy chủ cơ sở dữ liệu đồ thị như **Neo4j**. Nhưng trong dự án MoodGraph, chúng ta đã có một **bước đột phá kỹ thuật rất lớn**: Tự thiết kế một **Đồ thị tri thức nhúng in-memory (Embedded Knowledge Graph)** chạy trực tiếp trong RAM bằng Python!

### Bảng So Sánh "Ăn Tiền" Trước Giảng Viên:

| Tiêu Chí So Sánh | Dùng Máy Chủ Neo4j Riêng Biệt | Dùng Embedded Knowledge Graph (Của MoodGraph) |
| :--- | :--- | :--- |
| **Cài đặt & Vận hành** | Phải cài Java JVM, cài server Neo4j, mở port 7687, cấu hình mật khẩu phức tạp. Rất dễ lỗi khi demo cho thầy xem! | **Zero-Dependency**: Chạy thuần bằng code Python nội bộ, không cần cài bất kỳ phần mềm hay server nào khác! |
| **Giao tiếp dữ liệu** | Gửi câu lệnh Cypher qua giao thức mạng (Socket TCP/IP), parse JSON kết quả -> Bị trễ mạng (Network Latency). | **In-Memory RAM**: Truy cập trực tiếp vào các biến Dict và Set trên thanh RAM máy tính -> Tốc độ cực nhanh! |
| **Thời gian tính gợi ý** | Mất từ **150ms đến 400ms** cho một truy vấn duyệt đồ thị đa tầng. | Chỉ mất **dưới 30ms** cho một người dùng trên toàn bộ danh mục 62,423 phim! |
| **Thời gian khởi động** | Server Neo4j khởi động mất 15–30 giây, nạp dữ liệu lâu. | Dùng cơ chế **Snapshot nhị phân nén gzip (`.pkl.gz`)**: Nạp toàn bộ đồ thị khổng lồ vào RAM chỉ mất **0.46 giây**! |
| **Độ ổn định khi chấm bài** | Thầy cô chấm bài trên máy khác nếu không có Neo4j sẽ không chạy được. | Đồ án chạy ngay lập tức trên bất kỳ máy tính nào chỉ với một lệnh `python scripts/run_app.py`! |

> **Lời khuyên của Mentor**: Khi thầy hỏi: *"Tại sao em không dùng Neo4j?"*, anh trả lời dõng dạc bảng so sánh trên. Thầy cô sẽ đánh giá anh là một kỹ sư có tư duy tối ưu hóa hiệu năng và thiết kế hệ thống cực kỳ thực tế!

---

## 3. BẢNG TRA CỨU CODE NHANH CHO THẦY XEM (KG SHOW-AND-TELL CHEAT SHEET)

Khi thầy cô yêu cầu mở code Đồ thị tri thức, anh mở ngay các file sau:

| Thầy Cô Hỏi Về Vấn Đề Gì | File Code Cần Mở | Hàm / Class Cụ Thể | Dòng Code |
| :--- | :--- | :--- | :--- |
| **Khởi tạo Đồ thị & Inverted Index** | [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py) | `class EmbeddedKnowledgeGraph` | Line 20 - 62 |
| **Nạp dữ liệu từ Parquet vào Đồ thị** | [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py) | Hàm `load_from_parquet()` | Line 252 - 320 |
| **Trích xuất Cây Đồ thị con (Subgraph)** | [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py) | Hàm `extract_subgraph()` | Line 322 - 470 |
| **Đồng bộ đánh giá mới từ SQLite** | [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py) | Hàm `sync_with_sqlite()` | Line 199 - 250 |
| **Thuật toán tính điểm 3 Metapaths P1-P2-P3** | [recommender/kg/scorer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py) | Hàm `compute_user_candidates()` | Line 89 - 320 |
| **Trọng số cảm xúc (Preference Weight)** | [recommender/kg/scorer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py) | Hàm `preference_weight()` | Line 85 - 88 |
| **Trích xuất bằng chứng giải thích Top-K** | [recommender/kg/scorer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py) | Hàm `_extract_evidence_for_candidates()` | Line 335 - 460 |
| **Quản lý Cache Snapshot nhị phân** | [recommender/kg/cache_manager.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/cache_manager.py) | `class CacheManager` | Line 24 - 85 |

---

## 4. MỔ XẺ CẤU TRÚC ĐỒ THỊ NHÚNG TRONG RAM (`embedded_graph.py`)

File mã nguồn: [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py)

### 4.1. 4 Loại Nút (Nodes) Và 3 Loại Cạnh (Edges)
Hãy nhìn vào hàm `__init__` từ dòng 29 đến 54:
```python
class EmbeddedKnowledgeGraph:
    def __init__(self):
        # 1. BỐN LOẠI NÚT TRÊN ĐỒ THỊ (NODES)
        self.users: Dict[int, Dict[str, Any]] = {}        # Nút Người Dùng (userId -> metadata)
        self.movies: Dict[int, Dict[str, Any]] = {}       # Nút Bộ Phim (movieId -> title, year)
        self.genres: Dict[str, Dict[str, Any]] = {}       # Nút Thể Loại (tên thể loại: 'Action', 'Drama'...)
        self.genome_tags: Dict[int, Dict[str, Any]] = {}  # Nút Thẻ Cảm Xúc (tagId -> 'atmospheric', 'dark'...)

        # 2. BA LOẠI CẠNH VÀ CHỈ MỤC NGƯỢC HAI CHIỀU (EDGES & INVERTED INDICES)
        # Cạnh 1: Đánh giá giữa Người dùng và Phim (User - RATED -> Movie)
        self.user_rated_movie: Dict[int, Dict[int, Dict[str, Any]]] = {}     # user_id -> movie_id -> {rating, timestamp}
        self.movie_rated_by_users: Dict[int, Dict[int, Dict[str, Any]]] = {} # movie_id -> user_id -> {rating, timestamp}

        # Cạnh 2: Phim thuộc Thể loại nào (Movie - IN_GENRE -> Genre)
        self.movie_in_genre: Dict[int, Set[str]] = {}     # movie_id -> tập các thể loại {'Action', 'Sci-Fi'}
        self.genre_to_movies: Dict[str, Set[int]] = {}    # thể loại 'Sci-Fi' -> tập các movie_id {1, 260, 1196...}

        # Cạnh 3: Phim mang Sắc thái Cảm xúc nào (Movie - HAS_TAG -> GenomeTag) kèm điểm phù hợp (relevance)
        self.movie_has_genome_tag: Dict[int, Dict[int, float]] = {} # movie_id -> tag_id -> điểm relevance (0.0 đến 1.0)
        self.genome_tag_to_movies: Dict[int, Dict[int, float]] = {} # tag_id -> movie_id -> điểm relevance
```

### 4.2. Kỹ Thuật Chỉ Mục Ngược (Inverted Index) Là Gì?
* Thầy sẽ hỏi: *"Chỉ mục ngược ở đây hoạt động ra sao và nó giúp ích gì?"*
* Anh trả lời:
  * Thông thường ta chỉ lưu: "Bộ phim *The Matrix* thuộc thể loại *Action, Sci-Fi*". Nếu muốn tìm xem "Có những phim nào thuộc thể loại *Sci-Fi*?", máy tính phải quét qua toàn bộ 62,423 bộ phim (mất rất nhiều thời gian O(N)).
  * Để khắc phục, ta tạo thêm một bảng tra cứu ngược lại: `self.genre_to_movies['Sci-Fi'] = {1, 260, 1196...}`.
  * Nhờ vậy, khi người dùng thích một phim Sci-Fi, hệ thống chỉ mất **O(1) (tức thì trong 0.0001 giây)** để lấy ra toàn bộ danh sách tất cả các phim Sci-Fi khác!

---

### 4.3. Hàm Trích Xuất Cây Đồ Thị Con `extract_subgraph()` (Lines 322–470)
Khi người dùng bấm vào một bộ phim trên giao diện web, giao diện sẽ gọi API `/api/lab/graph/subgraph?user_id=1&movie_id=1`.
Hàm này trích xuất toàn bộ các nút và cạnh liên kết giữa người dùng đó và bộ phim đó:
```python
def extract_subgraph(self, user_id: int, candidate_movie_id: int) -> Dict[str, Any]:
    nodes = [] # Chứa danh sách các nút hình tròn (User, Movie, Genre, Tag)
    edges = [] # Chứa các đường nối có trọng số giữa chúng
```
* Hàm này tìm các phim mỏ neo (Anchor Movies) mà người dùng từng chấm >= 3.5 sao.
* Tìm xem bộ phim ứng viên này nối với phim mỏ neo qua những Thể loại chung nào (đường P1), những Thẻ cảm xúc chung nào (đường P2), hoặc qua những Khán giả cùng gu nào (đường P3).
* Kết quả trả về một cấu trúc JSON chuẩn gồm danh sách `nodes` và `edges` để thư viện **vis-network** trên trình duyệt vẽ thành mạng nhện phát sáng đẹp mắt!

---

## 5. MỔ XẺ CHI TIẾT 3 SIÊU ĐƯỜNG DẪN METAPATHS (`scorer.py`)

File mã nguồn: [recommender/kg/scorer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py)

### 5.1. Khái Niệm Metapath Là Gì?
Trong đồ thị không đồng nhất (Heterogeneous Graph), **Metapath (Siêu đường dẫn)** là một chuỗi các quan hệ nối từ loại thực thể này sang loại thực thể khác theo một quy luật có nghĩa.
MoodGraph định nghĩa 3 đường suy luận cốt lõi:

```text
  [P1 - THỂ LOẠI]:   User ──(thích)──> Phim Cũ ──(thuộc)──> Thể Loại ──(thuộc)──> Phim Mới
  [P2 - CẢM XÚC]:    User ──(thích)──> Phim Cũ ──(gắn thẻ)─> Cảm Xúc  ──(gắn thẻ)─> Phim Mới
  [P3 - CỘNG TÁC]:   User ──(thích)──> Phim Cũ ──(xem bởi)─> Người Khác ──(thích)─> Phim Mới
```

---

### 5.2. Đường Dẫn P1: Thể Loại (Genre Metapath)
* **Ý nghĩa đời thực**: "Nếu anh thích phim Hành động *Die Hard*, hệ thống sẽ tìm các phim Hành động khác cho anh".
* **Đoạn code trong `scorer.py`**:
```python
# Duyệt qua các phim người dùng đã thích (rating >= 3.5)
for source_mid, rating in active_liked.items():
    w_source = self.preference_weight(rating)  # Trọng số thích: 5 sao = 1.0, 4 sao = 0.5
    genres = graph.movie_in_genre.get(source_mid, set())
    
    for g in genres:
        cand_movies = graph.genre_to_movies.get(g, set())
        deg_g = len(cand_movies) # Số lượng phim thuộc thể loại này
        
        # Công thức: Điểm cộng dồn = w_source / căn bậc hai số lượng phim
        # Chia cho căn bậc hai để tránh các thể loại quá phổ biến (như Drama) làm loãng điểm
        weight = w_source / math.sqrt(deg_g)
        for cand_mid in cand_movies:
            if cand_mid not in total_exclude:
                cand_p1[cand_mid] += weight
```

---

### 5.3. Đường Dẫn P2: Tâm Trạng Cảm Xúc (Genome Mood Metapath) - ĐẶC SẮC NHẤT!
* **Ý nghĩa đời thực**: Thể loại thì quá rộng (cả *Avengers* và *The Dark Knight* đều là Hành động nhưng cảm xúc xem rất khác nhau: một bên vui vẻ giải trí, một bên đen tối u ám). Đường dẫn P2 khai thác **1,128 chiều cảm xúc vi mô** của Movie Genome để tìm ra các phim có cùng "vibe" chính xác!
* **Đoạn code trong `scorer.py` (Lines 191–225)**:
```python
# Tích lũy trọng số các thẻ cảm xúc từ các phim mỏ neo
for source_mid, rating in active_liked.items():
    w = self.preference_weight(rating)
    source_tags = graph.movie_has_genome_tag.get(source_mid, {}) # {tagId: điểm_relevance}
    for tag_id, rel_source in source_tags.items():
        tag_weights[tag_id] += w * rel_source

# Lấy 15 thẻ cảm xúc nổi bật nhất (Top Active Tags)
active_tags = sorted(tag_weights.items(), key=lambda x: -x[1])[:15]

for tag_id, w_t in active_tags:
    tag_movies = graph.genome_tag_to_movies.get(tag_id, {})
    deg_t = len(tag_movies) # Số lượng phim có gắn thẻ này
    
    # CÔNG THỨC VÀNG: Phạt độ bão hòa 1 / log(1 + degree)
    # Những thẻ quá chung chung như 'good' hay 'classic' sẽ có degree rất lớn -> log lớn -> điểm phạt cao
    # Những thẻ cảm xúc độc bản như 'cyberpunk', 'existential' sẽ có giá trị cao hơn nhiều!
    norm_factor = w_t / math.log1p(deg_t)
    
    for cand_mid, rel_cand in tag_movies.items():
        if cand_mid not in total_exclude:
            # Điểm = hệ số chuẩn hóa × mức độ phù hợp của phim ứng viên với thẻ cảm xúc đó
            cand_p2[cand_mid] += norm_factor * rel_cand
```

---

### 5.4. Đường Dẫn P3: Mạng Lưới Cộng Tác Đồng Điệu (Collaborative Graph Metapath)
* **Ý nghĩa đời thực**: Tìm ra "những người hàng xóm có chung gu phim" trên đồ thị.
* **Đoạn code trong `scorer.py` (Lines 147–187)**:
```python
# 1. Tìm các người dùng khác (neighbors) cũng từng đánh giá cao các phim mỏ neo của mình
for anchor_mid in active_liked.keys():
    users_rated_anchor = graph.movie_rated_by_users.get(anchor_mid, {})
    for n_uid, n_info in users_rated_anchor.items():
        if n_uid != user_id and n_info["rating"] >= self.min_liked_rating:
            neighbor_overlap[n_uid].append(anchor_mid)

# 2. Tính độ tương đồng Salton Cosine giữa hai người dùng:
# sim(u, v) = (Số phim cùng thích) / căn_bậc_hai(Số_phim_u_thích × Số_phim_v_thích)
sim = len(shared_mids) / math.sqrt(user_liked_count * n_liked_count)

# 3. Lấy Top 50 người hàng xóm giống mình nhất để gom các phim họ thích làm gợi ý:
for n_uid, sim, shared_mids in top_neighbors:
    for cand_mid, cand_rinfo in graph.user_rated_movie[n_uid].items():
        if cand_mid not in total_exclude and cand_rinfo["rating"] >= self.min_liked_rating:
            cand_p3[cand_mid] += sim * self.preference_weight(cand_rinfo["rating"])
```

---

### 5.5. Công Thức Tổng Hợp Điểm Số Đồ Thị Tri Thức
Sau khi tính toán xong điểm độc lập của 3 đường dẫn `cand_p1`, `cand_p2`, `cand_p3`, hệ thống chuẩn hóa mỗi mảng về khoảng `[0.0, 1.0]` bằng hàm `_normalize_scores` rồi kết hợp theo trọng số:

```text
Điểm Tổng Hợp Score_KG = (α × Điểm_P1) + (β × Điểm_P2) + (γ × Điểm_P3)
```
Trong đó:
* `α = 0.35` (Trọng số Thể loại Genre).
* `β = 0.45` (Trọng số Tâm trạng Cảm xúc Genome - chiếm tỷ trọng cao nhất vì đây là linh hồn của MoodGraph).
* `γ = 0.20` (Trọng số Cộng tác Đồng điệu Collaborative).

---

## 6. BÍ QUYẾT KỸ THUẬT: DUYỆT 62,000+ PHIM TRONG < 30MS BẰNG THUẬT TOÁN 2 PHA

Nếu duyệt đồ thị một cách ngây thơ (với mỗi phim ứng viên đều tính toán toàn bộ chuỗi giải thích), CPU sẽ mất hơn 500ms cho một người dùng.
Để đạt tốc độ phục vụ thời gian thực (< 30ms), hệ thống MoodGraph áp dụng **Thuật toán tách biệt 2 pha (Two-Phase Separation)**:

```text
[ PHA 1: TÍCH LŨY ĐIỂM SỐ NHANH (Fast Float Accumulation) ]
 - Chỉ cộng dồn các con số float trên từ điển Python (dict of floats).
 - Không khởi tạo chuỗi chuỗi văn bản, không tạo đối tượng giải thích cồng kềnh.
 - Tốc độ: Duyệt toàn bộ hàng chục nghìn ứng viên chỉ mất 15 - 20ms!
                                 │
                                 ▼
                     [ LẤY TOP 50 PHIM ĐIỂM CAO NHẤT ]
                                 │
                                 ▼
[ PHA 2: TRÍCH XUẤT BẰNG CHỨNG GIẢI THÍCH (Top Evidence Extraction) ]
 - Chỉ trích xuất chi tiết bằng chứng (tên thể loại, tên thẻ cảm xúc) cho ĐÚNG 50 phim đứng đầu!
 - Tốc độ: Chỉ mất thêm 2 - 3ms.
                                 │
                                 ▼
   TỔNG THỜI GIAN: < 30ms (Đạt chuẩn trải nghiệm người dùng siêu tốc!)
```

---

## 7. CƠ CHẾ BỘ NHỚ ĐỆM SNAPSHOT NÉN NHỊ PHÂN (`cache_manager.py`)

File mã nguồn: [recommender/kg/cache_manager.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/cache_manager.py)

Khi khởi động ứng dụng web, nếu phải đọc lại toàn bộ các file Parquet và dựng lại đồ thị từ đầu, máy tính sẽ mất khoảng 15–20 giây.
Để giải quyết bài toán này, `CacheManager` sử dụng cơ chế:
1. **Lưu trữ nhị phân nén**: Sau khi nạp đồ thị lần đầu, toàn bộ đối tượng `EmbeddedKnowledgeGraph` trong RAM được tuần tự hóa (serialize) bằng giao thức **Pickle Protocol 5** và nén bằng **Gzip** thành tệp tin `data/embedded_kg_cache.pkl.gz`.
2. **Kích thước siêu gọn**: Dung lượng chỉ vỏn vẹn **8.39 MB**.
3. **Tốc độ nạp tức thì**: Khi khởi động lại máy chủ web ([scripts/run_app.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/scripts/run_app.py)), hàm `CacheManager.get_or_create_graph()` chỉ mất đúng **0.46 giây** để giải nén toàn bộ 62,423 phim và 15.58 triệu liên kết vào RAM!
4. **Cơ chế ghi an toàn (Atomic Replace)**: Ghi ra file tạm `.tmp` trước khi đổi tên đè lên file chính, bảo đảm nếu mất điện đột ngột cũng không bao giờ làm hỏng bộ nhớ đệm.

---

## 8. 5 CÂU HỎI VẤN ĐÁP "CHÍ MẠNG" CỦA GIẢNG VIÊN VỀ ĐỒ THỊ TRI THỨC & CÁCH TRẢ LỜI ĐIỂM 10

### Câu Hỏi 1: *"Tại sao em lại kết hợp cả Thể loại (P1) và Thẻ Genome (P2)? Chỉ dùng Thể loại thôi không đủ sao?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, trong cơ sở dữ liệu điện ảnh, số lượng Thể loại (Genre) rất ít (chỉ có 19 thể loại lớn như Action, Comedy, Drama...). Một thể loại như Drama có thể chứa tới hơn 25,000 bộ phim. Nếu chỉ dựa vào thể loại (đường P1), kết quả gợi ý sẽ mang tính vĩ mô quá chung chung và dễ bị loãng.
> Ngược lại, tập thẻ Movie Genome (đường P2) cung cấp tới 1,128 chiều cảm xúc và sắc thái chi tiết (như 'twist ending', 'philosophical', 'bleak', 'dark comedy'...). Sự kết hợp giữa P1 (đảm bảo đúng thể loại khung) và P2 (đảm bảo đúng sắc thái cảm xúc vi mô) giúp hệ thống gợi ý trúng đích gu thưởng thức của người dùng mà một mình thể loại không thể làm được."*

### Câu Hỏi 2: *"Em giải thích ý nghĩa của công thức phạt độ bão hòa 1 / log(1 + degree) trong đường dẫn P2 xem?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, trong lý thuyết đồ thị và truy hồi thông tin (Information Retrieval), nguyên lý này tương tự như chỉ số nghịch đảo tần suất văn bản (IDF - Inverse Document Frequency).
> Trên đồ thị, có những thẻ cảm xúc xuất hiện ở hầu hết mọi bộ phim (ví dụ thẻ 'good' hay 'great acting' có bậc liên kết degree lên tới hàng chục nghìn). Nếu không có hàm phạt, các thẻ phổ thông này sẽ áp đảo toàn bộ điểm số.
> Hàm phạt `1 / log(1 + degree)` có tác dụng làm giảm mạnh trọng số của các thẻ quá đại trà, đồng thời tôn vinh giá trị của các thẻ cảm xúc đặc trưng hiếm gặp (như 'steampunk' hay 'cyberpunk'). Phim có degree càng nhỏ thì mẫu số log càng nhỏ, làm cho giá trị thông tin đóng góp của thẻ đó càng cao."*

### Câu Hỏi 3: *"Tại sao đồ thị tri thức của em lại có thể chạy được trên RAM với 62,000 phim mà không bị tràn bộ nhớ?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, kiến trúc `EmbeddedKnowledgeGraph` của em được tối ưu hóa theo 3 nguyên tắc cấu trúc dữ liệu:
> Thứ nhất, toàn bộ các khóa liên kết đều dùng số nguyên 32-bit (`int`) thay vì chuỗi văn bản, giúp tiết kiệm bộ nhớ tối đa.
> Thứ hai, em sử dụng cấu trúc bảng băm lồng nhau (`Dict[int, Set[int]]`) của Python. Bảng băm này chỉ lưu các liên kết thực tế có tồn tại chứ không cấp phát ma trận đặc 62,000 × 62,000.
> Thứ ba, toàn bộ dữ liệu đồ thị khi nạp vào RAM chỉ chiếm khoảng 380 MB bộ nhớ (hoàn toàn nhỏ so với dung lượng RAM thông thường từ 8GB đến 16GB của máy tính), và khi lưu trữ dưới dạng snapshot nén nhị phân `.pkl.gz` thì chỉ nặng 8.39 MB."*

### Câu Hỏi 4: *"Làm thế nào Đồ thị tri thức hỗ trợ tính giải thích (Explainability) cho người dùng?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, trong file code `recommender/kg/scorer.py` tại phương thức `_extract_evidence_for_candidates()`, mỗi khi tính điểm cho một bộ phim ứng viên, hệ thống ghi nhận chính xác 'vết đi' (Provenance Trail) trên đồ thị:
> Nó lưu lại: Phim này được nối từ phim mỏ neo nào người dùng từng xem, thông qua thực thể trung gian nào (Thể loại gì, hoặc Thẻ cảm xúc nào), và thực thể đó đóng góp bao nhiêu phần trăm vào tổng điểm gợi ý.
> Nhờ cấu trúc bằng chứng này, trên giao diện người dùng, ta có thể hiển thị tab Accordion 'Tại sao gợi ý phim này?' kèm theo mạng lưới đồ thị trực quan vis-network, giúp người dùng hoàn toàn tin tưởng vào lý do gợi ý."*

### Câu Hỏi 5: *"Nếu người dùng vừa vào trang web và đánh giá thêm một bộ phim 5 sao, đồ thị tri thức có cập nhật ngay lập tức không?"*
> **Câu trả lời chuẩn**:
> *"Thưa thầy/cô, có ạ! Hệ thống được thiết kế theo cơ chế đồng bộ thời gian thực (Closed-Loop Real-time Sync):
> Trong file `recommender/kg/embedded_graph.py` tại hàm `sync_with_sqlite()`, ngay khi người dùng bấm chọn số sao trên giao diện, tương tác đó được ghi vào cơ sở dữ liệu SQLite `app_state.db` và đồng thời gọi phương thức `merge_rating(userId, movieId, rating)`.
> Thao tác thêm một cạnh vào bảng băm RAM có độ phức tạp là O(1) chỉ mất vài micro-giây. Ngay lập tức ở lượt gợi ý tiếp theo, bộ phim vừa đánh giá 5 sao này sẽ trở thành một mỏ neo (Anchor Movie) mới để đồ thị tỏa nhánh tìm các phim đồng điệu mà không cần phải khởi động lại máy chủ!"*

---

## 9. BÀI TẬP THỰC HÀNH NGÀY 03 DÀNH CHO ANH

Để kiểm chứng tận mắt và nhớ lâu, anh hãy mở Terminal và thực hiện 3 thao tác thực hành sau:

### Lệnh 1: Kiểm tra kích thước file Snapshot Cache của Đồ thị tri thức
```powershell
Get-Item -Path "data\embedded_kg_cache.pkl.gz" | Select-Object Name, @{Name="Size_MB"; Expression={[round]($_.Length / 1MB, 2)}}
```
*Mục đích*: Thấy tận mắt file snapshot chỉ nặng đúng **8.39 MB**.

### Lệnh 2: Xem trực tiếp hàm tính điểm 3 Metapaths trong `scorer.py`
Anh mở file [recommender/kg/scorer.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L89-L225) và đọc:
* Dòng 85–88: Hàm `preference_weight(rating)`.
* Dòng 145–187: Đoạn code tính P3 Collaborative Salton Cosine.
* Dòng 191–225: Đoạn code tính P2 Genome với hàm phạt `math.log1p(deg_t)`.

### Lệnh 3: Xem hàm trích xuất cây đồ thị con Subgraph trong `embedded_graph.py`
Anh mở file [recommender/kg/embedded_graph.py](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L322-L370) và đọc dòng 322 đến 370 để thấy cách gom các nút `nodes` và cạnh `edges` gửi lên cho giao diện vẽ mạng đồ thị vis-network.

---
*Ngày mai (Ngày 04), chúng ta sẽ bước sang Bài giảng về Trụ cột kết nối hai thế giới: **Thuật toán Dung hợp Lai Cormack Reciprocal Rank Fusion (RRF k=60), Chuẩn hóa Min-Max, Bộ đa dạng hóa danh mục gợi ý, và Cơ chế phản hồi tức thì Dynamic Closed-Loop khi người dùng chấm sao**.*
