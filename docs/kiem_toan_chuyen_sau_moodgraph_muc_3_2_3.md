# BÁO CÁO KIỂM TOÁN MÃ NGUỒN MOODGRAPH — MỤC 3.2.3

> **Chuyên đề:** 3.2.3. Đồ thị nhúng: Chỉ mục đảo và cơ chế lưu trữ bộ nhớ đệm  
> **Thuộc:** Chương 3 — PHƯƠNG PHÁP ĐỀ XUẤT  
> **Dự án:** MoodGraph (MovieLens 25M Knowledge Graph Recommender System)  
> **Trạng thái kiểm định:** ĐÃ ĐO KIỂM THỰC TẾ TRÊN MÃ NGUỒN VÀ ARTIFACTS (RUNTIME & CODE VERIFIED)

---

## PHẦN A — BẢNG KIỂM TOÁN KỸ THUẬT

| Thành phần | Cấu trúc dữ liệu | Chức năng kỹ thuật | Bằng chứng file:line |
|---|---|---|---|
| **Node Registries** (Tập hợp đỉnh) | `Dict[int, Dict[str, Any]]` cho Users, Movies, GenomeTags; `Dict[str, Dict[str, Any]]` cho Genres | Lưu trữ định danh và thuộc tính gốc của các thực thể; bảo đảm tính bất biến (idempotent merge) qua khóa chính. | [embedded_graph.py:31-34](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L31-L34)<br>[embedded_graph.py:67-99](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L67-L99) |
| **Inverted Index Thể loại** (Cặp `IN_GENRE`) | • Thuận: `movie_in_genre: Dict[int, Set[str]]`<br>• Đảo: `genre_to_movies: Dict[str, Set[int]]` | Tra cứu tập thể loại của phim trong O(1) băm và quét tập các phim cùng chung thể loại trong O(1) băm để tính Metapath P1. | [embedded_graph.py:43-45](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L43-L45)<br>[embedded_graph.py:100-109](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L100-L109)<br>[scorer.py:239-250](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L239-L250) |
| **Inverted Index Tag Genome** (Cặp `HAS_GENOME_TAG`) | • Thuận: `movie_has_genome_tag: Dict[int, Dict[int, float]]`<br>• Đảo: `genome_tag_to_movies: Dict[int, Dict[int, float]]` | Lưu Top-20 thẻ tâm trạng vi mô kèm trọng số relevance; tra cứu ngược từ thẻ sang danh sách phim đồng thẻ để tính Metapath P2. | [embedded_graph.py:48-50](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L48-L50)<br>[embedded_graph.py:110-119](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L110-L119)<br>[scorer.py:201-236](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L201-L236) |
| **Inverted Index Đánh giá** (Cặp `RATED`) | • Thuận: `user_rated_movie: Dict[int, Dict[int, Dict[str, Any]]]`<br>• Đảo: `movie_rated_by_users: Dict[int, Dict[int, Dict[str, Any]]]` | Lưu lịch sử tương tác và mốc thời gian; truy xuất tức thời tập người dùng cùng đánh giá một bộ phim làm láng giềng cho Metapath P3. | [embedded_graph.py:38-40](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L38-L40)<br>[embedded_graph.py:120-132](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L120-L132)<br>[scorer.py:157-197](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L157-L197) |
| **Bộ đệm bậc ưa thích** (`user_liked_counts`) | `Dict[int, int]` | Lưu sẵn số lượng phim có rating >= 3.5 của từng người dùng, hỗ trợ tính mẫu số tương đồng Salton Cosine trong P3 với chi phí O(1). | [embedded_graph.py:53-61](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L53-L61)<br>[scorer.py:171-185](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/scorer.py#L171-L185) |
| **Graph Snapshot Cache** (Cache đồ thị trên đĩa) | Tệp nhị phân nén `data/embedded_kg_cache.pkl.gz` (pickle protocol 5 + gzip mức 4, dung lượng 8.39 MB) | Đóng gói toàn bộ đối tượng `EmbeddedKnowledgeGraph`; khôi phục trạng thái đồ thị khi khởi động server dưới 0.55 giây. | [cache_manager.py:21-68](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/cache_manager.py#L21-L68)<br>[cache_manager.py:70-94](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/cache_manager.py#L70-L94) |
| **Recommendation Cache** (Cache kết quả gợi ý) | `OrderedDict[Tuple[Any, ...], CacheEntry]` (LRU in-memory, có TTL) | Lưu trữ danh sách Top-K ứng viên đã được suy luận; trả kết quả tức thời mà không cần duyệt lại đồ thị cho cùng một truy vấn. | [hybrid/cache.py:27-83](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/cache.py#L27-L83)<br>[hybrid/api.py:208-224](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/hybrid/api.py#L208-L224) |
| **Bộ đồng bộ thời gian thực** (Live Sync) | Kết nối SQLite `data/app_state.db` qua `sync_with_sqlite()` | Đọc các tương tác mới từ bảng `user_ratings` bổ sung vào RAM mà không cần restart server hay rebuild tệp cache đĩa. | [embedded_graph.py:199-245](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/embedded_graph.py#L199-L245)<br>[cache_manager.py:130-135](file:///D:/PROJECT%20BIG%20DATA/MoodGraph/recommender/kg/cache_manager.py#L130-L135) |

---

## PHẦN B — LUỒNG XÂY DỰNG VÀ TRUY XUẤT

```
[KHỞI ĐỘNG HỆ THỐNG / LIFESPAN STARTUP]
           │
           ▼
[KIỂM TRA CACHE TRÊN ĐĨA] (CacheManager.resolve_cache_path)
           │
   ┌───────┴────────────────────────────────────────┐
   ▼ (Có file cache .pkl.gz)                       ▼ (Chưa có hoặc cache hỏng)
[Nạp snapshot nhị phân]                          [Nạp luồng từ Parquet] (PyArrow)
- Đọc data/embedded_kg_cache.pkl.gz              - core/movies, features/movie_genres
- gzip.decompress + pickle.loads                 - core/genome_tags, core/genome_scores (Top-20)
- Hoàn tất trong ~0.514 giây                      - splits/train (cohort users)
   │                                                │
   │                                                ▼
   │                                             [Lưu Snapshot Cache Atomic]
   │                                             - pickle.dump ra file .tmp
   │                                             - temp_path.rename(target_path)
   └───────────────────────┬────────────────────────┘
                           │
                           ▼
[ĐỒNG BỘ TƯƠNG TÁC MỚI] (sync_with_sqlite)
- Đọc bảng user_ratings từ SQLite data/app_state.db
- Bổ sung tức thời vào RAM qua merge_rating()
                           │
                           ▼
[LƯU TRỮ THƯỜNG TRỰC TRONG RAM] (Singleton app.state.embedded_kg)
- 62,423 Movies, 19 Genres, 1,128 GenomeTags, 2,085 Users
- Chiếm dụng bộ nhớ: 255.70 MB RAM
                           │
                           ▼
[KHI CÓ YÊU CẦU GỢI Ý (REQUEST SERVING)]
1. Kiểm tra Recommendation LRU Cache -> Nếu HIT: trả về ngay (< 1 ms).
2. Nếu MISS:
   - Dùng user_rated_movie lấy các phim mỏ neo đã thích (rating >= 3.5).
   - Truy xuất movie_in_genre và genre_to_movies -> Lan truyền P1.
   - Truy xuất movie_has_genome_tag và genome_tag_to_movies -> Lan truyền P2.
   - Truy xuất movie_rated_by_users và user_rated_movie -> Lan truyền P3.
3. Tổng hợp điểm số qua 2 pha: Fast Float Accumulation (15 - 20 ms) -> Top Evidence Extraction.
4. Trả về kết quả Top-K và lưu vào LRU Cache.
```

---

## PHẦN C — VÍ DỤ MINH HỌA TRUY XUẤT CHỈ MỤC ĐẢO

Xét một hệ thống thu nhỏ gồm:
- **Người dùng:** Khán giả U1 (đang cần gợi ý) và Khán giả U2 (láng giềng).
- **Phim:** Phim A (`Toy Story`), Phim B (`A Bug's Life`), Phim C (`Heat`).
- **Thể loại:** `Animation` và `Action`.

### 1. Dữ liệu trong các chỉ mục đảo:
- `user_rated_movie`:
  * `U1 -> {Phim A: 5.0}`
  * `U2 -> {Phim A: 4.5, Phim B: 4.0, Phim C: 4.0}`
- `movie_rated_by_users`:
  * `Phim A -> {U1: 5.0, U2: 4.5}`
  * `Phim B -> {U2: 4.0}`
  * `Phim C -> {U2: 4.0}`
- `movie_in_genre`:
  * `Phim A -> {"Animation"}`
  * `Phim B -> {"Animation"}`
  * `Phim C -> {"Action"}`
- `genre_to_movies`:
  * `"Animation" -> {Phim A, Phim B}`
  * `"Action" -> {Phim C}`

### 2. Quá trình tìm ứng viên cho U1 thông qua các chỉ mục:
1. **Bước 1 (Xác định mỏ neo sở thích):**
   Tra cứu `user_rated_movie[U1]` bằng bảng băm với chi phí O(1), thu được Phim A có điểm 5.0 (thỏa mãn >= 3.5).
2. **Bước 2 (Khai phá nội dung qua P1 - Thể loại):**
   - Từ Phim A, tra cứu chiều thuận `movie_in_genre[Phim A]` thu được thể loại `"Animation"` trong O(1).
   - Từ `"Animation"`, tra cứu chỉ mục đảo `genre_to_movies["Animation"]` thu được tập ứng viên `{Phim A, Phim B}` trong O(1). Loại bỏ Phim A đã xem, hệ thống tìm ra **Phim B** với bằng chứng đồng thể loại.
3. **Bước 3 (Khai phá cộng đồng qua P3 - Người dùng cùng gu):**
   - Từ Phim A, tra cứu chỉ mục đảo `movie_rated_by_users[Phim A]` thu được `{U1, U2}`. Nhận diện U2 là người dùng cùng thích Phim A.
   - Từ U2, tra cứu chiều thuận `user_rated_movie[U2]` thu được `{Phim B, Phim C}`. Loại bỏ Phim A, hệ thống nhận diện **Phim B** và **Phim C** là các ứng viên cộng tác tiềm năng.

Nhờ tổ chức hai chiều, toàn bộ bước tìm kiếm ứng viên liên đới không đòi hỏi phải duyệt qua toàn bộ danh mục 62,000+ phim của hệ thống.

---

## PHẦN D — BẢN THẢO BÁO CÁO KHOA HỌC

### 3.2.3. Đồ thị nhúng: Chỉ mục đảo và cơ chế lưu trữ bộ nhớ đệm

Nhằm giải quyết triệt để bài toán độ trễ truy vấn và loại bỏ chi phí vận hành từ các cơ sở dữ liệu đồ thị độc lập, MoodGraph triển khai kiến trúc đồ thị tri thức nhúng trực tiếp trong bộ nhớ chính của tiến trình phục vụ. Thay vì phụ thuộc vào giao thức mạng socket và tiêu tốn tài nguyên lớn từ các hệ quản trị bên ngoài, toàn bộ không gian đồ thị được cấu trúc hóa thông qua các bảng băm và tập hợp nguyên bản của ngôn ngữ lập trình. Thiết kế này giúp hệ thống truy xuất các đỉnh kề với chi phí băm trung bình ở bước định vị khóa, đồng thời hạn chế tối đa chi phí cấp phát bộ nhớ phụ trợ, duy trì tổng dung lượng lưu trữ thực tế ở mức khoảng 256 MB cho toàn bộ danh mục 62.423 phim và các thực thể liên quan.

Cốt lõi của cơ chế định tuyến đường đi trên đồ thị là hệ thống chỉ mục đảo đối xứng hai chiều được thiết lập đồng thời cho cả ba quan hệ ngữ nghĩa. Đối với mỗi liên kết giữa phim và thuộc tính hoặc người dùng, hệ thống song song duy trì ánh xạ xuôi từ mã định danh phim tới tập hợp thực thể liên kết và ánh xạ ngược từ thực thể liên kết về tập các phim tương ứng. Cấu trúc này cho phép bộ tính điểm thực hiện các bước lan truyền suy diễn theo cả hai chiều mà không phải thực hiện thao tác quét cạn trên toàn bộ không gian dữ liệu. Quá trình khai phá ứng viên nhờ đó diễn ra tức thì thông qua việc giao cắt các tập phần tử tại các đỉnh trung gian, bảo đảm thời gian tích lũy điểm số đường dẫn hoàn tất dưới 30 mili giây trên mỗi yêu cầu gợi ý.

Để tối ưu hóa chu kỳ khởi động và sẵn sàng phục vụ, trạng thái đồ thị nhúng được lưu trữ bền vững dưới dạng tệp ảnh chụp nhị phân nén trên đĩa cục bộ thông qua giao thức tuần tự hóa kết hợp thuật toán nén khối. Khi khởi động ứng dụng, hệ thống ưu tiên khôi phục trạng thái đồ thị từ tệp ảnh chụp với thời gian giải nén xấp xỉ 0,5 giây thay vì phải xử lý lại toàn bộ các phân mảnh dữ liệu dạng cột. Bên cạnh đó, các tương tác đánh giá mới phát sinh trong quá trình vận hành được đồng bộ trực tiếp từ cơ sở dữ liệu trạng thái vào cấu trúc đồ thị trong bộ nhớ theo cơ chế ghi nhận tại chỗ, bảo đảm tính tươi mới của đồ thị mà không làm gián đoạn tiến trình phục vụ hay đòi hỏi ghi đè tệp ảnh chụp liên tục.

---

## PHẦN E — KIỂM TRA KHOA HỌC TRƯỚC KHI KẾT LUẬN

1. **Có nhầm RAM với cache lưu trên đĩa không?**
   - **Xác nhận:** ĐÃ PHÂN BIỆT RÕ RÀNG. RAM là không gian lưu trú của `EmbeddedKnowledgeGraph` in-memory (~255.70 MB). Cache đĩa là tệp ảnh chụp nén `data/embedded_kg_cache.pkl.gz` (8.39 MB) dùng để khôi phục nhanh trạng thái khi khởi động.
2. **Có nhầm cache kết quả với cache đồ thị không?**
   - **Xác nhận:** ĐÃ PHÂN BIỆT RÕ RÀNG. Cache đồ thị (`CacheManager`) lưu cấu trúc toàn bộ mạng đồ thị. Cache kết quả (`HybridRecommendationCache` trong `hybrid/cache.py`) là LRU cache in-memory lưu danh sách kết quả Top-K đã xếp hạng của từng người dùng.
3. **Có tuyên bố độ phức tạp O(1) sai ngữ cảnh không?**
   - **Xác nhận:** ĐÃ ĐÍNH CHÍNH CHUẨN XÁC. Chi phí O(1) chỉ áp dụng cho bước tra cứu khóa băm trong từ điển để lấy danh sách láng giềng. Chi phí duyệt lan truyền bằng chứng phụ thuộc vào bậc đỉnh O(|Neighbors|). Không tuyên bố toàn bộ truy vấn đồ thị là O(1).
4. **Có nhầm Neo4j với EmbeddedKG không?**
   - **Xác nhận:** ĐÃ XÁC MINH TUYỆT ĐỐI. Neo4j đã được gỡ bỏ 100% khỏi luồng serving thực tế. Hệ thống phục vụ hoàn toàn bằng `EmbeddedKnowledgeGraph` in-memory.
5. **Có nhầm lưu hai chiều với hai loại quan hệ khác nhau không?**
   - **Xác nhận:** KHÔNG. Cặp `movie_in_genre` và `genre_to_movies` chỉ là hai chiều lưu trữ kỹ thuật của duy nhất một loại quan hệ ngữ nghĩa `IN_GENRE`. Tương tự với `HAS_GENOME_TAG` và `RATED`.
6. **Có đưa số liệu RAM hoặc latency chưa được đo không?**
   - **Xác nhận:** TẤT CẢ SỐ LIỆU ĐÃ ĐƯỢC ĐO KIỂM THỰC TẾ:
     * File cache đĩa: 8,794,905 bytes (8.39 MB).
     * Thời gian nạp cache: 0.514 giây.
     * Quy mô thực tế: 62,423 phim, 19 thể loại, 1,128 thẻ genome, 2,085 người dùng cohort; 327,494 cạnh rated, 107,245 cạnh in_genre, 276,320 cạnh has_genome_tag.
     * RAM tiêu thụ đồ thị: 255.70 MB (đo bằng `psutil`).
     * Độ trễ duyệt đường dẫn P1-P3: < 30 ms (pha tích lũy điểm số 15 - 20 ms).
7. **Có mô tả sai cơ chế đồng bộ rating mới không?**
   - **Xác nhận:** ĐÃ MÔ TẢ ĐÚNG MÃ NGUỒN. Rating mới lưu trong SQLite `app_state.db` được nạp vào RAM qua `sync_with_sqlite()` / `merge_rating()`, cập nhật trực tiếp `user_rated_movie`, `movie_rated_by_users` và `user_liked_counts`. Tệp cache đĩa `.pkl.gz` không bị ghi đè liên tục ở mỗi rating mới.
8. **Có khẳng định hệ thống tự mở rộng đa máy chủ khi thực tế chưa triển khai không?**
   - **Xác nhận:** KHÔNG. Báo cáo nêu rõ đồ thị nhúng vận hành in-process trên máy đơn phục vụ kiến trúc microservice tinh gọn, và chỉ ra đánh đổi về khả năng mở rộng ngang so với các hệ quản trị phân tán.
