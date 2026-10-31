"""
MoodGraph - HERMES Structured Persistent Memory Engine
Provides version-controlled structured knowledge storage in docs/agent_memory/
and an SQLite FTS5 full-text search index for fast retrieval across agent sessions.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_repo_root() -> Path:
    """Return repository root path."""
    return Path(__file__).resolve().parent.parent


@dataclass
class KnowledgeRecord:
    record_id: str
    module: str
    component: str
    topic: str
    category: str  # VERIFIED_FACT, ENGINEERING_DECISION, HYPOTHESIS, KNOWN_LIMITATION, OBSOLETE_INFO
    problem_statement: str
    solution_or_decision: str
    files_involved: List[str]
    relevant_tests: List[str]
    evidence: str
    code_version: str
    verification_status: str  # VERIFIED, PROPOSED, HYPOTHESIS
    date: str
    root_cause: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> KnowledgeRecord:
        return cls(**data)


class HermesMemory:
    """Manages structured JSON knowledge files and SQLite FTS5 search index."""

    def __init__(self, memory_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        root = get_repo_root()
        self.memory_dir = memory_dir or (root / "docs" / "agent_memory")
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or (self.memory_dir / "hermes_index.db")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        """Initialize SQLite tables with FTS5 virtual table."""
        with self._get_connection() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_records (
                    record_id TEXT PRIMARY KEY,
                    module TEXT,
                    component TEXT,
                    topic TEXT,
                    category TEXT,
                    problem_statement TEXT,
                    root_cause TEXT,
                    solution_or_decision TEXT,
                    files_involved TEXT,
                    relevant_tests TEXT,
                    evidence TEXT,
                    code_version TEXT,
                    verification_status TEXT,
                    date TEXT
                )
            """)
            con.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    record_id UNINDEXED,
                    module,
                    component,
                    topic,
                    category,
                    problem_statement,
                    solution_or_decision,
                    files_involved,
                    evidence,
                    content='knowledge_records',
                    content_rowid='rowid'
                )
            """)
            con.commit()

    def add_or_update_record(self, record: KnowledgeRecord) -> Path:
        """Save record to JSON and sync to SQLite index."""
        # Save JSON file (Source of truth)
        file_path = self.memory_dir / f"{record.record_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)

        # Index into SQLite
        with self._get_connection() as con:
            # Delete old FTS entry if exists
            con.execute("DELETE FROM knowledge_records WHERE record_id = ?", (record.record_id,))
            con.execute("DELETE FROM knowledge_fts WHERE record_id = ?", (record.record_id,))

            con.execute(
                """
                INSERT INTO knowledge_records (
                    record_id, module, component, topic, category, problem_statement,
                    root_cause, solution_or_decision, files_involved, relevant_tests,
                    evidence, code_version, verification_status, date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.module,
                    record.component,
                    record.topic,
                    record.category,
                    record.problem_statement,
                    record.root_cause or "",
                    record.solution_or_decision,
                    json.dumps(record.files_involved),
                    json.dumps(record.relevant_tests),
                    record.evidence,
                    record.code_version,
                    record.verification_status,
                    record.date,
                ),
            )
            con.execute(
                """
                INSERT INTO knowledge_fts (
                    rowid, record_id, module, component, topic, category,
                    problem_statement, solution_or_decision, files_involved, evidence
                ) VALUES (last_insert_rowid(), ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.record_id,
                    record.module,
                    record.component,
                    record.topic,
                    record.category,
                    record.problem_statement,
                    record.solution_or_decision,
                    json.dumps(record.files_involved),
                    record.evidence,
                ),
            )
            con.commit()

        return file_path

    def rebuild_index(self) -> int:
        """Rebuild SQLite index from all JSON files in docs/agent_memory/."""
        count = 0
        with self._get_connection() as con:
            con.execute("DELETE FROM knowledge_records")
            con.execute("DELETE FROM knowledge_fts")
            con.commit()

        json_files = list(self.memory_dir.glob("*.json"))
        for jf in json_files:
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rec = KnowledgeRecord.from_dict(data)
                self.add_or_update_record(rec)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load {jf.name}: {e}")

        return count

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge records using FTS5 or LIKE fallback."""
        results = []
        with self._get_connection() as con:
            try:
                # Try FTS5 MATCH
                cur = con.execute(
                    """
                    SELECT r.*, rank FROM knowledge_fts f
                    JOIN knowledge_records r ON f.record_id = r.record_id
                    WHERE knowledge_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, limit),
                )
                rows = cur.fetchall()
            except sqlite3.OperationalError:
                # Fallback to LIKE
                like_term = f"%{query}%"
                cur = con.execute(
                    """
                    SELECT *, 0 as rank FROM knowledge_records
                    WHERE topic LIKE ? OR problem_statement LIKE ? OR solution_or_decision LIKE ? OR evidence LIKE ?
                    LIMIT ?
                    """,
                    (like_term, like_term, like_term, like_term, limit),
                )
                rows = cur.fetchall()

            for row in rows:
                item = dict(row)
                item["files_involved"] = json.loads(item.get("files_involved", "[]"))
                item["relevant_tests"] = json.loads(item.get("relevant_tests", "[]"))
                results.append(item)

        return results

    def list_all(self) -> List[Dict[str, Any]]:
        """Return all knowledge records."""
        with self._get_connection() as con:
            cur = con.execute("SELECT * FROM knowledge_records ORDER BY module, record_id")
            rows = cur.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["files_involved"] = json.loads(item.get("files_involved", "[]"))
                item["relevant_tests"] = json.loads(item.get("relevant_tests", "[]"))
                results.append(item)
            return results


def main():
    parser = argparse.ArgumentParser(description="HERMES Memory Engine")
    subparsers = parser.add_subparsers(dest="command")

    # Search
    search_parser = subparsers.add_parser("search", help="Search memory")
    search_parser.add_argument("query", type=str, help="Search query")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results")

    # Rebuild
    subparsers.add_parser("rebuild", help="Rebuild index from JSON files")

    # List
    subparsers.add_parser("list", help="List all records")

    args = parser.parse_args()
    memory = HermesMemory()

    if args.command == "search":
        res = memory.search(args.query, limit=args.limit)
        print(f"Found {len(res)} results for '{args.query}':\n")
        for r in res:
            print(f"[{r['record_id']}] ({r['category']}) {r['topic']}")
            print(f"  Module: {r['module']} | Status: {r['verification_status']}")
            print(f"  Solution: {r['solution_or_decision'][:120]}...")
            print(f"  Files: {r['files_involved']}")
            print()
    elif args.command == "rebuild":
        n = memory.rebuild_index()
        print(f"Successfully rebuilt index with {n} records.")
    elif args.command == "list":
        records = memory.list_all()
        print(f"Total {len(records)} records in HERMES memory:")
        for r in records:
            print(f" - [{r['record_id']}] {r['module']}: {r['topic']} ({r['verification_status']})")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
