# KIẾN TRÚC HỆ THỐNG GỢI Ý KNOWLEDGE GRAPH (TASK 3B)

> **Tài liệu:** `docs/kg/architecture.md`  
> **Dự án:** MoodGraph: Personalized Movie Recommendation using Knowledge Graphs and Apache Spark  
> **Phiên bản:** 1.0 (Task 3B Specification & Architecture)

---

## 1. TỔNG QUAN KIẾN TRÚC

Hệ thống Knowledge Graph Recommender (Task 3B) chịu trách nhiệm sinh ứng viên gợi ý (**Candidate Generation**) và tính điểm liên quan (**Path-based KG Scoring**) độc lập với nhánh Collaborative Filtering phân tán Spark ALS (Task 3A).

```mermaid
flowchart TD
    subgraph Data Layer ["Lớp Dữ liệu (MovieLens 25M Parquet)"]
        Train["splits/train (Train Ratings Only)"]
        Movies["core/movies"]
        Genres["features/movie_genres"]
        GenomeTags["core/genome_tags"]
        GenomeScores["core/genome_scores (Top-M Filtered)"]
    end

    subgraph Graph Engine ["Neo4j Graph Database (Community Edition)"]
        UserNode["(:User {userId})"]
        MovieNode["(:Movie {movieId, title})"]
        GenreNode["(:Genre {name})"]
        TagNode["(:GenomeTag {tagId, name})"]

        UserNode -->|RATED {rating, timestamp}| MovieNode
        MovieNode -->|IN_GENRE| GenreNode
        MovieNode -->|HAS_GENOME_TAG {relevance}| TagNode
    end

    subgraph Reasoning Layer ["Suy luận Đường đi (Path Reasoning Engine)"]
        P1["P1: User -> Movie -> Genre <- Candidate"]
        P2["P2: User -> Movie -> GenomeTag <- Candidate"]
        P3["P3: User_A -> Movie_X <- User_B -> Candidate"]
    end

    subgraph Scoring & Ranking ["Chấm điểm & Xếp hạng"]
        Weighter["Trọng số sở thích: w(r) = max(0, (r - 3.0) / 2.0)"]
        Scorer["KG Score = α·norm(P1) + β·norm(P2) + γ·norm(P3)"]
        Filter["Lọc phim đã xem trong Train (và Val/Test khi đánh giá)"]
        TopN["Top-N Candidates + Explainable Evidence JSON"]
    end

    Data Layer --> Graph Engine
    Graph Engine --> Reasoning Layer
    Reasoning Layer --> Scoring & Ranking
```

---

## 2. GRAPH DATA MODEL (V1 SPECIFICATION)

### 2.1. Nút (Nodes) & Ràng buộc Khóa duy nhất (Unique Constraints)
Tất cả các label đều có ràng buộc tính duy nhất trên khóa chính:
1. `(:User)`: `userId: int` (Chỉ tạo từ `splits/train`).
2. `(:Movie)`: `movieId: int`, `title: string`, `genresRaw: string` (Tạo từ `core/movies`).
3. `(:Genre)`: `name: string` (Tạo từ `features/movie_genres`).
4. `(:GenomeTag)`: `tagId: int`, `name: string` (Tạo từ `core/genome_tags`).

### 2.2. Quan hệ (Relationships / Edges)
1. `(u:User)-[r:RATED]->(m:Movie)`:
   - Thuộc tính: `rating: float`, `timestamp: long`.
   - **Ranh giới:** Chỉ nạp từ `splits/train` ($24,675,013$ bản ghi). Tuyệt đối cấm nạp từ `splits/validation` hay `splits/test`.
2. `(m:Movie)-[:IN_GENRE]->(g:Genre)`:
   - Thuộc tính: không bắt buộc.
   - Nguồn: `features/movie_genres` ($107,245$ cạnh).
3. `(m:Movie)-[r:HAS_GENOME_TAG]->(t:GenomeTag)`:
   - Thuộc tính: `relevance: float`.
   - Nguồn: `core/genome_scores` ($15,584,448$ cặp).
   - **Chính sách lọc Top-M:** Mỗi phim chỉ giữ tối đa $M$ tags có `relevance` cao nhất ($M \in \{10, 20, 30\}$, tie-break theo `tagId ASC`). Không nạp toàn bộ $15.5$ triệu cạnh mặc định để tránh quá tải bộ nhớ.
4. `(u:User)-[:USER_TAGGED]->(m:Movie)` *(Tùy chọn mở rộng)*:
   - Chỉ dùng `features/tags_train`, không dùng `core/tags`.

---

## 3. CƠ CHẾ TÍNH ĐIỂM DỰA TRÊN ĐƯỜNG ĐI (PATH-BASED SCORING)

### 3.1. Trọng số Sở thích Tích cực (Positive Preference Weight)
Để bảo đảm chỉ những bộ phim người dùng thực sự yêu thích mới được dùng làm nguồn lan truyền tri thức:
$$w(r) = \max\left(0, \frac{r - 3.0}{2.0}\right)$$
Với các rating từ $0.5$ đến $5.0$:
- Rating $5.0 \implies w(r) = 1.0$
- Rating $4.0 \implies w(r) = 0.5$
- Rating $\le 3.0 \implies w(r) = 0.0$ (Bỏ qua, không đóng góp điểm lan truyền)

### 3.2. Điểm thành phần các Metapaths

#### Đường P1: Đồng thể loại (Genre Metapath)
Đường đi: `User -RATED-> Movie_A -IN_GENRE-> Genre <-IN_GENRE- Candidate`
$$S_{P1}(u, c) = \sum_{a \in \mathcal{H}_u} \sum_{g \in \mathcal{G}_a \cap \mathcal{G}_c} \frac{w(r_{u, a})}{\sqrt{|\mathcal{M}_g|}}$$
Trong đó:
- $\mathcal{H}_u$ là tập phim người dùng $u$ đã thích ($w(r) > 0$).
- $\mathcal{G}_x$ là tập thể loại của phim $x$.
- $|\mathcal{M}_g|$ là bậc của thể loại $g$ (tổng số phim thuộc thể loại $g$), đóng vai trò chuẩn hóa (degree normalization) để tránh các thể loại phổ thông (như Drama/Comedy) lấn át.

#### Đường P2: Tương đồng Ngữ nghĩa Tag Genome (Genome Metapath)
Đường đi: `User -RATED-> Movie_A -HAS_GENOME_TAG-> Tag <-HAS_GENOME_TAG- Candidate`
$$S_{P2}(u, c) = \sum_{a \in \mathcal{H}_u} \sum_{t \in \mathcal{T}_a \cap \mathcal{T}_c} \frac{w(r_{u, a}) \cdot \text{rel}(a, t) \cdot \text{rel}(c, t)}{\log(1 + |\mathcal{M}_t|)}$$
Trong đó:
- $\mathcal{T}_x$ là tập GenomeTag Top-M của phim $x$.
- $\text{rel}(x, t)$ là điểm liên quan của tag $t$ đối với phim $x$.
- $|\mathcal{M}_t|$ là số phim gắn tag $t$.

#### Đường P3: Hợp tác Đa bước (Collaborative Graph Metapath)
Đường đi: `User_A -RATED-> Movie_X <-RATED- User_B -RATED-> Candidate`
$$S_{P3}(u, c) = \sum_{v \in \mathcal{N}_u} \text{Sim}(u, v) \cdot w(r_{v, c})$$
Trong đó:
- $\mathcal{N}_u$ là tập người dùng láng giềng có chung các phim đã thích với $u$ ($\ge 2$ phim chung).
- $\text{Sim}(u, v) = \frac{|\mathcal{H}_u \cap \mathcal{H}_v|}{\sqrt{|\mathcal{H}_u| \cdot |\mathcal{H}_v|}}$ (Cosine Overlap trên phim thích).
- **Cơ chế chống nổ số đường đi:** Giới hạn tối đa $K=50$ láng giềng thân cận nhất; loại trừ các hub movie có quá nhiều ratings; giới hạn độ sâu truy vấn.

### 3.3. Điểm tổng hợp & Chuẩn hóa (Final KG Score)
$$S_{KG}(u, c) = \alpha \cdot \text{norm}(S_{P1}) + \beta \cdot \text{norm}(S_{P2}) + \gamma \cdot \text{norm}(S_{P3})$$
- Điều kiện trọng số: $\alpha, \beta, \gamma \ge 0$ và $\alpha + \beta + \gamma = 1.0$.
- Hàm chuẩn hóa $\text{norm}(S)$ thực hiện min-max scaling hoặc softmax trên tập ứng viên của từng người dùng để bảo đảm điểm các nhánh có thang đo tương thích trước khi kết hợp.
- Nếu một ứng viên không có đường đi cho một loại metapath, điểm của metapath đó bằng $0$ (không bịa đặt kết nối).

---

## 4. HỢP ĐỒNG BẰNG CHỨNG GIẢI THÍCH (EXPLAINABLE EVIDENCE CONTRACT)

Mỗi đề xuất $c \in \text{Top-N}$ bắt buộc kèm theo mảng `evidence` chứa các bằng chứng truy vết thực từ đồ thị:

```json
{
  "userId": 42,
  "movieId": 318,
  "raw_score": 0.742,
  "rank": 1,
  "model_name": "KG_PATH",
  "evidence": [
    {
      "path_type": "GENRE",
      "sourceMovieId": 1,
      "sourceMovieTitle": "Toy Story (1995)",
      "sharedEntity": {"type": "Genre", "key": "Animation"},
      "sourceRating": 5.0,
      "contribution": 0.312
    },
    {
      "path_type": "GENOME",
      "sourceMovieId": 296,
      "sourceMovieTitle": "Pulp Fiction (1994)",
      "sharedEntity": {"type": "GenomeTag", "key": 1024, "name": "clever dialog"},
      "sourceRating": 4.5,
      "contribution": 0.285
    },
    {
      "path_type": "COLLABORATIVE",
      "neighborUserId": 1337,
      "anchorMovieId": 1,
      "anchorMovieTitle": "Toy Story (1995)",
      "neighborRating": 5.0,
      "contribution": 0.145
    }
  ]
}
```

---

## 5. HỢP ĐỒNG TÍCH HỢP VỚI KHỐI 4 HYBRID

1. **Python Interface Facade:**
   ```python
   def recommend_kg(
       user_id: int,
       top_n: int = 10,
       exclude_movie_ids: set[int] | None = None
   ) -> list[dict]:
       """
       Sinh danh sách Top-N phim gợi ý dựa trên Knowledge Graph.
       
       Args:
           user_id: ID người dùng cần gợi ý
           top_n: Số lượng phim gợi ý tối đa
           exclude_movie_ids: Tập ID phim cần loại trừ (lịch sử Train, Val...)
           
       Returns:
           Danh sách dict tuân thủ Evidence Contract
       """
   ```

2. **Cơ chế Hợp tập Ứng viên (Candidate Union):**
   - Khối 4 Hybrid sẽ lấy hợp tập: $\mathcal{C}_{hybrid}(u) = \mathcal{C}_{ALS}(u) \cup \mathcal{C}_{KG}(u)$.
   - Điểm `raw_score` của KG và ALS độc lập về mặt phân phối; Khối 4 sẽ chuẩn hóa từng nhánh bằng phân vị hoặc min-max trước khi dung hợp tuyến tính.

