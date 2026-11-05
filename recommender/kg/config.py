"""
Cấu hình tập trung cho Task 3B Knowledge Graph Recommender.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


@dataclass
class KGConfig:
    data_root: Path
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str
    credential_source: str
    import_mode: str
    tag_top_m: int
    min_liked_rating: float
    batch_size: int
    weight_alpha_genre: float
    weight_beta_genome: float
    weight_gamma_collab: float


def load_kg_config() -> KGConfig:
    """Tải và thẩm định cấu hình từ biến môi trường hoặc .env."""
    # Nạp dotenv nếu khả dụng
    try:
        from dotenv import load_dotenv
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
    except ImportError:
        pass

    # Xác định data root độc lập với thư mục chạy (CWD)
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_data_root = os.getenv("MOODGRAPH_DATA_ROOT")
    if raw_data_root:
        data_root = Path(raw_data_root)
        if not data_root.is_absolute():
            # Thử resolve tương đối theo project root hoặc CWD
            candidate = (project_root / data_root).resolve()
            data_root = candidate if candidate.exists() else data_root.resolve()
    else:
        # Tự động tìm thư mục data đã tiền xử lý theo thứ tự ưu tiên
        candidate_paths = [
            project_root / "data" / "processed",
            project_root / "data" / "moodgraph_processed_v1.0",
            (Path("data") / "processed").resolve(),
            (Path("data") / "moodgraph_processed_v1.0").resolve(),
        ]
        data_root = candidate_paths[0]
        for cp in candidate_paths:
            if cp.exists():
                data_root = cp
                break

    # Neo4j settings
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    
    if os.getenv("NEO4J_PASSWORD"):
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        credential_source = "environment_variable"
    else:
        neo4j_password = "moodgraph_secret"
        credential_source = "default_placeholder"

    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    import_mode = os.getenv("KG_IMPORT_MODE", "synthetic")
    tag_top_m = int(os.getenv("KG_TAG_TOP_M", "20"))
    min_liked_rating = float(os.getenv("KG_MIN_LIKED_RATING", "3.5"))
    batch_size = int(os.getenv("KG_BATCH_SIZE", "5000"))

    alpha = float(os.getenv("KG_WEIGHT_ALPHA_GENRE", "0.35"))
    beta = float(os.getenv("KG_WEIGHT_BETA_GENOME", "0.45"))
    gamma = float(os.getenv("KG_WEIGHT_GAMMA_COLLAB", "0.20"))

    # Đảm bảo tổng trọng số bằng 1
    total = alpha + beta + gamma
    if abs(total - 1.0) > 1e-4:
        alpha /= total
        beta /= total
        gamma /= total

    return KGConfig(
        data_root=data_root,
        neo4j_uri=neo4j_uri,
        neo4j_user=neo4j_user,
        neo4j_password=neo4j_password,
        neo4j_database=neo4j_database,
        credential_source=credential_source,
        import_mode=import_mode,
        tag_top_m=tag_top_m,
        min_liked_rating=min_liked_rating,
        batch_size=batch_size,
        weight_alpha_genre=alpha,
        weight_beta_genome=beta,
        weight_gamma_collab=gamma,
    )

