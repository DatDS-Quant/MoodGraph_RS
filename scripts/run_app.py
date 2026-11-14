"""
MoodGraph Unified Web Serving Launcher.
Phuc vu dong thoi ca RESTful API backend va Single-Page Application frontend tren cung mot cong (mac dinh: 8000).
Tu dong pre-warm cache snapshot Do thi tri thuc nhung (EmbeddedKnowledgeGraph) truoc khi mo ket noi.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# Thiet lap PYTHONPATH tro den thu muc goc cua du an neu can thiet
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("moodgraph.launcher")


def verify_and_prewarm_embedded_kg() -> None:
    """
    Kiem tra va nap truoc snapshot cache cua Do thi tri thuc nhung (EmbeddedKnowledgeGraph).
    Dam bao thoi gian phan hoi duoi 0.5 giay khi nguoi dung gui request dau tien.
    """
    cache_path = PROJECT_ROOT / "data" / "embedded_kg_cache.pkl.gz"
    logger.info("Kiem tra trang thai bo nho dem Do thi tri thuc nhung (Embedded KG)...")

    start_time = time.perf_counter()
    try:
        from recommender.kg.cache_manager import CacheManager
        graph = CacheManager.get_or_create_graph(data_root=str(PROJECT_ROOT / "data"))
        elapsed = time.perf_counter() - start_time

        cache_size_mb = cache_path.stat().st_size / (1024 * 1024) if cache_path.exists() else 0.0
        logger.info(
            f"Pre-warm Do thi tri thuc thanh cong trong {elapsed:.3f}s. "
            f"Thuc the: {len(graph.movies):,} phim, {len(graph.genres):,} the loai, "
            f"{len(graph.genome_tags):,} the tam trang genome. "
            f"Kich thuoc snapshot: {cache_size_mb:.2f} MB."
        )
    except Exception as exc:
        logger.warning(f"Luu y khi khoi tao EmbeddedKnowledgeGraph cache: {exc}")


def print_banner(host: str, port: int) -> None:
    """In thong diep chao mung va huong dan truy cap bang Unicode chuan."""
    banner = f"""
================================================================================
          MOODGRAPH - HE THONG GOI Y DIEN ANH DUA TREN DO THI TRI THUC
                        PHAN HE HOMEPAGE & ACADEMIC LAB
================================================================================
 [1] Giao dien Nguoi dung (Mode A Discovery & Mode B Lab):
     -> http://{host}:{port}/
     -> http://{host}:{port}/demo/

 [2] Tai lieu dac ta API truc quan (Swagger UI OpenAPI):
     -> http://{host}:{port}/docs
     -> http://{host}:{port}/redoc

 [3] Kiem tra trang thai he thong (Health & Diagnostics):
     -> http://{host}:{port}/health
     -> http://{host}:{port}/api/movies/sample

 [4] Phan he Phong thi nghiem Hoc thuat (Academic Lab Endpoints):
     -> http://{host}:{port}/api/lab/compare?user_id=1
     -> http://{host}:{port}/api/lab/graph/subgraph?user_id=1&movie_id=1
================================================================================
 May chu dang lang nghe tai http://{host}:{port}. Nhan Ctrl+C de dung may chu.
================================================================================
"""
    print(banner)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MoodGraph Unified Web Serving Launcher (FastAPI Backend + Static Frontend)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Dia chi IP may chu lang nghe (mac dinh: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Cong may chu phuc vu (mac dinh: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=False,
        help="Bat che do tu dong tai lai khi co thay doi ma nguon (development reload)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Muc do chi tiet ghi log cua Uvicorn",
    )
    parser.add_argument(
        "--skip-prewarm",
        action="store_true",
        default=False,
        help="Bo qua buoc pre-warm Embedded Knowledge Graph khi khoi dong",
    )

    args = parser.parse_args()

    # Pre-warm cache nhung do thi
    if not args.skip_prewarm:
        verify_and_prewarm_embedded_kg()

    # In banner giao dien
    print_banner(args.host, args.port)

    # Khoi chay Uvicorn Server
    import uvicorn

    uvicorn.run(
        "recommender.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
