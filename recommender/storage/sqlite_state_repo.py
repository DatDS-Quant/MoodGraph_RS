"""
MoodGraph Phase 5: SQLite Application State Repository.
Manages demo user interactions, watchlist, feedback ratings, user preferences,
and experiment logs in WAL mode without touching read-only MovieLens datasets.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("recommender.storage.sqlite_state_repo")


class SQLiteStateRepository:
    """Manages SQLite application state persistence with WAL mode and transaction safety."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            workspace_root = Path(__file__).resolve().parents[2]
            db_path = workspace_root / "data" / "app_state.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with foreign keys and WAL mode."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Creates required schemas and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS demo_users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    bio TEXT,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS saved_movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    movie_id INTEGER NOT NULL,
                    list_type TEXT NOT NULL DEFAULT 'watchlist' CHECK(list_type IN ('watchlist', 'favorites', 'hidden')),
                    created_at INTEGER NOT NULL,
                    UNIQUE(user_id, movie_id, list_type),
                    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_saved_movies_user ON saved_movies(user_id, list_type);

                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    genres_json TEXT NOT NULL DEFAULT '[]',
                    moods_json TEXT NOT NULL DEFAULT '[]',
                    min_year INTEGER,
                    max_year INTEGER,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS user_ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    movie_id INTEGER NOT NULL,
                    rating REAL NOT NULL CHECK(rating >= 0.5 AND rating <= 5.0),
                    feedback_text TEXT,
                    created_at INTEGER NOT NULL,
                    UNIQUE(user_id, movie_id),
                    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_user_ratings_user ON user_ratings(user_id);
                CREATE INDEX IF NOT EXISTS idx_user_ratings_movie ON user_ratings(movie_id);

                CREATE TABLE IF NOT EXISTS experiment_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'compare',
                    model_a TEXT NOT NULL,
                    model_b TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES demo_users(user_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_experiment_user ON experiment_sessions(user_id, created_at DESC);
            """)

            # Ensure default demo user exists for seamless demo experience
            cursor.execute("""
                INSERT OR IGNORE INTO demo_users (user_id, username, display_name, bio, created_at)
                VALUES ('demo_user_1', 'cinephile_dat', 'Dat Recommender Tester', 'Lead Researcher demo account', ?)
            """, (int(time.time()),))
            conn.commit()
        logger.info(f"SQLite application state initialized at {self.db_path} (WAL Mode enabled).")

    # User Management
    def ensure_user(self, user_id: str, display_name: Optional[str] = None) -> None:
        """Ensures a user record exists in demo_users."""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO demo_users (user_id, username, display_name, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_id, display_name or f"User {user_id}", int(time.time())))
            conn.commit()

    # Saved Movies (Watchlist / Favorites)
    def save_movie(self, user_id: str, movie_id: int, list_type: str = "watchlist") -> bool:
        """Saves a movie to user's watchlist or favorites."""
        self.ensure_user(user_id)
        with self._get_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO saved_movies (user_id, movie_id, list_type, created_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, movie_id, list_type) DO UPDATE SET created_at = excluded.created_at
                """, (user_id, movie_id, list_type, int(time.time())))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Error saving movie {movie_id} for user {user_id}: {e}")
                return False

    def remove_saved_movie(self, user_id: str, movie_id: int, list_type: str = "watchlist") -> bool:
        """Removes a movie from user's saved list."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM saved_movies
                WHERE user_id = ? AND movie_id = ? AND list_type = ?
            """, (user_id, movie_id, list_type))
            conn.commit()
            return cursor.rowcount > 0

    def list_saved_movies(self, user_id: str, list_type: Optional[str] = "watchlist") -> List[Dict[str, Any]]:
        """Lists saved movies for a user."""
        with self._get_connection() as conn:
            if list_type:
                rows = conn.execute("""
                    SELECT movie_id, list_type, created_at
                    FROM saved_movies
                    WHERE user_id = ? AND list_type = ?
                    ORDER BY created_at DESC
                """, (user_id, list_type)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT movie_id, list_type, created_at
                    FROM saved_movies
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    # User Demo Ratings
    def record_rating(self, user_id: str, movie_id: int, rating: float, feedback_text: Optional[str] = None) -> bool:
        """Records or updates a user rating for a movie."""
        if not (0.5 <= rating <= 5.0):
            raise ValueError(f"Rating must be between 0.5 and 5.0, got {rating}")
        self.ensure_user(user_id)
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO user_ratings (user_id, movie_id, rating, feedback_text, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, movie_id) DO UPDATE SET
                    rating = excluded.rating,
                    feedback_text = excluded.feedback_text,
                    created_at = excluded.created_at
            """, (user_id, movie_id, rating, feedback_text, int(time.time())))
            conn.commit()
            return True

    def get_user_demo_ratings(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves demo ratings provided by this user."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT movie_id, rating, feedback_text, created_at
                FROM user_ratings
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,)).fetchall()
            return [dict(r) for r in rows]

    # User Preferences
    def save_preferences(
        self,
        user_id: str,
        genres: List[str],
        moods: Optional[List[str]] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
    ) -> bool:
        """Saves user genre, mood, and release year preferences."""
        self.ensure_user(user_id)
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO user_preferences (user_id, genres_json, moods_json, min_year, max_year, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    genres_json = excluded.genres_json,
                    moods_json = excluded.moods_json,
                    min_year = excluded.min_year,
                    max_year = excluded.max_year,
                    updated_at = excluded.updated_at
            """, (
                user_id,
                json.dumps(genres),
                json.dumps(moods or []),
                min_year,
                max_year,
                int(time.time()),
            ))
            conn.commit()
            return True

    def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves user preferences."""
        with self._get_connection() as conn:
            row = conn.execute("""
                SELECT genres_json, moods_json, min_year, max_year, updated_at
                FROM user_preferences
                WHERE user_id = ?
            """, (user_id,)).fetchone()
            if not row:
                return None
            return {
                "user_id": user_id,
                "genres": json.loads(row["genres_json"]),
                "moods": json.loads(row["moods_json"]),
                "min_year": row["min_year"],
                "max_year": row["max_year"],
                "updated_at": row["updated_at"],
            }

    # Experiment Session Logging
    def log_experiment_session(
        self,
        session_id: str,
        user_id: str,
        model_a: str,
        model_b: str,
        params: Dict[str, Any],
        metrics: Dict[str, Any],
        mode: str = "compare",
    ) -> bool:
        """Logs a multi-model comparison experiment."""
        self.ensure_user(user_id)
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO experiment_sessions (session_id, user_id, mode, model_a, model_b, params_json, metrics_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                user_id,
                mode,
                model_a,
                model_b,
                json.dumps(params),
                json.dumps(metrics),
                int(time.time()),
            ))
            conn.commit()
            return True


_global_sqlite_repo: Optional[SQLiteStateRepository] = None


def get_sqlite_state_repository(db_path: Optional[Path] = None) -> SQLiteStateRepository:
    """Singleton getter for SQLiteStateRepository."""
    global _global_sqlite_repo
    if _global_sqlite_repo is None or db_path is not None:
        _global_sqlite_repo = SQLiteStateRepository(db_path)
    return _global_sqlite_repo
