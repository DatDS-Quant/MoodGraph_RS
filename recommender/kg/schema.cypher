// ==============================================================================
// MoodGraph Task 3B: Graph Schema & Unique Constraints
// ==============================================================================

// 1. Ràng buộc duy nhất cho User (khóa userId)
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.userId IS UNIQUE;

// 2. Ràng buộc duy nhất cho Movie (khóa movieId)
CREATE CONSTRAINT movie_id_unique IF NOT EXISTS
FOR (m:Movie) REQUIRE m.movieId IS UNIQUE;

// 3. Ràng buộc duy nhất cho Genre (khóa name)
CREATE CONSTRAINT genre_name_unique IF NOT EXISTS
FOR (g:Genre) REQUIRE g.name IS UNIQUE;

// 4. Ràng buộc duy nhất cho GenomeTag (khóa tagId)
CREATE CONSTRAINT genome_tag_id_unique IF NOT EXISTS
FOR (t:GenomeTag) REQUIRE t.tagId IS UNIQUE;

// Indexes tối ưu hóa truy vấn cạnh
CREATE INDEX movie_title_index IF NOT EXISTS
FOR (m:Movie) ON (m.title);

CREATE INDEX rated_rating_index IF NOT EXISTS
FOR ()-[r:RATED]-() ON (r.rating);

