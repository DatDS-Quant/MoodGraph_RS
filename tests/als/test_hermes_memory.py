"""
Automated Acceptance Tests for HERMES Persistent Memory Engine
Verifies all 8 protocol acceptance criteria:
1. Record insertion & JSON serialization
2. Session/process persistence across instances
3. FTS5 & fallback search retrieval
4. Deduplication on repeated indexing
5. Rebuilding database from source JSON files
6. Detection of invalid & malformed records
7. Category distinction (VERIFIED_FACT vs HYPOTHESIS)
8. Security & leakage guard against sensitive credentials
"""

import json
import pytest
from pathlib import Path

from scripts.hermes_memory import (
    HermesMemory,
    KnowledgeRecord,
    validate_record_data,
)


@pytest.fixture
def temp_hermes(tmp_path: Path) -> HermesMemory:
    """Fixture providing an isolated HermesMemory instance in a temp directory."""
    mem_dir = tmp_path / "agent_memory"
    db_path = mem_dir / "test_hermes.db"
    return HermesMemory(memory_dir=mem_dir, db_path=db_path)


def test_01_insert_and_serialize(temp_hermes: HermesMemory):
    """Case 1: Inserting a record writes valid JSON and updates SQLite index."""
    rec = KnowledgeRecord(
        record_id="HERMES-TEST-01",
        module="TEST",
        component="UnitTest",
        topic="Testing Memory Insertion",
        category="VERIFIED_FACT",
        problem_statement="Test problem",
        solution_or_decision="Test solution",
        files_involved=["test.py"],
        relevant_tests=["test_01"],
        evidence="Observed test output",
        code_version="commit_sha",
        verification_status="VERIFIED",
        date="2026-10-31",
    )

    path = temp_hermes.add_or_update_record(rec)
    assert path.exists()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["record_id"] == "HERMES-TEST-01"
    assert data["category"] == "VERIFIED_FACT"

    # Verify present in SQLite
    all_recs = temp_hermes.list_all()
    assert len(all_recs) == 1
    assert all_recs[0]["record_id"] == "HERMES-TEST-01"


def test_02_persistence_across_process_sessions(tmp_path: Path):
    """Case 2: Memory survives across independent instances/sessions."""
    mem_dir = tmp_path / "persist_mem"
    db_path = mem_dir / "persist.db"

    # Session 1: Create and write
    session1 = HermesMemory(memory_dir=mem_dir, db_path=db_path)
    rec = KnowledgeRecord(
        record_id="HERMES-PERSIST-01",
        module="M01",
        component="SessionTest",
        topic="Persistence Verification",
        category="ENGINEERING_DECISION",
        problem_statement="Verify persistence",
        solution_or_decision="Stored in SQLite and JSON",
        files_involved=["persist.py"],
        relevant_tests=["test_02"],
        evidence="Verified across instances",
        code_version="1234567",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    session1.add_or_update_record(rec)

    # Session 2: Fresh instance pointing to the same directory and DB
    session2 = HermesMemory(memory_dir=mem_dir, db_path=db_path)
    res = session2.search("Persistence")
    assert len(res) == 1
    assert res[0]["record_id"] == "HERMES-PERSIST-01"
    assert res[0]["category"] == "ENGINEERING_DECISION"


def test_03_search_retrieves_correct_lesson(temp_hermes: HermesMemory):
    """Case 3: Full-text search correctly indexes and retrieves relevant records."""
    rec1 = KnowledgeRecord(
        record_id="REC-01",
        module="M01",
        component="Spark",
        topic="Distributed Optimization with Snappy",
        category="VERIFIED_FACT",
        problem_statement="Compression choice",
        solution_or_decision="Use Snappy parquet compression",
        files_involved=["data_loader.py"],
        relevant_tests=["test_snappy"],
        evidence="Reduced storage by 82%",
        code_version="abc",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    rec2 = KnowledgeRecord(
        record_id="REC-02",
        module="M02",
        component="Metrics",
        topic="NDCG Ranking Calculation",
        category="VERIFIED_FACT",
        problem_statement="Evaluate ranking",
        solution_or_decision="Compute NDCG with log2 discount",
        files_involved=["evaluator.py"],
        relevant_tests=["test_ndcg"],
        evidence="21 tests pass",
        code_version="abc",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    temp_hermes.add_or_update_record(rec1)
    temp_hermes.add_or_update_record(rec2)

    # Search for "Snappy"
    search_snappy = temp_hermes.search("Snappy")
    assert len(search_snappy) == 1
    assert search_snappy[0]["record_id"] == "REC-01"

    # Search for "NDCG"
    search_ndcg = temp_hermes.search("NDCG")
    assert len(search_ndcg) == 1
    assert search_ndcg[0]["record_id"] == "REC-02"


def test_04_deduplication_on_repeated_insert(temp_hermes: HermesMemory):
    """Case 4: Repeatedly adding the same record_id updates instead of duplicating."""
    rec = KnowledgeRecord(
        record_id="DEDUP-01",
        module="M03",
        component="Popularity",
        topic="Initial Version",
        category="VERIFIED_FACT",
        problem_statement="P1",
        solution_or_decision="S1",
        files_involved=["pop.py"],
        relevant_tests=["t1"],
        evidence="E1",
        code_version="v1",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    temp_hermes.add_or_update_record(rec)
    assert len(temp_hermes.list_all()) == 1

    # Update the record with new evidence
    rec_updated = KnowledgeRecord(
        record_id="DEDUP-01",
        module="M03",
        component="Popularity",
        topic="Updated Version",
        category="VERIFIED_FACT",
        problem_statement="P1",
        solution_or_decision="S1 updated",
        files_involved=["pop.py"],
        relevant_tests=["t1"],
        evidence="E1 updated",
        code_version="v2",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    temp_hermes.add_or_update_record(rec_updated)

    all_recs = temp_hermes.list_all()
    # Total count must strictly still be 1 (not 2)
    assert len(all_recs) == 1
    assert all_recs[0]["topic"] == "Updated Version"


def test_05_rebuild_from_json_files(temp_hermes: HermesMemory):
    """Case 5: Database index can be rebuilt from JSON files on disk."""
    rec1 = KnowledgeRecord(
        record_id="RB-01",
        module="M01",
        component="C1",
        topic="Topic 1",
        category="VERIFIED_FACT",
        problem_statement="P",
        solution_or_decision="S",
        files_involved=[],
        relevant_tests=[],
        evidence="E",
        code_version="v",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    rec2 = KnowledgeRecord(
        record_id="RB-02",
        module="M02",
        component="C2",
        topic="Topic 2",
        category="VERIFIED_FACT",
        problem_statement="P",
        solution_or_decision="S",
        files_involved=[],
        relevant_tests=[],
        evidence="E",
        code_version="v",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    temp_hermes.add_or_update_record(rec1)
    temp_hermes.add_or_update_record(rec2)

    # Wipe SQLite tables
    with temp_hermes._get_connection() as con:
        con.execute("DELETE FROM knowledge_records")
        con.execute("DELETE FROM knowledge_fts")
        con.commit()
    assert len(temp_hermes.list_all()) == 0

    # Rebuild
    count = temp_hermes.rebuild_index()
    assert count == 2
    assert len(temp_hermes.list_all()) == 2


def test_06_detect_invalid_record(temp_hermes: HermesMemory):
    """Case 6: Missing required field or invalid category is detected."""
    # Invalid category
    invalid_cat_data = {
        "record_id": "INV-01",
        "module": "M01",
        "component": "C",
        "topic": "T",
        "category": "INVALID_CATEGORY",
        "problem_statement": "P",
        "solution_or_decision": "S",
        "files_involved": [],
        "relevant_tests": [],
        "evidence": "E",
        "code_version": "v",
        "verification_status": "VERIFIED",
        "date": "2026-10-31",
    }
    is_valid, errors = validate_record_data(invalid_cat_data)
    assert not is_valid
    assert any("Invalid category" in err for err in errors)

    # Missing field
    missing_data = {
        "record_id": "INV-02",
        "module": "M01",
    }
    is_valid, errors = validate_record_data(missing_data)
    assert not is_valid
    assert any("Missing required field" in err for err in errors)

    # Attempting to add invalid record raises ValueError
    with pytest.raises(ValueError, match="Knowledge record validation failed"):
        temp_hermes.add_or_update_record(KnowledgeRecord.from_dict(invalid_cat_data))


def test_07_distinguish_verified_vs_hypothesis(temp_hermes: HermesMemory):
    """Case 7: Clear distinction between VERIFIED_FACT and HYPOTHESIS records."""
    rec_fact = KnowledgeRecord(
        record_id="FACT-01",
        module="M03",
        component="Popularity",
        topic="Measured HitRate",
        category="VERIFIED_FACT",
        problem_statement="What was observed?",
        solution_or_decision="Count HR is 5.52%",
        files_involved=[],
        relevant_tests=[],
        evidence="Measured on 109k users",
        code_version="v1",
        verification_status="VERIFIED",
        date="2026-10-31",
    )
    rec_hypo = KnowledgeRecord(
        record_id="HYPO-01",
        module="M03",
        component="Popularity",
        topic="Causal Hypothesis",
        category="HYPOTHESIS",
        problem_statement="Why did Count win?",
        solution_or_decision="Hypothesis: popularity bias causes blockbusters to dominate next-watch",
        files_involved=[],
        relevant_tests=[],
        evidence="Theoretical reasoning, not yet fully ablated",
        code_version="v1",
        verification_status="HYPOTHESIS",
        date="2026-10-31",
    )
    temp_hermes.add_or_update_record(rec_fact)
    temp_hermes.add_or_update_record(rec_hypo)

    all_recs = temp_hermes.list_all()
    categories = {r["record_id"]: r["category"] for r in all_recs}
    assert categories["FACT-01"] == "VERIFIED_FACT"
    assert categories["HYPO-01"] == "HYPOTHESIS"


def test_08_sensitive_data_and_leak_prevention(temp_hermes: HermesMemory):
    """Case 8: Rejects records containing sensitive keywords (passwords, tokens, api keys)."""
    leak_data = {
        "record_id": "LEAK-01",
        "module": "M01",
        "component": "Auth",
        "topic": "Secret Key Leak",
        "category": "VERIFIED_FACT",
        "problem_statement": "Secret exposed",
        "solution_or_decision": "My api_key is secret123",
        "files_involved": [],
        "relevant_tests": [],
        "evidence": "E",
        "code_version": "v",
        "verification_status": "VERIFIED",
        "date": "2026-10-31",
    }
    is_valid, errors = validate_record_data(leak_data)
    assert not is_valid
    assert any("Forbidden sensitive keyword" in err for err in errors)


def test_09_detect_obsolete_info(temp_hermes: HermesMemory):
    """Case 9: Correctly tracks and detects obsolete knowledge records."""
    rec_obs = KnowledgeRecord(
        record_id="OBS-01",
        module="M00",
        component="OldProtocol",
        topic="Old 99 negative sampling protocol",
        category="OBSOLETE_INFO",
        problem_statement="Was negative sampling used?",
        solution_or_decision="Replaced by full-catalog leave-1-last protocol",
        files_involved=["evaluation_protocol.md"],
        relevant_tests=[],
        evidence="Protocol approved in M00",
        code_version="v0",
        verification_status="OBSOLETE",
        date="2026-10-25",
    )
    temp_hermes.add_or_update_record(rec_obs)
    report = temp_hermes.verify_all_records()
    assert report["valid_count"] == 1
    assert report["obsolete_count"] == 1
    assert "OBS-01" in report["obsolete_records"]
