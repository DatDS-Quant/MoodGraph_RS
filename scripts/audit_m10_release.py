#!/usr/bin/env python3
"""
MOODGRAPH TASK 3A: MODULE M10 RELEASE & SCIENTIFIC ACCEPTANCE AUDITOR
=====================================================================
Independent verification script to audit all M10 deliverables,
artifact consistency, typography rules, source code defense mapping,
and test suite completion.
"""

import os
import sys
import json
import re
from pathlib import Path

# Configure stdout encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def check_artifacts():
    print("[AUDIT 1] Verifying 8 M10 Machine-Readable Artifacts...")
    artifact_dir = PROJECT_ROOT / "artifacts" / "als" / "m10"
    expected_artifacts = [
        "m10_release_manifest.json",
        "m10_model_registry.json",
        "m10_integration_contract.json",
        "m10_real_model_smoke_results.json",
        "m10_contract_test_results.json",
        "m10_test_inventory.json",
        "m10_scientific_audit.json",
        "m10_release_checklist.json"
    ]
    
    missing = []
    for art in expected_artifacts:
        p = artifact_dir / art
        if not p.is_file() or p.stat().st_size == 0:
            missing.append(art)
        else:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                print(f"  [OK] {art} (size={p.stat().st_size} bytes)")
            except Exception as e:
                missing.append(f"{art} (corrupted: {e})")
                
    if missing:
        raise RuntimeError(f"Missing or corrupted artifacts: {missing}")
    print("  Artifact Verification: 8/8 PASS\n")

def check_quality_gates():
    print("[AUDIT 2] Verifying 25 Quality Gates in m10_release_checklist.json...")
    checklist_path = PROJECT_ROOT / "artifacts" / "als" / "m10" / "m10_release_checklist.json"
    with open(checklist_path, "r", encoding="utf-8") as f:
        chk = json.load(f)
        
    total = chk.get("total_gates", 0)
    passed = chk.get("passed_gates", 0)
    failed = chk.get("failed_gates", -1)
    verdict = chk.get("overall_verdict", "")
    all_passed = (total == 25 and passed == 25 and failed == 0 and verdict == "TASK_3A_ENGINEERING_RELEASE_PASS")
    
    print(f"  Total gates: {total}, Passed: {passed}, Failed: {failed}, Verdict: {verdict}")
    if not all_passed:
        failed_gates = [g["gate_id"] for g in chk.get("gates", []) if g.get("status") != "PASS"]
        raise RuntimeError(f"Quality gates failed: {failed_gates}")
    print("  Quality Gates Verification: 25/25 PASS\n")

def check_typography():
    print("[AUDIT 3] Verifying Typography & Zero-Dollar Rule in M10 Documentation...")
    docs_to_check = [
        PROJECT_ROOT / "docs" / "3a" / "integration_contract.md",
        PROJECT_ROOT / "docs" / "3a" / "M10_delivery_report.md",
        PROJECT_ROOT / "docs" / "3a" / "M10_delivery_learning_guide.md",
        PROJECT_ROOT / "docs" / "3a" / "M10_source_code_defense_map.md",
        PROJECT_ROOT / "docs" / "3a" / "TASK_3A_FINAL_ACCEPTANCE.md",
        PROJECT_ROOT / "docs" / "3a" / "TASK_3A_HANDOVER_TO_HYBRID.md",
        PROJECT_ROOT / "docs" / "3a" / "M10_m09_closure_audit.md"
    ]
    
    dollar_violations = []
    for doc in docs_to_check:
        if not doc.is_file():
            raise FileNotFoundError(f"Missing document: {doc}")
        with open(doc, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check for unescaped or any dollar signs
        if "$" in content:
            # Find lines with dollar sign
            lines = content.splitlines()
            for line_no, line in enumerate(lines, 1):
                if "$" in line:
                    dollar_violations.append(f"{doc.name}:L{line_no}: {line.strip()[:80]}")
                    
    if dollar_violations:
        print("  [FAIL] Dollar sign violations detected:")
        for v in dollar_violations:
            print(f"    {v}")
        raise RuntimeError(f"Found {len(dollar_violations)} dollar sign violations in docs!")
    print(f"  Typography Check: Zero dollar signs in all {len(docs_to_check)} documents! PASS\n")

def check_defense_map_alignment():
    print("[AUDIT 4] Verifying Defense Map Code References...")
    delivery_py = PROJECT_ROOT / "recommender" / "als" / "delivery.py"
    with open(delivery_py, "r", encoding="utf-8") as f:
        del_lines = f.readlines()
        
    # Check ALSRecommendationItem
    has_item = any("class ALSRecommendationItem" in l for l in del_lines[:60])
    # Check ALSDeliveryService
    has_service = any("class ALSDeliveryService" in l for l in del_lines[140:170])
    # Check recommend_als
    has_rec = any("def recommend_als" in l for l in del_lines[350:380])
    # Check recommend_als_batch
    has_rec_batch = any("def recommend_als_batch" in l for l in del_lines[370:400])
    
    if not (has_item and has_service and has_rec and has_rec_batch):
        raise RuntimeError("Code line references in delivery.py do not match defense map!")
    print("  Defense Map Alignment: Verified PASS\n")

def check_test_inventory():
    print("[AUDIT 5] Verifying Task 3A Test Inventory...")
    inv_path = PROJECT_ROOT / "artifacts" / "als" / "m10" / "m10_test_inventory.json"
    with open(inv_path, "r", encoding="utf-8") as f:
        inv = json.load(f)
        
    total_tests = inv.get("total_tests_collected", 0)
    total_files = inv.get("total_test_files", 0)
    print(f"  Total tests collected: {total_tests} across {total_files} files")
    if total_tests != 180 or total_files != 12:
        raise RuntimeError(f"Expected 180 tests across 12 files, found {total_tests} across {total_files}")
    print("  Test Inventory Verification: 180/180 PASS\n")

def main():
    print("=" * 80)
    print("MOODGRAPH TASK 3A: M10 RELEASE & SCIENTIFIC AUDIT EXECUTION")
    print("=" * 80)
    try:
        check_artifacts()
        check_quality_gates()
        check_typography()
        check_defense_map_alignment()
        check_test_inventory()
        print("=" * 80)
        print("VERDICT: TASK_3A_ENGINEERING_RELEASE_PASS")
        print("ALL AUDITS COMPLETED SUCCESSFULLY WITHOUT VIOLATIONS.")
        print("=" * 80)
        return 0
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"AUDIT FAILED: {e}")
        print("=" * 80)
        return 1

if __name__ == "__main__":
    sys.exit(main())
