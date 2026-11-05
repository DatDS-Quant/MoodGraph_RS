"""
Kiểm thử KG-01 và KG-02: Preflight Schema, Manifest & Unique Node Constraints.
"""

import json
from pathlib import Path
import pytest
from recommender.kg.config import load_kg_config
from recommender.kg.queries import ALL_CONSTRAINTS
from tests.kg.fixtures.synthetic_data import EXPECTED_COUNTS


def test_kg01_preflight_schema_and_manifest():
    """KG-01: Kiểm tra tính tồn tại của dữ liệu, manifest và ranh giới an toàn."""
    config = load_kg_config()
    assert config.data_root.exists(), f"Data root {config.data_root} không tồn tại"

    manifest_path = config.data_root / "manifest.json"
    assert manifest_path.exists(), "manifest.json không tồn tại trong data root"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Kiểm tra các dataset cốt lõi
    datasets = manifest["datasets"]
    assert "core_movies" in datasets
    assert "feature_movie_genres" in datasets
    assert "core_genome_tags" in datasets
    assert "core_genome_scores" in datasets
    assert "split_train" in datasets
    assert "split_validation" in datasets
    assert "split_test" in datasets

    # Kiểm tra số dòng theo spec
    assert datasets["core_movies"]["row_count"] == 62423
    assert datasets["feature_movie_genres"]["row_count"] == 107245
    assert datasets["core_genome_tags"]["row_count"] == 1128
    assert datasets["core_genome_scores"]["row_count"] == 15584448
    assert datasets["split_train"]["row_count"] == 24675013
    assert datasets["split_validation"]["row_count"] == 162541
    assert datasets["split_test"]["row_count"] == 162541


def test_kg02_unique_constraints_definition():
    """KG-02: Kiểm tra định nghĩa các ràng buộc tính duy nhất của các nút."""
    constraint_text = "\n".join(ALL_CONSTRAINTS)
    assert "u.userId IS UNIQUE" in constraint_text
    assert "m.movieId IS UNIQUE" in constraint_text
    assert "g.name IS UNIQUE" in constraint_text
    assert "t.tagId IS UNIQUE" in constraint_text

