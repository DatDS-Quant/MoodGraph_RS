# MoodGraph Phase 5: Dac ta Hop dong API (API Contracts Specification)

## 1. Danh muc Endpoints

| HTTP Method | Endpoint | Nhom Chuc nang | Mo ta |
|-------------|----------|----------------|-------|
| GET | `/health` | He thong | Kiem tra trang thai he thong, so luong phim, tinh san sang cua model |
| POST | `/api/system/cache/clear` | He thong | Xoa sach toan bo cache goi y trong RAM |
| GET | `/api/movies` | Mode A: Discovery | Tim kiem phim theo tieu de, loc the loai, nam phat hanh, phan trang |
| GET | `/api/movies/{movie_id}` | Mode A: Discovery | Chi tiet phim, link IMDb/TMDb, danh sach phim tuong dong |
| GET | `/api/genres` | Mode A: Discovery | Danh sach 19 the loai phim chuan hoa |
| GET | `/api/users` | Mode A: Users | Danh sach mau nguoi dung dai dien cho demo |
| GET | `/api/users/{user_id}/profile` | Mode A: Users | Ho so so thich, phan bo the loai tu tap Train (Zero Leakage) |
| GET | `/api/users/{user_id}/history` | Mode A: Users | Lich su danh gia tu tap Train co phan trang |
| GET | `/api/recommendations/{user_id}` | Mode A: Serving | Goi y ca nhan hoa tuong thich 100% Phase 4 |
| GET | `/api/explanations/{user_id}/{movie_id}` | Mode A: Explain | Giai thich chi tiet theo do thi Metapath va Latent factor |
| GET | `/api/lab/models` | Mode B: Lab | Danh muc cac mo hinh duoc dang ky trong he thong |
| POST | `/api/lab/compare` | Mode B: Lab | So sanh song song cac mo hinh, tinh Jaccard va rank correlation |
| GET | `/api/lab/metrics` | Mode B: Lab | Bang chi so danh gia offline chuan Phase 4 (NDCG, HR, Coverage) |
| GET | `/api/lab/metadata` | Mode B: Lab | Sieu du lieu kich thuoc dataset, so luong split va cau hinh mo hinh |
| POST | `/api/interactions/watchlist` | Tuong tac | Luu phim vao watchlist hoac favorites |
| DELETE | `/api/interactions/watchlist` | Tuong tac | Xoa phim khoi danh sach luu |
| GET | `/api/interactions/watchlist/{user_id}` | Tuong tac | Lay danh sach phim da luu cua nguoi dung |
| POST | `/api/interactions/ratings` | Tuong tac | Gui danh gia demo (0.5 - 5.0 sao) va huy cache goi y |
| GET | `/api/interactions/ratings/{user_id}` | Tuong tac | Lay danh sach danh gia demo da gui |
| POST | `/api/interactions/preferences` | Tuong tac | Luu tuy chinh the loai va khoang nam yeu thich |
| GET | `/api/interactions/preferences/{user_id}` | Tuong tac | Lay thong tin so thich da luu |

---

## 2. Chi tiet Schemas Request & Response

### 2.1. Tra cuu Phim (`GET /api/movies`)
- **Query Parameters:**
  - `query` (string, optional): Tu khoa tim kiem trong tieu de phim.
  - `genre` (string, optional): The loai can loc.
  - `year_min` (int, 1870-2050): Nam phat hanh toi thieu.
  - `year_max` (int, 1870-2050): Nam phat hanh toi da.
  - `page` (int, default=1, ge=1).
  - `page_size` (int, default=20, 1-100).
  - `sort_by` (string, default="title", enum=["title", "year", "movieId"]).
- **Response Format:**
  ```json
  {
    "total": 62423,
    "page": 1,
    "page_size": 20,
    "total_pages": 3122,
    "items": [
      {
        "movieId": 1,
        "title": "Toy Story (1995)",
        "clean_title": "Toy Story",
        "release_year": 1995,
        "genres": ["Adventure", "Animation", "Children", "Comedy", "Fantasy"],
        "links": {
          "imdb_id": "0114709",
          "tmdb_id": "862",
          "imdb_url": "https://www.imdb.com/title/tt0114709",
          "tmdb_url": "https://www.themoviedb.org/movie/862"
        }
      }
    ]
  }
  ```

### 2.2. So sanh Mo hinh (`POST /api/lab/compare`)
- **Request Body:**
  ```json
  {
    "user_id": 1,
    "models": ["als", "kg", "hybrid_rrf", "hybrid_weighted", "popularity"],
    "top_n": 10,
    "filter_seen": true,
    "rrf_k": 60,
    "weight_als": 0.5,
    "weight_kg": 0.5
  }
  ```
- **Response Format:**
  ```json
  {
    "session_id": "lab_exp_1_1794042000",
    "user_id": 1,
    "top_n": 10,
    "results": {
      "als": {
        "model_id": "als",
        "execution_time_ms": 1.25,
        "recommendations_count": 10,
        "recommendations": [...]
      },
      "hybrid_rrf": {
        "model_id": "hybrid_rrf",
        "execution_time_ms": 2.85,
        "recommendations_count": 10,
        "recommendations": [...]
      }
    },
    "pairwise_overlaps": [
      {
        "model_a": "als",
        "model_b": "hybrid_rrf",
        "jaccard_similarity": 0.4286,
        "rank_correlation_spearman": 0.8571,
        "common_movies_count": 6
      }
    ],
    "summary": {
      "models_evaluated": 2,
      "total_comparisons": 1
    }
  }
  ```

### 2.3. Giai thich Goi y (`GET /api/explanations/{user_id}/{movie_id}`)
- **Response Format:**
  ```json
  {
    "userId": 1,
    "movieId": 1,
    "movie_title": "Toy Story (1995)",
    "overall_recommendation_source": "BOTH",
    "graph_explanations": [
      {
        "metapath": "P1_GENRE",
        "score_contribution": 0.45,
        "connecting_entities": [
          {
            "movieId": 260,
            "title": "Star Wars: Episode IV - A New Hope (1977)",
            "user_rating": 4.5,
            "shared_genres": ["Adventure", "Fantasy"]
          }
        ],
        "verbal_explanation": "Recommended because you gave 4.5 stars to 'Star Wars: Episode IV - A New Hope (1977)', sharing the genres: Adventure, Fantasy."
      }
    ],
    "latent_factor_explanation": {
      "dot_product_score": 0.612,
      "model_version": "ALS_R8_REG0.3_ITER10",
      "percentile_alignment": 0.88,
      "verbal_explanation": "Spark ALS latent factor alignment score: 0.612. High dimensional affinity between user taste vector and movie latent features."
    },
    "summary_text": "Movie 'Toy Story (1995)' is recommended based on BOTH signals: combining collaborative behavioral affinity and knowledge graph path reasoning."
  }
  ```
