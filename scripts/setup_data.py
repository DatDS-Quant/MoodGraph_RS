"""
MoodGraph - Data Setup & Automatic Download Script
Dataset: MovieLens 25M

This script automates data acquisition for all teammates:
1. Downloads ml-25m.zip directly from official GroupLens servers.
2. Verifies MD5 checksum to ensure complete integrity.
3. Automatically extracts files into data/raw/ml-25m/.
"""

import os
import sys
import ssl
import hashlib
import zipfile
import urllib.request
from pathlib import Path

EXPECTED_MD5 = "6b51fb2759a8657d3bfcbfc42b592ada"
ZIP_URL = "https://files.grouplens.org/datasets/movielens/ml-25m.zip"


def get_ssl_context():
    """Create a robust SSL context that works across various Windows/Linux Python environments."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        pass
    
    try:
        return ssl.create_default_context()
    except Exception:
        # Fallback for systems with unconfigured CA bundles
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx


def setup_data():
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"
    dataset_dir = raw_dir / "ml-25m"
    zip_path = raw_dir / "ml-25m.zip"

    # 1. Check if already extracted
    required_files = [
        "ratings.csv",
        "movies.csv",
        "tags.csv",
        "genome-scores.csv",
        "genome-tags.csv",
        "links.csv",
    ]
    all_exist = all((dataset_dir / f).exists() for f in required_files)
    if all_exist:
        print("[OK] Dataset MovieLens 25M da co san va day du tai:")
        print(f"     {dataset_dir}")
        print("Teammate co the bat tay vao lam viec ngay!")
        return

    raw_dir.mkdir(parents=True, exist_ok=True)
    ctx = get_ssl_context()

    # 2. Check existing zip or download
    download_needed = True
    if zip_path.exists():
        print(f"[*] Tim thay file {zip_path.name} ({zip_path.stat().st_size:,} bytes). Dang kiem tra MD5...")
        hasher = hashlib.md5()
        with open(zip_path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024 * 4), b""):
                hasher.update(chunk)
        if hasher.hexdigest().lower() == EXPECTED_MD5:
            print("[OK] File zip hop le! Bo qua buoc tai.")
            download_needed = False
        else:
            print("[!] File zip cu bi loi checksum. Dang tai lai...")
            zip_path.unlink()

    if download_needed:
        print(f"[*] Dang tai MovieLens 25M (~250 MB) tu GroupLens...")
        print(f"    URL: {ZIP_URL}")
        req = urllib.request.Request(ZIP_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx) as resp, open(zip_path, "wb") as out_f:
            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0
            block_size = 1024 * 1024  # 1MB
            last_pct = -1
            while True:
                buf = resp.read(block_size)
                if not buf:
                    break
                downloaded += len(buf)
                out_f.write(buf)
                if total_size > 0:
                    pct = int(downloaded * 100 / total_size)
                    if pct != last_pct and pct % 10 == 0:
                        print(f"    Tien do: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct}%)")
                        last_pct = pct
        print("[OK] Tai file zip hoan tat!")

    # 3. Verify MD5
    print("[*] Dang doi soat MD5 checksum...")
    hasher = hashlib.md5()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024 * 4), b""):
            hasher.update(chunk)
    actual_md5 = hasher.hexdigest().lower()
    if actual_md5 != EXPECTED_MD5:
        print(f"[ERROR] Checksum khong khop! Thuc te: {actual_md5} != Mong doi: {EXPECTED_MD5}")
        sys.exit(1)
    print(f"[OK] MD5 Checksum PASSED ({actual_md5})!")

    # 4. Extract
    print(f"[*] Dang giai nen vao {raw_dir}...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(raw_dir)
    print(f"[OK] Giai nen thanh cong! Du lieu nam tai:\n     {dataset_dir}")
    print("\nDanh sach cac file da san sang:")
    for f in required_files:
        fp = dataset_dir / f
        if fp.exists():
            print(f"  - {f:18s} ({fp.stat().st_size / (1024*1024):.2f} MB)")
    print("\n>>> SAN SANG LAM VIEC!")


if __name__ == "__main__":
    setup_data()
