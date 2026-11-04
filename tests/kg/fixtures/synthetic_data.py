"""
MoodGraph Task 3B: Synthetic Data Fixtures (Section 2.2 Spec)

Fixture tự xây dựng phục vụ kiểm thử đơn vị, kiểm thử tích hợp và tính toán đối chuẩn:
- 4 Users:
    - User 1: Fan phim hoạt hình, đã đánh giá Movie 1 (5.0), Movie 2 (4.5).
    - User 2: Đã đánh giá Movie 1 (5.0), Movie 3 (4.0). Nối collaborative P3 sang User 1.
    - User 3: Đã đánh giá Movie 4 (2.0 - rating thấp), Movie 5 (5.0 - phim hình sự).
    - User 4: User không có tương tác nào trong tập train (no-history user).
- 7 Movies:
    - Movie 1: "Toy Story Clone" (Genres: Animation, Children)
    - Movie 2: "Finding Nemo Clone" (Genres: Animation)
    - Movie 3: "Monsters Inc Clone" (Genres: Animation, Comedy)
    - Movie 4: "Dark Crime" (Genres: Crime)
    - Movie 5: "Godfather Clone" (Genres: Crime)
    - Movie 6: "Cold Start Indie" (Genre: Animation, không có lượt rating nào trong train)
    - Movie 7: "Isolated Mystery" (Không thể loại, không genome, không ratings)
- 4 Genres:
    - Animation, Children, Comedy, Crime
- 4 GenomeTags:
    - 1: "pixar", 2: "family friendly", 3: "mafia", 4: "unusual tag"
"""

SYNTHETIC_USERS = [
    {"userId": 1},
    {"userId": 2},
    {"userId": 3},
    {"userId": 4},
]

SYNTHETIC_MOVIES = [
    {"movieId": 1, "title": "Toy Story Clone (1995)", "genresRaw": "Animation|Children"},
    {"movieId": 2, "title": "Finding Nemo Clone (2003)", "genresRaw": "Animation"},
    {"movieId": 3, "title": "Monsters Inc Clone (2001)", "genresRaw": "Animation|Comedy"},
    {"movieId": 4, "title": "Dark Crime (1990)", "genresRaw": "Crime"},
    {"movieId": 5, "title": "Godfather Clone (1972)", "genresRaw": "Crime"},
    {"movieId": 6, "title": "Cold Start Indie (2020)", "genresRaw": "Animation"},
    {"movieId": 7, "title": "Isolated Mystery (2021)", "genresRaw": "(no genres listed)"},
]

SYNTHETIC_GENRES = [
    {"name": "Animation"},
    {"name": "Children"},
    {"name": "Comedy"},
    {"name": "Crime"},
]

SYNTHETIC_MOVIE_GENRES = [
    {"movieId": 1, "genre": "Animation"},
    {"movieId": 1, "genre": "Children"},
    {"movieId": 2, "genre": "Animation"},
    {"movieId": 3, "genre": "Animation"},
    {"movieId": 3, "genre": "Comedy"},
    {"movieId": 4, "genre": "Crime"},
    {"movieId": 5, "genre": "Crime"},
    {"movieId": 6, "genre": "Animation"},
]

SYNTHETIC_GENOME_TAGS = [
    {"tagId": 1, "tag": "pixar"},
    {"tagId": 2, "tag": "family friendly"},
    {"tagId": 3, "tag": "mafia"},
    {"tagId": 4, "tag": "unusual tag"},
]

SYNTHETIC_GENOME_SCORES = [
    {"movieId": 1, "tagId": 1, "relevance": 0.95},
    {"movieId": 1, "tagId": 2, "relevance": 0.85},
    {"movieId": 2, "tagId": 1, "relevance": 0.90},
    {"movieId": 2, "tagId": 2, "relevance": 0.80},
    {"movieId": 3, "tagId": 1, "relevance": 0.88},
    {"movieId": 3, "tagId": 2, "relevance": 0.70},
    {"movieId": 4, "tagId": 3, "relevance": 0.92},
    {"movieId": 5, "tagId": 3, "relevance": 0.98},
    {"movieId": 5, "tagId": 4, "relevance": 0.15},  # unusual tag
]

# Train ratings (Cấm nạp Val/Test vào đây)
SYNTHETIC_TRAIN_RATINGS = [
    {"userId": 1, "movieId": 1, "rating": 5.0, "timestamp": 1000},
    {"userId": 1, "movieId": 2, "rating": 4.5, "timestamp": 1010},
    {"userId": 2, "movieId": 1, "rating": 5.0, "timestamp": 1020},
    {"userId": 2, "movieId": 3, "rating": 4.0, "timestamp": 1030},
    {"userId": 3, "movieId": 4, "rating": 2.0, "timestamp": 1040},  # w(2.0) = 0
    {"userId": 3, "movieId": 5, "rating": 5.0, "timestamp": 1050},
]

# Đếm kỳ vọng chính xác
EXPECTED_COUNTS = {
    "users": 4,
    "movies": 7,
    "genres": 4,
    "genome_tags": 4,
    "rated_edges": 6,
    "in_genre_edges": 8,
    "has_genome_tag_edges": 9,
}

