#!/usr/bin/env python3
"""
MoodGraph Task 3B: Knowledge Graph Recommender Smoke Test (Gate 0)

Kiểm tra:
1. Đọc và xác thực cấu hình biến môi trường.
2. Kiểm tra kết nối tới cơ sở dữ liệu Neo4j qua official Python driver.
3. Kiểm tra khả năng đọc Parquet data và schema từ data root.
4. Xác nhận trạng thái sẵn sàng chuyển đổi giữa Live Neo4j và Synthetic mode.
"""

import os
import sys
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from recommender.kg.config import load_kg_config


def run_smoke_test():
    print("=" * 70)
    print("MOODGRAPH TASK 3B: KNOWLEDGE GRAPH SMOKE TEST (GATE 0)")
    print("=" * 70)

    # 1. Config Check
    config = load_kg_config()
    print(f"[1/3] Cấu hình môi trường:")
    print(f"  - DATA_ROOT     : {config.data_root} (Tồn tại: {config.data_root.exists()})")
    print(f"  - NEO4J_URI     : {config.neo4j_uri}")
    print(f"  - NEO4J_USER    : {config.neo4j_user}")
    print(f"  - NEO4J_PASS    : {'*' * len(config.neo4j_password)} (Nguồn: {config.credential_source})")
    print(f"  - IMPORT_MODE   : {config.import_mode}")
    print(f"  - TOP_M_GENOME  : {config.tag_top_m}")
    print(f"  - BATCH_SIZE    : {config.batch_size}")
    print()

    # 2. Neo4j Connectivity Check
    print(f"[2/3] Kiểm tra kết nối Neo4j:")
    neo4j_connected = False
    neo4j_info = "OFFLINE"
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_user, config.neo4j_password)
        )
        server_info = driver.get_server_info()
        driver.verify_connectivity()
        neo4j_connected = True
        neo4j_info = f"ONLINE (Agent: {server_info.agent}, Protocol: {server_info.protocol_version})"
        print(f"  -> Kết nối Neo4j THÀNH CÔNG: {neo4j_info}")
        driver.close()
    except Exception as exc:
        print(f"  -> Không thể kết nối Neo4j tại {config.neo4j_uri}: {exc}")
        print(f"  -> Trạng thái: Chuyển sang SYNTHETIC IN-MEMORY & TEST FIXTURE MODE.")

    print()

    # 3. Parquet Data Preflight Check
    print(f"[3/3] Kiểm tra dữ liệu Parquet & Schema:")
    parquet_ok = False
    try:
        import pyarrow.parquet as pq

        datasets_to_check = [
            ("core/movies", ["movieId", "title"]),
            ("features/movie_genres", ["movieId", "genre"]),
            ("core/genome_tags", ["tagId", "tag"]),
            ("core/genome_scores", ["movieId", "tagId", "relevance"]),
            ("splits/train", ["userId", "movieId", "rating", "timestamp"]),
        ]

        all_exist = True
        for rel_path, required_cols in datasets_to_check:
            full_path = config.data_root / rel_path
            if full_path.exists():
                # Xử lý cả tệp parquet đơn lẻ hoặc thư mục parquet phân mảnh
                if full_path.is_dir():
                    parquet_files = list(full_path.glob("*.parquet"))
                    if not parquet_files:
                        print(f"  [FAIL] {rel_path}: Thư mục không chứa tệp .parquet")
                        all_exist = False
                        continue
                    schema = pq.read_schema(str(parquet_files[0]))
                else:
                    schema = pq.read_schema(str(full_path))

                field_names = schema.names
                missing = [c for c in required_cols if c not in field_names]
                if missing:
                    print(f"  [FAIL] {rel_path}: Thiếu cột {missing}")
                    all_exist = False
                else:
                    print(f"  [OK]   {rel_path}: Schema hợp lệ ({len(field_names)} cột: {', '.join(field_names[:4])}...)")
            else:
                print(f"  [MISS] {rel_path}: Không tìm thấy tại {full_path}")
                all_exist = False

        parquet_ok = all_exist
    except Exception as exc:
        print(f"  -> Lỗi khi đọc Parquet qua pyarrow: {exc}")

    print()
    print("=" * 70)
    print("TỔNG KẾT SMOKE TEST (GATE 0):")
    print(f"  - Parquet Schema Check : {'PASS' if parquet_ok else 'FAIL'}")
    print(f"  - Neo4j Connectivity  : {'PASS (LIVE)' if neo4j_connected else 'SYNTHETIC_FALLBACK_ACTIVE'}")
    print("=" * 70)

    if parquet_ok:
        print("[GATE 0 RESULT]: PASS")
        return 0
    else:
        print("[GATE 0 RESULT]: FAIL (Parquet datasets missing)")
        return 1


if __name__ == "__main__":
    sys.exit(run_smoke_test())
