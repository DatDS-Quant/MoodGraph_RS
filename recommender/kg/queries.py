"""
Các mẫu truy vấn Cypher chuẩn hóa, an toàn với tham số cho Neo4j.
"""

# ==============================================================================
# 1. DDL: RÀNG BUỘC TÍNH DUY NHẤT & CHỈ MỤC
# ==============================================================================

CONSTRAINT_USER_UNIQUE = """
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE
"""

CONSTRAINT_MOVIE_UNIQUE = """
CREATE CONSTRAINT movie_id_unique IF NOT EXISTS
FOR (m:Movie) REQUIRE m.movieId IS UNIQUE
"""

CONSTRAINT_GENRE_UNIQUE = """
CREATE CONSTRAINT genre_name_unique IF NOT EXISTS
FOR (g:Genre) REQUIRE g.name IS UNIQUE
"""

CONSTRAINT_GENOME_TAG_UNIQUE = """
CREATE CONSTRAINT genome_tag_id_unique IF NOT EXISTS
FOR (t:GenomeTag) REQUIRE t.tagId IS UNIQUE
"""

INDEX_RATED_RATING = """
CREATE INDEX rated_rating_index IF NOT EXISTS
FOR ()-[r:RATED]-() ON (r.rating)
"""

INDEX_MOVIE_TITLE = """
CREATE INDEX movie_title_index IF NOT EXISTS
FOR (m:Movie) ON (m.title)
"""

ALL_CONSTRAINTS = [
    CONSTRAINT_USER_UNIQUE,
    CONSTRAINT_MOVIE_UNIQUE,
    CONSTRAINT_GENRE_UNIQUE,
    CONSTRAINT_GENOME_TAG_UNIQUE,
    INDEX_RATED_RATING,
    INDEX_MOVIE_TITLE
]

# ==============================================================================
# 2. DML BATCH IMPORT (UNWIND + MERGE IDEMPOTENT)
# ==============================================================================

IMPORT_USERS_BATCH = """
UNWIND $batch AS row
MERGE (u:User {userId: row.userId})
"""

IMPORT_MOVIES_BATCH = """
UNWIND $batch AS row
MERGE (m:Movie {movieId: row.movieId})
SET m.title = row.title,
    m.genresRaw = row.genresRaw
"""

IMPORT_GENRES_BATCH = """
UNWIND $batch AS row
MERGE (g:Genre {name: row.name})
"""

IMPORT_GENOME_TAGS_BATCH = """
UNWIND $batch AS row
MERGE (t:GenomeTag {tagId: row.tagId})
SET t.name = row.name
"""

IMPORT_MOVIE_GENRES_BATCH = """
UNWIND $batch AS row
MATCH (m:Movie {movieId: row.movieId})
MATCH (g:Genre {name: row.genre})
MERGE (m)-[:IN_GENRE]->(g)
"""

IMPORT_GENOME_SCORES_BATCH = """
UNWIND $batch AS row
MATCH (m:Movie {movieId: row.movieId})
MATCH (t:GenomeTag {tagId: row.tagId})
MERGE (m)-[r:HAS_GENOME_TAG]->(t)
SET r.relevance = row.relevance
"""

IMPORT_TRAIN_RATINGS_BATCH = """
UNWIND $batch AS row
MATCH (u:User {userId: row.userId})
MATCH (m:Movie {movieId: row.movieId})
MERGE (u)-[r:RATED]->(m)
SET r.rating = row.rating,
    r.timestamp = row.timestamp
"""

# ==============================================================================
# 3. TRUY VẤN ĐƯỜNG ĐI SUY LUẬN P1, P2, P3 & EVIDENCE
# ==============================================================================

# P1: Đường đồng thể loại (Genre Path)
QUERY_P1_GENRE_PATHS = """
MATCH (u:User {userId: $userId})-[r:RATED]->(liked:Movie)-[:IN_GENRE]->(g:Genre)<-[:IN_GENRE]-(candidate:Movie)
WHERE r.rating >= $minLikedRating
  AND NOT EXISTS { MATCH (u)-[:RATED]->(candidate) }
RETURN candidate.movieId AS candidateMovieId,
       candidate.title AS candidateTitle,
       liked.movieId AS sourceMovieId,
       liked.title AS sourceTitle,
       g.name AS sharedGenre,
       r.rating AS sourceRating
"""

# P2: Đường đặc trưng ngữ nghĩa Genome (Genome Path)
QUERY_P2_GENOME_PATHS = """
MATCH (u:User {userId: $userId})-[r:RATED]->(liked:Movie)-[rel1:HAS_GENOME_TAG]->(t:GenomeTag)<-[rel2:HAS_GENOME_TAG]-(candidate:Movie)
WHERE r.rating >= $minLikedRating
  AND NOT EXISTS { MATCH (u)-[:RATED]->(candidate) }
RETURN candidate.movieId AS candidateMovieId,
       candidate.title AS candidateTitle,
       liked.movieId AS sourceMovieId,
       liked.title AS sourceTitle,
       t.tagId AS sharedTagId,
       t.name AS sharedTagName,
       r.rating AS sourceRating,
       rel1.relevance AS sourceRelevance,
       rel2.relevance AS candidateRelevance
"""

# P3: Đường cộng tác đa bước User-Movie-User-Movie (Collaborative Graph Path)
QUERY_P3_COLLAB_PATHS = """
MATCH (u:User {userId: $userId})-[r1:RATED]->(anchor:Movie)<-[r2:RATED]-(neighbor:User)-[r3:RATED]->(candidate:Movie)
WHERE r1.rating >= $minLikedRating
  AND r2.rating >= $minLikedRating
  AND r3.rating >= $minLikedRating
  AND neighbor.userId <> u.userId
  AND NOT EXISTS { MATCH (u)-[:RATED]->(candidate) }
RETURN candidate.movieId AS candidateMovieId,
       candidate.title AS candidateTitle,
       anchor.movieId AS anchorMovieId,
       anchor.title AS anchorTitle,
       neighbor.userId AS neighborUserId,
       r1.rating AS userRating,
       r2.rating AS neighborAnchorRating,
       r3.rating AS neighborCandidateRating
LIMIT $limit
"""

# Lấy các phim người dùng đã xem trong Train
QUERY_SEEN_MOVIES = """
MATCH (u:User {userId: $userId})-[r:RATED]->(m:Movie)
RETURN m.movieId AS movieId, r.rating AS rating
"""

# Thống kê số lượng node và quan hệ
QUERY_GRAPH_COUNTS = """
CALL {
    MATCH (u:User) RETURN count(u) AS userCount
}
CALL {
    MATCH (m:Movie) RETURN count(m) AS movieCount
}
CALL {
    MATCH (g:Genre) RETURN count(g) AS genreCount
}
CALL {
    MATCH (t:GenomeTag) RETURN count(t) AS tagCount
}
CALL {
    MATCH ()-[r:RATED]->() RETURN count(r) AS ratedCount
}
CALL {
    MATCH ()-[r:IN_GENRE]->() RETURN count(r) AS inGenreCount
}
CALL {
    MATCH ()-[r:HAS_GENOME_TAG]->() RETURN count(r) AS hasGenomeTagCount
}
RETURN userCount, movieCount, genreCount, tagCount, ratedCount, inGenreCount, hasGenomeTagCount
"""

